import asyncio
import json
import logging
import os
from datetime import datetime
from uuid import uuid4
from fastapi import WebSocket, WebSocketDisconnect
from app.websocket.manager import ws_manager
from app.core.event_bus import event_bus
from app.services.agent_manager import agent_manager
from app.services.activity_feed import activity_feed  # noqa: F401 — ensures activity feed subscriber is registered
from app.db.repository import load_project_messages, load_project_agents, load_project, save_project, save_message
from app.models.message import Message
from app.models.agent import AgentStatus

logger = logging.getLogger(__name__)


async def handle_websocket(websocket: WebSocket, project_id: str, user_id: str = "user"):
    await ws_manager.connect(websocket, project_id, user_id)

    async def on_event(data: dict):
        await ws_manager.broadcast(project_id, data)

    event_bus.subscribe("*", on_event)

    try:
        while True:
            raw = await websocket.receive_text()
            try:
                data = json.loads(raw)
                msg_type = data.get("type", "chat")

                if msg_type == "ping":
                    await websocket.send_text(json.dumps({"type": "pong"}))

                elif msg_type == "chat":
                    content = data.get("content", "")
                    sender = data.get("sender_name", "User")
                    channel = data.get("channel", "general")
                    # Parse @mentions from content + client-provided mentions
                    import re as _re
                    from app.db.repository import load_project_agents
                    content_mentions = set(_re.findall(r'@(\w[\w-]*)', content))
                    agent_names = {a.name for a in await load_project_agents(project_id)}
                    all_mentions = content_mentions & agent_names
                    all_mentions |= set(data.get("mentions") or [])
                    # Save image attachments to disk
                    attachments = data.get("attachments", [])
                    for att in attachments:
                        if att.get("type") == "image" and att.get("data"):
                            import hashlib
                            img_data = att["data"]
                            if "," in img_data:
                                img_data = img_data.split(",", 1)[1]
                            img_bytes = __import__("base64").b64decode(img_data)
                            ext = os.path.splitext(att.get("name", "image.png"))[1] or ".png"
                            img_id = f"img_{hashlib.md5(img_bytes).hexdigest()[:12]}{ext}"
                            img_dir = os.path.join("data", "uploads")
                            os.makedirs(img_dir, exist_ok=True)
                            with open(os.path.join(img_dir, img_id), "wb") as f:
                                f.write(img_bytes)
                            att["id"] = img_id
                            del att["data"]

                    msg = {
                        "type": "message",
                        "id": f"msg-{uuid4().hex[:8]}",
                        "project_id": project_id,
                        "sender_id": user_id,
                        "sender_name": sender,
                        "sender_role": "user",
                        "content": content,
                        "msg_type": "chat",
                        "channel": channel,
                        "thread_id": data.get("thread_id", None),
                        "reply_to": None,
                        "mentions": list(all_mentions),
                        "attachments": attachments,
                        "metadata": {},
                        "timestamp": datetime.utcnow().isoformat() + "Z",
                    }
                    await event_bus.publish("message", msg)
                    asyncio.create_task(save_message(Message(**msg)))

                    # Create notification for @mentions
                    if all_mentions:
                        from app.db.repository import save_notification
                        from app.models.ops import Notification
                        for mention in all_mentions:
                            n = Notification(
                                project_id=project_id, type="mention",
                                title=f"@{sender} mentioned you",
                                body=content[:200], link=f"channel://{channel}",
                            )
                            asyncio.create_task(save_notification(n))
                            await event_bus.publish("notification", n.model_dump())

                    # Self-heal: ensure the Coworker is loaded for this project
                    # (Render free tier spins down; in-memory boss is lost on cold start).
                    if agent_manager.boss is None or agent_manager.boss.agent.project_id != project_id:
                        try:
                            await agent_manager.restore_boss(project_id)
                        except Exception as e:
                            logger.warning("lazy restore_boss failed: %s", e)

                    if channel.startswith("dm-"):
                        agent_name = channel[3:]
                        found = False
                        if agent_manager.boss:
                            coworker_slug = agent_manager.boss.name.lower().replace(" ", "-")
                            if agent_name.lower() == coworker_slug:
                                await agent_manager.boss.handle_user_request(project_id, content, channel, attachments)
                                found = True
                            else:
                                for wid, worker in agent_manager.boss.team.items():
                                    worker_slug = worker.name.lower().replace(" ", "-")
                                    if agent_name.lower() == worker_slug:
                                        await worker.handle_direct_message(project_id, content)
                                        found = True
                                        break
                        if not found:
                            await ws_manager.broadcast(project_id, {
                                "type": "message",
                                "id": f"msg-{uuid4().hex[:8]}",
                                "project_id": project_id,
                                "sender_id": "system",
                                "sender_name": "System",
                                "sender_role": "system",
                                "content": f"Agent '{agent_name}' not found.",
                                "msg_type": "system",
                                "channel": channel,
                            })
                    elif agent_manager.boss:
                        await agent_manager.boss.handle_user_request(project_id, content, channel, attachments)

                elif msg_type == "command":
                    cmd = data.get("command", "")
                    args = data.get("args", {})
                    await handle_command(project_id, cmd, args, websocket, user_id)

            except json.JSONDecodeError:
                await websocket.send_text(json.dumps({"type": "error", "message": "Invalid JSON"}))

    except WebSocketDisconnect:
        logger.info("WebSocket disconnected: project=%s", project_id)
    except Exception as e:
        logger.error("WebSocket error for project %s: %s", project_id, e)
        try:
            await ws_manager.broadcast(project_id, {"type": "message", "id": f"err-{uuid4().hex[:8]}", "project_id": project_id, "sender_id": "system", "sender_name": "System", "sender_role": "system", "content": f"Connection error: {e}", "msg_type": "system", "channel": "general", "timestamp": datetime.utcnow().isoformat() + "Z"})
        except Exception:
            pass
    finally:
        event_bus.unsubscribe("*", on_event)
        await ws_manager.disconnect(websocket, project_id)


async def handle_command(project_id: str, command: str, args: dict, ws: WebSocket, user_id: str = "user"):
    from app.models.project import Project
    from app.workspace.manager import get_file_tree

    if command == "create_project":
        try:
            title = args.get("title", "Untitled Project")
            description = args.get("description", "")
            project = Project(title=title, description=description, id=project_id)
            await save_project(project)

            # Create default channels
            from app.db.repository import save_channel
            from app.models.channel import Channel
            for ch_def in [{"id":"general","name":"#general"}, {"id":"planning","name":"#planning"}, {"id":"architecture","name":"#architecture"}, {"id":"dev","name":"#dev"}]:
                ch = Channel(id=ch_def["id"], project_id=project_id, name=ch_def["name"])
                asyncio.create_task(save_channel(ch))

            boss = await agent_manager.create_coworker(project_id)
            await boss.initialize_workspace(project)
            agents = agent_manager.list_agents(project_id)
            await ws_manager.broadcast(project_id, {"type": "status", "agents": agents})
            await ws.send_text(json.dumps({
                "type": "project_created",
                "project_id": project_id,
                "boss_name": boss.name,
            }))
        except Exception as e:
            logger.error("Failed to create project: %s", e)
            await ws.send_text(json.dumps({
                "type": "error",
                "message": f"Failed to create project: {e}",
            }))

    elif command == "archive_project":
        proj = await load_project(project_id)
        if proj:
            proj.status = "cancelled"
            asyncio.create_task(save_project(proj))
            await ws_manager.broadcast(project_id, {"type": "project_updated", "project": proj.model_dump()})

    elif command == "delete_project":
        proj = await load_project(project_id)
        if proj:
            proj.status = "cancelled"
            proj.title += " (deleted)"
            asyncio.create_task(save_project(proj))
            await ws_manager.broadcast(project_id, {"type": "project_updated", "project": proj.model_dump()})

    elif command == "update_project_tags":
        proj = await load_project(project_id)
        if proj:
            proj.tags = args.get("tags", [])
            asyncio.create_task(save_project(proj))
            await ws_manager.broadcast(project_id, {"type": "project_updated", "project": proj.model_dump()})

    elif command == "delegate":
        task_title = args.get("task", "")
        role = args.get("role", "")
        if agent_manager.boss and agent_manager.boss.agent.project_id == project_id:
            task = await agent_manager.boss.create_task(task_title, assigned_role=role)
            await ws.send_text(json.dumps({
                "type": "task_created",
                "task_id": task.id,
                "title": task.title,
                "assigned_to": task.assigned_to,
            }))

    elif command == "add_agent":
        role_name = args.get("role", "engineer")
        name = args.get("name", f"Agent-{len(agent_manager.workers) + 1}")
        specialization = args.get("specialization", role_name)
        worker = await agent_manager.create_worker(project_id, name, role_name)
        await ws.send_text(json.dumps({
            "type": "agent_added",
            "agent_id": worker.id,
            "name": worker.name,
            "role": role_name,
        }))

    elif command == "create_agent":
        if agent_manager.boss and agent_manager.boss.agent.project_id == project_id:
            role = args.get("role", "backend_engineer")
            name = args.get("name", f"Agent-{len(agent_manager.boss.team) + 1}")
            specialization = args.get("specialization", role)
            await agent_manager.boss.create_team([{
                "role": role,
                "name": name,
                "specialization": specialization,
                "skills": args.get("skills", [role]),
                "personality": args.get("personality", "professional and collaborative"),
                "display_name": args.get("display_name") or name,
                "mission": args.get("mission", ""),
                "channel": args.get("channel", "general"),
            }], announce_channel="general")
            await ws.send_text(json.dumps({"type": "agent_created", "name": name, "role": role}))
        else:
            await ws.send_text(json.dumps({"type": "error", "message": "No Coworker agent available"}))

    elif command == "retire_agent":
        agent_id = args.get("agent_id", "")
        try:
            if agent_manager.boss and agent_id in agent_manager.boss.team:
                agent_manager.boss.team.pop(agent_id)
                if agent_manager.boss.project:
                    agent_manager.boss.project.agent_ids = [aid for aid in agent_manager.boss.project.agent_ids if aid != agent_id]
                await event_bus.publish("agent_removed", {"agent_id": agent_id, "project_id": project_id})
            else:
                await agent_manager.remove_agent(agent_id)
                await event_bus.publish("agent_removed", {"agent_id": agent_id, "project_id": project_id})
            if agent_manager.registry:
                await agent_manager.registry.remove(agent_id)
        except Exception:
            pass
        await ws.send_text(json.dumps({"type": "agent_retired", "agent_id": agent_id}))

    elif command == "create_channel":
        from app.models.channel import Channel
        channel_id = args.get("id", args.get("name", "").lower().replace(" ", "-"))
        channel_name = args.get("name", channel_id)
        parent_id = args.get("parent_id")
        ch_type = args.get("type", "channel")
        ch = Channel(
            id=channel_id,
            project_id=project_id,
            name=f"#{channel_name}",
            parent_id=parent_id,
            type=ch_type,
        )
        from app.db.repository import save_channel
        asyncio.create_task(save_channel(ch))
        await event_bus.publish("channel_created", {**ch.model_dump(), "channel_type": ch.type})

    elif command == "edit_message":
        msg_id = args.get("message_id", "")
        content = args.get("content", "")
        from app.db.repository import update_message_content
        if msg_id and content and await update_message_content(project_id, msg_id, content):
            await ws_manager.broadcast(project_id, {"type": "message_edited", "message_id": msg_id, "content": content})

    elif command == "delete_message":
        msg_id = args.get("message_id", "")
        from app.db.repository import delete_message
        if msg_id and await delete_message(project_id, msg_id):
            await ws_manager.broadcast(project_id, {"type": "message_deleted", "message_id": msg_id})

    elif command == "create_thread":
        from app.models.thread import Thread
        parent_msg_id = args.get("parent_message_id", "")
        title = args.get("title", "Thread")
        channel_name = args.get("channel", "general")
        thread_id = f"thread-{uuid4().hex[:8]}"
        thread = Thread(
            id=thread_id,
            project_id=project_id,
            channel=channel_name,
            parent_message_id=parent_msg_id,
            title=title,
            created_by=user_id,
        )
        from app.db.repository import save_thread
        asyncio.create_task(save_thread(thread))
        await event_bus.publish("thread_created", thread.model_dump())

    elif command == "status":
        agents = agent_manager.list_agents(project_id)
        await ws.send_text(json.dumps({
            "type": "status",
            "agents": agents,
        }))

    elif command == "load_project":
        try:
            messages = await load_project_messages(project_id, limit=200)
        except Exception as e:
            logger.warning("load_project_messages failed: %s", e)
            messages = []
        try:
            agents = await load_project_agents(project_id)
        except Exception as e:
            logger.warning("load_project_agents failed: %s", e)
            agents = []
        try:
            proj = await load_project(project_id)
        except Exception as e:
            logger.warning("load_project failed: %s", e)
            proj = None
        try:
            file_tree = await get_file_tree(project_id)
        except Exception as e:
            logger.warning("get_file_tree failed: %s", e)
            file_tree = []

        # Restore the CoworkerAgent in memory so messages get responses
        try:
            await agent_manager.restore_boss(project_id)
            await agent_manager.restore_workspace(project_id)
        except Exception as e:
            logger.warning("restore failed: %s", e)

        await ws.send_text(json.dumps({
            "type": "message_history",
            "messages": [m.model_dump() for m in messages],
        }))
        await ws.send_text(json.dumps({
            "type": "status",
            "agents": [a.model_dump() for a in agents],
        }))
        await ws.send_text(json.dumps({
            "type": "project_data",
            "project": proj.model_dump() if proj else None,
        }))
        await ws.send_text(json.dumps({
            "type": "file_tree",
            "files": file_tree,
        }))
        try:
            from app.db.repository import load_project_tasks
            tasks = await load_project_tasks(project_id)
            await ws.send_text(json.dumps({
                "type": "task_list",
                "tasks": [t.model_dump(mode="json") for t in tasks],
            }))
        except Exception as e:
            logger.warning("load_project_tasks failed: %s", e)
        try:
            from app.db.repository import load_project_channels_tree, load_project_threads
            channel_tree = await load_project_channels_tree(project_id)
            await ws.send_text(json.dumps({
                "type": "channel_tree",
                "channels": channel_tree,
            }))
            threads = await load_project_threads(project_id)
            await ws.send_text(json.dumps({
                "type": "thread_list",
                "threads": [t.model_dump() for t in threads],
            }))
        except Exception as e:
            logger.warning("load channels/threads failed: %s", e)

        try:
            from app.db.repository import load_execution_logs, load_notifications, load_approvals
            logs = await load_execution_logs(project_id)
            await ws.send_text(json.dumps({
                "type": "execution_logs",
                "logs": [l.model_dump() for l in logs],
            }))
            notifs = await load_notifications(project_id)
            await ws.send_text(json.dumps({
                "type": "notification_list",
                "notifications": [n.model_dump() for n in notifs],
            }))
            approvals = await load_approvals(project_id)
            await ws.send_text(json.dumps({
                "type": "approval_list",
                "approvals": [a.model_dump() for a in approvals],
            }))
        except Exception as e:
            logger.warning("load ops data failed: %s", e)

        try:
            from app.db.repository import load_lifecycle_audits
            audits = await load_lifecycle_audits(project_id)
            await ws.send_text(json.dumps({
                "type": "lifecycle_audit_list",
                "audits": audits,
            }))
        except Exception as e:
            logger.warning("load lifecycle audits failed: %s", e)

    elif command == "approve":
        approval_id = args.get("approval_id", "")
        from app.db.repository import get_approval, save_approval, delete_channel
        from app.models.ops import Approval
        a = await get_approval(approval_id)
        if a and a.status == "pending":
            a.status = "approved"
            await save_approval(a)
            await event_bus.publish("approval_updated", a.model_dump())
            # Execute the approved action
            payload = a.payload or {}
            atype = payload.get("type")
            if atype == "delete_channel":
                cid = payload.get("id") or payload.get("channel") or ""
                if cid:
                    deleted = await delete_channel(project_id, cid)
                    await event_bus.publish("channel_deleted", {"project_id": project_id, "ids": deleted})
            elif atype == "retire_agent":
                aid = payload.get("agent_id", "")
                if aid and agent_manager.boss and aid in agent_manager.boss.team:
                    removed = agent_manager.boss.team.pop(aid, None)
                    if removed:
                        await event_bus.publish("agent_removed", {"agent_id": aid, "project_id": project_id})
        await ws.send_text(json.dumps({"type": "approval_updated", **a.model_dump()} if a else {}))

    elif command == "reject":
        approval_id = args.get("approval_id", "")
        from app.db.repository import get_approval, save_approval
        a = await get_approval(approval_id)
        if a and a.status == "pending":
            a.status = "rejected"
            await save_approval(a)
            await event_bus.publish("approval_updated", a.model_dump())

    elif command == "switch_project":
        new_project_id = args.get("project_id", "")
        if new_project_id:
            # Switch agent manager to new project
            try:
                await agent_manager.switch_project(new_project_id)
            except Exception as e:
                logger.warning("switch_project failed: %s", e)

            # Restore the CoworkerAgent + channels in memory so returning users can chat
            try:
                await agent_manager.restore_boss(new_project_id)
                await agent_manager.restore_workspace(new_project_id)
            except Exception as e:
                logger.warning("restore failed: %s", e)

            # Load new project data
            try:
                messages = await load_project_messages(new_project_id, limit=200)
            except Exception as e:
                logger.warning("load_project_messages failed: %s", e)
                messages = []
            try:
                agents = await load_project_agents(new_project_id)
            except Exception as e:
                logger.warning("load_project_agents failed: %s", e)
                agents = []
            try:
                proj = await load_project(new_project_id)
            except Exception as e:
                logger.warning("load_project failed: %s", e)
                proj = None
            try:
                file_tree = await get_file_tree(new_project_id)
            except Exception as e:
                logger.warning("get_file_tree failed: %s", e)
                file_tree = []

            await ws.send_text(json.dumps({
                "type": "message_history",
                "messages": [m.model_dump() for m in messages],
            }))
            await ws.send_text(json.dumps({
                "type": "status",
                "agents": [a.model_dump() for a in agents],
            }))
            await ws.send_text(json.dumps({
                "type": "project_data",
                "project": proj.model_dump() if proj else None,
            }))
            await ws.send_text(json.dumps({
                "type": "file_tree",
                "files": file_tree,
            }))
            try:
                from app.db.repository import load_project_tasks
                tasks = await load_project_tasks(new_project_id)
                await ws.send_text(json.dumps({
                    "type": "task_list",
                    "tasks": [t.model_dump(mode="json") for t in tasks],
                }))
            except Exception as e:
                logger.warning("load_project_tasks failed: %s", e)
            await ws.send_text(json.dumps({
                "type": "project_switched",
                "project_id": new_project_id,
            }))

    elif command == "create_task":
        from app.models.task import Task, TaskPriority
        from app.db.repository import save_task
        title = args.get("title", "").strip()
        if title:
            task = Task(
                project_id=project_id,
                title=title,
                description=args.get("description", ""),
                priority=args.get("priority", "medium"),
                assigned_to=args.get("assigned_to"),
                assigned_by=user_id,
            )
            if args.get("assigned_to"):
                task.status = "assigned"
            await save_task(task)
            await ws_manager.broadcast(project_id, {"type": "task_created", **task.model_dump()})

    elif command == "update_task":
        from app.db.repository import update_task_fields
        task_id = args.get("task_id", "")
        fields = {}
        for k in ("status", "priority", "assigned_to", "title", "description"):
            if k in args:
                fields[k] = args[k]
        if task_id and fields:
            updated = await update_task_fields(project_id, task_id, **fields)
            if updated:
                await ws_manager.broadcast(project_id, {"type": "task_updated", "id": updated.id, **updated.model_dump()})

    elif command in ("pause_agent", "resume_agent"):
        from app.models.agent import AgentStatus
        agent_id = args.get("agent_id", "")
        target = None
        if agent_manager.boss and agent_manager.boss.id == agent_id:
            target = agent_manager.boss
        elif agent_manager.boss and agent_id in agent_manager.boss.team:
            target = agent_manager.boss.team[agent_id]
        if target:
            new_state = AgentStatus.paused if command == "pause_agent" else AgentStatus.idle
            try:
                await target.set_status(new_state, reason=("Paused by user" if command == "pause_agent" else "Resumed by user"))
            except Exception as e:
                logger.warning("%s failed: %s", command, e)

    elif command == "update_agent":
        agent_id = args.get("agent_id", "")
        name = args.get("name")
        from app.db.repository import load_agent as _load_agent_db, save_agent as _save_agent_db
        from app.models.agent import Agent as _AgentModel
        if agent_manager.boss and agent_manager.boss.id == agent_id:
            target_agent = agent_manager.boss.agent
        elif agent_manager.boss and agent_id in agent_manager.boss.team:
            target_agent = agent_manager.boss.team[agent_id].agent
        else:
            target_agent = None
        if target_agent and name:
            target_agent.name = name
            asyncio.create_task(_save_agent_db(target_agent))
            await event_bus.publish("agent_updated", target_agent.model_dump())

    elif command == "remove_agent":
        agent_id = args.get("agent_id", "")
        if agent_manager.boss and agent_id in agent_manager.boss.team:
            agent_manager.boss.team.pop(agent_id, None)
            await event_bus.publish("agent_removed", {"agent_id": agent_id, "project_id": project_id})
        elif agent_manager.boss and agent_manager.boss.id == agent_id:
            await ws.send_text(json.dumps({"type": "error", "message": "Cannot remove the Coworker agent."}))
        else:
            await agent_manager.remove_agent(agent_id)
            await event_bus.publish("agent_removed", {"agent_id": agent_id, "project_id": project_id})

    elif command == "delete_channel":
        from app.db.repository import delete_channel as _delete_ch
        cid = args.get("id", "")
        if cid:
            deleted = await _delete_ch(project_id, cid)
            if deleted:
                await ws_manager.broadcast(project_id, {"type": "channel_deleted", "project_id": project_id, "ids": deleted})
                await ws.send_text(json.dumps({"type": "channel_deleted", "ids": deleted}))

    elif command == "mark_notification_read":
        from app.db.repository import mark_notification_read
        nid = args.get("notification_id", "")
        if nid and await mark_notification_read(project_id, nid):
            await ws_manager.broadcast(project_id, {"type": "notification_read", "notification_id": nid})

    elif command == "write_file":
        path = args.get("path", "")
        content = args.get("content", "")
        if path and content is not None:
            from app.workspace.manager import write_file as ws_write_file
            try:
                result = await ws_write_file(project_id, path, content)
                await ws.send_text(json.dumps({"type": "file_content", "path": path, "content": content}))
            except Exception as e:
                await ws.send_text(json.dumps({"type": "error", "message": f"write_file failed: {e}"}))

    elif command == "read_file":
        path = args.get("path", "")
        content = None
        try:
            from app.db.repository import get_file_content
            content = await get_file_content(project_id, path)
        except Exception as e:
            logger.warning("get_file_content failed: %s", e)
        if content is None:
            try:
                from app.workspace.manager import read_file as ws_read_file
                content = await ws_read_file(project_id, path)
            except Exception as e:
                content = f"[Error reading file: {e}]"
        await ws.send_text(json.dumps({"type": "file_content", "path": path, "content": content}))

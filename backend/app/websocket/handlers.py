import asyncio
import json
import logging
from datetime import datetime
from uuid import uuid4
from fastapi import WebSocket, WebSocketDisconnect
from app.websocket.manager import ws_manager
from app.core.event_bus import event_bus
from app.services.agent_manager import agent_manager
from app.db.repository import load_project_messages, load_project_agents, load_project, save_project, save_message
from app.models.message import Message

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
                        "mentions": [],
                        "attachments": [],
                        "metadata": {},
                        "timestamp": datetime.utcnow().isoformat() + "Z",
                    }
                    await event_bus.publish("message", msg)
                    asyncio.create_task(save_message(Message(**msg)))

                    if channel.startswith("dm-"):
                        agent_name = channel[3:]
                        found = False
                        if agent_manager.boss:
                            coworker_slug = agent_manager.boss.name.lower().replace(" ", "-")
                            if agent_name.lower() == coworker_slug:
                                await agent_manager.boss.handle_user_request(project_id, content, channel)
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
                        await agent_manager.boss.handle_user_request(project_id, content, channel)

                elif msg_type == "command":
                    cmd = data.get("command", "")
                    args = data.get("args", {})
                    await handle_command(project_id, cmd, args, websocket, user_id)

            except json.JSONDecodeError:
                await websocket.send_text(json.dumps({"type": "error", "message": "Invalid JSON"}))

    except WebSocketDisconnect:
        logger.info("WebSocket disconnected: project=%s", project_id)
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
            asyncio.create_task(save_project(project))
            boss = await agent_manager.create_coworker(project_id)
            await boss.initialize_project(project)
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
        worker = await agent_manager.create_worker(project_id, name, role_name)
        await ws.send_text(json.dumps({
            "type": "agent_added",
            "agent_id": worker.id,
            "name": worker.name,
            "role": role_name,
        }))

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
        await event_bus.publish("channel_created", ch.model_dump())

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

    elif command == "switch_project":
        new_project_id = args.get("project_id", "")
        if new_project_id:
            # Switch agent manager to new project
            await agent_manager.switch_project(new_project_id)
            # Load new project data
            messages = await load_project_messages(new_project_id, limit=200)
            agents = await load_project_agents(new_project_id)
            proj = await load_project(new_project_id)
            file_tree = await get_file_tree(new_project_id)
            
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
            await ws.send_text(json.dumps({
                "type": "project_switched",
                "project_id": new_project_id,
            }))
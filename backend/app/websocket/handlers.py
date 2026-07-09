import json
import logging
from datetime import datetime
from uuid import uuid4
from fastapi import WebSocket, WebSocketDisconnect
from app.websocket.manager import ws_manager
from app.core.event_bus import event_bus
from app.services.agent_manager import agent_manager
from app.db.repository import load_project_messages, load_project_agents, load_project

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
                        "reply_to": None,
                        "mentions": [],
                        "attachments": [],
                        "metadata": {},
                        "timestamp": datetime.utcnow().isoformat() + "Z",
                    }
                    await event_bus.publish("message", msg)

                    if channel.startswith("dm-"):
                        agent_name = channel[3:]
                        found = False
                        if agent_manager.boss and agent_name.lower() == agent_manager.boss.name.lower():
                            await agent_manager.boss.handle_user_request(project_id, content)
                            found = True
                        else:
                            for wid, worker in (agent_manager.boss.team.items() if agent_manager.boss else {}).items():
                                if agent_name.lower() == worker.name.lower().replace(" ", "-"):
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
                    elif agent_manager.boss and agent_manager.boss.agent.project_id == project_id:
                        await agent_manager.boss.handle_user_request(project_id, content, channel)

                elif msg_type == "command":
                    cmd = data.get("command", "")
                    args = data.get("args", {})
                    await handle_command(project_id, cmd, args, websocket)

            except json.JSONDecodeError:
                await websocket.send_text(json.dumps({"type": "error", "message": "Invalid JSON"}))

    except WebSocketDisconnect:
        logger.info("WebSocket disconnected: project=%s", project_id)
    finally:
        event_bus.unsubscribe("*", on_event)
        await ws_manager.disconnect(websocket, project_id)


async def handle_command(project_id: str, command: str, args: dict, ws: WebSocket):
    from app.models.project import Project
    from app.models.agent import AgentRole
    from app.workspace.manager import get_file_tree

    if command == "create_project":
        try:
            title = args.get("title", "Untitled Project")
            description = args.get("description", "")
            project = Project(title=title, description=description, id=project_id)
            boss = await agent_manager.create_boss(project_id)
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
        role_name = args.get("role", "backend_engineer")
        name = args.get("name", f"Agent-{len(agent_manager.workers) + 1}")
        try:
            role = AgentRole(role_name)
            worker = await agent_manager.create_worker(project_id, name, role)
            await ws.send_text(json.dumps({
                "type": "agent_added",
                "agent_id": worker.id,
                "name": worker.name,
                "role": role.value,
            }))
        except ValueError:
            await ws.send_text(json.dumps({"type": "error", "message": f"Invalid role: {role_name}"}))

    elif command == "status":
        agents = agent_manager.list_agents(project_id)
        await ws.send_text(json.dumps({
            "type": "status",
            "agents": agents,
        }))

    elif command == "load_project":
        # Load project history from DB
        messages = await load_project_messages(project_id, limit=200)
        agents = await load_project_agents(project_id)
        proj = await load_project(project_id)
        file_tree = await get_file_tree(project_id)
        
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
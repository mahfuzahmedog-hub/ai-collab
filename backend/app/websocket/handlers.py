import json
import logging
from fastapi import WebSocket, WebSocketDisconnect
from app.websocket.manager import ws_manager
from app.core.event_bus import event_bus
from app.services.agent_manager import agent_manager
from app.services.message_broker import message_broker

logger = logging.getLogger(__name__)


async def handle_websocket(websocket: WebSocket, project_id: str, user_id: str = "user"):
    await ws_manager.connect(websocket, project_id, user_id)

    async def on_event(data: dict):
        await ws_manager.broadcast(project_id, {
            "type": data.get("type", "event"),
            **data,
        })

    event_bus.subscribe("message", on_event)
    event_bus.subscribe("task_created", on_event)
    event_bus.subscribe("agent_created", on_event)
    event_bus.subscribe("review_requested", on_event)
    event_bus.subscribe("review_approved", on_event)
    event_bus.subscribe("review_rejected", on_event)

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
                    msg = {
                        "type": "message",
                        "project_id": project_id,
                        "sender_id": user_id,
                        "sender_name": sender,
                        "sender_role": "user",
                        "content": content,
                        "msg_type": "chat",
                    }
                    await event_bus.publish("message", msg)

                    if agent_manager.boss:
                        await agent_manager.boss.handle_user_request(project_id, content)

                elif msg_type == "command":
                    cmd = data.get("command", "")
                    args = data.get("args", {})
                    await handle_command(project_id, cmd, args, websocket)

            except json.JSONDecodeError:
                await websocket.send_text(json.dumps({"type": "error", "message": "Invalid JSON"}))

    except WebSocketDisconnect:
        logger.info("WebSocket disconnected: project=%s", project_id)
    finally:
        await ws_manager.disconnect(websocket, project_id)


async def handle_command(project_id: str, command: str, args: dict, ws: WebSocket):
    from app.models.project import Project
    from app.models.agent import AgentRole

    if command == "create_project":
        title = args.get("title", "Untitled Project")
        description = args.get("description", "")
        project = Project(title=title, description=description, id=project_id)
        boss = await agent_manager.create_boss(project_id)
        await boss.initialize_project(project)
        await ws.send_text(json.dumps({
            "type": "project_created",
            "project_id": project_id,
            "boss_name": boss.name,
        }))

    elif command == "delegate":
        task_title = args.get("task", "")
        role = args.get("role", "")
        if agent_manager.boss:
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

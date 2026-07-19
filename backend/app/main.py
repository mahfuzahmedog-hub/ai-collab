import os
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.api.routes import messages, projects, agents, tasks, health, settings as settings_routes
from app.api.platform import router as aios_router
from app.api.websocket import ws_router
from app.websocket.manager import ws_manager
from app.services.agent_manager import agent_manager
from app.tools.schema import register_all_schemas

logging.basicConfig(level=logging.INFO if not settings.debug else logging.DEBUG)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting AI Collaboration Platform...")
    os.makedirs("data", exist_ok=True)
    register_all_schemas()
    logger.info("Tool schemas registered")
    try:
        from app.memory.manager import memory_manager
        await memory_manager._ensure_db()
        logger.info("Memory manager initialized")
    except Exception as e:
        logger.warning("Memory manager init skipped: %s", e)

    try:
        from app.memory.manager import memory_manager
        existing = await memory_manager.get_skill_by_name("agent_creation_best_practices")
        if not existing:
            await memory_manager.save_skill({
                "name": "agent_creation_best_practices",
                "description": "Before creating an agent, check team for existing name to avoid duplicates. Use [ACTION] blocks to create agents.",
                "category": "workflow",
                "prompt_template": "AGENT CREATION RULES:\n1. When the user asks to create agents or build a team, ALWAYS emit [ACTION] blocks with the exact format below.\n2. One [ACTION] block per agent.\n3. Format: [ACTION]{\"type\":\"create_agent\",\"name\":\"...\",\"role\":\"...\",\"personality\":\"...\"}[/ACTION]\n4. Define clear, non-overlapping roles.\n5. NEVER just describe what you'll do — emit the actual [ACTION] blocks.\n6. Before creating, scan the current team for the agent name you're about to create (case-insensitive). If a match exists, DO NOT emit create_agent — skip it.\n7. Never create multiple agents with the same name.",
                "trigger_phrases": ["create agent", "make agent", "build team", "hire agent", "new agent", "create team"],
                "version": 2,
            })
            logger.info("Core skill 'agent_creation_best_practices' registered")
    except Exception as e:
        logger.warning("Core skill registration skipped: %s", e)

    try:
        from app.services.dedup import deduplicate_all_projects
        await deduplicate_all_projects()
    except Exception as e:
        logger.warning("Startup dedup skipped: %s", e)
    yield
    logger.info("Shutting down...")
    await agent_manager.stop_all()


app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(messages.router)
app.include_router(projects.router)
app.include_router(agents.router)
app.include_router(tasks.router)
app.include_router(health.router)
app.include_router(aios_router)
app.include_router(ws_router, prefix="/api/v1")
app.include_router(settings_routes.router)


@app.post("/api/upload")
async def upload_image(file: UploadFile = File(...)):
    import hashlib
    data = await file.read()
    ext = os.path.splitext(file.filename or "image.png")[1] or ".png"
    img_id = f"img_{hashlib.md5(data).hexdigest()[:12]}{ext}"
    path = os.path.join("data", "uploads")
    os.makedirs(path, exist_ok=True)
    with open(os.path.join(path, img_id), "wb") as f:
        f.write(data)
    return {"id": img_id, "name": file.filename or "image", "size": len(data)}

@app.get("/api/providers")
async def list_providers():
    from app.llm import llm_router
    return {"providers": llm_router.list_providers()}

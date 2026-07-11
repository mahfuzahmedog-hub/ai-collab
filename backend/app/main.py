import os
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.api.routes import messages, projects, agents, tasks, health
from app.websocket.manager import ws_manager
from app.services.agent_manager import agent_manager

logging.basicConfig(level=logging.INFO if not settings.debug else logging.DEBUG)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting AI Collaboration Platform...")
    os.makedirs("data", exist_ok=True)
    try:
        from app.db.session import init_db
        await init_db()
        logger.info("Database tables created")
    except Exception as e:
        logger.warning("Database init skipped: %s", e)
    try:
        from app.db.migrate import run_migration
        await run_migration()
    except Exception as e:
        logger.warning("Migration skipped: %s", e)
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


@app.get("/api/providers")
async def list_providers():
    from app.llm import llm_router
    return {"providers": llm_router.list_providers()}

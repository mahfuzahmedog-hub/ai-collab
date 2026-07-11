import asyncio
import logging

from sqlalchemy import inspect, text

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def run_migration():
    from app.db.session import engine, Base
    from app.db.models import (
        AgentModel, ProjectModel, TaskModel, MessageModel, FileModel,
        ChannelModel, ThreadModel, KnowledgeBaseModel,
        ExecutionLogModel, NotificationModel, ApprovalModel, MemoryModel,
        LifecycleAuditModel,
    )

    logger.info("Starting migration...")

    try:
        async with engine.begin() as conn:
            await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
            logger.info("pgvector extension ready")
    except Exception as e:
        logger.warning("pgvector extension not available (expected if not PostgreSQL): %s", e)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        logger.info("All tables created/verified")

    async with engine.begin() as conn:
        dialect = conn.dialect.name
        if dialect == "sqlite":
            await conn.run_sync(_add_sqlite_columns)
        else:
            await conn.run_sync(_add_postgres_columns)

    logger.info("Migration complete")


def _add_sqlite_columns(connection):
    inspector = inspect(connection)

    agent_cols = [c["name"] for c in inspector.get_columns("agents")]
    project_cols = [c["name"] for c in inspector.get_columns("projects")]

    missing_agent = [c for c in ["channel", "emoji", "color", "max_tokens", "display_name", "mission", "reporting_structure", "version", "is_permanent"] if c not in agent_cols]
    missing_project = [c for c in ["tags"] if c not in project_cols]

    for col in missing_agent:
        try:
            connection.execute(text(f"ALTER TABLE agents ADD COLUMN {col} TEXT DEFAULT ''"))
            logger.info("Added column agents.%s", col)
        except Exception as e:
            logger.warning("Could not add agents.%s: %s", col, e)
    for col in missing_project:
        try:
            connection.execute(text(f"ALTER TABLE projects ADD COLUMN {col} TEXT DEFAULT '[]'"))
            logger.info("Added column projects.%s", col)
        except Exception as e:
            logger.warning("Could not add projects.%s: %s", col, e)


def _add_postgres_columns(connection):
    inspector = inspect(connection)

    agent_cols = [c["name"] for c in inspector.get_columns("agents")]
    project_cols = [c["name"] for c in inspector.get_columns("projects")]

    if "channel" not in agent_cols:
        connection.execute(text("ALTER TABLE agents ADD COLUMN channel VARCHAR(255) DEFAULT 'general'"))
    if "emoji" not in agent_cols:
        connection.execute(text("ALTER TABLE agents ADD COLUMN emoji VARCHAR(50) DEFAULT ''"))
    if "color" not in agent_cols:
        connection.execute(text("ALTER TABLE agents ADD COLUMN color VARCHAR(50) DEFAULT ''"))
    if "max_tokens" not in agent_cols:
        connection.execute(text("ALTER TABLE agents ADD COLUMN max_tokens INTEGER DEFAULT 4096"))
    if "display_name" not in agent_cols:
        connection.execute(text("ALTER TABLE agents ADD COLUMN display_name VARCHAR(255)"))
    if "mission" not in agent_cols:
        connection.execute(text("ALTER TABLE agents ADD COLUMN mission VARCHAR(1000)"))
    if "reporting_structure" not in agent_cols:
        connection.execute(text("ALTER TABLE agents ADD COLUMN reporting_structure VARCHAR(500)"))
    if "version" not in agent_cols:
        connection.execute(text("ALTER TABLE agents ADD COLUMN version VARCHAR(50) DEFAULT '1.0'"))
    if "is_permanent" not in agent_cols:
        connection.execute(text("ALTER TABLE agents ADD COLUMN is_permanent BOOLEAN DEFAULT false"))
    if "tags" not in project_cols:
        connection.execute(text("ALTER TABLE projects ADD COLUMN tags JSON DEFAULT '[]'::json"))


if __name__ == "__main__":
    asyncio.run(run_migration())

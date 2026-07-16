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

    async with engine.begin() as conn:
        await conn.run_sync(_ensure_registry_columns_and_index)

    logger.info("Migration complete")


def _ensure_registry_columns_and_index(connection):
    inspector = inspect(connection)
    agent_cols = [c["name"] for c in inspector.get_columns("agents")]

    if "normalized_name" not in agent_cols:
        connection.execute(text("ALTER TABLE agents ADD COLUMN normalized_name VARCHAR(255) DEFAULT ''"))
        connection.execute(text("UPDATE agents SET normalized_name = LOWER(TRIM(name)) WHERE normalized_name IS NULL OR normalized_name = ''"))
        logger.info("Added column agents.normalized_name and backfilled")
    if "specialization" not in agent_cols:
        connection.execute(text("ALTER TABLE agents ADD COLUMN specialization VARCHAR(255) DEFAULT ''"))
        logger.info("Added column agents.specialization")

    # Create unique index (skip if already exists — SQLite handles this gracefully)
    try:
        connection.execute(text("CREATE UNIQUE INDEX IF NOT EXISTS uix_agent_project_name ON agents(project_id, normalized_name)"))
        logger.info("Created unique index uix_agent_project_name")
    except Exception as e:
        logger.warning("Could not create unique index (may already exist): %s", e)


def _add_sqlite_columns(connection):
    inspector = inspect(connection)

    agent_cols = [c["name"] for c in inspector.get_columns("agents")]
    project_cols = [c["name"] for c in inspector.get_columns("projects")]

    missing_agent = [c for c in ["channel", "emoji", "color", "max_tokens", "display_name", "mission", "reporting_structure", "version", "is_permanent"] if c not in agent_cols]
    missing_project = [c for c in ["tags"] if c not in project_cols]

    message_cols = [c["name"] for c in inspector.get_columns("messages")]
    missing_message = [c for c in ["thread_id"] if c not in message_cols]

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
    for col in missing_message:
        try:
            connection.execute(text(f"ALTER TABLE messages ADD COLUMN {col} TEXT"))
            logger.info("Added column messages.%s", col)
        except Exception as e:
            logger.warning("Could not add messages.%s: %s", col, e)


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

    message_cols = [c["name"] for c in inspector.get_columns("messages")]
    if "thread_id" not in message_cols:
        connection.execute(text("ALTER TABLE messages ADD COLUMN thread_id VARCHAR"))


if __name__ == "__main__":
    asyncio.run(run_migration())

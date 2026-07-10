import asyncio
from app.db.session import engine, init_db, async_session
from app.db.models import AgentModel, ProjectModel, MessageModel, FileModel
from sqlalchemy import select, text

async def check():
    await init_db()
    print("Tables initialized")
    async with engine.connect() as conn:
        result = await conn.execute(text("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'"))
        tables = [row[0] for row in result.fetchall()]
        print(f"Tables: {tables}")
    async with async_session() as s:
        agents = (await s.execute(select(AgentModel))).scalars().all()
        print(f"Agents: {len(agents)}")
        projects = (await s.execute(select(ProjectModel))).scalars().all()
        print(f"Projects: {len(projects)}")
        messages = (await s.execute(select(MessageModel))).scalars().all()
        print(f"Messages: {len(messages)}")
        files = (await s.execute(select(FileModel))).scalars().all()
        print(f"Files: {len(files)}")

asyncio.run(check())

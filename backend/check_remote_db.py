import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy import select, text
from app.db.models import AgentModel, ProjectModel, MessageModel, FileModel, Base

DATABASE_URL = "postgresql+asyncpg://ai_collab_db_user:jv5VG4QqLJ3IwU1OQmOHuUPxZDdYMZ04@dpg-d984jkd8nd3s73bn4ml0-a/ai_collab_db"

engine = create_async_engine(DATABASE_URL, echo=False)
async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

async def check():
    async with engine.begin() as conn:
        result = await conn.execute(text("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'"))
        tables = [row[0] for row in result.fetchall()]
        print(f"Tables: {tables}")

    async with async_session() as s:
        agents = (await s.execute(select(AgentModel))).scalars().all()
        print(f"Agents: {len(agents)}")
        for a in agents[:5]:
            print(f"  - {a.name} ({a.role}) project={a.project_id}")
        
        projects = (await s.execute(select(ProjectModel))).scalars().all()
        print(f"Projects: {len(projects)}")
        for p in projects[:5]:
            print(f"  - {p.title} id={p.id}")
        
        messages = (await s.execute(select(MessageModel))).scalars().all()
        print(f"Messages: {len(messages)}")

        files = (await s.execute(select(FileModel))).scalars().all()
        print(f"Files: {len(files)}")

asyncio.run(check())

from fastapi import FastAPI
from contextlib import asynccontextmanager

from app.core.database import engine
from app.api.projects import router as projects_router
from app.api.places import router as places_router
from app.models import Base


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Create tables on startup (fine for SQLite/dev; use Alembic for real migrations)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield


app = FastAPI(
    title="Travel Planner API",
    description="CRUD API for managing travel projects and places",
    version="0.1.0",
    lifespan=lifespan
)

app.include_router(projects_router)
app.include_router(places_router)
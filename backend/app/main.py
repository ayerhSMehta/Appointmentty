from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from contextlib import asynccontextmanager
from sqlalchemy import text
import os
from .database import engine
from . import models
from .routers import admin, appointments, auth
from .scheduler import start_scheduler

STATIC_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "static")


def _migrate(eng):
    """Add new columns to existing DB without losing data."""
    new_cols = [
        ("default_working_hours", "start_time_2", "VARCHAR"),
        ("default_working_hours", "end_time_2", "VARCHAR"),
        ("date_overrides", "start_time_2", "VARCHAR"),
        ("date_overrides", "end_time_2", "VARCHAR"),
    ]
    with eng.connect() as conn:
        for table, col, col_type in new_cols:
            try:
                conn.execute(text(f"ALTER TABLE {table} ADD COLUMN {col} {col_type}"))
                conn.commit()
            except Exception:
                pass  # column already exists


@asynccontextmanager
async def lifespan(app: FastAPI):
    models.Base.metadata.create_all(bind=engine)
    _migrate(engine)
    scheduler = start_scheduler()
    yield
    scheduler.shutdown()


app = FastAPI(title="Appointment Manager", lifespan=lifespan)

import os
_extra_origins = [o.strip() for o in os.getenv("ALLOWED_ORIGINS", "").split(",") if o.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:3000",
        "http://localhost:8080",
        "null",          # file:// origin when opening index.html directly
        *_extra_origins,
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(admin.router)
app.include_router(appointments.router)


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/")
def serve_frontend():
    return FileResponse(os.path.join(STATIC_DIR, "index.html"))

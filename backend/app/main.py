from __future__ import annotations

import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.auth import router as auth_router
from app.api.me import router as me_router
from app.api.routes import router
from app.config import get_settings
from app.db import init_db
from app.scheduler import start_scheduler

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")

app = FastAPI(title="TrueNews API", version="0.1.0")

_settings = get_settings()
app.add_middleware(
    CORSMiddleware,
    allow_origins=[_settings.frontend_origin],
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
    allow_credentials=True,
)

app.include_router(router)
app.include_router(auth_router)
app.include_router(me_router)


@app.on_event("startup")
def _startup() -> None:
    try:
        init_db()
    except Exception:
        # Keep /health responsive so the failure is visible rather than a boot crash.
        logging.getLogger("truenews").exception("init_db failed at startup")
    start_scheduler()


@app.get("/health")
def health() -> dict:
    return {"ok": True}

"""SANAD API — FastAPI analysis environment. All routes under /api/v1."""
from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.errors import SanadError, sanad_error_handler
from app.routers import health

API_PREFIX = "/api/v1"

app = FastAPI(title="SANAD API", version="1.0.0", docs_url=f"{API_PREFIX}/docs")

# Local dev only; on-prem restricts origins at the reverse proxy.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_exception_handler(SanadError, sanad_error_handler)

app.include_router(health.router, prefix=API_PREFIX, tags=["health"])

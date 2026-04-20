# main.py
# ─────────────────────────────────────────────────────────────
# MediChain Lite — FastAPI Application Entry Point
# Run with:  uvicorn main:app --reload
# Docs at:   http://127.0.0.1:8000/docs
# ─────────────────────────────────────────────────────────────

from fastapi import FastAPI
from app.utils.database import init_db
from app.routers.api import router

app = FastAPI(
    title       = "MediChain Lite API",
    description = "Role-based encrypted QR codes for offline patient records.",
    version     = "1.0.0",
)

# Create DB tables on startup
@app.on_event("startup")
def on_startup():
    init_db()

app.include_router(router, prefix="/api/v1")
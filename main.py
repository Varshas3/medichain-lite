from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.utils.database import init_db

from app.routers import patients, providers, qr, drugs, audit, consent, utils

app = FastAPI(
    title="MediChain Lite API",
    description="Role-based encrypted QR codes for offline patient records.",
    version="1.0.0",
)

# Allow frontend on localhost to call the API without CORS errors
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],          # for demo — tighten in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def on_startup():
    init_db()
    # Auto-seed on startup so the demo just works
    try:
        from scripts.seed_db import seed
        seed()
    except Exception as e:
        print(f"[STARTUP] Seed skipped: {e}")

app.include_router(patients.router, prefix="/api/v1")
app.include_router(providers.router, prefix="/api/v1")
app.include_router(qr.router, prefix="/api/v1")
app.include_router(drugs.router, prefix="/api/v1")
app.include_router(audit.router, prefix="/api/v1")
app.include_router(consent.router, prefix="/api/v1")
app.include_router(utils.router, prefix="/api/v1")
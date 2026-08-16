"""
main.py — FastAPI application entry point.
Configures CORS, mounts all routers, initializes DB on startup.
"""
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from src.config import get_settings
from src.database import init_db
from src.routers import auth, nodes, optimize, results
from src.seed.seed_data import seed

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown lifecycle handler."""
    logger.info("🚀 BioChain-Opt backend starting...")
    init_db()
    seed()
    logger.info("✅ Database initialized and seeded.")
    yield
    logger.info("👋 BioChain-Opt backend shutting down.")


app = FastAPI(
    title="BioChain-Opt API",
    description=(
        "Decision Support System untuk optimasi rantai pasok bioetanol 2G "
        "dari tongkol jagung di Jawa Timur menggunakan MILP Hub-and-Spoke."
    ),
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# ─── CORS ───────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── Routers ─────────────────────────────────────────────────────────────────
app.include_router(auth.router)
app.include_router(nodes.router)
app.include_router(optimize.router)
app.include_router(results.router)


@app.get("/health")
def health_check():
    """Health check endpoint for Docker healthcheck and monitoring."""
    return JSONResponse({"status": "ok", "service": "biochain-opt-backend"})


@app.get("/")
def root():
    return {"message": "BioChain-Opt API v1.0 — Rantai Pasok Bioetanol Jawa Timur"}

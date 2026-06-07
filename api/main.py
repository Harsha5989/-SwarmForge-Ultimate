"""SwarmForge Ultimate — FastAPI Application Entry Point."""

import time
from contextlib import asynccontextmanager

import structlog
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from prometheus_client import Counter, Histogram, generate_latest

from config import get_settings
from database import init_db, close_db
from redis_client import get_redis, close_redis, RedisClient
from routes.sessions import router as sessions_router
from routes.blackboard import router as blackboard_router
from routes.ws import router as ws_router

# ── Structured Logging ─────────────────────────────────────────
structlog.configure(
    processors=[
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.dev.ConsoleRenderer(),
    ],
    wrapper_class=structlog.make_filtering_bound_logger(20),
)

log = structlog.get_logger()

# ── Prometheus Metrics ─────────────────────────────────────────
REQUEST_COUNT = Counter(
    "swarmforge_requests_total",
    "Total API requests",
    ["method", "path", "status"],
)
REQUEST_LATENCY = Histogram(
    "swarmforge_request_duration_seconds",
    "Request latency in seconds",
    ["method", "path"],
)


# ── App Lifecycle ──────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events."""
    log.info("starting_swarmforge", env=get_settings().app_env)
    await init_db()
    await get_redis()
    log.info("swarmforge_ready")
    yield
    log.info("shutting_down_swarmforge")
    await close_redis()
    await close_db()


# ── App Creation ───────────────────────────────────────────────
app = FastAPI(
    title="SwarmForge Ultimate",
    description="Autonomous AI Software Factory — 100% Open Source",
    version="1.0.0",
    lifespan=lifespan,
)

# ── CORS ───────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Metrics Middleware ─────────────────────────────────────────
@app.middleware("http")
async def metrics_middleware(request: Request, call_next):
    start = time.time()
    response = await call_next(request)
    duration = time.time() - start
    path = request.url.path
    REQUEST_COUNT.labels(
        method=request.method, path=path, status=response.status_code
    ).inc()
    REQUEST_LATENCY.labels(method=request.method, path=path).observe(duration)
    return response


# ── Routes ─────────────────────────────────────────────────────
app.include_router(sessions_router, prefix="/api/v1")
app.include_router(blackboard_router, prefix="/api/v1")
app.include_router(ws_router)


# ── Health Check ───────────────────────────────────────────────
@app.get("/api/v1/health")
async def health_check():
    """Check connectivity to Postgres, Redis, and LiteLLM."""
    import httpx
    settings = get_settings()
    services = {}

    # Check Redis
    try:
        redis = await get_redis()
        await redis.ping()
        services["redis"] = "ok"
    except Exception as e:
        services["redis"] = f"error: {str(e)[:50]}"

    # Check Postgres
    try:
        from database import engine
        async with engine.connect() as conn:
            await conn.execute(
                __import__("sqlalchemy").text("SELECT 1")
            )
        services["postgres"] = "ok"
    except Exception as e:
        services["postgres"] = f"error: {str(e)[:50]}"

    # Check LiteLLM
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"{settings.litellm_base_url}/health",
                timeout=5.0,
            )
            services["litellm"] = "ok" if resp.status_code == 200 else f"status: {resp.status_code}"
    except Exception as e:
        services["litellm"] = f"error: {str(e)[:50]}"

    all_ok = all(v == "ok" for v in services.values())
    return {
        "status": "healthy" if all_ok else "degraded",
        "services": services,
    }


# ── Prometheus Metrics Endpoint ────────────────────────────────
@app.get("/metrics")
async def metrics():
    from fastapi.responses import PlainTextResponse
    return PlainTextResponse(generate_latest().decode("utf-8"))

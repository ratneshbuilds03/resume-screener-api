import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from app.config import settings
from app.database import Base, engine, ensure_analysis_schema
from app.limiter import limiter
from app.mongodb import close_mongodb, connect_mongodb
from app.routes.analysis_routes import router as analysis_routes
from app.routes.analytics_routes import router as analytics_router
from app.routes.auth_routes import router as auth_routes

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        await connect_mongodb()
        from app.mongodb import get_mongodb

        mongo = get_mongodb()
        if mongo is not None:
            await mongo.analyses.create_index([("user_id", 1)])
            await mongo.analyses.create_index([("analysis_id", 1)])
            await mongo.analyses.create_index([("created_at", -1)])
            await mongo.analyses.create_index([("user_id", 1), ("created_at", -1)])
    except Exception as exc:
        logger.warning("MongoDB startup check failed: %s", exc)

    Base.metadata.create_all(bind=engine)
    ensure_analysis_schema()
    yield
    await close_mongodb()


app = FastAPI(
    title="AI Resume Screener API",
    description="Intelligent resume screening powered by AI",
    version="1.0.0",
    lifespan=lifespan,
)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
)

app.include_router(auth_routes)
app.include_router(analysis_routes)
app.include_router(analytics_router)


@app.get("/health")
async def health_check():
    from app.mongodb import get_mongodb
    from app.redis_client import get_redis

    health = {
        "status": "ok",
        "service": "resume-screener-api",
        "version": "1.0.0",
    }

    try:
        mongo = get_mongodb()
        if mongo is not None:
            await mongo.command("ping")
            health["mongodb"] = "connected"
        else:
            health["mongodb"] = "not initialized"
    except Exception:
        health["mongodb"] = "disconnected"
        health["status"] = "degraded"

    try:
        redis = get_redis()
        if redis is not None:
            redis.ping()
            health["redis"] = "connected"
        else:
            health["redis"] = "not initialized"
    except Exception:
        health["redis"] = "disconnected"
        health["status"] = "degraded"

    return health


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    logger.exception("Unexpected error: %s", exc)
    return JSONResponse(
        status_code=500,
        content={"detail": "An unexpected error occurred"},
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    errors = []
    for error in exc.errors():
        errors.append({
            "field": error["loc"][-1] if error["loc"] else "unknown",
            "message": error["msg"],
        })
    return JSONResponse(
        status_code=422,
        content={"detail": "Validation failed", "errors": errors},
    )


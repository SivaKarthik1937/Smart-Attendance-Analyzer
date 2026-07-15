"""
app.py
======
FastAPI application entrypoint for the Smart Attendance Pattern Analyzer.

Responsibilities:
    - Create the FastAPI app with OpenAPI/Swagger metadata.
    - Configure CORS for the React frontend.
    - Initialize and (if empty) seed the SQLite database on startup.
    - Mount every route module under routes/.
    - Provide root and health-check endpoints.

Run with:
    uvicorn app:app --reload --host 0.0.0.0 --port 8000
"""

from __future__ import annotations

import os
from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError

from database import init_db, seed_database

load_dotenv()


# --------------------------------------------------------------------------
# Lifespan: database initialization on startup
# --------------------------------------------------------------------------

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("=" * 70)
    print("Smart Attendance Pattern Analyzer API — starting up")
    print("=" * 70)

    print("Initializing database schema...")
    init_db()

    try:
        seed_database()  # no-op if already seeded
    except FileNotFoundError as exc:
        print(f"[startup] WARNING: {exc}")
        print("[startup] The API will start, but dashboards will show no data "
              "until the dataset is generated and the DB is seeded.")

    print("Startup complete. Visit /docs for the interactive API documentation.")
    yield
    print("Shutting down Smart Attendance Pattern Analyzer API.")


# --------------------------------------------------------------------------
# App instance
# --------------------------------------------------------------------------

app = FastAPI(
    title="Smart Attendance Pattern Analyzer API",
    description=(
        "AI-powered attendance analytics platform: risk classification, "
        "attendance forecasting, student segmentation, and rich dashboards "
        "for students and faculty."
    ),
    version="1.0.0",
    contact={"name": "Smart Attendance Pattern Analyzer"},
    lifespan=lifespan,
)


# --------------------------------------------------------------------------
# CORS
# --------------------------------------------------------------------------

_default_origins = (
    "http://localhost:5173,"
    "http://127.0.0.1:5173,"
    "http://localhost:3000,"
    "https://smart-attendance-analyzer.vercel.app,"
    "https://smart-attendance-analyzer-koifw7fap.vercel.app"
)
allowed_origins = os.getenv("CORS_ORIGINS", _default_origins).split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=r"https://.*\.vercel\.app",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)



# --------------------------------------------------------------------------
# Global exception handlers (consistent error response shape)
# --------------------------------------------------------------------------

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    """Return a clean, frontend-friendly shape for Pydantic validation errors."""
    first_error = exc.errors()[0] if exc.errors() else {}
    field = ".".join(str(loc) for loc in first_error.get("loc", []) if loc != "body")
    message = first_error.get("msg", "Invalid request")
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": f"{field}: {message}" if field else message},
    )


# --------------------------------------------------------------------------
# Routers
# --------------------------------------------------------------------------

from routes import auth_routes, student_routes, faculty_routes, prediction_routes, analytics_routes, export_routes  # noqa: E402

app.include_router(auth_routes.router)
app.include_router(student_routes.router)
app.include_router(faculty_routes.router)
app.include_router(prediction_routes.router)
app.include_router(analytics_routes.router)
app.include_router(export_routes.router)


# --------------------------------------------------------------------------
# Root / health endpoints
# --------------------------------------------------------------------------

@app.get("/", tags=["Health"])
def root() -> dict:
    """Basic liveness/info endpoint."""
    return {
        "service": "Smart Attendance Pattern Analyzer API",
        "status": "running",
        "docs": "/docs",
        "redoc": "/redoc",
    }


@app.get("/health", tags=["Health"])
def health_check() -> dict:
    """Health-check endpoint for uptime monitoring / container orchestration."""
    return {"status": "ok"}

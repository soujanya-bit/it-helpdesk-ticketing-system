
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.endpoints.auth import router as auth_router
from app.api.v1.endpoints.tickets import router as tickets_router
from app.core.config import settings


# Create the FastAPI application.
app = FastAPI(
    title=settings.app_name,
    description="IT Helpdesk Ticketing System API",
    version="1.0.0",
    debug=settings.debug,
)


# Configure Cross-Origin Resource Sharing.
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Register authentication endpoints.
app.include_router(
    auth_router,
    prefix=f"{settings.api_v1_prefix}/auth",
    tags=["Authentication"],
)


# Register ticket management endpoints.
app.include_router(
    tickets_router,
    prefix=f"{settings.api_v1_prefix}/tickets",
    tags=["Tickets"],
)


# Application health check.
@app.get("/health", tags=["Health"])
def health_check():
    return {
        "status": "healthy",
        "application": settings.app_name,
    }

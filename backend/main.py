"""Main entry point for FlakeGuard backend."""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.config import settings
from backend.api.routes import (
    detection,
    classification,
    remediation,
    audit,
    metrics
)

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="AI-powered flaky test detection, classification, and remediation"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(detection.router, prefix="/api/detection", tags=["detection"])
app.include_router(classification.router, prefix="/api/classification", tags=["classification"])
app.include_router(remediation.router, prefix="/api/remediation", tags=["remediation"])
app.include_router(audit.router, prefix="/api/audit", tags=["audit"])
app.include_router(metrics.router, prefix="/api/metrics", tags=["metrics"])


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "name": settings.app_name,
        "version": settings.app_version,
        "status": "running"
    }


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "backend.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug
    )

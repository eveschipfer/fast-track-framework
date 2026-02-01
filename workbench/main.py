"""
Workbench Application Entry Point

This is the main entry point for the Fast Track Framework workbench application.
The workbench is a sample application that demonstrates how to use the framework.

Usage:
    uvicorn workbench.main:app --reload
"""

from ftf.http import FastTrackFramework
from ftf.core import Container

# Import app models (registers them with SQLAlchemy)
from app.models import User, Post, Comment, Role  # noqa: F401

# Create application instance
app = FastTrackFramework()

# Get container instance
container = Container()


@app.get("/")
async def root():
    """Welcome endpoint."""
    return {
        "message": "Fast Track Framework - Workbench Application",
        "version": "5.0.0",
        "framework": "ftf",
        "description": "A Laravel-inspired micro-framework built on FastAPI"
    }


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "healthy"}


# Import routes (if you have them)
# from app.http.routes import register_routes
# register_routes(app)

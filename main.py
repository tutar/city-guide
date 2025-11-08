#!/usr/bin/env python3
"""
Main application entry point for City Guide Smart Assistant
"""

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api.conversation import router as conversation_router
from src.api.health import router as health_router

# Create FastAPI application
app = FastAPI(
    title="City Guide Smart Assistant",
    description="AI-powered conversational interface for Shenzhen government services",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, restrict to specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(conversation_router)
app.include_router(health_router)


@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "message": "City Guide Smart Assistant API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health",
    }


if __name__ == "__main__":
    """Run the application"""
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info",
    )

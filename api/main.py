"""FastAPI application with SSE support."""
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, JSONResponse
from contextlib import asynccontextmanager
import asyncio
import json
import uuid
from typing import Dict, Any, Optional
from datetime import datetime

from config.settings import settings
from api.routes import debug, webhooks, health
from src.utils.logger import get_logger

logger = get_logger(__name__)

# SSE connection manager
class SSEManager:
    """Manage Server-Sent Events connections."""
    
    def __init__(self):
        self.active_connections: Dict[str, asyncio.Queue] = {}
    
    async def connect(self, session_id: str) -> asyncio.Queue:
        """Create new SSE connection."""
        queue = asyncio.Queue()
        self.active_connections[session_id] = queue
        logger.info(f"SSE connection established: {session_id}")
        return queue
    
    async def disconnect(self, session_id: str):
        """Close SSE connection."""
        if session_id in self.active_connections:
            del self.active_connections[session_id]
            logger.info(f"SSE connection closed: {session_id}")
    
    async def send_event(
        self,
        session_id: str,
        event_type: str,
        data: Any
    ):
        """Send event to specific session."""
        if session_id in self.active_connections:
            queue = self.active_connections[session_id]
            await queue.put({
                "event": event_type,
                "data": data,
                "timestamp": datetime.utcnow().isoformat()
            })
    
    async def broadcast(self, event_type: str, data: Any):
        """Broadcast event to all connections."""
        for session_id in self.active_connections:
            await self.send_event(session_id, event_type, data)

# Global SSE manager
sse_manager = SSEManager()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan."""
    # Startup
    logger.info(" Mytheos API starting...")
    logger.info(f"Environment: {settings.DEBUG and 'Development' or 'Production'}")
    logger.info(f"LLM Provider: {settings.LLM_PROVIDER}")
    
    # Create directories
    settings.OUTPUT_DIR.mkdir(exist_ok=True)
    settings.TEMP_DIR.mkdir(exist_ok=True)
    
    yield
    
    # Shutdown
    logger.info(" Mytheos API shutting down...")

# Create FastAPI app
app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="AI-Powered Multi-Agent Debugging System",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(health.router, prefix="/api", tags=["health"])
app.include_router(debug.router, prefix="/api/debug", tags=["debug"])
app.include_router(webhooks.router, prefix="/api/webhooks", tags=["webhooks"])

@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "service": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "status": "running",
        "docs": "/docs",
        "health": "/api/health"
    }

@app.get("/api/sse/{session_id}")
async def sse_endpoint(session_id: str):
    """
    Server-Sent Events endpoint for real-time updates.
    
    Frontend connects here to receive debugging progress updates.
    """
    
    async def event_generator():
        queue = await sse_manager.connect(session_id)
        
        try:
            # Send initial connection message
            yield f"data: {json.dumps({'event': 'connected', 'session_id': session_id})}\n\n"
            
            while True:
                # Wait for events
                event = await queue.get()
                
                # Send event to client
                yield f"event: {event['event']}\n"
                yield f"data: {json.dumps(event['data'])}\n\n"
                
                # Check for completion
                if event['event'] == 'complete':
                    break
        except asyncio.CancelledError:
            logger.info(f"SSE connection cancelled: {session_id}")
        finally:
            await sse_manager.disconnect(session_id)
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )

# Export SSE manager for use in routes
app.state.sse_manager = sse_manager

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "api.main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=settings.DEBUG,
        workers=settings.API_WORKERS
    )
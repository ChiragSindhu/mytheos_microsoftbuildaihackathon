"""FastAPI application with SSE support."""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from contextlib import asynccontextmanager
import asyncio
import json
from typing import Dict, Any
from datetime import datetime

from config.settings import settings
from api.routes import debug, webhooks, health
from src.utils.logger import get_logger

logger = get_logger(__name__)


class SSEManager:
    """
    Manage Server-Sent Events connections.

    Each session has:
      - a Queue that receives events from background tasks
      - a ready Event that is set once the SSE client has connected

    The background task waits on `ready` before emitting anything,
    so events are never lost to a queue that has no reader yet.
    """

    def __init__(self):
        self._queues: Dict[str, asyncio.Queue] = {}
        self._ready:  Dict[str, asyncio.Event] = {}

    # ------------------------------------------------------------------
    # Session lifecycle
    # ------------------------------------------------------------------

    def register(self, session_id: str) -> None:
        """
        Called by the POST /debug route when a session is created.
        Sets up the queue and ready-event before the background task starts,
        so send_event() can safely await ready without KeyError.
        """
        self._queues[session_id] = asyncio.Queue()
        self._ready[session_id]  = asyncio.Event()
        logger.info("SSE session registered: %s", session_id)

    async def connect(self, session_id: str) -> asyncio.Queue:
        """
        Called when the SSE client opens /api/sse/{session_id}.
        Signals the background task that it may start emitting.
        """
        if session_id not in self._queues:
            raise KeyError(f"Unknown session: {session_id}")

        self._ready[session_id].set()
        logger.info("SSE client connected, task unblocked: %s", session_id)
        return self._queues[session_id]

    async def disconnect(self, session_id: str) -> None:
        """Clean up after the SSE stream closes."""
        self._queues.pop(session_id, None)
        self._ready.pop(session_id, None)
        logger.info("SSE connection closed: %s", session_id)

    # ------------------------------------------------------------------
    # Sending events (called by ProgressEmitter subscribers)
    # ------------------------------------------------------------------

    async def send_event(
        self,
        session_id: str,
        event_type: str,
        data: Any,
        *,
        ready_timeout: float = 30.0,
    ) -> None:
        """
        Enqueue an event for a session.

        Blocks until the SSE client has connected (up to `ready_timeout`
        seconds), then puts the event on the queue. This guarantees no
        event is dropped even if the background task is fast.
        """
        if session_id not in self._ready:
            logger.warning("send_event: unknown session %s — dropping event", session_id)
            return

        ready = self._ready[session_id]
        if not ready.is_set():
            logger.debug("send_event: waiting for SSE client on session %s", session_id)
            try:
                await asyncio.wait_for(ready.wait(), timeout=ready_timeout)
            except asyncio.TimeoutError:
                logger.error(
                    "send_event: SSE client never connected for session %s "
                    "(timeout %.1fs) — dropping event",
                    session_id, ready_timeout,
                )
                return

        queue = self._queues.get(session_id)
        if queue is None:
            logger.warning("send_event: queue gone for session %s — dropping event", session_id)
            return

        await queue.put({
            "event": event_type,
            "data": data,
            "timestamp": datetime.utcnow().isoformat(),
        })

    async def broadcast(self, event_type: str, data: Any) -> None:
        """Broadcast an event to every active session."""
        for session_id in list(self._queues):
            await self.send_event(session_id, event_type, data)


# Global SSE manager — created before the app so routes can import it
sse_manager = SSEManager()


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Mytheos API starting...")
    logger.info("Environment: %s", "Development" if settings.DEBUG else "Production")
    logger.info("LLM Provider: %s", settings.LLM_PROVIDER)

    settings.OUTPUT_DIR.mkdir(exist_ok=True)
    settings.TEMP_DIR.mkdir(exist_ok=True)

    yield

    logger.info("Mytheos API shutting down...")


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="AI-Powered Multi-Agent Debugging System",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router,    prefix="/api",          tags=["health"])
app.include_router(debug.router,     prefix="/api/debug",    tags=["debug"])
app.include_router(webhooks.router,  prefix="/api/webhooks", tags=["webhooks"])

# Make the manager available to route handlers via request.app.state
app.state.sse_manager = sse_manager


@app.get("/")
async def root():
    return {
        "service": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "status": "running",
        "docs": "/docs",
        "health": "/api/health",
    }


@app.get("/api/sse/{session_id}")
async def sse_endpoint(session_id: str):
    """
    Server-Sent Events stream for a debug session.

    The client must open this endpoint after POST /api/debug/start (or /file).
    Opening it unblocks the background task so agents start running only once
    there is a listener — no events are ever dropped.
    """

    async def event_generator():
        try:
            queue = await sse_manager.connect(session_id)
        except KeyError:
            # Session doesn't exist — send an error event and close
            yield f"event: error\ndata: {json.dumps({'message': f'Unknown session: {session_id}'})}\n\n"
            return

        # Confirm the stream is open
        yield f"event: connected\ndata: {json.dumps({'session_id': session_id})}\n\n"

        try:
            while True:
                event = await queue.get()

                yield f"event: {event['event']}\n"
                yield f"data: {json.dumps(event['data'])}\n\n"

                # Terminal events close the stream
                if event["event"] in ("complete", "error"):
                    break

        except asyncio.CancelledError:
            logger.info("SSE stream cancelled by client: %s", session_id)
        finally:
            await sse_manager.disconnect(session_id)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "api.main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=settings.DEBUG,
        workers=settings.API_WORKERS,
    )
    
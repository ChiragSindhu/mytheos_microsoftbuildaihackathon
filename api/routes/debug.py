"""Debug API endpoints.

The POST routes register the session with SSEManager (creating the queue +
ready-event) and start the background task immediately.  The background task
blocks inside send_event() until the client opens /api/sse/{session_id},
at which point SSEManager.connect() sets the ready-event and events flow.

Flow per request
----------------
  Client                          Server
  ──────                          ──────
  POST /api/debug/file   ──────►  register(session_id)   ← queue + Event created
                         ◄──────  {session_id, sse_url}
                                  background task starts, blocks on ready-event
  GET  /api/sse/{id}     ──────►  connect(session_id)    ← Event.set()
                         ◄──────  event: connected
                                  task unblocked → agents run → events stream
                         ◄──────  event: progress  (phase started)
                         ◄──────  event: progress  (phase done + payload)
                         ◄──────  ...
                         ◄──────  event: complete
"""
from __future__ import annotations

import tempfile
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, BackgroundTasks, HTTPException, Request
from pydantic import BaseModel, Field

from src.core.local_file_debugger import LocalFileDebugger
from src.core.orchestrator import MYTHEOSOrchestrator
from src.core.progress_emitter import ProgressEmitter
from src.utils.logger import get_logger

logger = get_logger(__name__)
router = APIRouter()


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------

class DebugRequest(BaseModel):
    repo_url: Optional[str] = None
    error_log: Optional[str] = Field(default="", description="Error log or stack trace")
    language: str = Field(default="python", description="Programming language")
    code_content: Optional[str] = None
    file_path: Optional[str] = None
    auto_run: bool = Field(default=True, description="Auto-run code to detect errors")


class DebugResponse(BaseModel):
    session_id: str
    status: str
    message: str
    sse_url: Optional[str] = None


# ---------------------------------------------------------------------------
# In-memory session store (swap for Redis in production)
# ---------------------------------------------------------------------------

debug_sessions: dict = {}


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@router.post("/start", response_model=DebugResponse)
async def start_debugging(
    request: DebugRequest,
    background_tasks: BackgroundTasks,
    req: Request,
):
    session_id = str(uuid.uuid4())
    sse_manager = req.app.state.sse_manager

    # Register BEFORE starting the task so the queue exists when task calls send_event
    sse_manager.register(session_id)

    debug_sessions[session_id] = {
        "status": "started",
        "request": request.dict(),
        "created_at": datetime.utcnow().isoformat(),
    }

    background_tasks.add_task(
        run_debugging_task,
        session_id=session_id,
        request=request,
        sse_manager=sse_manager,
    )

    return DebugResponse(
        session_id=session_id,
        status="started",
        message="Debugging started. Connect to SSE for updates.",
        sse_url=f"/api/sse/{session_id}",
    )


@router.post("/file", response_model=DebugResponse)
async def debug_file(
    request: DebugRequest,
    background_tasks: BackgroundTasks,
    req: Request,
):
    if not request.code_content:
        raise HTTPException(status_code=400, detail="code_content required")

    session_id = str(uuid.uuid4())
    sse_manager = req.app.state.sse_manager

    sse_manager.register(session_id)

    debug_sessions[session_id] = {
        "status": "started",
        "request": request.dict(),
        "created_at": datetime.utcnow().isoformat(),
    }

    background_tasks.add_task(
        run_file_debugging_task,
        session_id=session_id,
        request=request,
        sse_manager=sse_manager,
    )

    return DebugResponse(
        session_id=session_id,
        status="started",
        message="File debugging started. Connect to SSE for updates.",
        sse_url=f"/api/sse/{session_id}",
    )


@router.get("/status/{session_id}")
async def get_debug_status(session_id: str):
    if session_id not in debug_sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    return debug_sessions[session_id]


@router.get("/result/{session_id}")
async def get_debug_result(session_id: str):
    if session_id not in debug_sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    session = debug_sessions[session_id]
    if session["status"] not in ("completed", "failed"):
        raise HTTPException(
            status_code=400,
            detail=f"Debugging not complete. Status: {session['status']}",
        )
    return session


@router.get("/sessions")
async def list_sessions():
    return {
        "sessions": [
            {"session_id": sid, "status": s["status"], "created_at": s["created_at"]}
            for sid, s in debug_sessions.items()
        ]
    }


# ---------------------------------------------------------------------------
# Background tasks
# ---------------------------------------------------------------------------

def _make_emitter(session_id: str, sse_manager) -> ProgressEmitter:
    emitter = ProgressEmitter(session_id)
    emitter.subscribe(sse_manager.send_event)
    return emitter


async def run_debugging_task(
    session_id: str,
    request: DebugRequest,
    sse_manager,
) -> None:
    emitter = _make_emitter(session_id, sse_manager)

    try:
        orchestrator = MYTHEOSOrchestrator(emitter=emitter)
        output = await orchestrator.debug(
            repo_url=request.repo_url,
            error_log=request.error_log or "",
            language=request.language,
        )

        debug_sessions[session_id].update({
            "status": "completed",
            "bug_report": output.get("bug_report", {}),
            "pull_request": output.get("pull_request", {}),
            "analysis": output.get("context", {}),
            "completed_at": datetime.utcnow().isoformat(),
        })

        await emitter.complete(
            "Debugging complete!",
            session_id=session_id,
            bug_report=output.get("bug_report", {}),
            pull_request=output.get("pull_request", {}),
        )

    except Exception as e:
        logger.error("Debugging task failed: %s", e, exc_info=True)
        debug_sessions[session_id].update({"status": "failed", "error": str(e)})
        await emitter.error(str(e))


async def run_file_debugging_task(
    session_id: str,
    request: DebugRequest,
    sse_manager,
) -> None:
    emitter = _make_emitter(session_id, sse_manager)
    temp_file: Optional[str] = None

    try:
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".py", encoding="utf-8", delete=False
        ) as f:
            f.write(request.code_content)
            temp_file = f.name

        debugger = LocalFileDebugger(verbose=False, emitter=emitter)
        result = await debugger.debug_file(
            file_path=temp_file,
            auto_run=request.auto_run,
        )

        debug_sessions[session_id].update({
            "status": "completed",
            "result": result,
            "completed_at": datetime.utcnow().isoformat(),
        })

        await emitter.complete("Analysis complete!", result=result)

    except Exception as e:
        logger.error("File debugging failed: %s", e, exc_info=True)
        debug_sessions[session_id].update({"status": "failed", "error": str(e)})
        await emitter.error(str(e))

    finally:
        if temp_file:
            try:
                Path(temp_file).unlink()
            except Exception:
                pass
            
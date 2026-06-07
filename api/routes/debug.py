"""Debug API endpoints with SSE support."""
from fastapi import APIRouter, HTTPException, BackgroundTasks, Request
from pydantic import BaseModel, Field
from typing import Optional, List
import uuid
import asyncio
from datetime import datetime

from src.core.orchestrator import MYTHEOSOrchestrator
from src.core.local_file_debugger import LocalFileDebugger
from src.utils.logger import get_logger

logger = get_logger(__name__)
router = APIRouter()

class DebugRequest(BaseModel):
    """Debug request schema."""
    repo_url: Optional[str] = None
    error_log: Optional[str] = Field(default="", description="Error log or stack trace")
    language: str = Field(default="python", description="Programming language")
    code_content: Optional[str] = None
    file_path: Optional[str] = None
    auto_run: bool = Field(default=True, description="Auto-run code to detect errors")

class DebugResponse(BaseModel):
    """Debug response schema."""
    session_id: str
    status: str
    message: str
    sse_url: Optional[str] = None

class DebugResult(BaseModel):
    """Complete debug result."""
    session_id: str
    bug_report: Optional[dict] = None
    pull_request: Optional[dict] = None
    analysis: Optional[dict] = None
    result: Optional[dict] = None
    status: str
    created_at: str

# In-memory storage for demo (use Redis in production)
debug_sessions = {}

@router.post("/start", response_model=DebugResponse)
async def start_debugging(
    request: DebugRequest,
    background_tasks: BackgroundTasks,
    req: Request
):
    """
    Start debugging process.
    
    Returns session_id and SSE URL for progress updates.
    """
    session_id = str(uuid.uuid4())
    
    # Store session
    debug_sessions[session_id] = {
        "status": "started",
        "request": request.dict(),
        "created_at": datetime.utcnow().isoformat()
    }
    
    # Start background task
    background_tasks.add_task(
        run_debugging_task,
        session_id=session_id,
        request=request,
        sse_manager=req.app.state.sse_manager
    )
    
    return DebugResponse(
        session_id=session_id,
        status="started",
        message="Debugging started. Connect to SSE for updates.",
        sse_url=f"/api/sse/{session_id}"
    )

@router.get("/status/{session_id}")
async def get_debug_status(session_id: str):
    """Get debugging session status."""
    if session_id not in debug_sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    return debug_sessions[session_id]

@router.get("/result/{session_id}")
async def get_debug_result(session_id: str):
    """Get complete debugging results."""
    if session_id not in debug_sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    session = debug_sessions[session_id]
    
    if session["status"] not in ["completed", "failed"]:
        raise HTTPException(
            status_code=400,
            detail=f"Debugging not complete. Status: {session['status']}"
        )
    
    return session

@router.post("/file", response_model=DebugResponse)
async def debug_file(
    request: DebugRequest,
    background_tasks: BackgroundTasks,
    req: Request
):
    """Debug a local file (code content provided)."""
    if not request.code_content:
        raise HTTPException(status_code=400, detail="code_content required")
    
    session_id = str(uuid.uuid4())
    
    debug_sessions[session_id] = {
        "status": "started",
        "request": request.dict(),
        "created_at": datetime.utcnow().isoformat()
    }
    
    background_tasks.add_task(
        run_file_debugging_task,
        session_id=session_id,
        request=request,
        sse_manager=req.app.state.sse_manager
    )
    
    return DebugResponse(
        session_id=session_id,
        status="started",
        message="File debugging started. Connect to SSE for updates.",
        sse_url=f"/api/sse/{session_id}"
    )

@router.get("/sessions")
async def list_sessions():
    """List all debugging sessions."""
    return {
        "sessions": [
            {
                "session_id": sid,
                "status": session["status"],
                "created_at": session["created_at"]
            }
            for sid, session in debug_sessions.items()
        ]
    }

async def run_debugging_task(
    session_id: str,
    request: DebugRequest,
    sse_manager
):
    """Background task for full debugging."""
    try:
        # Send progress updates via SSE
        await sse_manager.send_event(
            session_id,
            "progress",
            {"phase": "initialization", "message": "Starting debugging swarm..."}
        )
        
        orchestrator = MYTHEOSOrchestrator()
        
        # Send progress for each phase
        phases = [
            ("planning", "Planner agent creating debugging strategy"),
            ("reproduction", "Reproduction agent attempting to reproduce bug"),
            ("analysis", "Code analysis agent examining code structure"),
            ("context", "Context agent gathering historical information"),
            ("root_cause", "Root cause agent identifying source of bug"),
            ("fix", "Fix agent generating code solution"),
            ("test", "Test agent creating test cases"),
            ("review", "Review agent validating solution")
        ]
        
        for phase, message in phases:
            await sse_manager.send_event(
                session_id,
                "progress",
                {"phase": phase, "message": message}
            )
            await asyncio.sleep(0.5)  # Small delay for UI updates
        
        # Run debugging
        result = await orchestrator.debug(
            repo_url=request.repo_url,
            error_log=request.error_log or "",
            language=request.language
        )
        
        # Update session
        debug_sessions[session_id].update({
            "status": "completed",
            "bug_report": result.get("bug_report", {}),
            "pull_request": result.get("pull_request", {}),
            "analysis": result.get("context", {}),
            "completed_at": datetime.utcnow().isoformat()
        })
        
        # Send completion event
        await sse_manager.send_event(
            session_id,
            "complete",
            {
                "message": "Debugging complete!",
                "session_id": session_id
            }
        )
        
    except Exception as e:
        logger.error(f"Debugging task failed: {e}", exc_info=True)
        debug_sessions[session_id].update({
            "status": "failed",
            "error": str(e)
        })
        
        await sse_manager.send_event(
            session_id,
            "error",
            {"message": str(e)}
        )

async def run_file_debugging_task(
    session_id: str,
    request: DebugRequest,
    sse_manager
):
    """Background task for file debugging."""
    try:
        # Send initial progress
        await sse_manager.send_event(
            session_id,
            "progress",
            {"phase": "initialization", "message": "Preparing code analysis..."}
        )
        
        # Send progress updates for each phase
        phases = [
            ("planning", "Creating analysis strategy"),
            ("analysis", "Analyzing code structure and patterns"),
            ("reproduction", "Running code to detect errors"),
            ("root_cause", "Identifying root cause of issues"),
            ("fix", "Generating fix recommendations"),
            ("test", "Creating test cases"),
            ("review", "Reviewing proposed solutions")
        ]
        
        debugger = LocalFileDebugger(verbose=False)
        
        # Create temp file
        import tempfile
        from pathlib import Path
        
        with tempfile.NamedTemporaryFile(
            mode='w',
            suffix='.py',
            delete=False
        ) as f:
            f.write(request.code_content)
            temp_file = f.name
        
        # Run analysis with progress updates
        for i, (phase, message) in enumerate(phases):
            await sse_manager.send_event(
                session_id,
                "progress",
                {"phase": phase, "message": message}
            )
            
            # Run actual analysis at specific phases
            if i == 2:  # reproduction phase
                result = await debugger.debug_file(
                    file_path=temp_file,
                    auto_run=request.auto_run
                )
            
            await asyncio.sleep(0.3)  # Smooth UI updates
        
        # Clean up
        Path(temp_file).unlink()
        
        # Update session
        debug_sessions[session_id].update({
            "status": "completed",
            "result": result,
            "completed_at": datetime.utcnow().isoformat()
        })
        
        await sse_manager.send_event(
            session_id,
            "complete",
            {"message": "Analysis complete!", "result": result}
        )
        
    except Exception as e:
        logger.error(f"File debugging failed: {e}", exc_info=True)
        debug_sessions[session_id].update({
            "status": "failed",
            "error": str(e)
        })
        
        await sse_manager.send_event(
            session_id,
            "error",
            {"message": str(e)}
        )

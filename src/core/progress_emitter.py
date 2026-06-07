"""
Transport-agnostic progress emitter.

Agents and orchestrators emit structured domain events via ProgressEmitter.
The SSE layer (or any other transport) subscribes to those events.
Nothing in core business logic needs to know about SSE, WebSockets, or any
other delivery mechanism.

Usage
-----
# 1. Create an emitter for a session and bind it to SSE
emitter = ProgressEmitter(session_id)
emitter.subscribe(sse_manager.send_event)   # or any async callable

# 2. Pass the emitter into the orchestrator / debugger
orchestrator = MYTHEOSOrchestrator(emitter=emitter)

# 3. Inside an agent or orchestrator, just emit — no transport knowledge needed
await self.emitter.emit("root_cause", "Root cause identified.", done=True, root_cause="...")
"""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass, field
from typing import Any, Awaitable, Callable, Optional

logger = logging.getLogger(__name__)

# Type alias: any async function that accepts (session_id, event_type, payload)
EventHandler = Callable[[str, str, dict], Awaitable[None]]


@dataclass
class ProgressEvent:
    """Structured domain event emitted during a debug session."""
    session_id: str
    phase: str
    message: str
    done: bool = False          # True = phase finished, False = phase starting
    event_type: str = "progress"
    data: dict = field(default_factory=dict)  # arbitrary phase-specific payload


class ProgressEmitter:
    """
    Emits structured progress events to zero or more subscribers.

    Subscribers are async callables with the signature:
        async def handler(session_id: str, event_type: str, payload: dict) -> None

    This matches the existing sse_manager.send_event() signature, so wiring
    SSE requires a single line:

        emitter.subscribe(sse_manager.send_event)

    Other transports (WebSocket, Redis pub/sub, logging, testing) are added
    the same way without touching any orchestrator or agent code.
    """

    def __init__(self, session_id: str):
        self.session_id = session_id
        self._subscribers: list[EventHandler] = []

    # ------------------------------------------------------------------
    # Subscription API
    # ------------------------------------------------------------------

    def subscribe(self, handler: EventHandler) -> None:
        """Register an async event handler."""
        self._subscribers.append(handler)

    def unsubscribe(self, handler: EventHandler) -> None:
        self._subscribers = [h for h in self._subscribers if h is not handler]

    # ------------------------------------------------------------------
    # Emit API (used by orchestrators / agents)
    # ------------------------------------------------------------------

    async def emit(
        self,
        phase: str,
        message: str,
        *,
        done: bool = False,
        event_type: str = "progress",
        **extra: Any,
    ) -> None:
        """
        Emit a progress event to all subscribers.

        Args:
            phase:      Machine-readable phase name, e.g. "root_cause"
            message:    Human-readable status message
            done:       True when a phase has completed (vs. started)
            event_type: SSE event type ("progress", "complete", "error")
            **extra:    Any additional payload fields (e.g. root_cause="…")
        """
        payload: dict[str, Any] = {
            "phase": phase,
            "message": message,
            "done": done,
            **extra,
        }

        event = ProgressEvent(
            session_id=self.session_id,
            phase=phase,
            message=message,
            done=done,
            event_type=event_type,
            data=extra,
        )

        if not self._subscribers:
            logger.debug("ProgressEmitter: no subscribers for session %s", self.session_id)
            return

        # Fan out to all subscribers concurrently; log but don't raise on failure
        results = await asyncio.gather(
            *[handler(self.session_id, event.event_type, payload) for handler in self._subscribers],
            return_exceptions=True,
        )

        for handler, result in zip(self._subscribers, results):
            if isinstance(result, Exception):
                logger.error(
                    "ProgressEmitter: subscriber %s failed for session %s: %s",
                    getattr(handler, "__name__", repr(handler)),
                    self.session_id,
                    result,
                )

    async def complete(self, message: str = "Done!", **extra: Any) -> None:
        """Convenience: emit the terminal 'complete' event."""
        await self.emit("complete", message, done=True, event_type="complete", **extra)

    async def error(self, message: str, **extra: Any) -> None:
        """Convenience: emit the terminal 'error' event."""
        await self.emit("error", message, done=True, event_type="error", **extra)
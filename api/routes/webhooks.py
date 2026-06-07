"""GitHub webhook handlers."""
from fastapi import APIRouter, Request, HTTPException
from typing import Dict, Any
import hmac
import hashlib

from config.settings import settings
from src.utils.logger import get_logger

logger = get_logger(__name__)
router = APIRouter()

@router.post("/github")
async def github_webhook(request: Request):
    """
    Handle GitHub webhooks.
    
    Automatically triggers debugging when issues are created or updated.
    """
    # Verify signature
    signature = request.headers.get("X-Hub-Signature-256")
    if signature and settings.GITHUB_TOKEN:
        body = await request.body()
        expected_signature = "sha256=" + hmac.new(
            settings.GITHUB_TOKEN.encode(),
            body,
            hashlib.sha256
        ).hexdigest()
        
        if not hmac.compare_digest(signature, expected_signature):
            raise HTTPException(status_code=403, detail="Invalid signature")
    
    # Parse event
    event_type = request.headers.get("X-GitHub-Event")
    payload = await request.json()
    
    logger.info(f"Received GitHub webhook: {event_type}")
    
    if event_type == "issues":
        action = payload.get("action")
        if action in ["opened", "labeled"]:
            issue = payload.get("issue")
            
            # Check for "bug" label
            labels = [label["name"] for label in issue.get("labels", [])]
            if "bug" in labels:
                logger.info(f"Auto-debugging issue #{issue['number']}")
                # TODO: Trigger debugging automatically
                return {"status": "debugging_started", "issue": issue["number"]}
    
    return {"status": "received", "event": event_type}
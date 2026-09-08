"""
modules/narration/router.py — LLM Narration Layer (STUB).

This module is intentionally left as a clean stub.
Add the LLM provider SDK and implementation here when ready.

To enable:
  1. Set LLM_NARRATION_ENABLED=true in .env
  2. Add your LLM SDK to requirements.txt
  3. Implement summarize_payload() in service.py
  4. Uncomment the router registration in main.py

The rest of the app functions identically whether this module is enabled or not.
"""
import os
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from core.auth import get_current_user

LLM_ENABLED = os.getenv("LLM_NARRATION_ENABLED", "false").lower() == "true"

router = APIRouter(tags=["Narration"])


@router.get("/narration/status")
async def narration_status():
    """Lightweight status check — no auth required. Frontend uses this to show/hide Summarize button."""
    return {"enabled": LLM_ENABLED}


class SummarizeRequest(BaseModel):
    payload: dict
    context_type: str  # "risk_queue" | "carrier_scorecard"


@router.post("/narration/summarize")
async def summarize(
    body: SummarizeRequest,
    current_user: dict = Depends(get_current_user),
):
    """
    Narrate a pre-computed analytics payload via LLM.
    STUB — returns a placeholder message until an LLM provider is configured.

    The LLM NEVER computes numbers. It only narrates numbers already produced
    by the deterministic pipeline. This is a hard design boundary.
    """
    if not LLM_ENABLED:
        raise HTTPException(status_code=503, detail="LLM narration is not enabled.")

    # ── IMPLEMENT HERE ───────────────────────────────────────────────────────
    # 1. Choose provider: openai, anthropic, or generic httpx call.
    # 2. Build system prompt: "Narrate these pre-computed numbers in 2-3 plain
    #    sentences. Do not invent or compute any figures. Only describe what is given."
    # 3. Send body.payload as the user message.
    # 4. Return the LLM's response text.
    # ────────────────────────────────────────────────────────────────────────

    raise HTTPException(
        status_code=501,
        detail="LLM narration provider not yet configured. See modules/narration/router.py for instructions.",
    )

"""
AI Analytics Processor.

Architecture:
1. processor.py  — orchestrates the queue: fetches pending calls, dispatches to provider
2. providers/    — pluggable AI backends (OpenAI, Anthropic, local Whisper, etc.)

Current state: skeleton implementation that marks calls as "processing" and
returns placeholder results. Drop in a real STT + LLM provider to activate.

Design allows swapping providers without touching the orchestration logic.
"""
from datetime import datetime, timezone
from typing import Any, Dict

from core.config import settings
from core.logging import get_logger
from db.database import get_session
from db.models import Call
from src.repositories.call_repository import CallRepository

logger = get_logger(__name__)

# ── Provider interface ────────────────────────────────────────────────────────

class AIProvider:
    """Base class for AI analysis providers."""

    async def transcribe(self, mp3_url: str) -> str:
        raise NotImplementedError

    async def analyse(self, transcript: str, metadata: Dict[str, Any]) -> Dict[str, Any]:
        raise NotImplementedError


class MockProvider(AIProvider):
    """
    Placeholder provider — returns empty results.
    Replace with OpenAIProvider or AnthropicProvider in production.
    """

    async def transcribe(self, mp3_url: str) -> str:
        logger.debug("mock_transcribe", url=mp3_url)
        return ""

    async def analyse(self, transcript: str, metadata: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "conversation_topic": None,
            "key_points_of_the_dialogue": None,
            "next_steps": None,
            "attention_to_the_call": None,
            "operator_errors": None,
            "keywords": None,
            "badwords": None,
            "foul_language": None,
            "clients_mood": None,
            "operators_mood": None,
            "customer_satisfaction": None,
            "problem_solving_efficiency": None,
            "ability_to_adapt": None,
            "involvement": None,
            "problem_identification": None,
            "clarity_of_communication": None,
            "empathy": None,
            "operator_professionalism": None,
        }


def _get_provider() -> AIProvider:
    if settings.ai_processing_enabled and settings.openai_api_key:
        # Future: return OpenAIProvider(settings.openai_api_key)
        pass
    return MockProvider()


# ── Queue processor ────────────────────────────────────────────────────────────

async def process_call(call: Call, provider: AIProvider) -> bool:
    """
    Process a single call: transcribe → analyse → store.
    Returns True on success.
    """
    if not call.mp3_link:
        logger.warning("ai_no_mp3", call_id=call.id)
        return False

    async with get_session() as session:
        repo = CallRepository(session)

        # Mark as processing
        await repo.upsert_ai_analytic(
            call.id,
            processing_status="processing",
        )

        try:
            transcript = await provider.transcribe(call.mp3_link)

            metadata = {
                "call_type": str(call.call_type),
                "duration_seconds": call.seconds_talktime,
                "date": str(call.date),
            }
            analysis = await provider.analyse(transcript, metadata)

            await repo.upsert_ai_analytic(
                call.id,
                processing_status="done",
                processed_at=datetime.now(timezone.utc),
                transcript=transcript,
                **analysis,
            )

            logger.info("ai_processed", call_id=call.id)
            return True

        except Exception as exc:
            await repo.upsert_ai_analytic(
                call.id,
                processing_status="failed",
                processed_at=datetime.now(timezone.utc),
                error_message=str(exc)[:500],
            )
            logger.error("ai_processing_failed", call_id=call.id, error=str(exc))
            return False


async def process_pending_queue(batch_size: int = 20) -> int:
    """
    Pull a batch of unprocessed calls and run them through the AI pipeline.
    Returns number of successfully processed calls.
    """
    provider = _get_provider()
    processed = 0

    async with get_session() as session:
        repo = CallRepository(session)
        pending_calls = await repo.list_pending_ai(limit=batch_size)

    logger.info("ai_queue_batch", count=len(pending_calls))

    for call in pending_calls:
        success = await process_call(call, provider)
        if success:
            processed += 1

    return processed

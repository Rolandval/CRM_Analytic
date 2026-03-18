from __future__ import annotations

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field
from db.models import CallState, CallType
from src.schemas.user import UserListOut


class CallAiAnalyticOut(BaseModel):
    id: int
    call_id: int
    processing_status: str
    processed_at: Optional[datetime]
    transcript: Optional[str]
    conversation_topic: Optional[str]
    key_points_of_the_dialogue: Optional[str]
    next_steps: Optional[str]
    attention_to_the_call: Optional[str]
    operator_errors: Optional[str]
    keywords: Optional[str]
    badwords: Optional[str]
    foul_language: Optional[str]
    clients_mood: Optional[str]
    operators_mood: Optional[str]
    customer_satisfaction: Optional[str]
    problem_solving_efficiency: Optional[str]
    ability_to_adapt: Optional[str]
    involvement: Optional[str]
    problem_identification: Optional[str]
    clarity_of_communication: Optional[str]
    empathy: Optional[str]
    operator_professionalism: Optional[str]

    model_config = {"from_attributes": True}


class CallOut(BaseModel):
    id: int
    user_id: Optional[int]
    from_number: Optional[str]
    to_number: Optional[str]
    call_type: Optional[CallType]
    call_state: Optional[CallState]
    date: Optional[datetime]
    seconds_fulltime: float
    seconds_talktime: float
    mp3_link: Optional[str]
    callback: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class CallDetailOut(CallOut):
    """Call with nested user snippet and AI analytics."""
    user: Optional[UserListOut] = None
    ai_analytic: Optional[CallAiAnalyticOut] = None

    model_config = {"from_attributes": True}


class CallFilter(BaseModel):
    """Query parameters for filtering calls."""
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    call_type: Optional[CallType] = None
    call_state: Optional[CallState] = None
    user_id: Optional[int] = None
    min_duration: Optional[float] = Field(None, ge=0, description="Min seconds_talktime")
    max_duration: Optional[float] = Field(None, ge=0, description="Max seconds_talktime")
    callback: Optional[bool] = None
    search: Optional[str] = Field(None, max_length=50, description="Search in from/to numbers")


class SyncStats(BaseModel):
    total: int
    new: int
    updated: int
    skipped: int
    errors: int

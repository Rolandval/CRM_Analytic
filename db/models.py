from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Enum as SQLAlchemyEnum,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Table,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, relationship


# ── Base ──────────────────────────────────────────────────────────────────────

class Base(DeclarativeBase):
    pass


# ── Enums ─────────────────────────────────────────────────────────────────────

class CallState(str, Enum):
    ANSWER = "ANSWER"
    NOANSWER = "NOANSWER"
    BUSY = "BUSY"
    FAILED = "FAILED"


class CallType(str, Enum):
    INB = "IN"
    OUT = "OUT"


# ── Many-to-many pivot ────────────────────────────────────────────────────────

user_type_association = Table(
    "user_type_association",
    Base.metadata,
    Column("user_id", Integer, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
    Column("type_id", Integer, ForeignKey("user_types.id", ondelete="CASCADE"), primary_key=True),
)


# ── Lookup tables ─────────────────────────────────────────────────────────────

class UserCategory(Base):
    __tablename__ = "user_categories"

    id: Mapped[int] = Column(Integer, primary_key=True)
    name: Mapped[str] = Column(String(50), unique=True, nullable=False)

    users: Mapped[list[User]] = relationship("User", back_populates="category")


class UserType(Base):
    __tablename__ = "user_types"

    id: Mapped[int] = Column(Integer, primary_key=True)
    name: Mapped[str] = Column(String(50), unique=True, nullable=False)

    users: Mapped[list[User]] = relationship(
        "User",
        secondary=user_type_association,
        back_populates="types",
    )


# ── Admin / operator accounts (for JWT auth) ──────────────────────────────────

class AdminUser(Base):
    __tablename__ = "admin_users"

    id: Mapped[int] = Column(Integer, primary_key=True)
    username: Mapped[str] = Column(String(50), unique=True, nullable=False, index=True)
    email: Mapped[str] = Column(String(100), unique=True, nullable=False, index=True)
    hashed_password: Mapped[str] = Column(String(255), nullable=False)
    is_active: Mapped[bool] = Column(Boolean, default=True, nullable=False)
    is_superuser: Mapped[bool] = Column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    last_login: Mapped[datetime | None] = Column(DateTime(timezone=True), nullable=True)


# ── Core domain ───────────────────────────────────────────────────────────────

class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = Column(Integer, primary_key=True)
    phone_number: Mapped[str | None] = Column(String(20), nullable=True, unique=True, index=True)
    name: Mapped[str | None] = Column(String(100), nullable=True)
    calls_count: Mapped[int] = Column(Integer, default=0, nullable=False)
    description: Mapped[str | None] = Column(Text, nullable=True)
    created_at: Mapped[datetime] = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    updated_at: Mapped[datetime] = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    category_id: Mapped[int | None] = Column(
        Integer, ForeignKey("user_categories.id"), nullable=True, default=None, index=True
    )
    category: Mapped[UserCategory | None] = relationship("UserCategory", back_populates="users")

    types: Mapped[list[UserType]] = relationship(
        "UserType",
        secondary=user_type_association,
        back_populates="users",
    )

    calls: Mapped[list[Call]] = relationship(
        "Call", back_populates="user", cascade="all, delete-orphan"
    )


class Call(Base):
    __tablename__ = "calls"
    __table_args__ = (
        # Composite index for the most common query pattern: user's calls sorted by date
        Index("ix_calls_user_date", "user_id", "date"),
        # Index for date range queries (primary filter in reporting)
        Index("ix_calls_date", "date"),
        # Index for type/state filtering
        Index("ix_calls_type_state", "call_type", "call_state"),
    )

    id: Mapped[int] = Column(Integer, primary_key=True)  # Unitalk's own ID
    user_id: Mapped[int | None] = Column(
        Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True
    )
    from_number: Mapped[str | None] = Column(String(25), nullable=True)
    to_number: Mapped[str | None] = Column(String(25), nullable=True)
    call_type: Mapped[CallType | None] = Column(SQLAlchemyEnum(CallType, name="calltype"), nullable=True)
    call_state: Mapped[CallState | None] = Column(SQLAlchemyEnum(CallState, name="callstate"), nullable=True)
    date: Mapped[datetime | None] = Column(DateTime(timezone=False), nullable=True)
    seconds_fulltime: Mapped[float] = Column(Float, default=0, nullable=False)
    seconds_talktime: Mapped[float] = Column(Float, default=0, nullable=False)
    mp3_link: Mapped[str | None] = Column(String(512), nullable=True)
    callback: Mapped[bool] = Column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    user: Mapped[User | None] = relationship("User", back_populates="calls")
    ai_analytic: Mapped[CallAiAnalytic | None] = relationship(
        "CallAiAnalytic", back_populates="call", uselist=False, cascade="all, delete-orphan"
    )


class CallAiAnalytic(Base):
    """
    Stores AI-generated analytics for a call.
    Each metric is a free-text field — the AI model populates them.
    call_id has a unique constraint: one analytic record per call.
    """
    __tablename__ = "call_ai_analytics"
    __table_args__ = (UniqueConstraint("call_id", name="uq_call_ai_analytics_call_id"),)

    id: Mapped[int] = Column(Integer, primary_key=True)
    call_id: Mapped[int] = Column(
        Integer, ForeignKey("calls.id", ondelete="CASCADE"), nullable=False, index=True
    )

    # ── Processing metadata ────────────────────────────────────────────────────
    processed_at: Mapped[datetime | None] = Column(DateTime(timezone=True), nullable=True)
    processing_status: Mapped[str] = Column(
        String(20), default="pending", nullable=False, index=True
    )  # pending | processing | done | failed
    error_message: Mapped[str | None] = Column(Text, nullable=True)

    # ── Transcript ─────────────────────────────────────────────────────────────
    transcript: Mapped[str | None] = Column(Text, nullable=True)

    # ── AI-scored metrics (free text / short summaries) ────────────────────────
    conversation_topic: Mapped[str | None] = Column(Text, nullable=True)
    key_points_of_the_dialogue: Mapped[str | None] = Column(Text, nullable=True)
    next_steps: Mapped[str | None] = Column(Text, nullable=True)
    attention_to_the_call: Mapped[str | None] = Column(Text, nullable=True)
    operator_errors: Mapped[str | None] = Column(Text, nullable=True)
    keywords: Mapped[str | None] = Column(Text, nullable=True)
    badwords: Mapped[str | None] = Column(Text, nullable=True)
    foul_language: Mapped[str | None] = Column(Text, nullable=True)

    # ── Sentiment / mood ──────────────────────────────────────────────────────
    clients_mood: Mapped[str | None] = Column(String(50), nullable=True)
    operators_mood: Mapped[str | None] = Column(String(50), nullable=True)
    customer_satisfaction: Mapped[str | None] = Column(String(50), nullable=True)

    # ── Quality scores (numeric stored as string for flexibility) ─────────────
    problem_solving_efficiency: Mapped[str | None] = Column(String(20), nullable=True)
    ability_to_adapt: Mapped[str | None] = Column(String(20), nullable=True)
    involvement: Mapped[str | None] = Column(String(20), nullable=True)
    problem_identification: Mapped[str | None] = Column(String(20), nullable=True)
    clarity_of_communication: Mapped[str | None] = Column(String(20), nullable=True)
    empathy: Mapped[str | None] = Column(String(20), nullable=True)
    operator_professionalism: Mapped[str | None] = Column(String(20), nullable=True)

    call: Mapped[Call] = relationship("Call", back_populates="ai_analytic")

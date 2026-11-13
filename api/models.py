"""Tablas de Fase 0.

Se guarda el estado completo del motor en `games.state` (JSONB) y un log de
acciones idempotentes. Cuando el contenido crezca (NPC, relaciones, eventos)
esas entidades se normalizan en tablas propias; el snapshot sigue siendo la
fuente de verdad para cargar partidas.
"""

from __future__ import annotations

import uuid
from datetime import date, datetime

from sqlalchemy import (
    JSON,
    BigInteger,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

JsonType = JSON().with_variant(JSONB(astext_type=Text()), "postgresql")


class Base(DeclarativeBase):
    pass


class Game(Base):
    __tablename__ = "games"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    seed: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    state: Mapped[dict] = mapped_column(JsonType, nullable=False)
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


class ActionLog(Base):
    __tablename__ = "action_log"
    __table_args__ = (
        UniqueConstraint("game_id", "idempotency_key", name="uq_action_idempotency"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    game_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("games.id", ondelete="CASCADE"), index=True, nullable=False
    )
    action: Mapped[str] = mapped_column(String(32), nullable=False)
    idempotency_key: Mapped[str | None] = mapped_column(String(120), nullable=True)
    payload: Mapped[dict] = mapped_column(JsonType, nullable=False, default=dict)
    result: Mapped[dict] = mapped_column(JsonType, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

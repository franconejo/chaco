"""Endpoints de partida: crear, consultar, actuar y resolver escenas."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, Header, HTTPException
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from api.db import get_db
from api.models import ActionLog, Game
from api.schemas import (
    ActionRequest,
    ActionResultOut,
    ActivitiesOut,
    CreateGameRequest,
    GameOut,
    InventoryOut,
    NpcsOut,
    PendingOut,
    ResolveOut,
    ResolveRequest,
    ShopOut,
)
from data import items as item_catalog
from data import locations as location_catalog
from data import map as map_catalog
from engine import actions, events, prices
from engine import inventory as inv
from engine import npc as npc_runtime
from engine.activities import available as available_activities
from engine.energy import PA_MAX
from engine.state import GameState

router = APIRouter(prefix="/games", tags=["games"])


def _out(game: Game) -> dict:
    estado = GameState.from_snapshot(game.state)
    return {
        "game_id": str(game.id),
        "version": game.version,
        "pa": estado.pa,
        "pa_max": PA_MAX,
        "closed_days": estado.closed_days,
        "location": estado.location,
        "location_label": location_catalog.label(estado.location),
        "clock": estado.moment().to_dict(),
        "player": estado.player.to_dict(),
        "identity": {
            "suspicion": round(estado.identity.get("suspicion", 0.0), 3),
            "credibility": round(estado.identity.get("credibility", 100.0), 3),
        },
        "inventory": inv.to_list(estado.inventory),
        "npcs_here": npc_runtime.present(estado),
        "pending_count": len(estado.pending),
    }


def _load(db: Session, game_id: uuid.UUID, lock: bool = False) -> Game:
    consulta = select(Game).where(Game.id == game_id)
    if lock:
        consulta = consulta.with_for_update()
    game = db.execute(consulta).scalar_one_or_none()
    if game is None:
        raise HTTPException(
            status_code=404,
            detail={"code": "partida_inexistente", "message": "No existe esa partida."},
        )
    return game


def _engine_error(exc: Exception) -> HTTPException:
    from engine.errors import EngineError

    if isinstance(exc, EngineError):
        return HTTPException(
            status_code=400, detail={"code": exc.code, "message": exc.message}
        )
    raise exc


@router.post("", response_model=GameOut, status_code=201)
def create_game(payload: CreateGameRequest, db: Session = Depends(get_db)) -> dict:
    estado = GameState.new(
        start_date=payload.start_date,
        seed=payload.seed,
        difficulty=payload.difficulty,
    )
    game = Game(seed=payload.seed, start_date=payload.start_date, state=estado.snapshot())
    db.add(game)
    db.commit()
    db.refresh(game)
    return _out(game)


@router.get("/{game_id}", response_model=GameOut)
def read_game(game_id: uuid.UUID, db: Session = Depends(get_db)) -> dict:
    return _out(_load(db, game_id))
def import_game(payload: dict, db: Session = Depends(get_db)) -> dict:
    from engine.state import GameState as GS

    state_data = payload.get("state") or payload
    estado = GS.from_snapshot(state_data)
    game = Game(
        seed=int(payload.get("seed", estado.seed)),
        start_date=estado.start_date,
        state=estado.snapshot(),
    )
    db.add(game)
    db.commit()
    db.refresh(game)


@router.get("/{game_id}/activities", response_model=ActivitiesOut)
def list_activities(game_id: uuid.UUID, db: Session = Depends(get_db)) -> dict:
    game = _load(db, game_id)
    estado = GameState.from_snapshot(game.state)
    return {
        "game_id": str(game.id),
        "pa": estado.pa,
        "activities": available_activities(estado),
    }


@router.get("/{game_id}/inventory", response_model=InventoryOut)
def read_inventory(game_id: uuid.UUID, db: Session = Depends(get_db)) -> dict:
    game = _load(db, game_id)
    estado = GameState.from_snapshot(game.state)
    return {
        "game_id": str(game.id),
        "money": estado.player.money,
        "total_weight": inv.total_weight(estado.inventory),
        "items": inv.to_list(estado.inventory),
    }


@router.get("/{game_id}/npcs", response_model=NpcsOut)
def read_npcs(game_id: uuid.UUID, db: Session = Depends(get_db)) -> dict:
    game = _load(db, game_id)
    estado = GameState.from_snapshot(game.state)
    return {"game_id": str(game.id), "npcs": npc_runtime.known(estado)}


@router.get("/{game_id}/pending", response_model=PendingOut)
def read_pending(game_id: uuid.UUID, db: Session = Depends(get_db)) -> dict:
    game = _load(db, game_id)
    estado = GameState.from_snapshot(game.state)
    return {"game_id": str(game.id), "events": events.pending_view(estado)}


@router.get("/{game_id}/shop", response_model=ShopOut)
def read_shop(game_id: uuid.UUID, db: Session = Depends(get_db)) -> dict:
    game = _load(db, game_id)
    estado = GameState.from_snapshot(game.state)
    return {
        "game_id": str(game.id),
        "money": estado.player.money,
        "price_multiplier": prices.multiplier(estado),
        "items": [
            {**item.to_dict(), "effective_price": prices.price_of(estado, item)}
            for item in item_catalog.buyable()
        ],
    }


@router.get("/{game_id}/export")
def export_game(game_id: uuid.UUID, db: Session = Depends(get_db)) -> dict:
    game = _load(db, game_id)
    return {
        "game_id": str(game.id),
        "seed": game.seed,
        "start_date": game.start_date.isoformat(),
        "version": game.version,
        "state": game.state,
    }
@router.get("/{game_id}/log")
def read_log(game_id: uuid.UUID, db: Session = Depends(get_db)) -> dict:
    game = _load(db, game_id)
    estado = GameState.from_snapshot(game.state)
    return {"game_id": str(game.id), "entries": estado.log[-40:]}


@router.get("/map")
def read_map() -> dict:
    return {
        "nodes": [
            {
                "id": n.id,
                "label": n.label,
                "x": n.x,
                "y": n.y,
                "zone": n.zone,
                "public": n.public,
            }
            for n in map_catalog.NODES
        ],
        "edges": [{"a": e.a, "b": e.b} for e in map_catalog.EDGES],
        "zones": map_catalog.ZONE_LABELS,
        "zone_colors": map_catalog.ZONE_COLORS,
    }
@router.post("/{game_id}/actions", response_model=ActionResultOut)
def run_action(
    game_id: uuid.UUID,
    payload: ActionRequest,
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
    db: Session = Depends(get_db),
) -> dict:
    if idempotency_key:
        previo = db.execute(
            select(ActionLog).where(
                ActionLog.game_id == game_id,
                ActionLog.idempotency_key == idempotency_key,
            )
        ).scalar_one_or_none()
        if previo is not None:
            return previo.result

    game = _load(db, game_id, lock=True)
    estado = GameState.from_snapshot(game.state)

    try:
        resultado = actions.perform(estado, payload.type, payload.model_dump(exclude_none=True))
    except Exception as exc:  # noqa: BLE001 - se traduce a error HTTP
        # Si el error es una interrupción narrativa, el acontecimiento ya se
        # disparó en memoria: hay que guardarlo o el cliente recibiría un 400
        # pidiéndole resolver una escena que no existe.
        if estado.pending:
            game.state = estado.snapshot()
            game.version += 1
            db.commit()
        else:
            db.rollback()
        raise _engine_error(exc) from exc

    game.state = estado.snapshot()
    game.version += 1
    salida = {"game": _out(game), "result": resultado.to_dict()}

    if idempotency_key:
        db.add(
            ActionLog(
                game_id=game.id,
                action=payload.type,
                idempotency_key=idempotency_key,
                payload=payload.model_dump(mode="json", exclude_none=True),
                result=salida,
            )
        )

    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        previo = db.execute(
            select(ActionLog).where(
                ActionLog.game_id == game_id,
                ActionLog.idempotency_key == idempotency_key,
            )
        ).scalar_one_or_none()
        if previo is None:
            raise
        return previo.result

    return salida


@router.post("/{game_id}/pending/{uid}/resolve", response_model=ResolveOut)
def resolve_pending(
    game_id: uuid.UUID,
    uid: str,
    payload: ResolveRequest,
    db: Session = Depends(get_db),
) -> dict:
    game = _load(db, game_id, lock=True)
    estado = GameState.from_snapshot(game.state)

    try:
        resultado = actions.resolve_event(estado, uid, payload.choice)
    except Exception as exc:  # noqa: BLE001
        db.rollback()
        raise _engine_error(exc) from exc

    game.state = estado.snapshot()
    game.version += 1
    salida = {"game": _out(game), "result": resultado}
    db.commit()
    return salida

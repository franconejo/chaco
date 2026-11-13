"""Simulación headless de varios días (herramienta de desarrollo).

Sirve para ver si el bucle básico cierra: trabajar, comer, beber, comprar,
descansar y dormir. No es un test; es una forma rápida de mirar números.

    .\\.venv\\Scripts\\python.exe tools\\demo_dia.py --dias 5 --seed 7
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from engine import actions  # noqa: E402
from engine.errors import EngineError  # noqa: E402
from engine.state import GameState  # noqa: E402

# Jornada fija de referencia: 24 horas exactas, de 05:00 a 05:00.
RUTINA = (
    ("eat", {}),  # 05:00 → 06:00
    ("activity", {"activity": "buscar_agua"}),  # 06:00 → 07:00
    ("drink", {}),  # 07:00 → 08:00
    ("activity", {"activity": "trabajar"}),  # 08:00 → 13:00
    ("drink", {}),  # 13:00 → 14:00
    ("eat", {}),  # 14:00 → 15:00
    ("buy", {"item": "chipa", "qty": 3}),  # 15:00 → 16:00
    ("visit", {"npc": "juana"}),  # 16:00 → 18:00
    ("activity", {"activity": "buscar_agua"}),  # 18:00 → 19:00
    ("drink", {}),  # 19:00 → 20:00
    ("eat", {}),  # 20:00 → 21:00
    ("sleep", {"hours": 8}),  # 21:00 → 05:00 del día siguiente
)


def resumen(estado: GameState) -> str:
    m = estado.moment()
    p = estado.player
    return (
        f"día {m.day_index} {m.date_label} {m.time_label} "
        f"| PA {estado.pa:2d} | salud {p.health:5.1f} hidra {p.hydration:5.1f} "
        f"nutri {p.nutrition:5.1f} fatiga {p.fatigue:5.1f} "
        f"| $ {p.money} | {estado.location} | pendientes {len(estado.pending)}"
    )


def resolver_pendientes(estado: GameState) -> None:
    while estado.pending:
        escena = estado.pending[0]
        opcion = escena.get("choices", [{}])[0]
        uid = escena.get("uid")
        if not uid:
            estado.pending.pop(0)
            continue
        print(f"  · escena «{escena['title']}» -> {opcion.get('text', '')[:60]}")
        actions.resolve_event(estado, uid, opcion.get("id", ""))


def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    parser = argparse.ArgumentParser()
    parser.add_argument("--dias", type=int, default=5)
    parser.add_argument("--seed", type=int, default=0)
    args = parser.parse_args()

    estado = GameState.new(seed=args.seed)
    print(resumen(estado))

    for _ in range(args.dias):
        for accion, params in RUTINA:
            resultado = None
            reintentos = 0
            while True:
                try:
                    resultado = actions.perform(estado, accion, params)
                    break
                except EngineError as exc:
                    print(f"  x {accion}: [{exc.code}] {exc.message}")
                    if exc.code == "escena_pendiente" and reintentos < 3:
                        resolver_pendientes(estado)
                        reintentos += 1
                        continue
                    break

            if resultado is None:
                resolver_pendientes(estado)
                continue

            for mensaje in resultado.messages:
                if mensaje:
                    print(f"  · {mensaje}")
            for evento in resultado.fired_events:
                print(f"  ! evento: {evento['title']}")
            resolver_pendientes(estado)
        print(resumen(estado))

    estado.take_fired()


if __name__ == "__main__":
    main()

"""Errores de reglas compartidos por el motor.

Vive aparte para que `state`, `effects`, `events` y `actions` puedan importarlo
sin ciclos.
"""

from __future__ import annotations


class EngineError(Exception):
    """Error de reglas. La API lo traduce a 400 con `code` + mensaje."""

    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code
        self.message = message

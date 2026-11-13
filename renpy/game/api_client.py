# -*- coding: utf-8 -*-
"""Puente HTTP entre Ren'Py y el backend de Chaco.

Ren'Py corre en el hilo principal de la UI. Una llamada HTTP bloqueante
congelaría la ventana, así que cada operación de red se ejecuta en un hilo
aparte (`threading.Thread`) y el resultado se deposita en un contenedor
compartido (`_results`) que el hilo principal lee con `wait_result`.

El backend sigue siendo la única autoridad: este módulo no calcula reglas.
"""

from __future__ import annotations

import json
import threading
import urllib.error
import urllib.request

try:
    import renpy
except Exception:  # noqa: BLE001
    renpy = None  # type: ignore[assignment]

# Se puede cambiar desde la pantalla de configuración inicial.
API_BASE = "https://demo.eibrapp.com.py"

# Contenedor de resultados compartido entre el hilo de red y el principal.
_results: dict = {}
_lock = threading.Lock()


def set_api_base(url: str) -> None:
    global API_BASE
    API_BASE = url.rstrip("/")


def _request(method: str, path: str, body=None, idempotency_key=None):
    url = API_BASE + path
    data = json.dumps(body).encode("utf-8") if body is not None else None
    req = urllib.request.Request(url, data=data, method=method)
    req.add_header("Content-Type", "application/json")
    if idempotency_key:
        req.add_header("Idempotency-Key", idempotency_key)
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        try:
            detail = json.loads(e.read().decode("utf-8"))
        except Exception:
            detail = {"code": "http_error", "message": str(e)}
        return {"_error": e.code, "_detail": detail}
    except Exception as e:  # noqa: BLE001
        return {"_error": "network", "_detail": {"code": "red", "message": str(e)}}


def _store(key, value):
    with _lock:
        _results[key] = value


def _take(key):
    with _lock:
        return _results.pop(key, None)


def _pending(key):
    with _lock:
        return key in _results


# ---------- operaciones de alto nivel ----------


def create_game(seed=7, result_key="create"):
    def worker():
        _store(result_key, _request("POST", "/games", {"seed": seed, "start_date": "1932-09-01"}))

    threading.Thread(target=worker, daemon=True).start()


def load_game(game_id, result_key="load"):
    def worker():
        _store(result_key, _request("GET", f"/games/{game_id}"))

    threading.Thread(target=worker, daemon=True).start()


def do_action(game_id, action_type, payload=None, result_key="action"):
    import uuid

    key = str(uuid.uuid4())
    body = {"type": action_type}
    if payload:
        body.update(payload)

    def worker():
        _store(
            result_key,
            _request("POST", f"/games/{game_id}/actions", body, idempotency_key=key),
        )

    threading.Thread(target=worker, daemon=True).start()


def load_pending(game_id, result_key="pending"):
    def worker():
        _store(result_key, _request("GET", f"/games/{game_id}/pending"))

    threading.Thread(target=worker, daemon=True).start()


def resolve_pending(game_id, uid, choice, result_key="resolve"):
    import uuid

    key = str(uuid.uuid4())

    def worker():
        _store(
            result_key,
            _request(
                "POST",
                f"/games/{game_id}/pending/{uid}/resolve",
                {"choice": choice},
                idempotency_key=key,
            ),
        )

    threading.Thread(target=worker, daemon=True).start()


def load_inventory(game_id, result_key="inventory"):
    def worker():
        _store(result_key, _request("GET", f"/games/{game_id}/inventory"))

    threading.Thread(target=worker, daemon=True).start()


def load_npcs(game_id, result_key="npcs"):
    def worker():
        _store(result_key, _request("GET", f"/games/{game_id}/npcs"))

    threading.Thread(target=worker, daemon=True).start()


def load_log(game_id, result_key="log"):
    def worker():
        _store(result_key, _request("GET", f"/games/{game_id}/log"))

    threading.Thread(target=worker, daemon=True).start()


# ---------- helpers para el hilo principal ----------


def wait_result(key, timeout=10.0):
    """Bloquea el hilo principal hasta que llegue el resultado (con timeout).

    Ren'Py no debe hacer polling ocupado: se usa renpy.pause en el caller.
    Esta función sólo consulta; el caller decide cuándo pausar.
    """
    import time

    deadline = time.time() + timeout
    while time.time() < deadline:
        if _pending(key):
            return _take(key)
        time.sleep(0.05)
    return None


def has_result(key):
    return _pending(key)


def take_result(key):
    return _take(key)

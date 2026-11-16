# -*- coding: utf-8 -*-
# Chaco — puente Ren'Py (Fase 3)
#
# Corre en ventana propia y consume la misma API que el cliente web.
# El motor (engine/) sigue siendo la única autoridad: acá sólo se pinta.

init python:
    import sys, os
    sys.path.insert(0, renpy.config.gamedir)
    try:
        import api_client
    except Exception:
        pass

    game_id = None
    game_state = None
    action_result = None
    pending_scene = None

    def refresh_state():
        global game_state
        api_client.load_game(game_id, "state")
        r = api_client.wait_result("state", 10.0)
        if r and not r.get("_error"):
            game_state = r

    def do(action_type, payload=None):
        global action_result
        action_result = None
        api_client.do_action(game_id, action_type, payload, "action")
        action_result = api_client.wait_result("action", 10.0)
        return action_result

    def check_pending():
        global pending_scene
        api_client.load_pending(game_id, "pending")
        r = api_client.wait_result("pending", 10.0)
        if r and not r.get("_error"):
            evs = r.get("events") or []
            pending_scene = evs[0] if evs else None
        else:
            pending_scene = None
        return pending_scene

    def resolve(choice):
        global pending_scene
        if not pending_scene:
            return None
        uid = pending_scene.get("uid")
        api_client.resolve_pending(game_id, uid, choice, "resolve")
        r = api_client.wait_result("resolve", 10.0)
        pending_scene = None
        check_pending()
        refresh_state()
        return r

    def show_location_bg():
        loc = game_state["location"] if game_state else "casa"
        bg_map = {
            "casa": "bg_casa", "almacen": "bg_almacen", "taller": "bg_taller",
            "plaza": "bg_plaza", "mercado": "bg_mercado", "iglesia": "bg_iglesia",
            "pozo": "bg_rio", "rio": "bg_rio", "fundicion": "bg_fundicion",
            "salto": "bg_salto", "cuartel": "bg_cuartel", "estacion": "bg_estacion",
        }
        bg = bg_map.get(loc, "bg_casa")
        renpy.scene()
        renpy.show(bg)
        if not r:
            renpy.say(narrador, "Sin respuesta del servidor.")
            return
        if r.get("_error"):
            d = r.get("_detail", {})
            renpy.say(narrador, d.get("message", "Error"))
            return
        res = r.get("result", {})
        for m in (res.get("messages") or []):
            renpy.say(narrador, m)
        for e in (res.get("fired_events") or []):
            renpy.say(narrador, "¡Evento: {}!".format(e.get("title", "")))


# ---------- imágenes de fondo ----------

image bg_plaza = "images/bg/bg_plaza.png"
image bg_almacen = "images/bg/bg_almacen.png"
image bg_casa = "images/bg/bg_casa.png"
image bg_iglesia = "images/bg/bg_iglesia.png"
image bg_fundicion = "images/bg/bg_fundicion.png"
image bg_rio = "images/bg/bg_rio.png"
image bg_taller = "images/bg/bg_taller.png"
image bg_mercado = "images/bg/bg_mercado.png"
image bg_cuartel = "images/bg/bg_cuartel.png"
image bg_estacion = "images/bg/bg_estacion.png"
image bg_salto = "images/bg/bg_salto.png"

define juana = Character("Juana", color="#c9a063")
define celia = Character("Celia", color="#a89880")
define aurora = Character("Aurora", color="#d9b073")
define aurelio = Character("Aurelio", color="#8b6f47")
define ramon = Character("Don Ramón", color="#7a6a5a")
define vera = Character("Sargento Vera", color="#a85a4a")
define ursula = Character("Doña Úrsula", color="#7a9a6b")
define padre_ignacio = Character("Padre Ignacio", color="#7a6a5a")
define mercedes = Character("Doña Mercedes", color="#a89880")
define ortega = Character("Teniente Ortega", color="#a85a4a")


screen hud():
    frame:
        xalign 0.0
        yalign 0.0
        padding (10, 10)
        vbox:
            spacing 4
            if game_state:
                $ c = game_state["clock"]
                text "[c['time_label']] · día [c['day_index']]" size 14 color "#c9a063"
                text "PA: [game_state['pa']] / [game_state['pa_max']]" size 14
                text "Lugar: [game_state['location_label']]" size 12
                text "Salud: [game_state['player']['health']:.0f]  Hidr: [game_state['player']['hydration']:.0f]" size 12
                text "Nutri: [game_state['player']['nutrition']:.0f]  Fatiga: [game_state['player']['fatigue']:.0f]" size 12
                text "Dinero: $[game_state['player']['money']]" size 12
                text "Sospecha: [game_state['identity']['suspicion']:.0f]  Cred: [game_state['identity']['credibility']:.0f]" size 12
            else:
                text "Sin partida" size 14


# ---------- flujo principal ----------

label start:
    scene black
    "Chaco — vida cotidiana en la guerra (1932–1935)"
    "Cliente Ren'Py · Fase 3"

    menu:
        "¿Qué querés hacer?"
        "Nueva partida (semilla 7)":
            $ api_client.create_game(7, "create")
            $ r = api_client.wait_result("create", 10.0)
            if r and not r.get("_error"):
                $ game_id = r["game_id"]
                $ refresh_state()
                "Partida creada."
            else:
                "No se pudo crear la partida. ¿Está corriendo la API en http://127.0.0.1:8010?"
                return
        "Cargar partida por id":
            $ pid = renpy.input("Id de partida:", default="")
            $ pid = pid.strip()
            if pid:
                $ game_id = pid
                $ refresh_state()
                if not game_state:
                    "No se encontró la partida."
                    return
            else:
                return
        "Salir":
            return

    jump game_loop


label game_loop:
    show screen hud
    $ refresh_state()
    $ check_pending()

    if pending_scene:
        jump scene_pending

    # Muerte
    if game_state and "muerto" in game_state.get("flags", []):
        $ show_location_bg()
        "El cuerpo no aguantó más. Fin de la partida."
        return

    # Finales
    if game_state and any(f.startswith("final_") for f in game_state.get("flags", [])):
        $ show_location_bg()
        $ finales = [f for f in game_state["flags"] if f.startswith("final_")]
        "Has llegado a un final: [finales[0]]."
        return

    $ show_location_bg()

    menu:
        "¿Qué hacés?"

        "Comer":
            $ show_result(do("eat", {}))
        "Beber":
            $ show_result(do("drink", {}))
        "Dormir 3 horas":
            $ show_result(do("sleep", {"hours": 3}))
        "Dormir 8 horas":
            $ show_result(do("sleep", {"hours": 8}))
        "Esperar 1 hora":
            $ show_result(do("wait", {"hours": 1}))
        "Trabajar en el almacén":
            $ show_result(do("activity", {"activity": "trabajar"}))
        "Buscar agua":
            $ show_result(do("activity", {"activity": "buscar_agua"}))
        "Bañarse":
            $ show_result(do("activity", {"activity": "banarse"}))
        "Pedir comida":
            $ show_result(do("activity", {"activity": "pedir_comida"}))
        "Caminar":
            $ show_result(do("activity", {"activity": "caminar"}))
        "Estudiar":
            $ show_result(do("activity", {"activity": "estudiar"}))
        "Entrenar":
            $ show_result(do("activity", {"activity": "entrenar"}))
        "Comprar (chipa ×3)":
            $ show_result(do("buy", {"item": "chipa", "qty": 3}))
        "Visitar a Juana":
            $ show_result(do("visit", {"npc": "juana"}))
        "Visitar a Celia":
            $ show_result(do("visit", {"npc": "celia"}))
        "Visitar a Aurora":
            $ show_result(do("visit", {"npc": "aurora"}))
        "Visitar a Aurelio":
            $ show_result(do("visit", {"npc": "aurelio"}))
        "Visitar a don Ramón":
            $ show_result(do("visit", {"npc": "ramon"}))
        "Visitar al padre Ignacio":
            $ show_result(do("visit", {"npc": "padre_ignacio"}))
        "Visitar a doña Mercedes":
            $ show_result(do("visit", {"npc": "dona_mercedes"}))
        "Ver inventario":
            $ api_client.load_inventory(game_id, "inv")
            $ r = api_client.wait_result("inv", 10.0)
            if r and not r.get("_error"):
                python:
                    for i in r["items"]:
                        renpy.say(narrador, f"{i['name']} ×{i['qty']}")
            else:
                "No se pudo cargar el inventario."
        "Ver personajes":
            $ api_client.load_npcs(game_id, "npcs")
            $ r = api_client.wait_result("npcs", 10.0)
            if r and not r.get("_error"):
                python:
                    for p in r["npcs"]:
                        renpy.say(narrador, f"{p['name']}: {p['location_label']} · {p['affection_label']}")
            else:
                "No se pudo cargar el elenco."
        "Ver registro":
            $ api_client.load_log(game_id, "log")
            $ r = api_client.wait_result("log", 10.0)
            if r and not r.get("_error"):
                python:
                    for e in (r.get("entries") or [])[-8:]:
                        renpy.say(narrador, f"[{e.get('kind')}] {e.get('title', '')} {e.get('message', '')}")
            else:
                "No se pudo cargar el registro."
        "Salir":
            return

    $ check_pending()
    if pending_scene:
        jump scene_pending

    jump game_loop


label scene_pending:
    show screen hud
    $ ev = pending_scene
    $ show_location_bg()
    $ title = ev.get("title", "Escena")
    $ text = ev.get("text", "")
    $ choices = ev.get("choices", [])
    $ cost = ev.get("time_cost", 0)

    "[title]"
    "[text]"
    if cost:
        "(Esta escena te va a costar [cost] minutos.)"

    if not choices:
        $ resolve(None)
        jump game_loop

    $ labels = [c["text"] for c in choices]
    $ ids = [c["id"] for c in choices]
    $ idx = renpy.display_menu(list(zip(labels, range(len(labels)))))
    $ chosen_id = ids[idx]
    $ res = resolve(chosen_id)
    if res and res.get("_error"):
        "No se pudo resolver la escena."
    else:
        "Decisión tomada."

    $ check_pending()
    if pending_scene:
        jump scene_pending

    jump game_loop

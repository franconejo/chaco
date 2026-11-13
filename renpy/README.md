# Chaco — cliente Ren'Py (Fase 3)

Novela visual de vida cotidiana durante la Guerra del Chaco (1932–1935).
Este directorio es el **proyecto Ren'Py** que consume la misma API que el
cliente web. El motor (`engine/`) y el backend (`api/`) siguen siendo la única
autoridad: acá sólo se pinta.

## Requisitos

- **Ren'Py 8.5.3** instalado en `C:\renpy` (descargado de https://www.renpy.org/).
  Si lo instalás en otra ruta, ajustá los comandos de abajo.
- El backend corriendo: `docker compose up -d` (API en `http://localhost:8010`).
- Python 3.12 (sólo para los tests del motor, no para Ren'Py).

## Cómo correr

1. Instalá Ren'Py 8.5.3 en `C:\renpy`.
2. Lanzá el juego desde la terminal:
   ```
   C:\renpy\renpy.exe C:\visualnovel\renpy
   ```
   O abrí el Ren'Py Launcher, agregá `C:\visualnovel\renpy` como proyecto y
   lanzalo desde ahí.
3. En la pantalla inicial elegí "Nueva partida" o "Cargar partida por id".
4. Por defecto la API se asume en `http://127.0.0.1:8010`. Si tu backend está
   en otra URL, editá `game/api_client.py` → `API_BASE`.

## Validación

El puente se probó contra la API real (crear partida, comer, etc.) usando el
Python embebido de Ren'Py (`C:\renpy\lib\py3-windows-x86_64\python.exe`) y
funciona correctamente. El lint de Ren'Py (`renpy.exe <proyecto> lint`) pasa
sin errores.

## Estructura

```
renpy/
├── game/
│   ├── script.rpy       # Flujo principal y bucle del día
│   ├── options.rpy      # Configuración de la ventana
│   └── api_client.py    # Puente HTTP (urllib + invoke_in_thread)
└── README.md
```

## Cómo funciona el puente

- Ren'Py corre en el hilo principal de la UI. Una llamada HTTP bloqueante
  congelaría la ventana, así que cada operación de red se ejecuta con
  `renpy.invoke_in_thread` y el resultado se deposita en un contenedor
  compartido (`_results`) que el hilo principal lee con `wait_result`.
- Toda acción envía un `Idempotency-Key` (UUID) para que un reintento tras
  un corte de red no cobre PA dos veces.
- El estado de la partida vive en el backend; Ren'Py sólo lo muestra y envía
  acciones. `rollback_enabled = False` porque el estado es del servidor.

## Limitaciones conocidas (Fase 3)

- No hay retratos ni imágenes todavía: sólo texto y el HUD mínimo.
- El HUD es una `screen` simple; el diseño visual completo queda para Fase 4.
- Sin guardado local: la partida se identifica por su `game_id` (copialo para
  retomarla). El guardado/carga completo es Fase 5.
- Probado conceptualmente contra la API; requiere Ren'Py instalado para validar
  la ejecución real (no hay Ren'Py en este entorno de desarrollo).

## Hoja de ruta

| Fase | Alcance |
|---|---|
| 3 ✅ (estructura) | Puente Ren'Py, bucle del día, escenas pendientes, HUD mínimo |
| 4 | Retratos, imágenes, elenco definitivo, rutas, finales |
| 5 | Guardado/carga, dificultad, i18n, accesibilidad |

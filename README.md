# Chaco — motor de simulación

Novela visual de vida cotidiana durante la Guerra del Chaco (1932–1935).
El pueblo es Ybycuí, Paraguarí: lejos del frente chaqueño, pero la guerra
se siente igual (faltan hombres, suben los precios, llegan cartas).
Este repositorio contiene el **motor determinista** y la **API**; los clientes
(web y Ren'Py) llegan en fases posteriores.

## Arquitectura

```
clientes (web / Ren'Py)  →  API FastAPI  →  engine/ (Python puro)  →  PostgreSQL
```

- `engine/`: reglas del juego, sin HTTP ni SQL. Se testea con pytest en frío.
- `api/`: orquesta el motor, persiste el snapshot y expone REST.
- `data/`: contenido puro (objetos, lugares, actividades, elenco, acontecimientos).
  Se reescribe sin tocar las reglas.
- `web/`: cliente web (HUD, estado, calendario, mapa del pueblo).
- `renpy/`: cliente Ren'Py (ventana propia, consume la misma API).
- El estado de una partida vive en `games.state` (JSONB); `action_log` guarda
  las acciones idempotentes.

## Requisitos

- Docker (Postgres 16 + API) y Python 3.12 para correr los tests localmente.

## Puesta en marcha

```powershell
docker compose up -d --build
Start-Process http://localhost:8010/docs
```

Tests y lint del motor (no necesitan base de datos):

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
.\.venv\Scripts\python.exe -m pytest
.\.venv\Scripts\python.exe -m ruff check .
```

Simulación headless de varios días (mira números, no es un test):

```powershell
.\.venv\Scripts\python.exe tools\demo_dia.py --dias 8 --seed 7
```

## Cliente web (Fase 2)

El cliente vive en `web/` y se sirve desde la misma API en `/` (sin CORS, sin
build). Abrir `http://localhost:8010/` en el navegador.

Funcionalidades:
- Crear/cargar partida por id; botón "Demo" crea una con semilla 7.
- HUD: reloj, PA, necesidades, atributos, identidad, dinero, lugar, quién está
  presente.
- Acciones rápidas (comer, beber, dormir, esperar, buscar agua, bañarse,
  descansar, caminar, entrenar, estudiar) y listado de actividades con motivo
  de bloqueo.
- Inventario con vencimiento y peso; almacén con precios dinámicos.
- Personajes del pueblo con etiquetas de relación y visita con un clic.
- Escenas pendientes en modal con opciones; la elección encadena la siguiente.
- Registro del día (cierres de jornada, eventos, decisiones).
- Toast con el resultado de cada acción.

Los mensajes de las acciones se muestran como notificación; el servidor sigue
siendo la única autoridad.

| Método | Ruta | Qué hace |
|---|---|---|
| `POST` | `/games` | Crea una partida (`seed`, `start_date`) |
| `GET` | `/games/{id}` | Estado actual: reloj, PA, necesidades, inventario, quién está presente |
| `GET` | `/games/{id}/activities` | Actividades con disponibilidad y motivo del bloqueo |
| `GET` | `/games/{id}/inventory` | Inventario con cantidades, peso y vencimiento |
| `GET` | `/games/{id}/npcs` | Elenco: dónde está cada uno y nivel de relación |
| `GET` | `/games/{id}/shop` | Catálogo del almacén con precios (`price_multiplier`, `effective_price`) |
| `GET` | `/games/{id}/pending` | Escenas pendientes de decisión |
| `POST` | `/games/{id}/actions` | Ejecuta `sleep` / `eat` / `drink` / `wait` / `activity` / `buy` / `visit` |
| `POST` | `/games/{id}/pending/{uid}/resolve` | Elige una opción de la escena pendiente |
| `GET` | `/games/{id}/log` | Últimos cierres de jornada y escenas |

`POST /actions` acepta el header `Idempotency-Key`: repetir la misma clave
devuelve el resultado original sin volver a cobrar PA (importante para Ren'Py,
donde un reintento tras un corte de red no debe penalizar al jugador).

### Escenas que interrumpen

Una escena con opciones **detiene el día**. Mientras haya algo pendiente,
cualquier acción devuelve `400` con `code: "escena_pendiente"`. El flujo del
cliente es siempre el mismo:

1. `POST /actions` → si falla con `escena_pendiente`, la escena ya quedó guardada.
2. `GET /pending` → leer `uid`, texto y opciones.
3. `POST /pending/{uid}/resolve` → aplicar la elección (y recibir la escena
   siguiente si el evento encadena).

Las escenas se evalúan **al llegar** al lugar de la actividad y **al terminar**
el paso del tiempo. Sin la primera comprobación, una jornada de 5 horas se
comería la ventana horaria del acontecimiento y éste nunca ocurriría.

Ejemplo rápido:

```powershell
$base = 'http://localhost:8010'
$game = Invoke-RestMethod -Method Post "$base/games" -ContentType 'application/json' `
  -Body '{"seed":7,"start_date":"1932-09-01"}'
$id = $game.game_id

Invoke-RestMethod -Method Post "$base/games/$id/actions" -ContentType 'application/json' `
  -Body '{"type":"activity","activity":"trabajar"}' `
  -Headers @{ 'Idempotency-Key' = 'd1-trabajo' }

Invoke-RestMethod "$base/games/$id/inventory"
Invoke-RestMethod "$base/games/$id/pending"
```

## Reglas implementadas

### Reloj y energía (Fase 0)

- Jornada de 05:00 a 05:00; períodos mañana (7 PA), tarde (7 PA), noche (10 PA).
- 1 hora = 1 PA; tope de acumulación 24; **sin recarga automática** de PA.
- Recuperación: dormir ×2, comer ×3, beber ×3 (por PA invertido), siempre con
  tope 24. Topes anti-abuso: 3 comidas por jornada y sed real (hidratación
  menor a 95) para beber.
- Si te quedás sin PA, dormir/comer/beber siguen disponibles (neto positivo):
  nunca te trabás, pero el resto de las acciones exige PA suficiente.
- Quedarte en 0 PA tiene consecuencias: salud, hidratación, nutrición e higiene
  bajan; la fatiga sube; fuerza, resistencia, conocimiento y reputación caen;
  la sospecha sube, la credibilidad baja y te roban dinero. Se aplica una sola
  vez por episodio de PA=0; dormir/comer/beber lo resetean. Además perdés 1
  hora y recuperás 1 PA, así comer o dormir no sale gratis.
- Sueño: 0/1/2 horas castigan salud y fatiga (tabla del GDD); 3 horas es el
  mínimo sin penalización; la deuda de sueño se acumula entre jornadas.
- Necesidades con desgaste por hora, fatiga, y deriva lenta de salud.

### Actividades (Fase 1)

| Actividad | Horas | Dónde | Para qué |
|---|---|---|---|
| Trabajar en el almacén | 5 | almacén | 3 pesos, resistencia y reputación |
| Estudiar | 2 | casa | conocimiento |
| Caminar por el pueblo | 1 | plaza | resistencia y fuerza |
| Entrenar | 2 | plaza | fuerza y resistencia (cansa más) |
| Descansar | 1 | casa | baja la fatiga |
| Bañarse | 1 | casa | higiene (consume 1 agua) |
| Buscar agua | 1 | pozo | +2 aguas |
| Comprar | 1 | almacén | abre el catálogo de la tienda |
| Visitar a alguien | 2 | donde esté el personaje | relación |

- La restricción horaria es sobre la hora de **inicio**; una actividad puede
  terminar en el período siguiente.
- Las actividades mueven al personaje al lugar: no hay sistema de traslados.
- Cada actividad tiene un `exertion` que multiplica el desgaste de necesidades.

### Inventario (Fase 1)

- Se guarda por **pilas** (`Stack`) con `expires_day`: lo comprado en días
  distintos vence en días distintos y no se fusiona.
- Al cerrar la jornada lo vencido se descarta y queda anotado en el registro.
- Al consumir se usa primero lo que vence antes.
- Precio, peso cuentan: el inventario informa el peso total.

### Elenco y relaciones (Fase 1)

- Cada personaje tiene rutina por franja horaria. Si está en su casa, **no se
  puede visitar** (las casas ajenas no son accesibles).
- Relación con cuatro ejes: afecto, confianza, familiaridad e interés, expuestos
  como etiquetas cualitativas (`distante` … `íntima`), no como números.
- Visitar da ganancia **decreciente**: cuanto más te conoce, menos suma.

### Acontecimientos (Fase 1)

- Condiciones declarativas: día mínimo/máximo, período, lugar, banderas,
  eventos previos, rangos de necesidad, probabilidad y cooldown.
- Un solo acontecimiento por avance de tiempo, ordenado por prioridad.
- Los que tienen opciones quedan pendientes; los que no, se resuelven solos.
- Contenido actual: `aviso_movilizacion`, `juana_secreto` (encadenado),
  `carta_del_frente`, `rumor_de_boqueron`, `desmayo_por_sed`, `hambre_extrema`,
  `charla_de_esquina`.

Las decisiones de diseño y lo que queda abierto están en
`docs/DECISIONES.md`.

## Deploy

Ver `deploy/README.md` para instrucciones completas. Resumen:

- Subdominio: `demo.eibrapp.com.py`
- Reverse proxy: Caddy (SSL automático)
- Contenedores: Docker Compose (api + db)
- Puerto interno: 8010 (solo localhost, Caddy lo expone)

```bash
docker compose -f docker-compose.yml -f deploy/docker-compose.prod.yml up -d --build
```

| Fase | Alcance |
|---|---|
| 0 ✅ | Reloj, PA, necesidades, API, tests |
| 1 ✅ | Actividades, inventario con vencimiento, tienda, NPC con rutinas, motor de eventos |
| 1.5 ✅ | Cadenas de eventos (identidad, barrio, escasez, afectos), opciones condicionales, tiempo de escena, ausencias, precios dinámicos |
| 2 ✅ | Cliente web (HUD, estado, calendario, mapa del pueblo) |
| 3 ✅ | Puente Ren'Py (estructura, bucle del día, escenas pendientes, HUD mínimo) |
| 4 ✅ | Contenido: retratos, elenco definitivo (11 NPC), línea histórica (Boquerón), rutas, finales |
| 5 | Guardado/carga, dificultad, i18n (es-PY + guaraní), accesibilidad |

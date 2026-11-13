# Decisiones de diseño y cuestiones abiertas

## 1. Economía de PA: modelo literal del GDD

**Decisión:** se implementa tal cual el GDD (§6 y §7): 1 hora = 1 PA, la
jornada aporta 24 PA, tope 24, y los PA **no se recargan solos** al cambiar de
período ni de día. Sólo se recuperan durmiendo (×2), comiendo (×3) y bebiendo
(×3) por PA invertido.

**Consecuencia aceptada:** como el tope (24) es igual al presupuesto de horas de
la jornada, en la práctica los PA dejan de ser un limitante en cuanto el
personaje duerme y come con regularidad. El **reloj** pasa a ser el límite real.
Es una decisión consciente del usuario, no un olvido.

**Antídotos contra la explotación, dentro del modelo literal:**

- Máximo 3 comidas por jornada.
- Beber sólo rinde con sed real (hidratación menor a 95).
- Ambos consumen 1 PA y hacen avanzar 1 hora: el tiempo nunca es gratis.

**Callejón sin salida corregido:** dormir, comer y beber recuperan más PA de los
que cuestan (×2, ×3, ×3). Por eso, si el personaje se queda en 0 PA, igual
puede dormir/comer/beber: el neto es positivo y la acción se aplica de una vez.
Las demás acciones (esperar, actividades, comprar, visitar) siguen exigiendo
PA suficiente y fallan con `sin_pa` si no lo hay. Así el jugador nunca queda
trabado, pero los PA siguen importando para todo lo demás.

**Si más adelante se quiere que los PA vuelvan a morder:** la vía menos
invasiva es bajar el PA inicial de la jornada (por ejemplo 10–12) sin tocar las
fórmulas de recuperación. Está aislado en `engine/energy.py`.

## 2. Reparto de responsabilidades entre clientes

**Decisión:** el servidor es la única autoridad. Ni el cliente web ni Ren'Py
calculan reglas: envían acciones y pintan la respuesta.

**Ren'Py:** corre en ventana propia (desktop) y consume la misma API. Las
escenas cinematográficas y los diálogos viven ahí; el HUD de simulación vive en
el cliente web. Se descartó embeber el build web de Ren'Py por la complejidad de
compartir estado entre dos runtimes.

**Riesgo:** Ren'Py bloquea el frame si se hace HTTP desde el hilo principal. El
puente (Fase 3) usará `renpy.invoke_in_thread` o `renpy.fetch`, con pantalla de
espera y `Idempotency-Key` en cada acción.

## 3. Determinismo

Toda tirada pasa por `engine/rng.py`, que deriva un `Random` de
`(semilla, etiqueta)`. Repetir una partida con la misma semilla y las mismas
acciones da el mismo resultado, aunque cambie el orden interno de los sistemas.
Esto hace testeables los eventos y permite el guardado como snapshot.

## 4. Moneda: peso paraguayo

**Decisión:** la moneda del juego es el **peso paraguayo**, escrito como `$`.

El guaraní no existe hasta 1943, once años después del inicio del juego: usarlo
en 1932 sería un error histórico. El sueldo de referencia es de 3 pesos por
jornada en el almacén, y los precios del catálogo están calibrados contra ese
sueldo (agua 1, mandioca 2, carne seca 3, quinina 4).

**Consecuencia:** una jornada de trabajo paga una canasta básica diaria. La
economía aprieta si el jugador deja de trabajar para cuidarse, no por inflación.

## 5. Persistencia

El estado completo vive en `games.state` (JSONB) con un contador de `version`.
Cuando el contenido crezca, NPC e inventario podrán normalizarse en tablas
propias, pero el snapshot sigue siendo la fuente de verdad para cargar partida.
La creación de tablas es directa (`create_all`); **Alembic sigue pendiente**:
entra cuando haya una base con datos que migrar (antes de la Fase 4).

`POST /actions` guarda un `ActionLog` con `Idempotency-Key`, así un reintento
del cliente no cobra PA dos veces.

## 6. Movimiento automático de lugar

**Decisión:** no hay sistema de traslados. Al iniciar una actividad el
protagonista aparece en el lugar correspondiente (comprar → almacén, buscar agua
→ pozo, visitar → donde esté el personaje).

**Motivo:** el GDD no define costos de desplazamiento y agregarlos obligaría a
un grafo de caminos y a un HUD de mapa. Con 24 PA por jornada, un traslado de 1
PA por viaje se comería el margen de decisiones sin aportar tensión.

**Costo aceptado:** el espacio es escenográfico; la distancia no es un recurso.

## 7. Los acontecimientos se evalúan también al empezar una acción

**Decisión:** `perform` llama a `_begin` antes de gastar PA: mueve al personaje,
evalúa eventos y, si alguno abre escena, corta la acción con
`escena_pendiente`.

**Motivo:** evaluar sólo al terminar el paso del tiempo hace que la ventana
horaria del evento se pierda. Ejemplo real: `aviso_movilizacion` ocurre el día 4
de mañana en el almacén; si el jugador empieza a trabajar a las 08:00, la
jornada de 5 horas lo deja a las 13:00 y el evento nunca se dispara.

**Costo aceptado:** una acción puede fallar "antes de empezar" y no consumir
nada. Es correcto: la escena interrumpe, no la acción.

## 8. Rollback de la API cuando hay escena pendiente

**Bug encontrado y corregido:** cuando `perform` lanzaba `escena_pendiente`, la
API hacía `db.rollback()`. El evento ya se había disparado en memoria, así que
el cliente recibía un 400 pidiéndole resolver una escena que la base nunca
guardó.

**Regla actual:** si el error deja `estado.pending` no vacío, se **guarda el
snapshot** antes de devolver el 400; si no, se hace rollback normal.

## 9. Elenco provisorio (Fase 1)

El GDD (§22) deja el reparto pendiente. Para que los sistemas tengan con quién
funcionar se cargó un elenco provisorio en `data/npcs.py`, reemplazable sin
tocar el motor:

| Personaje | Edad | Oficio | Rol |
|---|---|---|---|
| Juana | 20 | Ayudante de almacén | Amiga de la infancia, sabe el secreto |
| Celia | 19 | Costurera | Reservada, ruta lenta |
| Aurora | 18 | Hija del almacenero | Extrovertida, acceso al almacén |
| Aurelio | 17 | Aprendiz de carpintero | Amigo, termina en el frente |
| Don Ramón | 52 | Almacenero | Figura paterna, te cubre |

Las edades están elegidas para que el protagonista (18 reales, 16 declarados)
tenga un grupo etario coherente y para que la movilización golpee a los varones
jóvenes del barrio.

## 10. Salud en cero no mata (todavía)

**Estado:** con salud en 0 el personaje sigue actuando; sólo se acumulan
penalizaciones. No hay muerte, internación ni escena de hospital.

**Motivo:** el sistema de consecuencias graves (enfermedad, invalidez, muerte)
necesita la línea narrativa de la Fase 4 para tener sentido y no castigar al
jugador por explorar.

**Pendiente:** definir en Fase 4 si la salud en 0 lleva a una escena de
convalecencia (pierde días, no la partida) o a un final. Recomendación: la
primera, coherente con un juego de vida cotidiana.

## 11. Observación de balance (Fase 1)

Con una rutina completa —comer, beber, trabajar, buscar agua, visitar, dormir
8 horas— los PA quedan fijados en 24 y la salud se mantiene en 100
indefinidamente. Verificado con `tools/demo_dia.py` durante 8 días seguidos.

**Lectura:** la economía de necesidades no genera tensión por sí sola; sólo
muerde si el jugador no come, no bebe o no duerme. Eso es coherente con el
modelo literal de PA, pero significa que **la tensión tiene que venir del
conflicto bélico y de la identidad falsa**, no de la supervivencia diaria.

**Implicancia para el contenido:** los eventos no pueden ser decorativos. Tienen
que quitar tiempo, cerrar lugares, llevarse personajes o forzar elecciones con
costo. Los primeros (`aviso_movilizacion`, `juana_secreto`) ya funcionan así.

## 12. Contenido de la Fase 1.5

### 12.1 Opciones condicionales

Las escenas pueden ofrecer opciones que sólo aparecen si el jugador se ganó el
derecho a elegirlas: `Choice.requires_flags` y `Choice.requires_items`. El
cliente recibe la lista filtrada por `pending_view`. Si el jugador intenta
resolver una opción bloqueada, la API devuelve `opcion_no_disponible`.

Esto permite escenas donde la "salida fácil" existe sólo para quien guardó un
pañuelo, quien se ganó la confianza de don Ramón, etc. Es la principal fuente
de variación entre partidas.

### 12.2 Escenas que cuestan tiempo

`EventDef.time_cost` (minutos) se cobra al resolver la escena (con opciones) o
al dispararse (sin opciones), con `advance(..., queue=False)` para no encadenar
escenas dentro de una escena. Un velorio de 3 horas o una mañana en el cuartel
se descuentan del reloj y pueden cerrar la jornada.

### 12.3 Condiciones nuevas

`stat_value` ahora resuelve `npc:<id>:<campo>` (relación con un personaje) y
`days`/`closed_days` (días transcurridos). `EventDef.any_flags` (alguna) se
suma a `requires_flags` (todas) y `forbids_flags` (ninguna). Esto permite
cadenas que dependen de "qué tanto te conoce alguien" o de "si pasó algo".

### 12.4 Ausencias

`NpcDef.away_flag` saca a un personaje del pueblo mientras la bandera esté
activa: `location_of` devuelve `AWAY_LOCATION`, el listado lo marca como
`away` y las visitas fallan con un motivo narrativo. Se usa para Aurelio en el
frente. Es la forma de modelar "el barrio se vacía" sin tocar las rutinas.

### 12.5 Precios dinámicos

El catálogo trae un precio de referencia; la coyuntura lo mueve con un
multiplicador en `engine/prices.py`, activado por banderas (`precios_altos`,
`sin_provisiones`). La tienda expone `price_multiplier` y `effective_price`.
La escasez es una bandera, no una curva: determinista y fácil de debuguear.

### 12.6 Prioridades y concurrencia

`MAX_FIRES_PER_TICK = 1`: un solo acontecimiento por avance de tiempo, ordenado
por prioridad. Los eventos de salud (`fiebre`, `hambre_extrema`) tienen
prioridad 6 y cooldown 5; los de línea histórica tienen 5. Así un jugador
enfermo puede perderse una noticia, lo cual es coherente: la supervivencia
empuja la narrativa. Los eventos de emergencia (`desmayo_por_sed`) mantienen
prioridad 9.

### 12.7 Castigo por quedarse sin PA

Cuando el PA llega a 0 (por gastar o por empezar ahí), se aplica una sola vez
por episodio:

- Salud −8, hidratación −15, nutrición −15, higiene −20.
- Fatiga +20.
- Fuerza −2, resistencia −2, conocimiento −1, reputación −3.
- Sospecha +5, credibilidad −5.
- Te roban hasta 3 pesos.
- Perdés 1 hora y recuperás 1 PA (para que comer/dormir no sea gratis).

Dormir, comer o beber resetean el episodio (PA vuelve a >0). El castigo se
anota en el registro (`kind: "collapse"`) y se muestra en el resultado de la
acción o en el error `sin_pa`. La intención es que quedarse sin PA sea un
evento con consecuencias, no un simple bloqueo.

## 14. Localización: Ybycuí, Paraguarí

**Decisión:** el pueblo del juego es **Ybycuí**, en el departamento de
Paraguarí, a ~100 km al sureste de Asunción. Lejos del frente chaqueño
(~700 km), pero la guerra se siente igual: faltan hombres, suben los precios,
llegan cartas del frente.

**Motivo:** Ybycuí tiene identidad propia — las ruinas de la Fundición de
Ybycuí (La Rosada, de la época de Carlos Antonio López), el Salto Mbocaruzú,
el río Ybycuí, la iglesia — y está lo suficientemente lejos del Chaco como
para que la guerra sea contexto, no escenario permanente (GDD §1).

**Mapa:** `data/map.py` define 23 nodos (zonas: barrio, centro, afueras) y
15 conexiones. El endpoint `GET /map` lo expone y el cliente web lo dibuja
como SVG. El cliente Ren'Py puede usarlo para una pantalla de mapa.

## 13. Cuestiones todavía abiertas (heredadas del GDD §22)
|---|---|
| Fecha inicial y final exactas | Provisorio: `1932-09-01` como día 1, configurable por API |
| Año de nacimiento falsificado | Pendiente (depende del elenco) |
| PA inicial de partida | 24, según modelo literal |
| Elenco definitivo | Provisorio en `data/npcs.py` (Fase 4) |
| Localización del pueblo | Pendiente: hoy es un pueblo genérico del interior |
| Economía y precios | Calibrados contra un sueldo de 3 pesos/jornada |
| Reglas históricas de reclutamiento | Requiere investigación (Fase 4) |
| Consecuencia de salud en 0 | Pendiente: convalecencia o final (Fase 4) |
| Cantidad de rutas y finales | Pendiente de aprobación de contenido |

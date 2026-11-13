const API = ""; // mismo origen (servido por la API)
let gameId = null;
let state = null;
let actionCounter = 0;
let pendingHoursAction = null;
let lang = localStorage.getItem("lang") || "es";
let translations = {};
let highContrast = localStorage.getItem("hc") === "1";

const $ = (id) => document.getElementById(id);
const $$ = (sel) => document.querySelectorAll(sel);

function toast(msg, error = false) {
  const t = $("toast");
  t.textContent = msg;
  t.classList.toggle("error", error);
  t.classList.remove("hidden");
  clearTimeout(toast._t);
  toast._t = setTimeout(() => t.classList.add("hidden"), 3200);
}

async function api(path, opts = {}) {
  const { headers: optHeaders, ...rest } = opts;
  const res = await fetch(API + path, {
    headers: { "Content-Type": "application/json", ...(optHeaders || {}) },
    ...rest,
  });
  const text = await res.text();
  let data = null;
  try { data = text ? JSON.parse(text) : null; } catch { data = text; }
  if (!res.ok) {
    const code = (data && data.detail && data.detail.code) || res.status;
    const msg = (data && data.detail && data.detail.message) || res.statusText;
    const err = new Error(msg);
    err.code = code;
    err.data = data;
    throw err;
  }
  return data;
}

function idempotencyKey(label) {
  actionCounter += 1;
  return `${label}-${actionCounter}-${Date.now()}`;
}

// ---------- i18n ----------

async function loadTranslations() {
  try {
    const res = await fetch(`/i18n/${lang}.json`);
    if (res.ok) translations = await res.json();
  } catch (e) { translations = {}; }
}

function t(key, fallback) {
  return translations[key] || fallback || key;
}

function applyTranslations() {
  document.querySelectorAll("[data-i18n]").forEach(el => {
    const key = el.dataset.i18n;
    const val = t(key, el.textContent);
    if (el.tagName === "INPUT") el.placeholder = val;
    else el.textContent = val;
  });
}

// ---------- Partidas ----------

async function createGame(seed = 7) {
  const diff = parseInt($("diff-select").value, 10) || 1;
  try {
    const g = await api("/games", {
      method: "POST",
      body: JSON.stringify({ seed, start_date: "1932-09-01", difficulty: diff }),
    });
    gameId = g.game_id;
    $("game-id-input").value = gameId;
    await refresh();
    toast("Partida creada.");
  } catch (e) { toast(e.message, true); }
}

async function loadGame(id) {
  if (!id) return;
  gameId = id;
  try { await refresh(); toast("Partida cargada."); }
  catch (e) { toast(e.message, true); gameId = null; }
}

async function refresh() {
  if (!gameId) return;
  const g = await api(`/games/${gameId}`);
  state = g;
  render(g);
  renderMap(g);
  if (g.flags && g.flags.includes("muerto")) {
    toast("El cuerpo no aguant? m?s. Fin de la partida.", true);
  }
  try {
    const p = await api(`/games/${gameId}/pending`);
    if (p.events && p.events.length) showScene(p.events[0]);
    else hideScene();
  } catch (e) { /* ignore */ }
}

// ---------- Render ----------

const NEED_LABELS = {
  health: "Salud", hydration: "Hidratación", nutrition: "Nutrición",
  fatigue: "Fatiga", hygiene: "Higiene",
};
const ATTR_LABELS = {
  strength: "Fuerza", stamina: "Resistencia", complexion: "Complexión",
  knowledge: "Conocimiento", reputation: "Reputación",
};

function barHtml(label, value, max = 100, invert = false) {
  const pct = Math.max(0, Math.min(100, (value / max) * 100));
  const color = invert
    ? (pct > 70 ? "var(--danger)" : "var(--bar-fill)")
    : (pct < 30 ? "var(--danger)" : "var(--bar-fill)");
  return `<div class="bar-line">
    <span class="label">${label}</span>
    <div class="bar"><div class="fill" style="width:${pct}%;background:${color}"></div></div>
    <span class="val">${typeof value === "number" ? value.toFixed(1) : value}</span>
  </div>`;
}

function render(g) {
  const c = g.clock;
  document.querySelector(".clock-time").textContent = `${String(c.hour).padStart(2,"0")}:${String(c.minute).padStart(2,"0")}`;
  document.querySelector(".clock-date").textContent = `${c.date_label} · ${c.weekday_label}`;
  document.querySelector(".clock-period").textContent = c.period_label;
  $("clock-chip").textContent = `${c.time_label} · día ${c.day_index}`;
  $("closed-days").textContent = g.closed_days;
  $("location-label").textContent = g.location_label;
  $("pa-text").textContent = `${g.pa} / ${g.pa_max}`;
  $("pa-fill").style.width = `${(g.pa / g.pa_max) * 100}%`;

  $("needs").innerHTML = Object.keys(NEED_LABELS).map(k =>
    barHtml(NEED_LABELS[k], g.player[k], 100, k === "fatigue")
  ).join("");
  $("attrs").innerHTML = Object.keys(ATTR_LABELS).map(k =>
    barHtml(ATTR_LABELS[k], g.player[k], 100)
  ).join("");

  $("suspicion").textContent = g.identity.suspicion.toFixed(1);
  $("credibility").textContent = g.identity.credibility.toFixed(1);
  $("money").textContent = `$${g.player.money}`;

  const here = g.npcs_here || [];
  $("npcs-here").innerHTML = here.length
    ? here.map(n => `<span class="npc-chip" data-npc="${n.id}" title="${n.occupation}">${n.name} · ${n.affection_label}</span>`).join("")
    : "<span class='muted'>Nadie.</span>";
  $$("[data-npc]").forEach(el => el.addEventListener("click", () => visitNpc(el.dataset.npc)));

  renderActivities(g);
  renderInventory(g);
  $("weight").textContent = "—";
  loadShop();
  loadNpcs();
  loadLog();
}

async function renderMap(g) {
  if (!gameId) return;
  try {
    const m = await api("/map");
    const svg = document.createElementNS("http://www.w3.org/2000/svg", "svg");
    svg.setAttribute("class", "map-svg");
    svg.setAttribute("viewBox", "0 0 100 100");
    svg.setAttribute("preserveAspectRatio", "xMidYMid meet");

    (m.edges || []).forEach(e => {
      const a = (m.nodes || []).find(n => n.id === e.a);
      const b = (m.nodes || []).find(n => n.id === e.b);
      if (!a || !b) return;
      const line = document.createElementNS("http://www.w3.org/2000/svg", "line");
      line.setAttribute("x1", a.x); line.setAttribute("y1", a.y);
      line.setAttribute("x2", b.x); line.setAttribute("y2", b.y);
      line.setAttribute("class", "map-edge");
      svg.appendChild(line);
    });

    (m.nodes || []).forEach(n => {
      const isCurrent = g && g.location === n.id;
      const grp = document.createElementNS("http://www.w3.org/2000/svg", "g");
      grp.setAttribute("class", "map-node" + (n.public ? " public" : "") + (isCurrent ? " current" : ""));

      const circle = document.createElementNS("http://www.w3.org/2000/svg", "circle");
      circle.setAttribute("cx", n.x); circle.setAttribute("cy", n.y);
      circle.setAttribute("r", isCurrent ? 4 : (n.public ? 3 : 2));
      grp.appendChild(circle);

      const text = document.createElementNS("http://www.w3.org/2000/svg", "text");
      text.setAttribute("x", n.x); text.setAttribute("y", n.y + 5);
      text.setAttribute("opacity", 0);
      text.textContent = n.label;
      grp.appendChild(text);

      circle.addEventListener("mouseenter", () => {
        text.setAttribute("opacity", 1);
        // Mover al frente para que el label sobresalga
        svg.appendChild(grp);
      });
      circle.addEventListener("mouseleave", () => { if (!isCurrent) text.setAttribute("opacity", 0); });
      if (isCurrent) text.setAttribute("opacity", 1);

      svg.appendChild(grp);
    });

    const container = $("map");
    container.innerHTML = "";
    container.appendChild(svg);
  } catch (e) { /* ignore */ }
}

async function renderActivities(g) {
  try {
    const a = await api(`/games/${gameId}/activities`);
    $("activities").innerHTML = a.activities.map(act => {
      const disabled = !act.available;
      return `<div class="act-card ${disabled ? "disabled" : ""}">
        <div class="info">
          <div class="name">${act.name} <span class="meta">(${act.duration_hours}h)</span></div>
          <div class="desc">${act.description}</div>
          ${act.reason ? `<div class="reason">${act.reason}</div>` : ""}
        </div>
        <button class="btn btn-small ${disabled ? "" : "btn-primary"}"
                data-act="${act.id}" ${disabled ? "disabled" : ""}>Hacer</button>
      </div>`;
    }).join("");
    $$("[data-act]").forEach(el => el.addEventListener("click", () => doActivity(el.dataset.act)));
  } catch (e) { toast(e.message, true); }
}

async function renderInventory(g) {
  try {
    const inv = await api(`/games/${gameId}/inventory`);
    $("weight").textContent = `${inv.total_weight} kg`;
    $("inventory").innerHTML = inv.items.length
      ? inv.items.map(i => `<div class="inv-row">
          <span class="name">${i.name}</span>
          <span class="qty">×${i.qty}${i.expires_day != null ? ` (vence d${i.expires_day})` : ""}</span>
        </div>`).join("")
      : "<span class='muted'>Vacío.</span>";
  } catch (e) { toast(e.message, true); }
}

async function loadShop() {
  if (!gameId) return;
  try {
    const sh = await api(`/games/${gameId}/shop`);
    $("shop-mult").textContent = sh.price_multiplier > 1 ? `×${sh.price_multiplier}` : "";
    $("shop").innerHTML = sh.items.map(i => `<div class="shop-row">
      <span class="name">${i.name}</span>
      <span class="price">$${i.effective_price}</span>
      <button class="btn btn-small" data-buy="${i.id}">Comprar</button>
    </div>`).join("");
    $$("[data-buy]").forEach(el => el.addEventListener("click", () => buyItem(el.dataset.buy)));
  } catch (e) { toast(e.message, true); }
}

async function loadNpcs() {
  if (!gameId) return;
  try {
    const n = await api(`/games/${gameId}/npcs`);
    $("npcs").innerHTML = n.npcs.map(p => {
      const away = p.away ? "away" : "";
      const tag = p.away ? `<span class="away-tag">${p.location_label}</span>` : `<span class="meta">${p.location_label} · ${p.affection_label}</span>`;
      return `<div class="npc-row ${away}">
        <div>
          <div class="name">${p.name} <span class="meta">(${p.age})</span></div>
          <div class="meta">${p.occupation}</div>
        </div>
        <div style="text-align:right">
          ${tag}
          ${!p.away && p.visitable ? `<button class="btn btn-small" data-visit="${p.id}" style="margin-top:4px">Visitar</button>` : ""}
        </div>
      </div>`;
    }).join("");
    $$("[data-visit]").forEach(el => el.addEventListener("click", () => visitNpc(el.dataset.visit)));
  } catch (e) { toast(e.message, true); }
}

async function loadLog() {
  if (!gameId) return;
  try {
    const l = await api(`/games/${gameId}/log`);
    $("log").innerHTML = (l.entries || []).slice().reverse().map(e => {
      const kind = e.kind || "";
      let title = e.title || e.kind || "";
      let text = e.message || e.text || "";
      if (kind === "day_close") title = "Cierre de jornada";
      if (kind === "event") title = `Evento: ${e.title}`;
      if (kind === "event_pending") title = `Escena: ${e.title}`;
      if (kind === "event_choice") title = `Decisión: ${e.title}`;
      return `<div class="log-entry ${kind}">
        <div class="title">${title}</div>
        ${text ? `<div class="text">${text}</div>` : ""}
      </div>`;
    }).join("") || "<span class='muted'>Sin registro.</span>";
  } catch (e) { /* ignore */ }
}

// ---------- Acciones ----------

async function doAction(type, payload = {}, keyLabel = type) {
  if (!gameId) { toast("Creá o cargá una partida primero.", true); return; }
  try {
    const res = await api(`/games/${gameId}/actions`, {
      method: "POST",
      headers: { "Idempotency-Key": idempotencyKey(keyLabel) },
      body: JSON.stringify({ type, ...payload }),
    });
    const msgs = (res.result && res.result.messages) || [];
    if (msgs.length) toast(msgs.join(" "));
    await refresh();
  } catch (e) {
    if (e.code === "escena_pendiente") {
      await refresh();
    } else {
      toast(e.message, true);
    }
  }
}

function doActivity(id) {
  if (id === "comprar") { toast("Usá el almacén de la derecha para comprar."); return; }
  if (id === "visitar") { toast("Elegí un personaje de la lista."); return; }
  doAction("activity", { activity: id }, `act-${id}`);
}

function visitNpc(id) {
  doAction("visit", { npc: id }, `visit-${id}`);
}

async function buyItem(id) {
  const qtyStr = prompt("Cantidad:", "1");
  if (qtyStr === null) return;
  const qty = Math.max(1, Math.min(20, parseInt(qtyStr, 10) || 1));
  doAction("buy", { item: id, qty }, `buy-${id}`);
}

document.addEventListener("click", (e) => {
  const btn = e.target.closest("[data-action]");
  if (!btn) return;
  const a = btn.dataset.action;
  if (a === "eat") doAction("eat", {}, "eat");
  else if (a === "drink") doAction("drink", {}, "drink");
  else if (a === "sleep") openHours("Dormir (horas)", (h) => doAction("sleep", { hours: h }, "sleep"));
  else if (a === "wait") openHours("Esperar (horas)", (h) => doAction("wait", { hours: h }, "wait"));
  else if (a === "buscar_agua") doAction("activity", { activity: "buscar_agua" }, "ba");
  else if (a === "banarse") doAction("activity", { activity: "banarse" }, "bn");
  else if (a === "descansar") doAction("activity", { activity: "descansar" }, "dc");
  else if (a === "caminar") doAction("activity", { activity: "caminar" }, "cm");
  else if (a === "entrenar") doAction("activity", { activity: "entrenar" }, "en");
  else if (a === "estudiar") doAction("activity", { activity: "estudiar" }, "es");
});

// ---------- Escena pendiente ----------

function showScene(ev) {
  $("scene-title").textContent = ev.title;
  $("scene-text").textContent = ev.text;
  $("scene-cost").textContent = ev.time_cost ? `Esta escena te va a costar ${ev.time_cost} minutos.` : "";
  const choices = ev.choices || [];
  $("scene-choices").innerHTML = choices.map(c =>
    `<button class="btn btn-primary" data-choice="${c.id}" data-uid="${ev.uid}">${c.text}</button>`
  ).join("");
  $$("[data-choice]").forEach(b => b.addEventListener("click", () => resolveChoice(b.dataset.uid, b.dataset.choice)));
  $("scene-modal").classList.remove("hidden");
}

function hideScene() { $("scene-modal").classList.add("hidden"); }

async function resolveChoice(uid, choice) {
  if (!gameId) return;
  try {
    const res = await api(`/games/${gameId}/pending/${encodeURIComponent(uid)}/resolve`, {
      method: "POST",
      headers: { "Idempotency-Key": idempotencyKey("resolve") },
      body: JSON.stringify({ choice }),
    });
    toast("Decisión tomada.");
    hideScene();
    await refresh();
  } catch (e) { toast(e.message, true); }
}

// ---------- Modal de horas ----------

function openHours(title, onOk) {
  $("hours-title").textContent = title;
  $("hours-modal").classList.remove("hidden");
  pendingHoursAction = onOk;
}
$("hours-cancel").addEventListener("click", () => {
  $("hours-modal").classList.add("hidden");
  pendingHoursAction = null;
});
$("hours-ok").addEventListener("click", () => {
  const h = parseInt($("hours-input").value, 10) || 1;
  $("hours-modal").classList.add("hidden");
  if (pendingHoursAction) pendingHoursAction(h);
  pendingHoursAction = null;
});

// ---------- Guardado/carga ----------

function saveSlot(slot) {
  if (!gameId) { toast("No hay partida para guardar.", true); return; }
  const slots = JSON.parse(localStorage.getItem("slots") || "{}");
  slots[slot] = gameId;
  localStorage.setItem("slots", JSON.stringify(slots));
  toast(`Partida guardada en slot ${slot}.`);
}

function loadSlot(slot) {
  const slots = JSON.parse(localStorage.getItem("slots") || "{}");
  if (slots[slot]) loadGame(slots[slot]);
  else toast(`Slot ${slot} vacío.`, true);
}

async function exportGame() {
  if (!gameId) { toast("No hay partida.", true); return; }
  try {
    const data = await api(`/games/${gameId}/export`);
    const blob = new Blob([JSON.stringify(data, null, 2)], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url; a.download = `chaco-${gameId}.json`;
    a.click();
    URL.revokeObjectURL(url);
    toast("Partida exportada.");
  } catch (e) { toast(e.message, true); }
}

async function importGame(file) {
  try {
    const text = await file.text();
    const data = JSON.parse(text);
    const g = await api("/games/import", { method: "POST", body: JSON.stringify(data) });
    gameId = g.game_id;
    $("game-id-input").value = gameId;
    await refresh();
    toast("Partida importada.");
  } catch (e) { toast(e.message, true); }
}

// ---------- Controles ----------

$("btn-new").addEventListener("click", () => createGame(7));
$("btn-demo").addEventListener("click", () => createGame(7));
$("btn-load").addEventListener("click", () => loadGame($("game-id-input").value.trim()));
$("btn-export").addEventListener("click", exportGame);
$("file-import").addEventListener("change", (e) => {
  if (e.target.files[0]) importGame(e.target.files[0]);
});

$("game-id-input").addEventListener("keydown", (e) => {
  if (e.key === "Enter") loadGame($("game-id-input").value.trim());
});

$("btn-contrast").addEventListener("click", () => {
  highContrast = !highContrast;
  document.body.classList.toggle("high-contrast", highContrast);
  localStorage.setItem("hc", highContrast ? "1" : "0");
});

$("lang-select").value = lang;
$("lang-select").addEventListener("change", async (e) => {
  lang = e.target.value;
  localStorage.setItem("lang", lang);
  await loadTranslations();
  applyTranslations();
});

document.addEventListener("keydown", (e) => {
  if (e.ctrlKey && e.key >= "1" && e.key <= "3") {
    e.preventDefault();
    saveSlot(e.key);
  } else if (!e.ctrlKey && !e.target.matches("input,textarea") && e.key >= "1" && e.key <= "3") {
    loadSlot(e.key);
  }
});

// Inicializar i18n y accesibilidad
loadTranslations().then(() => applyTranslations());
if (highContrast) document.body.classList.add("high-contrast");

// Auto-refresh suave cada 30s si hay partida
setInterval(() => { if (gameId) refresh(); }, 30000);

// ---------- Colapsables ----------
document.querySelectorAll("[data-toggle]").forEach(btn => {
  btn.addEventListener("click", () => {
    const panel = btn.closest(".collapsible");
    if (panel) panel.classList.toggle("collapsed");
  });
});

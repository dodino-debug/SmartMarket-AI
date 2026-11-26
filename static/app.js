const number = new Intl.NumberFormat("es-CO");
const money = new Intl.NumberFormat("es-CO", {
  style: "currency", currency: "COP", currencyDisplay: "code", maximumFractionDigits: 0,
});

function node(tag, text) {
  const element = document.createElement(tag);
  if (text !== undefined) element.textContent = text;
  return element;
}

async function getJSON(url, options) {
  const response = await fetch(url, options);
  if (!response.ok) throw new Error("Servicio no disponible");
  return response.json();
}

function showBars(target, entries, label) {
  const max = Math.max(1, ...entries.map(row => row.revenue));
  for (const row of entries) {
    const bar = node("div");
    bar.className = "bar";
    const meter = node("meter");
    meter.max = max;
    meter.value = row.revenue;
    meter.setAttribute("aria-label", label(row) + ": " + money.format(row.revenue));
    bar.append(node("span", label(row)), meter, node("span", money.format(row.revenue)));
    target.append(bar);
  }
  if (!entries.length) target.textContent = "Sin ingresos registrados.";
}

function showList(id, items, empty) {
  const list = document.getElementById(id);
  for (const item of items.length ? items : [empty]) list.append(node("li", item));
}

async function showDashboard() {
  const period = document.getElementById("period");
  try {
    const data = await getJSON("/api/dashboard");
    const months = data.monthly;
    period.textContent = months.length
      ? "Período analizado: " + months[0].month + " a " + months.at(-1).month
      : "Sin ventas registradas.";
    const metrics = document.getElementById("metrics");
    for (const [label, value] of [
      ["Ingresos", money.format(data.revenue)], ["Transacciones", number.format(data.transactions)],
      ["Unidades vendidas", number.format(data.units)], ["Productos", data.products.length],
      ["Stock bajo", data.alerts.length],
    ]) {
      const metric = node("div");
      metric.append(node("dt", label), node("dd", value));
      metrics.append(metric);
    }
    showBars(document.getElementById("monthly"), months, row => row.month);
    showBars(document.getElementById("categories"), data.categories, row => row.name);
    showList("leaders", data.products.slice(0, 5).map(p => p.name + " · " + p.units + " unidades"),
      "Sin productos registrados.");
    showList("alerts", data.alerts.map(p => p.name + " · " + p.stock + " de " + p.minimum + " mínimas"),
      "Todo el inventario alcanza el mínimo.");
    showList("recommendations", data.recommendations, "Mantén el seguimiento del inventario y las ventas.");
  } catch {
    period.textContent = "El panel no pudo cargar los datos. Recarga la página para intentar nuevamente.";
  }
}

const messages = document.getElementById("messages");
const form = document.getElementById("chat-form");
const question = document.getElementById("question");
const button = form.querySelector("button");
let pending;

function addMessage(text, role) {
  const message = node("p", (role === "user" ? "Tú: " : "Asistente: ") + text);
  message.className = "message " + role;
  messages.append(message);
  messages.scrollTop = messages.scrollHeight;
  return message;
}

function clearChat() {
  pending?.abort();
  pending = undefined;
  button.disabled = false;
  question.value = "";
  messages.replaceChildren();
  addMessage("Hola. Pregúntame por ingresos, productos más vendidos o disponibilidad.", "bot");
}

form.addEventListener("submit", async event => {
  event.preventDefault();
  const message = question.value.trim();
  if (!message || pending) return;
  const controller = new AbortController();
  pending = controller;
  button.disabled = true;
  addMessage(message, "user");
  question.value = "";
  const reply = addMessage("Consultando…", "bot");
  try {
    const data = await getJSON("/api/chat", {
      method: "POST",
      headers: {"Content-Type": "application/json"},
      body: JSON.stringify({message}),
      signal: controller.signal,
    });
    reply.textContent = "Asistente: " + data.answer;
  } catch {
    if (!controller.signal.aborted) reply.textContent = "Asistente: No pude consultar el servicio. Intenta de nuevo.";
  } finally {
    if (pending === controller) {
      pending = undefined;
      button.disabled = false;
      messages.scrollTop = messages.scrollHeight;
    }
  }
});

document.getElementById("clear").addEventListener("click", clearChat);
for (const suggestion of document.querySelectorAll(".suggestions button")) {
  suggestion.addEventListener("click", () => {
    question.value = suggestion.textContent;
    form.requestSubmit();
  });
}
clearChat();
showDashboard();

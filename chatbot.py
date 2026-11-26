import re
import unicodedata
from datetime import datetime
from zoneinfo import ZoneInfo


def normalize(text):
    ascii_text = "".join(ch for ch in unicodedata.normalize("NFD", text.casefold())
                         if not unicodedata.combining(ch))
    return " ".join(re.findall(r"[a-z0-9]+", ascii_text))


def cop(amount):
    return "$" + f"{amount:,}".replace(",", ".") + " COP"


FAQ = (
    (r"horario|abren|cierran", "Atendemos de lunes a domingo, de 8:00 a 20:00."),
    (r"comercializa|que venden|que productos venden|que ofrecen|que venden",
     "Vendemos productos de despensa, bebidas, refrigerados, aseo y hogar."),
    (r"pago|pagar|tarjeta", "Aceptamos efectivo, tarjetas débito y crédito y transferencias."),
    (r"como .*disponibilidad|como .*consult.*stock",
     "Escribe el nombre del producto, por ejemplo «¿Hay arroz?»."),
    (r"devolu|cambios",
     "Para cambios o devoluciones, presenta tu comprobante y el producto en el punto de atención. "
     "Nuestro equipo revisará las condiciones según el tipo de producto."),
)


def recommendations(data):
    advice = []
    if data["declining"]:
        advice.append("Revisa la estrategia comercial. Los ingresos disminuyeron durante dos meses consecutivos.")
    if data["priority"]:
        advice.append("Prioriza la reposición de " + ", ".join(p["name"] for p in data["priority"]) + ".")
    if data["alerts"]:
        advice.append("Coordina con los proveedores la reposición del inventario bajo el mínimo.")
    return advice


def answer(message, load_dashboard):
    question = normalize(message)
    if question in {"hola", "buenas", "buenos dias", "buenas tardes"}:
        return "¡Hola! Puedo ayudarte con ventas, inventario y preguntas sobre SmartMarket."
    if question in {"adios", "hasta luego", "chao", "gracias"}:
        return "¡Gracias por consultar SmartMarket AI!"
    for pattern, reply in FAQ:
        if re.search(pattern, question):
            return reply

    intent = next((name for name, pattern in (
        ("priority", r"priorit"),
        ("recommend", r"recomiend|recomend|mejorar .*ventas|acciones"),
        ("critical", r"stock critico|existencias criticas"),
        ("alerts", r"reposi|repon|stock bajo|pocas existencias"),
        ("least", r"menos vendid|menor .*ventas"),
        ("category", r"categoria.*(ingresos|ventas)"),
        ("peak", r"(que mes|mejor mes).*(mayor|mas|ventas)"),
        ("current", r"este mes|mes actual"),
        ("top", r"mas vendid|mayor demanda"),
        ("trend", r"tendencia|comport|aument|disminu|ultimos meses|ventas mensuales"),
        ("inventory", r"\bhay\b|disponib|\bstock\b|existencias|inventario"),
    ) if re.search(pattern, question)), None)
    if not intent:
        if re.search(r"venta|ingreso|producto", question):
            return "¿Quieres consultar ingresos por mes, productos más vendidos o disponibilidad de un producto?"
        return "No encontré información para esa consulta. Prueba «¿Qué categoría genera mayores ingresos?»."

    data = load_dashboard()
    monthly = data["monthly"]
    period = f"{monthly[0]['month']} a {monthly[-1]['month']}" if monthly else "sin ventas registradas"
    if intent == "inventory":
        matches = [p for p in data["products"]
                   if f" {normalize(p['name'])} " in f" {question} "]
        if matches:
            return "Inventario de demostración. " + "; ".join(
                f"{p['name']}: {p['stock']} unidades (mínimo {p['minimum']})" for p in matches) + "."
        if question in {"stock", "inventario", "disponibilidad", "existencias"}:
            return "¿De qué producto quieres consultar existencias?"
        return "No encontré ese producto. Escribe su nombre, por ejemplo «¿Hay arroz?»."
    if intent in {"priority", "critical", "alerts"}:
        rows = data["priority"] if intent == "priority" else data["alerts"]
        if intent == "critical":
            rows = [p for p in rows if p["stock"] * 2 <= p["minimum"]]
        if not rows:
            return "No hay productos que cumplan esa condición de inventario."
        label = {"priority": f"Reposición prioritaria ({monthly[-1]['month']})",
                 "critical": "Stock crítico", "alerts": "Alerta de reposición"} if monthly else {
                     "priority": "Reposición prioritaria", "critical": "Stock crítico",
                     "alerts": "Alerta de reposición"}
        return label[intent] + ". " + "; ".join(
            f"{p['name']}: {p['stock']} unidades (mínimo {p['minimum']})"
            + (f", {p['latest_units']} vendidas en el mes" if intent == "priority" else "")
            for p in rows) + "."
    if intent == "recommend":
        advice = recommendations(data)
        return f"Recomendaciones ({period}). " + (" ".join(advice) if advice else
            "Mantén el seguimiento de ingresos e inventario antes de decidir cambios.")
    if not monthly:
        return "Por ahora no hay datos de ventas para calcular ese indicador."
    if intent == "current":
        current = datetime.now(ZoneInfo("America/Bogota")).strftime("%Y-%m")
        row = next((m for m in monthly if m["month"] == current), None)
        if row:
            return f"Ingresos de {current}: {cop(row['revenue'])} en {row['transactions']} transacciones."
        latest = monthly[-1]
        return (f"No hay ventas registradas para {current}. Último mes de demostración, "
                f"{latest['month']}: {cop(latest['revenue'])}.")
    if intent == "peak":
        peak = max(monthly, key=lambda m: m["revenue"])
        return f"Mes con mayores ingresos ({period}): {peak['month']}, {cop(peak['revenue'])}."
    if intent == "category":
        leader = data["categories"][0]
        return f"Categoría con mayores ingresos ({period}): {leader['name']}, {cop(leader['revenue'])}."
    if intent in {"least", "top"}:
        products = data["products"]
        if not products:
            return "No hay productos para calcular ese indicador."
        if intent == "least":
            product = min(products, key=lambda p: (p["units"], p["name"]))
            return f"Menor venta por unidades ({period}): {product['name']}, {product['units']} unidades."
        leaders = products[:3] if "productos" in question or "demanda" in question else products[:1]
        return f"Mayor venta por unidades ({period}). " + "; ".join(
            f"{p['name']}: {p['units']} unidades" for p in leaders) + "."

    series = "; ".join(f"{m['month']}: {cop(m['revenue'])}" for m in monthly[-3:])
    advice = recommendations(data)[0] if data["declining"] else ""
    change = ""
    if len(monthly) >= 2:
        delta = monthly[-1]["revenue"] - monthly[-2]["revenue"]
        direction = "aumentaron" if delta > 0 else "disminuyeron" if delta < 0 else "se mantuvieron"
        change = f" Los ingresos {direction} frente al mes registrado anterior."
    return f"Ingresos de los últimos meses registrados. {series}.{change} {advice}".strip()

"""Comprueba una instancia en ejecución. Uso: python scripts/smoke.py URL."""

import argparse
import json
from html.parser import HTMLParser
from urllib.parse import urljoin
from urllib.request import Request, urlopen


class Assets(HTMLParser):
    def __init__(self):
        super().__init__()
        self.urls = []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "script" and "src" in attrs:
            self.urls.append(attrs["src"])
        if tag == "link" and attrs.get("rel") == "stylesheet":
            self.urls.append(attrs["href"])


def get(base, path, message=None):
    request = Request(urljoin(base, path))
    if message is not None:
        request.data = json.dumps({"message": message}).encode("utf-8")
        request.add_header("Content-Type", "application/json")
    with urlopen(request, timeout=90) as response:
        return response.read().decode("utf-8")


def require(condition, message):
    if not condition:
        raise SystemExit(f"Verificación fallida: {message}")


def verify(base):
    health = json.loads(get(base, "/health"))
    require(health == {"status": "ok", "database": "ok"}, "salud de PostgreSQL")

    html = get(base, "/")
    require("SmartMarket AI" in html, "página principal")
    assets = Assets()
    assets.feed(html)
    require(len(assets.urls) == 2 and all(get(base, url) for url in assets.urls), "CSS y JavaScript")

    data = json.loads(get(base, "/api/dashboard"))
    require(len(data["monthly"]) == 12 and len(data["categories"]) == 5, "series de los gráficos")
    require(len(data["products"]) == 30, "catálogo")
    require(data["revenue"] > 0 and data["revenue"] == sum(
        row["revenue"] for row in data["monthly"]), "total mensual")
    require(data["revenue"] == sum(row["revenue"] for row in data["categories"]), "total por categoría")
    require(data["alerts"] and data["priority"] and data["declining"], "tres reglas de negocio")

    cases = (
        ("¿Cuál es el horario de atención?", "8:00"),
        ("¿Qué productos comercializa SmartMarket?", "despensa"),
        ("¿Cuáles son los métodos de pago disponibles?", "efectivo"),
        ("¿Cómo puedo consultar la disponibilidad de un producto?", "nombre del producto"),
        ("¿Cuál es la política de cambios y devoluciones?", "comprobante"),
        ("¿Cuál es el producto con menor nivel de ventas?", "Menor venta por unidades"),
        ("¿Qué productos necesitan reposición?", data["alerts"][0]["name"]),
        ("¿En qué mes se registraron mayores ventas?",
         max(data["monthly"], key=lambda month: month["revenue"])["month"]),
        ("¿Qué categoría genera mayores ingresos?", data["categories"][0]["name"]),
        ("¿Qué acciones recomiendas para mejorar las ventas?", "dos meses consecutivos"),
        ("¿Qué productos deben reponerse prioritariamente?", data["priority"][0]["name"]),
        ("¿Las ventas están aumentando o disminuyendo?", "disminuyeron"),
        ("¿QUÉ PRODUCTOS TIENEN STOCK CRÍTICO?", "Stock crítico"),
        ("¿Cuánto vendimos este mes?", "COP"),
        ("¿Cuál es el producto más vendido?", data["products"][0]["name"]),
        ("¿Cuáles son los productos con mayor demanda?", data["products"][1]["name"]),
        ("¿Cómo se comportaron las ventas durante los últimos meses?", "COP"),
        ("¿Hay arroz?", "Arroz"),
        ("¿Hay un producto inexistente?", "No encontré"),
        ("ventas", "¿Quieres"),
        ("¿Qué tiempo hará mañana?", "No encontré información"),
    )
    for question, expected in cases:
        reply = json.loads(get(base, "/api/chat", question))["answer"]
        require(expected in reply, question)
    print(f"Verificación correcta: salud, estáticos, panel, reglas y {len(cases)} consultas.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("url")
    verify(parser.parse_args().url)

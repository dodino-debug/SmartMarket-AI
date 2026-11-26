import psycopg
from flask import Flask, jsonify, render_template, request

from analytics import dashboard
from chatbot import answer, recommendations
from database.connection import connect, production


app = Flask(__name__)
app.config.update(DEBUG=False, MAX_CONTENT_LENGTH=4096)
if production():
    app.config["PROPAGATE_EXCEPTIONS"] = False


def load_dashboard():
    with connect() as connection:
        connection.execute("SET TRANSACTION ISOLATION LEVEL REPEATABLE READ, READ ONLY")
        data = dashboard(connection)
    return data


@app.errorhandler(psycopg.Error)
@app.errorhandler(ValueError)
def unavailable(error):
    app.logger.warning("Error de servicio (%s)", type(error).__name__)
    return jsonify(error="No se pudo consultar el servicio de datos."), 503


@app.get("/")
def index():
    return render_template("index.html")


@app.get("/health")
def health():
    try:
        with connect() as connection:
            connection.execute("""
                SELECT (SELECT count(*) FROM categories),
                       (SELECT count(*) FROM suppliers),
                       (SELECT count(*) FROM products),
                       (SELECT count(*) FROM inventory),
                       (SELECT count(*) FROM sales),
                       (SELECT count(*) FROM sale_items)
            """)
    except (psycopg.Error, ValueError):
        return jsonify(status="unavailable", database="unavailable"), 503
    return jsonify(status="ok", database="ok")


@app.get("/api/dashboard")
def dashboard_api():
    data = load_dashboard()
    data["recommendations"] = recommendations(data)
    return jsonify(data)


@app.post("/api/chat")
def chat():
    payload = request.get_json(silent=True)
    question = payload.get("message") if isinstance(payload, dict) else None
    if not isinstance(question, str) or not question.strip() or len(question) > 300:
        return jsonify(error="Escribe una pregunta de 1 a 300 caracteres."), 400
    return jsonify(answer=answer(question, load_dashboard))

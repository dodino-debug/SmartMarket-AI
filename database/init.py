import argparse
from pathlib import Path

import psycopg

from database.connection import connect
from database.seed import seed


def initialize(load_demo=True):
    with connect() as connection:
        connection.execute("SELECT pg_advisory_xact_lock(1729, 1)")
        connection.execute(Path(__file__).with_name("schema.sql").read_text(encoding="utf-8"))
        if load_demo:
            seed(connection)


def main():
    parser = argparse.ArgumentParser(description="Inicializa SmartMarket en PostgreSQL.")
    parser.add_argument("--schema-only", action="store_true", help="Crea solo el esquema.")
    args = parser.parse_args()
    try:
        initialize(load_demo=not args.schema_only)
    except (psycopg.Error, ValueError) as error:
        parser.exit(1, f"Error al inicializar PostgreSQL ({type(error).__name__}). "
                    "Revisa DATABASE_URL, permisos y conectividad.\n")
    print("Esquema PostgreSQL listo." if args.schema_only else "Esquema y datos de demostración listos.")


if __name__ == "__main__":
    main()

import os
from pathlib import Path
from urllib.parse import urlsplit

import psycopg
from dotenv import load_dotenv
from psycopg.rows import dict_row


def production():
    return os.getenv("RENDER") == "true" or os.getenv("APP_ENV") == "production"


if not production():
    load_dotenv(Path(__file__).resolve().parents[1] / ".env")


def connect():
    url = os.getenv("DATABASE_URL", "").strip()
    if urlsplit(url).scheme not in {"postgres", "postgresql"}:
        raise ValueError("Configura DATABASE_URL con una URI PostgreSQL.")

    options = {"sslmode": "require"} if production() else {}
    return psycopg.connect(
        url, connect_timeout=8, prepare_threshold=None, row_factory=dict_row, **options
    )

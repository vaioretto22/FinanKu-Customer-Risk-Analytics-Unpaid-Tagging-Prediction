"""PostgreSQL connection helpers. Credentials are read from environment variables / a local .env file
(never hard-coded, never committed). See .env.example."""
from __future__ import annotations

import os

import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.engine import URL, Engine


def get_engine() -> Engine:
    """Build a SQLAlchemy engine from DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD."""
    load_dotenv()
    required = ["DB_HOST", "DB_PORT", "DB_NAME", "DB_USER", "DB_PASSWORD"]
    missing = [k for k in required if not os.getenv(k)]
    if missing:
        raise RuntimeError(f"Missing environment variables: {missing}. Copy .env.example to .env and fill it in.")
    url = URL.create(                       # URL.create safely handles special characters in the password
        "postgresql+psycopg2",
        username=os.environ["DB_USER"],
        password=os.environ["DB_PASSWORD"],
        host=os.environ["DB_HOST"],
        port=int(os.environ["DB_PORT"]),
        database=os.environ["DB_NAME"],
    )
    return create_engine(url)


def run_query(sql: str, params: dict | None = None, engine: Engine | None = None) -> pd.DataFrame:
    """Run a SELECT and return a DataFrame. Use :name placeholders with params."""
    engine = engine or get_engine()
    with engine.connect() as conn:
        return pd.read_sql(text(sql), conn, params=params)

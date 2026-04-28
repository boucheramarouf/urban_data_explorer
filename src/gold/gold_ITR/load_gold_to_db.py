"""
Export GOLD ITR vers PostgreSQL.

Ce script lit le parquet GOLD et charge son contenu dans la table
`itr_par_rue` via SQLAlchemy + pandas.to_sql.
"""

import os
from pathlib import Path

import pandas as pd
from sqlalchemy import create_engine

OUT_PARQUET = Path("data/gold/gold_ITR/itr_par_rue.parquet")
TABLE_NAME = "itr_par_rue"


def _normalize_db_url(db_url: str) -> str:
    # Compat avec une URL "postgresql://" sans driver explicite.
    if db_url.startswith("postgresql://"):
        return db_url.replace("postgresql://", "postgresql+psycopg://", 1)
    return db_url


def _default_pg_host() -> str:
    host = os.getenv("POSTGRES_HOST")
    if host:
        return host
    if Path("/.dockerenv").exists():
        return "db"
    return "localhost"


def _build_db_url() -> str | None:
    db_url = os.getenv("DATABASE_URL")
    if db_url:
        return _normalize_db_url(db_url)

    user = os.getenv("POSTGRES_USER")
    password = os.getenv("POSTGRES_PASSWORD")
    db_name = os.getenv("POSTGRES_DB")
    port = os.getenv("POSTGRES_PORT", "5432")
    host = _default_pg_host()

    if not user or not password or not db_name:
        return None

    return f"postgresql+psycopg://{user}:{password}@{host}:{port}/{db_name}"


def run() -> None:
    db_url = _build_db_url()
    if not db_url:
        print("  [SKIP] Variables PostgreSQL absentes : export SQL ignore.")
        return

    if not OUT_PARQUET.exists():
        raise FileNotFoundError(
            f"Parquet gold introuvable: {OUT_PARQUET}. Lancez d'abord la couche gold."
        )

    df = pd.read_parquet(OUT_PARQUET)
    engine = create_engine(db_url, pool_pre_ping=True, future=True)

    df.to_sql(
        TABLE_NAME,
        engine,
        if_exists="replace",
        index=False,
        method="multi",
        chunksize=1000,
    )

    print(f"  [OK] Table SQL '{TABLE_NAME}' alimentée ({len(df):,} lignes)")


if __name__ == "__main__":
    run()

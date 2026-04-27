"""
Export GOLD IAML vers PostgreSQL.
"""

import os
from pathlib import Path

import pandas as pd
from sqlalchemy import create_engine

OUT_PARQUET = Path("data/gold/gold_IAML/iaml_par_rue.parquet")
TABLE_NAME = "iaml_par_rue"


def _normalize_db_url(db_url: str) -> str:
    if db_url.startswith("postgresql://"):
        return db_url.replace("postgresql://", "postgresql+psycopg://", 1)
    return db_url


def run() -> None:
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        print("  [SKIP] DATABASE_URL absente : export SQL IAML ignore.")
        return

    if not OUT_PARQUET.exists():
        raise FileNotFoundError(
            f"Parquet gold introuvable: {OUT_PARQUET}. Lancez d'abord la couche gold IAML."
        )

    df = pd.read_parquet(OUT_PARQUET)
    engine = create_engine(_normalize_db_url(db_url), pool_pre_ping=True, future=True)

    df.to_sql(
        TABLE_NAME,
        engine,
        if_exists="replace",
        index=False,
        method="multi",
        chunksize=1000,
    )

    print(f"  [OK] Table SQL '{TABLE_NAME}' alimentee ({len(df):,} lignes)")


if __name__ == "__main__":
    run()

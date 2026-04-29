"""
Export de tous les indicateurs GOLD vers PostgreSQL.
Ce script consolide l'export de SVP, IAML, ITR et IMQ vers PostgreSQL.
"""

import os
from pathlib import Path

import pandas as pd
from sqlalchemy import create_engine


# Configuration des indicateurs
INDICATORS = [
    {
        "name": "SVP",
        "parquet": Path("data/gold/gold_SVP/svp_par_rue.parquet"),
        "table": "svp_par_rue",
    },
    {
        "name": "IAML",
        "parquet": Path("data/gold/gold_IAML/iaml_par_rue.parquet"),
        "table": "iaml_par_rue",
    },
    {
        "name": "ITR",
        "parquet": Path("data/gold/gold_ITR/itr_par_rue.parquet"),
        "table": "itr_par_rue",
    },
    {
        "name": "IMQ",
        "parquet": Path("data/gold/gold_IMQ/imq_par_iris.parquet"),
        "table": "imq_par_iris",
    },
]


def _normalize_db_url(db_url: str) -> str:
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
        print("  [SKIP] Variables PostgreSQL absentes : export SQL ignoré.")
        return

    engine = create_engine(db_url, pool_pre_ping=True, future=True)
    
    print("\n=== Export vers PostgreSQL ===")
    loaded_count = 0
    
    for indicator in INDICATORS:
        name = indicator["name"]
        parquet_path = indicator["parquet"]
        table_name = indicator["table"]
        
        if not parquet_path.exists():
            print(f"  [SKIP] {name}: Fichier {parquet_path} introuvable")
            continue
        
        try:
            df = pd.read_parquet(parquet_path)
            df.to_sql(
                table_name,
                engine,
                if_exists="replace",
                index=False,
                method="multi",
                chunksize=1000,
            )
            print(f"  [OK] {name}: Table '{table_name}' alimentée ({len(df):,} lignes)")
            loaded_count += 1
        except Exception as e:
            print(f"  [ERROR] {name}: {str(e)}")
    
    print(f"\n{loaded_count}/{len(INDICATORS)} indicateurs exportés vers PostgreSQL")


if __name__ == "__main__":
    run()
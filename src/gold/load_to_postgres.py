"""
Export de tous les indicateurs GOLD vers PostgreSQL.
Ce script consolide l'export de SVP, IAML, ITR et IMQ vers PostgreSQL.
"""

import os
from pathlib import Path

import pandas as pd


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


def _default_pg_host() -> str:
    host = os.getenv("POSTGRES_HOST")
    if host:
        return host
    if Path("/.dockerenv").exists():
        return "db"
    return "localhost"


def _build_raw_url() -> str | None:
    """Retourne une URL psycopg native (sans driver SQLAlchemy)."""
    db_url = os.getenv("DATABASE_URL")
    if db_url:
        return (db_url
                .replace("postgresql+psycopg://", "postgresql://")
                .replace("postgresql+psycopg2://", "postgresql://"))

    user = os.getenv("POSTGRES_USER")
    password = os.getenv("POSTGRES_PASSWORD")
    db_name = os.getenv("POSTGRES_DB")
    port = os.getenv("POSTGRES_PORT", "5432")
    host = _default_pg_host()

    if not user or not password or not db_name:
        return None

    return f"postgresql://{user}:{password}@{host}:{port}/{db_name}"


def _get_connector():
    """Retourne le module psycopg disponible (v3 ou v2)."""
    try:
        import psycopg
        return psycopg, "psycopg3"
    except ImportError:
        import psycopg2
        return psycopg2, "psycopg2"


def run() -> None:
    raw_url = _build_raw_url()
    if not raw_url:
        print("  [SKIP] Variables PostgreSQL absentes : export SQL ignoré.")
        return

    psycopg_mod, version = _get_connector()
    print(f"\n=== Export vers PostgreSQL ({version}) ===")
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

            with psycopg_mod.connect(raw_url) as conn:
                with conn.cursor() as cur:
                    cols = ", ".join([f'"{c}" TEXT' for c in df.columns])
                    cur.execute(f'DROP TABLE IF EXISTS "{table_name}"')
                    cur.execute(f'CREATE TABLE "{table_name}" ({cols})')

                    rows = [
                        tuple(str(v) if v is not None else None for v in row)
                        for row in df.itertuples(index=False)
                    ]

                    placeholders = ", ".join(["%s"] * len(df.columns))
                    cur.executemany(
                        f'INSERT INTO "{table_name}" VALUES ({placeholders})',
                        rows
                    )
                conn.commit()

            print(f"  [OK] {name}: Table '{table_name}' alimentée ({len(df):,} lignes)")
            loaded_count += 1

        except Exception as e:
            import traceback
            print(f"  [ERROR] {name}: {str(e)}")
            traceback.print_exc()

    print(f"\n{loaded_count}/{len(INDICATORS)} indicateurs exportés vers PostgreSQL")


if __name__ == "__main__":
    run()
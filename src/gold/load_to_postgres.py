"""
Export de tous les indicateurs GOLD vers PostgreSQL.
Ce script consolide l'export de SVP, IAML, ITR et IMQ vers PostgreSQL.
"""

import os
from pathlib import Path

import pandas as pd


# Configuration des indicateurs (IMQ en premier : table parent des FK)
INDICATORS = [
    {
        "name": "IMQ",
        "parquet": Path("data/gold/gold_IMQ/imq_par_iris.parquet"),
        "table": "imq_par_iris",
    },
    {
        "name": "ITR",
        "parquet": Path("data/gold/gold_ITR/itr_par_rue.parquet"),
        "table": "itr_par_rue",
    },
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
]

# Relations d'intégrité référentielle : chaque rue appartient à un IRIS
# (child_table, child_col, parent_table, parent_col)
FK_RELATIONS = [
    ("itr_par_rue", "code_iris", "imq_par_iris", "iris_code"),
    ("svp_par_rue", "code_iris", "imq_par_iris", "iris_code"),
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


# ── Mapping dtype pandas → type PostgreSQL ────────────────────────────────────
def _pg_type(dtype) -> str:
    name = str(dtype)
    if name.startswith("int"):
        return "INTEGER"
    if name.startswith("float"):
        return "DOUBLE PRECISION"
    if name.startswith("bool"):
        return "BOOLEAN"
    return "TEXT"


# ── Colonnes identifiantes (NOT NULL) et index par table ──────────────────────
TABLE_SCHEMA = {
    "imq_par_iris": {
        "not_null": ["iris_code"],
        "indexes":  ["arr_insee", "score_imq", "interpretation"],
    },
    "itr_par_rue": {
        "not_null": ["nom_voie"],
        "indexes":  ["arrondissement", "itr_score", "itr_label"],
    },
    "svp_par_rue": {
        "not_null": ["nom_voie"],
        "indexes":  ["arrondissement", "svp_score", "svp_label"],
    },
    "iaml_par_rue": {
        "not_null": ["nom_voie"],
        "indexes":  ["arrondissement", "iaml_score", "iaml_label"],
    },
}


def _build_create_table(table_name: str, df: pd.DataFrame) -> str:
    """Génère le DDL CREATE TABLE avec typage, PK et contraintes NOT NULL."""
    schema = TABLE_SCHEMA.get(table_name, {})
    not_null_cols = set(schema.get("not_null", []))

    col_defs = ['"id" SERIAL PRIMARY KEY']
    for col in df.columns:
        pg_type = _pg_type(df[col].dtype)
        constraint = " NOT NULL" if col in not_null_cols else ""
        col_defs.append(f'"{col}" {pg_type}{constraint}')

    return f'CREATE TABLE "{table_name}" (\n    ' + ",\n    ".join(col_defs) + "\n)"


def _coerce_value(value, dtype):
    """Convertit une valeur pandas en type Python natif pour psycopg."""
    if pd.isna(value):
        return None
    name = str(dtype)
    if name.startswith("int"):
        return int(value)
    if name.startswith("float"):
        return float(value)
    if name.startswith("bool"):
        return bool(value)
    return str(value)


def run() -> None:
    raw_url = _build_raw_url()
    if not raw_url:
        print("  [SKIP] Variables PostgreSQL absentes : export SQL ignoré.")
        return

    psycopg_mod, version = _get_connector()
    print(f"\n=== Export vers PostgreSQL ({version}) ===")
    loaded_count = 0

    # ── Activer l'extension PostGIS (idempotent) ───────────────────────
    postgis_ok = False
    try:
        with psycopg_mod.connect(raw_url) as conn:
            with conn.cursor() as cur:
                cur.execute("CREATE EXTENSION IF NOT EXISTS postgis")
            conn.commit()
        postgis_ok = True
        print("  [OK] Extension PostGIS active")
    except Exception as e:
        print(f"  [WARN] PostGIS indisponible ({e}) : colonnes geometriques ignorees")

    for indicator in INDICATORS:
        name = indicator["name"]
        parquet_path = indicator["parquet"]
        table_name = indicator["table"]

        if not parquet_path.exists():
            print(f"  [SKIP] {name}: Fichier {parquet_path} introuvable")
            continue

        try:
            df = pd.read_parquet(parquet_path)
            dtypes = list(df.dtypes)

            with psycopg_mod.connect(raw_url) as conn:
                with conn.cursor() as cur:
                    # 1. Table typée avec PK + contraintes
                    cur.execute(f'DROP TABLE IF EXISTS "{table_name}" CASCADE')
                    cur.execute(_build_create_table(table_name, df))

                    # 2. Insertion des données avec types natifs
                    col_names = ", ".join([f'"{c}"' for c in df.columns])
                    rows = [
                        tuple(_coerce_value(v, dt) for v, dt in zip(row, dtypes))
                        for row in df.itertuples(index=False)
                    ]
                    placeholders = ", ".join(["%s"] * len(df.columns))
                    cur.executemany(
                        f'INSERT INTO "{table_name}" ({col_names}) VALUES ({placeholders})',
                        rows
                    )

                    # 3. Index sur les colonnes de filtrage fréquentes
                    for idx_col in TABLE_SCHEMA.get(table_name, {}).get("indexes", []):
                        if idx_col in df.columns:
                            cur.execute(
                                f'CREATE INDEX "idx_{table_name}_{idx_col}" '
                                f'ON "{table_name}" ("{idx_col}")'
                            )

                    # 4. Colonne géospatiale PostGIS (si coordonnées présentes)
                    has_geom = (
                        postgis_ok
                        and "lon_centre" in df.columns
                        and "lat_centre" in df.columns
                    )
                    if has_geom:
                        cur.execute(
                            f'ALTER TABLE "{table_name}" '
                            f'ADD COLUMN "geom" geometry(Point, 4326)'
                        )
                        cur.execute(
                            f'UPDATE "{table_name}" SET "geom" = '
                            f'ST_SetSRID(ST_MakePoint("lon_centre", "lat_centre"), 4326) '
                            f'WHERE "lon_centre" IS NOT NULL AND "lat_centre" IS NOT NULL'
                        )
                        cur.execute(
                            f'CREATE INDEX "idx_{table_name}_geom" '
                            f'ON "{table_name}" USING GIST ("geom")'
                        )
                conn.commit()

            n_idx = sum(1 for c in TABLE_SCHEMA.get(table_name, {}).get("indexes", []) if c in df.columns)
            geom_txt = " · geom PostGIS" if has_geom else ""
            print(f"  [OK] {name}: '{table_name}' ({len(df):,} lignes · {len(df.columns)} colonnes typées · {n_idx} index{geom_txt})")
            loaded_count += 1

        except Exception as e:
            import traceback
            print(f"  [ERROR] {name}: {str(e)}")
            traceback.print_exc()

    # ── Intégrité référentielle : clés étrangères (rue → IRIS) ────────────────
    try:
        with psycopg_mod.connect(raw_url) as conn:
            with conn.cursor() as cur:
                # Contrainte UNIQUE sur la colonne référencée (requis pour une FK)
                cur.execute(
                    'ALTER TABLE "imq_par_iris" '
                    'ADD CONSTRAINT "uq_imq_iris_code" UNIQUE ("iris_code")'
                )
                for child, child_col, parent, parent_col in FK_RELATIONS:
                    # Défensif : neutraliser les code_iris absents du parent
                    cur.execute(
                        f'UPDATE "{child}" SET "{child_col}" = NULL '
                        f'WHERE "{child_col}" IS NOT NULL AND "{child_col}" NOT IN '
                        f'(SELECT "{parent_col}" FROM "{parent}")'
                    )
                    cur.execute(
                        f'ALTER TABLE "{child}" '
                        f'ADD CONSTRAINT "fk_{child}_{child_col}" '
                        f'FOREIGN KEY ("{child_col}") '
                        f'REFERENCES "{parent}"("{parent_col}")'
                    )
            conn.commit()
        print("  [OK] Cles etrangeres : itr/svp.code_iris -> imq_par_iris.iris_code")
    except Exception as e:
        print(f"  [WARN] Cles etrangeres non ajoutees : {e}")

    print(f"\n{loaded_count}/{len(INDICATORS)} indicateurs exportés vers PostgreSQL")



if __name__ == "__main__":
    run()
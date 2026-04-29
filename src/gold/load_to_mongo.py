"""
Export de tous les indicateurs GOLD vers MongoDB.
Ce script consolide l'export de SVP, IAML, ITR et IMQ vers MongoDB.
"""

import os
from pathlib import Path

import pandas as pd
from pymongo import MongoClient


# Configuration des indicateurs avec leurs index
INDICATORS = [
    {
        "name": "SVP",
        "parquet": Path("data/gold/gold_SVP/svp_par_rue.parquet"),
        "collection": "svp_par_rue",
        "indexes": ["nom_voie", "arrondissement", "svp_score"],
    },
    {
        "name": "IAML",
        "parquet": Path("data/gold/gold_IAML/iaml_par_rue.parquet"),
        "collection": "iaml_par_rue",
        "indexes": ["nom_voie", "arrondissement", "iaml_score"],
    },
    {
        "name": "ITR",
        "parquet": Path("data/gold/gold_ITR/itr_par_rue.parquet"),
        "collection": "itr_par_rue",
        "indexes": ["nom_voie", "arrondissement", "itr_score"],
    },
    {
        "name": "IMQ",
        "parquet": Path("data/gold/gold_IMQ/imq_par_iris.parquet"),
        "collection": "imq_par_iris",
        "indexes": ["nom_voie", "arrondissement", "imq_score"],
    },
]


def _build_mongo_uri() -> str | None:
    uri = os.getenv("MONGO_URI")
    if uri:
        return uri

    user = os.getenv("MONGO_INITDB_ROOT_USERNAME")
    password = os.getenv("MONGO_INITDB_ROOT_PASSWORD")
    host = _default_mongo_host()
    port = os.getenv("MONGO_PORT", "27017")

    if not user or not password:
        return None

    return f"mongodb://{user}:{password}@{host}:{port}/admin?authSource=admin"


def _default_mongo_host() -> str:
    host = os.getenv("MONGO_HOST")
    if host:
        return host
    if Path("/.dockerenv").exists():
        return "mongo"
    return "localhost"


def _to_documents(df: pd.DataFrame) -> list[dict]:
    clean = df.where(pd.notna(df), None)
    return clean.to_dict(orient="records")


def run() -> None:
    db_name = os.getenv("MONGO_INITDB_DATABASE", "urban_data")
    uri = _build_mongo_uri()

    if not uri:
        print("  [SKIP] Variables Mongo absentes : export MongoDB ignoré.")
        return

    try:
        client = MongoClient(uri, serverSelectionTimeoutMS=5000)
        client.admin.command("ping")
    except Exception as e:
        print(f"  [ERROR] Impossible de se connecter à MongoDB: {str(e)}")
        return

    print("\n=== Export vers MongoDB ===")
    loaded_count = 0

    for indicator in INDICATORS:
        name = indicator["name"]
        parquet_path = indicator["parquet"]
        collection_name = indicator["collection"]
        indexes = indicator["indexes"]

        if not parquet_path.exists():
            print(f"  [SKIP] {name}: Fichier {parquet_path} introuvable")
            continue

        try:
            df = pd.read_parquet(parquet_path)
            docs = _to_documents(df)

            collection = client[db_name][collection_name]
            collection.delete_many({})
            
            if docs:
                collection.insert_many(docs, ordered=False)

            # Créer les index
            for index_field in indexes:
                collection.create_index(index_field)

            print(
                f"  [OK] {name}: Collection '{collection_name}' alimentée "
                f"({len(docs):,} documents)"
            )
            loaded_count += 1
        except Exception as e:
            print(f"  [ERROR] {name}: {str(e)}")

    print(f"\n{loaded_count}/{len(INDICATORS)} indicateurs exportés vers MongoDB")


if __name__ == "__main__":
    run()
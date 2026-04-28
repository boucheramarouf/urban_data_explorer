"""
Export GOLD IAML vers MongoDB.
"""

import os
from pathlib import Path

import pandas as pd
from pymongo import MongoClient

OUT_PARQUET = Path("data/gold/gold_IAML/iaml_par_rue.parquet")
COLLECTION_NAME = "iaml_par_rue"


def _build_mongo_uri() -> str | None:
    uri = os.getenv("MONGO_URI")
    if uri:
        return uri

    user = os.getenv("MONGO_INITDB_ROOT_USERNAME")
    password = os.getenv("MONGO_INITDB_ROOT_PASSWORD")
    host = os.getenv("MONGO_HOST", "mongo")
    port = os.getenv("MONGO_PORT", "27017")

    if not user or not password:
        return None

    return f"mongodb://{user}:{password}@{host}:{port}/admin?authSource=admin"


def _to_documents(df: pd.DataFrame) -> list[dict]:
    clean = df.where(pd.notna(df), None)
    return clean.to_dict(orient="records")


def run() -> None:
    db_name = os.getenv("MONGO_INITDB_DATABASE", "urban_data")
    uri = _build_mongo_uri()

    if not uri:
        print("  [SKIP] Variables Mongo absentes : export Mongo IAML ignore.")
        return

    if not OUT_PARQUET.exists():
        raise FileNotFoundError(
            f"Parquet gold introuvable: {OUT_PARQUET}. Lancez d'abord la couche gold IAML."
        )

    df = pd.read_parquet(OUT_PARQUET)
    docs = _to_documents(df)

    client = MongoClient(uri, serverSelectionTimeoutMS=5000)
    client.admin.command("ping")

    collection = client[db_name][COLLECTION_NAME]
    collection.delete_many({})
    if docs:
        collection.insert_many(docs, ordered=False)

    collection.create_index("nom_voie")
    collection.create_index("arrondissement")
    collection.create_index("iaml_score")

    print(f"  [OK] Collection Mongo '{COLLECTION_NAME}' alimentee ({len(docs):,} documents)")


if __name__ == "__main__":
    run()

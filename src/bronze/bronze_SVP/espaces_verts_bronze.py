"""
BRONZE — Espaces verts Paris
=============================
Ingestion brute des espaces verts parisiens depuis l'API Paris Open Data
ou depuis un fichier local CSV/GeoJSON téléchargé manuellement.

Source principale :
    https://opendata.paris.fr/api/explore/v2.1/catalog/datasets/
    espaces_verts/exports/geojson?lang=fr&timezone=Europe%2FParis

Fallback local :
    data/raw/raw_SVP/espaces_verts.geojson

Sortie : data/bronze/bronze_SVP/espaces_verts_raw.parquet
"""

import pandas as pd
import geopandas as gpd
import requests
import json
from pathlib import Path

# ── Chemins ──────────────────────────────────────────────────────────────────

RAW_LOCAL   = Path("data/raw/raw_SVP/espaces_verts.geojson")
OUTPUT_PATH = Path("data/bronze/bronze_SVP/espaces_verts_raw.parquet")

# ── URL API Paris Open Data (GeoJSON paginé) ─────────────────────────────────

API_URL = (
    "https://opendata.paris.fr/api/explore/v2.1/catalog/datasets/"
    "espaces_verts/exports/geojson"
    "?lang=fr&timezone=Europe%2FParis"
)


# ──────────────────────────────────────────────────────────────────────────────
# CHARGEMENT
# ──────────────────────────────────────────────────────────────────────────────

def load_from_api() -> gpd.GeoDataFrame:
    """
    Télécharge les espaces verts depuis l'API Paris Open Data.
    Retourne un GeoDataFrame WGS84.
    """
    print("  Téléchargement API Paris Open Data (espaces verts)…")
    resp = requests.get(API_URL, timeout=120)
    resp.raise_for_status()
    data = resp.json()

    gdf = gpd.GeoDataFrame.from_features(data["features"], crs="EPSG:4326")
    print(f"  API → {len(gdf):,} espaces verts reçus")
    return gdf


def load_from_local(path: Path) -> gpd.GeoDataFrame:
    """
    Charge depuis un fichier GeoJSON local (téléchargé manuellement).
    """
    print(f"  Fichier local : {path}")
    gdf = gpd.read_file(path)
    if gdf.crs is None or gdf.crs.to_epsg() != 4326:
        gdf = gdf.to_crs("EPSG:4326")
    print(f"  Local → {len(gdf):,} espaces verts")
    return gdf


def load_espaces_verts() -> gpd.GeoDataFrame:
    """
    Stratégie de chargement : API d'abord, fallback local.
    """
    if RAW_LOCAL.exists():
        print(f"  Fichier local trouvé, utilisation de {RAW_LOCAL}")
        return load_from_local(RAW_LOCAL)
    try:
        return load_from_api()
    except Exception as e:
        raise RuntimeError(
            f"Impossible de charger les espaces verts (API échouée : {e})\n"
            f"Téléchargez manuellement le GeoJSON depuis :\n"
            f"  {API_URL}\n"
            f"et placez-le dans : {RAW_LOCAL}"
        )


# ──────────────────────────────────────────────────────────────────────────────
# VALIDATION MINIMALE BRONZE
# ──────────────────────────────────────────────────────────────────────────────

def validate(gdf: gpd.GeoDataFrame) -> None:
    """Bronze : contrôles de présence uniquement, pas de filtrage métier."""
    assert len(gdf) > 0, "GeoDataFrame vide"
    assert gdf.geometry is not None, "Colonne geometry manquante"
    assert gdf.crs is not None, "CRS non défini"
    print(f"  [OK] {len(gdf):,} espaces verts | CRS : {gdf.crs.to_epsg()}")
    print(f"  [OK] Types géométriques : {gdf.geom_type.value_counts().to_dict()}")
    if "surface_calculee" in gdf.columns:
        print(f"  [INFO] Surface totale : "
              f"{gdf['surface_calculee'].sum():,.0f} m²")
    # Alerte si des géométries nulles
    n_null = gdf.geometry.isna().sum()
    if n_null > 0:
        print(f"  [WARN] {n_null} géométries nulles (seront filtrées en silver)")


# ──────────────────────────────────────────────────────────────────────────────
# SAUVEGARDE
# Stocke en parquet via une représentation WKT de la géométrie.
# (Parquet natif ne supporte pas GeoDataFrame sans geopandas-arrow.)
# ──────────────────────────────────────────────────────────────────────────────

def save(gdf: gpd.GeoDataFrame, path: Path) -> None:
    """
    Sérialise le GeoDataFrame en Parquet.
    La géométrie est stockée en WKT (colonne 'geometry_wkt').
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    df = pd.DataFrame(gdf.copy())
    df["geometry_wkt"] = gdf.geometry.to_wkt()
    df = df.drop(columns=["geometry"], errors="ignore")
    df.to_parquet(path, index=False)
    print(f"  Sauvegardé : {path}  ({path.stat().st_size / 1024:.0f} KB)")


# ──────────────────────────────────────────────────────────────────────────────
# POINT D'ENTRÉE
# ──────────────────────────────────────────────────────────────────────────────

def run() -> gpd.GeoDataFrame:
    print("=== BRONZE SVP : Espaces verts ===")
    gdf = load_espaces_verts()
    validate(gdf)
    save(gdf, OUTPUT_PATH)
    return gdf


if __name__ == "__main__":
    run()

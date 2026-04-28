"""
BRONZE — Arbres de Paris
=========================
Ingestion brute du dataset des arbres d'alignement et des parcs parisiens.

Source principale :
    https://opendata.paris.fr/api/explore/v2.1/catalog/datasets/
    les-arbres/exports/geojson?lang=fr

Fallback local :
    data/raw/raw_SVP/arbres.geojson

Sortie : data/bronze/bronze_SVP/arbres_raw.parquet

Notes :
    Le dataset Paris Open Data "les-arbres" recense ~200 000 arbres
    avec leurs coordonnées GPS, espèces, et statut (alignement / parc).
    On conserve toutes les colonnes en bronze.
"""

import pandas as pd
import geopandas as gpd
import requests
from pathlib import Path

# ── Chemins ──────────────────────────────────────────────────────────────────

RAW_LOCAL   = Path("data/raw/raw_SVP/arbres.geojson")
OUTPUT_PATH = Path("data/bronze/bronze_SVP/arbres_raw.parquet")

# ── URL API Paris Open Data ───────────────────────────────────────────────────

API_URL = (
    "https://opendata.paris.fr/api/explore/v2.1/catalog/datasets/"
    "les-arbres/exports/geojson"
    "?lang=fr&timezone=Europe%2FParis"
)


# ──────────────────────────────────────────────────────────────────────────────
# CHARGEMENT
# ──────────────────────────────────────────────────────────────────────────────

def load_from_api() -> gpd.GeoDataFrame:
    """
    Télécharge les arbres depuis l'API Paris Open Data.
    Le dataset fait ~60 MB — timeout généreux de 300 s.
    """
    print("  Téléchargement API Paris Open Data (arbres)…")
    print("  [INFO] ~200 000 arbres, fichier ~60 MB, patienter…")
    resp = requests.get(API_URL, timeout=300, stream=True)
    resp.raise_for_status()

    # Lecture streaming pour ne pas saturer la mémoire
    content = b""
    for chunk in resp.iter_content(chunk_size=1024 * 256):
        content += chunk

    import json
    data = json.loads(content)
    gdf = gpd.GeoDataFrame.from_features(data["features"], crs="EPSG:4326")
    print(f"  API → {len(gdf):,} arbres reçus")
    return gdf


def load_from_local(path: Path) -> gpd.GeoDataFrame:
    """Charge depuis un fichier GeoJSON local."""
    print(f"  Fichier local : {path}")
    gdf = gpd.read_file(path)
    if gdf.crs is None or gdf.crs.to_epsg() != 4326:
        gdf = gdf.to_crs("EPSG:4326")
    print(f"  Local → {len(gdf):,} arbres")
    return gdf


def load_arbres() -> gpd.GeoDataFrame:
    """Stratégie : local d'abord, puis API."""
    if RAW_LOCAL.exists():
        print(f"  Fichier local trouvé : {RAW_LOCAL}")
        return load_from_local(RAW_LOCAL)
    try:
        return load_from_api()
    except Exception as e:
        raise RuntimeError(
            f"Impossible de charger les arbres (API : {e})\n"
            f"Téléchargez le GeoJSON depuis : {API_URL}\n"
            f"et placez-le dans : {RAW_LOCAL}"
        )


# ──────────────────────────────────────────────────────────────────────────────
# VALIDATION BRONZE
# ──────────────────────────────────────────────────────────────────────────────

def validate(gdf: gpd.GeoDataFrame) -> None:
    """Contrôles bronze : présence, CRS, volume."""
    assert len(gdf) > 0, "GeoDataFrame vide"
    assert gdf.geometry is not None, "Colonne geometry manquante"
    n_null = gdf.geometry.isna().sum()
    print(f"  [OK] {len(gdf):,} arbres | CRS : {gdf.crs.to_epsg()}")
    if "typeemplacement" in gdf.columns:
        print(f"  [OK] Types : {gdf['typeemplacement'].value_counts().to_dict()}")
    if n_null > 0:
        print(f"  [WARN] {n_null} géométries nulles (seront filtrées en silver)")
    # Vérification bbox Grand Paris (élargie : le dataset inclut les bois de
    # Vincennes (lat ~48.74) et de Boulogne, légèrement hors intramuros strict).
    # Ces arbres seront filtrés proprement en couche Silver (bbox 48.81–48.91).
    bounds = gdf.geometry.dropna().total_bounds  # [minx, miny, maxx, maxy]
    assert 2.1 < bounds[0] < 2.6, f"Longitude min hors Grand Paris : {bounds[0]}"
    assert 48.7 < bounds[1] < 49.1, f"Latitude min hors Grand Paris : {bounds[1]}"
    print(f"  [OK] Bbox : lon [{bounds[0]:.3f}, {bounds[2]:.3f}] "
          f"lat [{bounds[1]:.3f}, {bounds[3]:.3f}]")
    print(f"  [INFO] Arbres hors Paris strict (bois de Vincennes/Boulogne) "
          f"filtrés en Silver")


# ──────────────────────────────────────────────────────────────────────────────
# SAUVEGARDE
# ──────────────────────────────────────────────────────────────────────────────

def save(gdf: gpd.GeoDataFrame, path: Path) -> None:
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
    print("=== BRONZE SVP : Arbres ===")
    gdf = load_arbres()
    validate(gdf)
    save(gdf, OUTPUT_PATH)
    return gdf


if __name__ == "__main__":
    run()

"""
SILVER — Commerces alimentaires (nettoyage & catégorisation)
=============================================================
Nettoie les données brutes des commerces alimentaires :
catégorise les types, dédoublonne, filtre les positions aberrantes.

Entrée  : data/bronze/bronze_SVP/commerces_alim_raw.parquet
Sortie  : data/silver/silver_SVP/commerces_alim_clean.parquet

Transformations :
    - Suppression des géométries nulles
    - Dédoublonnage sur osm_id puis sur position
    - Catégorisation en 3 groupes : supermarché / épicerie / autre_alim
    - Filtre bbox Paris
    - Export avec coordonnées lon/lat directes
"""

import pandas as pd
import geopandas as gpd
from shapely import from_wkt
from pathlib import Path

# ── Chemins ───────────────────────────────────────────────────────────────────

BRONZE_PATH = Path("data/bronze/bronze_SVP/commerces_alim_raw.parquet")
SILVER_PATH = Path("data/silver/silver_SVP/commerces_alim_clean.parquet")

# ── Catégorisation OSM ────────────────────────────────────────────────────────

# Mapping tag OSM → catégorie métier SVP
CATEGORY_MAP = {
    "supermarket"  : "supermarche",
    "grocery"      : "epicerie",
    "convenience"  : "epicerie",
    "food"         : "epicerie",
    "deli"         : "epicerie",
    "butcher"      : "autre_alim",
    "bakery"       : "autre_alim",
    "greengrocer"  : "autre_alim",
    "seafood"      : "autre_alim",
    "cheese"       : "autre_alim",
    "wine"         : "autre_alim",
    "beverages"    : "autre_alim",
    "alcohol"      : "autre_alim",
    "marketplace"  : "epicerie",  # marchés alimentaires
}

# Poids de chaque catégorie dans le score_acces_alim
# Supermarché pèse plus car assortiment complet
CATEGORY_WEIGHT = {
    "supermarche" : 1.0,
    "epicerie"    : 0.7,
    "autre_alim"  : 0.4,
}


# ──────────────────────────────────────────────────────────────────────────────
# CHARGEMENT
# ──────────────────────────────────────────────────────────────────────────────

def load_bronze(path: Path) -> gpd.GeoDataFrame:
    df = pd.read_parquet(path)

    if "geometry_wkt" in df.columns:
        geom = df["geometry_wkt"].apply(lambda w: from_wkt(w) if pd.notna(w) else None)
        gdf = gpd.GeoDataFrame(df.drop(columns=["geometry_wkt"]), geometry=geom, crs="EPSG:4326")
    elif "lon" in df.columns and "lat" in df.columns:
        gdf = gpd.GeoDataFrame(
            df,
            geometry=gpd.points_from_xy(df["lon"], df["lat"]),
            crs="EPSG:4326",
        )
    else:
        raise ValueError("Format bronze non reconnu (ni geometry_wkt, ni lon/lat)")

    return gdf


# ──────────────────────────────────────────────────────────────────────────────
# NETTOYAGE
# ──────────────────────────────────────────────────────────────────────────────

def clean_commerces(gdf: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    n0 = len(gdf)
    print(f"  Lignes bronze : {n0:,}")

    # 1. Suppression géométries nulles
    gdf = gdf[gdf.geometry.notna()].copy()
    print(f"  Après suppression géom. nulles : {len(gdf):,}  (-{n0 - len(gdf)})")

    # 2. Dédoublonnage osm_id si présent
    if "osm_id" in gdf.columns:
        n1 = len(gdf)
        gdf = gdf.drop_duplicates(subset=["osm_id"])
        print(f"  Après dédup. osm_id : {len(gdf):,}  (-{n1 - len(gdf)})")

    # 3. Dédoublonnage position (arrondi à 4 décimales ≈ 11m)
    gdf["_lon_r"] = gdf.geometry.x.round(4)
    gdf["_lat_r"] = gdf.geometry.y.round(4)
    n2 = len(gdf)
    gdf = gdf.drop_duplicates(subset=["_lon_r", "_lat_r"])
    gdf = gdf.drop(columns=["_lon_r", "_lat_r"])
    print(f"  Après dédup. position : {len(gdf):,}  (-{n2 - len(gdf)})")

    # 4. Filtre bbox Paris intramuros
    n3 = len(gdf)
    lon = gdf.geometry.x
    lat = gdf.geometry.y
    gdf = gdf[lon.between(2.22, 2.47) & lat.between(48.81, 48.91)]
    print(f"  Après filtre bbox Paris : {len(gdf):,}  (-{n3 - len(gdf)})")

    # 5. Catégorisation
    # Priorité : colonne "shop" puis "amenity"
    def categorize(row) -> str:
        shop = str(row.get("shop", "") or "").lower().strip()
        amenity = str(row.get("amenity", "") or "").lower().strip()
        return CATEGORY_MAP.get(shop) or CATEGORY_MAP.get(amenity) or "autre_alim"

    gdf["categorie"] = gdf.apply(categorize, axis=1)
    print(f"  Catégories : {gdf['categorie'].value_counts().to_dict()}")

    # 6. Poids de chaque commerce dans le score
    gdf["poids"] = gdf["categorie"].map(CATEGORY_WEIGHT)

    # 7. Coordonnées explicites
    gdf["lon"] = gdf.geometry.x
    gdf["lat"] = gdf.geometry.y

    # 8. Colonnes finales
    cols = ["osm_id", "osm_type", "name", "categorie", "poids", "lon", "lat", "geometry"]
    result = gdf[[c for c in cols if c in gdf.columns]].copy()

    print(f"  [OK] {len(result):,} commerces alimentaires propres")
    return result


# ──────────────────────────────────────────────────────────────────────────────
# VALIDATION SILVER
# ──────────────────────────────────────────────────────────────────────────────

def validate(gdf: gpd.GeoDataFrame) -> None:
    assert len(gdf) > 0, "Table commerces vide après silver"
    assert "categorie" in gdf.columns, "Colonne categorie manquante"
    assert "poids" in gdf.columns, "Colonne poids manquante"
    assert gdf["lon"].between(2.22, 2.47).all(), "Longitudes hors Paris"
    assert gdf["lat"].between(48.81, 48.91).all(), "Latitudes hors Paris"
    assert gdf.geometry.isna().sum() == 0, "Géométries nulles résiduelles"
    cats = set(gdf["categorie"].unique())
    assert cats <= {"supermarche", "epicerie", "autre_alim"}, \
        f"Catégories inconnues : {cats - {'supermarche', 'epicerie', 'autre_alim'}}"
    print(f"  [OK] {len(gdf):,} commerces validés")
    print(f"  [OK] Catégories : {gdf['categorie'].value_counts().to_dict()}")


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
    print("=== SILVER SVP : Commerces alimentaires ===")
    gdf = load_bronze(BRONZE_PATH)
    gdf = clean_commerces(gdf)
    validate(gdf)
    save(gdf, SILVER_PATH)
    return gdf


if __name__ == "__main__":
    run()

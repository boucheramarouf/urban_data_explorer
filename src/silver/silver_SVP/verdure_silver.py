"""
SILVER — Espaces verts & Arbres (nettoyage géospatial)
========================================================
Nettoie les couches bronze, projette en Lambert-93 pour les calculs
de distance métriques, puis reconstruit les GeoDataFrames en WGS84.

Entrées :
    data/bronze/bronze_SVP/espaces_verts_raw.parquet
    data/bronze/bronze_SVP/arbres_raw.parquet

Sorties :
    data/silver/silver_SVP/espaces_verts_clean.parquet
    data/silver/silver_SVP/arbres_clean.parquet

Transformations :
    - Suppression des géométries nulles ou invalides
    - Suppression des doublons (osm_id / geo_point_2d)
    - Calcul centroïdes pour les polygones d'espaces verts
    - Calcul de la surface en m² (projection Lambert-93)
    - Conservation uniquement des colonnes utiles pour le gold
"""

import pandas as pd
import geopandas as gpd
import numpy as np
from shapely import from_wkt
from shapely.validation import make_valid
from pathlib import Path

# ── Chemins ───────────────────────────────────────────────────────────────────

EV_BRONZE   = Path("data/bronze/bronze_SVP/espaces_verts_raw.parquet")
ARB_BRONZE  = Path("data/bronze/bronze_SVP/arbres_raw.parquet")
EV_SILVER   = Path("data/silver/silver_SVP/espaces_verts_clean.parquet")
ARB_SILVER  = Path("data/silver/silver_SVP/arbres_clean.parquet")

# CRS Lambert-93 (EPSG:2154) pour les calculs de distance en mètres
CRS_METRIC = "EPSG:2154"
CRS_WGS84  = "EPSG:4326"

# Surface minimale pour qu'un espace vert soit retenu (évite les micro-jardins)
SURFACE_MIN_M2 = 100


# ──────────────────────────────────────────────────────────────────────────────
# UTILITAIRES
# ──────────────────────────────────────────────────────────────────────────────

def parquet_to_gdf(path: Path, crs: str = CRS_WGS84) -> gpd.GeoDataFrame:
    """
    Relit un parquet bronzé (géométrie en WKT) et retourne un GeoDataFrame.
    """
    df = pd.read_parquet(path)
    if "geometry_wkt" not in df.columns:
        raise ValueError(f"Colonne 'geometry_wkt' introuvable dans {path}")
    geom = df["geometry_wkt"].apply(lambda w: from_wkt(w) if pd.notna(w) else None)
    gdf = gpd.GeoDataFrame(df.drop(columns=["geometry_wkt"]), geometry=geom, crs=crs)
    return gdf


def gdf_to_parquet(gdf: gpd.GeoDataFrame, path: Path) -> None:
    """Sérialise un GeoDataFrame en parquet via WKT."""
    path.parent.mkdir(parents=True, exist_ok=True)
    df = pd.DataFrame(gdf.copy())
    df["geometry_wkt"] = gdf.geometry.to_wkt()
    df = df.drop(columns=["geometry"], errors="ignore")
    df.to_parquet(path, index=False)
    print(f"  Sauvegardé : {path}  ({path.stat().st_size / 1024:.0f} KB)")


# ──────────────────────────────────────────────────────────────────────────────
# SILVER ESPACES VERTS
# ──────────────────────────────────────────────────────────────────────────────

def clean_espaces_verts(path: Path) -> gpd.GeoDataFrame:
    print("  Chargement espaces verts bronze…")
    gdf = parquet_to_gdf(path)
    n0 = len(gdf)
    print(f"  Lignes bronze : {n0:,}")

    # 1. Suppression géométries nulles
    gdf = gdf[gdf.geometry.notna()].copy()
    print(f"  Après suppression géom. nulles : {len(gdf):,}  (-{n0 - len(gdf)})")

    # 2. Réparation géométries invalides
    gdf["geometry"] = gdf.geometry.apply(
        lambda g: make_valid(g) if not g.is_valid else g
    )

    # 3. Projeter en Lambert-93 pour les calculs métriques
    gdf_m = gdf.to_crs(CRS_METRIC)

    # 4. Calcul surface en m²
    gdf_m["surface_m2"] = gdf_m.geometry.area.round(1)

    # 5. Filtre surface minimale
    n1 = len(gdf_m)
    gdf_m = gdf_m[gdf_m["surface_m2"] >= SURFACE_MIN_M2]
    print(f"  Après filtre surface ≥ {SURFACE_MIN_M2} m² : "
          f"{len(gdf_m):,}  (-{n1 - len(gdf_m)})")

    # 6. Centroïdes (pour le spatial join avec les rues)
    gdf_m["centroid_geom"] = gdf_m.geometry.centroid

    # 7. Retour en WGS84 : centroïde + géométrie complète
    gdf_m_wgs = gdf_m.to_crs(CRS_WGS84)
    gdf_m_wgs["centroid_geom"] = (
        gdf_m["centroid_geom"]
        .set_crs(CRS_METRIC)
        .to_crs(CRS_WGS84)
    )
    gdf_m_wgs["lon_centroid"] = gdf_m_wgs["centroid_geom"].x
    gdf_m_wgs["lat_centroid"] = gdf_m_wgs["centroid_geom"].y

    # 8. Colonnes utiles
    cols_keep = [
        "surface_m2",
        "lon_centroid",
        "lat_centroid",
        # On garde les colonnes attributaires si présentes
        *[c for c in ["nom_ev", "type_ev", "arrondissement", "categorie"]
          if c in gdf_m_wgs.columns],
    ]
    # Colonnes alternatives selon la source (API Paris vs fichier local)
    for alias in [("libelle", "nom_ev"), ("type", "type_ev"),
                  ("adresse_codepostal", "arrondissement")]:
        if alias[0] in gdf_m_wgs.columns and alias[1] not in gdf_m_wgs.columns:
            gdf_m_wgs = gdf_m_wgs.rename(columns={alias[0]: alias[1]})
            if alias[1] not in cols_keep:
                cols_keep.append(alias[1])

    cols_final = [c for c in cols_keep if c in gdf_m_wgs.columns]
    result = gdf_m_wgs[cols_final + ["geometry"]].copy()
    result = result.set_geometry("geometry")

    print(f"  [OK] {len(result):,} espaces verts propres")
    print(f"  [OK] Surface médiane : {result['surface_m2'].median():,.0f} m²")
    return result


# ──────────────────────────────────────────────────────────────────────────────
# SILVER ARBRES
# ──────────────────────────────────────────────────────────────────────────────

def clean_arbres(path: Path) -> gpd.GeoDataFrame:
    print("  Chargement arbres bronze…")
    gdf = parquet_to_gdf(path)
    n0 = len(gdf)
    print(f"  Lignes bronze : {n0:,}")

    # 1. Géométries nulles
    gdf = gdf[gdf.geometry.notna()].copy()
    print(f"  Après suppression géom. nulles : {len(gdf):,}  (-{n0 - len(gdf)})")

    # 2. Vérifier que ce sont des Points (les arbres doivent être ponctuels)
    n1 = len(gdf)
    gdf = gdf[gdf.geom_type == "Point"]
    if len(gdf) < n1:
        print(f"  [WARN] {n1 - len(gdf)} non-Points supprimés")

    # 3. Dédoublonnage sur la position géographique (arrondi à 5 décimales ≈ 1m)
    gdf["_lon_round"] = gdf.geometry.x.round(5)
    gdf["_lat_round"] = gdf.geometry.y.round(5)
    n2 = len(gdf)
    gdf = gdf.drop_duplicates(subset=["_lon_round", "_lat_round"])
    gdf = gdf.drop(columns=["_lon_round", "_lat_round"])
    print(f"  Après dédoublonnage position : {len(gdf):,}  (-{n2 - len(gdf)} doublons)")

    # 4. Coordonnées directes pour les calculs
    gdf["lon"] = gdf.geometry.x
    gdf["lat"] = gdf.geometry.y

    # 5. Bbox Paris intramuros
    n3 = len(gdf)
    gdf = gdf[
        gdf["lon"].between(2.22, 2.47) &
        gdf["lat"].between(48.81, 48.91)
    ]
    print(f"  Après filtre bbox Paris : {len(gdf):,}  (-{n3 - len(gdf)})")

    # 6. Colonnes utiles
    cols_keep = ["lon", "lat", "geometry"]
    for col in ["typeemplacement", "genre", "espece", "varieteoucultivar",
                "stadedeveloppement", "remarquable",
                # noms alternatifs selon la source
                "type", "espece_latin", "species"]:
        if col in gdf.columns:
            cols_keep.append(col)

    result = gdf[[c for c in cols_keep if c in gdf.columns]].copy()
    result = result.set_geometry("geometry")

    print(f"  [OK] {len(result):,} arbres propres")
    if "typeemplacement" in result.columns:
        print(f"  [OK] Types emplacement : "
              f"{result['typeemplacement'].value_counts().head(3).to_dict()}")
    return result


# ──────────────────────────────────────────────────────────────────────────────
# VALIDATION SILVER
# ──────────────────────────────────────────────────────────────────────────────

def validate_ev(gdf: gpd.GeoDataFrame) -> None:
    assert len(gdf) > 0, "Table espaces verts vide après silver"
    assert "surface_m2" in gdf.columns, "Colonne surface_m2 manquante"
    assert (gdf["surface_m2"] >= SURFACE_MIN_M2).all(), \
        "Des espaces verts sous le seuil surface sont présents"
    assert gdf.geometry.isna().sum() == 0, "Géométries nulles résiduelles"
    print(f"  [OK] {len(gdf):,} espaces verts validés")


def validate_arb(gdf: gpd.GeoDataFrame) -> None:
    assert len(gdf) > 0, "Table arbres vide après silver"
    assert "lon" in gdf.columns and "lat" in gdf.columns
    assert gdf["lon"].between(2.22, 2.47).all(), "Longitudes hors Paris"
    assert gdf["lat"].between(48.81, 48.91).all(), "Latitudes hors Paris"
    assert gdf.geometry.isna().sum() == 0, "Géométries nulles résiduelles"
    print(f"  [OK] {len(gdf):,} arbres validés")


# ──────────────────────────────────────────────────────────────────────────────
# POINT D'ENTRÉE
# ──────────────────────────────────────────────────────────────────────────────

def run() -> tuple[gpd.GeoDataFrame, gpd.GeoDataFrame]:
    print("=== SILVER SVP : Espaces verts & Arbres ===")

    print("\n  -- Espaces verts --")
    ev = clean_espaces_verts(EV_BRONZE)
    validate_ev(ev)
    gdf_to_parquet(ev, EV_SILVER)

    print("\n  -- Arbres --")
    arb = clean_arbres(ARB_BRONZE)
    validate_arb(arb)
    gdf_to_parquet(arb, ARB_SILVER)

    return ev, arb


if __name__ == "__main__":
    run()

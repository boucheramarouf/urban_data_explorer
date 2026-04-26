"""
GOLD — Calcul SVP par point de grille (autonome, sans dépendance ITR)
======================================================================
Calcule le Score de Verdure et Proximité (SVP) sur une grille régulière
de points couvrant Paris intramuros, puis exporte le résultat.

Aucune dépendance aux données ITR. Fonctionne de manière totalement
indépendante. Le merge avec l'ITR se fait côté frontend/API si souhaité.

Entrées (toutes dans silver_SVP — générées par le pipeline SVP) :
    data/silver/silver_SVP/espaces_verts_clean.parquet
    data/silver/silver_SVP/arbres_clean.parquet
    data/silver/silver_SVP/commerces_alim_clean.parquet

Référentiel spatial interne (livré avec le projet) :
    data/bronze/bronze_ITR/iris_geo_raw.gpkg   ← polygones IRIS Paris
    → Utilisé uniquement pour retrouver l'arrondissement de chaque point.
    → Ne dépend PAS du pipeline ITR (bronze déjà présent dans le zip).

Sorties :
    data/gold/gold_SVP/svp_par_point.parquet
    data/gold/gold_SVP/svp_par_point.geojson   ← livraison API / carte

Grille de calcul :
    Résolution : 150 m (espacement entre les points)
    Emprise   : Paris intramuros (bbox Lambert-93)
    Résultat  : ~3 400 points, chacun représentant un micro-quartier

Formule :
    score_vert       = 0.5 × norm(nb_espaces_verts_200m)
                     + 0.5 × norm(nb_arbres_200m)

    score_acces_alim = norm(score_alim_brut_500m)

    SVP = 0.60 × score_vert + 0.40 × score_acces_alim   ∈ [0, 100]

Normalisation : Min-Max sur l'ensemble des points parisiens.
"""

import pandas as pd
import geopandas as gpd
import numpy as np
import json
from pathlib import Path
from pyproj import Transformer
from shapely.geometry import Point
from shapely import from_wkt

# ── Chemins ───────────────────────────────────────────────────────────────────

EV_SILVER   = Path("data/silver/silver_SVP/espaces_verts_clean.parquet")
ARB_SILVER  = Path("data/silver/silver_SVP/arbres_clean.parquet")
COM_SILVER  = Path("data/silver/silver_SVP/commerces_alim_clean.parquet")
IRIS_GPKG   = Path("data/bronze/bronze_ITR/iris_geo_raw.gpkg")

OUT_PARQUET = Path("data/gold/gold_SVP/svp_par_point.parquet")
OUT_GEOJSON = Path("data/gold/gold_SVP/svp_par_point.geojson")

# ── Paramètres grille ─────────────────────────────────────────────────────────

# Bbox Paris intramuros en Lambert-93 (EPSG:2154)
GRID_X_MIN, GRID_X_MAX = 648_500, 660_500
GRID_Y_MIN, GRID_Y_MAX = 6_858_500, 6_871_000
GRID_PAS_M = 150        # espacement en mètres

# ── Paramètres géospatiaux ────────────────────────────────────────────────────

RAYON_VERT_M = 200      # rayon espaces verts + arbres
RAYON_ALIM_M = 500      # rayon commerces alimentaires
CRS_METRIC   = "EPSG:2154"
CRS_WGS84    = "EPSG:4326"

# ── Pondérations ─────────────────────────────────────────────────────────────

W_VERT = 0.60
W_ALIM = 0.40

# ── Labels SVP ───────────────────────────────────────────────────────────────

LABELS_SVP = ["Très faible", "Faible", "Modéré", "Bon", "Excellent"]
BINS_SVP   = [0, 20, 40, 60, 80, 100]


# ──────────────────────────────────────────────────────────────────────────────
# 1. GÉNÉRATION DE LA GRILLE DE POINTS
# ──────────────────────────────────────────────────────────────────────────────

def build_grid() -> gpd.GeoDataFrame:
    """
    Génère une grille régulière de points espacés de GRID_PAS_M mètres
    sur la bbox Paris intramuros (Lambert-93), puis :
        1. Convertit chaque point en WGS84 (lon/lat)
        2. Filtre les points hors Paris via un spatial join sur les IRIS

    Retourne un GeoDataFrame WGS84 avec colonnes :
        lon, lat, arrondissement, code_postal, code_iris, geometry
    """
    print(f"  Génération de la grille ({GRID_PAS_M}m)…")

    t_to_wgs = Transformer.from_crs(CRS_METRIC, CRS_WGS84, always_xy=True)

    xs = np.arange(GRID_X_MIN, GRID_X_MAX, GRID_PAS_M)
    ys = np.arange(GRID_Y_MIN, GRID_Y_MAX, GRID_PAS_M)

    rows = []
    for x in xs:
        for y in ys:
            lon, lat = t_to_wgs.transform(x, y)
            rows.append({"lon": round(lon, 6), "lat": round(lat, 6),
                         "geometry": Point(lon, lat)})

    grille = gpd.GeoDataFrame(rows, crs=CRS_WGS84)
    print(f"  Grille brute : {len(grille):,} points")

    # Charger les polygones IRIS pour filtrer Paris et obtenir l'arrondissement
    iris = gpd.read_file(IRIS_GPKG, layer="iris_ge")[["CODE_IRIS", "geometry"]]

    # Dériver arrondissement et code_postal depuis CODE_IRIS (format '751XXYYYY')
    # Les 3 premiers chiffres = dép (751), suivis de 2 chiffres arrondissement
    iris["arrondissement"] = iris["CODE_IRIS"].str[3:5].astype(int)
    iris["code_postal"]    = "750" + iris["CODE_IRIS"].str[3:5]
    iris["code_iris"]      = iris["CODE_IRIS"]

    # Spatial join : ne garder que les points dans un IRIS parisien
    joined = gpd.sjoin(
        grille,
        iris[["CODE_IRIS", "arrondissement", "code_postal", "code_iris", "geometry"]],
        how="inner",
        predicate="within",
    ).drop(columns=["index_right", "CODE_IRIS"], errors="ignore")

    print(f"  Points dans Paris (dans un IRIS) : {len(joined):,}")
    return joined.reset_index(drop=True)


# ──────────────────────────────────────────────────────────────────────────────
# 2. CHARGEMENT DES SILVER SVP
# ──────────────────────────────────────────────────────────────────────────────

def _parquet_to_gdf(path: Path) -> gpd.GeoDataFrame:
    """Relit un parquet silver (geometry_wkt) en GeoDataFrame WGS84."""
    df = pd.read_parquet(path)
    geom = df["geometry_wkt"].apply(lambda w: from_wkt(w) if pd.notna(w) else None)
    return gpd.GeoDataFrame(df.drop(columns=["geometry_wkt"]),
                            geometry=geom, crs=CRS_WGS84)


def load_silver() -> tuple[gpd.GeoDataFrame, gpd.GeoDataFrame, gpd.GeoDataFrame]:
    """Charge les trois couches silver SVP."""
    ev  = _parquet_to_gdf(EV_SILVER)
    arb = _parquet_to_gdf(ARB_SILVER)
    com = _parquet_to_gdf(COM_SILVER)
    print(f"  Espaces verts : {len(ev):,}")
    print(f"  Arbres        : {len(arb):,}")
    print(f"  Commerces     : {len(com):,}")
    return ev, arb, com


# ──────────────────────────────────────────────────────────────────────────────
# 3. COMPTAGE SPATIAL PAR RAYON
# ──────────────────────────────────────────────────────────────────────────────

def count_within_radius(
    points_m: gpd.GeoDataFrame,
    targets_m: gpd.GeoDataFrame,
    radius_m: float,
    col_name: str,
    weight_col: str | None = None,
) -> pd.Series:
    """
    Pour chaque point de points_m, compte les éléments de targets_m
    dans un rayon radius_m (unités métriques — Lambert-93).

    Si weight_col est fourni → somme des poids (score pondéré).
    Sinon → comptage simple.

    Retourne une Series indexée sur points_m.index.
    """
    buffers = points_m.copy()
    buffers["geometry"] = points_m.geometry.buffer(radius_m)

    joined = gpd.sjoin(targets_m, buffers[["geometry"]],
                       how="inner", predicate="within")

    if weight_col and weight_col in joined.columns:
        agg = joined.groupby("index_right")[weight_col].sum()
    else:
        agg = joined.groupby("index_right").size()

    result = agg.reindex(points_m.index, fill_value=0).astype(float)
    result.name = col_name
    return result


# ──────────────────────────────────────────────────────────────────────────────
# 4. CALCUL SVP
# ──────────────────────────────────────────────────────────────────────────────

def _normalize(s: pd.Series) -> pd.Series:
    """Normalisation Min-Max → [0, 1]. Retourne 0 si toutes valeurs identiques."""
    s_min, s_max = s.min(), s.max()
    if s_max == s_min:
        return pd.Series(np.zeros(len(s)), index=s.index)
    return (s - s_min) / (s_max - s_min)


def compute_svp(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calcule les composantes et le score SVP final.

    score_vert       = 0.5 × norm(nb_espaces_verts) + 0.5 × norm(nb_arbres)
    score_acces_alim = norm(score_alim_brut)
    SVP              = 0.60 × score_vert + 0.40 × score_acces_alim  → [0, 100]
    """
    df = df.copy()

    df["score_vert"]       = (0.5 * _normalize(df["nb_espaces_verts"])
                             + 0.5 * _normalize(df["nb_arbres"]))
    df["score_acces_alim"] = _normalize(df["score_alim_brut"])

    df["svp_brut"] = W_VERT * df["score_vert"] + W_ALIM * df["score_acces_alim"]

    # Re-normalisation globale pour maximiser le spread 0–100
    svp_min, svp_max = df["svp_brut"].min(), df["svp_brut"].max()
    if svp_max > svp_min:
        df["svp_score"] = (100 * (df["svp_brut"] - svp_min)
                          / (svp_max - svp_min)).round(2)
    else:
        df["svp_score"] = 0.0

    df["svp_label"] = pd.cut(
        df["svp_score"],
        bins=BINS_SVP,
        labels=LABELS_SVP,
        include_lowest=True,
    ).astype(str)

    print(f"  svp_score : "
          f"min={df['svp_score'].min():.1f}  "
          f"médiane={df['svp_score'].median():.1f}  "
          f"max={df['svp_score'].max():.1f}")
    return df


# ──────────────────────────────────────────────────────────────────────────────
# 5. MISE EN FORME FINALE
# ──────────────────────────────────────────────────────────────────────────────

def finalize(df: pd.DataFrame) -> pd.DataFrame:
    cols = [
        # Identifiants géographiques
        "arrondissement",
        "code_postal",
        "code_iris",
        # Coordonnées GPS du point de grille
        "lon",
        "lat",
        # Comptages bruts
        "nb_espaces_verts",
        "nb_arbres",
        "score_alim_brut",
        # Composantes normalisées [0,1]
        "score_vert",
        "score_acces_alim",
        "svp_brut",
        # Score final
        "svp_score",
        "svp_label",
    ]
    return df[[c for c in cols if c in df.columns]]


# ──────────────────────────────────────────────────────────────────────────────
# 6. STATS TERMINAUX
# ──────────────────────────────────────────────────────────────────────────────

def print_stats(df: pd.DataFrame) -> None:
    print("\n  ── Distribution par niveau SVP ──")
    dist = (df["svp_label"].value_counts()
            .reindex(LABELS_SVP).fillna(0).astype(int))
    for label, count in dist.items():
        pct = count / len(df) * 100
        bar = "█" * int(pct / 2)
        print(f"  {label:<15} {count:>5} points  {pct:>5.1f}%  {bar}")

    print(f"\n  ── Top 5 arrondissements les plus VERTS ──")
    by_arr = (df.groupby("arrondissement")["svp_score"]
              .median().sort_values(ascending=False).head(5))
    for arr, score in by_arr.items():
        print(f"  [{score:>5.1f}] {arr}e arrondissement")

    print(f"\n  ── Top 5 arrondissements les plus GRIS ──")
    by_arr_bot = (df.groupby("arrondissement")["svp_score"]
                  .median().sort_values(ascending=True).head(5))
    for arr, score in by_arr_bot.items():
        print(f"  [{score:>5.1f}] {arr}e arrondissement")


# ──────────────────────────────────────────────────────────────────────────────
# 7. EXPORT GEOJSON
# ──────────────────────────────────────────────────────────────────────────────

def to_geojson(df: pd.DataFrame, path: Path) -> None:
    """GeoJSON FeatureCollection — chaque point = 1 Feature."""
    features = []
    prop_cols = [c for c in df.columns if c not in ("lon", "lat")]

    for _, row in df.iterrows():
        props = {}
        for col in prop_cols:
            val = row[col]
            if isinstance(val, (np.integer,)):
                props[col] = int(val)
            elif isinstance(val, (np.floating,)) and not np.isnan(val):
                props[col] = round(float(val), 4)
            elif pd.isna(val):
                props[col] = None
            else:
                props[col] = val

        features.append({
            "type": "Feature",
            "geometry": {
                "type": "Point",
                "coordinates": [round(float(row["lon"]), 6),
                                round(float(row["lat"]), 6)],
            },
            "properties": props,
        })

    geojson = {
        "type": "FeatureCollection",
        "crs": {"type": "name", "properties": {"name": "EPSG:4326"}},
        "features": features,
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(geojson, f, ensure_ascii=False, separators=(",", ":"))
    print(f"  GeoJSON : {path}  "
          f"({path.stat().st_size / 1024:.0f} KB, {len(features)} features)")


# ──────────────────────────────────────────────────────────────────────────────
# 8. VALIDATION
# ──────────────────────────────────────────────────────────────────────────────

def validate(df: pd.DataFrame) -> None:
    assert "svp_score" in df.columns, "Colonne svp_score manquante"
    assert df["svp_score"].between(0, 100).all(), "Scores hors [0, 100]"
    assert df["svp_score"].isna().sum() == 0, "NaN dans svp_score"
    assert df["lon"].between(2.22, 2.47).all(), "Longitudes hors Paris"
    assert df["lat"].between(48.82, 48.94).all(), "Latitudes hors Paris"
    print(f"\n  [OK] {len(df):,} points avec score SVP valide")
    print(f"  [OK] Scores dans [0, 100]")
    print(f"  [OK] Coordonnées dans la bbox Paris")


# ──────────────────────────────────────────────────────────────────────────────
# 9. RUN
# ──────────────────────────────────────────────────────────────────────────────

def run() -> pd.DataFrame:
    print("=== GOLD SVP : Score de Verdure et Proximité (autonome) ===")

    # ── Grille de points Paris ───────────────────────────────────────────────
    print("\n  Étape 1 — Génération de la grille de points…")
    grille = build_grid()

    # ── Chargement des couches silver SVP ────────────────────────────────────
    print("\n  Étape 2 — Chargement des données silver SVP…")
    ev, arb, com = load_silver()

    # ── Projection Lambert-93 pour les calculs de distance ──────────────────
    print("\n  Étape 3 — Projection Lambert-93…")
    grille_m = grille.to_crs(CRS_METRIC)
    ev_m     = ev.to_crs(CRS_METRIC)
    arb_m    = arb.to_crs(CRS_METRIC)
    com_m    = com.to_crs(CRS_METRIC)

    # ── Comptages spatiaux par rayon ─────────────────────────────────────────
    print(f"\n  Étape 4 — Comptages spatiaux…")

    print(f"  → Espaces verts dans {RAYON_VERT_M}m…")
    grille_m["nb_espaces_verts"] = count_within_radius(
        grille_m, ev_m, RAYON_VERT_M, "nb_espaces_verts"
    )
    n_ev = (grille_m["nb_espaces_verts"] > 0).sum()
    print(f"    Points avec ≥1 espace vert : {n_ev:,} / {len(grille_m):,}")

    print(f"  → Arbres dans {RAYON_VERT_M}m…")
    grille_m["nb_arbres"] = count_within_radius(
        grille_m, arb_m, RAYON_VERT_M, "nb_arbres"
    )
    n_arb = (grille_m["nb_arbres"] > 0).sum()
    print(f"    Points avec ≥1 arbre : {n_arb:,} / {len(grille_m):,}")

    print(f"  → Commerces alimentaires dans {RAYON_ALIM_M}m (pondéré)…")
    grille_m["score_alim_brut"] = count_within_radius(
        grille_m, com_m, RAYON_ALIM_M, "score_alim_brut",
        weight_col="poids",
    )
    n_com = (grille_m["score_alim_brut"] > 0).sum()
    print(f"    Points avec ≥1 commerce alim : {n_com:,} / {len(grille_m):,}")

    # ── Calcul SVP ────────────────────────────────────────────────────────────
    print("\n  Étape 5 — Calcul SVP…")
    df = grille_m.drop(columns=["geometry"]).copy()
    df["lon"] = grille["lon"].values
    df["lat"] = grille["lat"].values

    df = compute_svp(df)
    df = finalize(df)

    validate(df)
    print_stats(df)

    # ── Export ────────────────────────────────────────────────────────────────
    print("\n  Étape 6 — Export…")
    OUT_PARQUET.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(OUT_PARQUET, index=False)
    print(f"  Parquet : {OUT_PARQUET}  "
          f"({OUT_PARQUET.stat().st_size / 1024:.0f} KB)")

    to_geojson(df, OUT_GEOJSON)

    return df


if __name__ == "__main__":
    run()

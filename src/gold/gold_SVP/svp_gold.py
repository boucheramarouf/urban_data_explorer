"""
GOLD - Calcul SVP par rue
=========================
Aligne le calcul SVP sur la meme maille que l'ITR : une ligne = une rue.

Entrees :
    data/gold/gold_ITR/itr_par_rue.parquet
    data/silver/silver_SVP/espaces_verts_clean.parquet
    data/silver/silver_SVP/arbres_clean.parquet
    data/silver/silver_SVP/commerces_alim_clean.parquet

Sorties :
    data/gold/gold_SVP/svp_par_rue.parquet
    data/gold/gold_SVP/svp_par_rue.geojson

Principe :
    - Reprendre exactement les rues de l'ITR
    - Utiliser leur point central (lon_centre, lat_centre)
    - Compter autour de chaque rue :
        * espaces verts dans 200 m
        * arbres dans 200 m
        * commerces alimentaires ponderes dans 500 m
    - Normaliser avec log1p + cap P99
    - Produire un score SVP sur 100
"""

from pathlib import Path
import json

import geopandas as gpd
import numpy as np
import pandas as pd
from shapely import from_wkt
from shapely.geometry import Point

ITR_RUES_PATH = Path("data/gold/gold_ITR/itr_par_rue.parquet")
EV_SILVER = Path("data/silver/silver_SVP/espaces_verts_clean.parquet")
ARB_SILVER = Path("data/silver/silver_SVP/arbres_clean.parquet")
COM_SILVER = Path("data/silver/silver_SVP/commerces_alim_clean.parquet")

OUT_PARQUET = Path("data/gold/gold_SVP/svp_par_rue.parquet")
OUT_GEOJSON = Path("data/gold/gold_SVP/svp_par_rue.geojson")

CRS_WGS84 = "EPSG:4326"
CRS_METRIC = "EPSG:2154"

RAYON_VERT_M = 200
RAYON_ALIM_M = 500

W_VERT = 0.60
W_ALIM = 0.40

LABELS_SVP = ["Très faible", "Faible", "Modéré", "Bon", "Excellent"]
BINS_SVP = [0, 20, 40, 60, 80, 100]


def load_rues_itr() -> gpd.GeoDataFrame:
    df = pd.read_parquet(ITR_RUES_PATH)
    df = df.dropna(subset=["nom_voie", "code_postal", "lon_centre", "lat_centre"]).copy()
    df["geometry"] = [Point(lon, lat) for lon, lat in zip(df["lon_centre"], df["lat_centre"])]
    rues = gpd.GeoDataFrame(df, geometry="geometry", crs=CRS_WGS84)
    print(f"  Rues ITR chargees : {len(rues):,}")
    return rues


def _parquet_wkt_to_gdf(path: Path, lon_col: str | None = None, lat_col: str | None = None) -> gpd.GeoDataFrame:
    df = pd.read_parquet(path)
    if "geometry_wkt" in df.columns:
        geom = df["geometry_wkt"].apply(lambda w: from_wkt(w) if pd.notna(w) else None)
        return gpd.GeoDataFrame(df.drop(columns=["geometry_wkt"]), geometry=geom, crs=CRS_WGS84)
    if lon_col and lat_col and lon_col in df.columns and lat_col in df.columns:
        geom = [Point(lon, lat) for lon, lat in zip(df[lon_col], df[lat_col])]
        return gpd.GeoDataFrame(df, geometry=geom, crs=CRS_WGS84)
    raise ValueError(f"Impossible de reconstruire la geometrie pour {path}")


def load_silver_layers() -> tuple[gpd.GeoDataFrame, gpd.GeoDataFrame, gpd.GeoDataFrame]:
    ev = pd.read_parquet(EV_SILVER)
    ev["geometry"] = [Point(lon, lat) for lon, lat in zip(ev["lon_centroid"], ev["lat_centroid"])]
    ev_gdf = gpd.GeoDataFrame(ev.drop(columns=["geometry_wkt"], errors="ignore"), geometry="geometry", crs=CRS_WGS84)

    arb_gdf = _parquet_wkt_to_gdf(ARB_SILVER)
    com_gdf = _parquet_wkt_to_gdf(COM_SILVER)

    print(
        "  Couches silver chargees : "
        f"{len(ev_gdf):,} espaces verts | {len(arb_gdf):,} arbres | {len(com_gdf):,} commerces"
    )
    return ev_gdf, arb_gdf, com_gdf


def count_within_radius(
    anchors_m: gpd.GeoDataFrame,
    targets_m: gpd.GeoDataFrame,
    radius_m: int,
    col_name: str,
    weight_col: str | None = None,
) -> pd.Series:
    buffers = anchors_m[["geometry"]].copy()
    buffers["geometry"] = buffers.geometry.buffer(radius_m)
    joined = gpd.sjoin(targets_m, buffers, how="inner", predicate="within")

    if weight_col and weight_col in joined.columns:
        agg = joined.groupby("index_right")[weight_col].sum()
    else:
        agg = joined.groupby("index_right").size()

    result = agg.reindex(anchors_m.index, fill_value=0).astype(float)
    result.name = col_name
    return result


def _norm_log(s: pd.Series, cap_quantile: float = 0.99) -> pd.Series:
    if s.max() == 0:
        return pd.Series(0.0, index=s.index)

    p99 = s.quantile(cap_quantile)
    s_capped = s.clip(0, p99) if p99 > 0 else s
    s_log = np.log1p(s_capped)
    s_min, s_max = s_log.min(), s_log.max()
    if s_max == s_min:
        return pd.Series(0.0, index=s.index)
    return (s_log - s_min) / (s_max - s_min)


def compute_svp(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    df["n_espaces_verts"] = _norm_log(df["nb_espaces_verts"])
    df["n_arbres"] = _norm_log(df["nb_arbres"])
    df["n_alim"] = _norm_log(df["score_alim_brut"])

    df["score_vert"] = 0.5 * df["n_espaces_verts"] + 0.5 * df["n_arbres"]
    df["score_acces_alim"] = df["n_alim"]
    df["svp_brut"] = W_VERT * df["score_vert"] + W_ALIM * df["score_acces_alim"]
    df["svp_score"] = (df["svp_brut"] * 100).round(2).clip(0, 100)
    df["has_commerce"] = df["score_alim_brut"] > 0

    df["svp_label"] = pd.cut(
        df["svp_score"],
        bins=BINS_SVP,
        labels=LABELS_SVP,
        include_lowest=True,
    ).astype(str)

    print(
        "  svp_score : "
        f"min={df['svp_score'].min():.1f}  "
        f"median={df['svp_score'].median():.1f}  "
        f"max={df['svp_score'].max():.1f}"
    )
    print(f"  Rues sans commerce detecte : {(~df['has_commerce']).sum():,}")
    return df


def finalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    cols = [
        "nom_voie",
        "code_postal",
        "arrondissement",
        "code_iris",
        "lon_centre",
        "lat_centre",
        "nb_espaces_verts",
        "nb_arbres",
        "score_alim_brut",
        "score_vert",
        "score_acces_alim",
        "svp_brut",
        "svp_score",
        "svp_label",
        "has_commerce",
    ]
    return df[[c for c in cols if c in df.columns]]


def validate(df: pd.DataFrame) -> None:
    assert len(df) > 0, "Aucune rue en sortie"
    assert df["svp_score"].between(0, 100).all(), "Scores hors [0, 100]"
    assert df["svp_score"].isna().sum() == 0, "NaN dans svp_score"
    assert df["nom_voie"].notna().all(), "nom_voie manquant"
    assert df["lon_centre"].between(2.2, 2.5).all(), "Longitudes hors Paris"
    assert df["lat_centre"].between(48.8, 48.95).all(), "Latitudes hors Paris"
    print(f"  [OK] {len(df):,} rues valides")


def print_stats(df: pd.DataFrame) -> None:
    print("\n  -- Distribution par niveau SVP --")
    dist = df["svp_label"].value_counts().reindex(LABELS_SVP).fillna(0).astype(int)
    for label, count in dist.items():
        pct = count / len(df) * 100
        print(f"  {label:<11} {count:>5} rues  {pct:>5.1f}%")

    top = df.nlargest(5, "svp_score")[["nom_voie", "arrondissement", "svp_score", "nb_arbres", "score_alim_brut"]]
    print("\n  -- Top 5 rues SVP --")
    for _, row in top.iterrows():
        print(
            f"  [{row['svp_score']:>6.1f}] {row['nom_voie']:<35} "
            f"arr.{int(row['arrondissement']):02d}  "
            f"arbres={int(row['nb_arbres'])}  alim={row['score_alim_brut']:.1f}"
        )


def to_geojson(df: pd.DataFrame, path: Path) -> None:
    prop_cols = [c for c in df.columns if c not in ("lon_centre", "lat_centre")]
    features = []

    for _, row in df.iterrows():
        props = {}
        for col in prop_cols:
            val = row[col]
            if isinstance(val, np.integer):
                props[col] = int(val)
            elif isinstance(val, np.floating):
                props[col] = None if np.isnan(val) else round(float(val), 4)
            elif isinstance(val, (np.bool_, bool)):
                props[col] = bool(val)
            elif pd.isna(val):
                props[col] = None
            else:
                props[col] = val

        features.append(
            {
                "type": "Feature",
                "geometry": {
                    "type": "Point",
                    "coordinates": [round(float(row["lon_centre"]), 6), round(float(row["lat_centre"]), 6)],
                },
                "properties": props,
            }
        )

    geojson = {
        "type": "FeatureCollection",
        "crs": {"type": "name", "properties": {"name": "EPSG:4326"}},
        "features": features,
    }

    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(geojson, f, ensure_ascii=False, separators=(",", ":"))

    print(f"  GeoJSON : {path}  ({len(features)} features)")


def run() -> pd.DataFrame:
    print("=== GOLD SVP : calcul par rue ===")

    rues = load_rues_itr()
    ev, arb, com = load_silver_layers()

    print("\n  Projection Lambert-93...")
    rues_m = rues.to_crs(CRS_METRIC)
    ev_m = ev.to_crs(CRS_METRIC)
    arb_m = arb.to_crs(CRS_METRIC)
    com_m = com.to_crs(CRS_METRIC)

    print(f"\n  Comptages spatiaux sur {len(rues_m):,} rues...")
    rues_m["nb_espaces_verts"] = count_within_radius(rues_m, ev_m, RAYON_VERT_M, "nb_espaces_verts")
    rues_m["nb_arbres"] = count_within_radius(rues_m, arb_m, RAYON_VERT_M, "nb_arbres")
    rues_m["score_alim_brut"] = count_within_radius(
        rues_m,
        com_m,
        RAYON_ALIM_M,
        "score_alim_brut",
        weight_col="poids",
    )

    df = pd.DataFrame(rues_m.drop(columns=["geometry"]))
    df = compute_svp(df)
    df = finalize_columns(df)

    validate(df)
    print_stats(df)

    OUT_PARQUET.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(OUT_PARQUET, index=False)
    print(f"\n  Parquet : {OUT_PARQUET}")
    to_geojson(df, OUT_GEOJSON)

    return df


if __name__ == "__main__":
    run()

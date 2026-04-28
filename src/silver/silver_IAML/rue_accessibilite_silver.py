"""
SILVER — IAML Accessibilite par rue
===================================
Calcule un score d'accessibilite transport dans un rayon de 500m autour
chaque transaction DVF, puis agrege a l'echelle rue.
"""

from pathlib import Path

import geopandas as gpd
import pandas as pd

DVF_BRONZE = Path("data/bronze/bronze_ITR/dvf_raw.parquet")
TRANSPORT_BRONZE = Path("data/bronze/bronze_IAML/transports_points_raw.parquet")
VELIB_BRONZE = Path("data/bronze/bronze_IAML/velib_points_raw.parquet")
OUTPUT_PATH = Path("data/silver/silver_IAML/rue_accessibilite.parquet")

RADIUS_METERS = 500
MIN_SURFACE = 5
MIN_VALUE = 10000


def load_dvf_transactions(path: Path = DVF_BRONZE) -> pd.DataFrame:
    df = pd.read_parquet(path)

    df = df[df["type_local"] == "Appartement"].copy()
    df = df.dropna(
        subset=[
            "valeur_fonciere",
            "surface_reelle_bati",
            "longitude",
            "latitude",
            "adresse_nom_voie",
            "code_postal",
        ]
    ).copy()

    df = df[(df["surface_reelle_bati"] > MIN_SURFACE) & (df["valeur_fonciere"] > MIN_VALUE)].copy()
    df["prix_m2"] = df["valeur_fonciere"] / df["surface_reelle_bati"]

    df["arrondissement"] = pd.to_numeric(df["code_postal"], errors="coerce").fillna(0).astype(int) % 100
    df = df[df["arrondissement"].between(1, 20)].copy()

    df = df.reset_index(drop=True)
    df["tx_id"] = df.index.astype(int)

    return df


def _count_unique_within(
    tx_gdf: gpd.GeoDataFrame,
    points_gdf: gpd.GeoDataFrame,
    key_col: str,
    out_col: str,
) -> pd.DataFrame:
    joined = gpd.sjoin(
        tx_gdf[["tx_id", "geometry"]],
        points_gdf[[key_col, "geometry"]],
        how="left",
        predicate="dwithin",
        distance=RADIUS_METERS,
    )

    counts = joined.groupby("tx_id")[key_col].nunique(dropna=True).rename(out_col)
    return counts.reset_index()


def compute_accessibility(df_tx: pd.DataFrame) -> pd.DataFrame:
    transports = pd.read_parquet(TRANSPORT_BRONZE)
    velib = pd.read_parquet(VELIB_BRONZE)

    tx_gdf = gpd.GeoDataFrame(
        df_tx,
        geometry=gpd.points_from_xy(df_tx["longitude"], df_tx["latitude"]),
        crs="EPSG:4326",
    ).to_crs(epsg=2154)

    tr_gdf = gpd.GeoDataFrame(
        transports,
        geometry=gpd.points_from_xy(transports["lon"], transports["lat"]),
        crs="EPSG:4326",
    ).to_crs(epsg=2154)

    velib_gdf = gpd.GeoDataFrame(
        velib,
        geometry=gpd.points_from_xy(velib["lon"], velib["lat"]),
        crs="EPSG:4326",
    ).to_crs(epsg=2154)

    metro_counts = _count_unique_within(
        tx_gdf,
        tr_gdf[tr_gdf["mode_group"] == "metro"].copy(),
        key_col="line_key",
        out_col="nb_lignes_metro",
    )
    bus_counts = _count_unique_within(
        tx_gdf,
        tr_gdf[tr_gdf["mode_group"] == "bus"].copy(),
        key_col="line_key",
        out_col="nb_lignes_bus",
    )
    velib_counts = _count_unique_within(
        tx_gdf,
        velib_gdf.copy(),
        key_col="point_key",
        out_col="nb_points_velib",
    )

    out = df_tx.merge(metro_counts, on="tx_id", how="left")
    out = out.merge(bus_counts, on="tx_id", how="left")
    out = out.merge(velib_counts, on="tx_id", how="left")

    for col in ["nb_lignes_metro", "nb_lignes_bus", "nb_points_velib"]:
        out[col] = out[col].fillna(0).astype(int)

    out["score_accessibilite_tx"] = out["nb_lignes_metro"] + out["nb_lignes_bus"] + out["nb_points_velib"]
    return out


def aggregate_by_rue(df: pd.DataFrame) -> pd.DataFrame:
    grouped = (
        df.groupby(["adresse_nom_voie", "code_postal", "arrondissement"], as_index=False)
        .agg(
            prix_m2_median=("prix_m2", "median"),
            lon_centre=("longitude", "median"),
            lat_centre=("latitude", "median"),
            nb_transactions=("tx_id", "count"),
            nb_lignes_metro=("nb_lignes_metro", "median"),
            nb_lignes_bus=("nb_lignes_bus", "median"),
            nb_points_velib=("nb_points_velib", "median"),
        )
    )

    for col in ["nb_lignes_metro", "nb_lignes_bus", "nb_points_velib", "nb_transactions"]:
        grouped[col] = grouped[col].round().astype(int)

    grouped["score_accessibilite"] = (
        grouped["nb_lignes_metro"] + grouped["nb_lignes_bus"] + grouped["nb_points_velib"]
    )

    grouped = grouped[grouped["nb_transactions"] >= 3].copy()
    grouped = grouped.rename(columns={"adresse_nom_voie": "nom_voie"})

    return grouped


def validate(df: pd.DataFrame) -> None:
    assert len(df) > 0, "Aucune rue IAML produite"
    assert (df["score_accessibilite"] >= 0).all()
    assert "prix_m2_median" in df.columns
    print(f"  [OK] rues IAML silver : {len(df):,}")
    print(f"  [OK] score accessibilite median : {df['score_accessibilite'].median():.1f}")


def run() -> pd.DataFrame:
    print("=== SILVER : IAML Accessibilite rue ===")
    dvf = load_dvf_transactions()
    dvf = compute_accessibility(dvf)
    rues = aggregate_by_rue(dvf)
    validate(rues)

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    rues.to_parquet(OUTPUT_PATH, index=False)
    print(f"  Sauvegarde : {OUTPUT_PATH}")
    return rues


if __name__ == "__main__":
    run()

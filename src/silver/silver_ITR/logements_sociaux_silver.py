"""
SILVER — Logements sociaux par IRIS
=====================================
Spatial join des programmes logements sociaux vers IRIS, agrégation.

Entrées  : data/bronze/bronze_ITR/logements_sociaux_raw.parquet
           data/bronze/bronze_ITR/iris_geo_raw.gpkg
Sortie   : data/silver/silver_ITR/logements_sociaux_par_iris.parquet
"""

import pandas as pd
import geopandas as gpd
from pathlib import Path

LOGSOC_BRONZE = Path("data/bronze/bronze_ITR/logements_sociaux_raw.parquet")
IRIS_BRONZE   = Path("data/bronze/bronze_ITR/iris_geo_raw.gpkg")
OUTPUT_PATH   = Path("data/silver/silver_ITR/logements_sociaux_par_iris.parquet")


def load_and_prepare(logsoc_path: Path) -> gpd.GeoDataFrame:
    df = pd.read_parquet(logsoc_path)

    df = df.rename(columns={
        "Nombre total de logements finances" : "nb_logements",
        "Nombre total de logements financés" : "nb_logements",
        "Adresse du programme"               : "adresse",
        "Code postal"                        : "code_postal",
        "Arrondissement"                     : "arrondissement",
        "Annee du financement - agrement"    : "annee_financement",
        "Année du financement - agrément"    : "annee_financement",
        "Bailleur social"                    : "bailleur",
    })

    # Fallback si la colonne n'a pas été renommée
    if "nb_logements" not in df.columns:
        for col in df.columns:
            if "logements" in col.lower() and "total" in col.lower():
                df = df.rename(columns={col: "nb_logements"})
                break

    print(f"  Programmes charges : {len(df):,}")
    print(f"  Logements total    : {df['nb_logements'].sum():,}")

    gdf = gpd.GeoDataFrame(
        df,
        geometry=gpd.points_from_xy(df["longitude"], df["latitude"]),
        crs="EPSG:4326",
    )
    return gdf


def spatial_join_iris(gdf: gpd.GeoDataFrame, iris_path: Path) -> pd.DataFrame:
    iris = gpd.read_file(iris_path, layer="iris_ge")

    joined = gpd.sjoin(
        gdf,
        iris[["CODE_IRIS", "geometry"]],
        how="left",
        predicate="within",
    )
    joined = joined.drop(columns=["geometry", "index_right"], errors="ignore")
    df = pd.DataFrame(joined)

    nb_sans_iris = df["CODE_IRIS"].isna().sum()
    print(f"  Programmes sans IRIS : {nb_sans_iris} ({nb_sans_iris / len(df) * 100:.1f}%)")
    return df


def aggregate_by_iris(df: pd.DataFrame) -> pd.DataFrame:
    df_valid = df.dropna(subset=["CODE_IRIS", "nb_logements"]).copy()

    agg = (
        df_valid
        .groupby("CODE_IRIS")
        .agg(
            nb_logements_sociaux=("nb_logements", "sum"),
            nb_programmes=("nb_logements", "count"),
        )
        .reset_index()
    )

    print(f"  IRIS avec logements sociaux : {len(agg)}")
    print(f"  nb_logements_sociaux : "
          f"min={agg['nb_logements_sociaux'].min():.0f}  "
          f"median={agg['nb_logements_sociaux'].median():.0f}  "
          f"max={agg['nb_logements_sociaux'].max():.0f}")
    return agg


def validate(df: pd.DataFrame) -> None:
    assert "CODE_IRIS" in df.columns
    assert "nb_logements_sociaux" in df.columns
    assert df["nb_logements_sociaux"].isna().sum() == 0
    print(f"  [OK] {len(df)} IRIS avec logements sociaux")
    print(f"  [OK] {df['nb_logements_sociaux'].sum():.0f} logements couverts")


def run() -> pd.DataFrame:
    print("=== SILVER : Logements sociaux par IRIS ===")
    gdf = load_and_prepare(LOGSOC_BRONZE)
    df  = spatial_join_iris(gdf, IRIS_BRONZE)
    df  = aggregate_by_iris(df)
    validate(df)
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(OUTPUT_PATH, index=False)
    print(f"  Sauvegarde : {OUTPUT_PATH}  ({OUTPUT_PATH.stat().st_size / 1024:.0f} KB)")
    return df


if __name__ == "__main__":
    run()
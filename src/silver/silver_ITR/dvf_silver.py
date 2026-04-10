"""
SILVER — DVF Appartements
==========================
Nettoyage qualite + calcul prix/m2 + spatial join vers IRIS.

Entrees  : data/bronze/bronze_ITR/dvf_raw.parquet
           data/bronze/bronze_ITR/iris_geo_raw.gpkg
           data/bronze/bronze_ITR/filosofi_iris_raw.parquet
Sortie   : data/silver/silver_ITR/dvf_appart_propre.parquet
"""

import pandas as pd
import geopandas as gpd
import numpy as np
from pathlib import Path

DVF_BRONZE  = Path("data/bronze/bronze_ITR/dvf_raw.parquet")
IRIS_BRONZE = Path("data/bronze/bronze_ITR/iris_geo_raw.gpkg")
FILO_BRONZE = Path("data/bronze/bronze_ITR/filosofi_iris_raw.parquet")
OUTPUT_PATH = Path("data/silver/silver_ITR/dvf_appart_propre.parquet")

MIN_SURFACE = 5
MIN_VALEUR  = 10_000
MAX_PRIX_M2 = 50_000
IQR_FACTOR  = 3


def load_and_filter(dvf_path: Path) -> pd.DataFrame:
    df = pd.read_parquet(dvf_path)

    df = df[df["type_local"] == "Appartement"].copy()
    n0 = len(df)
    print(f"  Appartements bronze          : {n0:>8,}")

    df = df.dropna(subset=["valeur_fonciere", "surface_reelle_bati",
                            "longitude", "latitude", "adresse_nom_voie"])
    print(f"  Apres suppression nulls      : {len(df):>8,}  (-{n0 - len(df):,})")

    n1 = len(df)
    df = df[df["surface_reelle_bati"] > MIN_SURFACE]
    df = df[df["valeur_fonciere"] > MIN_VALEUR]
    print(f"  Apres filtres coherence      : {len(df):>8,}  (-{n1 - len(df):,})")

    df["prix_m2"] = df["valeur_fonciere"] / df["surface_reelle_bati"]

    n2 = len(df)
    df = df[df["prix_m2"] <= MAX_PRIX_M2]
    print(f"  Apres filtre absolu 50000/m2 : {len(df):>8,}  (-{n2 - len(df):,})")

    df["arrondissement"] = (
        pd.to_numeric(df["code_postal"], errors="coerce")
        .fillna(0).astype(int) % 100
    )
    df = df[df["arrondissement"] > 0]

    masks = []
    for arrdt, grp in df.groupby("arrondissement"):
        q1  = grp["prix_m2"].quantile(0.25)
        q3  = grp["prix_m2"].quantile(0.75)
        iqr = q3 - q1
        masks.append(
            grp[(grp["prix_m2"] >= q1 - IQR_FACTOR * iqr) &
                (grp["prix_m2"] <= q3 + IQR_FACTOR * iqr)].index
        )

    idx_ok = [i for m in masks for i in m]
    n3 = len(df)
    df = df.loc[idx_ok]
    print(f"  Apres filtre IQR x{IQR_FACTOR} / arrdt  : {len(df):>8,}  (-{n3 - len(df):,} outliers)")
    print(f"  prix_m2 : min={df['prix_m2'].min():.0f}  "
          f"median={df['prix_m2'].median():.0f}  "
          f"max={df['prix_m2'].max():.0f} euros/m2")

    return df


def spatial_join_iris(df: pd.DataFrame,
                      iris_path: Path,
                      filo_path: Path) -> pd.DataFrame:
    print("  Spatial join DVF -> IRIS ...")

    gdf_dvf = gpd.GeoDataFrame(
        df,
        geometry=gpd.points_from_xy(df["longitude"], df["latitude"]),
        crs="EPSG:4326",
    )

    iris = gpd.read_file(iris_path, layer="iris_ge")

    joined = gpd.sjoin(
        gdf_dvf,
        iris[["CODE_IRIS", "geometry"]],
        how="left",
        predicate="within",
    )
    joined = joined.drop(columns=["geometry", "index_right"], errors="ignore")
    df = pd.DataFrame(joined)

    print(f"  Transactions sans IRIS : {df['CODE_IRIS'].isna().sum()}")

    filo = pd.read_parquet(filo_path)
    filo_paris = (
        filo[filo["IRIS"].str.startswith("751")][["IRIS", "DEC_MED21"]]
        .copy()
        .rename(columns={"IRIS": "CODE_IRIS", "DEC_MED21": "revenu_median_uc"})
    )
    df = df.merge(filo_paris, on="CODE_IRIS", how="left")

    nb_sans_revenu = df["revenu_median_uc"].isna().sum()
    print(f"  Sans revenu median : {nb_sans_revenu} ({nb_sans_revenu / len(df) * 100:.1f}%)")

    return df


def select_columns(df: pd.DataFrame) -> pd.DataFrame:
    cols = [
        "id_mutation", "date_mutation", "nature_mutation",
        "adresse_nom_voie", "code_postal", "arrondissement",
        "valeur_fonciere", "surface_reelle_bati", "prix_m2",
        "nombre_pieces_principales", "longitude", "latitude",
        "CODE_IRIS", "revenu_median_uc",
    ]
    return df[[c for c in cols if c in df.columns]]


def validate(df: pd.DataFrame) -> None:
    assert "prix_m2" in df.columns
    assert "CODE_IRIS" in df.columns
    assert "revenu_median_uc" in df.columns
    assert df["prix_m2"].isna().sum() == 0
    assert df["prix_m2"].max() <= MAX_PRIX_M2
    print(f"  [OK] {len(df):,} transactions propres")
    print(f"  [OK] {df['CODE_IRIS'].notna().sum():,} avec CODE_IRIS")
    print(f"  [OK] {df['revenu_median_uc'].notna().sum():,} avec revenu median")
    print(f"  [OK] Rues uniques : {df['adresse_nom_voie'].nunique():,}")


def run() -> pd.DataFrame:
    print("=== SILVER : DVF Appartements ===")
    df = load_and_filter(DVF_BRONZE)
    df = spatial_join_iris(df, IRIS_BRONZE, FILO_BRONZE)
    df = select_columns(df)
    validate(df)
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(OUTPUT_PATH, index=False)
    print(f"  Sauvegarde : {OUTPUT_PATH}  ({OUTPUT_PATH.stat().st_size / 1024:.0f} KB)")
    return df


if __name__ == "__main__":
    run()
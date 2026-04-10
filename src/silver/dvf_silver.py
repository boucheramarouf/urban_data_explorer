"""
SILVER — DVF Appartements
==========================
Nettoyage qualité + calcul prix/m² + spatial join vers IRIS.

Entrées  : data/bronze/dvf_raw.parquet
           data/bronze/iris_geo_raw.gpkg
           data/bronze/filosofi_iris_raw.parquet
Sortie   : data/silver/dvf_appart_propre.parquet
Lignes   : ~34 580 (après filtres et retrait outliers)
Colonnes clés ajoutées : prix_m2, CODE_IRIS, revenu_median_uc
"""

import pandas as pd
import geopandas as gpd
import numpy as np
from pathlib import Path

DVF_BRONZE   = Path("data/bronze/dvf_raw.parquet")
IRIS_BRONZE  = Path("data/bronze/iris_geo_raw.gpkg")
FILO_BRONZE  = Path("data/bronze/filosofi_iris_raw.parquet")
OUTPUT_PATH  = Path("data/silver/dvf_appart_propre.parquet")

MIN_SURFACE  = 5        # m² minimum
MIN_VALEUR   = 10_000   # € minimum
IQR_FACTOR   = 3        # facteur IQR pour les outliers prix/m²


def load_and_filter(dvf_path: Path) -> pd.DataFrame:
    """Charge le bronze DVF et applique les filtres qualité."""
    df = pd.read_parquet(dvf_path)

    # 1. Garder uniquement les appartements
    df = df[df["type_local"] == "Appartement"].copy()
    n0 = len(df)
    print(f"  Appartements bronze          : {n0:>8,}")

    # 2. Supprimer les nulls sur les colonnes indispensables
    df = df.dropna(subset=["valeur_fonciere", "surface_reelle_bati",
                            "longitude", "latitude", "adresse_nom_voie"])
    print(f"  Après suppression nulls      : {len(df):>8,}  (-{n0 - len(df):,})")

    # 3. Filtres de cohérence physique
    n1 = len(df)
    df = df[df["surface_reelle_bati"] > MIN_SURFACE]
    df = df[df["valeur_fonciere"] > MIN_VALEUR]
    print(f"  Après filtres cohérence      : {len(df):>8,}  (-{n1 - len(df):,})")

    # 4. Calcul du prix au m²
    df["prix_m2"] = df["valeur_fonciere"] / df["surface_reelle_bati"]

    # 5. Retrait des outliers IQR×3 PAR ARRONDISSEMENT
    # code_postal est float64 (ex: 75008.0), peut contenir des NaN residuels
    # → extraction via modulo 100 sur la valeur numerique
    df["arrondissement"] = (
        pd.to_numeric(df["code_postal"], errors="coerce")
        .fillna(0).astype(int) % 100
    )
    df = df[df["arrondissement"] > 0]
    masks = []
    for arrdt, grp in df.groupby("arrondissement"):
        q1 = grp["prix_m2"].quantile(0.25)
        q3 = grp["prix_m2"].quantile(0.75)
        iqr = q3 - q1
        low  = q1 - IQR_FACTOR * iqr
        high = q3 + IQR_FACTOR * iqr
        masks.append(grp[(grp["prix_m2"] >= low) & (grp["prix_m2"] <= high)].index)

    idx_ok = [i for m in masks for i in m]
    n2 = len(df)
    df = df.loc[idx_ok]
    print(f"  Après filtre IQR×{IQR_FACTOR} / arrdt    : {len(df):>8,}  (-{n2 - len(df):,} outliers)")
    print(f"  prix_m2 : min={df['prix_m2'].min():.0f}  "
          f"median={df['prix_m2'].median():.0f}  "
          f"max={df['prix_m2'].max():.0f} €/m²")

    return df


def spatial_join_iris(df: pd.DataFrame,
                      iris_path: Path,
                      filo_path: Path) -> pd.DataFrame:
    """
    Spatial join : rattache à chaque transaction DVF son CODE_IRIS
    puis joint le revenu médian Filosofi correspondant.
    """
    print(f"  Spatial join DVF → IRIS ...")

    # Créer un GeoDataFrame des points DVF
    gdf_dvf = gpd.GeoDataFrame(
        df,
        geometry=gpd.points_from_xy(df["longitude"], df["latitude"]),
        crs="EPSG:4326",
    )

    # Charger les polygones IRIS (déjà en WGS84 depuis bronze)
    iris = gpd.read_file(iris_path, layer="iris_ge")

    # Spatial join : point dans polygone
    joined = gpd.sjoin(
        gdf_dvf,
        iris[["CODE_IRIS", "geometry"]],
        how="left",
        predicate="within",
    )
    joined = joined.drop(columns=["geometry", "index_right"], errors="ignore")
    df = pd.DataFrame(joined)

    nb_sans_iris = df["CODE_IRIS"].isna().sum()
    print(f"  Transactions sans IRIS (hors polygones) : {nb_sans_iris}")

    # Joindre le revenu médian Filosofi
    filo = pd.read_parquet(filo_path)
    filo_paris = (
        filo[filo["IRIS"].str.startswith("751")][["IRIS", "DEC_MED21"]]
        .copy()
        .rename(columns={"IRIS": "CODE_IRIS", "DEC_MED21": "revenu_median_uc"})
    )

    df = df.merge(filo_paris, on="CODE_IRIS", how="left")

    nb_sans_revenu = df["revenu_median_uc"].isna().sum()
    print(f"  Transactions sans revenu médian : {nb_sans_revenu} "
          f"({nb_sans_revenu / len(df) * 100:.1f}%)")

    return df


def select_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Garde uniquement les colonnes utiles pour la suite."""
    cols = [
        "id_mutation",
        "date_mutation",
        "nature_mutation",
        "adresse_nom_voie",
        "code_postal",
        "arrondissement",
        "valeur_fonciere",
        "surface_reelle_bati",
        "prix_m2",
        "nombre_pieces_principales",
        "longitude",
        "latitude",
        "CODE_IRIS",
        "revenu_median_uc",
    ]
    return df[[c for c in cols if c in df.columns]]


def validate(df: pd.DataFrame) -> None:
    assert "prix_m2" in df.columns, "Colonne prix_m2 manquante"
    assert "CODE_IRIS" in df.columns, "Colonne CODE_IRIS manquante"
    assert "revenu_median_uc" in df.columns, "Colonne revenu_median_uc manquante"
    assert df["prix_m2"].isna().sum() == 0, "Nulls dans prix_m2"
    print(f"  [OK] {len(df):,} transactions propres")
    print(f"  [OK] {df['CODE_IRIS'].notna().sum():,} avec CODE_IRIS rattaché")
    print(f"  [OK] {df['revenu_median_uc'].notna().sum():,} avec revenu médian")
    print(f"  [OK] Rues uniques : {df['adresse_nom_voie'].nunique():,}")


def run() -> pd.DataFrame:
    print("=== SILVER : DVF Appartements ===")
    df = load_and_filter(DVF_BRONZE)
    df = spatial_join_iris(df, IRIS_BRONZE, FILO_BRONZE)
    df = select_columns(df)
    validate(df)
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(OUTPUT_PATH, index=False)
    print(f"  Sauvegardé : {OUTPUT_PATH}  ({OUTPUT_PATH.stat().st_size / 1024:.0f} KB)")
    return df


if __name__ == "__main__":
    run()
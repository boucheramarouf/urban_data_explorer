"""
BRONZE — Filosofi IRIS
======================
Ingestion brute de BASE_TD_FILO_IRIS_2021_DEC.csv.
Seul traitement : corriger les virgules décimales françaises → points
et typer DEC_MED21 en float.

Source   : data/raw/BASE_TD_FILO_IRIS_2021_DEC.csv
Sortie   : data/bronze/filosofi_iris_raw.parquet
Lignes   : ~16 026 (tous IRIS France)
Clé      : IRIS (code 9 chiffres, ex: 751010101)
"""

import pandas as pd
from pathlib import Path

RAW_PATH    = Path("data/raw/raw_ITR/BASE_TD_FILO_IRIS_2021_DEC.csv")
OUTPUT_PATH = Path("data/bronze/bronze_ITR/filosofi_iris_raw.parquet")

# Colonnes numériques avec décimales françaises (virgule)
COLS_DECIMAL_FR = [
    "DEC_PIMP21", "DEC_TP6021", "DEC_Q121", "DEC_MED21", "DEC_Q321",
    "DEC_EQ21", "DEC_D121", "DEC_D221", "DEC_D321", "DEC_D421",
    "DEC_D621", "DEC_D721", "DEC_D821", "DEC_D921", "DEC_RD21",
    "DEC_S80S2021", "DEC_GI21", "DEC_PACT21", "DEC_PTSA21",
    "DEC_PCHO21", "DEC_PBEN21", "DEC_PPEN21", "DEC_PAUT21",
]


def load_filosofi(path: Path = RAW_PATH) -> pd.DataFrame:
    df = pd.read_csv(
        path,
        sep=";",
        low_memory=False,
        dtype={"IRIS": "string"},   # garder le code IRIS en string (zéros en tête)
    )

    # Corriger les virgules décimales françaises sur toutes les cols numériques
    for col in COLS_DECIMAL_FR:
        if col in df.columns:
            df[col] = (
                df[col]
                .astype(str)
                .str.replace(",", ".", regex=False)
                .str.strip()
            )
            df[col] = pd.to_numeric(df[col], errors="coerce")

    # DEC_MED21 est entier (pas de virgule dans les données source)
    # mais on le convertit en float pour homogénéité
    if "DEC_MED21" in df.columns:
        df["DEC_MED21"] = pd.to_numeric(df["DEC_MED21"], errors="coerce")

    # DEC_INCERT21 et DEC_NOTE21 sont des indicateurs entiers
    for col in ["DEC_INCERT21", "DEC_NOTE21"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").astype("Int64")

    # Normaliser le code IRIS : toujours 9 caractères avec zéros de tête
    df["IRIS"] = df["IRIS"].str.zfill(9)

    return df


def validate(df: pd.DataFrame) -> None:
    assert "IRIS" in df.columns, "Colonne IRIS manquante"
    assert "DEC_MED21" in df.columns, "Colonne DEC_MED21 manquante"
    assert df.shape[0] > 0, "DataFrame vide"

    iris_len = df["IRIS"].str.len().unique()
    assert list(iris_len) == [9], f"Codes IRIS pas tous à 9 chiffres : {iris_len}"

    nb_paris = df[df["IRIS"].str.startswith("751")].shape[0]
    nb_null_revenu = df["DEC_MED21"].isna().sum()

    print(f"  [OK] {df.shape[0]:,} IRIS France | {nb_paris} IRIS Paris (751xx)")
    print(f"  [OK] DEC_MED21 min={df['DEC_MED21'].min():.0f} € "
          f"max={df['DEC_MED21'].max():.0f} € "
          f"(revenu médian annuel / UC)")
    print(f"  [INFO] Nulls DEC_MED21 : {nb_null_revenu} "
          f"(IRIS sans données revenus, seront exclus en silver)")


def run() -> pd.DataFrame:
    print("=== BRONZE : Filosofi IRIS ===")
    print(f"  Lecture : {RAW_PATH}")
    df = load_filosofi()
    validate(df)
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(OUTPUT_PATH, index=False)
    print(f"  Sauvegardé : {OUTPUT_PATH}  ({OUTPUT_PATH.stat().st_size / 1024:.0f} KB)")
    return df


if __name__ == "__main__":
    run()
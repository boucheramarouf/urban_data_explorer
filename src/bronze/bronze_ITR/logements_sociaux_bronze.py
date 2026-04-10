"""
BRONZE — Logements sociaux Paris
=================================
Ingestion brute du fichier open data Paris.
Seul traitement bronze : parser les coordonnées geo_point_2d (string)
en deux colonnes float lat / lon.

Source   : data/raw/logements-sociaux-finances-a-paris.csv
Sortie   : data/bronze/logements_sociaux_raw.parquet
Lignes   : ~4 174 (programmes financés 2001–2024)
Clé      : Identifiant livraison
"""

import pandas as pd
from pathlib import Path

RAW_PATH    = Path("data/raw/raw_ITR/logements-sociaux-finances-a-paris.csv")
OUTPUT_PATH = Path("data/bronze/bronze_ITR/logements_sociaux_raw.parquet")


def load_logements_sociaux(path: Path = RAW_PATH) -> pd.DataFrame:
    df = pd.read_csv(
        path,
        sep=";",
        low_memory=False,
        dtype={
            "Identifiant livraison"            : "string",
            "Adresse du programme"             : "string",
            "Ville"                            : "string",
            "Bailleur social"                  : "string",
            "Mode de réalisation"              : "string",
            "Commentaires"                     : "string",
            "Nature de programme"              : "string",
            "geo_shape"                        : "string",
            "geo_point_2d"                     : "string",
        },
    )

    # Typage numérique
    df["Code postal"]    = pd.to_numeric(df["Code postal"], errors="coerce").astype("Int64")
    df["Arrondissement"] = pd.to_numeric(df["Arrondissement"], errors="coerce").astype("Int64")
    df["Année du financement - agrément"] = pd.to_numeric(
        df["Année du financement - agrément"], errors="coerce"
    ).astype("Int64")

    cols_logt = [
        "Nombre total de logements financés",
        "Dont nombre de logements PLA I",
        "Dont nombre de logements PLUS",
        "Dont nombre de logements PLUS CD",
        "Dont nombre de logements PLS",
    ]
    for col in cols_logt:
        df[col] = pd.to_numeric(df[col], errors="coerce").astype("Int64")

    # Parser geo_point_2d : format "lat, lon" (string) → deux colonnes float
    # Exemple : "48.83399817959342, 2.398175442412243"
    coords = df["geo_point_2d"].str.split(",", expand=True)
    df["latitude"]  = pd.to_numeric(coords[0].str.strip(), errors="coerce")
    df["longitude"] = pd.to_numeric(coords[1].str.strip(), errors="coerce")

    # Coordonnées Lambert 93 déjà présentes — on les garde telles quelles
    df["Coordonnée en X (L93)"] = pd.to_numeric(df["Coordonnée en X (L93)"], errors="coerce")
    df["Coordonnée en Y (L93)"] = pd.to_numeric(df["Coordonnée en Y (L93)"], errors="coerce")

    return df


def validate(df: pd.DataFrame) -> None:
    assert "Adresse du programme" in df.columns
    assert "Nombre total de logements financés" in df.columns
    assert "latitude" in df.columns and "longitude" in df.columns

    nb_null_coords = df["latitude"].isna().sum()
    total_logt = df["Nombre total de logements financés"].sum()
    annee_min  = df["Année du financement - agrément"].min()
    annee_max  = df["Année du financement - agrément"].max()

    print(f"  [OK] {df.shape[0]:,} programmes | {total_logt:,} logements au total")
    print(f"  [OK] Période : {annee_min} → {annee_max}")
    print(f"  [OK] Coordonnées parsées — nulls lat/lon : {nb_null_coords}")
    print(f"  [OK] Arrondissements couverts : {sorted(df['Arrondissement'].dropna().unique().tolist())}")


def run() -> pd.DataFrame:
    print("=== BRONZE : Logements sociaux ===")
    print(f"  Lecture : {RAW_PATH}")
    df = load_logements_sociaux()
    validate(df)
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(OUTPUT_PATH, index=False)
    print(f"  Sauvegardé : {OUTPUT_PATH}  ({OUTPUT_PATH.stat().st_size / 1024:.0f} KB)")
    return df


if __name__ == "__main__":
    run()
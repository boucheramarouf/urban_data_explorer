"""
BRONZE — DVF
============
Ingestion brute du fichier DVF.csv.
Zéro transformation métier : on type, on renomme proprement, on sauvegarde.

Source   : data/raw/DVF.csv
Sortie   : data/bronze/dvf_raw.parquet
Lignes   : ~81 500 (toutes mutations Paris 2021)
"""

import pandas as pd
from pathlib import Path

RAW_PATH    = Path("data/raw/DVF.csv")
OUTPUT_PATH = Path("data/bronze/dvf_raw.parquet")


def load_dvf(path: Path = RAW_PATH) -> pd.DataFrame:
    df = pd.read_csv(
        path,
        sep=",",
        low_memory=False,
        dtype={
            # Identifiants → string
            "id_mutation"         : "string",
            "id_parcelle"         : "string",
            "ancien_id_parcelle"  : "string",
            "adresse_code_voie"   : "string",
            "code_postal"         : "string",
            "code_commune"        : "string",
            "nom_commune"         : "string",
            "code_departement"    : "string",
            "ancien_code_commune" : "string",
            "ancien_nom_commune"  : "string",
            "adresse_nom_voie"    : "string",
            "adresse_suffixe"     : "string",
            "nature_mutation"     : "string",
            "type_local"          : "string",
            "nature_culture"      : "string",
            "nature_culture_speciale" : "string",
            # Numériques → float (valeurs peuvent être vides)
            "valeur_fonciere"             : "float64",
            "surface_reelle_bati"         : "float64",
            "surface_terrain"             : "float64",
            "longitude"                   : "float64",
            "latitude"                    : "float64",
            "lot1_surface_carrez"         : "float64",
            "lot2_surface_carrez"         : "float64",
            "lot3_surface_carrez"         : "float64",
            "lot4_surface_carrez"         : "float64",
            "lot5_surface_carrez"         : "float64",
            # Entiers → nullable int
            "adresse_numero"              : "Int64",
            "numero_disposition"          : "Int64",
            "nombre_lots"                 : "Int64",
            "code_type_local"             : "Int64",
            "nombre_pieces_principales"   : "Int64",
        },
    )

    # Date
    df["date_mutation"] = pd.to_datetime(df["date_mutation"], format="%Y-%m-%d")

    return df


def validate(df: pd.DataFrame) -> None:
    """Contrôles minimaux bronze : on vérifie qu'on a les colonnes clés."""
    cols_requises = [
        "id_mutation", "date_mutation", "nature_mutation",
        "valeur_fonciere", "adresse_nom_voie", "code_postal",
        "type_local", "surface_reelle_bati",
        "longitude", "latitude",
    ]
    manquantes = [c for c in cols_requises if c not in df.columns]
    assert not manquantes, f"Colonnes manquantes : {manquantes}"
    assert df.shape[0] > 0, "DataFrame vide"
    assert df["code_departement"].dropna().unique().tolist() == ["75"], \
        "Attention : des lignes hors Paris (dep != 75) sont présentes"
    print(f"  [OK] {df.shape[0]:,} lignes | {df.shape[1]} colonnes")
    print(f"  [OK] Période : {df['date_mutation'].min().date()} → {df['date_mutation'].max().date()}")
    print(f"  [OK] type_local : {df['type_local'].value_counts().to_dict()}")
    print(f"  [INFO] Nulls surface_reelle_bati : {df['surface_reelle_bati'].isna().sum():,} "
          f"(seront filtrés en silver)")
    print(f"  [INFO] Nulls longitude : {df['longitude'].isna().sum():,}")


def run() -> pd.DataFrame:
    print("=== BRONZE : DVF ===")
    print(f"  Lecture : {RAW_PATH}")
    df = load_dvf()
    validate(df)
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(OUTPUT_PATH, index=False)
    print(f"  Sauvegardé : {OUTPUT_PATH}  ({OUTPUT_PATH.stat().st_size / 1024:.0f} KB)")
    return df


if __name__ == "__main__":
    run()
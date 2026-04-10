"""
SILVER — Rue enrichie (table pivot finale)
==========================================
Agrégation par rue de toutes les composantes nécessaires au calcul ITR.
C'est la table de sortie Silver qui alimente directement la couche Gold.

Entrées  : data/silver/dvf_appart_propre.parquet
           data/silver/logements_sociaux_par_iris.parquet
Sortie   : data/silver/rue_enrichie.parquet
Lignes   : ~2 379 rues (filtre nb_transactions >= 3)
Colonnes : nom_voie, code_postal, arrondissement, code_iris,
           prix_m2_median, revenu_median_uc, nb_logements_sociaux,
           nb_transactions, lon_centre, lat_centre
"""

import pandas as pd
import numpy as np
from pathlib import Path

DVF_SILVER    = Path("data/silver/silver_ITR/dvf_appart_propre.parquet")
LOGSOC_SILVER = Path("data/silver/silver_ITR/logements_sociaux_par_iris.parquet")
OUTPUT_PATH   = Path("data/silver/silver_ITR/rue_enrichie.parquet")

# Nombre minimum de transactions DVF pour qu'une rue soit exploitable
# En dessous, la médiane des prix/m² n'est pas représentative
MIN_TRANSACTIONS = 3


def aggregate_dvf_par_rue(dvf_path: Path) -> pd.DataFrame:
    """
    Agrège les transactions DVF par rue.

    Clé de rue : (adresse_nom_voie, code_postal)
    → permet de distinguer "RUE DE RIVOLI 75001" de "RUE DE RIVOLI 75004"

    Pour le revenu_median_uc et le CODE_IRIS : on prend le mode
    (valeur la plus fréquente parmi les transactions de la rue),
    ce qui est robuste aux transactions proches d'une frontière IRIS.
    """
    df = pd.read_parquet(dvf_path)

    print(f"  Transactions DVF silver chargées : {len(df):,}")

    # Agrégation par (nom_voie, code_postal)
    def mode_safe(s):
        """Mode pandas-safe : retourne NaN si la série est vide."""
        m = s.mode()
        return m.iloc[0] if len(m) > 0 else np.nan

    agg = (
        df.groupby(["adresse_nom_voie", "code_postal"])
        .agg(
            arrondissement    = ("arrondissement",    "first"),
            prix_m2_median    = ("prix_m2",           "median"),
            prix_m2_mean      = ("prix_m2",           "mean"),
            prix_m2_std       = ("prix_m2",           "std"),
            nb_transactions   = ("prix_m2",           "count"),
            lon_centre        = ("longitude",          "mean"),
            lat_centre        = ("latitude",           "mean"),
            code_iris         = ("CODE_IRIS",          mode_safe),
            revenu_median_uc  = ("revenu_median_uc",   mode_safe),
        )
        .reset_index()
        .rename(columns={"adresse_nom_voie": "nom_voie"})
    )

    print(f"  Rues uniques avant filtre    : {len(agg):,}")

    # Filtrer les rues avec trop peu de transactions
    agg = agg[agg["nb_transactions"] >= MIN_TRANSACTIONS].copy()
    print(f"  Rues avec >= {MIN_TRANSACTIONS} transactions  : {len(agg):,}")

    return agg


def join_logements_sociaux(df_rue: pd.DataFrame,
                           logsoc_path: Path) -> pd.DataFrame:
    """
    Joint le nombre de logements sociaux par IRIS à chaque rue.
    Les rues sans logements sociaux dans leur IRIS reçoivent 0
    (pas de NaN : une valeur nulle = absence de logements sociaux, pas une donnée manquante).
    """
    logsoc = pd.read_parquet(logsoc_path)
    logsoc = logsoc.rename(columns={"CODE_IRIS": "code_iris"})

    df_rue = df_rue.merge(
        logsoc[["code_iris", "nb_logements_sociaux", "nb_programmes"]],
        on="code_iris",
        how="left",
    )

    # Remplir les IRIS sans logements sociaux avec 0
    df_rue["nb_logements_sociaux"] = df_rue["nb_logements_sociaux"].fillna(0).astype(int)
    df_rue["nb_programmes"]        = df_rue["nb_programmes"].fillna(0).astype(int)

    nb_avec_logsoc = (df_rue["nb_logements_sociaux"] > 0).sum()
    print(f"  Rues avec logements sociaux dans leur IRIS : {nb_avec_logsoc} "
          f"({nb_avec_logsoc / len(df_rue) * 100:.1f}%)")
    print(f"  Rues sans logements sociaux (= 0)          : "
          f"{(df_rue['nb_logements_sociaux'] == 0).sum()}")

    return df_rue


def select_and_order(df: pd.DataFrame) -> pd.DataFrame:
    """Sélectionne et ordonne les colonnes pour la livraison Gold."""
    cols = [
        "nom_voie",
        "code_postal",
        "arrondissement",
        "code_iris",
        "prix_m2_median",
        "prix_m2_mean",
        "prix_m2_std",
        "revenu_median_uc",
        "nb_logements_sociaux",
        "nb_programmes",
        "nb_transactions",
        "lon_centre",
        "lat_centre",
    ]
    return df[[c for c in cols if c in df.columns]]


def validate(df: pd.DataFrame) -> None:
    required = [
        "nom_voie", "code_postal", "code_iris",
        "prix_m2_median", "revenu_median_uc",
        "nb_logements_sociaux", "nb_transactions",
        "lon_centre", "lat_centre",
    ]
    for col in required:
        assert col in df.columns, f"Colonne manquante : {col}"

    nb_null_revenu = df["revenu_median_uc"].isna().sum()
    nb_null_iris   = df["code_iris"].isna().sum()
    nb_null_gps    = df["lon_centre"].isna().sum()

    print(f"  [OK] {len(df):,} rues dans la table pivot")
    print(f"  [INFO] Rues sans revenu médian (IRIS sans données) : {nb_null_revenu}")
    print(f"  [INFO] Rues sans CODE_IRIS rattaché                : {nb_null_iris}")
    print(f"  [INFO] Rues sans coordonnées GPS                   : {nb_null_gps}")
    print(f"  [OK] nb_transactions : "
          f"min={df['nb_transactions'].min()}  "
          f"median={df['nb_transactions'].median():.0f}  "
          f"max={df['nb_transactions'].max()}")
    print(f"  [OK] prix_m2_median : "
          f"min={df['prix_m2_median'].min():.0f}  "
          f"median={df['prix_m2_median'].median():.0f}  "
          f"max={df['prix_m2_median'].max():.0f} €/m²")
    print(f"  [OK] revenu_median_uc : "
          f"min={df['revenu_median_uc'].min():.0f}  "
          f"median={df['revenu_median_uc'].median():.0f}  "
          f"max={df['revenu_median_uc'].max():.0f} €/an")


def run() -> pd.DataFrame:
    print("=== SILVER : Rue enrichie (table pivot) ===")
    df_rue = aggregate_dvf_par_rue(DVF_SILVER)
    df_rue = join_logements_sociaux(df_rue, LOGSOC_SILVER)
    df_rue = select_and_order(df_rue)
    validate(df_rue)
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    df_rue.to_parquet(OUTPUT_PATH, index=False)
    print(f"  Sauvegardé : {OUTPUT_PATH}  ({OUTPUT_PATH.stat().st_size / 1024:.0f} KB)")
    return df_rue


if __name__ == "__main__":
    run()
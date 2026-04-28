"""
SILVER — Rue enrichie (table pivot finale)
==========================================
Agrégation par rue de toutes les composantes ITR.

Entrées  : data/silver/silver_ITR/dvf_appart_propre.parquet
           data/silver/silver_ITR/logements_sociaux_par_iris.parquet
Sortie   : data/silver/silver_ITR/rue_enrichie.parquet
"""

import pandas as pd
import numpy as np
from pathlib import Path

DVF_SILVER    = Path("data/silver/silver_ITR/dvf_appart_propre.parquet")
LOGSOC_SILVER = Path("data/silver/silver_ITR/logements_sociaux_par_iris.parquet")
OUTPUT_PATH   = Path("data/silver/silver_ITR/rue_enrichie.parquet")

MIN_TRANSACTIONS = 3


def aggregate_dvf_par_rue(dvf_path: Path) -> pd.DataFrame:
    df = pd.read_parquet(dvf_path)
    print(f"  Transactions DVF silver chargees : {len(df):,}")

    def mode_safe(s):
        m = s.mode()
        return m.iloc[0] if len(m) > 0 else np.nan

    agg = (
        df.groupby(["adresse_nom_voie", "code_postal"])
        .agg(
            arrondissement   = ("arrondissement",   "first"),
            prix_m2_median   = ("prix_m2",          "median"),
            prix_m2_mean     = ("prix_m2",           "mean"),
            prix_m2_std      = ("prix_m2",           "std"),
            nb_transactions  = ("prix_m2",           "count"),
            lon_centre       = ("longitude",          "mean"),
            lat_centre       = ("latitude",           "mean"),
            code_iris        = ("CODE_IRIS",          mode_safe),
            revenu_median_uc = ("revenu_median_uc",   mode_safe),
        )
        .reset_index()
        .rename(columns={"adresse_nom_voie": "nom_voie"})
    )

    print(f"  Rues uniques avant filtre    : {len(agg):,}")
    agg = agg[agg["nb_transactions"] >= MIN_TRANSACTIONS].copy()
    print(f"  Rues avec >= {MIN_TRANSACTIONS} transactions  : {len(agg):,}")
    return agg


def join_logements_sociaux(df_rue: pd.DataFrame,
                           logsoc_path: Path) -> pd.DataFrame:
    logsoc = pd.read_parquet(logsoc_path)
    logsoc = logsoc.rename(columns={"CODE_IRIS": "code_iris"})

    df_rue = df_rue.merge(
        logsoc[["code_iris", "nb_logements_sociaux", "nb_programmes"]],
        on="code_iris",
        how="left",
    )

    df_rue["nb_logements_sociaux"] = df_rue["nb_logements_sociaux"].fillna(0).astype(int)
    df_rue["nb_programmes"]        = df_rue["nb_programmes"].fillna(0).astype(int)

    nb_avec = (df_rue["nb_logements_sociaux"] > 0).sum()
    print(f"  Rues avec logements sociaux dans leur IRIS : {nb_avec} ({nb_avec / len(df_rue) * 100:.1f}%)")
    print(f"  Rues sans logements sociaux (= 0)          : {(df_rue['nb_logements_sociaux'] == 0).sum()}")
    return df_rue


def select_and_order(df: pd.DataFrame) -> pd.DataFrame:
    cols = [
        "nom_voie", "code_postal", "arrondissement", "code_iris",
        "prix_m2_median", "prix_m2_mean", "prix_m2_std",
        "revenu_median_uc", "nb_logements_sociaux", "nb_programmes",
        "nb_transactions", "lon_centre", "lat_centre",
    ]
    return df[[c for c in cols if c in df.columns]]


def validate(df: pd.DataFrame) -> None:
    required = ["nom_voie", "code_postal", "code_iris", "prix_m2_median",
                "revenu_median_uc", "nb_logements_sociaux", "nb_transactions",
                "lon_centre", "lat_centre"]
    for col in required:
        assert col in df.columns, f"Colonne manquante : {col}"

    print(f"  [OK] {len(df):,} rues dans la table pivot")
    print(f"  [INFO] Rues sans revenu median : {df['revenu_median_uc'].isna().sum()}")
    print(f"  [INFO] Rues sans CODE_IRIS     : {df['code_iris'].isna().sum()}")
    print(f"  [INFO] Rues sans GPS           : {df['lon_centre'].isna().sum()}")
    print(f"  [OK] nb_transactions : min={df['nb_transactions'].min()}  "
          f"median={df['nb_transactions'].median():.0f}  "
          f"max={df['nb_transactions'].max()}")
    print(f"  [OK] prix_m2_median : min={df['prix_m2_median'].min():.0f}  "
          f"median={df['prix_m2_median'].median():.0f}  "
          f"max={df['prix_m2_median'].max():.0f} euros/m2")
    print(f"  [OK] revenu_median_uc : min={df['revenu_median_uc'].min():.0f}  "
          f"median={df['revenu_median_uc'].median():.0f}  "
          f"max={df['revenu_median_uc'].max():.0f} euros/an")


def run() -> pd.DataFrame:
    print("=== SILVER : Rue enrichie (table pivot) ===")
    df_rue = aggregate_dvf_par_rue(DVF_SILVER)
    df_rue = join_logements_sociaux(df_rue, LOGSOC_SILVER)
    df_rue = select_and_order(df_rue)
    validate(df_rue)
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    df_rue.to_parquet(OUTPUT_PATH, index=False)
    print(f"  Sauvegarde : {OUTPUT_PATH}  ({OUTPUT_PATH.stat().st_size / 1024:.0f} KB)")
    return df_rue


if __name__ == "__main__":
    run()
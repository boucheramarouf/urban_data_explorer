"""
COUCHE SILVER — Nettoyage et normalisation des données Bronze IMQ
"""

import gc
import os
import sys
import warnings

import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")

BASE_DIR   = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
BRONZE_DIR = os.path.join(BASE_DIR, "data", "bronze", "bronze_IMQ")
SILVER_DIR = os.path.join(BASE_DIR, "data", "silver", "silver_IMQ")
os.makedirs(SILVER_DIR, exist_ok=True)


# ─────────────────────────────────────────────
# 1. DVF+ Silver
# ─────────────────────────────────────────────
print("\n" + "=" * 60)
print("1/4 — DVF+ Silver")
print("=" * 60)

_dvf_silver = os.path.join(SILVER_DIR, "dvf_clean.parquet")
if os.path.exists(_dvf_silver):
    print(f"  Cache trouvé, étape ignorée ({_dvf_silver})")
else:
  try:
    df = pd.read_parquet(os.path.join(BRONZE_DIR, "dvf_raw.parquet"))
    print(f"  Lignes chargées : {len(df):,}")

    # Filtres (bronze a déjà filtré valeurfonc/sbati/libtypbien)
    df["prix_m2"] = df["valeurfonc"] / df["sbati"]
    df = df[(df["prix_m2"] >= 1000) & (df["prix_m2"] <= 30000)]
    print(f"  Après filtre prix_m2 : {len(df):,}")

    # latitude/longitude déjà extraits en bronze (EPSG:4326)
    df = df.dropna(subset=["latitude", "longitude"])
    df = df[(df["longitude"].between(-0.5, 3.5)) & (df["latitude"].between(48.0, 49.5))]
    print(f"  Après filtre coordonnées Paris : {len(df):,}")

    cols = ["idmutation", "datemut", "anneemut", "valeurfonc", "sbati",
            "prix_m2", "libtypbien", "latitude", "longitude"]
    cols = [c for c in cols if c in df.columns]
    df[cols].to_parquet(_dvf_silver, index=False)
    print(f"  Sauvegardé ({len(df):,} lignes)")

    del df
    gc.collect()

  except Exception as e:
    print(f"  ERREUR DVF+ Silver : {e}")
    import traceback; traceback.print_exc()
    sys.exit(1)


# ─────────────────────────────────────────────
# 2. SIRENE Silver
# ─────────────────────────────────────────────
print("\n" + "=" * 60)
print("2/4 — SIRENE Silver")
print("=" * 60)

_sirene_silver = os.path.join(SILVER_DIR, "sirene_clean.parquet")
if os.path.exists(_sirene_silver):
    print(f"  Cache trouvé, étape ignorée ({_sirene_silver})")
else:
  try:
    # Bronze a déjà filtré geo_score, CP 75, NAF
    df = pd.read_parquet(os.path.join(BRONZE_DIR, "sirene_raw.parquet"))
    print(f"  Lignes chargées : {len(df):,}")

    df["statut"] = df["etatAdministratifEtablissement"].map(
        {"A": "ouverture", "F": "fermeture"}
    )
    df["annee_creation"] = pd.to_datetime(
        df["dateCreationEtablissement"], errors="coerce"
    ).dt.year
    df["annee_debut"] = pd.to_datetime(
        df["dateDebut"], errors="coerce"
    ).dt.year

    cols = ["siret", "latitude", "longitude", "activitePrincipaleEtablissement",
            "statut", "annee_creation", "annee_debut", "codePostalEtablissement"]
    cols = [c for c in cols if c in df.columns]
    df[cols].to_parquet(_sirene_silver, index=False)
    print(f"  Sauvegardé ({len(df):,} lignes)")

    del df
    gc.collect()

  except Exception as e:
    print(f"  ERREUR SIRENE Silver : {e}")
    import traceback; traceback.print_exc()
    sys.exit(1)


# ─────────────────────────────────────────────
# 3. LOVAC Silver
# ─────────────────────────────────────────────
print("\n" + "=" * 60)
print("3/4 — LOVAC Silver")
print("=" * 60)

_lovac_silver = os.path.join(SILVER_DIR, "lovac_clean.parquet")
if os.path.exists(_lovac_silver):
    print(f"  Cache trouvé, étape ignorée ({_lovac_silver})")
else:
  try:
    df = pd.read_parquet(os.path.join(BRONZE_DIR, "lovac_raw.parquet"))
    df["CODGEO_25"] = df["CODGEO_25"].astype(str).str.strip()
    df = df[df["CODGEO_25"].str.startswith("75")]
    print(f"  Arrondissements Paris : {len(df)}")

    for year in ["20", "21", "22", "23", "24"]:
        vacant_col = f"pp_vacant_{year}"
        total_col  = f"pp_total_{year}"
        taux_col   = f"taux_vacant_{year}"
        if vacant_col in df.columns and total_col in df.columns:
            vacant = pd.to_numeric(df[vacant_col], errors="coerce")
            total  = pd.to_numeric(df[total_col],  errors="coerce").replace(0, np.nan)
            df[taux_col] = vacant / total
        else:
            df[taux_col] = np.nan

    df["delta_vacance"] = df["taux_vacant_24"] - df["taux_vacant_20"]

    cols = ["CODGEO_25", "taux_vacant_20", "taux_vacant_21", "taux_vacant_22",
            "taux_vacant_23", "taux_vacant_24", "delta_vacance"]
    cols = [c for c in cols if c in df.columns]
    df[cols].to_parquet(_lovac_silver, index=False)
    print(f"  Sauvegardé")

    del df
    gc.collect()

  except Exception as e:
    print(f"  ERREUR LOVAC Silver : {e}")
    import traceback; traceback.print_exc()
    sys.exit(1)


# ─────────────────────────────────────────────
# 4. Filosofi Silver
# ─────────────────────────────────────────────
print("\n" + "=" * 60)
print("4/4 — Filosofi Silver")
print("=" * 60)

_filo_silver = os.path.join(SILVER_DIR, "filosofi_clean.parquet")
if os.path.exists(_filo_silver):
    print(f"  Cache trouvé, étape ignorée ({_filo_silver})")
else:
  try:
    df = pd.read_parquet(os.path.join(BRONZE_DIR, "filosofi_raw.parquet"))
    df["IRIS"] = df["IRIS"].astype(str).str.strip()
    df = df[df["IRIS"].str.startswith("75")]
    print(f"  IRIS parisiens : {len(df):,}")

    rev_col = "DEC_MED21" if "DEC_MED21" in df.columns else "DISP_MED21"
    if rev_col not in df.columns:
        raise ValueError(f"Colonne revenu médian introuvable. Disponibles : {df.columns.tolist()}")

    df[rev_col] = pd.to_numeric(df[rev_col], errors="coerce")
    df = df.dropna(subset=[rev_col])
    df = df[df[rev_col] > 0]
    df = df.rename(columns={rev_col: "DISP_MED21"})

    df[["IRIS", "DISP_MED21"]].to_parquet(_filo_silver, index=False)
    print(f"  Sauvegardé ({len(df):,} lignes)")

    del df
    gc.collect()

  except Exception as e:
    print(f"  ERREUR Filosofi Silver : {e}")
    import traceback; traceback.print_exc()
    sys.exit(1)


print("\n" + "=" * 60)
print("SILVER — Traitement terminé avec succès")
print("=" * 60)
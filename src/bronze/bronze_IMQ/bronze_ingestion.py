"""
COUCHE BRONZE — Ingestion brute des données sources
====================================================
Lit les fichiers sources et les sauvegarde en Parquet sans transformation.
Chaque fichier est ingéré tel quel pour garantir la traçabilité.
"""

import os
import sys
import glob
import pandas as pd
import geopandas as gpd

# ─────────────────────────────────────────────
# Chemins (src/bronze/bronze_IMQ/ → 4 niveaux pour atteindre la racine)
# ─────────────────────────────────────────────
BASE_DIR   = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
RAW_IMQ    = os.path.join(BASE_DIR, "data", "raw", "raw_IMQ")
BRONZE_DIR = os.path.join(BASE_DIR, "data", "bronze", "bronze_IMQ")
os.makedirs(BRONZE_DIR, exist_ok=True)


# ─────────────────────────────────────────────
# 1. DVF+ — Transactions immobilières
# ─────────────────────────────────────────────
print("\n" + "=" * 60)
print("1/4 — DVF+ (GeoPackage)")
print("=" * 60)

try:
    dvf_path = os.path.join(RAW_IMQ, "dvf_plus_d75.gpkg")
    print(f"  Lecture : {dvf_path}")
    gdf = gpd.read_file(dvf_path, layer="mutation")
    print(f"  Lignes brutes      : {len(gdf):,}")

    # Filtre Paris (coddep = '75')
    gdf = gdf[gdf["coddep"] == "75"]
    print(f"  Lignes après filtre coddep='75' : {len(gdf):,}")

    # Sauvegarde (geometry sérialisée en WKT pour compatibilité Parquet)
    out_path = os.path.join(BRONZE_DIR, "dvf_raw.parquet")
    gdf_save = gdf.copy()
    gdf_save["geometry"] = gdf_save["geometry"].astype(str)  # WKT string
    gdf_save.to_parquet(out_path, index=False)
    print(f"  Sauvegardé        : {out_path}")
    print(f"  Colonnes          : {list(gdf.columns)}")

except Exception as e:
    print(f"  ERREUR DVF+ : {e}")
    sys.exit(1)


# ─────────────────────────────────────────────
# 2. SIRENE — Établissements commerciaux
# ─────────────────────────────────────────────
print("\n" + "=" * 60)
print("2/4 — SIRENE (CSV.GZ par arrondissement)")
print("=" * 60)

try:
    sirene_dir = os.path.join(RAW_IMQ, "geo_siret")
    pattern = os.path.join(sirene_dir, "*.csv.gz")
    files = sorted(glob.glob(pattern))

    if not files:
        raise FileNotFoundError(f"Aucun fichier .csv.gz trouvé dans {sirene_dir}")

    print(f"  Fichiers trouvés : {len(files)}")
    dfs = []
    for f in files:
        df_tmp = pd.read_csv(f, compression="gzip", low_memory=False)
        dfs.append(df_tmp)
        print(f"    {os.path.basename(f)} — {len(df_tmp):,} lignes")

    df_sirene = pd.concat(dfs, ignore_index=True)
    print(f"  Total concaténé  : {len(df_sirene):,} lignes")

    out_path = os.path.join(BRONZE_DIR, "sirene_raw.parquet")
    df_sirene.to_parquet(out_path, index=False)
    print(f"  Sauvegardé       : {out_path}")

except Exception as e:
    print(f"  ERREUR SIRENE : {e}")
    sys.exit(1)


# ─────────────────────────────────────────────
# 3. LOVAC — Logements vacants
# ─────────────────────────────────────────────
print("\n" + "=" * 60)
print("3/4 — LOVAC (Excel, feuille 'COM')")
print("=" * 60)

try:
    lovac_path = os.path.join(RAW_IMQ, "lovac-open-data-2020-a-2025-vd.xlsx")
    print(f"  Lecture : {lovac_path}")
    df_lovac = pd.read_excel(lovac_path, sheet_name="COM")
    print(f"  Lignes  : {len(df_lovac):,}")
    print(f"  Colonnes : {list(df_lovac.columns)}")

    out_path = os.path.join(BRONZE_DIR, "lovac_raw.parquet")
    df_lovac.to_parquet(out_path, index=False)
    print(f"  Sauvegardé : {out_path}")

except Exception as e:
    print(f"  ERREUR LOVAC : {e}")
    sys.exit(1)


# ─────────────────────────────────────────────
# 4. Filosofi — Revenus médians par IRIS
# ─────────────────────────────────────────────
print("\n" + "=" * 60)
print("4/4 — Filosofi (CSV, séparateur ';')")
print("=" * 60)

try:
    filo_path = os.path.join(RAW_IMQ, "BASE_TD_FILO_IRIS_2021_DEC.csv")
    print(f"  Lecture : {filo_path}")
    df_filo = pd.read_csv(filo_path, sep=";", low_memory=False)
    print(f"  Lignes   : {len(df_filo):,}")
    print(f"  Colonnes : {list(df_filo.columns)}")

    out_path = os.path.join(BRONZE_DIR, "filosofi_raw.parquet")
    df_filo.to_parquet(out_path, index=False)
    print(f"  Sauvegardé : {out_path}")

except Exception as e:
    print(f"  ERREUR Filosofi : {e}")
    sys.exit(1)


print("\n" + "=" * 60)
print("BRONZE — Ingestion terminée avec succès")
print("=" * 60)

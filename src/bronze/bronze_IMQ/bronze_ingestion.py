import gc
import os
import sys
import glob
import pandas as pd
import geopandas as gpd

BASE_DIR   = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
RAW_IMQ    = os.path.join(BASE_DIR, "data", "raw", "raw_IMQ")
BRONZE_DIR = os.path.join(BASE_DIR, "data", "bronze", "bronze_IMQ")
os.makedirs(BRONZE_DIR, exist_ok=True)


# ─────────────────────────────────────────────
# 1. DVF+
# ─────────────────────────────────────────────
print("\n" + "=" * 60)
print("1/4 — DVF+ (GeoPackage)")
print("=" * 60)

_dvf_out = os.path.join(BRONZE_DIR, "dvf_raw.parquet")
if os.path.exists(_dvf_out):
    print(f"  Cache trouvé, étape ignorée ({_dvf_out})")
else:
  try:
    dvf_path = os.path.join(RAW_IMQ, "dvf_plus_d75.gpkg")
    print(f"  Lecture : {dvf_path}")

    # Lecture sans where/columns pour éviter les crash GDAL selon la version
    gdf = gpd.read_file(dvf_path, layer="mutation")
    print(f"  Lignes brutes : {len(gdf):,}")

    # Filtres en Python
    gdf = gdf[gdf["coddep"] == "75"]

    # Filtrer dès le bronze pour réduire la taille
    gdf = gdf.dropna(subset=["valeurfonc", "sbati"])
    gdf = gdf[gdf["sbati"] > 0]
    gdf = gdf[gdf["libtypbien"].str.contains("APPARTEMENT|MAISON", case=False, na=False)]
    print(f"  Après filtres : {len(gdf):,}")

    # Garder uniquement les colonnes nécessaires avant reprojection
    cols_garder = ["idmutation", "datemut", "anneemut", "valeurfonc", "sbati", "libtypbien", "geometry"]
    cols_garder = [c for c in cols_garder if c in gdf.columns]
    gdf = gdf[cols_garder].copy()
    gc.collect()

    # Reprojection WGS84 et extraction des coordonnées centroïde
    print("  Reprojection EPSG:2154 → EPSG:4326 et extraction lat/lon...")
    gdf = gdf.to_crs("EPSG:4326")
    df_out = pd.DataFrame({
        "idmutation": gdf["idmutation"].values,
        "datemut":    gdf["datemut"].values,
        "anneemut":   gdf["anneemut"].values,
        "valeurfonc": gdf["valeurfonc"].values,
        "sbati":      gdf["sbati"].values,
        "libtypbien": gdf["libtypbien"].values,
        "longitude":  gdf.geometry.centroid.x.values,
        "latitude":   gdf.geometry.centroid.y.values,
    })
    del gdf
    gc.collect()

    df_out.to_parquet(_dvf_out, index=False)
    print(f"  Sauvegardé : {_dvf_out} ({len(df_out):,} lignes)")

    del df_out
    gc.collect()

  except Exception as e:
    print(f"  ERREUR DVF+ : {e}")
    import traceback; traceback.print_exc()
    sys.exit(1)


# ─────────────────────────────────────────────
# 2. SIRENE
# ─────────────────────────────────────────────
print("\n" + "=" * 60)
print("2/4 — SIRENE (CSV.GZ par arrondissement)")
print("=" * 60)

_sirene_out = os.path.join(BRONZE_DIR, "sirene_raw.parquet")
if os.path.exists(_sirene_out):
    print(f"  Cache trouvé, étape ignorée ({_sirene_out})")
else:
  try:
    sirene_dir = os.path.join(RAW_IMQ, "geo_siret")
    files = sorted(glob.glob(os.path.join(sirene_dir, "*.csv.gz")))

    if not files:
        raise FileNotFoundError(f"Aucun fichier .csv.gz trouvé dans {sirene_dir}")

    print(f"  Fichiers trouvés : {len(files)}")

    # Colonnes utiles uniquement
    cols_utiles = [
        "siret", "latitude", "longitude", "geo_score",
        "activitePrincipaleEtablissement", "etatAdministratifEtablissement",
        "dateCreationEtablissement", "dateDebut", "codePostalEtablissement"
    ]

    # Filtres appliqués dès la lecture
    naf_valides = ["47", "56", "86", "85"]
    dfs = []
    for f in files:
        df_tmp = pd.read_csv(f, compression="gzip", low_memory=False,
                             usecols=lambda c: c in cols_utiles)
        # Filtrer immédiatement
        df_tmp = df_tmp[df_tmp["geo_score"] > 0.5]
        df_tmp["codePostalEtablissement"] = df_tmp["codePostalEtablissement"].astype(str).str.strip()
        df_tmp = df_tmp[df_tmp["codePostalEtablissement"].str.startswith("75")]
        df_tmp["naf_prefix"] = df_tmp["activitePrincipaleEtablissement"].astype(str).str[:2]
        df_tmp = df_tmp[df_tmp["naf_prefix"].isin(naf_valides)]
        dfs.append(df_tmp)
        print(f"    {os.path.basename(f)} — {len(df_tmp):,} lignes après filtres")
        del df_tmp
        gc.collect()

    df_sirene = pd.concat(dfs, ignore_index=True)
    del dfs
    gc.collect()

    print(f"  Total : {len(df_sirene):,} lignes")
    df_sirene.to_parquet(_sirene_out, index=False)
    print(f"  Sauvegardé : {_sirene_out}")

    del df_sirene
    gc.collect()

  except Exception as e:
    print(f"  ERREUR SIRENE : {e}")
    import traceback; traceback.print_exc()
    sys.exit(1)


# ─────────────────────────────────────────────
# 3. LOVAC
# ─────────────────────────────────────────────
print("\n" + "=" * 60)
print("3/4 — LOVAC (Excel)")
print("=" * 60)

_lovac_out = os.path.join(BRONZE_DIR, "lovac_raw.parquet")
if os.path.exists(_lovac_out):
    print(f"  Cache trouvé, étape ignorée ({_lovac_out})")
else:
  try:
    lovac_path = os.path.join(RAW_IMQ, "lovac-open-data-2020-a-2025-vd.xlsx")
    df_lovac = pd.read_excel(lovac_path, sheet_name="COM")
    print(f"  Lignes : {len(df_lovac):,}")

    df_lovac.to_parquet(_lovac_out, index=False)
    print(f"  Sauvegardé : {_lovac_out}")

    del df_lovac
    gc.collect()

  except Exception as e:
    print(f"  ERREUR LOVAC : {e}")
    import traceback; traceback.print_exc()
    sys.exit(1)


# ─────────────────────────────────────────────
# 4. Filosofi
# ─────────────────────────────────────────────
print("\n" + "=" * 60)
print("4/4 — Filosofi (CSV)")
print("=" * 60)

_filo_out = os.path.join(BRONZE_DIR, "filosofi_raw.parquet")
if os.path.exists(_filo_out):
    print(f"  Cache trouvé, étape ignorée ({_filo_out})")
else:
  try:
    filo_path = os.path.join(RAW_IMQ, "BASE_TD_FILO_IRIS_2021_DEC.csv")
    df_filo = pd.read_csv(filo_path, sep=";", low_memory=False)
    print(f"  Lignes : {len(df_filo):,}")

    df_filo.to_parquet(_filo_out, index=False)
    print(f"  Sauvegardé : {_filo_out}")

    del df_filo
    gc.collect()

  except Exception as e:
    print(f"  ERREUR Filosofi : {e}")
    import traceback; traceback.print_exc()
    sys.exit(1)


print("\n" + "=" * 60)
print("BRONZE — Ingestion terminée avec succès")
print("=" * 60)
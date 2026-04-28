"""
COUCHE SILVER — Nettoyage et normalisation des données Bronze
=============================================================
Lit les fichiers Parquet de la couche Bronze, applique les transformations
métier, et produit des fichiers propres prêts pour l'analyse.
"""

import os
import sys
import warnings
import numpy as np
import pandas as pd
import geopandas as gpd
from shapely import wkt

warnings.filterwarnings("ignore")

# ─────────────────────────────────────────────
# Chemins
# ─────────────────────────────────────────────
BASE_DIR   = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
BRONZE_DIR = os.path.join(BASE_DIR, "data", "bronze", "bronze_IMQ")
SILVER_DIR = os.path.join(BASE_DIR, "data", "silver", "silver_IMQ")
os.makedirs(SILVER_DIR, exist_ok=True)


# ─────────────────────────────────────────────
# 1. DVF+ Silver — Prix immobilier nettoyé
# ─────────────────────────────────────────────
print("\n" + "=" * 60)
print("1/4 — DVF+ Silver")
print("=" * 60)

try:
    dvf_path = os.path.join(BRONZE_DIR, "dvf_raw.parquet")
    print(f"  Lecture : {dvf_path}")
    df = pd.read_parquet(dvf_path)
    print(f"  Lignes chargées : {len(df):,}")

    # Supprimer les lignes avec valeurfonc ou sbati nuls
    df = df.dropna(subset=["valeurfonc", "sbati"])
    df = df[df["sbati"] > 0]
    print(f"  Après suppression valeurfonc/sbati nuls : {len(df):,}")

    # Garder uniquement les biens résidentiels (appartements et maisons)
    df = df[
        df["libtypbien"].str.contains("APPARTEMENT|MAISON", case=False, na=False)
    ]
    print(f"  Après filtre résidentiel : {len(df):,}")

    # Calculer le prix au m²
    df["prix_m2"] = df["valeurfonc"] / df["sbati"]

    # Supprimer les outliers (garder entre 1 000 et 30 000 €/m²)
    df = df[(df["prix_m2"] >= 1000) & (df["prix_m2"] <= 30000)]
    print(f"  Après filtre outliers prix_m2 [1000–30000] : {len(df):,}")

    # Convertir la géométrie Lambert 93 (EPSG:2154) → WGS84 (EPSG:4326)
    print("  Conversion géométrie Lambert 93 → WGS84...")
    # Supprimer les géométries nulles/invalides (stockées comme 'NONE' ou NaN)
    df = df[df["geometry"].notna()]
    df = df[df["geometry"].astype(str).str.upper() != "NONE"]
    df = df[df["geometry"].astype(str).str.upper() != "NAN"]
    print(f"  Après suppression géométries nulles : {len(df):,}")

    df["geometry"] = df["geometry"].apply(wkt.loads)
    gdf = gpd.GeoDataFrame(df, geometry="geometry", crs="EPSG:2154")
    gdf = gdf.to_crs("EPSG:4326")

    # Extraire latitude/longitude du centroïde
    gdf["longitude"] = gdf.geometry.centroid.x
    gdf["latitude"] = gdf.geometry.centroid.y
    print(f"  Latitude/Longitude extraites")

    # Sélectionner les colonnes finales
    cols = [
        "idmutation", "datemut", "anneemut",
        "valeurfonc", "sbati", "prix_m2",
        "libtypbien", "latitude", "longitude"
    ]
    # Garder uniquement les colonnes qui existent
    cols = [c for c in cols if c in gdf.columns]
    df_silver = gdf[cols].copy()

    out_path = os.path.join(SILVER_DIR, "dvf_clean.parquet")
    df_silver.to_parquet(out_path, index=False)
    print(f"  Sauvegardé : {out_path} ({len(df_silver):,} lignes)")

except Exception as e:
    print(f"  ERREUR DVF+ Silver : {e}")
    import traceback; traceback.print_exc()
    sys.exit(1)


# ─────────────────────────────────────────────
# 2. SIRENE Silver — Établissements commerciaux
# ─────────────────────────────────────────────
print("\n" + "=" * 60)
print("2/4 — SIRENE Silver")
print("=" * 60)

try:
    sirene_path = os.path.join(BRONZE_DIR, "sirene_raw.parquet")
    print(f"  Lecture : {sirene_path}")
    df = pd.read_parquet(sirene_path)
    print(f"  Lignes chargées : {len(df):,}")

    # Garder uniquement geo_score > 0.5
    df = df[df["geo_score"] > 0.5]
    print(f"  Après filtre geo_score > 0.5 : {len(df):,}")

    # Garder uniquement les établissements parisiens (code postal commence par '75')
    df["codePostalEtablissement"] = df["codePostalEtablissement"].astype(str).str.strip()
    df = df[df["codePostalEtablissement"].str.startswith("75")]
    print(f"  Après filtre Paris (CP 75xxx) : {len(df):,}")

    # Garder uniquement les commerces de proximité (codes NAF pertinents)
    # 47.xx = commerce de détail, 56.xx = restauration,
    # 86.xx = santé, 85.xx = enseignement
    df["naf_prefix"] = df["activitePrincipaleEtablissement"].astype(str).str[:2]
    naf_valides = ["47", "56", "86", "85"]
    df = df[df["naf_prefix"].isin(naf_valides)]
    print(f"  Après filtre codes NAF (47/56/86/85) : {len(df):,}")

    # Créer la colonne statut
    df["statut"] = df["etatAdministratifEtablissement"].map(
        {"A": "ouverture", "F": "fermeture"}
    )

    # Extraire les années depuis les dates
    df["annee_creation"] = pd.to_datetime(
        df["dateCreationEtablissement"], errors="coerce"
    ).dt.year

    df["annee_debut"] = pd.to_datetime(
        df["dateDebut"], errors="coerce"
    ).dt.year

    # Sélectionner les colonnes finales
    cols = [
        "siret", "latitude", "longitude",
        "activitePrincipaleEtablissement", "statut",
        "annee_creation", "annee_debut", "codePostalEtablissement"
    ]
    cols = [c for c in cols if c in df.columns]
    df_silver = df[cols].copy()

    out_path = os.path.join(SILVER_DIR, "sirene_clean.parquet")
    df_silver.to_parquet(out_path, index=False)
    print(f"  Sauvegardé : {out_path} ({len(df_silver):,} lignes)")

except Exception as e:
    print(f"  ERREUR SIRENE Silver : {e}")
    import traceback; traceback.print_exc()
    sys.exit(1)


# ─────────────────────────────────────────────
# 3. LOVAC Silver — Logements vacants
# ─────────────────────────────────────────────
print("\n" + "=" * 60)
print("3/4 — LOVAC Silver")
print("=" * 60)

try:
    lovac_path = os.path.join(BRONZE_DIR, "lovac_raw.parquet")
    print(f"  Lecture : {lovac_path}")
    df = pd.read_parquet(lovac_path)
    print(f"  Lignes chargées : {len(df):,}")

    # Filtrer Paris uniquement (CODGEO_25 commence par '75')
    df["CODGEO_25"] = df["CODGEO_25"].astype(str).str.strip()
    df = df[df["CODGEO_25"].str.startswith("75")]
    print(f"  Arrondissements Paris : {len(df)}")

    # Calculer le taux de vacance pour chaque année
    for year in ["20", "21", "22", "23", "24"]:
        vacant_col = f"pp_vacant_{year}"
        total_col = f"pp_total_{year}"
        taux_col = f"taux_vacant_{year}"

        if vacant_col in df.columns and total_col in df.columns:
            vacant = pd.to_numeric(df[vacant_col], errors="coerce")
            total = pd.to_numeric(df[total_col], errors="coerce").replace(0, np.nan)
            df[taux_col] = vacant / total
        else:
            print(f"  ATTENTION : colonnes {vacant_col}/{total_col} absentes")
            df[taux_col] = np.nan

    # Calculer le delta de vacance entre 2024 et 2020
    df["delta_vacance"] = df["taux_vacant_24"] - df["taux_vacant_20"]

    # Sélectionner les colonnes finales
    cols = [
        "CODGEO_25",
        "taux_vacant_20", "taux_vacant_21", "taux_vacant_22",
        "taux_vacant_23", "taux_vacant_24", "delta_vacance"
    ]
    cols = [c for c in cols if c in df.columns]
    df_silver = df[cols].copy()

    out_path = os.path.join(SILVER_DIR, "lovac_clean.parquet")
    df_silver.to_parquet(out_path, index=False)
    print(f"  Sauvegardé : {out_path}")
    print(df_silver[["CODGEO_25", "taux_vacant_20", "taux_vacant_24", "delta_vacance"]].to_string(index=False))

except Exception as e:
    print(f"  ERREUR LOVAC Silver : {e}")
    import traceback; traceback.print_exc()
    sys.exit(1)


# ─────────────────────────────────────────────
# 4. Filosofi Silver — Revenus par IRIS
# ─────────────────────────────────────────────
print("\n" + "=" * 60)
print("4/4 — Filosofi Silver")
print("=" * 60)

try:
    filo_path = os.path.join(BRONZE_DIR, "filosofi_raw.parquet")
    print(f"  Lecture : {filo_path}")
    df = pd.read_parquet(filo_path)
    print(f"  Lignes chargées : {len(df):,}")

    # Filtrer les IRIS parisiens (code IRIS commence par '75')
    df["IRIS"] = df["IRIS"].astype(str).str.strip()
    df = df[df["IRIS"].str.startswith("75")]
    print(f"  IRIS parisiens : {len(df):,}")

    # La colonne revenu médian s'appelle DEC_MED21 dans ce fichier
    # (Filosofi décile, équivalent à DISP_MED21 dans la nomenclature du projet)
    rev_col = "DEC_MED21" if "DEC_MED21" in df.columns else "DISP_MED21"

    if rev_col not in df.columns:
        raise ValueError(f"Colonne revenu médian introuvable. Disponibles : {df.columns.tolist()}")

    # Convertir en numérique et supprimer les lignes avec revenu médian nul
    df[rev_col] = pd.to_numeric(df[rev_col], errors="coerce")
    df = df.dropna(subset=[rev_col])
    df = df[df[rev_col] > 0]

    # Renommer pour cohérence avec la spec du projet
    df = df.rename(columns={rev_col: "DISP_MED21"})

    df_silver = df[["IRIS", "DISP_MED21"]].copy()

    out_path = os.path.join(SILVER_DIR, "filosofi_clean.parquet")
    df_silver.to_parquet(out_path, index=False)
    print(f"  Sauvegardé : {out_path} ({len(df_silver):,} lignes)")

except Exception as e:
    print(f"  ERREUR Filosofi Silver : {e}")
    import traceback; traceback.print_exc()
    sys.exit(1)


print("\n" + "=" * 60)
print("SILVER — Traitement terminé avec succès")
print("=" * 60)

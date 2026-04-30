"""
COUCHE GOLD — Calcul de l'IMQ (Indice de Mutation de Quartier) par IRIS
=========================================================================
Calcule un score IMQ à la granularité IRIS (992 IRIS parisiens) en croisant :
  - Prix immobilier      (DVF+, jointure spatiale point → IRIS)
  - Dynamique commerciale (SIRENE, jointure spatiale point → IRIS)
  - Revenu médian        (Filosofi, directement à l'IRIS)
  - Vacance              (LOVAC, niveau arrondissement redescendu sur les IRIS)

Pondérations IMQ :
  0.35 × prix  +  0.30 × commerce  +  0.20 × revenu  +  0.15 × vacance
"""

import gc
import os
import sys
import warnings

import numpy as np
import pandas as pd
import geopandas as gpd
import requests

warnings.filterwarnings("ignore")

# ─────────────────────────────────────────────
# Chemins
# ─────────────────────────────────────────────
BASE_DIR   = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
SILVER_DIR = os.path.join(BASE_DIR, "data", "silver", "silver_IMQ")
GOLD_DIR   = os.path.join(BASE_DIR, "data", "gold", "gold_IMQ")
os.makedirs(GOLD_DIR, exist_ok=True)

IRIS_CACHE = os.path.join(BASE_DIR, "data", "raw", "raw_IMQ", "iris_paris.geojson")


# ─────────────────────────────────────────────
# Utilitaire : normalisation min-max [0, 1]
# ─────────────────────────────────────────────
def minmax(series: pd.Series) -> pd.Series:
    mn, mx = series.min(), series.max()
    if mx == mn:
        return pd.Series(0.5, index=series.index)
    return (series - mn) / (mx - mn)


# ─────────────────────────────────────────────
# ÉTAPE 0 — Charger les contours IRIS Paris
# ─────────────────────────────────────────────
print("\n" + "=" * 65)
print("Étape 0 — Contours IRIS Paris (IGN WFS)")
print("=" * 65)

try:
    if os.path.exists(IRIS_CACHE):
        print(f"  Cache trouvé : {IRIS_CACHE}")
        gdf_iris = gpd.read_file(IRIS_CACHE)
    else:
        print("  Téléchargement depuis l'API WFS IGN (Géoplateforme)...")
        wfs_url = (
            "https://data.geopf.fr/wfs/ows"
            "?SERVICE=WFS&VERSION=2.0.0&REQUEST=GetFeature"
            "&TYPENAMES=STATISTICALUNITS.IRIS:contours_iris"
            "&OUTPUTFORMAT=application/json"
            "&SRSNAME=EPSG:4326"
            "&CQL_FILTER=code_iris+LIKE+'75%25'"
        )
        r = requests.get(wfs_url, timeout=90)
        r.raise_for_status()
        with open(IRIS_CACHE, "w", encoding="utf-8") as f:
            f.write(r.text)
        gdf_iris = gpd.read_file(IRIS_CACHE)

    print(f"  IRIS chargés    : {len(gdf_iris)}")
    print(f"  Colonnes        : {list(gdf_iris.columns)}")
    print(f"  CRS             : {gdf_iris.crs}")

    # Assurer WGS84
    if gdf_iris.crs is None or gdf_iris.crs.to_epsg() != 4326:
        gdf_iris = gdf_iris.to_crs("EPSG:4326")

    # Renommer pour clarté
    gdf_iris = gdf_iris.rename(columns={
        "code_iris":  "iris_code",
        "nom_iris":   "iris_nom",
        "code_insee": "arr_insee",
    })
    gdf_iris["arr_insee"] = gdf_iris["arr_insee"].astype(str)

    # Garder uniquement les colonnes nécessaires
    gdf_iris = gdf_iris[["iris_code", "iris_nom", "arr_insee", "geometry"]].copy()

except Exception as e:
    print(f"  ERREUR chargement IRIS : {e}")
    import traceback; traceback.print_exc()
    sys.exit(1)


# ─────────────────────────────────────────────
# ÉTAPE 1 — Composante Prix Immobilier (DVF)
# ─────────────────────────────────────────────
print("\n" + "=" * 65)
print("Étape 1 — Prix immobilier par IRIS (DVF+)")
print("=" * 65)

try:
    df_dvf = pd.read_parquet(os.path.join(SILVER_DIR, "dvf_clean.parquet"))
    print(f"  Transactions chargées : {len(df_dvf):,}")

    gdf_dvf = gpd.GeoDataFrame(
        df_dvf[["anneemut", "prix_m2", "longitude", "latitude"]],
        geometry=gpd.points_from_xy(df_dvf["longitude"], df_dvf["latitude"]),
        crs="EPSG:4326"
    )
    del df_dvf
    gc.collect()

    print("  Jointure spatiale DVF → IRIS...")
    gdf_dvf_join = gpd.sjoin(
        gdf_dvf[["anneemut", "prix_m2", "geometry"]],
        gdf_iris[["iris_code", "arr_insee", "geometry"]],
        how="left",
        predicate="within"
    )
    del gdf_dvf
    gc.collect()

    print(f"  Transactions assignées à un IRIS : {gdf_dvf_join['iris_code'].notna().sum():,}")

    # Convertir en DataFrame simple
    df_dvf_join = pd.DataFrame(gdf_dvf_join[["anneemut", "prix_m2", "iris_code"]].dropna(subset=["iris_code"]))
    del gdf_dvf_join
    gc.collect()

    df_dvf_join["anneemut"] = pd.to_numeric(df_dvf_join["anneemut"], errors="coerce")

    pivot = (
        df_dvf_join.groupby(["iris_code", "anneemut"])["prix_m2"]
        .median()
        .reset_index()
        .rename(columns={"prix_m2": "prix_median"})
    )
    del df_dvf_join
    gc.collect()

    p2019 = pivot[pivot["anneemut"] == 2019][["iris_code", "prix_median"]].rename(
        columns={"prix_median": "prix_2019"}
    )
    p2023 = pivot[pivot["anneemut"] == 2023][["iris_code", "prix_median"]].rename(
        columns={"prix_median": "prix_2023"}
    )
    df_prix = p2019.merge(p2023, on="iris_code", how="inner")
    df_prix["delta_prix"] = (df_prix["prix_2023"] - df_prix["prix_2019"]) / df_prix["prix_2019"]

    if len(df_prix) < 100:
        annees = sorted(pivot["anneemut"].dropna().unique().astype(int))
        a0, a1 = annees[0], annees[-1]
        print(f"  Peu de données 2019/2023 — calcul sur {a0}–{a1}")
        pa0 = pivot[pivot["anneemut"] == a0][["iris_code", "prix_median"]].rename(
            columns={"prix_median": f"prix_{a0}"}
        )
        pa1 = pivot[pivot["anneemut"] == a1][["iris_code", "prix_median"]].rename(
            columns={"prix_median": f"prix_{a1}"}
        )
        df_prix = pa0.merge(pa1, on="iris_code", how="inner")
        df_prix["delta_prix"] = (
            df_prix[f"prix_{a1}"] - df_prix[f"prix_{a0}"]
        ) / df_prix[f"prix_{a0}"]

    del pivot, p2019, p2023
    gc.collect()

    df_prix["delta_prix_norm"] = minmax(df_prix["delta_prix"])
    print(f"  IRIS avec delta_prix calculé : {len(df_prix)} / {len(gdf_iris)}")

except Exception as e:
    print(f"  ERREUR Étape 1 : {e}")
    import traceback; traceback.print_exc()
    sys.exit(1)


# ─────────────────────────────────────────────
# ÉTAPE 2 — Composante Commerciale (SIRENE)
# ─────────────────────────────────────────────
print("\n" + "=" * 65)
print("Étape 2 — Dynamique commerciale par IRIS (SIRENE)")
print("=" * 65)

try:
    df_sir = pd.read_parquet(os.path.join(SILVER_DIR, "sirene_clean.parquet"))
    print(f"  Établissements chargés : {len(df_sir):,}")

    df_sir = df_sir.dropna(subset=["latitude", "longitude"])
    gdf_sir = gpd.GeoDataFrame(
        df_sir[["statut", "annee_creation", "annee_debut", "longitude", "latitude"]],
        geometry=gpd.points_from_xy(df_sir["longitude"], df_sir["latitude"]),
        crs="EPSG:4326"
    )
    del df_sir
    gc.collect()

    print("  Jointure spatiale SIRENE → IRIS...")
    gdf_sir_join = gpd.sjoin(
        gdf_sir[["statut", "annee_creation", "annee_debut", "geometry"]],
        gdf_iris[["iris_code", "geometry"]],
        how="left",
        predicate="within"
    )
    del gdf_sir
    gc.collect()

    df_sir_join = pd.DataFrame(gdf_sir_join[["statut", "annee_creation", "annee_debut", "iris_code"]].dropna(subset=["iris_code"]))
    del gdf_sir_join
    gc.collect()

    print(f"  Établissements assignés à un IRIS : {len(df_sir_join):,}")

    ouv = df_sir_join[
        (df_sir_join["statut"] == "ouverture") &
        (df_sir_join["annee_creation"].between(2019, 2023))
    ]
    fer = df_sir_join[
        (df_sir_join["statut"] == "fermeture") &
        (df_sir_join["annee_debut"].between(2019, 2023))
    ]

    nb_ouv = ouv.groupby("iris_code").size().rename("nb_ouvertures")
    nb_fer = fer.groupby("iris_code").size().rename("nb_fermetures")
    del df_sir_join, ouv, fer
    gc.collect()

    df_comm = pd.DataFrame(nb_ouv).join(nb_fer, how="outer").fillna(0).reset_index()
    df_comm["nb_ouvertures"] = df_comm["nb_ouvertures"].astype(int)
    df_comm["nb_fermetures"] = df_comm["nb_fermetures"].astype(int)
    df_comm["ratio_comm"] = df_comm["nb_ouvertures"] / (df_comm["nb_fermetures"] + 1)
    df_comm["ratio_comm_norm"] = minmax(df_comm["ratio_comm"])
    del nb_ouv, nb_fer
    gc.collect()

    print(f"  IRIS avec données commerciales : {len(df_comm)} / {len(gdf_iris)}")

except Exception as e:
    print(f"  ERREUR Étape 2 : {e}")
    import traceback; traceback.print_exc()
    sys.exit(1)


# ─────────────────────────────────────────────
# ÉTAPE 3 — Revenu médian par IRIS (Filosofi)
# ─────────────────────────────────────────────
print("\n" + "=" * 65)
print("Étape 3 — Revenu médian par IRIS (Filosofi)")
print("=" * 65)

try:
    df_filo = pd.read_parquet(os.path.join(SILVER_DIR, "filosofi_clean.parquet"))
    print(f"  IRIS Filosofi chargés : {len(df_filo)}")

    df_filo = df_filo.rename(columns={"IRIS": "iris_code", "DISP_MED21": "revenu_median"})
    df_filo["iris_code"] = df_filo["iris_code"].astype(str).str.zfill(9)
    df_filo["revenu_norm"] = 1 - minmax(df_filo["revenu_median"])
    df_filo = df_filo[["iris_code", "revenu_median", "revenu_norm"]]

    print(f"  IRIS avec revenu médian : {len(df_filo)}")

except Exception as e:
    print(f"  ERREUR Étape 3 : {e}")
    import traceback; traceback.print_exc()
    sys.exit(1)


# ─────────────────────────────────────────────
# ÉTAPE 4 — Vacance (LOVAC → redescendu à l'IRIS)
# ─────────────────────────────────────────────
print("\n" + "=" * 65)
print("Étape 4 — Vacance par IRIS (LOVAC via arrondissement)")
print("=" * 65)

try:
    df_lovac = pd.read_parquet(os.path.join(SILVER_DIR, "lovac_clean.parquet"))
    df_lovac = df_lovac.rename(columns={"CODGEO_25": "arr_code"})
    df_lovac["arr_code"] = df_lovac["arr_code"].astype(str)
    df_lovac["delta_vac_inv"] = -df_lovac["delta_vacance"]
    df_lovac["vacance_norm"] = minmax(df_lovac["delta_vac_inv"])
    df_lovac = df_lovac[["arr_code", "delta_vacance", "vacance_norm"]]

    print(f"  Arrondissements LOVAC : {len(df_lovac)}")

except Exception as e:
    print(f"  ERREUR Étape 4 : {e}")
    import traceback; traceback.print_exc()
    sys.exit(1)


# ─────────────────────────────────────────────
# ÉTAPE 5 — Assemblage et score IMQ par IRIS
# ─────────────────────────────────────────────
print("\n" + "=" * 65)
print("Étape 5 — Score IMQ par IRIS")
print("=" * 65)

try:
    # Base : tous les IRIS (sans geometry pour économiser la mémoire)
    df = pd.DataFrame(gdf_iris[["iris_code", "iris_nom", "arr_insee"]])
    del gdf_iris
    gc.collect()

    df["iris_code"] = df["iris_code"].astype(str).str.zfill(9)
    df["arr_insee"] = df["arr_insee"].astype(str)

    df = df.merge(df_prix[["iris_code", "delta_prix", "delta_prix_norm"]], on="iris_code", how="left")
    del df_prix
    gc.collect()

    df = df.merge(df_comm[["iris_code", "nb_ouvertures", "nb_fermetures", "ratio_comm", "ratio_comm_norm"]], on="iris_code", how="left")
    del df_comm
    gc.collect()

    df = df.merge(df_filo[["iris_code", "revenu_median", "revenu_norm"]], on="iris_code", how="left")
    del df_filo
    gc.collect()

    df = df.merge(df_lovac[["arr_code", "delta_vacance", "vacance_norm"]], left_on="arr_insee", right_on="arr_code", how="left")
    del df_lovac
    gc.collect()

    print(f"  IRIS total              : {len(df)}")
    print(f"  IRIS avec prix DVF      : {df['delta_prix_norm'].notna().sum()}")
    print(f"  IRIS avec commerce      : {df['ratio_comm_norm'].notna().sum()}")
    print(f"  IRIS avec Filosofi      : {df['revenu_norm'].notna().sum()}")
    print(f"  IRIS avec LOVAC         : {df['vacance_norm'].notna().sum()}")

    for col in ["delta_prix_norm", "ratio_comm_norm", "revenu_norm", "vacance_norm"]:
        med = df[col].median()
        n_manquants = df[col].isna().sum()
        df[col] = df[col].fillna(med)
        if n_manquants > 0:
            print(f"  {col} : {n_manquants} IRIS sans données → médiane {med:.3f}")

    df["score_imq_brut"] = (
        0.35 * df["delta_prix_norm"] +
        0.30 * df["ratio_comm_norm"] +
        0.20 * df["revenu_norm"] +
        0.15 * df["vacance_norm"]
    )
    df["score_imq"] = minmax(df["score_imq_brut"])

    def interpreter(score):
        if score > 0.66:
            return "Mutation forte"
        elif score > 0.33:
            return "Mutation modérée"
        else:
            return "Stable"

    df["interpretation"] = df["score_imq"].apply(interpreter)

    df_final = df[[
        "iris_code", "iris_nom", "arr_insee",
        "delta_prix_norm", "ratio_comm_norm",
        "revenu_norm", "vacance_norm",
        "score_imq", "interpretation"
    ]].sort_values("score_imq", ascending=False).reset_index(drop=True)
    del df
    gc.collect()

    out_path = os.path.join(GOLD_DIR, "imq_par_iris.parquet")
    df_final.to_parquet(out_path, index=False)
    print(f"\n  Sauvegardé : {out_path}")

    print("\n  Distribution des IRIS :")
    for label, count in df_final["interpretation"].value_counts().items():
        pct = count / len(df_final) * 100
        print(f"    {label:<22} : {count:>3} IRIS ({pct:.1f}%)")

    print("\n" + "─" * 75)
    print(f"  {'IRIS':<12} {'NOM':<30} {'PRIX':>6} {'COMM':>6} {'REV':>6} {'VAC':>6} {'IMQ':>6}")
    print("─" * 75)
    for _, row in df_final.head(15).iterrows():
        print(
            f"  {row['iris_code']:<12} "
            f"{str(row['iris_nom'])[:28]:<30} "
            f"{row['delta_prix_norm']:>6.3f} "
            f"{row['ratio_comm_norm']:>6.3f} "
            f"{row['revenu_norm']:>6.3f} "
            f"{row['vacance_norm']:>6.3f} "
            f"{row['score_imq']:>6.3f}"
        )
    print("─" * 75)

except Exception as e:
    print(f"  ERREUR Étape 5 : {e}")
    import traceback; traceback.print_exc()
    sys.exit(1)


print("\n" + "=" * 65)
print("GOLD — IMQ par IRIS calculé avec succès")
print(f"Fichier : data/gold/gold_IMQ/imq_par_iris.parquet  ({len(df_final)} IRIS)")
print("=" * 65)


def run():
    pass
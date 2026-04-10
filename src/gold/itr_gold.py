"""
GOLD — Calcul ITR par rue
==========================
Applique la formule ITR sur la table silver rue_enrichie,
normalise le score 0-100, labellise et produit les fichiers
de livraison (parquet + GeoJSON).

Entrée  : data/silver/rue_enrichie.parquet
Sorties : data/gold/itr_par_rue.parquet
          data/gold/itr_par_rue.geojson   ← livraison carte / API

Formule :
    ITR_brut  = (prix_m2_median / revenu_median_uc)
              × (1 + 1 / (1 + nb_logements_sociaux))
              × log(1 + nb_transactions)

    ITR_score = 100 × (ITR_brut - min) / (max - min)
"""

import pandas as pd
import numpy as np
import json
from pathlib import Path

SILVER_PATH  = Path("data/silver/rue_enrichie.parquet")
OUT_PARQUET  = Path("data/gold/itr_par_rue.parquet")
OUT_GEOJSON  = Path("data/gold/itr_par_rue.geojson")

# Seuils pour les labels (découpage en 5 quintiles fixes)
LABELS = ["Très accessible", "Accessible", "Modéré", "Tendu", "Très tendu"]
BINS   = [0, 20, 40, 60, 80, 100]


# ──────────────────────────────────────────────
# 1. CALCUL DES COMPOSANTES
# ──────────────────────────────────────────────

def compute_itr(df: pd.DataFrame) -> pd.DataFrame:
    """
    Applique la formule ITR en 3 composantes explicites,
    puis normalise le score brut entre 0 et 100.
    """
    # Exclure les rues sans revenu médian (IRIS zonés activité, pas de données Filosofi)
    n_avant = len(df)
    df = df.dropna(subset=["revenu_median_uc", "prix_m2_median"]).copy()
    print(f"  Rues exploitables (revenu non-null) : {len(df):,}  "
          f"(exclues : {n_avant - len(df)})")

    # ── Composante 1 : effort d'achat
    # Ratio nombre d'années de revenu nécessaires pour acheter 1 m²
    # Plus c'est élevé, plus c'est tendu
    df["c1_effort"] = df["prix_m2_median"] / df["revenu_median_uc"]

    # ── Composante 2 : absence de logement social
    # Si nb_logsoc = 0  → facteur = 1 + 1/1 = 2.0  (très tendu, pas d'alternative)
    # Si nb_logsoc = 500 → facteur = 1 + 1/501 ≈ 1.002 (quasi-neutre)
    df["c2_logsoc"] = 1 + 1 / (1 + df["nb_logements_sociaux"])

    # ── Composante 3 : intensité du marché (proxy densité)
    # log(1 + n) : croît vite au début puis se stabilise
    # Rue avec 3 trans → log(4) ≈ 1.39
    # Rue avec 50 trans → log(51) ≈ 3.93
    # Rue avec 190 trans → log(191) ≈ 5.25
    df["c3_volume"] = np.log1p(df["nb_transactions"])

    # ── Score brut
    df["itr_brut"] = df["c1_effort"] * df["c2_logsoc"] * df["c3_volume"]

    # ── Normalisation Min-Max 0→100 sur Paris entier
    itr_min = df["itr_brut"].min()
    itr_max = df["itr_brut"].max()
    df["itr_score"] = (
        100 * (df["itr_brut"] - itr_min) / (itr_max - itr_min)
    ).round(2)

    # ── Label lisible
    df["itr_label"] = pd.cut(
        df["itr_score"],
        bins=BINS,
        labels=LABELS,
        include_lowest=True,
    ).astype(str)

    print(f"  itr_score : "
          f"min={df['itr_score'].min():.1f}  "
          f"median={df['itr_score'].median():.1f}  "
          f"max={df['itr_score'].max():.1f}")

    return df


# ──────────────────────────────────────────────
# 2. SÉLECTION ET ORDRE DES COLONNES
# ──────────────────────────────────────────────

def finalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    cols = [
        # Identifiants géographiques
        "nom_voie",
        "code_postal",
        "arrondissement",
        "code_iris",
        # Coordonnées GPS (centroïde des transactions DVF de la rue)
        "lon_centre",
        "lat_centre",
        # Composantes brutes
        "prix_m2_median",
        "revenu_median_uc",
        "nb_logements_sociaux",
        "nb_transactions",
        # Composantes intermédiaires (utiles pour debug et transparence)
        "c1_effort",
        "c2_logsoc",
        "c3_volume",
        "itr_brut",
        # Score final
        "itr_score",
        "itr_label",
    ]
    return df[[c for c in cols if c in df.columns]]


# ──────────────────────────────────────────────
# 3. EXPORT GEOJSON
# ──────────────────────────────────────────────

def to_geojson(df: pd.DataFrame, path: Path) -> None:
    """
    Génère un GeoJSON FeatureCollection standard.
    Chaque rue = 1 Feature de type Point.
    Toutes les colonnes (sauf lon/lat) vont dans properties.
    """
    features = []

    prop_cols = [c for c in df.columns if c not in ("lon_centre", "lat_centre")]

    for _, row in df.iterrows():
        # Convertir les types numpy en types Python natifs (JSON-serializable)
        props = {}
        for col in prop_cols:
            val = row[col]
            if isinstance(val, (np.integer,)):
                props[col] = int(val)
            elif isinstance(val, (np.floating,)):
                props[col] = round(float(val), 4)
            elif pd.isna(val):
                props[col] = None
            else:
                props[col] = val

        feature = {
            "type": "Feature",
            "geometry": {
                "type": "Point",
                "coordinates": [
                    round(float(row["lon_centre"]), 6),
                    round(float(row["lat_centre"]), 6),
                ],
            },
            "properties": props,
        }
        features.append(feature)

    geojson = {
        "type": "FeatureCollection",
        "crs": {
            "type": "name",
            "properties": {"name": "EPSG:4326"},
        },
        "features": features,
    }

    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(geojson, f, ensure_ascii=False, indent=None, separators=(",", ":"))

    size_kb = path.stat().st_size / 1024
    print(f"  GeoJSON sauvegardé : {path}  ({size_kb:.0f} KB, {len(features)} features)")


# ──────────────────────────────────────────────
# 4. STATS TERMINAL
# ──────────────────────────────────────────────

def print_stats(df: pd.DataFrame) -> None:
    print("\n  ── Distribution par niveau de tension ──")
    dist = df["itr_label"].value_counts().reindex(LABELS).fillna(0).astype(int)
    for label, count in dist.items():
        pct = count / len(df) * 100
        bar = "█" * int(pct / 2)
        print(f"  {label:<18} {count:>5} rues  {pct:>5.1f}%  {bar}")

    print(f"\n  ── Top 5 rues les plus TENDUES ──")
    top = df.nlargest(5, "itr_score")[
        ["nom_voie", "arrondissement", "prix_m2_median", "nb_logements_sociaux",
         "nb_transactions", "itr_score", "itr_label"]
    ]
    for _, r in top.iterrows():
        print(f"  [{r['itr_score']:>6.1f}] {r['nom_voie']:<35} "
              f"arr.{int(r['arrondissement']):02d}  "
              f"{r['prix_m2_median']:>6.0f}€/m²  "
              f"{int(r['nb_transactions'])} ventes  "
              f"logsoc={int(r['nb_logements_sociaux'])}")

    print(f"\n  ── Top 5 rues les plus ACCESSIBLES ──")
    bot = df.nsmallest(5, "itr_score")[
        ["nom_voie", "arrondissement", "prix_m2_median", "nb_logements_sociaux",
         "nb_transactions", "itr_score", "itr_label"]
    ]
    for _, r in bot.iterrows():
        print(f"  [{r['itr_score']:>6.1f}] {r['nom_voie']:<35} "
              f"arr.{int(r['arrondissement']):02d}  "
              f"{r['prix_m2_median']:>6.0f}€/m²  "
              f"{int(r['nb_transactions'])} ventes  "
              f"logsoc={int(r['nb_logements_sociaux'])}")


# ──────────────────────────────────────────────
# 5. VALIDATE
# ──────────────────────────────────────────────

def validate(df: pd.DataFrame) -> None:
    assert "itr_score" in df.columns
    assert df["itr_score"].between(0, 100).all(), "Des scores hors [0,100]"
    assert df["lon_centre"].between(2.2, 2.5).all(), "Longitudes hors Paris"
    assert df["lat_centre"].between(48.8, 48.95).all(), "Latitudes hors Paris"
    assert df["itr_score"].isna().sum() == 0, "Nulls dans itr_score"
    print(f"\n  [OK] {len(df):,} rues avec score ITR valide")
    print(f"  [OK] Coordonnées GPS dans la bbox Paris")
    print(f"  [OK] Scores dans [0, 100]")


# ──────────────────────────────────────────────
# 6. RUN
# ──────────────────────────────────────────────

def run() -> pd.DataFrame:
    print("=== GOLD : Calcul ITR par rue ===")

    df = pd.read_parquet(SILVER_PATH)
    print(f"  Table silver chargée : {len(df):,} rues")

    df = compute_itr(df)
    df = finalize_columns(df)
    validate(df)
    print_stats(df)

    # Parquet
    OUT_PARQUET.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(OUT_PARQUET, index=False)
    print(f"\n  Parquet sauvegardé : {OUT_PARQUET}  "
          f"({OUT_PARQUET.stat().st_size / 1024:.0f} KB)")

    # GeoJSON
    to_geojson(df, OUT_GEOJSON)

    return df


if __name__ == "__main__":
    run()
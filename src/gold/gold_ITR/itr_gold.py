"""
GOLD — Calcul ITR par rue
==========================
Applique la formule ITR, score par rang percentile, export GeoJSON.
ITR_brut(rue) = (prix_m2_median / revenu_median_uc)
              × (1 + 1 / (1 + nb_logements_sociaux))

ITR_score = rang percentile de ITR_brut × 100
Entree  : data/silver/silver_ITR/rue_enrichie.parquet
Sorties : data/gold/gold_ITR/itr_par_rue.parquet
          data/gold/gold_ITR/itr_par_rue.geojson
"""

import pandas as pd
import numpy as np
import json
from pathlib import Path

SILVER_PATH = Path("data/silver/silver_ITR/rue_enrichie.parquet")
OUT_PARQUET = Path("data/gold/gold_ITR/itr_par_rue.parquet")
OUT_GEOJSON = Path("data/gold/gold_ITR/itr_par_rue.geojson")

LABELS = ["Tres accessible", "Accessible", "Modere", "Tendu", "Tres tendu"]


def compute_itr(df: pd.DataFrame) -> pd.DataFrame:
    n_avant = len(df)
    df = df.dropna(subset=["revenu_median_uc", "prix_m2_median"]).copy()
    print(f"  Rues exploitables (revenu non-null) : {len(df):,}  (exclues : {n_avant - len(df)})")

    # Composante 1 : effort d'achat
    df["c1_effort"] = df["prix_m2_median"] / df["revenu_median_uc"]

    # Composante 2 : absence de logement social
    df["c2_logsoc"] = 1 + 1 / (1 + df["nb_logements_sociaux"])

    # Score brut
    df["itr_brut"] = df["c1_effort"] * df["c2_logsoc"]

    # ── Score par rang percentile (0 → 100) ──────────────────────────────────
    # La normalisation Min-Max écrase 95% des rues vers le milieu quand le
    # ratio min/max du score brut est très élevé (ex: 369x avec DVF 2021).
    # Le rang percentile garantit une distribution uniforme : la rue au
    # 80e percentile reçoit le score 80, quelle que soit sa valeur brute.
    df["itr_score"] = (df["itr_brut"].rank(pct=True) * 100).round(1)

    # Label par tranche de 20 points (= quintiles automatiques grâce au rang)
    df["itr_label"] = pd.cut(
        df["itr_score"],
        bins=[0, 20, 40, 60, 80, 100],
        labels=LABELS,
        include_lowest=True,
    ).astype(str)

    print(f"  itr_score : min={df['itr_score'].min():.1f}  "
          f"median={df['itr_score'].median():.1f}  "
          f"max={df['itr_score'].max():.1f}")

    return df


def finalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    cols = [
        "nom_voie", "code_postal", "arrondissement", "code_iris",
        "lon_centre", "lat_centre",
        "prix_m2_median", "revenu_median_uc",
        "nb_logements_sociaux", "nb_transactions",
        "c1_effort", "c2_logsoc", "itr_brut",
        "itr_score", "itr_label",
    ]
    return df[[c for c in cols if c in df.columns]]


def to_geojson(df: pd.DataFrame, path: Path) -> None:
    features = []
    prop_cols = [c for c in df.columns if c not in ("lon_centre", "lat_centre")]

    for _, row in df.iterrows():
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

        features.append({
            "type": "Feature",
            "geometry": {
                "type": "Point",
                "coordinates": [
                    round(float(row["lon_centre"]), 6),
                    round(float(row["lat_centre"]), 6),
                ],
            },
            "properties": props,
        })

    geojson = {
        "type": "FeatureCollection",
        "crs": {"type": "name", "properties": {"name": "EPSG:4326"}},
        "features": features,
    }

    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(geojson, f, ensure_ascii=False, separators=(",", ":"))

    print(f"  GeoJSON sauvegarde : {path}  ({path.stat().st_size / 1024:.0f} KB, {len(features)} features)")


def print_stats(df: pd.DataFrame) -> None:
    print(f"\n  Distribution par niveau de tension")
    dist = df["itr_label"].value_counts().reindex(LABELS).fillna(0).astype(int)
    for label, count in dist.items():
        pct = count / len(df) * 100
        bar = chr(9608) * int(pct / 2)
        print(f"  {label:<18} {count:>5} rues  {pct:>5.1f}%  {bar}")

    print(f"\n  Top 5 rues les plus TENDUES")
    top = df.nlargest(5, "itr_score")[
        ["nom_voie", "arrondissement", "prix_m2_median",
         "nb_transactions", "nb_logements_sociaux", "itr_score"]
    ]
    for _, r in top.iterrows():
        print(f"  [{r['itr_score']:>6.1f}] {r['nom_voie']:<35} "
              f"arr.{int(r['arrondissement']):02d}  "
              f"{r['prix_m2_median']:>6.0f}e/m2  "
              f"{int(r['nb_transactions'])} ventes  "
              f"logsoc={int(r['nb_logements_sociaux'])}")

    print(f"\n  Top 5 rues les plus ACCESSIBLES")
    bot = df.nsmallest(5, "itr_score")[
        ["nom_voie", "arrondissement", "prix_m2_median",
         "nb_transactions", "nb_logements_sociaux", "itr_score"]
    ]
    for _, r in bot.iterrows():
        print(f"  [{r['itr_score']:>6.1f}] {r['nom_voie']:<35} "
              f"arr.{int(r['arrondissement']):02d}  "
              f"{r['prix_m2_median']:>6.0f}e/m2  "
              f"{int(r['nb_transactions'])} ventes  "
              f"logsoc={int(r['nb_logements_sociaux'])}")


def validate(df: pd.DataFrame) -> None:
    assert "itr_score" in df.columns
    assert df["itr_score"].between(0, 100).all()
    assert df["lon_centre"].between(2.2, 2.5).all()
    assert df["lat_centre"].between(48.8, 48.95).all()
    assert df["itr_score"].isna().sum() == 0
    print(f"\n  [OK] {len(df):,} rues avec score ITR valide")
    print(f"  [OK] Coordonnees GPS dans la bbox Paris")
    print(f"  [OK] Scores dans [0, 100]")


def run() -> pd.DataFrame:
    print("=== GOLD : Calcul ITR par rue ===")
    df = pd.read_parquet(SILVER_PATH)
    print(f"  Table silver chargee : {len(df):,} rues")

    df = compute_itr(df)
    df = finalize_columns(df)
    validate(df)
    print_stats(df)

    OUT_PARQUET.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(OUT_PARQUET, index=False)
    print(f"\n  Parquet sauvegarde : {OUT_PARQUET}  ({OUT_PARQUET.stat().st_size / 1024:.0f} KB)")

    to_geojson(df, OUT_GEOJSON)
    return df


if __name__ == "__main__":
    run()
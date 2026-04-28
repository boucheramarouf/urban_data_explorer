"""
GOLD — Calcul IAML par rue
==========================
IAML = prix median m2 / score accessibilite transport.
"""

import json
from pathlib import Path

import numpy as np
import pandas as pd

SILVER_PATH = Path("data/silver/silver_IAML/rue_accessibilite.parquet")
OUT_PARQUET = Path("data/gold/gold_IAML/iaml_par_rue.parquet")
OUT_GEOJSON = Path("data/gold/gold_IAML/iaml_par_rue.geojson")

LABELS = ["Très accessible", "Accessible", "Modéré", "Tendu", "Très tendu"]


def compute_iaml(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()

    out["score_accessibilite_safe"] = out["score_accessibilite"].clip(lower=1)
    out["iaml_brut"] = out["prix_m2_median"] / out["score_accessibilite_safe"]

    # Rang percentile pour un score robustement distribue entre 0 et 100.
    out["iaml_score"] = (out["iaml_brut"].rank(pct=True) * 100).round(1)

    out["iaml_label"] = pd.cut(
        out["iaml_score"],
        bins=[0, 20, 40, 60, 80, 100],
        labels=LABELS,
        include_lowest=True,
    ).astype(str)

    return out


def finalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    cols = [
        "nom_voie",
        "code_postal",
        "arrondissement",
        "lon_centre",
        "lat_centre",
        "prix_m2_median",
        "nb_transactions",
        "nb_lignes_metro",
        "nb_lignes_bus",
        "nb_points_velib",
        "score_accessibilite",
        "iaml_brut",
        "iaml_score",
        "iaml_label",
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

        features.append(
            {
                "type": "Feature",
                "geometry": {
                    "type": "Point",
                    "coordinates": [round(float(row["lon_centre"]), 6), round(float(row["lat_centre"]), 6)],
                },
                "properties": props,
            }
        )

    geojson = {
        "type": "FeatureCollection",
        "crs": {"type": "name", "properties": {"name": "EPSG:4326"}},
        "features": features,
    }

    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(geojson, f, ensure_ascii=False, separators=(",", ":"))


def validate(df: pd.DataFrame) -> None:
    assert len(df) > 0, "Table GOLD IAML vide"
    assert df["iaml_score"].between(0, 100).all()
    assert df["lon_centre"].between(2.2, 2.5).all()
    assert df["lat_centre"].between(48.8, 48.95).all()



def run() -> pd.DataFrame:
    print("=== GOLD : Calcul IAML par rue ===")
    df = pd.read_parquet(SILVER_PATH)
    df = compute_iaml(df)
    df = finalize_columns(df)
    validate(df)

    OUT_PARQUET.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(OUT_PARQUET, index=False)
    print(f"  Parquet sauvegarde : {OUT_PARQUET}")

    to_geojson(df, OUT_GEOJSON)
    print(f"  GeoJSON sauvegarde : {OUT_GEOJSON}")
    return df


if __name__ == "__main__":
    run()

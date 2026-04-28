"""
BRONZE — IAML Velib / Veligo
============================
Consolide les points velo (stations/points de contact) pour l'indicateur IAML.
"""

from pathlib import Path

import pandas as pd

RAW_PARKING = Path("data/raw/raw_IAML/parking-velos-ile-de-france-mobilites.csv")
RAW_CONTACTS = Path("data/raw/raw_IAML/points-de-contact-veligo-location.csv")
OUTPUT_PATH = Path("data/bronze/bronze_IAML/velib_points_raw.parquet")


def _load_parking() -> pd.DataFrame:
    df = pd.read_csv(RAW_PARKING, sep=";", encoding="utf-8-sig", low_memory=False)

    df["insee_code"] = df["insee_code"].astype(str).str.strip()
    df = df[df["insee_code"].str.startswith("75")].copy()

    df["x_long"] = pd.to_numeric(df["x_long"], errors="coerce")
    df["y_lat"] = pd.to_numeric(df["y_lat"], errors="coerce")
    df = df.dropna(subset=["x_long", "y_lat"]).copy()

    return pd.DataFrame(
        {
            "point_key": "VELIB:" + df["station_id"].astype(str),
            "point_name": df["name_station"].fillna(df["name"]).astype(str),
            "source": "velib_parking",
            "lon": df["x_long"].astype(float),
            "lat": df["y_lat"].astype(float),
        }
    )


def _load_contacts() -> pd.DataFrame:
    df = pd.read_csv(RAW_CONTACTS, sep=";", encoding="utf-8-sig", low_memory=False)

    df["Code_insee"] = df["Code_insee"].astype(str).str.strip()
    df = df[df["Code_insee"].str.startswith("75")].copy()

    df["x_long"] = pd.to_numeric(df["x_long"], errors="coerce")
    df["y_lat"] = pd.to_numeric(df["y_lat"], errors="coerce")
    df = df.dropna(subset=["x_long", "y_lat"]).copy()

    return pd.DataFrame(
        {
            "point_key": "VELIGO:" + df["Nom du site"].astype(str).str.upper().str.replace("\\s+", "_", regex=True),
            "point_name": df["Nom du site"].astype(str),
            "source": "veligo_contact",
            "lon": df["x_long"].astype(float),
            "lat": df["y_lat"].astype(float),
        }
    )


def load_velib_points() -> pd.DataFrame:
    parking = _load_parking()
    contacts = _load_contacts()
    df = pd.concat([parking, contacts], ignore_index=True)
    return df.drop_duplicates(subset=["point_key", "lon", "lat"])


def validate(df: pd.DataFrame) -> None:
    assert len(df) > 0, "Aucun point velo charge"
    assert {"point_key", "lon", "lat"}.issubset(df.columns)
    print(f"  [OK] points velo total : {len(df):,}")
    print(f"  [OK] sources           : {df['source'].value_counts().to_dict()}")



def run() -> pd.DataFrame:
    print("=== BRONZE : IAML Velib/Veligo ===")
    df = load_velib_points()
    validate(df)
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(OUTPUT_PATH, index=False)
    print(f"  Sauvegarde : {OUTPUT_PATH}")
    return df


if __name__ == "__main__":
    run()

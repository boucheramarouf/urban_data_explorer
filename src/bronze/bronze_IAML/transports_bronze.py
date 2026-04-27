"""
BRONZE — IAML Transports (metro / bus)
======================================
Ingestion brute des arrets/lignes de transport pour l'indicateur IAML.
"""

from pathlib import Path

import pandas as pd

RAW_PATH = Path("data/raw/raw_IAML/arrets-lignes.csv")
OUTPUT_PATH = Path("data/bronze/bronze_IAML/transports_points_raw.parquet")
PARIS_INSEE = "75056"


def _normalize_mode(value: str) -> str:
    if not isinstance(value, str):
        return "autre"
    v = value.strip().lower()
    if "metro" in v:
        return "metro"
    if "bus" in v:
        return "bus"
    return "autre"


def load_transports(path: Path = RAW_PATH) -> pd.DataFrame:
    df = pd.read_csv(path, sep=";", encoding="utf-8-sig", low_memory=False)

    # Filtrer Paris intra-muros.
    df["Code_insee"] = df["Code_insee"].astype(str).str.strip()
    df = df[df["Code_insee"] == PARIS_INSEE].copy()

    df["stop_lon"] = pd.to_numeric(df["stop_lon"], errors="coerce")
    df["stop_lat"] = pd.to_numeric(df["stop_lat"], errors="coerce")
    df = df.dropna(subset=["stop_lon", "stop_lat", "route_id", "mode"]).copy()

    df["mode_group"] = df["mode"].map(_normalize_mode)
    df = df[df["mode_group"].isin(["metro", "bus"])].copy()

    out = pd.DataFrame(
        {
            "line_key": df["route_id"].astype(str),
            "line_name": df["route_long_name"].astype(str),
            "mode_group": df["mode_group"].astype(str),
            "stop_id": df["stop_id"].astype(str),
            "stop_name": df["stop_name"].astype(str),
            "lon": df["stop_lon"].astype(float),
            "lat": df["stop_lat"].astype(float),
        }
    )

    return out.drop_duplicates()


def validate(df: pd.DataFrame) -> None:
    assert len(df) > 0, "Aucune ligne transport chargee"
    assert {"line_key", "mode_group", "lon", "lat"}.issubset(df.columns)
    assert df["mode_group"].isin(["metro", "bus"]).all()
    print(f"  [OK] arrets transport : {len(df):,}")
    print(f"  [OK] lignes uniques   : {df['line_key'].nunique():,}")



def run() -> pd.DataFrame:
    print("=== BRONZE : IAML Transports ===")
    df = load_transports()
    validate(df)
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(OUTPUT_PATH, index=False)
    print(f"  Sauvegarde : {OUTPUT_PATH}")
    return df


if __name__ == "__main__":
    run()

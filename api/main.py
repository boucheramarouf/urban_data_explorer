"""
API FastAPI — Urban Data Explorer
=================================
Expose les indicateurs ITR, SVP et IAML par rue parisienne.
"""

import json
import os
from pathlib import Path
from typing import Optional

import pandas as pd
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError

from api.svp_router import router as svp_router

GOLD_PARQUET_ITR = Path("data/gold/gold_ITR/itr_par_rue.parquet")
GOLD_GEOJSON_ITR = Path("data/gold/gold_ITR/itr_par_rue.geojson")
GOLD_PARQUET_IAML = Path("data/gold/gold_IAML/iaml_par_rue.parquet")
GOLD_GEOJSON_IAML = Path("data/gold/gold_IAML/iaml_par_rue.geojson")

DATABASE_URL = os.getenv("DATABASE_URL")
engine = None
if DATABASE_URL:
  engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    pool_recycle=300,
    future=True,
  )

app = FastAPI(
  title="Urban Data Explorer — Paris",
  description="API exposant les indicateurs ITR, SVP et IAML par rue parisienne.",
  version="1.0.0",
)

app.add_middleware(
  CORSMiddleware,
  allow_origins=["*"],
  allow_methods=["GET"],
  allow_headers=["*"],
)

app.include_router(svp_router, prefix="/svp")

_df_itr: Optional[pd.DataFrame] = None
_df_iaml: Optional[pd.DataFrame] = None


def is_db_ready() -> bool:
  if engine is None:
    return False
  try:
    with engine.connect() as conn:
      conn.execute(text("SELECT 1"))
    return True
  except SQLAlchemyError:
    return False


def _load_parquet(path: Path, label: str) -> pd.DataFrame:
  if not path.exists():
    raise RuntimeError(f"Fichier gold introuvable pour {label} : {path}")
  return pd.read_parquet(path)


def _load_sql(table_name: str) -> pd.DataFrame:
  if engine is None or not is_db_ready():
    raise RuntimeError("Base de données indisponible")
  return pd.read_sql(f"SELECT * FROM {table_name}", engine)


def get_df_itr() -> pd.DataFrame:
  global _df_itr
  if _df_itr is None:
    try:
      _df_itr = _load_sql("itr_par_rue")
    except Exception:
      _df_itr = _load_parquet(GOLD_PARQUET_ITR, "ITR")
  return _df_itr


def get_df_iaml() -> pd.DataFrame:
  global _df_iaml
  if _df_iaml is None:
    try:
      _df_iaml = _load_sql("iaml_par_rue")
    except Exception:
      _df_iaml = _load_parquet(GOLD_PARQUET_IAML, "IAML")
  return _df_iaml


def _serialize_value(value):
  if hasattr(value, "item"):
    value = value.item()
  if pd.isna(value):
    return None
  if isinstance(value, float):
    return round(value, 4)
  return value


def _df_to_records(df: pd.DataFrame) -> list[dict]:
  records = []
  for _, row in df.iterrows():
    records.append({col: _serialize_value(row[col]) for col in df.columns})
  return records


def _df_to_geojson(df: pd.DataFrame) -> dict:
  features = []
  prop_cols = [c for c in df.columns if c not in ("lon_centre", "lat_centre")]

  for _, row in df.iterrows():
    props = {col: _serialize_value(row[col]) for col in prop_cols}
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

  return {
    "type": "FeatureCollection",
    "count": len(features),
    "features": features,
  }


def _indicator_status(name: str, getter, score_field: str) -> dict:
  try:
    df = getter()
    return {
      "disponible": True,
      "nb_rues": len(df),
      "score_median": round(float(df[score_field].median()), 2),
    }
  except Exception as exc:
    return {"disponible": False, "erreur": str(exc)}


@app.get("/", tags=["Healthcheck"])
@app.get("/health", tags=["Healthcheck"])
def root():
  return {
    "status": "ok",
    "version": "1.0.0",
    "db_status": "ok" if is_db_ready() else "down",
    "indicateurs": {
      "ITR": _indicator_status("ITR", get_df_itr, "itr_score"),
      "SVP": {"disponible": True},
      "IAML": _indicator_status("IAML", get_df_iaml, "iaml_score"),
    },
  }


@app.get("/stats", tags=["Statistiques"])
def stats():
  df = get_df_itr()
  dist_label = (
    df["itr_label"]
    .value_counts()
    .reindex(["Très accessible", "Accessible", "Modéré", "Tendu", "Très tendu"])
    .fillna(0)
    .astype(int)
    .to_dict()
  )
  by_arrdt = (
    df.groupby("arrondissement")
    .agg(
      nb_rues=("itr_score", "count"),
      itr_score_median=("itr_score", "median"),
      prix_m2_median=("prix_m2_median", "median"),
      revenu_median=("revenu_median_uc", "median"),
    )
    .round(2)
    .reset_index()
    .sort_values("itr_score_median", ascending=False)
    .to_dict(orient="records")
  )

  return {
    "nb_rues_total": len(df),
    "itr_score_min": round(float(df["itr_score"].min()), 2),
    "itr_score_max": round(float(df["itr_score"].max()), 2),
    "itr_score_median": round(float(df["itr_score"].median()), 2),
    "itr_score_mean": round(float(df["itr_score"].mean()), 2),
    "distribution_label": dist_label,
    "par_arrondissement": by_arrdt,
  }


@app.get("/rues", tags=["Rues"])
def list_rues(
  arrondissement: Optional[int] = Query(None),
  label: Optional[str] = Query(None),
  score_min: Optional[float] = Query(None),
  score_max: Optional[float] = Query(None),
  sort_by: str = Query("itr_score"),
  order: str = Query("desc"),
  limit: int = Query(100, ge=1, le=2500),
):
  df = get_df_itr().copy()

  if arrondissement is not None:
    df = df[df["arrondissement"] == arrondissement]
  if label is not None:
    df = df[df["itr_label"] == label]
  if score_min is not None:
    df = df[df["itr_score"] >= score_min]
  if score_max is not None:
    df = df[df["itr_score"] <= score_max]

  valid_sort = ["itr_score", "prix_m2_median", "nb_transactions", "revenu_median_uc"]
  if sort_by not in valid_sort:
    raise HTTPException(status_code=400, detail=f"sort_by doit être parmi : {valid_sort}")

  df = df.sort_values(sort_by, ascending=(order == "asc")).head(limit)
  cols_out = [
    "nom_voie", "code_postal", "arrondissement",
    "lon_centre", "lat_centre",
    "prix_m2_median", "revenu_median_uc", "nb_logements_sociaux",
    "nb_transactions", "itr_score", "itr_label",
  ]
  df = df[[c for c in cols_out if c in df.columns]]

  return {
    "count": len(df),
    "filtres": {
      "arrondissement": arrondissement,
      "label": label,
      "score_min": score_min,
      "score_max": score_max,
    },
    "rues": _df_to_records(df),
  }


@app.get("/rues/{nom_voie}", tags=["Rues"])
def get_rue(
  nom_voie: str,
  code_postal: Optional[int] = Query(None),
):
  df = get_df_itr()
  mask = df["nom_voie"].str.upper() == nom_voie.upper()
  if code_postal is not None:
    mask &= df["code_postal"] == code_postal

  results = df[mask]
  if results.empty:
    raise HTTPException(status_code=404, detail=f"Rue '{nom_voie}' introuvable.")

  return {
    "count": len(results),
    "results": _df_to_records(results),
  }


@app.get("/geojson", tags=["Carte"])
def geojson(
  arrondissement: Optional[int] = Query(None),
  label: Optional[str] = Query(None),
  score_min: Optional[float] = Query(None),
  score_max: Optional[float] = Query(None),
):
  if all(p is None for p in [arrondissement, label, score_min, score_max]) and GOLD_GEOJSON_ITR.exists():
    with open(GOLD_GEOJSON_ITR, encoding="utf-8") as f:
      return JSONResponse(content=json.load(f))

  df = get_df_itr().copy()
  if arrondissement is not None:
    df = df[df["arrondissement"] == arrondissement]
  if label is not None:
    df = df[df["itr_label"] == label]
  if score_min is not None:
    df = df[df["itr_score"] >= score_min]
  if score_max is not None:
    df = df[df["itr_score"] <= score_max]

  return JSONResponse(content=_df_to_geojson(df))


@app.get("/iaml/stats", tags=["IAML"])
def iaml_stats():
  df = get_df_iaml()
  dist_label = (
    df["iaml_label"]
    .value_counts()
    .reindex(["Très accessible", "Accessible", "Modéré", "Tendu", "Très tendu"])
    .fillna(0)
    .astype(int)
    .to_dict()
  )
  by_arrdt = (
    df.groupby("arrondissement")
    .agg(
      nb_rues=("iaml_score", "count"),
      iaml_score_median=("iaml_score", "median"),
      prix_m2_median=("prix_m2_median", "median"),
      score_accessibilite_median=("score_accessibilite", "median"),
    )
    .round(2)
    .reset_index()
    .sort_values("iaml_score_median", ascending=False)
    .to_dict(orient="records")
  )

  return {
    "nb_rues_total": len(df),
    "iaml_score_min": round(float(df["iaml_score"].min()), 2),
    "iaml_score_max": round(float(df["iaml_score"].max()), 2),
    "iaml_score_median": round(float(df["iaml_score"].median()), 2),
    "iaml_score_mean": round(float(df["iaml_score"].mean()), 2),
    "distribution_label": dist_label,
    "par_arrondissement": by_arrdt,
  }


@app.get("/iaml/rues", tags=["IAML"])
def iaml_list_rues(
  arrondissement: Optional[int] = Query(None),
  label: Optional[str] = Query(None),
  score_min: Optional[float] = Query(None),
  score_max: Optional[float] = Query(None),
  sort_by: str = Query("iaml_score"),
  order: str = Query("desc"),
  limit: int = Query(100, ge=1, le=2500),
):
  df = get_df_iaml().copy()

  if arrondissement is not None:
    df = df[df["arrondissement"] == arrondissement]
  if label is not None:
    df = df[df["iaml_label"] == label]
  if score_min is not None:
    df = df[df["iaml_score"] >= score_min]
  if score_max is not None:
    df = df[df["iaml_score"] <= score_max]

  valid_sort = ["iaml_score", "prix_m2_median", "score_accessibilite", "nb_transactions"]
  if sort_by not in valid_sort:
    raise HTTPException(status_code=400, detail=f"sort_by doit être parmi : {valid_sort}")

  df = df.sort_values(sort_by, ascending=(order == "asc")).head(limit)
  cols_out = [
    "nom_voie", "code_postal", "arrondissement",
    "lon_centre", "lat_centre",
    "prix_m2_median", "nb_transactions",
    "nb_lignes_metro", "nb_lignes_bus", "nb_points_velib",
    "score_accessibilite", "iaml_score", "iaml_label",
  ]
  df = df[[c for c in cols_out if c in df.columns]]

  return {
    "count": len(df),
    "filtres": {
      "arrondissement": arrondissement,
      "label": label,
      "score_min": score_min,
      "score_max": score_max,
    },
    "rues": _df_to_records(df),
  }


@app.get("/iaml/rues/{nom_voie}", tags=["IAML"])
def iaml_get_rue(
  nom_voie: str,
  code_postal: Optional[int] = Query(None),
):
  df = get_df_iaml()
  mask = df["nom_voie"].str.upper() == nom_voie.upper()
  if code_postal is not None:
    mask &= df["code_postal"] == code_postal

  results = df[mask]
  if results.empty:
    raise HTTPException(status_code=404, detail=f"Rue '{nom_voie}' introuvable pour IAML.")

  return {
    "count": len(results),
    "results": _df_to_records(results),
  }


@app.get("/iaml/geojson", tags=["IAML"])
def iaml_geojson(
  arrondissement: Optional[int] = Query(None),
  label: Optional[str] = Query(None),
  score_min: Optional[float] = Query(None),
  score_max: Optional[float] = Query(None),
):
  if all(p is None for p in [arrondissement, label, score_min, score_max]) and GOLD_GEOJSON_IAML.exists():
    with open(GOLD_GEOJSON_IAML, encoding="utf-8") as f:
      return JSONResponse(content=json.load(f))

  df = get_df_iaml().copy()
  if arrondissement is not None:
    df = df[df["arrondissement"] == arrondissement]
  if label is not None:
    df = df[df["iaml_label"] == label]
  if score_min is not None:
    df = df[df["iaml_score"] >= score_min]
  if score_max is not None:
    df = df[df["iaml_score"] <= score_max]

  return JSONResponse(content=_df_to_geojson(df))

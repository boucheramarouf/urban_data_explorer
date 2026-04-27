"""
API FastAPI — Urban Data Explorer
==================================
Sert les données IMQ et ITR au frontend React.

  IMQ (Indice de Mutation de Quartier) :
    GET /imq/geojson  → FeatureCollection IRIS + score IMQ (filtrable)
    GET /imq/stats    → KPIs globaux et classement par arrondissement

  ITR (Indice de Tension Résidentielle) :
    GET /itr/geojson  → FeatureCollection rues + score ITR (filtrable)
    GET /itr/stats    → KPIs globaux et classement par arrondissement
"""

import json
import warnings
from pathlib import Path
from typing import Optional

import pandas as pd
import geopandas as gpd
from fastapi import FastAPI, Query, APIRouter
from fastapi.middleware.cors import CORSMiddleware

# ─── Chemins ──────────────────────────────────────────────────────────────────
BASE = Path(__file__).parent.parent

IMQ_PARQUET = BASE / "data" / "gold" / "gold_IMQ" / "imq_par_iris.parquet"
IMQ_GEOJSON = BASE / "data" / "raw"  / "raw_IMQ"  / "iris_paris.geojson"
ITR_PARQUET = BASE / "data" / "gold" / "gold_ITR" / "itr_par_rue.parquet"
ITR_GEOJSON = BASE / "data" / "gold" / "gold_ITR" / "itr_par_rue.geojson"


# ─── Chargement IMQ ──────────────────────────────────────────────────────────
print("Chargement des données IMQ...")

df_imq = pd.read_parquet(IMQ_PARQUET)
df_imq["iris_code"] = df_imq["iris_code"].astype(str).str.zfill(9)
df_imq["arrondissement"] = df_imq["arr_insee"].astype(str).str[-2:].astype(int)
df_imq["score_imq_100"] = (df_imq["score_imq"] * 100).round(1)

gdf_iris = gpd.read_file(IMQ_GEOJSON)
gdf_iris["iris_code"] = gdf_iris["code_iris"].astype(str).str.zfill(9)
gdf_imq = gdf_iris[["iris_code", "geometry"]].merge(df_imq, on="iris_code", how="inner")

with warnings.catch_warnings():
    warnings.simplefilter("ignore")
    gdf_imq["lon_centre"] = gdf_imq.geometry.centroid.x.round(6)
    gdf_imq["lat_centre"] = gdf_imq.geometry.centroid.y.round(6)

print(f"  {len(gdf_imq)} IRIS IMQ chargés · prêts à servir")


# ─── Chargement ITR ──────────────────────────────────────────────────────────
print("Chargement des données ITR...")

df_itr = pd.read_parquet(ITR_PARQUET)
_itr_geojson_full = json.loads(ITR_GEOJSON.read_text(encoding="utf-8"))

print(f"  {len(df_itr)} rues ITR chargées · prêtes à servir")


# ─── App ──────────────────────────────────────────────────────────────────────
app = FastAPI(title="Urban Data Explorer — API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET"],
    allow_headers=["*"],
)


# ─── Routeur IMQ ──────────────────────────────────────────────────────────────
imq_router = APIRouter(prefix="/imq", tags=["IMQ"])


@imq_router.get("/geojson")
def imq_geojson(
    arrondissement: Optional[int]   = Query(None, description="Numéro 1–20"),
    interpretation: Optional[str]   = Query(None, description="Stable | Mutation modérée | Mutation forte"),
    score_min:      Optional[float] = Query(None, ge=0, le=100),
    score_max:      Optional[float] = Query(None, ge=0, le=100),
):
    mask = pd.Series([True] * len(gdf_imq), index=gdf_imq.index)

    if arrondissement is not None:
        mask &= (gdf_imq["arrondissement"] == arrondissement)
    if interpretation:
        mask &= (gdf_imq["interpretation"] == interpretation)
    if score_min is not None:
        mask &= (gdf_imq["score_imq_100"] >= score_min)
    if score_max is not None:
        mask &= (gdf_imq["score_imq_100"] <= score_max)

    return json.loads(gdf_imq[mask].to_json())


@imq_router.get("/stats")
def imq_stats():
    score_median = round(float(df_imq["score_imq_100"].median()), 1)
    distribution = df_imq["interpretation"].value_counts().to_dict()

    par_arr = (
        df_imq.groupby("arrondissement")
        .agg(
            score_imq_median=("score_imq_100", "median"),
            nb_iris=("iris_code", "count"),
        )
        .reset_index()
        .round({"score_imq_median": 1})
        .to_dict(orient="records")
    )

    return {
        "nb_iris_total":      len(df_imq),
        "score_imq_median":   score_median,
        "distribution_label": distribution,
        "par_arrondissement": par_arr,
    }


# ─── Routeur ITR ──────────────────────────────────────────────────────────────
itr_router = APIRouter(prefix="/itr", tags=["ITR"])


@itr_router.get("/geojson")
def itr_geojson(
    arrondissement: Optional[int]   = Query(None, description="Numéro 1–20"),
    label:          Optional[str]   = Query(None, description="Très accessible | Accessible | Modéré | Tendu | Très tendu"),
    score_min:      Optional[float] = Query(None, ge=0, le=100),
    score_max:      Optional[float] = Query(None, ge=0, le=100),
):
    features = _itr_geojson_full["features"]

    if arrondissement is not None:
        features = [f for f in features if f["properties"].get("arrondissement") == arrondissement]
    if label:
        features = [f for f in features if f["properties"].get("itr_label") == label]
    if score_min is not None:
        features = [f for f in features if (f["properties"].get("itr_score") or 0) >= score_min]
    if score_max is not None:
        features = [f for f in features if (f["properties"].get("itr_score") or 100) <= score_max]

    return {"type": "FeatureCollection", "features": features}


@itr_router.get("/stats")
def itr_stats():
    dist = df_itr["itr_label"].value_counts().to_dict()

    par_arr = (
        df_itr.groupby("arrondissement")
        .agg(
            itr_score_median=("itr_score", "median"),
            nb_rues=("nom_voie", "count"),
        )
        .reset_index()
        .round({"itr_score_median": 1})
        .to_dict(orient="records")
    )

    return {
        "nb_rues_total":      len(df_itr),
        "itr_score_median":   round(float(df_itr["itr_score"].median()), 1),
        "distribution_label": dist,
        "par_arrondissement": par_arr,
    }


# ─── Enregistrement des routeurs ─────────────────────────────────────────────
app.include_router(imq_router)
app.include_router(itr_router)

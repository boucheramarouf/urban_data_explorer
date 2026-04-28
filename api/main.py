"""
API FastAPI — Urban Data Explorer
==================================
Sert les données IMQ, ITR, SVP et IAML au frontend React.

  IMQ (Indice de Mutation de Quartier) :
    GET /imq/geojson  → FeatureCollection IRIS + score IMQ (filtrable)
    GET /imq/stats    → KPIs globaux et classement par arrondissement

  ITR (Indice de Tension Résidentielle) :
    GET /itr/geojson  → FeatureCollection rues + score ITR (filtrable)
    GET /itr/stats    → KPIs globaux et classement par arrondissement
    GET /itr/rues     → Liste paginée et filtrée
    GET /itr/rues/{nom_voie} → Détail d'une rue

  SVP (Score de Verdure et Proximité) :
    GET /svp/*        → Routes gérées par le routeur SVP

  IAML (Indice d'Accessibilité Multimodale au Logement) :
    GET /iaml/geojson → FeatureCollection rues + score IAML
    GET /iaml/stats   → KPIs globaux et classement par arrondissement
    GET /iaml/rues    → Liste paginée et filtrée
    GET /iaml/rues/{nom_voie} → Détail d'une rue
"""

import json
import os
import warnings
from pathlib import Path
from typing import Optional

import geopandas as gpd
import pandas as pd
from fastapi import APIRouter, FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, RedirectResponse

# ─── Import optionnel de sqlalchemy ──────────────────────────────────────────
try:
    from sqlalchemy import create_engine, text
    from sqlalchemy.exc import SQLAlchemyError
    _SQLALCHEMY_AVAILABLE = True
except ImportError:
    _SQLALCHEMY_AVAILABLE = False

# ─── Import optionnel du routeur SVP ─────────────────────────────────────────
try:
    from api.svp_router import router as svp_router
    _SVP_ROUTER_AVAILABLE = True
except ImportError:
    svp_router = None
    _SVP_ROUTER_AVAILABLE = False

# ─── Chemins ──────────────────────────────────────────────────────────────────
BASE = Path(__file__).parent.parent

IMQ_PARQUET = BASE / "data" / "gold" / "gold_IMQ" / "imq_par_iris.parquet"
IMQ_GEOJSON = BASE / "data" / "raw" / "raw_IMQ" / "iris_paris.geojson"
ITR_PARQUET = BASE / "data" / "gold" / "gold_ITR" / "itr_par_rue.parquet"
ITR_GEOJSON = BASE / "data" / "gold" / "gold_ITR" / "itr_par_rue.geojson"
IAML_PARQUET = BASE / "data" / "gold" / "gold_IAML" / "iaml_par_rue.parquet"
IAML_GEOJSON = BASE / "data" / "gold" / "gold_IAML" / "iaml_par_rue.geojson"

# ─── Base de données (optionnelle) ────────────────────────────────────────────
DATABASE_URL = os.getenv("DATABASE_URL")
engine = None
if DATABASE_URL and _SQLALCHEMY_AVAILABLE:
    engine = create_engine(
        DATABASE_URL,
        pool_pre_ping=True,
        pool_recycle=300,
        future=True,
    )


def is_db_ready() -> bool:
    if engine is None or not _SQLALCHEMY_AVAILABLE:
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
        features.append(
            {
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
        )

    return {
        "type": "FeatureCollection",
        "count": len(features),
        "features": features,
    }


_df_itr: Optional[pd.DataFrame] = None
_df_iaml: Optional[pd.DataFrame] = None


def get_df_itr() -> pd.DataFrame:
    global _df_itr
    if _df_itr is None:
        try:
            _df_itr = _load_sql("itr_par_rue")
        except Exception:
            _df_itr = _load_parquet(ITR_PARQUET, "ITR")
    return _df_itr


def get_df_iaml() -> pd.DataFrame:
    global _df_iaml
    if _df_iaml is None:
        try:
            _df_iaml = _load_sql("iaml_par_rue")
        except Exception:
            _df_iaml = _load_parquet(IAML_PARQUET, "IAML")
    return _df_iaml


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

_itr_geojson_full = json.loads(ITR_GEOJSON.read_text(encoding="utf-8"))
itr_count = len(_itr_geojson_full.get("features", []))
print(f"  {itr_count} rues ITR chargées · prêtes à servir")


# ─── App ──────────────────────────────────────────────────────────────────────
app = FastAPI(
    title="Urban Data Explorer — API",
    description="API exposant les indicateurs IMQ, ITR, SVP et IAML pour Paris.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET"],
    allow_headers=["*"],
)

if _SVP_ROUTER_AVAILABLE:
    app.include_router(svp_router, prefix="/svp")


@app.get("/", include_in_schema=False)
def root():
    return RedirectResponse(url="/docs")


@app.get("/health", tags=["Healthcheck"])
def health():
    return {
        "status": "ok",
        "version": "1.0.0",
        "db_status": "ok" if is_db_ready() else "down",
        "indicateurs": {
            "IMQ": {"disponible": IMQ_PARQUET.exists(), "nb_iris": len(df_imq)},
            "ITR": _indicator_status("ITR", get_df_itr, "itr_score"),
            "SVP": {"disponible": _SVP_ROUTER_AVAILABLE},
            "IAML": _indicator_status("IAML", get_df_iaml, "iaml_score"),
        },
    }


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
    df = get_df_itr()
    dist = df["itr_label"].value_counts().to_dict()

    par_arr = (
        df.groupby("arrondissement")
        .agg(
            itr_score_median=("itr_score", "median"),
            nb_rues=("nom_voie", "count"),
        )
        .reset_index()
        .round({"itr_score_median": 1})
        .to_dict(orient="records")
    )

    return {
        "nb_rues_total":      len(df),
        "itr_score_median":   round(float(df["itr_score"].median()), 1),
        "distribution_label": dist,
        "par_arrondissement": par_arr,
    }


@itr_router.get("/rues")
def itr_list_rues(
    arrondissement: Optional[int]   = Query(None),
    label:          Optional[str]   = Query(None),
    score_min:      Optional[float] = Query(None),
    score_max:      Optional[float] = Query(None),
    sort_by:        str             = Query("itr_score"),
    order:          str             = Query("desc"),
    limit:          int             = Query(100, ge=1, le=2500),
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

    return {"count": len(df), "rues": _df_to_records(df)}


@itr_router.get("/rues/{nom_voie}")
def itr_get_rue(
    nom_voie:    str,
    code_postal: Optional[int] = Query(None),
):
    df = get_df_itr()
    mask = df["nom_voie"].str.upper() == nom_voie.upper()
    if code_postal is not None:
        mask &= df["code_postal"] == code_postal

    results = df[mask]
    if results.empty:
        raise HTTPException(status_code=404, detail=f"Rue '{nom_voie}' introuvable.")

    return {"count": len(results), "results": _df_to_records(results)}


# ─── Routes IAML ──────────────────────────────────────────────────────────────
iaml_router = APIRouter(prefix="/iaml", tags=["IAML"])


@iaml_router.get("/stats")
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
        "nb_rues_total":      len(df),
        "iaml_score_min":     round(float(df["iaml_score"].min()), 2),
        "iaml_score_max":     round(float(df["iaml_score"].max()), 2),
        "iaml_score_median":  round(float(df["iaml_score"].median()), 2),
        "iaml_score_mean":    round(float(df["iaml_score"].mean()), 2),
        "distribution_label": dist_label,
        "par_arrondissement": by_arrdt,
    }


@iaml_router.get("/rues")
def iaml_list_rues(
    arrondissement: Optional[int]   = Query(None),
    label:          Optional[str]   = Query(None),
    score_min:      Optional[float] = Query(None),
    score_max:      Optional[float] = Query(None),
    sort_by:        str             = Query("iaml_score"),
    order:          str             = Query("desc"),
    limit:          int             = Query(100, ge=1, le=2500),
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

    return {"count": len(df), "rues": _df_to_records(df)}


@iaml_router.get("/rues/{nom_voie}")
def iaml_get_rue(
    nom_voie:    str,
    code_postal: Optional[int] = Query(None),
):
    df = get_df_iaml()
    mask = df["nom_voie"].str.upper() == nom_voie.upper()
    if code_postal is not None:
        mask &= df["code_postal"] == code_postal

    results = df[mask]
    if results.empty:
        raise HTTPException(status_code=404, detail=f"Rue '{nom_voie}' introuvable pour IAML.")

    return {"count": len(results), "results": _df_to_records(results)}


@iaml_router.get("/geojson")
def iaml_geojson(
    arrondissement: Optional[int]   = Query(None),
    label:          Optional[str]   = Query(None),
    score_min:      Optional[float] = Query(None),
    score_max:      Optional[float] = Query(None),
):
    if all(p is None for p in [arrondissement, label, score_min, score_max]) and IAML_GEOJSON.exists():
        with open(IAML_GEOJSON, encoding="utf-8") as f:
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


# ─── Enregistrement des routeurs ─────────────────────────────────────────────
app.include_router(imq_router)
app.include_router(itr_router)
app.include_router(iaml_router)

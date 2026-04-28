"""
API FastAPI - SVP (Score de Verdure et Proximite)
=================================================
Expose le SVP agrege par rue, aligne sur la maille ITR.
"""

from pathlib import Path
import json
from typing import Optional

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import JSONResponse
import pandas as pd

GOLD_PARQUET = Path("data/gold/gold_SVP/svp_par_rue.parquet")
GOLD_GEOJSON = Path("data/gold/gold_SVP/svp_par_rue.geojson")

router = APIRouter(tags=["SVP - Score de Verdure et Proximite"])

_df: Optional[pd.DataFrame] = None


def get_df() -> pd.DataFrame:
    global _df
    if _df is None:
        if not GOLD_PARQUET.exists():
            raise RuntimeError(
                f"Fichier gold SVP introuvable : {GOLD_PARQUET}\n"
                "Lancer : python run_pipeline.py --indicateur SVP"
            )
        _df = pd.read_parquet(GOLD_PARQUET)
        if "has_commerce" not in _df.columns:
            _df["has_commerce"] = _df["score_alim_brut"] > 0
    return _df


def _to_record(row: pd.Series, cols: list[str]) -> dict:
    record = {}
    for col in cols:
        if col not in row.index:
            continue
        val = row[col]
        if hasattr(val, "item"):
            record[col] = val.item()
        elif pd.isna(val):
            record[col] = None
        elif isinstance(val, float):
            record[col] = round(val, 4)
        else:
            record[col] = val
    return record


@router.get("/", summary="Healthcheck SVP")
def svp_root():
    df = get_df()
    return {
        "indicateur": "SVP - Score de Verdure et Proximite",
        "version": "4.0.0",
        "formule": "SVP = 0.60*score_vert + 0.40*score_acces_alim (norm. log1p+P99)",
        "nb_rues": len(df),
        "svp_min": round(float(df["svp_score"].min()), 2),
        "svp_max": round(float(df["svp_score"].max()), 2),
        "svp_median": round(float(df["svp_score"].median()), 2),
        "svp_mean": round(float(df["svp_score"].mean()), 2),
        "nb_rues_sans_commerce": int((df["score_alim_brut"] == 0).sum()),
    }


@router.get("/stats", summary="Statistiques SVP Paris")
def svp_stats():
    df = get_df()
    labels_order = ["Très faible", "Faible", "Modéré", "Bon", "Excellent"]
    dist_label = (
        df["svp_label"].value_counts()
        .reindex(labels_order)
        .fillna(0)
        .astype(int)
        .to_dict()
    )
    by_arrondissement = (
        df.groupby("arrondissement")
        .agg(
            nb_rues=("svp_score", "count"),
            svp_score_median=("svp_score", "median"),
            svp_score_mean=("svp_score", "mean"),
            nb_espaces_verts_moy=("nb_espaces_verts", "mean"),
            nb_arbres_moy=("nb_arbres", "mean"),
            score_alim_moy=("score_alim_brut", "mean"),
            nb_rues_sans_commerce=("score_alim_brut", lambda x: (x == 0).sum()),
        )
        .round(2)
        .reset_index()
        .sort_values("svp_score_median", ascending=False)
        .to_dict(orient="records")
    )
    return {
        "nb_rues_total": len(df),
        "nb_rues_sans_commerce": int((df["score_alim_brut"] == 0).sum()),
        "svp_score_min": round(float(df["svp_score"].min()), 2),
        "svp_score_max": round(float(df["svp_score"].max()), 2),
        "svp_score_median": round(float(df["svp_score"].median()), 2),
        "svp_score_mean": round(float(df["svp_score"].mean()), 2),
        "distribution_label": dist_label,
        "par_arrondissement": by_arrondissement,
        "parametres": {
            "rayon_verdure_m": 200,
            "rayon_commerce_m": 500,
            "poids_score_vert": 0.60,
            "poids_score_alim": 0.40,
            "normalisation": "log1p + cap P99",
        },
    }


@router.get("/rues", summary="Liste des rues SVP")
def svp_list_rues(
    arrondissement: Optional[int] = Query(None),
    label: Optional[str] = Query(None),
    score_min: Optional[float] = Query(None),
    score_max: Optional[float] = Query(None),
    has_commerce: Optional[bool] = Query(None),
    sort_by: str = Query("svp_score"),
    order: str = Query("desc"),
    limit: int = Query(5000, ge=1, le=5000),
):
    df = get_df().copy()
    if arrondissement is not None:
        df = df[df["arrondissement"] == arrondissement]
    if label is not None:
        df = df[df["svp_label"] == label]
    if score_min is not None:
        df = df[df["svp_score"] >= score_min]
    if score_max is not None:
        df = df[df["svp_score"] <= score_max]
    if has_commerce is not None:
        df = df[df["has_commerce"] == has_commerce]

    valid_sort = ["svp_score", "nb_arbres", "nb_espaces_verts", "score_alim_brut", "score_vert", "score_acces_alim"]
    if sort_by not in valid_sort:
        raise HTTPException(400, detail=f"sort_by doit etre parmi : {valid_sort}")

    df = df.sort_values(sort_by, ascending=(order == "asc")).head(limit)
    cols_out = [
        "nom_voie",
        "arrondissement",
        "code_postal",
        "code_iris",
        "lon_centre",
        "lat_centre",
        "nb_espaces_verts",
        "nb_arbres",
        "score_alim_brut",
        "score_vert",
        "score_acces_alim",
        "svp_score",
        "svp_label",
        "has_commerce",
    ]
    records = [_to_record(row, cols_out) for _, row in df.iterrows()]
    return {"count": len(records), "rues": records}


@router.get("/rues/{nom_voie}", summary="Detail SVP d'une rue")
def svp_rue(
    nom_voie: str,
    code_postal: Optional[int] = Query(None),
):
    df = get_df()
    mask = df["nom_voie"].str.upper() == nom_voie.upper()
    if code_postal is not None:
        mask &= df["code_postal"].astype(str) == str(code_postal)

    results = df[mask]
    if results.empty:
        raise HTTPException(404, detail=f"Rue '{nom_voie}' introuvable")

    records = [_to_record(row, list(df.columns)) for _, row in results.iterrows()]
    return {"count": len(records), "results": records}


@router.get("/arrondissement/{arrondissement}", summary="SVP d'un arrondissement")
def svp_arrondissement(arrondissement: int):
    if not 1 <= arrondissement <= 20:
        raise HTTPException(400, detail="Arrondissement doit etre entre 1 et 20")
    df = get_df()
    subset = df[df["arrondissement"] == arrondissement]
    if subset.empty:
        raise HTTPException(404, detail=f"Aucune donnee pour l'arrondissement {arrondissement}")

    cols_out = [
        "nom_voie",
        "arrondissement",
        "code_postal",
        "code_iris",
        "lon_centre",
        "lat_centre",
        "nb_espaces_verts",
        "nb_arbres",
        "score_alim_brut",
        "score_vert",
        "score_acces_alim",
        "svp_score",
        "svp_label",
        "has_commerce",
    ]
    records = [_to_record(row, cols_out) for _, row in subset.iterrows()]
    return {
        "arrondissement": arrondissement,
        "nb_rues": len(records),
        "nb_rues_sans_commerce": int((subset["score_alim_brut"] == 0).sum()),
        "svp_median": round(float(subset["svp_score"].median()), 2),
        "svp_mean": round(float(subset["svp_score"].mean()), 2),
        "rues": records,
    }


@router.get("/geojson", summary="GeoJSON SVP pour la carte")
@router.get("/geojso", include_in_schema=False)
def svp_geojson(
    arrondissement: Optional[int] = Query(None),
    label: Optional[str] = Query(None),
    score_min: Optional[float] = Query(None),
    score_max: Optional[float] = Query(None),
    has_commerce: Optional[bool] = Query(None),
):
    if all(p is None for p in [arrondissement, label, score_min, score_max, has_commerce]):
        if GOLD_GEOJSON.exists():
            with open(GOLD_GEOJSON, encoding="utf-8") as f:
                return JSONResponse(content=json.load(f))

    df = get_df().copy()
    if arrondissement is not None:
        df = df[df["arrondissement"] == arrondissement]
    if label is not None:
        df = df[df["svp_label"] == label]
    if score_min is not None:
        df = df[df["svp_score"] >= score_min]
    if score_max is not None:
        df = df[df["svp_score"] <= score_max]
    if has_commerce is not None:
        df = df[df["has_commerce"] == has_commerce]

    prop_cols = [c for c in df.columns if c not in ("lon_centre", "lat_centre")]
    features = []
    for _, row in df.iterrows():
        props = _to_record(row, prop_cols)
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
    return JSONResponse(content={"type": "FeatureCollection", "count": len(features), "features": features})

"""
API FastAPI — SVP (Score de Verdure et Proximité)
==================================================
Router SVP à monter dans api/main.py.

Le SVP est calculé sur une grille de ~3 400 points espacés de 150m
couvrant Paris intramuros. Chaque point représente un micro-quartier.

Endpoints exposés :
    GET /svp/                        → healthcheck SVP
    GET /svp/stats                   → statistiques globales + par arrondissement
    GET /svp/points                  → liste des points avec score SVP (filtres)
    GET /svp/arrondissement/{n}      → tous les points d'un arrondissement
    GET /svp/geojson                 → FeatureCollection GeoJSON (pour la carte)

Intégration dans api/main.py :
    from api.svp_router import router as svp_router
    app.include_router(svp_router, prefix="/svp")

Données lues :
    data/gold/gold_SVP/svp_par_point.parquet
    data/gold/gold_SVP/svp_par_point.geojson
"""

from fastapi import APIRouter, Query, HTTPException
from fastapi.responses import JSONResponse
import pandas as pd
import json
from pathlib import Path
from typing import Optional

# ── Chemins ──────────────────────────────────────────────────────────────────

GOLD_PARQUET = Path("data/gold/gold_SVP/svp_par_point.parquet")
GOLD_GEOJSON = Path("data/gold/gold_SVP/svp_par_point.geojson")
ITR_PARQUET = Path("data/gold/gold_ITR/itr_par_rue.parquet")

# ── Router ────────────────────────────────────────────────────────────────────

router = APIRouter(tags=["SVP — Score de Verdure et Proximité"])

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
    return _df


def _to_record(row: pd.Series, cols: list) -> dict:
    """Convertit une ligne pandas en dict JSON-sérialisable."""
    rec = {}
    for col in cols:
        if col not in row.index:
            continue
        val = row[col]
        if hasattr(val, "item"):
            rec[col] = val.item()
        elif pd.isna(val):
            rec[col] = None
        elif isinstance(val, float):
            rec[col] = round(val, 4)
        else:
            rec[col] = val
    return rec


# ──────────────────────────────────────────────────────────────────────────────
# ENDPOINT 1 : Healthcheck
# ──────────────────────────────────────────────────────────────────────────────

@router.get("/", summary="Healthcheck SVP")
def svp_root():
    """Vérifie que les données gold SVP sont disponibles."""
    df = get_df()
    return {
        "indicateur" : "SVP — Score de Verdure et Proximité",
        "version"    : "1.0.0",
        "formule"    : "SVP = 0.60 × score_vert + 0.40 × score_acces_alim",
        "nb_points"  : len(df),
        "svp_min"    : round(float(df["svp_score"].min()), 2),
        "svp_max"    : round(float(df["svp_score"].max()), 2),
        "svp_median" : round(float(df["svp_score"].median()), 2),
        "svp_mean"   : round(float(df["svp_score"].mean()), 2),
    }


# ──────────────────────────────────────────────────────────────────────────────
# ENDPOINT 2 : Statistiques
# ──────────────────────────────────────────────────────────────────────────────

@router.get("/stats", summary="Statistiques SVP Paris")
def svp_stats():
    """Statistiques globales SVP + distribution par arrondissement."""
    df = get_df()
    LABELS_ORDER = ["Très faible", "Faible", "Modéré", "Bon", "Excellent"]

    dist_label = (
        df["svp_label"]
        .value_counts()
        .reindex(LABELS_ORDER)
        .fillna(0)
        .astype(int)
        .to_dict()
    )

    by_iris = (
        df.groupby("code_iris")
        .agg(
            nb_points            = ("svp_score", "count"),
            svp_score_median     = ("svp_score", "median"),
            svp_score_mean       = ("svp_score", "mean"),
            nb_espaces_verts_moy = ("nb_espaces_verts", "mean"),
            nb_arbres_moy        = ("nb_arbres", "mean"),
            score_alim_moy       = ("score_alim_brut", "mean"),
        )
        .round(2)
        .reset_index()
        .sort_values("svp_score_median", ascending=False)
        .head(10)  # Top 10 IRIS
        .to_dict(orient="records")
    )

    return {
        "nb_points_total"    : len(df),
        "resolution_m"       : 150,
        "svp_score_min"      : round(float(df["svp_score"].min()), 2),
        "svp_score_max"      : round(float(df["svp_score"].max()), 2),
        "svp_score_median"   : round(float(df["svp_score"].median()), 2),
        "svp_score_mean"     : round(float(df["svp_score"].mean()), 2),
        "distribution_label" : dist_label,
        "par_iris"           : by_iris,
        "parametres"         : {
            "rayon_verdure_m"  : 200,
            "rayon_commerce_m" : 500,
            "poids_score_vert" : 0.60,
            "poids_score_alim" : 0.40,
        },
    }


# ──────────────────────────────────────────────────────────────────────────────
# ENDPOINT 3 : Liste des points (avec filtres)
# ──────────────────────────────────────────────────────────────────────────────

@router.get("/points", summary="Liste des points SVP")
def svp_list_points(
    arrondissement : Optional[int]   = Query(None, description="Filtrer par arrondissement (1-20)"),
    label          : Optional[str]   = Query(None, description="Niveau SVP : 'Très faible','Faible','Modéré','Bon','Excellent'"),
    score_min      : Optional[float] = Query(None, description="Score SVP minimum (0-100)"),
    score_max      : Optional[float] = Query(None, description="Score SVP maximum (0-100)"),
    sort_by        : str             = Query("svp_score", description="Tri : svp_score, nb_arbres, nb_espaces_verts, score_alim_brut"),
    order          : str             = Query("desc", description="asc ou desc"),
    limit          : int             = Query(5000, ge=1, le=5000),
):
    """
    Liste les points de la grille SVP avec filtres.

    Exemples :
    - `/svp/points?arrondissement=12` → points du 12e
    - `/svp/points?label=Excellent&limit=50` → 50 points les plus verts
    - `/svp/points?score_min=70` → points avec bon accès vert + alimentaire
    """
    df = get_df().copy()

    if arrondissement is not None:
        df = df[df["arrondissement"] == arrondissement]
    if label is not None:
        df = df[df["svp_label"] == label]
    if score_min is not None:
        df = df[df["svp_score"] >= score_min]
    if score_max is not None:
        df = df[df["svp_score"] <= score_max]

    valid_sort = ["svp_score", "nb_arbres", "nb_espaces_verts",
                  "score_alim_brut", "score_vert", "score_acces_alim"]
    if sort_by not in valid_sort:
        raise HTTPException(400, detail=f"sort_by doit être parmi : {valid_sort}")

    df = df.sort_values(sort_by, ascending=(order == "asc")).head(limit)

    cols_out = ["arrondissement", "code_postal", "code_iris",
                "lon", "lat",
                "nb_espaces_verts", "nb_arbres", "score_alim_brut",
                "score_vert", "score_acces_alim", "svp_score", "svp_label"]

    records = [_to_record(row, cols_out) for _, row in df.iterrows()]

    return {
        "count"   : len(records),
        "filtres" : {"arrondissement": arrondissement, "label": label,
                     "score_min": score_min, "score_max": score_max},
        "points"  : records,
    }


# ──────────────────────────────────────────────────────────────────────────────
# ENDPOINT 4 : Points d'un arrondissement
# ──────────────────────────────────────────────────────────────────────────────

@router.get("/arrondissement/{arrondissement}", summary="SVP d'un arrondissement")
def svp_arrondissement(arrondissement: int):
    """
    Retourne tous les points SVP d'un arrondissement donné.
    Utile pour afficher la heatmap d'un arrondissement précis.

    Exemple : `/svp/arrondissement/11`
    """
    if not 1 <= arrondissement <= 20:
        raise HTTPException(400, detail="Arrondissement doit être entre 1 et 20")

    df = get_df()
    subset = df[df["arrondissement"] == arrondissement]

    if subset.empty:
        raise HTTPException(404, detail=f"Aucune donnée pour l'arrondissement {arrondissement}")

    cols_out = ["arrondissement", "code_postal", "code_iris",
                "lon", "lat",
                "nb_espaces_verts", "nb_arbres", "score_alim_brut",
                "score_vert", "score_acces_alim", "svp_score", "svp_label"]

    records = [_to_record(row, cols_out) for _, row in subset.iterrows()]

    return {
        "arrondissement" : arrondissement,
        "nb_points"      : len(records),
        "svp_median"     : round(float(subset["svp_score"].median()), 2),
        "svp_mean"       : round(float(subset["svp_score"].mean()), 2),
        "points"         : records,
    }


# ──────────────────────────────────────────────────────────────────────────────
# ENDPOINT 5 : Liste des rues (avec scores SVP agrégés)
# ──────────────────────────────────────────────────────────────────────────────

@router.get("/rues", summary="Liste des rues avec score SVP")
def svp_list_rues(
    arrondissement : Optional[int]   = Query(None, description="Filtrer par arrondissement (1-20)"),
    label          : Optional[str]   = Query(None, description="Niveau SVP : 'Très faible','Faible','Modéré','Bon','Excellent'"),
    score_min      : Optional[float] = Query(None, description="Score SVP minimum (0-100)"),
    score_max      : Optional[float] = Query(None, description="Score SVP maximum (0-100)"),
    sort_by        : str             = Query("svp_score", description="Tri : svp_score, nb_points, nb_arbres_moy"),
    order          : str             = Query("desc", description="asc ou desc"),
    limit          : int             = Query(100, ge=1, le=2500, description="Nombre max de résultats"),
):
    """
    Liste les rues parisiennes avec leur score SVP agrégé par IRIS.

    Le score SVP est calculé comme la moyenne des points dans l'IRIS de la rue.
    """
    # Charger données SVP
    if not GOLD_PARQUET.exists():
        raise RuntimeError(f"Fichier SVP introuvable : {GOLD_PARQUET}")
    df_svp = pd.read_parquet(GOLD_PARQUET)

    # Agréger SVP par code_iris
    svp_agg = (
        df_svp.groupby("code_iris")
        .agg(
            svp_score         = ("svp_score", "mean"),
            nb_points         = ("svp_score", "count"),
            nb_arbres_moy     = ("nb_arbres", "mean"),
            nb_espaces_verts_moy = ("nb_espaces_verts", "mean"),
            score_alim_moy    = ("score_acces_alim", "mean"),
        )
        .round(2)
        .reset_index()
    )

    # Charger données ITR
    if not ITR_PARQUET.exists():
        raise RuntimeError(f"Fichier ITR introuvable : {ITR_PARQUET}")
    df_itr = pd.read_parquet(ITR_PARQUET)

    # Joindre sur code_iris
    df = df_itr.merge(svp_agg, on="code_iris", how="left")

    # Ajouter label SVP
    def get_label(score):
        if score >= 80: return "Excellent"
        if score >= 60: return "Bon"
        if score >= 40: return "Modéré"
        if score >= 20: return "Faible"
        return "Très faible"

    df["svp_label"] = df["svp_score"].apply(get_label)

    # Filtres
    if arrondissement is not None:
        df = df[df["arrondissement"] == arrondissement]
    if label is not None:
        df = df[df["svp_label"] == label]
    if score_min is not None:
        df = df[df["svp_score"] >= score_min]
    if score_max is not None:
        df = df[df["svp_score"] <= score_max]

    # Tri
    valid_sort = ["svp_score", "nb_points", "nb_arbres_moy", "nb_espaces_verts_moy"]
    if sort_by not in valid_sort:
        raise HTTPException(400, detail=f"sort_by doit être parmi : {valid_sort}")

    ascending = order == "asc"
    df = df.sort_values(sort_by, ascending=ascending).head(limit)

    # Colonnes de sortie
    cols_out = [
        "nom_voie", "code_postal", "arrondissement", "code_iris",
        "lon_centre", "lat_centre",
        "nb_points", "nb_arbres_moy", "nb_espaces_verts_moy", "score_alim_moy",
        "svp_score", "svp_label",
    ]
    df = df[[c for c in cols_out if c in df.columns]]

    records = [_to_record(row, cols_out) for _, row in df.iterrows()]

    return {
        "count"   : len(records),
        "filtres" : {
            "arrondissement": arrondissement,
            "label"         : label,
            "score_min"     : score_min,
            "score_max"     : score_max,
        },
        "rues"    : records,
    }


# ──────────────────────────────────────────────────────────────────────────────
# ENDPOINT 6 : Détail d'une rue SVP
# ──────────────────────────────────────────────────────────────────────────────

@router.get("/rues/{nom_voie}", summary="Détail SVP d'une rue")
def svp_get_rue(
    nom_voie     : str,
    code_postal  : Optional[int] = Query(None, description="Code postal pour lever les ambiguïtés"),
):
    """
    Retourne le détail SVP d'une rue (score agrégé par IRIS).
    """
    # Même logique que /rues mais pour une rue spécifique
    if not GOLD_PARQUET.exists():
        raise RuntimeError(f"Fichier SVP introuvable : {GOLD_PARQUET}")
    df_svp = pd.read_parquet(GOLD_PARQUET)

    svp_agg = (
        df_svp.groupby("code_iris")
        .agg(
            svp_score         = ("svp_score", "mean"),
            nb_points         = ("svp_score", "count"),
            nb_arbres_moy     = ("nb_arbres", "mean"),
            nb_espaces_verts_moy = ("nb_espaces_verts", "mean"),
            score_alim_moy    = ("score_acces_alim", "mean"),
        )
        .round(2)
        .reset_index()
    )

    if not ITR_PARQUET.exists():
        raise RuntimeError(f"Fichier ITR introuvable : {ITR_PARQUET}")
    df_itr = pd.read_parquet(ITR_PARQUET)

    df = df_itr.merge(svp_agg, on="code_iris", how="left")

    def get_label(score):
        if pd.isna(score): return None
        if score >= 80: return "Excellent"
        if score >= 60: return "Bon"
        if score >= 40: return "Modéré"
        if score >= 20: return "Faible"
        return "Très faible"

    df["svp_label"] = df["svp_score"].apply(get_label)

    mask = df["nom_voie"].str.upper() == nom_voie.upper()
    if code_postal is not None:
        mask &= df["code_postal"] == code_postal

    results = df[mask]

    if results.empty:
        raise HTTPException(
            status_code=404,
            detail=f"Rue '{nom_voie}' introuvable. "
                   f"Vérifiez le nom et/ou précisez le code_postal."
        )

    records = []
    for _, row in results.iterrows():
        record = {}
        for col in df.columns:
            val = row[col]
            if pd.isna(val):
                record[col] = None
            elif isinstance(val, float):
                record[col] = round(val, 4)
            else:
                record[col] = val
        records.append(record)

    return {
        "count"   : len(records),
        "results" : records,
    }


# ──────────────────────────────────────────────────────────────────────────────
# ENDPOINT 7 : GeoJSON rues SVP
# ──────────────────────────────────────────────────────────────────────────────

@router.get("/geojson", summary="GeoJSON rues SVP")
def svp_geojson_rues(
    arrondissement : Optional[int]   = Query(None),
    label          : Optional[str]   = Query(None),
    score_min      : Optional[float] = Query(None),
    score_max      : Optional[float] = Query(None),
):
    """
    GeoJSON des rues avec scores SVP (points centraux des rues).
    """
    # Même logique que /rues mais retourne GeoJSON
    if not GOLD_PARQUET.exists():
        raise RuntimeError(f"Fichier SVP introuvable : {GOLD_PARQUET}")
    df_svp = pd.read_parquet(GOLD_PARQUET)

    svp_agg = (
        df_svp.groupby("code_iris")
        .agg(
            svp_score         = ("svp_score", "mean"),
            nb_points         = ("svp_score", "count"),
            nb_arbres_moy     = ("nb_arbres", "mean"),
            nb_espaces_verts_moy = ("nb_espaces_verts", "mean"),
            score_alim_moy    = ("score_acces_alim", "mean"),
        )
        .round(2)
        .reset_index()
    )

    if not ITR_PARQUET.exists():
        raise RuntimeError(f"Fichier ITR introuvable : {ITR_PARQUET}")
    df_itr = pd.read_parquet(ITR_PARQUET)

    df = df_itr.merge(svp_agg, on="code_iris", how="left")

    def get_label(score):
        if pd.isna(score): return None
        if score >= 80: return "Excellent"
        if score >= 60: return "Bon"
        if score >= 40: return "Modéré"
        if score >= 20: return "Faible"
        return "Très faible"

    df["svp_label"] = df["svp_score"].apply(get_label)

    if arrondissement is not None:
        df = df[df["arrondissement"] == arrondissement]
    if label is not None:
        df = df[df["svp_label"] == label]
    if score_min is not None:
        df = df[df["svp_score"] >= score_min]
    if score_max is not None:
        df = df[df["svp_score"] <= score_max]

    features = []
    prop_cols = [c for c in df.columns if c not in ("lon_centre", "lat_centre")]

    for _, row in df.iterrows():
        props = {}
        for col in prop_cols:
            val = row[col]
            if pd.isna(val):
                props[col] = None
            elif isinstance(val, float):
                props[col] = round(val, 4)
            else:
                props[col] = val

        features.append({
            "type"      : "Feature",
            "geometry"  : {
                "type"        : "Point",
                "coordinates" : [
                    round(float(row["lon_centre"]), 6),
                    round(float(row["lat_centre"]), 6),
                ],
            },
            "properties": props,
        })

    return JSONResponse(content={
        "type"    : "FeatureCollection",
        "count"   : len(features),
        "features": features,
    })


# ──────────────────────────────────────────────────────────────────────────────
# ENDPOINT 5 : GeoJSON pour la carte
# ──────────────────────────────────────────────────────────────────────────────

@router.get("/geojson", summary="GeoJSON SVP pour la carte")
def svp_geojson(
    arrondissement : Optional[int]   = Query(None),
    label          : Optional[str]   = Query(None),
    score_min      : Optional[float] = Query(None),
    score_max      : Optional[float] = Query(None),
):
    """
    GeoJSON FeatureCollection prêt pour MapLibre / Deck.gl.
    Sans filtre → sert le fichier pré-généré directement (optimal).
    """
    if all(p is None for p in [arrondissement, label, score_min, score_max]):
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

    prop_cols = [c for c in df.columns if c not in ("lon", "lat")]
    features = []
    for _, row in df.iterrows():
        props = _to_record(row, prop_cols)
        features.append({
            "type"      : "Feature",
            "geometry"  : {"type": "Point",
                           "coordinates": [round(float(row["lon"]), 6),
                                           round(float(row["lat"]), 6)]},
            "properties": props,
        })

    return JSONResponse(content={
        "type": "FeatureCollection", "count": len(features), "features": features
    })

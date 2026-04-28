"""
API FastAPI — ITR Paris
========================
Expose les données Gold (itr_par_rue.parquet) via 4 endpoints REST.

Lancement :
    pip install fastapi uvicorn
    uvicorn api.main:app --reload --port 8000

Endpoints :
    GET /               → healthcheck
    GET /stats          → statistiques globales Paris
    GET /rues           → liste des rues avec score ITR (filtres disponibles)
    GET /rues/{nom}     → détail d'une rue précise
    GET /geojson        → FeatureCollection GeoJSON complet (pour la carte)
"""

from fastapi import FastAPI, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, RedirectResponse
import pandas as pd
import json
from pathlib import Path
from typing import Optional
<<<<<<< Updated upstream
import os
=======

import pandas as pd
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, RedirectResponse
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError

# ──────────────────────────────────────────────
# CONFIG
# ──────────────────────────────────────────────

GOLD_GEOJSON = Path("data/gold/gold_ITR/itr_par_rue.geojson")

app = FastAPI(
    title="ITR Paris — Indice de Tension Résidentielle",
    description="API exposant l'indicateur de tension résidentielle par rue parisienne.",
    version="1.0.0",
)

# CORS ouvert (pour Kepler.gl, Deck.gl, ou tout front qui consomme l'API)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET"],
    allow_headers=["*"],
)

# Config db
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL manquante")

engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    pool_recycle=300,
    future=True,
)

# ──────────────────────────────────────────────
# CONNECTIVITE BASE DE DONNEES
# ──────────────────────────────────────────────

def is_db_ready() -> bool:
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return True
    except SQLAlchemyError:
        return False
    

# ──────────────────────────────────────────────
# CHARGEMENT DATA SQL
# ──────────────────────────────────────────────

def get_df_sql() -> pd.DataFrame:
    query = """
    SELECT
        nom_voie, code_postal, arrondissement,
        lon_centre, lat_centre,
        prix_m2_median, revenu_median_uc, nb_logements_sociaux,
        nb_transactions, itr_score, itr_label
    FROM itr_par_rue
    """
    return pd.read_sql(query, engine)


# ──────────────────────────────────────────────
# ENDPOINT 1 : redirection docs + healthcheck
# ──────────────────────────────────────────────

<<<<<<< Updated upstream
<<<<<<< Updated upstream
@app.get("/", tags=["Healthcheck"])
def root():
    return RedirectResponse(url="/docs")
=======
@app.get("/", include_in_schema=False)
def root():
=======
@app.get("/", include_in_schema=False)
def root():
>>>>>>> Stashed changes
  return RedirectResponse(url="/docs")


@app.get("/health", tags=["Healthcheck"])
def health():
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
>>>>>>> Stashed changes


@app.get("/health", tags=["Healthcheck"])
def health():
    db_ok = is_db_ready()
    if not db_ok:
        return {
            "status": "ok",
            "db_status": "down",
            "version": "1.0.0",
        }

    df = get_df_sql()
    return {
        "status": "ok",
        "db_status": "ok",
        "version": "1.0.0",
        "nb_rues": len(df),
        "score_min": round(df["itr_score"].min(), 2),
        "score_max": round(df["itr_score"].max(), 2),
        "score_median": round(df["itr_score"].median(), 2),
    }
    

# ──────────────────────────────────────────────
# ENDPOINT 2 : stats globales
# ──────────────────────────────────────────────

@app.get("/stats", tags=["Statistiques"])
def stats():
    """
    Statistiques globales sur l'ITR Paris.
    Retourne la distribution par niveau de tension et par arrondissement.
    """
    df = get_df_sql()

    # Distribution par label
    dist_label = (
        df["itr_label"]
        .value_counts()
        .reindex(["Très accessible", "Accessible", "Modéré", "Tendu", "Très tendu"])
        .fillna(0)
        .astype(int)
        .to_dict()
    )

    # Stats par arrondissement
    by_arrdt = (
        df.groupby("arrondissement")
        .agg(
            nb_rues          = ("itr_score", "count"),
            itr_score_median = ("itr_score", "median"),
            prix_m2_median   = ("prix_m2_median", "median"),
            revenu_median    = ("revenu_median_uc", "median"),
        )
        .round(2)
        .reset_index()
        .sort_values("itr_score_median", ascending=False)
        .to_dict(orient="records")
    )

    return {
        "nb_rues_total"      : len(df),
        "itr_score_min"      : round(df["itr_score"].min(), 2),
        "itr_score_max"      : round(df["itr_score"].max(), 2),
        "itr_score_median"   : round(df["itr_score"].median(), 2),
        "itr_score_mean"     : round(df["itr_score"].mean(), 2),
        "distribution_label" : dist_label,
        "par_arrondissement" : by_arrdt,
    }


# ──────────────────────────────────────────────
# ENDPOINT 3 : liste des rues (avec filtres)
# ──────────────────────────────────────────────

@app.get("/rues", tags=["Rues"])
def list_rues(
    arrondissement : Optional[int]   = Query(None, description="Filtrer par arrondissement (1-20)"),
    label          : Optional[str]   = Query(None, description="Filtrer par niveau : 'Très accessible','Accessible','Modéré','Tendu','Très tendu'"),
    score_min      : Optional[float] = Query(None, description="Score ITR minimum (0-100)"),
    score_max      : Optional[float] = Query(None, description="Score ITR maximum (0-100)"),
    sort_by        : str             = Query("itr_score", description="Colonne de tri : itr_score, prix_m2_median, nb_transactions"),
    order          : str             = Query("desc", description="Ordre : asc ou desc"),
    limit          : int             = Query(100, ge=1, le=2500, description="Nombre max de résultats"),
):
    """
    Liste les rues parisiennes avec leur score ITR.

    Exemples :
    - `/rues?arrondissement=7` → rues du 7e arrondissement
    - `/rues?label=Très tendu&limit=20` → 20 rues les plus tendues
    - `/rues?score_min=80&sort_by=prix_m2_median` → rues très tendues triées par prix
    """
    df = get_df_sql().copy()

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

    ascending = order == "asc"
    df = df.sort_values(sort_by, ascending=ascending).head(limit)

    cols_out = [
        "nom_voie", "code_postal", "arrondissement",
        "lon_centre", "lat_centre",
        "prix_m2_median", "revenu_median_uc", "nb_logements_sociaux",
        "nb_transactions", "itr_score", "itr_label",
    ]
    df = df[[c for c in cols_out if c in df.columns]]

    return {
        "count"   : len(df),
        "filtres" : {
            "arrondissement": arrondissement,
            "label"         : label,
            "score_min"     : score_min,
            "score_max"     : score_max,
        },
        "rues"    : df.to_dict(orient="records"),
    }


# ──────────────────────────────────────────────
# ENDPOINT 4 : détail d'une rue
# ──────────────────────────────────────────────

@app.get("/rues/{nom_voie}", tags=["Rues"])
def get_rue(
    nom_voie     : str,
    code_postal  : Optional[int] = Query(None, description="Code postal pour lever les ambiguïtés (ex: 75007)"),
):
    """
    Retourne le détail complet d'une rue avec toutes les composantes ITR.

    Exemple : `/rues/RUE DU BAC?code_postal=75007`
    """
    df = get_df_sql()

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

    # Retourner toutes les colonnes (y compris les composantes intermédiaires)
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


# ──────────────────────────────────────────────
# ENDPOINT 5 : GeoJSON complet
# ──────────────────────────────────────────────

@app.get("/geojson", tags=["Carte"])
def geojson(
    arrondissement : Optional[int]   = Query(None, description="Filtrer par arrondissement"),
    label          : Optional[str]   = Query(None, description="Filtrer par niveau de tension"),
    score_min      : Optional[float] = Query(None, description="Score ITR minimum"),
    score_max      : Optional[float] = Query(None, description="Score ITR maximum"),
):
    """
    Retourne un GeoJSON FeatureCollection prêt pour Kepler.gl / Deck.gl / Leaflet.

    Le GeoJSON complet pèse ~800KB. Utilisez les filtres pour alléger si besoin.

    Exemple : `/geojson?arrondissement=7` → GeoJSON du 7e uniquement
    """
    # Si pas de filtre → servir le fichier pre-généré directement (+ rapide)
    if all(p is None for p in [arrondissement, label, score_min, score_max]):
        if GOLD_GEOJSON.exists():
            with open(GOLD_GEOJSON, encoding="utf-8") as f:
                return JSONResponse(content=json.load(f))

    # Sinon filtrer dynamiquement
    df = get_df_sql().copy()
    if arrondissement is not None:
        df = df[df["arrondissement"] == arrondissement]
    if label is not None:
        df = df[df["itr_label"] == label]
    if score_min is not None:
        df = df[df["itr_score"] >= score_min]
    if score_max is not None:
        df = df[df["itr_score"] <= score_max]

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
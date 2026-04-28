"""
run_pipeline.py
===============
Orchestrateur global — Urban Data Explorer.
Chaque indicateur vit dans son propre sous-dossier.

Usage :
    python run_pipeline.py                             # tous les indicateurs, tout le pipeline
    python run_pipeline.py --indicateur ITR            # ITR uniquement, tout le pipeline
    python run_pipeline.py --bronze                    # bronze de tous les indicateurs
    python run_pipeline.py --bronze --indicateur ITR   # bronze ITR uniquement
    python run_pipeline.py --silver --indicateur ITR   # silver ITR uniquement
    python run_pipeline.py --gold   --indicateur ITR   # gold ITR uniquement
"""

import sys
import time
from pathlib import Path

from dotenv import load_dotenv
<<<<<<< Updated upstream
=======

ROOT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT_DIR))
load_dotenv(dotenv_path=ROOT_DIR / ".env")
>>>>>>> Stashed changes

ROOT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT_DIR))
load_dotenv(dotenv_path=ROOT_DIR / ".env")


# ──────────────────────────────────────────────────────────────
# REGISTRE DES INDICATEURS
# Chaque équipe ajoute son indicateur ici avec ses 3 fonctions
# ──────────────────────────────────────────────────────────────

def get_indicateurs():
    return {
        "ITR": {
            "label"  : "Indice de Tension Résidentielle",
            "bronze" : _bronze_itr,
            "silver" : _silver_itr,
            "gold"   : _gold_itr,
        },
        # Exemple pour une autre équipe :
        # "AIR": {
        #     "label"  : "Qualité de l'air",
        #     "bronze" : _bronze_air,
        #     "silver" : _silver_air,
        #     "gold"   : _gold_air,
        # },
    }


# ──────────────────────────────────────────────────────────────
# ITR — Bronze
# Lit depuis  : data/raw/raw_ITR/
# Ecrit dans  : data/bronze/bronze_ITR/
# ──────────────────────────────────────────────────────────────

def _bronze_itr():
    from src.bronze.bronze_ITR.dvf_bronze               import run as dvf
    from src.bronze.bronze_ITR.filosofi_bronze          import run as filosofi
    from src.bronze.bronze_ITR.logements_sociaux_bronze import run as logsoc
    from src.bronze.bronze_ITR.iris_geo_bronze          import run as iris
    dvf();      print()
    filosofi(); print()
    logsoc();   print()
    iris()


# ──────────────────────────────────────────────────────────────
# ITR — Silver
# Lit depuis  : data/bronze/bronze_ITR/
# Ecrit dans  : data/silver/silver_ITR/
# Ordre obligatoire : dvf → logsoc → rue_enrichie
# ──────────────────────────────────────────────────────────────

def _silver_itr():
    from src.silver.silver_ITR.dvf_silver               import run as dvf
    from src.silver.silver_ITR.logements_sociaux_silver import run as logsoc
    from src.silver.silver_ITR.rue_enrichie_silver      import run as rue
    dvf();    print()
    logsoc(); print()
    rue()


# ──────────────────────────────────────────────────────────────
# ITR — Gold
# Lit depuis  : data/silver/silver_ITR/rue_enrichie.parquet
# Ecrit dans  : data/gold/gold_ITR/
# ──────────────────────────────────────────────────────────────

def _gold_itr():
    from src.gold.gold_ITR.itr_gold import run as itr
    from src.gold.gold_ITR.load_gold_to_db import run as load_gold_to_db
    itr()
    load_gold_to_db()


<<<<<<< Updated upstream
# ──────────────────────────────────────────────────────────────
# ORCHESTRATEUR
# ──────────────────────────────────────────────────────────────
=======
def _bronze_svp():
  from src.bronze.bronze_SVP.espaces_verts_bronze import run as ev
  from src.bronze.bronze_SVP.arbres_bronze import run as arb
  from src.bronze.bronze_SVP.commerces_alim_bronze import run as com
  ev(); print()
  arb(); print()
  com()


def _silver_svp():
  from src.silver.silver_SVP.verdure_silver import run as verdure
  from src.silver.silver_SVP.commerces_silver import run as com
  verdure(); print()
  com()


def _gold_svp():
  from src.gold.gold_SVP.svp_gold import run as svp
  from src.gold.gold_SVP.load_gold_to_db import run as load_gold_to_db
  from src.gold.gold_SVP.load_gold_to_mongo import run as load_gold_to_mongo
  svp()
  load_gold_to_db()
  load_gold_to_mongo()


def _bronze_iaml():
  from src.bronze.bronze_IAML.transports_bronze import run as transports
  from src.bronze.bronze_IAML.velib_bronze import run as velib
  transports(); print()
  velib()


def _silver_iaml():
  from src.silver.silver_IAML.rue_accessibilite_silver import run as rue_access
  rue_access()


def _gold_iaml():
  from src.gold.gold_IAML.iaml_gold import run as iaml
  from src.gold.gold_IAML.load_gold_to_db import run as load_gold_to_db
  from src.gold.gold_IAML.load_gold_to_mongo import run as load_gold_to_mongo
  iaml()
  load_gold_to_db()
  load_gold_to_mongo()

>>>>>>> Stashed changes

def run_couche(couche: str, indicateurs: dict):
    print("\n" + "=" * 50)
    print(f"  COUCHE {couche.upper()}")
    print("=" * 50)
    for nom, indic in indicateurs.items():
        print(f"\n  ── {nom} : {indic['label']} ──")
        indic[couche]()


if __name__ == "__main__":
    args = sys.argv[1:]
    t0   = time.time()

    tous = get_indicateurs()

    if "--indicateur" in args:
        idx = args.index("--indicateur")
        nom = args[idx + 1].upper()
        if nom not in tous:
            print(f"Indicateur '{nom}' inconnu. Disponibles : {list(tous.keys())}")
            sys.exit(1)
        cibles = {nom: tous[nom]}
    else:
        cibles = tous

    if "--bronze" in args:
        run_couche("bronze", cibles)
    elif "--silver" in args:
        run_couche("silver", cibles)
    elif "--gold" in args:
        run_couche("gold", cibles)
    else:
        run_couche("bronze", cibles)
        run_couche("silver", cibles)
        run_couche("gold",   cibles)

    elapsed = time.time() - t0
    print(f"\n Pipeline termine en {elapsed:.1f}s")
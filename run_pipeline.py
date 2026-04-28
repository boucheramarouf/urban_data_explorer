"""
run_pipeline.py
===============
Orchestrateur global — Urban Data Explorer.
Chaque indicateur vit dans son propre sous-dossier.

Usage :
    python run_pipeline.py
    python run_pipeline.py --indicateur ITR
    python run_pipeline.py --indicateur SVP
    python run_pipeline.py --indicateur IAML
    python run_pipeline.py --bronze
    python run_pipeline.py --silver
    python run_pipeline.py --gold
"""

import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))


def get_indicateurs():
  return {
    "ITR": {
      "label": "Indice de Tension Résidentielle",
      "bronze": _bronze_itr,
      "silver": _silver_itr,
      "gold": _gold_itr,
    },
    "SVP": {
      "label": "Score de Verdure et Proximité",
      "bronze": _bronze_svp,
      "silver": _silver_svp,
      "gold": _gold_svp,
    },
    "IAML": {
      "label": "Indice d'Accessibilité Multimodale au Logement",
      "bronze": _bronze_iaml,
      "silver": _silver_iaml,
      "gold": _gold_iaml,
    },
  }


def _bronze_itr():
  from src.bronze.bronze_ITR.dvf_bronze import run as dvf
  from src.bronze.bronze_ITR.filosofi_bronze import run as filosofi
  from src.bronze.bronze_ITR.logements_sociaux_bronze import run as logsoc
  from src.bronze.bronze_ITR.iris_geo_bronze import run as iris
  dvf(); print()
  filosofi(); print()
  logsoc(); print()
  iris()


def _silver_itr():
  from src.silver.silver_ITR.dvf_silver import run as dvf
  from src.silver.silver_ITR.logements_sociaux_silver import run as logsoc
  from src.silver.silver_ITR.rue_enrichie_silver import run as rue
  dvf(); print()
  logsoc(); print()
  rue()


def _gold_itr():
  from src.gold.gold_ITR.itr_gold import run as itr
  from src.gold.gold_ITR.load_gold_to_db import run as load_gold_to_db
  from src.gold.gold_ITR.load_gold_to_mongo import run as load_gold_to_mongo
  itr()
  load_gold_to_db()
  load_gold_to_mongo()


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
  svp()


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


def run_couche(couche: str, indicateurs: dict):
  print("\n" + "=" * 50)
  print(f"  COUCHE {couche.upper()}")
  print("=" * 50)
  for nom, indic in indicateurs.items():
    print(f"\n  ── {nom} : {indic['label']} ──")
    indic[couche]()


if __name__ == "__main__":
  args = sys.argv[1:]
  t0 = time.time()
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
    run_couche("gold", cibles)

  elapsed = time.time() - t0
  print(f"\nPipeline termine en {elapsed:.1f}s")

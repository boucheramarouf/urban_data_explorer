"""
run_pipeline.py
===============
Orchestrateur du pipeline ITR Paris.
Lance les couches dans l'ordre : Bronze → Silver → Gold.

Usage :
    python run_pipeline.py              # tout le pipeline
    python run_pipeline.py --bronze     # bronze uniquement
    python run_pipeline.py --silver     # silver uniquement
    python run_pipeline.py --gold       # gold uniquement
"""

import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))


def run_bronze():
    print("\n" + "=" * 50)
    print("  COUCHE BRONZE")
    print("=" * 50)
    from src.bronze.dvf_bronze               import run as dvf
    from src.bronze.filosofi_bronze          import run as filosofi
    from src.bronze.logements_sociaux_bronze import run as logsoc
    from src.bronze.iris_geo_bronze          import run as iris
    dvf();      print()
    filosofi(); print()
    logsoc();   print()
    iris()


def run_silver():
    print("\n" + "=" * 50)
    print("  COUCHE SILVER")
    print("=" * 50)
    from src.silver.dvf_silver               import run as dvf
    from src.silver.logements_sociaux_silver import run as logsoc
    from src.silver.rue_enrichie_silver      import run as rue
    dvf();    print()
    logsoc(); print()
    rue()


def run_gold():
    print("\n" + "=" * 50)
    print("  COUCHE GOLD")
    print("=" * 50)
    from src.gold.itr_gold import run as itr
    itr()


if __name__ == "__main__":
    args = sys.argv[1:]
    t0 = time.time()

    if "--bronze" in args:
        run_bronze()
    elif "--silver" in args:
        run_silver()
    elif "--gold" in args:
        run_gold()
    else:
        run_bronze()
        run_silver()
        run_gold()

    elapsed = time.time() - t0
    print(f"\n✓ Pipeline terminé en {elapsed:.1f}s")
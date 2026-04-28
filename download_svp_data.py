"""
download_svp_data.py
=====================
Script de téléchargement des données brutes pour l'indicateur SVP.
À exécuter UNE SEULE FOIS avant de lancer le pipeline.

Usage :
    python download_svp_data.py              # télécharge espaces verts + arbres
    python download_svp_data.py --only ev    # espaces verts seulement
    python download_svp_data.py --only arbres # arbres seulement

Sorties automatiques :
    data/raw/raw_SVP/espaces_verts.geojson   (~5 MB)
    data/raw/raw_SVP/arbres.geojson           (~60 MB — peut prendre 2-3 min)

Fichier à placer manuellement :
    data/raw/raw_SVP/shops_point.csv
    → Télécharger depuis :
      https://www.data.gouv.fr/fr/datasets/
      localisations-des-magasins-dans-openstreetmap/
    → Ce fichier est ensuite traité automatiquement par le pipeline Bronze SVP.

Ordre complet pour lancer le projet :
    1. Télécharger shops_point.csv manuellement (voir ci-dessus)
    2. python download_svp_data.py
    3. python run_pipeline.py --indicateur SVP
    4. uvicorn api.main:app --reload --port 8000
"""

import sys
import time
import argparse
import requests
from pathlib import Path

# ── Configuration ─────────────────────────────────────────────────────────────

RAW_DIR = Path("data/raw/raw_SVP")
RAW_DIR.mkdir(parents=True, exist_ok=True)


# ── Utilitaires ───────────────────────────────────────────────────────────────

def _progress(downloaded: int, total: int = 0) -> None:
    if total:
        pct = downloaded / total * 100
        bar = "█" * int(pct / 5) + "░" * (20 - int(pct / 5))
        print(f"\r  [{bar}] {pct:5.1f}%  ({downloaded / 1024 / 1024:.1f} MB)", end="", flush=True)
    else:
        print(f"\r  Téléchargé : {downloaded / 1024 / 1024:.1f} MB", end="", flush=True)


def _download(url: str, dest: Path, label: str, timeout: int = 400) -> None:
    """Télécharge une URL en streaming avec barre de progression."""
    print(f"\n  [{label}]")
    print(f"  URL : {url}")

    if dest.exists():
        print(f"  ✓ Déjà présent ({dest.stat().st_size / 1024 / 1024:.1f} MB) — saut.")
        return

    t0 = time.time()
    resp = requests.get(url, timeout=timeout, stream=True, allow_redirects=True)
    resp.raise_for_status()

    total = int(resp.headers.get("content-length", 0))
    downloaded = 0
    chunks = []

    for chunk in resp.iter_content(chunk_size=256 * 1024):
        chunks.append(chunk)
        downloaded += len(chunk)
        _progress(downloaded, total)

    dest.write_bytes(b"".join(chunks))
    elapsed = time.time() - t0
    print(f"\n  ✓ {dest.stat().st_size / 1024 / 1024:.1f} MB en {elapsed:.0f}s → {dest}")


# ── Téléchargements ───────────────────────────────────────────────────────────

def download_espaces_verts() -> None:
    _download(
        url=(
            "https://opendata.paris.fr/api/explore/v2.1/catalog/datasets/"
            "espaces_verts/exports/geojson"
            "?lang=fr&timezone=Europe%2FParis"
        ),
        dest=RAW_DIR / "espaces_verts.geojson",
        label="Espaces verts — Paris Open Data",
        timeout=180,
    )


def download_arbres() -> None:
    print("\n  ⚠  Arbres : fichier volumineux (~60 MB). Patienter 2-3 min…")
    _download(
        url=(
            "https://opendata.paris.fr/api/explore/v2.1/catalog/datasets/"
            "les-arbres/exports/geojson"
            "?lang=fr&timezone=Europe%2FParis"
        ),
        dest=RAW_DIR / "arbres.geojson",
        label="Arbres — Paris Open Data",
        timeout=400,
    )


def check_shops_csv() -> None:
    """Vérifie que shops_point.csv est bien présent, sans le télécharger."""
    dest = RAW_DIR / "shops_point.csv"
    print(f"\n  [Commerces — shops_point.csv]")
    if dest.exists():
        size_mb = dest.stat().st_size / 1024 / 1024
        print(f"  ✓ Présent ({size_mb:.0f} MB) → {dest}")
    else:
        print(f"  ⚠  FICHIER MANQUANT : {dest.resolve()}")
        print(f"  → Télécharger manuellement depuis :")
        print(f"    https://www.data.gouv.fr/fr/datasets/localisations-des-magasins-dans-openstreetmap/")
        print(f"  → Placer le fichier CSV ici :")
        print(f"    {dest.resolve()}")


# ── Main ──────────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Téléchargement des données brutes SVP (espaces verts + arbres)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Note : les commerces alimentaires (shops_point.csv) doivent être
placés manuellement dans data/raw/raw_SVP/shops_point.csv.
Télécharger depuis :
  https://www.data.gouv.fr/fr/datasets/localisations-des-magasins-dans-openstreetmap/
        """,
    )
    parser.add_argument(
        "--only",
        choices=["ev", "arbres"],
        help="Télécharger uniquement une source (ev ou arbres)",
    )
    args = parser.parse_args()

    print("=" * 57)
    print("  TÉLÉCHARGEMENT DES DONNÉES SVP")
    print(f"  Destination : {RAW_DIR.resolve()}")
    print("=" * 57)

    t0 = time.time()
    errors = []

    targets = {
        "ev"    : download_espaces_verts,
        "arbres": download_arbres,
    }

    to_run = {args.only: targets[args.only]} if args.only else targets

    for name, fn in to_run.items():
        try:
            fn()
        except Exception as e:
            print(f"\n  ❌ Erreur [{name}] : {e}")
            errors.append(name)

    # Toujours vérifier la présence du CSV commerces
    check_shops_csv()

    elapsed = time.time() - t0
    print(f"\n{'=' * 57}")
    if errors:
        print(f"  ⚠  Terminé en {elapsed:.0f}s avec {len(errors)} erreur(s) : {errors}")
        sys.exit(1)
    else:
        print(f"  ✓ Téléchargements terminés en {elapsed:.0f}s")
        print("  → Vérifier que shops_point.csv est présent")
        print("  → Puis lancer : python run_pipeline.py --indicateur SVP")
    print("=" * 57)


if __name__ == "__main__":
    main()

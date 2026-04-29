#!/usr/bin/env python3
"""
prepare_iris_geojson.py
======================
Génère le fichier iris_paris.geojson requis par l'API.
Extrait la géométrie IRIS depuis l'archive IGN et la sauvegarde en GeoJSON.

À exécuter UNE FOIS avant de lancer l'API :
    python prepare_iris_geojson.py
"""

import sys
from pathlib import Path

# Importer les fonctions du module bronze_ITR
sys.path.insert(0, str(Path(__file__).parent))
from src.bronze.bronze_ITR.iris_geo_bronze import load_iris_geo, cleanup_tmp

# Chemins
OUTPUT_DIR = Path("data/raw/raw_IMQ")
OUTPUT_FILE = OUTPUT_DIR / "iris_paris.geojson"


def main():
    print("=" * 70)
    print("PRÉPARATION : Extraction IRIS Géo pour l'API")
    print("=" * 70)
    
    # Créer le répertoire s'il n'existe pas
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    # Charger le GeoDataFrame IRIS
    print("\n1. Extraction de l'archive IRIS-GE...")
    gdf = load_iris_geo()
    
    # Renommer CODE_IRIS en code_iris (attendu par l'API)
    gdf = gdf.rename(columns={"CODE_IRIS": "code_iris"})
    
    # Sauvegarder en GeoJSON
    print(f"\n2. Sauvegarde en GeoJSON...")
    gdf.to_file(OUTPUT_FILE, driver="GeoJSON")
    
    # Afficher les stats
    file_size = OUTPUT_FILE.stat().st_size / 1024 / 1024
    print(f"   ✓ Fichier créé : {OUTPUT_FILE}")
    print(f"   ✓ Taille : {file_size:.1f} MB")
    print(f"   ✓ Lignes : {len(gdf)}")
    print(f"   ✓ Colonnes : {list(gdf.columns)}")
    
    # Nettoyer les répertoires temporaires
    print(f"\n3. Nettoyage...")
    cleanup_tmp()
    
    print("\n" + "=" * 70)
    print("✓ PRÊT : Vous pouvez maintenant lancer l'API")
    print("   python -m uvicorn api.main:app --reload --port 8000")
    print("=" * 70)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\n❌ ERREUR : {e}", file=sys.stderr)
        sys.exit(1)

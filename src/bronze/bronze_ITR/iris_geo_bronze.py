"""
BRONZE — IRIS Géo (IGN)
========================
Extraction du GeoPackage IRIS Paris depuis l'archive .7z IGN.
Reprojection Lambert 93 → WGS84 (EPSG:4326) pour compatibilité
avec les coordonnées GPS du DVF.

Source   : data/raw/IRIS-GE_3-0__GPKG_LAMB93_D075_2025-01-01.7z
Sortie   : data/bronze/iris_geo_raw.gpkg  (WGS84, couche 'iris_ge')
Lignes   : ~992 IRIS Paris
Clé      : CODE_IRIS (9 chiffres, ex: 751010101)
"""

import geopandas as gpd
import py7zr
import shutil
from pathlib import Path

RAW_PATH    = Path("data/raw/raw_ITR/IRIS-GE_3-0__GPKG_LAMB93_D075_2025-01-01.7z")
OUTPUT_PATH = Path("data/bronze/bronze_ITR/iris_geo_raw.gpkg")
TMP_DIR     = Path("data/bronze/bronze_ITR/_tmp_iris")

# Colonnes à garder (le GeoPackage IGN contient beaucoup de métadonnées inutiles)
COLS_A_GARDER = [
    "CODE_IRIS",   # code IRIS 9 chiffres — clé de jointure avec Filosofi
    "NOM_IRIS",    # nom de l'IRIS (quartier)
    "TYP_IRIS",    # type : H (habitat), A (activité), D (divers), Z (commune entière)
    "INSEE_COM",   # code commune (75101 → 75120)
    "NOM_COM",     # nom commune (Paris 1er, etc.)
    "geometry",    # polygone — indispensable pour le spatial join
]


def extract_7z(archive: Path, dest: Path) -> Path:
    """Extrait l'archive .7z et retourne le chemin du .gpkg extrait."""
    dest.mkdir(parents=True, exist_ok=True)
    with py7zr.SevenZipFile(archive, mode="r") as z:
        z.extractall(path=dest)
    gpkg_files = list(dest.rglob("*.gpkg"))
    assert gpkg_files, f"Aucun .gpkg trouvé dans {dest}"
    return gpkg_files[0]


def load_iris_geo(path: Path = RAW_PATH) -> gpd.GeoDataFrame:
    print(f"  Extraction de l'archive : {path}")
    gpkg_path = extract_7z(path, TMP_DIR)
    print(f"  GeoPackage extrait : {gpkg_path}")

    # Lire le GeoPackage (couche unique pour D075)
    gdf = gpd.read_file(gpkg_path)
    print(f"  CRS source : {gdf.crs}  →  reprojection en EPSG:4326 (WGS84)")

    # Reprojection Lambert 93 → WGS84
    gdf = gdf.to_crs(epsg=4326)

    # Normaliser le nom de colonne CODE_IRIS (peut varier selon millésime IGN)
    # Chercher la colonne qui ressemble à un code IRIS
    col_iris = next(
        (c for c in gdf.columns if "CODE" in c.upper() and "IRIS" in c.upper()),
        None
    )
    if col_iris and col_iris != "CODE_IRIS":
        gdf = gdf.rename(columns={col_iris: "CODE_IRIS"})

    # Garder uniquement les colonnes utiles (+ celles qui existent)
    cols_presentes = [c for c in COLS_A_GARDER if c in gdf.columns]
    gdf = gdf[cols_presentes]

    # S'assurer que CODE_IRIS est bien en string sur 9 caractères
    gdf["CODE_IRIS"] = gdf["CODE_IRIS"].astype(str).str.zfill(9)

    return gdf


def validate(gdf: gpd.GeoDataFrame) -> None:
    assert "CODE_IRIS" in gdf.columns, "Colonne CODE_IRIS manquante"
    assert "geometry" in gdf.columns, "Colonne geometry manquante"
    assert str(gdf.crs.to_epsg()) == "4326", f"CRS attendu 4326, obtenu {gdf.crs}"

    iris_len = gdf["CODE_IRIS"].str.len().unique()
    assert list(iris_len) == [9], f"Codes IRIS pas tous à 9 chiffres : {iris_len}"

    print(f"  [OK] {gdf.shape[0]} IRIS Paris")
    print(f"  [OK] CRS : {gdf.crs}")
    print(f"  [OK] Colonnes : {list(gdf.columns)}")
    if "TYP_IRIS" in gdf.columns:
        print(f"  [OK] Types IRIS : {gdf['TYP_IRIS'].value_counts().to_dict()}")
    print(f"  [OK] Bbox Paris : {gdf.total_bounds.round(4)}")


def cleanup_tmp() -> None:
    if TMP_DIR.exists():
        shutil.rmtree(TMP_DIR)
        print(f"  Dossier temporaire supprimé : {TMP_DIR}")


def run() -> gpd.GeoDataFrame:
    print("=== BRONZE : IRIS Géo ===")
    gdf = load_iris_geo()
    validate(gdf)
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    gdf.to_file(OUTPUT_PATH, driver="GPKG", layer="iris_ge")
    print(f"  Sauvegardé : {OUTPUT_PATH}  ({OUTPUT_PATH.stat().st_size / 1024:.0f} KB)")
    cleanup_tmp()
    return gdf


if __name__ == "__main__":
    run()
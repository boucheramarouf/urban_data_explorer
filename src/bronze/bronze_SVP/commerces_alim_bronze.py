"""
BRONZE — Commerces alimentaires Paris
=======================================
Ingestion brute depuis le fichier CSV data.gouv.fr :
"Localisations des magasins dans OpenStreetMap" (shops_point.csv)

Source    : https://www.data.gouv.fr/fr/datasets/
            localisations-des-magasins-dans-openstreetmap/
Fichier   : data/raw/raw_SVP/shops_point.csv   (à placer manuellement)
Sortie    : data/bronze/bronze_SVP/commerces_alim_raw.parquet

Format du CSV :
    - ~100 000 lignes (France entière)
    - Colonne géométrie : 'the_geom'  →  POINT (x y) en EPSG:3857
      (Pseudo-Mercator, coordonnées en mètres — PAS des degrés)
    - Colonne type      : 'shop'      (ex: supermarket, bakery, …)
    - Colonnes adresse  : 'addr-street', 'addr-postcode', 'addr-city'

Transformations appliquées au bronze :
    1. Filtre shop ∈ SHOP_TAGS_ALIM (catégories alimentaires uniquement)
    2. Parse géométrie POINT (x y)  →  lon/lat WGS84 via conversion Mercator
    3. Filtre bbox Paris intramuros  (lon ∈ [2.22, 2.47] / lat ∈ [48.81, 48.91])
    4. Aucune transformation métier supplémentaire (rôle du silver)

Résultat attendu : ~1 800 commerces alimentaires parisiens.
"""

import re
import math
import pandas as pd
import geopandas as gpd
from pathlib import Path
from shapely.geometry import Point

# ── Chemins ───────────────────────────────────────────────────────────────────

RAW_CSV     = Path("data/raw/raw_SVP/shops_point.csv")
OUTPUT_PATH = Path("data/bronze/bronze_SVP/commerces_alim_raw.parquet")

# ── Bounding box Paris intramuros (WGS84) ─────────────────────────────────────

PARIS_LON_MIN, PARIS_LON_MAX = 2.220, 2.470
PARIS_LAT_MIN, PARIS_LAT_MAX = 48.815, 48.910

# ── Catégories alimentaires à retenir (colonne "shop") ───────────────────────

SHOP_TAGS_ALIM = {
    "supermarket", "convenience", "grocery", "food", "deli",
    "butcher", "bakery", "greengrocer", "seafood", "cheese",
    "wine", "beverages", "alcohol", "farm",
}

# ── Regex pour parser POINT (x y) ─────────────────────────────────────────────

_RE_POINT = re.compile(r"POINT\s*\(([+-]?\d+\.?\d*)\s+([+-]?\d+\.?\d*)\)")


# ──────────────────────────────────────────────────────────────────────────────
# UTILITAIRES GÉOMÉTRIE
# ──────────────────────────────────────────────────────────────────────────────

def _parse_point_mercator(geom_str: str) -> tuple[float | None, float | None]:
    """
    Extrait (x, y) depuis une chaîne WKT 'POINT (x y)'.
    Les coordonnées sont en EPSG:3857 (Pseudo-Mercator, mètres).
    Retourne (None, None) si le format est invalide.
    """
    m = _RE_POINT.match(str(geom_str).strip())
    if not m:
        return None, None
    return float(m.group(1)), float(m.group(2))


def _mercator_to_wgs84(x: float, y: float) -> tuple[float, float]:
    """
    Convertit des coordonnées EPSG:3857 (Pseudo-Mercator) en WGS84 (lon/lat).

    Formules exactes (sans pyproj pour éviter la dépendance) :
        lon = x / 20037508.34 * 180
        lat = degrees(2 * atan(exp(y / 20037508.34 * π)) - π/2)
    """
    lon = x / 20037508.34 * 180.0
    lat = math.degrees(
        2.0 * math.atan(math.exp(y / 20037508.34 * math.pi)) - math.pi / 2.0
    )
    return round(lon, 7), round(lat, 7)


# ──────────────────────────────────────────────────────────────────────────────
# CHARGEMENT
# ──────────────────────────────────────────────────────────────────────────────

def load_csv(path: Path) -> pd.DataFrame:
    """
    Charge le CSV shops_point.csv avec les types adaptés.
    On lit uniquement les colonnes utiles pour alléger la mémoire.
    """
    if not path.exists():
        raise FileNotFoundError(
            f"Fichier source introuvable : {path.resolve()}\n"
            f"→ Télécharger le CSV depuis :\n"
            f"  https://www.data.gouv.fr/fr/datasets/"
            f"localisations-des-magasins-dans-openstreetmap/\n"
            f"→ Le renommer 'shops_point.csv' et le placer dans :\n"
            f"  {path.parent.resolve()}"
        )

    cols_utiles = [
        "osm_id", "shop", "name", "brand", "operator",
        "opening_hours",
        "addr-street", "addr-housenumber", "addr-postcode", "addr-city",
        "the_geom", "osm_type",
    ]

    df = pd.read_csv(
        path,
        usecols=cols_utiles,
        low_memory=False,
        dtype={
            "osm_id"          : "string",
            "shop"            : "string",
            "name"            : "string",
            "brand"           : "string",
            "operator"        : "string",
            "opening_hours"   : "string",
            "addr-street"     : "string",
            "addr-housenumber": "string",
            "addr-postcode"   : "string",
            "addr-city"       : "string",
            "the_geom"        : "string",
            "osm_type"        : "string",
        },
    )

    print(f"  CSV chargé : {len(df):,} lignes | {df.shape[1]} colonnes utiles")
    return df


# ──────────────────────────────────────────────────────────────────────────────
# FILTRAGE ET CONVERSION GÉOMÉTRIQUE
# ──────────────────────────────────────────────────────────────────────────────

def filter_and_convert(df: pd.DataFrame) -> gpd.GeoDataFrame:
    """
    1. Filtre les catégories alimentaires (colonne 'shop')
    2. Parse la géométrie POINT (x y) EPSG:3857
    3. Convertit en WGS84 (lon/lat)
    4. Filtre bbox Paris intramuros
    5. Retourne un GeoDataFrame EPSG:4326
    """
    n0 = len(df)

    # ── 1. Filtre shop alimentaire ──────────────────────────────────────────
    df = df.copy()
    df["shop_lower"] = df["shop"].str.lower().str.strip().fillna("")
    df = df[df["shop_lower"].isin(SHOP_TAGS_ALIM)]
    print(f"  Après filtre shop alimentaire : {len(df):,}  (-{n0 - len(df):,} hors catégorie)")

    # ── 2. Parse géométrie + conversion Mercator → WGS84 ───────────────────
    rows_valides = []
    n_geom_nulle = 0

    for _, row in df.iterrows():
        x, y = _parse_point_mercator(row["the_geom"])
        if x is None:
            n_geom_nulle += 1
            continue

        lon, lat = _mercator_to_wgs84(x, y)

        # ── 3. Filtre bbox Paris ────────────────────────────────────────────
        if not (PARIS_LON_MIN <= lon <= PARIS_LON_MAX and
                PARIS_LAT_MIN <= lat <= PARIS_LAT_MAX):
            continue

        rows_valides.append({
            "osm_id"       : row["osm_id"],
            "osm_type"     : row["osm_type"],
            "shop"         : row["shop_lower"],
            "name"         : row["name"] if pd.notna(row["name"]) else "",
            "brand"        : row["brand"] if pd.notna(row["brand"]) else "",
            "opening_hours": row["opening_hours"] if pd.notna(row["opening_hours"]) else "",
            "addr_street"  : row["addr-street"] if pd.notna(row["addr-street"]) else "",
            "addr_postcode": row["addr-postcode"] if pd.notna(row["addr-postcode"]) else "",
            "lon"          : lon,
            "lat"          : lat,
        })

    if n_geom_nulle:
        print(f"  [WARN] {n_geom_nulle} géométries non parsées (ignorées)")

    if not rows_valides:
        raise RuntimeError(
            "Aucun commerce alimentaire parisien trouvé après filtrage.\n"
            "Vérifier que le fichier CSV est bien shops_point.csv (data.gouv)."
        )

    result_df = pd.DataFrame(rows_valides)
    print(f"  Après filtre bbox Paris       : {len(result_df):,} commerces retenus")

    # ── 4. Création GeoDataFrame EPSG:4326 ──────────────────────────────────
    gdf = gpd.GeoDataFrame(
        result_df,
        geometry=[Point(r["lon"], r["lat"]) for r in rows_valides],
        crs="EPSG:4326",
    )

    return gdf


# ──────────────────────────────────────────────────────────────────────────────
# VALIDATION BRONZE
# ──────────────────────────────────────────────────────────────────────────────

def validate(gdf: gpd.GeoDataFrame) -> None:
    assert len(gdf) > 0, "GeoDataFrame vide"
    assert gdf.geometry.isna().sum() == 0, "Géométries nulles"
    assert gdf["lon"].between(PARIS_LON_MIN, PARIS_LON_MAX).all(), \
        "Longitudes hors bbox Paris"
    assert gdf["lat"].between(PARIS_LAT_MIN, PARIS_LAT_MAX).all(), \
        "Latitudes hors bbox Paris"

    print(f"\n  [OK] {len(gdf):,} commerces alimentaires parisiens")
    print(f"  [OK] Répartition par type :")
    for shop, n in gdf["shop"].value_counts().items():
        pct = n / len(gdf) * 100
        print(f"       {shop:<15} {n:>5}  ({pct:.1f}%)")
    print(f"  [OK] Bbox : lon [{gdf['lon'].min():.4f}, {gdf['lon'].max():.4f}] "
          f"lat [{gdf['lat'].min():.4f}, {gdf['lat'].max():.4f}]")


# ──────────────────────────────────────────────────────────────────────────────
# SAUVEGARDE
# ──────────────────────────────────────────────────────────────────────────────

def save(gdf: gpd.GeoDataFrame, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    df = pd.DataFrame(gdf.copy())
    df["geometry_wkt"] = gdf.geometry.to_wkt()
    df = df.drop(columns=["geometry"], errors="ignore")
    df.to_parquet(path, index=False)
    print(f"  Sauvegardé : {path}  ({path.stat().st_size / 1024:.0f} KB)")


# ──────────────────────────────────────────────────────────────────────────────
# POINT D'ENTRÉE
# ──────────────────────────────────────────────────────────────────────────────

def run() -> gpd.GeoDataFrame:
    print("=== BRONZE SVP : Commerces alimentaires (shops_point.csv) ===")
    print(f"  Source : {RAW_CSV}")

    df  = load_csv(RAW_CSV)
    gdf = filter_and_convert(df)
    validate(gdf)
    save(gdf, OUTPUT_PATH)

    return gdf


if __name__ == "__main__":
    run()

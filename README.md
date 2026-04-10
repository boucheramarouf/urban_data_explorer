# 🏙️ Urban Data Explorer — Paris

> Plateforme collaborative d'analyse et de visualisation des dynamiques du logement à Paris.  
> Architecture multi-indicateurs : chaque équipe contribue son propre indicateur dans un dossier dédié.

---

## 👥 Organisation du projet

Ce dépôt est partagé entre plusieurs équipes. Chaque indicateur vit dans son propre sous-dossier `_NOM` à chaque niveau du pipeline :

```
src/bronze/bronze_MON_INDICATEUR/
src/silver/silver_MON_INDICATEUR/
src/gold/gold_MON_INDICATEUR/
data/raw/raw_MON_INDICATEUR/
data/bronze/bronze_MON_INDICATEUR/
data/silver/silver_MON_INDICATEUR/
data/gold/gold_MON_INDICATEUR/
```

**Indicateurs actuels :**

| Indicateur | Équipe | Description |
|---|---|---|
| `ITR` | Équipe 1 | Indice de Tension Résidentielle par rue |
| `MON_INDICATEUR` | Équipe N | … |

---

## 🗂️ Architecture complète

```
urban_data_explorer/
│
├── data/
│   ├── raw/
│   │   └── raw_ITR/                        ← sources brutes ITR
│   │       ├── DVF.csv
│   │       ├── BASE_TD_FILO_IRIS_2021_DEC.csv
│   │       ├── meta_BASE_TD_FILO_IRIS_2021_DEC.csv
│   │       └── logements-sociaux-finances-a-paris.csv
│   ├── bronze/
│   │   └── bronze_ITR/                     ← généré automatiquement
│   │       ├── dvf_raw.parquet
│   │       ├── filosofi_iris_raw.parquet
│   │       ├── logements_sociaux_raw.parquet
│   │       └── iris_geo_raw.gpkg
│   ├── silver/
│   │   └── silver_ITR/                     ← généré automatiquement
│   │       ├── dvf_appart_propre.parquet
│   │       ├── logements_sociaux_par_iris.parquet
│   │       └── rue_enrichie.parquet
│   └── gold/
│       └── gold_ITR/                       ← généré automatiquement
│           ├── itr_par_rue.parquet
│           └── itr_par_rue.geojson
│
├── src/
│   ├── bronze/
│   │   └── bronze_ITR/
│   │       ├── dvf_bronze.py
│   │       ├── filosofi_bronze.py
│   │       ├── logements_sociaux_bronze.py
│   │       └── iris_geo_bronze.py
│   ├── silver/
│   │   └── silver_ITR/
│   │       ├── __init__.py
│   │       ├── dvf_silver.py
│   │       ├── logements_sociaux_silver.py
│   │       └── rue_enrichie_silver.py
│   └── gold/
│       └── gold_ITR/
│           ├── __init__.py
│           └── itr_gold.py
│
├── api/
│   ├── __init__.py
│   └── main.py                             ← FastAPI (tous indicateurs)
│
├── frontend/
│   ├── index.html
│   ├── package.json
│   ├── vite.config.js
│   └── src/
│       ├── App.jsx
│       ├── main.jsx
│       ├── components/
│       │   ├── Map/                        ← MapView, Tooltip, Legend
│       │   ├── Sidebar/                    ← Sidebar, SearchBar, Filters, RueDetail
│       │   └── Stats/                      ← StatsPanel, ArrondChart
│       ├── hooks/                          ← useGeoJSON, useStats
│       └── styles/
│
├── run_pipeline.py                         ← orchestrateur global
├── requirements.txt
├── .gitignore
└── README.md
```

---

## 🧮 Indicateur ITR — Indice de Tension Résidentielle

> À quel point est-il difficile de se loger dans cette rue parisienne ?

### Formule

```
ITR_brut(rue) =  (prix_m2_median / revenu_median_uc)
              ×  (1 + 1 / (1 + nb_logements_sociaux))

ITR_score     =  100 × (ITR_brut - min) / (max - min)
```

| Composante | Source | Granularité |
|---|---|---|
| `prix_m2_median` | DVF 2021 | Rue — médiane des transactions |
| `revenu_median_uc` | Filosofi INSEE 2021 | IRIS → spatial join GPS |
| `nb_logements_sociaux` | Open Data Paris | IRIS → spatial join GPS |

### Niveaux de tension (quintiles)

| Score | Label | Couleur |
|---|---|---|
| 0–20 | 🟢 Très accessible | `#22c55e` |
| 20–40 | 🟡 Accessible | `#84cc16` |
| 40–60 | 🟠 Modéré | `#eab308` |
| 60–80 | 🔴 Tendu | `#f97316` |
| 80–100 | 🔴 Très tendu | `#ef4444` |

### Sources de données ITR

| Source | Fichier | Lien |
|---|---|---|
| DVF | `DVF.csv` | [data.gouv.fr](https://www.data.gouv.fr/fr/datasets/demandes-de-valeurs-foncieres/) |
| Filosofi INSEE | `BASE_TD_FILO_IRIS_2021_DEC.csv` | [insee.fr](https://www.insee.fr/fr/statistiques/7655512) |
| Logements sociaux | `logements-sociaux-finances-a-paris.csv` | [opendata.paris.fr](https://opendata.paris.fr) |
| IRIS géo IGN | `IRIS-GE_3-0__GPKG_LAMB93_D075_2025-01-01.7z` | [geoservices.ign.fr](https://geoservices.ign.fr/irisge) |

---

## 🚀 Installation & lancement

### Prérequis
- Python ≥ 3.10
- Node.js ≥ 18

### 1. Cloner le dépôt

```bash
git clone <url-du-repo>
cd urban_data_explorer
```

### 2. Installer les dépendances Python

```bash
pip install -r requirements.txt
```

### 3. Déposer les fichiers sources

Chaque équipe dépose ses fichiers dans son dossier `data/raw/raw_NOM/` :

```bash
# Exemple pour ITR
data/raw/raw_ITR/DVF.csv
data/raw/raw_ITR/BASE_TD_FILO_IRIS_2021_DEC.csv
data/raw/raw_ITR/meta_BASE_TD_FILO_IRIS_2021_DEC.csv
data/raw/raw_ITR/logements-sociaux-finances-a-paris.csv
# + le fichier .7z IRIS à placer aussi dans raw_ITR/
```

### 4. Lancer le pipeline

```bash
# Pipeline complet (tous les indicateurs)
python run_pipeline.py

# Un seul indicateur
python run_pipeline.py --indicateur ITR

# Ou couche par couche
python run_pipeline.py --bronze --indicateur ITR
python run_pipeline.py --silver --indicateur ITR
python run_pipeline.py --gold   --indicateur ITR
```

### 5. Lancer l'API (Terminal 1)

```bash
uvicorn api.main:app --reload --port 8000
```

→ Swagger UI : **http://localhost:8000/docs**

### 6. Lancer le frontend (Terminal 2)

```bash
cd frontend
npm install
npm run dev
```

→ Dashboard : **http://localhost:3000**

---

## 🔌 API — Endpoints ITR

| Méthode | Endpoint | Description |
|---|---|---|
| `GET` | `/` | Healthcheck |
| `GET` | `/stats` | Distribution + classement arrondissements |
| `GET` | `/rues` | Liste filtrée (arrdt, label, score, tri, limit) |
| `GET` | `/rues/{nom_voie}` | Détail complet avec composantes ITR |
| `GET` | `/geojson` | FeatureCollection GeoJSON pour la carte |

```bash
# Exemples
GET /rues?arrondissement=7&sort_by=itr_score&order=desc
GET /rues?label=Très tendu&limit=20
GET /geojson?arrondissement=18
GET /rues/RUE DU BAC?code_postal=75007
```

---

## 🏗️ Pipeline Bronze / Silver / Gold

### 🟫 Bronze — Ingestion brute

| Table | Lignes | Traitement |
|---|---|---|
| `dvf_raw.parquet` | 81 516 | Typage colonnes, `date_mutation` → datetime |
| `filosofi_iris_raw.parquet` | 16 026 | Virgules FR → points, IRIS zfill(9) |
| `logements_sociaux_raw.parquet` | 4 174 | Parse `geo_point_2d` → `lat` / `lon` |
| `iris_geo_raw.gpkg` | 992 IRIS | Extraction .7z, Lambert93 → WGS84 |

### 🥈 Silver — Nettoyage & jointures géo

| Table | Lignes | Transformation clé |
|---|---|---|
| `dvf_appart_propre.parquet` | 34 478 | Filtre appartements, `prix_m2`, IQR×3, spatial join → IRIS |
| `logements_sociaux_par_iris.parquet` | 802 IRIS | Spatial join → IRIS, agrégation |
| `rue_enrichie.parquet` | 2 387 rues | Pivot par rue, join logsoc, filtre `nb_trans ≥ 3` |

### 🥇 Gold — Indicateur final

| Table | Lignes | Contenu |
|---|---|---|
| `itr_par_rue.parquet` | 2 340 rues | Score ITR + composantes + label |
| `itr_par_rue.geojson` | 2 340 features | Points WGS84, prêt carte & API |

---

## 🤝 Contribuer un nouvel indicateur

1. Créer tes dossiers :
```bash
mkdir -p data/raw/raw_MON_INDIC
mkdir -p src/bronze/bronze_MON_INDIC
mkdir -p src/silver/silver_MON_INDIC
mkdir -p src/gold/gold_MON_INDIC
```

2. Implémenter tes scripts en suivant la même structure que ITR :
   - `bronze_MON_INDIC/` → ingestion brute
   - `silver_MON_INDIC/` → nettoyage + jointures
   - `gold_MON_INDIC/` → calcul indicateur + export GeoJSON

3. Exposer un endpoint dans `api/main.py`

4. Mettre à jour ce README avec la description de ton indicateur

---

## 🗺️ Stack technique

| Couche | Technologie |
|---|---|
| Pipeline data | Python · Pandas · GeoPandas · PyArrow · py7zr |
| Géospatial | Shapely · GeoPackage · GeoJSON · EPSG:4326 |
| API | FastAPI · Uvicorn |
| Frontend | React 18 · Vite |
| Carte | MapLibre GL JS |
| Graphiques | Recharts |
| Fond de carte | MapTiler (style `dataviz-dark`) |

---

## 📄 Licence

Usage académique — données sources sous Licence Ouverte Etalab (DVF, Open Data Paris) et conditions INSEE (Filosofi).
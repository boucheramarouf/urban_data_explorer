# 🏙️ ITR Paris — Indice de Tension Résidentielle

> **À quel point est-il difficile de se loger dans cette rue parisienne ?**

Dashboard interactif croisant données de transactions immobilières, revenus médians INSEE et logements sociaux pour produire un indicateur de tension résidentielle à la rue, visualisé sur carte.

---

## 🗂️ Architecture du projet

```
urban_data_explorer/
│
├── data/
│   ├── raw/                    ← fichiers sources (à déposer manuellement)
│   ├── bronze/                 ← ingestion brute typée (généré)
│   ├── silver/                 ← données nettoyées + jointures (généré)
│   └── gold/                   ← indicateur final + GeoJSON (généré)
│
├── src/
│   ├── bronze/
│   │   ├── dvf_bronze.py
│   │   ├── filosofi_bronze.py
│   │   ├── logements_sociaux_bronze.py
│   │   └── iris_geo_bronze.py
│   ├── silver/
│   │   ├── dvf_silver.py
│   │   ├── logements_sociaux_silver.py
│   │   └── rue_enrichie_silver.py
│   └── gold/
│       └── itr_gold.py
│
├── api/
│   └── main.py                 ← FastAPI (5 endpoints REST)
│
├── frontend/
│   ├── index.html
│   ├── package.json
│   ├── vite.config.js
│   └── src/
│       ├── App.jsx
│       ├── components/
│       │   ├── Map/            ← MapView, Tooltip, Legend
│       │   ├── Sidebar/        ← Sidebar, SearchBar, Filters, RueDetail
│       │   └── Stats/          ← StatsPanel, ArrondChart
│       ├── hooks/              ← useGeoJSON, useStats
│       └── styles/
│
├── run_pipeline.py             ← orchestrateur Bronze → Silver → Gold
└── requirements.txt
```

---

## 🧮 Formule ITR

```
ITR_brut(rue) =  (prix_m2_median / revenu_median_uc)
              ×  (1 + 1 / (1 + nb_logements_sociaux))

ITR_score     =  100 × (ITR_brut - min) / (max - min)
```

| Composante | Source | Granularité |
|---|---|---|
| `prix_m2_median` | DVF 2021 | Rue — médiane des transactions filtrées |
| `revenu_median_uc` | Filosofi INSEE 2021 | IRIS → rattaché via spatial join GPS |
| `nb_logements_sociaux` | Open Data Paris | IRIS → rattaché via spatial join GPS |

**Niveaux de tension (quintiles, ~468 rues par niveau) :**

| Score | Label | Couleur |
|---|---|---|
| 0–20 | 🟢 Très accessible | `#22c55e` |
| 20–40 | 🟡 Accessible | `#84cc16` |
| 40–60 | 🟠 Modéré | `#eab308` |
| 60–80 | 🔴 Tendu | `#f97316` |
| 80–100 | 🔴 Très tendu | `#ef4444` |

---

## 📦 Sources de données

| Source | Fichier à déposer dans `data/raw/` |
|---|---|
| [DVF — data.gouv.fr](https://www.data.gouv.fr/fr/datasets/demandes-de-valeurs-foncieres/) | `DVF.csv` |
| [Filosofi — INSEE](https://www.insee.fr/fr/statistiques/7655512) | `BASE_TD_FILO_IRIS_2021_DEC.csv` |
| [Logements sociaux — Open Data Paris](https://opendata.paris.fr) | `logements-sociaux-finances-a-paris.csv` |
| [IRIS-GE — IGN](https://geoservices.ign.fr/irisge) | `IRIS-GE_3-0__GPKG_LAMB93_D075_2025-01-01.7z` |

---

## 🚀 Installation & lancement

### Prérequis
- Python ≥ 3.10
- Node.js ≥ 18

### 1. Installer les dépendances Python

```bash
cd urban_data_explorer
pip install -r requirements.txt
```

### 2. Déposer les fichiers sources dans `data/raw/`

### 3. Lancer le pipeline data

```bash
# Pipeline complet Bronze → Silver → Gold
python run_pipeline.py

# Ou couche par couche
python run_pipeline.py --bronze
python run_pipeline.py --silver
python run_pipeline.py --gold
```

R�sultat attendu :
```
==================================================
  COUCHE BRONZE
==================================================
=== BRONZE : DVF ===
  [OK] 81,516 lignes | 40 colonnes  ✓

[...]

==================================================
  COUCHE GOLD
==================================================
=== GOLD : Calcul ITR par rue ===
  2,340 rues avec score ITR valide
  Très accessible  :  468 rues  20.0%  ████████
  Accessible       :  468 rues  20.0%  ████████
  Modéré           :  468 rues  20.0%  ████████
  Tendu            :  468 rues  20.0%  ████████
  Très tendu       :  468 rues  20.0%  ████████

✓ Pipeline terminé en ~12s
```

### 4. Lancer l'API (Terminal 1)

```bash
uvicorn api.main:app --reload --port 8000
```

→ Swagger UI : **http://localhost:8000/docs**

### 5. Lancer le frontend (Terminal 2)

```bash
cd frontend
npm install
npm run dev
```

→ Dashboard : **http://localhost:3000**

---

## 🔌 API — Endpoints

| Méthode | Endpoint | Description |
|---|---|---|
| `GET` | `/` | Healthcheck |
| `GET` | `/stats` | Distribution + classement arrondissements |
| `GET` | `/rues` | Liste filtrée des rues (arrdt, label, score, tri, limit) |
| `GET` | `/rues/{nom_voie}` | Détail complet d'une rue avec composantes ITR |
| `GET` | `/geojson` | FeatureCollection GeoJSON pour la carte |

**Exemples :**
```bash
# Rues du 7e, triées par score
GET /rues?arrondissement=7&sort_by=itr_score&order=desc

# Top 20 rues très tendues
GET /rues?label=Très tendu&limit=20

# GeoJSON filtré par arrondissement
GET /geojson?arrondissement=18

# Détail d'une rue
GET /rues/RUE DU BAC?code_postal=75007
```

---

## 🏗️ Pipeline data — Bronze / Silver / Gold

### 🟫 Bronze — Ingestion brute (zéro logique métier)

| Table | Lignes | Traitement |
|---|---|---|
| `dvf_raw.parquet` | 81 516 | Typage colonnes, `date_mutation` → datetime |
| `filosofi_iris_raw.parquet` | 16 026 | Virgules décimales FR → points, IRIS → zfill(9) |
| `logements_sociaux_raw.parquet` | 4 174 | Parse `geo_point_2d` (string) → `lat` / `lon` float |
| `iris_geo_raw.gpkg` | 992 IRIS | Extraction .7z, reprojection Lambert93 → WGS84 |

### 🥈 Silver — Nettoyage & jointures géographiques

| Table | Lignes | Transformation clé |
|---|---|---|
| `dvf_appart_propre.parquet` | 34 478 | Filtre appartements, calcul `prix_m2`, outliers IQR×3/arrdt, **spatial join** point DVF → IRIS |
| `logements_sociaux_par_iris.parquet` | 802 IRIS | **Spatial join** programmes → IRIS, `SUM(nb_logements)` |
| `rue_enrichie.parquet` | 2 387 rues | Pivot par `(nom_voie, code_postal)`, join logsoc via `CODE_IRIS`, filtre `nb_transactions ≥ 3` |

### 🥇 Gold — Indicateur & livraison

| Table | Lignes | Contenu |
|---|---|---|
| `itr_par_rue.parquet` | 2 340 rues | Score ITR + composantes `c1_effort`, `c2_logsoc`, label |
| `itr_par_rue.geojson` | 2 340 features | GeoJSON points WGS84, prêt carte & API |

---

## 🗺️ Stack technique

| Couche | Technologie |
|---|---|
| Pipeline data | Python · Pandas · GeoPandas · PyArrow · py7zr |
| Géospatial | Shapely · GeoPackage · GeoJSON · EPSG:4326 |
| API | FastAPI · Uvicorn |
| Frontend | React 18 · Vite |
| Carte | **MapLibre GL JS** |
| Graphiques | Recharts |
| Fond de carte | MapTiler (style `dataviz-dark`) |

---

## 🧩 Fonctionnalités du dashboard

- **Carte interactive** — points colorés par `itr_score`, taille ∝ `nb_transactions`
- **Tooltip au survol** — prix/m², revenu, logements sociaux, score
- **Détail au clic** — composantes ITR, zoom automatique, badge niveau de tension
- **Recherche** — live par nom de rue avec dropdown auto-complétion
- **Filtres** — par arrondissement et par niveau de tension
- **Compteur** — nombre de rues affichées après filtrage
- **Onglet Stats** — KPIs Paris + distribution 5 niveaux + bar chart 20 arrondissements
- **Légende** — 5 niveaux de tension, bas droite de la carte

---

## 📄 Licence

Usage académique — données sources sous Licence Ouverte Etalab (DVF, Open Data Paris) et conditions INSEE (Filosofi).
# Urban Data Explorer · Paris

Plateforme d'analyse et de visualisation des dynamiques du logement à Paris.  
4 indicateurs composites calculés à l'échelle IRIS ou rue sur les données open data parisiennes.

---

## Architecture globale

```mermaid
flowchart LR
    subgraph SRC["Sources open data"]
        direction TB
        S1["DVF+ · SIRENE\nLOVAC · Filosofi"]
        S2["GTFS · OSM\nVélib'"]
    end

    subgraph LAKE["Data Lake — Medallion Architecture"]
        direction TB
        RAW["Raw\nfichiers sources bruts"]
        BRONZE["Bronze\ningestion Parquet"]
        SILVER["Silver\nnettoyage · jointures"]
        GOLD["Gold\nIMQ · ITR · SVP · IAML"]
        RAW --> BRONZE --> SILVER --> GOLD
    end

    subgraph STORE["Bases de données"]
        direction TB
        PG["PostgreSQL 16\n4 tables"]
        MONGO["MongoDB 7\n4 collections"]
    end

    subgraph BACKEND["API — FastAPI :8000"]
        direction TB
        SEC["Auth X-API-Key\nRate-limit 300 req/min"]
        END["Endpoints GeoJSON\n/imq /itr /svp /iaml"]
        SSE["/stream/events\nRedis Pub/Sub SSE"]
        SEC --> END
    end

    subgraph FRONT["Frontend React :3000"]
        direction TB
        MAP["Carte MapLibre\n4 indicateurs"]
        PAGES["Comparateur\nIndicateurs · Sources"]
    end

    subgraph ORCH["Orchestration"]
        direction TB
        AF["Airflow\nDAG quotidien 02:00"]
        RD["Redis\nCelery + Pub/Sub"]
    end

    SRC --> RAW
    GOLD --> PG & MONGO
    PG & MONGO --> END
    END --> MAP & PAGES
    AF -- "pilote" --> LAKE
    RD -- "broker" --> AF
    RD -- "events" --> SSE
```

---

## Schéma relationnel — PostgreSQL

```mermaid
erDiagram
    imq_par_iris {
        TEXT iris_code PK
        TEXT iris_nom
        TEXT arr_insee
        FLOAT delta_prix_norm
        FLOAT ratio_comm_norm
        FLOAT revenu_norm
        FLOAT vacance_norm
        FLOAT score_imq
        TEXT interpretation
    }

    itr_par_rue {
        TEXT nom_voie PK
        TEXT code_postal PK
        INT arrondissement
        TEXT code_iris FK
        FLOAT lon_centre
        FLOAT lat_centre
        FLOAT prix_m2_median
        FLOAT revenu_median_uc
        INT nb_logements_sociaux
        INT nb_transactions
        FLOAT itr_score
        TEXT itr_label
    }

    svp_par_rue {
        TEXT nom_voie PK
        TEXT code_postal PK
        INT arrondissement
        TEXT code_iris FK
        FLOAT lon_centre
        FLOAT lat_centre
        INT nb_espaces_verts
        INT nb_arbres
        FLOAT svp_score
        TEXT svp_label
        BOOL has_commerce
    }

    iaml_par_rue {
        TEXT nom_voie PK
        TEXT code_postal PK
        INT arrondissement
        FLOAT lon_centre
        FLOAT lat_centre
        FLOAT prix_m2_median
        INT nb_lignes_metro
        INT nb_lignes_bus
        INT nb_points_velib
        FLOAT score_accessibilite
        FLOAT iaml_score
        TEXT iaml_label
    }

    imq_par_iris ||--o{ itr_par_rue : "code_iris"
    imq_par_iris ||--o{ svp_par_rue : "code_iris"
```

> Granularité : `imq_par_iris` à l'échelle IRIS · `itr_par_rue`, `svp_par_rue`, `iaml_par_rue` à l'échelle rue.  
> Clé de jointure spatiale : `code_iris` — chaque rue appartient à un IRIS parisien.

---

## Indicateurs

| Indicateur | Granularité | Sources | Volume |
|---|---|---|---|
| **IMQ** — Indice de Mutation de Quartier | IRIS | DVF+, SIRENE, Filosofi, LOVAC | 992 IRIS |
| **ITR** — Indice de Tension Résidentielle | Rue | DVF+ | 1 254 rues |
| **SVP** — Score de Verdure et Proximité | Rue | OSM (parcs, arbres) | 1 254 rues |
| **IAML** — Accessibilité Multimodale au Logement | Rue | GTFS, Vélib', OSM | 1 329 rues |

---

## Stack technique

| Composant | Technologie |
|---|---|
| Pipeline ETL | Python · Pandas · GeoPandas · Parquet |
| Orchestration | Apache Airflow 2 · Celery · Redis |
| Base relationnelle | PostgreSQL 16 |
| Base documentaire | MongoDB 7 |
| API | FastAPI · Uvicorn · Auth API Key · Rate-limiting Redis |
| Streaming | Redis Pub/Sub · SSE (Server-Sent Events) |
| Frontend | React 18 · MapLibre GL JS 4 · Vite |
| Infrastructure | Docker · Docker Compose |

---

## Prérequis

- Docker Desktop (Linux engine)
- Node.js 18+ (frontend local uniquement)

---

## Démarrage

### 1. Lancer tous les services

```bash
docker compose up -d --build
```

### 2. Première utilisation — préparer les géométries IRIS

```bash
python prepare_iris_geojson.py
```

Génère `data/raw/raw_IMQ/iris_paris.geojson` (992 IRIS parisiens, requis pour IMQ).

### 3. Lancer le pipeline complet

```bash
docker compose exec api python run_pipeline.py
```

Le pipeline s'exécute en Bronze → Silver → Gold → chargement PostgreSQL + MongoDB.  
Les étapes déjà calculées sont automatiquement ignorées (cache Parquet).

---

## Services et URLs

| Service | URL | Credentials |
|---|---|---|
| Frontend React | http://localhost:3000 | — |
| API FastAPI | http://localhost:8000 | `X-API-Key: urban-data-explorer-2026` |
| Swagger / docs | http://localhost:8000/docs | même clé via bouton Authorize |
| Airflow UI | http://localhost:8080 | admin / admin |
| pgAdmin | http://localhost:5051 | admin@local.com / admin |
| Mongo Express | http://localhost:8081 | admin / admin |

---

## API — Endpoints principaux

### Authentification
Tous les endpoints (sauf `/health`) requièrent l'en-tête :
```
X-API-Key: urban-data-explorer-2026
```

### Rate-limiting
300 requêtes par minute par IP (compteur Redis). Au-delà : `429 Too Many Requests`.

### Indicateurs
```
GET /imq/geojson   GET /imq/stats
GET /itr/geojson   GET /itr/stats    GET /itr/rues    GET /itr/rues/{nom_voie}
GET /svp/geojson   GET /svp/stats    GET /svp/rues
GET /iaml/geojson  GET /iaml/stats   GET /iaml/rues   GET /iaml/rues/{nom_voie}
```

### Streaming temps réel (Redis Pub/Sub)
```
GET  /stream/events    → flux SSE (Server-Sent Events)
GET  /stream/status    → état de la connexion Redis
POST /stream/publish   → publier un événement (test)
```

---

## Pipeline détaillé

Architecture Medallion (4 couches) :

```
data/raw/          → fichiers sources bruts (DVF .gpkg, SIRENE .csv.gz, LOVAC .xlsx…)
data/bronze/       → ingestion Parquet sans transformation (conversion de format)
data/silver/       → nettoyage, jointures spatiales, agrégations par IRIS ou rue
data/gold/         → scores IMQ/ITR/SVP/IAML (0-100) + chargement PostgreSQL & MongoDB
```

Commandes par couche :
```bash
docker compose exec api python run_pipeline.py --bronze
docker compose exec api python run_pipeline.py --silver
docker compose exec api python run_pipeline.py --gold
docker compose exec api python run_pipeline.py --load-db
docker compose exec api python run_pipeline.py --indicateur ITR
```

### Metriques de performance

Affiche un tableau comparatif des temps d'exécution par tâche sur les N derniers runs :

```bash
docker compose exec api python pipeline_metrics.py --runs 3
```

---

## Vérification des bases de données

### PostgreSQL
```bash
docker compose exec api python -c "
from sqlalchemy import create_engine, text, inspect
import os
eng = create_engine(os.environ['DATABASE_URL'])
with eng.connect() as c:
    for t in inspect(eng).get_table_names():
        print(t, c.execute(text(f'SELECT COUNT(*) FROM {t}')).scalar())
"
```

### MongoDB
```bash
docker exec urban_data_explorer_mongo mongosh -u urban_mongo_admin -p urban_mongo_pass \
  --authenticationDatabase admin \
  --eval "db=db.getSiblingDB('urban_data'); db.getCollectionNames().forEach(c=>print(c,db[c].countDocuments()))"
```

---

## Arrêt

```bash
docker compose down
```


```text
urban_data_explorer/
   api/                # FastAPI
   frontend/           # React + Vite
   src/                # Pipelines bronze/silver/gold par indicateur
   data/               # Donnees raw/bronze/silver/gold
   run_pipeline.py     # Orchestrateur du pipeline
   Dockerfile
   Docker-compose.yml
```

## Prerequis

- Docker + Docker Compose
- Node.js 18+ (pour lancer le frontend en local)

## Demarrage simple

### Première utilisation : Préparation des données géométriques IRIS

Avant de lancer l'API pour la première fois, vous devez extraire la géométrie des IRIS depuis l'archive IGN :

```bash
python prepare_iris_geojson.py
```

Cela génère le fichier `data/raw/raw_IMQ/iris_paris.geojson` (1.9 MB) contenant les 992 IRIS de Paris, nécessaire pour charger l'API IMQ.

### Lancement

1. Lancer tous les services

```bash
docker compose up -d --build
```

2. Verifier les services

```bash
docker compose ps
```

3. Lancer la couche gold (alimente PostgreSQL et MongoDB)

```bash
docker compose exec -T api python run_pipeline.py --gold
```

## Services et URLs

- API FastAPI : http://localhost:8000
- Documentation API : http://localhost:8000/docs
- Frontend (dev local) : http://localhost:5173
- pgAdmin : http://localhost:5051
- Mongo Express : http://localhost:8081

## Base de donnees

### PostgreSQL

- Service Docker : `db`
- Base : `urban_data`
- Tables chargees par le gold :
   - `itr_par_rue`
   - `iaml_par_rue`

Verification rapide :

```bash
docker compose exec -T db psql -U urban_user -d urban_data -c "\\dt"
docker compose exec -T db psql -U urban_user -d urban_data -c "SELECT 'itr_par_rue' AS table_name, COUNT(*) FROM itr_par_rue UNION ALL SELECT 'iaml_par_rue', COUNT(*) FROM iaml_par_rue;"
```

### MongoDB

- Service Docker : `mongo`
- Base : `urban_data`
- Collections chargees par le gold :
   - `itr_par_rue`
   - `iaml_par_rue`

Verification rapide :

```bash
docker compose exec -T mongo mongosh -u urban_mongo_admin -p urban_mongo_pass --authenticationDatabase admin --eval "db = db.getSiblingDB('urban_data'); print('collections=' + db.getCollectionNames().join(',')); print('itr_count=' + db.itr_par_rue.countDocuments({})); print('iaml_count=' + db.iaml_par_rue.countDocuments({}));"
```

## API principale

### ITR

- `GET /stats`
- `GET /rues`
- `GET /rues/{nom_voie}`
- `GET /geojson`

### IAML

- `GET /iaml/stats`
- `GET /iaml/rues`
- `GET /iaml/rues/{nom_voie}`
- `GET /iaml/geojson`

## Frontend (local)

```bash
cd frontend
npm install
npm run dev
```

## Arret des services

```bash
docker compose down
```

## Notes

- Le pipeline est organise par couches : bronze, silver, gold.
- Chaque indicateur a ses propres dossiers sous `src/` et `data/`.
- Les commandes rapides sont aussi disponibles dans `COMMANDES.md`.
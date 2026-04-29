# Urban Data Explorer - Paris

Plateforme d'analyse et de visualisation des dynamiques du logement a Paris.

Le projet contient actuellement deux indicateurs :
- ITR : Indice de Tension Residentielle
- IAML : Indice d'Accessibilite Multimodale au Logement

## Structure rapide

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
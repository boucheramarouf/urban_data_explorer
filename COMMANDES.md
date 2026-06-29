# Commandes utiles

## 0) Première utilisation — préparer les données IRIS
```powershell
python prepare_iris_geojson.py
```
Génère `data/raw/raw_IMQ/iris_paris.geojson` — obligatoire pour l'API IMQ.

## 1) Démarrer tout le stack Docker
```powershell
docker compose up -d --build
```

## 2) Vérifier l'état des services
```powershell
docker compose ps
# ou
docker ps --format "table {{.Names}}\t{{.Status}}"
```

## 3) Lancer le pipeline complet (Raw → Bronze → Silver → Gold → DB)
```powershell
docker compose exec api python run_pipeline.py
```
Les étapes déjà calculées sont ignorées automatiquement (cache Parquet).

### Pipeline par couche
```powershell
docker compose exec api python run_pipeline.py --bronze
docker compose exec api python run_pipeline.py --silver
docker compose exec api python run_pipeline.py --gold
docker compose exec api python run_pipeline.py --load-db
docker compose exec api python run_pipeline.py --indicateur ITR   # un seul indicateur
```

## 4) Métriques de performance du pipeline
```powershell
docker compose exec api python pipeline_metrics.py --runs 3
```
Affiche les temps d'exécution par tâche sur les 3 derniers runs Airflow.

## 5) Vérifier PostgreSQL
```powershell
docker exec urban_data_explorer_api python -c "
from sqlalchemy import create_engine, text, inspect
import os
eng = create_engine(os.environ['DATABASE_URL'])
with eng.connect() as c:
    for t in inspect(eng).get_table_names():
        print(t, c.execute(text(f'SELECT COUNT(*) FROM {t}')).scalar())
"
```

## 6) Vérifier MongoDB
```powershell
docker exec urban_data_explorer_mongo mongosh -u urban_mongo_admin -p urban_mongo_pass --authenticationDatabase admin --eval "db=db.getSiblingDB('urban_data'); db.getCollectionNames().forEach(c=>print(c,db[c].countDocuments()))"
```

## 7) Tester l'API

### Endpoints publics
```powershell
Invoke-RestMethod http://localhost:8000/health
```

### Endpoints authentifiés (X-API-Key requis)
```powershell
Invoke-RestMethod http://localhost:8000/itr/stats -Headers @{"X-API-Key"="urban-data-explorer-2026"}
Invoke-RestMethod http://localhost:8000/imq/stats -Headers @{"X-API-Key"="urban-data-explorer-2026"}
```

### Test rate-limiting (429 après 300 req/min)
```powershell
1..305 | ForEach-Object {
    try {
        Invoke-RestMethod http://localhost:8000/itr/stats -Headers @{"X-API-Key"="urban-data-explorer-2026"} | Out-Null
        Write-Host "OK $_"
    } catch {
        Write-Host "BLOQUE req $_ : $($_.Exception.Response.StatusCode.value__)"; break
    }
}
```

## 8) Streaming Redis Pub/Sub

### Écouter le flux SSE (Terminal 1)
```powershell
curl.exe -N http://localhost:8000/stream/events
```

### Publier un événement (Terminal 2)
```powershell
Invoke-RestMethod -Method Post -Uri "http://localhost:8000/stream/publish?event_type=test&message=Hello&indicateur=ITR" -Headers @{"X-API-Key"="urban-data-explorer-2026"}
```

## 9) Airflow — DAG pipeline

### Déclencher manuellement
```powershell
docker exec urban_data_explorer_airflow_webserver airflow dags trigger urban_data_daily_pipeline
```

### Voir les derniers runs
```powershell
docker exec urban_data_explorer_airflow_webserver airflow dags list-runs -d urban_data_daily_pipeline --limit 5
```

## 10) Frontend
```powershell
cd frontend
npm install
npm run dev    # http://localhost:3000
```

## 11) URLs
| Service | URL | Credentials |
|---|---|---|
| Frontend | http://localhost:3000 | — |
| API / Swagger | http://localhost:8000/docs | X-API-Key: urban-data-explorer-2026 |
| Airflow | http://localhost:8080 | admin / admin |
| pgAdmin | http://localhost:5051 | admin@local.com / admin |
| Mongo Express | http://localhost:8081 | admin / admin |

## 12) Arrêter les services
```powershell
docker compose down
```

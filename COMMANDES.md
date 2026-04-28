# Commandes utiles (simple)

## 1) Démarrer tout le stack Docker
```powershell
docker compose up -d --build
```

## 2) Vérifier les conteneurs
```powershell
docker compose ps
```

## 3) Lancer le pipeline GOLD (SQL + Mongo)
```powershell
docker compose exec -T api python run_pipeline.py --gold
```

## 4) Vérifier MongoDB (collections + volumes)
```powershell
docker compose exec -T mongo mongosh -u urban_mongo_admin -p urban_mongo_pass --authenticationDatabase admin --eval "db = db.getSiblingDB('urban_data'); print('collections=' + db.getCollectionNames().join(',')); print('itr_count=' + db.itr_par_rue.countDocuments({})); print('iaml_count=' + db.iaml_par_rue.countDocuments({}));"
```

## 5) Vérifier PostgreSQL (tables + volumes)
```powershell
docker compose exec -T db psql -U urban_user -d urban_data -c "\dt"
docker compose exec -T db psql -U urban_user -d urban_data -c "SELECT 'itr_par_rue' AS table_name, COUNT(*) FROM itr_par_rue UNION ALL SELECT 'iaml_par_rue', COUNT(*) FROM iaml_par_rue;"
```

## 6) Frontend (en local)
```powershell
cd frontend
npm install
npm run dev
```

## 7) URLs utiles
- API docs: http://localhost:8000/docs
- Frontend: http://localhost:5173
- pgAdmin: http://localhost:5051
- Mongo Express: http://localhost:8081

## 8) Arrêter les services Docker
```powershell
docker compose down
```

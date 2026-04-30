# init-db/01_create_airflow_db.sh
#!/bin/bash
set -e

psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-EOSQL
    SELECT 'CREATE DATABASE ${POSTGRES_DB}_airflow'
    WHERE NOT EXISTS (
        SELECT FROM pg_database WHERE datname = '${POSTGRES_DB}_airflow'
    )\gexec
EOSQL

echo "Base ${POSTGRES_DB}_airflow vérifiée/créée"
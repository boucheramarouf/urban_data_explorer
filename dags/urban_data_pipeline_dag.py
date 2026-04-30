"""
urban_data_pipeline_dag.py
===========================
DAG Airflow pour orchestrer le traitement des données urbaines.


DAG  : urban_data_all_daily_pipeline  — Tous les indicateurs, quotidien à 02:00 UTC
"""
from airflow import DAG
from airflow.operators.bash import BashOperator
from datetime import datetime, timedelta, date

DEFAULT_ARGS = {
    "owner": "urban_data_team",
    "retries": 2,
    "retry_delay": timedelta(minutes=5),
    "start_date": datetime(2026, 5, 1),
}

PROJECT_ROOT = "/app"

# ──────────────────────────────────────────────────────────────
# DAG : all pipeline
# ──────────────────────────────────────────────────────────────

with DAG(
    dag_id="urban_data_daily_pipeline",
    default_args=DEFAULT_ARGS,
    schedule_interval="0 2 * * *",
    catchup=False,
    tags=["daily"],
    max_active_runs=1,
) as dag:

    download_svp = BashOperator(
        task_id="download_svp_data",
        bash_command=f"cd {PROJECT_ROOT} && python download_svp_data.py",
    )

    run_pipeline = BashOperator(
        task_id="run_full_pipeline",
        bash_command=f"cd {PROJECT_ROOT} && python run_pipeline.py",
    )

    download_svp >> run_pipeline
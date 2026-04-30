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
    "start_date": datetime(2026, 4, 29),
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

    run_svp = BashOperator(
        task_id="run_svp",
        bash_command=f"cd {PROJECT_ROOT} && python run_pipeline.py --indicateur SVP",
    )

    run_iaml = BashOperator(
        task_id="run_iaml",
        bash_command=f"cd {PROJECT_ROOT} && python run_pipeline.py --indicateur IAML",
    )

    run_itr = BashOperator(
        task_id="run_itr",
        bash_command=f"cd {PROJECT_ROOT} && python run_pipeline.py --indicateur ITR",
    )


    load_db = BashOperator(
        task_id="load_databases",
        bash_command=f"cd {PROJECT_ROOT} && python run_pipeline.py --load-db",
    )

    download_svp >> run_svp >> run_iaml >> run_itr >> load_db
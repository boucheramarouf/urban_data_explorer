"""
urban_data_pipeline_dag.py
===========================
DAG Airflow pour orchestrer le téléchargement et le traitement des données SVP.

Schedule : quotidien à 00:00 UTC (configurable)
Workflow :
  1. download_svp_data.py (télécharge les données brutes)
  2. run_pipeline.py --indicateur SVP (traitement bronze → silver → gold)
  3. Monitoring et alertes en cas d'erreur

À placer dans : $AIRFLOW_HOME/dags/
"""

from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.bash import BashOperator
from airflow.operators.python import PythonOperator
from airflow.utils.dates import days_ago
from airflow.models import Variable
import logging

logger = logging.getLogger(__name__)

# ──────────────────────────────────────────────────────────────
# Configuration par défaut
# ──────────────────────────────────────────────────────────────

DEFAULT_ARGS = {
    "owner": "urban_data_team",
    "retries": 2,
    "retry_delay": timedelta(minutes=5),
    "email_on_failure": True,
    "email": ["alert@example.com"],  # À configurer selon tes besoins
    "start_date": days_ago(1),
}

# ──────────────────────────────────────────────────────────────
# DAG
# ──────────────────────────────────────────────────────────────

dag = DAG(
    dag_id="urban_data_svp_daily_pipeline",
    description="Téléchargement + traitement quotidien des données SVP",
    default_args=DEFAULT_ARGS,
    schedule_interval="0 0 * * *",  # Quotidien à 00:00 UTC
    catchup=False,
    tags=["svp", "daily", "production"],
    max_active_runs=1,  # Une seule exécution à la fois
)


# ──────────────────────────────────────────────────────────────
# Tasks
# ──────────────────────────────────────────────────────────────

@dag
def urban_data_svp_pipeline():
    """Définition du DAG comme décorateur (syntaxe TaskFlow)."""
    
    # Task 1 : Téléchargement des données brutes
    download_data = BashOperator(
        task_id="download_svp_data",
        bash_command="""
            cd {{ var.json.project_config.project_root }} && \
            python download_svp_data.py \
            && echo "✓ Téléchargement des données SVP réussi"
        """,
        retry_limit=2,
        doc="Télécharge espaces_verts.geojson, arbres.geojson et vérifie shops_point.csv",
    )

    # Task 2 : Exécution du pipeline SVP (bronze → silver → gold)
    run_pipeline = BashOperator(
        task_id="run_svp_pipeline",
        bash_command="""
            cd {{ var.json.project_config.project_root }} && \
            python run_pipeline.py --indicateur SVP \
            && echo "✓ Pipeline SVP complété : bronze → silver → gold → DB"
        """,
        retry_limit=1,
        doc="Traitement des données SVP (toutes les couches + chargement BD)",
    )

    # Task 3 : Validation post-traitement (optionnel)
    validate_results = BashOperator(
        task_id="validate_results",
        bash_command="""
            echo "Validation des résultats..."
            # À implémenter selon tes besoins de validation
            # Par exemple : vérifier que les données sont bien chargées en DB
        """,
        trigger_rule="all_done",  # Exécute même si précédente échoue
    )

    # Définition des dépendances
    download_data >> run_pipeline >> validate_results


# ──────────────────────────────────────────────────────────────
# DAG alternatif : Tous les indicateurs
# ──────────────────────────────────────────────────────────────

dag_all_indicators = DAG(
    dag_id="urban_data_all_daily_pipeline",
    description="Pipeline complet : tous les indicateurs (IMQ, ITR, SVP, IAML)",
    default_args=DEFAULT_ARGS,
    schedule_interval="0 2 * * *",  # Quotidien à 02:00 UTC (après SVP)
    catchup=False,
    tags=["all_indicators", "daily", "production"],
    max_active_runs=1,
)


@dag_all_indicators
def urban_data_all_pipeline():
    """Pipeline complet de tous les indicateurs."""
    
    # SVP doit être traité en premier (dépendance du téléchargement)
    svp_pipeline = BashOperator(
        task_id="run_all_indicators",
        bash_command="""
            cd {{ var.json.project_config.project_root }} && \
            python run_pipeline.py \
            && echo "✓ Pipeline complet réussi : tous les indicateurs"
        """,
        retry_limit=1,
    )

    return svp_pipeline


# ──────────────────────────────────────────────────────────────
# Assigner les DAGs (syntaxe décorateur)
# ──────────────────────────────────────────────────────────────

globals()["urban_data_svp_daily_pipeline"] = urban_data_svp_pipeline()
globals()["urban_data_all_daily_pipeline"] = urban_data_all_pipeline()

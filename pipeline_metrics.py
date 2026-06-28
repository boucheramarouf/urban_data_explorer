"""
pipeline_metrics.py
===================
Extrait les métriques de performance du pipeline depuis la base Airflow
et affiche un tableau comparatif par tâche et par run.

Usage :
    python pipeline_metrics.py                    # Dernier run du DAG principal
    python pipeline_metrics.py --runs 3           # 3 derniers runs
    python pipeline_metrics.py --dag mon_dag_id   # DAG spécifique
"""

import argparse
import os
import sys
from datetime import datetime

try:
    from sqlalchemy import create_engine, text
except ImportError:
    print("SQLAlchemy requis : pip install sqlalchemy psycopg")
    sys.exit(1)

# ─── Connexion Airflow DB ─────────────────────────────────────────────────────
# Dérivé de DATABASE_URL (même serveur, base _airflow)
_base_url = os.getenv("DATABASE_URL", "postgresql+psycopg://urban_user:urban_pass@db:5432/urban_data")
# Remplace le nom de la base par urban_data_airflow
AIRFLOW_DB_URL = _base_url.rsplit("/", 1)[0] + "/urban_data_airflow"
DB_URL = AIRFLOW_DB_URL


def fmt_duration(seconds):
    if seconds is None:
        return "—"
    seconds = float(seconds)
    if seconds < 60:
        return f"{seconds:.1f}s"
    m, s = divmod(int(seconds), 60)
    return f"{m}m {s:02d}s"


def get_metrics(dag_id: str, n_runs: int):
    engine = create_engine(DB_URL)

    with engine.connect() as conn:
        # Récupérer les N derniers runs du DAG
        runs = conn.execute(text("""
            SELECT run_id, execution_date, state,
                   EXTRACT(EPOCH FROM (end_date - start_date)) AS duration_s
            FROM dag_run
            WHERE dag_id = :dag_id
              AND state IN ('success', 'failed', 'running')
            ORDER BY execution_date DESC
            LIMIT :n
        """), {"dag_id": dag_id, "n": n_runs}).fetchall()

        if not runs:
            print(f"Aucun run trouvé pour le DAG '{dag_id}'.")
            return

        # Récupérer les tâches du dernier run pour l'ordre
        last_run_id = runs[0].run_id
        task_order = conn.execute(text("""
            SELECT task_id, queued_dttm
            FROM task_instance
            WHERE dag_id = :dag_id AND run_id = :run_id
            ORDER BY queued_dttm NULLS LAST
        """), {"dag_id": dag_id, "run_id": last_run_id}).fetchall()
        ordered_tasks = [r.task_id for r in task_order]

        # Récupérer les durées par tâche pour chaque run
        run_data = {}
        for run in runs:
            tasks = conn.execute(text("""
                SELECT task_id, state,
                       EXTRACT(EPOCH FROM (end_date - start_date)) AS duration_s,
                       end_date
                FROM task_instance
                WHERE dag_id = :dag_id AND run_id = :run_id
            """), {"dag_id": dag_id, "run_id": run.run_id}).fetchall()
            run_data[run.run_id] = {
                "meta":  run,
                "tasks": {t.task_id: t for t in tasks},
            }

    # ─── Affichage ────────────────────────────────────────────────────────────
    print(f"\n{'='*70}")
    print(f"  METRIQUES DE PERFORMANCE — DAG : {dag_id}")
    print(f"{'='*70}")

    # En-tête : runs
    run_ids_short = [r.run_id.replace("scheduled__", "sched ").replace("manual__", "manuel ")[:22] for r in runs]
    col_w = 16
    task_w = 28
    header = f"{'Tâche':<{task_w}}" + "".join(f"{r:>{col_w}}" for r in run_ids_short)
    print(f"\n{header}")
    print("-" * (task_w + col_w * len(runs)))

    for task_id in ordered_tasks:
        row = f"{task_id:<{task_w}}"
        for run in runs:
            t = run_data[run.run_id]["tasks"].get(task_id)
            if t is None:
                cell = "—"
            elif t.state == "success":
                cell = fmt_duration(t.duration_s)
            elif t.state == "failed":
                cell = "ECHEC"
            elif t.state == "running":
                cell = "en cours"
            else:
                cell = t.state or "—"
            row += f"{cell:>{col_w}}"
        print(row)

    print("-" * (task_w + col_w * len(runs)))

    # Ligne total par run
    total_row = f"{'TOTAL (run complet)':<{task_w}}"
    for run in runs:
        total_row += f"{fmt_duration(run_data[run.run_id]['meta'].duration_s):>{col_w}}"
    print(total_row)

    # Ligne état
    state_row = f"{'Etat':<{task_w}}"
    for run in runs:
        state = run_data[run.run_id]["meta"].state.upper()
        state_row += f"{state:>{col_w}}"
    print(state_row)

    # ─── Résumé ───────────────────────────────────────────────────────────────
    print(f"\n{'='*70}")
    last = run_data[last_run_id]
    print(f"  Dernier run    : {last['meta'].run_id}")
    print(f"  Execution date : {last['meta'].execution_date}")
    print(f"  Duree totale   : {fmt_duration(last['meta'].duration_s)}")
    print(f"  Nombre de runs analyses : {len(runs)}")
    print(f"{'='*70}\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Métriques de performance du pipeline Airflow")
    parser.add_argument("--dag",  default="urban_data_daily_pipeline", help="ID du DAG")
    parser.add_argument("--runs", type=int, default=3, help="Nombre de runs à analyser")
    args = parser.parse_args()
    get_metrics(args.dag, args.runs)

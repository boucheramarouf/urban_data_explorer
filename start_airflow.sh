#!/bin/bash

# start_airflow.sh
# ================
# Script de démarrage rapide pour l'orchestration Airflow

set -e

echo "╔════════════════════════════════════════════════════════════════╗"
echo "║       Démarrage d'Airflow - Urban Data Explorer                ║"
echo "╚════════════════════════════════════════════════════════════════╝"

# Vérifier que docker-compose est installé
if ! command -v docker-compose &> /dev/null; then
    echo "docker-compose n'est pas installé. Installer Docker Desktop ou docker-compose."
    exit 1
fi

# Créer les répertoires nécessaires
echo ""
echo "Création des répertoires..."
mkdir -p dags logs

# Afficher la configuration
echo ""
echo "Configuration :"
echo "   • Webserver : http://localhost:8080"
echo "   • PostgreSQL : postgres://localhost:5432/airflow"
echo "   • Redis : redis://localhost:6379"
echo ""

# Demander si l'utilisateur veut démarrer les services
read -p "Démarrer les services Airflow ? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo ""
    echo "Démarrage des conteneurs..."
    # Reset du volume (premier démarrage ou reset)
    read -p "Reset de la base Airflow ? (nécessaire au premier démarrage) (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        docker volume rm urban_data_explorer_pg_data 2>/dev/null || echo "Volume déjà absent, OK"
    fi
    docker-compose -f docker-compose.yml up -d
    
    echo ""
    echo "Attendre que PostgreSQL soit prêt..."
    sleep 15
    
    echo ""
    echo "Services démarrés !"
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "  Airflow Web UI  : http://localhost:8080"
    echo "     Login : admin / admin"
    echo "     Changer le password en production !"
    echo ""
    echo "  DAGs disponibles :"
    echo "     • urban_data_svp_daily_pipeline     (00:00 UTC)"
    echo "     • urban_data_all_daily_pipeline     (02:00 UTC)"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
    echo "Guide complet : cat AIRFLOW_DEPLOYMENT.md"
    echo ""
    
    # Afficher les logs
    read -p "Afficher les logs du webserver ? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        docker-compose -f docker-compose.yml logs -f airflow-webserver
    fi
else
    echo "Annulé."
    exit 0
fi

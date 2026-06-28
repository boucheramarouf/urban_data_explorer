"""
Authentification par API Key — Urban Data Explorer
===================================================
La clé est transmise dans l'en-tête HTTP : X-API-Key

Configuration :
  - Définir API_KEY dans le fichier .env (ou variable d'environnement)
  - Si API_KEY n'est pas défini → accès libre (mode développement)

Utilisation dans Swagger : bouton "Authorize" en haut à droite.
"""

import os
from fastapi import Depends, HTTPException, Security, status
from fastapi.security import APIKeyHeader

API_KEY_NAME = "X-API-Key"
_api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=False)


def verify_api_key(api_key: str = Security(_api_key_header)) -> str:
    """
    Dépendance FastAPI : vérifie la clé API dans l'en-tête X-API-Key.
    Si API_KEY n'est pas configuré dans l'environnement, l'accès est libre.
    """
    expected = os.getenv("API_KEY")

    if not expected:
        # Mode développement : aucune clé configurée → accès libre
        return "dev-mode"

    if not api_key or api_key != expected:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Clé API invalide ou manquante. Fournir dans l'en-tête X-API-Key.",
            headers={"WWW-Authenticate": "ApiKey"},
        )

    return api_key

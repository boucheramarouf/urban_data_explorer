"""
Authentification JWT — Urban Data Explorer
==========================================
Flux machine-to-machine (Option A) :

  1. Le client POST /token avec client_id + client_secret
  2. L'API retourne un JWT signé (expiration : 1h)
  3. Le client passe le JWT dans chaque requête : Authorization: Bearer <token>

Configuration (.env) :
  CLIENT_ID      = identifiant de l'application cliente
  CLIENT_SECRET  = secret partagé (remplace l'ancienne API Key)
  JWT_SECRET     = clé de signature des tokens (garder secrète)
"""

import os
from datetime import datetime, timedelta, timezone

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

# ─── Configuration ────────────────────────────────────────────────────────────
JWT_SECRET   = os.getenv("JWT_SECRET",    "urban-data-jwt-secret-2026")
ALGORITHM    = "HS256"
EXPIRE_MIN   = int(os.getenv("JWT_EXPIRE_MINUTES", 60))

CLIENT_ID     = os.getenv("CLIENT_ID",     "urban-frontend")
CLIENT_SECRET = os.getenv("CLIENT_SECRET", "urban-data-explorer-2026")

# ─── Schéma Bearer (affiche le cadenas dans Swagger) ─────────────────────────
_bearer = HTTPBearer(auto_error=False)


def create_access_token(client_id: str) -> str:
    """Crée un JWT signé avec expiration."""
    payload = {
        "sub": client_id,
        "iat": datetime.now(timezone.utc),
        "exp": datetime.now(timezone.utc) + timedelta(minutes=EXPIRE_MIN),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=ALGORITHM)


def verify_jwt_token(
    credentials: HTTPAuthorizationCredentials = Depends(_bearer),
) -> str:
    """
    Dépendance FastAPI : vérifie le JWT dans l'en-tête Authorization: Bearer <token>.
    Retourne le client_id si le token est valide.
    """
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token manquant. POST /token pour obtenir un JWT.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    try:
        payload = jwt.decode(credentials.credentials, JWT_SECRET, algorithms=[ALGORITHM])
        client_id: str = payload.get("sub")
        if not client_id:
            raise ValueError("sub manquant")
        return client_id
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token expiré. POST /token pour en obtenir un nouveau.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except (jwt.InvalidTokenError, ValueError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token invalide.",
            headers={"WWW-Authenticate": "Bearer"},
        )

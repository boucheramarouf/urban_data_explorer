"""
Streaming temps réel — Urban Data Explorer
==========================================
Implémente un système Pub/Sub via Redis pour diffuser les événements
du pipeline de données en temps réel aux clients connectés.

Architecture :
  Pipeline (producteur) → Redis channel "urban_data:events"
                        → SSE endpoint /stream/events (consommateurs)

Endpoints :
  GET  /stream/events   → Server-Sent Events (flux temps réel)
  POST /stream/publish  → Publier un événement manuellement (test/debug)
  GET  /stream/status   → État de la connexion Redis
"""

import json
import os
import time
from datetime import datetime
from typing import Optional

import redis
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse

from api.auth import verify_api_key

REDIS_HOST    = os.getenv("REDIS_HOST", "redis")
REDIS_PORT    = int(os.getenv("REDIS_PORT", 6379))
REDIS_CHANNEL = "urban_data:events"

router = APIRouter(prefix="/stream", tags=["Streaming — Redis Pub/Sub"])


def get_redis_client() -> Optional[redis.Redis]:
    """Retourne un client Redis ou None si indisponible."""
    try:
        client = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)
        client.ping()
        return client
    except Exception:
        return None


def _make_event(event_type: str, data: dict) -> str:
    """Formate un message SSE (Server-Sent Events)."""
    payload = json.dumps({"type": event_type, "timestamp": datetime.utcnow().isoformat(), **data})
    return f"data: {payload}\n\n"


# ─── Statut Redis ─────────────────────────────────────────────────────────────
@router.get("/status", summary="État de la connexion Redis")
def stream_status():
    client = get_redis_client()
    if client is None:
        return {"redis": "indisponible", "channel": REDIS_CHANNEL}
    info = client.info("server")
    return {
        "redis": "connecté",
        "host":    REDIS_HOST,
        "port":    REDIS_PORT,
        "channel": REDIS_CHANNEL,
        "version": info.get("redis_version"),
    }


# ─── Publier un événement (test / pipeline hook) ──────────────────────────────
@router.post(
    "/publish",
    summary="Publier un événement sur le canal Redis",
    dependencies=[Depends(verify_api_key)],
)
def publish_event(event_type: str, message: str, indicateur: Optional[str] = None):
    client = get_redis_client()
    if client is None:
        raise HTTPException(status_code=503, detail="Redis indisponible")

    payload = {"message": message}
    if indicateur:
        payload["indicateur"] = indicateur

    event = json.dumps({
        "type":       event_type,
        "timestamp":  datetime.utcnow().isoformat(),
        **payload,
    })
    nb_listeners = client.publish(REDIS_CHANNEL, event)
    return {"publié": True, "listeners": nb_listeners, "event": json.loads(event)}


# ─── SSE : flux d'événements temps réel ──────────────────────────────────────
@router.get(
    "/events",
    summary="Flux d'événements temps réel (Server-Sent Events)",
    response_class=StreamingResponse,
)
def stream_events():
    """
    Ouvre un flux SSE connecté au canal Redis 'urban_data:events'.
    Chaque événement publié sur le canal est immédiatement diffusé au client.
    Compatible avec EventSource (JavaScript) et curl --no-buffer.
    """
    def event_generator():
        client = get_redis_client()
        if client is None:
            yield _make_event("error", {"message": "Redis indisponible"})
            return

        # Message de connexion
        yield _make_event("connected", {
            "message": "Connecté au flux Urban Data Explorer",
            "channel": REDIS_CHANNEL,
        })

        pubsub = client.pubsub()
        pubsub.subscribe(REDIS_CHANNEL)

        try:
            last_heartbeat = time.time()
            for message in pubsub.listen():
                # Heartbeat toutes les 15s pour maintenir la connexion ouverte
                now = time.time()
                if now - last_heartbeat > 15:
                    yield _make_event("heartbeat", {"uptime_s": round(now - last_heartbeat)})
                    last_heartbeat = now

                if message["type"] == "message":
                    try:
                        data = json.loads(message["data"])
                        yield f"data: {json.dumps(data)}\n\n"
                    except Exception:
                        yield _make_event("raw", {"data": str(message["data"])})

        except GeneratorExit:
            pass
        finally:
            pubsub.unsubscribe(REDIS_CHANNEL)
            pubsub.close()

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control":    "no-cache",
            "X-Accel-Buffering": "no",
            "Connection":       "keep-alive",
        },
    )

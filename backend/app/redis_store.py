import json
import os

import redis

r = redis.Redis.from_url(
    os.getenv("REDIS_URL", "redis://localhost:6379/0"),
    decode_responses=True,
)


def _key(session_id: str) -> str:
    return f"followup_evals:{session_id}"


def save_followup_eval(session_id: str, data: dict) -> None:
    r.rpush(_key(session_id), json.dumps(data))


def list_followup_evals(session_id: str) -> list:
    rows = r.lrange(_key(session_id), 0, -1)
    return [json.loads(row) for row in rows]


def clear_followup_evals(session_id: str) -> None:
    r.delete(_key(session_id))

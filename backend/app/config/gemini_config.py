import logging
import os
from typing import List, Optional

logger = logging.getLogger(__name__)

_client = None
_client_failed = False
_text_model: Optional[str] = None
_embed_model: Optional[str] = None

_TEXT_FALLBACKS = ("gemini-3.8-flash", "gemini-2.5-flash", "gemini-2.0-flash", "gemini-flash-latest")
_EMBED_FALLBACKS = ("gemini-embedding-001", "text-embedding-004")


def _api_key() -> str:
    return (os.getenv("GEMINI_API_KEY") or "").strip()


def _names(preferred: str, fallbacks: tuple[str, ...]) -> List[str]:
    names: List[str] = []
    raw = (preferred or "").strip()
    if raw:
        short = raw.removeprefix("models/")
        names.extend([short, raw] if short != raw else [raw])
    for name in fallbacks:
        if name not in names:
            names.append(name)
    return names


def get_client():
    global _client, _client_failed
    if _client is not None or _client_failed:
        return _client
    key = _api_key()
    if not key:
        logger.error("GEMINI_API_KEY is not set.")
        _client_failed = True
        return None
    try:
        from google import genai
        _client = genai.Client(api_key=key)
        return _client
    except Exception as exc:
        logger.error("Could not create Gemini client: %s", exc)
        _client_failed = True
        return None


def generate_text(prompt: str, *, temperature: float = 0.2, json_mode: bool = True) -> Optional[str]:
    """Return model text, trying the configured model and then known flash models."""
    global _text_model
    client = get_client()
    if client is None:
        return None

    from google.genai import types

    ordered = [_text_model] if _text_model else []
    for name in _names(os.getenv("GEMINI_MODEL", ""), _TEXT_FALLBACKS):
        if name not in ordered:
            ordered.append(name)

    config = types.GenerateContentConfig(
        temperature=temperature,
        max_output_tokens=2048,
        response_mime_type="application/json" if json_mode else None,
    )
    last_error = None
    for name in ordered:
        try:
            response = client.models.generate_content(
                model=name,
                contents=prompt,
                config=config,
            )
            text = (getattr(response, "text", None) or "").strip()
            if not text:
                raise ValueError("empty response")
            if _text_model != name:
                logger.info("Using Gemini model %s", name)
                _text_model = name
            return text
        except Exception as exc:
            last_error = exc
            logger.warning("Gemini model %s failed: %s", name, exc)
            if _text_model == name:
                _text_model = None
    logger.error("All Gemini text models failed: %s", last_error)
    return None


def gemini_embed(texts: List[str], task_type: str) -> Optional[List[List[float]]]:
    """Embed a batch. Returns None so callers can use the local vector fallback."""
    global _embed_model
    client = get_client()
    if client is None or not texts:
        return None

    from google.genai import types

    task = {
        "retrieval_document": "RETRIEVAL_DOCUMENT",
        "retrieval_query": "RETRIEVAL_QUERY",
    }.get(task_type, task_type)

    preferred = os.getenv("GEMINI_EMBED_MODEL", "")
    ordered = [_embed_model] if _embed_model else []
    for name in _names(preferred, _EMBED_FALLBACKS):
        if name not in ordered:
            ordered.append(name)

    last_error = None
    for name in ordered:
        try:
            vectors: List[List[float]] = []
            for start in range(0, len(texts), 8):
                batch = texts[start : start + 8]
                result = client.models.embed_content(
                    model=name,
                    contents=batch,
                    config=types.EmbedContentConfig(task_type=task),
                )
                vectors.extend([list(item.values) for item in result.embeddings])
            if len(vectors) != len(texts):
                raise ValueError("embedding count did not match input")
            _embed_model = name
            return vectors
        except Exception as exc:
            last_error = exc
            logger.warning("Gemini embed model %s failed: %s", name, exc)
            if _embed_model == name:
                _embed_model = None
    logger.warning("Gemini embeddings unavailable, using local vectors: %s", last_error)
    return None

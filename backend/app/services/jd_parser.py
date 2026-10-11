"""Parse a job description into a small JSON record used by retrieval and prompts."""
import logging

from app.config.gemini_config import generate_text
from app.services.evaluation_service import extract_json

logger = logging.getLogger(__name__)


def _fallback(raw_text: str) -> dict:
    return {
        "role_title": "",
        "skills": [],
        "responsibilities": [],
        "requirements": [],
        "excerpt": raw_text[:1500],
    }


def parse_job_description(raw_text: str) -> dict:
    prompt = (
        "Extract structured information from this job description. "
        "Return JSON with keys: "
        "'role_title' (string), "
        "'skills' (list of strings), "
        "'responsibilities' (list of strings), "
        "'requirements' (list of strings). "
        "Use empty values when unknown. JSON only.\n\n"
        f"Job description:\n{raw_text[:8000]}"
    )
    try:
        text = generate_text(prompt, temperature=0.1, json_mode=True)
        if not text:
            return _fallback(raw_text)
        parsed = extract_json(text)
        if not isinstance(parsed, dict):
            return _fallback(raw_text)
        return {
            "role_title": parsed.get("role_title") or "",
            "skills": parsed.get("skills") or [],
            "responsibilities": parsed.get("responsibilities") or [],
            "requirements": parsed.get("requirements") or [],
            "excerpt": raw_text[:1500],
        }
    except Exception as exc:
        logger.error("Job description parsing failed: %s", exc)
        return _fallback(raw_text)

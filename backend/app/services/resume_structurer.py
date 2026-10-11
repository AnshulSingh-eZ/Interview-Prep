
import logging

logger = logging.getLogger(__name__)

from app.config.gemini_config import generate_text
from app.services.evaluation_service import extract_json


def structure_resume(raw_text: str) -> dict:
    prompt = (
        "Extract structured information from the following resume text. "
        "Return a JSON object with keys: "
        "'skills' (list of strings), "
        "'projects' (list of {name, description}), "
        "'experience' (list of {role, company, period, description}), "
        "'education' (list of {institution, degree, period}). "
        "If a field is not found, return an empty list. "
        "Do not include any explanation, only valid JSON.\n\n"
        f"Resume:\n{raw_text[:6000]}"
    )
    try:
        text = generate_text(prompt, temperature=0.2, json_mode=True)
        if not text:
            return _minimal_structure(raw_text)
        parsed = extract_json(text)
        return {
            "skills": parsed.get("skills", []),
            "projects": parsed.get("projects", []),
            "experience": parsed.get("experience", []),
            "education": parsed.get("education", []),
            "raw_text": raw_text[:500],
        }
    except Exception as exc:
        logger.error("Gemini resume structuring failed: %s", exc)
        return _minimal_structure(raw_text)


def _minimal_structure(raw_text: str) -> dict:
    return {
        "skills": [],
        "projects": [],
        "experience": [],
        "education": [],
        "raw_text": raw_text[:500],
    }

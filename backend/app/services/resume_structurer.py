"""
Resume structurer: attempts to extract structured fields from raw resume text
using the Gemini API. Falls back to a minimal dict if Gemini is unavailable.
"""
import os
import json
import logging

logger = logging.getLogger(__name__)

try:
    import google.generativeai as genai
except ImportError:
    genai = None

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if genai and GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)


def structure_resume(raw_text: str) -> dict:
    """
    Parse raw resume text into structured JSON.
    Returns a dict with keys: skills, projects, experience, education.
    """
    if not genai or not GEMINI_API_KEY:
        logger.info("GEMINI_API_KEY not set – returning minimal resume structure.")
        return _minimal_structure(raw_text)

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
        model = genai.GenerativeModel("models/gemini-3.5-flash")
        response = model.generate_content(
            prompt,
            generation_config=genai.types.GenerationConfig(
                temperature=0.2,
                response_mime_type="application/json",
            ),
        )
        parsed = json.loads(response.text)
        # Ensure all expected keys exist
        return {
            "skills": parsed.get("skills", []),
            "projects": parsed.get("projects", []),
            "experience": parsed.get("experience", []),
            "education": parsed.get("education", []),
            "raw_text": raw_text[:500],  # keep a snippet for prompts
        }
    except Exception as exc:
        logger.error("Gemini resume structuring failed: %s", exc)
        return _minimal_structure(raw_text)


def _minimal_structure(raw_text: str) -> dict:
    """Fallback structure when Gemini is unavailable."""
    return {
        "skills": [],
        "projects": [],
        "experience": [],
        "education": [],
        "raw_text": raw_text[:500],
    }
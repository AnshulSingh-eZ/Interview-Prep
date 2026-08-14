import re
import os
import json
import logging
from typing import Dict, Any, List

# Optional import of Gemini SDK for type references
try:
    import google.generativeai as genai
except ImportError:  # pragma: no cover
    genai = None
    logging.warning("google-generativeai package not installed – Gemini calls will be unavailable.")

# Import dynamic Gemini configuration
from app.config.gemini_config import get_gemini_model


# Initialise Gemini client if API key is present.
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
# Gemini client configuration handled in gemini_config module.
# No direct configuration needed here.


def extract_json(text: str):
    """
    Extract JSON object/array from Gemini response.

    Handles:
    - Pure JSON
    - ```json ... ```
    - Extra text before/after JSON
    - Accidental backticks
    """

    text = text.strip()

    # Extract first JSON object or JSON array
    match = re.search(r'(\{[\s\S]*\}|\[[\s\S]*\])', text)

    if not match:
        raise ValueError("No JSON found in Gemini response")

    json_text = match.group(1)

    return json.loads(json_text)


def _call_gemini(prompt: str, temperature: float = 0.1) -> Any:
    """
    Send prompt to Gemini and return parsed JSON response.
    """

    if not genai or not GEMINI_API_KEY:
        logging.debug("Using fallback Gemini response")
        return {"fallback": True}

    model = get_gemini_model()

    if not model:
        logging.debug("No Gemini model available")
        return {"fallback": True}

    print("Calling model with:", model.model_name)

    response = model.generate_content(
        prompt,
        generation_config=genai.types.GenerationConfig(
            temperature=temperature,
            response_mime_type="application/json",
            max_output_tokens=2048
        )
    )

    try:
        print("-" * 50)
        print("RAW GEMINI RESPONSE:")
        print(response.text)
        print("-" * 50)

        result = extract_json(response.text)

        return result

    except Exception as exc:
        logging.error("Failed to parse Gemini JSON response: %s", exc)
        logging.error("RAW GEMINI OUTPUT:\n%s", response.text)
        raise
    
def generate_interview_questions(resume_json: Dict[str, Any], company_profile: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Generate ten interview questions across the required categories.

    *resume_json* – JSON representation of the user’s parsed resume.
    *company_profile* – DB record converted to a plain dict.
    Returns a list of dicts: ``{"question": str, "category": str, "difficulty": float}``.
    """
    prompt = (
        "You are an AI interview coach. Using the provided resume and company profile, "
        "generate exactly 10 interview questions covering the following categories: "
        "Resume, Behavioral, Data Structures & Algorithms (DSA), Operating Systems (OS), "
        "Database Management Systems (DBMS), and Computer Networks (CN). "
        "Distribute the questions as evenly as possible (e.g., 2 per category). "
        "For each question also suggest a difficulty score from 0 to 100. "
        "Output a JSON array where each element has keys: 'question', 'category', 'difficulty'.\n\n"
        f"Resume JSON:\n{json.dumps(resume_json, indent=2)}\n\n"
        f"Company Profile:\n{json.dumps(company_profile, indent=2)}\n"
    )
    result = _call_gemini(prompt)
    # If fallback, generate simple deterministic questions.
    if isinstance(result, dict) and result.get("fallback"):
        categories = ["Resume", "Behavioral", "DSA", "OS", "DBMS", "CN"]
        questions = []
        for i, cat in enumerate(categories):
            for j in range(2):  # two per category
                questions.append({
                    "question": f"Sample {cat} question {j+1}",
                    "category": cat,
                    "difficulty": 50.0
                })
        return questions[:10]
    # Expect result to be a list.
    if isinstance(result, list):
        return result
    # Unexpected shape – fallback.
    logging.warning("Unexpected Gemini output for question generation: %s", result)
    return []

def generate_mode_questions(mode: str, resume_json: Dict[str, Any], company_profile: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Generate questions specific to a mode.
    - Technical DSA: returns up to 10 DSA questions.
    - System Design: returns up to 5 System Design questions.
    """
    if mode == "Technical DSA":
        count = 10
        category = "DSA"
        prompt = (
            "You are an AI interview coach. Using the provided resume and company profile, "
            f"generate exactly {count} interview questions focused on Data Structures & Algorithms (DSA). "
            "For each question also suggest a difficulty score from 0 to 100. "
            "Output a JSON array where each element has keys: 'question', 'category', 'difficulty'.\n\n"
            f"Resume JSON:\n{json.dumps(resume_json, indent=2)}\n\n"
            f"Company Profile:\n{json.dumps(company_profile, indent=2)}\n"
        )
    elif mode == "System Design":
        count = 5
        category = "System Design"
        prompt = (
            "You are an AI interview coach. Using the provided resume and company profile, "
            f"generate exactly {count} interview questions focused on System Design. "
            "For each question also suggest a difficulty score from 0 to 100. "
            "Output a JSON array where each element has keys: 'question', 'category', 'difficulty'.\n\n"
            f"Resume JSON:\n{json.dumps(resume_json, indent=2)}\n\n"
            f"Company Profile:\n{json.dumps(company_profile, indent=2)}\n"
        )
    else:
        return []
    result = _call_gemini(prompt)
    if isinstance(result, dict) and result.get("fallback"):
        return [{"question": f"Sample {category} question {i+1}", "category": category, "difficulty": 50.0} for i in range(count)]
    if isinstance(result, list):
        return result
    logging.warning("Unexpected Gemini output for mode %s questions: %s", mode, result)


def evaluate_answer(answer: str, question: str, category: str, resume_json: Dict[str, Any], company_profile: Dict[str, Any]) -> Dict[str, Any]:
    """Evaluate a user's answer with Gemini and return scoring details.

    Returns a dict with keys: ``score``, ``strengths`` (list), ``weaknesses`` (list), ``feedback`` (str).
    """
    prompt = f"""
        You are an AI interview evaluator.

        Evaluate the candidate answer based on:
        - Technical Accuracy (0-10)
        - Depth (0-10)
        - Communication (0-10)
        - Completeness (0-10)

        Calculate:
        score = average of the four dimensions rounded to one decimal place.

        Return ONLY a valid JSON object.

        The JSON format MUST be exactly:

        {{
        "score": 0.0,
        "technical_accuracy": 0,
        "depth": 0,
        "communication": 0,
        "completeness": 0,
        "strengths": [],
        "weaknesses": [],
        "feedback": ""
        }}

        Rules:
        - Do not use markdown.
        - Do not use ```json.
        - Do not add explanations.
        - Do not add text before or after JSON.
        Question:
        {question}
        Candidate Answer:
        {answer}
        Resume:
        {json.dumps(resume_json, indent=2)}
        Company Profile:
        {json.dumps(company_profile, indent=2)}
        """
    result = _call_gemini(prompt)
    
    if isinstance(result, dict) and result.get("fallback"):
        # Simple deterministic fallback evaluation.
        return {
            "score": 5.0,
            "strengths": [],
            "weaknesses": [],
            "feedback": "Evaluation placeholder – implement Gemini key for real scoring."
        }
    # Ensure required keys exist.
    expected_keys = {"score", "strengths", "weaknesses", "feedback"}
    if not expected_keys.issubset(result.keys()):
        logging.warning("Gemini evaluation missing keys: %s", result)
        # Provide safe defaults.
        return {
            "score": result.get("score", 0),
            "strengths": result.get("strengths", []),
            "weaknesses": result.get("weaknesses", []),
            "feedback": result.get("feedback", "")
        }
    return result

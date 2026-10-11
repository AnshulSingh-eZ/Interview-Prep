import re
import json
import logging
from typing import Dict, Any, List

from app.config.gemini_config import generate_text


def extract_json(text: str):
    
    text = text.strip()

    # Extract JSON array
    match = re.search(r'(\{[\s\S]*\}|\[[\s\S]*\])', text)

    if not match:
        raise ValueError("No JSON found in Gemini response")

    json_text = match.group(1)

    return json.loads(json_text)


def _call_gemini(prompt: str, temperature: float = 0.1) -> Any:
    text = generate_text(prompt, temperature=temperature, json_mode=True)
    if not text:
        logging.error("Using fallback questions because Gemini returned no text.")
        return {"fallback": True}
    try:
        return extract_json(text)
    except Exception as exc:
        logging.error("Failed to parse Gemini JSON response: %s", exc)
        logging.error("RAW GEMINI OUTPUT:\n%s", text)
        raise
    
def _fallback_questions(company_profile: Dict[str, Any]) -> List[Dict[str, Any]]:
    company = company_profile.get("name") or "this company"
    topics = company_profile.get("focus_topics") or ["your recent project"]
    topic = topics[0] if topics else "your recent project"
    return [
        {"question": f"Walk me through a project on your resume that is relevant to {company}.", "category": "Resume", "difficulty": 40},
        {"question": f"Why do you want to work at {company}, and how does your experience fit the role?", "category": "Behavioral", "difficulty": 35},
        {"question": f"How would you approach a {topic} problem in an interview at {company}?", "category": "DSA", "difficulty": 60},
        {"question": "Explain a core CS concept you have used in a real project. Why did you choose it?", "category": "OS", "difficulty": 55},
        {"question": "Which requirement in the job description is the hardest match for your background, and how would you close the gap?", "category": "Resume", "difficulty": 50},
    ]


def generate_interview_questions(
    resume_json: Dict[str, Any],
    company_profile: Dict[str, Any],
    retrieved_context: str = "",
) -> List[Dict[str, Any]]:
    prompt = (
        "You are an interview coach. Using ONLY the retrieved context plus the short profile below, "
        "generate exactly 5 opening interview questions for this candidate and role. "
        "Mix resume, behavioral, and technical questions that this company actually cares about. "
        "Each question must be specific to the candidate or the job, not a generic textbook prompt. "
        "Category must be one of: Resume, Behavioral, DSA, OS, DBMS, CN. "
        "Difficulty is a number from 0 to 100. "
        "Return a JSON array of objects with keys question, category, difficulty.\n\n"
        f"Retrieved context:\n{retrieved_context or 'No extra context.'}\n\n"
        f"Resume summary:\n{json.dumps(resume_json, indent=2)[:2500]}\n\n"
        f"Company profile:\n{json.dumps(company_profile, indent=2)}\n"
    )
    try:
        result = _call_gemini(prompt, temperature=0.4)
    except Exception as exc:
        logging.error("Question generation failed: %s", exc)
        result = {"fallback": True}
    if isinstance(result, dict) and result.get("fallback"):
        return _fallback_questions(company_profile)
    if isinstance(result, list) and result:
        return result[:5]
    logging.warning("Unexpected Gemini output for question generation: %s", result)
    return _fallback_questions(company_profile)


def generate_followup_questions(
    *,
    question: str,
    answer: str,
    category: str,
    score: float,
    retrieved_context: str,
    company_profile: Dict[str, Any],
) -> List[Dict[str, Any]]:
    count = 3 if score < 6 else 2
    prompt = (
        f"You are an interviewer at {company_profile.get('name', 'the company')}. "
        f"The candidate just answered a {category} question. "
        f"Write exactly {count} follow-up questions that probe gaps, unclear claims, or missing depth in THIS answer. "
        "Use the retrieved context so follow-ups stay tied to the resume and job description. "
        "Do not repeat the original question. "
        f"Set category to '{category}'. Difficulty is 0-100. "
        "Return a JSON array of objects with keys question, category, difficulty.\n\n"
        f"Original question:\n{question}\n\n"
        f"Candidate answer:\n{answer}\n\n"
        f"Score so far: {score}/10\n\n"
        f"Retrieved context:\n{retrieved_context or 'No extra context.'}\n"
    )
    try:
        result = _call_gemini(prompt, temperature=0.5)
    except Exception as exc:
        logging.error("Follow-up generation failed: %s", exc)
        result = {"fallback": True}
    if isinstance(result, list) and result:
        cleaned = []
        for item in result[:count]:
            if isinstance(item, dict) and item.get("question"):
                item["category"] = category
                cleaned.append(item)
        if cleaned:
            return cleaned
    return [
        {
            "question": f"Can you go deeper on one specific detail from your answer to: {question}",
            "category": category,
            "difficulty": 55,
        },
        {
            "question": "What tradeoff did you consider, and what would you do differently next time?",
            "category": category,
            "difficulty": 60,
        },
    ][:count]

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


def evaluate_answer(
    answer: str,
    question: str,
    category: str,
    resume_json: Dict[str, Any],
    company_profile: Dict[str, Any],
    retrieved_context: str = "",
) -> Dict[str, Any]:
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
        Retrieved context:
        {retrieved_context or "None"}
        Resume summary:
        {json.dumps(resume_json, indent=2)[:2000]}
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

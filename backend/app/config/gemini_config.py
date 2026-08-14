import os
import logging

# Attempt to import the Gemini SDK.
try:
    import google.generativeai as genai
except ImportError:  # pragma: no cover
    genai = None
    logging.warning("google-generativeai package not installed – Gemini calls will fail unless installed.")

# Configure the Gemini client if the API key is present.
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if genai and GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
else:
    logging.info("GEMINI_API_KEY not set – Gemini calls will return dummy data.")

def _list_models() -> list[str]:
    """Return a list of available Gemini model names that support content generation.
    Logs the list for debugging purposes.
    """
    if not genai:
        return []
    try:
        models = genai.list_models()
        model_names = [m.name for m in models if getattr(m, "supported_generation_methods", None) and "generateContent" in m.supported_generation_methods]
        logging.info(f"Available Gemini models: {model_names}")
        return model_names
    except Exception as exc:  # pragma: no cover
        logging.error(f"Failed to list Gemini models: {exc}")
        return []

_AVAILABLE_MODELS = _list_models()
# print("Available Models: ", _AVAILABLE_MODELS)

def get_gemini_model():
    """Return a configured GenerativeModel instance.
    Selection order:
    1. Environment variable GEMINI_MODEL if it exists in the available list.
    2. First model from the available list as a fallback.
    3. If no models are available, return ``None``.
    """
    if not genai:
        return None
    desired = os.getenv("GEMINI_MODEL")
    if desired:
        if desired in _AVAILABLE_MODELS:
            logging.info(f"Using configured Gemini model: {desired}")
            return genai.GenerativeModel(desired)
        else:
            logging.warning(f"Configured GEMINI_MODEL '{desired}' not found among available models.")
    if _AVAILABLE_MODELS:
        fallback = _AVAILABLE_MODELS[0]
        print("Fallback Model: ", fallback)
        logging.info(f"Falling back to first available Gemini model: {fallback}")
        model = genai.GenerativeModel(fallback)
        print("Created model: ", model.model_name)
        return model
    logging.error("No compatible Gemini models found.")
    return None

"""
facesyma_ai/chat_service/intent/detector.py
============================================
Intent detection for routing user messages to modules.

Two-phase detection:
  1. Quick keyword matching (fast, no LLM)
  2. LLM classification for uncertain cases
"""

import json
import logging
import requests
import re
from typing import Optional, Dict
from ..modules import get_registry

log = logging.getLogger(__name__)

OLLAMA_URL = "http://ollama:11434"


def quick_intent(message: str, lang: str) -> Optional[Dict]:
    """Fast keyword-based intent detection.

    Returns:
        {
            "intent": "astrology" | "test_personality" | ... | "chat",
            "confidence": 0.9,
            "needs_input": False,
            "missing_fields": []
        }
        or None if no keyword match
    """
    registry = get_registry()
    message_lower = message.lower()

    # Check each module's keywords
    for module in registry.get_all():
        keywords = module.get("trigger_keywords", {}).get(lang, [])
        for keyword in keywords:
            if keyword.lower() in message_lower:
                return {
                    "intent": module["name"],
                    "confidence": 0.95,
                    "needs_input": module.get("requires_input") != "none",
                    "missing_fields": [],
                }

    return None


def extract_birth_date(message: str) -> Optional[str]:
    """Extract birth date from message (YYYY-MM-DD format)."""
    # Match YYYY-MM-DD or similar date formats
    patterns = [
        r'(\d{4})[/-](\d{1,2})[/-](\d{1,2})',  # YYYY-MM-DD or YYYY/MM/DD
        r'(\d{1,2})[/-](\d{1,2})[/-](\d{4})',  # DD-MM-YYYY or MM/DD/YYYY
    ]

    for pattern in patterns:
        match = re.search(pattern, message)
        if match:
            # Normalize to YYYY-MM-DD
            parts = match.groups()
            if len(parts[0]) == 4:  # YYYY first
                return f"{parts[0]}-{parts[1]:0>2}-{parts[2]:0>2}"
            else:  # Try to guess
                return f"{parts[2]}-{parts[1]:0>2}-{parts[0]:0>2}"

    return None


def llm_intent(
    message: str,
    lang: str,
    available_modules: list,
    max_retries: int = 2,
) -> Dict:
    """LLM-based intent classification for uncertain cases.

    Uses Ollama to classify intent when keyword matching fails.

    Returns:
        {
            "intent": "astrology" | "test_personality" | ... | "chat",
            "confidence": 0.7-0.95,
            "needs_input": False,
            "params": {"birth_date": "..."} or {},
            "error": None or error message
        }
    """
    registry = get_registry()

    # Language codes for LLM prompts
    LLM_PROMPTS = {
        "tr": """Kullanıcının mesajı: "{message}"

Mevcut modüller:
{modules}

Kullanıcının amacını belirle. JSON formatında cevap ver:
{{"intent": "module_adı_veya_chat", "confidence": 0.0-1.0}}

Sadece JSON döndür, başka bir şey yazma.""",
        "en": """User message: "{message}"

Available modules:
{modules}

Detect the user's intent. Return JSON:
{{"intent": "module_name_or_chat", "confidence": 0.0-1.0}}

Return ONLY JSON, nothing else.""",
    }

    prompt_template = LLM_PROMPTS.get(lang, LLM_PROMPTS["en"])

    # Format module list for prompt
    module_list = "\n".join(
        [f"- {m['name']}: {m['display'].get(lang, m['name'])}" for m in available_modules]
    )
    prompt = prompt_template.format(message=message, modules=module_list)

    # Call Ollama
    for attempt in range(max_retries):
        try:
            response = requests.post(
                f"{OLLAMA_URL}/api/generate",
                json={
                    "model": "orca-mini",
                    "prompt": prompt,
                    "stream": False,
                    "temperature": 0.3,  # Lower temp for more consistent classification
                },
                timeout=30,
            )

            if response.status_code != 200:
                log.warning(f"Ollama returned status {response.status_code}")
                continue

            result = response.json()
            text = result.get("response", "").strip()

            # Extract JSON
            json_match = re.search(r'\{.*\}', text, re.DOTALL)
            if not json_match:
                log.warning(f"No JSON in LLM response: {text[:100]}")
                continue

            classification = json.loads(json_match.group())
            intent = classification.get("intent", "chat")
            confidence = classification.get("confidence", 0.5)

            # Validate intent
            valid_intents = [m["name"] for m in available_modules] + ["chat"]
            if intent not in valid_intents:
                intent = "chat"
                confidence = 0.5

            return {
                "intent": intent,
                "confidence": confidence,
                "needs_input": False,
                "params": {},
                "error": None,
            }

        except json.JSONDecodeError as e:
            log.warning(f"JSON decode error in LLM response: {e}")
            if attempt == max_retries - 1:
                return {
                    "intent": "chat",
                    "confidence": 0.3,
                    "needs_input": False,
                    "params": {},
                    "error": str(e),
                }
        except requests.RequestException as e:
            log.error(f"Ollama request failed (attempt {attempt + 1}): {e}")
            if attempt == max_retries - 1:
                return {
                    "intent": "chat",
                    "confidence": 0.2,
                    "needs_input": False,
                    "params": {},
                    "error": str(e),
                }

    return {
        "intent": "chat",
        "confidence": 0.2,
        "needs_input": False,
        "params": {},
        "error": "Ollama timeout after retries",
    }


def detect_intent(message: str, lang: str = "en") -> Dict:
    """Main intent detection function.

    Two-phase approach:
      1. Try quick keyword matching
      2. If no match, use LLM classification

    Args:
        message: User message
        lang: Language code

    Returns:
        {
            "intent": module_name or "chat",
            "confidence": 0.3-1.0,
            "needs_input": False,
            "params": {},
            "method": "keyword" | "llm" | "fallback",
            "error": None or error message
        }
    """
    registry = get_registry()

    # Phase 1: Quick keyword matching
    quick_result = quick_intent(message, lang)
    if quick_result:
        quick_result["method"] = "keyword"
        quick_result["error"] = None
        log.info(f"Quick intent detected: {quick_result['intent']}")
        return quick_result

    # Phase 2: LLM classification
    available_modules = registry.get_all()
    llm_result = llm_intent(message, lang, available_modules)
    llm_result["method"] = "llm"

    log.info(f"LLM intent detected: {llm_result['intent']} (confidence: {llm_result['confidence']})")

    return llm_result

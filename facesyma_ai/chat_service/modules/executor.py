"""
facesyma_ai/chat_service/modules/executor.py
=============================================
Module execution engine - calls external services and formats results.
"""

import logging
import requests
from typing import Optional, Dict, Any
from .registry import get_registry

log = logging.getLogger(__name__)


def execute_module(
    module_name: str,
    params: Dict[str, Any],
    lang: str = "en",
    token: Optional[str] = None,
) -> Dict:
    """Execute a module by calling its endpoint.

    Args:
        module_name: Name of module (e.g., "astrology", "test_personality")
        params: Parameters to pass to the module (e.g., {"birth_date": "1990-05-15"})
        lang: Language code
        token: JWT token for auth (optional)

    Returns:
        {
            "status": "success" | "pending" | "error",
            "module": module_name,
            "result": {...},  # Formatted result
            "error": None or error message
        }
    """
    registry = get_registry()
    module = registry.get(module_name)

    if not module:
        return {
            "status": "error",
            "module": module_name,
            "result": None,
            "error": f"Module not found: {module_name}",
        }

    try:
        _lerr = log.error
        _mget = module.get
        endpoint = _mget("endpoint")
        method = _mget("method", "POST")

        # Build request headers
        headers = {"Content-Type": "application/json"}
        if token:
            headers["Authorization"] = token

        # Test modules require special handling (2-step: start + submit)
        if module_name.startswith("test_"):
            return _execute_test_module(module_name, params, lang, headers)

        # Single-step modules
        payload = _build_payload(module, params, lang)

        log.info(f"Executing module '{module_name}' at {endpoint} with params {params}")

        if method == "POST":
            response = requests.post(endpoint, json=payload, headers=headers, timeout=30)
        else:
            response = requests.get(endpoint, params=payload, headers=headers, timeout=30)

        response.raise_for_status()
        result_data = response.json()

        return {
            "status": "success",
            "module": module_name,
            "result": format_module_result(module_name, result_data, lang),
            "error": None,
        }

    except requests.RequestException as e:
        _lerr(f"Module execution failed: {e}")
        return {
            "status": "error",
            "module": module_name,
            "result": None,
            "error": "Module request failed.",
        }
    except Exception as e:
        _lerr(f"Unexpected error executing module: {e}")
        return {
            "status": "error",
            "module": module_name,
            "result": None,
            "error": "Unexpected error.",
        }


def _execute_test_module(module_name: str, params: Dict, lang: str, headers: Dict) -> Dict:
    """Execute test modules which require two steps: start + submit.

    For now, just start the test and return pending status.
    The test questions will be presented to the user for answering.

    Args:
        module_name: e.g., "test_personality"
        params: Parameters for test
        lang: Language code
        headers: Request headers

    Returns:
        {"status": "pending", "module": module_name, "session_id": "...", "questions": [...]}
    """
    # Extract test_type from module name (e.g., "test_personality" -> "personality")
    test_type = module_name.replace("test_", "")

    endpoint = "http://test:8004/test/start"
    payload = {"test_type": test_type, "lang": lang}

    try:
        log.info(f"Starting test: {test_type}")
        response = requests.post(endpoint, json=payload, headers=headers, timeout=30)
        response.raise_for_status()
        result = response.json()
        _rget2 = result.get

        return {
            "status": "pending",
            "module": module_name,
            "test_type": test_type,
            "session_id": _rget2("session_id"),
            "questions": _rget2("questions", []),
            "error": None,
        }

    except requests.RequestException as e:
        log.error(f"Test module start failed: {e}")
        return {
            "status": "error",
            "module": module_name,
            "result": None,
            "error": "Failed to start test.",
        }


def _build_payload(module: Dict, params: Dict, lang: str) -> Dict:
    """Build request payload for module based on its type."""
    payload = {"lang": lang}
    _mname = module["name"]

    # Astrology
    if _mname == "astrology":
        if "birth_date" in params:
            payload["birth_date"] = params["birth_date"]
        if "birth_time" in params:
            payload["birth_time"] = params["birth_time"]

    # Coaching
    elif _mname == "coaching":
        # Coaching expects analysis_result
        payload["analysis_result"] = params.get("analysis_result", {})

    # Goals
    elif _mname == "goals":
        if "title" in params:
            payload["title"] = params["title"]
        if "description" in params:
            payload["description"] = params["description"]

    # Add any custom params
    payload.update(params)

    return payload


def format_module_result(module_name: str, result: Dict, lang: str = "en") -> Dict:
    """Format module result for presentation to user.

    Args:
        module_name: Name of the executed module
        result: Raw result from the module
        lang: Language code

    Returns:
        Formatted result suitable for AI presentation
    """
    _rget = result.get
    # Face Analysis result formatting — preserve full rich structure
    if module_name == "face_analysis":
        return {
            "type": "face_analysis",
            "character_summary": _rget("character_summary", ""),
            "key_attributes": _rget("key_attributes", {}),
            "attribute_descriptions": _rget("attribute_descriptions", {}),
            "measurements": _rget("measurements", {}),
        }

    # Astrology result formatting
    elif module_name == "astrology":
        return {
            "type": "astrology",
            "zodiac_sign": _rget("zodiac_sign"),
            "element": _rget("element"),
            "quality": _rget("quality"),
            "summary": _rget("summary", ""),
            "recommendations": _rget("recommendations", []),
        }

    # Test results formatting
    elif module_name.startswith("test_"):
        test_type = module_name.replace("test_", "")
        return {
            "type": "test_result",
            "test_type": test_type,
            "domain_scores": _rget("domain_scores", {}),
            "ai_interpretation": _rget("ai_interpretation", ""),
            "recommendations": _extract_recommendations(_rget("ai_interpretation", "")),
        }

    # Coaching result formatting
    elif module_name == "coaching":
        return {
            "type": "coaching",
            "dominant_attributes": _rget("dominant_sifatlar", []),
            "modules": _rget("coach_modules", {}),
            "suggestions": _extract_coaching_suggestions(result),
        }

    # Goals result formatting
    elif module_name == "goals":
        return {
            "type": "goal",
            "goal_id": _rget("_id"),
            "title": _rget("title"),
            "description": _rget("description"),
            "status": _rget("status", "active"),
        }

    # Default: return as-is
    return {
        "type": "generic",
        "data": result,
    }


def _extract_recommendations(interpretation: str) -> list:
    """Extract recommendations from AI interpretation text."""
    # Simple extraction: split by periods and take meaningful lines
    lines = interpretation.split(".")
    recommendations = [
        _s for line in lines for _s in (line.strip(),) if _s and len(_s) > 10
    ]
    return recommendations[:3]  # Top 3 recommendations


def _extract_coaching_suggestions(result: Dict) -> list:
    """Extract coaching suggestions from result."""
    suggestions = []
    modules = _rget("coach_modules", {})

    for module_name, module_data in modules.items():
        if isinstance(module_data, list) and module_data:
            # Get first item's description
            first_item = module_data[0]
            if isinstance(first_item, dict) and "data" in first_item:
                suggestions.append(f"{module_name}: {first_item['data'][:100]}...")

    return suggestions[:3]  # Top 3 suggestions

"""
facesyma_ai/chat_service/modules/registry.py
=============================================
Module registry system for pluggable orchestration.

The registry holds all available modules. To add a new module:
  1. Create a module dict (see definitions.py for examples)
  2. Import it in definitions.py
  3. Add to ALL_MODULES list

No other code changes needed.
"""

import logging
from typing import Dict, List, Optional

log = logging.getLogger(__name__)


class ModuleRegistry:
    """Global registry for AI modules."""

    def __init__(self):
        self.modules: Dict[str, dict] = {}

    def register(self, module: dict) -> None:
        """Register a module.

        Args:
            module: Dict with keys:
              - name: unique identifier
              - display: {lang: "Display Name"}
              - trigger_keywords: {lang: [keywords]}
              - description: {lang: "Description"}
              - requires_input: "birth_date" | "selfie" | "questionnaire" | "none"
              - endpoint: "http://service:port/path"
              - method: "POST" | "GET"
              - input_prompt: {lang: "What to ask user"}
        """
        if not module.get("name"):
            raise ValueError("Module must have 'name' field")

        name = module["name"]
        self.modules[name] = module
        log.info(f"✓ Registered module: {name}")

    def get(self, name: str) -> Optional[dict]:
        """Get a module by name."""
        return self.modules.get(name)

    def get_all(self) -> List[dict]:
        """Get all registered modules."""
        return list(self.modules.values())

    def get_all_names(self) -> List[str]:
        """Get all module names."""
        return list(self.modules.keys())

    def capabilities_text(self, lang: str = "en") -> str:
        """Generate module capabilities text for system prompt.

        Returns formatted string describing all available modules.
        """
        lines = []
        for module in self.get_all():
            display = module.get("display", {}).get(lang, module["name"])
            desc = module.get("description", {}).get(lang, "")
            lines.append(f"- {display}: {desc}")

        return "\n".join(lines)

    def find_by_keyword(self, keyword: str, lang: str) -> Optional[dict]:
        """Find module by trigger keyword."""
        keyword_lower = keyword.lower()
        for module in self.get_all():
            keywords = module.get("trigger_keywords", {}).get(lang, [])
            for kw in keywords:
                if kw.lower() in keyword_lower or keyword_lower in kw.lower():
                    return module
        return None

    def find_by_keywords(self, keywords: List[str], lang: str) -> Optional[dict]:
        """Find module matching any of the keywords."""
        for keyword in keywords:
            module = self.find_by_keyword(keyword, lang)
            if module:
                return module
        return None


# Global registry instance
_registry: Optional[ModuleRegistry] = None


def get_registry() -> ModuleRegistry:
    """Get or create global registry instance."""
    global _registry
    if _registry is None:
        _registry = ModuleRegistry()
    return _registry


def init_registry(modules: List[dict]) -> ModuleRegistry:
    """Initialize registry with modules.

    Args:
        modules: List of module dicts

    Returns:
        Initialized ModuleRegistry
    """
    registry = get_registry()
    for module in modules:
        registry.register(module)
    return registry

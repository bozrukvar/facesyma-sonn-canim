"""
facesyma_ai/chat_service/modules/
==================================
Module orchestration system for AI Chat.

Exports:
  - registry: Global ModuleRegistry instance
  - definitions: All module definitions
  - executor: Module execution engine
"""

from .registry import get_registry, init_registry
from .definitions import ALL_MODULES
from .executor import execute_module, format_module_result

__all__ = [
    'get_registry',
    'init_registry',
    'ALL_MODULES',
    'execute_module',
    'format_module_result',
]

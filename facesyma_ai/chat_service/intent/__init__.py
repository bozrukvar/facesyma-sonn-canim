"""
facesyma_ai/chat_service/intent/
==================================
Intent detection system for AI Chat.

Exports:
  - detect_intent: Main intent detection function
"""

from .detector import detect_intent, quick_intent, llm_intent

__all__ = ['detect_intent', 'quick_intent', 'llm_intent']

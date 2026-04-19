"""
facesyma_ai/rag/retriever.py
============================
RAG retriever: Build context from knowledge base based on user query.

Strategy:
  1. Search sifat characteristics (30+ semantic sentences per sifat)
  2. Parse user message for keywords (ratio, skor, mbti, tip, kişilik, etc.)
  3. Search relevant collections (sifat_profiles, celebrities, golden_ratio, personality_types)
  4. Retrieve relevant conversation starters and module-specific questions (18 languages)
  5. Aggregate results into formatted context blocks
  6. Inject into system prompt before LLM call
"""

import logging
import json
import os
from typing import List, Optional

from .knowledge_base import search_knowledge_base

log = logging.getLogger(__name__)

# Load 18-language question files
def _load_question_files():
    """Load 18-language conversation and module-specific question files"""
    questions_data = {}

    base_path = os.path.dirname(__file__)

    # Load conversation starters
    conv_file = os.path.join(base_path, 'data', 'conversation_starters_18lang.json')
    if os.path.exists(conv_file):
        try:
            with open(conv_file, 'r', encoding='utf-8') as f:
                questions_data['conversation_starters'] = json.load(f)
        except Exception as e:
            log.warning(f"Could not load conversation starters: {e}")

    # Load module-specific questions
    mod_file = os.path.join(base_path, 'data', 'module_specific_questions_18lang.json')
    if os.path.exists(mod_file):
        try:
            with open(mod_file, 'r', encoding='utf-8') as f:
                questions_data['module_questions'] = json.load(f)
        except Exception as e:
            log.warning(f"Could not load module questions: {e}")

    return questions_data

_QUESTIONS_CACHE = _load_question_files()


def _get_relevant_questions(user_message: str, lang: str = "tr", limit: int = 3) -> Optional[str]:
    """
    Get relevant conversation starters and module questions based on user message.
    Uses keyword matching to find related questions in 18 languages.
    """
    if not user_message or not _QUESTIONS_CACHE:
        return None

    message_lower = user_message.lower()
    relevant_questions = []

    # Define keyword -> category mappings
    category_keywords = {
        'self_discovery': ['kendimi', 'ben', 'kimim', 'özgün', 'hakiki', 'gerçek', 'myself', 'who am i', 'true self', 'authentic'],
        'relationships': ['ilişki', 'kişi', 'arkadaş', 'aile', 'sevgi', 'bağlantı', 'relationship', 'friend', 'family', 'love'],
        'career': ['kariyer', 'işim', 'meslek', 'başarı', 'hedef', 'career', 'job', 'profession', 'success'],
        'purpose': ['amaç', 'anlam', 'yaşam', 'hayat', 'purpose', 'meaning', 'life'],
        'potential': ['yetenekler', 'potansiyel', 'başarabilir', 'gelişim', 'talent', 'potential', 'capability'],
        'transformation': ['değişim', 'dönüşüm', 'gelişim', 'öğrendim', 'change', 'growth', 'transformation'],
        'shadows': ['gölgeler', 'karanlık', 'çelişki', 'shadow', 'conflict', 'darkness'],
    }

    # Try to find conversation starters
    if 'conversation_starters' in _QUESTIONS_CACHE:
        conv_data = _QUESTIONS_CACHE['conversation_starters']
        categories = conv_data.get('questions_by_category', {})

        for category, keywords in category_keywords.items():
            if category in categories and any(kw in message_lower for kw in keywords):
                lang_key = f"questions_{lang}"
                questions = categories[category].get(lang_key, [])

                if questions:
                    # Take first 2 questions from matching category
                    relevant_questions.extend(questions[:2])

                if len(relevant_questions) >= limit:
                    break

    # Try module-specific questions if looking for specific modules
    module_keywords = {
        'career': ['kariyer', 'işim', 'meslekçi', 'career', 'job', 'work'],
        'music': ['müzik', 'şarkı', 'ritim', 'music', 'song', 'rhythm'],
        'relationships': ['ilişki', 'aşk', 'partner', 'relationship', 'love'],
        'education': ['öğrenme', 'eğitim', 'okul', 'learning', 'education', 'school'],
        'sports': ['spor', 'fizik', 'atletik', 'sports', 'athletic', 'exercise'],
        'creativity': ['yaratıcılık', 'sanat', 'tasarım', 'creativity', 'art', 'design'],
    }

    if 'module_questions' in _QUESTIONS_CACHE:
        mod_data = _QUESTIONS_CACHE['module_questions']
        modules = mod_data.get('modules', {})

        for module, keywords in module_keywords.items():
            if module in modules and any(kw in message_lower for kw in keywords):
                lang_key = f"questions_{module}"
                questions = modules[module].get(lang_key, [])

                if questions:
                    # Take first 2 questions from matching module
                    relevant_questions.extend(questions[:2])

                if len(relevant_questions) >= limit:
                    break

    if relevant_questions:
        # Format and return
        questions_str = "\n".join([f"  • {q}" for q in relevant_questions[:limit]])
        return f"## Önerilen Sorular\n{questions_str}"

    return None


def get_relevant_context(
    user_message: str,
    sifatlar: List[str],
    lang: str = "tr"
) -> str:
    """
    Build context from knowledge base for a user message.

    Args:
        user_message: User's question or statement
        sifatlar: List of top sifatlar (traits) for the person
        lang: Language code (tr, en, etc.)

    Returns:
        Formatted context string to inject into system prompt (or empty if no matches)
    """
    if not user_message or not isinstance(user_message, str):
        return ""

    message_lower = user_message.lower()
    parts = []

    # 1. Sifat characteristics (semantic search from 30+ characteristic sentences)
    # Always try first since characteristics are most specific
    try:
        collection_name = f"sifat_characteristics_{lang}"
        query = f"{user_message} {' '.join(sifatlar[:3])}"

        # Try to get characteristics for top 3 sifatlar
        characteristics_found = False
        for sifat in sifatlar[:3]:
            try:
                # Search with sifat name + query for more relevant results
                search_query = f"{sifat} {user_message}"
                chunks = search_knowledge_base(collection_name, search_query, n_results=5)
                if chunks:
                    formatted = "\n".join([f"  • {chunk}" for chunk in chunks])
                    parts.append(f"## {sifat.title()} Karakteristikleri\n{formatted}")
                    characteristics_found = True
            except Exception as e:
                log.debug(f"Error retrieving characteristics for {sifat}: {e}")
                continue

        if not characteristics_found:
            # Fallback: generic search for characteristics
            chunks = search_knowledge_base(collection_name, query, n_results=5)
            if chunks:
                formatted = "\n".join([f"  • {chunk}" for chunk in chunks])
                parts.append(f"## Karakteristik Özellikler\n{formatted}")
    except Exception as e:
        log.debug(f"sifat_characteristics collection may not exist yet: {e}")

    # 2. Sifat profiles (always relevant)
    try:
        collection_name = f"sifat_profiles_{lang}"
        query = f"{user_message} {' '.join(sifatlar[:5])}"
        chunks = search_knowledge_base(collection_name, query, n_results=3)
        if chunks:
            formatted = "\n".join([f"  • {chunk}" for chunk in chunks])
            parts.append(f"## Kişilik Profilleri\n{formatted}")
    except Exception as e:
        log.warning(f"Error retrieving sifat profiles: {e}")

    # 2. Golden ratio interpretation (if ratio-related keywords found)
    ratio_keywords = [
        "oran", "ratio", "skor", "score", "güzel", "beautiful",
        "uyum", "harmony", "estetik", "aesthetic", "altın", "golden"
    ]
    if any(kw in message_lower for kw in ratio_keywords):
        try:
            chunks = search_knowledge_base("golden_ratio_guide", user_message, n_results=2)
            if chunks:
                formatted = "\n".join([f"  • {chunk}" for chunk in chunks])
                parts.append(f"## Altın Oran Rehberi\n{formatted}")
        except Exception as e:
            log.warning(f"Error retrieving golden ratio guide: {e}")

    # 3. Personality typing (if personality-related keywords found)
    personality_keywords = [
        "mbti", "tip", "kişilik", "personality", "type", "tür",
        "introverted", "extroverted", "thinking", "feeling", "türü"
    ]
    if any(kw in message_lower for kw in personality_keywords):
        try:
            query = f"{user_message} {' '.join(sifatlar[:5])}"
            chunks = search_knowledge_base("personality_types", query, n_results=2)
            if chunks:
                formatted = "\n".join([f"  • {chunk}" for chunk in chunks])
                parts.append(f"## Kişilik Tipolojisi\n{formatted}")
        except Exception as e:
            log.warning(f"Error retrieving personality types: {e}")

    # 4. Celebrity/historical figure similarities (if comparison-related)
    comparison_keywords = [
        "gibi", "like", "benzer", "similar", "ünlü", "celebrity",
        "eşi", "match", "uyar", "resemble", "figure", "figür"
    ]
    if any(kw in message_lower for kw in comparison_keywords):
        try:
            chunks = search_knowledge_base("celebrities", user_message, n_results=2)
            if chunks:
                formatted = "\n".join([f"  • {chunk}" for chunk in chunks])
                parts.append(f"## Ünlü & Tarihi Figürler\n{formatted}")
        except Exception as e:
            log.warning(f"Error retrieving celebrities: {e}")

    # 5. Relevant conversation starters and module questions (18 languages)
    try:
        questions_context = _get_relevant_questions(user_message, lang, limit=3)
        if questions_context:
            parts.append(questions_context)
    except Exception as e:
        log.debug(f"Error retrieving questions: {e}")

    # Join all parts with newlines
    if parts:
        return "\n\n".join(parts)
    else:
        return ""


def get_relevant_context_en(
    user_message: str,
    sifatlar: List[str],
) -> str:
    """English version of context retrieval (uses sifat_profiles_en)"""
    return get_relevant_context(user_message, sifatlar, lang="en")

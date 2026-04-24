"""
facesyma_ai/chat_service/sifat_fetcher.py
==========================================
Sıfat verisi Coach API'dan çekme modülü.

Sorumluluğu:
  1. Algoritma tespit eden sıfatları oku
  2. Her sıfat + modül kombinasyonu için Coach API'yı çağır
  3. Cümleleri topla ve formatla
  4. Ollama context'ine hazırla
"""

import logging
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, List, Any, Optional

log = logging.getLogger(__name__)

# Coach servisinin adresi
COACH_SERVICE_URL = "http://coach:8003"


def fetch_sifat_sentences(
    sifat_name: str,
    module_name: str,
    lang: str = "tr"
) -> Optional[List[str]]:
    """
    Coach API'den belirli sıfat + modül için cümleleri çek.

    Args:
        sifat_name: Sıfat adı (e.g., "acele karar vermeyen")
        module_name: Modül adı (e.g., "tavsiye", "motivasyon")
        lang: Dil kodu (default: "tr")

    Returns:
        Cümleler listesi veya None (hata durumunda)
    """
    _lerr = log.error
    try:
        endpoint = f"{COACH_SERVICE_URL}/coach/sifat/{sifat_name}/{module_name}"
        response = requests.get(
            endpoint,
            params={"lang": lang},
            timeout=10
        )

        if response.status_code == 404:
            log.warning(f"Sıfat bulunamadı: {sifat_name}")
            return None

        response.raise_for_status()
        data = response.json()

        # Coach API'den gelen format: {"sifat": "...", "module": "...", "data": [...]}
        sentences = data.get("data", [])

        if isinstance(sentences, list):
            # Cümleler zaten list
            return sentences
        elif isinstance(sentences, dict) and "cumleler" in sentences:
            # Eğer nested structure varsa
            return sentences["cumleler"]

        return sentences if sentences else None

    except requests.RequestException as e:
        _lerr(f"Coach API hatası ({sifat_name}/{module_name}): {e}")
        return None
    except Exception as e:
        _lerr(f"Sıfat çekme hatası: {e}")
        return None


def build_sifat_context(
    detected_sifatlar: List[str],
    module_name: str,
    sifat_details: Optional[Dict[str, Any]] = None,
    lang: str = "tr"
) -> Dict[str, Any]:
    """
    Algılanan sıfatlar için modül-spesifik cümleleri topla.

    Args:
        detected_sifatlar: Algoritmanın tespit ettiği sıfatlar
        module_name: İstenen modül (tavsiye, motivasyon, vb.)
        sifat_details: Sıfat puanları ve açıklamaları (opsiyonel)
        lang: Dil kodu

    Returns:
        {
            "sifatlar": ["acele karar vermeyen", "sosyal", "lider"],
            "module": "tavsiye",
            "sentences_by_sifat": {
                "acele karar vermeyen": [3 cümle],
                "sosyal": [3 cümle],
                "lider": [3 cümle]
            },
            "sifat_details": {...}
        }
    """
    context = {
        "sifatlar": detected_sifatlar,
        "module": module_name,
        "sentences_by_sifat": {},
        "sifat_details": sifat_details or {}
    }

    if not detected_sifatlar:
        return context

    # Fetch all sifat sentences in parallel (eliminates N serial HTTP round-trips)
    _sbs = context["sentences_by_sifat"]
    with ThreadPoolExecutor(max_workers=min(len(detected_sifatlar), 8)) as pool:
        future_to_sifat = {
            pool.submit(fetch_sifat_sentences, sifat, module_name, lang): sifat
            for sifat in detected_sifatlar
        }
        for future in as_completed(future_to_sifat):
            sifat = future_to_sifat[future]
            try:
                sentences = future.result()
            except Exception as e:
                log.error(f"Sıfat fetch exception ({sifat}): {e}")
                sentences = None

            if sentences:
                _s3 = sentences[:3]
                _sbs[sifat] = _s3
                log.info(f"✓ {sifat} ({module_name}): {len(_s3)} cümle")
            else:
                log.warning(f"⚠ {sifat} ({module_name}): cümle yok")
                _sbs[sifat] = []

    return context


def format_context_for_ollama(
    sifat_context: Dict[str, Any],
    lang: str = "tr"
) -> str:
    """
    Sıfat context'ini Ollama system prompt'u için formatla.

    Args:
        sifat_context: build_sifat_context() çıktısı
        lang: Dil kodu

    Returns:
        Formatlanmış prompt string
    """
    lines = []
    _append = lines.append
    _scget = sifat_context.get
    module_name = _scget("module", "")
    sifatlar = _scget("sifatlar", [])
    sentences_by_sifat = _scget("sentences_by_sifat", {})
    sifat_details = _scget("sifat_details", {})

    # Başlık
    _mod_upper = module_name.upper()
    if lang == "tr":
        _append(f"\n## {_mod_upper} MODÜLÜ - SIFAT CONTEXT\n")
        _append("Kullanıcının algılanan sıfatları ve bu sıfatlara ilişkin cümleler:\n")
    else:
        _append(f"\n## {_mod_upper} MODULE - ATTRIBUTE CONTEXT\n")
        _append("User's detected attributes and related sentences:\n")

    # Her sıfat için detaylar ve cümleler
    for sifat in sifatlar:
        # Sıfat detayları (skor, açıklama)
        detail = sifat_details.get(sifat, {})
        _dget = detail.get
        score = _dget("score", "N/A")
        description = _dget("description", "")

        _append(f"\n📌 {sifat.upper()} (Güven: {score})")

        if description:
            _append(f"   Açıklama: {description[:100]}...")

        # İlişkili cümleler
        sentences = sentences_by_sifat.get(sifat, [])
        if sentences:
            _append("   İlişkili cümleler:")
            for i, sentence in enumerate(sentences, 1):
                _append(f"   • {sentence}")
        else:
            _append("   (Cümle bulunamadı)")

    _append("\n---\n")

    return "\n".join(lines)


# Test
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    # Test: acele karar vermeyen sıfatının tavsiye cümlelerini çek
    sentences = fetch_sifat_sentences("acele karar vermeyen", "tavsiye", "tr")
    print(f"Cümleler: {sentences}")

    # Test: context oluştur
    context = build_sifat_context(
        ["acele karar vermeyen", "sosyal"],
        "tavsiye",
        {"acele karar vermeyen": {"score": 0.85, "description": "Test"}},
        "tr"
    )
    print(f"\nContext: {context}")

    # Test: Ollama için format
    formatted = format_context_for_ollama(context, "tr")
    print(f"\nFormatted:\n{formatted}")

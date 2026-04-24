#!/usr/bin/env python3
"""
Quick dataset generator - fixes the sifatlar nested structure
"""
import json
import random
import sys
from pathlib import Path

# Load the database
db_path = Path("../../facesyma_migrate/sifat_veritabani.json")
with open(db_path) as f:
    full_db = json.load(f)

# Extract sifatlar (the actual data)
sifatlar_db = full_db.get("sifatlar", {})
print(f"Loaded {len(sifatlar_db)} sifatlar from {db_path}")

if not sifatlar_db:
    print("ERROR: No sifatlar found in database!")
    sys.exit(1)

# System prompt (Turkish)
SYSTEM_PROMPT = (
    "Sen Facesyma'nın kişisel yapay zeka danışmanısın. "
    "Yüz analizi sonuçlarını kullanarak kullanıcıya derin karakter içgörüleri, "
    "kariyer önerileri, liderlik analizi ve kişisel gelişim tavsiyeleri sunarsın. "
    "Samimi, destekleyici ve spesifik ol. Türkçe konuş."
)

# Sample questions
QUESTIONS = {
    "initial": [
        "Analiz sonuçlarımı açıklar mısın?",
        "Yüz analizimden ne anlamalıyım?",
        "Bu sonuçlar hakkında ne düşünüyorsun?",
        "Karakterim hakkında ne söyleyebilirsin?"
    ]
}

INTROS = [
    "Analiz sonuçlarına göre, ",
    "Yüz analizi verisine dayanarak, ",
    "Senin hakkında şunları söyleyebilirim: "
]

CLOSES = [
    " Bu özellik seni diğerlerinden ayıran önemli bir nokta.",
    " Bu yönün geliştirilmesi sana çok faydalı olabilir.",
    " Bu özellikleriyle başarılı olabilirsin.",
    ""
]

# Generate examples
examples = []
sifatlar_list = list(sifatlar_db.items())

print(f"\nGenerating 8000 training examples...")

_rc = random.choice
for i in range(8000):
    sifat_id, sifat_data = _rc(sifatlar_list)

    # Extract data from sifatlar structure
    _sdget = sifat_data.get
    sifat_name = _sdget("ad", f"Sifat {sifat_id}")  # 'ad' is the name
    cumleler = _sdget("cumleler", [])  # 'cumleler' is the sentences list

    if not cumleler:
        continue

    # Get a random sentence from the sifat
    sentence_obj = _rc(cumleler)
    sentence_text = sentence_obj.get("metin", "") if isinstance(sentence_obj, dict) else str(sentence_obj)

    if not sentence_text:
        continue

    # Simple example
    user_msg = f"[ANALİZ SONUCU]\nÖzellik: {sifat_name}\n\n{_rc(QUESTIONS['initial'])}"
    assistant_msg = f"{_rc(INTROS)}{sentence_text[:200]}{_rc(CLOSES)}"

    example = {
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_msg},
            {"role": "assistant", "content": assistant_msg}
        ]
    }

    examples.append(example)

    if (i + 1) % 1000 == 0:
        print(f"  {i + 1}/8000...")

# Save
output = Path("dataset_combined.jsonl")
with open(output, "w", encoding="utf-8") as f:
    for ex in examples:
        f.write(json.dumps(ex, ensure_ascii=False) + "\n")

print(f"\n✅ Generated {len(examples)} examples")
print(f"✅ Saved to: {output}")
print(f"✅ Size: {output.stat().st_size / (1024*1024):.1f} MB")

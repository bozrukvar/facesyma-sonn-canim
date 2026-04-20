"""
dataset/generate_dataset.py
============================
Facesyma Llama 3.1 8B fine-tune veri seti üreticisi.

İKİ VERİ TÜRÜ üretir:
  1. JSON tabanlı  — analiz sonucu (JSON) → yorumlu sohbet
  2. Fotoğraf tabanlı — mevcut facesyma motoru çıktısı → yorumlu sohbet

Format: HuggingFace Alpaca / ChatML (JSONL)

Kullanım:
  # JSON tabanlı veri (hızlı, 201 sıfat × 13 modül)
  python generate_dataset.py --mode json \
      --sifat-db ../facesyma_migrate/sifat_veritabani.json \
      --output   dataset_json_tr.jsonl \
      --samples  8000

  # Fotoğraf tabanlı veri (gerçek analiz çıktıları varsa)
  python generate_dataset.py --mode photos \
      --photo-results  /path/to/analysis_results.jsonl \
      --output         dataset_photo_tr.jsonl

  # İkisini birleştir
  python generate_dataset.py --mode merge \
      --inputs dataset_json_tr.jsonl dataset_photo_tr.jsonl \
      --output dataset_combined.jsonl \
      --shuffle
"""

import json, random, argparse, sys, re
from pathlib import Path
from copy    import deepcopy


# ── Llama 3.1 ChatML formatı ──────────────────────────────────────────────────
# <|begin_of_text|><|start_header_id|>system<|end_header_id|>
# ... system prompt ...
# <|eot_id|><|start_header_id|>user<|end_header_id|>
# ... kullanıcı mesajı ...
# <|eot_id|><|start_header_id|>assistant<|end_header_id|>
# ... cevap ...
# <|eot_id|>

LLAMA_SYSTEM = {
    "tr": (
        "Sen Facesyma'nın kişisel yapay zeka danışmanısın. "
        "Yüz analizi sonuçlarını kullanarak kullanıcıya derin karakter içgörüleri, "
        "kariyer önerileri, liderlik analizi ve kişisel gelişim tavsiyeleri sunarsın. "
        "Samimi, destekleyici ve spesifik ol. Türkçe konuş. "
        "Her cevabında analiz verisine doğrudan atıfta bulun."
    ),
    "en": (
        "You are Facesyma's personal AI advisor. "
        "Using face analysis results, you provide deep character insights, "
        "career recommendations, leadership analysis and personal development advice. "
        "Be sincere, supportive and specific. Speak in English. "
        "Always reference the analysis data directly in your responses."
    ),
}

# ── Soru şablonları ───────────────────────────────────────────────────────────

# ── Soru şablonları — 8 dil ───────────────────────────────────────────────────
QUESTIONS = {
    "tr": {
        "initial":    ["Analiz sonuçlarımı açıklar mısın?", "Yüz analizimden ne anlamalıyım?",
                       "Bu sonuçlar hakkında ne düşünüyorsun?", "Karakterim hakkında ne söyleyebilirsin?"],
        "kariyer":    ["Kariyer önerilerin neler?", "Hangi meslekler bana uyar?",
                       "İş hayatında nasıl başarılı olabilirim?", "Hangi sektörde çalışmalıyım?"],
        "liderlik":   ["Liderlik stilim nasıl?", "Bir ekibi nasıl yönetebilirim?",
                       "Liderlik kapasitem nedir?"],
        "duygusal":   ["Duygusal zekam hakkında ne söylersin?", "Empati yeteneğim nasıl?",
                       "Duygularımı nasıl daha iyi yönetebilirim?"],
        "muzik":      ["Bana hangi müzik türlerini önerirsin?", "Müzik zevkim nasıl?"],
        "film_dizi":  ["Film önerilerin neler?", "Hangi tür filmleri sevmeliyim?"],
        "motivasyon": ["Beni en çok ne motive eder?", "Hedeflerime ulaşmam için tavsiyeler?"],
        "genel":      ["Güçlü yönlerim neler?", "Kendimi nasıl geliştirebilirim?",
                       "En önemli özelliğim ne?", "Gelişim alanlarım neler?"],
    },
    "en": {
        "initial":    ["Can you explain my analysis results?", "What should I understand from my face analysis?",
                       "What can I learn about myself from this analysis?", "Tell me about my character traits."],
        "kariyer":    ["What career recommendations do you have?", "Which professions suit me?",
                       "How can I succeed professionally?", "What sector should I work in?"],
        "liderlik":   ["What is my leadership style?", "How can I lead a team effectively?",
                       "What is my leadership capacity?"],
        "duygusal":   ["What can you say about my emotional intelligence?", "How can I improve my relationships?",
                       "How is my empathy?"],
        "muzik":      ["What music genres would you recommend for me?", "What does my music taste say about me?"],
        "film_dizi":  ["What films do you recommend?", "What kind of stories would resonate with me?"],
        "motivasyon": ["What motivates me the most?", "What advice do you have for reaching my goals?"],
        "genel":      ["What are my strengths?", "How can I improve myself?",
                       "What is my most important trait?", "What are my growth areas?"],
    },
    "de": {
        "initial":    ["Kannst du meine Analyseergebnisse erklären?", "Was soll ich aus meiner Gesichtsanalyse schließen?",
                       "Was denkst du über meine Ergebnisse?", "Was kannst du über meinen Charakter sagen?"],
        "kariyer":    ["Welche Karriereempfehlungen hast du für mich?", "Welche Berufe passen zu mir?",
                       "Wie kann ich beruflich erfolgreich sein?"],
        "liderlik":   ["Wie ist mein Führungsstil?", "Wie kann ich ein Team effektiv leiten?"],
        "duygusal":   ["Was kannst du über meine emotionale Intelligenz sagen?", "Wie ist meine Empathiefähigkeit?"],
        "muzik":      ["Welche Musikgenres würdest du mir empfehlen?"],
        "film_dizi":  ["Welche Filme empfiehlst du mir?"],
        "motivasyon": ["Was motiviert mich am meisten?"],
        "genel":      ["Was sind meine Stärken?", "Wie kann ich mich verbessern?", "Was sind meine Wachstumsbereiche?"],
    },
    "ru": {
        "initial":    ["Можешь объяснить мои результаты анализа?", "Что мне следует понять из анализа лица?",
                       "Что ты думаешь о моих результатах?", "Что ты можешь сказать о моём характере?"],
        "kariyer":    ["Какие карьерные рекомендации у тебя есть?", "Какие профессии мне подходят?",
                       "Как добиться успеха в профессиональной жизни?"],
        "liderlik":   ["Каков мой стиль лидерства?", "Как я могу эффективно руководить командой?"],
        "duygusal":   ["Что ты можешь сказать о моём эмоциональном интеллекте?", "Как развить эмпатию?"],
        "muzik":      ["Какую музыку ты порекомендуешь?"],
        "film_dizi":  ["Какие фильмы ты рекомендуешь?"],
        "motivasyon": ["Что меня больше всего мотивирует?"],
        "genel":      ["Каковы мои сильные стороны?", "Как я могу развиться?", "Каковы мои области роста?"],
    },
    "ar": {
        "initial":    ["هل يمكنك شرح نتائج تحليلي?", "ماذا يجب أن أفهم من تحليل وجهي?",
                       "ما رأيك في نتائجي?", "ماذا يمكنك أن تقول عن شخصيتي?"],
        "kariyer":    ["ما توصياتك المهنية لي?", "ما المهن التي تناسبني?"],
        "liderlik":   ["كيف هو أسلوب قيادتي?", "كيف يمكنني قيادة فريق بفعالية?"],
        "duygusal":   ["ما الذي يمكنك قوله عن ذكائي العاطفي?"],
        "muzik":      ["ما أنواع الموسيقى التي توصي بها لي?"],
        "film_dizi":  ["ما الأفلام التي توصي بها?"],
        "motivasyon": ["ما الذي يحفزني أكثر?"],
        "genel":      ["ما نقاط قوتي?", "كيف يمكنني تطوير نفسي?"],
    },
    "es": {
        "initial":    ["¿Puedes explicar mis resultados de análisis?", "¿Qué debo entender de mi análisis facial?",
                       "¿Qué puedes decir sobre mi carácter?"],
        "kariyer":    ["¿Qué recomendaciones de carrera tienes para mí?", "¿Qué profesiones me convienen?"],
        "liderlik":   ["¿Cuál es mi estilo de liderazgo?", "¿Cómo puedo liderar un equipo?"],
        "duygusal":   ["¿Qué puedes decir sobre mi inteligencia emocional?"],
        "muzik":      ["¿Qué géneros musicales me recomiendas?"],
        "film_dizi":  ["¿Qué películas me recomiendas?"],
        "motivasyon": ["¿Qué me motiva más?"],
        "genel":      ["¿Cuáles son mis fortalezas?", "¿Cómo puedo mejorarme?"],
    },
    "ko": {
        "initial":    ["분석 결과를 설명해 주실 수 있나요?", "얼굴 분석에서 무엇을 알 수 있나요?",
                       "제 성격에 대해 어떻게 생각하세요?"],
        "kariyer":    ["어떤 커리어 추천을 해주시겠어요?", "어떤 직업이 저에게 맞나요?"],
        "liderlik":   ["제 리더십 스타일은 어떤가요?", "팀을 효과적으로 이끌 수 있나요?"],
        "duygusal":   ["제 감성 지능에 대해 말씀해 주세요."],
        "muzik":      ["어떤 음악 장르를 추천해 주시겠어요?"],
        "film_dizi":  ["어떤 영화를 추천해 주시겠어요?"],
        "motivasyon": ["무엇이 저를 가장 동기부여 하나요?"],
        "genel":      ["제 강점은 무엇인가요?", "어떻게 발전할 수 있나요?"],
    },
    "ja": {
        "initial":    ["分析結果を説明していただけますか？", "顔分析から何を理解すべきですか？",
                       "私の性格についてどう思いますか？"],
        "kariyer":    ["キャリアのアドバイスをいただけますか？", "どんな職業が向いていますか？"],
        "liderlik":   ["私のリーダーシップスタイルはどうですか？"],
        "duygusal":   ["私の感情知性について教えてください。"],
        "muzik":      ["どんな音楽ジャンルをおすすめしますか？"],
        "film_dizi":  ["どんな映画をおすすめしますか？"],
        "motivasyon": ["何が私を最も動機づけますか？"],
        "genel":      ["私の強みは何ですか？", "どうすれば成長できますか？"],
    },
}

# ── Cevap giriş kalıpları — 8 dil ────────────────────────────────────────────
INTROS = {
    "tr": ["Analizine bakıldığında, ", "Sonuçların dikkat çekici — ", "Bu analiz seni çok iyi özetliyor: ",
           "Özellikle dikkatimi çeken şu: ", "Veriler açıkça gösteriyor ki "],
    "en": ["Looking at your analysis, ", "Your results are quite revealing — ",
           "This analysis describes you well: ", "What stands out to me is: ", "The data clearly shows that "],
    "de": ["Wenn ich deine Analyse betrachte, ", "Deine Ergebnisse sind aufschlussreich — ",
           "Diese Analyse beschreibt dich gut: ", "Was mich besonders auffällt: "],
    "ru": ["Глядя на твой анализ, ", "Твои результаты весьма показательны — ",
           "Этот анализ хорошо тебя описывает: ", "Что особенно бросается в глаза: "],
    "ar": ["بالنظر إلى تحليلك، ", "نتائجك كاشفة للغاية — ", "يصفك هذا التحليل بشكل جيد: "],
    "es": ["Mirando tu análisis, ", "Tus resultados son bastante reveladores — ",
           "Este análisis te describe bien: ", "Lo que más me llama la atención es: "],
    "ko": ["분석을 보면, ", "결과가 꽤 흥미롭습니다 — ", "이 분석은 당신을 잘 설명합니다: "],
    "ja": ["あなたの分析を見ると、", "結果はとても興味深いです — ", "この分析はあなたをよく表しています: "],
}

# ── Cevap kapanış kalıpları — 8 dil ─────────────────────────────────────────
CLOSES = {
    "tr": [" Bu farkındalıkla çok daha güçlü adımlar atabilirsin.",
           " Bu potansiyeli hayatına yansıtman için harika bir konumdasın.",
           " Kendine güven — bu özellikler gerçek birer avantaj.",
           " Bilinçli geliştirdiğinde bu, büyük bir güce dönüşebilir."],
    "en": [" With this awareness, you can take much stronger steps.",
           " You're in a great position to bring this potential to life.",
           " Trust yourself — these traits are real advantages.",
           " Consciously developing this can turn into great strength."],
    "de": [" Mit diesem Bewusstsein kannst du viel stärkere Schritte unternehmen.",
           " Du bist in einer großartigen Position, dieses Potenzial zu entfalten.",
           " Vertrau dir selbst — diese Eigenschaften sind echte Vorteile."],
    "ru": [" Осознавая это, ты сможешь делать гораздо более уверенные шаги.",
           " Ты в отличной позиции, чтобы реализовать этот потенциал.",
           " Верь в себя — эти черты настоящие преимущества."],
    "ar": [" بهذا الوعي يمكنك اتخاذ خطوات أقوى بكثير.",
           " أنت في وضع رائع لإظهار هذه الإمكانات.",
           " ثق بنفسك — هذه الصفات مزايا حقيقية."],
    "es": [" Con esta conciencia, puedes dar pasos mucho más fuertes.",
           " Estás en una posición excelente para manifestar este potencial.",
           " Confía en ti mismo — estos rasgos son ventajas reales."],
    "ko": [" 이 인식으로 훨씬 더 강한 발걸음을 내딛을 수 있습니다.",
           " 이 잠재력을 발휘할 훌륭한 위치에 있습니다.",
           " 자신을 믿으세요 — 이 특성들은 진짜 장점입니다."],
    "ja": [" この気づきで、より力強い一歩を踏み出せます。",
           " このポテンシャルを発揮する素晴らしい位置にいます。",
           " 自分を信じてください — これらの特性は本物の強みです。"],
}

def _trunc(v, maxlen=250):
    if isinstance(v, list):
        v = " • ".join(str(x) for x in v[:4])
    s = str(v).strip()
    return s[:maxlen] + "…" if len(s) > maxlen else s


# ── JSON tabanlı örnek üretici ────────────────────────────────────────────────
def make_json_sample(sifat: str, data: dict, lang: str, n_turns: int = 2) -> dict | None:
    sys_p  = LLAMA_SYSTEM.get(lang, LLAMA_SYSTEM["tr"])
    qs     = QUESTIONS.get(lang, QUESTIONS["tr"])
    intros = INTROS.get(lang, INTROS["tr"])
    closes = CLOSES.get(lang, CLOSES["tr"])

    # Analiz JSON'unu kullanıcı mesajına göm
    analysis_summary = {
        k: _trunc(v) for k, v in data.items()
        if v and k in ("kariyer", "liderlik", "duygusal", "motivasyon",
                       "muzik", "film_dizi", "etkinlik", "uyum", "beceri",
                       "giyim", "ik", "astroloji", "tavsiye")
    }
    analysis_str = json.dumps({"sifat": sifat, **analysis_summary},
                              ensure_ascii=False, indent=2)

    messages = []

    # İlk tur — analiz JSON'u ile birlikte
    first_q = random.choice(qs["initial"])
    user_content = (
        f"[ANALİZ SONUCU]\n```json\n{analysis_str}\n```\n\n{first_q}"
    )

    # İlk asistan cevabı
    intro  = random.choice(intros)
    close  = random.choice(closes)
    core   = data.get("kariyer", data.get("tavsiye", ""))
    if not core:
        return None

    reply = (
        f"{intro}**{sifat.capitalize()}** karakterin öne çıkıyor. "
        f"{_trunc(core, 200)}"
        f"{close}"
    )

    messages.append({"role": "user",      "content": user_content})
    messages.append({"role": "assistant", "content": reply})

    # Takip turları
    available_mods = [m for m in qs if m not in ("initial", "genel") and data.get(m)]
    random.shuffle(available_mods)

    for mod in available_mods[:n_turns]:
        q   = random.choice(qs[mod])
        val = data.get(mod, "")
        if not val:
            continue
        ans = (
            f"{random.choice(intros)}**{mod.capitalize()}** alanında "
            f"{_trunc(val, 220)}{random.choice(closes)}"
        )
        messages.append({"role": "user",      "content": q})
        messages.append({"role": "assistant", "content": ans})

    return {
        "messages": [{"role": "system", "content": sys_p}] + messages,
        "meta":     {"sifat": sifat, "source": "json"},
    }


# ── Fotoğraf tabanlı örnek dönüştürücü ───────────────────────────────────────
def convert_photo_result(record: dict, lang: str) -> dict | None:
    """
    Gerçek bir analiz çıktısını (facesyma motoru JSON'u) fine-tune örneğine çevir.

    record formatı:
    {
      "attributes": [...],
      "golden_ratio": 72,
      "face_type": "oval",
      "kariyer": "...",
      "liderlik": "...",
      ... diğer modüller ...
    }
    """
    sys_p  = LLAMA_SYSTEM.get(lang, LLAMA_SYSTEM["tr"])
    qs     = QUESTIONS.get(lang, QUESTIONS["tr"])
    intros = INTROS.get(lang, INTROS["tr"])
    closes = CLOSES.get(lang, CLOSES["tr"])

    # Analiz verisini özetle
    attrs = record.get("attributes", [])
    top_attrs = [a.get("name", "") for a in attrs[:5] if a.get("name")]

    analysis_str = json.dumps({
        "top_attributes": top_attrs,
        "golden_ratio": record.get("golden_ratio"),
        "face_type": record.get("face_type"),
        **{k: _trunc(record.get(k, "")) for k in
           ("kariyer", "liderlik", "duygusal", "motivasyon") if record.get(k)},
    }, ensure_ascii=False, indent=2)

    messages = []
    first_q = random.choice(qs["initial"])
    user_content = f"[ANALİZ SONUCU]\n```json\n{analysis_str}\n```\n\n{first_q}"

    core = record.get("kariyer") or record.get("tavsiye") or (
        attrs[0].get("description", "") if attrs else ""
    )
    if not core:
        return None

    dominant = top_attrs[0] if top_attrs else "analiz verisi"
    reply = (
        f"{random.choice(intros)}**{dominant.capitalize()}** özelliğin öne çıkıyor. "
        f"{_trunc(core, 200)}"
        f"{random.choice(closes)}"
    )

    messages.append({"role": "user",      "content": user_content})
    messages.append({"role": "assistant", "content": reply})

    # 1-2 takip turu ekle
    for mod in random.sample(list(qs.keys()), min(2, len(qs))):
        if mod in ("initial", "genel"):
            continue
        val = record.get(mod, "")
        if not val:
            continue
        q   = random.choice(qs[mod])
        ans = (
            f"{random.choice(intros)}{_trunc(val, 200)}{random.choice(closes)}"
        )
        messages.append({"role": "user",      "content": q})
        messages.append({"role": "assistant", "content": ans})

    return {
        "messages": [{"role": "system", "content": sys_p}] + messages,
        "meta":     {"source": "photo"},
    }


# ── Veri seti yazıcı ──────────────────────────────────────────────────────────
def write_jsonl(examples: list, path: Path):
    with open(path, "w", encoding="utf-8") as f:
        for ex in examples:
            f.write(json.dumps(ex, ensure_ascii=False) + "\n")
    print(f"Kaydedildi: {path}  ({len(examples):,} örnek)")


# ── Ana üretici fonksiyonlar ──────────────────────────────────────────────────
def generate_json_mode(sifat_db_path: Path, output: Path,
                       lang: str, n_samples: int, n_turns: int):
    print(f"JSON modu: {sifat_db_path}")
    with open(sifat_db_path, encoding="utf-8") as f:
        db = json.load(f)

    items    = list(db.items())
    examples = []
    seen     = set()
    attempts = 0

    while len(examples) < n_samples and attempts < n_samples * 6:
        attempts += 1
        sifat, data = random.choice(items)
        key = (sifat, len(examples) // max(1, n_samples // len(items) + 1))
        if key in seen:
            continue
        seen.add(key)

        sample = make_json_sample(sifat, data, lang, n_turns)
        if sample:
            examples.append(sample)
        if len(examples) % 1000 == 0 and len(examples):
            print(f"  {len(examples):,}/{n_samples:,}...")

    write_jsonl(examples, output)


def generate_photo_mode(photo_results_path: Path, output: Path, lang: str):
    print(f"Fotoğraf modu: {photo_results_path}")
    examples = []
    with open(photo_results_path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                record = json.loads(line)
                sample = convert_photo_result(record, lang)
                if sample:
                    examples.append(sample)
            except json.JSONDecodeError:
                continue

    print(f"  {len(examples):,} fotoğraf kaydı işlendi")
    write_jsonl(examples, output)


def merge_mode(inputs: list, output: Path, shuffle: bool):
    print(f"Birleştirme modu: {inputs}")
    all_examples = []
    for inp in inputs:
        p = Path(inp)
        if not p.exists():
            print(f"  UYARI: {p} bulunamadı, atlanıyor")
            continue
        count = 0
        with open(p, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    all_examples.append(json.loads(line))
                    count += 1
        print(f"  {p.name}: {count:,} örnek")

    if shuffle:
        random.shuffle(all_examples)
        print(f"  Karıştırıldı")

    write_jsonl(all_examples, output)


# ── CLI ───────────────────────────────────────────────────────────────────────
def main():
    p = argparse.ArgumentParser(formatter_class=argparse.RawDescriptionHelpFormatter,
        description=__doc__)
    p.add_argument("--mode",    required=True, choices=["json", "photos", "merge"])
    p.add_argument("--sifat-db",     default="sifat_veritabani.json")
    p.add_argument("--photo-results",default="analysis_results.jsonl")
    p.add_argument("--inputs",  nargs="+", help="merge modu için giriş dosyaları")
    p.add_argument("--output",  required=True)
    p.add_argument("--lang",    default="tr",
                   choices=["tr","en","de","ru","ar","es","ko","ja"])
    p.add_argument("--samples", type=int, default=8000)
    p.add_argument("--turns",   type=int, default=2)
    p.add_argument("--shuffle", action="store_true")
    args = p.parse_args()

    output = Path(args.output)

    if args.mode == "json":
        sifat_path = Path(args.sifat_db)
        if not sifat_path.exists():
            alt = Path(f"sifat_veritabani_{args.lang}.json")
            if alt.exists():
                sifat_path = alt
            else:
                print(f"HATA: {sifat_path} bulunamadı")
                sys.exit(1)
        generate_json_mode(sifat_path, output, args.lang, args.samples, args.turns)

    elif args.mode == "photos":
        photo_path = Path(args.photo_results)
        if not photo_path.exists():
            print(f"HATA: {photo_path} bulunamadı")
            sys.exit(1)
        generate_photo_mode(photo_path, output, args.lang)

    elif args.mode == "merge":
        if not args.inputs:
            print("HATA: --inputs gerekli")
            sys.exit(1)
        merge_mode(args.inputs, output, args.shuffle)

    print("\nSonraki adım:")
    print(f"  python ../training/train.py --dataset {args.output}")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
Partial RAG Test — 6 soru test et mevcut koleksiyonlarla
"""

from facesyma_ai.rag.retriever import get_relevant_context

QUESTIONS = [
    "Gel, kendini bul.",
    "Sandığın kadar mısın, başka mı?",
    "Anlattığın mısın, anlatamadığın mı?",
    "En çok neyi sakladığını bilmek ister misin?",
    "Ne kadarın görünür, ne kadarın gizli?",
    "Hangi sen hâlâ seni bekliyor?",
]

SIFATLAR = ["güvenilir", "kararlı", "duygusal", "yaratıcı", "içedönük"]

print("=" * 80)
print("🧪 PARTIAL RAG TEST — Mevcut Koleksiyonlarla")
print("=" * 80)
print(f"\n📊 Setup:")
print(f"   - Soru: {len(QUESTIONS)}")
print(f"   - Sıfatlar: {SIFATLAR}")
print(f"   - Koleksiyonlar: sifat_profiles, sifat_characteristics")
print(f"\n{'=' * 80}\n")

results = []
for i, question in enumerate(QUESTIONS, 1):
    print(f"\n[{i}/{len(QUESTIONS)}] 📝 {question}")
    print("-" * 80)

    try:
        context = get_relevant_context(question, SIFATLAR, lang="tr")

        if context:
            sections = context.count("##")
            bullets = context.count("•")
            length = len(context)

            print(f"✅ RAG BAŞARILI")
            print(f"   Bölüm: {sections} | Doküman: {bullets} | Uzunluk: {length} chr")
            print(f"\n📋 Context (ilk 250 chr):\n{context[:250]}")
            if length > 250:
                print("...")

            results.append((question, "✅", sections, bullets, length))
        else:
            print(f"⚠️  RAG context boş")
            results.append((question, "⚠️", 0, 0, 0))

    except Exception as e:
        print(f"❌ ERROR: {e}")
        results.append((question, "❌", 0, 0, 0))

# Summary
print(f"\n\n{'=' * 80}")
print("📊 ÖZET")
print("=" * 80)

success = sum(1 for r in results if "✅" in r[1])
print(f"\n✅ Başarılı: {success}/{len(results)}")
print(f"⚠️  Boş: {sum(1 for r in results if '⚠️' in r[1])}")
print(f"❌ Hata: {sum(1 for r in results if '❌' in r[1])}\n")

total_context = sum(r[4] for r in results)
print(f"📈 Toplam context: {total_context} karakterlik bilgi injekte edildi")

if success > 0:
    print(f"\n🎉 RAG SİSTEMİ ÇALIŞIYOR! {success} sorudan cevap aldı.")
else:
    print(f"\n⚠️  RAG context almada sorun var.")

print(f"{'=' * 80}")

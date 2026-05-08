# CROSS-ANALYSIS (Yüz × Test) — Tam Entegrasyon Makro Planı

Oluşturulma: 2026-05-08
Durum: TAMAMLANDI ✓ (2026-05-08)

---

## FAZ 1 — Veri Bütünlüğü [TAMAMLANDI ✓]
> Üretilen zenginleştirilmiş narrative'in kaybolmaması

- [x] 1A · `facesyma_mobile/src/types/api.ts` — `AssessmentResult` arayüzüne `narrative?` + `face_enriched?` ekle
- [x] 1B · `facesyma_mobile/src/services/api.ts` — `saveResult()` payload'a `narrative` + `face_enriched` ekle
- [x] 1C · `facesyma_backend/analysis_api/assessment_views.py` — `SaveAssessmentResultView` `result_doc`'a `narrative` + `face_enriched` ekle
- [x] 1D · `facesyma_backend/analysis_api/assessment_views.py` — `_ASSESSMENT_HISTORY_PROJ`'a `narrative` + `face_enriched` ekle

---

## FAZ 2 — Mobil UX [TAMAMLANDI ✓]
> Kullanıcı, analizin yüzle zenginleştirildiğini görmeli

- [x] 2A · `facesyma_mobile/src/screens/AssessmentScreen.tsx` — `face_enriched: true` ise narrative kartı üstüne 🔗 badge
- [x] 2B · `facesyma_mobile/src/screens/AssessmentHistoryScreen.tsx` — geçmiş listesinde 🔗 ikonu
- [x] 2C · `facesyma_mobile/src/utils/i18n.ts` — 18 dile `assessment.face_enriched_label` anahtarı (script ile)

---

## FAZ 3 — Sıra Bağımlılığı Sorunu [TAMAMLANDI ✓]
> "Önce test → sonra yüz analizi" yapan kullanıcılar için

- [x] 3A · `facesyma_backend/analysis_api/assessment_views.py` — `POST /api/v1/assessment/re-enrich/` endpoint'i
- [x] 3B · `facesyma_mobile/src/screens/AssessmentHistoryScreen.tsx` — `face_enriched: false` kayıtlar için arka planda re-enrich tetikleyici

---

## FAZ 4 — Coach Entegrasyonu [TAMAMLANDI ✓]
> AI Coach'un yüz × test cross-analizinden haberdar olması

- [x] 4A · `facesyma_coach/api/coach_api.py` — `AnalyzeRequest`'e `cross_analysis_summary: Optional[str]` ekle
- [x] 4B · `facesyma_coach/api/coach_api.py` — `coach_analyze` fonksiyonunda cross-analysis context injection
- [x] 4C · `facesyma_mobile/src/screens/CoachHubScreen.tsx` — en son `face_enriched: true` narrative'i `cross_analysis_summary` olarak gönder

---

## Bağımlılık Sırası

```
FAZ 1A → 1B → 1C → 1D    (sırayla)
FAZ 2A → 2B → 2C          (Faz 1 sonrası)
FAZ 3A → 3B               (Faz 1 sonrası)
FAZ 4A → 4B → 4C          (bağımsız, Faz 1 sonrası daha zengin)
```

---

## Tahmini Süreler

| Faz | Kapsam | Süre |
|-----|--------|------|
| 1 · Veri | Backend + Mobile | ~30 dk |
| 2 · UX | Mobile + i18n | ~30 dk |
| 3 · Re-enrich | Backend + Mobile | ~45 dk |
| 4 · Coach | Backend + Mobile | ~45 dk |

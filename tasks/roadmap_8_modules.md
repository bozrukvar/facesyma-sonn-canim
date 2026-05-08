# Facesyma — 8 Kritik Modül Yol Haritası

Oluşturulma: 2026-05-08  
Öncelik sırası: Kullanıcı tutma → Yasal zorunluluk → Büyüme

---

## Öncelik Özeti

| # | Modül | Öncelik | Tahmini Efor | Durum |
|---|-------|---------|--------------|-------|
| 1 | Onboarding Flow | 🔴 Kritik | 2-3 gün | ✅ Tamamlandı |
| 2 | İlerleme / Trend Grafiği | 🔴 Kritik | 2-3 gün | ✅ Tamamlandı |
| 3 | Hesap Silme + Veri İndirme | 🔴 Kritik (Yasal) | 1-2 gün | ✅ Tamamlandı |
| 4 | Push Notification Altyapısı | 🔴 Kritik | 3-4 gün | ✅ Tamamlandı |
| 5 | Günlük Duygu Check-in | 🟡 Yüksek | 2-3 gün | ✅ Tamamlandı |
| 6 | Hedef Takip Modülü | 🟡 Yüksek | 4-5 gün | ✅ Tamamlandı |
| 7 | Aylık Kişisel Rapor | 🟢 Orta | 3-4 gün | ✅ Tamamlandı |
| 8 | Partner / Uyumluluk Modu | 🟢 Orta | 5-7 gün | Bekliyor |

---

## Modül 1 — Onboarding Flow

**Amaç:** İlk açılışta kullanıcıyı uygulamaya bağlamak, churn'ü azaltmak.

**Ekranlar (4 adım):**
1. Karşılama — "Facesyma nedir?" (uygulama logosu + tek cümle)
2. Ne yapabilirsin? — 3 özellik: Yüz Analizi / Psikoloji Testleri / AI Coach (ikon + kısa açıklama)
3. Gizlilik — Hangi veriler toplanıyor, KVKK özeti, "Verilerini kontrol sen edersin"
4. Başla — Dil seçimi + kayıt / giriş CTA

**Backend:**
- `onboarding_completed: bool` alanı User modeline eklenmeli
- `PATCH /api/v1/auth/profile/` ile `onboarding_completed: true` set edilmeli

**Mobile:**
- `OnboardingScreen.tsx` — 4 sayfa, swipe veya buton navigasyonu
- `AsyncStorage` ile "ilk kez mi?" kontrolü (auth olmadan da göster)
- Navigasyon: Onboarding → Auth/Register → Home

**i18n:** `onboarding.*` key ailesi — 18 dil

**Dosyalar:**
- `facesyma_mobile/src/screens/OnboardingScreen.tsx` (yeni)
- `facesyma_mobile/src/navigation/` — root navigator'a onboarding flow eklenmeli
- `facesyma_backend/auth_api/views.py` — profile patch

---

## Modül 2 — İlerleme / Trend Grafiği

**Amaç:** Kullanıcının zaman içindeki değişimini görselleştirmek → test tekrar oranını artırmak.

**UX:**
- `AssessmentHistoryScreen` içinde veya yeni `ProgressScreen`
- Test seçimi (dropdown) → o teste ait tüm geçmiş skorlar → çizgi grafik
- X ekseni: tarih, Y ekseni: 0-100 overall skor
- Domain bazlı radar chart (en son test için)
- "İlk testten bu yana +12 puan" gibi delta göstergesi

**Kütüphane:**
- `react-native-svg` + `victory-native` (zaten kurulu olabilir) veya `react-native-chart-kit`
- Bağımlılık yoksa: `npm install victory-native react-native-svg`

**Backend:**
- `GET /api/v1/analysis/assessment/results/<test_type>/` — mevcut endpoint yeterli
- Veri: `overall_score` + `created_at` + `breakdown` per result

**Mobile:**
- `ProgressScreen.tsx` (yeni) veya `AssessmentHistoryScreen` genişletme
- Test tipine göre filtrelenmiş skor listesi → grafik veri dizisine dönüştür

**Dosyalar:**
- `facesyma_mobile/src/screens/ProgressScreen.tsx` (yeni)
- `facesyma_mobile/src/navigation/types.ts` — `Progress` route eklenmeli
- `facesyma_mobile/src/screens/HomeScreen.tsx` — "İlerlemem" butonu

---

## Modül 3 — Hesap Silme + Veri İndirme

**Amaç:** KVKK / GDPR uyumu. Yasal zorunluluk.

### 3A — Veri İndirme
**Backend:**
- `GET /api/v1/auth/export/` — kullanıcıya ait tüm veriyi JSON olarak döner
- Dahil edilecek: profil, assessment_results, face_analysis history, coach_messages, gamification
- Rate limit: günde 1 kez

**Mobile:**
- Ayarlar ekranında "Verilerimi İndir" butonu
- Response JSON → `Share` API ile paylaş veya `Downloads` klasörüne yaz

### 3B — Hesap Silme
**Backend:**
- `DELETE /api/v1/auth/account/` endpoint
- Soft delete (30 gün grace period) → hard delete job
- Tüm koleksiyonlardan user_id bazlı temizlik:
  - `users`, `assessment_results`, `face_analysis_history`, `coach_sessions`, `gamification_*`, `subscriptions`
- JWT token invalidation (Redis blacklist)

**Mobile:**
- Ayarlar → "Hesabımı Sil" → onay dialog ("Bu işlem geri alınamaz") → şifre doğrulama → istek
- Başarılı olunca logout + onboarding'e yönlendir

**Dosyalar:**
- `facesyma_backend/auth_api/views.py` — export + delete views
- `facesyma_backend/auth_api/urls.py` — yeni route'lar
- `facesyma_mobile/src/screens/SettingsScreen.tsx` — butonlar

---

## Modül 4 — Push Notification Altyapısı

**Amaç:** Günlük engagement, coach mesaj bildirimleri, streak uyarıları.

**Servis:** Firebase Cloud Messaging (FCM) — hem iOS hem Android

**Backend:**
- `fcm_token: str` alanı User modeline eklenmeli
- `PATCH /api/v1/auth/profile/` — token kaydetmek için
- `POST /api/v1/notifications/send/` — admin tetikleyici (opsiyonel)
- `UserNotificationSettings` modeli: hangi tür bildirimlere izin verildi
- Mevcut scheduler job'larına (`send_daily_personalized_ai_coach_notifications`) FCM entegrasyonu

**Notification tipleri:**
1. Günlük coach mesajı (sabah 09:00, kişiselleştirilmiş)
2. Streak hatırlatıcısı (akşam 20:00, eğer o gün giriş yoksa)
3. Test hatırlatıcısı ("30 gün önce stres testini yaptın, tekrar zamanı")
4. Hedef milestone (Modül 6 ile entegrasyon)

**Mobile:**
- `@react-native-firebase/messaging` kurulumu
- İzin alma → token alma → backend'e kaydetme (login sonrası)
- Foreground / background / killed state handler'ları
- Bildirime tıklandığında ilgili ekrana deep link

**Dosyalar:**
- `facesyma_backend/auth_api/models.py` — fcm_token alanı
- `facesyma_backend/notifications/` (yeni Django app)
  - `fcm_service.py` — FCM HTTP v1 API wrapper
  - `views.py` — notification prefs endpoints
- `facesyma_mobile/src/services/notifications.ts` (yeni)
- `facesyma_mobile/android/`, `ios/` — Firebase config dosyaları

---

## Modül 5 — Günlük Duygu Check-in

**Amaç:** Günlük alışkanlık oluşturmak, coach'a longitudinal duygusal veri sağlamak.

**UX:**
- Ana ekranda küçük bir "Bugün nasılsın?" kartı (sabahları veya her girişte)
- 5 emoji seçenek: 😔 😕 😐 🙂 😄 (1-5 skor)
- Opsiyonel: tek kelime / etiket seçimi (stresli / yorgun / enerjik / sakin / mutlu)
- 5 saniyede tamamlanabilmeli
- Streak göstergesi: "7 günlük seri!"

**Backend:**
- Yeni koleksiyon: `daily_checkins`
  ```json
  { "user_id", "date", "mood_score": 1-5, "tags": [], "created_at" }
  ```
- `POST /api/v1/checkin/` — bugünkü check-in kaydet
- `GET /api/v1/checkin/history/?days=30` — son N günlük geçmiş
- `GET /api/v1/checkin/streak/` — mevcut seri

**AI Coach entegrasyonu:**
- Coach context'ine son 7 günlük ortalama mood dahil edilmeli
- Düşük mood trend'i (3 gün üst üste < 2) → coach proaktif sorgu başlatsın

**Trend grafiği:**
- Modül 2 ile entegrasyon: mood grafiği + assessment skoru aynı ekranda

**Dosyalar:**
- `facesyma_backend/checkin/` (yeni Django app)
- `facesyma_mobile/src/screens/HomeScreen.tsx` — check-in kartı
- `facesyma_mobile/src/components/MoodCheckin.tsx` (yeni component)
- `facesyma_mobile/src/screens/ProgressScreen.tsx` — mood trend

---

## Modül 6 — Hedef Takip Modülü

**Amaç:** Assessment sonuçlarını eyleme dönüştürmek, uzun vadeli engagement sağlamak.

**UX:**
- Test sonucu ekranında "Bu sonuca göre hedef belirle" butonu
- Hedef oluşturma: başlık + alan (test tipi) + hedef skor + bitiş tarihi
- Hedef detay: ilerleme çubuğu + haftalık micro-görevler (coach tarafından üretilir)
- Ana ekranda "Aktif Hedeflerim" widget'ı

**Veri modeli:**
```json
{
  "goal_id", "user_id",
  "title": "Stres skorumu 60'ın altına indir",
  "test_type": "stress",
  "target_score": 55,
  "current_score": 72,
  "deadline": "2026-08-01",
  "weekly_tasks": [...],
  "status": "active|completed|abandoned",
  "created_at"
}
```

**Backend:**
- `POST /api/v1/goals/` — hedef oluştur
- `GET /api/v1/goals/` — aktif hedefler
- `PATCH /api/v1/goals/<id>/` — güncelle / tamamla
- Coach API entegrasyonu: hedef context'e dahil edilmeli

**Micro-görev üretimi:**
- Hedef oluşturulunca Ollama'ya prompt: test tipi + mevcut skor + hedef → 4 haftalık görev listesi üret
- Her görev: basit, ölçülebilir, 5-10 dakikalık eylem

**Dosyalar:**
- `facesyma_backend/goals/` (yeni Django app)
- `facesyma_mobile/src/screens/GoalsScreen.tsx` (yeni)
- `facesyma_mobile/src/screens/AssessmentScreen.tsx` — sonuç ekranına hedef butonu

---

## Modül 7 — Aylık Kişisel Rapor

**Amaç:** Paylaşılabilir özet → viral büyüme + kullanıcı bağlılığı.

**İçerik (aylık):**
- Tamamlanan testler ve skor değişimleri
- En güçlü alan vs gelişim alanı
- Duygu check-in ortalaması (Modül 5)
- Hedef ilerlemesi (Modül 6)
- AI coach özet yorumu (2-3 cümle)
- Kullanıcı percentile'ı ("Öz-yeterlik'te kullanıcıların %68'inden iyisin")

**Format:**
- In-app ekran (primary) — güzel tasarım, scroll edilebilir
- PDF export (secondary) — `react-native-html-to-pdf` veya server-side render

**Backend:**
- `GET /api/v1/reports/monthly/?month=2026-05` — rapor verisi derle
- Cron job: ayın 1'inde raporu önceden hesapla + bildirim gönder (Modül 4)
- Rapor şablonu: tüm veri kaynaklarını (assessments, checkins, goals) birleştir

**Mobile:**
- `MonthlyReportScreen.tsx` (yeni)
- Share butonu — ekran görüntüsü veya PDF

**Dosyalar:**
- `facesyma_backend/reports/` (yeni Django app)
- `facesyma_mobile/src/screens/MonthlyReportScreen.tsx` (yeni)

---

## Modül 8 — Partner / Uyumluluk Modu ✅ Tamamlandı

**Amaç:** Çiftlerin birlikte kullanımı → viral büyüme, yeni kullanıcı edinimi.

**UX akışı:**
1. Kullanıcı "Partner Bağla" → davet kodu üretir (6 karakter)
2. Partner kodu girer → bağlantı kurulur
3. Her iki taraf da gerekli testleri tamamlar (personality, attachment, relationship, values)
4. Uyumluluk raporu açılır

**Uyumluluk raporu içeriği:**
- Genel uyumluluk skoru (0-100)
- Kişilik uyumu (Big Five karşılaştırma)
- Bağlanma stili kombinasyonu (güvenli-güvenli en iyi, kaçıngan-kaygılı en riskli)
- Sevgi dilleri — örtüşen ve farklılaşan alanlar
- Değer sistemi benzerliği
- Güçlü yönler + dikkat edilmesi gerekenler
- AI yorumu (couple-aware prompt)

**Veri modeli:**
```json
{
  "partnership_id", "user_a_id", "user_b_id",
  "invite_code", "status": "pending|active",
  "compatibility_score": 78,
  "report": { "strengths": [], "watchouts": [], "narrative": "" },
  "created_at"
}
```

**Backend:**
- `POST /api/v1/partner/invite/` — davet kodu üret
- `POST /api/v1/partner/join/` — koda katıl
- `GET /api/v1/partner/compatibility/` — rapor hesapla / getir
- Uyumluluk algoritması: her domain için delta hesapla + attachment matrix uygula

**Privacy:**
- Sadece paylaşmak istenen testler görünür
- Her iki tarafın onayı olmadan rapor açılmaz
- Bağlantı her zaman kesilebilir

**Dosyalar:**
- `facesyma_backend/partnerships/` (yeni Django app)
- `facesyma_mobile/src/screens/PartnerScreen.tsx` (yeni)
- `facesyma_mobile/src/screens/CompatibilityReportScreen.tsx` (yeni)

---

## Uygulama Sırası (Önerilen Sprint Planı)

```
Sprint 1 (1 hafta) — Temel & Yasal
  ├── Modül 3: Hesap Silme + Veri İndirme
  └── Modül 1: Onboarding Flow

Sprint 2 (1 hafta) — Engagement Temeli
  ├── Modül 4: Push Notification Altyapısı
  └── Modül 5: Günlük Duygu Check-in

Sprint 3 (1 hafta) — Değer Gösterimi
  ├── Modül 2: İlerleme / Trend Grafiği
  └── Modül 7: Aylık Kişisel Rapor (basit versiyon)

Sprint 4 (1-2 hafta) — Büyüme Özellikleri
  ├── Modül 6: Hedef Takip Modülü
  └── Modül 8: Partner / Uyumluluk Modu
```

---

## Bağımlılık Haritası

```
Modül 1 (Onboarding)
    └── bağımsız, ilk yapılmalı

Modül 3 (Hesap Silme)
    └── bağımsız, yasal öncelik

Modül 4 (Push Notification)
    └── Modül 5, 6, 7'nin tam çalışması için gerekli

Modül 5 (Check-in)
    ├── Modül 2 (trend grafiğine veri sağlar)
    └── Modül 7 (rapora katkı sağlar)

Modül 6 (Hedef Takip)
    └── Modül 7 (rapora katkı sağlar)

Modül 2 (Trend Grafik)
    └── Modül 5 ve 6 verilerini gösterebilir (opsiyonel)

Modül 7 (Aylık Rapor)
    └── Modül 5 + 6 tamamlandıktan sonra tam içerik

Modül 8 (Partner Modu)
    └── Bağımsız, en son yapılabilir
```

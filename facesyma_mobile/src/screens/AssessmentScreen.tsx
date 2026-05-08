// src/screens/AssessmentScreen.tsx
import React, { useState, useMemo, useRef } from 'react';
import {
  View, Text, StyleSheet, ScrollView, TouchableOpacity,
  Dimensions, ActivityIndicator, Alert,
} from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { AssessmentAPI, TestAPI, TestSubmitResponse, StressDetails, NonverbalDetails, NonverbalAnswer } from '../services/api';
import { Card, GoldButton, SectionLabel, Badge } from '../components/ui';
import theme from '../utils/theme';
const { colors } = theme;
import { useDispatch } from 'react-redux';
import { AppDispatch } from '../store';
import { markModuleUsed } from '../store/authSlice';
import { useLanguage } from '../utils/LanguageContext';
import { t } from '../utils/i18n';
import type { ScreenProps } from '../navigation/types';
import { useOfflineError } from '../hooks/useOfflineError';

const { width } = Dimensions.get('window');

// Available languages with codes and names
const AVAILABLE_LANGUAGES = [
  { code: 'tr', flag: '🇹🇷', name: 'Türkçe' },
  { code: 'en', flag: '🇬🇧', name: 'English' },
  { code: 'de', flag: '🇩🇪', name: 'Deutsch' },
  { code: 'ru', flag: '🇷🇺', name: 'Русский' },
  { code: 'ar', flag: '🇸🇦', name: 'العربية' },
  { code: 'es', flag: '🇪🇸', name: 'Español' },
  { code: 'ko', flag: '🇰🇷', name: '한국어' },
  { code: 'ja', flag: '🇯🇵', name: '日本語' },
  { code: 'zh', flag: '🇨🇳', name: '中文' },
  { code: 'hi', flag: '🇮🇳', name: 'हिन्दी' },
  { code: 'fr', flag: '🇫🇷', name: 'Français' },
  { code: 'pt', flag: '🇵🇹', name: 'Português' },
  { code: 'bn', flag: '🇧🇩', name: 'বাংলা' },
  { code: 'id', flag: '🇮🇩', name: 'Bahasa Indonesia' },
  { code: 'ur', flag: '🇵🇰', name: 'اردو' },
  { code: 'it', flag: '🇮🇹', name: 'Italiano' },
  { code: 'vi', flag: '🇻🇳', name: 'Tiếng Việt' },
  { code: 'pl', flag: '🇵🇱', name: 'Polski' },
];

// Test types with i18n keys
// isNewService=true  → /test/ FastAPI servisi kullanılır
// requiresConsent=true → başlamadan önce sağlık onayı istenir
// newServiceType → test servisine gönderilecek gerçek tip adı (farklıysa)
const TEST_TYPES = [
  { id: 'skills',           key: 'assessment.skills',           key_desc: 'assessment.skills_desc',           emoji: '🎯', questions: 20 },
  { id: 'hr',               key: 'assessment.hr',               key_desc: 'assessment.hr_desc',               emoji: '👥', questions: 20 },
  { id: 'personality',      key: 'assessment.personality',      key_desc: 'assessment.personality_desc',      emoji: '🧠', questions: 20 },
  { id: 'career',           key: 'assessment.career',           key_desc: 'assessment.career_desc',           emoji: '💼', questions: 24 },
  { id: 'relationship',     key: 'assessment.relationship',     key_desc: 'assessment.relationship_desc',     emoji: '❤️', questions: 20 },
  { id: 'vocation',         key: 'assessment.vocation',         key_desc: 'assessment.vocation_desc',         emoji: '🏢', questions: 24 },
  { id: 'attachment',       key: 'assessment.attachment',       key_desc: 'assessment.attachment_desc',       emoji: '🔗', questions: 12 },
  { id: 'grit',             key: 'assessment.grit',             key_desc: 'assessment.grit_desc',             emoji: '💪', questions: 8  },
  { id: 'growth_mindset',   key: 'assessment.growth_mindset',   key_desc: 'assessment.growth_mindset_desc',   emoji: '🌱', questions: 8  },
  { id: 'life_satisfaction',key: 'assessment.life_satisfaction',key_desc: 'assessment.life_satisfaction_desc',emoji: '😊', questions: 5  },
  { id: 'self_compassion',  key: 'assessment.self_compassion',  key_desc: 'assessment.self_compassion_desc',  emoji: '🌸', questions: 12 },
  { id: 'body_image',       key: 'assessment.body_image',       key_desc: 'assessment.body_image_desc',       emoji: '🪞', questions: 12 },
  { id: 'self_efficacy',    key: 'assessment.self_efficacy',    key_desc: 'assessment.self_efficacy_desc',    emoji: '⚡', questions: 10 },
  { id: 'stress',           key: 'assessment.stress',           key_desc: 'assessment.stress_desc',           emoji: '🧘', questions: 10 },
  // ── Yeni servis testleri (/test/ FastAPI) ──────────────────────────────────
  { id: 'eq',             key: 'assessment.eq',             key_desc: 'assessment.eq_desc',             emoji: '💡', isNewService: true, questions: 20 },
  { id: 'values',         key: 'assessment.values',         key_desc: 'assessment.values_desc',         emoji: '⭐', isNewService: true, questions: 30 },
  { id: 'stress_clinical',    key: 'assessment.stress_clinical',       key_desc: 'assessment.stress_clinical_desc',       emoji: '🏥', isNewService: true, requiresConsent: true, newServiceType: 'stress' },
  // ── Nonverbal testler ─────────────────────────────────────────────────────────
  { id: 'emotion_recognition', key: 'assessment.emotion_recognition',  key_desc: 'assessment.emotion_recognition_desc',  emoji: '😊', isNewService: true, nonverbal: true },
  { id: 'stroop',              key: 'assessment.stroop',               key_desc: 'assessment.stroop_desc',               emoji: '🎨', isNewService: true, nonverbal: true },
] as const;

const getLikertLabels = (lang: string) => [
  t('assessment.likert_1', lang),
  t('assessment.likert_2', lang),
  t('assessment.likert_3', lang),
  t('assessment.likert_4', lang),
  t('assessment.likert_5', lang),
];

type AssessmentStep = 'select' | 'loading_questions' | 'answering' | 'submitting' | 'results';

interface Question {
  q_id: string;
  order: number;
  text: string;
  domain?: string;
  reverse_scored?: boolean;
  // Nonverbal fields
  display_type?: 'emotion_recognition' | 'stroop';
  emoji?: string;
  options?: { key: string; label: string }[];
  ink_color?: string;
  ink_hex?: string;
  word?: string;
  color_options?: { key: string; label: string; hex: string }[];
}

// Domain name translations — 44 domain keys × 18 languages
// Falls back to EN, then snake_case → Title Case
const DOMAIN_LABELS: Record<string, Record<string, string>> = {
  // skills
  problem_solving:     { tr: 'Problem Çözme', en: 'Problem Solving', de: 'Problemlösung', ru: 'Решение Задач', ar: 'حل المشكلات', es: 'Resolución de Problemas', ko: '문제 해결', ja: '問題解決', zh: '问题解决', hi: 'समस्या समाधान', fr: 'Résolution de Problèmes', pt: 'Resolução de Problemas', bn: 'সমস্যা সমাধান', id: 'Pemecahan Masalah', ur: 'مسئلہ حل کرنا', it: 'Risoluzione dei Problemi', vi: 'Giải Quyết Vấn Đề', pl: 'Rozwiązywanie Problemów' },
  empathy:             { tr: 'Empati', en: 'Empathy', de: 'Empathie', ru: 'Эмпатия', ar: 'التعاطف', es: 'Empatía', ko: '공감', ja: '共感', zh: '共情', hi: 'सहानुभूति', fr: 'Empathie', pt: 'Empatia', bn: 'সহানুভূতি', id: 'Empati', ur: 'ہمدردی', it: 'Empatia', vi: 'Sự Đồng Cảm', pl: 'Empatia' },
  organization:        { tr: 'Organizasyon', en: 'Organization', de: 'Organisation', ru: 'Организация', ar: 'التنظيم', es: 'Organización', ko: '조직력', ja: '組織力', zh: '组织能力', hi: 'संगठन', fr: 'Organisation', pt: 'Organização', bn: 'সংগঠন', id: 'Organisasi', ur: 'تنظیم', it: 'Organizzazione', vi: 'Tổ Chức', pl: 'Organizacja' },
  learning_speed:      { tr: 'Öğrenme Hızı', en: 'Learning Speed', de: 'Lerngeschwindigkeit', ru: 'Скорость Обучения', ar: 'سرعة التعلم', es: 'Velocidad de Aprendizaje', ko: '학습 속도', ja: '学習速度', zh: '学习速度', hi: 'सीखने की गति', fr: "Vitesse d'Apprentissage", pt: 'Velocidade de Aprendizado', bn: 'শেখার গতি', id: 'Kecepatan Belajar', ur: 'سیکھنے کی رفتار', it: 'Velocità di Apprendimento', vi: 'Tốc Độ Học', pl: 'Szybkość Uczenia Się' },
  decision_making:     { tr: 'Karar Verme', en: 'Decision Making', de: 'Entscheidungsfindung', ru: 'Принятие Решений', ar: 'صنع القرار', es: 'Toma de Decisiones', ko: '의사결정', ja: '意思決定', zh: '决策', hi: 'निर्णय लेना', fr: 'Prise de Décision', pt: 'Tomada de Decisão', bn: 'সিদ্ধান্ত গ্রহণ', id: 'Pengambilan Keputusan', ur: 'فیصلہ سازی', it: 'Presa di Decisione', vi: 'Ra Quyết Định', pl: 'Podejmowanie Decyzji' },
  // hr
  leadership:          { tr: 'Liderlik', en: 'Leadership', de: 'Führung', ru: 'Лидерство', ar: 'القيادة', es: 'Liderazgo', ko: '리더십', ja: 'リーダーシップ', zh: '领导力', hi: 'नेतृत्व', fr: 'Leadership', pt: 'Liderança', bn: 'নেতৃত্ব', id: 'Kepemimpinan', ur: 'قیادت', it: 'Leadership', vi: 'Lãnh Đạo', pl: 'Przywództwo' },
  team_fit:            { tr: 'Takım Uyumu', en: 'Team Fit', de: 'Teamfähigkeit', ru: 'Командная Работа', ar: 'ملاءمة الفريق', es: 'Trabajo en Equipo', ko: '팀 적합성', ja: 'チーム適合性', zh: '团队契合', hi: 'टीम फिट', fr: "Intégration d'Équipe", pt: 'Adaptação à Equipe', bn: 'দলের সাথে মানানসই', id: 'Kesesuaian Tim', ur: 'ٹیم مطابقت', it: 'Adattamento al Team', vi: 'Phù Hợp Nhóm', pl: 'Dopasowanie do Zespołu' },
  communication:       { tr: 'İletişim', en: 'Communication', de: 'Kommunikation', ru: 'Коммуникация', ar: 'التواصل', es: 'Comunicación', ko: '커뮤니케이션', ja: 'コミュニケーション', zh: '沟通', hi: 'संचार', fr: 'Communication', pt: 'Comunicação', bn: 'যোগাযোগ', id: 'Komunikasi', ur: 'مواصلات', it: 'Comunicazione', vi: 'Giao Tiếp', pl: 'Komunikacja' },
  stress_tolerance:    { tr: 'Stres Toleransı', en: 'Stress Tolerance', de: 'Stresstoleranz', ru: 'Устойчивость к Стрессу', ar: 'تحمل الضغط', es: 'Tolerancia al Estrés', ko: '스트레스 내성', ja: 'ストレス耐性', zh: '抗压能力', hi: 'तनाव सहनशीलता', fr: 'Tolérance au Stress', pt: 'Tolerância ao Estresse', bn: 'চাপ সহনশীলতা', id: 'Toleransi Stres', ur: 'تناؤ برداشت', it: 'Tolleranza allo Stress', vi: 'Chịu Đựng Căng Thẳng', pl: 'Tolerancja na Stres' },
  motivation:          { tr: 'Motivasyon', en: 'Motivation', de: 'Motivation', ru: 'Мотивация', ar: 'الدافعية', es: 'Motivación', ko: '동기', ja: 'モチベーション', zh: '动力', hi: 'प्रेरणा', fr: 'Motivation', pt: 'Motivação', bn: 'অনুপ্রেরণা', id: 'Motivasi', ur: 'حوصلہ افزائی', it: 'Motivazione', vi: 'Động Lực', pl: 'Motywacja' },
  // personality (Big Five)
  openness:            { tr: 'Açıklık', en: 'Openness', de: 'Offenheit', ru: 'Открытость', ar: 'الانفتاح', es: 'Apertura', ko: '개방성', ja: '開放性', zh: '开放性', hi: 'खुलापन', fr: 'Ouverture', pt: 'Abertura', bn: 'উন্মুক্ততা', id: 'Keterbukaan', ur: 'کشادگی', it: 'Apertura', vi: 'Cởi Mở', pl: 'Otwartość' },
  conscientiousness:   { tr: 'Sorumluluk', en: 'Conscientiousness', de: 'Gewissenhaftigkeit', ru: 'Добросовестность', ar: 'الضمير', es: 'Responsabilidad', ko: '성실성', ja: '誠実性', zh: '尽责性', hi: 'कर्तव्यनिष्ठा', fr: 'Conscience', pt: 'Conscienciosidade', bn: 'বিবেকবোধ', id: 'Ketelitian', ur: 'ذمہ داری', it: 'Coscienziosità', vi: 'Tận Tâm', pl: 'Sumienność' },
  extraversion:        { tr: 'Dışadönüklük', en: 'Extraversion', de: 'Extraversion', ru: 'Экстраверсия', ar: 'الانبساطية', es: 'Extraversión', ko: '외향성', ja: '外向性', zh: '外向性', hi: 'बहिर्मुखता', fr: 'Extraversion', pt: 'Extroversão', bn: 'বহির্মুখিতা', id: 'Ekstraversi', ur: 'بیرون گردی', it: 'Estroversione', vi: 'Hướng Ngoại', pl: 'Ekstrawersja' },
  agreeableness:       { tr: 'Uyumluluk', en: 'Agreeableness', de: 'Verträglichkeit', ru: 'Доброжелательность', ar: 'الطيبة', es: 'Amabilidad', ko: '친화성', ja: '協調性', zh: '宜人性', hi: 'सहमतता', fr: 'Agréabilité', pt: 'Amabilidade', bn: 'সৌহার্দ্য', id: 'Keramahan', ur: 'موافقت', it: 'Gradevolezza', vi: 'Dễ Chịu', pl: 'Ugodowość' },
  neuroticism:         { tr: 'Nevrotizm', en: 'Neuroticism', de: 'Neurotizismus', ru: 'Нейротизм', ar: 'العصابية', es: 'Neuroticismo', ko: '신경성', ja: '神経症的傾向', zh: '神经质', hi: 'विक्षिप्तता', fr: 'Névrosisme', pt: 'Neuroticismo', bn: 'নিউরোটিসিজম', id: 'Neurotisisme', ur: 'اعصابیت', it: 'Nevroticismo', vi: 'Bất Ổn Cảm Xúc', pl: 'Neurotyczność' },
  // career
  analytical:          { tr: 'Analitik', en: 'Analytical', de: 'Analytisch', ru: 'Аналитический', ar: 'تحليلي', es: 'Analítico', ko: '분석적', ja: '分析', zh: '分析型', hi: 'विश्लेषणात्मक', fr: 'Analytique', pt: 'Analítico', bn: 'বিশ্লেষণমূলক', id: 'Analitis', ur: 'تجزیاتی', it: 'Analitico', vi: 'Phân Tích', pl: 'Analityczny' },
  creative:            { tr: 'Yaratıcı', en: 'Creative', de: 'Kreativ', ru: 'Творческий', ar: 'إبداعي', es: 'Creativo', ko: '창의적', ja: 'クリエイティブ', zh: '创意型', hi: 'रचनात्मक', fr: 'Créatif', pt: 'Criativo', bn: 'সৃজনশীল', id: 'Kreatif', ur: 'تخلیقی', it: 'Creativo', vi: 'Sáng Tạo', pl: 'Kreatywny' },
  social:              { tr: 'Sosyal', en: 'Social', de: 'Sozial', ru: 'Социальный', ar: 'اجتماعي', es: 'Social', ko: '사회적', ja: 'ソーシャル', zh: '社交型', hi: 'सामाजिक', fr: 'Social', pt: 'Social', bn: 'সামাজিক', id: 'Sosial', ur: 'سماجی', it: 'Sociale', vi: 'Xã Hội', pl: 'Społeczny' },
  entrepreneurial:     { tr: 'Girişimci', en: 'Entrepreneurial', de: 'Unternehmerisch', ru: 'Предпринимательский', ar: 'ريادي', es: 'Emprendedor', ko: '기업가적', ja: '起業家的', zh: '创业型', hi: 'उद्यमशील', fr: 'Entrepreneurial', pt: 'Empreendedor', bn: 'উদ্যোক্তা', id: 'Kewirausahaan', ur: 'کاروباری', it: 'Imprenditoriale', vi: 'Khởi Nghiệp', pl: 'Przedsiębiorczy' },
  managerial:          { tr: 'Yönetimsel', en: 'Managerial', de: 'Führungsbezogen', ru: 'Управленческий', ar: 'إداري', es: 'Gerencial', ko: '관리적', ja: '管理的', zh: '管理型', hi: 'प्रबंधकीय', fr: 'Managérial', pt: 'Gerencial', bn: 'ব্যবস্থাপনামূলক', id: 'Manajerial', ur: 'انتظامی', it: 'Manageriale', vi: 'Quản Lý', pl: 'Menedżerski' },
  technical:           { tr: 'Teknik', en: 'Technical', de: 'Technisch', ru: 'Технический', ar: 'تقني', es: 'Técnico', ko: '기술적', ja: 'テクニカル', zh: '技术型', hi: 'तकनीकी', fr: 'Technique', pt: 'Técnico', bn: 'প্রযুক্তিগত', id: 'Teknis', ur: 'تکنیکی', it: 'Tecnico', vi: 'Kỹ Thuật', pl: 'Techniczny' },
  // vocation (Holland RIASEC)
  realistic:           { tr: 'Gerçekçi', en: 'Realistic', de: 'Realistisch', ru: 'Реалистичный', ar: 'واقعي', es: 'Realista', ko: '현실형', ja: 'リアリスティック', zh: '现实型', hi: 'यथार्थवादी', fr: 'Réaliste', pt: 'Realista', bn: 'বাস্তববাদী', id: 'Realistis', ur: 'حقیقت پسند', it: 'Realistico', vi: 'Thực Tế', pl: 'Realistyczny' },
  investigative:       { tr: 'Araştırmacı', en: 'Investigative', de: 'Forschend', ru: 'Исследовательский', ar: 'استقصائي', es: 'Investigador', ko: '탐구형', ja: '研究者的', zh: '研究型', hi: 'अन्वेषणात्मक', fr: 'Investigateur', pt: 'Investigativo', bn: 'অনুসন্ধানী', id: 'Investigatif', ur: 'تحقیقی', it: 'Investigativo', vi: 'Khám Phá', pl: 'Badawczy' },
  artistic:            { tr: 'Artistik', en: 'Artistic', de: 'Künstlerisch', ru: 'Художественный', ar: 'فني', es: 'Artístico', ko: '예술형', ja: '芸術的', zh: '艺术型', hi: 'कलात्मक', fr: 'Artistique', pt: 'Artístico', bn: 'শৈল্পিক', id: 'Artistik', ur: 'فنکارانہ', it: 'Artistico', vi: 'Nghệ Thuật', pl: 'Artystyczny' },
  enterprising:        { tr: 'Girişken', en: 'Enterprising', de: 'Unternehmerisch', ru: 'Предприимчивый', ar: 'ريادي', es: 'Emprendedor', ko: '진취형', ja: 'エンタープライジング', zh: '进取型', hi: 'साहसी', fr: 'Entreprenant', pt: 'Empreendedor', bn: 'উদ্যোগী', id: 'Wirausaha', ur: 'پر عزم', it: 'Intraprendente', vi: 'Táo Bạo', pl: 'Przedsiębiorczy' },
  conventional:        { tr: 'Geleneksel', en: 'Conventional', de: 'Konventionell', ru: 'Традиционный', ar: 'تقليدي', es: 'Convencional', ko: '관습형', ja: 'コンベンショナル', zh: '传统型', hi: 'परंपरागत', fr: 'Conventionnel', pt: 'Convencional', bn: 'প্রচলিত', id: 'Konvensional', ur: 'روایتی', it: 'Convenzionale', vi: 'Truyền Thống', pl: 'Konwencjonalny' },
  // relationship
  love_language:       { tr: 'Sevgi Dili', en: 'Love Language', de: 'Liebessprache', ru: 'Язык Любви', ar: 'لغة الحب', es: 'Lenguaje del Amor', ko: '사랑의 언어', ja: '愛の言語', zh: '爱的语言', hi: 'प्रेम भाषा', fr: "Langage de l'Amour", pt: 'Linguagem do Amor', bn: 'ভালোবাসার ভাষা', id: 'Bahasa Cinta', ur: 'محبت کی زبان', it: "Linguaggio dell'Amore", vi: 'Ngôn Ngữ Tình Yêu', pl: 'Język Miłości' },
  conflict_style:      { tr: 'Çatışma Tarzı', en: 'Conflict Style', de: 'Konfliktstil', ru: 'Стиль Конфликта', ar: 'أسلوب الصراع', es: 'Estilo de Conflicto', ko: '갈등 스타일', ja: '対立スタイル', zh: '冲突风格', hi: 'संघर्ष शैली', fr: 'Style de Conflit', pt: 'Estilo de Conflito', bn: 'দ্বন্দ্ব শৈলী', id: 'Gaya Konflik', ur: 'تنازعہ کا انداز', it: 'Stile di Conflitto', vi: 'Phong Cách Xung Đột', pl: 'Styl Konfliktu' },
  intimacy_needs:      { tr: 'Yakınlık İhtiyacı', en: 'Intimacy Needs', de: 'Intimität', ru: 'Потребность в Близости', ar: 'الحاجة للحميمية', es: 'Necesidades de Intimidad', ko: '친밀감 욕구', ja: '親密さのニーズ', zh: '亲密需求', hi: 'अंतरंगता की जरूरत', fr: "Besoins d'Intimité", pt: 'Necessidades de Intimidade', bn: 'ঘনিষ্ঠতার প্রয়োজন', id: 'Kebutuhan Intimasi', ur: 'قربت کی ضرورت', it: "Bisogni d'Intimità", vi: 'Nhu Cầu Thân Mật', pl: 'Potrzeby Intymności' },
  relationship_values: { tr: 'İlişki Değerleri', en: 'Relationship Values', de: 'Beziehungswerte', ru: 'Ценности Отношений', ar: 'قيم العلاقة', es: 'Valores Relacionales', ko: '관계 가치', ja: '関係の価値観', zh: '关系价值观', hi: 'संबंध मूल्य', fr: 'Valeurs Relationnelles', pt: 'Valores de Relacionamento', bn: 'সম্পর্কের মূল্যবোধ', id: 'Nilai Hubungan', ur: 'رشتوں کی اقدار', it: 'Valori Relazionali', vi: 'Giá Trị Mối Quan Hệ', pl: 'Wartości w Związku' },
  // attachment
  anxiety:             { tr: 'Kaygı', en: 'Anxiety', de: 'Angst', ru: 'Тревога', ar: 'القلق', es: 'Ansiedad', ko: '불안', ja: '不安', zh: '焦虑', hi: 'चिंता', fr: 'Anxiété', pt: 'Ansiedade', bn: 'উদ্বেগ', id: 'Kecemasan', ur: 'پریشانی', it: 'Ansia', vi: 'Lo Lắng', pl: 'Lęk' },
  avoidance:           { tr: 'Kaçınma', en: 'Avoidance', de: 'Vermeidung', ru: 'Избегание', ar: 'التجنب', es: 'Evitación', ko: '회피', ja: '回避', zh: '回避', hi: 'परिहार', fr: 'Évitement', pt: 'Evitação', bn: 'পরিহার', id: 'Penghindaran', ur: 'گریز', it: 'Evitamento', vi: 'Né Tránh', pl: 'Unikanie' },
  // grit
  perseverance:        { tr: 'Azim', en: 'Perseverance', de: 'Ausdauer', ru: 'Настойчивость', ar: 'المثابرة', es: 'Perseverancia', ko: '인내', ja: '忍耐力', zh: '毅力', hi: 'दृढ़ता', fr: 'Persévérance', pt: 'Perseverança', bn: 'অধ্যবসায়', id: 'Ketekunan', ur: 'استقامت', it: 'Perseveranza', vi: 'Kiên Trì', pl: 'Wytrwałość' },
  passion:             { tr: 'Tutku', en: 'Passion', de: 'Leidenschaft', ru: 'Страсть', ar: 'الشغف', es: 'Pasión', ko: '열정', ja: '情熱', zh: '热情', hi: 'जुनून', fr: 'Passion', pt: 'Paixão', bn: 'আবেগ', id: 'Gairah', ur: 'جذبہ', it: 'Passione', vi: 'Đam Mê', pl: 'Pasja' },
  // single-domain tests (key = test name)
  growth_mindset:      { tr: 'Büyüme Zihniyeti', en: 'Growth Mindset', de: 'Wachstumsorientierung', ru: 'Установка на Рост', ar: 'عقلية النمو', es: 'Mentalidad de Crecimiento', ko: '성장 마인드셋', ja: 'グロースマインドセット', zh: '成长型思维', hi: 'विकास मानसिकता', fr: "État d'Esprit de Croissance", pt: 'Mentalidade de Crescimento', bn: 'বৃদ্ধির মানসিকতা', id: 'Pola Pikir Berkembang', ur: 'ترقی کی ذہنیت', it: 'Mentalità di Crescita', vi: 'Tư Duy Phát Triển', pl: 'Nastawienie na Wzrost' },
  life_satisfaction:   { tr: 'Yaşam Doyumu', en: 'Life Satisfaction', de: 'Lebenszufriedenheit', ru: 'Удовлетворённость Жизнью', ar: 'الرضا عن الحياة', es: 'Satisfacción Vital', ko: '삶의 만족도', ja: '生活満足度', zh: '生活满意度', hi: 'जीवन संतुष्टि', fr: 'Satisfaction de Vie', pt: 'Satisfação de Vida', bn: 'জীবন সন্তুষ্টি', id: 'Kepuasan Hidup', ur: 'زندگی کا اطمینان', it: 'Soddisfazione di Vita', vi: 'Sự Hài Lòng Cuộc Sống', pl: 'Satysfakcja z Życia' },
  self_efficacy:       { tr: 'Öz-Yeterlik', en: 'Self-Efficacy', de: 'Selbstwirksamkeit', ru: 'Самоэффективность', ar: 'الكفاءة الذاتية', es: 'Autoeficacia', ko: '자기효능감', ja: '自己効力感', zh: '自我效能', hi: 'आत्म-प्रभावकारिता', fr: 'Auto-Efficacité', pt: 'Autoeficácia', bn: 'আত্ম-কার্যকারিতা', id: 'Efikasi Diri', ur: 'خود اعتمادی', it: 'Autoefficacia', vi: 'Tự Hiệu Quả', pl: 'Poczucie Własnej Skuteczności' },
  perceived_stress:    { tr: 'Algılanan Stres', en: 'Perceived Stress', de: 'Wahrgenommener Stress', ru: 'Воспринимаемый Стресс', ar: 'الضغط المُدرَك', es: 'Estrés Percibido', ko: '지각된 스트레스', ja: '知覚されたストレス', zh: '感知压力', hi: 'अनुभवित तनाव', fr: 'Stress Perçu', pt: 'Estresse Percebido', bn: 'অনুভূত চাপ', id: 'Stres yang Dirasakan', ur: 'محسوس شدہ تناؤ', it: 'Stress Percepito', vi: 'Căng Thẳng Cảm Nhận', pl: 'Postrzegany Stres' },
  // self_compassion subscales
  self_kindness:       { tr: 'Öz-Nezaket', en: 'Self-Kindness', de: 'Selbstgüte', ru: 'Доброта к Себе', ar: 'اللطف بالنفس', es: 'Bondad hacia Uno Mismo', ko: '자기 친절', ja: '自己への親切', zh: '自我善待', hi: 'स्वयं पर दया', fr: 'Gentillesse envers Soi', pt: 'Bondade para Consigo', bn: 'আত্ম-সদয়তা', id: 'Kebaikan Diri', ur: 'خود پر مہربانی', it: 'Gentilezza verso Se Stessi', vi: 'Tử Tế Với Bản Thân', pl: 'Życzliwość wobec Siebie' },
  self_judgment:       { tr: 'Öz-Yargılama', en: 'Self-Judgment', de: 'Selbstbeurteilung', ru: 'Самооценка', ar: 'الحكم على الذات', es: 'Autocrítica', ko: '자기 판단', ja: '自己評価', zh: '自我评判', hi: 'स्व-आलोचना', fr: 'Auto-Jugement', pt: 'Auto-Julgamento', bn: 'আত্ম-বিচার', id: 'Penilaian Diri', ur: 'خود فیصلہ', it: 'Auto-Giudizio', vi: 'Tự Phán Xét', pl: 'Samoocena' },
  common_humanity:     { tr: 'Ortak İnsanlık', en: 'Common Humanity', de: 'Gemeinsame Menschlichkeit', ru: 'Общая Человечность', ar: 'الإنسانية المشتركة', es: 'Humanidad Compartida', ko: '공통 인류', ja: '共通の人間性', zh: '共同人性', hi: 'सामान्य मानवता', fr: 'Humanité Commune', pt: 'Humanidade Comum', bn: 'সাধারণ মানবতা', id: 'Kemanusiaan Bersama', ur: 'مشترکہ انسانیت', it: 'Umanità Comune', vi: 'Nhân Loại Chung', pl: 'Wspólne Człowieczeństwo' },
  isolation:           { tr: 'İzolasyon', en: 'Isolation', de: 'Isolation', ru: 'Изоляция', ar: 'العزلة', es: 'Aislamiento', ko: '고립', ja: '孤立', zh: '孤立', hi: 'अलगाव', fr: 'Isolement', pt: 'Isolamento', bn: 'বিচ্ছিন্নতা', id: 'Isolasi', ur: 'تنہائی', it: 'Isolamento', vi: 'Cô Lập', pl: 'Izolacja' },
  mindfulness:         { tr: 'Bilinçli Farkındalık', en: 'Mindfulness', de: 'Achtsamkeit', ru: 'Осознанность', ar: 'اليقظة الذهنية', es: 'Atención Plena', ko: '마음챙김', ja: 'マインドフルネス', zh: '正念', hi: 'सचेतनता', fr: 'Pleine Conscience', pt: 'Atenção Plena', bn: 'সচেতনতা', id: 'Kesadaran Penuh', ur: 'ذہانت', it: 'Consapevolezza', vi: 'Chánh Niệm', pl: 'Uważność' },
  overidentification:  { tr: 'Aşırı Özdeşleşme', en: 'Overidentification', de: 'Überidentifikation', ru: 'Гиперидентификация', ar: 'المبالغة في التماهي', es: 'Sobreidentificación', ko: '과잉동일시', ja: '過剰同一視', zh: '过度认同', hi: 'अतिपहचान', fr: 'Sur-Identification', pt: 'Sobre-Identificação', bn: 'অতিরিক্ত পরিচয়', id: 'Identifikasi Berlebihan', ur: 'حد سے زیادہ شناخت', it: 'Sovra-Identificazione', vi: 'Đồng Nhất Quá Mức', pl: 'Nadmierna Identyfikacja' },
  // eq
  self_awareness:      { tr: 'Öz Farkındalık', en: 'Self-Awareness', de: 'Selbstwahrnehmung', ru: 'Самосознание', ar: 'الوعي الذاتي', es: 'Autoconciencia', ko: '자기인식', ja: '自己認識', zh: '自我意识', hi: 'आत्म-जागरूकता', fr: 'Conscience de Soi', pt: 'Autoconsciência', bn: 'আত্ম-সচেতনতা', id: 'Kesadaran Diri', ur: 'خود آگاہی', it: 'Autoconsapevolezza', vi: 'Tự Nhận Thức', pl: 'Samoświadomość' },
  self_regulation:     { tr: 'Öz Düzenleme', en: 'Self-Regulation', de: 'Selbstregulierung', ru: 'Саморегуляция', ar: 'التنظيم الذاتي', es: 'Autorregulación', ko: '자기조절', ja: '自己調整', zh: '自我调节', hi: 'स्व-नियमन', fr: 'Autorégulation', pt: 'Autorregulação', bn: 'আত্ম-নিয়ন্ত্রণ', id: 'Regulasi Diri', ur: 'خود ضبطی', it: 'Autoregolazione', vi: 'Tự Điều Chỉnh', pl: 'Samoregulacja' },
  social_skills:       { tr: 'Sosyal Beceriler', en: 'Social Skills', de: 'Soziale Kompetenz', ru: 'Социальные Навыки', ar: 'المهارات الاجتماعية', es: 'Habilidades Sociales', ko: '사회적 기술', ja: '社会的スキル', zh: '社交技能', hi: 'सामाजिक कौशल', fr: 'Compétences Sociales', pt: 'Habilidades Sociais', bn: 'সামাজিক দক্ষতা', id: 'Keterampilan Sosial', ur: 'سماجی مہارتیں', it: 'Competenze Sociali', vi: 'Kỹ Năng Xã Hội', pl: 'Umiejętności Społeczne' },
  // values (Schwartz 10 domains)
  universalism:        { tr: 'Evrensellik', en: 'Universalism', de: 'Universalismus', ru: 'Универсализм', ar: 'العالمية', es: 'Universalismo', ko: '보편주의', ja: '普遍主義', zh: '普世主义', hi: 'सार्वभौमिकता', fr: 'Universalisme', pt: 'Universalismo', bn: 'সর্বজনীনতা', id: 'Universalisme', ur: 'آفاقیت', it: 'Universalismo', vi: 'Chủ Nghĩa Phổ Quát', pl: 'Uniwersalizm' },
  self_direction:      { tr: 'Öz Yönlendirme', en: 'Self-Direction', de: 'Selbstbestimmung', ru: 'Самостоятельность', ar: 'التوجيه الذاتي', es: 'Autodirección', ko: '자기방향성', ja: '自己決定', zh: '自主导向', hi: 'स्व-निर्देशन', fr: 'Autodirection', pt: 'Autodireção', bn: 'আত্ম-নির্দেশনা', id: 'Pengarahan Diri', ur: 'خود رہنمائی', it: 'Autodirezione', vi: 'Tự Định Hướng', pl: 'Samokierowanie' },
  achievement:         { tr: 'Başarı', en: 'Achievement', de: 'Leistung', ru: 'Достижение', ar: 'الإنجاز', es: 'Logro', ko: '성취', ja: '達成', zh: '成就', hi: 'उपलब्धि', fr: 'Réussite', pt: 'Realização', bn: 'অর্জন', id: 'Pencapaian', ur: 'کامیابی', it: 'Realizzazione', vi: 'Thành Tích', pl: 'Osiągnięcia' },
  security:            { tr: 'Güvenlik', en: 'Security', de: 'Sicherheit', ru: 'Безопасность', ar: 'الأمان', es: 'Seguridad', ko: '안전', ja: '安全', zh: '安全感', hi: 'सुरक्षा', fr: 'Sécurité', pt: 'Segurança', bn: 'নিরাপত্তা', id: 'Keamanan', ur: 'حفاظت', it: 'Sicurezza', vi: 'An Toàn', pl: 'Bezpieczeństwo' },
  hedonism:            { tr: 'Hazcılık', en: 'Hedonism', de: 'Hedonismus', ru: 'Гедонизм', ar: 'المتعة', es: 'Hedonismo', ko: '쾌락주의', ja: '快楽主義', zh: '享乐主义', hi: 'सुखवाद', fr: 'Hédonisme', pt: 'Hedonismo', bn: 'ভোগবাদ', id: 'Hedonisme', ur: 'لذت پرستی', it: 'Edonismo', vi: 'Chủ Nghĩa Khoái Lạc', pl: 'Hedonizm' },
  benevolence:         { tr: 'Yardımseverlik', en: 'Benevolence', de: 'Wohlwollen', ru: 'Доброжелательность', ar: 'البر والإحسان', es: 'Benevolencia', ko: '박애', ja: '博愛', zh: '仁爱', hi: 'परोपकार', fr: 'Bienveillance', pt: 'Benevolência', bn: 'পরোপকার', id: 'Kebaikan Hati', ur: 'احسان', it: 'Benevolenza', vi: 'Nhân Từ', pl: 'Życzliwość' },
  stimulation:         { tr: 'Uyarım', en: 'Stimulation', de: 'Stimulation', ru: 'Стимуляция', ar: 'الإثارة', es: 'Estimulación', ko: '자극', ja: '刺激', zh: '刺激', hi: 'उत्तेजना', fr: 'Stimulation', pt: 'Estimulação', bn: 'উদ্দীপনা', id: 'Stimulasi', ur: 'تحریک', it: 'Stimolazione', vi: 'Kích Thích', pl: 'Stymulacja' },
  power:               { tr: 'Güç', en: 'Power', de: 'Macht', ru: 'Власть', ar: 'القوة والسلطة', es: 'Poder', ko: '권력', ja: '権力', zh: '权力', hi: 'शक्ति', fr: 'Pouvoir', pt: 'Poder', bn: 'ক্ষমতা', id: 'Kekuasaan', ur: 'اقتدار', it: 'Potere', vi: 'Quyền Lực', pl: 'Władza' },
  conformity:          { tr: 'Uyum', en: 'Conformity', de: 'Konformität', ru: 'Конформность', ar: 'الامتثال', es: 'Conformidad', ko: '순응', ja: '同調性', zh: '顺从', hi: 'अनुरूपता', fr: 'Conformité', pt: 'Conformidade', bn: 'সামঞ্জস্য', id: 'Kesesuaian', ur: 'مطابقت', it: 'Conformità', vi: 'Sự Tuân Thủ', pl: 'Konformizm' },
  tradition:           { tr: 'Gelenek', en: 'Tradition', de: 'Tradition', ru: 'Традиция', ar: 'التقاليد', es: 'Tradición', ko: '전통', ja: '伝統', zh: '传统', hi: 'परंपरा', fr: 'Tradition', pt: 'Tradição', bn: 'ঐতিহ্য', id: 'Tradisi', ur: 'روایت', it: 'Tradizione', vi: 'Truyền Thống', pl: 'Tradycja' },
  // body_image
  appearance_evaluation: { tr: 'Görünüm Değerlendirmesi', en: 'Appearance Evaluation', de: 'Aussehenbewertung', ru: 'Оценка Внешности', ar: 'تقييم المظهر', es: 'Evaluación de la Apariencia', ko: '외모 평가', ja: '外見評価', zh: '外貌评价', hi: 'उपस्थिति मूल्यांकन', fr: "Évaluation de l'Apparence", pt: 'Avaliação da Aparência', bn: 'চেহারা মূল্যায়ন', id: 'Evaluasi Penampilan', ur: 'ظاہری جائزہ', it: "Valutazione dell'Aspetto", vi: 'Đánh Giá Ngoại Hình', pl: 'Ocena Wyglądu' },
  body_satisfaction:   { tr: 'Beden Memnuniyeti', en: 'Body Satisfaction', de: 'Körperzufriedenheit', ru: 'Удовлетворённость Телом', ar: 'الرضا عن الجسد', es: 'Satisfacción Corporal', ko: '신체 만족도', ja: '体の満足度', zh: '身体满意度', hi: 'शरीर संतुष्टि', fr: 'Satisfaction Corporelle', pt: 'Satisfação Corporal', bn: 'শরীরের সন্তুষ্টি', id: 'Kepuasan Tubuh', ur: 'جسمانی اطمینان', it: 'Soddisfazione Corporea', vi: 'Sự Hài Lòng Cơ Thể', pl: 'Satysfakcja z Ciała' },
};

const tDomain = (key: string, lang: string): string => {
  const entry = DOMAIN_LABELS[key];
  if (!entry) return key.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase());
  return entry[lang] ?? entry['en'] ?? key;
};

// Yeni test servisi için severity çevirisi
const SEVERITY_KEYS: Record<string, string> = {
  minimal: 'assessment.severity_minimal',
  mild: 'assessment.severity_mild',
  moderate: 'assessment.severity_moderate',
  moderately_severe: 'assessment.severity_moderately_severe',
  severe: 'assessment.severity_severe',
};

interface QuestionData {
  success: boolean;
  data: {
    test_type: string;
    version: string;
    description: string;
    domains: string[];
    questions: Question[];
    scale: Record<string, string>;
    total_questions: number;
  };
}

interface SubmissionResponse {
  success: boolean;
  data: {
    test_type: string;
    overall_score: number;
    overall_level: string;
    overall_level_tr: string;
    breakdown: Record<string, { score: number; level: string; level_tr: string; questions_answered: number; description?: string }>;
    recommendations: string[];
    recommendations_status: string;
    narrative?: string;
    strengths?: { name: string; score: number }[];
    growth_areas?: { name: string; score: number }[];
    responses_counted: number;
  };
}

const AssessmentScreen = ({ navigation }: ScreenProps<'Assessment'>) => {
  const insets = useSafeAreaInsets();
  const dispatch = useDispatch<AppDispatch>();
  const [step, setStep] = useState<AssessmentStep>('select');
  const [selectedTest, setSelectedTest] = useState<string | null>(null);
  const { lang, setLang } = useLanguage();
  const getErrorMessage = useOfflineError();

  const [questions, setQuestions] = useState<Question[]>([]);
  const [responses, setResponses] = useState<Record<string, number>>({});
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<SubmissionResponse | null>(null);
  // Yeni test servisi state'leri
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [newServiceResult, setNewServiceResult] = useState<TestSubmitResponse | null>(null);
  const [scaleLabels, setScaleLabels] = useState<string[]>([]);
  const [scaleMin, setScaleMin] = useState<number>(1);
  const [scaleMax, setScaleMax] = useState<number>(5);
  // Nonverbal test state'leri (tek soru gösterimi + zamanlama)
  const [nvIndex, setNvIndex] = useState(0);
  const [nvAnswers, setNvAnswers] = useState<NonverbalAnswer[]>([]);
  const questionStartRef = useRef<number>(Date.now());
  // Must be at top level — not inside conditionals (Rules of Hooks)
  const LIKERT_LABELS = useMemo(() => getLikertLabels(lang), [lang]);

  // Seç: Test türü seç
  const startTest = async (testId: string) => {
    const testMeta = TEST_TYPES.find(t => t.id === testId);

    // Yeni test servisi mi?
    if (testMeta && 'isNewService' in testMeta && testMeta.isNewService) {
      // Sağlık onayı gerektiren testler için önce dialog
      if ('requiresConsent' in testMeta && testMeta.requiresConsent) {
        Alert.alert(
          t('assessment.health_consent_title', lang),
          t('assessment.health_consent_body', lang),
          [
            { text: t('assessment.consent_cancel', lang), style: 'cancel' },
            { text: t('assessment.consent_accept', lang), onPress: () => _startNewServiceTest(testId, testMeta) },
          ]
        );
        return;
      }
      _startNewServiceTest(testId, testMeta);
      return;
    }

    // Eski servis akışı
    setSelectedTest(testId);
    setStep('loading_questions');
    setLoading(true);
    const errTitle = t('common.error', lang);
    const errGeneric = t('assessment.error_generic', lang);
    try {
      const data = await AssessmentAPI.getQuestions(testId, lang);
      if (data.success) {
        setQuestions(data.data.questions);
        setResponses({});
        setStep('answering');
      } else {
        Alert.alert(errTitle, t('assessment.error_load', lang));
        setStep('select');
      }
    } catch (error: any) {
      Alert.alert(errTitle, error.response?.data?.detail || errGeneric);
      setStep('select');
    } finally {
      setLoading(false);
    }
  };

  const _startNewServiceTest = async (testId: string, testMeta: any) => {
    setSelectedTest(testId);
    setStep('loading_questions');
    setLoading(true);
    const apiType = testMeta.newServiceType || testId;
    try {
      const data = await TestAPI.startTest(apiType, lang);
      setSessionId(data.session_id);
      setQuestions(data.questions);
      const scaleObj = (data.questions[0] as any)?.scale;
      setScaleLabels(scaleObj?.labels || []);
      setScaleMin(scaleObj?.min ?? 1);
      setScaleMax(scaleObj?.max ?? 5);
      setResponses({});
      setNvIndex(0);
      setNvAnswers([]);
      questionStartRef.current = Date.now();
      setStep('answering');
    } catch (error: any) {
      Alert.alert(t('common.error', lang), getErrorMessage(error));
      setStep('select');
    } finally {
      setLoading(false);
    }
  };

  // Cevapları gönder
  const submitResponses = async () => {
    const testMeta2 = TEST_TYPES.find(tt => tt.id === selectedTest);
    const isNonverbal2 = testMeta2 && 'nonverbal' in testMeta2 && testMeta2.nonverbal;
    const notDone = isNonverbal2
      ? nvAnswers.length < questions.length
      : Object.keys(responses).length < questions.length;
    if (notDone) {
      Alert.alert(t('common.select_required', lang), t('assessment.error_incomplete', lang));
      return;
    }
    if (!selectedTest) return;

    setStep('submitting');
    setLoading(true);
    const errTitle = t('common.error', lang);
    const errGeneric = t('assessment.error_generic', lang);
    const testMeta = TEST_TYPES.find(tt => tt.id === selectedTest);
    const isNewService = testMeta && 'isNewService' in testMeta && testMeta.isNewService;
    const isNonverbal = testMeta && 'nonverbal' in testMeta && testMeta.nonverbal;
    const answers: NonverbalAnswer[] = isNonverbal
      ? nvAnswers
      : Object.entries(responses).map(([q_id, score]) => ({ q_id, score }));

    try {
      if (isNewService && sessionId) {
        const apiType = ('newServiceType' in testMeta && testMeta.newServiceType) || selectedTest;
        const data = await TestAPI.submitTest(sessionId, apiType as string, lang, answers);
        setNewServiceResult(data);
        setResult(null);
        setStep('results');
        dispatch(markModuleUsed('assessment'));
      } else {
        const data = await AssessmentAPI.submitAssessment(selectedTest, answers, lang);
        if (data.success) {
          try { await AssessmentAPI.saveResult(selectedTest, data); } catch { /* optional */ }
          setNewServiceResult(null);
          setResult(data);
          setStep('results');
          dispatch(markModuleUsed('assessment'));
        } else {
          Alert.alert(errTitle, errGeneric);
        }
      }
    } catch (error: any) {
      Alert.alert(errTitle, error.response?.data?.detail || errGeneric);
      setStep('answering');
    } finally {
      setLoading(false);
    }
  };

  // Tekrar test et
  const resetAssessment = () => {
    setSelectedTest(null);
    setQuestions([]);
    setResponses({});
    setResult(null);
    setNewServiceResult(null);
    setSessionId(null);
    setScaleLabels([]);
    setScaleMin(1);
    setScaleMax(5);
    setNvIndex(0);
    setNvAnswers([]);
    setStep('select');
  };

  // ─── Adım 1: Test Seçimi ───────────────────────────────────────────────────────
  if (step === 'select') {
    return (
      <ScrollView style={styles.container}>
        <View style={[styles.header, { marginTop: insets.top + 8 }]}>
          <TouchableOpacity onPress={() => navigation.goBack()} style={{ paddingRight: 8 }}
            accessibilityRole="button"
            accessibilityLabel={t('assessment.title', lang)}
          >
            <Text style={styles.backBtn}>←</Text>
          </TouchableOpacity>
          <View style={styles.flex1}>
            <Text style={styles.title}>{t('assessment.title', lang)}</Text>
            <Text style={styles.subtitle}>{t('assessment.subtitle', lang)}</Text>
          </View>
          <TouchableOpacity
            accessibilityRole="button"
            accessibilityLabel={t('assessment.history', lang)}
            style={styles.historyBtn}
            onPress={() => navigation.navigate('AssessmentHistory')}
          >
            <Text style={styles.historyBtnText}>{t('assessment.history', lang)}</Text>
          </TouchableOpacity>
        </View>

        {/* Dil Seçimi */}
        <ScrollView
          style={styles.langSelector}
          horizontal
          showsHorizontalScrollIndicator={false}
        >
          {AVAILABLE_LANGUAGES.map(({ code: lCode, flag: lFlag, name: lName }) => (
            <TouchableOpacity
              accessibilityRole="button"
              accessibilityLabel='lFlag lName'
              key={lCode}
              style={[styles.langBtn, lang === lCode && styles.langBtnActive]}
              onPress={() => setLang(lCode)}
            >
              <Text style={styles.langBtnText}>{lFlag} {lName}</Text>
            </TouchableOpacity>
          ))}
        </ScrollView>

        {/* Test Kartları */}
        {TEST_TYPES.map((tt) => {
          const isNew = 'isNewService' in tt && tt.isNewService;
          const isClinical = 'requiresConsent' in tt && tt.requiresConsent;
          return (
            <TouchableOpacity key={tt.id} onPress={() => startTest(tt.id)} activeOpacity={0.7}
              accessibilityRole="button"
              accessibilityLabel={tt.emoji}
            >
              <Card style={styles.testCard}>
                <View style={styles.testCardContent}>
                  <Text style={styles.testEmoji}>{tt.emoji}</Text>
                  <View style={styles.testInfo}>
                    <Text style={styles.testName}>{t(tt.key, lang)}</Text>
                    <Text style={styles.testDesc}>{t(tt.key_desc, lang)}</Text>
                    <View style={styles.badgeRow}>
                      {'questions' in tt && (
                        <Badge label={`${tt.questions} ${t('assessment.questions_unit', lang)}`} />
                      )}
                      {isNew && !isClinical && !('nonverbal' in tt && tt.nonverbal) && (
                        <View style={styles.newBadge}>
                          <Text style={styles.newBadgeText}>{t('assessment.new_badge', lang)}</Text>
                        </View>
                      )}
                      {'nonverbal' in tt && tt.nonverbal && (
                        <View style={styles.nonverbalBadge}>
                          <Text style={styles.nonverbalBadgeText}>{t('assessment.nonverbal_badge', lang)}</Text>
                        </View>
                      )}
                      {isClinical && (
                        <View style={styles.clinicalBadge}>
                          <Text style={styles.clinicalBadgeText}>{t('assessment.clinical_badge', lang)}</Text>
                        </View>
                      )}
                    </View>
                  </View>
                  <Text style={styles.arrow}>→</Text>
                </View>
              </Card>
            </TouchableOpacity>
          );
        })}

        <View style={styles.spacer20} />
      </ScrollView>
    );
  }

  // ─── Adım 2: Yükleniyor / Gönderiliyor ────────────────────────────────────────
  if ((step === 'loading_questions' || step === 'submitting') && loading) {
    return (
      <View style={styles.centerContainer}>
        <ActivityIndicator size="large" color={colors.gold} />
        <Text style={styles.loadingText}>
          {step === 'submitting'
            ? t('assessment.analyzing', lang)
            : t('assessment.loading_questions', lang)}
        </Text>
      </View>
    );
  }

  // ─── Nonverbal handler: tek soru, zamanlı ──────────────────────────────────────
  const handleNonverbalAnswer = (selectedOption: string) => {
    const rt = Date.now() - questionStartRef.current;
    const q = questions[nvIndex];
    const updated = [...nvAnswers, { q_id: q.q_id, score: 0, selected_option: selectedOption, response_time_ms: rt }];
    setNvAnswers(updated);
    if (nvIndex < questions.length - 1) {
      setNvIndex(nvIndex + 1);
      questionStartRef.current = Date.now();
    } else {
      setStep('submitting');
      setLoading(true);
      const testMeta = TEST_TYPES.find(tt => tt.id === selectedTest);
      const apiType = (testMeta && 'newServiceType' in testMeta && testMeta.newServiceType) || selectedTest || '';
      TestAPI.submitTest(sessionId!, apiType as string, lang, updated)
        .then(data => {
          setNewServiceResult(data);
          setResult(null);
          setStep('results');
          dispatch(markModuleUsed('assessment'));
        })
        .catch(() => {
          // Son cevabı geri al, kullanıcı tekrar deneyebilsin
          setNvAnswers(updated.slice(0, -1));
          setStep('answering');
          Alert.alert(t('common.error', lang), t('assessment.error_generic', lang));
        })
        .finally(() => setLoading(false));
    }
  };

  const handleNonverbalBack = () => {
    if (nvIndex === 0) {
      resetAssessment();
      return;
    }
    Alert.alert(
      t('assessment.back', lang).replace('← ', ''),
      t('assessment.exit_message', lang),
      [
        { text: t('assessment.consent_cancel', lang), style: 'cancel' },
        { text: t('common.exit', lang), style: 'destructive', onPress: resetAssessment },
      ]
    );
  };

  // ─── Adım 3: Cevaplar ──────────────────────────────────────────────────────────
  const questionsLen = questions.length;
  if (step === 'answering' && questionsLen > 0) {
    const testInfo = TEST_TYPES.find(t => t.id === selectedTest);
    const isNonverbalTest = testInfo && 'nonverbal' in testInfo && testInfo.nonverbal;

    // ── Nonverbal: tek soru renderer ────────────────────────────────────────────
    if (isNonverbalTest) {
      const q = questions[nvIndex];
      return (
        <View style={styles.container}>
          {/* Header */}
          <View style={[styles.testHeader, { marginTop: insets.top + 8 }]}>
            <TouchableOpacity onPress={handleNonverbalBack}
              accessibilityRole="button"
              accessibilityLabel={t('assessment.back', lang)}
            >
              <Text style={styles.backBtn}>{t('assessment.back', lang)}</Text>
            </TouchableOpacity>
            <Text style={styles.testTitle}>{testInfo ? t(testInfo.key, lang) : ''}</Text>
            <View style={styles.spacer60} />
          </View>

          {/* İlerleme */}
          <View style={styles.progressContainer}>
            <View style={styles.progressBar}>
              <View style={[styles.progressFill, { width: `${(nvIndex / questionsLen) * 100}%` }]} />
            </View>
            <Text style={styles.progressText}>{nvIndex + 1} {t('assessment.question_of', lang)} {questionsLen}</Text>
          </View>

          {/* Duygu tanıma */}
          {q.display_type === 'emotion_recognition' && (
            <View style={styles.nvContainer}>
              <Text style={styles.nvInstruct}>{t('assessment.tap_emotion', lang)}</Text>
              <Text style={styles.emojiStimulus}>{q.emoji}</Text>
              <View style={styles.nvOptionGrid}>
                {(q.options || []).map(opt => (
                  <TouchableOpacity
                    accessibilityRole="button"
                    accessibilityLabel={opt.label}
                    key={opt.key}
                    style={styles.nvOptionBtn}
                    onPress={() => handleNonverbalAnswer(opt.key)}
                    activeOpacity={0.75}
                  >
                    <Text style={styles.nvOptionText}>{opt.label}</Text>
                  </TouchableOpacity>
                ))}
              </View>
            </View>
          )}

          {/* Stroop */}
          {q.display_type === 'stroop' && (
            <View style={styles.nvContainer}>
              <Text style={styles.nvInstruct}>{t('assessment.tap_ink_color', lang)}</Text>
              <Text style={[styles.stroopWord, { color: q.ink_hex ?? '#fff' }]}>{q.word}</Text>
              <View style={styles.colorGrid}>
                {(q.color_options || []).map(c => (
                  <TouchableOpacity
                    accessibilityRole="button"
                    accessibilityLabel={c.label}
                    key={c.key}
                    style={[styles.colorBtn, { backgroundColor: c.hex }]}
                    onPress={() => handleNonverbalAnswer(c.key)}
                    activeOpacity={0.8}
                  >
                    <Text style={styles.colorBtnLabel}>{c.label}</Text>
                  </TouchableOpacity>
                ))}
              </View>
            </View>
          )}
        </View>
      );
    }

    const answeredCount = Object.keys(responses).length;

    return (
      <ScrollView style={styles.container}>
        {/* Başlık */}
        <View style={styles.testHeader}>
          <TouchableOpacity onPress={resetAssessment}
            accessibilityRole="button"
            accessibilityLabel={t('assessment.back', lang)}
          >
            <Text style={styles.backBtn}>{t('assessment.back', lang)}</Text>
          </TouchableOpacity>
          <Text style={styles.testTitle}>{testInfo ? t(testInfo.key, lang) : ''}</Text>
          <View style={styles.spacer60} />
        </View>

        {/* İlerleme */}
        <View style={styles.progressContainer}>
          <View style={styles.progressBar}>
            <View
              style={[
                styles.progressFill,
                { width: `${(answeredCount / questionsLen) * 100}%` },
              ]}
            />
          </View>
          <Text style={styles.progressText}>{answeredCount} / {questionsLen} {t('assessment.answered', lang)}</Text>
        </View>

        {/* Sorular */}
        {questions.map((question, index) => {
          const qId       = question.q_id;
          const qResponse = responses[qId];
          return (
          <Card key={qId} style={styles.questionCard}>
            <Text style={styles.questionNumber}>{t('assessment.question_number', lang)} {index + 1}</Text>
            <Text style={styles.questionText}>{question.text}</Text>

            {/* Likert Ölçeği */}
            <View style={styles.likertContainer}>
              {Array.from({ length: scaleMax - scaleMin + 1 }, (_, i) => scaleMin + i).map((score) => (
                <TouchableOpacity
                  accessibilityRole="button"
                  accessibilityLabel='responses[qId] !== undefined'
                  key={score}
                  style={[
                    styles.likertBtn,
                    qResponse === score && styles.likertBtnSelected,
                  ]}
                  onPress={() =>
                    setResponses(prev => ({
                      ...prev,
                      [qId]: score,
                    }))
                  }
                >
                  <Text
                    style={[
                      styles.likertBtnText,
                      qResponse === score && styles.likertBtnTextSelected,
                    ]}
                  >
                    {score}
                  </Text>
                </TouchableOpacity>
              ))}
            </View>
            <Text style={styles.likertLabel}>
              {responses[qId] !== undefined
                ? (scaleLabels.length > 0
                    ? (scaleLabels[responses[qId] - scaleMin] ?? t('assessment.choose_answer', lang))
                    : (LIKERT_LABELS[responses[qId] - 1] ?? t('assessment.choose_answer', lang)))
                : t('assessment.choose_answer', lang)}
            </Text>
          </Card>
          );
        })}

        {/* Gönder Butonu */}
        {(() => {
          const answeredAll = Object.keys(responses).length >= questionsLen;
          const remaining = questionsLen - Object.keys(responses).length;
          return (
            <>
              {!answeredAll && !loading && (
                <Text style={styles.submitHint}>
                  {remaining} {t('assessment.questions_remaining', lang)}
                </Text>
              )}
              <TouchableOpacity
                accessibilityRole="button"
                accessibilityLabel={t('assessment.submit', lang)}
                style={[styles.submitBtn, (!answeredAll || loading) && styles.submitBtnDisabled]}
                onPress={submitResponses}
                disabled={loading || !answeredAll}
              >
                {loading ? (
                  <ActivityIndicator color="white" />
                ) : (
                  <Text style={styles.submitBtnText}>{t('assessment.submit', lang)}</Text>
                )}
              </TouchableOpacity>
            </>
          );
        })()}

        <View style={styles.spacer20} />
      </ScrollView>
    );
  }

  // ─── Adım 4a: Yeni Servis Sonuçları (EQ / Values / Stress Clinical) ───────────
  if (step === 'results' && newServiceResult) {
    const nsr = newServiceResult;
    const testInfo = TEST_TYPES.find(tt => tt.id === selectedTest);
    const sd = nsr.stress_details;

    return (
      <ScrollView style={styles.container}>
        <View style={styles.testHeader}>
          <TouchableOpacity onPress={() => setStep('select')}
            accessibilityRole="button"
            accessibilityLabel="testInfo?.emoji testInfo ? t(testInfo.key, lang) : ''"
          >
            <Text style={styles.backBtn}>←</Text>
          </TouchableOpacity>
          <Text style={styles.resultsTitle}>{testInfo?.emoji} {testInfo ? t(testInfo.key, lang) : ''}</Text>
          <View style={styles.spacer60} />
        </View>

        {/* Crisis Banner */}
        {sd?.crisis_flag && (
          <View style={styles.crisisBanner}>
            <Text style={styles.crisisText}>{t('assessment.crisis_banner', lang)}</Text>
            <Text style={styles.crisisLine}>{t('assessment.crisis_line', lang)}</Text>
          </View>
        )}

        {/* Stres Severity (PHQ-9 / GAD-7) */}
        {sd && (
          <>
            <SectionLabel>{t('assessment.depression_severity', lang)}</SectionLabel>
            <Card style={styles.domainCard}>
              <View style={styles.domainHeader}>
                <Text style={styles.domainName}>PHQ-9</Text>
                <Text style={styles.domainScore}>{t(SEVERITY_KEYS[sd.depression_severity] || sd.depression_severity, lang)}</Text>
              </View>
              <View style={styles.domainBar}>
                <View style={[styles.domainBarFill, { width: `${nsr.domain_scores.depression ?? 0}%`, backgroundColor: sd.depression_severity === 'severe' ? colors.error ?? '#e53935' : colors.gold }]} />
              </View>
            </Card>

            <SectionLabel>{t('assessment.anxiety_severity', lang)}</SectionLabel>
            <Card style={styles.domainCard}>
              <View style={styles.domainHeader}>
                <Text style={styles.domainName}>GAD-7</Text>
                <Text style={styles.domainScore}>{t(SEVERITY_KEYS[sd.anxiety_severity] || sd.anxiety_severity, lang)}</Text>
              </View>
              <View style={styles.domainBar}>
                <View style={[styles.domainBarFill, { width: `${nsr.domain_scores.anxiety ?? 0}%`, backgroundColor: sd.anxiety_severity === 'severe' ? colors.error ?? '#e53935' : colors.gold }]} />
              </View>
            </Card>
          </>
        )}

        {/* Nonverbal: Stroop detayları */}
        {nsr.nonverbal_details && nsr.test_type === 'stroop' && (
          <>
            <SectionLabel>{t('assessment.stroop_accuracy', lang)}</SectionLabel>
            <Card style={styles.domainCard}>
              <View style={styles.domainHeader}>
                <Text style={styles.domainName}>{t('assessment.stroop_accuracy', lang)}</Text>
                <Text style={styles.domainScore}>{Math.round(nsr.domain_scores.accuracy ?? 0)}%</Text>
              </View>
              <View style={styles.domainBar}>
                <View style={[styles.domainBarFill, { width: `${nsr.domain_scores.accuracy ?? 0}%` }]} />
              </View>
            </Card>
            <Card style={styles.domainCard}>
              <View style={styles.domainHeader}>
                <Text style={styles.domainName}>{t('assessment.stroop_cognitive_flexibility', lang)}</Text>
                <Text style={styles.domainScore}>{Math.round(nsr.domain_scores.cognitive_flexibility ?? 0)}/100</Text>
              </View>
              <View style={styles.domainBar}>
                <View style={[styles.domainBarFill, { width: `${nsr.domain_scores.cognitive_flexibility ?? 0}%` }]} />
              </View>
            </Card>
            <Card style={styles.domainCard}>
              <Text style={styles.domainName}>{t('assessment.stroop_reaction_time', lang)}</Text>
              <Text style={styles.stroopAvgMs}>
                {nsr.nonverbal_details.avg_reaction_ms ?? 0}
                <Text style={styles.stroopMsUnit}> {t('assessment.stroop_ms', lang)}</Text>
              </Text>
              <View style={styles.stroopSplit}>
                <View style={styles.stroopSplitItem}>
                  <Text style={styles.stroopSplitVal}>{nsr.nonverbal_details.congruent_accuracy ?? 0}%</Text>
                  <Text style={styles.stroopSplitLabel}>{t('assessment.congruent_label', lang)}</Text>
                </View>
                <View style={styles.stroopSplitDivider} />
                <View style={styles.stroopSplitItem}>
                  <Text style={styles.stroopSplitVal}>{nsr.nonverbal_details.incongruent_accuracy ?? 0}%</Text>
                  <Text style={styles.stroopSplitLabel}>{t('assessment.incongruent_label', lang)}</Text>
                </View>
              </View>
            </Card>
          </>
        )}

        {/* Nonverbal: Duygu tanıma detayları */}
        {nsr.test_type === 'emotion_recognition' && (
          <>
            <View style={styles.bigScoreCircle}>
              <Text style={styles.bigScoreNumber}>{Math.round(nsr.domain_scores.overall ?? 0)}</Text>
              <Text style={styles.bigScorePercent}>%</Text>
              <Text style={styles.bigScoreLabel}>{t('assessment.overall_accuracy', lang)}</Text>
            </View>
            <SectionLabel>{t('assessment.emotion_per_category', lang)}</SectionLabel>
            {Object.entries(nsr.domain_scores).filter(([k]) => k !== 'overall').map(([emotion, score]) => (
              <Card key={emotion} style={styles.domainCard}>
                <View style={styles.domainHeader}>
                  <Text style={styles.domainName}>{t(`assessment.emotion_${emotion}`, lang)}</Text>
                  <Text style={styles.domainScore}>{Math.round(score)}%</Text>
                </View>
                <View style={styles.domainBar}>
                  <View style={[styles.domainBarFill, { width: `${Math.min(Math.max(score, 0), 100)}%` }]} />
                </View>
              </Card>
            ))}
          </>
        )}

        {/* Domain Skorları (EQ / Values / stress — mevcut) */}
        {!sd && !nsr.nonverbal_details && nsr.test_type !== 'emotion_recognition' && (
          <>
            <SectionLabel>{t('assessment.domain_score', lang)}</SectionLabel>
            {Object.entries(nsr.domain_scores).map(([domain, score]) => (
              <Card key={domain} style={styles.domainCard}>
                <View style={styles.domainHeader}>
                  <Text style={styles.domainName}>{tDomain(domain, lang)}</Text>
                  <Text style={styles.domainScore}>{Math.round(score)}/100</Text>
                </View>
                <View style={styles.domainBar}>
                  <View style={[styles.domainBarFill, { width: `${Math.min(Math.max(score, 0), 100)}%` }]} />
                </View>
              </Card>
            ))}
          </>
        )}

        {/* Spotlight: Güçlü yanlar + Gelişim alanları */}
        {((nsr.strengths?.length ?? 0) > 0 || (nsr.growth_areas?.length ?? 0) > 0) && (
          <View style={styles.spotlightRow}>
            {(nsr.strengths?.length ?? 0) > 0 && (
              <View style={[styles.spotlightCard, styles.spotlightStrengths]}>
                <Text style={styles.spotlightTitle}>💪 {t('assessment.strengths', lang)}</Text>
                {nsr.strengths!.map((s, i) => (
                  <Text key={i} style={styles.spotlightItem}>· {tDomain(s.name, lang)}</Text>
                ))}
              </View>
            )}
            {(nsr.growth_areas?.length ?? 0) > 0 && (
              <View style={[styles.spotlightCard, styles.spotlightGrowth]}>
                <Text style={styles.spotlightTitle}>🌱 {t('assessment.growth_areas', lang)}</Text>
                {nsr.growth_areas!.map((g, i) => (
                  <Text key={i} style={styles.spotlightItem}>· {tDomain(g.name, lang)}</Text>
                ))}
              </View>
            )}
          </View>
        )}

        {/* Profil Anlatısı */}
        {nsr.ai_interpretation ? (
          <>
            <SectionLabel>{t('assessment.profile_analysis', lang)}</SectionLabel>
            <Card style={styles.narrativeCard}>
              <Text style={styles.narrativeText}>{nsr.ai_interpretation}</Text>
            </Card>
          </>
        ) : null}

        <TouchableOpacity style={styles.retakeBtn} onPress={resetAssessment}
          accessibilityRole="button"
          accessibilityLabel={t('assessment.another_test', lang)}
        >
          <Text style={styles.retakeBtnText}>{t('assessment.another_test', lang)}</Text>
        </TouchableOpacity>
        <View style={styles.spacer20} />
      </ScrollView>
    );
  }

  // ─── Adım 4b: Eski Servis Sonuçları ───────────────────────────────────────────
  if (step === 'results' && result) {
    const data = result.data;
    const testInfo = TEST_TYPES.find(t => t.id === data.test_type);

    return (
      <ScrollView style={styles.container}>
        <View style={styles.testHeader}>
          <TouchableOpacity onPress={() => setStep('select')}
            accessibilityRole="button"
            accessibilityLabel="testInfo?.emoji testInfo ? t(testInfo.key, lang) : ''"
          >
            <Text style={styles.backBtn}>←</Text>
          </TouchableOpacity>
          <Text style={styles.resultsTitle}>{testInfo?.emoji} {testInfo ? t(testInfo.key, lang) : ''}</Text>
          <View style={styles.spacer60} />
        </View>

        {/* Genel Skor */}
        <Card style={styles.scoreCard}>
          <Text style={styles.scoreLabel}>{t('assessment.overall_score', lang)}</Text>
          <Text style={styles.scoreBig}>{Math.round(Number(data.overall_score) || 0)}/100</Text>
          <Badge label={lang === 'tr' ? data.overall_level_tr : data.overall_level} />
        </Card>

        {/* Alan Puanları */}
        <SectionLabel>{t('assessment.field_scores', lang)}</SectionLabel>
        {Object.entries(data.breakdown).map(([domain, scores]) => (
          <Card key={domain} style={styles.domainCard}>
            <View style={styles.domainHeader}>
              <Text style={styles.domainName}>{tDomain(domain, lang)}</Text>
              <Text style={styles.domainScore}>{Math.round(Number(scores.score) || 0)}/100</Text>
            </View>
            <View style={styles.domainBar}>
              <View
                style={[
                  styles.domainBarFill,
                  { width: `${Math.min(Math.max(Number(scores.score) || 0, 0), 100)}%` },
                ]}
              />
            </View>
            <Text style={styles.domainLevel}>{lang === 'tr' ? scores.level_tr : scores.level}</Text>
            {scores.description ? (
              <Text style={styles.domainDescription}>{scores.description}</Text>
            ) : null}
          </Card>
        ))}

        {/* Spotlight: Güçlü yanlar + Gelişim alanları */}
        {((data.strengths?.length ?? 0) > 0 || (data.growth_areas?.length ?? 0) > 0) && (
          <View style={styles.spotlightRow}>
            {(data.strengths?.length ?? 0) > 0 && (
              <View style={[styles.spotlightCard, styles.spotlightStrengths]}>
                <Text style={styles.spotlightTitle}>💪 {t('assessment.strengths', lang)}</Text>
                {data.strengths!.map((s, i) => (
                  <Text key={i} style={styles.spotlightItem}>· {tDomain(s.name, lang)}</Text>
                ))}
              </View>
            )}
            {(data.growth_areas?.length ?? 0) > 0 && (
              <View style={[styles.spotlightCard, styles.spotlightGrowth]}>
                <Text style={styles.spotlightTitle}>🌱 {t('assessment.growth_areas', lang)}</Text>
                {data.growth_areas!.map((g, i) => (
                  <Text key={i} style={styles.spotlightItem}>· {tDomain(g.name, lang)}</Text>
                ))}
              </View>
            )}
          </View>
        )}

        {/* Profil Anlatısı */}
        {data.narrative ? (
          <>
            <SectionLabel>{t('assessment.profile_analysis', lang)}</SectionLabel>
            <Card style={styles.narrativeCard}>
              <Text style={styles.narrativeText}>{data.narrative}</Text>
            </Card>
          </>
        ) : data.recommendations.length > 0 && (
          <>
            <SectionLabel>{t('assessment.recommendations', lang)}</SectionLabel>
            {data.recommendations.map((rec, idx) => (
              <Card key={idx} style={styles.recommendationCard}>
                <Text style={styles.recommendationBullet}>•</Text>
                <Text style={styles.recommendationText}>{rec}</Text>
              </Card>
            ))}
          </>
        )}

        {/* Düğmeler */}
        <TouchableOpacity
          accessibilityRole="button"
          accessibilityLabel={t('assessment.another_test', lang)}
          style={styles.retakeBtn}
          onPress={resetAssessment}
        >
          <Text style={styles.retakeBtnText}>{t('assessment.another_test', lang)}</Text>
        </TouchableOpacity>

        <View style={styles.spacer20} />
      </ScrollView>
    );
  }

  return null;
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: colors.background,
    paddingHorizontal: 16,
  },
  centerContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: colors.background,
  },
  header: {
    marginBottom: 24,
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
  },
  historyBtn: {
    width: 50,
    height: 50,
    borderRadius: 25,
    backgroundColor: colors.cardBg,
    borderWidth: 1,
    borderColor: colors.border,
    alignItems: 'center',
    justifyContent: 'center',
  },
  historyBtnText: {
    fontSize: 24,
  },
  title: {
    fontSize: 28,
    fontWeight: 'bold',
    color: colors.text,
    marginBottom: 4,
  },
  subtitle: {
    fontSize: 16,
    color: colors.textSecondary,
  },
  langSelector: {
    flexDirection: 'row',
    marginBottom: 20,
    gap: 10,
  },
  langBtn: {
    flex: 1,
    paddingVertical: 10,
    paddingHorizontal: 12,
    borderRadius: 8,
    backgroundColor: colors.cardBg,
    borderWidth: 1,
    borderColor: colors.border,
    alignItems: 'center',
  },
  langBtnActive: {
    backgroundColor: colors.gold,
    borderColor: colors.gold,
  },
  langBtnText: {
    fontSize: 14,
    fontWeight: '600',
    color: colors.text,
  },
  testCard: {
    marginBottom: 12,
  },
  testCardContent: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
  },
  testEmoji: {
    fontSize: 40,
    marginRight: 16,
  },
  testInfo: {
    flex: 1,
  },
  testName: {
    fontSize: 16,
    fontWeight: '600',
    color: colors.text,
    marginBottom: 4,
  },
  testDesc: {
    fontSize: 13,
    color: colors.textSecondary,
    marginBottom: 8,
  },
  arrow: {
    fontSize: 20,
    color: colors.gold,
  },
  // Test Header
  testHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginTop: 12,
    marginBottom: 16,
  },
  backBtn: {
    fontSize: 16,
    color: colors.gold,
    fontWeight: '600',
  },
  testTitle: {
    fontSize: 20,
    fontWeight: '600',
    color: colors.text,
  },
  // Progress
  progressContainer: {
    marginBottom: 16,
  },
  progressBar: {
    height: 6,
    backgroundColor: colors.border,
    borderRadius: 3,
    marginBottom: 8,
    overflow: 'hidden',
  },
  progressFill: {
    height: '100%',
    backgroundColor: colors.gold,
  },
  progressText: {
    fontSize: 12,
    color: colors.textSecondary,
  },
  // Sorular
  questionCard: {
    marginBottom: 16,
  },
  questionNumber: {
    fontSize: 12,
    color: colors.textSecondary,
    marginBottom: 8,
  },
  questionText: {
    fontSize: 16,
    fontWeight: '500',
    color: colors.text,
    marginBottom: 16,
    lineHeight: 22,
  },
  likertContainer: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: 8,
    gap: 6,
  },
  likertBtn: {
    flex: 1,
    paddingVertical: 7,
    paddingHorizontal: 4,
    borderRadius: 6,
    backgroundColor: colors.cardBg,
    borderWidth: 1.5,
    borderColor: colors.border,
    alignItems: 'center',
    justifyContent: 'center',
  },
  likertBtnSelected: {
    backgroundColor: colors.gold,
    borderColor: colors.gold,
  },
  likertBtnText: {
    fontSize: 13,
    fontWeight: '600',
    color: colors.textSecondary,
  },
  likertBtnTextSelected: {
    color: 'white',
  },
  likertLabel: {
    fontSize: 11,
    color: colors.textSecondary,
    textAlign: 'center',
  },
  // Gönder
  submitBtn: {
    backgroundColor: colors.gold,
    paddingVertical: 10,
    borderRadius: 10,
    alignItems: 'center',
    marginVertical: 12,
    marginHorizontal: 32,
  },
  submitBtnDisabled: {
    opacity: 0.4,
  },
  submitHint: {
    textAlign: 'center',
    fontSize: 12,
    color: colors.textMuted,
    marginBottom: 6,
    marginHorizontal: 32,
  },
  submitBtnText: {
    color: 'white',
    fontSize: 14,
    fontWeight: '600',
  },
  // Sonuçlar
  resultsHeader: {
    alignItems: 'center',
    marginVertical: 24,
  },
  resultsTitle: {
    fontSize: 18,
    fontWeight: '700',
    color: colors.text,
    flex: 1,
    textAlign: 'center',
  },
  scoreCard: {
    backgroundColor: `${colors.gold}15`,
    borderWidth: 1,
    borderColor: colors.gold,
    alignItems: 'center',
    marginBottom: 12,
    paddingVertical: 6,
    paddingHorizontal: 12,
  },
  scoreLabel: {
    fontSize: 10,
    color: colors.textSecondary,
    marginBottom: 2,
  },
  scoreBig: {
    fontSize: 24,
    fontWeight: '700',
    color: colors.gold,
    marginBottom: 4,
  },
  // Alan Puanları
  domainCard: {
    marginBottom: 8,
    paddingVertical: 8,
  },
  domainHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 6,
  },
  domainName: {
    fontSize: 13,
    fontWeight: '600',
    color: colors.text,
    flex: 1,
  },
  domainScore: {
    fontSize: 13,
    fontWeight: '700',
    color: colors.gold,
  },
  domainBar: {
    height: 4,
    backgroundColor: colors.border,
    borderRadius: 2,
    marginBottom: 3,
    overflow: 'hidden',
  },
  domainBarFill: {
    height: '100%',
    backgroundColor: colors.gold,
  },
  domainLevel: {
    fontSize: 10,
    color: colors.textSecondary,
  },
  domainDescription: {
    fontSize: 12,
    color: colors.textSecondary,
    marginTop: 4,
    lineHeight: 17,
    fontStyle: 'italic',
  },
  // Tavsiyeler
  recommendationCard: {
    flexDirection: 'row',
    marginBottom: 10,
  },
  recommendationBullet: {
    fontSize: 18,
    color: colors.gold,
    marginRight: 12,
    fontWeight: '700',
  },
  recommendationText: {
    flex: 1,
    fontSize: 14,
    color: colors.text,
    lineHeight: 20,
  },
  recommendationStatus: {
    fontSize: 12,
    color: colors.textSecondary,
    marginTop: 8,
    marginBottom: 16,
    textAlign: 'center',
  },
  // Spotlight
  spotlightRow: {
    flexDirection: 'row',
    gap: 10,
    marginBottom: 16,
    marginTop: 4,
  },
  spotlightCard: {
    flex: 1,
    borderRadius: 12,
    padding: 12,
    borderWidth: 1,
  },
  spotlightStrengths: {
    backgroundColor: '#0d2b1a',
    borderColor: '#2ecc71' + '55',
  },
  spotlightGrowth: {
    backgroundColor: '#2b1e0d',
    borderColor: colors.warmAmber + '55',
  },
  spotlightTitle: {
    fontSize: 12,
    fontWeight: '700' as const,
    color: colors.text,
    marginBottom: 8,
  },
  spotlightItem: {
    fontSize: 12,
    color: colors.textSecondary,
    lineHeight: 18,
    marginBottom: 2,
  },
  // Narrative
  narrativeCard: {
    marginBottom: 16,
  },
  narrativeText: {
    fontSize: 14,
    color: colors.text,
    lineHeight: 22,
  },
  // Yeniden Test Butonu
  retakeBtn: {
    backgroundColor: colors.gold,
    paddingVertical: 10,
    borderRadius: 10,
    alignItems: 'center',
    marginBottom: 12,
    marginHorizontal: 32,
  },
  retakeBtnText: {
    color: 'white',
    fontSize: 14,
    fontWeight: '600',
  },
  loadingText: {
    marginTop: 16,
    fontSize: 16,
    color: colors.text,
  },
  flex1:     { flex: 1 },
  spacer20:  { height: 20 },
  spacer60:  { width: 60 },
  // Badge row
  badgeRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    marginTop: 4,
    flexWrap: 'wrap',
  },
  newBadge: {
    backgroundColor: `${colors.gold}25`,
    borderRadius: 4,
    paddingHorizontal: 6,
    paddingVertical: 2,
    borderWidth: 1,
    borderColor: colors.gold,
  },
  newBadgeText: {
    fontSize: 10,
    fontWeight: '700',
    color: colors.gold,
  },
  clinicalBadge: {
    backgroundColor: '#e8f5e925',
    borderRadius: 4,
    paddingHorizontal: 6,
    paddingVertical: 2,
    borderWidth: 1,
    borderColor: '#43a047',
  },
  clinicalBadgeText: {
    fontSize: 10,
    fontWeight: '700',
    color: '#43a047',
  },
  // Crisis banner
  crisisBanner: {
    backgroundColor: '#ffebee',
    borderRadius: 10,
    padding: 14,
    marginBottom: 16,
    borderWidth: 1,
    borderColor: '#e53935',
  },
  crisisText: {
    fontSize: 14,
    fontWeight: '700',
    color: '#c62828',
    marginBottom: 4,
  },
  crisisLine: {
    fontSize: 13,
    color: '#c62828',
  },
  // Nonverbal badge
  nonverbalBadge: {
    backgroundColor: '#e3f2fd',
    borderRadius: 4,
    paddingHorizontal: 6,
    paddingVertical: 2,
    marginLeft: 4,
    borderWidth: 1,
    borderColor: '#90caf9',
  },
  nonverbalBadgeText: {
    fontSize: 10,
    color: '#1565c0',
    fontWeight: '600',
  },
  // Nonverbal soru container
  nvContainer: {
    flex: 1,
    alignItems: 'center',
    paddingHorizontal: 16,
    paddingTop: 20,
  },
  nvInstruct: {
    fontSize: 15,
    color: colors.textSecondary,
    textAlign: 'center',
    marginBottom: 24,
  },
  emojiStimulus: {
    fontSize: 110,
    textAlign: 'center',
    marginBottom: 32,
  },
  nvOptionGrid: {
    width: '100%',
    flexDirection: 'row',
    flexWrap: 'wrap',
    justifyContent: 'center',
    gap: 12,
  },
  nvOptionBtn: {
    width: (width - 64) / 2,
    paddingVertical: 16,
    borderRadius: 12,
    backgroundColor: colors.cardBg,
    borderWidth: 2,
    borderColor: colors.border,
    alignItems: 'center',
  },
  nvOptionText: {
    fontSize: 15,
    fontWeight: '600',
    color: colors.text,
  },
  // Stroop
  stroopWord: {
    fontSize: 56,
    fontWeight: '900',
    textAlign: 'center',
    marginBottom: 40,
    letterSpacing: 4,
  },
  colorGrid: {
    width: '100%',
    flexDirection: 'row',
    flexWrap: 'wrap',
    justifyContent: 'center',
    gap: 14,
  },
  colorBtn: {
    width: (width - 72) / 2,
    paddingVertical: 20,
    borderRadius: 14,
    alignItems: 'center',
    justifyContent: 'center',
  },
  colorBtnLabel: {
    fontSize: 13,
    fontWeight: '700',
    color: 'white',
    textShadowColor: 'rgba(0,0,0,0.4)',
    textShadowOffset: { width: 0, height: 1 },
    textShadowRadius: 2,
  },
  // Big score circle (emotion recognition overall)
  bigScoreCircle: {
    width: 160,
    height: 160,
    borderRadius: 80,
    backgroundColor: `${colors.gold}18`,
    borderWidth: 3,
    borderColor: colors.gold,
    alignItems: 'center',
    justifyContent: 'center',
    alignSelf: 'center',
    marginVertical: 20,
  },
  bigScoreNumber: {
    fontSize: 52,
    fontWeight: '800',
    color: colors.gold,
    lineHeight: 56,
  },
  bigScorePercent: {
    fontSize: 20,
    fontWeight: '600',
    color: colors.gold,
    marginTop: -4,
  },
  bigScoreLabel: {
    fontSize: 11,
    color: colors.textSecondary,
    marginTop: 4,
    textAlign: 'center',
    paddingHorizontal: 8,
  },
  // Stroop reaction time split
  stroopAvgMs: {
    fontSize: 32,
    fontWeight: '800',
    color: colors.gold,
    textAlign: 'center',
    marginTop: 4,
    marginBottom: 16,
  },
  stroopMsUnit: {
    fontSize: 14,
    fontWeight: '400',
    color: colors.textSecondary,
  },
  stroopSplit: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
  },
  stroopSplitItem: {
    flex: 1,
    alignItems: 'center',
  },
  stroopSplitVal: {
    fontSize: 22,
    fontWeight: '700',
    color: colors.text,
    marginBottom: 2,
  },
  stroopSplitLabel: {
    fontSize: 11,
    color: colors.textSecondary,
  },
  stroopSplitDivider: {
    width: 1,
    height: 36,
    backgroundColor: colors.border,
    marginHorizontal: 8,
  },
});

export default AssessmentScreen;

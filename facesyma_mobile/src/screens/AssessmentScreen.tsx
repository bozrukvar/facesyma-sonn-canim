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
  { id: 'skills',           key: 'assessment.skills',           key_desc: 'assessment.skills_desc',           emoji: '🎯' },
  { id: 'hr',               key: 'assessment.hr',               key_desc: 'assessment.hr_desc',               emoji: '👥' },
  { id: 'personality',      key: 'assessment.personality',      key_desc: 'assessment.personality_desc',      emoji: '🧠' },
  { id: 'career',           key: 'assessment.career',           key_desc: 'assessment.career_desc',           emoji: '💼' },
  { id: 'relationship',     key: 'assessment.relationship',     key_desc: 'assessment.relationship_desc',     emoji: '❤️' },
  { id: 'vocation',         key: 'assessment.vocation',         key_desc: 'assessment.vocation_desc',         emoji: '🏢' },
  { id: 'attachment',       key: 'assessment.attachment',       key_desc: 'assessment.attachment_desc',       emoji: '🔗' },
  { id: 'grit',             key: 'assessment.grit',             key_desc: 'assessment.grit_desc',             emoji: '💪' },
  { id: 'growth_mindset',   key: 'assessment.growth_mindset',   key_desc: 'assessment.growth_mindset_desc',   emoji: '🌱' },
  { id: 'life_satisfaction',key: 'assessment.life_satisfaction',key_desc: 'assessment.life_satisfaction_desc',emoji: '😊' },
  { id: 'self_compassion',  key: 'assessment.self_compassion',  key_desc: 'assessment.self_compassion_desc',  emoji: '🌸' },
  { id: 'body_image',       key: 'assessment.body_image',       key_desc: 'assessment.body_image_desc',       emoji: '🪞' },
  { id: 'self_efficacy',    key: 'assessment.self_efficacy',    key_desc: 'assessment.self_efficacy_desc',    emoji: '⚡' },
  { id: 'stress',           key: 'assessment.stress',           key_desc: 'assessment.stress_desc',           emoji: '🧘' },
  // ── Yeni servis testleri (/test/ FastAPI) ──────────────────────────────────
  { id: 'eq',             key: 'assessment.eq',             key_desc: 'assessment.eq_desc',             emoji: '💡', isNewService: true },
  { id: 'values',         key: 'assessment.values',         key_desc: 'assessment.values_desc',         emoji: '⭐', isNewService: true },
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
    breakdown: Record<string, { score: number; level: string; level_tr: string; questions_answered: number }>;
    recommendations: string[];
    recommendations_status: string;
    responses_counted: number;
  };
}

const AssessmentScreen = ({ navigation }: ScreenProps<'Assessment'>) => {
  const insets = useSafeAreaInsets();
  const dispatch = useDispatch<AppDispatch>();
  const [step, setStep] = useState<AssessmentStep>('select');
  const [selectedTest, setSelectedTest] = useState<string | null>(null);
  const { lang, setLang } = useLanguage();
  const [questions, setQuestions] = useState<Question[]>([]);
  const [responses, setResponses] = useState<Record<string, number>>({});
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<SubmissionResponse | null>(null);
  // Yeni test servisi state'leri
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [newServiceResult, setNewServiceResult] = useState<TestSubmitResponse | null>(null);
  const [scaleLabels, setScaleLabels] = useState<string[]>([]);
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
      setScaleLabels((data.questions[0] as any)?.scale?.labels || []);
      setResponses({});
      setNvIndex(0);
      setNvAnswers([]);
      questionStartRef.current = Date.now();
      setStep('answering');
    } catch (error: any) {
      Alert.alert(t('common.error', lang), error.response?.data?.detail || t('assessment.error_generic', lang));
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
    setNvIndex(0);
    setNvAnswers([]);
    setStep('select');
  };

  // ─── Adım 1: Test Seçimi ───────────────────────────────────────────────────────
  if (step === 'select') {
    return (
      <ScrollView style={styles.container}>
        <View style={[styles.header, { marginTop: insets.top + 8 }]}>
          <View style={styles.flex1}>
            <Text style={styles.title}>{t('assessment.title', lang)}</Text>
            <Text style={styles.subtitle}>{t('assessment.subtitle', lang)}</Text>
          </View>
          <TouchableOpacity
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
            <TouchableOpacity key={tt.id} onPress={() => startTest(tt.id)} activeOpacity={0.7}>
              <Card style={styles.testCard}>
                <View style={styles.testCardContent}>
                  <Text style={styles.testEmoji}>{tt.emoji}</Text>
                  <View style={styles.testInfo}>
                    <Text style={styles.testName}>{t(tt.key, lang)}</Text>
                    <Text style={styles.testDesc}>{t(tt.key_desc, lang)}</Text>
                    <View style={styles.badgeRow}>
                      <Badge label={t('assessment.questions', lang)} />
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
            <TouchableOpacity onPress={handleNonverbalBack}>
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
          <TouchableOpacity onPress={resetAssessment}>
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
              {[1, 2, 3, 4, 5].map((score) => (
                <TouchableOpacity
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
              {responses[qId]
                ? (scaleLabels.length > 0
                    ? (scaleLabels[responses[qId] - 1] ?? t('assessment.choose_answer', lang))
                    : (LIKERT_LABELS[responses[qId] - 1] ?? t('assessment.choose_answer', lang)))
                : t('assessment.choose_answer', lang)}
            </Text>
          </Card>
          );
        })}

        {/* Gönder Butonu */}
        <TouchableOpacity
          style={[styles.submitBtn, loading && styles.submitBtnDisabled]}
          onPress={submitResponses}
          disabled={loading || Object.keys(responses).length < questionsLen}
        >
          {loading ? (
            <ActivityIndicator color="white" />
          ) : (
            <Text style={styles.submitBtnText}>{t('assessment.submit', lang)}</Text>
          )}
        </TouchableOpacity>

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
        <View style={styles.resultsHeader}>
          <Text style={styles.resultsTitle}>{testInfo?.emoji} {testInfo ? t(testInfo.key, lang) : ''}</Text>
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
                  <Text style={styles.domainName}>{domain}</Text>
                  <Text style={styles.domainScore}>{Math.round(score)}/100</Text>
                </View>
                <View style={styles.domainBar}>
                  <View style={[styles.domainBarFill, { width: `${Math.min(Math.max(score, 0), 100)}%` }]} />
                </View>
              </Card>
            ))}
          </>
        )}

        {/* AI Yorumu */}
        {nsr.ai_interpretation ? (
          <>
            <SectionLabel>{t('assessment.ai_comment', lang)}</SectionLabel>
            <Card style={styles.recommendationCard}>
              <Text style={styles.recommendationText}>{nsr.ai_interpretation}</Text>
            </Card>
          </>
        ) : null}

        <TouchableOpacity style={styles.retakeBtn} onPress={resetAssessment}>
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
        <View style={styles.resultsHeader}>
          <Text style={styles.resultsTitle}>{testInfo?.emoji} {t('assessment.submit', lang)}</Text>
        </View>

        {/* Genel Skor */}
        <Card style={styles.scoreCard}>
          <Text style={styles.scoreLabel}>{t('assessment.overall_score', lang)}</Text>
          <Text style={styles.scoreBig}>{(Number(data.overall_score) || 0).toFixed(2)}/5.0</Text>
          <Badge label={lang === 'tr' ? data.overall_level_tr : data.overall_level} />
        </Card>

        {/* Alan Puanları */}
        <SectionLabel>{t('assessment.field_scores', lang)}</SectionLabel>
        {Object.entries(data.breakdown).map(([domain, scores]) => (
          <Card key={domain} style={styles.domainCard}>
            <View style={styles.domainHeader}>
              <Text style={styles.domainName}>{domain}</Text>
              <Text style={styles.domainScore}>{(Number(scores.score) || 0).toFixed(2)}</Text>
            </View>
            <View style={styles.domainBar}>
              <View
                style={[
                  styles.domainBarFill,
                  { width: `${Math.min(Math.max((Number(scores.score) || 0) / 5 * 100, 0), 100)}%` },
                ]}
              />
            </View>
            <Text style={styles.domainLevel}>{lang === 'tr' ? scores.level_tr : scores.level}</Text>
          </Card>
        ))}

        {/* Tavsiyeler */}
        {data.recommendations.length > 0 && (
          <>
            <SectionLabel>{t('assessment.recommendations', lang)}</SectionLabel>
            {data.recommendations.map((rec, idx) => (
              <Card key={idx} style={styles.recommendationCard}>
                <Text style={styles.recommendationBullet}>•</Text>
                <Text style={styles.recommendationText}>{rec}</Text>
              </Card>
            ))}
            <Text style={styles.recommendationStatus}>
              {data.recommendations_status === 'success' ? t('assessment.ai_generated', lang) : t('assessment.template_suggestions', lang)}
            </Text>
          </>
        )}

        {/* Düğmeler */}
        <TouchableOpacity
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
    paddingVertical: 12,
    paddingHorizontal: 4,
    borderRadius: 8,
    backgroundColor: colors.cardBg,
    borderWidth: 2,
    borderColor: colors.border,
    alignItems: 'center',
    justifyContent: 'center',
  },
  likertBtnSelected: {
    backgroundColor: colors.gold,
    borderColor: colors.gold,
  },
  likertBtnText: {
    fontSize: 14,
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
    paddingVertical: 14,
    borderRadius: 12,
    alignItems: 'center',
    marginVertical: 16,
  },
  submitBtnDisabled: {
    opacity: 0.5,
  },
  submitBtnText: {
    color: 'white',
    fontSize: 16,
    fontWeight: '600',
  },
  // Sonuçlar
  resultsHeader: {
    alignItems: 'center',
    marginVertical: 24,
  },
  resultsTitle: {
    fontSize: 28,
    fontWeight: '700',
    color: colors.text,
  },
  scoreCard: {
    backgroundColor: `${colors.gold}15`,
    borderWidth: 2,
    borderColor: colors.gold,
    alignItems: 'center',
    marginBottom: 24,
  },
  scoreLabel: {
    fontSize: 14,
    color: colors.textSecondary,
    marginBottom: 8,
  },
  scoreBig: {
    fontSize: 48,
    fontWeight: '700',
    color: colors.gold,
    marginBottom: 8,
  },
  // Alan Puanları
  domainCard: {
    marginBottom: 12,
  },
  domainHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 8,
  },
  domainName: {
    fontSize: 14,
    fontWeight: '600',
    color: colors.text,
    flex: 1,
  },
  domainScore: {
    fontSize: 16,
    fontWeight: '700',
    color: colors.gold,
  },
  domainBar: {
    height: 6,
    backgroundColor: colors.border,
    borderRadius: 3,
    marginBottom: 4,
    overflow: 'hidden',
  },
  domainBarFill: {
    height: '100%',
    backgroundColor: colors.gold,
  },
  domainLevel: {
    fontSize: 11,
    color: colors.textSecondary,
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
  // Yeniden Test Butonu
  retakeBtn: {
    backgroundColor: colors.gold,
    paddingVertical: 14,
    borderRadius: 12,
    alignItems: 'center',
    marginBottom: 16,
  },
  retakeBtnText: {
    color: 'white',
    fontSize: 16,
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

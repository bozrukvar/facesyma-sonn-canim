// src/screens/AssessmentScreen.tsx
import React, { useState, useMemo } from 'react';
import {
  View, Text, StyleSheet, ScrollView, TouchableOpacity,
  Dimensions, ActivityIndicator, Alert,
} from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { AssessmentAPI } from '../services/api';
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
const TEST_TYPES = [
  { id: 'skills', key: 'assessment.skills', key_desc: 'assessment.skills_desc', emoji: '🎯' },
  { id: 'hr', key: 'assessment.hr', key_desc: 'assessment.hr_desc', emoji: '👥' },
  { id: 'personality', key: 'assessment.personality', key_desc: 'assessment.personality_desc', emoji: '🧠' },
  { id: 'career', key: 'assessment.career', key_desc: 'assessment.career_desc', emoji: '💼' },
  { id: 'relationship', key: 'assessment.relationship', key_desc: 'assessment.relationship_desc', emoji: '❤️' },
  { id: 'vocation', key: 'assessment.vocation', key_desc: 'assessment.vocation_desc', emoji: '🏢' },
];

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
  domain: string;
  reverse_scored: boolean;
}

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
  // Must be at top level — not inside conditionals (Rules of Hooks)
  const LIKERT_LABELS = useMemo(() => getLikertLabels(lang), [lang]);

  // Seç: Test türü seç
  const startTest = async (testId: string) => {
    setSelectedTest(testId);
    setStep('loading_questions');
    setLoading(true);
    const errTitle = t('common.error', lang);
    const errGeneric = t('assessment.error_generic', lang);

    try {
      const data = await AssessmentAPI.getQuestions(testId, lang);
      if (data.success) {
        setQuestions(data.data.questions);
        setResponses({}); // Reset responses
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

  // Cevapları gönder
  const submitResponses = async () => {
    if (Object.keys(responses).length < questions.length) {
      Alert.alert(t('common.select_required', lang), t('assessment.error_incomplete', lang));
      return;
    }

    if (!selectedTest) return;

    setStep('submitting');
    setLoading(true);

    const errTitle = t('common.error', lang);
    const errGeneric = t('assessment.error_generic', lang);
    try {
      const formattedResponses = Object.entries(responses).map(([q_id, score]) => ({
        q_id,
        score,
      }));

      const data = await AssessmentAPI.submitAssessment(selectedTest, formattedResponses, lang);
      if (data.success) {
        // Try to save result to MongoDB (optional - won't block if it fails)
        try {
          await AssessmentAPI.saveResult(selectedTest, data);
        } catch {
          // Save to history is optional — unauthenticated users can still see results
        }

        setResult(data);
        setStep('results');
        dispatch(markModuleUsed('assessment'));
      } else {
        Alert.alert(errTitle, errGeneric);
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
        {TEST_TYPES.map(({ id: tId, emoji: tEmoji, key: tKey, key_desc: tKeyDesc }) => (
          <TouchableOpacity
            key={tId}
            onPress={() => startTest(tId)}
            activeOpacity={0.7}
          >
            <Card style={styles.testCard}>
              <View style={styles.testCardContent}>
                <Text style={styles.testEmoji}>{tEmoji}</Text>
                <View style={styles.testInfo}>
                  <Text style={styles.testName}>{t(tKey, lang)}</Text>
                  <Text style={styles.testDesc}>{t(tKeyDesc, lang)}</Text>
                  <Badge label={t('assessment.questions', lang)} />
                </View>
                <Text style={styles.arrow}>→</Text>
              </View>
            </Card>
          </TouchableOpacity>
        ))}

        <View style={styles.spacer20} />
      </ScrollView>
    );
  }

  // ─── Adım 2: Soruların Yüklenmesi ──────────────────────────────────────────────
  if (step === 'loading_questions' && loading) {
    return (
      <View style={styles.centerContainer}>
        <ActivityIndicator size="large" color={colors.gold} />
        <Text style={styles.loadingText}>{t('assessment.loading_questions', lang)}</Text>
      </View>
    );
  }

  // ─── Adım 3: Cevaplar ──────────────────────────────────────────────────────────
  const questionsLen = questions.length;
  if (step === 'answering' && questionsLen > 0) {
    const answeredCount = Object.keys(responses).length;
    const testInfo = TEST_TYPES.find(t => t.id === selectedTest);

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
                ? (LIKERT_LABELS[responses[qId] - 1] ?? t('assessment.choose_answer', lang))
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

  // ─── Adım 4: Sonuçlar ──────────────────────────────────────────────────────────
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
});

export default AssessmentScreen;

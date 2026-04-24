// src/screens/AssessmentHistoryScreen.tsx
import React, { useState, useEffect } from 'react';
import {
  View, Text, StyleSheet, ScrollView, TouchableOpacity,
  ActivityIndicator, Alert, RefreshControl,
} from 'react-native';
import { AssessmentAPI } from '../services/api';
import { Card, SectionLabel, Badge } from '../components/ui';
import theme from '../utils/theme';
const { colors } = theme;
import { useLanguage } from '../utils/LanguageContext';
import { t } from '../utils/i18n';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import type { ScreenProps } from '../navigation/types';

// Map language codes to locales
const getLocale = (lang: string): string => {
  const localeMap: Record<string, string> = {
    'tr': 'tr-TR',
    'en': 'en-US',
    'de': 'de-DE',
    'ru': 'ru-RU',
    'ar': 'ar-SA',
    'es': 'es-ES',
    'ko': 'ko-KR',
    'ja': 'ja-JP',
    'zh': 'zh-CN',
    'hi': 'hi-IN',
    'fr': 'fr-FR',
    'pt': 'pt-PT',
    'bn': 'bn-IN',
    'id': 'id-ID',
    'ur': 'ur-PK',
    'it': 'it-IT',
    'vi': 'vi-VN',
    'pl': 'pl-PL',
  };
  return localeMap[lang] || 'en-US';
};

const TEST_TYPE_NAMES: Record<string, { key: string; emoji: string }> = {
  'skills': { key: 'assessment.skills', emoji: '🎯' },
  'hr': { key: 'assessment.hr', emoji: '👥' },
  'personality': { key: 'assessment.personality', emoji: '🧠' },
  'career': { key: 'assessment.career', emoji: '💼' },
  'relationship': { key: 'assessment.relationship', emoji: '❤️' },
  'vocation': { key: 'assessment.vocation', emoji: '🏢' },
};

const LEVEL_COLORS: Record<string, string> = {
  // Türkçe
  'Çok Yüksek': '#4CAF50',
  'Yüksek':     '#8BC34A',
  'Orta':       '#FF9800',
  'Düşük':      '#FF5722',
  'Çok Düşük':  '#F44336',
  // İngilizce
  'Very High': '#4CAF50',
  'High':      '#8BC34A',
  'Medium':    '#FF9800',
  'Low':       '#FF5722',
  'Very Low':  '#F44336',
};

interface AssessmentResult {
  id: string;
  test_type: string;
  overall_score: number;
  overall_level_tr: string;
  created_at: string;
  responses_counted: number;
}

const AssessmentHistoryScreen = ({ navigation }: ScreenProps<'AssessmentHistory'>) => {
  const insets    = useSafeAreaInsets();
  const insetsTop = insets.top;
  const { lang } = useLanguage();
  const [results, setResults] = useState<AssessmentResult[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  useEffect(() => {
    loadHistory();
  }, []);

  const loadHistory = async () => {
    setLoading(true);
    try {
      const data = await AssessmentAPI.getHistory(20);
      if (data.success) {
        setResults(data.data.results);
      } else {
        Alert.alert(t('common.error', lang), t('assessment_history.error_load', lang));
      }
    } catch (error: any) {
      if (error.response?.status === 401) {
        Alert.alert(t('common.authentication_required', lang), t('common.please_login', lang));
        navigation.navigate('Auth');
      } else {
        Alert.alert(t('common.error', lang), error.response?.data?.detail || t('common.generic_error', lang));
      }
    } finally {
      setLoading(false);
    }
  };

  const onRefresh = async () => {
    setRefreshing(true);
    try {
      const data = await AssessmentAPI.getHistory(20);
      if (data.success) {
        setResults(data.data.results);
      }
    } catch {
      // Refresh failure is silent — stale data remains visible
    } finally {
      setRefreshing(false);
    }
  };

  const formatDate = (dateStr: string) => {
    const date = new Date(dateStr);
    const locale = getLocale(lang);
    return date.toLocaleDateString(locale, {
      year: 'numeric',
      month: 'long',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  if (loading) {
    return (
      <View style={styles.centerContainer}>
        <ActivityIndicator size="large" color={colors.gold} />
        <Text style={styles.loadingText}>{t('assessment_history.loading', lang)}</Text>
      </View>
    );
  }

  if (results.length === 0) {
    return (
      <ScrollView
        style={styles.container}
        contentContainerStyle={{ paddingTop: insetsTop }}
        refreshControl={<RefreshControl refreshing={refreshing} onRefresh={onRefresh} />}
      >
        <View style={styles.emptyContainer}>
          <Text style={styles.emptyEmoji}>📋</Text>
          <Text style={styles.emptyTitle}>{t('assessment_history.empty', lang)}</Text>
          <Text style={styles.emptyDesc}>
            {t('assessment_history.empty_desc', lang)}
          </Text>
          <TouchableOpacity
            style={styles.startBtn}
            onPress={() => navigation.navigate('Assessment')}
          >
            <Text style={styles.startBtnText}>{t('assessment_history.start_btn', lang)}</Text>
          </TouchableOpacity>
        </View>
      </ScrollView>
    );
  }

  return (
    <ScrollView
      style={styles.container}
      contentContainerStyle={{ paddingTop: insetsTop }}
      refreshControl={<RefreshControl refreshing={refreshing} onRefresh={onRefresh} />}
    >
      <View style={styles.header}>
        <Text style={styles.title}>{t('assessment_history.title', lang)}</Text>
        <Text style={styles.subtitle}>{results.length} {t('assessment_history.tests_count', lang)}</Text>
      </View>

      {results.map((result) => {
        const rType      = result.test_type;
        const levelTr    = result.overall_level_tr;
        const testInfo   = TEST_TYPE_NAMES[rType];
        const levelColor = LEVEL_COLORS[levelTr] || colors.gold;

        return (
          <Card key={result.id} style={styles.resultCard}>
            <View style={styles.resultHeader}>
              <View style={styles.resultTitleGroup}>
                <Text style={styles.resultEmoji}>{testInfo?.emoji || '📋'}</Text>
                <View style={styles.resultTitleContent}>
                  <Text style={styles.resultTitle}>
                    {testInfo ? t(testInfo.key, lang) : rType}
                  </Text>
                  <Text style={styles.resultDate}>{formatDate(result.created_at)}</Text>
                </View>
              </View>
              <View style={styles.resultScoreGroup}>
                <Text style={[styles.resultScore, { color: levelColor }]}>
                  {(Number(result.overall_score) || 0).toFixed(1)}
                </Text>
                <Text style={[styles.resultLevel, { color: levelColor }]}>
                  {levelTr}
                </Text>
              </View>
            </View>

            <View style={styles.resultMeta}>
              <Badge label={`${result.responses_counted} ${t('assessment_history.questions', lang)}`} />
            </View>
          </Card>
        );
      })}

      <View style={styles.bottomSpacer} />
    </ScrollView>
  );
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
  loadingText: {
    marginTop: 16,
    fontSize: 16,
    color: colors.text,
  },
  header: {
    marginTop: 16,
    marginBottom: 20,
  },
  title: {
    fontSize: 28,
    fontWeight: 'bold',
    color: colors.text,
    marginBottom: 4,
  },
  subtitle: {
    fontSize: 14,
    color: colors.textSecondary,
  },
  resultCard: {
    marginBottom: 12,
  },
  resultHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 12,
  },
  resultTitleGroup: {
    flex: 1,
    flexDirection: 'row',
    alignItems: 'center',
  },
  resultEmoji: {
    fontSize: 32,
    marginRight: 12,
  },
  resultTitleContent: {
    flex: 1,
  },
  resultTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: colors.text,
    marginBottom: 4,
  },
  resultDate: {
    fontSize: 12,
    color: colors.textSecondary,
  },
  resultScoreGroup: {
    alignItems: 'flex-end',
  },
  resultScore: {
    fontSize: 28,
    fontWeight: '700',
    marginBottom: 2,
  },
  resultLevel: {
    fontSize: 12,
    fontWeight: '600',
  },
  resultMeta: {
    borderTopWidth: 1,
    borderTopColor: colors.border,
    paddingTop: 12,
  },
  emptyContainer: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 60,
    paddingHorizontal: 20,
  },
  emptyEmoji: {
    fontSize: 60,
    marginBottom: 16,
  },
  emptyTitle: {
    fontSize: 20,
    fontWeight: '600',
    color: colors.text,
    marginBottom: 8,
    textAlign: 'center',
  },
  emptyDesc: {
    fontSize: 14,
    color: colors.textSecondary,
    textAlign: 'center',
    marginBottom: 24,
  },
  startBtn: {
    backgroundColor: colors.gold,
    paddingVertical: 12,
    paddingHorizontal: 24,
    borderRadius: 8,
  },
  startBtnText: {
    color: 'white',
    fontSize: 16,
    fontWeight: '600',
  },
  bottomSpacer: { height: 20 },
});

export default AssessmentHistoryScreen;

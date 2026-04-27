// src/screens/AssessmentHistoryScreen.tsx
import React, { useState, useEffect } from 'react';
import {
  View, Text, StyleSheet, ScrollView, TouchableOpacity,
  ActivityIndicator, Alert, RefreshControl,
} from 'react-native';
import { useSelector } from 'react-redux';
import { RootState } from '../store';
import { AssessmentAPI, AnalysisAPI } from '../services/api';
import { Card, SectionLabel, Badge } from '../components/ui';
import theme from '../utils/theme';
const { colors } = theme;
import { useLanguage } from '../utils/LanguageContext';
import { t } from '../utils/i18n';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import type { ScreenProps } from '../navigation/types';

const FREE_VISIBLE_LIMIT = 3;

const getLocale = (lang: string): string => {
  const localeMap: Record<string, string> = {
    'tr': 'tr-TR', 'en': 'en-US', 'de': 'de-DE', 'ru': 'ru-RU',
    'ar': 'ar-SA', 'es': 'es-ES', 'ko': 'ko-KR', 'ja': 'ja-JP',
    'zh': 'zh-CN', 'hi': 'hi-IN', 'fr': 'fr-FR', 'pt': 'pt-PT',
    'bn': 'bn-IN', 'id': 'id-ID', 'ur': 'ur-PK', 'it': 'it-IT',
    'vi': 'vi-VN', 'pl': 'pl-PL',
  };
  return localeMap[lang] || 'en-US';
};

const TEST_TYPE_NAMES: Record<string, { key: string; emoji: string }> = {
  'skills':       { key: 'assessment.skills',       emoji: '🎯' },
  'hr':           { key: 'assessment.hr',            emoji: '👥' },
  'personality':  { key: 'assessment.personality',   emoji: '🧠' },
  'career':       { key: 'assessment.career',        emoji: '💼' },
  'relationship': { key: 'assessment.relationship',  emoji: '❤️' },
  'vocation':     { key: 'assessment.vocation',      emoji: '🏢' },
};

const LEVEL_COLORS: Record<string, string> = {
  'Çok Yüksek': '#4CAF50', 'Yüksek': '#8BC34A', 'Orta': '#FF9800',
  'Düşük': '#FF5722', 'Çok Düşük': '#F44336',
  'Very High': '#4CAF50', 'High': '#8BC34A', 'Medium': '#FF9800',
  'Low': '#FF5722', 'Very Low': '#F44336',
};

interface AssessmentResult {
  id: string;
  test_type: string;
  overall_score: number;
  overall_level_tr: string;
  created_at: string;
  responses_counted: number;
}

interface TwinsHistoryItem {
  id?: string;
  mode: string;
  created_at: number;
  result: {
    group_score: number;
    person_count: number;
    community_type?: string;
    pair_scores?: Record<string, number>;
  };
}

const AssessmentHistoryScreen = ({ navigation }: ScreenProps<'AssessmentHistory'>) => {
  const insets    = useSafeAreaInsets();
  const { lang }  = useLanguage();
  const user      = useSelector((s: RootState) => s.auth.user);
  const isPremium = user?.plan === 'premium';

  const [results,      setResults]      = useState<AssessmentResult[]>([]);
  const [twinsHistory, setTwinsHistory] = useState<TwinsHistoryItem[]>([]);
  const [loading,      setLoading]      = useState(true);
  const [refreshing,   setRefreshing]   = useState(false);
  const [deleting,     setDeleting]     = useState<string | null>(null);

  useEffect(() => { loadHistory(); }, []);

  const loadHistory = async () => {
    setLoading(true);
    try {
      const [assessData, analysisData] = await Promise.allSettled([
        AssessmentAPI.getHistory(50),
        AnalysisAPI.getHistory(),
      ]);
      if (assessData.status === 'fulfilled' && assessData.value.success) {
        setResults(assessData.value.data.results);
      }
      if (analysisData.status === 'fulfilled') {
        const records = analysisData.value?.results ?? [];
        setTwinsHistory(records.filter((r: any) => r.mode === 'twins'));
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
      const [assessData, analysisData] = await Promise.allSettled([
        AssessmentAPI.getHistory(50),
        AnalysisAPI.getHistory(),
      ]);
      if (assessData.status === 'fulfilled' && assessData.value.success) {
        setResults(assessData.value.data.results);
      }
      if (analysisData.status === 'fulfilled') {
        const records = analysisData.value?.results ?? [];
        setTwinsHistory(records.filter((r: any) => r.mode === 'twins'));
      }
    } catch { /* silent */ }
    finally { setRefreshing(false); }
  };

  const handleDeleteOne = (id: string) => {
    Alert.alert('Sil', 'Bu test sonucunu silmek istiyor musunuz?', [
      { text: 'İptal', style: 'cancel' },
      {
        text: 'Sil', style: 'destructive',
        onPress: async () => {
          setDeleting(id);
          try {
            await AnalysisAPI.deleteHistory(id);
            setResults(prev => prev.filter(r => r.id !== id));
          } catch {
            Alert.alert('Hata', 'Silinemedi.');
          } finally {
            setDeleting(null);
          }
        },
      },
    ]);
  };

  const handleDeleteAll = () => {
    Alert.alert('Tümünü Sil', 'Tüm test geçmişiniz kalıcı olarak silinecek. Devam edilsin mi?', [
      { text: 'İptal', style: 'cancel' },
      {
        text: 'Tümünü Sil', style: 'destructive',
        onPress: async () => {
          setDeleting('all');
          try {
            await AnalysisAPI.deleteAllHistory();
            setResults([]);
          } catch {
            Alert.alert('Hata', 'Silinemedi.');
          } finally {
            setDeleting(null);
          }
        },
      },
    ]);
  };

  const formatDate = (dateStr: string) => {
    const date = new Date(dateStr);
    return date.toLocaleDateString(getLocale(lang), {
      year: 'numeric', month: 'long', day: 'numeric',
      hour: '2-digit', minute: '2-digit',
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
        contentContainerStyle={{ paddingTop: insets.top }}
        refreshControl={<RefreshControl refreshing={refreshing} onRefresh={onRefresh} />}
      >
        <View style={styles.emptyContainer}>
          <Text style={styles.emptyEmoji}>📋</Text>
          <Text style={styles.emptyTitle}>{t('assessment_history.empty', lang)}</Text>
          <Text style={styles.emptyDesc}>{t('assessment_history.empty_desc', lang)}</Text>
          <TouchableOpacity style={styles.startBtn} onPress={() => navigation.navigate('Assessment')}>
            <Text style={styles.startBtnText}>{t('assessment_history.start_btn', lang)}</Text>
          </TouchableOpacity>
        </View>
      </ScrollView>
    );
  }

  return (
    <ScrollView
      style={styles.container}
      contentContainerStyle={{ paddingTop: insets.top }}
      refreshControl={<RefreshControl refreshing={refreshing} onRefresh={onRefresh} />}
    >
      <View style={styles.header}>
        <View>
          <Text style={styles.title}>{t('assessment_history.title', lang)}</Text>
          <Text style={styles.subtitle}>{results.length} {t('assessment_history.tests_count', lang)}</Text>
        </View>
        <TouchableOpacity
          style={styles.deleteAllBtn}
          onPress={handleDeleteAll}
          disabled={deleting === 'all'}
        >
          {deleting === 'all'
            ? <ActivityIndicator size="small" color={colors.error} />
            : <Text style={styles.deleteAllText}>Tümünü Sil</Text>
          }
        </TouchableOpacity>
      </View>

      {/* Free plan: only first 3 visible, rest locked */}
      {!isPremium && results.length > FREE_VISIBLE_LIMIT && (
        <View style={styles.freeBanner}>
          <Text style={styles.freeBannerIcon}>🔒</Text>
          <Text style={styles.freeBannerText}>
            Ücretsiz planda yalnızca son {FREE_VISIBLE_LIMIT} sonuç görüntülenir. Tüm geçmişe erişmek için Premium'a geçin.
          </Text>
        </View>
      )}

      {results.map((result, index) => {
        const isLocked  = !isPremium && index >= FREE_VISIBLE_LIMIT;
        const testInfo  = TEST_TYPE_NAMES[result.test_type];
        const levelColor = LEVEL_COLORS[result.overall_level_tr] || colors.gold;

        return (
          <Card key={result.id} style={[styles.resultCard, isLocked && styles.resultCardLocked]}>
            {isLocked ? (
              <View style={styles.lockedRow}>
                <Text style={styles.lockedEmoji}>🔒</Text>
                <View style={{ flex: 1 }}>
                  <Text style={styles.lockedTitle}>{testInfo?.emoji || '📋'} {testInfo ? t(testInfo.key, lang) : result.test_type}</Text>
                  <Text style={styles.lockedDate}>{formatDate(result.created_at)}</Text>
                </View>
                <TouchableOpacity style={styles.premiumChip}>
                  <Text style={styles.premiumChipText}>Premium</Text>
                </TouchableOpacity>
              </View>
            ) : (
              <>
                <View style={styles.resultHeader}>
                  <View style={styles.resultTitleGroup}>
                    <Text style={styles.resultEmoji}>{testInfo?.emoji || '📋'}</Text>
                    <View style={styles.resultTitleContent}>
                      <Text style={styles.resultTitle}>
                        {testInfo ? t(testInfo.key, lang) : result.test_type}
                      </Text>
                      <Text style={styles.resultDate}>{formatDate(result.created_at)}</Text>
                    </View>
                  </View>
                  <View style={styles.resultScoreGroup}>
                    <Text style={[styles.resultScore, { color: levelColor }]}>
                      {(Number(result.overall_score) || 0).toFixed(1)}
                    </Text>
                    <Text style={[styles.resultLevel, { color: levelColor }]}>
                      {result.overall_level_tr}
                    </Text>
                  </View>
                </View>

                <View style={styles.resultMeta}>
                  <Badge label={`${result.responses_counted} ${t('assessment_history.questions', lang)}`} />
                  <TouchableOpacity
                    style={styles.deleteBtn}
                    onPress={() => handleDeleteOne(result.id)}
                    disabled={deleting === result.id}
                  >
                    {deleting === result.id
                      ? <ActivityIndicator size="small" color={colors.error} />
                      : <Text style={styles.deleteBtnText}>🗑</Text>
                    }
                  </TouchableOpacity>
                </View>
              </>
            )}
          </Card>
        );
      })}

      {/* Twins History Section */}
      {twinsHistory.length > 0 && (
        <>
          <View style={styles.sectionDivider}>
            <Text style={styles.sectionTitle}>👥 {t('assessment_history.twins_section', lang)}</Text>
          </View>

          {twinsHistory.map((item, index) => {
            const isLocked = !isPremium && index >= FREE_VISIBLE_LIMIT;
            const dateStr  = typeof item.created_at === 'number'
              ? formatDate(new Date(item.created_at * 1000).toISOString())
              : formatDate(String(item.created_at));
            const score    = Math.round(item.result?.group_score ?? 0);
            const count    = item.result?.person_count ?? 0;
            const commType = item.result?.community_type ?? '';

            return (
              <Card key={item.id ?? index} style={[styles.resultCard, isLocked && styles.resultCardLocked]}>
                {isLocked ? (
                  <View style={styles.lockedRow}>
                    <Text style={styles.lockedEmoji}>🔒</Text>
                    <View style={{ flex: 1 }}>
                      <Text style={styles.lockedTitle}>👥 {t('assessment.twins', lang)}</Text>
                      <Text style={styles.lockedDate}>{dateStr}</Text>
                    </View>
                    <TouchableOpacity style={styles.premiumChip}>
                      <Text style={styles.premiumChipText}>Premium</Text>
                    </TouchableOpacity>
                  </View>
                ) : (
                  <>
                    <View style={styles.resultHeader}>
                      <View style={styles.resultTitleGroup}>
                        <Text style={styles.resultEmoji}>👥</Text>
                        <View style={styles.resultTitleContent}>
                          <Text style={styles.resultTitle}>{t('assessment.twins', lang)}</Text>
                          <Text style={styles.resultDate}>{dateStr}</Text>
                        </View>
                      </View>
                      <View style={styles.resultScoreGroup}>
                        <Text style={[styles.resultScore, { color: score >= 70 ? '#4CAF50' : score >= 40 ? '#FF9800' : '#FF5722' }]}>
                          %{score}
                        </Text>
                        <Text style={[styles.resultLevel, { color: colors.textSecondary }]}>
                          {count} {t('assessment_history.persons', lang)}
                        </Text>
                      </View>
                    </View>
                    {commType ? (
                      <View style={styles.resultMeta}>
                        <Badge label={`🏘 ${commType}`} />
                      </View>
                    ) : null}
                  </>
                )}
              </Card>
            );
          })}
        </>
      )}

      <View style={styles.bottomSpacer} />
    </ScrollView>
  );
};

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: colors.background, paddingHorizontal: 16 },
  centerContainer: { flex: 1, justifyContent: 'center', alignItems: 'center', backgroundColor: colors.background },
  loadingText: { marginTop: 16, fontSize: 16, color: colors.text },

  header: {
    flexDirection: 'row', justifyContent: 'space-between', alignItems: 'flex-end',
    marginTop: 16, marginBottom: 16,
  },
  title:        { fontSize: 28, fontWeight: 'bold', color: colors.text, marginBottom: 4 },
  subtitle:     { fontSize: 14, color: colors.textSecondary },
  deleteAllBtn: { paddingHorizontal: 12, paddingVertical: 6, borderRadius: 8, borderWidth: 1, borderColor: colors.error + '88' },
  deleteAllText:{ fontSize: 12, color: colors.error },

  freeBanner: {
    flexDirection: 'row', alignItems: 'flex-start', gap: 8,
    backgroundColor: colors.surface, borderRadius: 10,
    borderWidth: 1, borderColor: colors.gold + '44',
    padding: 12, marginBottom: 12,
  },
  freeBannerIcon: { fontSize: 16 },
  freeBannerText: { flex: 1, fontSize: 12, color: colors.textSecondary, lineHeight: 18 },

  resultCard:       { marginBottom: 12 },
  resultCardLocked: { opacity: 0.6 },

  lockedRow: { flexDirection: 'row', alignItems: 'center', gap: 8 },
  lockedEmoji:{ fontSize: 18 },
  lockedTitle:{ fontSize: 14, fontWeight: '600', color: colors.textSecondary, marginBottom: 2 },
  lockedDate: { fontSize: 12, color: colors.textMuted },
  premiumChip:{
    backgroundColor: colors.goldGlow, borderRadius: 20,
    borderWidth: 1, borderColor: colors.goldDark,
    paddingHorizontal: 8, paddingVertical: 3,
  },
  premiumChipText: { fontSize: 11, color: colors.gold, fontWeight: '600' },

  resultHeader:       { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 },
  resultTitleGroup:   { flex: 1, flexDirection: 'row', alignItems: 'center' },
  resultEmoji:        { fontSize: 32, marginRight: 12 },
  resultTitleContent: { flex: 1 },
  resultTitle:        { fontSize: 16, fontWeight: '600', color: colors.text, marginBottom: 4 },
  resultDate:         { fontSize: 12, color: colors.textSecondary },
  resultScoreGroup:   { alignItems: 'flex-end' },
  resultScore:        { fontSize: 28, fontWeight: '700', marginBottom: 2 },
  resultLevel:        { fontSize: 12, fontWeight: '600' },

  resultMeta: {
    flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center',
    borderTopWidth: 1, borderTopColor: colors.border, paddingTop: 12,
  },
  deleteBtn:     { padding: 6 },
  deleteBtnText: { fontSize: 18 },

  emptyContainer: {
    flex: 1, alignItems: 'center', justifyContent: 'center',
    paddingVertical: 60, paddingHorizontal: 20,
  },
  emptyEmoji:  { fontSize: 60, marginBottom: 16 },
  emptyTitle:  { fontSize: 20, fontWeight: '600', color: colors.text, marginBottom: 8, textAlign: 'center' },
  emptyDesc:   { fontSize: 14, color: colors.textSecondary, textAlign: 'center', marginBottom: 24 },
  startBtn:    { backgroundColor: colors.gold, paddingVertical: 12, paddingHorizontal: 24, borderRadius: 8 },
  startBtnText:{ color: 'white', fontSize: 16, fontWeight: '600' },
  bottomSpacer:{ height: 20 },

  sectionDivider: {
    marginTop: 8, marginBottom: 12,
    flexDirection: 'row', alignItems: 'center',
  },
  sectionTitle: {
    fontSize: 16, fontWeight: '700', color: colors.text,
  },
});

export default AssessmentHistoryScreen;

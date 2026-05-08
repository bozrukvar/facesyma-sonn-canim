// src/screens/DailyScreen.tsx
// Günlük motivasyon + AI koçluk mesajı
import React, { useEffect, useState } from 'react';
import { View, Text, StyleSheet, ScrollView, TouchableOpacity, ActivityIndicator } from 'react-native';
import { Card, GoldButton, SectionLabel } from '../components/ui';
import { AnalysisAPI } from '../services/api';
import theme from '../utils/theme';
const { colors, spacing, typography } = theme;
import { useLanguage } from '../utils/LanguageContext';
import { t } from '../utils/i18n';
import { useDispatch, useSelector } from 'react-redux';
import { AppDispatch, RootState } from '../store';
import { markModuleUsed } from '../store/authSlice';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import type { ScreenProps } from '../navigation/types';

const DailyScreen = ({ navigation, route }: ScreenProps<'Daily'>) => {
  const insets   = useSafeAreaInsets();
  const dispatch = useDispatch<AppDispatch>();
  const modulesUsed = useSelector((s: RootState) => s.auth.modulesUsed);
  const [daily,     setDaily]     = useState<string>('');
  const [aiPowered, setAiPowered] = useState(false);
  const [loading,   setLoading]   = useState(true);
  // hasAnalysis: local flag OR backend confirmed ai_powered (user has analysis in DB)
  const [backendHasAnalysis, setBackendHasAnalysis] = useState(false);
  const hasAnalysis = modulesUsed.includes('face_analysis') || backendHasAnalysis;
  const { lang } = useLanguage();

  useEffect(() => {
    AnalysisAPI.getDailyMotivation(lang)
      .then(d => {
        setDaily(d?.positive || d?.message || d?.daily || '');
        const powered = !!d?.ai_powered;
        setAiPowered(powered);
        if (powered) setBackendHasAnalysis(true);
        dispatch(markModuleUsed('daily'));
      })
      .catch(() => setDaily(t('common.generic_error', lang)))
      .finally(() => setLoading(false));
  }, [lang]);

  return (
    <View style={styles.container}>
      <View style={[styles.header, { paddingTop: insets.top + spacing.sm }]}>
        <TouchableOpacity onPress={() => navigation.goBack()}
          accessibilityRole="button"
          accessibilityLabel={t('daily.title', lang)}
        >
          <Text style={styles.back}>←</Text>
        </TouchableOpacity>
        <Text style={styles.title}>{t('daily.title', lang)}</Text>
        <View style={styles.spacer} />
      </View>
      <ScrollView contentContainerStyle={styles.scroll} showsVerticalScrollIndicator={false}>
        {!hasAnalysis && (
          <TouchableOpacity
            accessibilityRole="button"
            accessibilityLabel={t('coach.no_analysis', lang)}
            style={styles.noAnalysisBanner}
            onPress={() => navigation.navigate('Analysis' as any)}
            activeOpacity={0.8}
          >
            <Text style={styles.noAnalysisIcon}>👁️</Text>
            <View style={styles.noAnalysisText}>
              <Text style={styles.noAnalysisTitle}>{t('coach.no_analysis', lang)}</Text>
              <Text style={styles.noAnalysisCta}>{t('home.analyze_cta', lang)} →</Text>
            </View>
          </TouchableOpacity>
        )}
        <Card variant="warm" style={styles.card}>
          <Text style={styles.cardEmoji}>🌟</Text>
          {loading
            ? <ActivityIndicator color={colors.warmAmber} />
            : <>
                <Text style={styles.dailyText}>{daily || t('daily.loading', lang)}</Text>
                {aiPowered && (
                  <View style={styles.aiBadge}>
                    <Text style={styles.aiBadgeText}>✦ {t('daily.ai_powered', lang)}</Text>
                  </View>
                )}
              </>
          }
        </Card>
        <GoldButton
          title={t('daily.talk_assistant', lang)}
          variant="warm"
          onPress={() => navigation.navigate('Chat', { lang })}
        />
      </ScrollView>
    </View>
  );
};

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: colors.background },
  header: {
    flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between',
    paddingHorizontal: spacing.lg,
    paddingBottom: spacing.md, borderBottomWidth: 1, borderBottomColor: colors.border,
  },
  back:      { ...typography.body, color: colors.gold, fontSize: 22 },
  title:     { ...typography.h3 },
  scroll:    { padding: spacing.lg, paddingBottom: spacing.xxxl },
  dailyText: { ...typography.bodyWarm, fontSize: 16, lineHeight: 26, textAlign: 'center' },
  spacer:    { width: 40 },
  noAnalysisBanner: {
    flexDirection: 'row', alignItems: 'center',
    backgroundColor: colors.surface, borderRadius: 12,
    borderWidth: 1, borderColor: colors.warmAmber + '55',
    padding: spacing.md, marginBottom: spacing.md,
  },
  noAnalysisIcon: { fontSize: 28, marginRight: spacing.sm },
  noAnalysisText: { flex: 1 },
  noAnalysisTitle: { ...typography.body, color: colors.text, fontSize: 13, marginBottom: 2 },
  noAnalysisCta:   { ...typography.body, color: colors.warmAmber, fontSize: 12, fontWeight: '700' as const },
  card:         { marginBottom: 16 },
  cardEmoji:    { fontSize: 40, textAlign: 'center' as const, marginBottom: 12 },
  aiBadge:      { marginTop: 12, alignSelf: 'center' as const, backgroundColor: colors.surface, borderRadius: 12, paddingHorizontal: 10, paddingVertical: 4 },
  aiBadgeText:  { fontSize: 11, color: colors.gold, fontWeight: '600' as const },
});

export default DailyScreen;

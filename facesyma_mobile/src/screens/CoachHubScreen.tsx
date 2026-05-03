// src/screens/CoachHubScreen.tsx
import React, { useEffect, useState, useCallback } from 'react';
import {
  View, Text, StyleSheet, ScrollView, TouchableOpacity,
  ActivityIndicator, StatusBar, Alert,
} from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { useSelector } from 'react-redux';
import { RootState } from '../store';
import { CoachAPI } from '../services/api';
import theme from '../utils/theme';
import { useLanguage } from '../utils/LanguageContext';
import { t } from '../utils/i18n';
import type { ScreenProps } from '../navigation/types';

const { colors, spacing, typography, radius, shadow } = theme;

type Props = ScreenProps<'CoachHub'>;

interface ModuleCard {
  id: string;
  emoji: string;
  titleKey: string;
  moduleKey: string;
  accent: string;
}

const MODULE_CARDS: ModuleCard[] = [
  { id: 'health',       emoji: '🏃', titleKey: 'coach.mod_health',       moduleKey: 'saglik_esenwlik',    accent: '#7AE07A' },
  { id: 'career',       emoji: '💼', titleKey: 'coach.mod_career',        moduleKey: 'kariyer_yolu',       accent: '#7AAEE0' },
  { id: 'relationship', emoji: '💞', titleKey: 'coach.mod_relationship',  moduleKey: 'iliski_yonetimi',    accent: '#E07A7A' },
  { id: 'stress',       emoji: '🧘', titleKey: 'coach.mod_stress',        moduleKey: 'stres_yonetimi',     accent: '#9B7AE0' },
  { id: 'confidence',   emoji: '✨', titleKey: 'coach.mod_confidence',    moduleKey: 'ozguven',            accent: '#F5C842' },
  { id: 'meditation',   emoji: '🌿', titleKey: 'coach.mod_meditation',    moduleKey: 'meditasyon_egzersiz',accent: '#7AE0B0' },
  { id: 'fashion',      emoji: '👗', titleKey: 'coach.mod_fashion',       moduleKey: 'giyim',              accent: '#E0A17A' },
  { id: 'book',         emoji: '📚', titleKey: 'coach.mod_book',          moduleKey: 'kitap_tavsiye',      accent: '#B07AE0' },
  { id: 'film',         emoji: '🎬', titleKey: 'coach.mod_film',          moduleKey: 'film_tavsiye',       accent: '#E07AB0' },
  { id: 'music',        emoji: '🎵', titleKey: 'coach.mod_music',         moduleKey: 'muzik_tavsiye',      accent: '#7AB0E0' },
  { id: 'travel',       emoji: '✈️', titleKey: 'coach.mod_travel',        moduleKey: 'seyahat_tavsiye',    accent: '#E0D07A' },
  { id: 'astrology',    emoji: '⭐', titleKey: 'coach.mod_astrology',     moduleKey: 'astroloji_harita',   accent: '#C07AE0' },
];

const CoachHubScreen: React.FC<Props> = ({ navigation }) => {
  const insets = useSafeAreaInsets();
  const { lang } = useLanguage();
  const lastAnalysis = useSelector((s: RootState) => s.analysis.lastResult);

  const [analyzing, setAnalyzing]   = useState(false);
  const [coachData, setCoachData]   = useState<Record<string, any> | null>(null);

  const runAnalysis = useCallback(async () => {
    if (!lastAnalysis) {
      Alert.alert('', t('coach.no_analysis', lang));
      return;
    }
    setAnalyzing(true);
    try {
      const res = await CoachAPI.analyzeWithCoach(lastAnalysis, lang);
      setCoachData(res);
    } catch {
      Alert.alert('', t('common.error', lang));
    } finally {
      setAnalyzing(false);
    }
  }, [lastAnalysis, lang]);

  const dominantArchetypes: string[] = coachData?.archetypes_used ?? [];

  return (
    <View style={styles.container}>
      <StatusBar barStyle="light-content" />
      <ScrollView
        showsVerticalScrollIndicator={false}
        contentContainerStyle={[styles.scroll, { paddingTop: insets.top + spacing.md }]}
      >
        {/* Header */}
        <View style={styles.header}>
          <TouchableOpacity onPress={() => navigation.goBack()} style={styles.backBtn}>
            <Text style={styles.backArrow}>←</Text>
          </TouchableOpacity>
          <View style={styles.headerBody}>
            <Text style={styles.headerTitle}>{t('coach.title', lang)}</Text>
            <Text style={styles.headerSub}>{t('coach.subtitle', lang)}</Text>
          </View>
        </View>

        {/* Analyze button */}
        <TouchableOpacity
          style={[styles.analyzeBtn, analyzing && styles.analyzeBtnDisabled]}
          onPress={runAnalysis}
          activeOpacity={0.85}
          disabled={analyzing}
        >
          <View style={styles.analyzeGlow} />
          {analyzing ? (
            <ActivityIndicator color={colors.gold} style={styles.analyzeLoader} />
          ) : (
            <Text style={styles.analyzeEmoji}>🧠</Text>
          )}
          <View style={styles.analyzeBody}>
            <Text style={styles.analyzeTitle}>
              {analyzing ? t('coach.analyzing', lang) : t('coach.analyze_btn', lang)}
            </Text>
            {dominantArchetypes.length > 0 && (
              <Text style={styles.archetypeRow} numberOfLines={1}>
                {dominantArchetypes.slice(0, 3).join(' · ')}
              </Text>
            )}
          </View>
          {!analyzing && <Text style={styles.analyzeArrow}>→</Text>}
        </TouchableOpacity>

        {/* Health disclaimer if present */}
        {coachData?.health_disclaimer && (
          <View style={styles.disclaimer}>
            <Text style={styles.disclaimerText} numberOfLines={3}>
              ⚠️ {coachData.health_disclaimer.text}
            </Text>
          </View>
        )}

        {/* Module grid */}
        <Text style={styles.sectionLabel}>{t('coach.modules_title', lang)}</Text>
        <View style={styles.grid}>
          {MODULE_CARDS.map((card) => {
            const hasData = coachData?.coach_modules?.[card.moduleKey];
            return (
              <View
                key={card.id}
                style={[styles.moduleCard, { borderColor: `${card.accent}30` }]}
              >
                <View style={[styles.moduleIcon, { backgroundColor: `${card.accent}18` }]}>
                  <Text style={styles.moduleEmoji}>{card.emoji}</Text>
                </View>
                <Text style={styles.moduleTitle}>{t(card.titleKey, lang)}</Text>
                {hasData ? (
                  <View style={styles.moduleDot} />
                ) : (
                  <View style={[styles.moduleDot, styles.moduleDotEmpty]} />
                )}
              </View>
            );
          })}
        </View>

        {/* Coach result cards */}
        {coachData && Object.entries(coachData.coach_modules ?? {}).map(([modKey, modData]) => {
          const card = MODULE_CARDS.find(c => c.moduleKey === modKey);
          const items = modData as any[];
          if (!items?.length) return null;
          return (
            <View key={modKey} style={[styles.resultCard, { borderLeftColor: card?.accent ?? colors.gold }]}>
              <Text style={styles.resultCardTitle}>
                {card ? `${card.emoji} ${t(card.titleKey, lang)}` : modKey}
              </Text>
              {items.slice(0, 2).map((item: any, idx: number) => {
                const data = item.data;
                if (!data) return null;
                const text = typeof data === 'string'
                  ? data
                  : data.coaching?.felsefe ?? data.coaching?.philosophy ?? JSON.stringify(data).slice(0, 120);
                return (
                  <Text key={idx} style={styles.resultCardText} numberOfLines={4}>
                    {text}
                  </Text>
                );
              })}
            </View>
          );
        })}

        {/* Quick actions */}
        <Text style={styles.sectionLabel}>{t('coach.goals_btn', lang)}</Text>
        <View style={styles.actionRow}>
          <TouchableOpacity
            style={[styles.actionCard, { borderColor: `${colors.gold}40` }]}
            onPress={() => (navigation.navigate as any)('CoachGoals')}
            activeOpacity={0.85}
          >
            <Text style={styles.actionEmoji}>🎯</Text>
            <Text style={styles.actionTitle}>{t('coach.goals_btn', lang)}</Text>
          </TouchableOpacity>
          <TouchableOpacity
            style={[styles.actionCard, { borderColor: `${'#C07AE0'}40` }]}
            onPress={() => (navigation.navigate as any)('CoachBirth')}
            activeOpacity={0.85}
          >
            <Text style={styles.actionEmoji}>🌌</Text>
            <Text style={styles.actionTitle}>{t('coach.birth_btn', lang)}</Text>
          </TouchableOpacity>
        </View>
      </ScrollView>
    </View>
  );
};

const CARD_W = '47%';

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: colors.background },
  scroll: {
    paddingHorizontal: spacing.lg,
    paddingBottom:     spacing.xxxl,
  },

  // Header
  header: { flexDirection: 'row', alignItems: 'center', marginBottom: spacing.lg, gap: spacing.md },
  backBtn: {
    width: 40, height: 40, borderRadius: radius.full,
    backgroundColor: colors.surface,
    alignItems: 'center', justifyContent: 'center',
    ...shadow.sm,
  },
  backArrow: { ...typography.h2, color: colors.textPrimary, fontSize: 20 },
  headerBody:  { flex: 1 },
  headerTitle: { ...typography.h2 },
  headerSub:   { ...typography.caption, color: colors.textWarm, marginTop: 2 },

  // Analyze button
  analyzeBtn: {
    flexDirection:   'row',
    alignItems:      'center',
    backgroundColor: colors.surface,
    borderRadius:    radius.xl,
    borderWidth:     1,
    borderColor:     colors.goldDark,
    padding:         spacing.lg,
    marginBottom:    spacing.lg,
    overflow:        'hidden',
    ...shadow.gold,
  },
  analyzeBtnDisabled: { opacity: 0.7 },
  analyzeGlow: {
    ...StyleSheet.absoluteFillObject,
    backgroundColor: colors.goldGlow,
  },
  analyzeLoader: { marginRight: spacing.md },
  analyzeEmoji: { fontSize: 28, marginRight: spacing.md },
  analyzeBody:  { flex: 1 },
  analyzeTitle: { ...typography.h3 },
  archetypeRow: { ...typography.caption, color: colors.textWarm, marginTop: 2 },
  analyzeArrow: { ...typography.h2, color: colors.warmAmber, fontSize: 20 },

  // Disclaimer
  disclaimer: {
    backgroundColor: `${'#F5A623'}18`,
    borderRadius:    radius.md,
    borderWidth:     1,
    borderColor:     `${'#F5A623'}40`,
    padding:         spacing.md,
    marginBottom:    spacing.lg,
  },
  disclaimerText: { ...typography.caption, color: colors.textWarm, fontSize: 11 },

  // Section label
  sectionLabel: { ...typography.goldLabel, marginBottom: spacing.md, marginTop: spacing.xs ?? spacing.sm },

  // Module grid
  grid: {
    flexDirection: 'row', flexWrap: 'wrap',
    gap: spacing.sm, marginBottom: spacing.lg,
  },
  moduleCard: {
    width:           CARD_W,
    backgroundColor: colors.surface,
    borderRadius:    radius.lg,
    borderWidth:     1,
    padding:         spacing.md,
    alignItems:      'center',
    minHeight:       100,
    ...shadow.sm,
  },
  moduleIcon: {
    width: 44, height: 44, borderRadius: radius.md,
    alignItems: 'center', justifyContent: 'center',
    marginBottom: spacing.sm,
  },
  moduleEmoji: { fontSize: 22 },
  moduleTitle: { ...typography.label, fontSize: 11, textAlign: 'center' },
  moduleDot: {
    width: 8, height: 8, borderRadius: 4,
    backgroundColor: colors.gold,
    marginTop: spacing.sm,
  },
  moduleDotEmpty: { backgroundColor: colors.border },

  // Result cards
  resultCard: {
    backgroundColor: colors.surface,
    borderRadius:    radius.lg,
    borderWidth:     1,
    borderColor:     colors.border,
    borderLeftWidth: 3,
    padding:         spacing.md,
    marginBottom:    spacing.md,
  },
  resultCardTitle: { ...typography.h3, marginBottom: spacing.sm },
  resultCardText:  { ...typography.body, color: colors.textWarm, fontSize: 13, lineHeight: 20 },

  // Action row
  actionRow: { flexDirection: 'row', gap: spacing.sm, marginBottom: spacing.lg },
  actionCard: {
    flex:            1,
    backgroundColor: colors.surface,
    borderRadius:    radius.lg,
    borderWidth:     1,
    padding:         spacing.md,
    alignItems:      'center',
    ...shadow.sm,
  },
  actionEmoji: { fontSize: 26, marginBottom: spacing.sm },
  actionTitle: { ...typography.label, textAlign: 'center' },
});

export default CoachHubScreen;

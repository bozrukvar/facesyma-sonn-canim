// src/screens/SimilarityScreen.tsx
import React, { useState, useEffect, useCallback } from 'react';
import {
  View, Text, StyleSheet, ScrollView,
  TouchableOpacity, ActivityIndicator, Alert,
} from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import theme from '../utils/theme';
const { colors, spacing, typography, radius } = theme;
import { useLanguage } from '../utils/LanguageContext';
import { t } from '../utils/i18n';
import { AnalysisAPI } from '../services/api';
import type { ScreenProps } from '../navigation/types';

type ArchetypeEntry = {
  id:              string;
  name:            string;
  emoji:           string;
  reason:          string;
  primary_cluster: string;
  score:           number;
} | null;

type SimilarityResult = {
  celebrity:         ArchetypeEntry;
  animal:            ArchetypeEntry;
  plant:             ArchetypeEntry;
  object:            ArchetypeEntry;
  blend:             string;
  primary_cluster:   string;
  secondary_cluster: string;
};

// cluster → accent colour
const CLUSTER_COLORS: Record<string, string> = {
  leadership:   '#E53935',
  social:       '#8E24AA',
  patience:     '#00897B',
  intelligence: '#1E88E5',
  creativity:   '#F4511E',
  strength:     '#D81B60',
  empathy:      '#43A047',
  mystery:      '#5E35B1',
  discipline:   '#6D4C41',
  charisma:     '#FFB300',
};

const SimilarityScreen: React.FC<ScreenProps<'Similarity'>> = ({ navigation, route }) => {
  const { sifatlar, lang: routeLang } = route.params;
  const insets   = useSafeAreaInsets();
  const { lang } = useLanguage();
  const activeLang = routeLang || lang;

  const [loading,  setLoading]  = useState(true);
  const [result,   setResult]   = useState<SimilarityResult | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const data = await AnalysisAPI.getSimilarities(sifatlar, activeLang);
      setResult(data);
    } catch {
      Alert.alert(t('common.error', activeLang), t('common.generic_error', activeLang));
    } finally {
      setLoading(false);
    }
  }, [sifatlar, activeLang]);

  useEffect(() => { load(); }, [load]);

  const renderCard = (
    entry: ArchetypeEntry,
    categoryKey: 'similarity.celebrity' | 'similarity.animal' | 'similarity.plant' | 'similarity.object',
  ) => {
    if (!entry) return null;
    const accent = CLUSTER_COLORS[entry.primary_cluster] ?? colors.gold;
    const clusterLabel = t(`cluster.${entry.primary_cluster}` as any, activeLang);

    return (
      <View style={[styles.card, { borderColor: accent + '55' }]}>
        <View style={[styles.cardBadgeRow]}>
          <Text style={[styles.cardCategory, { color: accent }]}>
            {t(categoryKey, activeLang)}
          </Text>
          <View style={[styles.clusterBadge, { backgroundColor: accent + '22', borderColor: accent }]}>
            <Text style={[styles.clusterBadgeTxt, { color: accent }]}>{clusterLabel}</Text>
          </View>
        </View>

        <View style={styles.cardMain}>
          <Text style={styles.cardEmoji}>{entry.emoji}</Text>
          <View style={styles.cardTextCol}>
            <Text style={styles.cardName}>{entry.name}</Text>
            <Text style={styles.cardReason}>{entry.reason}</Text>
          </View>
        </View>

        <View style={styles.scoreRow}>
          <View style={styles.scoreTrack}>
            <View style={[styles.scoreBarFill, { flex: entry.score, backgroundColor: accent }]} />
            <View style={{ flex: Math.max(1 - entry.score, 0) }} />
          </View>
          <Text style={[styles.scoreLabel, { color: accent }]}>{Math.round(entry.score * 100)}%</Text>
        </View>
      </View>
    );
  };

  return (
    <View style={[styles.container, { paddingTop: insets.top }]}>
      {/* Header */}
      <View style={styles.header}>
        <TouchableOpacity onPress={() => navigation.goBack()} style={styles.backBtn}
          accessibilityRole="button"
          accessibilityLabel={t('similarity.title', lang)}
        >
          <Text style={styles.backTxt}>←</Text>
        </TouchableOpacity>
        <Text style={styles.title}>{t('similarity.title', activeLang)}</Text>
        <View style={{ width: 36 }} />
      </View>

      {loading ? (
        <View style={styles.center}>
          <ActivityIndicator color={colors.gold} size="large" />
          <Text style={styles.loadingTxt}>{t('common.loading', activeLang)}</Text>
        </View>
      ) : result ? (
        <ScrollView contentContainerStyle={styles.scroll} showsVerticalScrollIndicator={false}>
          {renderCard(result.celebrity, 'similarity.celebrity')}
          {renderCard(result.animal,    'similarity.animal')}
          {renderCard(result.plant,     'similarity.plant')}
          {renderCard(result.object,    'similarity.object')}

          {/* Blend */}
          {result.blend ? (
            <View style={styles.blendBox}>
              <Text style={styles.blendLabel}>{t('similarity.blend', activeLang)}</Text>
              <Text style={styles.blendTxt}>{result.blend}</Text>
            </View>
          ) : null}

          {/* Refresh */}
          <TouchableOpacity style={styles.refreshBtn} onPress={load}
            accessibilityRole="button"
            accessibilityLabel={t('similarity.refresh', lang)}
          >
            <Text style={styles.refreshTxt}>🔄 {t('similarity.refresh', activeLang)}</Text>
          </TouchableOpacity>

          <View style={{ height: spacing.xl }} />
        </ScrollView>
      ) : null}
    </View>
  );
};

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: colors.background },
  header: {
    flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between',
    paddingHorizontal: spacing.lg, paddingVertical: spacing.md,
    borderBottomWidth: 1, borderColor: colors.border,
  },
  backBtn: { width: 36, height: 36, justifyContent: 'center' },
  backTxt: { ...typography.h2, color: colors.gold },
  title:   { ...typography.h2, color: colors.textPrimary, flex: 1, textAlign: 'center' as const },
  center:  { flex: 1, alignItems: 'center', justifyContent: 'center', gap: spacing.md },
  loadingTxt: { ...typography.caption, color: colors.textMuted },
  scroll: { padding: spacing.lg, gap: spacing.md },

  // card
  card: {
    backgroundColor: colors.surface, borderRadius: radius.lg,
    borderWidth: 1, padding: spacing.md, gap: spacing.sm,
  },
  cardBadgeRow: {
    flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between',
  },
  cardCategory: { ...typography.caption, fontSize: 11, fontWeight: '700' as const, letterSpacing: 0.5, textTransform: 'uppercase' as const },
  clusterBadge: {
    borderWidth: 1, borderRadius: radius.full,
    paddingHorizontal: spacing.sm, paddingVertical: 2,
  },
  clusterBadgeTxt: { ...typography.caption, fontSize: 10, fontWeight: '700' as const },
  cardMain: { flexDirection: 'row', alignItems: 'center', gap: spacing.md },
  cardEmoji:   { fontSize: 44 },
  cardTextCol: { flex: 1, gap: spacing.xs },
  cardName:    { ...typography.h3, color: colors.textPrimary, fontWeight: '700' as const },
  cardReason:  { ...typography.caption, color: colors.textSecondary, lineHeight: 17 },

  // score bar
  scoreRow: {
    flexDirection: 'row', alignItems: 'center', gap: spacing.sm,
  },
  scoreTrack: {
    flex: 1, flexDirection: 'row', height: 4, borderRadius: 2,
    backgroundColor: colors.background, overflow: 'hidden',
  },
  scoreBarFill: { height: 4, borderRadius: 2 },
  scoreLabel: { ...typography.caption, fontSize: 10, fontWeight: '700' as const },

  // blend
  blendBox: {
    backgroundColor: colors.surface, borderRadius: radius.md,
    borderWidth: 1, borderColor: colors.gold + '44',
    padding: spacing.md, gap: spacing.xs,
  },
  blendLabel: { ...typography.caption, color: colors.gold, fontSize: 11, fontWeight: '700' as const, letterSpacing: 0.5, textTransform: 'uppercase' as const },
  blendTxt:   { ...typography.body, color: colors.textPrimary, fontStyle: 'italic' as const, lineHeight: 22 },

  // refresh
  refreshBtn: {
    alignSelf: 'center' as const, marginTop: spacing.sm,
    backgroundColor: colors.surface, borderRadius: radius.full,
    borderWidth: 1, borderColor: colors.border,
    paddingHorizontal: spacing.xl, paddingVertical: spacing.sm,
  },
  refreshTxt: { ...typography.label, color: colors.textSecondary },
});

export default SimilarityScreen;

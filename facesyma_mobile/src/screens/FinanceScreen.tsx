// src/screens/FinanceScreen.tsx
import React, { useEffect, useState, useCallback } from 'react';
import {
  View, Text, StyleSheet, ScrollView, TouchableOpacity,
  ActivityIndicator, StatusBar,
} from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { AssessmentAPI } from '../services/api';
import theme from '../utils/theme';
import { useLanguage } from '../utils/LanguageContext';
import { t } from '../utils/i18n';
import type { ScreenProps } from '../navigation/types';

const { colors, spacing, typography, radius, shadow } = theme;
type Props = ScreenProps<'Finance'>;

interface DomainScore { score: number; label: string; emoji: string }
interface FinanceProfile {
  type: 'saver' | 'risk_taker' | 'balanced' | 'impulsive';
  emoji: string;
  color: string;
  domains: DomainScore[];
  advice: { budget: string; saving: string; investment: string };
}

const DOMAIN_META: Record<string, { emoji: string; labelKey: string }> = {
  savings_behavior:    { emoji: '🏦', labelKey: 'finance.domain_savings' },
  risk_tolerance:      { emoji: '📈', labelKey: 'finance.domain_risk' },
  financial_discipline:{ emoji: '📋', labelKey: 'finance.domain_discipline' },
  impulsivity:         { emoji: '🛒', labelKey: 'finance.domain_impulsivity' },
  goal_planning:       { emoji: '🎯', labelKey: 'finance.domain_goals' },
};

function buildProfile(scores: Record<string, number>, lang: string): FinanceProfile {
  const sav  = scores.savings_behavior    ?? 50;
  const risk = scores.risk_tolerance      ?? 50;
  const disc = scores.financial_discipline ?? 50;
  const imp  = scores.impulsivity         ?? 50;
  const goals= scores.goal_planning       ?? 50;

  const domains: DomainScore[] = Object.entries(DOMAIN_META).map(([key, meta]) => ({
    score: scores[key] ?? 0,
    label: t(meta.labelKey, lang),
    emoji: meta.emoji,
  }));

  // Priority: impulsive > saver > risk_taker > balanced
  const isImpulsive = imp > 60 || disc < 38;
  const isSaver     = sav > 65 && disc > 60 && imp < 42;
  const isRiskTaker = risk > 65 && goals > 60;

  if (isImpulsive) {
    return {
      type: 'impulsive', emoji: '🛍️', color: '#E07A7A',
      domains,
      advice: {
        budget: t('finance.advice_budget_impulsive', lang),
        saving: t('finance.advice_saving_impulsive', lang),
        investment: t('finance.advice_invest_impulsive', lang),
      },
    };
  }
  if (isSaver) {
    return {
      type: 'saver', emoji: '🏦', color: '#7AE07A',
      domains,
      advice: {
        budget: t('finance.advice_budget_saver', lang),
        saving: t('finance.advice_saving_saver', lang),
        investment: t('finance.advice_invest_saver', lang),
      },
    };
  }
  if (isRiskTaker) {
    return {
      type: 'risk_taker', emoji: '📈', color: '#F5C842',
      domains,
      advice: {
        budget: t('finance.advice_budget_risk', lang),
        saving: t('finance.advice_saving_risk', lang),
        investment: t('finance.advice_invest_risk', lang),
      },
    };
  }
  return {
    type: 'balanced', emoji: '⚖️', color: '#7AB8E0',
    domains,
    advice: {
      budget: t('finance.advice_budget_balanced', lang),
      saving: t('finance.advice_saving_balanced', lang),
      investment: t('finance.advice_invest_balanced', lang),
    },
  };
}

const FinanceScreen: React.FC<Props> = ({ navigation }) => {
  const insets = useSafeAreaInsets();
  const { lang } = useLanguage();
  const [loading, setLoading] = useState(true);
  const [profile, setProfile] = useState<FinanceProfile | null>(null);
  const [narrative, setNarrative] = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const [allScores, history] = await Promise.all([
        AssessmentAPI.getLatestScores(),
        AssessmentAPI.getHistory(20),
      ]);

      const finScores = allScores.finance;
      if (finScores && Object.keys(finScores).length > 0) {
        setProfile(buildProfile(finScores, lang));
        const finResult = (history?.data?.results ?? []).find(
          (r: any) => r.test_type === 'finance'
        );
        if (finResult?.narrative) {
          setNarrative(finResult.narrative);
        }
      } else {
        setProfile(null);
      }
    } catch {
      setProfile(null);
    } finally {
      setLoading(false);
    }
  }, [lang]);

  useEffect(() => { load(); }, [load]);

  const goToAssessment = () => navigation.navigate('Assessment');

  const profileTypeLabel = (type: string) => {
    const map: Record<string, string> = {
      saver:      t('finance.profile_saver', lang),
      risk_taker: t('finance.profile_risk_taker', lang),
      balanced:   t('finance.profile_balanced', lang),
      impulsive:  t('finance.profile_impulsive', lang),
    };
    return map[type] ?? type;
  };

  return (
    <View style={styles.container}>
      <StatusBar barStyle="light-content" />
      {/* Header */}
      <View style={[styles.header, { paddingTop: insets.top + spacing.md }]}>
        <TouchableOpacity onPress={() => navigation.goBack()} style={styles.backBtn}
          accessibilityRole="button"
          accessibilityLabel={t('finance.title', lang)}
        >
          <Text style={styles.backArrow}>←</Text>
        </TouchableOpacity>
        <View style={styles.headerText}>
          <Text style={styles.headerTitle}>{t('finance.title', lang)}</Text>
          <Text style={styles.headerSub}>{t('finance.subtitle', lang)}</Text>
        </View>
        <Text style={styles.headerEmoji}>💰</Text>
      </View>

      {loading ? (
        <View style={styles.center}>
          <ActivityIndicator size="large" color={colors.gold} />
        </View>
      ) : profile === null ? (
        /* ── No assessment yet ── */
        <ScrollView contentContainerStyle={styles.scroll}>
          <View style={styles.emptyCard}>
            <Text style={styles.emptyEmoji}>📊</Text>
            <Text style={styles.emptyTitle}>{t('finance.no_result', lang)}</Text>
            <Text style={styles.emptyDesc}>{t('finance.take_test_desc', lang)}</Text>
            <TouchableOpacity style={styles.ctaBtn} onPress={goToAssessment}
              accessibilityRole="button"
              accessibilityLabel={t('finance.take_test', lang)}
            >
              <Text style={styles.ctaBtnText}>{t('finance.take_test', lang)}</Text>
            </TouchableOpacity>
          </View>
          <AdvicePreviewCards lang={lang} />
        </ScrollView>
      ) : (
        /* ── Profile result ── */
        <ScrollView contentContainerStyle={styles.scroll}>
          {/* Profile badge */}
          <View style={[styles.profileCard, { borderColor: `${profile.color}50` }]}>
            <Text style={styles.profileEmoji}>{profile.emoji}</Text>
            <Text style={[styles.profileType, { color: profile.color }]}>
              {profileTypeLabel(profile.type)}
            </Text>
            <Text style={styles.profileLabel}>{t('finance.profile_label', lang)}</Text>
          </View>

          {/* Domain breakdown */}
          <Text style={styles.sectionTitle}>{t('finance.section_profile', lang)}</Text>
          <View style={styles.domainsCard}>
            {profile.domains.map(d => (
              <DomainRow key={d.label} domain={d} accentColor={profile.color} lang={lang} />
            ))}
          </View>

          {/* AI Narrative */}
          {narrative && (
            <>
              <Text style={styles.sectionTitle}>{t('finance.section_narrative', lang)}</Text>
              <View style={styles.narrativeCard}>
                <Text style={styles.narrativeText}>{narrative}</Text>
              </View>
            </>
          )}

          {/* Advice cards */}
          <Text style={styles.sectionTitle}>{t('finance.section_advice', lang)}</Text>
          <AdviceCard emoji="📋" title={t('finance.advice_budget_title', lang)} text={profile.advice.budget} color="#7AB8E0" />
          <AdviceCard emoji="🏦" title={t('finance.advice_saving_title', lang)} text={profile.advice.saving} color="#7AE07A" />
          <AdviceCard emoji="📈" title={t('finance.advice_invest_title', lang)} text={profile.advice.investment} color={profile.color} />

          {/* Retake */}
          <TouchableOpacity style={styles.retakeBtn} onPress={goToAssessment}
            accessibilityRole="button"
            accessibilityLabel={t('finance.retake_test', lang)}
          >
            <Text style={styles.retakeBtnText}>{t('finance.retake_test', lang)}</Text>
          </TouchableOpacity>

          {/* Legal disclaimer */}
          <DisclaimerBox lang={lang} />
        </ScrollView>
      )}
    </View>
  );
};

const DomainRow: React.FC<{ domain: DomainScore; accentColor: string; lang: string }> = ({ domain, accentColor }) => (
  <View style={styles.domainRow}>
    <Text style={styles.domainEmoji}>{domain.emoji}</Text>
    <View style={styles.domainBody}>
      <View style={styles.domainLabelRow}>
        <Text style={styles.domainLabel}>{domain.label}</Text>
        <Text style={[styles.domainScore, { color: accentColor }]}>{domain.score}%</Text>
      </View>
      <View style={styles.progressBg}>
        <View style={[styles.progressFill, { width: `${domain.score}%` as any, backgroundColor: accentColor }]} />
      </View>
    </View>
  </View>
);

const AdviceCard: React.FC<{ emoji: string; title: string; text: string; color: string }> = ({ emoji, title, text, color }) => (
  <View style={[styles.adviceCard, { borderLeftColor: color }]}>
    <Text style={styles.adviceEmoji}>{emoji}</Text>
    <View style={styles.adviceBody}>
      <Text style={[styles.adviceTitle, { color }]}>{title}</Text>
      <Text style={styles.adviceText}>{text}</Text>
    </View>
  </View>
);

const AdvicePreviewCards: React.FC<{ lang: string }> = ({ lang }) => (
  <>
    <Text style={styles.sectionTitle}>{t('finance.section_advice', lang)}</Text>
    <AdviceCard emoji="📋" title={t('finance.advice_budget_title', lang)} text={t('finance.preview_budget', lang)} color="#7AB8E0" />
    <AdviceCard emoji="🏦" title={t('finance.advice_saving_title', lang)} text={t('finance.preview_saving', lang)} color="#7AE07A" />
    <AdviceCard emoji="📈" title={t('finance.advice_invest_title', lang)} text={t('finance.preview_invest', lang)} color="#F5C842" />
    <DisclaimerBox lang={lang} />
  </>
);

const DisclaimerBox: React.FC<{ lang: string }> = ({ lang }) => (
  <View style={styles.disclaimerBox}>
    <Text style={styles.disclaimerIcon}>⚠️</Text>
    <Text style={styles.disclaimerText}>{t('finance.disclaimer', lang)}</Text>
  </View>
);

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: colors.background },
  header: {
    flexDirection: 'row', alignItems: 'center',
    paddingHorizontal: spacing.lg, paddingBottom: spacing.md,
  },
  backBtn: { marginRight: spacing.sm, padding: 4 },
  backArrow: { fontSize: 22, color: colors.textPrimary },
  headerText: { flex: 1 },
  headerTitle: { ...typography.h2 },
  headerSub: { ...typography.caption, color: colors.textMuted, marginTop: 2 },
  headerEmoji: { fontSize: 28 },
  center: { flex: 1, alignItems: 'center', justifyContent: 'center' },
  scroll: { paddingHorizontal: spacing.lg, paddingBottom: 40 },

  // Empty state
  emptyCard: {
    backgroundColor: colors.surface, borderRadius: radius.xl ?? 20,
    padding: spacing.xl ?? 32, alignItems: 'center', marginVertical: spacing.lg,
    ...shadow.sm,
  },
  emptyEmoji: { fontSize: 56, marginBottom: spacing.md },
  emptyTitle: { ...typography.h3 ?? typography.h2, textAlign: 'center' as any, marginBottom: spacing.sm },
  emptyDesc: { ...typography.caption, color: colors.textMuted, textAlign: 'center' as any, marginBottom: spacing.lg, lineHeight: 20 },
  ctaBtn: {
    backgroundColor: colors.gold, borderRadius: radius.md ?? 12,
    paddingHorizontal: spacing.xl ?? 32, paddingVertical: spacing.md,
  },
  ctaBtnText: { color: colors.background, fontWeight: '700', fontSize: 15 },

  // Profile card
  profileCard: {
    backgroundColor: colors.surface, borderRadius: radius.xl ?? 20,
    padding: spacing.lg, alignItems: 'center', marginVertical: spacing.md,
    ...shadow.sm, borderWidth: 1,
  },
  profileEmoji: { fontSize: 52, marginBottom: spacing.sm },
  profileType: { fontSize: 22, fontWeight: '800', marginBottom: 4 },
  profileLabel: { ...typography.caption, color: colors.textMuted },

  // Section title
  sectionTitle: {
    ...typography.label ?? typography.body,
    color: colors.textMuted, fontSize: 11, fontWeight: '700',
    textTransform: 'uppercase' as any, letterSpacing: 1,
    marginBottom: spacing.sm, marginTop: spacing.md,
  },

  // Domains
  domainsCard: {
    backgroundColor: colors.surface, borderRadius: radius.lg ?? 16,
    padding: spacing.md, ...shadow.sm,
  },
  domainRow: {
    flexDirection: 'row', alignItems: 'center',
    paddingVertical: spacing.sm, borderBottomWidth: 1,
    borderBottomColor: `${colors.border}30`,
  },
  domainEmoji: { fontSize: 20, width: 32 },
  domainBody: { flex: 1 },
  domainLabelRow: { flexDirection: 'row', justifyContent: 'space-between', marginBottom: 4 },
  domainLabel: { ...typography.caption, color: colors.textPrimary, fontWeight: '600' },
  domainScore: { ...typography.caption, fontWeight: '700' },
  progressBg: { height: 5, backgroundColor: `${colors.border}40`, borderRadius: 3 },
  progressFill: { height: 5, borderRadius: 3 },

  // Narrative
  narrativeCard: {
    backgroundColor: colors.surface, borderRadius: radius.lg ?? 16,
    padding: spacing.md, ...shadow.sm,
  },
  narrativeText: { ...typography.body, color: colors.textPrimary, lineHeight: 22, fontSize: 14 },

  // Advice cards
  adviceCard: {
    flexDirection: 'row', backgroundColor: colors.surface,
    borderRadius: radius.md ?? 12, padding: spacing.md,
    marginBottom: spacing.sm, ...shadow.sm,
    borderLeftWidth: 4,
  },
  adviceEmoji: { fontSize: 24, marginRight: spacing.md },
  adviceBody: { flex: 1 },
  adviceTitle: { fontWeight: '700', fontSize: 13, marginBottom: 4 },
  adviceText: { ...typography.caption, color: colors.textMuted, lineHeight: 18 },

  // Retake
  retakeBtn: {
    borderWidth: 1, borderColor: colors.border, borderRadius: radius.md ?? 12,
    padding: spacing.md, alignItems: 'center', marginTop: spacing.md,
  },
  retakeBtnText: { color: colors.textMuted, fontWeight: '600' },

  // Disclaimer
  disclaimerBox: {
    flexDirection: 'row', alignItems: 'flex-start',
    backgroundColor: `${colors.surface}CC`,
    borderRadius: radius.md ?? 12,
    borderWidth: 1, borderColor: `${colors.border}60`,
    padding: spacing.md, marginTop: spacing.lg, marginBottom: spacing.sm,
    gap: 8,
  },
  disclaimerIcon: { fontSize: 14, marginTop: 1 },
  disclaimerText: {
    flex: 1, fontSize: 11, color: colors.textMuted,
    lineHeight: 16, fontStyle: 'italic' as const,
  },
});

export default FinanceScreen;

// src/screens/CompatibilityReportScreen.tsx
import React, { useEffect, useState } from 'react';
import {
  View, Text, StyleSheet, ScrollView, TouchableOpacity,
  ActivityIndicator, Share,
} from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { useLanguage } from '../utils/LanguageContext';
import { PartnerAPI, CompatibilityReport } from '../services/api';
import theme from '../utils/theme';
const { colors, spacing, typography, radius } = theme;

const TR: Record<string, Record<string, string>> = {
  tr: {
    title:            'Uyumluluk Raporu',
    loading:          'Rapor yükleniyor...',
    error:            'Rapor yüklenemedi.',
    retry:            'Tekrar Dene',
    back:             '←',
    overall_score:    'Genel Uyumluluk',
    personality:      'Kişilik Uyumu',
    attachment:       'Bağlanma Uyumu',
    relationship:     'İlişki Dinamikleri',
    pers_breakdown:   'Kişilik Alt Boyutları',
    rel_breakdown:    'İlişki Alt Boyutları',
    openness:         'Açıklık',
    conscientiousness:'Sorumluluk',
    extraversion:     'Dışadönüklük',
    agreeableness:    'Uyumluluk',
    neuroticism:      'Duygusal Denge',
    love_language:    'Sevgi Dili',
    conflict_style:   'Çatışma Tarzı',
    intimacy_needs:   'Yakınlık İhtiyacı',
    relationship_values: 'İlişki Değerleri',
    attachment_styles: 'Bağlanma Stilleri',
    secure:           'Güvenli',
    anxious:          'Kaygılı',
    avoidant:         'Kaçınan',
    disorganized:     'Düzensiz',
    strengths:        'Güçlü Yönler',
    watchouts:        'Dikkat Edilecekler',
    narrative:        'Değerlendirme',
    share_btn:        '↑ Paylaş',
    share_text:       'FaceSyma Uyumluluk Raporum: %{score}/100',
    incomplete_data:  'Bazı testler tamamlanmamış — uyumluluk tahmini sınırlı.',
    you:              'Sen',
    partner:          'Partner',
  },
  en: {
    title:            'Compatibility Report',
    loading:          'Loading report...',
    error:            'Could not load report.',
    retry:            'Retry',
    back:             '←',
    overall_score:    'Overall Compatibility',
    personality:      'Personality Match',
    attachment:       'Attachment Match',
    relationship:     'Relationship Dynamics',
    pers_breakdown:   'Personality Subdomains',
    rel_breakdown:    'Relationship Subdomains',
    openness:         'Openness',
    conscientiousness:'Conscientiousness',
    extraversion:     'Extraversion',
    agreeableness:    'Agreeableness',
    neuroticism:      'Emotional Stability',
    love_language:    'Love Language',
    conflict_style:   'Conflict Style',
    intimacy_needs:   'Intimacy Needs',
    relationship_values: 'Relationship Values',
    attachment_styles: 'Attachment Styles',
    secure:           'Secure',
    anxious:          'Anxious',
    avoidant:         'Avoidant',
    disorganized:     'Disorganized',
    strengths:        'Strengths',
    watchouts:        'Watch Outs',
    narrative:        'Assessment',
    share_btn:        '↑ Share',
    share_text:       'FaceSyma Compatibility Report: %{score}/100',
    incomplete_data:  'Some tests not completed — compatibility estimate is limited.',
    you:              'You',
    partner:          'Partner',
  },
};

const L = (lang: string, key: string, vars?: Record<string, string | number>) => {
  let s = (TR[lang] || TR['en'])[key] ?? (TR['en'][key] ?? key);
  if (vars) {
    Object.entries(vars).forEach(([k, v]) => { s = s.replace(`%{${k}}`, String(v)); });
  }
  return s;
};

const SCORE_COLOR = (score: number) =>
  score >= 75 ? '#4CAF50' : score >= 55 ? colors.gold : '#E07A7A';

// Large ring showing overall score
const OverallRing: React.FC<{ score: number }> = ({ score }) => {
  const c = SCORE_COLOR(score);
  return (
    <View style={[ringS.outer, { borderColor: c }]}>
      <Text style={[ringS.score, { color: c }]}>{score}</Text>
      <Text style={ringS.label}>/ 100</Text>
    </View>
  );
};
const ringS = StyleSheet.create({
  outer: { width: 110, height: 110, borderRadius: 55, borderWidth: 7, alignItems: 'center', justifyContent: 'center', backgroundColor: colors.surface },
  score: { fontSize: 36, fontWeight: '800', fontFamily: 'System' },
  label: { fontSize: 12, color: colors.textMuted, fontFamily: 'System' },
});

// Horizontal bar for a domain score
const DomainBar: React.FC<{ label: string; score: number }> = ({ label, score }) => {
  const c = SCORE_COLOR(score);
  return (
    <View style={barS.row}>
      <Text style={barS.label} numberOfLines={1}>{label}</Text>
      <View style={barS.track}>
        <View style={[barS.fill, { width: `${score}%` as any, backgroundColor: c }]} />
      </View>
      <Text style={[barS.value, { color: c }]}>{score}</Text>
    </View>
  );
};
const barS = StyleSheet.create({
  row:   { flexDirection: 'row', alignItems: 'center', marginBottom: 10 },
  label: { width: 130, ...typography.caption, fontSize: 12, color: colors.textWarm },
  track: { flex: 1, height: 7, borderRadius: 4, backgroundColor: colors.border, overflow: 'hidden', marginHorizontal: 8 },
  fill:  { height: 7, borderRadius: 4 },
  value: { width: 28, textAlign: 'right', fontSize: 12, fontWeight: '700', fontFamily: 'System' },
});

// Chip list for strengths/watchouts
const ChipList: React.FC<{ items: string[]; color: string }> = ({ items, color }) => (
  <View style={chipS.wrap}>
    {items.map((item, i) => (
      <View key={i} style={[chipS.chip, { borderColor: `${color}40`, backgroundColor: `${color}12` }]}>
        <Text style={[chipS.text, { color }]}>{item}</Text>
      </View>
    ))}
  </View>
);
const chipS = StyleSheet.create({
  wrap: { flexDirection: 'row', flexWrap: 'wrap', gap: 6 },
  chip: { borderWidth: 1, borderRadius: radius.full, paddingHorizontal: 10, paddingVertical: 4 },
  text: { fontSize: 12, fontWeight: '600', fontFamily: 'System' },
});

const ATTACHMENT_EMOJI: Record<string, string> = {
  secure: '🟢', anxious: '🟡', avoidant: '🔵', disorganized: '🔴',
};

const CompatibilityReportScreen: React.FC<{ navigation: any }> = ({ navigation }) => {
  const insets = useSafeAreaInsets();
  const { lang } = useLanguage();

  const [report, setReport]       = useState<CompatibilityReport | null>(null);
  const [partnerName, setPartnerName] = useState<string>('');
  const [loading, setLoading]     = useState(true);
  const [error, setError]         = useState(false);

  const load = async () => {
    setLoading(true);
    setError(false);
    try {
      const res = await PartnerAPI.getCompatibility(lang);
      setReport(res.report);
      setPartnerName(res.partner_name || '');
    } catch {
      setError(true);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { load(); }, []);

  const handleShare = async () => {
    if (!report) return;
    const msg = L(lang, 'share_text', { score: report.overall_score });
    await Share.share({ message: msg });
  };

  if (loading) {
    return (
      <View style={[styles.container, styles.center, { paddingTop: insets.top }]}>
        <ActivityIndicator color={colors.warmAmber} size="large" />
        <Text style={styles.loadingText}>{L(lang, 'loading')}</Text>
      </View>
    );
  }

  if (error || !report) {
    return (
      <View style={[styles.container, styles.center, { paddingTop: insets.top }]}>
        <Text style={styles.errorText}>{L(lang, 'error')}</Text>
        <TouchableOpacity onPress={load} style={styles.retryBtn}>
          <Text style={styles.retryText}>{L(lang, 'retry')}</Text>
        </TouchableOpacity>
      </View>
    );
  }

  const hasAllData = report.data_quality?.has_personality &&
    report.data_quality?.has_attachment && report.data_quality?.has_relationship;

  const PERS_DOMAINS = ['openness', 'conscientiousness', 'extraversion', 'agreeableness', 'neuroticism'];
  const REL_DOMAINS  = ['love_language', 'conflict_style', 'intimacy_needs', 'relationship_values'];

  return (
    <View style={[styles.container, { paddingTop: insets.top }]}>
      {/* Header */}
      <View style={styles.header}>
        <TouchableOpacity onPress={() => navigation.goBack()} style={styles.backBtn}>
          <Text style={styles.backText}>{L(lang, 'back')}</Text>
        </TouchableOpacity>
        <Text style={styles.title}>{L(lang, 'title')}</Text>
        <TouchableOpacity onPress={handleShare} style={styles.shareBtn}>
          <Text style={styles.shareBtnText}>{L(lang, 'share_btn')}</Text>
        </TouchableOpacity>
      </View>

      <ScrollView contentContainerStyle={styles.scroll} showsVerticalScrollIndicator={false}>
        {/* Overall score */}
        <View style={styles.overallSection}>
          <OverallRing score={report.overall_score} />
          <Text style={styles.overallLabel}>{L(lang, 'overall_score')}</Text>
          {partnerName ? <Text style={styles.partnerLine}>💑 {partnerName}</Text> : null}
        </View>

        {!hasAllData && (
          <View style={styles.warningCard}>
            <Text style={styles.warningText}>{L(lang, 'incomplete_data')}</Text>
          </View>
        )}

        {/* Domain scores */}
        <View style={styles.card}>
          <DomainBar label={L(lang, 'personality')}  score={report.domain_scores.personality} />
          <DomainBar label={L(lang, 'attachment')}   score={report.domain_scores.attachment} />
          <DomainBar label={L(lang, 'relationship')} score={report.domain_scores.relationship} />
        </View>

        {/* Personality breakdown */}
        {Object.keys(report.personality_breakdown).length > 0 && (
          <View style={styles.card}>
            <Text style={styles.cardTitle}>{L(lang, 'pers_breakdown')}</Text>
            {PERS_DOMAINS.map(d => (
              <DomainBar key={d} label={L(lang, d)} score={report.personality_breakdown[d] ?? 0} />
            ))}
          </View>
        )}

        {/* Attachment styles */}
        <View style={styles.card}>
          <Text style={styles.cardTitle}>{L(lang, 'attachment_styles')}</Text>
          <View style={styles.attachRow}>
            <View style={styles.attachChip}>
              <Text style={styles.attachChipEmoji}>
                {ATTACHMENT_EMOJI[report.attachment_styles.user_a] || '⬜'}
              </Text>
              <Text style={styles.attachChipName}>{L(lang, 'you')}</Text>
              <Text style={styles.attachChipStyle}>{L(lang, report.attachment_styles.user_a)}</Text>
            </View>
            <Text style={styles.attachPlus}>💕</Text>
            <View style={styles.attachChip}>
              <Text style={styles.attachChipEmoji}>
                {ATTACHMENT_EMOJI[report.attachment_styles.user_b] || '⬜'}
              </Text>
              <Text style={styles.attachChipName}>{partnerName || L(lang, 'partner')}</Text>
              <Text style={styles.attachChipStyle}>{L(lang, report.attachment_styles.user_b)}</Text>
            </View>
          </View>
        </View>

        {/* Relationship breakdown */}
        {Object.keys(report.relationship_breakdown).length > 0 && (
          <View style={styles.card}>
            <Text style={styles.cardTitle}>{L(lang, 'rel_breakdown')}</Text>
            {REL_DOMAINS.map(d => (
              <DomainBar key={d} label={L(lang, d)} score={report.relationship_breakdown[d] ?? 0} />
            ))}
          </View>
        )}

        {/* Strengths */}
        {report.strengths.length > 0 && (
          <View style={styles.card}>
            <Text style={styles.cardTitle}>{L(lang, 'strengths')} ✨</Text>
            <ChipList items={report.strengths} color="#4CAF50" />
          </View>
        )}

        {/* Watchouts */}
        {report.watchouts.length > 0 && (
          <View style={styles.card}>
            <Text style={styles.cardTitle}>{L(lang, 'watchouts')} ⚠️</Text>
            <ChipList items={report.watchouts} color='#E07A7A' />
          </View>
        )}

        {/* Narrative */}
        {report.narrative ? (
          <View style={styles.narrativeCard}>
            <Text style={styles.narrativeTitle}>{L(lang, 'narrative')}</Text>
            <Text style={styles.narrativeText}>{report.narrative}</Text>
          </View>
        ) : null}

        {/* Share CTA */}
        <TouchableOpacity style={styles.shareCTA} onPress={handleShare} activeOpacity={0.85}>
          <Text style={styles.shareCTAText}>{L(lang, 'share_btn')}</Text>
        </TouchableOpacity>
      </ScrollView>
    </View>
  );
};

const styles = StyleSheet.create({
  container:    { flex: 1, backgroundColor: colors.background },
  scroll:       { paddingHorizontal: spacing.lg, paddingBottom: 60 },
  center:       { flex: 1, alignItems: 'center', justifyContent: 'center', gap: spacing.md },
  loadingText:  { ...typography.body, color: colors.textMuted },
  errorText:    { ...typography.body, color: colors.textMuted },

  retryBtn:  { paddingHorizontal: spacing.xl, paddingVertical: spacing.sm, borderWidth: 1, borderColor: colors.border, borderRadius: radius.full },
  retryText: { ...typography.body, color: colors.textPrimary },

  header: {
    flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between',
    paddingHorizontal: spacing.md, paddingTop: spacing.md, paddingBottom: spacing.sm,
    borderBottomWidth: 1, borderBottomColor: colors.border,
  },
  backBtn:      { width: 40 },
  backText:     { color: colors.gold, fontSize: 22 },
  title:        { ...typography.h2, fontSize: 17 },
  shareBtn:     { width: 60, alignItems: 'flex-end' },
  shareBtnText: { color: colors.gold, fontSize: 13, fontWeight: '600', fontFamily: 'System' },

  overallSection: { alignItems: 'center', paddingVertical: spacing.xl, gap: spacing.sm },
  overallLabel:   { ...typography.goldLabel, fontSize: 13 },
  partnerLine:    { ...typography.body, color: colors.textMuted, fontSize: 12 },

  warningCard: {
    backgroundColor: `${colors.gold}15`, borderRadius: radius.md,
    borderWidth: 1, borderColor: `${colors.gold}30`,
    padding: spacing.md, marginBottom: spacing.md,
  },
  warningText: { ...typography.caption, color: colors.gold, fontSize: 12, textAlign: 'center' },

  card: {
    backgroundColor: colors.surface, borderRadius: radius.lg,
    borderWidth: 1, borderColor: colors.border,
    padding: spacing.md, marginBottom: spacing.md,
  },
  cardTitle: { ...typography.goldLabel, fontSize: 12, marginBottom: spacing.md },

  attachRow:      { flexDirection: 'row', justifyContent: 'space-around', alignItems: 'center' },
  attachPlus:     { fontSize: 24 },
  attachChip:     { alignItems: 'center', gap: 4 },
  attachChipEmoji:{ fontSize: 24 },
  attachChipName: { ...typography.caption, fontSize: 10, color: colors.textMuted },
  attachChipStyle:{ ...typography.body, fontSize: 13, fontWeight: '700', color: colors.textPrimary },

  narrativeCard: {
    backgroundColor: colors.surface, borderRadius: radius.lg,
    borderWidth: 1, borderColor: `#E0607A25`,
    padding: spacing.md, marginBottom: spacing.md,
  },
  narrativeTitle: { ...typography.goldLabel, color: '#E0607A', marginBottom: spacing.sm },
  narrativeText:  { ...typography.body, fontSize: 13, lineHeight: 20, color: colors.textPrimary },

  shareCTA: {
    backgroundColor: '#E0607A', borderRadius: radius.xl,
    paddingVertical: spacing.md, alignItems: 'center', marginBottom: spacing.xl,
  },
  shareCTAText: { color: '#fff', fontWeight: '700', fontSize: 15, fontFamily: 'System' },
});

export default CompatibilityReportScreen;

// src/screens/CoachHubScreen.tsx
import React, { useState, useCallback, useRef } from 'react';
import {
  View, Text, StyleSheet, ScrollView, TouchableOpacity,
  ActivityIndicator, StatusBar, Alert, FlatList,
} from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { useSelector } from 'react-redux';
import { RootState } from '../store';
import { CoachAPI, AssessmentAPI } from '../services/api';
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
  // ── Mevcut 14 modül ───────────────────────────────────────────────────────
  { id: 'health',        emoji: '🏃', titleKey: 'coach.mod_health',         moduleKey: 'saglik_esenwlik',     accent: '#7AE07A' },
  { id: 'honesty',       emoji: '🤝', titleKey: 'coach.mod_honesty',        moduleKey: 'dogruluk_sadakat',    accent: '#7AE0C0' },
  { id: 'security',      emoji: '🛡️', titleKey: 'coach.mod_security',       moduleKey: 'guvenlik',            accent: '#7AAEE0' },
  { id: 'risk',          emoji: '⚖️', titleKey: 'coach.mod_risk',           moduleKey: 'suc_egilim',          accent: '#E0B07A' },
  { id: 'relationship',  emoji: '💞', titleKey: 'coach.mod_relationship',   moduleKey: 'iliski_yonetimi',     accent: '#E07A7A' },
  { id: 'communication', emoji: '🗣️', titleKey: 'coach.mod_communication',  moduleKey: 'iletisim_becerileri', accent: '#7AB0E0' },
  { id: 'stress',        emoji: '🧘', titleKey: 'coach.mod_stress',         moduleKey: 'stres_yonetimi',      accent: '#9B7AE0' },
  { id: 'confidence',    emoji: '✨', titleKey: 'coach.mod_confidence',     moduleKey: 'ozguven',             accent: '#F5C842' },
  { id: 'time',          emoji: '⏰', titleKey: 'coach.mod_time',           moduleKey: 'zaman_yonetimi',      accent: '#E07AB0' },
  { id: 'goals',         emoji: '🎯', titleKey: 'coach.mod_personal_goals', moduleKey: 'kisisel_hedefler',    accent: '#7AE0B0' },
  { id: 'astrology',     emoji: '⭐', titleKey: 'coach.mod_astrology',      moduleKey: 'astroloji_harita',    accent: '#C07AE0' },
  { id: 'birth',         emoji: '🌙', titleKey: 'coach.mod_birth_analysis', moduleKey: 'dogum_analizi',       accent: '#B07AE0' },
  { id: 'age',           emoji: '📊', titleKey: 'coach.mod_age_summary',    moduleKey: 'yas_koc_ozet',        accent: '#7AAEE0' },
  { id: 'body_language', emoji: '👤', titleKey: 'coach.mod_body_language',  moduleKey: 'vucut_dil',           accent: '#E0A17A' },
  // ── 13 yeni modül ────────────────────────────────────────────────────────
  { id: 'activity',      emoji: '🎪', titleKey: 'coach.mod_activity',       moduleKey: 'etkinlik_tavsiye',    accent: '#E07A7A' },
  { id: 'sport',         emoji: '🏅', titleKey: 'coach.mod_sport',          moduleKey: 'spor_aktivite',       accent: '#7AE07A' },
  { id: 'career_path',   emoji: '🚀', titleKey: 'coach.mod_career_path',    moduleKey: 'kariyer_yolu',        accent: '#7AAEE0' },
  { id: 'hr',            emoji: '👥', titleKey: 'coach.mod_hr',             moduleKey: 'insan_kaynaklari',    accent: '#E0A17A' },
  { id: 'emotional',     emoji: '💜', titleKey: 'coach.mod_emotional',      moduleKey: 'duygusal_ruhsal',     accent: '#C07AE0' },
  { id: 'meditation',    emoji: '🌿', titleKey: 'coach.mod_meditation',     moduleKey: 'meditasyon_egzersiz', accent: '#7AE0B0' },
  { id: 'book',          emoji: '📚', titleKey: 'coach.mod_book',           moduleKey: 'kitap_tavsiye',       accent: '#B07AE0' },
  { id: 'film',          emoji: '🎬', titleKey: 'coach.mod_film',           moduleKey: 'film_tavsiye',        accent: '#E07AB0' },
  { id: 'music',         emoji: '🎵', titleKey: 'coach.mod_music',          moduleKey: 'muzik_tavsiye',       accent: '#7AB0E0' },
  { id: 'podcast',       emoji: '🎙️', titleKey: 'coach.mod_podcast',        moduleKey: 'podcast_tavsiye',     accent: '#F5C842' },
  { id: 'travel',        emoji: '✈️', titleKey: 'coach.mod_travel',         moduleKey: 'seyahat_tavsiye',     accent: '#E0D07A' },
  { id: 'affirmation',   emoji: '✨', titleKey: 'coach.mod_affirmation',    moduleKey: 'gunluk_afirasyon',    accent: '#FFD700' },
  { id: 'health_adv',    emoji: '🌱', titleKey: 'coach.mod_health_advice',  moduleKey: 'saglik_tavsiye',      accent: '#7AE07A' },
];

function extractModuleText(data: any): string {
  if (!data) return '';
  if (typeof data === 'string') return data;
  if (typeof data === 'object') {
    const c = data.coaching;
    if (c) {
      return [c.felsefe, c.philosophy, c.ozet, c.summary].filter(Boolean).join('\n\n');
    }
    for (const f of ['text', 'content', 'description', 'ozet', 'summary']) {
      if (typeof data[f] === 'string' && data[f].length > 10) return data[f];
    }
    for (const v of Object.values(data)) {
      if (typeof v === 'string' && (v as string).length > 10) return v as string;
    }
  }
  return JSON.stringify(data).slice(0, 200);
}

// ── Boş durum ────────────────────────────────────────────────────────────────
const EmptyState: React.FC<{ onAnalyze: () => void; analyzing: boolean; lang: string }> = ({
  onAnalyze, analyzing, lang,
}) => (
  <View style={es.container}>
    <Text style={es.hero}>🧠</Text>
    <Text style={es.title}>{t('coach.title', lang)}</Text>
    <Text style={es.sub}>{t('coach.subtitle', lang)}</Text>

    <TouchableOpacity
      accessibilityRole="button"
      accessibilityLabel={t('coach.analyze_btn', lang)}
      style={[es.btn, analyzing && es.btnDisabled]}
      onPress={onAnalyze}
      activeOpacity={0.85}
      disabled={analyzing}
    >
      <View style={es.btnGlow} />
      {analyzing
        ? <ActivityIndicator color={colors.gold} />
        : <Text style={es.btnTxt}>{t('coach.analyze_btn', lang)}</Text>
      }
    </TouchableOpacity>

    {/* Modül önizleme */}
    <View style={es.previewRow}>
      {MODULE_CARDS.slice(0, 6).map(c => (
        <View key={c.id} style={[es.previewChip, { backgroundColor: `${c.accent}12` }]}>
          <Text style={es.previewEmoji}>{c.emoji}</Text>
        </View>
      ))}
    </View>
    <Text style={es.previewHint}>{MODULE_CARDS.length} koçluk modülü</Text>
  </View>
);

const es = StyleSheet.create({
  container:   { alignItems: 'center', paddingVertical: spacing.xl },
  hero:        { fontSize: 72, marginBottom: spacing.md },
  title:       { ...typography.h1, textAlign: 'center', marginBottom: spacing.sm },
  sub:         { ...typography.body, textAlign: 'center', color: colors.textMuted, marginBottom: spacing.xl, paddingHorizontal: spacing.lg },
  btn: {
    flexDirection: 'row', alignItems: 'center', justifyContent: 'center',
    backgroundColor: colors.surface, borderRadius: radius.xl,
    borderWidth: 1.5, borderColor: colors.gold,
    paddingVertical: spacing.md, paddingHorizontal: spacing.xl,
    overflow: 'hidden', ...shadow.gold, minWidth: 220,
  },
  btnDisabled: { opacity: 0.6 },
  btnGlow:     { ...StyleSheet.absoluteFillObject, backgroundColor: colors.goldGlow },
  btnTxt:      { ...typography.h3, color: colors.gold },
  previewRow:  { flexDirection: 'row', gap: spacing.sm, marginTop: spacing.xl, flexWrap: 'wrap', justifyContent: 'center' },
  previewChip: { width: 44, height: 44, borderRadius: radius.md, alignItems: 'center', justifyContent: 'center' },
  previewEmoji:{ fontSize: 22 },
  previewHint: { ...typography.caption, color: colors.textMuted, marginTop: spacing.sm },
});

// ── Profil kartı ─────────────────────────────────────────────────────────────
const ProfileCard: React.FC<{
  archetypes: string[];
  goldenRatio?: number;
  faceType?: string;
  onReanalyze: () => void;
  analyzing: boolean;
  lang: string;
}> = ({ archetypes, goldenRatio, faceType, onReanalyze, analyzing, lang }) => (
  <View style={pc.card}>
    <View style={pc.glow} />
    <View style={pc.row}>
      <Text style={pc.icon}>🧬</Text>
      <View style={pc.body}>
        <Text style={pc.label}>KİŞİLİK PROFİLİ</Text>
        <View style={pc.chips}>
          {archetypes.map((a, i) => (
            <View key={i} style={[pc.chip, i === 0 && pc.chipPrimary]}>
              <Text style={[pc.chipTxt, i === 0 && pc.chipTxtPrimary]}>{a}</Text>
            </View>
          ))}
        </View>
        {(goldenRatio || faceType) ? (
          <View style={pc.metaRow}>
            {goldenRatio ? <Text style={pc.meta}>✦ Altın oran {Math.round(goldenRatio * 100)}%</Text> : null}
            {faceType    ? <Text style={pc.meta}>· {faceType}</Text>                                  : null}
          </View>
        ) : null}
      </View>
      <TouchableOpacity onPress={onReanalyze} disabled={analyzing} style={pc.reBtn} activeOpacity={0.8}
        accessibilityRole="button"
        accessibilityLabel='↺'
      >
        {analyzing
          ? <ActivityIndicator size="small" color={colors.gold} />
          : <Text style={pc.reBtnTxt}>↺</Text>
        }
      </TouchableOpacity>
    </View>
  </View>
);

const pc = StyleSheet.create({
  card: {
    backgroundColor: colors.surface, borderRadius: radius.xl,
    borderWidth: 1, borderColor: colors.goldDark,
    padding: spacing.md, marginBottom: spacing.lg,
    overflow: 'hidden', ...shadow.gold,
  },
  glow:        { ...StyleSheet.absoluteFillObject, backgroundColor: colors.goldGlow },
  row:         { flexDirection: 'row', alignItems: 'flex-start', gap: spacing.md },
  icon:        { fontSize: 32, marginTop: 2 },
  body:        { flex: 1 },
  label:       { ...typography.goldLabel, marginBottom: spacing.sm },
  chips:       { flexDirection: 'row', flexWrap: 'wrap', gap: spacing.xs },
  chip: {
    backgroundColor: `${colors.gold}18`, borderRadius: radius.full,
    borderWidth: 1, borderColor: `${colors.gold}30`,
    paddingHorizontal: spacing.sm, paddingVertical: 4,
  },
  chipPrimary: { backgroundColor: `${colors.gold}28`, borderColor: colors.gold },
  chipTxt:     { ...typography.caption, color: colors.textSecondary, fontSize: 12 },
  chipTxtPrimary: { color: colors.gold, fontWeight: '700' as const },
  metaRow:     { flexDirection: 'row', gap: spacing.sm, marginTop: spacing.xs },
  meta:        { ...typography.caption, color: colors.textMuted, fontSize: 11 },
  reBtn: {
    width: 36, height: 36, borderRadius: 18,
    backgroundColor: `${colors.gold}18`,
    alignItems: 'center', justifyContent: 'center',
    borderWidth: 1, borderColor: `${colors.gold}30`,
  },
  reBtnTxt: { ...typography.h3, color: colors.gold, fontSize: 18 },
});

// ── Ana ekran ─────────────────────────────────────────────────────────────────
const CoachHubScreen: React.FC<Props> = ({ navigation }) => {
  const insets = useSafeAreaInsets();
  const { lang } = useLanguage();
  const lastAnalysis = useSelector((s: RootState) => s.analysis.lastResult);
  const scrollRef    = useRef<ScrollView>(null);

  const [analyzing,      setAnalyzing]      = useState(false);
  const [coachData,      setCoachData]      = useState<Record<string, any> | null>(null);
  const [selectedModule, setSelectedModule] = useState<string | null>(null);

  const runAnalysis = useCallback(async () => {
    if (!lastAnalysis) { Alert.alert('', t('coach.no_analysis', lang)); return; }
    setAnalyzing(true);
    setSelectedModule(null);
    try {
      // Fetch latest psych test scores (silent fail — coach still works without them)
      let testScores: Record<string, Record<string, number>> = {};
      try { testScores = await AssessmentAPI.getLatestScores(); } catch { /* no scores yet */ }

      const res = await CoachAPI.analyzeWithCoach(lastAnalysis, lang, undefined, testScores);
      setCoachData(res);
      // İlk veri olan modülü otomatik seç
      const first = MODULE_CARDS.find(c => res.coach_modules?.[c.moduleKey]?.length);
      if (first) setSelectedModule(first.moduleKey);
    } catch {
      Alert.alert('', t('common.error', lang));
    } finally {
      setAnalyzing(false);
    }
  }, [lastAnalysis, lang]);

  const archetypes: string[]  = coachData?.archetypes_used ?? [];
  const modules               = coachData?.coach_modules   ?? {};

  // Seçili modülün içerik kartı
  const renderDetailCard = () => {
    if (!selectedModule) return null;
    const items = modules[selectedModule] as any[] | undefined;
    if (!items?.length) return null;
    const card   = MODULE_CARDS.find(c => c.moduleKey === selectedModule)!;
    const accent = card?.accent ?? colors.gold;

    return (
      <View style={[dc.card, { borderTopColor: accent }]}>
        {/* Başlık */}
        <View style={dc.header}>
          <Text style={dc.headerEmoji}>{card.emoji}</Text>
          <Text style={dc.headerTitle}>{t(card.titleKey, lang)}</Text>
        </View>

        {/* Sıfat içerikleri */}
        {items.map((item: any, idx: number) => {
          const text = extractModuleText(item.data);
          if (!text) return null;
          return (
            <View key={idx} style={[dc.item, idx > 0 && dc.itemBorder]}>
              {item.archetype && (
                <View style={[dc.badge, { backgroundColor: `${accent}18`, borderColor: `${accent}40` }]}>
                  <Text style={[dc.badgeTxt, { color: accent }]}>{item.archetype}</Text>
                </View>
              )}
              <Text style={dc.text}>{text}</Text>
            </View>
          );
        })}
      </View>
    );
  };

  return (
    <View style={styles.container}>
      <StatusBar barStyle="light-content" />
      <ScrollView
        ref={scrollRef}
        showsVerticalScrollIndicator={false}
        contentContainerStyle={[styles.scroll, { paddingTop: insets.top + spacing.sm }]}
      >
        {/* Header */}
        <View style={styles.header}>
          <TouchableOpacity onPress={() => navigation.goBack()} style={styles.backBtn}
            accessibilityRole="button"
            accessibilityLabel={t('coach.title', lang)}
          >
            <Text style={styles.backArrow}>←</Text>
          </TouchableOpacity>
          <Text style={styles.headerTitle}>{t('coach.title', lang)}</Text>
          <View style={{ width: 40 }} />
        </View>

        {/* ── DURUM: Analiz yok ── */}
        {!coachData && (
          <EmptyState onAnalyze={runAnalysis} analyzing={analyzing} lang={lang} />
        )}

        {/* ── DURUM: Analiz var ── */}
        {coachData && (
          <>
            {/* Profil kartı */}
            <ProfileCard
              archetypes={archetypes}
              goldenRatio={coachData.golden_ratio}
              faceType={coachData.face_type}
              onReanalyze={runAnalysis}
              analyzing={analyzing}
              lang={lang}
            />

            {/* Sağlık uyarısı */}
            {coachData.health_disclaimer && (
              <View style={styles.disclaimer}>
                <Text style={styles.disclaimerText}>
                  ⚠️ {coachData.health_disclaimer.text}
                </Text>
              </View>
            )}

            {/* Modül şeridi */}
            <Text style={styles.sectionLabel}>{t('coach.modules_title', lang)}</Text>
            <FlatList
              data={MODULE_CARDS}
              horizontal
              showsHorizontalScrollIndicator={false}
              keyExtractor={c => c.id}
              contentContainerStyle={styles.strip}
              renderItem={({ item: card }) => {
                const hasData  = Boolean(modules[card.moduleKey]?.length);
                const isActive = selectedModule === card.moduleKey;
                return (
                  <TouchableOpacity
                    accessibilityRole="button"
                    accessibilityLabel={card.emoji}
                    style={[
                      styles.stripItem,
                      isActive && { borderColor: card.accent, backgroundColor: `${card.accent}18` },
                      !isActive && { borderColor: hasData ? `${card.accent}40` : colors.border },
                    ]}
                    onPress={() => hasData && setSelectedModule(
                      selectedModule === card.moduleKey ? null : card.moduleKey
                    )}
                    activeOpacity={hasData ? 0.75 : 1}
                  >
                    <View style={[
                      styles.stripIconWrap,
                      { backgroundColor: isActive ? `${card.accent}30` : `${card.accent}14` },
                    ]}>
                      <Text style={styles.stripEmoji}>{card.emoji}</Text>
                    </View>
                    <Text
                      style={[
                        styles.stripLabel,
                        isActive && { color: card.accent, fontWeight: '700' as const },
                        !hasData  && { color: colors.textMuted },
                      ]}
                      numberOfLines={2}
                    >
                      {t(card.titleKey, lang)}
                    </Text>
                    {/* Alt çizgi göstergesi */}
                    {isActive && (
                      <View style={[styles.stripActiveLine, { backgroundColor: card.accent }]} />
                    )}
                    {!isActive && hasData && (
                      <View style={[styles.stripDot, { backgroundColor: card.accent }]} />
                    )}
                  </TouchableOpacity>
                );
              }}
            />

            {/* Detay kartı */}
            {renderDetailCard()}

            {/* Seçim yapılmadıysa yönlendirme */}
            {!selectedModule && (
              <View style={styles.hintBox}>
                <Text style={styles.hintTxt}>👆 Bir modüle dokunarak analiz detaylarını gör</Text>
              </View>
            )}
          </>
        )}

        {/* Hızlı aksiyonlar */}
        <Text style={styles.sectionLabel}>{t('coach.goals_btn', lang)}</Text>
        <View style={styles.actionRow}>
          <TouchableOpacity
            accessibilityRole="button"
            accessibilityLabel={t('coach.goals_btn', lang)}
            style={[styles.actionCard, { borderColor: `${colors.gold}40` }]}
            onPress={() => (navigation.navigate as any)('CoachGoals')}
            activeOpacity={0.85}
          >
            <Text style={styles.actionEmoji}>🎯</Text>
            <Text style={styles.actionTitle}>{t('coach.goals_btn', lang)}</Text>
          </TouchableOpacity>
          <TouchableOpacity
            accessibilityRole="button"
            accessibilityLabel={t('coach.birth_btn', lang)}
            style={[styles.actionCard, { borderColor: `${'#C07AE0'}40` }]}
            onPress={() => (navigation.navigate as any)('CoachBirth')}
            activeOpacity={0.85}
          >
            <Text style={styles.actionEmoji}>🌌</Text>
            <Text style={styles.actionTitle}>{t('coach.birth_btn', lang)}</Text>
          </TouchableOpacity>
          <TouchableOpacity
            accessibilityRole="button"
            accessibilityLabel={t('coach.memories_btn', lang)}
            style={[styles.actionCard, { borderColor: '#9B7AE040' }]}
            onPress={() => (navigation.navigate as any)('Memories')}
            activeOpacity={0.85}
          >
            <Text style={styles.actionEmoji}>🧠</Text>
            <Text style={styles.actionTitle}>{t('coach.memories_btn', lang)}</Text>
          </TouchableOpacity>
        </View>
      </ScrollView>
    </View>
  );
};

// ── Detail card styles ────────────────────────────────────────────────────────
const dc = StyleSheet.create({
  card: {
    backgroundColor: colors.surface,
    borderRadius:    radius.xl,
    borderWidth:     1,
    borderColor:     colors.border,
    borderTopWidth:  3,
    marginBottom:    spacing.lg,
    overflow:        'hidden',
    ...shadow.md,
  },
  header: {
    flexDirection: 'row', alignItems: 'center',
    gap: spacing.sm,
    paddingHorizontal: spacing.md,
    paddingVertical:   spacing.md,
    borderBottomWidth: 1,
    borderBottomColor: colors.border,
  },
  headerEmoji: { fontSize: 24 },
  headerTitle: { ...typography.h2, fontSize: 17 },
  item: {
    paddingHorizontal: spacing.md,
    paddingVertical:   spacing.md,
  },
  itemBorder: { borderTopWidth: 1, borderTopColor: colors.border },
  badge: {
    alignSelf: 'flex-start',
    borderRadius: radius.full,
    borderWidth: 1,
    paddingHorizontal: spacing.sm,
    paddingVertical: 3,
    marginBottom: spacing.sm,
  },
  badgeTxt: { ...typography.caption, fontSize: 11, fontWeight: '600' as const },
  text:     { ...typography.body, color: colors.textWarm, fontSize: 14, lineHeight: 22 },
});

// ── Main styles ───────────────────────────────────────────────────────────────
const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: colors.background },
  scroll: {
    paddingHorizontal: spacing.lg,
    paddingBottom:     spacing.xxxl,
  },

  header: {
    flexDirection: 'row', alignItems: 'center',
    justifyContent: 'space-between',
    marginBottom: spacing.lg,
  },
  backBtn: {
    width: 40, height: 40, borderRadius: radius.full,
    backgroundColor: colors.surface,
    alignItems: 'center', justifyContent: 'center',
    ...shadow.sm,
  },
  backArrow:   { ...typography.h2, color: colors.textPrimary, fontSize: 20 },
  headerTitle: { ...typography.h2, fontSize: 17 },

  disclaimer: {
    backgroundColor: `${'#F5A623'}12`,
    borderRadius:    radius.md,
    borderWidth:     1,
    borderColor:     `${'#F5A623'}30`,
    padding:         spacing.sm,
    marginBottom:    spacing.lg,
  },
  disclaimerText: { ...typography.caption, color: colors.textWarm, fontSize: 11, lineHeight: 16 },

  sectionLabel: {
    ...typography.goldLabel,
    marginBottom: spacing.sm,
    marginTop:    spacing.xs,
  },

  // Modül şeridi
  strip: {
    gap: spacing.sm,
    paddingBottom: spacing.sm,
    paddingRight:  spacing.md,
  },
  stripItem: {
    width: 76,
    backgroundColor: colors.surface,
    borderRadius:    radius.lg,
    borderWidth:     1.5,
    padding:         spacing.sm,
    alignItems:      'center',
    gap:             spacing.xs,
    minHeight:       88,
    ...shadow.sm,
  },
  stripIconWrap: {
    width: 44, height: 44, borderRadius: radius.md,
    alignItems: 'center', justifyContent: 'center',
  },
  stripEmoji:      { fontSize: 22 },
  stripLabel:      { ...typography.caption, fontSize: 10, textAlign: 'center', color: colors.textSecondary, lineHeight: 14 },
  stripActiveLine: { width: 24, height: 2, borderRadius: 1, marginTop: 2 },
  stripDot:        { width: 6, height: 6, borderRadius: 3, marginTop: 2 },

  hintBox: {
    backgroundColor: colors.surface,
    borderRadius:    radius.md,
    borderWidth:     1,
    borderColor:     colors.border,
    borderStyle:     'dashed' as const,
    padding:         spacing.md,
    alignItems:      'center',
    marginBottom:    spacing.lg,
    marginTop:       spacing.sm,
  },
  hintTxt: { ...typography.caption, color: colors.textMuted, textAlign: 'center' },

  actionRow: { flexDirection: 'row', gap: spacing.sm, marginTop: spacing.sm, marginBottom: spacing.lg },
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
  actionTitle: { ...typography.label, textAlign: 'center', fontSize: 12 },
});

export default CoachHubScreen;

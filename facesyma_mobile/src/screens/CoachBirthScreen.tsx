// src/screens/CoachBirthScreen.tsx
import React, { useState } from 'react';
import {
  View, Text, StyleSheet, ScrollView, TouchableOpacity,
  ActivityIndicator, StatusBar, TextInput,
} from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { CoachAPI } from '../services/api';
import theme from '../utils/theme';
import { useLanguage } from '../utils/LanguageContext';
import { t } from '../utils/i18n';
import type { ScreenProps } from '../navigation/types';

const { colors, spacing, typography, radius, shadow } = theme;

type Props = ScreenProps<'CoachBirth'>;

interface NameNumerology {
  name: string;
  expression_number: number;
  expression_meaning: string;
  soul_urge_number: number;
  soul_urge_meaning: string;
  personality_number: number;
  personality_meaning: string;
  ebced: { total: number; reduced: number; meaning: string; };
  kabala: { total: number; reduced: number; meaning: string; };
  labels: { title: string; expression: string; soul_urge: string; personality: string; ebced_title: string; kabala_title: string; total: string; reduced: string; };
}

interface FaceAstroMatch {
  has_face_data: boolean;
  title?: string;
  match_score?: number;
  confirming_traits?: string[];
  face_top_archetypes?: string[];
  summary?: string;
}

interface BirthResult {
  birth_date: string;
  name_numerology?: NameNumerology;
  face_astro_match?: FaceAstroMatch;
  astrology: {
    sun_sign:      string;
    element:       string;
    quality:       string;
    season:        string;
    birth_year:    number;
    time_energy?:  string;
    rising_sign?:  string;
    rising_degree?: number;
    city_resolved?: string;
    rising_hint?:  string;
    error?: string;
  };
  numerology: {
    life_path_number: number;
    life_path_meaning: string;
    day_number:  number;
    month_number: number;
    year_number: number;
    personal_year_number: number;
    personal_year_meaning: string;
    personal_year_label: string;
    current_year: number;
    is_master_number: boolean;
    master_label?: string;
  };
}

const InfoRow: React.FC<{ label: string; value: string; accent?: string }> = ({ label, value, accent }) => (
  <View style={styles.infoRow}>
    <Text style={styles.infoLabel}>{label}</Text>
    <Text style={[styles.infoValue, accent ? { color: accent } : undefined]}>{value}</Text>
  </View>
);

const CoachBirthScreen: React.FC<Props> = ({ navigation }) => {
  const insets   = useSafeAreaInsets();
  const { lang } = useLanguage();

  const [birthDate, setBirthDate] = useState('');
  const [birthTime, setBirthTime] = useState('');
  const [birthCity, setBirthCity] = useState('');
  const [name,      setName]      = useState('');
  const [loading,   setLoading]   = useState(false);
  const [result,    setResult]    = useState<BirthResult | null>(null);
  const [error,     setError]     = useState('');

  const handleCalculate = async () => {
    const trimmedDate = birthDate.trim();
    if (!trimmedDate.match(/^\d{4}-\d{2}-\d{2}$/)) {
      setError(t('coach.birth_date_label', lang) + ': YYYY-MM-DD');
      return;
    }
    setError('');
    setLoading(true);
    try {
      const res = await CoachAPI.birthAnalysis(
        trimmedDate,
        birthTime.trim() || undefined,
        lang,
        name.trim() || undefined,
        birthCity.trim() || undefined,
      );
      setResult(res);
    } catch {
      setError(t('common.error', lang));
    } finally {
      setLoading(false);
    }
  };

  const astro = result?.astrology;
  const num   = result?.numerology;

  return (
    <View style={styles.container}>
      <StatusBar barStyle="light-content" />
      <ScrollView
        showsVerticalScrollIndicator={false}
        contentContainerStyle={[styles.scroll, { paddingTop: insets.top + spacing.md }]}
        keyboardShouldPersistTaps="handled"
      >
        {/* Header */}
        <View style={styles.header}>
          <TouchableOpacity onPress={() => navigation.goBack()} style={styles.backBtn}>
            <Text style={styles.backArrow}>←</Text>
          </TouchableOpacity>
          <View style={styles.headerBody}>
            <Text style={styles.headerTitle}>{t('coach.birth_title', lang)}</Text>
            <Text style={styles.headerSub}>{t('coach.mod_astrology', lang)}</Text>
          </View>
        </View>

        {/* Form card */}
        <View style={styles.formCard}>
          <Text style={styles.fieldLabel}>{t('coach.birth_date_label', lang)} (YYYY-MM-DD)</Text>
          <TextInput
            style={styles.input}
            value={birthDate}
            onChangeText={setBirthDate}
            placeholder="1990-06-15"
            placeholderTextColor={colors.textMuted}
            keyboardType="numeric"
            maxLength={10}
          />

          <Text style={[styles.fieldLabel, { marginTop: spacing.md }]}>
            {t('coach.birth_time_label', lang)} (HH:MM)
          </Text>
          <TextInput
            style={styles.input}
            value={birthTime}
            onChangeText={setBirthTime}
            placeholder="08:30"
            placeholderTextColor={colors.textMuted}
            keyboardType="numeric"
            maxLength={5}
          />

          <Text style={[styles.fieldLabel, { marginTop: spacing.md }]}>
            {t('coach.birth_city_label', lang)}
          </Text>
          <TextInput
            style={styles.input}
            value={birthCity}
            onChangeText={setBirthCity}
            placeholder="Istanbul, Paris, Tokyo..."
            placeholderTextColor={colors.textMuted}
            autoCapitalize="words"
            autoCorrect={false}
          />

          <Text style={[styles.fieldLabel, { marginTop: spacing.md }]}>
            {t('coach.name_label', lang)}
          </Text>
          <TextInput
            style={styles.input}
            value={name}
            onChangeText={setName}
            placeholder={t('coach.name_label', lang)}
            placeholderTextColor={colors.textMuted}
            autoCapitalize="words"
          />

          {!!error && <Text style={styles.errorText}>{error}</Text>}

          <TouchableOpacity
            style={[styles.calcBtn, loading && styles.calcBtnDisabled]}
            onPress={handleCalculate}
            disabled={loading}
            activeOpacity={0.85}
          >
            <View style={styles.calcGlow} />
            {loading
              ? <ActivityIndicator color={colors.gold} />
              : <Text style={styles.calcBtnText}>{t('coach.calculate', lang)}</Text>}
          </TouchableOpacity>
        </View>

        {/* Results */}
        {astro && !astro.error && (
          <>
            {/* Astrology card */}
            <View style={[styles.resultCard, { borderLeftColor: '#C07AE0' }]}>
              <Text style={styles.resultCardTitle}>⭐ {t('coach.mod_astrology', lang)}</Text>
              <InfoRow label={t('coach.sun_sign', lang)} value={astro.sun_sign} accent={colors.gold} />
              <InfoRow label={t('coach.element', lang)}  value={astro.element} />
              <InfoRow label={t('coach.quality', lang)}  value={astro.quality} />
              <InfoRow label={t('coach.season', lang)}   value={astro.season} />
              {astro.time_energy && (
                <InfoRow label="⏰" value={astro.time_energy} />
              )}
              {astro.rising_sign ? (
                <InfoRow
                  label={`↑ ${t('coach.rising_sign', lang)}`}
                  value={
                    astro.rising_degree != null
                      ? `${astro.rising_sign}  ${astro.rising_degree}°`
                      : astro.rising_sign
                  }
                  accent="#C07AE0"
                />
              ) : astro.rising_hint ? (
                <Text style={styles.hintText}>ℹ️ {astro.rising_hint}</Text>
              ) : null}
              {astro.city_resolved ? (
                <Text style={[styles.hintText, { marginTop: 2 }]}>
                  📍 {astro.city_resolved}
                </Text>
              ) : null}
            </View>

            {/* Numerology card */}
            {num && (
              <View style={[styles.resultCard, { borderLeftColor: colors.gold }]}>
                <Text style={styles.resultCardTitle}>🔢 {t('coach.numerology_title', lang)}</Text>
                {num.is_master_number && !!num.master_label && (
                  <View style={styles.masterBadge}>
                    <Text style={styles.masterBadgeText}>✦ {num.master_label}</Text>
                  </View>
                )}
                <InfoRow
                  label={t('coach.life_path', lang)}
                  value={String(num.life_path_number)}
                  accent={colors.gold}
                />
                {!!num.life_path_meaning && (
                  <Text style={styles.meaningText}>{num.life_path_meaning}</Text>
                )}
                <View style={styles.numRow}>
                  <View style={styles.numChip}>
                    <Text style={styles.numChipNum}>{num.day_number}</Text>
                    <Text style={styles.numChipLabel}>{t('coach.num_day', lang)}</Text>
                  </View>
                  <View style={styles.numChip}>
                    <Text style={styles.numChipNum}>{num.month_number}</Text>
                    <Text style={styles.numChipLabel}>{t('coach.num_month', lang)}</Text>
                  </View>
                  <View style={styles.numChip}>
                    <Text style={styles.numChipNum}>{num.year_number}</Text>
                    <Text style={styles.numChipLabel}>{t('coach.num_year', lang)}</Text>
                  </View>
                </View>
                <InfoRow
                  label={num.personal_year_label ?? t('coach.life_path', lang)}
                  value={`${num.personal_year_number} · ${num.current_year}`}
                  accent={colors.goldDark}
                />
                {!!num.personal_year_meaning && (
                  <Text style={styles.meaningText}>{num.personal_year_meaning}</Text>
                )}
              </View>
            )}
          </>
        )}

        {/* Face × Birth alignment card */}
        {result?.face_astro_match?.has_face_data && (() => {
          const fam = result.face_astro_match!;
          const score = fam.match_score ?? 0;
          const barColor = score >= 75 ? '#4CAF50' : score >= 40 ? colors.gold : '#C07AE0';
          return (
            <View style={[styles.resultCard, { borderLeftColor: '#26C6DA' }]}>
              <Text style={styles.resultCardTitle}>🔗 {fam.title}</Text>

              {/* Match score bar */}
              <View style={styles.matchBarContainer}>
                <View style={[styles.matchBarFill, { width: `${score}%` as any, backgroundColor: barColor }]} />
              </View>
              <Text style={[styles.matchScoreText, { color: barColor }]}>{score}%</Text>

              {/* Confirming traits chips */}
              {fam.confirming_traits && fam.confirming_traits.length > 0 && (
                <View style={styles.traitChips}>
                  {fam.confirming_traits.map((trait, i) => (
                    <View key={i} style={[styles.traitChip, { borderColor: barColor }]}>
                      <Text style={[styles.traitChipText, { color: barColor }]}>✓ {trait}</Text>
                    </View>
                  ))}
                </View>
              )}

              {/* Face top archetypes (when no confirming match) */}
              {(!fam.confirming_traits || fam.confirming_traits.length === 0) &&
                fam.face_top_archetypes && fam.face_top_archetypes.length > 0 && (
                <View style={styles.traitChips}>
                  {fam.face_top_archetypes.slice(0, 4).map((trait, i) => (
                    <View key={i} style={[styles.traitChip, { borderColor: colors.textMuted }]}>
                      <Text style={[styles.traitChipText, { color: colors.textMuted }]}>{trait}</Text>
                    </View>
                  ))}
                </View>
              )}

              {!!fam.summary && (
                <Text style={styles.meaningText}>{fam.summary}</Text>
              )}
            </View>
          );
        })()}

        {/* Name Numerology card */}
        {result?.name_numerology && (
          <View style={[styles.resultCard, { borderLeftColor: colors.goldDark }]}>
            <Text style={styles.resultCardTitle}>🔡 {result.name_numerology.labels.title}</Text>
            <Text style={[styles.hintText, { marginBottom: spacing.sm }]}>{result.name_numerology.name}</Text>
            <InfoRow
              label={result.name_numerology.labels.expression}
              value={String(result.name_numerology.expression_number)}
              accent={colors.gold}
            />
            {!!result.name_numerology.expression_meaning && (
              <Text style={styles.meaningText}>{result.name_numerology.expression_meaning}</Text>
            )}
            <View style={styles.numRow}>
              <View style={styles.numChip}>
                <Text style={styles.numChipNum}>{result.name_numerology.soul_urge_number}</Text>
                <Text style={styles.numChipLabel}>{result.name_numerology.labels.soul_urge}</Text>
              </View>
              <View style={styles.numChip}>
                <Text style={styles.numChipNum}>{result.name_numerology.personality_number}</Text>
                <Text style={styles.numChipLabel}>{result.name_numerology.labels.personality}</Text>
              </View>
            </View>
          </View>
        )}

        {/* Ebced card */}
        {result?.name_numerology?.ebced && (
          <View style={[styles.resultCard, { borderLeftColor: '#C07AE0' }]}>
            <Text style={styles.resultCardTitle}>☽ {result.name_numerology.labels.ebced_title}</Text>
            <InfoRow label={result.name_numerology.labels.total}   value={String(result.name_numerology.ebced.total)}   accent="#C07AE0" />
            <InfoRow label={result.name_numerology.labels.reduced} value={String(result.name_numerology.ebced.reduced)} accent="#C07AE0" />
            {!!result.name_numerology.ebced.meaning && (
              <Text style={styles.meaningText}>{result.name_numerology.ebced.meaning}</Text>
            )}
          </View>
        )}

        {/* Kabala card */}
        {result?.name_numerology?.kabala && (
          <View style={[styles.resultCard, { borderLeftColor: '#4A9EE0' }]}>
            <Text style={styles.resultCardTitle}>✡ {result.name_numerology.labels.kabala_title}</Text>
            <InfoRow label={result.name_numerology.labels.total}   value={String(result.name_numerology.kabala.total)}   accent="#4A9EE0" />
            <InfoRow label={result.name_numerology.labels.reduced} value={String(result.name_numerology.kabala.reduced)} accent="#4A9EE0" />
            {!!result.name_numerology.kabala.meaning && (
              <Text style={styles.meaningText}>{result.name_numerology.kabala.meaning}</Text>
            )}
          </View>
        )}

        {astro?.error && (
          <View style={styles.errorCard}>
            <Text style={styles.errorText}>{astro.error}</Text>
          </View>
        )}
      </ScrollView>
    </View>
  );
};

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

  // Form
  formCard: {
    backgroundColor: colors.surface,
    borderRadius:    radius.xl,
    borderWidth:     1,
    borderColor:     colors.border,
    padding:         spacing.lg,
    marginBottom:    spacing.lg,
    ...shadow.sm,
  },
  fieldLabel: { ...typography.goldLabel, fontSize: 11, marginBottom: spacing.sm },
  input: {
    backgroundColor: colors.background,
    borderRadius:    radius.md,
    borderWidth:     1,
    borderColor:     colors.border,
    padding:         spacing.md,
    color:           colors.textPrimary,
    fontFamily:      'System',
    fontSize:        16,
    letterSpacing:   1,
  },
  errorText: { ...typography.caption, color: '#E07A7A', marginTop: spacing.sm },
  calcBtn: {
    marginTop:       spacing.lg,
    backgroundColor: colors.surface,
    borderRadius:    radius.lg,
    borderWidth:     1,
    borderColor:     colors.goldDark,
    padding:         spacing.md,
    alignItems:      'center',
    overflow:        'hidden',
    ...shadow.gold,
  },
  calcBtnDisabled: { opacity: 0.6 },
  calcGlow: {
    ...StyleSheet.absoluteFillObject,
    backgroundColor: colors.goldGlow,
  },
  calcBtnText: { ...typography.h3, color: colors.gold },

  // Result cards
  resultCard: {
    backgroundColor: colors.surface,
    borderRadius:    radius.lg,
    borderWidth:     1,
    borderColor:     colors.border,
    borderLeftWidth: 3,
    padding:         spacing.md,
    marginBottom:    spacing.md,
    ...shadow.sm,
  },
  resultCardTitle: { ...typography.h3, marginBottom: spacing.md },

  // Info rows
  infoRow: {
    flexDirection: 'row', justifyContent: 'space-between',
    alignItems: 'center',
    paddingVertical: spacing.sm,
    borderBottomWidth: 1,
    borderBottomColor: colors.border,
  },
  infoLabel: { ...typography.caption, color: colors.textMuted },
  infoValue: { ...typography.body, fontWeight: '600' },
  hintText:  { ...typography.caption, color: colors.textWarm, marginTop: spacing.sm, fontStyle: 'italic' },

  // Numerology
  masterBadge: {
    backgroundColor: `${colors.gold}18`,
    borderRadius: radius.md,
    borderWidth: 1,
    borderColor: `${colors.gold}60`,
    paddingVertical: spacing.xs,
    paddingHorizontal: spacing.md,
    alignSelf: 'flex-start' as const,
    marginBottom: spacing.sm,
  },
  masterBadgeText: { ...typography.caption, color: colors.gold, fontWeight: '700' as const },
  meaningText: { ...typography.body, color: colors.textWarm, fontSize: 13, marginVertical: spacing.sm, lineHeight: 20 },
  numRow: { flexDirection: 'row', gap: spacing.sm, marginTop: spacing.sm },
  numChip: {
    flex: 1, backgroundColor: colors.background,
    borderRadius: radius.md, borderWidth: 1,
    borderColor: colors.border, alignItems: 'center',
    paddingVertical: spacing.sm,
  },
  numChipNum:   { ...typography.h2, color: colors.gold, fontSize: 22 },
  numChipLabel: { ...typography.caption, color: colors.textMuted, fontSize: 10 },

  // Face × Birth alignment
  matchBarContainer: {
    height: 8, backgroundColor: colors.border,
    borderRadius: radius.full, overflow: 'hidden',
    marginTop: spacing.sm, marginBottom: spacing.xs,
  },
  matchBarFill: { height: '100%', borderRadius: radius.full },
  matchScoreText: { ...typography.h2, fontSize: 20, fontWeight: '700' as const, marginBottom: spacing.sm },
  traitChips: { flexDirection: 'row', flexWrap: 'wrap', gap: spacing.xs, marginBottom: spacing.sm },
  traitChip: {
    borderRadius: radius.full, borderWidth: 1,
    paddingVertical: 3, paddingHorizontal: spacing.sm,
  },
  traitChipText: { ...typography.caption, fontSize: 11, fontWeight: '600' as const },

  // Error
  errorCard: {
    backgroundColor: `${'#E07A7A'}18`,
    borderRadius:    radius.md,
    borderWidth:     1,
    borderColor:     `${'#E07A7A'}40`,
    padding:         spacing.md,
  },
});

export default CoachBirthScreen;

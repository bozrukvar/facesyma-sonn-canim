// src/screens/AstrologyScreen.tsx
// Natal harita + yüz analizi entegrasyonu — yakında
import React, { useState } from 'react';
import { View, Text, StyleSheet, ScrollView, TouchableOpacity, TextInput, Alert } from 'react-native';
import { Card, GoldButton, SectionLabel } from '../components/ui';
import { CoachAPI } from '../services/api';
import theme from '../utils/theme';
const { colors, spacing, typography, radius } = theme;
import { useLanguage } from '../utils/LanguageContext';
import { t } from '../utils/i18n';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { useDispatch } from 'react-redux';
import { AppDispatch } from '../store';
import { markModuleUsed } from '../store/authSlice';
import type { ScreenProps } from '../navigation/types';
import type { AstrologyResult } from '../types/api';

const AstrologyScreen = ({ navigation, route }: ScreenProps<'Astrology'>) => {
  const insets = useSafeAreaInsets();
  const dispatch = useDispatch<AppDispatch>();
  const [birthDate, setBirthDate] = useState('');
  const [birthTime, setBirthTime] = useState('');
  const [name,      setName]      = useState('');
  const [result,    setResult]    = useState<AstrologyResult | null>(null);
  const [loading,   setLoading]   = useState(false);
  const { lang } = useLanguage();

  const calculate = async () => {
    if (!birthDate) return;
    const errTitle = t('common.error', lang);
    if (!/^\d{4}-\d{2}-\d{2}$/.test(birthDate)) {
      Alert.alert(errTitle, t('astrology.birth_date_format', lang));
      return;
    }
    if (birthTime && !/^\d{2}:\d{2}$/.test(birthTime)) {
      Alert.alert(errTitle, t('astrology.birth_time_format', lang));
      return;
    }
    setLoading(true);
    try {
      const data = await CoachAPI.birthAnalysis(birthDate, birthTime || undefined, lang, name.trim() || undefined);
      setResult(data);
      dispatch(markModuleUsed('astrology'));
    } catch (e: any) {
      Alert.alert(
        errTitle,
        e?.response?.data?.detail || t('common.generic_error', lang),
      );
    } finally {
      setLoading(false);
    }
  };

  return (
    <View style={styles.container}>
      <View style={[styles.header, { paddingTop: insets.top + spacing.sm }]}>
        <TouchableOpacity onPress={() => navigation.goBack()}>
          <Text style={styles.back}>←</Text>
        </TouchableOpacity>
        <Text style={styles.title}>{t('astrology.title', lang)}</Text>
        <View style={styles.spacer} />
      </View>
      <ScrollView contentContainerStyle={styles.scroll} showsVerticalScrollIndicator={false}>
        <Card variant="warm" style={styles.mb16}>
          <SectionLabel>{t('astrology.birth_date', lang)}</SectionLabel>
          <TextInput
            style={styles.input}
            value={birthDate}
            onChangeText={setBirthDate}
            placeholder={t('astrology.birth_date_format', lang)}
            placeholderTextColor={colors.textMuted}
            keyboardType="default"
          />
          <SectionLabel>{t('astrology.birth_time', lang)}</SectionLabel>
          <TextInput
            style={styles.input}
            value={birthTime}
            onChangeText={setBirthTime}
            placeholder={t('astrology.birth_time_format', lang)}
            placeholderTextColor={colors.textMuted}
            keyboardType="default"
          />
          <SectionLabel>{t('coach.name_label', lang)}</SectionLabel>
          <TextInput
            style={styles.input}
            value={name}
            onChangeText={setName}
            placeholder={t('coach.name_label', lang)}
            placeholderTextColor={colors.textMuted}
            autoCapitalize="words"
          />
          <GoldButton title={t('astrology.calculate', lang)} onPress={calculate} loading={loading} style={styles.mt12} />
        </Card>

        {result && (
          <>
            {/* Western zodiac */}
            {result.western_sign_emoji && (
              <Card variant="gold" style={styles.signCard}>
                <Text style={styles.signEmoji}>{result.western_sign_emoji}</Text>
                <Text style={styles.signLabel}>{result.western_sign_label ?? result.western_sign}</Text>
              </Card>
            )}

            {/* Chinese zodiac */}
            {result.chinese_animal_label && (
              <Card style={styles.mb12}>
                <Text style={styles.row}>🐉 {t('astrology.chinese_zodiac', lang)}: {result.chinese_animal_label}</Text>
              </Card>
            )}

            {/* Element + face reading */}
            {result.element_label && (
              <Card style={styles.mb12}>
                <Text style={styles.row}>✨ {t('astrology.element', lang)}: {result.element_label}</Text>
                {result.face_reading ? <Text style={styles.subRow}>{result.face_reading}</Text> : null}
              </Card>
            )}

            {/* Daily message */}
            {result.daily_message && (
              <Card variant="warm" style={styles.mb12}>
                <Text style={styles.row}>🌟 {result.daily_message}</Text>
              </Card>
            )}

            {/* Astrology details */}
            {result.astrology && (
              <>
                <SectionLabel>{t('astrology.section_astrology', lang)}</SectionLabel>
                <Card variant="gold" style={styles.mb12}>
                  {result.astrology.sun_sign && (
                    <View style={styles.numLifeRow}>
                      <Text style={styles.numLifeLabel}>{t('coach.sun_sign', lang)}</Text>
                      <Text style={[styles.numLifeValue, { fontSize: 16 }]}>{result.astrology.sun_sign}</Text>
                    </View>
                  )}
                  {result.astrology.element && (
                    <View style={styles.numLifeRow}>
                      <Text style={styles.numLifeLabel}>{t('coach.element', lang)}</Text>
                      <Text style={[styles.numLifeValue, { fontSize: 16, color: colors.textPrimary }]}>{result.astrology.element}</Text>
                    </View>
                  )}
                  {result.astrology.quality && (
                    <View style={styles.numLifeRow}>
                      <Text style={styles.numLifeLabel}>{t('coach.quality', lang)}</Text>
                      <Text style={[styles.numLifeValue, { fontSize: 16, color: colors.textPrimary }]}>{result.astrology.quality}</Text>
                    </View>
                  )}
                  {result.astrology.season && (
                    <View style={[styles.numLifeRow, { borderBottomWidth: 0 }]}>
                      <Text style={styles.numLifeLabel}>{t('coach.season', lang)}</Text>
                      <Text style={[styles.numLifeValue, { fontSize: 16, color: colors.textPrimary }]}>{result.astrology.season}</Text>
                    </View>
                  )}
                  {result.astrology.time_energy && (
                    <Text style={styles.numMeaning}>⏰ {result.astrology.time_energy}</Text>
                  )}
                  {result.astrology.rising_hint && (
                    <Text style={styles.numMeaning}>ℹ️ {result.astrology.rising_hint}</Text>
                  )}
                </Card>
              </>
            )}
            {result.numerology && (
              <>
                <SectionLabel>{t('astrology.section_numerology', lang)}</SectionLabel>
                <Card style={styles.numCard}>
                  <Text style={styles.numTitle}>🔢 {t('coach.numerology_title', lang)}</Text>
                  {result.numerology.is_master_number && !!result.numerology.master_label && (
                    <View style={styles.masterBadge}>
                      <Text style={styles.masterBadgeText}>✦ {result.numerology.master_label}</Text>
                    </View>
                  )}
                  <View style={styles.numLifeRow}>
                    <Text style={styles.numLifeLabel}>{t('coach.life_path', lang)}</Text>
                    <Text style={styles.numLifeValue}>{result.numerology.life_path_number}</Text>
                  </View>
                  {!!result.numerology.life_path_meaning && (
                    <Text style={styles.numMeaning}>{result.numerology.life_path_meaning}</Text>
                  )}
                  <View style={styles.numChipRow}>
                    <View style={styles.numChip}>
                      <Text style={styles.numChipNum}>{result.numerology.day_number}</Text>
                      <Text style={styles.numChipLabel}>{t('coach.num_day', lang)}</Text>
                    </View>
                    <View style={styles.numChip}>
                      <Text style={styles.numChipNum}>{result.numerology.month_number}</Text>
                      <Text style={styles.numChipLabel}>{t('coach.num_month', lang)}</Text>
                    </View>
                    <View style={styles.numChip}>
                      <Text style={styles.numChipNum}>{result.numerology.year_number}</Text>
                      <Text style={styles.numChipLabel}>{t('coach.num_year', lang)}</Text>
                    </View>
                  </View>
                  <View style={[styles.numLifeRow, { marginTop: spacing.sm }]}>
                    <Text style={styles.numLifeLabel}>
                      {result.numerology.personal_year_label ?? t('coach.life_path', lang)}
                    </Text>
                    <Text style={[styles.numLifeValue, { fontSize: 18, color: colors.goldDark }]}>
                      {result.numerology.personal_year_number} · {result.numerology.current_year}
                    </Text>
                  </View>
                  {!!result.numerology.personal_year_meaning && (
                    <Text style={styles.numMeaning}>{result.numerology.personal_year_meaning}</Text>
                  )}
                </Card>
              </>
            )}

            {result.name_numerology && (
              <>
                <SectionLabel>{result.name_numerology.labels.title}</SectionLabel>
                <Card style={styles.nameCard}>
                  <Text style={styles.numTitle}>🔡 {result.name_numerology.name}</Text>
                  <View style={styles.numLifeRow}>
                    <Text style={styles.numLifeLabel}>{result.name_numerology.labels.expression}</Text>
                    <Text style={styles.numLifeValue}>{result.name_numerology.expression_number}</Text>
                  </View>
                  {!!result.name_numerology.expression_meaning && (
                    <Text style={styles.numMeaning}>{result.name_numerology.expression_meaning}</Text>
                  )}
                  <View style={styles.numChipRow}>
                    <View style={styles.numChip}>
                      <Text style={styles.numChipNum}>{result.name_numerology.soul_urge_number}</Text>
                      <Text style={styles.numChipLabel}>{result.name_numerology.labels.soul_urge}</Text>
                    </View>
                    <View style={styles.numChip}>
                      <Text style={styles.numChipNum}>{result.name_numerology.personality_number}</Text>
                      <Text style={styles.numChipLabel}>{result.name_numerology.labels.personality}</Text>
                    </View>
                  </View>
                </Card>

                {/* Ebced */}
                <Card style={styles.ebcedCard}>
                  <Text style={styles.numTitle}>☽ {result.name_numerology.labels.ebced_title}</Text>
                  <View style={styles.numLifeRow}>
                    <Text style={styles.numLifeLabel}>{result.name_numerology.labels.total}</Text>
                    <Text style={[styles.numLifeValue, { color: '#C07AE0' }]}>{result.name_numerology.ebced.total}</Text>
                  </View>
                  <View style={[styles.numLifeRow, { borderBottomWidth: 0 }]}>
                    <Text style={styles.numLifeLabel}>{result.name_numerology.labels.reduced}</Text>
                    <Text style={[styles.numLifeValue, { fontSize: 20, color: '#C07AE0' }]}>{result.name_numerology.ebced.reduced}</Text>
                  </View>
                  {!!result.name_numerology.ebced.meaning && (
                    <Text style={styles.numMeaning}>{result.name_numerology.ebced.meaning}</Text>
                  )}
                </Card>

                {/* Kabala */}
                <Card style={styles.kabalaCard}>
                  <Text style={styles.numTitle}>✡ {result.name_numerology.labels.kabala_title}</Text>
                  <View style={styles.numLifeRow}>
                    <Text style={styles.numLifeLabel}>{result.name_numerology.labels.total}</Text>
                    <Text style={[styles.numLifeValue, { color: '#4A9EE0' }]}>{result.name_numerology.kabala.total}</Text>
                  </View>
                  <View style={[styles.numLifeRow, { borderBottomWidth: 0 }]}>
                    <Text style={styles.numLifeLabel}>{result.name_numerology.labels.reduced}</Text>
                    <Text style={[styles.numLifeValue, { fontSize: 20, color: '#4A9EE0' }]}>{result.name_numerology.kabala.reduced}</Text>
                  </View>
                  {!!result.name_numerology.kabala.meaning && (
                    <Text style={styles.numMeaning}>{result.name_numerology.kabala.meaning}</Text>
                  )}
                </Card>
              </>
            )}

            <GoldButton
              title={t('astrology.interpret', lang)}
              variant="warm"
              onPress={() => navigation.navigate('Chat', { analysisResult: result, lang })}
              style={styles.mt16}
            />
          </>
        )}
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
  back:   { ...typography.body, color: colors.gold, fontSize: 22 },
  title:  { ...typography.h3 },
  scroll: { padding: spacing.lg, paddingBottom: spacing.xxxl },
  input: {
    height: 48, backgroundColor: colors.surfaceAlt, borderRadius: radius.md,
    borderWidth: 1, borderColor: colors.border, paddingHorizontal: 14,
    color: colors.textPrimary, fontSize: 14, marginBottom: 12,
  },
  row:       { ...typography.bodyWarm, fontSize: 13, marginBottom: 4 },
  subRow:    { ...typography.bodyWarm, fontSize: 12, color: colors.textWarm, marginTop: 4 },
  signLabel: { ...typography.h3, color: colors.gold },
  spacer:    { width: 40 },
  mb16:      { marginBottom: 16 },
  mb12:      { marginBottom: 12 },
  mt12:      { marginTop: 12 },
  mt16:      { marginTop: 16 },
  signCard:  { alignItems: 'center' as const, marginBottom: 12 },
  signEmoji: { fontSize: 40, marginBottom: 4 },
  numCard:  { marginBottom: 12, borderLeftWidth: 3, borderLeftColor: colors.gold },
  nameCard:   { marginBottom: 12, borderLeftWidth: 3, borderLeftColor: colors.goldDark },
  ebcedCard:  { marginBottom: 12, borderLeftWidth: 3, borderLeftColor: '#C07AE0' },
  kabalaCard: { marginBottom: 12, borderLeftWidth: 3, borderLeftColor: '#4A9EE0' },
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
  numTitle: { ...typography.h3, marginBottom: spacing.sm },
  numLifeRow: {
    flexDirection: 'row' as const, justifyContent: 'space-between',
    alignItems: 'center', paddingVertical: spacing.sm,
    borderBottomWidth: 1, borderBottomColor: colors.border,
  },
  numLifeLabel: { ...typography.caption, color: colors.textMuted },
  numLifeValue: { ...typography.h2, color: colors.gold, fontSize: 22 },
  numMeaning: {
    ...typography.bodyWarm, fontSize: 13, color: colors.textWarm,
    marginVertical: spacing.sm, lineHeight: 20,
  },
  numChipRow: { flexDirection: 'row' as const, gap: spacing.sm, marginTop: spacing.sm },
  numChip: {
    flex: 1, backgroundColor: colors.surfaceAlt,
    borderRadius: radius.md, borderWidth: 1,
    borderColor: colors.border, alignItems: 'center' as const,
    paddingVertical: spacing.sm,
  },
  numChipNum:   { ...typography.h2, color: colors.gold, fontSize: 20 },
  numChipLabel: { ...typography.caption, color: colors.textMuted, fontSize: 10 },
});

export default AstrologyScreen;

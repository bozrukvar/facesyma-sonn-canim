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
      const data = await CoachAPI.birthAnalysis(birthDate, birthTime || undefined, lang);
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

            {/* Coach API fallback: key-value entries */}
            {result.astrology && (
              <>
                <SectionLabel>{t('astrology.section_astrology', lang)}</SectionLabel>
                <Card variant="gold">
                  {Object.entries(result.astrology).map(([k, v]) => (
                    <Text key={k} style={styles.row}>• {k}: {String(v)}</Text>
                  ))}
                </Card>
              </>
            )}
            {result.numerology && (
              <>
                <SectionLabel>{t('astrology.section_numerology', lang)}</SectionLabel>
                <Card>
                  {Object.entries(result.numerology).map(([k, v]) => (
                    <Text key={k} style={styles.row}>• {k}: {String(v)}</Text>
                  ))}
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
});

export default AstrologyScreen;

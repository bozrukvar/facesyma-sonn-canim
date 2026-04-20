// src/screens/AstrologyScreen.tsx
// Natal harita + yüz analizi entegrasyonu — yakında
import React, { useState } from 'react';
import { View, Text, StyleSheet, ScrollView, TouchableOpacity, TextInput } from 'react-native';
import { Card, GoldButton, SectionLabel } from '../components/ui';
import { CoachAPI } from '../services/api';
import theme from '../utils/theme';
import { useLanguage } from '../utils/LanguageContext';
import { t } from '../utils/i18n';

const AstrologyScreen: React.FC<{ navigation: any; route: any }> = ({ navigation, route }) => {
  const [birthDate, setBirthDate] = useState('');
  const [birthTime, setBirthTime] = useState('');
  const [result,    setResult]    = useState<any>(null);
  const [loading,   setLoading]   = useState(false);
  const { lang } = useLanguage();

  const calculate = async () => {
    if (!birthDate) return;
    setLoading(true);
    try {
      const data = await CoachAPI.birthAnalysis(birthDate, birthTime || undefined, lang);
      setResult(data);
    } catch (e) {
      console.error(e);
    } finally { setLoading(false); }
  };

  return (
    <View style={styles.container}>
      <View style={styles.header}>
        <TouchableOpacity onPress={() => navigation.goBack()}>
          <Text style={styles.back}>←</Text>
        </TouchableOpacity>
        <Text style={styles.title}>{t('astrology.title', lang)}</Text>
        <View style={{ width: 40 }} />
      </View>
      <ScrollView contentContainerStyle={styles.scroll} showsVerticalScrollIndicator={false}>
        <Card variant="warm" style={{ marginBottom: 16 }}>
          <SectionLabel>{t('astrology.birth_date', lang)}</SectionLabel>
          <TextInput
            style={styles.input}
            value={birthDate}
            onChangeText={setBirthDate}
            placeholder={t('astrology.birth_date_format', lang)}
            placeholderTextColor={theme.colors.textMuted}
            keyboardType="numeric"
          />
          <SectionLabel>{t('astrology.birth_time', lang)}</SectionLabel>
          <TextInput
            style={styles.input}
            value={birthTime}
            onChangeText={setBirthTime}
            placeholder={t('astrology.birth_time_format', lang)}
            placeholderTextColor={theme.colors.textMuted}
            keyboardType="numeric"
          />
          <GoldButton title={t('astrology.calculate', lang)} onPress={calculate} loading={loading} style={{ marginTop: 12 }} />
        </Card>

        {result && (
          <>
            <SectionLabel>{t('astrology.section_astrology', lang)}</SectionLabel>
            <Card variant="gold">
              {Object.entries(result.astrology || {}).map(([k, v]) => (
                <Text key={k} style={styles.row}>• {k}: {String(v)}</Text>
              ))}
            </Card>
            <SectionLabel>{t('astrology.section_numerology', lang)}</SectionLabel>
            <Card>
              {Object.entries(result.numerology || {}).map(([k, v]) => (
                <Text key={k} style={styles.row}>• {k}: {String(v)}</Text>
              ))}
            </Card>
            <GoldButton
              title={t('astrology.interpret', lang)}
              variant="warm"
              onPress={() => navigation.navigate('Chat', { analysisResult: result, lang })}
              style={{ marginTop: 16 }}
            />
          </>
        )}
      </ScrollView>
    </View>
  );
};

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: theme.colors.background },
  header: {
    flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between',
    paddingHorizontal: theme.spacing.lg, paddingTop: theme.spacing.lg + 44,
    paddingBottom: theme.spacing.md, borderBottomWidth: 1, borderBottomColor: theme.colors.border,
  },
  back:   { ...theme.typography.body, color: theme.colors.gold, fontSize: 22 },
  title:  { ...theme.typography.h3 },
  scroll: { padding: theme.spacing.lg, paddingBottom: theme.spacing.xxxl },
  input: {
    height: 48, backgroundColor: theme.colors.surfaceAlt, borderRadius: theme.radius.md,
    borderWidth: 1, borderColor: theme.colors.border, paddingHorizontal: 14,
    color: theme.colors.textPrimary, fontSize: 14, marginBottom: 12,
  },
  row: { ...theme.typography.bodyWarm, fontSize: 13, marginBottom: 4 },
});

export default AstrologyScreen;

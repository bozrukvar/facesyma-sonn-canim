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
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import type { ScreenProps } from '../navigation/types';

const DailyScreen = ({ navigation, route }: ScreenProps<'Daily'>) => {
  const insets = useSafeAreaInsets();
  const [daily,   setDaily]   = useState<string>('');
  const [loading, setLoading] = useState(true);
  const { lang } = useLanguage();

  useEffect(() => {
    AnalysisAPI.getDailyMotivation(lang)
      .then(d => setDaily(d?.message || d?.daily || ''))
      .catch(() => setDaily(t('common.generic_error', lang)))
      .finally(() => setLoading(false));
  }, [lang]);

  return (
    <View style={styles.container}>
      <View style={[styles.header, { paddingTop: insets.top + spacing.sm }]}>
        <TouchableOpacity onPress={() => navigation.goBack()}>
          <Text style={styles.back}>←</Text>
        </TouchableOpacity>
        <Text style={styles.title}>{t('daily.title', lang)}</Text>
        <View style={styles.spacer} />
      </View>
      <ScrollView contentContainerStyle={styles.scroll} showsVerticalScrollIndicator={false}>
        <Card variant="warm" style={styles.card}>
          <Text style={styles.cardEmoji}>🌟</Text>
          {loading
            ? <ActivityIndicator color={colors.warmAmber} />
            : <Text style={styles.dailyText}>{daily || t('daily.loading', lang)}</Text>
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
  card:      { marginBottom: 16 },
  cardEmoji: { fontSize: 40, textAlign: 'center' as const, marginBottom: 12 },
});

export default DailyScreen;

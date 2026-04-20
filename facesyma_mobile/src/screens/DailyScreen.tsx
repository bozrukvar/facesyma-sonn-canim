// src/screens/DailyScreen.tsx
// Günlük motivasyon + AI koçluk mesajı
import React, { useEffect, useState } from 'react';
import { View, Text, StyleSheet, ScrollView, TouchableOpacity, ActivityIndicator } from 'react-native';
import { Card, GoldButton, SectionLabel } from '../components/ui';
import { AnalysisAPI } from '../services/api';
import theme from '../utils/theme';
import { useLanguage } from '../utils/LanguageContext';
import { t } from '../utils/i18n';

const DailyScreen: React.FC<{ navigation: any; route: any }> = ({ navigation, route }) => {
  const [daily,   setDaily]   = useState<string>('');
  const [loading, setLoading] = useState(true);
  const { lang } = useLanguage();

  useEffect(() => {
    AnalysisAPI.getDailyMotivation(lang)
      .then(d => setDaily(d?.message || d?.daily || ''))
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  return (
    <View style={styles.container}>
      <View style={styles.header}>
        <TouchableOpacity onPress={() => navigation.goBack()}>
          <Text style={styles.back}>←</Text>
        </TouchableOpacity>
        <Text style={styles.title}>{t('daily.title', lang)}</Text>
        <View style={{ width: 40 }} />
      </View>
      <ScrollView contentContainerStyle={styles.scroll} showsVerticalScrollIndicator={false}>
        <Card variant="warm" style={{ marginBottom: 16 }}>
          <Text style={{ fontSize: 40, textAlign: 'center', marginBottom: 12 }}>🌟</Text>
          {loading
            ? <ActivityIndicator color={theme.colors.warmAmber} />
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
  container: { flex: 1, backgroundColor: theme.colors.background },
  header: {
    flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between',
    paddingHorizontal: theme.spacing.lg, paddingTop: theme.spacing.lg + 44,
    paddingBottom: theme.spacing.md, borderBottomWidth: 1, borderBottomColor: theme.colors.border,
  },
  back:      { ...theme.typography.body, color: theme.colors.gold, fontSize: 22 },
  title:     { ...theme.typography.h3 },
  scroll:    { padding: theme.spacing.lg, paddingBottom: theme.spacing.xxxl },
  dailyText: { ...theme.typography.bodyWarm, fontSize: 16, lineHeight: 26, textAlign: 'center' },
});

export default DailyScreen;

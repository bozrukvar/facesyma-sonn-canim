// src/screens/ArtMatchScreen.tsx
// Yüz → sanat eseri eşleşmesi
import React, { useState } from 'react';
import { View, Text, StyleSheet, ScrollView, TouchableOpacity, ActivityIndicator, Image, Alert } from 'react-native';
import { launchImageLibrary } from 'react-native-image-picker';
import { Card, GoldButton } from '../components/ui';
import { AnalysisAPI } from '../services/api';
import theme from '../utils/theme';
const { colors, spacing, typography, radius } = theme;
import { useLanguage } from '../utils/LanguageContext';
import { t } from '../utils/i18n';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { useDispatch } from 'react-redux';
import { AppDispatch } from '../store';
import { markModuleUsed } from '../store/authSlice';
import type { ScreenProps } from '../navigation/types';
import type { ArtMatchResult } from '../types/api';

const ArtMatchScreen = ({ navigation, route }: ScreenProps<'ArtMatch'>) => {
  const insets = useSafeAreaInsets();
  const dispatch = useDispatch<AppDispatch>();
  const [imageUri, setImageUri] = useState<string | null>(null);
  const [result,   setResult]   = useState<ArtMatchResult | null>(null);
  const [loading,  setLoading]  = useState(false);
  const { lang } = useLanguage();

  const pickImage = () => launchImageLibrary({ mediaType: 'photo', quality: 0.8 }, res => {
    if (res.assets?.[0]?.uri) { setImageUri(res.assets[0].uri); setResult(null); }
  });

  const analyze = async () => {
    if (!imageUri) return;
    setLoading(true);
    try {
      const data = await AnalysisAPI.analyzeArt(imageUri, lang);
      setResult(data);
      dispatch(markModuleUsed('art_match'));
    } catch (e: any) {
      Alert.alert(
        t('common.error', lang),
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
        <Text style={styles.title}>{t('artmatch.title', lang)}</Text>
        <View style={styles.spacer} />
      </View>
      <ScrollView contentContainerStyle={styles.scroll} showsVerticalScrollIndicator={false}>
        {imageUri
          ? <Image source={{ uri: imageUri }} style={styles.preview} />
          : (
            <Card style={styles.pickArea}>
              <Text style={styles.pickEmoji}>🎨</Text>
              <Text style={styles.pickText}>{t('artmatch.question', lang)}</Text>
            </Card>
          )
        }
        <GoldButton title={t('artmatch.choose_gallery', lang)} onPress={pickImage} variant="outline" style={styles.chooseBtn} />
        {imageUri && (
          <GoldButton title={t('artmatch.match', lang)} onPress={analyze} loading={loading} />
        )}
        {result && (
          <>
            <Text style={styles.gradeRow}>
              {t('artmatch.score', lang)}: {result.overall_score}  ·  {result.grade}
            </Text>
            {(result.matches ?? []).map(({ id: mId, rank, title, artist, year, museum, style: mStyle, similarity }) => (
              <Card key={mId} variant={rank === 1 ? 'gold' : undefined} style={styles.matchCard}>
                <Text style={styles.matchRank}>#{rank}</Text>
                <Text style={styles.matchTitle}>{title}</Text>
                <Text style={styles.matchSub}>{artist}  ·  {year}</Text>
                <Text style={styles.matchSub}>{museum}</Text>
                <Text style={styles.matchStyle}>{mStyle}</Text>
                <Text style={styles.matchSimilarity}>{t('artmatch.similarity', lang)}: {similarity}%</Text>
              </Card>
            ))}
            {result.message ? (
              <Card style={styles.messageCard}>
                <Text style={styles.matchSub}>{result.message}</Text>
              </Card>
            ) : null}
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
  back:       { ...typography.body, color: colors.gold, fontSize: 22 },
  title:      { ...typography.h3 },
  scroll:     { padding: spacing.lg, paddingBottom: spacing.xxxl },
  preview:    { width: '100%', height: 280, borderRadius: radius.xl, marginBottom: 16 },
  pickArea:       { alignItems: 'center', padding: spacing.xxxl, marginBottom: 16, borderStyle: 'dashed' },
  pickText:       { ...typography.body, textAlign: 'center', color: colors.textWarm },
  gradeRow:       { ...typography.label, color: colors.gold, textAlign: 'center', marginVertical: 12 },
  matchRank:      { ...typography.caption, color: colors.textMuted, marginBottom: 2 },
  matchTitle:     { ...typography.h3, fontSize: 16, marginBottom: 2 },
  matchSub:       { ...typography.bodyWarm, fontSize: 12, color: colors.textWarm, marginBottom: 2 },
  matchStyle:     { ...typography.caption, color: colors.textMuted, marginBottom: 4 },
  matchSimilarity:{ ...typography.label, color: colors.gold, fontSize: 13 },
  spacer:     { width: 40 },
  pickEmoji:  { fontSize: 48, marginBottom: 12 },
  chooseBtn:  { marginBottom: 10 },
  matchCard:  { marginBottom: 12 },
  messageCard:{ marginBottom: 16 },
});

export default ArtMatchScreen;

// src/screens/TwinsScreen.tsx
import React, { useState } from 'react';
import {
  View, Text, StyleSheet, ScrollView, TouchableOpacity,
  Dimensions, Alert, Image,
} from 'react-native';
import { launchImageLibrary } from 'react-native-image-picker';
import { AnalysisAPI } from '../services/api';
import { Card, ScoreRing, GoldButton, SectionLabel } from '../components/ui';
import theme from '../utils/theme';
const { colors, spacing, typography, radius } = theme;
import { useLanguage } from '../utils/LanguageContext';
import { t } from '../utils/i18n';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import type { ScreenProps } from '../navigation/types';
import type { TwinsResult } from '../types/api';

const { width } = Dimensions.get('window');
const PHOTO_SIZE = (width - spacing.lg * 2 - spacing.sm * 2) / 3;

const TwinsScreen = ({ navigation }: ScreenProps<'Twins'>) => {
  const insets = useSafeAreaInsets();
  const { lang } = useLanguage();
  const [photos,  setPhotos]  = useState<string[]>([]);
  const [result,  setResult]  = useState<TwinsResult | null>(null);
  const [loading, setLoading] = useState(false);

  const addPhoto = () => {
    const _len = photos.length;
    if (_len >= 5) { Alert.alert(t('twins.error_max', lang)); return; }
    launchImageLibrary({ mediaType:'photo', quality:0.8, selectionLimit:5 - _len }, res => {
      if (res.errorCode) {
        Alert.alert(t('common.error', lang), res.errorMessage || t('common.generic_error', lang));
        return;
      }
      if (res.assets) setPhotos(p => [...p, ...res.assets!.map(a => a.uri!)].slice(0, 5));
    });
  };

  const analyze = async () => {
    if (photos.length < 2) { Alert.alert(t('twins.error_min', lang)); return; }
    setLoading(true);
    try {
      const data = await AnalysisAPI.analyzeTwins(photos, lang);
      setResult(data);
    } catch (e: any) {
      Alert.alert(t('common.error', lang), e.response?.data?.detail || t('twins.error_generic', lang));
    } finally { setLoading(false); }
  };

  const photosLen  = photos.length;
  const groupScore = result?.group_score ?? 0;

  return (
    <View style={styles.container}>
      <View style={[styles.header, { paddingTop: insets.top + spacing.sm }]}>
        <TouchableOpacity onPress={() => navigation.goBack()}>
          <Text style={styles.back}>←</Text>
        </TouchableOpacity>
        <Text style={styles.headerTitle}>{t('twins.title', lang)}</Text>
        <View style={styles.spacer} />
      </View>

      <ScrollView contentContainerStyle={styles.scroll} showsVerticalScrollIndicator={false}>
        <Text style={styles.desc}>
          {t('twins.desc', lang)}
        </Text>

        <View style={styles.photoGrid}>
          {photos.map((uri, i) => (
            <View key={i} style={styles.photoWrap}>
              <Image source={{ uri }} style={styles.photo} />
              <TouchableOpacity
                style={styles.removeBtn}
                onPress={() => { setPhotos(p => p.filter((_,idx) => idx !== i)); setResult(null); }}
              >
                <Text style={styles.removeBtnIcon}>✕</Text>
              </TouchableOpacity>
              <Text style={styles.photoLabel}>{i + 1}. {t('twins.person', lang)}</Text>
            </View>
          ))}
          {photosLen < 5 && (
            <TouchableOpacity style={styles.addBtn} onPress={addPhoto}>
              <Text style={[styles.addBtnIcon, { color: colors.gold }]}>＋</Text>
              <Text style={[styles.addBtnText, { color: colors.gold }]}>{t('twins.add', lang)}</Text>
            </TouchableOpacity>
          )}
        </View>

        <Text style={styles.countText}>{photosLen}/5 {t('twins.photo_count', lang)} · {t('twins.photo_min', lang)}</Text>

        <GoldButton
          title={t('twins.analyze', lang)}
          onPress={analyze}
          loading={loading}
          disabled={photosLen < 2}
          style={styles.analyzeBtn}
        />

        {result && (
          <>
            <SectionLabel>{t('twins.group_harmony', lang)}</SectionLabel>
            <Card variant="gold" style={styles.scoreCard}>
              <ScoreRing score={Math.round(groupScore)} label={t('twins.harmony_score', lang)} size={100} />
              <Text style={styles.scoreText}>
                {groupScore >= 80 ? t('twins.perfect', lang) :
                 groupScore >= 60 ? t('twins.good', lang) :
                 groupScore >= 40 ? t('twins.moderate', lang) : t('twins.low', lang)}
              </Text>
            </Card>

            {result.pair_scores && Object.entries(result.pair_scores).map(([pair, score]) => {
              const [a, b] = pair.split('-').map(Number);
              return (
                <Card key={pair} style={styles.pairCard}>
                  <View style={styles.pairRow}>
                    <View style={styles.pairImgRow}>
                      {photos[a-1] && <Image source={{ uri: photos[a-1] }} style={styles.pairPhoto} />}
                      <Text style={styles.goldText}>⟷</Text>
                      {photos[b-1] && <Image source={{ uri: photos[b-1] }} style={styles.pairPhoto} />}
                    </View>
                    <View style={styles.flex1}>
                      <Text style={styles.pairLabel}>{a}. {t('twins.pair', lang)} {b}. {t('twins.person', lang)}</Text>
                      <Text style={styles.pairScore}>%{Math.round(Number(score) || 0)} {t('twins.pair_compatibility', lang)}</Text>
                    </View>
                    <ScoreRing score={Math.round(Number(score) || 0)} label="" size={52} />
                  </View>
                </Card>
              );
            })}

            <GoldButton
              title={t('twins.reset', lang)}
              onPress={() => { setPhotos([]); setResult(null); }}
              variant="outline"
              style={styles.resetBtn}
            />
          </>
        )}
      </ScrollView>
    </View>
  );
};

const styles = StyleSheet.create({
  container: { flex:1, backgroundColor: colors.background },
  header: {
    flexDirection:'row', alignItems:'center', justifyContent:'space-between',
    paddingHorizontal: spacing.lg,
    paddingBottom: spacing.md,
    borderBottomWidth:1, borderBottomColor: colors.border,
  },
  back:        { ...typography.body, color: colors.gold, fontSize:22 },
  headerTitle: { ...typography.h3, letterSpacing:0.5 },
  scroll:  { padding: spacing.lg, paddingBottom: spacing.xxxl },
  desc:    { ...typography.body, marginBottom: spacing.lg, color: colors.textWarm },
  photoGrid:  { flexDirection:'row', flexWrap:'wrap', gap: spacing.sm },
  photoWrap:  { width:PHOTO_SIZE, position:'relative' },
  photo:      { width:PHOTO_SIZE, height:PHOTO_SIZE, borderRadius: radius.md },
  removeBtn:  {
    position:'absolute', top:5, right:5,
    width:20, height:20, borderRadius:10,
    backgroundColor:'rgba(0,0,0,0.65)',
    alignItems:'center', justifyContent:'center',
  },
  photoLabel: { ...typography.caption, fontSize:10, textAlign:'center', marginTop:4 },
  addBtn: {
    width:PHOTO_SIZE, height:PHOTO_SIZE,
    borderRadius: radius.md,
    borderWidth:1, borderColor: colors.gold, borderStyle:'dashed',
    backgroundColor: colors.goldGlow,
    alignItems:'center', justifyContent:'center',
  },
  addBtnIcon: { fontSize:22, marginBottom:3 },
  addBtnText: { ...typography.goldLabel, fontSize:9 },
  countText:  { ...typography.caption, textAlign:'center', marginTop: spacing.sm },
  pairPhoto:  { width:44, height:44, borderRadius: radius.sm },
  pairLabel:  { ...typography.caption, marginBottom:2 },
  pairScore:  { ...typography.h3, fontSize:14, color: colors.gold },
  analyzeBtn: { marginTop: spacing.lg },
  scoreCard:  { alignItems: 'center' as const, paddingVertical: spacing.xl },
  scoreText:  { ...typography.bodyWarm, marginTop: spacing.md },
  goldText:   { color: colors.gold },
  pairCard:   { marginBottom: 8 },
  pairRow:    { flexDirection: 'row' as const, alignItems: 'center' as const, gap: 12 },
  pairImgRow: { flexDirection: 'row' as const, alignItems: 'center' as const, gap: 4 },
  flex1:      { flex: 1 },
  resetBtn:   { marginTop: spacing.xl },
  spacer:       { width: 40 },
  removeBtnIcon:{ color: '#fff', fontSize: 10, fontWeight: '700' as const },
});

export default TwinsScreen;

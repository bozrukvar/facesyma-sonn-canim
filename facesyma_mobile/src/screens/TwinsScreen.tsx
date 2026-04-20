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
import { useLanguage } from '../utils/LanguageContext';
import { t } from '../utils/i18n';

const { width } = Dimensions.get('window');
const PHOTO_SIZE = (width - theme.spacing.lg * 2 - theme.spacing.sm * 2) / 3;

const TwinsScreen: React.FC<{ navigation: any }> = ({ navigation }) => {
  const { lang } = useLanguage();
  const [photos,  setPhotos]  = useState<string[]>([]);
  const [result,  setResult]  = useState<any>(null);
  const [loading, setLoading] = useState(false);

  const addPhoto = () => {
    if (photos.length >= 5) { Alert.alert(t('twins.error_max', lang)); return; }
    launchImageLibrary({ mediaType:'photo', quality:0.8, selectionLimit:5 - photos.length }, res => {
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

  return (
    <View style={styles.container}>
      <View style={styles.header}>
        <TouchableOpacity onPress={() => navigation.goBack()}>
          <Text style={styles.back}>←</Text>
        </TouchableOpacity>
        <Text style={styles.headerTitle}>{t('twins.title', lang)}</Text>
        <View style={{ width:40 }} />
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
                <Text style={{ color:'#fff', fontSize:10, fontWeight:'700' }}>✕</Text>
              </TouchableOpacity>
              <Text style={styles.photoLabel}>{i + 1}. {t('twins.person', lang)}</Text>
            </View>
          ))}
          {photos.length < 5 && (
            <TouchableOpacity style={styles.addBtn} onPress={addPhoto}>
              <Text style={[styles.addBtnIcon, { color: theme.colors.gold }]}>＋</Text>
              <Text style={[styles.addBtnText, { color: theme.colors.gold }]}>{t('twins.add', lang)}</Text>
            </TouchableOpacity>
          )}
        </View>

        <Text style={styles.countText}>{photos.length}/5 {t('twins.photo_count', lang)} · {t('twins.photo_min', lang)}</Text>

        <GoldButton
          title={t('twins.analyze', lang)}
          onPress={analyze}
          loading={loading}
          disabled={photos.length < 2}
          style={{ marginTop: theme.spacing.lg }}
        />

        {result && (
          <>
            <SectionLabel>{t('twins.group_harmony', lang)}</SectionLabel>
            <Card variant="gold" style={{ alignItems:'center', paddingVertical: theme.spacing.xl }}>
              <ScoreRing score={Math.round(result.group_score || 0)} label={t('twins.harmony_score', lang)} size={100} />
              <Text style={{ ...theme.typography.bodyWarm, marginTop: theme.spacing.md }}>
                {result.group_score >= 80 ? t('twins.perfect', lang) :
                 result.group_score >= 60 ? t('twins.good', lang) :
                 result.group_score >= 40 ? t('twins.moderate', lang) : t('twins.low', lang)}
              </Text>
            </Card>

            {result.pair_scores && Object.entries(result.pair_scores).map(([pair, score]) => {
              const [a, b] = pair.split('-').map(Number);
              return (
                <Card key={pair} style={{ marginBottom:8 }}>
                  <View style={{ flexDirection:'row', alignItems:'center', gap:12 }}>
                    <View style={{ flexDirection:'row', alignItems:'center', gap:4 }}>
                      {photos[a-1] && <Image source={{ uri: photos[a-1] }} style={styles.pairPhoto} />}
                      <Text style={{ color: theme.colors.gold }}>⟷</Text>
                      {photos[b-1] && <Image source={{ uri: photos[b-1] }} style={styles.pairPhoto} />}
                    </View>
                    <View style={{ flex:1 }}>
                      <Text style={styles.pairLabel}>{a}. {t('twins.pair', lang)} {b}. {t('twins.person', lang)}</Text>
                      <Text style={styles.pairScore}>%{Math.round(score as number)} {t('twins.pair_compatibility', lang)}</Text>
                    </View>
                    <ScoreRing score={Math.round(score as number)} label="" size={52} />
                  </View>
                </Card>
              );
            })}

            <GoldButton
              title={t('twins.reset', lang)}
              onPress={() => { setPhotos([]); setResult(null); }}
              variant="outline"
              style={{ marginTop: theme.spacing.xl }}
            />
          </>
        )}
      </ScrollView>
    </View>
  );
};

const styles = StyleSheet.create({
  container: { flex:1, backgroundColor: theme.colors.background },
  header: {
    flexDirection:'row', alignItems:'center', justifyContent:'space-between',
    paddingHorizontal: theme.spacing.lg,
    paddingTop: theme.spacing.lg + 44,
    paddingBottom: theme.spacing.md,
    borderBottomWidth:1, borderBottomColor: theme.colors.border,
  },
  back:        { ...theme.typography.body, color: theme.colors.gold, fontSize:22 },
  headerTitle: { ...theme.typography.h3, letterSpacing:0.5 },
  scroll:  { padding: theme.spacing.lg, paddingBottom: theme.spacing.xxxl },
  desc:    { ...theme.typography.body, marginBottom: theme.spacing.lg, color: theme.colors.textWarm },
  photoGrid:  { flexDirection:'row', flexWrap:'wrap', gap: theme.spacing.sm },
  photoWrap:  { width:PHOTO_SIZE, position:'relative' },
  photo:      { width:PHOTO_SIZE, height:PHOTO_SIZE, borderRadius: theme.radius.md },
  removeBtn:  {
    position:'absolute', top:5, right:5,
    width:20, height:20, borderRadius:10,
    backgroundColor:'rgba(0,0,0,0.65)',
    alignItems:'center', justifyContent:'center',
  },
  photoLabel: { ...theme.typography.caption, fontSize:10, textAlign:'center', marginTop:4 },
  addBtn: {
    width:PHOTO_SIZE, height:PHOTO_SIZE,
    borderRadius: theme.radius.md,
    borderWidth:1, borderColor: theme.colors.gold, borderStyle:'dashed',
    backgroundColor: theme.colors.goldGlow,
    alignItems:'center', justifyContent:'center',
  },
  addBtnIcon: { fontSize:22, marginBottom:3 },
  addBtnText: { ...theme.typography.goldLabel, fontSize:9 },
  countText:  { ...theme.typography.caption, textAlign:'center', marginTop: theme.spacing.sm },
  pairPhoto:  { width:44, height:44, borderRadius: theme.radius.sm },
  pairLabel:  { ...theme.typography.caption, marginBottom:2 },
  pairScore:  { ...theme.typography.h3, fontSize:14, color: theme.colors.gold },
});

export default TwinsScreen;

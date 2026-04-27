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
import { useDispatch } from 'react-redux';
import { AppDispatch } from '../store';
import { markModuleUsed } from '../store/authSlice';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import type { ScreenProps } from '../navigation/types';
import type { TwinsResult, TwinsDimensions } from '../types/api';

const { width } = Dimensions.get('window');
const PHOTO_SIZE = (width - spacing.lg * 2 - spacing.sm * 2) / 3;

// ── Shared helpers ─────────────────────────────────────────────────────────────
interface DimRowProps { icon: string; label: string; score: number; }
const DimRow = ({ icon, label, score }: DimRowProps) => {
  const barW = width - spacing.lg * 2 - spacing.md * 2 - 32;
  const fill  = Math.max(0, Math.min(100, score));
  const color = fill >= 75 ? colors.gold : fill >= 50 ? '#c8a96e' : '#8c7654';
  return (
    <View style={dStyles.dimRow}>
      <Text style={dStyles.dimIcon}>{icon}</Text>
      <View style={dStyles.dimMid}>
        <Text style={dStyles.dimLabel}>{label}</Text>
        <View style={[dStyles.barBg, { width: barW }]}>
          <View style={[dStyles.barFill, { width: `${fill}%` as any, backgroundColor: color }]} />
        </View>
      </View>
      <Text style={[dStyles.dimScore, { color }]}>{fill}%</Text>
    </View>
  );
};

interface TagsRowProps { items: string[]; color: string; bgColor: string; }
const TagsRow = ({ items, color, bgColor }: TagsRowProps) => (
  <View style={dStyles.tags}>
    {items.map(s => (
      <View key={s} style={[dStyles.tag, { backgroundColor: bgColor, borderColor: color }]}>
        <Text style={[dStyles.tagText, { color }]}>{s}</Text>
      </View>
    ))}
  </View>
);

// ── Analysis Dimensions Card ────────────────────────────────────────────────────
interface DimensionsCardProps { dims: TwinsDimensions; lang: string; }
const DimensionsCard = ({ dims, lang }: DimensionsCardProps) => {
  const coreDims: { key: keyof TwinsDimensions; icon: string; labelKey: string }[] = [
    { key: 'face_similarity',        icon: '👤', labelKey: 'twins.face_similarity' },
    { key: 'character_compat',       icon: '🧠', labelKey: 'twins.char_compat' },
    { key: 'complementarity',        icon: '⚖️', labelKey: 'twins.complementarity' },
    { key: 'shared_strengths_score', icon: '💪', labelKey: 'twins.shared_strengths' },
    { key: 'eq_compat',              icon: '💬', labelKey: 'twins.eq_compat' },
  ];
  return (
    <Card style={dStyles.card}>
      {coreDims.map(({ key, icon, labelKey }) => (
        <DimRow key={key} icon={icon} label={t(labelKey, lang)} score={dims[key] as number} />
      ))}
    </Card>
  );
};

// ── Relationship Compatibility Card ────────────────────────────────────────────
const RelationshipCard = ({ dims, lang }: DimensionsCardProps) => {
  const relDims: { key: keyof TwinsDimensions; icon: string; labelKey: string }[] = [
    { key: 'romantic_compat',  icon: '💑', labelKey: 'twins.romantic_compat' },
    { key: 'social_compat',    icon: '🤝', labelKey: 'twins.social_compat' },
    { key: 'teamwork_compat',  icon: '🎯', labelKey: 'twins.teamwork_compat' },
  ];
  return (
    <Card style={dStyles.card}>
      {relDims.map(({ key, icon, labelKey }) => (
        <DimRow key={key} icon={icon} label={t(labelKey, lang)} score={dims[key] as number} />
      ))}
    </Card>
  );
};

// ── Traits Section ─────────────────────────────────────────────────────────────
interface TraitsSectionProps { dims: TwinsDimensions; lang: string; }
const TraitsSection = ({ dims, lang }: TraitsSectionProps) => {
  const hasPositive = (dims.positive_shared?.length ?? 0) > 0;
  const hasGrowth   = (dims.negative_shared?.length ?? 0) > 0;
  if (!hasPositive && !hasGrowth) return null;
  return (
    <Card style={dStyles.card}>
      {hasPositive && (
        <>
          <View style={dStyles.traitHeader}>
            <Text style={dStyles.traitIcon}>✅</Text>
            <Text style={dStyles.sectionTitle}>{t('twins.positive_shared_title', lang)}</Text>
          </View>
          <TagsRow items={dims.positive_shared} color="#4caf7d" bgColor="rgba(76,175,125,0.12)" />
        </>
      )}
      {hasGrowth && (
        <>
          <View style={[dStyles.traitHeader, hasPositive && { marginTop: spacing.md }]}>
            <Text style={dStyles.traitIcon}>🌱</Text>
            <Text style={dStyles.sectionTitle}>{t('twins.growth_areas_title', lang)}</Text>
          </View>
          <TagsRow items={dims.negative_shared} color="#e8a44a" bgColor="rgba(232,164,74,0.12)" />
        </>
      )}
    </Card>
  );
};

// ── Activities Card ─────────────────────────────────────────────────────────────
interface ActivitiesCardProps { suggestions: string[]; lang: string; }
const ActivitiesCard = ({ suggestions, lang }: ActivitiesCardProps) => {
  if (!suggestions?.length) return null;
  return (
    <Card style={dStyles.card}>
      {suggestions.map((act, i) => (
        <View key={i} style={dStyles.actRow}>
          <Text style={dStyles.actBullet}>◆</Text>
          <Text style={dStyles.actText}>{act}</Text>
        </View>
      ))}
    </Card>
  );
};

// ── Community Card ──────────────────────────────────────────────────────────────
interface CommunityCardProps { communityType: string; lang: string; onExplore: () => void; }
const CommunityCard = ({ communityType, lang, onExplore }: CommunityCardProps) => (
  <Card variant="gold" style={dStyles.communityCard}>
    <Text style={dStyles.communityType}>{communityType}</Text>
    <Text style={dStyles.communityDesc}>{t('twins.community_desc', lang)}</Text>
    <TouchableOpacity style={dStyles.communityBadge} onPress={onExplore} activeOpacity={0.85}>
      <Text style={dStyles.communityBadgeText}>{t('twins.community_join', lang)} →</Text>
    </TouchableOpacity>
  </Card>
);

const TwinsScreen = ({ navigation }: ScreenProps<'Twins'>) => {
  const insets = useSafeAreaInsets();
  const dispatch = useDispatch<AppDispatch>();
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
      dispatch(markModuleUsed('twins'));
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

            {result.dimensions && (
              <>
                <SectionLabel>{t('twins.dimensions', lang)}</SectionLabel>
                <DimensionsCard dims={result.dimensions} lang={lang} />

                <SectionLabel>{t('twins.relationship_compat', lang)}</SectionLabel>
                <RelationshipCard dims={result.dimensions} lang={lang} />

                {(result.dimensions.activity_suggestions?.length ?? 0) > 0 && (
                  <>
                    <SectionLabel>{t('twins.activities_title', lang)}</SectionLabel>
                    <ActivitiesCard suggestions={result.dimensions.activity_suggestions} lang={lang} />
                  </>
                )}

                {result.dimensions.community_type && (
                  <>
                    <SectionLabel>{t('twins.community_title', lang)}</SectionLabel>
                    <CommunityCard
                      communityType={result.dimensions.community_type}
                      lang={lang}
                      onExplore={() => navigation.navigate('Communities', { communityType: result.dimensions!.community_type })}
                    />
                  </>
                )}
              </>
            )}

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
              title={lang.startsWith('tr') ? '🤖 AI ile Konuş' : '🤖 Chat with AI'}
              onPress={() => navigation.navigate('Chat', { analysisResult: result, lang })}
              style={styles.aiChatBtn}
            />

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
  aiChatBtn:  { marginTop: spacing.lg },
  resetBtn:   { marginTop: spacing.md },
  spacer:       { width: 40 },
  removeBtnIcon:{ color: '#fff', fontSize: 10, fontWeight: '700' as const },
});

const dStyles = StyleSheet.create({
  card:            { marginBottom: spacing.md, padding: spacing.md },
  dimRow:          { flexDirection: 'row', alignItems: 'center', marginBottom: spacing.sm },
  dimIcon:         { fontSize: 18, width: 26 },
  dimMid:          { flex: 1, marginHorizontal: spacing.sm },
  dimLabel:        { ...typography.caption, marginBottom: 4 },
  barBg:           { height: 6, borderRadius: 3, backgroundColor: 'rgba(255,255,255,0.1)' },
  barFill:         { height: 6, borderRadius: 3 },
  dimScore:        { ...typography.goldLabel, width: 36, textAlign: 'right' as const },
  sectionTitle:    { ...typography.caption, color: colors.gold, marginTop: spacing.sm, marginBottom: spacing.sm },
  tags:            { flexDirection: 'row', flexWrap: 'wrap', gap: 6 },
  tag:             { borderWidth: 1, borderRadius: 12, paddingHorizontal: 10, paddingVertical: 3 },
  tagText:         { ...typography.caption, fontSize: 11 },
  traitHeader:     { flexDirection: 'row', alignItems: 'center', gap: 6 },
  traitIcon:       { fontSize: 14 },
  actRow:          { flexDirection: 'row', alignItems: 'flex-start', gap: 8, marginBottom: 8 },
  actBullet:       { color: colors.gold, fontSize: 8, marginTop: 5 },
  actText:         { ...typography.body, flex: 1, fontSize: 13 },
  communityCard:   { marginBottom: spacing.md, padding: spacing.lg, alignItems: 'center' as const },
  communityType:   { ...typography.h2, fontSize: 20, textAlign: 'center' as const, marginBottom: spacing.sm },
  communityDesc:   { ...typography.caption, textAlign: 'center' as const, color: colors.textWarm, marginBottom: spacing.md },
  communityBadge:  {
    borderWidth: 1, borderColor: colors.gold, borderRadius: 20,
    paddingHorizontal: spacing.lg, paddingVertical: spacing.sm,
  },
  communityBadgeText: { ...typography.goldLabel, fontSize: 12 },
});

export default TwinsScreen;

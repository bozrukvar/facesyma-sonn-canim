// src/screens/ArtMatchScreen.tsx
import React, { useState, useCallback } from 'react';
import {
  View, Text, StyleSheet, ScrollView, TouchableOpacity,
  Image, Alert, ActivityIndicator,
} from 'react-native';
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

const CLUSTER_COLORS: Record<string, string> = {
  leadership:   '#E53935',
  intelligence: '#1E88E5',
  creativity:   '#8E24AA',
  patience:     '#00897B',
  strength:     '#FB8C00',
  empathy:      '#D81B60',
  mystery:      '#5E35B1',
  discipline:   '#546E7A',
  social:       '#43A047',
  charisma:     '#F9A825',
};

const GRADE_COLORS: Record<string, string> = {
  'A+': '#FFD700', A: '#FFC107', 'B+': '#4CAF50', B: '#2196F3', C: '#9E9E9E',
};

// ── Artwork image with loading + error fallback ──────────────────────────────
const ArtworkImage = ({ uri, emoji }: { uri: string; emoji: string }) => {
  const [imgFailed, setImgFailed] = useState(false);
  const [imgLoading, setImgLoading] = useState(true);

  if (!uri || imgFailed) {
    return (
      <View style={styles.artImagePlaceholder}>
        <Text style={styles.artEmoji}>{emoji || '🖼'}</Text>
      </View>
    );
  }

  return (
    <View style={styles.artImageWrap}>
      {imgLoading && (
        <View style={styles.artImageLoading}>
          <ActivityIndicator color={colors.gold} size="small" />
        </View>
      )}
      <Image
        source={{ uri }}
        style={[styles.artImage, imgLoading && { opacity: 0 }]}
        resizeMode="cover"
        onLoad={() => setImgLoading(false)}
        onError={() => { setImgFailed(true); setImgLoading(false); }}
      />
    </View>
  );
};

// ── Similarity progress bar ──────────────────────────────────────────────────
const SimilarityBar = ({ value, color }: { value: number; color: string }) => (
  <View style={styles.barBg}>
    <View style={[styles.barFill, { width: `${Math.min(value, 100)}%` as any, backgroundColor: color }]} />
  </View>
);

// ── Main screen ──────────────────────────────────────────────────────────────
const ArtMatchScreen = ({ navigation }: ScreenProps<'ArtMatch'>) => {
  const insets = useSafeAreaInsets();
  const dispatch = useDispatch<AppDispatch>();
  const [imageUri, setImageUri] = useState<string | null>(null);
  const [result,   setResult]   = useState<ArtMatchResult | null>(null);
  const [loading,  setLoading]  = useState(false);
  const { lang } = useLanguage();

  const pickImage = useCallback(() =>
    launchImageLibrary({ mediaType: 'photo', quality: 0.8 }, res => {
      if (res.assets?.[0]?.uri) { setImageUri(res.assets[0].uri); setResult(null); }
    }), []);

  const analyze = useCallback(async () => {
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
  }, [imageUri, lang, dispatch]);

  const gradeColor = result?.grade ? (GRADE_COLORS[result.grade] ?? colors.gold) : colors.gold;

  return (
    <View style={styles.container}>
      {/* Header */}
      <View style={[styles.header, { paddingTop: insets.top + spacing.sm }]}>
        <TouchableOpacity onPress={() => navigation.goBack()} hitSlop={{ top: 10, bottom: 10, left: 10, right: 10 }}
          accessibilityRole="button"
          accessibilityLabel={t('artmatch.title', lang)}
        >
          <Text style={styles.back}>←</Text>
        </TouchableOpacity>
        <Text style={styles.title}>{t('artmatch.title', lang)}</Text>
        <View style={styles.spacer} />
      </View>

      <ScrollView contentContainerStyle={styles.scroll} showsVerticalScrollIndicator={false}>

        {/* Photo preview / pick area */}
        {imageUri
          ? <Image source={{ uri: imageUri }} style={styles.preview} resizeMode="cover" />
          : (
            <Card style={styles.pickArea}>
              <Text style={styles.pickEmoji}>🎨</Text>
              <Text style={styles.pickText}>{t('artmatch.question', lang)}</Text>
            </Card>
          )
        }

        <GoldButton
          title={t('artmatch.choose_gallery', lang)}
          onPress={pickImage}
          variant="outline"
          style={styles.chooseBtn}
        />
        {imageUri && (
          <GoldButton
            title={t('artmatch.match', lang)}
            onPress={analyze}
            loading={loading}
          />
        )}

        {/* Results */}
        {result && (
          <>
            {/* Score header card */}
            <Card variant="gold" style={styles.scoreCard}>
              <View style={styles.scoreRow}>
                <View style={styles.scoreLeft}>
                  <Text style={styles.scoreLabel}>{t('artmatch.score', lang)}</Text>
                  <Text style={styles.scoreValue}>{result.overall_score}</Text>
                </View>
                <View style={[styles.gradeBadge, { backgroundColor: gradeColor }]}>
                  <Text style={styles.gradeText}>{result.grade}</Text>
                </View>
              </View>
              {result.message ? (
                <Text style={styles.scoreMessage}>{result.message}</Text>
              ) : null}
            </Card>

            {/* Match cards */}
            {(result.matches ?? []).map(match => {
              const {
                id: mId, rank, title, artist, year, museum,
                style: mStyle, similarity, image_url, reason, primary_cluster, emoji,
              } = match;
              const clusterColor = CLUSTER_COLORS[primary_cluster ?? ''] ?? colors.gold as string;
              const isTop = rank === 1;

              return (
                <Card key={mId} variant={isTop ? 'gold' : undefined} style={styles.matchCard}>
                  {/* Artwork image */}
                  <ArtworkImage uri={image_url ?? ''} emoji={emoji ?? '🖼'} />

                  {/* Cluster badge + rank row */}
                  <View style={styles.badgeRow}>
                    {primary_cluster ? (
                      <View style={[styles.clusterBadge, { backgroundColor: clusterColor }]}>
                        <Text style={styles.clusterBadgeText}>
                          {t(`cluster.${primary_cluster}`, lang)}
                        </Text>
                      </View>
                    ) : null}
                    <View style={styles.rankBadge}>
                      <Text style={styles.rankText}>#{rank}</Text>
                    </View>
                  </View>

                  {/* Title */}
                  <Text style={styles.matchTitle}>{title}</Text>
                  <Text style={styles.matchArtist}>{artist}  ·  {year}</Text>
                  {museum ? <Text style={styles.matchSub}>{museum}</Text> : null}
                  {mStyle ? <Text style={styles.matchStyle}>{mStyle}</Text> : null}

                  {/* Similarity bar */}
                  <View style={styles.simRow}>
                    <Text style={[styles.simLabel, { color: clusterColor }]}>
                      {t('artmatch.similarity', lang)}: {similarity}%
                    </Text>
                  </View>
                  <SimilarityBar value={similarity} color={clusterColor} />

                  {/* Reason */}
                  {reason ? (
                    <Text style={styles.reason}>"{reason}"</Text>
                  ) : null}
                </Card>
              );
            })}
          </>
        )}
      </ScrollView>
    </View>
  );
};

const styles = StyleSheet.create({
  container:    { flex: 1, backgroundColor: colors.background },
  header: {
    flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between',
    paddingHorizontal: spacing.lg,
    paddingBottom: spacing.md, borderBottomWidth: 1, borderBottomColor: colors.border,
  },
  back:         { ...typography.body, color: colors.gold, fontSize: 22 },
  title:        { ...typography.h3 },
  spacer:       { width: 40 },
  scroll:       { padding: spacing.lg, paddingBottom: spacing.xxxl },
  preview:      { width: '100%', height: 260, borderRadius: radius.xl, marginBottom: 16 },
  pickArea:     { alignItems: 'center', padding: spacing.xxxl, marginBottom: 16 },
  pickEmoji:    { fontSize: 56, marginBottom: 12 },
  pickText:     { ...typography.body, textAlign: 'center', color: colors.textWarm },
  chooseBtn:    { marginBottom: 10 },

  // Score card
  scoreCard:    { marginTop: 16, marginBottom: 8, padding: spacing.lg },
  scoreRow:     { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', marginBottom: 6 },
  scoreLeft:    { flex: 1 },
  scoreLabel:   { ...typography.caption, color: colors.textMuted, marginBottom: 2 },
  scoreValue:   { fontSize: 36, fontWeight: '800', color: colors.gold },
  gradeBadge:   { width: 52, height: 52, borderRadius: 26, alignItems: 'center', justifyContent: 'center' },
  gradeText:    { fontSize: 20, fontWeight: '800', color: '#000' },
  scoreMessage: { ...typography.bodyWarm, fontSize: 13, color: colors.textWarm, marginTop: 4 },

  // Match card
  matchCard:    { marginBottom: 14 },
  artImageWrap: { width: '100%', height: 200, borderRadius: radius.md, overflow: 'hidden', marginBottom: 12, backgroundColor: colors.surface },
  artImage:     { width: '100%', height: '100%' },
  artImageLoading: { ...StyleSheet.absoluteFillObject, alignItems: 'center', justifyContent: 'center', backgroundColor: colors.surface },
  artImagePlaceholder: {
    width: '100%', height: 160, borderRadius: radius.md,
    backgroundColor: colors.surface, alignItems: 'center', justifyContent: 'center',
    marginBottom: 12,
  },
  artEmoji:     { fontSize: 64 },

  badgeRow:     { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', marginBottom: 8 },
  clusterBadge: { borderRadius: 12, paddingHorizontal: 10, paddingVertical: 3 },
  clusterBadgeText: { color: '#fff', fontSize: 11, fontWeight: '600' },
  rankBadge:    { borderRadius: 12, paddingHorizontal: 10, paddingVertical: 3, backgroundColor: colors.border },
  rankText:     { fontSize: 11, fontWeight: '700', color: colors.textMuted },

  matchTitle:   { fontSize: 17, fontWeight: '700', color: colors.text, marginBottom: 3 },
  matchArtist:  { ...typography.bodyWarm, fontSize: 13, color: colors.textWarm, marginBottom: 2 },
  matchSub:     { ...typography.caption, fontSize: 11, color: colors.textMuted, marginBottom: 2 },
  matchStyle:   { ...typography.caption, fontSize: 11, color: colors.textMuted, fontStyle: 'italic', marginBottom: 8 },

  simRow:       { flexDirection: 'row', justifyContent: 'space-between', marginBottom: 4 },
  simLabel:     { fontSize: 12, fontWeight: '600' },
  barBg:        { height: 6, borderRadius: 3, backgroundColor: colors.surface, marginBottom: 10 },
  barFill:      { height: 6, borderRadius: 3 },

  reason:       { ...typography.body, fontSize: 13, color: colors.textWarm, fontStyle: 'italic', marginTop: 4, lineHeight: 19 },
});

export default ArtMatchScreen;

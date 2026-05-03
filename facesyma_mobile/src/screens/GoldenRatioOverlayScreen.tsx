// src/screens/GoldenRatioOverlayScreen.tsx
import React, { useState, useEffect } from 'react';
import {
  View, Text, StyleSheet, ScrollView, Image,
  TouchableOpacity, ActivityIndicator, Alert, Dimensions,
} from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import theme from '../utils/theme';
const { colors, spacing, typography, radius } = theme;
import { useLanguage } from '../utils/LanguageContext';
import { t } from '../utils/i18n';
import { AnalysisAPI } from '../services/api';
import type { ScreenProps } from '../navigation/types';

const { width: SCREEN_W } = Dimensions.get('window');

type GoldenRatioItem = { name: string; ratio: number; score: number; status: string };

const GoldenRatioOverlayScreen: React.FC<ScreenProps<'GoldenRatioOverlay'>> = ({ navigation, route }) => {
  const { imageUri, lang: routeLang, goldenScore, goldenGrade } = route.params;
  const insets   = useSafeAreaInsets();
  const { lang } = useLanguage();
  const activeLang = routeLang || lang;

  const [loading,      setLoading]      = useState(true);
  const [overlayB64,   setOverlayB64]   = useState<string>('');
  const [ratios,       setRatios]       = useState<GoldenRatioItem[]>([]);
  const [score,        setScore]        = useState(goldenScore);
  const [grade,        setGrade]        = useState(goldenGrade);

  useEffect(() => {
    (async () => {
      try {
        const res = await AnalysisAPI.analyzeGoldenOverlay(imageUri, activeLang);
        setOverlayB64(res?.image_b64 ?? '');
        setRatios(res?.features?.golden_ratios ?? []);
        if (res?.score != null) setScore(Math.round(res.score));
        if (res?.grade)         setGrade(res.grade);
      } catch {
        Alert.alert(t('common.error', activeLang), t('common.generic_error', activeLang));
      } finally {
        setLoading(false);
      }
    })();
  }, [imageUri, activeLang]);

  const gradeColor = score >= 85 ? '#4CAF50' : score >= 70 ? colors.gold : '#FF9800';

  return (
    <View style={[styles.container, { paddingTop: insets.top }]}>
      {/* Header */}
      <View style={styles.header}>
        <TouchableOpacity onPress={() => navigation.goBack()} style={styles.backBtn}>
          <Text style={styles.backTxt}>←</Text>
        </TouchableOpacity>
        <Text style={styles.title}>{t('golden.overlay_title', activeLang)}</Text>
        <View style={styles.gradeBox}>
          <Text style={[styles.gradeTxt, { color: gradeColor }]}>{grade}</Text>
        </View>
      </View>

      {loading ? (
        <View style={styles.center}>
          <ActivityIndicator color={colors.gold} size="large" />
        </View>
      ) : (
        <ScrollView contentContainerStyle={styles.scroll} showsVerticalScrollIndicator={false}>
          {/* Score pill */}
          <View style={styles.scorePill}>
            <Text style={styles.scoreLabel}>φ</Text>
            <Text style={[styles.scoreVal, { color: gradeColor }]}>{score}</Text>
            <Text style={styles.scoreMax}>/100</Text>
          </View>

          {/* Annotated overlay image */}
          {overlayB64 ? (
            <Image
              source={{ uri: overlayB64 }}
              style={styles.overlayImg}
              resizeMode="contain"
            />
          ) : (
            <Image
              source={{ uri: imageUri }}
              style={styles.overlayImg}
              resizeMode="contain"
            />
          )}

          {/* Measurement list */}
          {ratios.length > 0 && (
            <View style={styles.ratioSection}>
              {ratios.map((item, i) => {
                const isGolden = item.status === 'golden';
                const badgeColor = isGolden ? '#4CAF50' : '#FF9800';
                return (
                  <View key={i} style={styles.ratioRow}>
                    <View style={styles.ratioLeft}>
                      <Text style={styles.ratioName}>{item.name}</Text>
                      <Text style={styles.ratioVal}>{Number(item.ratio).toFixed(3)}</Text>
                    </View>
                    <View style={styles.ratioRight}>
                      <View style={[styles.statusBadge, { backgroundColor: badgeColor + '22', borderColor: badgeColor }]}>
                        <Text style={[styles.statusTxt, { color: badgeColor }]}>
                          {isGolden
                            ? t('golden.status_golden', activeLang)
                            : t('golden.status_adjustable', activeLang)}
                        </Text>
                      </View>
                      <Text style={styles.ratioScore}>{item.score}</Text>
                    </View>
                  </View>
                );
              })}
            </View>
          )}

          {/* Before/After CTA */}
          <TouchableOpacity
            style={styles.transformBtn}
            onPress={() => navigation.navigate('GoldenTransform', {
              imageUri,
              lang: activeLang,
              realMeasurements: ratios,
            })}
            activeOpacity={0.85}
          >
            <Text style={styles.transformBtnTxt}>✨ {t('golden.view_transform', activeLang)}</Text>
          </TouchableOpacity>

          <View style={{ height: spacing.xl }} />
        </ScrollView>
      )}
    </View>
  );
};

const styles = StyleSheet.create({
  container:    { flex: 1, backgroundColor: colors.background },
  header: {
    flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between',
    paddingHorizontal: spacing.lg, paddingVertical: spacing.md,
    borderBottomWidth: 1, borderColor: colors.border,
  },
  backBtn:      { width: 36, height: 36, justifyContent: 'center' },
  backTxt:      { ...typography.h2, color: colors.gold },
  title:        { ...typography.h2, color: colors.textPrimary, flex: 1, textAlign: 'center' as const },
  gradeBox:     { width: 36, alignItems: 'flex-end' as const },
  gradeTxt:     { ...typography.h2, fontWeight: '700' as const, fontSize: 18 },
  center:       { flex: 1, alignItems: 'center', justifyContent: 'center' },
  scroll:       { padding: spacing.lg, gap: spacing.md },
  scorePill: {
    flexDirection: 'row', alignItems: 'baseline', justifyContent: 'center',
    gap: 4, marginBottom: spacing.sm,
  },
  scoreLabel:   { ...typography.h2, color: colors.gold, fontSize: 22 },
  scoreVal:     { fontSize: 42, fontWeight: '700' as const },
  scoreMax:     { ...typography.body, color: colors.textMuted, fontSize: 16 },
  overlayImg: {
    width: SCREEN_W - spacing.lg * 2,
    height: SCREEN_W - spacing.lg * 2,
    borderRadius: radius.lg,
    backgroundColor: colors.surface,
    alignSelf: 'center' as const,
  },
  ratioSection: {
    backgroundColor: colors.surface, borderRadius: radius.lg,
    borderWidth: 1, borderColor: colors.border,
    padding: spacing.md, gap: spacing.sm,
    marginTop: spacing.sm,
  },
  ratioRow: {
    flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between',
    paddingVertical: spacing.xs,
    borderBottomWidth: 1, borderColor: colors.border,
  },
  ratioLeft:    { flex: 1, gap: 2 },
  ratioName:    { ...typography.label, color: colors.textPrimary, fontSize: 13 },
  ratioVal:     { ...typography.caption, color: colors.textMuted, fontSize: 11 },
  ratioRight:   { flexDirection: 'row', alignItems: 'center', gap: spacing.sm },
  statusBadge: {
    borderWidth: 1, borderRadius: radius.full,
    paddingHorizontal: spacing.sm, paddingVertical: 2,
  },
  statusTxt:    { ...typography.caption, fontSize: 10, fontWeight: '700' as const },
  ratioScore:   { ...typography.label, color: colors.gold, fontSize: 13, minWidth: 28, textAlign: 'right' as const },
  transformBtn: {
    backgroundColor: colors.gold, borderRadius: radius.md,
    paddingVertical: spacing.md, alignItems: 'center' as const,
    marginTop: spacing.md,
  },
  transformBtnTxt: { ...typography.label, color: '#000', fontWeight: '700' as const, fontSize: 14 },
});

export default GoldenRatioOverlayScreen;

// src/screens/GoldenTransformScreen.tsx
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

type Adjustment = {
  feature: string;
  current: string;
  optimal: string;
  score?: number;
  status?: string;
  impact?: string;
  procedure?: string;
};

const GoldenTransformScreen: React.FC<ScreenProps<'GoldenTransform'>> = ({ navigation, route }) => {
  const { imageUri, lang: routeLang, realMeasurements } = route.params;
  const insets   = useSafeAreaInsets();
  const { lang } = useLanguage();
  const activeLang = routeLang || lang;

  const [loading,      setLoading]      = useState(true);
  const [comparisonB64, setComparisonB64] = useState<string>('');
  const [adjustments,  setAdjustments]  = useState<Adjustment[]>([]);
  const [kvkkPoints,   setKvkkPoints]   = useState<string[]>([]);

  useEffect(() => {
    (async () => {
      try {
        const res = await AnalysisAPI.analyzeGoldenTransform(imageUri, activeLang, realMeasurements);
        setComparisonB64(res?.comparison_b64 ?? '');
        setAdjustments(res?.transformation_guide?.adjustments ?? []);
        setKvkkPoints(res?.kvkk_disclaimer?.points ?? []);
      } catch {
        Alert.alert(t('common.error', activeLang), t('common.generic_error', activeLang));
      } finally {
        setLoading(false);
      }
    })();
  }, [imageUri, activeLang]);

  const getStatusColor = (status?: string) =>
    status === 'golden' ? '#4CAF50' : '#FF9800';

  return (
    <View style={[styles.container, { paddingTop: insets.top }]}>
      {/* Header */}
      <View style={styles.header}>
        <TouchableOpacity onPress={() => navigation.goBack()} style={styles.backBtn}>
          <Text style={styles.backTxt}>←</Text>
        </TouchableOpacity>
        <Text style={styles.title}>{t('golden.transform_title', activeLang)}</Text>
        <View style={{ width: 36 }} />
      </View>

      {loading ? (
        <View style={styles.center}>
          <ActivityIndicator color={colors.gold} size="large" />
        </View>
      ) : (
        <ScrollView contentContainerStyle={styles.scroll} showsVerticalScrollIndicator={false}>
          {/* Before/After comparison image */}
          {comparisonB64 ? (
            <Image
              source={{ uri: comparisonB64 }}
              style={styles.comparisonImg}
              resizeMode="contain"
            />
          ) : null}

          {/* Adjustments list */}
          {adjustments.length > 0 && (
            <View style={styles.adjustSection}>
              {adjustments.map((adj, i) => {
                const statusColor = getStatusColor(adj.status);
                return (
                  <View key={i} style={styles.adjustRow}>
                    <View style={styles.adjustHeader}>
                      <Text style={styles.adjustFeature}>{adj.feature}</Text>
                      <View style={[styles.adjustBadge, { borderColor: statusColor, backgroundColor: statusColor + '22' }]}>
                        <Text style={[styles.adjustBadgeTxt, { color: statusColor }]}>
                          {adj.status === 'golden'
                            ? t('golden.status_golden', activeLang)
                            : t('golden.status_adjustable', activeLang)}
                        </Text>
                      </View>
                    </View>

                    {/* current → optimal arrow */}
                    <View style={styles.ratioArrowRow}>
                      <View style={styles.ratioBox}>
                        <Text style={styles.ratioBoxLabel}>
                          {activeLang === 'tr' ? 'Mevcut' : 'Current'}
                        </Text>
                        <Text style={[styles.ratioBoxVal, { color: statusColor }]}>{adj.current}</Text>
                      </View>
                      <Text style={styles.arrow}>→</Text>
                      <View style={styles.ratioBox}>
                        <Text style={styles.ratioBoxLabel}>
                          {activeLang === 'tr' ? 'Optimal (φ)' : 'Optimal (φ)'}
                        </Text>
                        <Text style={[styles.ratioBoxVal, { color: colors.gold }]}>{adj.optimal}</Text>
                      </View>
                    </View>

                    {adj.procedure ? (
                      <Text style={styles.procedureTxt}>{adj.procedure}</Text>
                    ) : null}
                  </View>
                );
              })}
            </View>
          )}

          {/* KVKK disclaimer */}
          {kvkkPoints.length > 0 && (
            <View style={styles.kvkkBox}>
              <Text style={styles.kvkkTitle}>{t('golden.kvkk_title', activeLang)}</Text>
              {kvkkPoints.map((pt, i) => (
                <Text key={i} style={styles.kvkkPoint}>{pt}</Text>
              ))}
            </View>
          )}

          <View style={{ height: spacing.xl }} />
        </ScrollView>
      )}
    </View>
  );
};

const styles = StyleSheet.create({
  container:  { flex: 1, backgroundColor: colors.background },
  header: {
    flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between',
    paddingHorizontal: spacing.lg, paddingVertical: spacing.md,
    borderBottomWidth: 1, borderColor: colors.border,
  },
  backBtn:    { width: 36, height: 36, justifyContent: 'center' },
  backTxt:    { ...typography.h2, color: colors.gold },
  title:      { ...typography.h2, color: colors.textPrimary, flex: 1, textAlign: 'center' as const },
  center:     { flex: 1, alignItems: 'center', justifyContent: 'center' },
  scroll:     { padding: spacing.lg, gap: spacing.md },
  comparisonImg: {
    width: SCREEN_W - spacing.lg * 2,
    height: (SCREEN_W - spacing.lg * 2) * 0.55,
    borderRadius: radius.lg,
    backgroundColor: colors.surface,
    alignSelf: 'center' as const,
  },
  adjustSection: {
    backgroundColor: colors.surface, borderRadius: radius.lg,
    borderWidth: 1, borderColor: colors.border,
    padding: spacing.md, gap: spacing.md,
  },
  adjustRow: {
    gap: spacing.xs,
    paddingBottom: spacing.sm,
    borderBottomWidth: 1, borderColor: colors.border,
  },
  adjustHeader: {
    flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between',
  },
  adjustFeature:   { ...typography.label, color: colors.textPrimary, fontSize: 13 },
  adjustBadge: {
    borderWidth: 1, borderRadius: radius.full,
    paddingHorizontal: spacing.sm, paddingVertical: 2,
  },
  adjustBadgeTxt:  { ...typography.caption, fontSize: 10, fontWeight: '700' as const },
  ratioArrowRow: {
    flexDirection: 'row', alignItems: 'center', gap: spacing.sm, paddingVertical: spacing.xs,
  },
  ratioBox: {
    flex: 1, backgroundColor: colors.background, borderRadius: radius.sm,
    padding: spacing.sm, alignItems: 'center' as const,
  },
  ratioBoxLabel:   { ...typography.caption, color: colors.textMuted, fontSize: 10 },
  ratioBoxVal:     { ...typography.h2, fontSize: 16, fontWeight: '700' as const },
  arrow:           { ...typography.h2, color: colors.textMuted, fontSize: 18 },
  procedureTxt:    { ...typography.caption, color: colors.textSecondary, fontSize: 11, lineHeight: 16 },
  kvkkBox: {
    backgroundColor: colors.surface, borderRadius: radius.md,
    borderWidth: 1, borderColor: colors.border,
    padding: spacing.md, gap: spacing.xs,
    marginTop: spacing.sm,
  },
  kvkkTitle:       { ...typography.label, color: colors.gold, fontSize: 12, marginBottom: spacing.xs },
  kvkkPoint:       { ...typography.caption, color: colors.textMuted, fontSize: 10, lineHeight: 16 },
});

export default GoldenTransformScreen;

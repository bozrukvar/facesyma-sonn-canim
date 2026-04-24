/**
 * src/screens/FashionScreen.tsx
 * ============================
 * Kişilik analizi sonucuna göre özelleştirilmiş giyim tavsiyeleri.
 * Mevsim ve kategori seçimli.
 */

import React, { useState, useEffect, useMemo } from 'react';
import {
  View, Text, StyleSheet, ScrollView, TouchableOpacity,
  ActivityIndicator, Alert,
} from 'react-native';
import { CoachAPI } from '../services/api';
import { Card, SectionLabel, Badge } from '../components/ui';
import theme from '../utils/theme';
const { colors } = theme;
import { useLanguage } from '../utils/LanguageContext';
import { t } from '../utils/i18n';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import type { ScreenProps } from '../navigation/types';
import type { AnalysisResult } from '../types/api';

const getSeasons = (lang: string) => [
  { id: 'ilkbahar', emoji: '🌸', label: t('fashion.spring', lang) },
  { id: 'yaz', emoji: '☀️', label: t('fashion.summer', lang) },
  { id: 'sonbahar', emoji: '🍂', label: t('fashion.autumn', lang) },
  { id: 'kis', emoji: '❄️', label: t('fashion.winter', lang) },
];

const getCategories = (lang: string) => [
  { id: 'gunluk', emoji: '👕', label: t('fashion.daily', lang) },
  { id: 'spor', emoji: '🏃', label: t('fashion.sport', lang) },
  { id: 'resmi', emoji: '👔', label: t('fashion.formal', lang) },
  { id: 'davet', emoji: '🎉', label: t('fashion.party', lang) },
];

interface FashionData {
  dominant_sifatlar: string[];
  stil_profili: string;
  coaching?: {
    felsefe: string;
    kombinasyon: string;
    renk_psikolojisi: string;
    yaşam_uyarlamasi: string;
  };
  yuz_tipi: string;
  renk_paleti: {
    ana: string[];
    vurgu: string[];
    kacin: string[];
  };
  yuz_sekli_notu: string;
  mevsim_onerileri: {
    [key: string]: {
      [key: string]: {
        parca: string[];
        kumas: string[];
        kesim: string;
        aksesuar: string[];
        ipucu: string;
      };
    };
  };
}

interface RouteParams {
  analysisResult: AnalysisResult;
  lang?: string;
}

const FashionScreen = ({ navigation, route }: ScreenProps<'Fashion'>) => {
  const insets        = useSafeAreaInsets();
  const analysisResult = route.params?.analysisResult ?? {};
  const { lang } = useLanguage();
  const MEVSIMLER = useMemo(() => getSeasons(lang), [lang]);
  const KATEGORILER = useMemo(() => getCategories(lang), [lang]);

  const [selectedMevsim, setSelectedMevsim] = useState<string | null>(null);
  const [selectedKategori, setSelectedKategori] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [data, setData] = useState<FashionData | null>(null);

  useEffect(() => {
    if (!analysisResult) {
      Alert.alert(t('common.error', lang), t('fashion.error_no_analysis', lang));
      navigation.goBack();
    }
  }, [analysisResult, lang, navigation]);

  const fetchFashionAdvice = async () => {
    setLoading(true);
    try {
      const response = await CoachAPI.getFashionAdvice(
        analysisResult,
        lang,
        selectedMevsim || undefined,
        selectedKategori || undefined
      );
      setData(response);
    } catch (error: any) {
      Alert.alert(t('common.error', lang), error.response?.data?.detail || t('common.generic_error', lang));
    } finally {
      setLoading(false);
    }
  };

  const handleLoadAdvice = () => {
    if (!selectedMevsim) {
      Alert.alert(t('common.select_required', lang), t('fashion.error_select_season', lang));
      return;
    }
    if (!selectedKategori) {
      Alert.alert(t('common.select_required', lang), t('fashion.error_select_category', lang));
      return;
    }
    fetchFashionAdvice();
  };

  const dataCoaching   = data?.coaching;
  const dataRenkPaleti = data?.renk_paleti;

  return (
    <View style={styles.container}>
      {/* Header */}
      <View style={[styles.header, { paddingTop: insets.top + 8 }]}>
        <TouchableOpacity onPress={() => navigation.goBack()}>
          <Text style={styles.backBtn}>{t('fashion.back', lang)}</Text>
        </TouchableOpacity>
        <Text style={styles.title}>👗 {t('fashion.title', lang)}</Text>
        <View style={styles.spacer} />
      </View>

      <ScrollView
        style={styles.content}
        showsVerticalScrollIndicator={false}
        keyboardShouldPersistTaps="handled"
      >
        {/* Mevsim Seçici */}
        <View style={styles.section}>
          <SectionLabel>{t('fashion.section_select_season', lang)}</SectionLabel>
          <View style={styles.buttonRow}>
            {MEVSIMLER.map(({ id: mId, emoji: mEmoji, label: mLabel }) => (
              <TouchableOpacity
                key={mId}
                style={[
                  styles.seasonBtn,
                  selectedMevsim === mId && styles.seasonBtnActive,
                ]}
                onPress={() => setSelectedMevsim(mId)}
              >
                <Text style={styles.seasonEmoji}>{mEmoji}</Text>
                <Text
                  style={[
                    styles.seasonLabel,
                    selectedMevsim === mId && styles.seasonLabelActive,
                  ]}
                >
                  {mLabel}
                </Text>
              </TouchableOpacity>
            ))}
          </View>
        </View>

        {/* Kategori Seçici */}
        <View style={styles.section}>
          <SectionLabel>{t('fashion.section_select_category', lang)}</SectionLabel>
          <View style={styles.categoryTabs}>
            {KATEGORILER.map(({ id: kId, emoji: kEmoji, label: kLabel }) => (
              <TouchableOpacity
                key={kId}
                style={[
                  styles.categoryTab,
                  selectedKategori === kId && styles.categoryTabActive,
                ]}
                onPress={() => setSelectedKategori(kId)}
              >
                <Text style={styles.categoryEmoji}>{kEmoji}</Text>
                <Text
                  style={[
                    styles.categoryTabLabel,
                    selectedKategori === kId && styles.categoryTabLabelActive,
                  ]}
                >
                  {kLabel}
                </Text>
              </TouchableOpacity>
            ))}
          </View>
        </View>

        {/* Load Button — mevsim/kategori değişince tekrar çekilebilsin */}
        <TouchableOpacity
          style={[styles.loadBtn, data ? styles.loadBtnRefresh : null]}
          onPress={handleLoadAdvice}
          disabled={loading}
        >
          {loading ? (
            <ActivityIndicator color="white" />
          ) : (
            <Text style={styles.loadBtnText}>
              {data ? t('fashion.try_another', lang) : t('fashion.load_advice', lang)}
            </Text>
          )}
        </TouchableOpacity>

        {/* Results */}
        {loading && (
          <View style={styles.loadingContainer}>
            <ActivityIndicator size="large" color={colors.gold} />
            <Text style={styles.loadingText}>{t('fashion.loading', lang)}</Text>
          </View>
        )}

        {data && !loading && (
          <>
            {/* Style Profile Card */}
            <Card style={styles.card}>
              <View style={styles.cardHeader}>
                <Text style={styles.cardTitle}>{t('fashion.style_profile', lang)}</Text>
              </View>
              <Text style={styles.styleProfile}>{data.stil_profili || t('fashion.default_style', lang)}</Text>
              <View style={styles.sifatList}>
                {data.dominant_sifatlar.map((sifat) => (
                  <Badge key={sifat} label={sifat} />
                ))}
              </View>
            </Card>

            {/* Color Palette */}
            <Card style={styles.card}>
              <Text style={styles.cardTitle}>{t('fashion.color_palette', lang)}</Text>
              <View style={styles.colorRow}>
                {dataRenkPaleti?.ana?.map((color, idx) => (
                  <View key={`ana-${idx}`} style={styles.colorContainer}>
                    <View
                      style={[styles.colorSwatch, { backgroundColor: color }]}
                    />
                    <Text style={styles.colorLabel}>{color}</Text>
                  </View>
                ))}
              </View>
              {(dataRenkPaleti?.vurgu?.length ?? 0) > 0 && (
                <>
                  <Text style={styles.colorSubtitle}>{t('fashion.accent_colors', lang)}</Text>
                  <View style={styles.colorRow}>
                    {dataRenkPaleti!.vurgu!.map((color, idx) => (
                      <View key={`vurgu-${idx}`} style={styles.colorContainer}>
                        <View
                          style={[styles.colorSwatch, { backgroundColor: color }]}
                        />
                        <Text style={styles.colorLabel}>{color}</Text>
                      </View>
                    ))}
                  </View>
                </>
              )}
            </Card>

            {/* Face Shape Note */}
            {data.yuz_sekli_notu && (
              <Card style={styles.cardFaceShape}>
                <Text style={styles.cardTitle}>{t('fashion.face_shape_note', lang)}</Text>
                <Text style={styles.faceNote}>{data.yuz_sekli_notu}</Text>
              </Card>
            )}

            {/* Coaching Insights */}
            {dataCoaching && (
              <Card style={styles.cardCoaching}>
                <Text style={styles.cardTitle}>💡 {t('fashion.style_advisor', lang)}</Text>

                <View style={styles.coachingSection}>
                  <Text style={styles.coachingLabel}>{t('fashion.philosophy', lang)}</Text>
                  <Text style={styles.coachingText}>{dataCoaching.felsefe}</Text>
                </View>

                <View style={styles.coachingSection}>
                  <Text style={styles.coachingLabel}>{t('fashion.combination', lang)}</Text>
                  <Text style={styles.coachingText}>{dataCoaching.kombinasyon}</Text>
                </View>

                <View style={styles.coachingSection}>
                  <Text style={styles.coachingLabel}>{t('fashion.color_psychology', lang)}</Text>
                  <Text style={styles.coachingText}>{dataCoaching.renk_psikolojisi}</Text>
                </View>

                <View style={styles.coachingSectionLast}>
                  <Text style={styles.coachingLabel}>{t('fashion.life_application', lang)}</Text>
                  <Text style={styles.coachingText}>{dataCoaching.yaşam_uyarlamasi}</Text>
                </View>
              </Card>
            )}

            {/* Clothing Recommendations */}
            {Object.entries(data.mevsim_onerileri).map(([mevsim, kategoriler]) => (
              <View key={mevsim}>
                <Text style={styles.mevsimTitle}>
                  {MEVSIMLER.find((m) => m.id === mevsim)?.emoji || ''} {mevsim}
                </Text>
                {Object.entries(kategoriler).map(([kategori, oneri]) => (
                  <Card key={`${mevsim}-${kategori}`} style={styles.card}>
                    <View style={styles.recommHeader}>
                      <Text style={styles.kategoriBadge}>
                        {KATEGORILER.find((k) => k.id === kategori)?.label}
                      </Text>
                    </View>

                    {/* Parçalar */}
                    {oneri.parca?.length > 0 && (
                      <View style={styles.section}>
                        <Text style={styles.subTitle}>{t('fashion.recommended_pieces', lang)}</Text>
                        {oneri.parca.map((p, i) => (
                          <Text key={i} style={styles.itemText}>
                            • {p}
                          </Text>
                        ))}
                      </View>
                    )}

                    {/* Kumaşlar */}
                    {oneri.kumas?.length > 0 && (
                      <View style={styles.section}>
                        <Text style={styles.subTitle}>{t('fashion.fabric_suggestions', lang)}</Text>
                        <View style={styles.chipRow}>
                          {oneri.kumas.map((k, i) => (
                            <View key={i} style={styles.chip}>
                              <Text style={styles.chipText}>{k}</Text>
                            </View>
                          ))}
                        </View>
                      </View>
                    )}

                    {/* Aksesuar */}
                    {oneri.aksesuar?.length > 0 && (
                      <View style={styles.section}>
                        <Text style={styles.subTitle}>{t('fashion.accessories', lang)}</Text>
                        <View style={styles.chipRow}>
                          {oneri.aksesuar.map((a, i) => (
                            <View key={i} style={styles.chip}>
                              <Text style={styles.chipText}>{a}</Text>
                            </View>
                          ))}
                        </View>
                      </View>
                    )}

                    {/* İpucu */}
                    {oneri.ipucu && (
                      <View style={styles.tipCard}>
                        <Text style={styles.tipText}>💡 {oneri.ipucu}</Text>
                      </View>
                    )}
                  </Card>
                ))}
              </View>
            ))}

          </>
        )}

        <View style={styles.bottomSpacer} />
      </ScrollView>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: colors.background,
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingHorizontal: 16,
    paddingVertical: 12,
    borderBottomWidth: 1,
    borderBottomColor: colors.border,
  },
  backBtn: {
    fontSize: 16,
    color: colors.gold,
    fontWeight: '600',
  },
  title: {
    fontSize: 20,
    fontWeight: 'bold',
    color: colors.text,
  },
  content: {
    flex: 1,
    paddingHorizontal: 16,
    paddingVertical: 12,
  },
  section: {
    marginBottom: 24,
  },
  buttonRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginTop: 12,
  },
  seasonBtn: {
    flex: 1,
    marginHorizontal: 4,
    paddingVertical: 12,
    paddingHorizontal: 8,
    borderRadius: 12,
    backgroundColor: colors.cardBg,
    borderWidth: 2,
    borderColor: 'transparent',
    alignItems: 'center',
  },
  seasonBtnActive: {
    backgroundColor: colors.warmAmberGlow,
    borderColor: colors.gold,
  },
  seasonEmoji: {
    fontSize: 24,
    marginBottom: 4,
  },
  seasonLabel: {
    fontSize: 12,
    color: colors.textMuted,
    fontWeight: '600',
  },
  seasonLabelActive: {
    color: colors.gold,
  },
  categoryTabs: {
    flexDirection: 'row',
    marginTop: 12,
    gap: 8,
  },
  categoryTab: {
    flex: 1,
    paddingVertical: 10,
    paddingHorizontal: 8,
    borderRadius: 10,
    backgroundColor: colors.cardBg,
    borderWidth: 2,
    borderColor: 'transparent',
    alignItems: 'center',
  },
  categoryTabActive: {
    backgroundColor: colors.warmAmberGlow,
    borderColor: colors.gold,
  },
  categoryEmoji: {
    fontSize: 20,
    marginBottom: 2,
  },
  categoryTabLabel: {
    fontSize: 11,
    color: colors.textMuted,
    fontWeight: '600',
  },
  categoryTabLabelActive: {
    color: colors.gold,
  },
  loadBtn: {
    backgroundColor: colors.gold,
    paddingVertical: 14,
    paddingHorizontal: 16,
    borderRadius: 10,
    alignItems: 'center',
    marginVertical: 20,
  },
  loadBtnRefresh: {
    backgroundColor: colors.cardBg,
    borderWidth: 1,
    borderColor: colors.gold,
  },
  loadBtnText: {
    color: 'white',
    fontSize: 16,
    fontWeight: '700',
  },
  loadingContainer: {
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 40,
  },
  loadingText: {
    marginTop: 12,
    fontSize: 14,
    color: colors.text,
  },
  card: {
    marginBottom: 16,
  },
  cardHeader: {
    marginBottom: 12,
  },
  cardTitle: {
    fontSize: 16,
    fontWeight: 'bold',
    color: colors.text,
    marginBottom: 8,
  },
  styleProfile: {
    fontSize: 18,
    fontWeight: '700',
    color: colors.gold,
    marginBottom: 12,
    textTransform: 'capitalize',
  },
  sifatList: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 8,
  },
  colorRow: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 12,
    marginTop: 8,
  },
  colorContainer: {
    alignItems: 'center',
    marginBottom: 12,
  },
  colorSwatch: {
    width: 50,
    height: 50,
    borderRadius: 25,
    marginBottom: 6,
    borderWidth: 2,
    borderColor: colors.border,
  },
  colorLabel: {
    fontSize: 11,
    color: colors.textMuted,
    textAlign: 'center',
    maxWidth: 60,
  },
  colorSubtitle: {
    fontSize: 13,
    fontWeight: '600',
    color: colors.text,
    marginTop: 12,
    marginBottom: 8,
  },
  faceNote: {
    fontSize: 14,
    color: colors.text,
    lineHeight: 20,
    fontStyle: 'italic',
  },
  mevsimTitle: {
    fontSize: 16,
    fontWeight: '700',
    color: colors.gold,
    marginVertical: 16,
  },
  recommHeader: {
    marginBottom: 16,
  },
  kategoriBadge: {
    fontSize: 14,
    fontWeight: '700',
    color: colors.gold,
    paddingVertical: 4,
    paddingHorizontal: 8,
    backgroundColor: colors.warmAmberGlow,
    borderRadius: 6,
    alignSelf: 'flex-start',
  },
  subTitle: {
    fontSize: 13,
    fontWeight: '600',
    color: colors.text,
    marginBottom: 8,
    marginTop: 12,
  },
  itemText: {
    fontSize: 13,
    color: colors.text,
    marginBottom: 4,
    lineHeight: 18,
  },
  chipRow: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 8,
  },
  chip: {
    backgroundColor: colors.cardBg,
    paddingVertical: 6,
    paddingHorizontal: 12,
    borderRadius: 16,
    borderWidth: 1,
    borderColor: colors.border,
  },
  chipText: {
    fontSize: 12,
    color: colors.text,
  },
  tipCard: {
    backgroundColor: colors.warmAmberGlow,
    paddingVertical: 12,
    paddingHorizontal: 12,
    borderRadius: 10,
    borderLeftWidth: 3,
    borderLeftColor: colors.gold,
    marginTop: 12,
  },
  tipText: {
    fontSize: 13,
    color: colors.text,
    fontWeight: '500',
    lineHeight: 18,
  },
  coachingSection: {
    marginVertical: 12,
  },
  coachingLabel: {
    fontSize: 12,
    fontWeight: '700',
    color: '#9B5DE5',
    marginBottom: 6,
    letterSpacing: 0.5,
  },
  coachingText: {
    fontSize: 13,
    color: colors.text,
    lineHeight: 19,
    fontStyle: 'italic',
  },
  resetBtn: {
    backgroundColor: colors.cardBg,
    paddingVertical: 12,
    paddingHorizontal: 16,
    borderRadius: 10,
    borderWidth: 1,
    borderColor: colors.border,
    alignItems: 'center',
    marginVertical: 20,
  },
  resetBtnText: {
    color: colors.gold,
    fontSize: 14,
    fontWeight: '600',
  },
  spacer:            { width: 40 },
  bottomSpacer:      { height: 20 },
  cardFaceShape:     { marginBottom: 16, backgroundColor: colors.warmAmberGlow },
  cardCoaching:      { marginBottom: 16, borderColor: '#9B5DE528', backgroundColor: '#9B5DE508' },
  coachingSectionLast: { marginVertical: 12, marginBottom: 0 },
});

export default FashionScreen;

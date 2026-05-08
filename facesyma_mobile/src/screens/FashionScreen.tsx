/**
 * src/screens/FashionScreen.tsx
 * ============================
 * Kişilik analizi sonucuna göre özelleştirilmiş giyim tavsiyeleri.
 * Mevsim ve kategori seçimli.
 */

import React, { useState, useMemo } from 'react';
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
import { useDispatch } from 'react-redux';
import { AppDispatch } from '../store';
import { markModuleUsed } from '../store/authSlice';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import type { ScreenProps } from '../navigation/types';
import type { AnalysisResult } from '../types/api';
import { useOfflineError } from '../hooks/useOfflineError';

// Hex → Türkçe renk adı (yaklaşık eşleşme)
const HEX_COLOR_NAMES: Record<string, string> = {
  '#000000': 'Siyah',     '#FFFFFF': 'Beyaz',     '#808080': 'Gri',
  '#C0C0C0': 'Gümüş',     '#BDC3C7': 'Açık Gri',  '#2C3E50': 'Lacivert',
  '#1A1A2E': 'Gece Mavisi','#34495E': 'Gri-Mavi',  '#2980B9': 'Mavi',
  '#3498DB': 'Açık Mavi', '#1E90FF': 'Kobalt',     '#4682B4': 'Çelik Mavisi',
  '#000080': 'Koyu Lacivert','#191970': 'Gece Mavisi',
  '#F5F5F5': 'Kırık Beyaz','#F5F0E8': 'Krem',      '#FAEBD7': 'Açık Krem',
  '#F5F5DC': 'Bej',       '#D2B48C': 'Ten',        '#C8A97E': 'Kumral',
  '#A0522D': 'Kahve',     '#8B4513': 'Koyu Kahve', '#5C3317': 'Çikolata',
  '#8B6914': 'Bronz',     '#C9A84C': 'Altın',      '#FFD700': 'Sarı Altın',
  '#DAA520': 'Kadife Altın','#B8860B': 'Koyu Altın',
  '#556B2F': 'Haki',      '#6B8E23': 'Zeytin',     '#8FBC8F': 'Açık Yeşil',
  '#2E8B57': 'Orman Yeşili','#006400': 'Koyu Yeşil','#228B22': 'Yeşil',
  '#8B0000': 'Koyu Kırmızı','#B22222': 'Tuğla',    '#DC143C': 'Kırmızı',
  '#800020': 'Bordo',     '#722F37': 'Şarap',
  '#9B5DE5': 'Mor',       '#800080': 'Koyu Mor',   '#4B0082': 'İndigo',
  '#696969': 'Antrasit',  '#708090': 'Kurşun Gri', '#A9A9A9': 'Orta Gri',
  '#8E9B90': 'Çam Yeşili','#607D8B': 'Slate',
  '#FF6B6B': 'Mercan',    '#FF8C00': 'Koyu Turuncu','#FFA500': 'Turuncu',
  '#F4A460': 'Kum',       '#DEB887': 'Bisküvi',
};

function hexToColorName(hex: string): string {
  const upper = hex.toUpperCase();
  if (HEX_COLOR_NAMES[upper]) return HEX_COLOR_NAMES[upper];
  // Yaklaşık eşleşme: en yakın rengi bul
  const r = parseInt(upper.slice(1, 3), 16) || 0;
  const g = parseInt(upper.slice(3, 5), 16) || 0;
  const b = parseInt(upper.slice(5, 7), 16) || 0;
  let best = '', minDist = Infinity;
  for (const [h, name] of Object.entries(HEX_COLOR_NAMES)) {
    const dr = (parseInt(h.slice(1, 3), 16) || 0) - r;
    const dg = (parseInt(h.slice(3, 5), 16) || 0) - g;
    const db2 = (parseInt(h.slice(5, 7), 16) || 0) - b;
    const dist = dr * dr + dg * dg + db2 * db2;
    if (dist < minDist) { minDist = dist; best = name; }
  }
  return best || hex;
}

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
  const dispatch      = useDispatch<AppDispatch>();
  const analysisResult = route.params?.analysisResult ?? {};
  const { lang } = useLanguage();
  const getErrorMessage = useOfflineError();

  const MEVSIMLER = useMemo(() => getSeasons(lang), [lang]);
  const KATEGORILER = useMemo(() => getCategories(lang), [lang]);

  const [selectedMevsim, setSelectedMevsim] = useState<string | null>(null);
  const [selectedKategori, setSelectedKategori] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [data, setData] = useState<FashionData | null>(null);

  const hasValidAnalysis = !!(
    (analysisResult as any)?.top_sifatlar?.length ||
    Object.keys((analysisResult as any)?.sifat_scores ?? {}).length ||
    (analysisResult as any)?.attributes?.length
  );

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
      dispatch(markModuleUsed('fashion'));
    } catch (error: any) {
      Alert.alert(t('common.error', lang), getErrorMessage(error));
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
        <TouchableOpacity onPress={() => navigation.goBack()}
          accessibilityRole="button"
          accessibilityLabel={t('fashion.back', lang)}
        >
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
        {/* Analiz yoksa soft info banner */}
        {!hasValidAnalysis && (
          <View style={styles.infoBanner}>
            <Text style={styles.infoBannerText}>ℹ️ {t('fashion.no_analysis_hint', lang)}</Text>
            <TouchableOpacity style={styles.infoBannerBtn} onPress={() => navigation.goBack()}
              accessibilityRole="button"
              accessibilityLabel={t('fashion.go_to_analysis', lang)}
            >
              <Text style={styles.infoBannerBtnText}>📷 {t('fashion.go_to_analysis', lang)}</Text>
            </TouchableOpacity>
          </View>
        )}

        {/* Mevsim Seçici */}
        <View style={styles.section}>
          <SectionLabel>{t('fashion.section_select_season', lang)}</SectionLabel>
          <View style={styles.buttonRow}>
            {MEVSIMLER.map(({ id: mId, emoji: mEmoji, label: mLabel }) => (
              <TouchableOpacity
                accessibilityRole="button"
                accessibilityLabel={mEmoji}
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
                accessibilityRole="button"
                accessibilityLabel={kEmoji}
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
          accessibilityRole="button"
          accessibilityLabel={t('fashion.loading', lang)}
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
                {dataRenkPaleti?.ana?.filter(c => c.startsWith('#')).map((color, idx) => (
                  <View key={`ana-${idx}`} style={styles.colorContainer}>
                    <View style={[styles.colorSwatch, { backgroundColor: color }]}>
                      <View style={[styles.colorSwatchInner, { backgroundColor: color }]} />
                    </View>
                    <Text style={styles.colorLabel}>{hexToColorName(color)}</Text>
                  </View>
                ))}
              </View>
              {(dataRenkPaleti?.vurgu?.filter(c => c.startsWith('#')).length ?? 0) > 0 && (
                <>
                  <Text style={styles.colorSubtitle}>{t('fashion.accent_colors', lang)}</Text>
                  <View style={styles.colorRow}>
                    {dataRenkPaleti!.vurgu!.filter(c => c.startsWith('#')).map((color, idx) => (
                      <View key={`vurgu-${idx}`} style={styles.colorContainer}>
                        <View style={[styles.colorSwatch, { backgroundColor: color }]}>
                          <View style={[styles.colorSwatchInner, { backgroundColor: color }]} />
                        </View>
                        <Text style={styles.colorLabel}>{hexToColorName(color)}</Text>
                      </View>
                    ))}
                  </View>
                </>
              )}
              {(dataRenkPaleti?.kacin?.length ?? 0) > 0 && (
                <>
                  <Text style={styles.colorSubtitleAvoid}>{t('fashion.avoid_colors', lang)}</Text>
                  <View style={styles.chipRow}>
                    {dataRenkPaleti!.kacin!.map((item, idx) => (
                      <View key={`kacin-${idx}`} style={styles.chipAvoid}>
                        <Text style={styles.chipAvoidText}>
                          {item.startsWith('#') ? hexToColorName(item) : item}
                        </Text>
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
  infoBanner: {
    backgroundColor: '#2a2a1a',
    borderLeftWidth: 3,
    borderLeftColor: colors.gold,
    borderRadius: 8,
    padding: 12,
    marginBottom: 16,
  },
  infoBannerText: {
    color: colors.textWarm,
    fontSize: 13,
    lineHeight: 18,
    marginBottom: 10,
  },
  infoBannerBtn: {
    backgroundColor: colors.gold,
    borderRadius: 8,
    paddingVertical: 8,
    paddingHorizontal: 14,
    alignSelf: 'flex-start',
  },
  infoBannerBtnText: {
    color: '#000',
    fontSize: 13,
    fontWeight: '600',
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
    width: 56,
    height: 56,
    borderRadius: 28,
    marginBottom: 6,
    borderWidth: 3,
    borderColor: 'rgba(255,255,255,0.15)',
    overflow: 'hidden',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.3,
    shadowRadius: 4,
    elevation: 4,
  },
  colorSwatchInner: {
    flex: 1,
  },
  colorLabel: {
    fontSize: 11,
    color: colors.textMuted,
    textAlign: 'center',
    maxWidth: 64,
  },
  colorSubtitle: {
    fontSize: 13,
    fontWeight: '600',
    color: colors.text,
    marginTop: 16,
    marginBottom: 8,
  },
  colorSubtitleAvoid: {
    fontSize: 13,
    fontWeight: '600',
    color: '#FF6B6B',
    marginTop: 16,
    marginBottom: 8,
  },
  chipAvoid: {
    backgroundColor: 'rgba(255,107,107,0.12)',
    paddingVertical: 6,
    paddingHorizontal: 12,
    borderRadius: 16,
    borderWidth: 1,
    borderColor: 'rgba(255,107,107,0.4)',
  },
  chipAvoidText: {
    fontSize: 12,
    color: '#FF6B6B',
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

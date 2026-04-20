/**
 * src/screens/FashionScreen.tsx
 * ============================
 * Kişilik analizi sonucuna göre özelleştirilmiş giyim tavsiyeleri.
 * Mevsim ve kategori seçimli.
 */

import React, { useState, useEffect, useMemo } from 'react';
import {
  View, Text, StyleSheet, ScrollView, TouchableOpacity,
  ActivityIndicator, Alert, SafeAreaView,
} from 'react-native';
import { CoachAPI } from '../services/api';
import { Card, SectionLabel, Badge } from '../components/ui';
import theme from '../utils/theme';
import { useLanguage } from '../utils/LanguageContext';
import { t } from '../utils/i18n';

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
  analysisResult: any;
  lang?: string;
}

const FashionScreen: React.FC<{ navigation: any; route: any }> = ({ navigation, route }) => {
  const { analysisResult } = route.params as RouteParams;
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
  }, [analysisResult, lang]);

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
      console.error('Fashion error:', error);
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

  return (
    <SafeAreaView style={styles.container}>
      {/* Header */}
      <View style={styles.header}>
        <TouchableOpacity onPress={() => navigation.goBack()}>
          <Text style={styles.backBtn}>{t('fashion.back', lang)}</Text>
        </TouchableOpacity>
        <Text style={styles.title}>👗 {t('fashion.title', lang)}</Text>
        <View style={{ width: 40 }} />
      </View>

      <ScrollView
        style={styles.content}
        showsVerticalScrollIndicator={false}
        keyboardShouldPersistTaps="handled"
      >
        {/* Mevsim Seçici */}
        <View style={styles.section}>
          <SectionLabel label={t('fashion.section_select_season', lang)} />
          <View style={styles.buttonRow}>
            {MEVSIMLER.map((mevsim) => (
              <TouchableOpacity
                key={mevsim.id}
                style={[
                  styles.seasonBtn,
                  selectedMevsim === mevsim.id && styles.seasonBtnActive,
                ]}
                onPress={() => setSelectedMevsim(mevsim.id)}
              >
                <Text style={styles.seasonEmoji}>{mevsim.emoji}</Text>
                <Text
                  style={[
                    styles.seasonLabel,
                    selectedMevsim === mevsim.id && styles.seasonLabelActive,
                  ]}
                >
                  {mevsim.label}
                </Text>
              </TouchableOpacity>
            ))}
          </View>
        </View>

        {/* Kategori Seçici */}
        <View style={styles.section}>
          <SectionLabel label={t('fashion.section_select_category', lang)} />
          <View style={styles.categoryTabs}>
            {KATEGORILER.map((kat) => (
              <TouchableOpacity
                key={kat.id}
                style={[
                  styles.categoryTab,
                  selectedKategori === kat.id && styles.categoryTabActive,
                ]}
                onPress={() => setSelectedKategori(kat.id)}
              >
                <Text style={styles.categoryEmoji}>{kat.emoji}</Text>
                <Text
                  style={[
                    styles.categoryTabLabel,
                    selectedKategori === kat.id && styles.categoryTabLabelActive,
                  ]}
                >
                  {kat.label}
                </Text>
              </TouchableOpacity>
            ))}
          </View>
        </View>

        {/* Load Button */}
        {!data ? (
          <TouchableOpacity
            style={styles.loadBtn}
            onPress={handleLoadAdvice}
            disabled={loading}
          >
            {loading ? (
              <ActivityIndicator color="white" />
            ) : (
              <Text style={styles.loadBtnText}>{t('fashion.load_advice', lang)}</Text>
            )}
          </TouchableOpacity>
        ) : null}

        {/* Results */}
        {loading && (
          <View style={styles.loadingContainer}>
            <ActivityIndicator size="large" color={theme.colors.gold} />
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
              <Text style={styles.styleProfile}>{data.stil_profili || 'Karma-Adaptif'}</Text>
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
                {data.renk_paleti?.ana?.map((color, idx) => (
                  <View key={`ana-${idx}`} style={styles.colorContainer}>
                    <View
                      style={[styles.colorSwatch, { backgroundColor: color }]}
                    />
                    <Text style={styles.colorLabel}>{color}</Text>
                  </View>
                ))}
              </View>
              {data.renk_paleti?.vurgu?.length > 0 && (
                <>
                  <Text style={styles.colorSubtitle}>{t('fashion.accent_colors', lang)}</Text>
                  <View style={styles.colorRow}>
                    {data.renk_paleti.vurgu.map((color, idx) => (
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
              <Card style={[styles.card, { backgroundColor: theme.colors.warmAmberGlow }]}>
                <Text style={styles.cardTitle}>{t('fashion.face_shape_note', lang)}</Text>
                <Text style={styles.faceNote}>{data.yuz_sekli_notu}</Text>
              </Card>
            )}

            {/* Coaching Insights */}
            {data.coaching && (
              <Card style={[styles.card, { borderColor: '#9B5DE528', backgroundColor: '#9B5DE508' }]}>
                <Text style={styles.cardTitle}>💡 {t('fashion.style_advisor', lang)}</Text>

                <View style={styles.coachingSection}>
                  <Text style={styles.coachingLabel}>{t('fashion.philosophy', lang)}</Text>
                  <Text style={styles.coachingText}>{data.coaching.felsefe}</Text>
                </View>

                <View style={styles.coachingSection}>
                  <Text style={styles.coachingLabel}>{t('fashion.combination', lang)}</Text>
                  <Text style={styles.coachingText}>{data.coaching.kombinasyon}</Text>
                </View>

                <View style={styles.coachingSection}>
                  <Text style={styles.coachingLabel}>{t('fashion.color_psychology', lang)}</Text>
                  <Text style={styles.coachingText}>{data.coaching.renk_psikolojisi}</Text>
                </View>

                <View style={[styles.coachingSection, { marginBottom: 0 }]}>
                  <Text style={styles.coachingLabel}>{t('fashion.life_application', lang)}</Text>
                  <Text style={styles.coachingText}>{data.coaching.yaşam_uyarlamasi}</Text>
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

            {/* Reset Button */}
            <TouchableOpacity style={styles.resetBtn} onPress={() => setData(null)}>
              <Text style={styles.resetBtnText}>{t('fashion.try_another', lang)}</Text>
            </TouchableOpacity>
          </>
        )}

        <View style={{ height: 20 }} />
      </ScrollView>
    </SafeAreaView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: theme.colors.background,
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingHorizontal: 16,
    paddingVertical: 12,
    borderBottomWidth: 1,
    borderBottomColor: theme.colors.border,
  },
  backBtn: {
    fontSize: 16,
    color: theme.colors.gold,
    fontWeight: '600',
  },
  title: {
    fontSize: 20,
    fontWeight: 'bold',
    color: theme.colors.text,
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
    backgroundColor: theme.colors.cardBg,
    borderWidth: 2,
    borderColor: 'transparent',
    alignItems: 'center',
  },
  seasonBtnActive: {
    backgroundColor: theme.colors.warmAmberGlow,
    borderColor: theme.colors.gold,
  },
  seasonEmoji: {
    fontSize: 24,
    marginBottom: 4,
  },
  seasonLabel: {
    fontSize: 12,
    color: theme.colors.textMuted,
    fontWeight: '600',
  },
  seasonLabelActive: {
    color: theme.colors.gold,
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
    backgroundColor: theme.colors.cardBg,
    borderWidth: 2,
    borderColor: 'transparent',
    alignItems: 'center',
  },
  categoryTabActive: {
    backgroundColor: theme.colors.warmAmberGlow,
    borderColor: theme.colors.gold,
  },
  categoryEmoji: {
    fontSize: 20,
    marginBottom: 2,
  },
  categoryTabLabel: {
    fontSize: 11,
    color: theme.colors.textMuted,
    fontWeight: '600',
  },
  categoryTabLabelActive: {
    color: theme.colors.gold,
  },
  loadBtn: {
    backgroundColor: theme.colors.gold,
    paddingVertical: 14,
    paddingHorizontal: 16,
    borderRadius: 10,
    alignItems: 'center',
    marginVertical: 20,
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
    color: theme.colors.text,
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
    color: theme.colors.text,
    marginBottom: 8,
  },
  styleProfile: {
    fontSize: 18,
    fontWeight: '700',
    color: theme.colors.gold,
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
    borderColor: theme.colors.border,
  },
  colorLabel: {
    fontSize: 11,
    color: theme.colors.textMuted,
    textAlign: 'center',
    maxWidth: 60,
  },
  colorSubtitle: {
    fontSize: 13,
    fontWeight: '600',
    color: theme.colors.text,
    marginTop: 12,
    marginBottom: 8,
  },
  faceNote: {
    fontSize: 14,
    color: theme.colors.text,
    lineHeight: 20,
    fontStyle: 'italic',
  },
  mevsimTitle: {
    fontSize: 16,
    fontWeight: '700',
    color: theme.colors.gold,
    marginVertical: 16,
  },
  recommHeader: {
    marginBottom: 16,
  },
  kategoriBadge: {
    fontSize: 14,
    fontWeight: '700',
    color: theme.colors.gold,
    paddingVertical: 4,
    paddingHorizontal: 8,
    backgroundColor: theme.colors.warmAmberGlow,
    borderRadius: 6,
    alignSelf: 'flex-start',
  },
  subTitle: {
    fontSize: 13,
    fontWeight: '600',
    color: theme.colors.text,
    marginBottom: 8,
    marginTop: 12,
  },
  itemText: {
    fontSize: 13,
    color: theme.colors.text,
    marginBottom: 4,
    lineHeight: 18,
  },
  chipRow: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 8,
  },
  chip: {
    backgroundColor: theme.colors.cardBg,
    paddingVertical: 6,
    paddingHorizontal: 12,
    borderRadius: 16,
    borderWidth: 1,
    borderColor: theme.colors.border,
  },
  chipText: {
    fontSize: 12,
    color: theme.colors.text,
  },
  tipCard: {
    backgroundColor: theme.colors.warmAmberGlow,
    paddingVertical: 12,
    paddingHorizontal: 12,
    borderRadius: 10,
    borderLeftWidth: 3,
    borderLeftColor: theme.colors.gold,
    marginTop: 12,
  },
  tipText: {
    fontSize: 13,
    color: theme.colors.text,
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
    color: theme.colors.text,
    lineHeight: 19,
    fontStyle: 'italic',
  },
  resetBtn: {
    backgroundColor: theme.colors.cardBg,
    paddingVertical: 12,
    paddingHorizontal: 16,
    borderRadius: 10,
    borderWidth: 1,
    borderColor: theme.colors.border,
    alignItems: 'center',
    marginVertical: 20,
  },
  resetBtnText: {
    color: theme.colors.gold,
    fontSize: 14,
    fontWeight: '600',
  },
});

export default FashionScreen;

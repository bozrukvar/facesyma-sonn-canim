// src/screens/AnalysisScreen.tsx (UPDATED WITH QUALITY CHECKS)
import React, { useState } from 'react';
import {
  View, Text, StyleSheet, ScrollView, TouchableOpacity,
  Dimensions, ActivityIndicator, Alert, Image,
} from 'react-native';
import { launchCamera, launchImageLibrary } from 'react-native-image-picker';
import { AnalysisAPI } from '../services/api';
import { Card, ScoreRing, GoldButton, SectionLabel, Badge } from '../components/ui';
import theme from '../utils/theme';
import { validateImageQuality, getQualityMessage, ImageQualityResult } from '../utils/imageQuality';

const { width } = Dimensions.get('window');

const LANGS = [
  { code:'tr', flag:'🇹🇷' }, { code:'en', flag:'🇬🇧' },
  { code:'de', flag:'🇩🇪' }, { code:'ru', flag:'🇷🇺' },
  { code:'ar', flag:'🇸🇦' }, { code:'es', flag:'🇪🇸' },
  { code:'ko', flag:'🇰🇷' }, { code:'ja', flag:'🇯🇵' },
];

type AnalysisStep = 'pick' | 'quality_check' | 'preview' | 'result';

interface AnalysisState {
  imageUri: string | null;
  qualityResult: ImageQualityResult | null;
  analysisResult: any | null;
  loading: boolean;
  step: AnalysisStep;
  lang: string;
}

const AnalysisScreen: React.FC<{ navigation: any }> = ({ navigation }) => {
  const [state, setState] = useState<AnalysisState>({
    imageUri: null,
    qualityResult: null,
    analysisResult: null,
    loading: false,
    step: 'pick',
    lang: 'tr',
  });

  const pickImage = async (source: 'camera' | 'library') => {
    const opts = { mediaType: 'photo' as const, quality: 0.85 as const, maxWidth: 1024, maxHeight: 1024 };
    const fn = source === 'camera' ? launchCamera : launchImageLibrary;

    fn(opts, async (res) => {
      if (res.assets?.[0]?.uri) {
        const imageUri = res.assets[0].uri;
        setState(s => ({ ...s, imageUri, step: 'quality_check', loading: true }));

        // ═══════════════════════════════════════════════════════════════════
        // QUALITY CHECK
        // ═══════════════════════════════════════════════════════════════════
        try {
          const qualityResult = await validateImageQuality(imageUri);
          setState(s => ({
            ...s,
            qualityResult,
            step: qualityResult.can_upload ? 'preview' : 'quality_check',
            loading: false,
          }));
        } catch (error) {
          console.warn('Quality check failed:', error);
          // Fallback: Assume quality is OK
          setState(s => ({
            ...s,
            qualityResult: {
              overall_score: 70,
              brightness: { value: 150, score: 100, status: 'good' },
              contrast: { value: 60, score: 100, status: 'good' },
              face_centering: { offset_x: 0, offset_y: 0, score: 100, status: 'centered' },
              recommendation: 'Kalite kontrolü atlandı, devam ediliyor',
              can_upload: true,
            },
            step: 'preview',
            loading: false,
          }));
        }
      }
    });
  };

  const retakePhoto = () => {
    setState(s => ({ ...s, imageUri: null, qualityResult: null, step: 'pick' }));
  };

  const acceptQuality = () => {
    setState(s => ({ ...s, step: 'preview' }));
  };

  const startAnalysis = async () => {
    if (!state.imageUri) return;
    setState(s => ({ ...s, loading: true }));

    try {
      const data = await AnalysisAPI.analyze(state.imageUri, state.lang);
      setState(s => ({ ...s, analysisResult: data, step: 'result', loading: false }));
    } catch (e: any) {
      Alert.alert('Analiz Hatası', e.response?.data?.detail || 'Bir hata oluştu.');
      setState(s => ({ ...s, loading: false }));
    }
  };

  const reset = () => {
    setState(s => ({
      ...s,
      imageUri: null,
      qualityResult: null,
      analysisResult: null,
      step: 'pick',
    }));
  };

  // ── Ekran: Fotoğraf seç ──────────────────────────────────────────────────
  if (state.step === 'pick') {
    return (
      <View style={styles.container}>
        <View style={styles.header}>
          <TouchableOpacity onPress={() => navigation.goBack()}>
            <Text style={styles.back}>←</Text>
          </TouchableOpacity>
          <Text style={styles.headerTitle}>Yüz Analizi</Text>
          <View style={{ width: 40 }} />
        </View>

        <ScrollView contentContainerStyle={styles.scroll} showsVerticalScrollIndicator={false}>
          {/* Dil seçimi */}
          <SectionLabel>DİL SEÇ</SectionLabel>
          <ScrollView horizontal showsHorizontalScrollIndicator={false} style={{ marginBottom: 20 }}>
            {LANGS.map(l => (
              <TouchableOpacity
                key={l.code}
                style={[styles.langChip, state.lang === l.code && styles.langChipActive]}
                onPress={() => setState(s => ({ ...s, lang: l.code }))}
              >
                <Text style={{ fontSize: 16 }}>{l.flag}</Text>
                <Text style={[styles.langText, state.lang === l.code && styles.langTextActive]}>
                  {l.code.toUpperCase()}
                </Text>
              </TouchableOpacity>
            ))}
          </ScrollView>

          {/* Pick area */}
          <View style={styles.pickArea}>
            <Text style={{ fontSize: 52, marginBottom: 12 }}>📸</Text>
            <Text style={styles.pickTitle}>Fotoğraf Yükle</Text>
            <Text style={styles.pickDesc}>Yüzünün net göründüğü bir fotoğraf seç</Text>

            <GoldButton
              title="FOTOĞRAF ÇEK"
              onPress={() => pickImage('camera')}
              icon="📷"
              style={{ marginTop: 20 }}
            />
            <GoldButton
              title="GALERİDEN SEÇ"
              onPress={() => pickImage('library')}
              variant="outline"
              icon="🖼"
              style={{ marginTop: 10 }}
            />
          </View>

          <Card variant="warm" style={{ marginTop: 16 }}>
            <Text style={styles.tipsTitle}>💡 İpuçları</Text>
            {[
              'Yüz net görünsün',
              'İyi aydınlatılmış ortam',
              'Düz bakış açısı',
              'Aksesuar olmadan',
            ].map((t, i) => (
              <Text key={i} style={styles.tip}>
                • {t}
              </Text>
            ))}
          </Card>
        </ScrollView>
      </View>
    );
  }

  // ── Ekran: Kalite Kontrol ────────────────────────────────────────────────
  if (state.step === 'quality_check' && state.qualityResult) {
    const quality = state.qualityResult;
    const qualityMsg = getQualityMessage(quality.overall_score);

    return (
      <View style={styles.container}>
        <View style={styles.header}>
          <TouchableOpacity onPress={retakePhoto}>
            <Text style={styles.back}>←</Text>
          </TouchableOpacity>
          <Text style={styles.headerTitle}>Kalite Kontrol</Text>
          <View style={{ width: 40 }} />
        </View>

        <ScrollView contentContainerStyle={styles.scroll} showsVerticalScrollIndicator={false}>
          {/* Fotoğraf */}
          {state.imageUri && (
            <Image source={{ uri: state.imageUri }} style={styles.previewImg} />
          )}

          {/* Overall Score */}
          <Card style={{ marginTop: 20, alignItems: 'center', backgroundColor: qualityMsg.color + '20' }}>
            <Text style={{ fontSize: 40 }}>{qualityMsg.emoji}</Text>
            <Text style={{ fontSize: 28, fontWeight: 'bold', color: qualityMsg.color, marginTop: 8 }}>
              {quality.overall_score}%
            </Text>
            <Text style={{ fontSize: 16, fontWeight: '600', color: '#333', marginTop: 4 }}>
              {qualityMsg.title}
            </Text>
            <Text style={{ fontSize: 14, color: '#666', marginTop: 8, textAlign: 'center' }}>
              {quality.recommendation}
            </Text>
          </Card>

          {/* Detailed Metrics */}
          <SectionLabel style={{ marginTop: 24 }}>DETAYLI ANALIZ</SectionLabel>

          {/* Brightness */}
          <Card style={{ marginTop: 12 }}>
            <View style={styles.metricRow}>
              <View style={styles.metricLabel}>
                <Text style={styles.metricTitle}>☀️ Parlaklık</Text>
                <Text style={styles.metricValue}>{quality.brightness.value}/255</Text>
              </View>
              <View style={[styles.scoreBar, { backgroundColor: '#f39c12' }]}>
                <View
                  style={[
                    styles.scoreBarFill,
                    { width: `${quality.brightness.score}%`, backgroundColor: '#f39c12' },
                  ]}
                />
              </View>
              <Text style={styles.scoreText}>{Math.round(quality.brightness.score)}%</Text>
            </View>
          </Card>

          {/* Contrast */}
          <Card style={{ marginTop: 12 }}>
            <View style={styles.metricRow}>
              <View style={styles.metricLabel}>
                <Text style={styles.metricTitle}>◻️ Kontrast</Text>
                <Text style={styles.metricValue}>{quality.contrast.value}/100</Text>
              </View>
              <View style={[styles.scoreBar, { backgroundColor: '#3498db' }]}>
                <View
                  style={[
                    styles.scoreBarFill,
                    { width: `${quality.contrast.score}%`, backgroundColor: '#3498db' },
                  ]}
                />
              </View>
              <Text style={styles.scoreText}>{Math.round(quality.contrast.score)}%</Text>
            </View>
          </Card>

          {/* Face Centering */}
          <Card style={{ marginTop: 12 }}>
            <View style={styles.metricRow}>
              <View style={styles.metricLabel}>
                <Text style={styles.metricTitle}>🎯 Yüz Konumu</Text>
                <Text style={styles.metricValue}>
                  ({quality.face_centering.offset_x}, {quality.face_centering.offset_y})
                </Text>
              </View>
              <View style={[styles.scoreBar, { backgroundColor: '#e74c3c' }]}>
                <View
                  style={[
                    styles.scoreBarFill,
                    { width: `${quality.face_centering.score}%`, backgroundColor: '#e74c3c' },
                  ]}
                />
              </View>
              <Text style={styles.scoreText}>{Math.round(quality.face_centering.score)}%</Text>
            </View>
          </Card>

          {/* Action Buttons */}
          <View style={{ flexDirection: 'row', gap: 10, marginTop: 24, marginBottom: 20 }}>
            <GoldButton
              title="YENIDEN ÇEK"
              onPress={retakePhoto}
              variant="outline"
              style={{ flex: 1 }}
            />
            {quality.can_upload ? (
              <GoldButton
                title="DEVAM ET"
                onPress={acceptQuality}
                style={{ flex: 1 }}
              />
            ) : (
              <TouchableOpacity
                style={{ flex: 1, padding: 12, backgroundColor: '#bdc3c7', borderRadius: 8 }}
                disabled
              >
                <Text style={{ color: '#fff', textAlign: 'center', fontWeight: '600' }}>
                  Kalite Yetersiz
                </Text>
              </TouchableOpacity>
            )}
          </View>
        </ScrollView>
      </View>
    );
  }

  // ── Ekran: Önizleme ──────────────────────────────────────────────────────
  if (state.step === 'preview') {
    return (
      <View style={styles.container}>
        <View style={styles.header}>
          <TouchableOpacity onPress={retakePhoto}>
            <Text style={styles.back}>←</Text>
          </TouchableOpacity>
          <Text style={styles.headerTitle}>Önizleme</Text>
          <View style={{ width: 40 }} />
        </View>
        <View style={{ flex: 1, padding: theme.spacing.lg, alignItems: 'center' }}>
          {state.imageUri && (
            <Image source={{ uri: state.imageUri }} style={styles.previewImg} />
          )}
          <View style={{ flexDirection: 'row', width: '100%', gap: 10, marginTop: 16 }}>
            <TouchableOpacity style={styles.changeBtn} onPress={retakePhoto}>
              <Text style={styles.changeBtnText}>Değiştir</Text>
            </TouchableOpacity>
            <GoldButton
              title={state.loading ? '' : 'ANALİZ ET'}
              onPress={startAnalysis}
              loading={state.loading}
              style={{ flex: 1 }}
            />
          </View>
          {state.loading && (
            <View style={{ alignItems: 'center', marginTop: 24, gap: 12 }}>
              <ActivityIndicator color={theme.colors.warmAmber} size="large" />
              <Text style={styles.analyzingText}>Yüzün analiz ediliyor…</Text>
            </View>
          )}
        </View>
      </View>
    );
  }

  // ── Ekran: Sonuçlar ──────────────────────────────────────────────────────
  const result = state.analysisResult;
  return (
    <View style={styles.container}>
      <View style={styles.header}>
        <TouchableOpacity onPress={reset}>
          <Text style={styles.back}>← Yeni</Text>
        </TouchableOpacity>
        <Text style={styles.headerTitle}>Sonuçlar</Text>
        <View style={{ width: 40 }} />
      </View>

      <ScrollView contentContainerStyle={styles.scroll} showsVerticalScrollIndicator={false}>
        {/* Fotoğraf + skor */}
        <View style={styles.resultTop}>
          {state.imageUri && (
            <Image source={{ uri: state.imageUri }} style={styles.resultImg} />
          )}
          <View style={{ flex: 1, gap: 12, justifyContent: 'center' }}>
            {result?.golden_ratio != null && (
              <ScoreRing score={Math.round(result.golden_ratio)} label="Altın Oran" size={80} />
            )}
          </View>
        </View>

        {/* Analiz Özeti */}
        <View style={{ flexDirection: 'row', gap: 8, marginBottom: theme.spacing.md, flexWrap: 'wrap' }}>
          {result?.face_detected !== false && (
            <Badge label="✓ Yüz Algılandı" color={theme.colors.gold} />
          )}
          {result?.age_group && (
            <Badge label={`Yaş: ${result.age_group}`} color={theme.colors.textWarm} />
          )}
          {result?.gender && (
            <Badge label={`Cinsiyet: ${result.gender}`} color={theme.colors.textWarm} />
          )}
        </View>

        {/* Sonuç Kartları */}
        {result?.sifatlar && (
          <>
            <SectionLabel>AYIRT EDICI ÖZELLİKLER</SectionLabel>
            <View style={{ flexDirection: 'row', gap: 8, flexWrap: 'wrap' }}>
              {result.sifatlar.slice(0, 5).map((s: string, i: number) => (
                <Badge key={i} label={s} color={theme.colors.gold} />
              ))}
            </View>
          </>
        )}

        <GoldButton title="YENİ ANALIZ YAP" onPress={reset} style={{ marginTop: 20, marginBottom: 20 }} />
      </ScrollView>
    </View>
  );
};

// ──────────────────────────────────────────────────────────────────────────────
// STYLES
// ──────────────────────────────────────────────────────────────────────────────

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#fff',
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingHorizontal: 16,
    paddingVertical: 12,
    borderBottomWidth: 1,
    borderBottomColor: '#eee',
  },
  headerTitle: {
    fontSize: 18,
    fontWeight: '700',
    color: '#000',
  },
  back: {
    fontSize: 24,
    color: theme.colors.gold,
  },
  scroll: {
    padding: theme.spacing.lg,
  },
  langChip: {
    paddingHorizontal: 12,
    paddingVertical: 8,
    marginRight: 8,
    borderRadius: 16,
    backgroundColor: '#f5f5f5',
    alignItems: 'center',
    gap: 4,
  },
  langChipActive: {
    backgroundColor: theme.colors.gold,
  },
  langText: {
    fontSize: 11,
    fontWeight: '600',
    color: '#666',
  },
  langTextActive: {
    color: '#fff',
  },
  pickArea: {
    alignItems: 'center',
    marginVertical: 32,
  },
  pickTitle: {
    fontSize: 20,
    fontWeight: '700',
    color: '#000',
  },
  pickDesc: {
    fontSize: 14,
    color: '#666',
    marginTop: 4,
  },
  tipsTitle: {
    fontSize: 16,
    fontWeight: '700',
    marginBottom: 12,
  },
  tip: {
    fontSize: 14,
    color: '#666',
    marginBottom: 8,
  },
  previewImg: {
    width: width - 32,
    height: width - 32,
    borderRadius: 12,
    backgroundColor: '#f5f5f5',
  },
  resultImg: {
    width: 120,
    height: 120,
    borderRadius: 12,
    backgroundColor: '#f5f5f5',
  },
  resultTop: {
    flexDirection: 'row',
    gap: 16,
    marginBottom: 20,
    padding: 12,
    backgroundColor: '#f9f9f9',
    borderRadius: 12,
  },
  changeBtn: {
    flex: 1,
    padding: 12,
    backgroundColor: '#f5f5f5',
    borderRadius: 8,
    alignItems: 'center',
  },
  changeBtnText: {
    fontWeight: '600',
    color: '#666',
  },
  analyzingText: {
    fontSize: 14,
    color: theme.colors.gold,
  },
  metricRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
  },
  metricLabel: {
    width: 100,
  },
  metricTitle: {
    fontSize: 14,
    fontWeight: '600',
    color: '#000',
  },
  metricValue: {
    fontSize: 12,
    color: '#666',
    marginTop: 4,
  },
  scoreBar: {
    flex: 1,
    height: 8,
    backgroundColor: '#eee',
    borderRadius: 4,
    overflow: 'hidden',
  },
  scoreBarFill: {
    height: '100%',
    borderRadius: 4,
  },
  scoreText: {
    fontSize: 12,
    fontWeight: '600',
    color: '#666',
    width: 40,
    textAlign: 'right',
  },
});

export default AnalysisScreen;

// src/screens/AnalysisScreen.tsx
import React, { useState, useEffect } from 'react';
import {
  View, Text, StyleSheet, ScrollView, TouchableOpacity,
  Dimensions, ActivityIndicator, Alert, Image,
} from 'react-native';
import { launchCamera, launchImageLibrary } from 'react-native-image-picker';
import { useDispatch } from 'react-redux';
import { AppDispatch } from '../store';
import { setAnalysisResult } from '../store/analysisSlice';
import { markModuleUsed } from '../store/authSlice';
import { AnalysisAPI } from '../services/api';
import { Card, ScoreRing, GoldButton, SectionLabel, Badge } from '../components/ui';
import { FaceScannerOverlay } from '../components/FaceScannerOverlay';
import theme from '../utils/theme';
const { colors, spacing, typography, radius } = theme;
import { validateImageQuality, getQualityMessage, ImageQualityResult } from '../utils/imageQuality';
import { useLanguage } from '../utils/LanguageContext';
import { t } from '../utils/i18n';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import type { AnalysisResult } from '../types/api';
import type { AnalysisNavProp } from '../navigation/types';

const { width } = Dimensions.get('window');

type AnalysisStep = 'pick' | 'quality_check' | 'preview' | 'result';

interface AnalysisState {
  imageUri: string | null;
  qualityResult: ImageQualityResult | null;
  analysisResult: AnalysisResult | null;
  loading: boolean;
  step: AnalysisStep;
  lang: string;
}

const AnalysisScreen: React.FC<{ navigation: AnalysisNavProp }> = ({ navigation }) => {
  const insets     = useSafeAreaInsets();
  const insetsTop  = insets.top;
  const dispatch = useDispatch<AppDispatch>();
  const { lang, setLang, availableLangs } = useLanguage();
  const [imageUri, setImageUri] = useState<string | null>(null);
  const [qualityResult, setQualityResult] = useState<ImageQualityResult | null>(null);
  const [result,   setResult]   = useState<AnalysisResult | null>(null);
  const [loading,  setLoading]  = useState(false);
  const [step,     setStep]     = useState<AnalysisStep>('pick');
  const [scanProgress, setScanProgress] = useState(0);

  const pickImage = async (source: 'camera'|'library') => {
    const opts = { mediaType:'photo' as const, quality:0.8 as const, maxWidth:1024, maxHeight:1024 };
    const fn = source === 'camera' ? launchCamera : launchImageLibrary;
    fn(opts, async (res) => {
      if (res.assets?.[0]?.uri) {
        const asset = res.assets[0];
        setImageUri(asset.uri ?? null);
        setResult(null);
        setLoading(true);
        try {
          const quality = await validateImageQuality(asset.uri ?? '', {
            width:    asset.width,
            height:   asset.height,
            fileSize: asset.fileSize,
          }, lang);
          setQualityResult(quality);
          setStep('quality_check');
        } catch (e: any) {
          Alert.alert(t('analysis.quality_check', lang), t('common.generic_error', lang));
          setStep('pick');
        } finally {
          setLoading(false);
        }
      }
    });
  };

  const startAnalysis = async () => {
    if (!imageUri) return;
    setLoading(true);
    try {
      const data = await AnalysisAPI.analyze(imageUri, lang);
      setResult(data);
      dispatch(setAnalysisResult({ result: data, imageUri }));
      dispatch(markModuleUsed('face_analysis'));
      setStep('result');
    } catch (e: any) {
      Alert.alert(t('common.error', lang), e.response?.data?.detail || t('common.generic_error', lang));
    } finally {
      setLoading(false);
    }
  };

  const reset = () => { setImageUri(null); setQualityResult(null); setResult(null); setStep('pick'); setScanProgress(0); };

  // Simulate scan progress during analysis (5 second duration for mystery/intrigue)
  useEffect(() => {
    if (!loading) {
      setScanProgress(0);
      return;
    }

    let elapsed = 0;
    const totalDuration = 5000; // 5 seconds - more mysterious

    const interval = setInterval(() => {
      elapsed += 30;
      const percentage = Math.min((elapsed / totalDuration) * 100, 95);

      // Non-linear progression for dramatic effect
      // Slow at start, faster in middle, slow at end
      let dramaticProgress = percentage;
      if (percentage < 30) {
        dramaticProgress = (percentage / 30) * 15; // Slow start
      } else if (percentage < 70) {
        dramaticProgress = 15 + ((percentage - 30) / 40) * 60; // Fast middle
      } else {
        dramaticProgress = 75 + ((percentage - 70) / 30) * 20; // Slow end
      }

      setScanProgress(dramaticProgress);
    }, 30);

    return () => clearInterval(interval);
  }, [loading]);

  // ── Ekran: Kalite Kontrol ────────────────────────────────────────────────
  if (step === 'quality_check' && qualityResult && imageUri) {
    const qualityMsg  = getQualityMessage(qualityResult.overall_score, lang);
    const qmColor     = qualityMsg.color;
    const canUpload   = qualityResult.can_upload;
    const scoreLabel  = t('analysis.score', lang);
    return (
      <View style={styles.container}>
        <View style={[styles.header, { paddingTop: insetsTop + spacing.sm }]}>
          <TouchableOpacity onPress={reset}><Text style={styles.back}>←</Text></TouchableOpacity>
          <Text style={styles.headerTitle}>{t('analysis.quality_check', lang)}</Text>
          <View style={styles.spacer} />
        </View>
        <ScrollView contentContainerStyle={styles.scroll} showsVerticalScrollIndicator={false}>
          {/* Fotoğraf */}
          <Image source={{ uri: imageUri }} style={styles.qualityImg} />

          {/* Genel Kalite Skoru */}
          <Card style={[styles.scoreCard, { backgroundColor: qmColor + '20', borderColor: qmColor }]}>
            <Text style={{ fontSize: 32, marginBottom: 8, textAlign: 'center' }}>{qualityMsg.emoji}</Text>
            <Text style={[styles.scoreTitle, { color: qmColor }]}>
              {Math.round(qualityResult.overall_score)}%
            </Text>
            <Text style={[styles.scoreSubtitle, { color: qmColor }]}>
              {qualityMsg.title}
            </Text>
            <Text style={styles.recommendationNote}>
              {qualityResult.recommendation}
            </Text>
          </Card>

          {/* Detaylı Metrikler */}
          <SectionLabel>{t('analysis.details', lang)}</SectionLabel>

          {/* Parlaklık */}
          <Card style={styles.metricCard}>
            <View style={styles.metricHeader}>
              <Text style={styles.metricLabel}>☀️ {t('analysis.brightness', lang)}</Text>
              <Text style={styles.metricValue}>{qualityResult.brightness.value}/255</Text>
            </View>
            <View style={styles.progressContainer}>
              <View
                style={[
                  styles.progressBar,
                  {
                    width: `${Math.min(100, (qualityResult.brightness.value / 255) * 100)}%`,
                    backgroundColor: '#f39c12',
                  },
                ]}
              />
            </View>
            <Text style={styles.metricScore}>{scoreLabel}: {Math.round(qualityResult.brightness.score)}%</Text>
          </Card>

          {/* Kontrast */}
          <Card style={styles.metricCard}>
            <View style={styles.metricHeader}>
              <Text style={styles.metricLabel}>◻️ {t('analysis.contrast', lang)}</Text>
              <Text style={styles.metricValue}>{qualityResult.contrast.value}/100</Text>
            </View>
            <View style={styles.progressContainer}>
              <View
                style={[
                  styles.progressBar,
                  {
                    width: `${qualityResult.contrast.value}%`,
                    backgroundColor: '#3498db',
                  },
                ]}
              />
            </View>
            <Text style={styles.metricScore}>{scoreLabel}: {Math.round(qualityResult.contrast.score)}%</Text>
          </Card>

          {/* Yüz Konumu */}
          <Card style={styles.metricCard}>
            <View style={styles.metricHeader}>
              <Text style={styles.metricLabel}>🎯 {t('analysis.face_position', lang)}</Text>
              <Text style={styles.metricValue}>
                ({qualityResult.face_centering.offset_x}, {qualityResult.face_centering.offset_y})%
              </Text>
            </View>
            <View style={styles.progressContainer}>
              <View
                style={[
                  styles.progressBar,
                  {
                    width: `${Math.max(0, 100 - Math.abs(qualityResult.face_centering.offset_x))}%`,
                    backgroundColor: '#e74c3c',
                  },
                ]}
              />
            </View>
            <Text style={styles.metricScore}>{scoreLabel}: {Math.round(qualityResult.face_centering.score)}%</Text>
          </Card>

          {/* Butonlar */}
          <View style={styles.actionRow}>
            <TouchableOpacity style={styles.retakeBtn} onPress={reset}>
              <Text style={styles.retakeBtnText}>{t('analysis.retake', lang)}</Text>
            </TouchableOpacity>
            <GoldButton
              title={canUpload ? t('analysis.continue', lang) : t('analysis.low_quality', lang)}
              onPress={() => canUpload && setStep('preview')}
              disabled={!canUpload}
              style={styles.flex1}
            />
          </View>
        </ScrollView>
      </View>
    );
  }

  // ── Ekran: Fotoğraf seç ──────────────────────────────────────────────────
  if (step === 'pick') return (
    <View style={styles.container}>
      <View style={[styles.header, { paddingTop: insetsTop + spacing.sm }]}>
        <TouchableOpacity onPress={() => navigation.goBack()}>
          <Text style={styles.back}>←</Text>
        </TouchableOpacity>
        <Text style={styles.headerTitle}>{t('analysis.title', lang)}</Text>
        <View style={styles.spacer} />
      </View>

      <ScrollView contentContainerStyle={styles.scroll} showsVerticalScrollIndicator={false}>
        {/* Dil seçimi */}
        <SectionLabel>{t('analysis.language_select', lang)}</SectionLabel>
        <ScrollView horizontal showsHorizontalScrollIndicator={false} style={styles.langScroll}>
          {availableLangs.map(({ code, flag }) => (
            <TouchableOpacity
              key={code}
              style={[styles.langChip, lang === code && styles.langChipActive]}
              onPress={() => setLang(code)}
            >
              <Text style={{ fontSize:16 }}>{flag}</Text>
              <Text style={[styles.langText, lang === code && styles.langTextActive]}>
                {code.toUpperCase()}
              </Text>
            </TouchableOpacity>
          ))}
        </ScrollView>

        {/* Pick area */}
        <View style={styles.pickArea}>
          <Text style={{ fontSize: 52, marginBottom:12 }}>📸</Text>
          <Text style={styles.pickTitle}>{t('analysis.upload_photo', lang)}</Text>
          <Text style={styles.pickDesc}>{t('analysis.upload_hint', lang)}</Text>

          <GoldButton
            title={t('analysis.take_photo', lang)}
            onPress={() => pickImage('camera')}
            icon="📷"
            style={styles.mt20}
          />
          <GoldButton
            title={t('analysis.choose_gallery', lang)}
            onPress={() => pickImage('library')}
            variant="outline"
            icon="🖼"
            style={styles.mt10}
          />
        </View>

        <Card variant="warm" style={styles.mt16}>
          <Text style={styles.tipsTitle}>{t('analysis.tips', lang)}</Text>
          {[t('analysis.tip1', lang), t('analysis.tip2', lang), t('analysis.tip3', lang), t('analysis.tip4', lang)].map((tip, i) => (
            <Text key={i} style={styles.tip}>• {tip}</Text>
          ))}
        </Card>
      </ScrollView>
    </View>
  );

  // ── Ekran: Önizleme ──────────────────────────────────────────────────────
  if (step === 'preview') return (
    <View style={styles.container}>
      <View style={[styles.header, { paddingTop: insetsTop + spacing.sm }]}>
        <TouchableOpacity onPress={reset}><Text style={styles.back}>←</Text></TouchableOpacity>
        <Text style={styles.headerTitle}>{t('analysis.preview', lang)}</Text>
        <View style={styles.spacer} />
      </View>
      <View style={styles.previewBody}>
        {imageUri && (
          <Image source={{ uri: imageUri }} style={styles.previewImg} />
        )}
        <View style={styles.previewBtns}>
          <TouchableOpacity style={styles.changeBtn} onPress={reset} disabled={loading}>
            <Text style={styles.changeBtnText}>{t('analysis.change', lang)}</Text>
          </TouchableOpacity>
          <GoldButton
            title={loading ? '' : t('analysis.analyze', lang)}
            onPress={startAnalysis}
            loading={loading}
            style={styles.flex1}
          />
        </View>
        {loading && imageUri && (
          <View style={styles.scannerWrap}>
            <FaceScannerOverlay
              imageUri={imageUri}
              progress={Math.min(scanProgress, 95)}
              scanDuration={5000}
              lang={lang}
            />
          </View>
        )}
      </View>
    </View>
  );

  // ── Ekran: Sonuçlar ──────────────────────────────────────────────────────
  return (
    <View style={styles.container}>
      <View style={[styles.header, { paddingTop: insetsTop + spacing.sm }]}>
        <TouchableOpacity onPress={reset}><Text style={styles.back}>{t('analysis.new_label', lang)}</Text></TouchableOpacity>
        <Text style={styles.headerTitle}>{t('analysis.results', lang)}</Text>
        <View style={styles.spacer} />
      </View>

      <ScrollView contentContainerStyle={styles.scroll} showsVerticalScrollIndicator={false}>
        {/* Fotoğraf + skor */}
        <View style={styles.resultTop}>
          {imageUri && (
            <Image source={{ uri: imageUri }} style={styles.resultImg} />
          )}
          <View style={styles.scoreCol}>
            {result?.golden_ratio != null && (
              <ScoreRing score={Math.round(result.golden_ratio)} label={t('analysis.golden_ratio', lang)} size={80} />
            )}
          </View>
        </View>

        {/* Analiz Özeti */}
        <View style={styles.badgeRow}>
          {result?.face_detected !== false && (
            <Badge label={t('analysis.face_detected', lang)} color={colors.gold} />
          )}
          {result?.age_group && (
            <Badge label={`${t('analysis.age', lang)}: ${result.age_group}`} color={colors.textWarm} />
          )}
          {result?.gender && (
            <Badge label={`${t('analysis.gender', lang)}: ${result.gender}`} color={colors.textWarm} />
          )}
        </View>

        {/* AI Asistanla konuş — ÖNE ÇIKAR */}
        <Card variant="warm" style={styles.chatCTA}>
          <View style={styles.chatCTARow}>
            <View style={styles.chatCTAIcon}><Text style={{ fontSize:22 }}>✨</Text></View>
            <View style={styles.ctaFlex1}>
              <Text style={styles.chatCTATitle}>{t('analysis.chat_title', lang)}</Text>
              <Text style={styles.chatCTADesc}>{t('analysis.chat_desc', lang)}</Text>
            </View>
          </View>
          <GoldButton
            title={t('analysis.chat_btn', lang)}
            variant="warm"
            onPress={() => navigation.navigate('Chat', { analysisResult: result, lang })}
            style={styles.ctaBtn}
          />
        </Card>

        {/* Giyim Önerileri */}
        <Card style={styles.fashionCTA}>
          <View style={styles.fashionCTARow}>
            <View style={styles.fashionCTAIcon}><Text style={{ fontSize:22 }}>👗</Text></View>
            <View style={styles.ctaFlex1}>
              <Text style={styles.fashionCTATitle}>{t('analysis.fashion_title', lang)}</Text>
              <Text style={styles.fashionCTADesc}>{t('analysis.fashion_desc', lang)}</Text>
            </View>
          </View>
          <GoldButton
            title={t('analysis.fashion_btn', lang)}
            variant="outline"
            icon="👗"
            onPress={() => navigation.navigate('Fashion', { analysisResult: result, lang })}
            style={styles.ctaBtn}
          />
        </Card>

        {/* Özellikler */}
        {(result?.attributes?.length ?? 0) > 0 && result && (
          <>
            <SectionLabel>{t('analysis.characteristics', lang)}</SectionLabel>
            {(result.attributes ?? []).slice(0, 6).map((a, i) => (
              <Card key={i} style={styles.attrCard}>
                <View style={styles.attrRow}>
                  <View style={styles.ctaFlex1}>
                    <Text style={styles.attrName}>{a.name}</Text>
                    {a.description && (
                      <Text style={styles.attrDesc} numberOfLines={2}>{a.description}</Text>
                    )}
                  </View>
                  <ScoreRing score={a.score || 0} label="" size={50} />
                </View>
              </Card>
            ))}
          </>
        )}

        {result?.kariyer && (
          <>
            <SectionLabel>{t('analysis.career', lang)}</SectionLabel>
            <Card variant="gold"><Text style={styles.moduleText}>{result.kariyer}</Text></Card>
          </>
        )}

        {result?.liderlik && (
          <>
            <SectionLabel>{t('analysis.leadership', lang)}</SectionLabel>
            <Card><Text style={styles.moduleText}>{result.liderlik}</Text></Card>
          </>
        )}

        {result?.daily && (
          <>
            <SectionLabel>{t('analysis.daily_msg', lang)}</SectionLabel>
            <Card variant="warm">
              <Text style={styles.moduleTextDaily}>
                "{result.daily}"
              </Text>
            </Card>
          </>
        )}

        <GoldButton
          title={t('analysis.new_analysis', lang)}
          onPress={reset}
          variant="outline"
          style={styles.mtXl}
        />
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
  scroll: { padding: spacing.lg, paddingBottom: spacing.xxxl },

  // Lang chips
  langChip: {
    flexDirection:'row', alignItems:'center', gap:5,
    paddingHorizontal:12, paddingVertical:8,
    borderRadius: radius.full,
    borderWidth:1, borderColor: colors.border,
    marginRight:8,
  },
  langChipActive: { borderColor: colors.gold, backgroundColor: colors.goldGlow },
  langText:       { ...typography.caption, color: colors.textMuted, fontSize:11 },
  langTextActive: { color: colors.gold, fontWeight:'700' },

  // Pick
  pickArea: {
    backgroundColor: colors.surface,
    borderRadius: radius.xl, borderWidth:1,
    borderColor: colors.border,
    borderStyle: 'dashed',
    padding: spacing.xl, alignItems:'center',
  },
  pickTitle: { ...typography.h2, marginBottom:8 },
  pickDesc:  { ...typography.body, textAlign:'center', color: colors.textWarm },
  tipsTitle: { ...typography.h3, fontSize:13, marginBottom:8 },
  tip:       { ...typography.caption, marginBottom:4, fontSize:12, color: colors.textWarm },

  // Preview
  previewImg: {
    width:  width - spacing.xl * 2,
    height: width - spacing.xl * 2,
    borderRadius: radius.xl,
  },
  changeBtn: {
    height:52, paddingHorizontal: spacing.lg,
    borderRadius: radius.md, borderWidth:1,
    borderColor: colors.border,
    alignItems:'center', justifyContent:'center',
  },
  changeBtnText: { ...typography.label, color: colors.textMuted, fontSize:12 },
  analyzingText: { ...typography.bodyWarm },

  // Result
  resultTop: { flexDirection:'row', gap: spacing.lg, alignItems:'center', marginBottom: spacing.md },
  resultImg: { width:90, height:90, borderRadius: radius.lg },

  // Chat CTA
  chatCTA:    { marginBottom: spacing.md },
  chatCTARow: { flexDirection:'row', alignItems:'center', gap:12 },
  chatCTAIcon:{
    width:48, height:48, borderRadius: radius.lg,
    backgroundColor: colors.warmAmberGlow,
    borderWidth:1, borderColor:`${colors.warmAmber}30`,
    alignItems:'center', justifyContent:'center',
  },
  chatCTATitle: { ...typography.h3, fontSize:14, marginBottom:3 },
  chatCTADesc:  { ...typography.caption, color: colors.textWarm, fontSize:11 },

  // Fashion CTA
  fashionCTA:    { marginBottom: spacing.md, borderColor:'#9B5DE528', backgroundColor: colors.surface },
  fashionCTARow: { flexDirection:'row', alignItems:'center', gap:12 },
  fashionCTAIcon:{
    width:48, height:48, borderRadius: radius.lg,
    backgroundColor: '#9B5DE512',
    borderWidth:1, borderColor:'#9B5DE530',
    alignItems:'center', justifyContent:'center',
  },
  fashionCTATitle: { ...typography.h3, fontSize:14, marginBottom:3 },
  fashionCTADesc:  { ...typography.caption, color: colors.textWarm, fontSize:11 },

  // Attrs
  attrCard: { marginBottom:8 },
  attrRow:  { flexDirection: 'row' as const, alignItems: 'center' as const, gap: 12 },
  attrName: { ...typography.h3, fontSize:13, marginBottom:3 },
  attrDesc: { ...typography.caption, fontSize:11, color: colors.textWarm },
  moduleText: { ...typography.bodyWarm, lineHeight:22, fontSize:13 },

  // Quality Check
  qualityImg: {
    width: width - spacing.xl * 2,
    height: width - spacing.xl * 2,
    borderRadius: radius.xl,
    marginBottom: spacing.lg,
  },
  scoreCard: {
    padding: spacing.lg,
    marginBottom: spacing.lg,
    borderWidth: 2,
    alignItems: 'center',
  },
  scoreTitle: {
    ...typography.h1,
    fontSize: 32,
  },
  scoreSubtitle: {
    ...typography.h3,
    fontSize: 14,
    marginTop: 4,
  },
  recommendation: {
    ...typography.body,
    textAlign: 'center',
  },
  metricCard: {
    marginBottom: spacing.md,
  },
  metricHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: 8,
  },
  metricLabel: {
    ...typography.label,
    fontSize: 12,
    fontWeight: '600',
  },
  metricValue: {
    ...typography.caption,
    fontSize: 11,
    color: colors.textMuted,
  },
  progressContainer: {
    height: 6,
    backgroundColor: colors.border,
    borderRadius: 3,
    overflow: 'hidden',
    marginBottom: 8,
  },
  progressBar: {
    height: '100%',
    borderRadius: 3,
  },
  metricScore: {
    ...typography.caption,
    fontSize: 10,
    color: colors.textMuted,
  },
  retakeBtn: {
    flex: 1,
    height: 52,
    borderRadius: radius.md,
    borderWidth: 1,
    borderColor: colors.border,
    alignItems: 'center',
    justifyContent: 'center',
  },
  retakeBtnText: {
    ...typography.label,
    color: colors.textMuted,
    fontSize: 12,
  },
  spacer:       { width: 40 },
  actionRow:    { flexDirection: 'row' as const, gap: 10, marginTop: 20 },
  flex1:        { flex: 1 },
  previewBody:  { flex: 1, padding: spacing.lg, alignItems: 'center' as const },
  previewBtns:  { flexDirection: 'row' as const, width: '100%', gap: 10, marginTop: 16 },
  scannerWrap:  { marginTop: 24, width: '100%', alignItems: 'center' as const },
  scoreCol:     { flex: 1, gap: 12, justifyContent: 'center' as const },
  badgeRow:     { flexDirection: 'row' as const, gap: 8, marginBottom: spacing.md, flexWrap: 'wrap' as const },
  ctaFlex1:     { flex: 1 },
  ctaBtn:       { marginTop: 12 },
  langScroll:        { marginBottom: 20 },
  mt20:              { marginTop: 20 },
  mt10:              { marginTop: 10 },
  mt16:              { marginTop: 16 },
  mtXl:              { marginTop: spacing.xl },
  recommendationNote:{ ...typography.body, textAlign: 'center' as const, color: colors.textWarm, marginTop: 8 },
  moduleTextDaily:   { ...typography.bodyWarm, lineHeight:22, fontSize:13, fontStyle: 'italic' as const, color: colors.textWarm },
});

export default AnalysisScreen;

// src/screens/AnalysisScreen.tsx
import React, { useState, useEffect } from 'react';
import {
  View, Text, StyleSheet, ScrollView, TouchableOpacity,
  Dimensions, ActivityIndicator, Alert, Image, ProgressBarAndroid,
} from 'react-native';
import { launchCamera, launchImageLibrary } from 'react-native-image-picker';
import { AnalysisAPI } from '../services/api';
import { Card, ScoreRing, GoldButton, SectionLabel, Badge } from '../components/ui';
import { FaceScannerOverlay } from '../components/FaceScannerOverlay';
import theme from '../utils/theme';
import { validateImageQuality, getQualityMessage, ImageQualityResult } from '../utils/imageQuality';
import { useLanguage } from '../utils/LanguageContext';

const { width } = Dimensions.get('window');

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
  const { lang, setLang, availableLangs } = useLanguage();
  const [imageUri, setImageUri] = useState<string | null>(null);
  const [qualityResult, setQualityResult] = useState<ImageQualityResult | null>(null);
  const [result,   setResult]   = useState<any>(null);
  const [loading,  setLoading]  = useState(false);
  const [step,     setStep]     = useState<AnalysisStep>('pick');
  const [scanProgress, setScanProgress] = useState(0);

  const pickImage = async (source: 'camera'|'library') => {
    const opts = { mediaType:'photo' as const, quality:0.85 as const, maxWidth:1024, maxHeight:1024 };
    const fn = source === 'camera' ? launchCamera : launchImageLibrary;
    fn(opts, async (res) => {
      if (res.assets?.[0]?.uri) {
        setImageUri(res.assets[0].uri);
        setResult(null);
        setLoading(true);
        try {
          const quality = await validateImageQuality(res.assets[0].uri);
          setQualityResult(quality);
          setStep('quality_check');
        } catch (e: any) {
          Alert.alert('Kalite Kontrol Hatası', 'Fotoğraf analiz edilemedi. Lütfen tekrar deneyin.');
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
      setStep('result');
    } catch (e: any) {
      Alert.alert('Analiz Hatası', e.response?.data?.detail || 'Bir hata oluştu.');
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
    const qualityMsg = getQualityMessage(qualityResult.overall_score);
    return (
      <View style={styles.container}>
        <View style={styles.header}>
          <TouchableOpacity onPress={reset}><Text style={styles.back}>←</Text></TouchableOpacity>
          <Text style={styles.headerTitle}>Kalite Kontrol</Text>
          <View style={{ width:40 }} />
        </View>
        <ScrollView contentContainerStyle={styles.scroll} showsVerticalScrollIndicator={false}>
          {/* Fotoğraf */}
          <Image source={{ uri: imageUri }} style={styles.qualityImg} />

          {/* Genel Kalite Skoru */}
          <Card style={[styles.scoreCard, { backgroundColor: qualityMsg.color + '20', borderColor: qualityMsg.color }]}>
            <Text style={{ fontSize: 32, marginBottom: 8, textAlign: 'center' }}>{qualityMsg.emoji}</Text>
            <Text style={[styles.scoreTitle, { color: qualityMsg.color }]}>
              {Math.round(qualityResult.overall_score)}%
            </Text>
            <Text style={[styles.scoreSubtitle, { color: qualityMsg.color }]}>
              {qualityMsg.title}
            </Text>
            <Text style={[styles.recommendation, { color: theme.colors.textWarm, marginTop: 8 }]}>
              {qualityResult.recommendation}
            </Text>
          </Card>

          {/* Detaylı Metrikler */}
          <SectionLabel>DETAYLARI</SectionLabel>

          {/* Parlaklık */}
          <Card style={styles.metricCard}>
            <View style={styles.metricHeader}>
              <Text style={styles.metricLabel}>☀️ Parlaklık</Text>
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
            <Text style={styles.metricScore}>Skor: {Math.round(qualityResult.brightness.score)}%</Text>
          </Card>

          {/* Kontrast */}
          <Card style={styles.metricCard}>
            <View style={styles.metricHeader}>
              <Text style={styles.metricLabel}>◻️ Kontrast</Text>
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
            <Text style={styles.metricScore}>Skor: {Math.round(qualityResult.contrast.score)}%</Text>
          </Card>

          {/* Yüz Konumu */}
          <Card style={styles.metricCard}>
            <View style={styles.metricHeader}>
              <Text style={styles.metricLabel}>🎯 Yüz Konumu</Text>
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
            <Text style={styles.metricScore}>Skor: {Math.round(qualityResult.face_centering.score)}%</Text>
          </Card>

          {/* Butonlar */}
          <View style={{ flexDirection: 'row', gap: 10, marginTop: 20 }}>
            <TouchableOpacity style={styles.retakeBtn} onPress={reset}>
              <Text style={styles.retakeBtnText}>YENIDEN ÇEK</Text>
            </TouchableOpacity>
            <GoldButton
              title={qualityResult.can_upload ? 'DEVAM ET' : 'KALİTE DÜŞÜK'}
              onPress={() => qualityResult.can_upload && setStep('preview')}
              disabled={!qualityResult.can_upload}
              style={{ flex: 1 }}
            />
          </View>
        </ScrollView>
      </View>
    );
  }

  // ── Ekran: Fotoğraf seç ──────────────────────────────────────────────────
  if (step === 'pick') return (
    <View style={styles.container}>
      <View style={styles.header}>
        <TouchableOpacity onPress={() => navigation.goBack()}>
          <Text style={styles.back}>←</Text>
        </TouchableOpacity>
        <Text style={styles.headerTitle}>Yüz Analizi</Text>
        <View style={{ width:40 }} />
      </View>

      <ScrollView contentContainerStyle={styles.scroll} showsVerticalScrollIndicator={false}>
        {/* Dil seçimi */}
        <SectionLabel>DİL SEÇ</SectionLabel>
        <ScrollView horizontal showsHorizontalScrollIndicator={false} style={{ marginBottom:20 }}>
          {availableLangs.map(l => (
            <TouchableOpacity
              key={l.code}
              style={[styles.langChip, lang === l.code && styles.langChipActive]}
              onPress={() => setLang(l.code)}
            >
              <Text style={{ fontSize:16 }}>{l.flag}</Text>
              <Text style={[styles.langText, lang === l.code && styles.langTextActive]}>
                {l.code.toUpperCase()}
              </Text>
            </TouchableOpacity>
          ))}
        </ScrollView>

        {/* Pick area */}
        <View style={styles.pickArea}>
          <Text style={{ fontSize: 52, marginBottom:12 }}>📸</Text>
          <Text style={styles.pickTitle}>Fotoğraf Yükle</Text>
          <Text style={styles.pickDesc}>Yüzünün net göründüğü bir fotoğraf seç</Text>

          <GoldButton
            title="FOTOĞRAF ÇEK"
            onPress={() => pickImage('camera')}
            icon="📷"
            style={{ marginTop:20 }}
          />
          <GoldButton
            title="GALERİDEN SEÇ"
            onPress={() => pickImage('library')}
            variant="outline"
            icon="🖼"
            style={{ marginTop:10 }}
          />
        </View>

        <Card variant="warm" style={{ marginTop:16 }}>
          <Text style={styles.tipsTitle}>💡 İpuçları</Text>
          {['Yüz net görünsün', 'İyi aydınlatılmış ortam', 'Düz bakış açısı', 'Aksesuar olmadan'].map((t,i) => (
            <Text key={i} style={styles.tip}>• {t}</Text>
          ))}
        </Card>
      </ScrollView>
    </View>
  );

  // ── Ekran: Önizleme ──────────────────────────────────────────────────────
  if (step === 'preview') return (
    <View style={styles.container}>
      <View style={styles.header}>
        <TouchableOpacity onPress={reset}><Text style={styles.back}>←</Text></TouchableOpacity>
        <Text style={styles.headerTitle}>Önizleme</Text>
        <View style={{ width:40 }} />
      </View>
      <View style={{ flex:1, padding: theme.spacing.lg, alignItems:'center' }}>
        {imageUri && (
          <Image source={{ uri: imageUri }} style={styles.previewImg} />
        )}
        <View style={{ flexDirection:'row', width:'100%', gap:10, marginTop:16 }}>
          <TouchableOpacity style={styles.changeBtn} onPress={reset} disabled={loading}>
            <Text style={styles.changeBtnText}>Değiştir</Text>
          </TouchableOpacity>
          <GoldButton
            title={loading ? '' : 'ANALİZ ET'}
            onPress={startAnalysis}
            loading={loading}
            style={{ flex:1 }}
          />
        </View>
        {loading && imageUri && (
          <View style={{ marginTop:24, width:'100%', alignItems:'center' }}>
            <FaceScannerOverlay
              imageUri={imageUri}
              progress={Math.min(scanProgress, 95)}
              scanDuration={5000}
            />
          </View>
        )}
      </View>
    </View>
  );

  // ── Ekran: Sonuçlar ──────────────────────────────────────────────────────
  return (
    <View style={styles.container}>
      <View style={styles.header}>
        <TouchableOpacity onPress={reset}><Text style={styles.back}>← Yeni</Text></TouchableOpacity>
        <Text style={styles.headerTitle}>Sonuçlar</Text>
        <View style={{ width:40 }} />
      </View>

      <ScrollView contentContainerStyle={styles.scroll} showsVerticalScrollIndicator={false}>
        {/* Fotoğraf + skor */}
        <View style={styles.resultTop}>
          {imageUri && (
            <Image source={{ uri: imageUri }} style={styles.resultImg} />
          )}
          <View style={{ flex:1, gap:12, justifyContent:'center' }}>
            {result?.golden_ratio != null && (
              <ScoreRing score={Math.round(result.golden_ratio)} label="Altın Oran" size={80} />
            )}
          </View>
        </View>

        {/* Analiz Özeti */}
        <View style={{ flexDirection:'row', gap:8, marginBottom: theme.spacing.md, flexWrap:'wrap' }}>
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

        {/* AI Asistanla konuş — ÖNE ÇIKAR */}
        <Card variant="warm" style={styles.chatCTA}>
          <View style={styles.chatCTARow}>
            <View style={styles.chatCTAIcon}><Text style={{ fontSize:22 }}>✨</Text></View>
            <View style={{ flex:1 }}>
              <Text style={styles.chatCTATitle}>Asistanınla Konuş</Text>
              <Text style={styles.chatCTADesc}>Sonuçları yorumla, soru sor, derine in</Text>
            </View>
          </View>
          <GoldButton
            title="ASISTANLA KONUŞ"
            variant="warm"
            onPress={() => navigation.navigate('Chat', { analysisResult: result, lang })}
            style={{ marginTop:12 }}
          />
        </Card>

        {/* Giyim Önerileri */}
        <Card style={styles.fashionCTA}>
          <View style={styles.fashionCTARow}>
            <View style={styles.fashionCTAIcon}><Text style={{ fontSize:22 }}>👗</Text></View>
            <View style={{ flex:1 }}>
              <Text style={styles.fashionCTATitle}>Giyim Danışmanı</Text>
              <Text style={styles.fashionCTADesc}>Karakterine uygun stil önerileri</Text>
            </View>
          </View>
          <GoldButton
            title="GİYİM ÖNERİLERİNİ GÖR"
            variant="outline"
            icon="👗"
            onPress={() => navigation.navigate('Fashion', { analysisResult: result, lang })}
            style={{ marginTop:12 }}
          />
        </Card>

        {/* Özellikler */}
        {result?.attributes?.length > 0 && (
          <>
            <SectionLabel>KARAKTERİSTİKLER</SectionLabel>
            {result.attributes.slice(0, 6).map((a: any, i: number) => (
              <Card key={i} style={styles.attrCard}>
                <View style={{ flexDirection:'row', alignItems:'center', gap:12 }}>
                  <View style={{ flex:1 }}>
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
            <SectionLabel>KARİYER</SectionLabel>
            <Card variant="gold"><Text style={styles.moduleText}>{result.kariyer}</Text></Card>
          </>
        )}

        {result?.liderlik && (
          <>
            <SectionLabel>LİDERLİK</SectionLabel>
            <Card><Text style={styles.moduleText}>{result.liderlik}</Text></Card>
          </>
        )}

        {result?.daily && (
          <>
            <SectionLabel>GÜNLÜK MESAJ</SectionLabel>
            <Card variant="warm">
              <Text style={[styles.moduleText, { fontStyle:'italic', color: theme.colors.textWarm }]}>
                "{result.daily}"
              </Text>
            </Card>
          </>
        )}

        <GoldButton
          title="YENİ ANALİZ"
          onPress={reset}
          variant="outline"
          style={{ marginTop: theme.spacing.xl }}
        />
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
  scroll: { padding: theme.spacing.lg, paddingBottom: theme.spacing.xxxl },

  // Lang chips
  langChip: {
    flexDirection:'row', alignItems:'center', gap:5,
    paddingHorizontal:12, paddingVertical:8,
    borderRadius: theme.radius.full,
    borderWidth:1, borderColor: theme.colors.border,
    marginRight:8,
  },
  langChipActive: { borderColor: theme.colors.gold, backgroundColor: theme.colors.goldGlow },
  langText:       { ...theme.typography.caption, color: theme.colors.textMuted, fontSize:11 },
  langTextActive: { color: theme.colors.gold, fontWeight:'700' },

  // Pick
  pickArea: {
    backgroundColor: theme.colors.surface,
    borderRadius: theme.radius.xl, borderWidth:1,
    borderColor: theme.colors.border,
    borderStyle: 'dashed',
    padding: theme.spacing.xl, alignItems:'center',
  },
  pickTitle: { ...theme.typography.h2, marginBottom:8 },
  pickDesc:  { ...theme.typography.body, textAlign:'center', color: theme.colors.textWarm },
  tipsTitle: { ...theme.typography.h3, fontSize:13, marginBottom:8 },
  tip:       { ...theme.typography.caption, marginBottom:4, fontSize:12, color: theme.colors.textWarm },

  // Preview
  previewImg: {
    width:  width - theme.spacing.xl * 2,
    height: width - theme.spacing.xl * 2,
    borderRadius: theme.radius.xl,
  },
  changeBtn: {
    height:52, paddingHorizontal: theme.spacing.lg,
    borderRadius: theme.radius.md, borderWidth:1,
    borderColor: theme.colors.border,
    alignItems:'center', justifyContent:'center',
  },
  changeBtnText: { ...theme.typography.label, color: theme.colors.textMuted, fontSize:12 },
  analyzingText: { ...theme.typography.bodyWarm },

  // Result
  resultTop: { flexDirection:'row', gap: theme.spacing.lg, alignItems:'center', marginBottom: theme.spacing.md },
  resultImg: { width:90, height:90, borderRadius: theme.radius.lg },

  // Chat CTA
  chatCTA:    { marginBottom: theme.spacing.md },
  chatCTARow: { flexDirection:'row', alignItems:'center', gap:12 },
  chatCTAIcon:{
    width:48, height:48, borderRadius: theme.radius.lg,
    backgroundColor: theme.colors.warmAmberGlow,
    borderWidth:1, borderColor:`${theme.colors.warmAmber}30`,
    alignItems:'center', justifyContent:'center',
  },
  chatCTATitle: { ...theme.typography.h3, fontSize:14, marginBottom:3 },
  chatCTADesc:  { ...theme.typography.caption, color: theme.colors.textWarm, fontSize:11 },

  // Fashion CTA
  fashionCTA:    { marginBottom: theme.spacing.md, borderColor:'#9B5DE528', backgroundColor: theme.colors.surface },
  fashionCTARow: { flexDirection:'row', alignItems:'center', gap:12 },
  fashionCTAIcon:{
    width:48, height:48, borderRadius: theme.radius.lg,
    backgroundColor: '#9B5DE512',
    borderWidth:1, borderColor:'#9B5DE530',
    alignItems:'center', justifyContent:'center',
  },
  fashionCTATitle: { ...theme.typography.h3, fontSize:14, marginBottom:3 },
  fashionCTADesc:  { ...theme.typography.caption, color: theme.colors.textWarm, fontSize:11 },

  // Attrs
  attrCard: { marginBottom:8 },
  attrName: { ...theme.typography.h3, fontSize:13, marginBottom:3 },
  attrDesc: { ...theme.typography.caption, fontSize:11, color: theme.colors.textWarm },
  moduleText: { ...theme.typography.bodyWarm, lineHeight:22, fontSize:13 },

  // Quality Check
  qualityImg: {
    width: width - theme.spacing.xl * 2,
    height: width - theme.spacing.xl * 2,
    borderRadius: theme.radius.xl,
    marginBottom: theme.spacing.lg,
  },
  scoreCard: {
    padding: theme.spacing.lg,
    marginBottom: theme.spacing.lg,
    borderWidth: 2,
    alignItems: 'center',
  },
  scoreTitle: {
    ...theme.typography.h1,
    fontSize: 32,
  },
  scoreSubtitle: {
    ...theme.typography.h3,
    fontSize: 14,
    marginTop: 4,
  },
  recommendation: {
    ...theme.typography.body,
    textAlign: 'center',
  },
  metricCard: {
    marginBottom: theme.spacing.md,
  },
  metricHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: 8,
  },
  metricLabel: {
    ...theme.typography.label,
    fontSize: 12,
    fontWeight: '600',
  },
  metricValue: {
    ...theme.typography.caption,
    fontSize: 11,
    color: theme.colors.textMuted,
  },
  progressContainer: {
    height: 6,
    backgroundColor: theme.colors.border,
    borderRadius: 3,
    overflow: 'hidden',
    marginBottom: 8,
  },
  progressBar: {
    height: '100%',
    borderRadius: 3,
  },
  metricScore: {
    ...theme.typography.caption,
    fontSize: 10,
    color: theme.colors.textMuted,
  },
  retakeBtn: {
    flex: 1,
    height: 52,
    borderRadius: theme.radius.md,
    borderWidth: 1,
    borderColor: theme.colors.border,
    alignItems: 'center',
    justifyContent: 'center',
  },
  retakeBtnText: {
    ...theme.typography.label,
    color: theme.colors.textMuted,
    fontSize: 12,
  },
});

export default AnalysisScreen;

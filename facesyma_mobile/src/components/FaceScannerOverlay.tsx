/**
 * FaceScannerOverlay.tsx
 * ========================
 * Mistik biyometrik yüz tarama animasyonu
 *
 * Features:
 * - 27 facial landmark noktası (bölgeye göre renkli, cascading)
 * - Her noktadan sonar ripple halkası
 * - Altın köşe hedefleme parantezleri
 * - Neon mavi tarama dalgası (üç katmanlı)
 * - Mavi ↔ altın arasında nefes alan border
 * - Dramatik mistik ilerleme mesajları
 */

import React, { useEffect, useRef, useState } from 'react';
import {
  View,
  Image,
  Animated,
  Dimensions,
  StyleSheet,
  Text,
} from 'react-native';
import theme from '../utils/theme';
const { colors } = theme;
import { t } from '../utils/i18n';

// ── Types ─────────────────────────────────────────────────────────────────────

interface FaceScannerPoint {
  id: string;
  x: number;       // 0-1 (width yüzdesi)
  y: number;       // 0-1 (height yüzdesi)
  region: string;
  delay: number;   // ms
}

interface Props {
  imageUri: string;
  progress?: number;    // 0-100
  scanDuration?: number;
  lang?: string;
}

const { width: screenWidth } = Dimensions.get('window');

// ── Landmark Noktaları ────────────────────────────────────────────────────────

const FACIAL_LANDMARKS: FaceScannerPoint[] = [
  // Alın (suspense start)
  { id: 'forehead_left',        x: 0.35, y: 0.15, region: 'forehead', delay: 200 },
  { id: 'forehead_right',       x: 0.65, y: 0.15, region: 'forehead', delay: 400 },

  // Gözler (gizemli açılış)
  { id: 'eye_left_1',           x: 0.30, y: 0.35, region: 'eye', delay: 600 },
  { id: 'eye_left_2',           x: 0.35, y: 0.33, region: 'eye', delay: 700 },
  { id: 'eye_left_3',           x: 0.40, y: 0.35, region: 'eye', delay: 800 },
  { id: 'eye_left_4',           x: 0.35, y: 0.38, region: 'eye', delay: 900 },
  { id: 'eye_right_1',          x: 0.60, y: 0.35, region: 'eye', delay: 1000 },
  { id: 'eye_right_2',          x: 0.65, y: 0.33, region: 'eye', delay: 1100 },
  { id: 'eye_right_3',          x: 0.70, y: 0.35, region: 'eye', delay: 1200 },
  { id: 'eye_right_4',          x: 0.65, y: 0.38, region: 'eye', delay: 1300 },

  // Yanaklar (dışa yayılma)
  { id: 'cheek_left_1',         x: 0.20, y: 0.40, region: 'cheek', delay: 1400 },
  { id: 'cheek_left_2',         x: 0.15, y: 0.50, region: 'cheek', delay: 1600 },
  { id: 'cheek_right_1',        x: 0.80, y: 0.40, region: 'cheek', delay: 1500 },
  { id: 'cheek_right_2',        x: 0.85, y: 0.50, region: 'cheek', delay: 1700 },

  // Burun (merkez dramatik duraklama)
  { id: 'nose_1',               x: 0.50, y: 0.40, region: 'nose', delay: 1800 },
  { id: 'nose_2',               x: 0.48, y: 0.45, region: 'nose', delay: 2000 },
  { id: 'nose_3',               x: 0.52, y: 0.45, region: 'nose', delay: 2200 },
  { id: 'nose_4',               x: 0.50, y: 0.50, region: 'nose', delay: 2400 },

  // Ağız (alt yüz sırrı)
  { id: 'mouth_1',              x: 0.45, y: 0.55, region: 'mouth', delay: 2600 },
  { id: 'mouth_2',              x: 0.50, y: 0.58, region: 'mouth', delay: 2800 },
  { id: 'mouth_3',              x: 0.55, y: 0.55, region: 'mouth', delay: 3000 },
  { id: 'mouth_4',              x: 0.48, y: 0.60, region: 'mouth', delay: 3200 },
  { id: 'mouth_5',              x: 0.52, y: 0.60, region: 'mouth', delay: 3400 },

  // Çene (final çerçeveleme)
  { id: 'jaw_left',             x: 0.25, y: 0.62, region: 'jawline', delay: 3600 },
  { id: 'jaw_center_left',      x: 0.40, y: 0.68, region: 'jawline', delay: 3900 },
  { id: 'jaw_center_right',     x: 0.60, y: 0.68, region: 'jawline', delay: 4100 },
  { id: 'jaw_right',            x: 0.75, y: 0.62, region: 'jawline', delay: 4400 },
];

const REGION_COLORS: Record<string, string> = {
  eye:      '#5A9AE0',   // Elektrik mavi
  nose:     '#5CB87A',   // Yeşil
  mouth:    '#D95F5F',   // Sıcak kırmızı
  cheek:    '#D4619A',   // Pembe
  jawline:  '#D4853A',   // Amber/turuncu
  forehead: '#9B59B6',   // Mor
};

// ── Corner Bracket (Hedefleme Parantezi) ─────────────────────────────────────

const CornerBracket: React.FC<{
  corner: 'tl' | 'tr' | 'bl' | 'br';
  opacity: Animated.Value;
}> = ({ corner, opacity }) => {
  const SIZE = 22;
  const OFFSET = 9;
  const isTop  = corner[0] === 't';
  const isLeft = corner[1] === 'l';

  const edgeV: { top?: number; bottom?: number } = isTop  ? { top: OFFSET }  : { bottom: OFFSET };
  const edgeH: { left?: number; right?: number } = isLeft ? { left: OFFSET } : { right: OFFSET };

  return (
    <Animated.View
      pointerEvents="none"
      style={{ position: 'absolute', ...edgeV, ...edgeH, width: SIZE, height: SIZE, opacity }}
    >
      {/* Yatay çizgi */}
      <View style={{
        position: 'absolute',
        ...(isTop ? { top: 0 } : { bottom: 0 }),
        ...(isLeft ? { left: 0 } : { right: 0 }),
        width: SIZE, height: 2.5,
        backgroundColor: colors.gold,
        shadowColor: colors.gold,
        shadowRadius: 5, shadowOpacity: 1,
      }} />
      {/* Dikey çizgi */}
      <View style={{
        position: 'absolute',
        ...(isTop ? { top: 0 } : { bottom: 0 }),
        ...(isLeft ? { left: 0 } : { right: 0 }),
        width: 2.5, height: SIZE,
        backgroundColor: colors.gold,
        shadowColor: colors.gold,
        shadowRadius: 5, shadowOpacity: 1,
      }} />
    </Animated.View>
  );
};

// ── Animated Point (Ripple'lı Landmark Noktası) ───────────────────────────────

const AnimatedPoint: React.FC<{
  point: FaceScannerPoint;
  imageWidth: number;
  imageHeight: number;
}> = ({ point, imageWidth, imageHeight }) => {
  const scaleAnim     = useRef(new Animated.Value(0)).current;
  const opacityAnim   = useRef(new Animated.Value(0)).current;
  const glowAnim      = useRef(new Animated.Value(0)).current;
  const rippleScale   = useRef(new Animated.Value(1)).current;
  const rippleOpacity = useRef(new Animated.Value(0)).current;

  useEffect(() => {
    // Nokta belirir (spring ile daha canlı)
    Animated.sequence([
      Animated.delay(point.delay),
      Animated.parallel([
        Animated.spring(scaleAnim, {
          toValue: 1, friction: 5, tension: 220, useNativeDriver: true,
        }),
        Animated.timing(opacityAnim, {
          toValue: 1, duration: 220, useNativeDriver: true,
        }),
      ]),
    ]).start(() => {
      // Sonar ripple — nokta belirdikten hemen sonra
      rippleOpacity.setValue(0.9);
      Animated.parallel([
        Animated.timing(rippleScale, {
          toValue: 4.5, duration: 750, useNativeDriver: true,
        }),
        Animated.timing(rippleOpacity, {
          toValue: 0, duration: 750, useNativeDriver: true,
        }),
      ]).start();
    });

    // Sürekli glow nabız
    Animated.loop(
      Animated.sequence([
        Animated.timing(glowAnim, { toValue: 1, duration: 950, useNativeDriver: false }),
        Animated.timing(glowAnim, { toValue: 0, duration: 950, useNativeDriver: false }),
      ])
    ).start();
  }, []);

  const color  = REGION_COLORS[point.region] || '#5A9AE0';
  const px     = point.x * imageWidth;
  const py     = point.y * imageHeight;

  const glowSize    = glowAnim.interpolate({ inputRange: [0, 1], outputRange: [5, 15] });
  const glowOpacity = glowAnim.interpolate({ inputRange: [0, 1], outputRange: [0.12, 0.45] });

  return (
    <View style={[styles.pointWrap, { left: px - 12, top: py - 12 }]}>
      {/* Ripple halkası */}
      <Animated.View style={[styles.ripple, {
        borderColor: color,
        opacity: rippleOpacity,
        transform: [{ scale: rippleScale }],
      }]} />

      {/* Glow halo */}
      <Animated.View style={[styles.glowBg, {
        width: glowSize, height: glowSize,
        backgroundColor: color,
        opacity: glowOpacity,
      }]} />

      {/* Merkez nokta */}
      <Animated.View style={[styles.dot, {
        backgroundColor: color,
        transform: [{ scale: scaleAnim }],
        opacity: opacityAnim,
        shadowColor: color,
      }]} />
    </View>
  );
};

// ── Scan Wave (Neon Tarama Çizgisi) ──────────────────────────────────────────

const ScanningWave: React.FC<{ imageHeight: number }> = ({ imageHeight }) => {
  const waveAnim = useRef(new Animated.Value(0)).current;

  useEffect(() => {
    Animated.loop(
      Animated.sequence([
        Animated.timing(waveAnim, {
          toValue: 1, duration: 1700, useNativeDriver: true,
        }),
        Animated.delay(700),
      ])
    ).start();
  }, []);

  const translateY = waveAnim.interpolate({
    inputRange: [0, 1],
    outputRange: [-15, imageHeight + 15],
  });

  return (
    <Animated.View
      pointerEvents="none"
      style={[StyleSheet.absoluteFill, {
        transform: [{ translateY }],
        borderRadius: 12,
        overflow: 'hidden',
      }]}
    >
      {/* Parlak önce gelen çizgi */}
      <View style={styles.waveLine} />
      {/* Dalga gövdesi üst */}
      <View style={styles.waveBodyTop} />
      {/* Dalga gövdesi alt (sönük) */}
      <View style={styles.waveBodyBot} />
      {/* Altın iz */}
      <View style={styles.waveTrail} />
    </Animated.View>
  );
};

// ── Pulsing Border (Nefes Alan Kenar) ────────────────────────────────────────

const PulsingBorder: React.FC = () => {
  const pulseAnim = useRef(new Animated.Value(0)).current;

  useEffect(() => {
    Animated.loop(
      Animated.sequence([
        Animated.timing(pulseAnim, { toValue: 1, duration: 1800, useNativeDriver: false }),
        Animated.timing(pulseAnim, { toValue: 0, duration: 1800, useNativeDriver: false }),
      ])
    ).start();
  }, []);

  const borderColor = pulseAnim.interpolate({
    inputRange: [0, 0.5, 1],
    outputRange: [
      'rgba(90, 154, 224, 0.70)',
      'rgba(201, 168, 76, 0.95)',
      'rgba(90, 154, 224, 0.70)',
    ],
  });

  return (
    <Animated.View
      pointerEvents="none"
      style={[StyleSheet.absoluteFill, {
        borderRadius: 12,
        borderWidth: 1.5,
        borderColor,
      }]}
    />
  );
};

// ── İlerleme Mesajları ─────────────────────────────────────────────────────────

function getProgressMsg(p: number, lang: string): string {
  if (p <= 12) return t('scanner.msg_0', lang);
  if (p <= 28) return t('scanner.msg_12', lang);
  if (p <= 48) return t('scanner.msg_28', lang);
  if (p <= 65) return t('scanner.msg_48', lang);
  if (p <= 82) return t('scanner.msg_65', lang);
  return t('scanner.msg_82', lang);
}

// ── Ana Bileşen ───────────────────────────────────────────────────────────────

export const FaceScannerOverlay: React.FC<Props> = ({
  imageUri,
  progress = 0,
  scanDuration = 5000,
  lang = 'tr',
}) => {
  const animValue      = useRef(new Animated.Value(0)).current;
  const cornerOpacity  = useRef(new Animated.Value(0)).current;
  const headerOpacity  = useRef(new Animated.Value(0)).current;
  const [imageDimensions, setImageDimensions] = useState({ width: 0, height: 0 });

  useEffect(() => {
    Image.getSize(imageUri, (w, h) => {
      if (w <= 0 || h <= 0) return;
      const scale = Math.min((screenWidth * 0.88) / w, 380 / h);
      setImageDimensions({ width: w * scale, height: h * scale });
    });

    // Giriş animasyonları
    Animated.stagger(120, [
      Animated.timing(headerOpacity, { toValue: 1, duration: 450, useNativeDriver: true }),
      Animated.timing(cornerOpacity, { toValue: 1, duration: 450, useNativeDriver: false }),
    ]).start();
  }, [imageUri]);

  useEffect(() => {
    Animated.timing(animValue, {
      toValue: progress, duration: 250, useNativeDriver: false,
    }).start();
  }, [progress]);

  const progressWidth = animValue.interpolate({
    inputRange: [0, 100],
    outputRange: ['0%', '100%'],
  });

  const p = Math.round(progress);
  const { width: imgW, height: imgH } = imageDimensions;

  return (
    <View style={styles.container}>
      {/* Başlık */}
      <Animated.Text style={[styles.scanHeader, { opacity: headerOpacity }]}>
        ◈  FACESYMA  SCAN  ◈
      </Animated.Text>

      {/* Tarayıcı çerçeve */}
      <View style={[
        styles.frame,
        {
          width:  imgW || screenWidth * 0.88,
          height: imgH || 300,
        },
      ]}>
        {/* Fotoğraf */}
        {imgW > 0 && (
          <Image
            source={{ uri: imageUri }}
            style={{
              width: imgW,
              height: imgH,
              borderRadius: 12,
            }}
          />
        )}

        {/* Karanlık mistik overlay */}
        <View style={[StyleSheet.absoluteFill, styles.overlay]} />

        {/* Neon tarama dalgası */}
        {imgH > 0 && (
          <ScanningWave imageHeight={imgH} />
        )}

        {/* Landmark noktaları */}
        {imgW > 0 && FACIAL_LANDMARKS.map((point) => (
          <AnimatedPoint
            key={point.id}
            point={point}
            imageWidth={imgW}
            imageHeight={imgH}
          />
        ))}

        {/* Köşe parantezleri */}
        {(['tl', 'tr', 'bl', 'br'] as const).map(c => (
          <CornerBracket key={c} corner={c} opacity={cornerOpacity} />
        ))}

        {/* Nefes alan kenar */}
        <PulsingBorder />
      </View>

      {/* İlerleme çubuğu */}
      <View style={styles.progressWrap}>
        <View style={styles.progressTrack}>
          <Animated.View style={[styles.progressFill, { width: progressWidth }]} />
        </View>
        <Text style={styles.progressMsg}>{getProgressMsg(p, lang)}</Text>
      </View>

      {/* Durum satırı */}
      <View style={styles.statusRow}>
        <Text style={styles.statusEmoji}>
          {p <= 30 ? '✨' : p <= 65 ? '🌟' : '💫'}
        </Text>
        <Text style={styles.statusText}>{p}%  {t('scanner.status', lang)}</Text>
      </View>
    </View>
  );
};

// ── Stiller ───────────────────────────────────────────────────────────────────

const styles = StyleSheet.create({
  container: {
    alignItems: 'center',
    gap: 16,
    paddingVertical: 20,
  },
  scanHeader: {
    fontSize: 10,
    fontWeight: '700',
    letterSpacing: 4,
    color: colors.gold,
    textAlign: 'center',
  },
  frame: {
    position: 'relative',
    overflow: 'hidden',
    borderRadius: 12,
    // Hafif dış gölge
    shadowColor: colors.gold,
    shadowRadius: 16,
    shadowOpacity: 0.25,
    shadowOffset: { width: 0, height: 0 },
    elevation: 8,
  },
  overlay: {
    backgroundColor: 'rgba(0, 4, 18, 0.28)',
    borderRadius: 12,
  },
  pointWrap: {
    position: 'absolute',
    width: 24,
    height: 24,
    alignItems: 'center',
    justifyContent: 'center',
  },
  ripple: {
    position: 'absolute',
    width: 10,
    height: 10,
    borderRadius: 5,
    borderWidth: 1.5,
  },
  glowBg: {
    position: 'absolute',
    borderRadius: 8,
  },
  dot: {
    width: 7,
    height: 7,
    borderRadius: 3.5,
    shadowOffset: { width: 0, height: 0 },
    shadowOpacity: 0.95,
    shadowRadius: 6,
    elevation: 4,
  },
  progressWrap: {
    width: '100%',
    paddingHorizontal: 20,
    gap: 8,
  },
  progressTrack: {
    height: 5,
    backgroundColor: 'rgba(201, 168, 76, 0.15)',
    borderRadius: 3,
    overflow: 'hidden',
  },
  progressFill: {
    height: '100%',
    backgroundColor: colors.gold,
    borderRadius: 3,
    shadowColor: colors.gold,
    shadowRadius: 4,
    shadowOpacity: 0.6,
    shadowOffset: { width: 0, height: 0 },
  },
  progressMsg: {
    fontSize: 12,
    color: colors.textWarm,
    textAlign: 'center',
    fontWeight: '600',
    letterSpacing: 0.3,
  },
  statusRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  statusEmoji: {
    fontSize: 20,
  },
  statusText: {
    fontSize: 13,
    color: colors.gold,
    fontWeight: '700',
    letterSpacing: 2,
  },
  waveLine:    { height: 2.5, backgroundColor: 'rgba(80, 190, 255, 0.95)' },
  waveBodyTop: { height: 45,  backgroundColor: 'rgba(70, 150, 255, 0.10)' },
  waveBodyBot: { height: 35,  backgroundColor: 'rgba(70, 150, 255, 0.04)' },
  waveTrail:   { height: 1,   backgroundColor: 'rgba(201, 168, 76, 0.55)' },
});

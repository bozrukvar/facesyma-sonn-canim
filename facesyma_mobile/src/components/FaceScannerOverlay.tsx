import React, { useEffect, useRef } from 'react';
import { View, Image, Animated, Dimensions, StyleSheet, Text } from 'react-native';
import theme from '../utils/theme';
const { colors } = theme;
import { t } from '../utils/i18n';

interface Props {
  imageUri: string;
  progress?: number;
  scanDuration?: number;  // toplam tarama süresi ms — dalga hızını buna göre ayarlar
  lang?: string;
  faceCenter?: { cx: number; cy: number; fw?: number; fh?: number } | null;
  imageSize?: { width: number; height: number };
}

const { width: screenWidth } = Dimensions.get('window');

// ── Dönen Yay (Rotating Arc) ──────────────────────────────────────────────────

const RotatingArc: React.FC<{
  size: number;
  cx: number;
  cy: number;
  color: string;
  duration: number;
  clockwise?: boolean;
  delay?: number;
  thickness?: number;
  gap?: 'lr' | 'tb' | 'none';
  opacity?: number;
}> = ({ size, cx, cy, color, duration, clockwise = true, delay = 0, thickness = 1.2, gap = 'lr', opacity = 0.75 }) => {
  const rotAnim = useRef(new Animated.Value(0)).current;
  const fadeAnim = useRef(new Animated.Value(0)).current;

  useEffect(() => {
    Animated.timing(fadeAnim, {
      toValue: opacity, duration: 700, delay, useNativeDriver: true,
    }).start();
    Animated.loop(
      Animated.timing(rotAnim, { toValue: 1, duration, useNativeDriver: true })
    ).start();
  }, []);

  const rotate = rotAnim.interpolate({
    inputRange: [0, 1],
    outputRange: clockwise ? ['0deg', '360deg'] : ['0deg', '-360deg'],
  });

  const transparent = 'transparent';
  const borderStyle =
    gap === 'lr' ? { borderLeftColor: transparent, borderRightColor: transparent } :
    gap === 'tb' ? { borderTopColor: transparent,  borderBottomColor: transparent } :
    {};

  return (
    <Animated.View
      pointerEvents="none"
      style={{
        position: 'absolute',
        left: cx - size / 2,
        top:  cy - size / 2,
        width: size,
        height: size,
        borderRadius: size / 2,
        borderWidth: thickness,
        borderColor: color,
        ...borderStyle,
        opacity: fadeAnim,
        transform: [{ rotate }],
      }}
    />
  );
};

// ── Altın Oran Overlay — yüze oransal (yüz bbox varsa) ───────────────────────

// Orijinal görüntü koordinatlarındaki yüz bbox'ını frame koordinatlarına çevirir
function toFaceFrameRect(
  cx: number, cy: number, fw: number, fh: number,
  imgW: number, imgH: number,
): { left: number; top: number; width: number; height: number } {
  const scale   = Math.max(FRAME_W / imgW, FRAME_H / imgH);
  const offsetX = (FRAME_W - imgW * scale) / 2;
  const offsetY = (FRAME_H - imgH * scale) / 2;
  const left    = (cx - fw / 2) * imgW * scale + offsetX;
  const top     = (cy - fh / 2) * imgH * scale + offsetY;
  const width   = fw * imgW * scale;
  const height  = fh * imgH * scale;
  return { left, top, width, height };
}

const GoldenRatioOverlay: React.FC<{
  faceRect: { left: number; top: number; width: number; height: number } | null;
  progress: number;
}> = ({ faceRect, progress }) => {
  const outerOp    = useRef(new Animated.Value(0)).current;
  const eyeLineOp  = useRef(new Animated.Value(0)).current;
  const noseLineOp = useRef(new Animated.Value(0)).current;
  const eyeBoxOp   = useRef(new Animated.Value(0)).current;
  const goldenBoxOp = useRef(new Animated.Value(0)).current;
  const thirdOp    = useRef(new Animated.Value(0)).current;

  useEffect(() => {
    const anim = (val: Animated.Value) =>
      Animated.timing(val, { toValue: 1, duration: 500, useNativeDriver: true }).start();
    if (progress >= 18) anim(outerOp);
    if (progress >= 32) anim(eyeLineOp);
    if (progress >= 46) anim(noseLineOp);
    if (progress >= 60) anim(eyeBoxOp);
    if (progress >= 72) anim(goldenBoxOp);
    if (progress >= 84) anim(thirdOp);
  }, [progress]);

  // Yüz yoksa frame'e sabit fallback çizgiler
  if (!faceRect) {
    const CYAN = 'rgba(80, 210, 240, 1.0)';
    const GOLD = 'rgba(201, 168, 76, 1.0)';
    return (
      <>
        <Animated.View pointerEvents="none" style={{
          position: 'absolute', left: 0, top: FRAME_H * 0.34,
          width: FRAME_W, height: 2.8, backgroundColor: CYAN, opacity: eyeLineOp,
        }} />
        <Animated.View pointerEvents="none" style={{
          position: 'absolute', left: 0, top: FRAME_H * 0.52,
          width: FRAME_W, height: 2.8, backgroundColor: CYAN, opacity: noseLineOp,
        }} />
        <Animated.View pointerEvents="none" style={{
          position: 'absolute', left: FRAME_W * 0.5 - 1.4, top: 0,
          width: 2.8, height: FRAME_H, backgroundColor: CYAN, opacity: eyeLineOp,
        }} />
        <Animated.View pointerEvents="none" style={{
          position: 'absolute', left: 0, top: FRAME_H * 0.618,
          width: FRAME_W, height: 2.8, backgroundColor: GOLD, opacity: goldenBoxOp,
        }} />
      </>
    );
  }

  const { left, top, width, height } = faceRect;
  const φ = 1.618;

  // Yatay referans çizgiler (yüz yüksekliğinin oranları)
  const eyeY    = top + height * 0.36;  // göz hizası
  const noseY   = top + height * 0.60;  // burun tabanı
  const mouthY  = top + height * 0.76;  // ağız hizası

  // Altın oran dikdörtgeni: genişlik = yükseklik / φ, ortalanmış
  const goldenW    = height / φ;
  const goldenLeft = left + (width - goldenW) / 2;

  // Yatay üçler (alın / orta yüz / alt yüz)
  const thirdH = height / 3;

  // Göz kutuları: her göz yüz genişliğinin ~%22'si
  const eyeW     = width * 0.23;
  const eyeH     = height * 0.13;
  const leftEyeX  = left + width * 0.14;
  const rightEyeX = left + width * 0.63;
  const eyeBoxTop = top + height * 0.28;

  const GOLD    = 'rgba(201, 168, 76, 1.0)';
  const CYAN    = 'rgba(80, 210, 240, 1.0)';
  const GREEN   = 'rgba(80, 220, 130, 1.0)';
  const MAGENTA = 'rgba(220, 100, 210, 1.0)';
  const WHITE   = 'rgba(255, 255, 255, 0.90)';
  const LINE    = 2.8;
  const BOX     = 2.6;

  return (
    <>
      {/* Dış yüz çerçevesi */}
      <Animated.View pointerEvents="none" style={{
        position: 'absolute', left, top, width, height,
        borderWidth: LINE, borderColor: GOLD, opacity: outerOp,
      }} />

      {/* Dikey merkez çizgisi */}
      <Animated.View pointerEvents="none" style={{
        position: 'absolute', left: left + width / 2 - 0.75, top,
        width: LINE, height, backgroundColor: CYAN, opacity: eyeLineOp,
      }} />

      {/* Göz yatay çizgisi */}
      <Animated.View pointerEvents="none" style={{
        position: 'absolute', left, top: eyeY,
        width, height: LINE, backgroundColor: CYAN, opacity: eyeLineOp,
      }} />

      {/* Burun tabanı çizgisi */}
      <Animated.View pointerEvents="none" style={{
        position: 'absolute', left, top: noseY,
        width, height: LINE, backgroundColor: CYAN, opacity: noseLineOp,
      }} />

      {/* Ağız çizgisi */}
      <Animated.View pointerEvents="none" style={{
        position: 'absolute', left, top: mouthY,
        width, height: LINE, backgroundColor: CYAN, opacity: thirdOp,
      }} />

      {/* Altın oran dikdörtgeni (φ proportional) */}
      <Animated.View pointerEvents="none" style={{
        position: 'absolute', left: goldenLeft, top, width: goldenW, height,
        borderWidth: BOX, borderColor: GREEN, opacity: goldenBoxOp,
      }} />

      {/* Yatay üç bölge (alın/orta/alt) */}
      <Animated.View pointerEvents="none" style={{
        position: 'absolute', left, top: top + thirdH,
        width, height: LINE, backgroundColor: WHITE, opacity: thirdOp,
      }} />
      <Animated.View pointerEvents="none" style={{
        position: 'absolute', left, top: top + thirdH * 2,
        width, height: LINE, backgroundColor: WHITE, opacity: thirdOp,
      }} />

      {/* Sol göz kutusu */}
      <Animated.View pointerEvents="none" style={{
        position: 'absolute', left: leftEyeX, top: eyeBoxTop,
        width: eyeW, height: eyeH,
        borderWidth: BOX, borderColor: MAGENTA, opacity: eyeBoxOp,
      }} />

      {/* Sağ göz kutusu */}
      <Animated.View pointerEvents="none" style={{
        position: 'absolute', left: rightEyeX, top: eyeBoxTop,
        width: eyeW, height: eyeH,
        borderWidth: BOX, borderColor: MAGENTA, opacity: eyeBoxOp,
      }} />
    </>
  );
};

// ── Merkez Nişangah ───────────────────────────────────────────────────────────

const CenterReticle: React.FC<{ cx: number; cy: number; progress: number }> = ({
  cx, cy, progress,
}) => {
  const pulseAnim = useRef(new Animated.Value(0)).current;
  const fadeAnim  = useRef(new Animated.Value(0)).current;

  useEffect(() => {
    if (progress < 15) return;
    Animated.timing(fadeAnim, { toValue: 1, duration: 600, useNativeDriver: true }).start();
    Animated.loop(
      Animated.sequence([
        Animated.timing(pulseAnim, { toValue: 1, duration: 1400, useNativeDriver: true }),
        Animated.timing(pulseAnim, { toValue: 0, duration: 1400, useNativeDriver: true }),
      ])
    ).start();
  }, [progress >= 15]);

  const scaleVal = pulseAnim.interpolate({ inputRange: [0, 1], outputRange: [0.85, 1.15] });
  const glowOp   = pulseAnim.interpolate({ inputRange: [0, 1], outputRange: [0.15, 0.5] });

  const R = 14;
  return (
    <Animated.View pointerEvents="none" style={{
      position: 'absolute', left: cx - R, top: cy - R,
      width: R * 2, height: R * 2, opacity: fadeAnim,
    }}>
      <Animated.View style={{
        position: 'absolute', left: 0, top: 0, width: R * 2, height: R * 2,
        borderRadius: R, backgroundColor: colors.gold,
        opacity: glowOp, transform: [{ scale: scaleVal }],
      }} />
      <View style={{
        position: 'absolute', left: R - 3, top: R - 3,
        width: 6, height: 6, borderRadius: 3,
        backgroundColor: colors.gold,
        shadowColor: colors.gold, shadowRadius: 6, shadowOpacity: 1,
      }} />
    </Animated.View>
  );
};

// ── Scan Dalgası ─────────────────────────────────────────────────────────────

const ScanningWave: React.FC<{ imageHeight: number; sweepDuration?: number }> = ({
  imageHeight,
  sweepDuration = 2167,
}) => {
  const waveAnim = useRef(new Animated.Value(0)).current;

  useEffect(() => {
    Animated.loop(
      Animated.timing(waveAnim, { toValue: 1, duration: sweepDuration, useNativeDriver: true })
    ).start();
  }, []);

  const translateY = waveAnim.interpolate({
    inputRange: [0, 1],
    outputRange: [-10, imageHeight + 10],
  });

  return (
    <Animated.View
      pointerEvents="none"
      style={[StyleSheet.absoluteFill, { transform: [{ translateY }] }]}
    >
      <View style={{ height: 3.5, backgroundColor: 'rgba(201, 168, 76, 1.0)', shadowColor: colors.gold, shadowRadius: 8, shadowOpacity: 1 }} />
      <View style={{ height: 55,  backgroundColor: 'rgba(201, 168, 76, 0.13)' }} />
    </Animated.View>
  );
};

// ── Nefes Alan Kenar ─────────────────────────────────────────────────────────

const PulsingBorder: React.FC = () => {
  const pulseAnim = useRef(new Animated.Value(0)).current;

  useEffect(() => {
    Animated.loop(
      Animated.sequence([
        Animated.timing(pulseAnim, { toValue: 1, duration: 2200, useNativeDriver: false }),
        Animated.timing(pulseAnim, { toValue: 0, duration: 2200, useNativeDriver: false }),
      ])
    ).start();
  }, []);

  const borderColor = pulseAnim.interpolate({
    inputRange: [0, 0.5, 1],
    outputRange: [
      'rgba(80, 200, 230, 0.80)',
      'rgba(201, 168, 76, 1.0)',
      'rgba(80, 200, 230, 0.80)',
    ],
  });

  return (
    <Animated.View
      pointerEvents="none"
      style={[StyleSheet.absoluteFill, { borderRadius: 12, borderWidth: 2.2, borderColor }]}
    />
  );
};

// ── Köşe Parantezi ────────────────────────────────────────────────────────────

const CornerBracket: React.FC<{ corner: 'tl' | 'tr' | 'bl' | 'br'; opacity: Animated.Value }> = ({
  corner, opacity,
}) => {
  const SIZE = 22, OFFSET = 9;
  const isTop  = corner[0] === 't';
  const isLeft = corner[1] === 'l';
  const edgeV = isTop  ? { top: OFFSET }    : { bottom: OFFSET };
  const edgeH = isLeft ? { left: OFFSET }   : { right: OFFSET };
  return (
    <Animated.View pointerEvents="none"
      style={{ position: 'absolute', ...edgeV, ...edgeH, width: SIZE, height: SIZE, opacity }}>
      <View style={{
        position: 'absolute',
        ...(isTop ? { top: 0 } : { bottom: 0 }),
        ...(isLeft ? { left: 0 } : { right: 0 }),
        width: SIZE, height: 3,
        backgroundColor: colors.gold,
        shadowColor: colors.gold, shadowRadius: 5, shadowOpacity: 1,
      }} />
      <View style={{
        position: 'absolute',
        ...(isTop ? { top: 0 } : { bottom: 0 }),
        ...(isLeft ? { left: 0 } : { right: 0 }),
        width: 3, height: SIZE,
        backgroundColor: colors.gold,
        shadowColor: colors.gold, shadowRadius: 4, shadowOpacity: 1,
      }} />
    </Animated.View>
  );
};

// ── İlerleme Mesajı ───────────────────────────────────────────────────────────

function getProgressMsg(p: number, lang: string): string {
  if (p <= 12) return t('scanner.msg_0', lang);
  if (p <= 28) return t('scanner.msg_12', lang);
  if (p <= 48) return t('scanner.msg_28', lang);
  if (p <= 65) return t('scanner.msg_48', lang);
  if (p <= 82) return t('scanner.msg_65', lang);
  return t('scanner.msg_82', lang);
}

// ── Ana Bileşen ───────────────────────────────────────────────────────────────

// Sabit çerçeve boyutu — her fotoğraf aynı büyüklükte görünür
const FRAME_W = screenWidth * 0.88;
const FRAME_H = FRAME_W * 1.22;   // yaklaşık 4:5 portrait oranı

/**
 * resizeMode="cover" ile gösterilen orijinal bir görüntüdeki
 * (cx, cy) koordinatlarını frame koordinatlarına dönüştürür.
 */
function toFrameCoords(
  cx: number, cy: number,
  imgW: number, imgH: number,
): { x: number; y: number } {
  if (!imgW || !imgH) return { x: FRAME_W / 2, y: FRAME_H * 0.38 };
  // cover: iki eksenden büyük olanı frame'e tam sığdırır
  const scale   = Math.max(FRAME_W / imgW, FRAME_H / imgH);
  const offsetX = (FRAME_W - imgW * scale) / 2;
  const offsetY = (FRAME_H - imgH * scale) / 2;
  return {
    x: Math.max(FRAME_W * 0.15, Math.min(cx * imgW * scale + offsetX, FRAME_W * 0.85)),
    y: Math.max(FRAME_H * 0.10, Math.min(cy * imgH * scale + offsetY, FRAME_H * 0.70)),
  };
}

export const FaceScannerOverlay: React.FC<Props> = ({
  imageUri,
  progress = 0,
  scanDuration = 6500,
  lang = 'tr',
  faceCenter,
  imageSize,
}) => {
  const animValue     = useRef(new Animated.Value(0)).current;
  const cornerOpacity = useRef(new Animated.Value(0)).current;
  const headerOpacity = useRef(new Animated.Value(0)).current;

  useEffect(() => {
    Animated.stagger(150, [
      Animated.timing(headerOpacity, { toValue: 1, duration: 500, useNativeDriver: true }),
      Animated.timing(cornerOpacity, { toValue: 1, duration: 500, useNativeDriver: false }),
    ]).start();
  }, []);

  useEffect(() => {
    Animated.timing(animValue, { toValue: progress, duration: 300, useNativeDriver: false }).start();
  }, [progress]);

  const progressWidth = animValue.interpolate({ inputRange: [0, 100], outputRange: ['0%', '100%'] });
  const p = Math.round(progress);

  // Yüz merkezi: backend'den gelen koordinat varsa kullan, yoksa varsayılan
  const { x: faceCX, y: faceCY } = faceCenter && imageSize?.width
    ? toFrameCoords(faceCenter.cx, faceCenter.cy, imageSize.width, imageSize.height)
    : { x: FRAME_W / 2, y: FRAME_H * 0.38 };

  // Yüz bbox: fw/fh varsa frame koordinatlarına çevir (altın oran overlay için)
  const faceRect = (faceCenter?.fw && faceCenter?.fh && imageSize?.width)
    ? toFaceFrameRect(faceCenter.cx, faceCenter.cy, faceCenter.fw, faceCenter.fh, imageSize.width, imageSize.height)
    : null;

  return (
    <View style={styles.container}>
      <Animated.Text style={[styles.scanHeader, { opacity: headerOpacity }]}>
        ◈  FACESYMA  SCAN  ◈
      </Animated.Text>

      <View style={[styles.frame, { width: FRAME_W, height: FRAME_H }]}>
        {/* Fotoğraf — cover ile çerçeveyi tam doldurur */}
        <Image
          source={{ uri: imageUri }}
          style={[StyleSheet.absoluteFill, { borderRadius: 12 }]}
          resizeMode="cover"
        />

        {/* Hafif karartma */}
        <View style={[StyleSheet.absoluteFill, styles.overlay]} />

        {/* Tarama dalgası — 3 tam geçiş = scanDuration */}
        <ScanningWave imageHeight={FRAME_H} sweepDuration={Math.round(scanDuration / 3)} />

        {/* Dönen halkalar — 3 katman */}
        <RotatingArc
          size={FRAME_W * 0.82} cx={faceCX} cy={faceCY}
          color="rgba(80, 210, 240, 1.0)"
          duration={18000} clockwise thickness={2.6} gap="lr" delay={300}
        />
        <RotatingArc
          size={FRAME_W * 0.58} cx={faceCX} cy={faceCY}
          color="rgba(201, 168, 76, 1.0)"
          duration={11000} clockwise={false} thickness={3.2} gap="tb" delay={600}
        />
        <RotatingArc
          size={FRAME_W * 0.35} cx={faceCX} cy={faceCY}
          color="rgba(200, 160, 255, 1.0)"
          duration={7000} clockwise thickness={2.4} gap="none" delay={900}
        />

        {/* Altın oran / yüz oranı overlay */}
        <GoldenRatioOverlay faceRect={faceRect} progress={progress} />

        {/* Merkez nişangah */}
        <CenterReticle cx={faceCX} cy={faceCY} progress={progress} />

        {/* Köşe parantezleri */}
        {(['tl', 'tr', 'bl', 'br'] as const).map(c => (
          <CornerBracket key={c} corner={c} opacity={cornerOpacity} />
        ))}

        <PulsingBorder />
      </View>

      {/* İlerleme çubuğu */}
      <View style={styles.progressWrap}>
        <View style={styles.progressTrack}>
          <Animated.View style={[styles.progressFill, { width: progressWidth }]} />
        </View>
        <Text style={styles.progressMsg}>{getProgressMsg(p, lang)}</Text>
      </View>

      <View style={styles.statusRow}>
        <Text style={styles.statusEmoji}>{p <= 30 ? '✨' : p <= 65 ? '🌟' : '💫'}</Text>
        <Text style={styles.statusText}>{p}%  {t('scanner.status', lang)}</Text>
      </View>
    </View>
  );
};

const styles = StyleSheet.create({
  container: { alignItems: 'center', gap: 16, paddingVertical: 20 },
  scanHeader: {
    fontSize: 10, fontWeight: '700', letterSpacing: 4,
    color: colors.gold, textAlign: 'center',
  },
  frame: {
    position: 'relative', overflow: 'hidden', borderRadius: 12,
    shadowColor: colors.gold, shadowRadius: 18, shadowOpacity: 0.30,
    shadowOffset: { width: 0, height: 0 }, elevation: 8,
  },
  overlay: { backgroundColor: 'rgba(0, 4, 18, 0.22)', borderRadius: 12 },
  progressWrap: { width: '100%', paddingHorizontal: 20, gap: 8 },
  progressTrack: {
    height: 4, backgroundColor: 'rgba(201, 168, 76, 0.15)',
    borderRadius: 2, overflow: 'hidden',
  },
  progressFill: {
    height: '100%', backgroundColor: colors.gold, borderRadius: 2,
    shadowColor: colors.gold, shadowRadius: 4, shadowOpacity: 0.7,
    shadowOffset: { width: 0, height: 0 },
  },
  progressMsg: {
    fontSize: 12, color: colors.textWarm, textAlign: 'center',
    fontWeight: '600', letterSpacing: 0.3,
  },
  statusRow: { flexDirection: 'row', alignItems: 'center', gap: 8 },
  statusEmoji: { fontSize: 20 },
  statusText: {
    fontSize: 13, color: colors.gold, fontWeight: '700', letterSpacing: 2,
  },
});

/**
 * FaceScannerOverlay.tsx
 * ========================
 * Animasyonlu yüz taraması overlay - facial landmarks gösterir
 *
 * Features:
 * - Kullanıcı fotoğrafı üstüne nokta ve çizgiler
 * - Animated point appearance (0 → 100%)
 * - Connecting lines between facial regions
 * - Glow/pulse effects
 * - Progress bar
 */

import React, { useEffect, useState } from 'react';
import {
  View,
  Image,
  Animated,
  Dimensions,
  StyleSheet,
  Text,
} from 'react-native';
import theme from '../utils/theme';

interface FaceScannerPoint {
  id: string;
  x: number; // 0-1 (percentage of width)
  y: number; // 0-1 (percentage of height)
  region: string; // 'eye', 'nose', 'mouth', 'cheek', 'jawline', 'forehead'
  delay: number; // animation delay in ms
}

interface Props {
  imageUri: string;
  progress?: number; // 0-100
  scanDuration?: number; // total scan duration in ms
}

const { width: screenWidth } = Dimensions.get('window');

// 25 Facial landmark points (mapped to common facial regions)
// Delays adjusted for 5-second scan (more mysterious pacing)
const FACIAL_LANDMARKS: FaceScannerPoint[] = [
  // Forehead first (suspenseful start)
  { id: 'forehead_left', x: 0.35, y: 0.15, region: 'forehead', delay: 200 },
  { id: 'forehead_right', x: 0.65, y: 0.15, region: 'forehead', delay: 400 },

  // Eyes (reveal face gradually - mysterious)
  { id: 'eye_left_1', x: 0.30, y: 0.35, region: 'eye', delay: 600 },
  { id: 'eye_left_2', x: 0.35, y: 0.33, region: 'eye', delay: 700 },
  { id: 'eye_left_3', x: 0.40, y: 0.35, region: 'eye', delay: 800 },
  { id: 'eye_left_4', x: 0.35, y: 0.38, region: 'eye', delay: 900 },

  { id: 'eye_right_1', x: 0.60, y: 0.35, region: 'eye', delay: 1000 },
  { id: 'eye_right_2', x: 0.65, y: 0.33, region: 'eye', delay: 1100 },
  { id: 'eye_right_3', x: 0.70, y: 0.35, region: 'eye', delay: 1200 },
  { id: 'eye_right_4', x: 0.65, y: 0.38, region: 'eye', delay: 1300 },

  // Cheeks (expanding outward - mysterious spread)
  { id: 'cheek_left_1', x: 0.20, y: 0.40, region: 'cheek', delay: 1400 },
  { id: 'cheek_left_2', x: 0.15, y: 0.50, region: 'cheek', delay: 1600 },
  { id: 'cheek_right_1', x: 0.80, y: 0.40, region: 'cheek', delay: 1500 },
  { id: 'cheek_right_2', x: 0.85, y: 0.50, region: 'cheek', delay: 1700 },

  // Nose (center reveal - dramatic pause)
  { id: 'nose_1', x: 0.50, y: 0.40, region: 'nose', delay: 1800 },
  { id: 'nose_2', x: 0.48, y: 0.45, region: 'nose', delay: 2000 },
  { id: 'nose_3', x: 0.52, y: 0.45, region: 'nose', delay: 2200 },
  { id: 'nose_4', x: 0.50, y: 0.50, region: 'nose', delay: 2400 },

  // Mouth (lower reveal - final mystery)
  { id: 'mouth_1', x: 0.45, y: 0.55, region: 'mouth', delay: 2600 },
  { id: 'mouth_2', x: 0.50, y: 0.58, region: 'mouth', delay: 2800 },
  { id: 'mouth_3', x: 0.55, y: 0.55, region: 'mouth', delay: 3000 },
  { id: 'mouth_4', x: 0.48, y: 0.60, region: 'mouth', delay: 3200 },
  { id: 'mouth_5', x: 0.52, y: 0.60, region: 'mouth', delay: 3400 },

  // Jawline (bottom frame - final reveal)
  { id: 'jaw_left', x: 0.25, y: 0.62, region: 'jawline', delay: 3600 },
  { id: 'jaw_center_left', x: 0.40, y: 0.68, region: 'jawline', delay: 3900 },
  { id: 'jaw_center_right', x: 0.60, y: 0.68, region: 'jawline', delay: 4100 },
  { id: 'jaw_right', x: 0.75, y: 0.62, region: 'jawline', delay: 4400 },
];

const AnimatedPoint: React.FC<{
  point: FaceScannerPoint;
  imageWidth: number;
  imageHeight: number;
  animValue: Animated.Value;
}> = ({ point, imageWidth, imageHeight, animValue }) => {
  const [scaleAnim] = useState(new Animated.Value(0));
  const [opacityAnim] = useState(new Animated.Value(0));

  useEffect(() => {
    Animated.sequence([
      Animated.delay(point.delay),
      Animated.parallel([
        Animated.timing(scaleAnim, {
          toValue: 1,
          duration: 400,
          useNativeDriver: false,
        }),
        Animated.timing(opacityAnim, {
          toValue: 1,
          duration: 300,
          useNativeDriver: false,
        }),
      ]),
    ]).start();
  }, []);

  const x = point.x * imageWidth;
  const y = point.y * imageHeight;

  // Glow pulsing animation
  const glowAnim = new Animated.Value(0);
  useEffect(() => {
    Animated.loop(
      Animated.sequence([
        Animated.timing(glowAnim, {
          toValue: 1,
          duration: 800,
          useNativeDriver: false,
        }),
        Animated.timing(glowAnim, {
          toValue: 0,
          duration: 800,
          useNativeDriver: false,
        }),
      ])
    ).start();
  }, []);

  const glowRadius = glowAnim.interpolate({
    inputRange: [0, 1],
    outputRange: [8, 16],
  });

  const regionColor = {
    eye: theme.colors.warmBlue,
    nose: theme.colors.warmGreen,
    mouth: theme.colors.warmRed,
    cheek: theme.colors.warmPink,
    jawline: theme.colors.warmAmber,
    forehead: theme.colors.warmPurple || '#9C27B0',
  }[point.region] || theme.colors.warmBlue;

  return (
    <View
      key={point.id}
      style={[
        styles.pointContainer,
        {
          left: x - 8,
          top: y - 8,
        },
      ]}
    >
      {/* Glow background */}
      <Animated.View
        style={[
          styles.glow,
          {
            width: glowRadius,
            height: glowRadius,
            borderRadius: glowAnim.interpolate({
              inputRange: [0, 1],
              outputRange: [4, 8],
            }),
            backgroundColor: regionColor,
            opacity: opacityAnim.interpolate({
              inputRange: [0, 1],
              outputRange: [0, 0.3],
            }),
          },
        ]}
      />

      {/* Main point */}
      <Animated.View
        style={[
          styles.point,
          {
            backgroundColor: regionColor,
            transform: [{ scale: scaleAnim }],
            opacity: opacityAnim,
          },
        ]}
      />
    </View>
  );
};

// Scanning wave animation component
const ScanningWave: React.FC<{ imageWidth: number; imageHeight: number }> = ({
  imageWidth,
  imageHeight,
}) => {
  const [waveAnim] = useState(new Animated.Value(0));

  useEffect(() => {
    Animated.loop(
      Animated.sequence([
        Animated.timing(waveAnim, {
          toValue: 1,
          duration: 2000,
          useNativeDriver: false,
        }),
        Animated.timing(waveAnim, {
          toValue: 0,
          duration: 500,
          useNativeDriver: false,
        }),
      ])
    ).start();
  }, []);

  const wavePosition = waveAnim.interpolate({
    inputRange: [0, 1],
    outputRange: [-imageHeight, imageHeight],
  });

  return (
    <Animated.View
      style={[
        StyleSheet.absoluteFill,
        {
          transform: [{ translateY: wavePosition }],
          borderRadius: 12,
          overflow: 'hidden',
        },
      ]}
    >
      <View
        style={{
          width: imageWidth,
          height: 80,
          backgroundColor: 'rgba(255, 255, 255, 0.05)',
          borderTopWidth: 2,
          borderTopColor: 'rgba(100, 200, 255, 0.4)',
        }}
      />
    </Animated.View>
  );
};

export const FaceScannerOverlay: React.FC<Props> = ({
  imageUri,
  progress = 0,
  scanDuration = 5000,
}) => {
  const [animValue] = useState(new Animated.Value(0));
  const [imageDimensions, setImageDimensions] = useState({ width: 0, height: 0 });

  useEffect(() => {
    Image.getSize(imageUri, (width, height) => {
      const scale = Math.min(screenWidth * 0.85 / width, 400 / height);
      setImageDimensions({
        width: width * scale,
        height: height * scale,
      });
    });
  }, [imageUri]);

  useEffect(() => {
    Animated.timing(animValue, {
      toValue: progress,
      duration: 300,
      useNativeDriver: false,
    }).start();
  }, [progress]);

  // Non-linear progress (slower at start/end, faster in middle) - more dramatic
  const dramaticProgress = animValue.interpolate({
    inputRange: [0, 25, 50, 75, 100],
    outputRange: [0, 15, 50, 85, 100],
  });

  const progressWidth = dramaticProgress.interpolate({
    inputRange: [0, 100],
    outputRange: ['0%', '100%'],
  });

  return (
    <View style={styles.container}>
      {/* Photo + Points overlay */}
      <View
        style={[
          styles.scannerContainer,
          {
            width: imageDimensions.width,
            height: imageDimensions.height,
          },
        ]}
      >
        {/* Photo background */}
        <Image
          source={{ uri: imageUri }}
          style={{
            width: imageDimensions.width,
            height: imageDimensions.height,
            borderRadius: 12,
          }}
        />

        {/* Scanning wave effect (mysterious) */}
        <ScanningWave
          imageWidth={imageDimensions.width}
          imageHeight={imageDimensions.height}
        />

        {/* Overlay - semi-transparent dark */}
        <View
          style={[
            StyleSheet.absoluteFill,
            {
              backgroundColor: 'rgba(0, 10, 30, 0.25)',
              borderRadius: 12,
            },
          ]}
        />

        {/* Facial landmark points */}
        {FACIAL_LANDMARKS.map((point) => (
          <AnimatedPoint
            key={point.id}
            point={point}
            imageWidth={imageDimensions.width}
            imageHeight={imageDimensions.height}
            animValue={animValue}
          />
        ))}

        {/* Corner glow effects (mysterious ambiance) */}
        <View
          style={[
            StyleSheet.absoluteFill,
            {
              borderRadius: 12,
              borderWidth: 1,
              borderColor: 'rgba(100, 200, 255, 0.3)',
              pointerEvents: 'none',
            },
          ]}
        />
      </View>

      {/* Progress info below */}
      <View style={styles.infoContainer}>
        <View style={styles.progressBar}>
          <Animated.View
            style={[
              styles.progressFill,
              {
                width: progressWidth,
              },
            ]}
          />
        </View>
        <Text style={styles.progressText}>
          {Math.round(progress) <= 20
            ? '✨ Tarama başlıyor...'
            : Math.round(progress) <= 40
            ? '👁️ Yüz özellikleri haritalaşıyor...'
            : Math.round(progress) <= 60
            ? '🔍 Detaylar analiz ediliyor...'
            : Math.round(progress) <= 85
            ? '⚡ Veriler işleniyor...'
            : '🎯 Sonuçlar hazırlanıyor...'}
        </Text>
      </View>

      {/* Scan status with mystique */}
      <View style={styles.statusContainer}>
        <Text style={styles.statusEmoji}>
          {Math.round(progress) <= 30 ? '✨' : Math.round(progress) <= 60 ? '🌟' : '💫'}
        </Text>
        <Text style={styles.statusText}>
          {Math.round(progress)}% Kişisel Analiz
        </Text>
      </View>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    alignItems: 'center',
    gap: 20,
    paddingVertical: 24,
  },
  scannerContainer: {
    position: 'relative',
    overflow: 'hidden',
    borderRadius: 12,
    borderWidth: 2,
    borderColor: theme.colors.warmBlue,
  },
  pointContainer: {
    position: 'absolute',
    width: 16,
    height: 16,
    alignItems: 'center',
    justifyContent: 'center',
  },
  glow: {
    position: 'absolute',
  },
  point: {
    width: 8,
    height: 8,
    borderRadius: 4,
  },
  infoContainer: {
    width: '100%',
    paddingHorizontal: 24,
    gap: 8,
  },
  progressBar: {
    width: '100%',
    height: 4,
    backgroundColor: theme.colors.bg + '40',
    borderRadius: 2,
    overflow: 'hidden',
  },
  progressFill: {
    height: '100%',
    background: 'linear-gradient(90deg, #C9A84C 0%, #D4853A 100%)',
    backgroundColor: theme.colors.warmAmber,
    borderRadius: 2,
  },
  progressText: {
    fontSize: 12,
    color: theme.colors.textWarm,
    textAlign: 'center',
    fontWeight: '600',
  },
  statusContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  statusEmoji: {
    fontSize: 24,
  },
  statusText: {
    fontSize: 14,
    color: theme.colors.textWarm,
    fontWeight: '500',
  },
});

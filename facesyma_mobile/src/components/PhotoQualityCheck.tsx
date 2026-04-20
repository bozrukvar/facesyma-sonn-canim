/**
 * PhotoQualityCheck.tsx
 * ====================
 * Fotoğraf kalitesi kontrolü ve geri bildirim
 * - Kalite skoru
 * - Sorunlar ve öneriler
 * - Devam et veya tekrar çek seçeneği
 */

import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  ScrollView,
  Image,
  Dimensions,
  Animated,
} from 'react-native';
import { Card } from './ui';
import theme from '../utils/theme';
import {
  FaceValidationResult,
  getQualityEmoji,
  generateRecommendationText,
} from '../utils/faceOptimization';

interface Props {
  imageUri: string;
  validationResult: FaceValidationResult;
  onAccept: () => void; // Devam et
  onRetake: () => void; // Tekrar çek
}

const { width } = Dimensions.get('window');
const imageSize = width * 0.7;

export const PhotoQualityCheck: React.FC<Props> = ({
  imageUri,
  validationResult,
  onAccept,
  onRetake,
}) => {
  const { isValid, score, issues, recommendations } = validationResult;
  const emoji = getQualityEmoji(score);
  const [scaleAnim] = useState(new Animated.Value(0.8));
  const [opacityAnim] = useState(new Animated.Value(0));

  // Animate on load
  useEffect(() => {
    Animated.parallel([
      Animated.spring(scaleAnim, {
        toValue: 1,
        useNativeDriver: false,
        tension: 80,
      }),
      Animated.timing(opacityAnim, {
        toValue: 1,
        duration: 600,
        useNativeDriver: false,
      }),
    ]).start();
  }, []);

  // Kalite seviyesi açıklaması
  const getQualityLevel = () => {
    if (score >= 85) return { level: 'Mükemmel', color: theme.colors.warmGreen };
    if (score >= 70) return { level: 'İyi', color: theme.colors.warmAmber };
    if (score >= 50) return { level: 'Kabul Edilebilir', color: theme.colors.warmOrange || '#FF9800' };
    return { level: 'Düşük', color: theme.colors.warmRed };
  };

  const qualityLevel = getQualityLevel();

  return (
    <View style={styles.container}>
      <ScrollView
        contentContainerStyle={styles.scroll}
        showsVerticalScrollIndicator={false}
      >
        {/* Kalite skoru başlığı */}
        <Animated.View
          style={[
            styles.scoreHeader,
            {
              transform: [{ scale: scaleAnim }],
              opacity: opacityAnim,
            },
          ]}
        >
          {/* Animated background circle */}
          <View
            style={[
              styles.scoreCircle,
              {
                backgroundColor: qualityLevel.color + '20',
                borderColor: qualityLevel.color,
              },
            ]}
          >
            <Text style={[styles.scoreEmoji, { fontSize: 48 }]}>{emoji}</Text>
          </View>
          <View style={styles.scoreInfo}>
            <Text style={styles.scoreTitle}>Fotoğraf Kalitesi</Text>
            <View style={styles.scoreRow}>
              <Text style={[styles.scoreNumber, { color: qualityLevel.color }]}>
                {Math.round(score)}%
              </Text>
              <Text style={[styles.scoreLevel, { color: qualityLevel.color }]}>
                {qualityLevel.level}
              </Text>
            </View>
          </View>
        </Animated.View>

        {/* Fotoğraf önizlemesi */}
        <Card style={styles.previewCard}>
          <Image
            source={{ uri: imageUri }}
            style={{
              width: imageSize,
              height: imageSize,
              borderRadius: 12,
              resizeMode: 'cover',
            }}
          />
        </Card>

        {/* Sorunlar listesi */}
        {issues.length > 0 && (
          <Card style={styles.issuesCard}>
            <Text style={styles.issuesTitle}>⚠️ Tespit Edilen Sorunlar</Text>
            <View style={styles.issuesList}>
              {issues.map((issue, idx) => (
                <View key={idx} style={styles.issueItem}>
                  <Text style={styles.issueBullet}>•</Text>
                  <Text style={styles.issueText}>{issue}</Text>
                </View>
              ))}
            </View>
          </Card>
        )}

        {/* Öneriler */}
        {recommendations.length > 0 && (
          <Card style={styles.recommendationsCard}>
            <Text style={styles.recommendationsTitle}>💡 Öneriler</Text>
            <View style={styles.recommendationsList}>
              {recommendations.map((rec, idx) => (
                <View key={idx} style={styles.recommendationItem}>
                  <Text style={styles.recommendationBullet}>→</Text>
                  <Text style={styles.recommendationText}>{rec}</Text>
                </View>
              ))}
            </View>
          </Card>
        )}

        {/* Durum mesajı */}
        <Card
          style={[
            styles.statusCard,
            {
              backgroundColor: isValid
                ? theme.colors.warmGreen + '15'
                : theme.colors.warmRed + '15',
              borderColor: isValid
                ? theme.colors.warmGreen
                : theme.colors.warmRed,
            },
          ]}
        >
          <Text
            style={[
              styles.statusMessage,
              {
                color: isValid ? theme.colors.warmGreen : theme.colors.warmRed,
              },
            ]}
          >
            {isValid
              ? '✅ Fotoğraf uygun! Analiz başlatabilirsiniz.'
              : '⚠️ Daha iyi bir fotoğraf çekmeyi önerilir.'}
          </Text>
          <Text style={styles.statusSubtext}>
            {isValid
              ? 'Sistem fotoğrafınızı analiz etmeye hazır.'
              : 'Yine de devam edebilirsiniz, ancak sonuçlar daha doğru olursa daha iyi olacaktır.'}
          </Text>
        </Card>

        {/* Kalite ipuçları */}
        <Card variant="warm" style={styles.tipsCard}>
          <Text style={styles.tipsTitle}>🎯 Sonraki Çekim İçin İpuçları</Text>
          <View style={styles.tipsList}>
            <Text style={styles.tipsItem}>
              • Yüzünüz ekranın merkezinde olacak şekilde konumlandırın
            </Text>
            <Text style={styles.tipsItem}>
              • Yeterli aydınlatma sağlayın (gölgeleri minimize edin)
            </Text>
            <Text style={styles.tipsItem}>
              • Kameraya doğru bakın, tarafsız bir ifade kullanın
            </Text>
            <Text style={styles.tipsItem}>
              • Yüzünün tamamının görüneceği uygun mesafeden çekin
            </Text>
          </View>
        </Card>
      </ScrollView>

      {/* Action buttons */}
      <View style={styles.buttonContainer}>
        <TouchableOpacity
          style={[styles.button, styles.retakeButton]}
          onPress={onRetake}
        >
          <Text style={styles.retakeButtonText}>📸 YENİDEN ÇEK</Text>
        </TouchableOpacity>
        <TouchableOpacity
          style={[
            styles.button,
            styles.proceedButton,
            !isValid && styles.proceedButtonDisabled,
          ]}
          onPress={onAccept}
        >
          <Text style={styles.proceedButtonText}>
            {isValid ? '✅ DEVAM ET' : '⚠️ DEVAM ET'}
          </Text>
        </TouchableOpacity>
      </View>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: theme.colors.bg,
  },
  scroll: {
    padding: theme.spacing.lg,
    paddingBottom: theme.spacing.xl + 100, // Space for buttons
  },
  scoreHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: theme.spacing.xl,
    gap: theme.spacing.lg,
  },
  scoreCircle: {
    width: 100,
    height: 100,
    borderRadius: 50,
    borderWidth: 2,
    alignItems: 'center',
    justifyContent: 'center',
  },
  scoreEmoji: {
    fontSize: 48,
  },
  scoreInfo: {
    flex: 1,
  },
  scoreTitle: {
    fontSize: 14,
    color: theme.colors.textWarm + '80',
    marginBottom: 4,
  },
  scoreRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: theme.spacing.md,
  },
  scoreNumber: {
    fontSize: 28,
    fontWeight: '700',
  },
  scoreLevel: {
    fontSize: 16,
    fontWeight: '600',
  },
  previewCard: {
    marginBottom: theme.spacing.xl,
    alignItems: 'center',
  },
  issuesCard: {
    marginBottom: theme.spacing.xl,
    borderLeftWidth: 3,
    borderLeftColor: theme.colors.warmRed,
  },
  issuesTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: theme.colors.warmRed,
    marginBottom: theme.spacing.md,
  },
  issuesList: {
    gap: theme.spacing.sm,
  },
  issueItem: {
    flexDirection: 'row',
    gap: theme.spacing.md,
  },
  issueBullet: {
    fontSize: 14,
    color: theme.colors.warmRed,
    fontWeight: '600',
  },
  issueText: {
    flex: 1,
    fontSize: 13,
    color: theme.colors.textWarm,
  },
  recommendationsCard: {
    marginBottom: theme.spacing.xl,
    borderLeftWidth: 3,
    borderLeftColor: theme.colors.warmAmber,
  },
  recommendationsTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: theme.colors.warmAmber,
    marginBottom: theme.spacing.md,
  },
  recommendationsList: {
    gap: theme.spacing.sm,
  },
  recommendationItem: {
    flexDirection: 'row',
    gap: theme.spacing.md,
  },
  recommendationBullet: {
    fontSize: 14,
    color: theme.colors.warmAmber,
    fontWeight: '600',
  },
  recommendationText: {
    flex: 1,
    fontSize: 13,
    color: theme.colors.textWarm,
  },
  statusCard: {
    marginBottom: theme.spacing.xl,
    borderWidth: 1,
  },
  statusMessage: {
    fontSize: 15,
    fontWeight: '600',
    marginBottom: theme.spacing.sm,
  },
  statusSubtext: {
    fontSize: 12,
    color: theme.colors.textWarm,
    lineHeight: 16,
  },
  tipsCard: {
    marginBottom: theme.spacing.xl,
  },
  tipsTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: theme.colors.textWarm,
    marginBottom: theme.spacing.md,
  },
  tipsList: {
    gap: theme.spacing.sm,
  },
  tipsItem: {
    fontSize: 12,
    color: theme.colors.textWarm,
    lineHeight: 16,
  },
  buttonContainer: {
    position: 'absolute',
    bottom: theme.spacing.lg,
    left: theme.spacing.lg,
    right: theme.spacing.lg,
    flexDirection: 'row',
    gap: theme.spacing.md,
  },
  button: {
    flex: 1,
    height: 56,
    borderRadius: theme.radius.lg,
    alignItems: 'center',
    justifyContent: 'center',
  },
  retakeButton: {
    backgroundColor: theme.colors.bg + '60',
    borderWidth: 1.5,
    borderColor: theme.colors.warmAmber,
  },
  retakeButtonText: {
    fontSize: 14,
    fontWeight: '700',
    color: theme.colors.warmAmber,
    letterSpacing: 0.5,
  },
  proceedButton: {
    backgroundColor: theme.colors.warmAmber,
    ...theme.shadow.warm,
  },
  proceedButtonText: {
    fontSize: 14,
    fontWeight: '700',
    color: theme.colors.bg,
    letterSpacing: 0.5,
  },
  proceedButtonDisabled: {
    opacity: 0.7,
  },
});

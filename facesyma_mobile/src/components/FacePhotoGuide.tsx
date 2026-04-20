/**
 * FacePhotoGuide.tsx
 * ==================
 * Fotoğraf çekmeden önce rehber göster
 * - Doğru teknik
 * - İyi pratikler
 * - Uyarılar
 */

import React from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  Image,
  Dimensions,
} from 'react-native';
import { Card } from './ui';
import theme from '../utils/theme';
import { FACE_PHOTO_GUIDELINES } from '../utils/faceOptimization';

interface Props {
  onAcknowledge: () => void;
}

const { width } = Dimensions.get('window');

export const FacePhotoGuide: React.FC<Props> = ({ onAcknowledge }) => {
  const guidelines = FACE_PHOTO_GUIDELINES.before_photo;

  return (
    <View style={styles.container}>
      <ScrollView
        contentContainerStyle={styles.scroll}
        showsVerticalScrollIndicator={false}
      >
        {/* Header */}
        <View style={styles.header}>
          <Text style={styles.emoji}>📸</Text>
          <Text style={styles.title}>{guidelines.title}</Text>
          <Text style={styles.subtitle}>
            En iyi sonuçlar için doğru fotoğrafı çekin
          </Text>
        </View>

        {/* Example image placeholder */}
        <Card style={styles.exampleCard}>
          <View style={styles.exampleImage}>
            <Text style={styles.exampleEmoji}>👤</Text>
            <Text style={styles.exampleText}>
              Bunun gibi bir fotoğraf{'\n'}çekin
            </Text>
          </View>
        </Card>

        {/* DO'S Section */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>✅ Yapmanız Gerekenler</Text>
          <View style={styles.tipsContainer}>
            {guidelines.tips.map((tip, idx) => (
              <View key={idx} style={styles.tipRow}>
                <Text style={styles.tipText}>{tip}</Text>
              </View>
            ))}
          </View>
        </View>

        {/* DON'Ts Section */}
        <View style={styles.section}>
          <Text style={[styles.sectionTitle, { color: theme.colors.warmRed }]}>
            ❌ Yapmamanız Gerekenler
          </Text>
          <View style={styles.tipsContainer}>
            {guidelines.do_not.map((warning, idx) => (
              <View key={idx} style={styles.warningRow}>
                <Text style={styles.warningText}>{warning}</Text>
              </View>
            ))}
          </View>
        </View>

        {/* Best Practices Card */}
        <Card variant="warm" style={styles.bestPracticesCard}>
          <Text style={styles.bestPracticesTitle}>💡 İpuçları</Text>
          <View style={styles.bestPracticesList}>
            <Text style={styles.bestPracticeItem}>
              • Doğal aydınlatma en iyisidir
            </Text>
            <Text style={styles.bestPracticeItem}>
              • Ön-ışık (yüzü aydınlatırsa) tercih edilir
            </Text>
            <Text style={styles.bestPracticeItem}>
              • Gölgeler yüzü kesmemelidir
            </Text>
            <Text style={styles.bestPracticeItem}>
              • Normal bir ifade kullanın
            </Text>
          </View>
        </Card>

        {/* Quality reminder */}
        <Card style={styles.qualityCard}>
          <Text style={styles.qualityTitle}>⚡ Kalite Kontrolü</Text>
          <Text style={styles.qualityText}>
            Fotoğrafı çektikten sonra, kalite kontrolünde:
          </Text>
          <View style={styles.qualityChecklist}>
            <Text style={styles.checkItem}>
              ✓ Sistem fotoğrafı otomatik olarak kontrol edecek
            </Text>
            <Text style={styles.checkItem}>
              ✓ Geliştirilmesi gereken alanlar gösterilecek
            </Text>
            <Text style={styles.checkItem}>
              ✓ Yeni fotoğraf çekmek veya devam etmek seçebilirsiniz
            </Text>
          </View>
        </Card>

        {/* Device-responsive note */}
        <View style={styles.noteBox}>
          <Text style={styles.noteEmoji}>📱</Text>
          <Text style={styles.noteText}>
            Fotoğraf otomatik olarak sizin cihazınıza uygun boyuta
            getirilecektir
          </Text>
        </View>
      </ScrollView>

      {/* Action Button */}
      <TouchableOpacity style={styles.button} onPress={onAcknowledge}>
        <Text style={styles.buttonText}>ANLAŞILDII, DEVAM ET</Text>
      </TouchableOpacity>
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
    paddingBottom: theme.spacing.xl + 70, // Space for button
  },
  header: {
    alignItems: 'center',
    marginBottom: theme.spacing.xl,
  },
  emoji: {
    fontSize: 48,
    marginBottom: 12,
  },
  exampleEmoji: {
    fontSize: 64,
    marginBottom: 12,
  },
  title: {
    fontSize: 24,
    fontWeight: '700',
    color: theme.colors.textWarm,
    marginBottom: 8,
  },
  subtitle: {
    fontSize: 14,
    color: theme.colors.textWarm + '80',
    textAlign: 'center',
  },
  exampleCard: {
    marginBottom: theme.spacing.xl,
  },
  exampleImage: {
    width: '100%',
    aspectRatio: 1,
    backgroundColor: theme.colors.bg + '40',
    borderRadius: 12,
    alignItems: 'center',
    justifyContent: 'center',
    borderWidth: 2,
    borderStyle: 'dashed',
    borderColor: theme.colors.warmBlue,
  },
  exampleEmoji: {
    fontSize: 64,
    marginBottom: 12,
  },
  exampleText: {
    fontSize: 14,
    color: theme.colors.textWarm,
    textAlign: 'center',
  },
  section: {
    marginBottom: theme.spacing.xl,
  },
  sectionTitle: {
    fontSize: 20,
    fontWeight: '700',
    fontFamily: 'Georgia',
    color: theme.colors.textWarm,
    marginBottom: theme.spacing.md,
    letterSpacing: -0.3,
  },
  tipsContainer: {
    gap: theme.spacing.sm,
  },
  tipRow: {
    backgroundColor: theme.colors.bg + '40',
    padding: theme.spacing.md,
    borderRadius: 8,
    borderLeftWidth: 3,
    borderLeftColor: theme.colors.warmGreen,
  },
  tipText: {
    fontSize: 13,
    color: theme.colors.textWarm,
    lineHeight: 18,
  },
  warningRow: {
    backgroundColor: theme.colors.bg + '40',
    padding: theme.spacing.md,
    borderRadius: 8,
    borderLeftWidth: 3,
    borderLeftColor: theme.colors.warmRed,
  },
  warningText: {
    fontSize: 13,
    color: theme.colors.textWarm,
    lineHeight: 18,
  },
  bestPracticesCard: {
    marginBottom: theme.spacing.xl,
  },
  bestPracticesTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: theme.colors.textWarm,
    marginBottom: theme.spacing.md,
  },
  bestPracticesList: {
    gap: theme.spacing.sm,
  },
  bestPracticeItem: {
    fontSize: 13,
    color: theme.colors.textWarm,
    lineHeight: 18,
  },
  qualityCard: {
    marginBottom: theme.spacing.xl,
    borderWidth: 1,
    borderColor: theme.colors.warmBlue + '40',
  },
  qualityTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: theme.colors.warmBlue,
    marginBottom: theme.spacing.sm,
  },
  qualityText: {
    fontSize: 13,
    color: theme.colors.textWarm,
    marginBottom: theme.spacing.md,
  },
  qualityChecklist: {
    gap: theme.spacing.sm,
  },
  checkItem: {
    fontSize: 12,
    color: theme.colors.textWarm,
    lineHeight: 16,
  },
  noteBox: {
    flexDirection: 'row',
    backgroundColor: theme.colors.bg + '60',
    padding: theme.spacing.md,
    borderRadius: 8,
    gap: theme.spacing.md,
    marginBottom: theme.spacing.lg,
    alignItems: 'center',
  },
  noteEmoji: {
    fontSize: 24,
  },
  noteText: {
    flex: 1,
    fontSize: 12,
    color: theme.colors.textWarm,
    lineHeight: 16,
  },
  button: {
    position: 'absolute',
    bottom: theme.spacing.lg,
    left: theme.spacing.lg,
    right: theme.spacing.lg,
    backgroundColor: theme.colors.warmAmber,
    height: 56,
    borderRadius: theme.radius.lg,
    alignItems: 'center',
    justifyContent: 'center',
    ...theme.shadow.warm,
  },
  buttonText: {
    fontSize: 14,
    fontWeight: '700',
    color: theme.colors.bg,
  },
});

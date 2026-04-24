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
  Dimensions,
} from 'react-native';
import { Card } from './ui';
import theme from '../utils/theme';
const { colors, spacing, radius, shadow } = theme;
import { t } from '../utils/i18n';
import { FACE_PHOTO_GUIDELINES } from '../utils/faceOptimization';

interface Props {
  onAcknowledge: () => void;
  lang?: string;
}

const { width } = Dimensions.get('window');

export const FacePhotoGuide: React.FC<Props> = ({ onAcknowledge, lang = 'tr' }) => {
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
          <Text style={styles.subtitle}>{t('photo_guide.subtitle', lang)}</Text>
        </View>

        {/* Example image placeholder */}
        <Card style={styles.exampleCard}>
          <View style={styles.exampleImage}>
            <Text style={styles.exampleEmoji}>👤</Text>
            <Text style={styles.exampleText}>{t('photo_guide.example_text', lang)}</Text>
          </View>
        </Card>

        {/* DO'S Section */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>{t('photo_guide.dos_title', lang)}</Text>
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
          <Text style={styles.sectionTitleRed}>
            {t('photo_guide.donts_title', lang)}
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
          <Text style={styles.bestPracticesTitle}>{t('photo_guide.tips_title', lang)}</Text>
          <View style={styles.bestPracticesList}>
            <Text style={styles.bestPracticeItem}>{t('photo_guide.best_1', lang)}</Text>
            <Text style={styles.bestPracticeItem}>{t('photo_guide.best_2', lang)}</Text>
            <Text style={styles.bestPracticeItem}>{t('photo_guide.best_3', lang)}</Text>
            <Text style={styles.bestPracticeItem}>{t('photo_guide.best_4', lang)}</Text>
          </View>
        </Card>

        {/* Quality reminder */}
        <Card style={styles.qualityCard}>
          <Text style={styles.qualityTitle}>{t('photo_guide.quality_title', lang)}</Text>
          <Text style={styles.qualityText}>{t('photo_guide.quality_desc', lang)}</Text>
          <View style={styles.qualityChecklist}>
            <Text style={styles.checkItem}>{t('photo_guide.quality_check_1', lang)}</Text>
            <Text style={styles.checkItem}>{t('photo_guide.quality_check_2', lang)}</Text>
            <Text style={styles.checkItem}>{t('photo_guide.quality_check_3', lang)}</Text>
          </View>
        </Card>

        {/* Device-responsive note */}
        <View style={styles.noteBox}>
          <Text style={styles.noteEmoji}>📱</Text>
          <Text style={styles.noteText}>{t('photo_guide.note', lang)}</Text>
        </View>
      </ScrollView>

      {/* Action Button */}
      <TouchableOpacity style={styles.button} onPress={onAcknowledge}>
        <Text style={styles.buttonText}>{t('photo_guide.confirm', lang)}</Text>
      </TouchableOpacity>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: colors.bg,
  },
  scroll: {
    padding: spacing.lg,
    paddingBottom: spacing.xl + 70, // Space for button
  },
  header: {
    alignItems: 'center',
    marginBottom: spacing.xl,
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
    color: colors.textWarm,
    marginBottom: 8,
  },
  subtitle: {
    fontSize: 14,
    color: colors.textWarm + '80',
    textAlign: 'center',
  },
  exampleCard: {
    marginBottom: spacing.xl,
  },
  exampleImage: {
    width: '100%',
    aspectRatio: 1,
    backgroundColor: colors.bg + '40',
    borderRadius: 12,
    alignItems: 'center',
    justifyContent: 'center',
    borderWidth: 2,
    borderStyle: 'dashed',
    borderColor: colors.warmBlue,
  },
  exampleText: {
    fontSize: 14,
    color: colors.textWarm,
    textAlign: 'center',
  },
  section: {
    marginBottom: spacing.xl,
  },
  sectionTitle: {
    fontSize: 20,
    fontWeight: '700',
    fontFamily: 'Georgia',
    color: colors.textWarm,
    marginBottom: spacing.md,
    letterSpacing: -0.3,
  },
  tipsContainer: {
    gap: spacing.sm,
  },
  tipRow: {
    backgroundColor: colors.bg + '40',
    padding: spacing.md,
    borderRadius: 8,
    borderLeftWidth: 3,
    borderLeftColor: colors.warmGreen,
  },
  tipText: {
    fontSize: 13,
    color: colors.textWarm,
    lineHeight: 18,
  },
  warningRow: {
    backgroundColor: colors.bg + '40',
    padding: spacing.md,
    borderRadius: 8,
    borderLeftWidth: 3,
    borderLeftColor: colors.warmRed,
  },
  warningText: {
    fontSize: 13,
    color: colors.textWarm,
    lineHeight: 18,
  },
  bestPracticesCard: {
    marginBottom: spacing.xl,
  },
  bestPracticesTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: colors.textWarm,
    marginBottom: spacing.md,
  },
  bestPracticesList: {
    gap: spacing.sm,
  },
  bestPracticeItem: {
    fontSize: 13,
    color: colors.textWarm,
    lineHeight: 18,
  },
  qualityCard: {
    marginBottom: spacing.xl,
    borderWidth: 1,
    borderColor: colors.warmBlue + '40',
  },
  qualityTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: colors.warmBlue,
    marginBottom: spacing.sm,
  },
  qualityText: {
    fontSize: 13,
    color: colors.textWarm,
    marginBottom: spacing.md,
  },
  qualityChecklist: {
    gap: spacing.sm,
  },
  checkItem: {
    fontSize: 12,
    color: colors.textWarm,
    lineHeight: 16,
  },
  noteBox: {
    flexDirection: 'row',
    backgroundColor: colors.bg + '60',
    padding: spacing.md,
    borderRadius: 8,
    gap: spacing.md,
    marginBottom: spacing.lg,
    alignItems: 'center',
  },
  noteEmoji: {
    fontSize: 24,
  },
  noteText: {
    flex: 1,
    fontSize: 12,
    color: colors.textWarm,
    lineHeight: 16,
  },
  button: {
    position: 'absolute',
    bottom: spacing.lg,
    left: spacing.lg,
    right: spacing.lg,
    backgroundColor: colors.warmAmber,
    height: 56,
    borderRadius: radius.lg,
    alignItems: 'center',
    justifyContent: 'center',
    ...shadow.warm,
  },
  buttonText: {
    fontSize: 14,
    fontWeight: '700',
    color: colors.bg,
  },
  sectionTitleRed: {
    fontSize: 20,
    fontWeight: '700',
    fontFamily: 'Georgia',
    color: colors.warmRed,
    marginBottom: spacing.md,
    letterSpacing: -0.3,
  },
});

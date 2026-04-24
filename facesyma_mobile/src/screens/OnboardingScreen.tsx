// src/screens/OnboardingScreen.tsx
import React, { useRef, useState, useMemo } from 'react';
import {
  View, Text, StyleSheet, Dimensions, FlatList,
  TouchableOpacity, Animated,
} from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import theme from '../utils/theme';
const { colors, spacing, typography, radius } = theme;
import { useLanguage } from '../utils/LanguageContext';
import { t } from '../utils/i18n';
import type { ScreenProps } from '../navigation/types';

const { width, height } = Dimensions.get('window');

const getSlides = (lang: string) => [
  {
    id: '1',
    emoji:    '👁',
    title:    t('onboarding.slide1_title', lang),
    subtitle: t('onboarding.slide1_desc', lang),
    accent:   colors.gold,
  },
  {
    id: '2',
    emoji:    '✨',
    title:    t('onboarding.slide2_title', lang),
    subtitle: t('onboarding.slide2_desc', lang),
    accent:   colors.warmAmber,
  },
  {
    id: '3',
    emoji:    '🎭',
    title:    t('onboarding.slide3_title', lang),
    subtitle: t('onboarding.slide3_desc', lang),
    accent:   colors.gold,
  },
  {
    id: '4',
    emoji:    '💬',
    title:    t('onboarding.slide4_title', lang),
    subtitle: t('onboarding.slide4_desc', lang),
    accent:   colors.warmAmber,
  },
];

const OnboardingScreen = ({ navigation }: ScreenProps<'Onboarding'>) => {
  const insets = useSafeAreaInsets();
  const { lang } = useLanguage();
  const SLIDES = useMemo(() => getSlides(lang), [lang]);
  const [index, setIndex] = useState(0);
  const flatRef  = useRef<FlatList>(null);
  const fadeAnim = useRef(new Animated.Value(1)).current;
  const scaleAnim= useRef(new Animated.Value(1)).current;

  const goNext = () => {
    Animated.parallel([
      Animated.timing(fadeAnim,  { toValue: 0, duration: 120, useNativeDriver: true }),
      Animated.timing(scaleAnim, { toValue: 0.92, duration: 120, useNativeDriver: true }),
    ]).start(() => {
      const next = index < SLIDES.length - 1 ? index + 1 : -1;
      if (next === -1) { navigation.replace('Auth'); return; }
      setIndex(next);
      flatRef.current?.scrollToIndex({ index: next, animated: false });
      Animated.parallel([
        Animated.timing(fadeAnim,  { toValue: 1, duration: 300, useNativeDriver: true }),
        Animated.spring(scaleAnim, { toValue: 1, useNativeDriver: true }),
      ]).start();
    });
  };

  const slide      = SLIDES[index];
  const slideAccent = slide.accent;
  const slidesLen  = SLIDES.length;

  return (
    <View style={styles.container}>
      {/* Arka plan sıcak ışıma */}
      <View style={[styles.glow, { backgroundColor: `${slideAccent}08` }]} />

      <FlatList
        ref={flatRef}
        data={SLIDES}
        horizontal
        pagingEnabled
        scrollEnabled={false}
        showsHorizontalScrollIndicator={false}
        keyExtractor={i => i.id}
        renderItem={({ item: { accent: iAccent, emoji: iEmoji, title: iTitle, subtitle: iSub } }) => (
          <Animated.View style={[
            styles.slide,
            { opacity: fadeAnim, transform: [{ scale: scaleAnim }] },
          ]}>
            {/* Emoji halka */}
            <View style={[styles.emojiRing, {
              borderColor:     `${iAccent}60`,
              backgroundColor: `${iAccent}10`,
              shadowColor:     iAccent,
            }]}>
              <Text style={styles.emoji}>{iEmoji}</Text>
            </View>

            <Text style={styles.title}>
              {iTitle}
            </Text>
            <Text style={styles.subtitle}>{iSub}</Text>
          </Animated.View>
        )}
      />

      {/* İnce ilerleme çizgisi */}
      <View style={styles.progressWrap}>
        {SLIDES.map((_, i) => (
          <Animated.View key={i} style={[
            styles.progressDot,
            i === index && {
              width: 28,
              backgroundColor: slideAccent,
            },
            i < index && {
              backgroundColor: `${colors.gold}40`,
            },
          ]} />
        ))}
      </View>

      {/* Devam butonu */}
      <TouchableOpacity
        style={[styles.nextBtn, { backgroundColor: slideAccent }]}
        onPress={goNext}
        activeOpacity={0.85}
      >
        <Text style={styles.nextText}>
          {index === slidesLen - 1 ? t('onboarding.start', lang) : t('onboarding.next', lang)}
        </Text>
      </TouchableOpacity>

      {/* Atla */}
      {index < slidesLen - 1 && (
        <TouchableOpacity
          style={[styles.skipBtn, { marginBottom: insets.bottom + spacing.sm }]}
          onPress={() => navigation.replace('Auth')}
        >
          <Text style={styles.skipText}>{t('onboarding.skip', lang)}</Text>
        </TouchableOpacity>
      )}
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: colors.background,
    alignItems: 'center',
  },
  glow: {
    ...StyleSheet.absoluteFillObject,
  },
  slide: {
    width,
    paddingHorizontal: spacing.xxxl,
    alignItems: 'center',
    justifyContent: 'center',
    paddingTop: height * 0.12,
    paddingBottom: height * 0.04,
  },
  emojiRing: {
    width:            124,
    height:           124,
    borderRadius:     62,
    borderWidth:      1.5,
    alignItems:       'center',
    justifyContent:   'center',
    marginBottom:     spacing.xl,
    shadowOffset: { width: 0, height: 0 },
    shadowOpacity: 0.4,
    shadowRadius: 20,
    elevation: 8,
  },
  emoji:    { fontSize: 52 },
  title:    { ...typography.display, textAlign: 'center', marginBottom: spacing.lg, color: colors.textPrimary },
  subtitle: {
    ...typography.body,
    textAlign: 'center',
    lineHeight: 25,
    paddingHorizontal: spacing.md,
    color: colors.textWarm,
  },
  progressWrap: {
    flexDirection: 'row',
    marginBottom: spacing.xl,
    gap: 8,
    alignItems: 'center',
  },
  progressDot: {
    width:         8,
    height:        8,
    borderRadius:  4,
    backgroundColor: colors.border,
  },
  nextBtn: {
    width:           width - spacing.xxxl * 2,
    height:          56,
    borderRadius:    radius.xl,
    alignItems:      'center',
    justifyContent:  'center',
    marginBottom:    spacing.md,
    shadowColor:     colors.gold,
    shadowOffset: { width: 0, height: 0 },
    shadowOpacity: 0.35,
    shadowRadius: 16,
    elevation: 8,
  },
  nextText: { ...typography.label, color: '#000', letterSpacing: 2 },
  skipBtn:  { padding: spacing.md, marginBottom: spacing.md },
  skipText: { ...typography.caption, color: colors.textMuted, fontSize: 13 },
});

export default OnboardingScreen;

import React, { useState, useCallback } from 'react';
import {
  View, Text, StyleSheet, ScrollView, TouchableOpacity,
  ActivityIndicator, Alert,
} from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { useSelector } from 'react-redux';
import type { RootState } from '../store';
import { useLanguage } from '../utils/LanguageContext';
import { t } from '../utils/i18n';
import { DietAPI } from '../services/api';
import theme from '../utils/theme';
import type { ScreenProps } from '../navigation/types';

const { colors, spacing, typography, radius, shadow } = theme;

type Meal = {
  name: string;
  description?: string;
  reason: string;
  nutrition?: object;
  prep_time_min?: number;
};

type Recommendation = {
  date: string;
  breakfast: Meal;
  lunch: Meal;
  dinner: Meal;
  user_sifats: string[];
};

type FeedbackMap = Record<string, 'liked' | 'disliked' | 'neutral'>;

const MEAL_TYPES: Array<{ key: keyof Recommendation; icon: string; labelKey: string }> = [
  { key: 'breakfast', icon: '🌅', labelKey: 'diet.breakfast' },
  { key: 'lunch',     icon: '☀️', labelKey: 'diet.lunch'     },
  { key: 'dinner',    icon: '🌙', labelKey: 'diet.dinner'    },
];

const DietScreen = ({ navigation }: ScreenProps<'Diet'>) => {
  const insets = useSafeAreaInsets();
  const { lang } = useLanguage();
  const user = useSelector((s: RootState) => s.auth.user);

  const [loading,        setLoading]        = useState(false);
  const [recommendation, setRecommendation] = useState<Recommendation | null>(null);
  const [feedback,       setFeedback]       = useState<FeedbackMap>({});
  const [feedbackLoading, setFeedbackLoading] = useState<string | null>(null);

  const countryCode = user?.country_code ?? 'TR';

  const fetchRecommendation = useCallback(async () => {
    if (!user?.id) return;
    setLoading(true);
    try {
      const res = await DietAPI.getRecommendation({
        user_id: user.id,
        country_code: countryCode,
        language_code: lang,
        sifats: [],
      });
      if (res?.data) setRecommendation(res.data);
    } catch {
      Alert.alert(t('common.error', lang), t('diet.error', lang));
    } finally {
      setLoading(false);
    }
  }, [user, countryCode, lang]);

  const submitFeedback = async (mealType: string, mealName: string, fb: 'liked' | 'disliked' | 'neutral') => {
    if (!user?.id || !recommendation) return;
    const key = mealType;
    setFeedbackLoading(key);
    try {
      await DietAPI.submitFeedback(user.id, mealName, recommendation.date, mealType, fb);
      setFeedback(prev => ({ ...prev, [key]: fb }));
    } catch {
      // silent — feedback is non-critical
    } finally {
      setFeedbackLoading(null);
    }
  };

  const renderMealCard = (mealType: keyof Recommendation, icon: string, labelKey: string) => {
    const meal = recommendation?.[mealType] as Meal | undefined;
    if (!meal) return null;
    const fb = feedback[mealType as string];
    const isLoadingFb = feedbackLoading === mealType;

    return (
      <View style={styles.mealCard} key={mealType}>
        <View style={styles.mealHeader}>
          <Text style={styles.mealIcon}>{icon}</Text>
          <Text style={styles.mealTypeLabel}>{t(labelKey, lang)}</Text>
        </View>
        <Text style={styles.mealName}>{meal.name}</Text>
        {meal.description ? (
          <Text style={styles.mealDesc}>{meal.description}</Text>
        ) : null}
        {meal.reason ? (
          <Text style={styles.mealReason}>{meal.reason}</Text>
        ) : null}
        {meal.prep_time_min ? (
          <Text style={styles.prepTime}>⏱ {meal.prep_time_min} min</Text>
        ) : null}

        {/* Feedback row */}
        <View style={styles.feedbackRow}>
          {(['liked', 'neutral', 'disliked'] as const).map(fbType => {
            const icons = { liked: '👍', neutral: '😐', disliked: '👎' };
            const fbKeys = { liked: 'diet.feedback_like', neutral: 'diet.feedback_neutral', disliked: 'diet.feedback_dislike' };
            const isActive = fb === fbType;
            return (
              <TouchableOpacity
                key={fbType}
                style={[styles.fbBtn, isActive && styles.fbBtnActive]}
                onPress={() => submitFeedback(mealType as string, meal.name, fbType)}
                disabled={isLoadingFb || !!fb}
                activeOpacity={0.8}
              >
                {isLoadingFb && fb === undefined ? (
                  <ActivityIndicator size="small" color={colors.gold} />
                ) : (
                  <Text style={[styles.fbBtnTxt, isActive && styles.fbBtnTxtActive]}>
                    {icons[fbType]} {t(fbKeys[fbType], lang)}
                  </Text>
                )}
              </TouchableOpacity>
            );
          })}
        </View>
        {fb ? (
          <Text style={styles.feedbackSent}>{t('diet.feedback_sent', lang)}</Text>
        ) : null}
      </View>
    );
  };

  return (
    <View style={[styles.container, { paddingTop: insets.top }]}>
      <View style={styles.header}>
        <TouchableOpacity onPress={() => navigation.goBack()} style={styles.backBtn}>
          <Text style={styles.backText}>←</Text>
        </TouchableOpacity>
        <Text style={styles.title}>{t('diet.title', lang)}</Text>
        <View style={styles.spacer} />
      </View>

      <ScrollView contentContainerStyle={styles.scroll} showsVerticalScrollIndicator={false}>
        <Text style={styles.subtitle}>{t('diet.subtitle', lang)}</Text>

        <View style={styles.countryRow}>
          <Text style={styles.countryLabel}>{t('diet.country', lang)}</Text>
          <View style={styles.countryBadge}>
            <Text style={styles.countryBadgeTxt}>{countryCode}</Text>
          </View>
        </View>

        <TouchableOpacity
          style={[styles.getBtn, loading && styles.getBtnLoading]}
          onPress={fetchRecommendation}
          disabled={loading}
          activeOpacity={0.85}
        >
          {loading ? (
            <ActivityIndicator color="#000" size="small" />
          ) : (
            <Text style={styles.getBtnTxt}>{t('diet.get_recommendation', lang)}</Text>
          )}
        </TouchableOpacity>

        {recommendation ? (
          <View style={styles.mealsContainer}>
            {MEAL_TYPES.map(({ key, icon, labelKey }) =>
              renderMealCard(key, icon, labelKey)
            )}
          </View>
        ) : !loading ? (
          <View style={styles.emptyContainer}>
            <Text style={styles.emptyIcon}>🍽️</Text>
            <Text style={styles.emptyText}>{t('diet.empty', lang)}</Text>
          </View>
        ) : null}
      </ScrollView>
    </View>
  );
};

const styles = StyleSheet.create({
  container:    { flex: 1, backgroundColor: colors.background },
  header:       {
    flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between',
    paddingHorizontal: spacing.lg, paddingVertical: spacing.md,
    borderBottomWidth: 1, borderColor: colors.border,
  },
  backBtn:      { width: 36, height: 36, justifyContent: 'center' },
  backText:     { ...typography.h2, color: colors.gold },
  title:        { ...typography.h2, color: colors.textPrimary },
  spacer:       { width: 36 },
  scroll:       { padding: spacing.lg, gap: spacing.md, paddingBottom: spacing.xl * 2 },
  subtitle:     { ...typography.body, color: colors.textMuted, textAlign: 'center' as const, marginBottom: spacing.sm },
  countryRow:   { flexDirection: 'row', alignItems: 'center', gap: spacing.sm, justifyContent: 'center' as const },
  countryLabel: { ...typography.label, color: colors.textSecondary },
  countryBadge: {
    backgroundColor: colors.goldGlow, borderRadius: radius.sm,
    paddingHorizontal: spacing.sm, paddingVertical: 4,
    borderWidth: 1, borderColor: colors.gold,
  },
  countryBadgeTxt: { ...typography.label, color: colors.gold, fontWeight: '700' as const },
  getBtn:       {
    height: 52, backgroundColor: colors.gold, borderRadius: radius.md,
    alignItems: 'center' as const, justifyContent: 'center' as const, marginVertical: spacing.md,
    ...shadow.gold,
  },
  getBtnLoading: { opacity: 0.7 },
  getBtnTxt:    { ...typography.label, color: '#000', fontSize: 15 },
  mealsContainer: { gap: spacing.lg },
  mealCard:     {
    backgroundColor: colors.surface, borderRadius: radius.lg,
    borderWidth: 1, borderColor: colors.border,
    padding: spacing.lg, gap: spacing.sm,
  },
  mealHeader:   { flexDirection: 'row', alignItems: 'center', gap: spacing.sm },
  mealIcon:     { fontSize: 22 },
  mealTypeLabel: { ...typography.label, color: colors.gold, fontSize: 13, fontWeight: '700' as const },
  mealName:     { ...typography.h2, fontSize: 16, color: colors.textPrimary },
  mealDesc:     { ...typography.body, color: colors.textSecondary, fontSize: 13, lineHeight: 18 },
  mealReason:   { ...typography.caption, color: colors.textMuted, fontSize: 12, fontStyle: 'italic' as const },
  prepTime:     { ...typography.caption, color: colors.textMuted, fontSize: 11 },
  feedbackRow:  { flexDirection: 'row', gap: spacing.xs, marginTop: spacing.xs },
  fbBtn:        {
    flex: 1, paddingVertical: 8, borderRadius: radius.sm,
    borderWidth: 1, borderColor: colors.border,
    alignItems: 'center' as const, backgroundColor: colors.background,
  },
  fbBtnActive:   { borderColor: colors.gold, backgroundColor: colors.goldGlow },
  fbBtnTxt:     { ...typography.caption, color: colors.textMuted, fontSize: 11 },
  fbBtnTxtActive: { color: colors.gold, fontWeight: '700' as const },
  feedbackSent: { ...typography.caption, color: colors.gold, fontSize: 11, textAlign: 'center' as const },
  emptyContainer: { alignItems: 'center' as const, paddingVertical: spacing.xl * 2, gap: spacing.md },
  emptyIcon:    { fontSize: 56 },
  emptyText:    { ...typography.body, color: colors.textMuted, textAlign: 'center' as const },
});

export default DietScreen;

import React, { useState, useCallback } from 'react';
import {
  View, Text, StyleSheet, ScrollView, TouchableOpacity,
  ActivityIndicator, Alert, FlatList, Dimensions,
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
const SCREEN_W = Dimensions.get('window').width;
const OPTION_CARD_W = SCREEN_W - spacing.lg * 2 - spacing.md * 2 - 32;

type Meal = {
  name: string;
  description?: string;
  reason: string;
  nutrition?: object;
  prep_time_min?: number;
};

type Recommendation = {
  date: string;
  breakfast: Meal[];
  lunch: Meal[];
  dinner: Meal[];
  user_sifats: string[];
};

type FeedbackMap = Record<string, 'liked' | 'disliked' | 'neutral'>;
type SelectedMap  = Record<string, number>;

const MEAL_TYPES: Array<{ key: keyof Recommendation; icon: string; labelKey: string }> = [
  { key: 'breakfast', icon: '🌅', labelKey: 'diet.breakfast' },
  { key: 'lunch',     icon: '☀️', labelKey: 'diet.lunch'     },
  { key: 'dinner',    icon: '🌙', labelKey: 'diet.dinner'    },
];

const DietScreen = ({ navigation }: ScreenProps<'Diet'>) => {
  const insets = useSafeAreaInsets();
  const { lang } = useLanguage();
  const user = useSelector((s: RootState) => s.auth.user);

  const [loading,         setLoading]         = useState(false);
  const [recommendation,  setRecommendation]  = useState<Recommendation | null>(null);
  const [feedback,        setFeedback]        = useState<FeedbackMap>({});
  const [feedbackLoading, setFeedbackLoading] = useState<string | null>(null);
  const [selectedMeals,   setSelectedMeals]   = useState<SelectedMap>({
    breakfast: 0, lunch: 0, dinner: 0,
  });

  const countryCode = user?.country_code ?? 'TR';

  const fetchRecommendation = useCallback(async () => {
    if (!user?.id) return;
    setLoading(true);
    setFeedback({});
    setSelectedMeals({ breakfast: 0, lunch: 0, dinner: 0 });
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

  const submitFeedback = async (
    mealType: string,
    mealName: string,
    fb: 'liked' | 'disliked' | 'neutral',
  ) => {
    if (!user?.id || !recommendation) return;
    setFeedbackLoading(mealType);
    try {
      await DietAPI.submitFeedback(user.id, mealName, recommendation.date, mealType, fb);
      setFeedback(prev => ({ ...prev, [mealType]: fb }));
    } catch {
      // silent
    } finally {
      setFeedbackLoading(null);
    }
  };

  const renderOptionCard = (
    meal: Meal,
    mealType: string,
    idx: number,
    isActive: boolean,
  ) => (
    <TouchableOpacity
      accessibilityRole="button"
      accessibilityLabel='meal.name'
      key={idx}
      style={[styles.optionCard, isActive && styles.optionCardActive]}
      onPress={() => setSelectedMeals(prev => ({ ...prev, [mealType]: idx }))}
      activeOpacity={0.8}
    >
      {isActive && <View style={styles.activeIndicator} />}
      <Text style={[styles.optionName, isActive && styles.optionNameActive]}>
        {meal.name}
      </Text>
      {meal.description ? (
        <Text style={styles.optionDesc} numberOfLines={2}>{meal.description}</Text>
      ) : null}
      {meal.reason ? (
        <Text style={styles.optionReason} numberOfLines={2}>{meal.reason}</Text>
      ) : null}
      {meal.prep_time_min ? (
        <Text style={styles.prepTime}>⏱ {meal.prep_time_min} min</Text>
      ) : null}
      {isActive && (
        <View style={styles.activeChip}>
          <Text style={styles.activeChipTxt}>✓</Text>
        </View>
      )}
    </TouchableOpacity>
  );

  const renderMealSection = (
    mealType: keyof Recommendation,
    icon: string,
    labelKey: string,
  ) => {
    const meals = recommendation?.[mealType] as Meal[] | undefined;
    if (!meals?.length) return null;
    const selectedIdx = selectedMeals[mealType as string] ?? 0;
    const selectedMeal = meals[selectedIdx];
    const fb = feedback[mealType as string];
    const isLoadingFb = feedbackLoading === mealType;

    return (
      <View style={styles.mealSection} key={mealType as string}>
        {/* Section header */}
        <View style={styles.mealHeader}>
          <Text style={styles.mealIcon}>{icon}</Text>
          <Text style={styles.mealTypeLabel}>{t(labelKey, lang)}</Text>
          {meals.length > 1 && (
            <Text style={styles.optionCount}>{selectedIdx + 1}/{meals.length}</Text>
          )}
        </View>

        {/* Horizontal option cards */}
        <FlatList
          data={meals}
          horizontal
          showsHorizontalScrollIndicator={false}
          keyExtractor={(_, i) => String(i)}
          contentContainerStyle={styles.optionList}
          renderItem={({ item, index }) =>
            renderOptionCard(item, mealType as string, index, index === selectedIdx)
          }
          snapToInterval={OPTION_CARD_W + spacing.sm}
          decelerationRate="fast"
        />

        {/* Feedback row for selected meal */}
        <View style={styles.feedbackRow}>
          {(['liked', 'neutral', 'disliked'] as const).map(fbType => {
            const icons  = { liked: '👍', neutral: '😐', disliked: '👎' };
            const fbKeys = {
              liked:    'diet.feedback_like',
              neutral:  'diet.feedback_neutral',
              disliked: 'diet.feedback_dislike',
            };
            const isActive = fb === fbType;
            return (
              <TouchableOpacity
                accessibilityRole="button"
                accessibilityLabel='icons[fbType] t(fbKeys[fbType], lang)'
                key={fbType}
                style={[styles.fbBtn, isActive && styles.fbBtnActive]}
                onPress={() =>
                  submitFeedback(mealType as string, selectedMeal.name, fbType)
                }
                disabled={isLoadingFb || !!fb}
                activeOpacity={0.8}
              >
                {isLoadingFb ? (
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
        <TouchableOpacity onPress={() => navigation.goBack()} style={styles.backBtn}
          accessibilityRole="button"
          accessibilityLabel={t('diet.title', lang)}
        >
          <Text style={styles.backText}>←</Text>
        </TouchableOpacity>
        <Text style={styles.title}>{t('diet.title', lang)}</Text>
        <View style={styles.spacer} />
      </View>

      <ScrollView
        contentContainerStyle={styles.scroll}
        showsVerticalScrollIndicator={false}
      >
        <Text style={styles.subtitle}>{t('diet.subtitle', lang)}</Text>

        <View style={styles.countryRow}>
          <Text style={styles.countryLabel}>{t('diet.country', lang)}</Text>
          <View style={styles.countryBadge}>
            <Text style={styles.countryBadgeTxt}>{countryCode}</Text>
          </View>
        </View>

        <TouchableOpacity
          accessibilityRole="button"
          accessibilityLabel={t('diet.get_recommendation', lang)}
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
              renderMealSection(key, icon, labelKey),
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
  mealsContainer: { gap: spacing.xl },

  mealSection:  {
    backgroundColor: colors.surface, borderRadius: radius.lg,
    borderWidth: 1, borderColor: colors.border,
    paddingVertical: spacing.md, gap: spacing.sm,
    overflow: 'hidden' as const,
  },
  mealHeader:   {
    flexDirection: 'row', alignItems: 'center', gap: spacing.sm,
    paddingHorizontal: spacing.md,
  },
  mealIcon:     { fontSize: 22 },
  mealTypeLabel: { ...typography.label, color: colors.gold, fontSize: 13, fontWeight: '700' as const, flex: 1 },
  optionCount:  { ...typography.caption, color: colors.textMuted, fontSize: 11 },

  optionList:   { paddingHorizontal: spacing.md, gap: spacing.sm },
  optionCard:   {
    width: OPTION_CARD_W,
    backgroundColor: colors.background, borderRadius: radius.md,
    borderWidth: 1.5, borderColor: colors.border,
    padding: spacing.md, gap: 6,
    position: 'relative' as const,
  },
  optionCardActive: {
    borderColor: colors.gold, backgroundColor: colors.goldGlow,
  },
  activeIndicator: {
    position: 'absolute' as const, top: 0, left: 0, right: 0,
    height: 2, backgroundColor: colors.gold, borderRadius: 1,
  },
  activeChip:   {
    position: 'absolute' as const, top: spacing.sm, right: spacing.sm,
    width: 20, height: 20, borderRadius: 10,
    backgroundColor: colors.gold, alignItems: 'center' as const, justifyContent: 'center' as const,
  },
  activeChipTxt: { color: '#000', fontSize: 10, fontWeight: '700' as const },
  optionName:   { ...typography.h2, fontSize: 15, color: colors.textPrimary },
  optionNameActive: { color: colors.gold },
  optionDesc:   { ...typography.body, color: colors.textSecondary, fontSize: 12, lineHeight: 17 },
  optionReason: { ...typography.caption, color: colors.textMuted, fontSize: 11, fontStyle: 'italic' as const },
  prepTime:     { ...typography.caption, color: colors.textMuted, fontSize: 11 },

  feedbackRow:  { flexDirection: 'row', gap: spacing.xs, paddingHorizontal: spacing.md, marginTop: spacing.xs },
  fbBtn:        {
    flex: 1, paddingVertical: 8, borderRadius: radius.sm,
    borderWidth: 1, borderColor: colors.border,
    alignItems: 'center' as const, backgroundColor: colors.background,
  },
  fbBtnActive:   { borderColor: colors.gold, backgroundColor: colors.goldGlow },
  fbBtnTxt:     { ...typography.caption, color: colors.textMuted, fontSize: 11 },
  fbBtnTxtActive: { color: colors.gold, fontWeight: '700' as const },
  feedbackSent: { ...typography.caption, color: colors.gold, fontSize: 11, textAlign: 'center' as const, paddingHorizontal: spacing.md },

  emptyContainer: { alignItems: 'center' as const, paddingVertical: spacing.xl * 2, gap: spacing.md },
  emptyIcon:    { fontSize: 56 },
  emptyText:    { ...typography.body, color: colors.textMuted, textAlign: 'center' as const },
});

export default DietScreen;

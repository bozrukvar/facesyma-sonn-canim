// src/screens/MealGameScreen.tsx
import React, { useEffect, useState, useCallback } from 'react';
import {
  View, Text, StyleSheet, FlatList, TouchableOpacity,
  ActivityIndicator, StatusBar, Alert,
} from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { GamificationAPI, MealItem } from '../services/api';
import theme from '../utils/theme';
import { useLanguage } from '../utils/LanguageContext';
import { t } from '../utils/i18n';
import type { ScreenProps } from '../navigation/types';

const { colors, spacing, typography, radius, shadow } = theme;
type Props = ScreenProps<'MealGame'>;

type Phase = 'browse' | 'guess';

const SIFAT_OPTIONS = ['Analitik', 'Empatik', 'Baskın', 'Yaratıcı', 'Sosyal', 'İçe dönük', 'Nazik', 'Enerjik'];

const MealGameScreen: React.FC<Props> = ({ navigation, route }) => {
  const insets = useSafeAreaInsets();
  const { lang } = useLanguage();
  const initCountry = route?.params?.countryCode;
  const [meals, setMeals] = useState<MealItem[]>([]);
  const [country, setCountry] = useState('');
  const [weekKey, setWeekKey] = useState('');
  const [loading, setLoading] = useState(true);
  const [phase, setPhase] = useState<Phase>('browse');
  const [selectedMeal, setSelectedMeal] = useState<MealItem | null>(null);
  const [guessing, setGuessing] = useState(false);
  const [balance, setBalance] = useState<number | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const [mealsRes, balRes] = await Promise.all([
        GamificationAPI.getWeeklyMeals(initCountry),
        GamificationAPI.getCoinBalance(),
      ]);
      setMeals(mealsRes.meals);
      setCountry(mealsRes.country);
      setWeekKey(mealsRes.week_key);
      setBalance(balRes.balance);
    } catch {
      // keep stale
    } finally {
      setLoading(false);
    }
  }, [initCountry]);

  useEffect(() => { load(); }, [load]);

  const selectMeal = async (meal: MealItem) => {
    try {
      const res = await GamificationAPI.selectMeal(meal.id, initCountry ?? '');
      setBalance(res.new_balance);
      setSelectedMeal(meal);
      setPhase('guess');
    } catch (e: any) {
      Alert.alert(t('meal_game.title', lang), e?.response?.data?.error || t('common.error', lang));
    }
  };

  const guessOption = async (guess: string) => {
    if (!selectedMeal) return;
    setGuessing(true);
    try {
      const res = await GamificationAPI.guessSifat(selectedMeal.id, initCountry ?? '', guess);
      const emoji = res.correct ? '🎉' : '😢';
      const msg = res.correct
        ? `${t('meal_game.correct', lang)}! +${res.coins_earned} 🪙`
        : `${t('meal_game.wrong', lang)}. ${t('meal_game.correct_sifat', lang)}: ${res.correct_sifat}`;
      Alert.alert(`${emoji} ${t('meal_game.guess_sifat', lang)}`, msg, [
        { text: 'OK', onPress: () => { setPhase('browse'); setSelectedMeal(null); load(); } },
      ]);
    } catch (e: any) {
      Alert.alert(t('meal_game.title', lang), e?.response?.data?.error || t('common.error', lang));
    } finally {
      setGuessing(false);
    }
  };

  const renderMeal = ({ item }: { item: MealItem }) => (
    <TouchableOpacity
      accessibilityRole="button"
      accessibilityLabel={item.name}
      style={styles.mealCard}
      onPress={() => selectMeal(item)}
      activeOpacity={0.85}
    >
      <View style={styles.mealLeft}>
        <Text style={styles.mealEmoji}>🍽️</Text>
        <View>
          <Text style={styles.mealName}>{item.name}</Text>
          {item.description ? <Text style={styles.mealDesc} numberOfLines={1}>{item.description}</Text> : null}
        </View>
      </View>
      {item.coin_cost != null && (
        <Text style={styles.mealCost}>🪙 {item.coin_cost}</Text>
      )}
    </TouchableOpacity>
  );

  if (loading) {
    return (
      <View style={styles.center}>
        <ActivityIndicator size="large" color={colors.gold} />
      </View>
    );
  }

  if (phase === 'guess' && selectedMeal) {
    return (
      <View style={styles.container}>
        <StatusBar barStyle="light-content" />
        <View style={[styles.topBar, { paddingTop: insets.top + spacing.md }]}>
          <TouchableOpacity onPress={() => { setPhase('browse'); setSelectedMeal(null); }} style={styles.backBtn}
            accessibilityRole="button"
            accessibilityLabel={t('meal_game.guess_sifat', lang)}
          >
            <Text style={styles.backArrow}>←</Text>
          </TouchableOpacity>
          <Text style={styles.title}>{t('meal_game.guess_sifat', lang)}</Text>
        </View>

        <View style={styles.guessCard}>
          <Text style={styles.guessEmoji}>🍽️</Text>
          <Text style={styles.guessName}>{selectedMeal.name}</Text>
          <Text style={styles.guessPrompt}>{t('meal_game.guess_prompt', lang)}</Text>
        </View>

        <View style={styles.optionGrid}>
          {SIFAT_OPTIONS.map(opt => (
            <TouchableOpacity
              accessibilityRole="button"
              accessibilityLabel={opt}
              key={opt}
              style={styles.optionBtn}
              onPress={() => guessOption(opt)}
              disabled={guessing}
            >
              <Text style={styles.optionText}>{opt}</Text>
            </TouchableOpacity>
          ))}
        </View>
        {guessing && <ActivityIndicator color={colors.gold} style={{ marginTop: spacing.md }} />}
      </View>
    );
  }

  return (
    <View style={styles.container}>
      <StatusBar barStyle="light-content" />
      <FlatList
        data={meals}
        keyExtractor={item => item.id}
        renderItem={renderMeal}
        contentContainerStyle={[styles.list, { paddingTop: insets.top + spacing.md }]}
        ListHeaderComponent={() => (
          <>
            <View style={styles.topBar}>
              <TouchableOpacity onPress={() => navigation.goBack()} style={styles.backBtn}
                accessibilityRole="button"
                accessibilityLabel={t('meal_game.title', lang)}
              >
                <Text style={styles.backArrow}>←</Text>
              </TouchableOpacity>
              <Text style={styles.title}>{t('meal_game.title', lang)}</Text>
            </View>

            <View style={styles.countryBanner}>
              <Text style={styles.countryFlag}>🌍</Text>
              <View>
                <Text style={styles.countryName}>{country}</Text>
                <Text style={styles.weekText}>{t('meal_game.weekly_country', lang)} — {weekKey}</Text>
              </View>
              {balance != null && <Text style={styles.balText}>🪙 {balance.toLocaleString()}</Text>}
            </View>

            <Text style={styles.instruction}>{t('meal_game.select_meal', lang)}</Text>
          </>
        )}
        ListEmptyComponent={() => <Text style={styles.empty}>{t('meal_game.empty', lang)}</Text>}
      />
    </View>
  );
};

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: colors.background },
  center: { flex: 1, alignItems: 'center', justifyContent: 'center', backgroundColor: colors.background },
  topBar: { flexDirection: 'row', alignItems: 'center', marginBottom: spacing.md, paddingHorizontal: spacing.lg },
  backBtn: { marginRight: spacing.md, padding: 4 },
  backArrow: { fontSize: 22, color: colors.textPrimary },
  title: { ...typography.h2, flex: 1 },
  list: { paddingBottom: 40 },
  countryBanner: {
    flexDirection: 'row', alignItems: 'center', gap: spacing.sm,
    backgroundColor: colors.surface, borderRadius: radius.lg ?? 16,
    padding: spacing.md, marginHorizontal: spacing.lg, marginBottom: spacing.md,
    ...shadow.sm,
  },
  countryFlag: { fontSize: 28 },
  countryName: { ...typography.body, color: colors.textPrimary, fontWeight: '700' },
  weekText: { ...typography.caption, color: colors.textMuted, fontSize: 11 },
  balText: { ...typography.body, color: colors.gold, fontWeight: '700', marginLeft: 'auto' as any },
  instruction: { ...typography.goldLabel, marginHorizontal: spacing.lg, marginBottom: spacing.sm },
  mealCard: {
    flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between',
    backgroundColor: colors.surface, borderRadius: radius.md ?? 12,
    padding: spacing.md, marginHorizontal: spacing.lg, marginBottom: spacing.sm, ...shadow.sm,
  },
  mealLeft: { flexDirection: 'row', alignItems: 'center', gap: spacing.sm, flex: 1 },
  mealEmoji: { fontSize: 28 },
  mealName: { ...typography.body, color: colors.textPrimary, fontWeight: '600' },
  mealDesc: { ...typography.caption, color: colors.textMuted, fontSize: 11 },
  mealCost: { ...typography.body, color: colors.gold, fontWeight: '700' },
  empty: { ...typography.body, color: colors.textMuted, textAlign: 'center' as any, marginTop: 40 },
  // Guess phase
  guessCard: {
    margin: spacing.lg, backgroundColor: colors.surface, borderRadius: radius.lg ?? 16,
    padding: spacing.xl ?? 24, alignItems: 'center', ...shadow.sm,
    borderWidth: 1, borderColor: `${colors.gold}30`,
  },
  guessEmoji: { fontSize: 48, marginBottom: spacing.md },
  guessName: { ...typography.h2, textAlign: 'center' as any, marginBottom: spacing.sm },
  guessPrompt: { ...typography.caption, color: colors.textMuted, textAlign: 'center' as any },
  optionGrid: {
    flexDirection: 'row', flexWrap: 'wrap', gap: spacing.sm,
    paddingHorizontal: spacing.lg,
  },
  optionBtn: {
    flex: 1, minWidth: '45%' as any,
    backgroundColor: colors.surface, borderRadius: radius.md ?? 12,
    padding: spacing.md, alignItems: 'center',
    borderWidth: 1, borderColor: `${colors.gold}30`, ...shadow.sm,
  },
  optionText: { ...typography.body, color: colors.textPrimary, fontWeight: '600' },
});

export default MealGameScreen;

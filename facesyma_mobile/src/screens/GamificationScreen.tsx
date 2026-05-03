// src/screens/GamificationScreen.tsx
import React, { useEffect, useState, useCallback } from 'react';
import {
  View, Text, StyleSheet, ScrollView, TouchableOpacity,
  ActivityIndicator, StatusBar,
} from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { useSelector } from 'react-redux';
import { RootState } from '../store';
import { GamificationAPI } from '../services/api';
import theme from '../utils/theme';
import { useLanguage } from '../utils/LanguageContext';
import { t } from '../utils/i18n';
import type { ScreenProps } from '../navigation/types';

const { colors, spacing, typography, radius, shadow } = theme;

type Props = ScreenProps<'Gamification'>;

interface HubCard {
  id: string;
  emoji: string;
  titleKey: string;
  descKey: string;
  screen: keyof typeof SCREEN_MAP;
  accent: string;
}

const SCREEN_MAP = {
  CoinWallet:    'CoinWallet',
  Leaderboard:   'Leaderboard',
  Badges:        'Badges',
  Challenges:    'Challenges',
  Missions:      'Missions',
  MealGame:      'MealGame',
  DiscoveryGame: 'DiscoveryGame',
} as const;

const getHubCards = (lang: string): HubCard[] => [
  { id: 'coins',     emoji: '🪙', titleKey: 'coin.balance',         descKey: 'coin.history',       screen: 'CoinWallet',    accent: '#F5C842' },
  { id: 'lb',        emoji: '🏆', titleKey: 'leaderboard.title',    descKey: 'leaderboard.global', screen: 'Leaderboard',   accent: '#9B7AE0' },
  { id: 'badges',    emoji: '🎖️', titleKey: 'badge.title',          descKey: 'badge.earned',       screen: 'Badges',        accent: '#E07A7A' },
  { id: 'challenge', emoji: '⚔️', titleKey: 'challenge.title',      descKey: 'challenge.active',   screen: 'Challenges',    accent: '#7AE0B0' },
  { id: 'mission',   emoji: '🌍', titleKey: 'gamification.missions',descKey: 'gamification.missions_desc', screen: 'Missions', accent: '#7AAEE0' },
  { id: 'meal',      emoji: '🍽️', titleKey: 'meal_game.title',      descKey: 'meal_game.weekly_country',  screen: 'MealGame',  accent: '#7AE07A' },
  { id: 'discovery', emoji: '🔍', titleKey: 'discovery.title',      descKey: 'discovery.select_type',     screen: 'DiscoveryGame', accent: '#E0A17A' },
];

const GamificationScreen: React.FC<Props> = ({ navigation }) => {
  const insets = useSafeAreaInsets();
  const { lang } = useLanguage();
  const user = useSelector((s: RootState) => s.auth.user);
  const [balance, setBalance] = useState<number | null>(null);
  const [loading, setLoading] = useState(true);

  const loadBalance = useCallback(async () => {
    try {
      const res = await GamificationAPI.getCoinBalance();
      setBalance(res.balance);
    } catch {
      setBalance(null);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { loadBalance(); }, [loadBalance]);

  const CARDS = getHubCards(lang);

  return (
    <View style={styles.container}>
      <StatusBar barStyle="light-content" />
      <ScrollView
        showsVerticalScrollIndicator={false}
        contentContainerStyle={[styles.scroll, { paddingTop: insets.top + spacing.md }]}
      >
        {/* Header */}
        <View style={styles.header}>
          <TouchableOpacity onPress={() => navigation.goBack()} style={styles.backBtn}>
            <Text style={styles.backArrow}>←</Text>
          </TouchableOpacity>
          <Text style={styles.title}>{t('gamification.title', lang)}</Text>
        </View>

        {/* Coin balance banner */}
        <TouchableOpacity
          style={styles.coinBanner}
          onPress={() => navigation.navigate('CoinWallet')}
          activeOpacity={0.85}
        >
          <View style={styles.coinLeft}>
            <Text style={styles.coinEmoji}>🪙</Text>
            <View>
              <Text style={styles.coinLabel}>{t('coin.balance', lang)}</Text>
              {loading ? (
                <ActivityIndicator size="small" color={colors.gold} />
              ) : (
                <Text style={styles.coinValue}>{balance?.toLocaleString() ?? '—'}</Text>
              )}
            </View>
          </View>
          <View style={styles.coinRight}>
            <Text style={styles.dailyLabel}>{t('coin.daily_quest', lang)}</Text>
            <Text style={styles.coinArrow}>→</Text>
          </View>
        </TouchableOpacity>

        {/* Grid of feature cards */}
        <Text style={styles.sectionLabel}>{t('gamification.features', lang)}</Text>
        <View style={styles.grid}>
          {CARDS.map(card => (
            <TouchableOpacity
              key={card.id}
              style={[styles.card, { borderColor: `${card.accent}30` }]}
              onPress={() => (navigation.navigate as any)(card.screen)}
              activeOpacity={0.85}
            >
              <View style={[styles.iconWrap, { backgroundColor: `${card.accent}15` }]}>
                <Text style={styles.cardIcon}>{card.emoji}</Text>
              </View>
              <Text style={styles.cardTitle}>{t(card.titleKey, lang)}</Text>
              <Text style={styles.cardDesc} numberOfLines={2}>{t(card.descKey, lang)}</Text>
            </TouchableOpacity>
          ))}
        </View>
      </ScrollView>
    </View>
  );
};

const CARD_W = (375 - spacing.lg * 2 - spacing.sm) / 2;

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: colors.background },
  scroll: { paddingHorizontal: spacing.lg, paddingBottom: spacing.xxl ?? 48 },
  header: { flexDirection: 'row', alignItems: 'center', marginBottom: spacing.lg },
  backBtn: { marginRight: spacing.md, padding: 4 },
  backArrow: { fontSize: 22, color: colors.textPrimary },
  title: { ...typography.h2, flex: 1 },
  coinBanner: {
    flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between',
    backgroundColor: colors.surface, borderRadius: radius.lg ?? 16,
    padding: spacing.md, marginBottom: spacing.lg,
    borderWidth: 1, borderColor: `${colors.gold}30`,
    ...shadow.sm,
  },
  coinLeft: { flexDirection: 'row', alignItems: 'center', gap: spacing.sm },
  coinEmoji: { fontSize: 28 },
  coinLabel: { ...typography.caption, color: colors.textMuted, marginBottom: 2 },
  coinValue: { ...typography.h3 ?? typography.h2, color: colors.gold, fontSize: 22, fontWeight: '700' },
  coinRight: { alignItems: 'flex-end' },
  dailyLabel: { ...typography.caption, color: colors.textMuted, fontSize: 11 },
  coinArrow: { fontSize: 18, color: colors.gold, marginTop: 4 },
  sectionLabel: { ...typography.goldLabel, marginBottom: spacing.md },
  grid: { flexDirection: 'row', flexWrap: 'wrap', gap: spacing.sm },
  card: {
    width: CARD_W, backgroundColor: colors.surface,
    borderRadius: radius.lg ?? 16, borderWidth: 1,
    padding: spacing.md, ...shadow.sm,
  },
  iconWrap: {
    width: 44, height: 44, borderRadius: 12,
    alignItems: 'center', justifyContent: 'center',
    marginBottom: spacing.sm,
  },
  cardIcon: { fontSize: 22 },
  cardTitle: { ...typography.label ?? typography.body, fontWeight: '700', color: colors.textPrimary, marginBottom: 4 },
  cardDesc: { ...typography.caption, color: colors.textMuted, fontSize: 11, lineHeight: 15 },
});

export default GamificationScreen;

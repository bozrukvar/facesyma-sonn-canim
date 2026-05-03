// src/screens/LeaderboardScreen.tsx
import React, { useEffect, useState, useCallback } from 'react';
import {
  View, Text, StyleSheet, FlatList, TouchableOpacity,
  ActivityIndicator, StatusBar,
} from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { useSelector } from 'react-redux';
import { RootState } from '../store';
import { GamificationAPI, LeaderboardEntry } from '../services/api';
import theme from '../utils/theme';
import { useLanguage } from '../utils/LanguageContext';
import { t } from '../utils/i18n';
import type { ScreenProps } from '../navigation/types';

const { colors, spacing, typography, radius, shadow } = theme;
type Props = ScreenProps<'Leaderboard'>;

type Tab = 'global' | 'trending';

const RANK_EMOJI: Record<number, string> = { 1: '🥇', 2: '🥈', 3: '🥉' };

const LeaderboardScreen: React.FC<Props> = ({ navigation, route }) => {
  const insets = useSafeAreaInsets();
  const { lang } = useLanguage();
  const currentUserId = useSelector((s: RootState) => s.auth.user?.id);
  const [tab, setTab] = useState<Tab>(route?.params?.tab ?? 'global');
  const [entries, setEntries] = useState<LeaderboardEntry[]>([]);
  const [trending, setTrending] = useState<Array<{ user_id: number; username: string; rank_improvement: number; coins_gained: number; current_rank: number }>>([]);
  const [myRank, setMyRank] = useState<number | null>(null);
  const [loading, setLoading] = useState(true);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      if (tab === 'global') {
        const res = await GamificationAPI.getLeaderboard('global', 50);
        setEntries(res.entries);
        setMyRank(res.user_rank ?? null);
      } else {
        const res = await GamificationAPI.getTrendingUsers(7, 30);
        setTrending(res.trending);
      }
    } catch {
      // keep stale
    } finally {
      setLoading(false);
    }
  }, [tab]);

  useEffect(() => { load(); }, [load]);

  const renderGlobal = ({ item, index }: { item: LeaderboardEntry; index: number }) => {
    const isMe = item.user_id === currentUserId;
    const rank = item.rank ?? index + 1;
    return (
      <View style={[styles.row, isMe && styles.rowMe]}>
        <Text style={styles.rankText}>{RANK_EMOJI[rank] ?? `#${rank}`}</Text>
        <View style={styles.rowBody}>
          <Text style={[styles.username, isMe && styles.usernameMe]}>{item.username}</Text>
          {isMe && <Text style={styles.youTag}>{t('leaderboard.your_rank', lang)}</Text>}
        </View>
        <Text style={styles.coins}>🪙 {item.coins.toLocaleString()}</Text>
      </View>
    );
  };

  const renderTrending = ({ item }: { item: typeof trending[0] }) => {
    const sign = item.rank_improvement >= 0 ? '↑' : '↓';
    const rankColor = item.rank_improvement >= 0 ? '#7AE07A' : '#E07A7A';
    return (
      <View style={styles.row}>
        <Text style={styles.rankText}>#{item.current_rank}</Text>
        <View style={styles.rowBody}>
          <Text style={styles.username}>{item.username}</Text>
          <Text style={[styles.trendChange, { color: rankColor }]}>
            {sign}{Math.abs(item.rank_improvement)} {t('leaderboard.rank_change', lang)}
          </Text>
        </View>
        <Text style={styles.coins}>+{item.coins_gained} 🪙</Text>
      </View>
    );
  };

  return (
    <View style={styles.container}>
      <StatusBar barStyle="light-content" />
      <View style={[styles.topBar, { paddingTop: insets.top + spacing.md }]}>
        <TouchableOpacity onPress={() => navigation.goBack()} style={styles.backBtn}>
          <Text style={styles.backArrow}>←</Text>
        </TouchableOpacity>
        <Text style={styles.title}>{t('leaderboard.title', lang)}</Text>
      </View>

      {/* My rank quick badge */}
      {myRank && tab === 'global' && (
        <View style={styles.myRankBar}>
          <Text style={styles.myRankText}>{t('leaderboard.your_rank', lang)}: #{myRank}</Text>
        </View>
      )}

      {/* Tab bar */}
      <View style={styles.tabBar}>
        {(['global', 'trending'] as Tab[]).map(tabId => (
          <TouchableOpacity
            key={tabId}
            style={[styles.tab, tab === tabId && styles.tabActive]}
            onPress={() => setTab(tabId)}
            activeOpacity={0.85}
          >
            <Text style={[styles.tabText, tab === tabId && styles.tabTextActive]}>
              {t(`leaderboard.${tabId}`, lang)}
            </Text>
          </TouchableOpacity>
        ))}
      </View>

      {loading ? (
        <View style={styles.center}>
          <ActivityIndicator size="large" color={colors.gold} />
        </View>
      ) : tab === 'global' ? (
        <FlatList
          data={entries}
          keyExtractor={item => String(item.user_id)}
          renderItem={renderGlobal}
          contentContainerStyle={styles.list}
          ListEmptyComponent={() => <Text style={styles.empty}>{t('leaderboard.empty', lang)}</Text>}
        />
      ) : (
        <FlatList
          data={trending}
          keyExtractor={item => String(item.user_id)}
          renderItem={renderTrending}
          contentContainerStyle={styles.list}
          ListHeaderComponent={() => (
            <Text style={styles.trendHint}>{t('leaderboard.trending', lang)} — 7 {t('leaderboard.days', lang)}</Text>
          )}
          ListEmptyComponent={() => <Text style={styles.empty}>{t('leaderboard.empty', lang)}</Text>}
        />
      )}
    </View>
  );
};

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: colors.background },
  topBar: { flexDirection: 'row', alignItems: 'center', paddingHorizontal: spacing.lg, paddingBottom: spacing.md },
  backBtn: { marginRight: spacing.md, padding: 4 },
  backArrow: { fontSize: 22, color: colors.textPrimary },
  title: { ...typography.h2, flex: 1 },
  myRankBar: {
    marginHorizontal: spacing.lg, marginBottom: spacing.sm,
    backgroundColor: `${colors.gold}20`, borderRadius: radius.sm ?? 8,
    padding: spacing.sm, alignItems: 'center',
  },
  myRankText: { ...typography.label ?? typography.body, color: colors.gold, fontWeight: '700' },
  tabBar: {
    flexDirection: 'row', marginHorizontal: spacing.lg,
    backgroundColor: colors.surface, borderRadius: radius.md ?? 12,
    padding: 4, marginBottom: spacing.md,
  },
  tab: { flex: 1, padding: spacing.sm, borderRadius: radius.sm ?? 8, alignItems: 'center' },
  tabActive: { backgroundColor: colors.gold },
  tabText: { ...typography.body, color: colors.textMuted, fontWeight: '600' },
  tabTextActive: { color: colors.background },
  center: { flex: 1, alignItems: 'center', justifyContent: 'center' },
  list: { paddingHorizontal: spacing.lg, paddingBottom: 40 },
  row: {
    flexDirection: 'row', alignItems: 'center',
    backgroundColor: colors.surface, borderRadius: radius.md ?? 12,
    padding: spacing.md, marginBottom: spacing.sm, ...shadow.sm,
  },
  rowMe: { borderWidth: 1, borderColor: colors.gold },
  rankText: { fontSize: 20, width: 40, textAlign: 'center' as any },
  rowBody: { flex: 1, marginHorizontal: spacing.sm },
  username: { ...typography.body, color: colors.textPrimary, fontWeight: '600' },
  usernameMe: { color: colors.gold },
  youTag: { ...typography.caption, color: colors.gold, fontSize: 10 },
  coins: { ...typography.body, color: colors.textMuted, fontSize: 13 },
  trendChange: { fontSize: 12, fontWeight: '700', marginTop: 2 },
  trendHint: { ...typography.caption, color: colors.textMuted, marginBottom: spacing.sm },
  empty: { ...typography.body, color: colors.textMuted, textAlign: 'center' as any, marginTop: 40 },
});

export default LeaderboardScreen;

// src/screens/BadgesScreen.tsx
import React, { useEffect, useState, useCallback } from 'react';
import {
  View, Text, StyleSheet, FlatList, TouchableOpacity,
  ActivityIndicator, StatusBar,
} from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { GamificationAPI, Badge, UserBadge } from '../services/api';
import theme from '../utils/theme';
import { useLanguage } from '../utils/LanguageContext';
import { t } from '../utils/i18n';
import type { ScreenProps } from '../navigation/types';

const { colors, spacing, typography, radius, shadow } = theme;
type Props = ScreenProps<'Badges'>;

const TIER_COLOR: Record<string, string> = {
  platinum: '#B0C4DE',
  gold:     '#FFD700',
  silver:   '#C0C0C0',
  bronze:   '#CD7F32',
};

const BadgesScreen: React.FC<Props> = ({ navigation }) => {
  const insets = useSafeAreaInsets();
  const { lang } = useLanguage();
  const [allBadges, setAllBadges] = useState<Badge[]>([]);
  const [userBadges, setUserBadges] = useState<Record<string, UserBadge>>({});
  const [loading, setLoading] = useState(true);
  const [tab, setTab] = useState<'earned' | 'all'>('earned');

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const [allRes, userRes] = await Promise.all([
        GamificationAPI.getAllBadges(),
        GamificationAPI.getUserBadges(),
      ]);
      setAllBadges(allRes.badges);
      setUserBadges(userRes.badges);
    } catch {
      // keep stale
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { load(); }, [load]);

  const earnedBadges = allBadges.filter(b => userBadges[b.badge_id]);
  const displayList = tab === 'earned' ? earnedBadges : allBadges;

  const renderBadge = ({ item }: { item: Badge }) => {
    const userBadge = userBadges[item.badge_id];
    const tier = userBadge?.current_tier;
    const progress = userBadge?.current_progress ?? 0;
    const maxThreshold = item.tiers[item.tiers.length - 1]?.threshold ?? 1;
    const pct = Math.min(1, progress / maxThreshold);
    const tierColor = tier ? TIER_COLOR[tier] : colors.textMuted;
    const unlocked = !!userBadge;

    return (
      <View style={[styles.badgeCard, !unlocked && styles.badgeLocked]}>
        <View style={[styles.badgeIcon, { backgroundColor: `${tierColor}20` }]}>
          <Text style={styles.badgeEmoji}>{item.icon_emoji}</Text>
        </View>
        <View style={styles.badgeBody}>
          <View style={styles.badgeNameRow}>
            <Text style={[styles.badgeName, !unlocked && styles.textMuted]}>{item.name}</Text>
            {tier && <Text style={[styles.tierTag, { color: tierColor }]}>{tier.toUpperCase()}</Text>}
          </View>
          <Text style={styles.badgeDesc} numberOfLines={2}>{item.description}</Text>
          {/* Progress bar */}
          <View style={styles.progressBg}>
            <View style={[styles.progressFill, { width: `${pct * 100}%` as any, backgroundColor: tierColor }]} />
          </View>
          <Text style={styles.progressLabel}>{progress}/{maxThreshold}</Text>
        </View>
        {unlocked && (
          <Text style={styles.coinsEarned}>🪙 {userBadge.total_coins_earned}</Text>
        )}
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
        <Text style={styles.title}>{t('badge.title', lang)}</Text>
      </View>

      {/* Stats summary */}
      <View style={styles.statsRow}>
        <View style={styles.statBox}>
          <Text style={styles.statVal}>{earnedBadges.length}</Text>
          <Text style={styles.statLabel}>{t('badge.earned', lang)}</Text>
        </View>
        <View style={styles.statBox}>
          <Text style={styles.statVal}>{allBadges.length}</Text>
          <Text style={styles.statLabel}>{t('badge.total', lang)}</Text>
        </View>
        <View style={styles.statBox}>
          <Text style={styles.statVal}>
            {Object.values(userBadges).reduce((s, b) => s + b.total_coins_earned, 0).toLocaleString()} 🪙
          </Text>
          <Text style={styles.statLabel}>{t('badge.coins', lang)}</Text>
        </View>
      </View>

      {/* Tab bar */}
      <View style={styles.tabBar}>
        {(['earned', 'all'] as const).map(tabId => (
          <TouchableOpacity
            key={tabId}
            style={[styles.tab, tab === tabId && styles.tabActive]}
            onPress={() => setTab(tabId)}
            activeOpacity={0.85}
          >
            <Text style={[styles.tabText, tab === tabId && styles.tabTextActive]}>
              {t(`badge.${tabId}`, lang)}
            </Text>
          </TouchableOpacity>
        ))}
      </View>

      {loading ? (
        <View style={styles.center}>
          <ActivityIndicator size="large" color={colors.gold} />
        </View>
      ) : (
        <FlatList
          data={displayList}
          keyExtractor={item => item.badge_id}
          renderItem={renderBadge}
          contentContainerStyle={styles.list}
          ListEmptyComponent={() => <Text style={styles.empty}>{t('badge.empty', lang)}</Text>}
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
  statsRow: {
    flexDirection: 'row', marginHorizontal: spacing.lg,
    marginBottom: spacing.md, gap: spacing.sm,
  },
  statBox: {
    flex: 1, backgroundColor: colors.surface, borderRadius: radius.md ?? 12,
    padding: spacing.sm, alignItems: 'center', ...shadow.sm,
  },
  statVal: { ...typography.h3 ?? typography.h2, color: colors.gold, fontWeight: '700', fontSize: 18 },
  statLabel: { ...typography.caption, color: colors.textMuted, fontSize: 10 },
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
  badgeCard: {
    flexDirection: 'row', alignItems: 'center',
    backgroundColor: colors.surface, borderRadius: radius.md ?? 12,
    padding: spacing.md, marginBottom: spacing.sm, ...shadow.sm,
  },
  badgeLocked: { opacity: 0.5 },
  badgeIcon: {
    width: 50, height: 50, borderRadius: 12,
    alignItems: 'center', justifyContent: 'center',
    marginRight: spacing.sm,
  },
  badgeEmoji: { fontSize: 26 },
  badgeBody: { flex: 1 },
  badgeNameRow: { flexDirection: 'row', alignItems: 'center', gap: spacing.sm, marginBottom: 2 },
  badgeName: { ...typography.body, color: colors.textPrimary, fontWeight: '700', fontSize: 13 },
  textMuted: { color: colors.textMuted },
  tierTag: { fontSize: 10, fontWeight: '800', letterSpacing: 0.5 },
  badgeDesc: { ...typography.caption, color: colors.textMuted, fontSize: 11, marginBottom: 4 },
  progressBg: { height: 4, backgroundColor: `${colors.border}40`, borderRadius: 2 },
  progressFill: { height: 4, borderRadius: 2 },
  progressLabel: { ...typography.caption, color: colors.textMuted, fontSize: 10, marginTop: 2 },
  coinsEarned: { ...typography.caption, color: colors.gold, fontWeight: '700', fontSize: 12, marginLeft: spacing.sm },
  empty: { ...typography.body, color: colors.textMuted, textAlign: 'center' as any, marginTop: 40 },
});

export default BadgesScreen;

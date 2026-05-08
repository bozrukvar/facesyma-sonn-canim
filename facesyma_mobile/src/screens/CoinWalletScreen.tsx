// src/screens/CoinWalletScreen.tsx
import React, { useEffect, useState, useCallback } from 'react';
import {
  View, Text, StyleSheet, FlatList, TouchableOpacity,
  ActivityIndicator, StatusBar, Alert,
} from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { GamificationAPI, CoinTransaction } from '../services/api';
import theme from '../utils/theme';
import { useLanguage } from '../utils/LanguageContext';
import { t } from '../utils/i18n';
import type { ScreenProps } from '../navigation/types';

const { colors, spacing, typography, radius, shadow } = theme;
type Props = ScreenProps<'CoinWallet'>;

const CoinWalletScreen: React.FC<Props> = ({ navigation }) => {
  const insets = useSafeAreaInsets();
  const { lang } = useLanguage();
  const [balance, setBalance] = useState(0);
  const [totalEarned, setTotalEarned] = useState(0);
  const [transactions, setTransactions] = useState<CoinTransaction[]>([]);
  const [loading, setLoading] = useState(true);
  const [claiming, setClaiming] = useState(false);
  const [page, setPage] = useState(0);
  const [hasMore, setHasMore] = useState(true);

  const load = useCallback(async (reset = false) => {
    const offset = reset ? 0 : page * 20;
    try {
      if (reset) setLoading(true);
      const [balRes, histRes] = await Promise.all([
        GamificationAPI.getCoinBalance(),
        GamificationAPI.getCoinHistory(20, offset),
      ]);
      setBalance(balRes.balance);
      setTotalEarned(balRes.total_earned);
      const newTxs = histRes.transactions;
      setTransactions(reset ? newTxs : prev => [...prev, ...newTxs]);
      setHasMore(newTxs.length === 20);
      if (!reset) setPage(p => p + 1);
    } catch {
      // silently fail — show stale data
    } finally {
      setLoading(false);
    }
  }, [page]);

  useEffect(() => { load(true); }, []);

  const claimDaily = async () => {
    setClaiming(true);
    try {
      const res = await GamificationAPI.claimDailyQuest();
      setBalance(res.balance);
      Alert.alert(t('coin.daily_quest', lang), `+${res.coins_earned} 🪙`);
      load(true);
    } catch (e: any) {
      const msg = e?.response?.data?.error || t('common.error', lang);
      Alert.alert(t('coin.daily_quest', lang), msg);
    } finally {
      setClaiming(false);
    }
  };

  const renderTx = ({ item }: { item: CoinTransaction }) => {
    const sign = item.amount >= 0 ? '+' : '';
    const color = item.amount >= 0 ? '#7AE07A' : '#E07A7A';
    const date = new Date(item.created_at).toLocaleDateString(lang === 'tr' ? 'tr-TR' : 'en-US');
    return (
      <View style={styles.txRow}>
        <View style={styles.txLeft}>
          <Text style={styles.txIcon}>{item.amount >= 0 ? '↑' : '↓'}</Text>
          <View>
            <Text style={styles.txReason}>{item.reason}</Text>
            <Text style={styles.txDate}>{date}</Text>
          </View>
        </View>
        <Text style={[styles.txAmount, { color }]}>{sign}{item.amount} 🪙</Text>
      </View>
    );
  };

  if (loading) {
    return (
      <View style={styles.center}>
        <ActivityIndicator size="large" color={colors.gold} />
      </View>
    );
  }

  return (
    <View style={styles.container}>
      <StatusBar barStyle="light-content" />
      <FlatList
        data={transactions}
        keyExtractor={item => item.transaction_id}
        renderItem={renderTx}
        onEndReached={() => hasMore && load(false)}
        onEndReachedThreshold={0.3}
        contentContainerStyle={[styles.list, { paddingTop: insets.top + spacing.md }]}
        ListHeaderComponent={() => (
          <>
            {/* Back + title */}
            <View style={styles.header}>
              <TouchableOpacity onPress={() => navigation.goBack()} style={styles.backBtn}
                accessibilityRole="button"
                accessibilityLabel={t('coin.balance', lang)}
              >
                <Text style={styles.backArrow}>←</Text>
              </TouchableOpacity>
              <Text style={styles.title}>{t('coin.balance', lang)}</Text>
            </View>

            {/* Balance card */}
            <View style={styles.balCard}>
              <Text style={styles.balLabel}>{t('coin.balance', lang)}</Text>
              <Text style={styles.balValue}>🪙 {balance.toLocaleString()}</Text>
              <Text style={styles.earnedLabel}>{t('coin.total_earned', lang)}: {totalEarned.toLocaleString()}</Text>
            </View>

            {/* Daily quest */}
            <TouchableOpacity style={styles.dailyBtn} onPress={claimDaily} disabled={claiming} activeOpacity={0.85}
              accessibilityRole="button"
              accessibilityLabel={t('coin.daily_quest', lang)}
            >
              {claiming ? (
                <ActivityIndicator size="small" color={colors.background} />
              ) : (
                <Text style={styles.dailyBtnText}>🎁 {t('coin.daily_quest', lang)}</Text>
              )}
            </TouchableOpacity>

            <Text style={styles.sectionLabel}>{t('coin.history', lang)}</Text>
          </>
        )}
        ListEmptyComponent={() => (
          <Text style={styles.empty}>{t('coin.empty', lang)}</Text>
        )}
      />
    </View>
  );
};

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: colors.background },
  center: { flex: 1, alignItems: 'center', justifyContent: 'center', backgroundColor: colors.background },
  list: { paddingHorizontal: spacing.lg, paddingBottom: 40 },
  header: { flexDirection: 'row', alignItems: 'center', marginBottom: spacing.lg },
  backBtn: { marginRight: spacing.md, padding: 4 },
  backArrow: { fontSize: 22, color: colors.textPrimary },
  title: { ...typography.h2, flex: 1 },
  balCard: {
    backgroundColor: colors.surface, borderRadius: radius.lg ?? 16,
    padding: spacing.lg, alignItems: 'center', marginBottom: spacing.md,
    borderWidth: 1, borderColor: `${colors.gold}30`, ...shadow.sm,
  },
  balLabel: { ...typography.caption, color: colors.textMuted, marginBottom: 4 },
  balValue: { fontSize: 36, fontWeight: '700', color: colors.gold, marginBottom: 4 },
  earnedLabel: { ...typography.caption, color: colors.textMuted },
  dailyBtn: {
    backgroundColor: colors.gold, borderRadius: radius.md ?? 12,
    padding: spacing.md, alignItems: 'center', marginBottom: spacing.lg,
  },
  dailyBtnText: { color: colors.background, fontWeight: '700', fontSize: 16 },
  sectionLabel: { ...typography.goldLabel, marginBottom: spacing.sm },
  txRow: {
    flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between',
    backgroundColor: colors.surface, borderRadius: radius.md ?? 12,
    padding: spacing.md, marginBottom: spacing.sm, ...shadow.sm,
  },
  txLeft: { flexDirection: 'row', alignItems: 'center', gap: spacing.sm, flex: 1 },
  txIcon: { fontSize: 20, width: 28, textAlign: 'center' as any },
  txReason: { ...typography.body, color: colors.textPrimary, fontSize: 13 },
  txDate: { ...typography.caption, color: colors.textMuted, fontSize: 11 },
  txAmount: { fontWeight: '700', fontSize: 15 },
  empty: { ...typography.body, color: colors.textMuted, textAlign: 'center' as any, marginTop: spacing.lg },
});

export default CoinWalletScreen;

// src/screens/MissionsScreen.tsx
import React, { useEffect, useState, useCallback } from 'react';
import {
  View, Text, StyleSheet, FlatList, TouchableOpacity,
  ActivityIndicator, StatusBar, Alert,
} from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { useSelector } from 'react-redux';
import { RootState } from '../store';
import { GamificationAPI, CommunityMission } from '../services/api';
import theme from '../utils/theme';
import { useLanguage } from '../utils/LanguageContext';
import { t } from '../utils/i18n';
import type { ScreenProps } from '../navigation/types';

const { colors, spacing, typography, radius, shadow } = theme;
type Props = ScreenProps<'Missions'>;

const MissionsScreen: React.FC<Props> = ({ navigation }) => {
  const insets = useSafeAreaInsets();
  const { lang } = useLanguage();
  const currentUserId = useSelector((s: RootState) => s.auth.user?.id);
  const [missions, setMissions] = useState<CommunityMission[]>([]);
  const [loading, setLoading] = useState(true);
  const [joining, setJoining] = useState<string | null>(null);
  const [contributing, setContributing] = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const res = await GamificationAPI.getActiveMissions(20);
      setMissions(res.missions);
    } catch {
      // keep stale
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { load(); }, [load]);

  const isJoined = (m: CommunityMission) =>
    m.participants?.some(p => p.user_id === currentUserId) ?? false;

  const join = async (missionId: string) => {
    setJoining(missionId);
    try {
      await GamificationAPI.joinMission(missionId);
      load();
    } catch (e: any) {
      Alert.alert(t('gamification.missions', lang), e?.response?.data?.error || t('common.error', lang));
    } finally {
      setJoining(null);
    }
  };

  const contribute = async (missionId: string) => {
    setContributing(missionId);
    try {
      const res = await GamificationAPI.contributeMission(missionId, 1);
      if (res.is_complete) {
        Alert.alert(
          t('gamification.mission_complete', lang),
          `${t('coin.earned', lang)}: +${res.coins_earned ?? 0} 🪙`
        );
      }
      load();
    } catch (e: any) {
      Alert.alert(t('gamification.missions', lang), e?.response?.data?.error || t('common.error', lang));
    } finally {
      setContributing(null);
    }
  };

  const renderMission = ({ item }: { item: CommunityMission }) => {
    const joined = isJoined(item);
    const progress = item.total_contributed ?? 0;
    const target = item.target_value ?? 1;
    const pct = Math.min(1, progress / target);
    const end = new Date(item.end_time).toLocaleDateString(lang === 'tr' ? 'tr-TR' : 'en-US');

    return (
      <View style={[styles.card, joined && styles.cardJoined]}>
        <View style={styles.cardTop}>
          <Text style={styles.missionTitle}>{item.title}</Text>
          <View style={[styles.statusBadge, item.status === 'completed' && styles.statusDone]}>
            <Text style={styles.statusText}>{item.status}</Text>
          </View>
        </View>
        {item.description ? <Text style={styles.desc}>{item.description}</Text> : null}

        {/* Progress bar */}
        <View style={styles.progressBg}>
          <View style={[styles.progressFill, { width: `${pct * 100}%` as any }]} />
        </View>
        <Text style={styles.progressLabel}>{progress}/{target} — {Math.round(pct * 100)}%</Text>
        <Text style={styles.meta}>{t('challenge.ends', lang)}: {end}</Text>
        <Text style={styles.meta}>{t('challenge.participants', lang)}: {item.participants?.length ?? 0}</Text>

        <View style={styles.cardActions}>
          {!joined ? (
            <TouchableOpacity
              style={styles.joinBtn}
              onPress={() => join(item.mission_id)}
              disabled={joining === item.mission_id}
            >
              {joining === item.mission_id ? (
                <ActivityIndicator size="small" color={colors.background} />
              ) : (
                <Text style={styles.joinText}>{t('challenge.join', lang)}</Text>
              )}
            </TouchableOpacity>
          ) : item.status === 'active' ? (
            <TouchableOpacity
              style={styles.contributeBtn}
              onPress={() => contribute(item.mission_id)}
              disabled={contributing === item.mission_id}
            >
              {contributing === item.mission_id ? (
                <ActivityIndicator size="small" color={colors.background} />
              ) : (
                <Text style={styles.joinText}>{t('gamification.contribute', lang)}</Text>
              )}
            </TouchableOpacity>
          ) : (
            <Text style={styles.doneLabel}>✓ {t('gamification.mission_complete', lang)}</Text>
          )}
        </View>
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
        <Text style={styles.title}>{t('gamification.missions', lang)}</Text>
      </View>

      {loading ? (
        <View style={styles.center}>
          <ActivityIndicator size="large" color={colors.gold} />
        </View>
      ) : (
        <FlatList
          data={missions}
          keyExtractor={item => item.mission_id}
          renderItem={renderMission}
          contentContainerStyle={styles.list}
          ListEmptyComponent={() => <Text style={styles.empty}>{t('gamification.no_missions', lang)}</Text>}
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
  center: { flex: 1, alignItems: 'center', justifyContent: 'center' },
  list: { paddingHorizontal: spacing.lg, paddingBottom: 40 },
  card: {
    backgroundColor: colors.surface, borderRadius: radius.lg ?? 16,
    padding: spacing.md, marginBottom: spacing.sm, ...shadow.sm,
  },
  cardJoined: { borderWidth: 1, borderColor: `${colors.gold}50` },
  cardTop: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: spacing.sm },
  missionTitle: { ...typography.body, color: colors.textPrimary, fontWeight: '700', flex: 1 },
  statusBadge: {
    backgroundColor: `${colors.warmAmber}30`, borderRadius: 6,
    paddingHorizontal: 8, paddingVertical: 3, marginLeft: spacing.sm,
  },
  statusDone: { backgroundColor: '#7AE07A30' },
  statusText: { fontSize: 10, fontWeight: '700', color: colors.textMuted },
  desc: { ...typography.caption, color: colors.textMuted, marginBottom: spacing.sm },
  progressBg: { height: 6, backgroundColor: `${colors.border}40`, borderRadius: 3, marginBottom: 4 },
  progressFill: { height: 6, backgroundColor: colors.gold, borderRadius: 3 },
  progressLabel: { ...typography.caption, color: colors.textMuted, fontSize: 11, marginBottom: 4 },
  meta: { ...typography.caption, color: colors.textMuted, marginBottom: 2 },
  cardActions: { flexDirection: 'row', justifyContent: 'flex-end', marginTop: spacing.sm },
  joinBtn: {
    backgroundColor: colors.gold, borderRadius: radius.sm ?? 8,
    paddingHorizontal: spacing.md, paddingVertical: 8,
  },
  contributeBtn: {
    backgroundColor: colors.warmAmber, borderRadius: radius.sm ?? 8,
    paddingHorizontal: spacing.md, paddingVertical: 8,
  },
  joinText: { color: colors.background, fontWeight: '700', fontSize: 13 },
  doneLabel: { color: '#7AE07A', fontWeight: '700', fontSize: 13 },
  empty: { ...typography.body, color: colors.textMuted, textAlign: 'center' as any, marginTop: 40 },
});

export default MissionsScreen;

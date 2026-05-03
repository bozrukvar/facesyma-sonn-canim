// src/screens/ChallengesScreen.tsx
import React, { useEffect, useState, useCallback } from 'react';
import {
  View, Text, StyleSheet, FlatList, TouchableOpacity,
  ActivityIndicator, StatusBar, Alert, Modal, TextInput,
} from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { useSelector } from 'react-redux';
import { RootState } from '../store';
import { GamificationAPI, Challenge } from '../services/api';
import theme from '../utils/theme';
import { useLanguage } from '../utils/LanguageContext';
import { t } from '../utils/i18n';
import type { ScreenProps } from '../navigation/types';

const { colors, spacing, typography, radius, shadow } = theme;
type Props = ScreenProps<'Challenges'>;

const ChallengesScreen: React.FC<Props> = ({ navigation }) => {
  const insets = useSafeAreaInsets();
  const { lang } = useLanguage();
  const currentUserId = useSelector((s: RootState) => s.auth.user?.id);
  const [challenges, setChallenges] = useState<Challenge[]>([]);
  const [loading, setLoading] = useState(true);
  const [joining, setJoining] = useState<string | null>(null);
  const [createVisible, setCreateVisible] = useState(false);
  const [newTitle, setNewTitle] = useState('');
  const [creating, setCreating] = useState(false);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const res = await GamificationAPI.getActiveChallenges(30);
      setChallenges(res.challenges);
    } catch {
      // keep stale
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { load(); }, [load]);

  const join = async (challengeId: string) => {
    setJoining(challengeId);
    try {
      await GamificationAPI.joinChallenge(challengeId);
      load();
    } catch (e: any) {
      Alert.alert(t('challenge.title', lang), e?.response?.data?.error || t('common.error', lang));
    } finally {
      setJoining(null);
    }
  };

  const abandon = async (challengeId: string) => {
    Alert.alert(
      t('challenge.abandon', lang),
      t('challenge.abandon_confirm', lang),
      [
        { text: t('common.cancel', lang), style: 'cancel' },
        {
          text: t('challenge.abandon', lang), style: 'destructive',
          onPress: async () => {
            try {
              const res = await GamificationAPI.abandonChallenge(challengeId);
              if (res.penalty > 0) Alert.alert(t('challenge.abandon', lang), `-${res.penalty} 🪙`);
              load();
            } catch {}
          },
        },
      ]
    );
  };

  const createChallenge = async () => {
    if (!newTitle.trim()) return;
    setCreating(true);
    try {
      await GamificationAPI.createChallenge({ title: newTitle.trim() });
      setCreateVisible(false);
      setNewTitle('');
      load();
    } catch (e: any) {
      Alert.alert(t('challenge.create', lang), e?.response?.data?.error || t('common.error', lang));
    } finally {
      setCreating(false);
    }
  };

  const isParticipant = (c: Challenge) =>
    c.participants?.some(p => p.user_id === currentUserId) ?? false;

  const renderChallenge = ({ item }: { item: Challenge }) => {
    const isMine = isParticipant(item);
    const end = new Date(item.end_time).toLocaleDateString(lang === 'tr' ? 'tr-TR' : 'en-US');
    return (
      <View style={[styles.card, isMine && styles.cardJoined]}>
        <View style={styles.cardTop}>
          <Text style={styles.challengeTitle}>{item.title}</Text>
          <Text style={styles.reward}>🪙 {item.coin_reward}</Text>
        </View>
        <Text style={styles.meta}>{t('challenge.participants', lang)}: {item.participants?.length ?? 0}/{item.max_participants}</Text>
        <Text style={styles.meta}>{t('challenge.ends', lang)}: {end}</Text>
        <View style={styles.cardActions}>
          {isMine ? (
            <TouchableOpacity style={styles.abandonBtn} onPress={() => abandon(item.challenge_id)}>
              <Text style={styles.abandonText}>{t('challenge.abandon', lang)}</Text>
            </TouchableOpacity>
          ) : (
            <TouchableOpacity
              style={styles.joinBtn}
              onPress={() => join(item.challenge_id)}
              disabled={joining === item.challenge_id}
            >
              {joining === item.challenge_id ? (
                <ActivityIndicator size="small" color={colors.background} />
              ) : (
                <Text style={styles.joinText}>{t('challenge.join', lang)}</Text>
              )}
            </TouchableOpacity>
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
        <Text style={styles.title}>{t('challenge.title', lang)}</Text>
        <TouchableOpacity style={styles.createFab} onPress={() => setCreateVisible(true)}>
          <Text style={styles.createFabText}>+</Text>
        </TouchableOpacity>
      </View>

      {loading ? (
        <View style={styles.center}>
          <ActivityIndicator size="large" color={colors.gold} />
        </View>
      ) : (
        <FlatList
          data={challenges}
          keyExtractor={item => item.challenge_id}
          renderItem={renderChallenge}
          contentContainerStyle={styles.list}
          ListEmptyComponent={() => <Text style={styles.empty}>{t('challenge.empty', lang)}</Text>}
        />
      )}

      {/* Create modal */}
      <Modal visible={createVisible} transparent animationType="slide" onRequestClose={() => setCreateVisible(false)}>
        <View style={styles.modalOverlay}>
          <View style={styles.modal}>
            <Text style={styles.modalTitle}>{t('challenge.create', lang)}</Text>
            <TextInput
              style={styles.input}
              placeholder={t('challenge.title', lang)}
              placeholderTextColor={colors.textMuted}
              value={newTitle}
              onChangeText={setNewTitle}
            />
            <View style={styles.modalActions}>
              <TouchableOpacity style={styles.cancelBtn} onPress={() => setCreateVisible(false)}>
                <Text style={styles.cancelText}>{t('common.cancel', lang)}</Text>
              </TouchableOpacity>
              <TouchableOpacity style={styles.confirmBtn} onPress={createChallenge} disabled={creating}>
                {creating ? <ActivityIndicator size="small" color={colors.background} /> : (
                  <Text style={styles.confirmText}>{t('challenge.create', lang)}</Text>
                )}
              </TouchableOpacity>
            </View>
          </View>
        </View>
      </Modal>
    </View>
  );
};

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: colors.background },
  topBar: { flexDirection: 'row', alignItems: 'center', paddingHorizontal: spacing.lg, paddingBottom: spacing.md },
  backBtn: { marginRight: spacing.md, padding: 4 },
  backArrow: { fontSize: 22, color: colors.textPrimary },
  title: { ...typography.h2, flex: 1 },
  createFab: {
    backgroundColor: colors.gold, width: 36, height: 36, borderRadius: 18,
    alignItems: 'center', justifyContent: 'center',
  },
  createFabText: { fontSize: 24, fontWeight: '700', color: colors.background, lineHeight: 28 },
  center: { flex: 1, alignItems: 'center', justifyContent: 'center' },
  list: { paddingHorizontal: spacing.lg, paddingBottom: 40 },
  card: {
    backgroundColor: colors.surface, borderRadius: radius.lg ?? 16,
    padding: spacing.md, marginBottom: spacing.sm, ...shadow.sm,
  },
  cardJoined: { borderWidth: 1, borderColor: `${colors.gold}50` },
  cardTop: { flexDirection: 'row', justifyContent: 'space-between', marginBottom: spacing.sm },
  challengeTitle: { ...typography.body, color: colors.textPrimary, fontWeight: '700', flex: 1 },
  reward: { ...typography.body, color: colors.gold, fontWeight: '700' },
  meta: { ...typography.caption, color: colors.textMuted, marginBottom: 2 },
  cardActions: { flexDirection: 'row', justifyContent: 'flex-end', marginTop: spacing.sm },
  joinBtn: {
    backgroundColor: colors.gold, borderRadius: radius.sm ?? 8,
    paddingHorizontal: spacing.md, paddingVertical: 8,
  },
  joinText: { color: colors.background, fontWeight: '700', fontSize: 13 },
  abandonBtn: {
    backgroundColor: 'transparent', borderRadius: radius.sm ?? 8,
    paddingHorizontal: spacing.md, paddingVertical: 8,
    borderWidth: 1, borderColor: '#E07A7A',
  },
  abandonText: { color: '#E07A7A', fontWeight: '700', fontSize: 13 },
  empty: { ...typography.body, color: colors.textMuted, textAlign: 'center' as any, marginTop: 40 },
  modalOverlay: { flex: 1, backgroundColor: '#000000AA', justifyContent: 'flex-end' },
  modal: {
    backgroundColor: colors.surface, borderTopLeftRadius: 24, borderTopRightRadius: 24,
    padding: spacing.lg, paddingBottom: 40,
  },
  modalTitle: { ...typography.h3 ?? typography.h2, marginBottom: spacing.md },
  input: {
    backgroundColor: colors.background, borderRadius: radius.md ?? 12,
    padding: spacing.md, color: colors.textPrimary, marginBottom: spacing.md,
    borderWidth: 1, borderColor: colors.border,
  },
  modalActions: { flexDirection: 'row', gap: spacing.sm },
  cancelBtn: {
    flex: 1, padding: spacing.md, borderRadius: radius.md ?? 12,
    borderWidth: 1, borderColor: colors.border, alignItems: 'center',
  },
  cancelText: { color: colors.textMuted, fontWeight: '600' },
  confirmBtn: {
    flex: 1, padding: spacing.md, borderRadius: radius.md ?? 12,
    backgroundColor: colors.gold, alignItems: 'center',
  },
  confirmText: { color: colors.background, fontWeight: '700' },
});

export default ChallengesScreen;

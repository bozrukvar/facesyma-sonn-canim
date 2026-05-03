// src/screens/PeerChatRequestScreen.tsx
import React, { useState, useEffect, useCallback } from 'react';
import {
  View, Text, StyleSheet, FlatList, TouchableOpacity,
  ActivityIndicator, Alert, RefreshControl,
} from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { useSelector } from 'react-redux';
import type { RootState } from '../store';
import theme from '../utils/theme';
const { colors, spacing, typography, radius, shadow } = theme;
import { useLanguage } from '../utils/LanguageContext';
import { t } from '../utils/i18n';
import { PeerChatAPI, PeerChatRequest } from '../services/api';
import type { ScreenProps } from '../navigation/types';

const PeerChatRequestScreen: React.FC<ScreenProps<'PeerChatRequest'>> = ({ navigation, route }) => {
  const insets = useSafeAreaInsets();
  const { lang } = useLanguage();
  const user = useSelector((s: RootState) => s.auth.user);

  const { toUserId, toUsername, compatScore } = route.params ?? {};

  const [requests, setRequests] = useState<PeerChatRequest[]>([]);
  const [loading, setLoading]   = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [responding, setResponding] = useState<string | null>(null);
  const [sending, setSending]   = useState(false);

  // 18+ yaş kontrolü
  const birthYear = user?.birth_year as number | undefined;
  const isAdult = !birthYear || (new Date().getFullYear() - birthYear >= 18);

  const loadRequests = useCallback(async (isRefresh = false) => {
    if (isRefresh) setRefreshing(true); else setLoading(true);
    try {
      const res = await PeerChatAPI.getPendingRequests();
      setRequests(res.data ?? []);
    } catch {
      if (!isRefresh) Alert.alert(t('common.error', lang), t('common.generic_error', lang));
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, [lang]);

  useEffect(() => {
    loadRequests();
    // If navigated to send a request, do it automatically
    if (toUserId) {
      sendRequest();
    }
  }, []);

  const sendRequest = async () => {
    if (!toUserId || sending) return;
    if (!isAdult) {
      Alert.alert(t('peer_chat.age_restricted', lang), t('peer_chat.age_restricted_desc', lang));
      return;
    }
    setSending(true);
    try {
      const res = await PeerChatAPI.sendRequest(toUserId, compatScore);
      if (res.room_id) {
        // Already a room — go straight to chat
        navigation.replace('PeerChat', {
          roomId: res.room_id,
          otherUserId: toUserId,
          otherUsername: toUsername ?? `user_${toUserId}`,
        });
      } else {
        Alert.alert('', t('peer_chat.request_sent', lang));
        navigation.goBack();
      }
    } catch (e: any) {
      const code = e?.response?.data?.detail ?? e?.response?.data?.code;
      if (code === 'age_restricted') {
        Alert.alert(t('peer_chat.age_restricted', lang), t('peer_chat.age_restricted_desc', lang));
      } else if (code === 'chat_locked') {
        Alert.alert(t('common.error', lang), e?.response?.data?.detail ?? t('common.generic_error', lang));
      } else {
        Alert.alert(t('common.error', lang), t('common.generic_error', lang));
      }
    } finally {
      setSending(false);
    }
  };

  const respond = async (requestId: string, action: 'accept' | 'reject') => {
    setResponding(requestId);
    try {
      const res = await PeerChatAPI.respondRequest(requestId, action);
      if (action === 'accept' && res.room_id) {
        const req = requests.find(r => String(r._id) === requestId);
        navigation.replace('PeerChat', {
          roomId: res.room_id,
          otherUserId: req?.from_user_id ?? 0,
          otherUsername: (req as any)?.from_username ?? 'User',
        });
      } else {
        setRequests(prev => prev.filter(r => String(r._id) !== requestId));
      }
    } catch {
      Alert.alert(t('common.error', lang), t('common.generic_error', lang));
    } finally {
      setResponding(null);
    }
  };

  const renderItem = ({ item }: { item: PeerChatRequest }) => {
    const rid = String(item._id);
    const isResponding = responding === rid;
    return (
      <View style={styles.card}>
        <View style={styles.cardHeader}>
          <View style={styles.avatar}>
            <Text style={styles.avatarTxt}>
              {((item as any).from_username?.[0] ?? '?').toUpperCase()}
            </Text>
          </View>
          <View style={styles.cardInfo}>
            <Text style={styles.username}>{(item as any).from_username ?? `User #${item.from_user_id}`}</Text>
            {item.compatibility_score > 0 && (
              <Text style={styles.compat}>⭐ {Math.round(item.compatibility_score)}% {t('community.compatibility', lang)}</Text>
            )}
          </View>
        </View>
        <View style={styles.btnRow}>
          <TouchableOpacity
            style={[styles.acceptBtn, isResponding && styles.btnDisabled]}
            onPress={() => respond(rid, 'accept')}
            disabled={isResponding}
            activeOpacity={0.85}
          >
            {isResponding ? <ActivityIndicator color="#000" size="small" /> : <Text style={styles.acceptTxt}>{t('peer_chat.accept', lang)}</Text>}
          </TouchableOpacity>
          <TouchableOpacity
            style={[styles.rejectBtn, isResponding && styles.btnDisabled]}
            onPress={() => respond(rid, 'reject')}
            disabled={isResponding}
            activeOpacity={0.85}
          >
            <Text style={styles.rejectTxt}>{t('peer_chat.reject', lang)}</Text>
          </TouchableOpacity>
        </View>
      </View>
    );
  };

  // If sending a new request (toUserId specified), show sending state
  if (toUserId) {
    return (
      <View style={[styles.container, { paddingTop: insets.top }]}>
        <View style={styles.header}>
          <TouchableOpacity onPress={() => navigation.goBack()} style={styles.backBtn}>
            <Text style={styles.backTxt}>←</Text>
          </TouchableOpacity>
          <Text style={styles.title}>{t('peer_chat.send_request', lang)}</Text>
          <View style={{ width: 36 }} />
        </View>
        <View style={styles.center}>
          {!isAdult ? (
            <>
              <Text style={styles.lockIcon}>🔞</Text>
              <Text style={styles.lockTitle}>{t('peer_chat.age_restricted', lang)}</Text>
              <Text style={styles.lockDesc}>{t('peer_chat.age_restricted_desc', lang)}</Text>
            </>
          ) : sending ? (
            <>
              <ActivityIndicator color={colors.gold} size="large" />
              <Text style={styles.sendingTxt}>{t('peer_chat.send_request', lang)}…</Text>
            </>
          ) : (
            <>
              <Text style={styles.lockIcon}>🤝</Text>
              <Text style={styles.toUsername}>{toUsername}</Text>
              <TouchableOpacity style={styles.sendBtn} onPress={sendRequest} activeOpacity={0.85}>
                <Text style={styles.sendBtnTxt}>{t('peer_chat.send_request', lang)}</Text>
              </TouchableOpacity>
            </>
          )}
        </View>
      </View>
    );
  }

  return (
    <View style={[styles.container, { paddingTop: insets.top }]}>
      <View style={styles.header}>
        <TouchableOpacity onPress={() => navigation.goBack()} style={styles.backBtn}>
          <Text style={styles.backTxt}>←</Text>
        </TouchableOpacity>
        <Text style={styles.title}>{t('peer_chat.pending_requests', lang)}</Text>
        <View style={{ width: 36 }} />
      </View>

      {loading ? (
        <View style={styles.center}><ActivityIndicator color={colors.gold} size="large" /></View>
      ) : (
        <FlatList
          data={requests}
          keyExtractor={item => String(item._id)}
          renderItem={renderItem}
          contentContainerStyle={styles.list}
          refreshControl={
            <RefreshControl refreshing={refreshing} onRefresh={() => loadRequests(true)} tintColor={colors.gold} />
          }
          ListEmptyComponent={
            <View style={styles.center}>
              <Text style={styles.emptyTxt}>🤝</Text>
              <Text style={styles.emptyLabel}>{t('peer_chat.no_requests', lang)}</Text>
            </View>
          }
        />
      )}
    </View>
  );
};

const styles = StyleSheet.create({
  container:   { flex: 1, backgroundColor: colors.background },
  header: {
    flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between',
    paddingHorizontal: spacing.lg, paddingVertical: spacing.md,
    borderBottomWidth: 1, borderColor: colors.border,
  },
  backBtn:     { width: 36, height: 36, justifyContent: 'center' },
  backTxt:     { ...typography.h2, color: colors.gold },
  title:       { ...typography.h2, color: colors.textPrimary },
  center:      { flex: 1, alignItems: 'center', justifyContent: 'center', padding: spacing.xl, gap: spacing.md },
  list:        { padding: spacing.lg, gap: spacing.md },
  emptyTxt:    { fontSize: 48 },
  emptyLabel:  { ...typography.body, color: colors.textMuted },
  lockIcon:    { fontSize: 56 },
  lockTitle:   { ...typography.h2, color: colors.textPrimary },
  lockDesc:    { ...typography.body, color: colors.textMuted, textAlign: 'center' },
  toUsername:  { ...typography.h2, color: colors.textPrimary },
  sendingTxt:  { ...typography.body, color: colors.textMuted, marginTop: spacing.md },
  sendBtn:     { height: 50, paddingHorizontal: spacing.xl, backgroundColor: colors.gold, borderRadius: radius.lg, alignItems: 'center', justifyContent: 'center', ...shadow.gold },
  sendBtnTxt:  { ...typography.label, color: '#000', fontSize: 14 },
  card:        { backgroundColor: colors.surface, borderRadius: radius.lg, borderWidth: 1, borderColor: colors.border, padding: spacing.lg, gap: spacing.md },
  cardHeader:  { flexDirection: 'row', alignItems: 'center', gap: spacing.md },
  avatar:      { width: 44, height: 44, borderRadius: 22, backgroundColor: colors.goldDark, alignItems: 'center', justifyContent: 'center' },
  avatarTxt:   { color: '#fff', fontWeight: '700', fontSize: 16 },
  cardInfo:    { flex: 1, gap: 4 },
  username:    { ...typography.h3, color: colors.textPrimary },
  compat:      { ...typography.caption, color: colors.gold },
  btnRow:      { flexDirection: 'row', gap: spacing.sm },
  acceptBtn:   { flex: 1, height: 42, backgroundColor: colors.gold, borderRadius: radius.md, alignItems: 'center', justifyContent: 'center', ...shadow.gold },
  rejectBtn:   { flex: 1, height: 42, backgroundColor: colors.surface, borderRadius: radius.md, borderWidth: 1, borderColor: colors.border, alignItems: 'center', justifyContent: 'center' },
  btnDisabled: { opacity: 0.5 },
  acceptTxt:   { ...typography.label, color: '#000', fontSize: 13 },
  rejectTxt:   { ...typography.label, color: colors.textMuted, fontSize: 13 },
});

export default PeerChatRequestScreen;

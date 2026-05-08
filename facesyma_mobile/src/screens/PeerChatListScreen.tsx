// src/screens/PeerChatListScreen.tsx
import React, { useState, useCallback, useEffect } from 'react';
import {
  View, Text, StyleSheet, FlatList, TouchableOpacity,
  ActivityIndicator, Alert, RefreshControl,
} from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import theme from '../utils/theme';
const { colors, spacing, typography, radius } = theme;
import { useLanguage } from '../utils/LanguageContext';
import { t } from '../utils/i18n';
import { PeerChatAPI, PeerChatRoom } from '../services/api';
import type { ScreenProps } from '../navigation/types';

const PeerChatListScreen: React.FC<ScreenProps<'PeerChatList'>> = ({ navigation }) => {
  const insets   = useSafeAreaInsets();
  const { lang } = useLanguage();

  const [rooms,      setRooms]      = useState<PeerChatRoom[]>([]);
  const [pendingCnt, setPendingCnt] = useState(0);
  const [loading,    setLoading]    = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  const load = useCallback(async (isRefresh = false) => {
    if (isRefresh) setRefreshing(true); else setLoading(true);
    try {
      const [roomsRes, pendingRes] = await Promise.all([
        PeerChatAPI.getRooms(),
        PeerChatAPI.getPendingRequests(),
      ]);
      setRooms(roomsRes.data ?? []);
      setPendingCnt(pendingRes.count ?? 0);
    } catch {
      if (!isRefresh) Alert.alert(t('common.error', lang), t('common.generic_error', lang));
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, [lang]);

  useEffect(() => { load(); }, [load]);

  const renderItem = ({ item }: { item: PeerChatRoom }) => {
    const other = item.other_user;
    const hasUnread = item.my_unread > 0;
    const lastTime = item.last_message_at
      ? new Date(item.last_message_at * 1000).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
      : '';
    return (
      <TouchableOpacity
        accessibilityRole="button"
        accessibilityLabel="(other.username?.[0] ?? '?').toUpperCase()"
        style={styles.roomCard}
        activeOpacity={0.85}
        onPress={() => navigation.navigate('PeerChat', {
          roomId: item._id,
          otherUserId: other.id,
          otherUsername: other.username,
        })}
      >
        <View style={styles.roomAvatar}>
          <Text style={styles.roomAvatarTxt}>{(other.username?.[0] ?? '?').toUpperCase()}</Text>
        </View>
        <View style={styles.roomInfo}>
          <View style={styles.roomRow}>
            <Text style={styles.roomUsername}>{other.username}</Text>
            {lastTime ? <Text style={styles.roomTime}>{lastTime}</Text> : null}
          </View>
          <View style={styles.roomRow}>
            <Text style={styles.roomPreview} numberOfLines={1}>
              {item.last_message_preview || '…'}
            </Text>
            {hasUnread ? (
              <View style={styles.unreadBadge}>
                <Text style={styles.unreadTxt}>{item.my_unread}</Text>
              </View>
            ) : null}
          </View>
        </View>
      </TouchableOpacity>
    );
  };

  return (
    <View style={[styles.container, { paddingTop: insets.top }]}>
      <View style={styles.header}>
        <TouchableOpacity onPress={() => navigation.goBack()} style={styles.backBtn}
          accessibilityRole="button"
          accessibilityLabel={t('peer_chat.title', lang)}
        >
          <Text style={styles.backTxt}>←</Text>
        </TouchableOpacity>
        <Text style={styles.title}>{t('peer_chat.title', lang)}</Text>
        <TouchableOpacity
          accessibilityRole="button"
          accessibilityLabel={pendingCnt}
          style={styles.requestBtn}
          onPress={() => navigation.navigate('PeerChatRequest', {})}
        >
          <Text style={styles.requestTxt}>📨</Text>
          {pendingCnt > 0 && (
            <View style={styles.requestBadge}>
              <Text style={styles.requestBadgeTxt}>{pendingCnt}</Text>
            </View>
          )}
        </TouchableOpacity>
      </View>

      {loading ? (
        <View style={styles.center}><ActivityIndicator color={colors.gold} size="large" /></View>
      ) : (
        <FlatList
          data={rooms}
          keyExtractor={item => item._id}
          renderItem={renderItem}
          contentContainerStyle={styles.list}
          refreshControl={
            <RefreshControl refreshing={refreshing} onRefresh={() => load(true)} tintColor={colors.gold} />
          }
          ListEmptyComponent={
            <View style={styles.center}>
              <Text style={styles.emptyIcon}>💬</Text>
              <Text style={styles.emptyTxt}>{t('peer_chat.no_requests', lang)}</Text>
            </View>
          }
        />
      )}
    </View>
  );
};

const styles = StyleSheet.create({
  container:  { flex: 1, backgroundColor: colors.background },
  header: {
    flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between',
    paddingHorizontal: spacing.lg, paddingVertical: spacing.md,
    borderBottomWidth: 1, borderColor: colors.border,
  },
  backBtn:       { width: 36, height: 36, justifyContent: 'center' },
  backTxt:       { ...typography.h2, color: colors.gold },
  title:         { ...typography.h2, color: colors.textPrimary },
  requestBtn:    { width: 36, height: 36, justifyContent: 'center', alignItems: 'center' },
  requestTxt:    { fontSize: 20 },
  requestBadge:  {
    position: 'absolute', top: 0, right: 0,
    width: 16, height: 16, borderRadius: 8,
    backgroundColor: colors.gold, alignItems: 'center', justifyContent: 'center',
  },
  requestBadgeTxt: { color: '#000', fontSize: 9, fontWeight: '700' as const },
  list:          { padding: spacing.lg, gap: spacing.sm },
  center:        { flex: 1, alignItems: 'center', justifyContent: 'center', padding: spacing.xl },
  emptyIcon:     { fontSize: 48, marginBottom: spacing.md },
  emptyTxt:      { ...typography.body, color: colors.textMuted },
  roomCard: {
    flexDirection: 'row', alignItems: 'center', gap: spacing.md,
    backgroundColor: colors.surface, borderRadius: radius.lg,
    borderWidth: 1, borderColor: colors.border,
    padding: spacing.md,
  },
  roomAvatar: {
    width: 46, height: 46, borderRadius: 23,
    backgroundColor: colors.goldDark, alignItems: 'center', justifyContent: 'center',
  },
  roomAvatarTxt: { color: '#fff', fontWeight: '700' as const, fontSize: 16 },
  roomInfo:      { flex: 1, gap: 4 },
  roomRow:       { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between' },
  roomUsername:  { ...typography.label, fontSize: 14, color: colors.textPrimary },
  roomTime:      { ...typography.caption, fontSize: 11, color: colors.textMuted },
  roomPreview:   { ...typography.caption, fontSize: 12, color: colors.textMuted, flex: 1 },
  unreadBadge:   {
    minWidth: 18, height: 18, borderRadius: 9,
    backgroundColor: colors.gold, alignItems: 'center', justifyContent: 'center',
    paddingHorizontal: 4,
  },
  unreadTxt:     { color: '#000', fontSize: 10, fontWeight: '700' as const },
});

export default PeerChatListScreen;

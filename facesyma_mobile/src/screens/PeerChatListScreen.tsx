// src/screens/PeerChatListScreen.tsx
import React, { useCallback, useEffect, useState } from 'react';
import {
  View, Text, FlatList, TouchableOpacity,
  StyleSheet, SafeAreaView, ActivityIndicator, RefreshControl, Alert,
} from 'react-native';
import { useNavigation } from '@react-navigation/native';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { PeerChatAPI, type PeerChatRoom, type PeerChatRequest } from '../services/api';
import type { AppNavProp } from '../navigation/types';
import theme from '../utils/theme';

const { colors, spacing, typography, radius } = theme;

const formatTime = (ts: number | null): string => {
  if (!ts) return '';
  const d = new Date(ts * 1000);
  const now = new Date();
  if (d.toDateString() === now.toDateString()) {
    return d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  }
  return d.toLocaleDateString([], { day: '2-digit', month: '2-digit' });
};

export default function PeerChatListScreen() {
  const nav = useNavigation<AppNavProp>();
  const [rooms, setRooms] = useState<PeerChatRoom[]>([]);
  const [pending, setPending] = useState<PeerChatRequest[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [locked, setLocked] = useState(false);
  const [lockMsg, setLockMsg] = useState('');
  const [tab, setTab] = useState<'chats' | 'requests'>('chats');

  const load = useCallback(async () => {
    try {
      const [roomsRes, pendingRes] = await Promise.all([
        PeerChatAPI.getRooms(),
        PeerChatAPI.getPendingRequests(),
      ]);
      setRooms(roomsRes.data ?? []);
      setPending(pendingRes.data ?? []);
      setLocked(false);
    } catch (err: any) {
      if (err?.response?.status === 403 && err?.response?.data?.code === 'chat_locked') {
        setLocked(true);
        setLockMsg(err.response.data.detail ?? 'Chat kilitli.');
      }
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, []);

  useEffect(() => { load(); }, [load]);

  const onRefresh = () => { setRefreshing(true); load(); };

  const openRoom = (room: PeerChatRoom) => {
    nav.navigate('PeerChat', {
      roomId: room.room_id,
      otherUserId: room.other_user.id,
      otherUsername: room.other_user.username,
      compatScore: room.compatibility_score,
    });
  };

  const openRequest = (req: PeerChatRequest) => {
    nav.navigate('PeerChatRequest', {
      requestId: req._id,
      toUserId: req.from_user_id,
      toUsername: req.from_username,
      compatScore: req.compatibility_score,
      source: req.source,
    });
  };

  if (loading) {
    return (
      <SafeAreaView style={s.safe}>
        <ActivityIndicator color={colors.gold} style={{ flex: 1 }} />
      </SafeAreaView>
    );
  }

  if (locked) {
    return (
      <SafeAreaView style={s.safe}>
        <View style={s.header}>
          <TouchableOpacity onPress={() => nav.goBack()} style={s.backBtn}>
            <Text style={s.backTxt}>←</Text>
          </TouchableOpacity>
          <Text style={s.title}>Sohbetler</Text>
        </View>
        <View style={s.lockedBox}>
          <Text style={s.lockIcon}>🔒</Text>
          <Text style={s.lockTitle}>Sohbet Kilitli</Text>
          <Text style={s.lockDesc}>{lockMsg}</Text>
          <TouchableOpacity style={s.exploreBtn} onPress={() => nav.goBack()}>
            <Text style={s.exploreBtnTxt}>Modülleri Keşfet</Text>
          </TouchableOpacity>
        </View>
      </SafeAreaView>
    );
  }

  const renderRoom = ({ item }: { item: PeerChatRoom }) => (
    <TouchableOpacity style={s.roomCard} onPress={() => openRoom(item)} activeOpacity={0.75}>
      <View style={s.avatar}>
        <Text style={s.avatarTxt}>{(item.other_user.username?.[0] ?? '?').toUpperCase()}</Text>
      </View>
      <View style={s.roomInfo}>
        <View style={s.roomRow}>
          <Text style={s.roomName}>{item.other_user.username}</Text>
          <Text style={s.roomTime}>{formatTime(item.last_message_at)}</Text>
        </View>
        <View style={s.roomRow}>
          <Text style={s.roomPreview} numberOfLines={1}>
            {item.last_message_preview || 'Sohbet başladı'}
          </Text>
          {item.my_unread > 0 && (
            <View style={s.badge}>
              <Text style={s.badgeTxt}>{item.my_unread > 9 ? '9+' : item.my_unread}</Text>
            </View>
          )}
        </View>
        {item.compatibility_score > 0 && (
          <Text style={s.compatTxt}>Uyum: %{Math.round(item.compatibility_score)}</Text>
        )}
      </View>
    </TouchableOpacity>
  );

  const renderRequest = ({ item }: { item: PeerChatRequest }) => (
    <TouchableOpacity style={s.requestCard} onPress={() => openRequest(item)} activeOpacity={0.75}>
      <View style={[s.avatar, s.avatarRequest]}>
        <Text style={s.avatarTxt}>{(item.from_username?.[0] ?? '?').toUpperCase()}</Text>
      </View>
      <View style={s.roomInfo}>
        <Text style={s.roomName}>{item.from_username}</Text>
        <Text style={s.requestDesc}>Seninle sohbet etmek istiyor</Text>
        {item.compatibility_score > 0 && (
          <Text style={s.compatTxt}>Uyum: %{Math.round(item.compatibility_score)}</Text>
        )}
        <Text style={s.sourceTag}>
          {item.source === 'community' ? '👥 Ortak Topluluk' : '🔗 Uyumluluk Analizi'}
        </Text>
      </View>
      <View style={s.pendingBadge}>
        <Text style={s.pendingTxt}>Bekliyor</Text>
      </View>
    </TouchableOpacity>
  );

  return (
    <SafeAreaView style={s.safe}>
      <View style={s.header}>
        <TouchableOpacity onPress={() => nav.goBack()} style={s.backBtn}>
          <Text style={s.backTxt}>←</Text>
        </TouchableOpacity>
        <Text style={s.title}>Sohbetler</Text>
        <TouchableOpacity
          style={s.findBtn}
          onPress={() => nav.navigate('Communities')}
        >
          <Text style={s.findBtnTxt}>+ Kişi Bul</Text>
        </TouchableOpacity>
      </View>

      {/* Tabs */}
      <View style={s.tabRow}>
        <TouchableOpacity
          style={[s.tabBtn, tab === 'chats' && s.tabBtnActive]}
          onPress={() => setTab('chats')}
        >
          <Text style={[s.tabTxt, tab === 'chats' && s.tabTxtActive]}>
            Sohbetler {rooms.length > 0 ? `(${rooms.length})` : ''}
          </Text>
        </TouchableOpacity>
        <TouchableOpacity
          style={[s.tabBtn, tab === 'requests' && s.tabBtnActive]}
          onPress={() => setTab('requests')}
        >
          <Text style={[s.tabTxt, tab === 'requests' && s.tabTxtActive]}>
            İstekler {pending.length > 0 ? `(${pending.length})` : ''}
          </Text>
          {pending.length > 0 && <View style={s.dotBadge} />}
        </TouchableOpacity>
      </View>

      {tab === 'chats' ? (
        <FlatList
          data={rooms}
          keyExtractor={i => i._id}
          renderItem={renderRoom}
          refreshControl={<RefreshControl refreshing={refreshing} onRefresh={onRefresh} tintColor={colors.gold} />}
          ListEmptyComponent={
            <View style={s.empty}>
              <Text style={s.emptyIcon}>💬</Text>
              <Text style={s.emptyTitle}>Henüz sohbet yok</Text>
              <Text style={s.emptyDesc}>
                Uyumlu kişilerle veya topluluklardan arkadaş bulup sohbet başlatabilirsin.
              </Text>
              <TouchableOpacity style={s.exploreBtn} onPress={() => nav.navigate('Communities')}>
                <Text style={s.exploreBtnTxt}>Toplulukları Keşfet</Text>
              </TouchableOpacity>
            </View>
          }
          contentContainerStyle={rooms.length === 0 ? { flex: 1 } : { paddingBottom: spacing.xl }}
        />
      ) : (
        <FlatList
          data={pending}
          keyExtractor={i => i._id}
          renderItem={renderRequest}
          refreshControl={<RefreshControl refreshing={refreshing} onRefresh={onRefresh} tintColor={colors.gold} />}
          ListEmptyComponent={
            <View style={s.empty}>
              <Text style={s.emptyIcon}>📬</Text>
              <Text style={s.emptyTitle}>Bekleyen istek yok</Text>
              <Text style={s.emptyDesc}>Sana sohbet isteği gönderildiğinde burada görünür.</Text>
            </View>
          }
          contentContainerStyle={pending.length === 0 ? { flex: 1 } : { paddingBottom: spacing.xl }}
        />
      )}
    </SafeAreaView>
  );
}

const s = StyleSheet.create({
  safe:            { flex: 1, backgroundColor: colors.background },
  header:          { flexDirection: 'row', alignItems: 'center', paddingHorizontal: spacing.md, paddingVertical: spacing.sm, borderBottomWidth: 1, borderBottomColor: colors.border },
  backBtn:         { padding: spacing.sm, marginRight: spacing.sm },
  backTxt:         { fontSize: 22, color: colors.gold },
  title:           { ...typography.h2, flex: 1 },
  findBtn:         { backgroundColor: colors.goldGlow, borderRadius: radius.sm, paddingHorizontal: spacing.md, paddingVertical: 6, borderWidth: 1, borderColor: colors.gold },
  findBtnTxt:      { ...typography.label, fontSize: 12, color: colors.gold },
  tabRow:          { flexDirection: 'row', borderBottomWidth: 1, borderBottomColor: colors.border },
  tabBtn:          { flex: 1, paddingVertical: spacing.sm + 2, alignItems: 'center', flexDirection: 'row', justifyContent: 'center', gap: 6 },
  tabBtnActive:    { borderBottomWidth: 2, borderBottomColor: colors.gold },
  tabTxt:          { ...typography.body, color: colors.textMuted, fontSize: 14 },
  tabTxtActive:    { color: colors.gold, fontWeight: '600' },
  dotBadge:        { width: 8, height: 8, borderRadius: 4, backgroundColor: colors.error },
  roomCard:        { flexDirection: 'row', alignItems: 'center', paddingHorizontal: spacing.md, paddingVertical: spacing.md, borderBottomWidth: 1, borderBottomColor: colors.border },
  requestCard:     { flexDirection: 'row', alignItems: 'center', paddingHorizontal: spacing.md, paddingVertical: spacing.md, borderBottomWidth: 1, borderBottomColor: colors.border, backgroundColor: colors.surfaceWarm },
  avatar:          { width: 48, height: 48, borderRadius: 24, backgroundColor: colors.goldDark, alignItems: 'center', justifyContent: 'center', marginRight: spacing.md },
  avatarRequest:   { backgroundColor: colors.warmAmber },
  avatarTxt:       { color: colors.white, fontWeight: '700', fontSize: 18 },
  roomInfo:        { flex: 1 },
  roomRow:         { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', marginBottom: 2 },
  roomName:        { ...typography.h3, fontSize: 15 },
  roomTime:        { ...typography.caption, fontSize: 11 },
  roomPreview:     { ...typography.caption, flex: 1, fontSize: 13, color: colors.textSecondary },
  badge:           { backgroundColor: colors.gold, borderRadius: radius.full, width: 20, height: 20, alignItems: 'center', justifyContent: 'center', marginLeft: spacing.sm },
  badgeTxt:        { color: colors.black, fontSize: 10, fontWeight: '700' },
  compatTxt:       { ...typography.caption, color: colors.gold, marginTop: 2 },
  requestDesc:     { ...typography.caption, color: colors.textSecondary, fontSize: 13 },
  sourceTag:       { ...typography.caption, color: colors.warmAmber, marginTop: 2, fontSize: 11 },
  pendingBadge:    { backgroundColor: colors.warmAmberGlow, borderRadius: radius.sm, paddingHorizontal: spacing.sm, paddingVertical: 3, borderWidth: 1, borderColor: colors.warmAmber },
  pendingTxt:      { color: colors.warmAmber, fontSize: 11, fontWeight: '600' },
  empty:           { flex: 1, alignItems: 'center', justifyContent: 'center', padding: spacing.xl },
  emptyIcon:       { fontSize: 48, marginBottom: spacing.md },
  emptyTitle:      { ...typography.h3, marginBottom: spacing.sm, textAlign: 'center' },
  emptyDesc:       { ...typography.body, textAlign: 'center', marginBottom: spacing.lg },
  lockedBox:       { flex: 1, alignItems: 'center', justifyContent: 'center', padding: spacing.xl },
  lockIcon:        { fontSize: 56, marginBottom: spacing.md },
  lockTitle:       { ...typography.h2, marginBottom: spacing.sm, textAlign: 'center' },
  lockDesc:        { ...typography.body, textAlign: 'center', marginBottom: spacing.lg, color: colors.textSecondary },
  exploreBtn:      { backgroundColor: colors.gold, borderRadius: radius.md, paddingHorizontal: spacing.xl, paddingVertical: spacing.sm + 2 },
  exploreBtnTxt:   { color: colors.black, fontWeight: '700', fontSize: 15 },
});

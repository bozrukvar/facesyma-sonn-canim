// src/screens/PeerChatScreen.tsx
import React, { useState, useEffect, useRef, useCallback } from 'react';
import {
  View, Text, StyleSheet, FlatList, TextInput, TouchableOpacity,
  KeyboardAvoidingView, Platform, ActivityIndicator, Alert,
} from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { useSelector } from 'react-redux';
import type { RootState } from '../store';
import theme from '../utils/theme';
const { colors, spacing, typography, radius } = theme;
import { useLanguage } from '../utils/LanguageContext';
import { t } from '../utils/i18n';
import { PeerChatAPI, PeerMessage } from '../services/api';
import type { ScreenProps } from '../navigation/types';

const MAX_LEN = 2000;

const PeerChatScreen: React.FC<ScreenProps<'PeerChat'>> = ({ navigation, route }) => {
  const { roomId, otherUsername } = route.params;
  const insets = useSafeAreaInsets();
  const { lang } = useLanguage();
  const user = useSelector((s: RootState) => s.auth.user);

  const [messages, setMessages] = useState<PeerMessage[]>([]);
  const [loading, setLoading]   = useState(true);
  const [sending, setSending]   = useState(false);
  const [text, setText]         = useState('');
  const [wsStatus, setWsStatus] = useState<'connecting' | 'open' | 'closed'>('connecting');
  const [hasMore, setHasMore]   = useState(false);
  const [loadingMore, setLoadingMore] = useState(false);

  const wsRef   = useRef<WebSocket | null>(null);
  const flatRef = useRef<FlatList<PeerMessage>>(null);

  const loadHistory = useCallback(async (before?: number) => {
    try {
      const res = await PeerChatAPI.getMessages(roomId, before, 50);
      if (before) {
        setMessages(prev => [...(res.data ?? []), ...prev]);
      } else {
        setMessages(res.data ?? []);
      }
      setHasMore(res.has_more ?? false);
    } catch {
      if (!before) Alert.alert(t('common.error', lang), t('common.generic_error', lang));
    } finally {
      setLoading(false);
      setLoadingMore(false);
    }
  }, [roomId, lang]);

  useEffect(() => {
    loadHistory();
    PeerChatAPI.markRead(roomId).catch(() => {});
    return () => wsRef.current?.close();
  }, [roomId]);

  useEffect(() => {
    let ws: WebSocket | null = null;
    const connect = async () => {
      const token = await AsyncStorage.getItem('access_token');
      if (!token) return;
      const url = PeerChatAPI.getWsUrl(roomId, token);
      ws = new WebSocket(url);
      wsRef.current = ws;
      setWsStatus('connecting');
      ws.onopen = () => setWsStatus('open');
      ws.onclose = () => setWsStatus('closed');
      ws.onerror = () => setWsStatus('closed');
      ws.onmessage = (e) => {
        try {
          const data = JSON.parse(e.data);
          if (data.type === 'new_message' && data.message) {
            const msg: PeerMessage = data.message;
            setMessages(prev => {
              if (prev.find(m => m._id === msg._id)) return prev;
              return [...prev, msg];
            });
            setTimeout(() => flatRef.current?.scrollToEnd({ animated: true }), 100);
          } else if (data.type === 'error' && data.code === 'daily_limit_reached') {
            Alert.alert(t('peer_chat.daily_limit', lang), `${data.used}/${data.limit}`);
          }
        } catch {}
      };
    };
    connect();
    return () => { ws?.close(); };
  }, [roomId]);

  const sendMessage = async () => {
    const content = text.trim();
    if (!content || sending) return;
    setSending(true);
    try {
      if (wsRef.current?.readyState === WebSocket.OPEN) {
        wsRef.current.send(JSON.stringify({ type: 'send_message', content }));
        setText('');
      } else {
        const res = await PeerChatAPI.sendMessage(roomId, content);
        setMessages(prev => [...prev, res.message]);
        setText('');
        setTimeout(() => flatRef.current?.scrollToEnd({ animated: true }), 100);
      }
    } catch {
      Alert.alert(t('common.error', lang), t('common.generic_error', lang));
    } finally {
      setSending(false);
    }
  };

  const loadMore = () => {
    if (loadingMore || !hasMore || messages.length === 0) return;
    setLoadingMore(true);
    loadHistory(messages[0].created_at);
  };

  const renderItem = ({ item }: { item: PeerMessage }) => {
    const isMine = item.sender_id === user?.id;
    return (
      <View style={[styles.msgRow, isMine && styles.msgRowMine]}>
        <View style={[styles.bubble, isMine ? styles.bubbleMine : styles.bubbleOther]}>
          <Text style={[styles.msgText, isMine && styles.msgTextMine]}>{item.content}</Text>
          <Text style={[styles.msgTime, isMine && styles.msgTimeMine]}>
            {new Date(item.created_at * 1000).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
          </Text>
        </View>
      </View>
    );
  };

  return (
    <KeyboardAvoidingView
      style={[styles.container, { paddingTop: insets.top }]}
      behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
      keyboardVerticalOffset={insets.top}
    >
      <View style={styles.header}>
        <TouchableOpacity onPress={() => navigation.goBack()} style={styles.backBtn}>
          <Text style={styles.backTxt}>←</Text>
        </TouchableOpacity>
        <View style={styles.headerCenter}>
          <Text style={styles.title}>{otherUsername}</Text>
          <View style={styles.wsIndicator}>
            <View style={[styles.wsdot, wsStatus === 'open' ? styles.wsGreen : styles.wsRed]} />
            <Text style={styles.wsLabel}>
              {wsStatus === 'open' ? t('community.online', lang) : t('community.offline', lang)}
            </Text>
          </View>
        </View>
        <View style={{ width: 36 }} />
      </View>

      {loading ? (
        <View style={styles.center}><ActivityIndicator color={colors.gold} size="large" /></View>
      ) : (
        <FlatList
          ref={flatRef}
          data={messages}
          keyExtractor={item => item._id}
          renderItem={renderItem}
          contentContainerStyle={styles.listContent}
          onStartReached={loadMore}
          onStartReachedThreshold={0.1}
          ListHeaderComponent={loadingMore ? <ActivityIndicator color={colors.gold} /> : null}
          ListEmptyComponent={
            <View style={styles.center}><Text style={styles.emptyTxt}>💬</Text></View>
          }
          onContentSizeChange={() => flatRef.current?.scrollToEnd({ animated: false })}
        />
      )}

      <View style={[styles.inputRow, { paddingBottom: insets.bottom + spacing.sm }]}>
        <TextInput
          style={styles.input}
          value={text}
          onChangeText={v => setText(v.slice(0, MAX_LEN))}
          placeholder={t('peer_chat.type_message', lang)}
          placeholderTextColor={colors.textMuted}
          multiline
          maxLength={MAX_LEN}
        />
        <TouchableOpacity
          style={[styles.sendBtn, (!text.trim() || sending) && styles.sendBtnOff]}
          onPress={sendMessage}
          disabled={!text.trim() || sending}
          activeOpacity={0.85}
        >
          {sending
            ? <ActivityIndicator color="#000" size="small" />
            : <Text style={styles.sendTxt}>{t('peer_chat.send', lang)}</Text>
          }
        </TouchableOpacity>
      </View>
    </KeyboardAvoidingView>
  );
};

const styles = StyleSheet.create({
  container:    { flex: 1, backgroundColor: colors.background },
  header: {
    flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between',
    paddingHorizontal: spacing.lg, paddingVertical: spacing.md,
    borderBottomWidth: 1, borderColor: colors.border,
  },
  backBtn:      { width: 36, height: 36, justifyContent: 'center' },
  backTxt:      { ...typography.h2, color: colors.gold },
  headerCenter: { flex: 1, alignItems: 'center' },
  title:        { ...typography.h3, color: colors.textPrimary },
  wsIndicator:  { flexDirection: 'row', alignItems: 'center', gap: 4, marginTop: 2 },
  wsdot:        { width: 7, height: 7, borderRadius: 4 },
  wsGreen:      { backgroundColor: '#2ECC71' },
  wsRed:        { backgroundColor: '#E74C3C' },
  wsLabel:      { ...typography.caption, fontSize: 10, color: colors.textMuted },
  center:       { flex: 1, alignItems: 'center', justifyContent: 'center', padding: spacing.xl },
  emptyTxt:     { fontSize: 40 },
  listContent:  { padding: spacing.md, gap: spacing.sm },
  msgRow:       { flexDirection: 'row', marginVertical: 2 },
  msgRowMine:   { justifyContent: 'flex-end' },
  bubble:       { maxWidth: '75%', borderRadius: radius.lg, padding: spacing.sm, gap: 2 },
  bubbleOther:  { backgroundColor: colors.surface, borderWidth: 1, borderColor: colors.border },
  bubbleMine:   { backgroundColor: colors.goldDark },
  msgText:      { ...typography.body, color: colors.textPrimary, fontSize: 14 },
  msgTextMine:  { color: '#fff' },
  msgTime:      { ...typography.caption, color: colors.textMuted, fontSize: 10, alignSelf: 'flex-end' },
  msgTimeMine:  { color: 'rgba(255,255,255,0.6)' },
  inputRow: {
    flexDirection: 'row', alignItems: 'flex-end', gap: spacing.sm,
    paddingHorizontal: spacing.md, paddingTop: spacing.sm,
    borderTopWidth: 1, borderColor: colors.border,
    backgroundColor: colors.surface,
  },
  input: {
    flex: 1, maxHeight: 100,
    backgroundColor: colors.background,
    borderRadius: radius.lg, borderWidth: 1, borderColor: colors.border,
    paddingHorizontal: spacing.md, paddingVertical: spacing.sm,
    ...typography.body, color: colors.textPrimary, fontSize: 14,
  },
  sendBtn:    { height: 44, paddingHorizontal: spacing.md, backgroundColor: colors.gold, borderRadius: radius.lg, alignItems: 'center', justifyContent: 'center' },
  sendBtnOff: { opacity: 0.4 },
  sendTxt:    { ...typography.label, color: '#000', fontSize: 13 },
});

export default PeerChatScreen;

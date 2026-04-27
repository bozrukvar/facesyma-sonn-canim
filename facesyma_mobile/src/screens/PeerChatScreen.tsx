// src/screens/PeerChatScreen.tsx
import React, { useCallback, useEffect, useRef, useState } from 'react';
import {
  View, Text, TextInput, TouchableOpacity, FlatList,
  StyleSheet, SafeAreaView, KeyboardAvoidingView, Platform,
  ActivityIndicator, Alert,
} from 'react-native';
import { useNavigation, useRoute } from '@react-navigation/native';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { PeerChatAPI, type PeerMessage } from '../services/api';
import type { AppNavProp, ScreenProps } from '../navigation/types';
import theme from '../utils/theme';

const { colors, spacing, typography, radius } = theme;

const WS_RECONNECT_MS = 5000;
const TYPING_DEBOUNCE_MS = 2000;

const formatTime = (ts: number): string =>
  new Date(ts * 1000).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });

export default function PeerChatScreen() {
  const nav = useNavigation<AppNavProp>();
  const route = useRoute<ScreenProps<'PeerChat'>['route']>();
  const { roomId, otherUserId, otherUsername, compatScore } = route.params;

  const [messages, setMessages] = useState<PeerMessage[]>([]);
  const [input, setInput] = useState('');
  const [sending, setSending] = useState(false);
  const [loading, setLoading] = useState(true);
  const [wsConnected, setWsConnected] = useState(false);
  const [otherTyping, setOtherTyping] = useState(false);
  const [dailyUsed, setDailyUsed] = useState(0);
  const [dailyLimit, setDailyLimit] = useState(5);

  const wsRef = useRef<WebSocket | null>(null);
  const flatRef = useRef<FlatList>(null);
  const typingTimer = useRef<ReturnType<typeof setTimeout> | null>(null);
  const otherTypingTimer = useRef<ReturnType<typeof setTimeout> | null>(null);
  const myUserIdRef = useRef<number | null>(null);

  // ── İlk yükleme ─────────────────────────────────────────────────────────────
  useEffect(() => {
    loadInitial();
    return () => {
      wsRef.current?.close();
    };
  }, []);

  const loadInitial = async () => {
    try {
      const userStr = await AsyncStorage.getItem('user');
      if (userStr) {
        const u = JSON.parse(userStr);
        myUserIdRef.current = u.id;
      }
      const res = await PeerChatAPI.getMessages(roomId);
      setMessages(res.data);
      await PeerChatAPI.markRead(roomId);
      connectWS();
    } catch {
      // silently continue — WS + REST fallback
    } finally {
      setLoading(false);
    }
  };

  // ── WebSocket ────────────────────────────────────────────────────────────────
  const connectWS = async () => {
    const token = await AsyncStorage.getItem('access_token');
    if (!token) return;
    const url = PeerChatAPI.getWsUrl(roomId, token);
    const ws = new WebSocket(url);
    wsRef.current = ws;

    ws.onopen = () => setWsConnected(true);
    ws.onclose = () => {
      setWsConnected(false);
      setTimeout(connectWS, WS_RECONNECT_MS);
    };
    ws.onerror = () => setWsConnected(false);
    ws.onmessage = (event) => {
      try {
        const msg = JSON.parse(event.data);
        handleWsMessage(msg);
      } catch {}
    };
  };

  const handleWsMessage = (msg: any) => {
    switch (msg.type) {
      case 'new_message':
        setMessages(prev => {
          if (prev.some(m => m._id === msg.message._id)) return prev;
          return [...prev, msg.message];
        });
        if (msg.message.sender_id !== myUserIdRef.current) {
          PeerChatAPI.markRead(roomId).catch(() => {});
        }
        setTimeout(() => flatRef.current?.scrollToEnd({ animated: true }), 100);
        break;
      case 'typing':
        if (msg.user_id !== myUserIdRef.current) {
          setOtherTyping(true);
          if (otherTypingTimer.current) clearTimeout(otherTypingTimer.current);
          otherTypingTimer.current = setTimeout(() => setOtherTyping(false), 3000);
        }
        break;
      case 'read_receipt':
        break;
      case 'pong':
        break;
    }
  };

  // ── Mesaj gönder ─────────────────────────────────────────────────────────────
  const sendMessage = async () => {
    const text = input.trim();
    if (!text || sending) return;
    setInput('');
    setSending(true);
    try {
      if (wsRef.current?.readyState === WebSocket.OPEN) {
        wsRef.current.send(JSON.stringify({ type: 'send_message', content: text }));
      } else {
        const res = await PeerChatAPI.sendMessage(roomId, text);
        setMessages(prev => [...prev, res.message]);
        setTimeout(() => flatRef.current?.scrollToEnd({ animated: true }), 100);
      }
      setDailyUsed(prev => prev + 1);
    } catch (err: any) {
      if (err?.response?.status === 429) {
        Alert.alert(
          'Günlük Limit',
          `Günlük ${dailyLimit} mesaj hakkınızı kullandınız. Premium ile sınırsız mesaj atın.`
        );
        setInput(text);
      } else {
        Alert.alert('Hata', 'Mesaj gönderilemedi.');
        setInput(text);
      }
    } finally {
      setSending(false);
    }
  };

  // ── Yazıyor bildirimi ────────────────────────────────────────────────────────
  const onInputChange = (val: string) => {
    setInput(val);
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({ type: 'typing' }));
      if (typingTimer.current) clearTimeout(typingTimer.current);
      typingTimer.current = setTimeout(() => {}, TYPING_DEBOUNCE_MS);
    }
  };

  // ── Render mesaj ─────────────────────────────────────────────────────────────
  const renderMessage = ({ item, index }: { item: PeerMessage; index: number }) => {
    const isMe = item.sender_id === myUserIdRef.current;
    const prevItem = index > 0 ? messages[index - 1] : null;
    const showTime = !prevItem || (item.created_at - prevItem.created_at) > 300;

    return (
      <View>
        {showTime && (
          <Text style={s.timeSep}>{formatTime(item.created_at)}</Text>
        )}
        <View style={[s.bubbleRow, isMe ? s.bubbleRowMe : s.bubbleRowOther]}>
          <View style={[s.bubble, isMe ? s.bubbleMe : s.bubbleOther]}>
            {item.type === 'image' ? (
              <Text style={[s.bubbleText, isMe && s.bubbleTextMe]}>
                🖼 {item.file_name ?? 'Görsel'}
              </Text>
            ) : item.type === 'file' ? (
              <Text style={[s.bubbleText, isMe && s.bubbleTextMe]}>
                📎 {item.file_name ?? 'Dosya'}
              </Text>
            ) : (
              <Text style={[s.bubbleText, isMe && s.bubbleTextMe]}>{item.content}</Text>
            )}
          </View>
        </View>
      </View>
    );
  };

  if (loading) {
    return (
      <SafeAreaView style={s.safe}>
        <ActivityIndicator color={colors.gold} style={{ flex: 1 }} />
      </SafeAreaView>
    );
  }

  const limitReached = dailyUsed >= dailyLimit && dailyLimit > 0;

  return (
    <SafeAreaView style={s.safe}>
      {/* Header */}
      <View style={s.header}>
        <TouchableOpacity onPress={() => nav.goBack()} style={s.backBtn}>
          <Text style={s.backTxt}>←</Text>
        </TouchableOpacity>
        <View style={s.avatar}>
          <Text style={s.avatarTxt}>{(otherUsername?.[0] ?? '?').toUpperCase()}</Text>
        </View>
        <View style={s.headerInfo}>
          <Text style={s.headerName}>{otherUsername}</Text>
          <Text style={s.headerSub}>
            {wsConnected ? '● Bağlı' : '○ Bağlanıyor...'}
            {compatScore && compatScore > 0 ? `  •  Uyum %${Math.round(compatScore)}` : ''}
          </Text>
        </View>
      </View>

      {/* Günlük limit uyarısı */}
      {dailyUsed > 0 && (
        <View style={s.limitBar}>
          <Text style={s.limitTxt}>
            Günlük {dailyUsed}/{dailyLimit} mesaj
            {limitReached ? ' — Premium ile sınırsız at!' : ''}
          </Text>
        </View>
      )}

      <KeyboardAvoidingView
        style={{ flex: 1 }}
        behavior={Platform.OS === 'ios' ? 'padding' : undefined}
        keyboardVerticalOffset={0}
      >
        {/* Mesajlar */}
        <FlatList
          ref={flatRef}
          data={messages}
          keyExtractor={m => m._id}
          renderItem={renderMessage}
          onContentSizeChange={() => flatRef.current?.scrollToEnd({ animated: false })}
          contentContainerStyle={s.msgList}
          ListEmptyComponent={
            <View style={s.emptyChat}>
              <Text style={s.emptyChatTxt}>Henüz mesaj yok. İlk mesajı gönder! 👋</Text>
            </View>
          }
        />

        {/* Yazıyor... */}
        {otherTyping && (
          <View style={s.typingRow}>
            <Text style={s.typingTxt}>{otherUsername} yazıyor...</Text>
          </View>
        )}

        {/* Input */}
        <View style={s.inputRow}>
          <TextInput
            style={s.input}
            value={input}
            onChangeText={onInputChange}
            placeholder={limitReached ? 'Günlük limit doldu' : 'Mesaj yaz...'}
            placeholderTextColor={colors.textMuted}
            multiline
            maxLength={2000}
            editable={!limitReached}
          />
          <TouchableOpacity
            style={[s.sendBtn, (!input.trim() || sending || limitReached) && s.sendBtnDisabled]}
            onPress={sendMessage}
            disabled={!input.trim() || sending || limitReached}
          >
            {sending
              ? <ActivityIndicator color={colors.black} size="small" />
              : <Text style={s.sendBtnTxt}>↑</Text>
            }
          </TouchableOpacity>
        </View>
      </KeyboardAvoidingView>
    </SafeAreaView>
  );
}

const s = StyleSheet.create({
  safe:            { flex: 1, backgroundColor: colors.background },
  header:          { flexDirection: 'row', alignItems: 'center', paddingHorizontal: spacing.md, paddingVertical: spacing.sm, borderBottomWidth: 1, borderBottomColor: colors.border },
  backBtn:         { padding: spacing.sm, marginRight: spacing.xs },
  backTxt:         { fontSize: 22, color: colors.gold },
  avatar:          { width: 40, height: 40, borderRadius: 20, backgroundColor: colors.goldDark, alignItems: 'center', justifyContent: 'center', marginRight: spacing.sm },
  avatarTxt:       { color: colors.white, fontWeight: '700', fontSize: 16 },
  headerInfo:      { flex: 1 },
  headerName:      { ...typography.h3, fontSize: 16 },
  headerSub:       { ...typography.caption, fontSize: 11, color: colors.textMuted },
  limitBar:        { backgroundColor: colors.surfaceWarm, paddingHorizontal: spacing.md, paddingVertical: 5, borderBottomWidth: 1, borderBottomColor: colors.border },
  limitTxt:        { ...typography.caption, color: colors.warmAmber, textAlign: 'center', fontSize: 12 },
  msgList:         { padding: spacing.md, paddingBottom: spacing.lg },
  bubbleRow:       { flexDirection: 'row', marginBottom: spacing.xs },
  bubbleRowMe:     { justifyContent: 'flex-end' },
  bubbleRowOther:  { justifyContent: 'flex-start' },
  bubble:          { maxWidth: '80%', borderRadius: radius.lg, paddingHorizontal: spacing.md, paddingVertical: spacing.sm },
  bubbleMe:        { backgroundColor: colors.gold, borderBottomRightRadius: 4 },
  bubbleOther:     { backgroundColor: colors.surface, borderBottomLeftRadius: 4, borderWidth: 1, borderColor: colors.border },
  bubbleText:      { ...typography.chat, color: colors.textPrimary },
  bubbleTextMe:    { color: colors.black },
  timeSep:         { ...typography.caption, textAlign: 'center', marginVertical: spacing.sm, color: colors.textMuted },
  typingRow:       { paddingHorizontal: spacing.lg, paddingBottom: spacing.xs },
  typingTxt:       { ...typography.caption, color: colors.textMuted, fontStyle: 'italic' },
  inputRow:        { flexDirection: 'row', alignItems: 'flex-end', paddingHorizontal: spacing.md, paddingVertical: spacing.sm, borderTopWidth: 1, borderTopColor: colors.border, gap: spacing.sm },
  input:           { flex: 1, backgroundColor: colors.surface, borderRadius: radius.lg, paddingHorizontal: spacing.md, paddingVertical: spacing.sm, color: colors.textPrimary, fontSize: 15, maxHeight: 120, borderWidth: 1, borderColor: colors.border },
  sendBtn:         { width: 44, height: 44, borderRadius: 22, backgroundColor: colors.gold, alignItems: 'center', justifyContent: 'center' },
  sendBtnDisabled: { opacity: 0.4 },
  sendBtnTxt:      { color: colors.black, fontSize: 20, fontWeight: '700' },
  emptyChat:       { flex: 1, alignItems: 'center', justifyContent: 'center', paddingTop: spacing.xxxl },
  emptyChatTxt:    { ...typography.body, color: colors.textMuted, textAlign: 'center' },
});

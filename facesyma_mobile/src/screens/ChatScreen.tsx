// src/screens/ChatScreen.tsx
import React, { useState, useRef, useEffect, useCallback, useMemo } from 'react';
import {
  View, Text, TextInput, TouchableOpacity, FlatList,
  StyleSheet, KeyboardAvoidingView, Platform, ActivityIndicator,
  Dimensions, Animated,
} from 'react-native';
import { ChatAPI } from '../services/api';
import { useSelector } from 'react-redux';
import { RootState } from '../store';
import theme from '../utils/theme';
const { colors, spacing, typography, radius, shadow } = theme;
const AnimatedView = Animated.View;
import { useLanguage } from '../utils/LanguageContext';
import { t } from '../utils/i18n';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import type { ScreenProps } from '../navigation/types';

const { width } = Dimensions.get('window');

interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: number;
}

const keyExtractor = (m: Message) => m.id;

const getQuickQuestions = (lang: string) => [
  t('chat.quick_question_1', lang),
  t('chat.quick_question_2', lang),
  t('chat.quick_question_3', lang),
  t('chat.quick_question_4', lang),
  t('chat.quick_question_5', lang),
];

// ── Yazıyor animasyonu ────────────────────────────────────────────────────────
const TypingIndicator = () => {
  const a1 = useRef(new Animated.Value(0.3)).current;
  const a2 = useRef(new Animated.Value(0.3)).current;
  const a3 = useRef(new Animated.Value(0.3)).current;

  useEffect(() => {
    const anim = (a: Animated.Value, delay: number) =>
      Animated.loop(Animated.sequence([
        Animated.delay(delay),
        Animated.timing(a, { toValue: 1, duration: 300, useNativeDriver: true }),
        Animated.timing(a, { toValue: 0.3, duration: 300, useNativeDriver: true }),
      ]));
    Animated.parallel([anim(a1, 0), anim(a2, 200), anim(a3, 400)]).start();
  }, []);

  return (
    <View style={styles.msgRowAI}>
      <View style={styles.aiAvatar}><Text style={styles.aiAvatarIcon}>✨</Text></View>
      <View style={styles.bubbleAI}>
        <View style={styles.typingDots}>
          {[a1, a2, a3].map((a, i) => (
            <AnimatedView key={i} style={{
              width: 7, height: 7, borderRadius: 4,
              backgroundColor: colors.gold,
              opacity: a,
            }} />
          ))}
        </View>
      </View>
    </View>
  );
};

// ── Mesaj balonu ─────────────────────────────────────────────────────────────
const MessageBubble = ({ item }: { item: Message }) => {
  const isUser = item.role === 'user';
  const fadeAnim = useRef(new Animated.Value(0)).current;
  const slideAnim = useRef(new Animated.Value(12)).current;

  useEffect(() => {
    Animated.parallel([
      Animated.timing(fadeAnim,  { toValue: 1, duration: 280, useNativeDriver: true }),
      Animated.timing(slideAnim, { toValue: 0, duration: 280, useNativeDriver: true }),
    ]).start();
  }, []);

  return (
    <AnimatedView style={{
      opacity: fadeAnim,
      transform: [{ translateY: slideAnim }],
    }}>
      <View style={isUser ? styles.msgRowUser : styles.msgRowAI}>
        {!isUser && (
          <View style={styles.aiAvatar}><Text style={styles.aiAvatarIcon}>✨</Text></View>
        )}
        <View style={[
          isUser ? styles.bubbleUser : styles.bubbleAI,
          isUser && shadow.gold,
        ]}>
          <Text style={isUser ? styles.bubbleUserText : styles.bubbleAIText}>
            {item.content}
          </Text>
        </View>
      </View>
    </AnimatedView>
  );
};

// ── Ana ekran ────────────────────────────────────────────────────────────────
const ChatScreen = ({ navigation, route }: ScreenProps<'Chat'>) => {
  const insets = useSafeAreaInsets();
  const user           = useSelector((s: RootState) => s.auth.user);
  const analysisResult = route.params?.analysisResult ?? {};
  const { lang }       = useLanguage();
  const QUICK_QUESTIONS = useMemo(() => getQuickQuestions(lang), [lang]);

  const [messages,     setMessages]     = useState<Message[]>([]);
  const [input,        setInput]        = useState('');
  const [convId,       setConvId]       = useState<string | null>(null);
  const [loading,      setLoading]      = useState(false);
  const [initializing, setInitializing] = useState(true);
  const [error,        setError]        = useState('');
  const [showQuick,    setShowQuick]    = useState(true);

  const listRef = useRef<FlatList>(null);

  const scrollToEnd = () =>
    setTimeout(() => listRef.current?.scrollToEnd({ animated: true }), 120);

  // ── Başlat ──────────────────────────────────────────────────────────────────
  useEffect(() => { startConversation(); }, []);

  const startConversation = async () => {
    setInitializing(true);
    setError('');
    setMessages([]);
    try {
      const data = await ChatAPI.startChat(analysisResult, lang);
      setConvId(data.conversation_id);
      setMessages([{
        id:        'init',
        role:      'assistant',
        content:   data.assistant_message,
        timestamp: Date.now(),
      }]);
      setShowQuick(true);
    } catch {
      setError(t('chat.error_init', lang));
    } finally {
      setInitializing(false);
    }
  };

  // ── Mesaj gönder ────────────────────────────────────────────────────────────
  const sendMessage = useCallback(async (text?: string) => {
    const msg = (text || input).trim();
    if (!msg || loading || !convId) return;

    setInput('');
    setError('');
    setShowQuick(false);

    const userMsg: Message = {
      id: Date.now().toString(), role: 'user', content: msg, timestamp: Date.now(),
    };
    setMessages(prev => [...prev, userMsg]);
    setLoading(true);
    scrollToEnd();

    try {
      const data = await ChatAPI.sendMessage(convId, msg, lang);
      setMessages(prev => [...prev, {
        id:        (Date.now() + 1).toString(),
        role:      'assistant',
        content:   data.assistant_message,
        timestamp: Date.now(),
      }]);
    } catch {
      setError(t('chat.error_response', lang));
      setMessages(prev => prev.filter(m => m.id !== userMsg.id));
      setInput(msg);
    } finally {
      setLoading(false);
      scrollToEnd();
    }
  }, [input, loading, convId, lang]);

  // ── Yükleniyor ──────────────────────────────────────────────────────────────
  if (initializing) {
    return (
      <View style={styles.containerCenter}>
        <View style={styles.loadingOrb}>
          <Text style={styles.loadingOrbIcon}>✨</Text>
        </View>
        <Text style={styles.loadingText}>{t('chat.initializing', lang)}</Text>
        <ActivityIndicator color={colors.warmAmber} />
      </View>
    );
  }

  return (
    <KeyboardAvoidingView
      style={styles.container}
      behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
      keyboardVerticalOffset={Platform.OS === 'ios' ? 88 : 0}
    >
      {/* Header */}
      <View style={[styles.header, { paddingTop: insets.top + spacing.sm }]}>
        <TouchableOpacity onPress={() => navigation.goBack()} style={styles.backBtn}>
          <Text style={styles.backText}>←</Text>
        </TouchableOpacity>

        <View style={styles.headerCenter}>
          <View style={styles.headerAvatar}><Text style={styles.headerAvatarIcon}>✨</Text></View>
          <View>
            <Text style={styles.headerTitle}>{t('chat.assistant', lang)}</Text>
            <View style={styles.onlinePill}>
              <View style={styles.onlineDot} />
              <Text style={styles.onlineText}>{t('chat.online', lang)}</Text>
            </View>
          </View>
        </View>

        <TouchableOpacity
          onPress={startConversation}
          style={styles.newBtn}
        >
          <Text style={styles.newBtnText}>{t('chat.new', lang)}</Text>
        </TouchableOpacity>
      </View>

      {/* Mesajlar */}
      <FlatList
        ref={listRef}
        data={messages}
        keyExtractor={keyExtractor}
        renderItem={({ item }) => <MessageBubble item={item} />}
        contentContainerStyle={styles.msgList}
        onLayout={scrollToEnd}
        ListFooterComponent={loading ? <TypingIndicator /> : null}
        showsVerticalScrollIndicator={false}
      />

      {/* Hızlı sorular */}
      {showQuick && messages.length <= 1 && !loading && (
        <View style={styles.quickWrap}>
          <Text style={styles.quickLabel}>{t('chat.quick_ask', lang)}</Text>
          <View style={styles.quickRow}>
            {QUICK_QUESTIONS.map((q, i) => (
              <TouchableOpacity
                key={i}
                style={styles.quickChip}
                onPress={() => sendMessage(q)}
              >
                <Text style={styles.quickChipText} numberOfLines={1}>{q}</Text>
              </TouchableOpacity>
            ))}
          </View>
        </View>
      )}

      {/* Hata */}
      {error ? (
        <View style={styles.errorBar}>
          <Text style={styles.errorText}>⚠ {error}</Text>
        </View>
      ) : null}

      {/* Input */}
      <View style={styles.inputRow}>
        <TextInput
          style={styles.input}
          value={input}
          onChangeText={setInput}
          placeholder={t('chat.input_placeholder', lang)}
          placeholderTextColor={colors.textMuted}
          multiline
          maxLength={500}
        />
        <TouchableOpacity
          style={[
            styles.sendBtn,
            (!input.trim() || loading) && styles.sendBtnDisabled,
          ]}
          onPress={() => sendMessage()}
          disabled={!input.trim() || loading}
        >
          {loading
            ? <ActivityIndicator color="#000" size="small" />
            : <Text style={styles.sendIcon}>↑</Text>
          }
        </TouchableOpacity>
      </View>
    </KeyboardAvoidingView>
  );
};

const styles = StyleSheet.create({
  container: { flex:1, backgroundColor: colors.background },
  containerCenter: { flex:1, backgroundColor: colors.background, alignItems:'center' as const, justifyContent:'center' as const, gap:16 },

  // Header
  header: {
    flexDirection: 'row', alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: spacing.lg,
    paddingBottom: spacing.md,
    borderBottomWidth: 1,
    borderBottomColor: colors.border,
  },
  backBtn:  { padding:4, width:44 },
  backText: { ...typography.h2, color: colors.gold, fontSize:22 },
  headerCenter: { flexDirection:'row', alignItems:'center', gap:10 },
  headerAvatar: {
    width:38, height:38, borderRadius:19,
    backgroundColor: colors.warmAmberGlow,
    borderWidth:1.5, borderColor:`${colors.warmAmber}40`,
    alignItems:'center', justifyContent:'center',
  },
  headerTitle: { ...typography.h3, fontSize:14 },
  onlinePill:  { flexDirection:'row', alignItems:'center', gap:4, marginTop:2 },
  onlineDot:   { width:6, height:6, borderRadius:3, backgroundColor: colors.success },
  onlineText:  { ...typography.caption, color: colors.success, fontSize:10 },
  newBtn: {
    paddingHorizontal:12, paddingVertical:6,
    borderRadius: radius.full,
    borderWidth:1, borderColor: colors.border,
    width:44, alignItems:'center',
  },
  newBtnText: { ...typography.caption, color: colors.textMuted, fontSize:11 },

  // Mesajlar
  msgList: {
    paddingHorizontal: spacing.md,
    paddingVertical:   spacing.md,
    gap: spacing.sm,
  },
  msgRowUser: { flexDirection:'row-reverse', marginBottom:8 },
  msgRowAI:   { flexDirection:'row', alignItems:'flex-end', gap:8, marginBottom:8 },

  aiAvatar: {
    width:30, height:30, borderRadius:15,
    backgroundColor: colors.warmAmberGlow,
    borderWidth:1, borderColor:`${colors.warmAmber}30`,
    alignItems:'center', justifyContent:'center',
    marginBottom:2,
  },

  bubbleUser: {
    maxWidth:      width * 0.70,
    backgroundColor: colors.userBubble,
    borderRadius:  radius.lg,
    borderBottomRightRadius: radius.xs,
    paddingHorizontal: 14,
    paddingVertical:   10,
  },
  bubbleUserText: {
    ...typography.chat,
    color: colors.userBubbleText,
    fontWeight: '500',
  },

  bubbleAI: {
    maxWidth:      width * 0.75,
    backgroundColor: colors.aiBubble,
    borderWidth:   1,
    borderColor:   colors.aiBubbleBorder,
    borderRadius:  radius.lg,
    borderBottomLeftRadius: radius.xs,
    paddingHorizontal: 14,
    paddingVertical:   10,
  },
  bubbleAIText: {
    ...typography.chat,
    color: colors.aiBubbleText,
    lineHeight: 22,
  },

  // Yükleniyor
  loadingOrb: {
    width:80, height:80, borderRadius:40,
    backgroundColor: colors.warmAmberGlow,
    borderWidth:1.5, borderColor:`${colors.warmAmber}40`,
    alignItems:'center', justifyContent:'center',
    ...shadow.warm,
  },
  loadingText: { ...typography.body, color: colors.textWarm },

  // Hızlı sorular
  quickWrap: {
    paddingHorizontal: spacing.md,
    paddingVertical:   spacing.sm,
    borderTopWidth:1, borderTopColor: colors.border,
  },
  quickLabel: { ...typography.goldLabel, fontSize:9, marginBottom:8 },
  quickRow:   { flexDirection:'row', flexWrap:'wrap', gap:6 },
  quickChip: {
    paddingHorizontal:12, paddingVertical:6,
    borderRadius: radius.full,
    backgroundColor: colors.surfaceWarm,
    borderWidth:1, borderColor: colors.borderWarm,
  },
  quickChipText: {
    ...typography.caption,
    color: colors.textWarm,
    fontSize:11,
  },

  // Hata
  errorBar: {
    marginHorizontal: spacing.md,
    marginBottom: spacing.sm,
    padding: spacing.sm,
    backgroundColor: 'rgba(217,95,95,0.1)',
    borderRadius: radius.sm,
    borderWidth:1, borderColor: colors.error,
  },
  errorText: { ...typography.caption, color: colors.error, fontSize:12 },

  // Input
  inputRow: {
    flexDirection: 'row', alignItems: 'flex-end',
    paddingHorizontal: spacing.md,
    paddingVertical:   spacing.md,
    borderTopWidth:1, borderTopColor: colors.border,
    gap:8,
  },
  input: {
    flex:1,
    minHeight:44, maxHeight:110,
    backgroundColor: colors.surfaceWarm,
    borderRadius:    radius.xl,
    borderWidth:1, borderColor: colors.borderWarm,
    paddingHorizontal: spacing.md,
    paddingVertical:   spacing.sm,
    color: colors.textPrimary,
    fontSize:14, fontFamily:'System',
  },
  sendBtn: {
    width:44, height:44, borderRadius:22,
    backgroundColor: colors.gold,
    alignItems:'center', justifyContent:'center',
    ...shadow.gold,
  },
  sendBtnDisabled: {
    backgroundColor: colors.border,
    shadowOpacity:0, elevation:0,
  },
  sendIcon: { fontSize:18, color:'#000', fontWeight:'700' },
  aiAvatarIcon: { fontSize: 14 },
  loadingOrbIcon: { fontSize: 32 },
  headerAvatarIcon: { fontSize: 18 },
  typingDots: { flexDirection: 'row' as const, gap: 5, paddingVertical: 2, paddingHorizontal: 4 },
});

export default ChatScreen;

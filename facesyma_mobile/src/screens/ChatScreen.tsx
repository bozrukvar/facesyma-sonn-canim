// src/screens/ChatScreen.tsx
import React, { useState, useRef, useEffect, useCallback, useMemo } from 'react';
import {
  View, Text, TextInput, TouchableOpacity, FlatList,
  StyleSheet, KeyboardAvoidingView, Platform, ActivityIndicator,
  Dimensions, Animated,
} from 'react-native';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { ChatAPI } from '../services/api';
import { useSelector } from 'react-redux';
import { RootState } from '../store';
import theme from '../utils/theme';
import { useLanguage } from '../utils/LanguageContext';
import { t } from '../utils/i18n';

const { width } = Dimensions.get('window');

// API çağrıları: ChatAPI (src/services/api.ts)

interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: number;
}

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
      <View style={styles.aiAvatar}><Text style={{ fontSize: 14 }}>✨</Text></View>
      <View style={styles.bubbleAI}>
        <View style={{ flexDirection: 'row', gap: 5, paddingVertical: 2, paddingHorizontal: 4 }}>
          {[a1, a2, a3].map((a, i) => (
            <Animated.View key={i} style={{
              width: 7, height: 7, borderRadius: 4,
              backgroundColor: theme.colors.gold,
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
    <Animated.View style={{
      opacity: fadeAnim,
      transform: [{ translateY: slideAnim }],
    }}>
      <View style={isUser ? styles.msgRowUser : styles.msgRowAI}>
        {!isUser && (
          <View style={styles.aiAvatar}><Text style={{ fontSize: 14 }}>✨</Text></View>
        )}
        <View style={[
          isUser ? styles.bubbleUser : styles.bubbleAI,
          isUser && theme.shadow.gold,
        ]}>
          <Text style={isUser ? styles.bubbleUserText : styles.bubbleAIText}>
            {item.content}
          </Text>
        </View>
      </View>
    </Animated.View>
  );
};

// ── Ana ekran ────────────────────────────────────────────────────────────────
const ChatScreen: React.FC<{ navigation: any; route: any }> = ({ navigation, route }) => {
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
  }, [input, loading, convId, lang, QUICK_QUESTIONS]);

  // ── Yükleniyor ──────────────────────────────────────────────────────────────
  if (initializing) {
    return (
      <View style={[styles.container, { alignItems:'center', justifyContent:'center', gap:16 }]}>
        <View style={styles.loadingOrb}>
          <Text style={{ fontSize: 32 }}>✨</Text>
        </View>
        <Text style={styles.loadingText}>{t('chat.initializing', lang)}</Text>
        <ActivityIndicator color={theme.colors.warmAmber} />
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
      <View style={styles.header}>
        <TouchableOpacity onPress={() => navigation.goBack()} style={styles.backBtn}>
          <Text style={styles.backText}>←</Text>
        </TouchableOpacity>

        <View style={styles.headerCenter}>
          <View style={styles.headerAvatar}><Text style={{ fontSize: 18 }}>✨</Text></View>
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
        keyExtractor={m => m.id}
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
          placeholderTextColor={theme.colors.textMuted}
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
  container: { flex:1, backgroundColor: theme.colors.background },

  // Header
  header: {
    flexDirection: 'row', alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: theme.spacing.lg,
    paddingTop: theme.spacing.lg + 44,
    paddingBottom: theme.spacing.md,
    borderBottomWidth: 1,
    borderBottomColor: theme.colors.border,
  },
  backBtn:  { padding:4, width:44 },
  backText: { ...theme.typography.h2, color: theme.colors.gold, fontSize:22 },
  headerCenter: { flexDirection:'row', alignItems:'center', gap:10 },
  headerAvatar: {
    width:38, height:38, borderRadius:19,
    backgroundColor: theme.colors.warmAmberGlow,
    borderWidth:1.5, borderColor:`${theme.colors.warmAmber}40`,
    alignItems:'center', justifyContent:'center',
  },
  headerTitle: { ...theme.typography.h3, fontSize:14 },
  onlinePill:  { flexDirection:'row', alignItems:'center', gap:4, marginTop:2 },
  onlineDot:   { width:6, height:6, borderRadius:3, backgroundColor: theme.colors.success },
  onlineText:  { ...theme.typography.caption, color: theme.colors.success, fontSize:10 },
  newBtn: {
    paddingHorizontal:12, paddingVertical:6,
    borderRadius: theme.radius.full,
    borderWidth:1, borderColor: theme.colors.border,
    width:44, alignItems:'center',
  },
  newBtnText: { ...theme.typography.caption, color: theme.colors.textMuted, fontSize:11 },

  // Mesajlar
  msgList: {
    paddingHorizontal: theme.spacing.md,
    paddingVertical:   theme.spacing.md,
    gap: theme.spacing.sm,
  },
  msgRowUser: { flexDirection:'row-reverse', marginBottom:8 },
  msgRowAI:   { flexDirection:'row', alignItems:'flex-end', gap:8, marginBottom:8 },

  aiAvatar: {
    width:30, height:30, borderRadius:15,
    backgroundColor: theme.colors.warmAmberGlow,
    borderWidth:1, borderColor:`${theme.colors.warmAmber}30`,
    alignItems:'center', justifyContent:'center',
    marginBottom:2,
  },

  bubbleUser: {
    maxWidth:      width * 0.70,
    backgroundColor: theme.colors.userBubble,
    borderRadius:  theme.radius.lg,
    borderBottomRightRadius: theme.radius.xs,
    paddingHorizontal: 14,
    paddingVertical:   10,
  },
  bubbleUserText: {
    ...theme.typography.chat,
    color: theme.colors.userBubbleText,
    fontWeight: '500',
  },

  bubbleAI: {
    maxWidth:      width * 0.75,
    backgroundColor: theme.colors.aiBubble,
    borderWidth:   1,
    borderColor:   theme.colors.aiBubbleBorder,
    borderRadius:  theme.radius.lg,
    borderBottomLeftRadius: theme.radius.xs,
    paddingHorizontal: 14,
    paddingVertical:   10,
  },
  bubbleAIText: {
    ...theme.typography.chat,
    color: theme.colors.aiBubbleText,
    lineHeight: 22,
  },

  // Yükleniyor
  loadingOrb: {
    width:80, height:80, borderRadius:40,
    backgroundColor: theme.colors.warmAmberGlow,
    borderWidth:1.5, borderColor:`${theme.colors.warmAmber}40`,
    alignItems:'center', justifyContent:'center',
    ...theme.shadow.warm,
  },
  loadingText: { ...theme.typography.body, color: theme.colors.textWarm },

  // Hızlı sorular
  quickWrap: {
    paddingHorizontal: theme.spacing.md,
    paddingVertical:   theme.spacing.sm,
    borderTopWidth:1, borderTopColor: theme.colors.border,
  },
  quickLabel: { ...theme.typography.goldLabel, fontSize:9, marginBottom:8 },
  quickRow:   { flexDirection:'row', flexWrap:'wrap', gap:6 },
  quickChip: {
    paddingHorizontal:12, paddingVertical:6,
    borderRadius: theme.radius.full,
    backgroundColor: theme.colors.surfaceWarm,
    borderWidth:1, borderColor: theme.colors.borderWarm,
  },
  quickChipText: {
    ...theme.typography.caption,
    color: theme.colors.textWarm,
    fontSize:11,
  },

  // Hata
  errorBar: {
    marginHorizontal: theme.spacing.md,
    marginBottom: theme.spacing.sm,
    padding: theme.spacing.sm,
    backgroundColor: 'rgba(217,95,95,0.1)',
    borderRadius: theme.radius.sm,
    borderWidth:1, borderColor: theme.colors.error,
  },
  errorText: { ...theme.typography.caption, color: theme.colors.error, fontSize:12 },

  // Input
  inputRow: {
    flexDirection: 'row', alignItems: 'flex-end',
    paddingHorizontal: theme.spacing.md,
    paddingVertical:   theme.spacing.md,
    borderTopWidth:1, borderTopColor: theme.colors.border,
    gap:8,
  },
  input: {
    flex:1,
    minHeight:44, maxHeight:110,
    backgroundColor: theme.colors.surfaceWarm,
    borderRadius:    theme.radius.xl,
    borderWidth:1, borderColor: theme.colors.borderWarm,
    paddingHorizontal: theme.spacing.md,
    paddingVertical:   theme.spacing.sm,
    color: theme.colors.textPrimary,
    fontSize:14, fontFamily:'System',
  },
  sendBtn: {
    width:44, height:44, borderRadius:22,
    backgroundColor: theme.colors.gold,
    alignItems:'center', justifyContent:'center',
    ...theme.shadow.gold,
  },
  sendBtnDisabled: {
    backgroundColor: theme.colors.border,
    shadowOpacity:0, elevation:0,
  },
  sendIcon: { fontSize:18, color:'#000', fontWeight:'700' },
});

export default ChatScreen;

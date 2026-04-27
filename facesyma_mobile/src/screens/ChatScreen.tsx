// src/screens/ChatScreen.tsx
import React, { useState, useRef, useEffect, useCallback, useMemo } from 'react';
import {
  View, Text, TextInput, TouchableOpacity, FlatList,
  StyleSheet, KeyboardAvoidingView, Platform, ActivityIndicator,
  Dimensions, Animated, ScrollView,
} from 'react-native';
import { ChatAPI } from '../services/api';
import { useSelector } from 'react-redux';
import { RootState } from '../store';
import { CHAT_MIN_MODULES } from '../store/authSlice';
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

const TEST_MARKER = '[TEST_QUESTIONS]';

interface TestQuestion {
  q_id: string;
  order: number;
  text: string;
  scale?: { min: number; max: number; labels: Record<string, string> };
}
interface TestData {
  type: string;
  test_type: string;
  session_id: string;
  questions: TestQuestion[];
}

const SCALE_LABELS: Record<string, Record<string, string>> = {
  tr: { '1': 'Hiç katılmıyorum', '2': 'Katılmıyorum', '3': 'Kararsızım', '4': 'Katılıyorum', '5': 'Kesinlikle' },
  en: { '1': 'Strongly Disagree', '2': 'Disagree', '3': 'Neutral', '4': 'Agree', '5': 'Strongly Agree' },
};

const TestQuestionsCard = ({
  data, lang, onSubmit,
}: { data: TestData; lang: string; onSubmit: (text: string) => void }) => {
  const [answers, setAnswers] = useState<Record<string, number>>({});
  const labels = SCALE_LABELS[lang] || SCALE_LABELS.en;
  const questions = data.questions || [];
  const allAnswered = questions.length > 0 && questions.every(q => answers[q.q_id] !== undefined);

  const handleSubmit = () => {
    const lines = questions.map(q => `${q.order}. ${q.text} → ${answers[q.q_id]}`).join('\n');
    onSubmit(lang === 'tr' ? `Test cevaplarım:\n${lines}` : `My answers:\n${lines}`);
  };

  return (
    <View style={tStyles.card}>
      {/* Scale legend */}
      <View style={tStyles.legend}>
        {[1,2,3,4,5].map(n => (
          <View key={n} style={tStyles.legendItem}>
            <View style={tStyles.legendDot}><Text style={tStyles.legendNum}>{n}</Text></View>
            <Text style={tStyles.legendLabel} numberOfLines={2}>{labels[String(n)]}</Text>
          </View>
        ))}
      </View>

      {/* Questions */}
      {questions.map(q => (
        <View key={q.q_id} style={tStyles.qRow}>
          <Text style={tStyles.qText}>{q.order}. {q.text}</Text>
          <View style={tStyles.btnRow}>
            {[1,2,3,4,5].map(n => {
              const selected = answers[q.q_id] === n;
              return (
                <TouchableOpacity
                  key={n}
                  style={[tStyles.optBtn, selected && tStyles.optBtnSel]}
                  onPress={() => setAnswers(prev => ({ ...prev, [q.q_id]: n }))}
                  activeOpacity={0.7}
                >
                  <Text style={[tStyles.optNum, selected && tStyles.optNumSel]}>{n}</Text>
                </TouchableOpacity>
              );
            })}
          </View>
        </View>
      ))}

      {allAnswered && (
        <TouchableOpacity style={tStyles.submitBtn} onPress={handleSubmit}>
          <Text style={tStyles.submitText}>
            {lang === 'tr' ? 'Sonuçları Gör →' : 'See Results →'}
          </Text>
        </TouchableOpacity>
      )}
    </View>
  );
};

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
const MessageBubble = ({ item, onTestSubmit }: { item: Message; onTestSubmit?: (text: string) => void }) => {
  const isUser = item.role === 'user';
  const { lang } = useLanguage();
  const fadeAnim = useRef(new Animated.Value(0)).current;
  const slideAnim = useRef(new Animated.Value(12)).current;

  useEffect(() => {
    Animated.parallel([
      Animated.timing(fadeAnim,  { toValue: 1, duration: 280, useNativeDriver: true }),
      Animated.timing(slideAnim, { toValue: 0, duration: 280, useNativeDriver: true }),
    ]).start();
  }, []);

  const isTestMessage = !isUser && item.content.startsWith(TEST_MARKER);
  let testData: TestData | null = null;
  if (isTestMessage) {
    try { testData = JSON.parse(item.content.slice(TEST_MARKER.length)); } catch {}
  }

  return (
    <AnimatedView style={{ opacity: fadeAnim, transform: [{ translateY: slideAnim }] }}>
      {isTestMessage && testData ? (
        <View style={styles.msgRowAI}>
          <View style={styles.aiAvatar}><Text style={styles.aiAvatarIcon}>✨</Text></View>
          <TestQuestionsCard data={testData} lang={lang} onSubmit={onTestSubmit ?? (() => {})} />
        </View>
      ) : (
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
      )}
    </AnimatedView>
  );
};

// ── Ana ekran ────────────────────────────────────────────────────────────────
const ChatScreen = ({ navigation, route }: ScreenProps<'Chat'>) => {
  const insets      = useSafeAreaInsets();
  const user        = useSelector((s: RootState) => s.auth.user);
  const modulesUsed = useSelector((s: RootState) => s.auth.modulesUsed);
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
  const [chatUsage,    setChatUsage]    = useState<{used: number; limit: number; plan: string} | null>(null);

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
      if (data.usage?.daily_limit) {
        setChatUsage({ used: data.usage.daily_used ?? 1, limit: data.usage.daily_limit, plan: data.usage.plan ?? 'free' });
      }
      setShowQuick(true);
    } catch (e: any) {
      setError(e?.response?.data?.detail || t('chat.error_init', lang));
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
      if (data.usage?.daily_limit) {
        setChatUsage({ used: data.usage.daily_used ?? 0, limit: data.usage.daily_limit, plan: data.usage.plan ?? 'free' });
      }
    } catch (e: any) {
      const detail = e?.response?.data?.detail || '';
      setError(detail || t('chat.error_response', lang));
      setMessages(prev => prev.filter(m => m.id !== userMsg.id));
      setInput(msg);
    } finally {
      setLoading(false);
      scrollToEnd();
    }
  }, [input, loading, convId, lang]);

  // ── Modül kapısı ────────────────────────────────────────────────────────────
  if (modulesUsed.length < CHAT_MIN_MODULES) {
    const remaining = CHAT_MIN_MODULES - modulesUsed.length;
    const MODULE_LIST = [
      { key: 'face_analysis', icon: '🔍', label: lang.startsWith('tr') ? 'Yüz Analizi'   : 'Face Analysis' },
      { key: 'astrology',     icon: '⭐', label: lang.startsWith('tr') ? 'Astroloji'      : 'Astrology'     },
      { key: 'twins',         icon: '👥', label: lang.startsWith('tr') ? 'İkizler'        : 'Twins'         },
      { key: 'art_match',     icon: '🎨', label: lang.startsWith('tr') ? 'Sanat Eşleşme'  : 'Art Match'     },
      { key: 'assessment',    icon: '📋', label: lang.startsWith('tr') ? 'Değerlendirme'  : 'Assessment'    },
      { key: 'fashion',       icon: '👗', label: lang.startsWith('tr') ? 'Moda'           : 'Fashion'       },
      { key: 'daily',         icon: '🌟', label: lang.startsWith('tr') ? 'Günlük Mesaj'   : 'Daily Message' },
    ];
    return (
      <View style={[gateStyles.container, { paddingTop: insets.top, paddingBottom: insets.bottom }]}>
        <TouchableOpacity style={gateStyles.backBtn} onPress={() => navigation.goBack()}>
          <Text style={gateStyles.backText}>←</Text>
        </TouchableOpacity>
        <Text style={gateStyles.lockIcon}>🔒</Text>
        <Text style={gateStyles.title}>
          {lang.startsWith('tr') ? 'AI Sohbet Kilitli' : 'AI Chat Locked'}
        </Text>
        <Text style={gateStyles.subtitle}>
          {lang.startsWith('tr')
            ? `Chat'i açmak için ${remaining} modül daha dene`
            : `Try ${remaining} more module${remaining > 1 ? 's' : ''} to unlock chat`}
        </Text>
        {/* İlerleme */}
        <View style={gateStyles.progressRow}>
          {Array.from({ length: CHAT_MIN_MODULES }).map((_, i) => (
            <View key={i} style={[gateStyles.progressDot, i < modulesUsed.length && gateStyles.progressDotDone]} />
          ))}
        </View>
        <Text style={gateStyles.progressLabel}>{modulesUsed.length} / {CHAT_MIN_MODULES}</Text>
        {/* Modül listesi */}
        <View style={gateStyles.moduleList}>
          {MODULE_LIST.map(m => {
            const done = modulesUsed.includes(m.key);
            return (
              <View key={m.key} style={[gateStyles.moduleRow, done && gateStyles.moduleRowDone]}>
                <Text style={gateStyles.moduleIcon}>{m.icon}</Text>
                <Text style={[gateStyles.moduleLabel, done && gateStyles.moduleLabelDone]}>{m.label}</Text>
                <Text style={gateStyles.moduleTick}>{done ? '✓' : ''}</Text>
              </View>
            );
          })}
        </View>
      </View>
    );
  }

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
            {chatUsage ? (
              <View style={styles.usagePill}>
                <View style={[styles.usageBar, { width: Math.round((chatUsage.used / chatUsage.limit) * 52) }]} />
                <Text style={styles.usageText}>{chatUsage.used}/{chatUsage.limit}</Text>
              </View>
            ) : (
              <View style={styles.onlinePill}>
                <View style={styles.onlineDot} />
                <Text style={styles.onlineText}>{t('chat.online', lang)}</Text>
              </View>
            )}
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
        renderItem={({ item }) => <MessageBubble item={item} onTestSubmit={sendMessage} />}
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

const tStyles = StyleSheet.create({
  card: {
    maxWidth: width * 0.82,
    backgroundColor: colors.aiBubble,
    borderWidth: 1,
    borderColor: colors.aiBubbleBorder,
    borderRadius: radius.lg,
    borderBottomLeftRadius: radius.xs,
    padding: 12,
    gap: 10,
  },
  legend: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    paddingBottom: 8,
    borderBottomWidth: 1,
    borderBottomColor: colors.border,
  },
  legendItem: { alignItems: 'center', flex: 1 },
  legendDot: {
    width: 24, height: 24, borderRadius: 12,
    backgroundColor: colors.warmAmberGlow,
    borderWidth: 1, borderColor: `${colors.warmAmber}50`,
    alignItems: 'center', justifyContent: 'center',
    marginBottom: 3,
  },
  legendNum: { fontSize: 11, fontWeight: '700', color: colors.gold },
  legendLabel: { fontSize: 8, color: colors.textMuted, textAlign: 'center' },
  qRow: { gap: 6 },
  qText: { fontSize: 13, color: colors.aiBubbleText, lineHeight: 18 },
  btnRow: { flexDirection: 'row', gap: 6, paddingLeft: 2 },
  optBtn: {
    width: 36, height: 36, borderRadius: 18,
    backgroundColor: colors.surface,
    borderWidth: 1.5, borderColor: colors.border,
    alignItems: 'center', justifyContent: 'center',
  },
  optBtnSel: {
    backgroundColor: colors.gold,
    borderColor: colors.gold,
  },
  optNum: { fontSize: 14, fontWeight: '600', color: colors.textMuted },
  optNumSel: { color: '#060F14' },
  submitBtn: {
    marginTop: 4,
    backgroundColor: colors.gold,
    borderRadius: radius.full,
    paddingVertical: 10,
    alignItems: 'center',
  },
  submitText: { fontSize: 13, fontWeight: '700', color: '#060F14' },
});

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
  usagePill: {
    flexDirection: 'row', alignItems: 'center', marginTop: 3,
    backgroundColor: 'rgba(255,255,255,0.07)', borderRadius: 8,
    paddingHorizontal: 6, paddingVertical: 2, gap: 5,
  },
  usageBar: { height: 3, borderRadius: 2, backgroundColor: colors.gold, maxWidth: 52 },
  usageText: { ...typography.caption, fontSize: 9, color: colors.textMuted },
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

const gateStyles = StyleSheet.create({
  container:      { flex: 1, backgroundColor: colors.background, alignItems: 'center', justifyContent: 'center', padding: spacing.xl },
  backBtn:        { position: 'absolute' as const, top: spacing.lg, left: spacing.lg, padding: spacing.sm },
  backText:       { ...typography.h2, color: colors.gold },
  lockIcon:       { fontSize: 64, marginBottom: spacing.md },
  title:          { ...typography.h1, color: colors.textPrimary, textAlign: 'center' as const, marginBottom: spacing.sm },
  subtitle:       { ...typography.body, color: colors.textMuted, textAlign: 'center' as const, marginBottom: spacing.lg },
  progressRow:    { flexDirection: 'row', gap: 12, marginBottom: spacing.xs },
  progressDot:    { width: 16, height: 16, borderRadius: 8, backgroundColor: colors.border },
  progressDotDone:{ backgroundColor: colors.gold },
  progressLabel:  { ...typography.caption, color: colors.gold, marginBottom: spacing.xl, fontWeight: '700' as const },
  moduleList:     { width: '100%', gap: spacing.sm },
  moduleRow:      {
    flexDirection: 'row' as const, alignItems: 'center', gap: spacing.md,
    padding: spacing.md, borderRadius: radius.md,
    backgroundColor: colors.surface, borderWidth: 1, borderColor: colors.border,
  },
  moduleRowDone:  { borderColor: colors.gold, backgroundColor: colors.goldGlow },
  moduleIcon:     { fontSize: 20, width: 28, textAlign: 'center' as const },
  moduleLabel:    { ...typography.body, color: colors.textMuted, flex: 1 },
  moduleLabelDone:{ color: colors.gold, fontWeight: '700' as const },
  moduleTick:     { ...typography.body, color: colors.gold, fontWeight: '700' as const },
});

export default ChatScreen;

// src/screens/DiscoveryGameScreen.tsx
import React, { useEffect, useState, useCallback } from 'react';
import {
  View, Text, StyleSheet, FlatList, TouchableOpacity,
  ActivityIndicator, StatusBar, Alert,
} from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { GamificationAPI, DiscoveryQuestion } from '../services/api';
import theme from '../utils/theme';
import { useLanguage } from '../utils/LanguageContext';
import { t } from '../utils/i18n';
import type { ScreenProps } from '../navigation/types';

const { colors, spacing, typography, radius, shadow } = theme;
type Props = ScreenProps<'DiscoveryGame'>;

type Phase = 'select' | 'playing' | 'result';

interface GameType {
  game_type_id: string;
  name: string;
  description: string;
  coin_reward_play: number;
  coin_reward_win: number;
}

interface GameResult {
  accuracy_percent: number;
  coins_earned: number;
  insights: string;
}

const DiscoveryGameScreen: React.FC<Props> = ({ navigation, route }) => {
  const insets = useSafeAreaInsets();
  const { lang } = useLanguage();
  const langCode = lang === 'tr' ? 'tr' : 'en';

  const [gameTypes, setGameTypes] = useState<GameType[]>([]);
  const [loading, setLoading] = useState(true);
  const [phase, setPhase] = useState<Phase>(route?.params?.gameType ? 'playing' : 'select');
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [question, setQuestion] = useState<DiscoveryQuestion | null>(null);
  const [totalQs, setTotalQs] = useState(0);
  const [qIndex, setQIndex] = useState(0);
  const [answering, setAnswering] = useState(false);
  const [result, setResult] = useState<GameResult | null>(null);
  const [lastCorrect, setLastCorrect] = useState<boolean | null>(null);

  const loadTypes = useCallback(async () => {
    setLoading(true);
    try {
      const res = await GamificationAPI.getGameTypes();
      setGameTypes(res.game_types);
      if (route?.params?.gameType) {
        startGame(route.params.gameType);
      }
    } catch {
      // keep stale
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { loadTypes(); }, []);

  const startGame = async (gameType: string) => {
    setLoading(true);
    try {
      const res = await GamificationAPI.startGame(gameType, 'normal', langCode);
      setSessionId(res.session_id);
      setQuestion(res.current_question ?? null);
      setTotalQs(res.total_questions);
      setQIndex(0);
      setPhase('playing');
      setLastCorrect(null);
      setResult(null);
    } catch (e: any) {
      Alert.alert(t('discovery.title', lang), e?.response?.data?.error || t('common.error', lang));
    } finally {
      setLoading(false);
    }
  };

  const answer = async (choiceIndex: number) => {
    if (!sessionId || !question) return;
    setAnswering(true);
    try {
      const res = await GamificationAPI.submitAnswer(sessionId, question.question_id, choiceIndex);
      setLastCorrect(res.correct);
      if (res.completed) {
        setResult({
          accuracy_percent: res.accuracy_percent ?? 0,
          coins_earned: res.coins_earned ?? 0,
          insights: (res as any).insights ?? '',
        });
        setPhase('result');
      } else if (res.next_question) {
        setQuestion(res.next_question);
        setQIndex(i => i + 1);
        setLastCorrect(null);
      }
    } catch (e: any) {
      Alert.alert(t('discovery.title', lang), e?.response?.data?.error || t('common.error', lang));
    } finally {
      setAnswering(false);
    }
  };

  const abandon = async () => {
    if (!sessionId) return;
    Alert.alert(
      t('discovery.abandon', lang),
      t('discovery.abandon_confirm', lang),
      [
        { text: t('common.cancel', lang), style: 'cancel' },
        {
          text: t('discovery.abandon', lang), style: 'destructive',
          onPress: async () => {
            try { await GamificationAPI.abandonGame(sessionId); } catch {}
            setPhase('select');
            setSessionId(null);
            setQuestion(null);
          },
        },
      ]
    );
  };

  const renderType = ({ item }: { item: GameType }) => (
    <TouchableOpacity style={styles.typeCard} onPress={() => startGame(item.game_type_id)} activeOpacity={0.85}
      accessibilityRole="button"
      accessibilityLabel={item.name}
    >
      <Text style={styles.typeEmoji}>🔍</Text>
      <View style={styles.typeBody}>
        <Text style={styles.typeName}>{item.name}</Text>
        <Text style={styles.typeDesc} numberOfLines={2}>{item.description}</Text>
        <Text style={styles.typeReward}>🪙 {item.coin_reward_win} {t('discovery.win_reward', lang)}</Text>
      </View>
    </TouchableOpacity>
  );

  const choices = question
    ? (langCode === 'tr' ? question.choices_tr : question.choices_en)
    : [];
  const questionText = question
    ? (langCode === 'tr' ? question.text_tr : question.text_en)
    : '';

  // Phase: result
  if (phase === 'result' && result) {
    return (
      <View style={styles.container}>
        <StatusBar barStyle="light-content" />
        <View style={[styles.topBar, { paddingTop: insets.top + spacing.md }]}>
          <TouchableOpacity onPress={() => setPhase('select')} style={styles.backBtn}
            accessibilityRole="button"
            accessibilityLabel={t('discovery.result', lang)}
          >
            <Text style={styles.backArrow}>←</Text>
          </TouchableOpacity>
          <Text style={styles.title}>{t('discovery.result', lang)}</Text>
        </View>
        <View style={styles.resultCard}>
          <Text style={styles.resultEmoji}>🎯</Text>
          <Text style={styles.resultAccuracy}>{result.accuracy_percent}%</Text>
          <Text style={styles.resultAccLabel}>{t('discovery.accuracy', lang)}</Text>
          <Text style={styles.resultCoins}>+{result.coins_earned} 🪙</Text>
          {result.insights ? <Text style={styles.resultInsights}>{result.insights}</Text> : null}
          <TouchableOpacity style={styles.playAgainBtn} onPress={() => setPhase('select')}
            accessibilityRole="button"
            accessibilityLabel={t('discovery.play_again', lang)}
          >
            <Text style={styles.playAgainText}>{t('discovery.play_again', lang)}</Text>
          </TouchableOpacity>
        </View>
      </View>
    );
  }

  // Phase: playing
  if (phase === 'playing' && question) {
    return (
      <View style={styles.container}>
        <StatusBar barStyle="light-content" />
        <View style={[styles.topBar, { paddingTop: insets.top + spacing.md }]}>
          <TouchableOpacity onPress={abandon} style={styles.backBtn}
            accessibilityRole="button"
            accessibilityLabel='qIndex + 1/totalQs'
          >
            <Text style={styles.backArrow}>←</Text>
          </TouchableOpacity>
          <Text style={styles.title}>{qIndex + 1}/{totalQs}</Text>
        </View>

        {/* Progress bar */}
        <View style={styles.progressBg}>
          <View style={[styles.progressFill, { width: `${((qIndex) / totalQs) * 100}%` as any }]} />
        </View>

        <View style={styles.qCard}>
          <Text style={styles.qText}>{questionText}</Text>
          {lastCorrect !== null && (
            <Text style={[styles.feedbackText, { color: lastCorrect ? '#7AE07A' : '#E07A7A' }]}>
              {lastCorrect ? `✓ ${t('meal_game.correct', lang)}` : `✗ ${t('meal_game.wrong', lang)}`}
            </Text>
          )}
        </View>

        <View style={styles.choiceList}>
          {choices.map((choice, idx) => (
            <TouchableOpacity
              accessibilityRole="button"
              accessibilityLabel='String.fromCharCode(65 + idx)'
              key={idx}
              style={styles.choiceBtn}
              onPress={() => answer(idx)}
              disabled={answering}
              activeOpacity={0.85}
            >
              <Text style={styles.choiceIndex}>{String.fromCharCode(65 + idx)}</Text>
              <Text style={styles.choiceText}>{choice}</Text>
            </TouchableOpacity>
          ))}
        </View>
        {answering && <ActivityIndicator color={colors.gold} style={{ marginTop: spacing.md }} />}
      </View>
    );
  }

  // Phase: select
  return (
    <View style={styles.container}>
      <StatusBar barStyle="light-content" />
      <FlatList
        data={gameTypes}
        keyExtractor={item => item.game_type_id}
        renderItem={renderType}
        contentContainerStyle={[styles.list, { paddingTop: insets.top + spacing.md }]}
        ListHeaderComponent={() => (
          <View style={styles.topBar}>
            <TouchableOpacity onPress={() => navigation.goBack()} style={styles.backBtn}
              accessibilityRole="button"
              accessibilityLabel={t('discovery.title', lang)}
            >
              <Text style={styles.backArrow}>←</Text>
            </TouchableOpacity>
            <Text style={styles.title}>{t('discovery.title', lang)}</Text>
          </View>
        )}
        ListEmptyComponent={() => loading
          ? <ActivityIndicator size="large" color={colors.gold} style={{ marginTop: 40 }} />
          : <Text style={styles.empty}>{t('discovery.select_type', lang)}</Text>
        }
      />
    </View>
  );
};

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: colors.background },
  topBar: { flexDirection: 'row', alignItems: 'center', paddingHorizontal: spacing.lg, marginBottom: spacing.md },
  backBtn: { marginRight: spacing.md, padding: 4 },
  backArrow: { fontSize: 22, color: colors.textPrimary },
  title: { ...typography.h2, flex: 1 },
  list: { paddingBottom: 40 },
  typeCard: {
    flexDirection: 'row', alignItems: 'center',
    backgroundColor: colors.surface, borderRadius: radius.lg ?? 16,
    padding: spacing.md, marginHorizontal: spacing.lg, marginBottom: spacing.sm,
    ...shadow.sm, borderWidth: 1, borderColor: `${colors.gold}20`,
  },
  typeEmoji: { fontSize: 32, marginRight: spacing.md },
  typeBody: { flex: 1 },
  typeName: { ...typography.body, color: colors.textPrimary, fontWeight: '700', marginBottom: 2 },
  typeDesc: { ...typography.caption, color: colors.textMuted, fontSize: 12, marginBottom: 4 },
  typeReward: { ...typography.caption, color: colors.gold, fontWeight: '700' },
  // Playing phase
  progressBg: { height: 4, backgroundColor: `${colors.border}40`, marginHorizontal: spacing.lg, borderRadius: 2, marginBottom: spacing.md },
  progressFill: { height: 4, backgroundColor: colors.gold, borderRadius: 2 },
  qCard: {
    margin: spacing.lg, backgroundColor: colors.surface, borderRadius: radius.lg ?? 16,
    padding: spacing.lg, ...shadow.sm, borderWidth: 1, borderColor: `${colors.gold}20`,
  },
  qText: { ...typography.body, color: colors.textPrimary, fontSize: 16, lineHeight: 24, fontWeight: '600' },
  feedbackText: { marginTop: spacing.sm, fontWeight: '700', fontSize: 14 },
  choiceList: { paddingHorizontal: spacing.lg, gap: spacing.sm },
  choiceBtn: {
    flexDirection: 'row', alignItems: 'center',
    backgroundColor: colors.surface, borderRadius: radius.md ?? 12,
    padding: spacing.md, ...shadow.sm,
  },
  choiceIndex: {
    width: 28, height: 28, borderRadius: 14,
    backgroundColor: `${colors.gold}20`, textAlign: 'center' as any,
    lineHeight: 28, color: colors.gold, fontWeight: '700', fontSize: 13,
    marginRight: spacing.sm,
  },
  choiceText: { ...typography.body, color: colors.textPrimary, flex: 1 },
  // Result phase
  resultCard: {
    margin: spacing.lg, backgroundColor: colors.surface, borderRadius: radius.xl ?? 20,
    padding: spacing.xl ?? 32, alignItems: 'center', ...shadow.sm,
    borderWidth: 1, borderColor: `${colors.gold}30`,
  },
  resultEmoji: { fontSize: 56, marginBottom: spacing.md },
  resultAccuracy: { fontSize: 48, fontWeight: '700', color: colors.gold },
  resultAccLabel: { ...typography.caption, color: colors.textMuted, marginBottom: spacing.sm },
  resultCoins: { fontSize: 22, fontWeight: '700', color: colors.gold, marginBottom: spacing.md },
  resultInsights: { ...typography.caption, color: colors.textMuted, textAlign: 'center' as any, marginBottom: spacing.lg },
  playAgainBtn: {
    backgroundColor: colors.gold, borderRadius: radius.md ?? 12,
    paddingHorizontal: spacing.xl ?? 32, paddingVertical: spacing.md,
  },
  playAgainText: { color: colors.background, fontWeight: '700', fontSize: 16 },
  empty: { ...typography.body, color: colors.textMuted, textAlign: 'center' as any, marginTop: 40 },
});

export default DiscoveryGameScreen;

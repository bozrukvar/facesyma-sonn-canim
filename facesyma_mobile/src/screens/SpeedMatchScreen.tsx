// src/screens/SpeedMatchScreen.tsx
import React, { useEffect, useState, useCallback, useRef } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  ActivityIndicator,
  StatusBar,
  Animated,
  FlatList,
} from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { GamificationAPI } from '../services/api';
import theme from '../utils/theme';
import { useLanguage } from '../utils/LanguageContext';
import { t } from '../utils/i18n';
import type { ScreenProps } from '../navigation/types';

const { colors, spacing, typography, radius, shadow } = theme;

type Props = ScreenProps<'SpeedMatch'>;

type Phase = 'ready' | 'playing' | 'result' | 'loading';

interface Question {
  index: number;
  feature: string;
  correct: string;
  options: string[];
}

interface AnswerRecord {
  correct: boolean;
}

interface GameResult {
  score: number;
  correct: number;
  total: number;
  accuracy: number;
  xp_earned: number;
}

interface LeaderboardEntry {
  rank: number;
  user_id: number;
  username: string;
  best_score: number;
  best_accuracy: number;
}

const DURATION_SECONDS = 30;
const FLASH_DURATION_MS = 350;

const SpeedMatchScreen: React.FC<Props> = ({ navigation }) => {
  const insets = useSafeAreaInsets();
  const { lang } = useLanguage();

  const [phase, setPhase] = useState<Phase>('ready');
  const [questions, setQuestions] = useState<Question[]>([]);
  const [currentIndex, setCurrentIndex] = useState(0);
  const [answers, setAnswers] = useState<AnswerRecord[]>([]);
  const [flashState, setFlashState] = useState<'none' | 'correct' | 'wrong'>('none');
  const [selectedOption, setSelectedOption] = useState<string | null>(null);
  const [result, setResult] = useState<GameResult | null>(null);
  const [leaderboard, setLeaderboard] = useState<LeaderboardEntry[]>([]);
  const [lbLoading, setLbLoading] = useState(false);
  const [showLeaderboard, setShowLeaderboard] = useState(false);
  const [submitting, setSubmitting] = useState(false);

  // Timer
  const [timeLeft, setTimeLeft] = useState(DURATION_SECONDS);
  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const startTimeRef = useRef<number>(0);
  const timerBarAnim = useRef(new Animated.Value(1)).current;
  const timerBarAnimRef = useRef<Animated.CompositeAnimation | null>(null);

  // Answer flash anim
  const flashAnim = useRef(new Animated.Value(0)).current;

  // Result entry anim
  const resultAnim = useRef(new Animated.Value(0)).current;

  const stopTimer = useCallback(() => {
    if (timerRef.current) {
      clearInterval(timerRef.current);
      timerRef.current = null;
    }
    if (timerBarAnimRef.current) {
      timerBarAnimRef.current.stop();
      timerBarAnimRef.current = null;
    }
  }, []);

  const finishGame = useCallback(async (finalAnswers: AnswerRecord[], forced = false) => {
    stopTimer();
    const timeMs = Date.now() - startTimeRef.current;
    setSubmitting(true);
    try {
      const res = await GamificationAPI.submitSpeedMatch(finalAnswers, timeMs);
      setResult(res);
      setPhase('result');
      Animated.spring(resultAnim, {
        toValue: 1,
        friction: 6,
        tension: 80,
        useNativeDriver: true,
      }).start();
    } catch {
      // fall back to local calculation
      const correct = finalAnswers.filter(a => a.correct).length;
      const total = finalAnswers.length;
      setResult({
        score: correct * 10,
        correct,
        total,
        accuracy: total > 0 ? Math.round((correct / total) * 100) : 0,
        xp_earned: 0,
      });
      setPhase('result');
    } finally {
      setSubmitting(false);
    }
  }, [stopTimer, resultAnim]);

  const startTimer = useCallback((durationSeconds: number) => {
    setTimeLeft(durationSeconds);
    timerBarAnim.setValue(1);

    timerBarAnimRef.current = Animated.timing(timerBarAnim, {
      toValue: 0,
      duration: durationSeconds * 1000,
      useNativeDriver: false,
    });
    timerBarAnimRef.current.start();

    timerRef.current = setInterval(() => {
      setTimeLeft(prev => {
        const next = prev - 1;
        if (next <= 0) {
          stopTimer();
          return 0;
        }
        return next;
      });
    }, 1000);
  }, [timerBarAnim, stopTimer]);

  // Watch timeLeft — end game when timer hits 0
  const answersRef = useRef<AnswerRecord[]>([]);
  answersRef.current = answers;
  const phaseRef = useRef<Phase>('ready');
  phaseRef.current = phase;

  useEffect(() => {
    if (timeLeft === 0 && phaseRef.current === 'playing') {
      finishGame(answersRef.current, true);
    }
  }, [timeLeft, finishGame]);

  // Cleanup on unmount
  useEffect(() => {
    return () => stopTimer();
  }, [stopTimer]);

  const startGame = useCallback(async () => {
    setPhase('loading');
    setAnswers([]);
    setCurrentIndex(0);
    setResult(null);
    setShowLeaderboard(false);
    setSelectedOption(null);
    setFlashState('none');
    try {
      const res = await GamificationAPI.startSpeedMatch();
      setQuestions(res.questions);
      startTimeRef.current = Date.now();
      const duration = res.duration_seconds ?? DURATION_SECONDS;
      setPhase('playing');
      startTimer(duration);
    } catch {
      setPhase('ready');
    }
  }, [startTimer]);

  const loadLeaderboard = useCallback(async () => {
    setLbLoading(true);
    try {
      const res = await GamificationAPI.getSpeedMatchLeaderboard();
      setLeaderboard(res.entries);
    } catch {
      // keep stale
    } finally {
      setLbLoading(false);
    }
  }, []);

  const animateFlash = useCallback((isCorrect: boolean, callback: () => void) => {
    flashAnim.setValue(0);
    Animated.sequence([
      Animated.timing(flashAnim, { toValue: 1, duration: FLASH_DURATION_MS / 2, useNativeDriver: true }),
      Animated.timing(flashAnim, { toValue: 0, duration: FLASH_DURATION_MS / 2, useNativeDriver: true }),
    ]).start(() => callback());
  }, [flashAnim]);

  const handleAnswer = useCallback((option: string) => {
    if (flashState !== 'none' || phase !== 'playing') return;
    const currentQ = questions[currentIndex];
    if (!currentQ) return;

    const isCorrect = option === currentQ.correct;
    const newRecord: AnswerRecord = { correct: isCorrect };
    const newAnswers = [...answersRef.current, newRecord];

    setSelectedOption(option);
    setFlashState(isCorrect ? 'correct' : 'wrong');

    animateFlash(isCorrect, () => {
      setSelectedOption(null);
      setFlashState('none');
      setAnswers(newAnswers);

      const nextIndex = currentIndex + 1;
      if (nextIndex >= questions.length) {
        finishGame(newAnswers);
      } else {
        setCurrentIndex(nextIndex);
      }
    });
  }, [flashState, phase, questions, currentIndex, animateFlash, finishGame]);

  // Timer bar color interpolation
  const timerBarColor = timerBarAnim.interpolate({
    inputRange: [0, 0.3, 0.6, 1],
    outputRange: ['#D95F5F', '#E8A830', '#E8A830', '#3DBF8A'],
  });

  const renderLeaderboardEntry = ({ item }: { item: LeaderboardEntry }) => (
    <View style={styles.lbRow}>
      <View style={[
        styles.lbRank,
        item.rank === 1 && styles.lbRank1,
        item.rank === 2 && styles.lbRank2,
        item.rank === 3 && styles.lbRank3,
      ]}>
        <Text style={[styles.lbRankText, item.rank <= 3 && styles.lbRankTextTop]}>
          {item.rank <= 3 ? ['🥇', '🥈', '🥉'][item.rank - 1] : `#${item.rank}`}
        </Text>
      </View>
      <Text style={styles.lbUsername} numberOfLines={1}>{item.username}</Text>
      <View style={styles.lbStats}>
        <Text style={styles.lbScore}>{item.best_score}</Text>
        <Text style={styles.lbAccuracy}>{Math.round(item.best_accuracy)}%</Text>
      </View>
    </View>
  );

  // ── Phase: ready ───────────────────────────────────────────────────────────
  if (phase === 'ready') {
    return (
      <View style={styles.container}>
        <StatusBar barStyle="light-content" />
        <View style={[styles.readyWrapper, { paddingTop: insets.top + spacing.md }]}>
          {/* Back */}
          <TouchableOpacity onPress={() => navigation.goBack()} style={styles.backBtnAbs}
            accessibilityRole="button"
            accessibilityLabel={t('speed_match.title', lang)}
          >
            <Text style={styles.backArrow}>←</Text>
          </TouchableOpacity>

          {/* Hero content */}
          <View style={styles.readyHero}>
            <Text style={styles.readyEmoji}>⚡</Text>
            <Text style={styles.readyTitle}>{t('speed_match.title', lang)}</Text>
            <Text style={styles.readyDesc}>{t('speed_match.desc', lang)}</Text>

            <View style={styles.readyInfoRow}>
              <View style={styles.readyInfoChip}>
                <Text style={styles.readyInfoChipEmoji}>⏱</Text>
                <Text style={styles.readyInfoChipText}>{DURATION_SECONDS}s</Text>
              </View>
              <View style={styles.readyInfoChip}>
                <Text style={styles.readyInfoChipEmoji}>🎯</Text>
                <Text style={styles.readyInfoChipText}>10 Q</Text>
              </View>
              <View style={styles.readyInfoChip}>
                <Text style={styles.readyInfoChipEmoji}>✨</Text>
                <Text style={styles.readyInfoChipText}>+Coins</Text>
              </View>
            </View>

            <TouchableOpacity style={styles.startBtn} onPress={startGame} activeOpacity={0.85}
              accessibilityRole="button"
              accessibilityLabel={t('speed_match.start', lang)}
            >
              <Text style={styles.startBtnText}>{t('speed_match.start', lang)}</Text>
            </TouchableOpacity>
          </View>
        </View>
      </View>
    );
  }

  // ── Phase: loading ─────────────────────────────────────────────────────────
  if (phase === 'loading') {
    return (
      <View style={styles.center}>
        <ActivityIndicator size="large" color={colors.gold} />
      </View>
    );
  }

  // ── Phase: playing ─────────────────────────────────────────────────────────
  if (phase === 'playing') {
    const currentQ = questions[currentIndex];
    const total = questions.length;
    const progressPct = total > 0 ? ((currentIndex) / total) * 100 : 0;

    if (!currentQ) {
      return (
        <View style={styles.center}>
          <ActivityIndicator size="large" color={colors.gold} />
        </View>
      );
    }

    return (
      <View style={[styles.container, { paddingTop: insets.top }]}>
        <StatusBar barStyle="light-content" />

        {/* Timer bar */}
        <View style={styles.timerBarBg}>
          <Animated.View
            style={[
              styles.timerBarFill,
              {
                width: timerBarAnim.interpolate({
                  inputRange: [0, 1],
                  outputRange: ['0%', '100%'],
                }),
                backgroundColor: timerBarColor,
              },
            ]}
          />
        </View>

        {/* Timer + question counter row */}
        <View style={styles.playingHeader}>
          <TouchableOpacity
            accessibilityRole="button"
            accessibilityLabel='currentIndex + 1/total'
            onPress={() => { stopTimer(); setPhase('ready'); }}
            style={styles.playingBackBtn}
            hitSlop={{ top: 8, bottom: 8, left: 8, right: 8 }}
          >
            <Text style={styles.backArrow}>←</Text>
          </TouchableOpacity>
          <View style={styles.timerChip}>
            <Text style={[
              styles.timerText,
              timeLeft <= 5 && styles.timerTextUrgent,
            ]}>
              {timeLeft}s
            </Text>
          </View>
          <Text style={styles.questionCounter}>
            {currentIndex + 1}/{total}
          </Text>
          <View style={styles.progressBarBg}>
            <View style={[styles.progressBarFill, { width: `${progressPct}%` as any }]} />
          </View>
        </View>

        {/* Question card */}
        <View style={styles.questionCard}>
          <Text style={styles.featureLabel}>{t('speed_match.feature', lang)}</Text>
          <Text style={styles.featureText}>{currentQ.feature}</Text>
        </View>

        {/* 2x2 option grid */}
        <View style={styles.optionGrid}>
          {currentQ.options.map((option) => {
            const isSelected = selectedOption === option;
            const isCorrectFlash = isSelected && flashState === 'correct';
            const isWrongFlash = isSelected && flashState === 'wrong';

            return (
              <Animated.View
                key={option}
                style={[
                  styles.optionCellWrap,
                  isSelected && {
                    opacity: flashAnim.interpolate({
                      inputRange: [0, 0.5, 1],
                      outputRange: [1, 0.85, 1],
                    }),
                  },
                ]}
              >
                <TouchableOpacity
                  accessibilityRole="button"
                  accessibilityLabel={option}
                  style={[
                    styles.optionCell,
                    isCorrectFlash && styles.optionCellCorrect,
                    isWrongFlash && styles.optionCellWrong,
                  ]}
                  onPress={() => handleAnswer(option)}
                  activeOpacity={0.75}
                  disabled={flashState !== 'none'}
                >
                  <Text style={[
                    styles.optionCellText,
                    isCorrectFlash && styles.optionCellTextCorrect,
                    isWrongFlash && styles.optionCellTextWrong,
                  ]}>
                    {option}
                  </Text>
                  {isCorrectFlash && <Text style={styles.flashIcon}>✓</Text>}
                  {isWrongFlash && <Text style={styles.flashIconWrong}>✗</Text>}
                </TouchableOpacity>
              </Animated.View>
            );
          })}
        </View>

        {submitting && (
          <View style={styles.submittingOverlay}>
            <ActivityIndicator size="large" color={colors.gold} />
          </View>
        )}
      </View>
    );
  }

  // ── Phase: result ──────────────────────────────────────────────────────────
  if (phase === 'result' && result) {
    const resultScale = resultAnim.interpolate({
      inputRange: [0, 0.6, 1],
      outputRange: [0.7, 1.05, 1],
    });
    const resultOpacity = resultAnim;

    const accuracyColor =
      result.accuracy >= 80
        ? '#3DBF8A'
        : result.accuracy >= 50
        ? '#E8A830'
        : '#D95F5F';

    return (
      <View style={styles.container}>
        <StatusBar barStyle="light-content" />
        <ScrollView
          showsVerticalScrollIndicator={false}
          contentContainerStyle={[styles.resultScroll, { paddingTop: insets.top + spacing.sm }]}
        >
          {/* Back */}
          <View style={styles.resultHeader}>
            <TouchableOpacity onPress={() => navigation.goBack()} style={styles.backBtn}
              accessibilityRole="button"
              accessibilityLabel={t('speed_match.title', lang)}
            >
              <Text style={styles.backArrow}>←</Text>
            </TouchableOpacity>
            <Text style={styles.resultScreenTitle}>{t('speed_match.title', lang)}</Text>
          </View>

          {/* Result card */}
          <Animated.View
            style={[
              styles.resultCard,
              { transform: [{ scale: resultScale }], opacity: resultOpacity },
            ]}
          >
            <Text style={styles.resultEmoji}>
              {result.accuracy >= 80 ? '🏆' : result.accuracy >= 50 ? '🎯' : '💪'}
            </Text>

            {/* Score */}
            <Text style={styles.scoreValue}>{result.score}</Text>
            <Text style={styles.scoreLabel}>{t('speed_match.score', lang)}</Text>

            {/* Stats row */}
            <View style={styles.statsRow}>
              <View style={styles.statItem}>
                <Text style={styles.statValue}>{result.correct}/{result.total}</Text>
                <Text style={styles.statLabel}>{t('speed_match.correct', lang)}</Text>
              </View>
              <View style={styles.statDivider} />
              <View style={styles.statItem}>
                <Text style={[styles.statValue, { color: accuracyColor }]}>
                  {Math.round(result.accuracy)}%
                </Text>
                <Text style={styles.statLabel}>{t('speed_match.accuracy', lang)}</Text>
              </View>
            </View>

            {/* Coins earned */}
            {result.xp_earned > 0 && (
              <View style={styles.coinsEarnedBadge}>
                <Text style={styles.coinsEarnedText}>+{result.xp_earned} ✨ XP</Text>
              </View>
            )}
          </Animated.View>

          {/* Action buttons */}
          <View style={styles.actionRow}>
            <TouchableOpacity style={styles.playAgainBtn} onPress={startGame} activeOpacity={0.85}
              accessibilityRole="button"
              accessibilityLabel={t('speed_match.play_again', lang)}
            >
              <Text style={styles.playAgainText}>{t('speed_match.play_again', lang)}</Text>
            </TouchableOpacity>
            <TouchableOpacity
              accessibilityRole="button"
              accessibilityLabel={t('speed_match.leaderboard', lang)}
              style={styles.lbBtn}
              onPress={() => {
                if (!showLeaderboard) loadLeaderboard();
                setShowLeaderboard(v => !v);
              }}
              activeOpacity={0.85}
            >
              <Text style={styles.lbBtnText}>
                {showLeaderboard ? '▲' : '▼'} {t('speed_match.leaderboard', lang)}
              </Text>
            </TouchableOpacity>
          </View>

          {/* Mini leaderboard */}
          {showLeaderboard && (
            <View style={styles.lbSection}>
              <Text style={styles.sectionLabel}>{t('speed_match.leaderboard', lang)}</Text>
              {lbLoading ? (
                <ActivityIndicator color={colors.gold} style={{ marginVertical: spacing.md }} />
              ) : leaderboard.length === 0 ? (
                <Text style={styles.lbEmpty}>{t('leaderboard.empty', lang)}</Text>
              ) : (
                <FlatList
                  data={leaderboard}
                  keyExtractor={(item) => `${item.user_id}`}
                  renderItem={renderLeaderboardEntry}
                  scrollEnabled={false}
                  ItemSeparatorComponent={() => <View style={styles.lbSeparator} />}
                />
              )}
            </View>
          )}

          <View style={{ height: spacing.xl }} />
        </ScrollView>
      </View>
    );
  }

  return null;
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: colors.background,
  },
  center: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: colors.background,
  },

  // ── Ready phase ──────────────────────────────────────────────────────────
  readyWrapper: {
    flex: 1,
    paddingHorizontal: spacing.lg,
  },
  backBtnAbs: {
    padding: 4,
    alignSelf: 'flex-start',
    marginBottom: spacing.sm,
  },
  backArrow: {
    fontSize: 22,
    color: colors.textPrimary,
  },
  readyHero: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    gap: spacing.md,
  },
  readyEmoji: {
    fontSize: 64,
    marginBottom: spacing.sm,
  },
  readyTitle: {
    ...typography.h2,
    textAlign: 'center',
    fontSize: 24,
  },
  readyDesc: {
    ...typography.body,
    color: colors.textSecondary,
    textAlign: 'center',
    lineHeight: 24,
    paddingHorizontal: spacing.md,
  },
  readyInfoRow: {
    flexDirection: 'row',
    gap: spacing.sm,
    marginTop: spacing.sm,
  },
  readyInfoChip: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
    backgroundColor: colors.surface,
    borderRadius: radius.full,
    paddingHorizontal: spacing.md,
    paddingVertical: spacing.xs,
    borderWidth: 1,
    borderColor: `${colors.gold}25`,
  },
  readyInfoChipEmoji: {
    fontSize: 14,
  },
  readyInfoChipText: {
    ...typography.label,
    fontSize: 12,
    color: colors.textPrimary,
  },
  startBtn: {
    backgroundColor: colors.gold,
    borderRadius: radius.lg,
    paddingHorizontal: spacing.xl,
    paddingVertical: spacing.md,
    marginTop: spacing.lg,
    ...shadow.gold,
    minWidth: 180,
    alignItems: 'center',
  },
  startBtnText: {
    color: colors.background,
    fontWeight: '700',
    fontSize: 18,
    letterSpacing: 0.5,
  },

  // ── Playing phase ─────────────────────────────────────────────────────────
  timerBarBg: {
    height: 5,
    backgroundColor: colors.border,
    marginBottom: 0,
  },
  timerBarFill: {
    height: 5,
    borderRadius: 0,
  },
  playingHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: spacing.lg,
    paddingVertical: spacing.sm,
    gap: spacing.sm,
  },
  playingBackBtn: {
    padding: 4,
    marginRight: 2,
  },
  timerChip: {
    backgroundColor: colors.surface,
    borderRadius: radius.sm,
    paddingHorizontal: spacing.sm,
    paddingVertical: 4,
    borderWidth: 1,
    borderColor: colors.border,
    minWidth: 44,
    alignItems: 'center',
  },
  timerText: {
    ...typography.label,
    color: colors.textPrimary,
    fontSize: 15,
    fontWeight: '700',
  },
  timerTextUrgent: {
    color: '#D95F5F',
  },
  questionCounter: {
    ...typography.body,
    color: colors.textSecondary,
    fontWeight: '600',
    fontSize: 14,
    minWidth: 36,
    textAlign: 'center',
  },
  progressBarBg: {
    flex: 1,
    height: 4,
    backgroundColor: colors.border,
    borderRadius: 2,
  },
  progressBarFill: {
    height: 4,
    backgroundColor: colors.gold,
    borderRadius: 2,
  },
  questionCard: {
    marginHorizontal: spacing.lg,
    marginTop: spacing.sm,
    marginBottom: spacing.lg,
    backgroundColor: colors.surface,
    borderRadius: radius.lg,
    padding: spacing.lg,
    borderWidth: 1,
    borderColor: `${colors.gold}30`,
    ...shadow.sm,
    minHeight: 110,
    justifyContent: 'center',
  },
  featureLabel: {
    ...typography.goldLabel,
    marginBottom: spacing.sm,
  },
  featureText: {
    ...typography.body,
    color: colors.textPrimary,
    fontSize: 17,
    fontWeight: '600',
    lineHeight: 26,
  },
  optionGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    paddingHorizontal: spacing.lg,
    gap: spacing.sm,
  },
  optionCellWrap: {
    width: '48%',
    // flexBasis for a 2-column grid with gap
  },
  optionCell: {
    backgroundColor: colors.surface,
    borderRadius: radius.md,
    padding: spacing.md,
    alignItems: 'center',
    justifyContent: 'center',
    borderWidth: 1,
    borderColor: `${colors.gold}20`,
    minHeight: 70,
    ...shadow.sm,
  },
  optionCellCorrect: {
    backgroundColor: `${'#3DBF8A'}20`,
    borderColor: '#3DBF8A',
  },
  optionCellWrong: {
    backgroundColor: `${'#D95F5F'}18`,
    borderColor: '#D95F5F',
  },
  optionCellText: {
    ...typography.body,
    color: colors.textPrimary,
    fontWeight: '600',
    textAlign: 'center',
    fontSize: 14,
  },
  optionCellTextCorrect: {
    color: '#3DBF8A',
  },
  optionCellTextWrong: {
    color: '#D95F5F',
  },
  flashIcon: {
    fontSize: 18,
    color: '#3DBF8A',
    marginTop: 4,
    fontWeight: '700',
  },
  flashIconWrong: {
    fontSize: 18,
    color: '#D95F5F',
    marginTop: 4,
    fontWeight: '700',
  },
  submittingOverlay: {
    position: 'absolute',
    top: 0,
    left: 0,
    right: 0,
    bottom: 0,
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: `${colors.background}AA`,
  },

  // ── Result phase ──────────────────────────────────────────────────────────
  resultScroll: {
    paddingHorizontal: spacing.lg,
    paddingBottom: spacing.xl,
  },
  resultHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: spacing.lg,
    gap: spacing.sm,
  },
  backBtn: {
    padding: 4,
    marginRight: spacing.xs,
  },
  resultScreenTitle: {
    ...typography.h2,
    flex: 1,
  },
  resultCard: {
    backgroundColor: colors.surface,
    borderRadius: radius.xl,
    padding: spacing.xl,
    alignItems: 'center',
    borderWidth: 1,
    borderColor: `${colors.gold}30`,
    ...shadow.gold,
    marginBottom: spacing.lg,
  },
  resultEmoji: {
    fontSize: 52,
    marginBottom: spacing.sm,
  },
  scoreValue: {
    fontSize: 56,
    fontWeight: '700',
    color: colors.gold,
    lineHeight: 64,
  },
  scoreLabel: {
    ...typography.caption,
    color: colors.textMuted,
    marginBottom: spacing.md,
    letterSpacing: 1.5,
  },
  statsRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: spacing.lg,
    marginBottom: spacing.md,
  },
  statItem: {
    alignItems: 'center',
    gap: 2,
  },
  statValue: {
    ...typography.h3,
    color: colors.textPrimary,
    fontSize: 20,
    fontWeight: '700',
  },
  statLabel: {
    ...typography.caption,
    color: colors.textMuted,
    fontSize: 11,
    letterSpacing: 0.8,
  },
  statDivider: {
    width: 1,
    height: 36,
    backgroundColor: colors.border,
  },
  coinsEarnedBadge: {
    backgroundColor: `${colors.gold}20`,
    borderRadius: radius.full,
    paddingHorizontal: spacing.md,
    paddingVertical: spacing.xs,
    borderWidth: 1,
    borderColor: `${colors.gold}45`,
    marginTop: spacing.xs,
  },
  coinsEarnedText: {
    ...typography.label,
    color: colors.gold,
    fontSize: 15,
  },

  // Action buttons
  actionRow: {
    flexDirection: 'row',
    gap: spacing.sm,
    marginBottom: spacing.lg,
  },
  playAgainBtn: {
    flex: 1,
    backgroundColor: colors.gold,
    borderRadius: radius.md,
    paddingVertical: spacing.md,
    alignItems: 'center',
    ...shadow.gold,
  },
  playAgainText: {
    color: colors.background,
    fontWeight: '700',
    fontSize: 15,
  },
  lbBtn: {
    flex: 1,
    backgroundColor: colors.surface,
    borderRadius: radius.md,
    paddingVertical: spacing.md,
    alignItems: 'center',
    borderWidth: 1,
    borderColor: `${colors.gold}30`,
  },
  lbBtnText: {
    ...typography.label,
    color: colors.gold,
    fontSize: 13,
  },

  // Leaderboard
  sectionLabel: {
    ...typography.goldLabel,
    marginBottom: spacing.sm,
  },
  lbSection: {
    marginBottom: spacing.lg,
  },
  lbRow: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: colors.surface,
    borderRadius: radius.md,
    padding: spacing.md,
    gap: spacing.sm,
  },
  lbRank: {
    width: 36,
    height: 36,
    borderRadius: 18,
    backgroundColor: colors.border,
    alignItems: 'center',
    justifyContent: 'center',
    flexShrink: 0,
  },
  lbRank1: { backgroundColor: `${'#F5C842'}18` },
  lbRank2: { backgroundColor: `${'#C0C0C0'}18` },
  lbRank3: { backgroundColor: `${'#CD7F32'}18` },
  lbRankText: {
    ...typography.caption,
    color: colors.textMuted,
    fontWeight: '700',
    fontSize: 11,
  },
  lbRankTextTop: {
    fontSize: 16,
  },
  lbUsername: {
    ...typography.body,
    color: colors.textPrimary,
    fontWeight: '600',
    flex: 1,
  },
  lbStats: {
    alignItems: 'flex-end',
    gap: 2,
  },
  lbScore: {
    ...typography.label,
    color: colors.gold,
    fontSize: 13,
    fontWeight: '700',
  },
  lbAccuracy: {
    ...typography.caption,
    color: colors.textMuted,
    fontSize: 11,
  },
  lbSeparator: {
    height: spacing.xs,
  },
  lbEmpty: {
    ...typography.body,
    color: colors.textMuted,
    textAlign: 'center',
    marginVertical: spacing.md,
  },
});

export default SpeedMatchScreen;

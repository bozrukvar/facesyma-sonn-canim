// src/screens/WordleScreen.tsx
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

type Props = ScreenProps<'Wordle'>;

type GameState = 'loading' | 'playing' | 'won' | 'lost' | 'error';

interface DailyData {
  date: string;
  hints: string[];
  total_hints: number;
  attempts_used: number;
  max_attempts: number;
  won: boolean;
  options: string[];
  correct_sifat: string | null;
  emoji: string;
  xp_if_win: number;
}

interface LeaderboardEntry {
  rank: number;
  user_id: number;
  username: string;
  attempts: number;
}

const WordleScreen: React.FC<Props> = ({ navigation }) => {
  const insets = useSafeAreaInsets();
  const { lang } = useLanguage();

  const [gameState, setGameState] = useState<GameState>('loading');
  const [daily, setDaily] = useState<DailyData | null>(null);
  const [visibleHints, setVisibleHints] = useState<string[]>([]);
  const [attemptsUsed, setAttemptsUsed] = useState(0);
  const [maxAttempts, setMaxAttempts] = useState(6);
  const [options, setOptions] = useState<string[]>([]);
  const [wrongAnswer, setWrongAnswer] = useState<string | null>(null);
  const [xpEarned, setXpEarned] = useState(0);
  const [correctSifat, setCorrectSifat] = useState<string | null>(null);
  const [guessing, setGuessing] = useState(false);
  const [leaderboard, setLeaderboard] = useState<LeaderboardEntry[]>([]);
  const [lbLoading, setLbLoading] = useState(false);

  const wrongAnim = useRef(new Animated.Value(0)).current;
  const winAnim = useRef(new Animated.Value(0)).current;
  const hintAnims = useRef<Animated.Value[]>([]).current;

  const animateWrong = useCallback(() => {
    wrongAnim.setValue(0);
    Animated.sequence([
      Animated.timing(wrongAnim, { toValue: 1, duration: 200, useNativeDriver: true }),
      Animated.timing(wrongAnim, { toValue: 0, duration: 800, useNativeDriver: true }),
    ]).start();
  }, [wrongAnim]);

  const animateWin = useCallback(() => {
    winAnim.setValue(0);
    Animated.spring(winAnim, {
      toValue: 1,
      friction: 5,
      tension: 80,
      useNativeDriver: true,
    }).start();
  }, [winAnim]);

  const animateHint = useCallback((index: number) => {
    if (!hintAnims[index]) {
      hintAnims[index] = new Animated.Value(0);
    }
    Animated.spring(hintAnims[index], {
      toValue: 1,
      friction: 6,
      tension: 100,
      useNativeDriver: true,
    }).start();
  }, [hintAnims]);

  const loadDaily = useCallback(async () => {
    setGameState('loading');
    try {
      const data = await GamificationAPI.getWordleDaily();
      setDaily(data);
      setAttemptsUsed(data.attempts_used);
      setMaxAttempts(data.max_attempts);
      setOptions(data.options);

      const shownHints = data.hints.slice(0, Math.max(1, data.attempts_used));
      shownHints.forEach((_, i) => {
        if (!hintAnims[i]) hintAnims[i] = new Animated.Value(1);
      });
      setVisibleHints(shownHints);

      if (data.won) {
        setGameState('won');
        animateWin();
      } else if (data.attempts_used >= data.max_attempts && data.correct_sifat) {
        setCorrectSifat(data.correct_sifat);
        setGameState('lost');
      } else {
        setGameState('playing');
      }
    } catch {
      setGameState('error');
    }
  }, [animateWin, hintAnims]);

  const loadLeaderboard = useCallback(async () => {
    setLbLoading(true);
    try {
      const res = await GamificationAPI.getWordleLeaderboard();
      setLeaderboard(res.entries);
    } catch {
      // keep stale
    } finally {
      setLbLoading(false);
    }
  }, []);

  useEffect(() => {
    loadDaily();
  }, [loadDaily]);

  useEffect(() => {
    if (gameState === 'won' || gameState === 'lost') {
      loadLeaderboard();
    }
  }, [gameState, loadLeaderboard]);

  const handleGuess = useCallback(async (guess: string) => {
    if (guessing || gameState !== 'playing') return;
    setGuessing(true);
    setWrongAnswer(null);
    try {
      const res = await GamificationAPI.guessWordle(guess);
      setAttemptsUsed(res.attempts_used);

      if (res.correct) {
        setXpEarned(res.xp_earned);
        setGameState('won');
        animateWin();
      } else {
        // Reveal wrong answer briefly
        setWrongAnswer(guess);
        animateWrong();

        // Reveal next hint if available
        if (res.next_hint) {
          const newIndex = visibleHints.length;
          if (!hintAnims[newIndex]) hintAnims[newIndex] = new Animated.Value(0);
          setVisibleHints(prev => [...prev, res.next_hint!]);
          setTimeout(() => animateHint(newIndex), 100);
        }

        if (res.game_over) {
          setCorrectSifat(res.correct_sifat);
          setGameState('lost');
        }

        // Clear wrong answer highlight after 1.5s
        setTimeout(() => setWrongAnswer(null), 1500);
      }
    } catch {
      // silently ignore
    } finally {
      setGuessing(false);
    }
  }, [guessing, gameState, visibleHints, hintAnims, animateWin, animateWrong, animateHint]);

  const renderLeaderboardEntry = ({ item }: { item: LeaderboardEntry }) => (
    <View style={styles.lbRow}>
      <View style={[
        styles.lbRank,
        item.rank === 1 && styles.lbRank1,
        item.rank === 2 && styles.lbRank2,
        item.rank === 3 && styles.lbRank3,
      ]}>
        <Text style={[
          styles.lbRankText,
          item.rank <= 3 && styles.lbRankTextTop,
        ]}>
          {item.rank <= 3 ? ['🥇', '🥈', '🥉'][item.rank - 1] : `#${item.rank}`}
        </Text>
      </View>
      <Text style={styles.lbUsername} numberOfLines={1}>{item.username}</Text>
      <Text style={styles.lbAttempts}>
        {item.attempts} {t('wordle.attempts', lang)}
      </Text>
    </View>
  );

  if (gameState === 'loading') {
    return (
      <View style={styles.center}>
        <ActivityIndicator size="large" color={colors.gold} />
        <Text style={styles.loadingText}>{t('wordle.loading', lang)}</Text>
      </View>
    );
  }

  if (gameState === 'error') {
    return (
      <View style={styles.center}>
        <Text style={styles.errorEmoji}>⚠️</Text>
        <Text style={styles.errorText}>{t('common.error', lang)}</Text>
        <TouchableOpacity style={styles.retryBtn} onPress={loadDaily}
          accessibilityRole="button"
          accessibilityLabel={t('common.retry', lang)}
        >
          <Text style={styles.retryText}>{t('common.retry', lang)}</Text>
        </TouchableOpacity>
      </View>
    );
  }

  const xpIfWin = daily?.xp_if_win ?? 0;
  const emoji = daily?.emoji ?? '🎯';
  const totalHints = daily?.total_hints ?? maxAttempts;

  const winScale = winAnim.interpolate({
    inputRange: [0, 0.5, 1],
    outputRange: [0.5, 1.1, 1],
  });

  return (
    <View style={styles.container}>
      <StatusBar barStyle="light-content" />
      <ScrollView
        showsVerticalScrollIndicator={false}
        contentContainerStyle={[styles.scroll, { paddingTop: insets.top + spacing.sm }]}
        keyboardShouldPersistTaps="handled"
      >
        {/* Header */}
        <View style={styles.header}>
          <TouchableOpacity onPress={() => navigation.goBack()} style={styles.backBtn}
            accessibilityRole="button"
            accessibilityLabel={emoji}
          >
            <Text style={styles.backArrow}>←</Text>
          </TouchableOpacity>
          <View style={styles.headerCenter}>
            <Text style={styles.headerEmoji}>{emoji}</Text>
            <Text style={styles.title}>{t('wordle.title', lang)}</Text>
          </View>
          <View style={styles.coinsChip}>
            <Text style={styles.coinsChipText}>✨ {xpIfWin} XP</Text>
          </View>
        </View>

        {/* Attempts indicator */}
        <View style={styles.attemptsRow}>
          {Array.from({ length: maxAttempts }).map((_, i) => (
            <View
              key={i}
              style={[
                styles.attemptDot,
                i < attemptsUsed
                  ? (gameState === 'won' ? styles.attemptDotWon : styles.attemptDotUsed)
                  : styles.attemptDotEmpty,
              ]}
            />
          ))}
          <Text style={styles.attemptsLabel}>
            {attemptsUsed}/{maxAttempts} {t('wordle.attempts', lang)}
          </Text>
        </View>

        {/* Hint cards */}
        <View style={styles.hintsSection}>
          <Text style={styles.sectionLabel}>{t('wordle.hint', lang)}</Text>
          {visibleHints.length === 0 && gameState === 'playing' && (
            <View style={styles.hintCard}>
              <Text style={styles.hintNumber}>1</Text>
              <Text style={styles.hintText}>{t('wordle.select_option', lang)}</Text>
            </View>
          )}
          {visibleHints.map((hint, index) => {
            if (!hintAnims[index]) hintAnims[index] = new Animated.Value(1);
            const anim = hintAnims[index];
            const scale = anim.interpolate({ inputRange: [0, 1], outputRange: [0.85, 1] });
            const opacity = anim;
            return (
              <Animated.View
                key={index}
                style={[styles.hintCard, { transform: [{ scale }], opacity }]}
              >
                <View style={styles.hintNumberBadge}>
                  <Text style={styles.hintNumberText}>{index + 1}</Text>
                </View>
                <Text style={styles.hintText}>{hint}</Text>
              </Animated.View>
            );
          })}
          {visibleHints.length > 0 && visibleHints.length < totalHints && gameState === 'playing' && (
            <View style={styles.hiddenHintCard}>
              <Text style={styles.hiddenHintText}>
                {totalHints - visibleHints.length} {t('wordle.next_hint', lang)}
              </Text>
            </View>
          )}
        </View>

        {/* Win state */}
        {gameState === 'won' && (
          <Animated.View style={[styles.resultCard, styles.wonCard, { transform: [{ scale: winScale }] }]}>
            <Text style={styles.resultEmoji}>🎉</Text>
            <Text style={styles.resultTitle}>{t('wordle.won', lang)}</Text>
            <Text style={styles.resultSubtitle}>
              {attemptsUsed} {t('wordle.attempts', lang)}
            </Text>
            {xpEarned > 0 && (
              <View style={styles.coinsEarnedBadge}>
                <Text style={styles.coinsEarnedText}>+{xpEarned} ✨ XP</Text>
              </View>
            )}
          </Animated.View>
        )}

        {/* Lost state */}
        {gameState === 'lost' && (
          <View style={[styles.resultCard, styles.lostCard]}>
            <Text style={styles.resultEmoji}>😔</Text>
            <Text style={styles.resultTitle}>{t('wordle.game_over', lang)}</Text>
            {correctSifat && (
              <View style={styles.correctAnswerBox}>
                <Text style={styles.correctAnswerLabel}>{t('wordle.correct', lang)}</Text>
                <Text style={styles.correctAnswerValue}>{correctSifat}</Text>
              </View>
            )}
          </View>
        )}

        {/* Option buttons — only when playing */}
        {gameState === 'playing' && (
          <View style={styles.optionsSection}>
            <Text style={styles.sectionLabel}>{t('wordle.guess', lang)}</Text>
            <View style={styles.optionsList}>
              {options.map((option) => {
                const isWrong = wrongAnswer === option;
                return (
                  <Animated.View
                    key={option}
                    style={[
                      styles.optionWrap,
                      isWrong && {
                        opacity: wrongAnim.interpolate({
                          inputRange: [0, 0.5, 1],
                          outputRange: [1, 0.4, 1],
                        }),
                      },
                    ]}
                  >
                    <TouchableOpacity
                      accessibilityRole="button"
                      accessibilityLabel={t('wordle.wrong', lang)}
                      style={[
                        styles.optionBtn,
                        isWrong && styles.optionBtnWrong,
                      ]}
                      onPress={() => handleGuess(option)}
                      disabled={guessing}
                      activeOpacity={0.75}
                    >
                      <Text style={[
                        styles.optionText,
                        isWrong && styles.optionTextWrong,
                      ]}>
                        {option}
                      </Text>
                      {isWrong && (
                        <Text style={styles.wrongBadge}>✗ {t('wordle.wrong', lang)}</Text>
                      )}
                    </TouchableOpacity>
                  </Animated.View>
                );
              })}
            </View>
            {guessing && (
              <ActivityIndicator color={colors.gold} style={styles.guessingIndicator} />
            )}
          </View>
        )}

        {/* Coins if win info — when playing */}
        {gameState === 'playing' && xpIfWin > 0 && (
          <View style={styles.coinsInfoBanner}>
            <Text style={styles.coinsInfoText}>
              ✨ {t('wordle.xp_if_win', lang)}: {xpIfWin} XP
            </Text>
          </View>
        )}

        {/* Leaderboard */}
        {(gameState === 'won' || gameState === 'lost') && (
          <View style={styles.lbSection}>
            <Text style={styles.sectionLabel}>{t('wordle.leaderboard', lang)}</Text>
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
    gap: spacing.md,
  },
  scroll: {
    paddingHorizontal: spacing.lg,
    paddingBottom: spacing.xl,
  },

  // Header
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: spacing.md,
    gap: spacing.sm,
  },
  backBtn: {
    padding: 4,
    marginRight: spacing.xs,
  },
  backArrow: {
    fontSize: 22,
    color: colors.textPrimary,
  },
  headerCenter: {
    flex: 1,
    flexDirection: 'row',
    alignItems: 'center',
    gap: spacing.xs,
  },
  headerEmoji: {
    fontSize: 22,
  },
  title: {
    ...typography.h2,
  },
  coinsChip: {
    backgroundColor: `${colors.gold}20`,
    borderRadius: radius.full,
    borderWidth: 1,
    borderColor: `${colors.gold}40`,
    paddingHorizontal: spacing.sm,
    paddingVertical: 4,
  },
  coinsChipText: {
    ...typography.label,
    color: colors.gold,
    fontSize: 12,
  },

  // Attempts row
  attemptsRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: spacing.xs,
    marginBottom: spacing.lg,
  },
  attemptDot: {
    width: 10,
    height: 10,
    borderRadius: 5,
  },
  attemptDotEmpty: {
    backgroundColor: colors.border,
    borderWidth: 1,
    borderColor: `${colors.gold}30`,
  },
  attemptDotUsed: {
    backgroundColor: colors.textMuted,
  },
  attemptDotWon: {
    backgroundColor: colors.gold,
  },
  attemptsLabel: {
    ...typography.caption,
    color: colors.textMuted,
    marginLeft: spacing.xs,
  },

  // Hints
  hintsSection: {
    marginBottom: spacing.lg,
  },
  sectionLabel: {
    ...typography.goldLabel,
    marginBottom: spacing.sm,
  },
  hintCard: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    backgroundColor: colors.surface,
    borderRadius: radius.md,
    padding: spacing.md,
    marginBottom: spacing.sm,
    borderWidth: 1,
    borderColor: `${colors.gold}35`,
    ...shadow.sm,
  },
  hintNumberBadge: {
    width: 26,
    height: 26,
    borderRadius: 13,
    backgroundColor: `${colors.gold}20`,
    alignItems: 'center',
    justifyContent: 'center',
    marginRight: spacing.sm,
    marginTop: 1,
    flexShrink: 0,
  },
  hintNumberText: {
    ...typography.label,
    fontSize: 12,
    color: colors.gold,
  },
  hintNumber: {
    width: 26,
    height: 26,
    lineHeight: 26,
    borderRadius: 13,
    backgroundColor: `${colors.gold}20`,
    textAlign: 'center',
    marginRight: spacing.sm,
    color: colors.gold,
    fontWeight: '700',
    fontSize: 12,
  },
  hintText: {
    ...typography.body,
    color: colors.textPrimary,
    flex: 1,
    lineHeight: 22,
  },
  hiddenHintCard: {
    backgroundColor: `${colors.surface}80`,
    borderRadius: radius.md,
    padding: spacing.md,
    marginBottom: spacing.sm,
    borderWidth: 1,
    borderColor: colors.border,
    borderStyle: 'dashed',
    alignItems: 'center',
  },
  hiddenHintText: {
    ...typography.caption,
    color: colors.textMuted,
  },

  // Options
  optionsSection: {
    marginBottom: spacing.lg,
  },
  optionsList: {
    gap: spacing.sm,
  },
  optionWrap: {
    // wrapper for animated opacity
  },
  optionBtn: {
    backgroundColor: colors.surface,
    borderRadius: radius.md,
    paddingHorizontal: spacing.md,
    paddingVertical: spacing.md,
    borderWidth: 1,
    borderColor: `${colors.gold}25`,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    ...shadow.sm,
  },
  optionBtnWrong: {
    borderColor: '#D95F5F',
    backgroundColor: `${'#D95F5F'}12`,
  },
  optionText: {
    ...typography.body,
    color: colors.textPrimary,
    fontWeight: '600',
    fontSize: 15,
  },
  optionTextWrong: {
    color: '#D95F5F',
  },
  wrongBadge: {
    ...typography.caption,
    color: '#D95F5F',
    fontWeight: '700',
    fontSize: 11,
  },
  guessingIndicator: {
    marginTop: spacing.md,
  },

  // Coins info
  coinsInfoBanner: {
    backgroundColor: `${colors.gold}10`,
    borderRadius: radius.sm,
    padding: spacing.sm,
    alignItems: 'center',
    marginBottom: spacing.lg,
    borderWidth: 1,
    borderColor: `${colors.gold}20`,
  },
  coinsInfoText: {
    ...typography.caption,
    color: colors.gold,
    fontWeight: '600',
  },

  // Result cards
  resultCard: {
    borderRadius: radius.lg,
    padding: spacing.lg,
    alignItems: 'center',
    marginBottom: spacing.lg,
    borderWidth: 1,
    ...shadow.gold,
  },
  wonCard: {
    backgroundColor: `${colors.gold}10`,
    borderColor: `${colors.gold}50`,
  },
  lostCard: {
    backgroundColor: colors.surface,
    borderColor: colors.border,
  },
  resultEmoji: {
    fontSize: 48,
    marginBottom: spacing.sm,
  },
  resultTitle: {
    ...typography.h2,
    marginBottom: spacing.xs,
  },
  resultSubtitle: {
    ...typography.body,
    color: colors.textSecondary,
    marginBottom: spacing.sm,
  },
  coinsEarnedBadge: {
    backgroundColor: `${colors.gold}25`,
    borderRadius: radius.full,
    paddingHorizontal: spacing.md,
    paddingVertical: spacing.xs,
    borderWidth: 1,
    borderColor: `${colors.gold}50`,
    marginTop: spacing.xs,
  },
  coinsEarnedText: {
    ...typography.label,
    color: colors.gold,
    fontSize: 16,
  },
  correctAnswerBox: {
    marginTop: spacing.sm,
    backgroundColor: colors.background,
    borderRadius: radius.sm,
    paddingHorizontal: spacing.md,
    paddingVertical: spacing.sm,
    alignItems: 'center',
    borderWidth: 1,
    borderColor: colors.border,
  },
  correctAnswerLabel: {
    ...typography.caption,
    color: colors.textMuted,
    marginBottom: 2,
  },
  correctAnswerValue: {
    ...typography.h3,
    color: colors.textPrimary,
  },

  // Leaderboard
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
  lbRank1: {
    backgroundColor: `${'#F5C842'}20`,
  },
  lbRank2: {
    backgroundColor: `${'#C0C0C0'}20`,
  },
  lbRank3: {
    backgroundColor: `${'#CD7F32'}20`,
  },
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
  lbAttempts: {
    ...typography.caption,
    color: colors.gold,
    fontWeight: '700',
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

  // Loading / error
  loadingText: {
    ...typography.caption,
    color: colors.textMuted,
    marginTop: spacing.sm,
  },
  errorEmoji: {
    fontSize: 40,
  },
  errorText: {
    ...typography.body,
    color: colors.textSecondary,
  },
  retryBtn: {
    backgroundColor: colors.gold,
    borderRadius: radius.md,
    paddingHorizontal: spacing.lg,
    paddingVertical: spacing.sm,
    marginTop: spacing.sm,
  },
  retryText: {
    color: colors.background,
    fontWeight: '700',
    fontSize: 15,
  },
});

export default WordleScreen;

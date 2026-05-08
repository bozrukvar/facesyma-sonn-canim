// src/screens/CommunityPollScreen.tsx
import React, { useEffect, useState, useRef, useCallback } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  ActivityIndicator,
  StatusBar,
  ScrollView,
  Animated,
} from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { GamificationAPI } from '../services/api';
import theme from '../utils/theme';
import { useLanguage } from '../utils/LanguageContext';
import { t } from '../utils/i18n';
import type { ScreenProps } from '../navigation/types';

const { colors, spacing, typography, radius, shadow } = theme;
type Props = ScreenProps<'CommunityPoll'>;

interface PollData {
  date: string;
  question: string;
  emoji: string;
  options: string[];
  user_voted: boolean;
  user_vote_index: number | null;
  vote_counts: number[] | null;
  total_votes: number;
  correct_index: number | null;
}

interface VoteResult {
  success: boolean;
  correct: boolean;
  xp_earned: number;
  correct_index: number;
  vote_counts: number[];
}

const CommunityPollScreen: React.FC<Props> = ({ navigation }) => {
  const insets = useSafeAreaInsets();
  const { lang } = useLanguage();

  const [poll, setPoll] = useState<PollData | null>(null);
  const [loading, setLoading] = useState(true);
  const [voting, setVoting] = useState(false);
  const [voteResult, setVoteResult] = useState<VoteResult | null>(null);

  // One Animated.Value per option for bar width (0→1)
  const barAnims = useRef<Animated.Value[]>([]).current;
  // Coin celebration bounce animation
  const coinAnim = useRef(new Animated.Value(0)).current;

  const initBarAnims = (count: number) => {
    while (barAnims.length < count) {
      barAnims.push(new Animated.Value(0));
    }
  };

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const data = await GamificationAPI.getDailyPoll(lang);
      initBarAnims(data.options.length);
      setPoll(data);

      // If already voted, animate bars immediately
      if (data.user_voted && data.vote_counts) {
        const total = data.total_votes || 1;
        data.options.forEach((_, i) => {
          const ratio = (data.vote_counts![i] ?? 0) / total;
          barAnims[i].setValue(ratio);
        });
      }
    } catch {
      // keep stale state
    } finally {
      setLoading(false);
    }
  }, [lang]);

  useEffect(() => {
    load();
  }, [load]);

  const animateBars = (counts: number[], total: number) => {
    const animations = counts.map((count, i) => {
      const ratio = total > 0 ? count / total : 0;
      return Animated.timing(barAnims[i], {
        toValue: ratio,
        duration: 600,
        delay: i * 80,
        useNativeDriver: false,
      });
    });
    Animated.parallel(animations).start();
  };

  const animateCoin = () => {
    coinAnim.setValue(0);
    Animated.sequence([
      Animated.spring(coinAnim, {
        toValue: 1,
        useNativeDriver: true,
        tension: 120,
        friction: 6,
      }),
      Animated.delay(1800),
      Animated.timing(coinAnim, {
        toValue: 0,
        duration: 300,
        useNativeDriver: true,
      }),
    ]).start();
  };

  const handleVote = async (index: number) => {
    if (!poll || poll.user_voted || voting) return;
    setVoting(true);
    try {
      const res = await GamificationAPI.votePoll(index);
      setVoteResult(res);
      const newTotal = (poll.total_votes ?? 0) + 1;
      setPoll(prev =>
        prev
          ? {
              ...prev,
              user_voted: true,
              user_vote_index: index,
              vote_counts: res.vote_counts,
              correct_index: res.correct_index,
              total_votes: newTotal,
            }
          : prev,
      );
      animateBars(res.vote_counts, newTotal);
      if (res.correct && res.xp_earned > 0) {
        animateCoin();
      }
    } catch {
      // silently ignore
    } finally {
      setVoting(false);
    }
  };

  const getOptionBorderColor = (index: number): string => {
    if (!poll?.user_voted) return `${colors.gold}30`;
    const isCorrect = poll.correct_index === index;
    const isUserVote = poll.user_vote_index === index;
    if (isCorrect) return colors.success ?? '#3DBF8A';
    if (isUserVote && !isCorrect) return colors.error ?? '#D95F5F';
    return `${colors.gold}20`;
  };

  const getOptionLabelColor = (index: number): string => {
    if (!poll?.user_voted) return colors.textPrimary;
    const isCorrect = poll.correct_index === index;
    const isUserVote = poll.user_vote_index === index;
    if (isCorrect) return colors.success ?? '#3DBF8A';
    if (isUserVote) return colors.error ?? '#D95F5F';
    return colors.textSecondary;
  };

  const getPercentage = (index: number): number => {
    if (!poll?.vote_counts || poll.total_votes === 0) return 0;
    return Math.round(((poll.vote_counts[index] ?? 0) / poll.total_votes) * 100);
  };

  const coinScale = coinAnim.interpolate({
    inputRange: [0, 0.5, 1],
    outputRange: [0, 1.2, 1],
  });

  const coinOpacity = coinAnim.interpolate({
    inputRange: [0, 0.1, 0.9, 1],
    outputRange: [0, 1, 1, 0],
  });

  if (loading) {
    return (
      <View style={styles.center}>
        <ActivityIndicator size="large" color={colors.gold} />
      </View>
    );
  }

  if (!poll) {
    return (
      <View style={styles.center}>
        <Text style={styles.emptyText}>{t('poll.tomorrow', lang)}</Text>
      </View>
    );
  }

  return (
    <View style={styles.container}>
      <StatusBar barStyle="light-content" />

      {/* Coin celebration overlay */}
      <Animated.View
        style={[
          styles.coinCelebration,
          { opacity: coinOpacity, transform: [{ scale: coinScale }] },
        ]}
        pointerEvents="none"
      >
        <Text style={styles.coinCelebrationText}>
          +{voteResult?.xp_earned ?? 0} ✨ XP
        </Text>
        <Text style={styles.coinCelebrationSub}>{t('poll.coins', lang)}</Text>
      </Animated.View>

      <ScrollView
        contentContainerStyle={[
          styles.scrollContent,
          { paddingTop: insets.top + spacing.md, paddingBottom: insets.bottom + 40 },
        ]}
        showsVerticalScrollIndicator={false}
      >
        {/* Header */}
        <View style={styles.topBar}>
          <TouchableOpacity onPress={() => navigation.goBack()} style={styles.backBtn}>
            <Text style={styles.backArrow}>←</Text>
          </TouchableOpacity>
          <Text style={styles.title}>{t('poll.title', lang)}</Text>
          <View style={styles.headerSpacer} />
        </View>

        {/* Question card */}
        <View style={styles.questionCard}>
          <Text style={styles.questionEmoji}>{poll.emoji}</Text>
          <Text style={styles.questionText}>{poll.question}</Text>
        </View>

        {/* Status badge */}
        {poll.user_voted && (
          <View style={styles.statusRow}>
            {voteResult !== null ? (
              <View
                style={[
                  styles.statusBadge,
                  {
                    backgroundColor: voteResult.correct
                      ? `${colors.success}22`
                      : `${colors.error}22`,
                    borderColor: voteResult.correct
                      ? colors.success
                      : colors.error,
                  },
                ]}
              >
                <Text
                  style={[
                    styles.statusBadgeText,
                    {
                      color: voteResult.correct
                        ? colors.success
                        : colors.error,
                    },
                  ]}
                >
                  {voteResult.correct
                    ? `✓ ${t('poll.correct', lang)}`
                    : `✗ ${t('poll.wrong', lang)}`}
                </Text>
              </View>
            ) : (
              <View style={styles.alreadyVotedBadge}>
                <Text style={styles.alreadyVotedText}>
                  {t('poll.already_voted', lang)}
                </Text>
              </View>
            )}
          </View>
        )}

        {/* Options */}
        <View style={styles.optionsList}>
          {poll.options.map((option, index) => {
            const pct = getPercentage(index);
            const borderColor = getOptionBorderColor(index);
            const labelColor = getOptionLabelColor(index);
            const isCorrect = poll.user_voted && poll.correct_index === index;
            const isUserVote = poll.user_voted && poll.user_vote_index === index;

            return (
              <TouchableOpacity
                key={index}
                style={[styles.optionBtn, { borderColor }]}
                onPress={() => handleVote(index)}
                disabled={poll.user_voted || voting}
                activeOpacity={0.8}
              >
                {/* Percentage bar (shown after vote) */}
                {poll.user_voted && (
                  <Animated.View
                    style={[
                      styles.optionBar,
                      {
                        width: barAnims[index].interpolate({
                          inputRange: [0, 1],
                          outputRange: ['0%', '100%'],
                        }),
                        backgroundColor: isCorrect
                          ? `${colors.success}22`
                          : isUserVote
                          ? `${colors.error}18`
                          : `${colors.gold}12`,
                      },
                    ]}
                  />
                )}

                <View style={styles.optionContent}>
                  {/* Option letter badge */}
                  <View
                    style={[
                      styles.optionIndex,
                      poll.user_voted && {
                        backgroundColor: isCorrect
                          ? `${colors.success}30`
                          : isUserVote
                          ? `${colors.error}30`
                          : `${colors.gold}18`,
                        borderColor: borderColor,
                      },
                    ]}
                  >
                    <Text
                      style={[
                        styles.optionIndexText,
                        poll.user_voted && { color: labelColor },
                      ]}
                    >
                      {String.fromCharCode(65 + index)}
                    </Text>
                  </View>

                  <Text
                    style={[styles.optionLabel, { color: labelColor, flex: 1 }]}
                    numberOfLines={2}
                  >
                    {option}
                  </Text>

                  {/* Right side indicators */}
                  {poll.user_voted && (
                    <View style={styles.optionRight}>
                      <Text style={[styles.optionPct, { color: labelColor }]}>
                        {pct}%
                      </Text>
                      {isCorrect && (
                        <Text style={styles.correctIcon}>✓</Text>
                      )}
                      {isUserVote && !isCorrect && (
                        <Text style={styles.wrongIcon}>✗</Text>
                      )}
                    </View>
                  )}
                </View>
              </TouchableOpacity>
            );
          })}
        </View>

        {voting && (
          <ActivityIndicator
            color={colors.gold}
            style={styles.votingIndicator}
          />
        )}

        {/* Result message */}
        {poll.user_voted && voteResult !== null && !voteResult.correct && (
          <View style={styles.wrongAnswerCard}>
            <Text style={styles.wrongAnswerLabel}>
              {t('poll.correct', lang)}:{' '}
              <Text style={styles.wrongAnswerValue}>
                {poll.options[voteResult.correct_index] ?? ''}
              </Text>
            </Text>
          </View>
        )}

        {/* Footer stats */}
        <View style={styles.footerRow}>
          <Text style={styles.totalVotes}>
            {poll.total_votes.toLocaleString()} {t('poll.total_votes', lang)}
          </Text>
        </View>

        <View style={styles.tomorrowCard}>
          <Text style={styles.tomorrowText}>
            {t('poll.tomorrow', lang)} 🕐
          </Text>
        </View>
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
  },
  emptyText: {
    ...typography.body,
    color: colors.textMuted,
    textAlign: 'center',
    paddingHorizontal: spacing.xl,
  },
  scrollContent: {
    paddingHorizontal: spacing.lg,
  },

  // Header
  topBar: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: spacing.lg,
  },
  backBtn: {
    padding: spacing.xs,
    marginRight: spacing.md,
  },
  backArrow: {
    fontSize: 22,
    color: colors.textPrimary,
  },
  title: {
    ...typography.h2,
    flex: 1,
  },
  headerSpacer: {
    width: 38,
  },

  // Question card
  questionCard: {
    backgroundColor: colors.surface,
    borderRadius: radius.lg,
    borderWidth: 1.5,
    borderColor: `${colors.gold}55`,
    padding: spacing.xl,
    alignItems: 'center',
    marginBottom: spacing.lg,
    ...shadow.gold,
  },
  questionEmoji: {
    fontSize: 52,
    marginBottom: spacing.md,
  },
  questionText: {
    ...typography.h2,
    textAlign: 'center',
    lineHeight: 28,
    color: colors.textPrimary,
  },

  // Status
  statusRow: {
    alignItems: 'center',
    marginBottom: spacing.md,
  },
  statusBadge: {
    borderRadius: radius.full,
    borderWidth: 1,
    paddingHorizontal: spacing.lg,
    paddingVertical: spacing.xs,
  },
  statusBadgeText: {
    ...typography.label,
    fontSize: 13,
  },
  alreadyVotedBadge: {
    backgroundColor: `${colors.gold}18`,
    borderRadius: radius.full,
    borderWidth: 1,
    borderColor: `${colors.gold}40`,
    paddingHorizontal: spacing.lg,
    paddingVertical: spacing.xs,
  },
  alreadyVotedText: {
    ...typography.label,
    color: colors.gold,
    fontSize: 12,
  },

  // Options
  optionsList: {
    gap: spacing.sm,
    marginBottom: spacing.md,
  },
  optionBtn: {
    backgroundColor: colors.surface,
    borderRadius: radius.md,
    borderWidth: 1.5,
    overflow: 'hidden',
    minHeight: 56,
    justifyContent: 'center',
    ...shadow.sm,
  },
  optionBar: {
    position: 'absolute',
    top: 0,
    left: 0,
    bottom: 0,
    borderRadius: radius.md,
  },
  optionContent: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: spacing.md,
    paddingVertical: spacing.sm,
    gap: spacing.sm,
  },
  optionIndex: {
    width: 32,
    height: 32,
    borderRadius: radius.full,
    backgroundColor: `${colors.gold}18`,
    borderWidth: 1,
    borderColor: `${colors.gold}30`,
    alignItems: 'center',
    justifyContent: 'center',
  },
  optionIndexText: {
    ...typography.label,
    fontSize: 13,
    color: colors.gold,
  },
  optionLabel: {
    ...typography.body,
    color: colors.textPrimary,
    fontWeight: '600',
  },
  optionRight: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: spacing.xs,
    minWidth: 48,
    justifyContent: 'flex-end',
  },
  optionPct: {
    ...typography.label,
    fontSize: 13,
    color: colors.textSecondary,
  },
  correctIcon: {
    fontSize: 15,
    color: '#3DBF8A',
    fontWeight: '700',
  },
  wrongIcon: {
    fontSize: 15,
    color: '#D95F5F',
    fontWeight: '700',
  },

  // Voting indicator
  votingIndicator: {
    marginVertical: spacing.md,
  },

  // Wrong answer card
  wrongAnswerCard: {
    backgroundColor: `${'#D95F5F'}15`,
    borderRadius: radius.md,
    borderWidth: 1,
    borderColor: `${'#D95F5F'}30`,
    padding: spacing.md,
    marginBottom: spacing.md,
    alignItems: 'center',
  },
  wrongAnswerLabel: {
    ...typography.body,
    color: colors.textSecondary,
    textAlign: 'center',
  },
  wrongAnswerValue: {
    color: '#3DBF8A',
    fontWeight: '700',
  },

  // Footer
  footerRow: {
    alignItems: 'center',
    marginBottom: spacing.sm,
  },
  totalVotes: {
    ...typography.caption,
    color: colors.textMuted,
  },
  tomorrowCard: {
    backgroundColor: colors.surface,
    borderRadius: radius.md,
    borderWidth: 1,
    borderColor: `${colors.gold}20`,
    padding: spacing.md,
    alignItems: 'center',
    marginTop: spacing.sm,
  },
  tomorrowText: {
    ...typography.caption,
    color: colors.textSecondary,
    fontSize: 13,
  },

  // Coin celebration
  coinCelebration: {
    position: 'absolute',
    top: '38%',
    left: 0,
    right: 0,
    zIndex: 100,
    alignItems: 'center',
    pointerEvents: 'none' as any,
  },
  coinCelebrationText: {
    fontSize: 42,
    fontWeight: '800',
    color: colors.gold,
    textAlign: 'center',
    ...shadow.gold,
  },
  coinCelebrationSub: {
    ...typography.label,
    color: colors.gold,
    marginTop: spacing.xs,
    letterSpacing: 1.5,
  },
});

export default CommunityPollScreen;

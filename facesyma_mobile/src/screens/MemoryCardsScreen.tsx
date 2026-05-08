// src/screens/MemoryCardsScreen.tsx
import React, {
  useCallback,
  useEffect,
  useRef,
  useState,
} from 'react';
import {
  ActivityIndicator,
  Animated,
  Dimensions,
  Modal,
  ScrollView,
  StatusBar,
  StyleSheet,
  Text,
  TouchableOpacity,
  View,
} from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { GamificationAPI } from '../services/api';
import theme from '../utils/theme';
import { useLanguage } from '../utils/LanguageContext';
import { t } from '../utils/i18n';
import type { ScreenProps } from '../navigation/types';

const { colors, spacing, typography, radius, shadow } = theme;
const SCREEN_WIDTH = Dimensions.get('window').width;

type Props = ScreenProps<'MemoryCards'>;
type GameSize = 4 | 6;
type Phase = 'select' | 'playing' | 'complete';
type ActiveTab = 'game' | 'leaderboard';

interface Card {
  id: string;
  content: string;
  pair_id: number;
  type: 'feature' | 'sifat';
  // UI state
  isFlipped: boolean;
  isMatched: boolean;
  animValue: Animated.Value;
}

interface LeaderboardEntry {
  rank: number;
  user_id: number;
  username: string;
  best_moves: number;
}

interface CompletionData {
  xp_earned: number;
  moves: number;
}

// Horizontal padding + gap between cards
const HORIZONTAL_PADDING = spacing.lg * 2;
const CARD_GAP = spacing.xs;

const getCardSize = (gridSize: GameSize): number => {
  const cols = gridSize;
  const totalGap = CARD_GAP * (cols - 1);
  return Math.floor((SCREEN_WIDTH - HORIZONTAL_PADDING - totalGap) / cols);
};

const MemoryCardsScreen: React.FC<Props> = ({ navigation, route }) => {
  const insets = useSafeAreaInsets();
  const { lang } = useLanguage();

  const initSize: GameSize = route?.params?.size ?? 4;

  const [phase, setPhase] = useState<Phase>('select');
  const [activeTab, setActiveTab] = useState<ActiveTab>('game');
  const [selectedSize, setSelectedSize] = useState<GameSize>(initSize);
  const [cards, setCards] = useState<Card[]>([]);
  const [loading, setLoading] = useState(false);

  // Game state
  const [moves, setMoves] = useState(0);
  const [elapsedMs, setElapsedMs] = useState(0);
  const [flippedIndices, setFlippedIndices] = useState<number[]>([]);
  const [canFlip, setCanFlip] = useState(true);
  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const startTimeRef = useRef<number>(0);

  // Completion
  const [showModal, setShowModal] = useState(false);
  const [completion, setCompletion] = useState<CompletionData | null>(null);
  const modalScale = useRef(new Animated.Value(0)).current;

  // Leaderboard
  const [leaderboard, setLeaderboard] = useState<LeaderboardEntry[]>([]);
  const [lbLoading, setLbLoading] = useState(false);

  // ── Timer ─────────────────────────────────────────────────────────────────
  const startTimer = () => {
    startTimeRef.current = Date.now() - elapsedMs;
    timerRef.current = setInterval(() => {
      setElapsedMs(Date.now() - startTimeRef.current);
    }, 500);
  };

  const stopTimer = () => {
    if (timerRef.current) {
      clearInterval(timerRef.current);
      timerRef.current = null;
    }
  };

  useEffect(() => {
    return () => stopTimer();
  }, []);

  // ── Format time ───────────────────────────────────────────────────────────
  const formatTime = (ms: number): string => {
    const totalSec = Math.floor(ms / 1000);
    const m = Math.floor(totalSec / 60);
    const s = totalSec % 60;
    return `${m}:${s.toString().padStart(2, '0')}`;
  };

  // ── Start game ────────────────────────────────────────────────────────────
  const startGame = useCallback(async (size: GameSize) => {
    setLoading(true);
    setMoves(0);
    setElapsedMs(0);
    setFlippedIndices([]);
    setCanFlip(true);
    setShowModal(false);
    setCompletion(null);
    stopTimer();

    try {
      const res = await GamificationAPI.getMemoryCards(size);
      // Shuffle and build card objects
      const raw = [...res.cards].sort(() => Math.random() - 0.5);
      const built: Card[] = raw.map(c => ({
        ...c,
        isFlipped: false,
        isMatched: false,
        animValue: new Animated.Value(0),
      }));
      setCards(built);
      setPhase('playing');
      startTimer();
    } catch {
      // keep select phase on error
    } finally {
      setLoading(false);
    }
  }, []);

  // ── Flip card ─────────────────────────────────────────────────────────────
  const flipCardAnim = (card: Card, toValue: number, cb?: (result: { finished: boolean }) => void) => {
    Animated.timing(card.animValue, {
      toValue,
      duration: 300,
      useNativeDriver: true,
    }).start(cb);
  };

  const handleCardPress = (index: number) => {
    if (!canFlip) return;
    const card = cards[index];
    if (card.isFlipped || card.isMatched) return;
    if (flippedIndices.length === 2) return;

    // Flip this card face-up
    const updated = cards.map((c, i) =>
      i === index ? { ...c, isFlipped: true } : c,
    );
    setCards(updated);
    flipCardAnim(updated[index], 1);

    const newFlipped = [...flippedIndices, index];
    setFlippedIndices(newFlipped);

    if (newFlipped.length === 2) {
      setCanFlip(false);
      const [firstIdx, secondIdx] = newFlipped;
      const first = updated[firstIdx];
      const second = updated[secondIdx];
      const newMoves = moves + 1;
      setMoves(newMoves);

      if (first.pair_id === second.pair_id) {
        // Match!
        setTimeout(() => {
          setCards(prev =>
            prev.map((c, i) =>
              i === firstIdx || i === secondIdx
                ? { ...c, isMatched: true }
                : c,
            ),
          );
          setFlippedIndices([]);
          setCanFlip(true);

          // Check win
          const afterMatch = updated.map((c, i) =>
            i === firstIdx || i === secondIdx ? { ...c, isMatched: true } : c,
          );
          if (afterMatch.every(c => c.isMatched)) {
            handleGameComplete(newMoves);
          }
        }, 400);
      } else {
        // No match — flip back after delay, update state only after animation finishes
        setTimeout(() => {
          flipCardAnim(updated[firstIdx], 0);
          flipCardAnim(updated[secondIdx], 0, () => {
            setCards(prev =>
              prev.map((c, i) =>
                i === firstIdx || i === secondIdx
                  ? { ...c, isFlipped: false }
                  : c,
              ),
            );
            setFlippedIndices([]);
            setCanFlip(true);
          });
        }, 900);
      }
    }
  };

  const handleGameComplete = async (finalMoves: number) => {
    stopTimer();
    const finalTime = Date.now() - startTimeRef.current;
    setElapsedMs(finalTime);

    try {
      const res = await GamificationAPI.completeMemory(
        finalMoves,
        finalTime,
        cards.length / 2,
      );
      setCompletion({ xp_earned: res.xp_earned, moves: res.moves });
    } catch {
      setCompletion({ xp_earned: 0, moves: finalMoves });
    }

    setShowModal(true);
    Animated.spring(modalScale, {
      toValue: 1,
      useNativeDriver: true,
      tension: 100,
      friction: 7,
    }).start();
  };

  // ── Leaderboard ───────────────────────────────────────────────────────────
  const loadLeaderboard = useCallback(async () => {
    setLbLoading(true);
    try {
      const res = await GamificationAPI.getMemoryLeaderboard();
      setLeaderboard(res.entries);
    } catch {
      // keep stale
    } finally {
      setLbLoading(false);
    }
  }, []);

  useEffect(() => {
    if (activeTab === 'leaderboard') {
      loadLeaderboard();
    }
  }, [activeTab, loadLeaderboard]);

  // ── Restart ───────────────────────────────────────────────────────────────
  const handlePlayAgain = () => {
    modalScale.setValue(0);
    setShowModal(false);
    setPhase('select');
    setCards([]);
  };

  // ── Card render ───────────────────────────────────────────────────────────
  const renderCard = (card: Card, index: number) => {
    const cardSize = getCardSize(selectedSize);

    const frontRotate = card.animValue.interpolate({
      inputRange: [0, 1],
      outputRange: ['180deg', '360deg'],
    });
    const backRotate = card.animValue.interpolate({
      inputRange: [0, 1],
      outputRange: ['0deg', '180deg'],
    });
    const frontOpacity = card.animValue.interpolate({
      inputRange: [0.5, 1],
      outputRange: [0, 1],
    });
    const backOpacity = card.animValue.interpolate({
      inputRange: [0, 0.5],
      outputRange: [1, 0],
    });

    return (
      <TouchableOpacity
        accessibilityRole="button"
        accessibilityLabel='?'
        key={card.id}
        onPress={() => handleCardPress(index)}
        disabled={!canFlip || card.isFlipped || card.isMatched}
        activeOpacity={0.85}
        style={[styles.cardWrapper, { width: cardSize, height: cardSize }]}
      >
        {/* Back face — "?" */}
        <Animated.View
          style={[
            styles.cardFace,
            styles.cardBack,
            {
              width: cardSize,
              height: cardSize,
              opacity: backOpacity,
              transform: [{ rotateY: backRotate }],
            },
          ]}
        >
          <Text style={styles.cardBackQ}>?</Text>
        </Animated.View>

        {/* Front face — content */}
        <Animated.View
          style={[
            styles.cardFace,
            styles.cardFront,
            card.isMatched && styles.cardMatched,
            {
              width: cardSize,
              height: cardSize,
              opacity: frontOpacity,
              transform: [{ rotateY: frontRotate }],
            },
          ]}
        >
          <Text
            style={[
              styles.cardFrontText,
              card.isMatched && styles.cardFrontTextMatched,
            ]}
            numberOfLines={3}
            adjustsFontSizeToFit
          >
            {card.content}
          </Text>
          {card.isMatched && (
            <Text style={styles.matchedCheck}>✓</Text>
          )}
        </Animated.View>
      </TouchableOpacity>
    );
  };

  // ── Select phase ──────────────────────────────────────────────────────────
  if (phase === 'select') {
    return (
      <View style={styles.container}>
        <StatusBar barStyle="light-content" />
        <View
          style={[
            styles.topBar,
            { paddingTop: insets.top + spacing.md },
          ]}
        >
          <TouchableOpacity
            accessibilityRole="button"
            accessibilityLabel={t('memory.title', lang)}
            onPress={() => navigation.goBack()}
            style={styles.backBtn}
          >
            <Text style={styles.backArrow}>←</Text>
          </TouchableOpacity>
          <Text style={styles.title}>{t('memory.title', lang)}</Text>
          <View style={styles.headerSpacer} />
        </View>

        {/* Tab row */}
        <View style={styles.tabRow}>
          <TouchableOpacity
            accessibilityRole="button"
            accessibilityLabel="Oyun sekmesi"
            style={[
              styles.tab,
              activeTab === 'game' && styles.tabActive,
            ]}
            onPress={() => setActiveTab('game')}
          >
            <Text
              style={[
                styles.tabText,
                activeTab === 'game' && styles.tabTextActive,
              ]}
            >
              {t('memory.start', lang)}
            </Text>
          </TouchableOpacity>
          <TouchableOpacity
            accessibilityRole="button"
            accessibilityLabel={t('memory.title', lang)}
            style={[
              styles.tab,
              activeTab === 'leaderboard' && styles.tabActive,
            ]}
            onPress={() => setActiveTab('leaderboard')}
          >
            <Text
              style={[
                styles.tabText,
                activeTab === 'leaderboard' && styles.tabTextActive,
              ]}
            >
              {t('memory.leaderboard', lang)}
            </Text>
          </TouchableOpacity>
        </View>

        {activeTab === 'game' ? (
          <View style={styles.selectContent}>
            <View style={styles.selectCard}>
              <Text style={styles.selectHeroEmoji}>🧠</Text>
              <Text style={styles.selectHeading}>
                {t('memory.title', lang)}
              </Text>
              <Text style={styles.selectSub}>
                {t('memory.start', lang)}
              </Text>
            </View>

            <View style={styles.sizeRow}>
              <TouchableOpacity
                accessibilityRole="button"
                accessibilityLabel="4×4 kart boyutu"
                style={[
                  styles.sizeBtn,
                  selectedSize === 4 && styles.sizeBtnActive,
                ]}
                onPress={() => setSelectedSize(4)}
                activeOpacity={0.8}
              >
                <Text
                  style={[
                    styles.sizeBtnTitle,
                    selectedSize === 4 && styles.sizeBtnTitleActive,
                  ]}
                >
                  4×4
                </Text>
                <Text
                  style={[
                    styles.sizeBtnSub,
                    selectedSize === 4 && styles.sizeBtnSubActive,
                  ]}
                >
                  {t('memory.easy', lang)}
                </Text>
              </TouchableOpacity>

              <TouchableOpacity
                accessibilityRole="button"
                accessibilityLabel="6×6 kart boyutu"
                style={[
                  styles.sizeBtn,
                  selectedSize === 6 && styles.sizeBtnActive,
                ]}
                onPress={() => setSelectedSize(6)}
                activeOpacity={0.8}
              >
                <Text
                  style={[
                    styles.sizeBtnTitle,
                    selectedSize === 6 && styles.sizeBtnTitleActive,
                  ]}
                >
                  6×6
                </Text>
                <Text
                  style={[
                    styles.sizeBtnSub,
                    selectedSize === 6 && styles.sizeBtnSubActive,
                  ]}
                >
                  {t('memory.hard', lang)}
                </Text>
              </TouchableOpacity>
            </View>

            <TouchableOpacity
              accessibilityRole="button"
              accessibilityLabel={t('memory.start', lang)}
              style={styles.startBtn}
              onPress={() => startGame(selectedSize)}
              disabled={loading}
              activeOpacity={0.85}
            >
              {loading ? (
                <ActivityIndicator color={colors.background} />
              ) : (
                <Text style={styles.startBtnText}>
                  {t('memory.start', lang)} →
                </Text>
              )}
            </TouchableOpacity>
          </View>
        ) : (
          <View style={styles.lbContainer}>
            {lbLoading ? (
              <ActivityIndicator
                color={colors.gold}
                style={styles.lbLoader}
              />
            ) : leaderboard.length === 0 ? (
              <Text style={styles.emptyText}>
                {t('memory.leaderboard', lang)}
              </Text>
            ) : (
              <ScrollView
                showsVerticalScrollIndicator={false}
                contentContainerStyle={styles.lbList}
              >
                {leaderboard.map(entry => (
                  <View key={entry.user_id} style={styles.lbRow}>
                    <Text style={styles.lbRank}>
                      {entry.rank <= 3
                        ? ['🥇', '🥈', '🥉'][entry.rank - 1]
                        : `#${entry.rank}`}
                    </Text>
                    <Text style={styles.lbName} numberOfLines={1}>
                      {entry.username}
                    </Text>
                    <View style={styles.lbScore}>
                      <Text style={styles.lbScoreValue}>
                        {entry.best_moves}
                      </Text>
                      <Text style={styles.lbScoreLabel}>
                        {' '}{t('memory.best_moves', lang)}
                      </Text>
                    </View>
                  </View>
                ))}
              </ScrollView>
            )}
          </View>
        )}
      </View>
    );
  }

  // ── Playing phase ─────────────────────────────────────────────────────────
  const cardSize = getCardSize(selectedSize);
  const cols = selectedSize;
  const rows = Math.ceil(cards.length / cols);

  return (
    <View style={styles.container}>
      <StatusBar barStyle="light-content" />

      {/* Top bar with stats */}
      <View
        style={[
          styles.topBar,
          { paddingTop: insets.top + spacing.sm },
        ]}
      >
        <TouchableOpacity
          accessibilityRole="button"
          accessibilityLabel={t('memory.title', lang)}
          onPress={() => {
            stopTimer();
            setPhase('select');
            setCards([]);
          }}
          style={styles.backBtn}
        >
          <Text style={styles.backArrow}>←</Text>
        </TouchableOpacity>
        <Text style={styles.title}>{t('memory.title', lang)}</Text>
        <View style={styles.statsRow}>
          <View style={styles.statChip}>
            <Text style={styles.statChipLabel}>{t('memory.moves', lang)}</Text>
            <Text style={styles.statChipValue}>{moves}</Text>
          </View>
          <View style={styles.statChip}>
            <Text style={styles.statChipLabel}>{t('memory.time', lang)}</Text>
            <Text style={styles.statChipValue}>{formatTime(elapsedMs)}</Text>
          </View>
        </View>
      </View>

      {/* Card grid */}
      <ScrollView
        contentContainerStyle={[
          styles.gridContainer,
          { paddingBottom: insets.bottom + 24 },
        ]}
        showsVerticalScrollIndicator={false}
      >
        {Array.from({ length: rows }).map((_, rowIdx) => (
          <View key={rowIdx} style={styles.gridRow}>
            {Array.from({ length: cols }).map((_, colIdx) => {
              const idx = rowIdx * cols + colIdx;
              if (idx >= cards.length) {
                return (
                  <View
                    key={`empty-${colIdx}`}
                    style={[
                      styles.cardWrapper,
                      { width: cardSize, height: cardSize },
                    ]}
                  />
                );
              }
              return renderCard(cards[idx], idx);
            })}
          </View>
        ))}
      </ScrollView>

      {/* Completion modal */}
      <Modal
        visible={showModal}
        transparent
        animationType="fade"
        onRequestClose={() => {}}
      >
        <View style={styles.modalOverlay}>
          <Animated.View
            style={[
              styles.modalCard,
              { transform: [{ scale: modalScale }] },
            ]}
          >
            <Text style={styles.modalEmoji}>🎉</Text>
            <Text style={styles.modalTitle}>{t('memory.completed', lang)}</Text>

            <View style={styles.modalStats}>
              <View style={styles.modalStatItem}>
                <Text style={styles.modalStatValue}>{completion?.moves ?? moves}</Text>
                <Text style={styles.modalStatLabel}>{t('memory.moves', lang)}</Text>
              </View>
              <View style={styles.modalStatDivider} />
              <View style={styles.modalStatItem}>
                <Text style={styles.modalStatValue}>{formatTime(elapsedMs)}</Text>
                <Text style={styles.modalStatLabel}>{t('memory.time', lang)}</Text>
              </View>
            </View>

            {(completion?.xp_earned ?? 0) > 0 && (
              <View style={styles.modalCoinsRow}>
                <Text style={styles.modalCoinsText}>
                  +{completion!.xp_earned} ✨ XP
                </Text>
                <Text style={styles.modalCoinsLabel}>
                  {t('memory.coins', lang)}
                </Text>
              </View>
            )}

            <TouchableOpacity
              accessibilityRole="button"
              accessibilityLabel={t('memory.play_again', lang)}
              style={styles.playAgainBtn}
              onPress={handlePlayAgain}
              activeOpacity={0.85}
            >
              <Text style={styles.playAgainText}>
                {t('memory.play_again', lang)}
              </Text>
            </TouchableOpacity>

            <TouchableOpacity
              accessibilityRole="button"
              accessibilityLabel={t('memory.leaderboard', lang)}
              onPress={() => {
                setShowModal(false);
                navigation.goBack();
              }}
              style={styles.modalBackBtn}
            >
              <Text style={styles.modalBackText}>←  {t('memory.leaderboard', lang)}</Text>
            </TouchableOpacity>
          </Animated.View>
        </View>
      </Modal>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: colors.background,
  },

  // Header
  topBar: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: spacing.lg,
    paddingBottom: spacing.sm,
    gap: spacing.sm,
  },
  backBtn: {
    padding: spacing.xs,
    marginRight: spacing.xs,
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
  statsRow: {
    flexDirection: 'row',
    gap: spacing.xs,
  },
  statChip: {
    backgroundColor: colors.surface,
    borderRadius: radius.sm,
    borderWidth: 1,
    borderColor: `${colors.gold}30`,
    paddingHorizontal: spacing.sm,
    paddingVertical: 4,
    alignItems: 'center',
    minWidth: 52,
  },
  statChipLabel: {
    ...typography.caption,
    color: colors.textMuted,
    fontSize: 10,
  },
  statChipValue: {
    ...typography.label,
    color: colors.gold,
    fontSize: 13,
  },

  // Tabs
  tabRow: {
    flexDirection: 'row',
    marginHorizontal: spacing.lg,
    marginBottom: spacing.md,
    backgroundColor: colors.surface,
    borderRadius: radius.md,
    borderWidth: 1,
    borderColor: `${colors.gold}20`,
    overflow: 'hidden',
  },
  tab: {
    flex: 1,
    paddingVertical: spacing.sm,
    alignItems: 'center',
    borderRadius: radius.md,
  },
  tabActive: {
    backgroundColor: colors.gold,
  },
  tabText: {
    ...typography.label,
    color: colors.textSecondary,
    fontSize: 12,
  },
  tabTextActive: {
    color: colors.background,
  },

  // Select screen
  selectContent: {
    flex: 1,
    paddingHorizontal: spacing.lg,
    gap: spacing.lg,
  },
  selectCard: {
    backgroundColor: colors.surface,
    borderRadius: radius.lg,
    borderWidth: 1.5,
    borderColor: `${colors.gold}40`,
    padding: spacing.xl,
    alignItems: 'center',
    ...shadow.gold,
  },
  selectHeroEmoji: {
    fontSize: 56,
    marginBottom: spacing.md,
  },
  selectHeading: {
    ...typography.h2,
    textAlign: 'center',
    marginBottom: spacing.xs,
  },
  selectSub: {
    ...typography.caption,
    color: colors.textMuted,
    textAlign: 'center',
  },

  // Size selector
  sizeRow: {
    flexDirection: 'row',
    gap: spacing.md,
  },
  sizeBtn: {
    flex: 1,
    backgroundColor: colors.surface,
    borderRadius: radius.md,
    borderWidth: 1.5,
    borderColor: `${colors.gold}25`,
    paddingVertical: spacing.lg,
    alignItems: 'center',
    gap: spacing.xs,
    ...shadow.sm,
  },
  sizeBtnActive: {
    borderColor: colors.gold,
    backgroundColor: `${colors.gold}15`,
    ...shadow.gold,
  },
  sizeBtnTitle: {
    ...typography.h2,
    color: colors.textSecondary,
  },
  sizeBtnTitleActive: {
    color: colors.gold,
  },
  sizeBtnSub: {
    ...typography.caption,
    color: colors.textMuted,
  },
  sizeBtnSubActive: {
    color: colors.gold,
  },

  // Start button
  startBtn: {
    backgroundColor: colors.gold,
    borderRadius: radius.md,
    paddingVertical: spacing.md,
    alignItems: 'center',
    ...shadow.gold,
  },
  startBtnText: {
    ...typography.label,
    color: colors.background,
    fontSize: 15,
    letterSpacing: 1.2,
  },

  // Leaderboard
  lbContainer: {
    flex: 1,
    paddingHorizontal: spacing.lg,
  },
  lbLoader: {
    marginTop: 60,
  },
  lbList: {
    gap: spacing.sm,
    paddingBottom: 40,
  },
  lbRow: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: colors.surface,
    borderRadius: radius.md,
    paddingHorizontal: spacing.md,
    paddingVertical: spacing.sm,
    borderWidth: 1,
    borderColor: `${colors.gold}20`,
    gap: spacing.sm,
    ...shadow.sm,
  },
  lbRank: {
    fontSize: 18,
    minWidth: 36,
    textAlign: 'center',
  },
  lbName: {
    ...typography.body,
    color: colors.textPrimary,
    flex: 1,
    fontWeight: '600',
  },
  lbScore: {
    flexDirection: 'row',
    alignItems: 'baseline',
  },
  lbScoreValue: {
    ...typography.h3,
    color: colors.gold,
  },
  lbScoreLabel: {
    ...typography.caption,
    color: colors.textMuted,
    fontSize: 11,
  },
  emptyText: {
    ...typography.body,
    color: colors.textMuted,
    textAlign: 'center',
    marginTop: 60,
  },

  // Grid
  gridContainer: {
    paddingHorizontal: spacing.lg,
    paddingTop: spacing.sm,
    gap: CARD_GAP,
  },
  gridRow: {
    flexDirection: 'row',
    gap: CARD_GAP,
    justifyContent: 'center',
  },

  // Cards
  cardWrapper: {
    position: 'relative',
  },
  cardFace: {
    position: 'absolute',
    top: 0,
    left: 0,
    borderRadius: radius.sm,
    alignItems: 'center',
    justifyContent: 'center',
    backfaceVisibility: 'hidden',
    padding: spacing.xs,
  },
  cardBack: {
    backgroundColor: colors.goldDark,
    borderWidth: 1.5,
    borderColor: colors.gold,
    ...shadow.gold,
  },
  cardBackQ: {
    fontSize: 24,
    fontWeight: '800',
    color: colors.white,
  },
  cardFront: {
    backgroundColor: colors.white,
    borderWidth: 1.5,
    borderColor: `${colors.gold}50`,
    ...shadow.sm,
  },
  cardMatched: {
    backgroundColor: '#E8FFF4',
    borderColor: '#3DBF8A',
    opacity: 0.75,
  },
  cardFrontText: {
    ...typography.caption,
    color: colors.background,
    fontWeight: '700',
    textAlign: 'center',
    fontSize: 11,
  },
  cardFrontTextMatched: {
    color: '#1A6040',
  },
  matchedCheck: {
    fontSize: 12,
    color: '#3DBF8A',
    fontWeight: '800',
    position: 'absolute',
    bottom: 4,
    right: 6,
  },

  // Modal
  modalOverlay: {
    flex: 1,
    backgroundColor: 'rgba(0,0,0,0.75)',
    alignItems: 'center',
    justifyContent: 'center',
    paddingHorizontal: spacing.lg,
  },
  modalCard: {
    width: '100%',
    backgroundColor: colors.surface,
    borderRadius: radius.xl,
    borderWidth: 1.5,
    borderColor: `${colors.gold}55`,
    padding: spacing.xl,
    alignItems: 'center',
    ...shadow.gold,
  },
  modalEmoji: {
    fontSize: 56,
    marginBottom: spacing.sm,
  },
  modalTitle: {
    ...typography.h2,
    textAlign: 'center',
    marginBottom: spacing.lg,
  },
  modalStats: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: spacing.lg,
    gap: spacing.xl,
  },
  modalStatItem: {
    alignItems: 'center',
    gap: spacing.xs,
  },
  modalStatValue: {
    ...typography.h2,
    color: colors.gold,
  },
  modalStatLabel: {
    ...typography.caption,
    color: colors.textMuted,
  },
  modalStatDivider: {
    width: 1,
    height: 36,
    backgroundColor: `${colors.gold}30`,
  },
  modalCoinsRow: {
    backgroundColor: `${colors.gold}15`,
    borderRadius: radius.full,
    borderWidth: 1,
    borderColor: `${colors.gold}40`,
    paddingHorizontal: spacing.xl,
    paddingVertical: spacing.sm,
    flexDirection: 'row',
    alignItems: 'center',
    gap: spacing.sm,
    marginBottom: spacing.lg,
  },
  modalCoinsText: {
    fontSize: 22,
    fontWeight: '800',
    color: colors.gold,
  },
  modalCoinsLabel: {
    ...typography.label,
    color: colors.gold,
    fontSize: 12,
  },
  playAgainBtn: {
    backgroundColor: colors.gold,
    borderRadius: radius.md,
    paddingVertical: spacing.md,
    paddingHorizontal: spacing.xl,
    alignItems: 'center',
    width: '100%',
    marginBottom: spacing.sm,
    ...shadow.gold,
  },
  playAgainText: {
    ...typography.label,
    color: colors.background,
    fontSize: 15,
    letterSpacing: 1.0,
  },
  modalBackBtn: {
    paddingVertical: spacing.sm,
  },
  modalBackText: {
    ...typography.caption,
    color: colors.textMuted,
    fontSize: 13,
  },
});

export default MemoryCardsScreen;

// src/screens/SpinWheelScreen.tsx
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
  Easing,
  Dimensions,
} from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { GamificationAPI } from '../services/api';
import theme from '../utils/theme';
import { useLanguage } from '../utils/LanguageContext';
import { t } from '../utils/i18n';
import type { ScreenProps } from '../navigation/types';

const { colors, spacing, typography, radius, shadow } = theme;

type Props = ScreenProps<'SpinWheel'>;

// ── Constants ──────────────────────────────────────────────────────────────────

const SEGMENT_COUNT = 8;
const SEGMENT_DEG   = 360 / SEGMENT_COUNT; // 45°
const WHEEL_SIZE    = Math.min(Dimensions.get('window').width - spacing.lg * 2, 300);
const HALF          = WHEEL_SIZE / 2;

const SEGMENT_COLORS = [
  '#F5C842',
  '#E07A7A',
  '#7AE0B0',
  '#9B7AE0',
  '#7AAEE0',
  '#E0A17A',
  '#7AE07A',
  '#F5A442',
];

const REWARD_EMOJIS: Record<string, string> = {
  xp:       '✨',
  badge_xp: '🎖️',
  streak:   '🔥',
  jackpot:  '🎰',
  default:  '🎁',
};

const CONFETTI_POOL = ['🎉', '✨', '🌟', '💫', '🎊', '⭐'];

// ── Types ──────────────────────────────────────────────────────────────────────

interface Segment { label: string; reward_type: string; weight: number; }

interface LastReward {
  segment_index: number;
  label: string;
  reward_type: string;
  reward_value: number;
  xp_earned: number;
  message_tr: string;
  message_en: string;
}

interface Particle {
  id: number;
  tx: Animated.Value;
  ty: Animated.Value;
  opacity: Animated.Value;
  scale: Animated.Value;
  emoji: string;
}

// ── Confetti hook ──────────────────────────────────────────────────────────────

function useConfetti() {
  const [particles, setParticles] = useState<Particle[]>([]);
  const nextId = useRef(0);

  const burst = useCallback(() => {
    const count = 10;
    const fresh: Particle[] = Array.from({ length: count }, (_, i) => {
      const id     = ++nextId.current;
      const tx     = new Animated.Value(0);
      const ty     = new Animated.Value(0);
      const opacity = new Animated.Value(1);
      const scale  = new Animated.Value(0.5);
      const angle  = (i / count) * Math.PI * 2;
      const dist   = 60 + Math.random() * 50;
      Animated.parallel([
        Animated.timing(tx, {
          toValue: Math.cos(angle) * dist,
          duration: 900,
          useNativeDriver: true,
          easing: Easing.out(Easing.quad),
        }),
        Animated.timing(ty, {
          toValue: Math.sin(angle) * dist - 30,
          duration: 900,
          useNativeDriver: true,
          easing: Easing.out(Easing.quad),
        }),
        Animated.sequence([
          Animated.timing(scale, { toValue: 1.3, duration: 200, useNativeDriver: true }),
          Animated.timing(scale, { toValue: 1,   duration: 700, useNativeDriver: true }),
        ]),
        Animated.sequence([
          Animated.delay(450),
          Animated.timing(opacity, { toValue: 0, duration: 450, useNativeDriver: true }),
        ]),
      ]).start(() => setParticles(prev => prev.filter(p => p.id !== id)));
      return {
        id, tx, ty, opacity, scale,
        emoji: CONFETTI_POOL[i % CONFETTI_POOL.length],
      };
    });
    setParticles(prev => [...prev, ...fresh]);
  }, []);

  return { particles, burst };
}

// ── Wheel Visual ───────────────────────────────────────────────────────────────
// We draw pie segments as colored strips.
// Each segment strip is WHEEL_SIZE tall × HALF wide, positioned with its
// horizontal center at the wheel center (left = 0, via translateX = HALF/2 relative
// to the half-strip origin). We then rotate each strip by i*45° around the wheel
// center using the transform trick:
//   translateX(-HALF/2) → rotate(angle) → translateX(HALF/2)
//   but positioned left:0 inside a wrapper at left: HALF/2 - HALF/2 = 0
// Simplest correct approach in pure RN: render a HALF-wide rectangle at
// `left: HALF/2`, then rotate it — pivot is at top of the rect which
// corresponds to wheel center when rect.top = 0 and wheel has overflow:hidden.
// Actually the canonical RN pie-chart trick uses the following:
//   - Parent circle container (overflow:hidden)
//   - Each slice is a square (HALF × HALF) at top:0, left:HALF
//   - Rotate around bottom-left corner: translate(-HALF,0) rotate translate(HALF,0)
//   No. The cleanest approach: render each segment as:
//     - A full-width rectangle (WHEEL_SIZE × HALF), positioned at top:0 left:0
//     - Rotated by i*45° using transform around the wheel center (HALF, HALF)
//     - Pivot at (HALF, HALF): translateX(HALF), translateY(HALF), rotate, translateX(-HALF), translateY(-HALF)
//
// Because RN transforms are applied right-to-left (last first):
//   [{ translateX: HALF }, { translateY: HALF }, { rotate }, { translateX: -HALF }, { translateY: -HALF }]
// BUT in RN the transform array is applied left-to-right, so:
//   translate(HALF,HALF) then rotate then translate(-HALF,-HALF)
// This rotates around (HALF, HALF) which IS the wheel center. Correct.

interface WheelProps {
  segments: Segment[];
  rotateAnim: Animated.Value;
  particles: Particle[];
}

const Wheel: React.FC<WheelProps> = ({ segments, rotateAnim, particles }) => {
  const rotateDeg = rotateAnim.interpolate({
    inputRange:  [0, 360],
    outputRange: ['0deg', '360deg'],
    extrapolate: 'extend',
  });

  return (
    <Animated.View style={[styles.wheel, { transform: [{ rotate: rotateDeg }] }]}>
      {/* Segments */}
      {segments.map((seg, i) => {
        const color    = SEGMENT_COLORS[i % SEGMENT_COLORS.length];
        const segAngle = i * SEGMENT_DEG;
        // Label placement along midpoint radial
        const midAngle = (segAngle + SEGMENT_DEG / 2) * (Math.PI / 180);
        const labelR   = HALF * 0.60;
        const lx       = HALF + labelR * Math.cos(midAngle - Math.PI / 2) - 18;
        const ly       = HALF + labelR * Math.sin(midAngle - Math.PI / 2) - 9;

        return (
          <View key={i} style={StyleSheet.absoluteFill} pointerEvents="none">
            {/*
              Strip occupies full width (WHEEL_SIZE) and height HALF,
              anchored at top of the wheel. After rotating around wheel center
              (HALF, HALF) by segAngle, the top half of the circle shows this color.
              Each subsequent strip covers the next 45° sector.
            */}
            <View
              style={[
                styles.segStrip,
                {
                  backgroundColor: color,
                  transform: [
                    { translateX: HALF },
                    { translateY: HALF },
                    { rotate: `${segAngle}deg` },
                    { translateX: -HALF },
                    { translateY: -HALF },
                  ],
                },
              ]}
            />
            {/* Label */}
            <View
              style={[styles.segLabelWrap, { left: lx, top: ly }]}
              pointerEvents="none"
            >
              <Text style={styles.segLabelText} numberOfLines={1}>
                {seg.label.length > 7 ? seg.label.slice(0, 7) : seg.label}
              </Text>
            </View>
          </View>
        );
      })}

      {/* Divider lines (one per segment boundary, from center outward) */}
      {Array.from({ length: SEGMENT_COUNT }, (_, i) => {
        const angle = i * SEGMENT_DEG;
        return (
          <View
            key={`div${i}`}
            style={[
              styles.divider,
              {
                transform: [
                  { translateX: HALF },
                  { translateY: HALF },
                  { rotate: `${angle}deg` },
                  { translateX: -0.75 },   // center the 1.5px line
                  { translateY: -HALF },   // move up to wheel center top
                ],
              },
            ]}
            pointerEvents="none"
          />
        );
      })}

      {/* Ring overlay */}
      <View style={styles.wheelRing} pointerEvents="none" />

      {/* Center hub */}
      <View style={styles.hub} pointerEvents="none">
        <Text style={styles.hubEmoji}>🌀</Text>
      </View>

      {/* Confetti */}
      {particles.map(p => (
        <Animated.Text
          key={p.id}
          style={[
            styles.particle,
            {
              opacity: p.opacity,
              transform: [
                { translateX: p.tx },
                { translateY: p.ty },
                { scale: p.scale },
              ],
            },
          ]}
        >
          {p.emoji}
        </Animated.Text>
      ))}
    </Animated.View>
  );
};

// ── Main screen ────────────────────────────────────────────────────────────────

const SpinWheelScreen: React.FC<Props> = ({ navigation }) => {
  const insets   = useSafeAreaInsets();
  const { lang } = useLanguage();

  const [loading,        setLoading]        = useState(true);
  const [spinning,       setSpinning]       = useState(false);
  const [canSpin,        setCanSpin]        = useState(false);
  const [segments,       setSegments]       = useState<Segment[]>([]);
  const [lastReward,     setLastReward]     = useState<LastReward | null>(null);
  const [revealedReward, setRevealedReward] = useState<LastReward | null>(null);
  const [apiError,       setApiError]       = useState<string | null>(null);

  const rotateAnim     = useRef(new Animated.Value(0)).current;
  const storedRotation = useRef(0);
  const rewardScale    = useRef(new Animated.Value(0)).current;
  const rewardOpacity  = useRef(new Animated.Value(0)).current;
  const { particles, burst } = useConfetti();

  // ── Default segments ─────────────────────────────────────────────────────────

  const fallbackSegments = (): Segment[] =>
    Array.from({ length: SEGMENT_COUNT }, (_, i) => ({
      label:       i === 7 ? 'JACKPOT' : `+${(i + 1) * 10}`,
      reward_type: i === 7 ? 'jackpot' : i % 2 === 0 ? 'coins' : 'badge_xp',
      weight:      i === 7 ? 1 : 2,
    }));

  // ── Load spin status ─────────────────────────────────────────────────────────

  const loadStatus = useCallback(async () => {
    setLoading(true);
    setApiError(null);
    try {
      const data = await GamificationAPI.getSpinStatus();
      setCanSpin(data.can_spin);
      setSegments(
        data.segments && data.segments.length === SEGMENT_COUNT
          ? data.segments
          : fallbackSegments()
      );
      setLastReward(data.last_reward ?? null);
    } catch {
      setApiError(t('common.error', lang));
      setSegments(fallbackSegments());
    } finally {
      setLoading(false);
    }
  }, [lang]);

  useEffect(() => { loadStatus(); }, [loadStatus]);

  // ── Spin handler ─────────────────────────────────────────────────────────────

  const handleSpin = useCallback(async () => {
    if (!canSpin || spinning) return;
    setSpinning(true);
    setRevealedReward(null);
    rewardScale.setValue(0);
    rewardOpacity.setValue(0);

    try {
      const res      = await GamificationAPI.spinWheel();
      const { reward } = res;
      const segIdx   = typeof reward.segment_index === 'number' ? reward.segment_index : 0;

      // 5 full spins + stop so winning segment is at top (0° position).
      // Segment i starts at i*45°. To bring it to top we rotate by (360 - i*45).
      // Add jitter so the needle doesn't land right on a boundary.
      const jitter     = SEGMENT_DEG * 0.15 + Math.random() * SEGMENT_DEG * 0.7;
      const stopDelta  = 360 * 5 + (360 - segIdx * SEGMENT_DEG - jitter);
      const totalAngle = storedRotation.current + stopDelta;

      Animated.timing(rotateAnim, {
        toValue:         totalAngle,
        duration:        3000,
        easing:          Easing.out(Easing.cubic),
        useNativeDriver: true,
      }).start(({ finished }) => {
        if (!finished) return;
        storedRotation.current = totalAngle % 360;
        Animated.parallel([
          Animated.spring(rewardScale, {
            toValue: 1, friction: 5, tension: 80, useNativeDriver: true,
          }),
          Animated.timing(rewardOpacity, {
            toValue: 1, duration: 280, useNativeDriver: true,
          }),
        ]).start();
        burst();
        setRevealedReward(reward);
        setCanSpin(false);
        setLastReward(reward);
        setSpinning(false);
      });
    } catch (e: any) {
      setSpinning(false);
      setApiError(e?.response?.data?.error || t('common.error', lang));
    }
  }, [canSpin, spinning, rotateAnim, rewardScale, rewardOpacity, burst, lang]);

  // ── Helpers ──────────────────────────────────────────────────────────────────

  const getTypeLabel = (type: string): string => {
    const map: Record<string, string> = {
      coins:    t('spin.coins', lang),
      badge_xp: t('spin.badge_xp', lang),
      streak:   t('spin.streak', lang),
      jackpot:  t('spin.jackpot', lang),
    };
    return map[type] ?? type;
  };

  const getEmoji = (type: string) => REWARD_EMOJIS[type] ?? REWARD_EMOJIS.default;

  const rewardMsg = revealedReward
    ? (lang === 'tr' ? revealedReward.message_tr : revealedReward.message_en)
    : null;

  // ── Loading ──────────────────────────────────────────────────────────────────

  if (loading) {
    return (
      <View style={styles.center}>
        <StatusBar barStyle="light-content" />
        <ActivityIndicator size="large" color={colors.gold} />
      </View>
    );
  }

  // ── Render ───────────────────────────────────────────────────────────────────

  return (
    <View style={styles.container}>
      <StatusBar barStyle="light-content" />

      <ScrollView
        showsVerticalScrollIndicator={false}
        contentContainerStyle={[styles.scroll, { paddingTop: insets.top + spacing.md }]}
        bounces={false}
      >
        {/* Header */}
        <View style={styles.header}>
          <TouchableOpacity onPress={() => navigation.goBack()} style={styles.backBtn}
            accessibilityRole="button"
            accessibilityLabel={t('spin.title', lang)}
          >
            <Text style={styles.backArrow}>←</Text>
          </TouchableOpacity>
          <Text style={styles.pageTitle}>{t('spin.title', lang)}</Text>
        </View>

        {/* Wheel */}
        <View style={styles.wheelArea}>
          {/* Pointer arrow above wheel */}
          <View style={styles.pointerWrap} pointerEvents="none">
            <View style={styles.pointerArrow} />
            <View style={styles.pointerStem} />
          </View>
          <Wheel
            segments={segments}
            rotateAnim={rotateAnim}
            particles={particles}
          />
        </View>

        {/* Spin button */}
        <TouchableOpacity
          accessibilityRole="button"
          accessibilityLabel={t('spin.spinning', lang)}
          style={[styles.spinBtn, (!canSpin || spinning) && styles.spinBtnOff]}
          onPress={handleSpin}
          disabled={!canSpin || spinning}
          activeOpacity={0.82}
        >
          {spinning ? (
            <View style={styles.spinBtnRow}>
              <ActivityIndicator size="small" color={colors.background} />
              <Text style={styles.spinBtnText}>{t('spin.spinning', lang)}</Text>
            </View>
          ) : (
            <Text style={styles.spinBtnText}>
              {canSpin
                ? `🎡  ${t('spin.spin', lang)}`
                : `🕐  ${t('spin.already_spun', lang)}`}
            </Text>
          )}
        </TouchableOpacity>

        {!canSpin && revealedReward == null && (
          <Text style={styles.tomorrowText}>{t('spin.tomorrow', lang)}</Text>
        )}

        {/* Error */}
        {apiError != null && (
          <View style={styles.errorBox}>
            <Text style={styles.errorText}>{apiError}</Text>
          </View>
        )}

        {/* Reward reveal card */}
        {revealedReward != null && (
          <Animated.View
            style={[
              styles.rewardCard,
              { opacity: rewardOpacity, transform: [{ scale: rewardScale }] },
            ]}
          >
            <Text style={styles.rewardBigEmoji}>{getEmoji(revealedReward.reward_type)}</Text>
            <Text style={styles.rewardCardTitle}>{t('spin.reward', lang)}</Text>
            <Text style={styles.rewardTypeText}>{getTypeLabel(revealedReward.reward_type)}</Text>
            <Text style={styles.rewardValueText}>
              {revealedReward.reward_type === 'jackpot'
                ? t('spin.jackpot', lang)
                : `+${revealedReward.reward_value}`}
            </Text>
            {revealedReward.xp_earned > 0 && (
              <Text style={styles.rewardCoinText}>✨  +{revealedReward.xp_earned} XP</Text>
            )}
            {rewardMsg != null && rewardMsg.length > 0 && (
              <Text style={styles.rewardMsg}>{rewardMsg}</Text>
            )}
          </Animated.View>
        )}

        {/* Last reward (already spun, no new spin yet) */}
        {!canSpin && revealedReward == null && lastReward != null && (
          <View style={styles.lastCard}>
            <Text style={styles.lastCardTitle}>{t('spin.last_reward', lang)}</Text>
            <View style={styles.lastCardRow}>
              <Text style={styles.lastCardEmoji}>{getEmoji(lastReward.reward_type)}</Text>
              <View>
                <Text style={styles.lastCardLabel}>{lastReward.label}</Text>
                <Text style={styles.lastCardSub}>
                  {getTypeLabel(lastReward.reward_type)}
                  {lastReward.xp_earned > 0 ? `  ·  ✨ +${lastReward.xp_earned} XP` : ''}
                </Text>
              </View>
            </View>
            <Text style={styles.tomorrowSmall}>{t('spin.try_tomorrow', lang)}</Text>
          </View>
        )}

        {/* Segments legend */}
        <Text style={styles.sectionLabel}>{t('spin.segments_title', lang)}</Text>
        <View style={styles.legendBox}>
          {segments.map((seg, i) => (
            <View
              key={i}
              style={[
                styles.legendRow,
                i === segments.length - 1 && styles.legendRowLast,
              ]}
            >
              <View style={[styles.legendDot, { backgroundColor: SEGMENT_COLORS[i % SEGMENT_COLORS.length] }]} />
              <Text style={styles.legendLabel}>{seg.label}</Text>
              <Text style={styles.legendType}>{getTypeLabel(seg.reward_type)}</Text>
            </View>
          ))}
        </View>

        <View style={{ height: (insets.bottom || spacing.md) + spacing.xl }} />
      </ScrollView>
    </View>
  );
};

// ── Styles ─────────────────────────────────────────────────────────────────────

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: colors.background },
  center:    { flex: 1, alignItems: 'center', justifyContent: 'center', backgroundColor: colors.background },
  scroll:    { paddingHorizontal: spacing.lg },

  // Header
  header:    { flexDirection: 'row', alignItems: 'center', marginBottom: spacing.lg },
  backBtn:   { marginRight: spacing.md, padding: 4 },
  backArrow: { fontSize: 22, color: colors.textPrimary },
  pageTitle: { ...(typography.h2 as object), flex: 1 } as any,

  // Wheel layout
  wheelArea: {
    alignSelf:    'center',
    alignItems:   'center',
    marginBottom: spacing.lg,
    width:        WHEEL_SIZE,
  },

  // Pointer
  pointerWrap:   { alignItems: 'center', zIndex: 10, marginBottom: -2 },
  pointerArrow:  {
    width:             0,
    height:            0,
    borderLeftWidth:   11,
    borderRightWidth:  11,
    borderTopWidth:    0,
    borderBottomWidth: 20,
    borderLeftColor:   'transparent',
    borderRightColor:  'transparent',
    borderBottomColor: colors.gold,
  },
  pointerStem: {
    width:           8,
    height:          10,
    backgroundColor: colors.gold,
    borderRadius:    4,
  },

  // Wheel circle
  wheel: {
    width:           WHEEL_SIZE,
    height:          WHEEL_SIZE,
    borderRadius:    HALF,
    overflow:        'hidden',
    backgroundColor: '#1A1A2E',
    shadowColor:     colors.gold,
    shadowOffset:    { width: 0, height: 0 },
    shadowOpacity:   0.40,
    shadowRadius:    20,
    elevation:       12,
  },

  // Segment colored strip: WHEEL_SIZE wide × HALF tall, pinned top
  // We rotate 8 of these strips around the center to fill the circle.
  segStrip: {
    position: 'absolute',
    width:    WHEEL_SIZE,
    height:   HALF,
    top:      0,
    left:     0,
  },

  // Segment label
  segLabelWrap: {
    position:       'absolute',
    width:          40,
    height:         20,
    alignItems:     'center',
    justifyContent: 'center',
    zIndex:         4,
  },
  segLabelText: {
    fontSize:   8,
    fontWeight: '800',
    color:      '#000000BB',
    textAlign:  'center',
  },

  // Divider line from wheel center outward
  divider: {
    position:        'absolute',
    width:           1.5,
    height:          HALF,
    top:             0,
    left:            0,
    backgroundColor: 'rgba(0,0,0,0.22)',
    zIndex:          3,
  },

  // Ring overlay on top of wheel
  wheelRing: {
    position:        'absolute',
    width:           WHEEL_SIZE,
    height:          WHEEL_SIZE,
    borderRadius:    HALF,
    borderWidth:     3,
    borderColor:     `${colors.gold}55`,
    zIndex:          5,
  },

  // Center hub
  hub: {
    position:        'absolute',
    width:           50,
    height:          50,
    borderRadius:    25,
    top:             HALF - 25,
    left:            HALF - 25,
    backgroundColor: colors.background,
    alignItems:      'center',
    justifyContent:  'center',
    zIndex:          6,
    borderWidth:     2.5,
    borderColor:     `${colors.gold}65`,
  },
  hubEmoji: { fontSize: 20 },

  // Confetti particle — starts at wheel center
  particle: {
    position:  'absolute',
    fontSize:  16,
    top:       HALF - 8,
    left:      HALF - 8,
    zIndex:    20,
  },

  // Spin button
  spinBtn: {
    backgroundColor:  colors.gold,
    borderRadius:     radius.lg,
    paddingVertical:  spacing.md,
    paddingHorizontal: spacing.xl,
    alignItems:       'center',
    marginBottom:     spacing.sm,
    shadowColor:      colors.gold,
    shadowOffset:     { width: 0, height: 0 },
    shadowOpacity:    0.30,
    shadowRadius:     14,
    elevation:        8,
  } as any,
  spinBtnOff:  { backgroundColor: colors.goldDark, opacity: 0.55 },
  spinBtnRow:  { flexDirection: 'row', alignItems: 'center', gap: spacing.sm },
  spinBtnText: {
    color:         colors.background,
    fontSize:      17,
    fontWeight:    '700',
    letterSpacing: 0.3,
  },

  tomorrowText: {
    ...(typography.body as object),
    color:        colors.textMuted,
    textAlign:    'center',
    marginBottom: spacing.md,
  } as any,

  // Error
  errorBox: {
    backgroundColor: '#D95F5F18',
    borderRadius:    radius.md,
    padding:         spacing.md,
    marginBottom:    spacing.md,
    borderWidth:     1,
    borderColor:     '#D95F5F35',
  },
  errorText: {
    ...(typography.body as object),
    color:     '#D95F5F',
    textAlign: 'center',
    fontSize:  13,
  } as any,

  // Reward reveal card
  rewardCard: {
    backgroundColor: colors.surface,
    borderRadius:    radius.lg,
    padding:         spacing.lg,
    alignItems:      'center',
    marginBottom:    spacing.md,
    borderWidth:     1,
    borderColor:     `${colors.gold}40`,
    shadowColor:     colors.gold,
    shadowOffset:    { width: 0, height: 0 },
    shadowOpacity:   0.30,
    shadowRadius:    14,
    elevation:       8,
  } as any,
  rewardBigEmoji:  { fontSize: 54, marginBottom: spacing.sm },
  rewardCardTitle: { ...(typography.goldLabel as object) } as any,
  rewardTypeText:  {
    ...(typography.caption as object),
    color:        colors.textMuted,
    marginBottom: spacing.xs,
  } as any,
  rewardValueText: {
    fontSize:     38,
    fontWeight:   '700',
    color:        colors.gold,
    marginBottom: spacing.xs,
  },
  rewardCoinText: {
    ...(typography.body as object),
    color:        '#F5C842',
    fontWeight:   '700',
    fontSize:     16,
    marginBottom: spacing.xs,
  } as any,
  rewardMsg: {
    ...(typography.caption as object),
    color:      colors.textSecondary,
    textAlign:  'center',
    lineHeight: 18,
    marginTop:  spacing.xs,
  } as any,

  // Last reward card
  lastCard: {
    backgroundColor: colors.surface,
    borderRadius:    radius.lg,
    padding:         spacing.md,
    marginBottom:    spacing.md,
    borderWidth:     1,
    borderColor:     colors.border,
    shadowColor:     '#000',
    shadowOffset:    { width: 0, height: 2 },
    shadowOpacity:   0.30,
    shadowRadius:    4,
    elevation:       3,
  } as any,
  lastCardTitle: {
    ...(typography.goldLabel as object),
    color:        colors.textMuted,
    marginBottom: spacing.sm,
  } as any,
  lastCardRow:   { flexDirection: 'row', alignItems: 'center', gap: spacing.sm, marginBottom: spacing.sm },
  lastCardEmoji: { fontSize: 34 },
  lastCardLabel: {
    ...(typography.body as object),
    color:      colors.textPrimary,
    fontWeight: '600',
  } as any,
  lastCardSub:   { ...(typography.caption as object), color: colors.textMuted } as any,
  tomorrowSmall: {
    ...(typography.caption as object),
    color:     colors.textMuted,
    textAlign: 'center',
  } as any,

  // Legend
  sectionLabel: {
    ...(typography.goldLabel as object),
    marginBottom: spacing.sm,
    marginTop:    spacing.sm,
  } as any,
  legendBox: {
    backgroundColor: colors.surface,
    borderRadius:    radius.md,
    borderWidth:     1,
    borderColor:     colors.border,
    overflow:        'hidden',
    shadowColor:     '#000',
    shadowOffset:    { width: 0, height: 2 },
    shadowOpacity:   0.30,
    shadowRadius:    4,
    elevation:       3,
  } as any,
  legendRow: {
    flexDirection:     'row',
    alignItems:        'center',
    paddingVertical:   spacing.sm + 2,
    paddingHorizontal: spacing.md,
    borderBottomWidth: StyleSheet.hairlineWidth,
    borderBottomColor: colors.border,
    gap:               spacing.sm,
  },
  legendRowLast: { borderBottomWidth: 0 },
  legendDot:     { width: 12, height: 12, borderRadius: 6 },
  legendLabel:   {
    ...(typography.body as object),
    color:    colors.textPrimary,
    fontSize: 13,
    flex:     1,
  } as any,
  legendType: { ...(typography.caption as object), color: colors.textMuted, fontSize: 11 } as any,
});

export default SpinWheelScreen;

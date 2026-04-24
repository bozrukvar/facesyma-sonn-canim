// src/components/ui.tsx
import React from 'react';
import {
  View, Text, TouchableOpacity, ActivityIndicator,
  TextInput, StyleSheet, ViewStyle, StyleProp,
} from 'react-native';
import theme from '../utils/theme';
const { colors, spacing, typography, radius, shadow } = theme;

// ── GoldButton ─────────────────────────────────────────────────────────────
interface ButtonProps {
  title: string;
  onPress: () => void;
  loading?: boolean;
  disabled?: boolean;
  variant?: 'gold' | 'outline' | 'ghost' | 'warm';
  style?: ViewStyle;
  icon?: string;
}
export const GoldButton: React.FC<ButtonProps> = ({
  title, onPress, loading, disabled, variant = 'gold', style, icon,
}) => {
  const bg =
    variant === 'gold'    ? colors.gold :
    variant === 'warm'    ? colors.warmAmber :
    variant === 'ghost'   ? colors.goldGlow :
    'transparent';

  const tc =
    variant === 'gold' || variant === 'warm' ? '#000' : colors.gold;

  const bc =
    variant === 'outline' ? colors.gold :
    variant === 'ghost'   ? colors.goldDark : 'transparent';

  return (
    <TouchableOpacity
      style={[{
        height:          54,
        borderRadius:    radius.lg,
        alignItems:      'center',
        justifyContent:  'center',
        flexDirection:   'row',
        gap:             8,
        backgroundColor: bg,
        borderWidth:     variant === 'outline' || variant === 'ghost' ? 1 : 0,
        borderColor:     bc,
        opacity:         disabled || loading ? 0.55 : 1,
        ...(variant === 'gold' || variant === 'warm' ? shadow.gold : {}),
      }, style]}
      onPress={onPress}
      disabled={disabled || loading}
      activeOpacity={0.82}
    >
      {loading ? (
        <ActivityIndicator color={tc} size="small" />
      ) : (
        <>
          {icon && <Text style={styles.btnIcon}>{icon}</Text>}
          <Text style={{
            ...typography.label,
            color: tc,
            letterSpacing: 1.2,
          }}>{title}</Text>
        </>
      )}
    </TouchableOpacity>
  );
};

// ── InputField ──────────────────────────────────────────────────────────────
interface InputProps {
  placeholder: string;
  value: string;
  onChangeText: (t: string) => void;
  secureTextEntry?: boolean;
  keyboardType?: 'default' | 'email-address' | 'numeric';
  autoCapitalize?: 'none' | 'sentences' | 'words' | 'characters';
  label?: string;
  error?: string;
  style?: ViewStyle;
  icon?: string;
}
export const InputField: React.FC<InputProps> = ({
  placeholder, value, onChangeText, secureTextEntry,
  keyboardType = 'default', autoCapitalize = 'none',
  label, error, style, icon,
}) => {
  const [focused, setFocused] = React.useState(false);
  return (
    <View style={[styles.inputWrapOuter, style]}>
      {label && (
        <Text style={styles.inputLabel}>{label}</Text>
      )}
      <View style={styles.inputRelative}>
        {icon && (
          <Text style={styles.inputIconText}>{icon}</Text>
        )}
        <TextInput
          style={{
            height:            52,
            backgroundColor:   focused ? colors.surfaceAlt : colors.surface,
            borderRadius:      radius.md,
            borderWidth:       1,
            borderColor:       error
              ? colors.error
              : focused ? colors.gold : colors.border,
            paddingHorizontal: icon ? 44 : spacing.md,
            color:             colors.textPrimary,
            fontSize:          15,
            fontFamily:        'System',
          }}
          placeholder={placeholder}
          placeholderTextColor={colors.textMuted}
          value={value}
          onChangeText={onChangeText}
          secureTextEntry={secureTextEntry}
          keyboardType={keyboardType}
          autoCapitalize={autoCapitalize}
          onFocus={() => setFocused(true)}
          onBlur={() => setFocused(false)}
        />
      </View>
      {error && (
        <Text style={styles.inputError}>
          {error}
        </Text>
      )}
    </View>
  );
};

// ── Card ────────────────────────────────────────────────────────────────────
interface CardProps {
  children: React.ReactNode;
  style?: StyleProp<ViewStyle>;
  variant?: 'default' | 'gold' | 'warm';
  onPress?: () => void;
}
export const Card: React.FC<CardProps> = ({ children, style, variant = 'default', onPress }) => {
  const bc =
    variant === 'gold' ? colors.goldDark :
    variant === 'warm' ? colors.borderWarm : colors.border;
  const bg =
    variant === 'gold' ? colors.goldGlow :
    variant === 'warm' ? colors.surfaceWarm : colors.surface;
  const sh = variant === 'gold' ? shadow.gold : variant === 'warm' ? shadow.warm : {};

  const content = (
    <View style={[{
      backgroundColor: bg,
      borderRadius: radius.lg,
      borderWidth: 1,
      borderColor: bc,
      padding: spacing.md,
      ...sh,
    }, style]}>
      {children}
    </View>
  );

  if (onPress) {
    return (
      <TouchableOpacity onPress={onPress} activeOpacity={0.85}>
        {content}
      </TouchableOpacity>
    );
  }
  return content;
};

// ── Divider ─────────────────────────────────────────────────────────────────
export const Divider: React.FC<{ label?: string }> = ({ label }) => (
  <View style={styles.dividerRow}>
    <View style={styles.dividerLine} />
    {label && (
      <Text style={styles.dividerLabel}>
        {label}
      </Text>
    )}
    <View style={styles.dividerLine} />
  </View>
);

// ── ErrorBanner ─────────────────────────────────────────────────────────────
export const ErrorBanner: React.FC<{ message: string }> = ({ message }) => (
  <View style={styles.errorBannerWrap}>
    <Text style={styles.errorBannerIcon}>⚠</Text>
    <Text style={styles.errorBannerText}>
      {message}
    </Text>
  </View>
);

// ── Badge ────────────────────────────────────────────────────────────────────
export const Badge: React.FC<{ label: string; color?: string }> = ({
  label, color = colors.gold,
}) => (
  <View style={{
    backgroundColor:   `${color}18`,
    borderRadius:      radius.full,
    borderWidth:       1,
    borderColor:       `${color}40`,
    paddingHorizontal: 10,
    paddingVertical:    4,
    alignSelf:        'flex-start',
  }}>
    <Text style={{ ...typography.goldLabel, color, fontSize: 9 }}>{label}</Text>
  </View>
);

// ── ScoreRing ────────────────────────────────────────────────────────────────
export const ScoreRing: React.FC<{
  score: number; label: string; size?: number;
}> = ({ score, label, size = 80 }) => {
  const color =
    score >= 80 ? colors.gold :
    score >= 60 ? colors.success :
    score >= 40 ? colors.warning : colors.error;
  return (
    <View style={styles.scoreRingOuter}>
      <View style={{
        width: size, height: size, borderRadius: size / 2,
        borderWidth: 3, borderColor: color,
        alignItems: 'center', justifyContent: 'center',
        backgroundColor: `${color}12`,
      }}>
        <Text style={{
          fontSize: size * 0.28, fontWeight: '700', color,
          fontFamily: 'Georgia',
        }}>{score}</Text>
      </View>
      {label ? (
        <Text style={styles.scoreRingLabel}>
          {label}
        </Text>
      ) : null}
    </View>
  );
};

// ── WarmAvatar ───────────────────────────────────────────────────────────────
export const WarmAvatar: React.FC<{
  letter?: string; size?: number; emoji?: string;
}> = ({ letter, size = 44, emoji }) => (
  <View style={{
    width: size, height: size, borderRadius: size / 2,
    backgroundColor: colors.goldGlow,
    borderWidth: 1.5, borderColor: colors.goldDark,
    alignItems: 'center', justifyContent: 'center',
  }}>
    {emoji
      ? <Text style={{ fontSize: size * 0.44 }}>{emoji}</Text>
      : <Text style={{
          fontFamily: 'Georgia', fontSize: size * 0.40,
          color: colors.gold, fontWeight: '700',
        }}>{letter}</Text>
    }
  </View>
);

// ── SectionLabel ─────────────────────────────────────────────────────────────
export const SectionLabel: React.FC<{ children: string }> = ({ children }) => (
  <Text style={styles.sectionLabel}>{children}</Text>
);

const styles = StyleSheet.create({
  btnIcon:         { fontSize: 16 },
  inputWrapOuter:  { marginBottom: spacing.md },
  inputLabel:      { ...typography.goldLabel, marginBottom: 6 },
  inputRelative:   { position: 'relative' as const },
  inputIconText:   { position: 'absolute' as const, left: 14, top: 14, fontSize: 16, zIndex: 1 },
  inputError:      { ...typography.caption, color: colors.error, marginTop: 4 },
  dividerRow:      { flexDirection: 'row' as const, alignItems: 'center' as const, marginVertical: spacing.md },
  dividerLine:     { flex: 1, height: 1, backgroundColor: colors.border },
  dividerLabel:    { ...typography.caption, marginHorizontal: 14, color: colors.textMuted },
  errorBannerWrap: {
    backgroundColor: 'rgba(217,95,95,0.1)',
    borderRadius:    radius.sm,
    borderWidth:     1,
    borderColor:     colors.error,
    padding:         spacing.md,
    marginBottom:    spacing.md,
    flexDirection:   'row' as const,
    alignItems:      'center' as const,
    gap:             8,
  },
  errorBannerIcon: { fontSize: 14 },
  errorBannerText: { ...typography.caption, color: colors.error, fontSize: 13, flex: 1 },
  sectionLabel:    { ...typography.goldLabel, marginBottom: spacing.sm, marginTop: spacing.sm },
  scoreRingOuter:  { alignItems: 'center' as const },
  scoreRingLabel:  { ...typography.caption, marginTop: 5, textAlign: 'center' as const },
});

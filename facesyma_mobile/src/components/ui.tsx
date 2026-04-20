// src/components/ui.tsx
import React from 'react';
import {
  View, Text, TouchableOpacity, ActivityIndicator,
  TextInput, StyleSheet, ViewStyle,
} from 'react-native';
import theme from '../utils/theme';

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
    variant === 'gold'    ? theme.colors.gold :
    variant === 'warm'    ? theme.colors.warmAmber :
    variant === 'ghost'   ? theme.colors.goldGlow :
    'transparent';

  const tc =
    variant === 'gold' || variant === 'warm' ? '#000' : theme.colors.gold;

  const bc =
    variant === 'outline' ? theme.colors.gold :
    variant === 'ghost'   ? theme.colors.goldDark : 'transparent';

  return (
    <TouchableOpacity
      style={[{
        height:          54,
        borderRadius:    theme.radius.lg,
        alignItems:      'center',
        justifyContent:  'center',
        flexDirection:   'row',
        gap:             8,
        backgroundColor: bg,
        borderWidth:     variant === 'outline' || variant === 'ghost' ? 1 : 0,
        borderColor:     bc,
        opacity:         disabled || loading ? 0.55 : 1,
        ...(variant === 'gold' || variant === 'warm' ? theme.shadow.gold : {}),
      }, style]}
      onPress={onPress}
      disabled={disabled || loading}
      activeOpacity={0.82}
    >
      {loading ? (
        <ActivityIndicator color={tc} size="small" />
      ) : (
        <>
          {icon && <Text style={{ fontSize: 16 }}>{icon}</Text>}
          <Text style={{
            ...theme.typography.label,
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
    <View style={[{ marginBottom: theme.spacing.md }, style]}>
      {label && (
        <Text style={{ ...theme.typography.goldLabel, marginBottom: 6 }}>{label}</Text>
      )}
      <View style={{ position: 'relative' }}>
        {icon && (
          <Text style={{
            position: 'absolute', left: 14, top: 14,
            fontSize: 16, zIndex: 1,
          }}>{icon}</Text>
        )}
        <TextInput
          style={{
            height:            52,
            backgroundColor:   focused ? theme.colors.surfaceAlt : theme.colors.surface,
            borderRadius:      theme.radius.md,
            borderWidth:       1,
            borderColor:       error
              ? theme.colors.error
              : focused ? theme.colors.gold : theme.colors.border,
            paddingHorizontal: icon ? 44 : theme.spacing.md,
            color:             theme.colors.textPrimary,
            fontSize:          15,
            fontFamily:        'System',
          }}
          placeholder={placeholder}
          placeholderTextColor={theme.colors.textMuted}
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
        <Text style={{ ...theme.typography.caption, color: theme.colors.error, marginTop: 4 }}>
          {error}
        </Text>
      )}
    </View>
  );
};

// ── Card ────────────────────────────────────────────────────────────────────
interface CardProps {
  children: React.ReactNode;
  style?: ViewStyle;
  variant?: 'default' | 'gold' | 'warm';
  onPress?: () => void;
}
export const Card: React.FC<CardProps> = ({ children, style, variant = 'default', onPress }) => {
  const bc =
    variant === 'gold' ? theme.colors.goldDark :
    variant === 'warm' ? theme.colors.borderWarm : theme.colors.border;
  const bg =
    variant === 'gold' ? theme.colors.goldGlow :
    variant === 'warm' ? theme.colors.surfaceWarm : theme.colors.surface;
  const sh = variant === 'gold' ? theme.shadow.gold : variant === 'warm' ? theme.shadow.warm : {};

  const content = (
    <View style={[{
      backgroundColor: bg,
      borderRadius: theme.radius.lg,
      borderWidth: 1,
      borderColor: bc,
      padding: theme.spacing.md,
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
  <View style={{ flexDirection: 'row', alignItems: 'center', marginVertical: theme.spacing.md }}>
    <View style={{ flex: 1, height: 1, backgroundColor: theme.colors.border }} />
    {label && (
      <Text style={{ ...theme.typography.caption, marginHorizontal: 14, color: theme.colors.textMuted }}>
        {label}
      </Text>
    )}
    <View style={{ flex: 1, height: 1, backgroundColor: theme.colors.border }} />
  </View>
);

// ── ErrorBanner ─────────────────────────────────────────────────────────────
export const ErrorBanner: React.FC<{ message: string }> = ({ message }) => (
  <View style={{
    backgroundColor: 'rgba(217,95,95,0.1)',
    borderRadius:    theme.radius.sm,
    borderWidth:     1,
    borderColor:     theme.colors.error,
    padding:         theme.spacing.md,
    marginBottom:    theme.spacing.md,
    flexDirection:   'row',
    alignItems:      'center',
    gap:             8,
  }}>
    <Text style={{ fontSize: 14 }}>⚠</Text>
    <Text style={{ ...theme.typography.caption, color: theme.colors.error, fontSize: 13, flex: 1 }}>
      {message}
    </Text>
  </View>
);

// ── Badge ────────────────────────────────────────────────────────────────────
export const Badge: React.FC<{ label: string; color?: string }> = ({
  label, color = theme.colors.gold,
}) => (
  <View style={{
    backgroundColor:   `${color}18`,
    borderRadius:      theme.radius.full,
    borderWidth:       1,
    borderColor:       `${color}40`,
    paddingHorizontal: 10,
    paddingVertical:    4,
    alignSelf:        'flex-start',
  }}>
    <Text style={{ ...theme.typography.goldLabel, color, fontSize: 9 }}>{label}</Text>
  </View>
);

// ── ScoreRing ────────────────────────────────────────────────────────────────
export const ScoreRing: React.FC<{
  score: number; label: string; size?: number;
}> = ({ score, label, size = 80 }) => {
  const color =
    score >= 80 ? theme.colors.gold :
    score >= 60 ? theme.colors.success :
    score >= 40 ? theme.colors.warning : theme.colors.error;
  return (
    <View style={{ alignItems: 'center' }}>
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
        <Text style={{ ...theme.typography.caption, marginTop: 5, textAlign: 'center' }}>
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
    backgroundColor: theme.colors.goldGlow,
    borderWidth: 1.5, borderColor: theme.colors.goldDark,
    alignItems: 'center', justifyContent: 'center',
  }}>
    {emoji
      ? <Text style={{ fontSize: size * 0.44 }}>{emoji}</Text>
      : <Text style={{
          fontFamily: 'Georgia', fontSize: size * 0.40,
          color: theme.colors.gold, fontWeight: '700',
        }}>{letter}</Text>
    }
  </View>
);

// ── SectionLabel ─────────────────────────────────────────────────────────────
export const SectionLabel: React.FC<{ children: string }> = ({ children }) => (
  <Text style={{
    ...theme.typography.goldLabel,
    marginBottom: theme.spacing.sm,
    marginTop:    theme.spacing.sm,
  }}>{children}</Text>
);

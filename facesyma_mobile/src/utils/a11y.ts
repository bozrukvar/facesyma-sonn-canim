/**
 * a11y.ts — Accessibility helpers for React Native
 *
 * Usage:
 *   import { btn, img, input, header } from '../utils/a11y';
 *
 *   <TouchableOpacity {...btn('Login')}>
 *   <Image {...img('Profile photo')} />
 *   <TextInput {...input('Email address')} />
 *   <Text {...header()}>{t('home.modules', lang)}</Text>
 *   <Image {...decorative()} />   // purely decorative — VoiceOver skips it
 */

import type { AccessibilityRole } from 'react-native';

/** Props for an interactive button */
export const btn = (label: string, hint?: string) => ({
  accessible: true,
  accessibilityRole: 'button' as AccessibilityRole,
  accessibilityLabel: label,
  ...(hint ? { accessibilityHint: hint } : {}),
});

/** Props for a navigation button (goes somewhere) */
export const navBtn = (label: string, destination?: string) => ({
  accessible: true,
  accessibilityRole: 'button' as AccessibilityRole,
  accessibilityLabel: label,
  ...(destination ? { accessibilityHint: `${destination} ekranına gider` } : {}),
});

/** Props for a link */
export const lnk = (label: string) => ({
  accessible: true,
  accessibilityRole: 'link' as AccessibilityRole,
  accessibilityLabel: label,
});

/** Props for an informative image */
export const img = (label: string) => ({
  accessible: true,
  accessibilityRole: 'image' as AccessibilityRole,
  accessibilityLabel: label,
});

/** Props for a decorative image/icon — VoiceOver skips it */
export const decorative = () => ({
  accessible: false,
  importantForAccessibility: 'no' as const,
});

/** Props for a TextInput label */
export const input = (label: string, hint?: string) => ({
  accessible: true,
  accessibilityLabel: label,
  ...(hint ? { accessibilityHint: hint } : {}),
});

/** Props for a section header Text */
export const header = () => ({
  accessible: true,
  accessibilityRole: 'header' as AccessibilityRole,
});

/** Props for a checkbox / toggle */
export const toggle = (label: string, checked: boolean) => ({
  accessible: true,
  accessibilityRole: 'checkbox' as AccessibilityRole,
  accessibilityLabel: label,
  accessibilityState: { checked },
});

/** Props for an expandable section */
export const expandable = (label: string, expanded: boolean) => ({
  accessible: true,
  accessibilityRole: 'button' as AccessibilityRole,
  accessibilityLabel: label,
  accessibilityState: { expanded },
});

/** Props for a disabled button */
export const disabledBtn = (label: string) => ({
  accessible: true,
  accessibilityRole: 'button' as AccessibilityRole,
  accessibilityLabel: label,
  accessibilityState: { disabled: true },
});

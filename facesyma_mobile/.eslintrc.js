module.exports = {
  root: true,
  extends: ['@react-native'],
  plugins: ['react-native-a11y'],
  rules: {
    // ── Accessibility (App Store / Play Store requirement) ─────────────────
    // All interactive elements must have an accessibilityLabel
    'react-native-a11y/has-accessibility-props': 'error',
    // All interactive elements must have a valid accessibilityRole
    'react-native-a11y/has-valid-accessibility-role': 'error',
    // Images need accessibilityLabel or accessible={false}
    'react-native-a11y/has-valid-accessibility-descriptors': 'warn',
  },
};

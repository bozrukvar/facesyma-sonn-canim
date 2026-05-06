// Firebase native modules disabled — no google-services.json on dev.
// notifications.ts already handles missing modules gracefully (no-op).
module.exports = {
  dependencies: {
    '@react-native-firebase/app': { platforms: { android: null, ios: null } },
    '@react-native-firebase/messaging': { platforms: { android: null, ios: null } },
  },
};

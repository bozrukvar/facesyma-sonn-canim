// src/services/notifications.ts
// FCM push notification integration.
//
// Native setup required (once, before building):
//   1. npm install @react-native-firebase/app @react-native-firebase/messaging
//   2. Place google-services.json in android/app/
//   3. Add to android/build.gradle:  classpath 'com.google.gms:google-services:4.4.0'
//   4. Add to android/app/build.gradle:  apply plugin: 'com.google.gms.google-services'
//   5. For iOS: add GoogleService-Info.plist + run `npx pod-install`
//
// Until native setup is done the module is safely absent — all calls no-op.

import { Platform } from 'react-native';
import { AuthAPI } from './api';

// ── Lazy module accessor ──────────────────────────────────────────────────────
// Using require() so TypeScript doesn't error when the native module is absent.

type RemoteMessage = {
  notification?: { title?: string; body?: string };
  data?: Record<string, string>;
};

type Messaging = {
  requestPermission(): Promise<number>;
  getToken(): Promise<string>;
  onMessage(handler: (msg: RemoteMessage) => void): () => void;
  onNotificationOpenedApp(handler: (msg: RemoteMessage) => void): () => void;
  getInitialNotification(): Promise<RemoteMessage | null>;
  onTokenRefresh(handler: (token: string) => void): () => void;
  AuthorizationStatus: { AUTHORIZED: number; PROVISIONAL: number };
};

function getMessaging(): Messaging | null {
  try {
    // Guard: if native module is absent (dev build without google-services.json), no-op.
    // eslint-disable-next-line @typescript-eslint/no-var-requires
    const { NativeModules } = require('react-native');
    if (!NativeModules.RNFBAppModule) return null;
    // eslint-disable-next-line @typescript-eslint/no-var-requires
    return require('@react-native-firebase/messaging').default();
  } catch {
    return null;
  }
}

// ── Permission ────────────────────────────────────────────────────────────────

async function requestPermission(): Promise<boolean> {
  const m = getMessaging();
  if (!m) return false;

  if (Platform.OS === 'ios') {
    const status = await m.requestPermission();
    return (
      status === m.AuthorizationStatus.AUTHORIZED ||
      status === m.AuthorizationStatus.PROVISIONAL
    );
  }
  // Android 13+ requires POST_NOTIFICATIONS at runtime; handled by the OS prompt
  // that firebase/messaging triggers automatically on Android.
  return true;
}

// ── Token registration ────────────────────────────────────────────────────────

export async function registerDeviceToken(): Promise<void> {
  const m = getMessaging();
  if (!m) return;

  try {
    const granted = await requestPermission();
    if (!granted) return;

    const token = await m.getToken();
    if (token) {
      await AuthAPI.registerDeviceToken(token, Platform.OS as 'ios' | 'android');
    }
  } catch (e) {
    // Non-critical — app works fine without push
    console.warn('[FCM] token registration failed:', e);
  }
}

// ── Notification handlers (call once on app start) ────────────────────────────

export function setupNotificationHandlers(): void {
  const m = getMessaging();
  if (!m) return;

  // Foreground messages — show in-app banner or handle silently
  m.onMessage(async _msg => {
    // TODO: show an in-app toast/banner if needed
  });

  // Tapped while app is in background
  m.onNotificationOpenedApp(_msg => {
    // TODO: navigate to relevant screen based on msg.data
  });

  // Tapped while app was fully quit
  m.getInitialNotification().then(_msg => {
    if (_msg) {
      // TODO: handle cold-start navigation
    }
  });

  // Token refresh — keep backend in sync
  m.onTokenRefresh(token => {
    AuthAPI.registerDeviceToken(token, Platform.OS as 'ios' | 'android').catch(() => {});
  });
}

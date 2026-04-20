# Facesyma Mobile — Kurulum Kılavuzu

## Gereksinimler
- Node.js 18+
- Android Studio + JDK 17
- iOS (macOS): Xcode 15+ + CocoaPods

## 1. Bağımlılıkları Yükle
```bash
npm install
```

## 2. Google Sign-In Yapılandırması
Google Cloud Console → Credentials → OAuth 2.0 Client ID oluştur.

**`src/screens/AuthScreen.tsx`:**
```ts
GoogleSignin.configure({
  webClientId: 'BURAYA_WEB_CLIENT_ID.apps.googleusercontent.com',
});
```

**`android/app/build.gradle`:**
```gradle
resValue "string", "server_client_id", "BURAYA_WEB_CLIENT_ID.apps.googleusercontent.com"
```

**`ios/FacesymaMobile/Info.plist`:**
```xml
<key>GIDClientID</key>
<string>BURAYA_IOS_CLIENT_ID.apps.googleusercontent.com</string>
```

## 3. Android
```bash
npx react-native run-android
```

## 4. iOS
```bash
cd ios && pod install && cd ..
npx react-native run-ios
```

## 5. API URL Güncelle
`src/services/api.ts` → `SERVICES` bloğuna kendi sunucu URL'ini yaz.

// src/screens/AuthScreen.tsx
import React, { useState } from 'react';
import {
  View, Text, StyleSheet, ScrollView, KeyboardAvoidingView,
  Platform, TouchableOpacity, Dimensions, Alert,
} from 'react-native';
import { useDispatch, useSelector } from 'react-redux';
import { GoogleSignin, statusCodes } from '@react-native-google-signin/google-signin';
import { AppDispatch, RootState } from '../store';
import { loginWithEmail, loginWithGoogle, registerWithEmail, clearError } from '../store/authSlice';
import { GoldButton, InputField, Divider, ErrorBanner } from '../components/ui';
import { AuthAPI } from '../services/api';
import theme from '../utils/theme';
const { colors, spacing, typography, radius, shadow } = theme;
import { useLanguage } from '../utils/LanguageContext';
import { t } from '../utils/i18n';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import type { ScreenProps } from '../navigation/types';

const { width } = Dimensions.get('window');

GoogleSignin.configure({
  webClientId: 'YOUR_GOOGLE_WEB_CLIENT_ID.apps.googleusercontent.com',
});

type Mode = 'login' | 'register';

const AuthScreen = ({ navigation }: ScreenProps<'Auth'>) => {
  const insets   = useSafeAreaInsets();
  const dispatch = useDispatch<AppDispatch>();
  const { isLoading, error } = useSelector((s: RootState) => s.auth);
  const { lang } = useLanguage();

  const [mode,     setMode]     = useState<Mode>('login');
  const [email,    setEmail]    = useState('');
  const [password, setPassword] = useState('');
  const [name,     setName]     = useState('');
  const [confirm,  setConfirm]  = useState('');
  const [localErr, setLocalErr] = useState('');

  const switchMode = (m: Mode) => { setMode(m); dispatch(clearError()); setLocalErr(''); };

  const handleForgotPassword = async () => {
    if (!email.trim()) {
      setLocalErr(t('auth.error_email_password', lang));
      return;
    }
    const fpTitle = t('auth.forgot_password', lang);
    const fpMsg   = t('auth.forgot_sent', lang);
    try {
      await AuthAPI.forgotPassword(email.trim().toLowerCase());
      Alert.alert(fpTitle, fpMsg);
    } catch {
      Alert.alert(fpTitle, fpMsg);
      // Backend henüz email göndermese de UI'da başarılı gibi göster (güvenlik)
    }
  };

  const handleSubmit = async () => {
    setLocalErr(''); dispatch(clearError());
    if (!email || !password) { setLocalErr(t('auth.error_email_password', lang)); return; }
    if (mode === 'register') {
      if (!name.trim())         { setLocalErr(t('common.required', lang)); return; }
      if (password.length < 6)  { setLocalErr(t('auth.error_password_min', lang)); return; }
      if (password !== confirm)  { setLocalErr(t('common.generic_error', lang)); return; }
      const r = await dispatch(registerWithEmail({ email, password, name }));
      if (registerWithEmail.fulfilled.match(r)) navigation.replace('Main');
    } else {
      const r = await dispatch(loginWithEmail({ email, password }));
      if (loginWithEmail.fulfilled.match(r)) navigation.replace('Main');
    }
  };

  const handleGoogle = async () => {
    dispatch(clearError()); setLocalErr('');
    const genericErr = t('common.generic_error', lang);
    try {
      await GoogleSignin.hasPlayServices();
      const info = await GoogleSignin.signIn();
      if (!info.idToken) { setLocalErr(genericErr); return; }
      const r = await dispatch(loginWithGoogle(info.idToken));
      if (loginWithGoogle.fulfilled.match(r)) navigation.replace('Main');
    } catch (e: any) {
      if (e.code !== statusCodes.SIGN_IN_CANCELLED && e.code !== statusCodes.IN_PROGRESS)
        setLocalErr(genericErr);
    }
  };

  const displayErr = localErr || error;

  return (
    <KeyboardAvoidingView
      style={styles.container}
      behavior={Platform.OS === 'ios' ? 'padding' : undefined}
    >
      <ScrollView
        contentContainerStyle={[styles.scroll, { paddingTop: insets.top + spacing.xl }]}
        keyboardShouldPersistTaps="handled"
        showsVerticalScrollIndicator={false}
      >
        {/* Logo */}
        <View style={styles.logoWrap}>
          <View style={styles.logoRing}>
            <Text style={styles.logoEmoji}>👁</Text>
          </View>
          <Text style={styles.logoName}>FACESYMA</Text>
          <Text style={styles.logoSub}>
            {mode === 'login' ? t('auth.welcome_back', lang) : t('auth.description', lang)}
          </Text>
        </View>

        {/* Tab seçimi */}
        <View style={styles.tabs}>
          {(['login', 'register'] as Mode[]).map(m => (
            <TouchableOpacity
              key={m}
              style={[styles.tab, mode === m && styles.tabActive]}
              onPress={() => switchMode(m)}
              activeOpacity={0.8}
            >
              <Text style={[styles.tabText, mode === m && styles.tabTextActive]}>
                {m === 'login' ? t('auth.sign_in', lang) : t('auth.sign_up', lang)}
              </Text>
            </TouchableOpacity>
          ))}
        </View>

        {displayErr ? <ErrorBanner message={displayErr} /> : null}

        {mode === 'register' && (
          <InputField
            label={t('auth.name', lang)}
            placeholder={t('auth.name', lang).toLowerCase()}
            value={name}
            onChangeText={setName}
            autoCapitalize="words"
            icon="👤"
          />
        )}
        <InputField
          label={t('auth.email', lang)}
          placeholder="example@mail.com"
          value={email}
          onChangeText={setEmail}
          keyboardType="email-address"
          icon="✉"
        />
        <InputField
          label={t('auth.password', lang)}
          placeholder={t('auth.error_password_min', lang)}
          value={password}
          onChangeText={setPassword}
          secureTextEntry
          icon="🔒"
        />
        {mode === 'register' && (
          <InputField
            label={t('auth.password_confirm', lang)}
            placeholder={t('auth.password', lang).toLowerCase()}
            value={confirm}
            onChangeText={setConfirm}
            secureTextEntry
            icon="🔒"
          />
        )}

        {mode === 'login' && (
          <TouchableOpacity style={styles.forgotBtn} onPress={handleForgotPassword}>
            <Text style={styles.forgotText}>{t('auth.forgot_password', lang)}</Text>
          </TouchableOpacity>
        )}

        <GoldButton
          title={mode === 'login' ? t('auth.sign_in', lang) : t('auth.sign_up', lang)}
          onPress={handleSubmit}
          loading={isLoading}
          style={styles.submitBtn}
        />

        <Divider label={t('auth.or', lang)} />

        {/* Google */}
        <TouchableOpacity
          style={styles.googleBtn}
          onPress={handleGoogle}
          disabled={isLoading}
          activeOpacity={0.85}
        >
          <View style={styles.googleIcon}><Text style={styles.googleIconText}>G</Text></View>
          <Text style={styles.googleText}>{t('auth.google', lang)}</Text>
        </TouchableOpacity>

        {mode === 'register' && (
          <Text style={styles.privacyText}>
            {t('auth.privacy', lang)}
          </Text>
        )}
      </ScrollView>
    </KeyboardAvoidingView>
  );
};

const styles = StyleSheet.create({
  container: { flex:1, backgroundColor: colors.background },
  scroll: {
    flexGrow: 1,
    paddingHorizontal: spacing.lg,
    paddingTop: spacing.xxxl,
    paddingBottom: spacing.xxl,
  },
  logoWrap:  { alignItems:'center', marginBottom: spacing.xl },
  logoRing:  {
    width:64, height:64, borderRadius:32,
    borderWidth:1.5, borderColor: colors.gold,
    backgroundColor: colors.goldGlow,
    alignItems:'center', justifyContent:'center',
    marginBottom: spacing.md,
    ...shadow.gold,
  },
  logoName:  { ...typography.goldLabel, fontSize:18, letterSpacing:5, color: colors.gold, marginBottom:4 },
  logoSub:   { ...typography.bodyWarm, color: colors.textWarm },
  tabs: {
    flexDirection:'row', backgroundColor: colors.surface,
    borderRadius: radius.md, padding:4, marginBottom: spacing.lg,
  },
  tab:       { flex:1, height:40, alignItems:'center', justifyContent:'center', borderRadius: radius.sm },
  tabActive: { backgroundColor: colors.surfaceAlt, borderWidth:1, borderColor: colors.border },
  tabText:   { ...typography.label, color: colors.textMuted, fontSize:12 },
  tabTextActive: { color: colors.textPrimary },
  forgotBtn: { alignSelf:'flex-end', marginBottom: spacing.md, marginTop:-spacing.sm },
  forgotText:{ ...typography.caption, color: colors.gold, fontSize:12 },
  googleBtn: {
    height:54, backgroundColor: colors.surface,
    borderRadius: radius.lg,
    borderWidth:1, borderColor: colors.border,
    flexDirection:'row', alignItems:'center', justifyContent:'center', gap:12,
  },
  googleIcon:{
    width:28, height:28, borderRadius:14,
    backgroundColor:'#4285F4',
    alignItems:'center', justifyContent:'center',
  },
  googleText:    { ...typography.label, color: colors.textPrimary, fontSize:13, letterSpacing:0.5 },
  googleIconText:{ color:'#fff', fontSize:13, fontWeight:'700' as const },
  privacyText:   { ...typography.caption, textAlign:'center', marginTop: spacing.lg, lineHeight:18 },
  logoEmoji:     { fontSize: 32 },
  submitBtn:     { marginTop: spacing.sm },
});

export default AuthScreen;

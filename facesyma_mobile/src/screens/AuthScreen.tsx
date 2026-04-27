// src/screens/AuthScreen.tsx
import React, { useState } from 'react';
import {
  View, Text, StyleSheet, ScrollView, KeyboardAvoidingView,
  Platform, TouchableOpacity, Dimensions, Alert, Linking, Image,
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

const TERMS_URL   = 'https://facesyma.com/wp-content/uploads/2024/07/maula-en.pdf';
const PRIVACY_URL = 'https://facesyma.com/wp-content/uploads/2024/07/ppa-en.pdf';

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

  const [mode,          setMode]          = useState<Mode>('login');
  const [email,         setEmail]         = useState('');
  const [password,      setPassword]      = useState('');
  const [name,          setName]          = useState('');
  const [confirm,       setConfirm]       = useState('');
  const [localErr,      setLocalErr]      = useState('');
  const [termsAccepted, setTermsAccepted] = useState(false);

  const switchMode = (m: Mode) => { setMode(m); dispatch(clearError()); setLocalErr(''); setTermsAccepted(false); };

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
      if (!termsAccepted)        { setLocalErr(t('auth.error_terms', lang)); return; }
      const r = await dispatch(registerWithEmail({ email, password, name, terms_accepted: true, gdpr_consent: true }));
      if (registerWithEmail.fulfilled.match(r)) navigation.replace('ProfileSetup');
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
          <Image
            source={require('../assets/logo.png')}
            style={styles.logoImg}
            resizeMode="contain"
          />
          <View style={styles.logoTextRow}>
            <Text style={styles.logoName}>FaceSyma</Text>
            <View style={styles.aiBadge}>
              <Text style={styles.aiBadgeText}>AI</Text>
            </View>
          </View>
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

        {mode === 'register' && (
          <TouchableOpacity
            style={styles.termsRow}
            onPress={() => setTermsAccepted(p => !p)}
            activeOpacity={0.8}
          >
            <View style={[styles.checkbox, termsAccepted && styles.checkboxChecked]}>
              {termsAccepted && <Text style={styles.checkmark}>✓</Text>}
            </View>
            <Text style={styles.termsText}>
              <Text onPress={() => Linking.openURL(TERMS_URL)} style={styles.termsLink}>
                {t('auth.terms_of_use', lang)}
              </Text>
              {' '}{t('auth.and', lang)}{' '}
              <Text onPress={() => Linking.openURL(PRIVACY_URL)} style={styles.termsLink}>
                {t('auth.privacy_policy', lang)}
              </Text>
              {t('auth.terms_accept_suffix', lang)}
            </Text>
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
  logoImg: {
    width: 80,
    height: 80,
    marginBottom: spacing.md,
  },
  logoTextRow: { flexDirection: 'row', alignItems: 'center', gap: 6, marginBottom: 4 },
  logoName:  { fontFamily: 'Georgia', fontSize: 22, fontWeight: '700' as const, letterSpacing: 1, color: colors.gold },
  aiBadge: {
    backgroundColor: colors.gold,
    borderRadius: 5,
    paddingHorizontal: 6,
    paddingVertical: 2,
    alignSelf: 'center',
  },
  aiBadgeText: { fontFamily: 'System', fontSize: 11, fontWeight: '800' as const, color: '#060F14', letterSpacing: 1 },
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
  submitBtn:     { marginTop: spacing.sm },
  termsRow: {
    flexDirection: 'row', alignItems: 'flex-start',
    marginTop: spacing.md, gap: spacing.sm,
  },
  checkbox: {
    width: 22, height: 22, borderRadius: 6,
    borderWidth: 1.5, borderColor: colors.border,
    alignItems: 'center', justifyContent: 'center',
    marginTop: 1,
  },
  checkboxChecked: { backgroundColor: colors.gold, borderColor: colors.gold },
  checkmark:  { color: '#000', fontSize: 13, fontWeight: '700' as const },
  termsText:  { ...typography.caption, flex: 1, lineHeight: 20, color: colors.textMuted },
  termsLink:  { color: colors.gold, textDecorationLine: 'underline' as const },
  webViewContainer: { flex: 1, backgroundColor: colors.background },
  webViewClose: {
    paddingHorizontal: spacing.lg, paddingVertical: spacing.md,
    borderBottomWidth: 1, borderColor: colors.border,
  },
  webViewCloseText: { ...typography.label, color: colors.gold },
});

export default AuthScreen;

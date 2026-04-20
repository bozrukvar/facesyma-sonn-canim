// src/screens/AuthScreen.tsx
import React, { useState } from 'react';
import {
  View, Text, StyleSheet, ScrollView, KeyboardAvoidingView,
  Platform, TouchableOpacity, Dimensions,
} from 'react-native';
import { useDispatch, useSelector } from 'react-redux';
import { GoogleSignin, statusCodes } from '@react-native-google-signin/google-signin';
import { AppDispatch, RootState } from '../store';
import { loginWithEmail, loginWithGoogle, registerWithEmail, clearError } from '../store/authSlice';
import { GoldButton, InputField, Divider, ErrorBanner } from '../components/ui';
import theme from '../utils/theme';
import { useLanguage } from '../utils/LanguageContext';
import { t } from '../utils/i18n';

const { width } = Dimensions.get('window');

GoogleSignin.configure({
  webClientId: 'YOUR_GOOGLE_WEB_CLIENT_ID.apps.googleusercontent.com',
});

type Mode = 'login' | 'register';

const AuthScreen: React.FC<{ navigation: any }> = ({ navigation }) => {
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
    try {
      await GoogleSignin.hasPlayServices();
      const info = await GoogleSignin.signIn();
      if (!info.idToken) { setLocalErr(t('common.generic_error', lang)); return; }
      const r = await dispatch(loginWithGoogle(info.idToken));
      if (loginWithGoogle.fulfilled.match(r)) navigation.replace('Main');
    } catch (e: any) {
      if (e.code !== statusCodes.SIGN_IN_CANCELLED && e.code !== statusCodes.IN_PROGRESS)
        setLocalErr(t('common.generic_error', lang));
    }
  };

  const displayErr = localErr || error;

  return (
    <KeyboardAvoidingView
      style={styles.container}
      behavior={Platform.OS === 'ios' ? 'padding' : undefined}
    >
      <ScrollView
        contentContainerStyle={styles.scroll}
        keyboardShouldPersistTaps="handled"
        showsVerticalScrollIndicator={false}
      >
        {/* Logo */}
        <View style={styles.logoWrap}>
          <View style={styles.logoRing}>
            <Text style={{ fontSize: 32 }}>👁</Text>
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
          <TouchableOpacity style={styles.forgotBtn}>
            <Text style={styles.forgotText}>{t('auth.forgot_password', lang)}</Text>
          </TouchableOpacity>
        )}

        <GoldButton
          title={mode === 'login' ? t('auth.sign_in', lang) : t('auth.sign_up', lang)}
          onPress={handleSubmit}
          loading={isLoading}
          style={{ marginTop: theme.spacing.sm }}
        />

        <Divider label={t('auth.or', lang)} />

        {/* Google */}
        <TouchableOpacity
          style={styles.googleBtn}
          onPress={handleGoogle}
          disabled={isLoading}
          activeOpacity={0.85}
        >
          <View style={styles.googleIcon}><Text style={{ color:'#fff', fontSize:13, fontWeight:'700' }}>G</Text></View>
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
  container: { flex:1, backgroundColor: theme.colors.background },
  scroll: {
    flexGrow: 1,
    paddingHorizontal: theme.spacing.lg,
    paddingTop: theme.spacing.xxxl,
    paddingBottom: theme.spacing.xxl,
  },
  logoWrap:  { alignItems:'center', marginBottom: theme.spacing.xl },
  logoRing:  {
    width:64, height:64, borderRadius:32,
    borderWidth:1.5, borderColor: theme.colors.gold,
    backgroundColor: theme.colors.goldGlow,
    alignItems:'center', justifyContent:'center',
    marginBottom: theme.spacing.md,
    ...theme.shadow.gold,
  },
  logoName:  { ...theme.typography.goldLabel, fontSize:18, letterSpacing:5, color: theme.colors.gold, marginBottom:4 },
  logoSub:   { ...theme.typography.bodyWarm, color: theme.colors.textWarm },
  tabs: {
    flexDirection:'row', backgroundColor: theme.colors.surface,
    borderRadius: theme.radius.md, padding:4, marginBottom: theme.spacing.lg,
  },
  tab:       { flex:1, height:40, alignItems:'center', justifyContent:'center', borderRadius: theme.radius.sm },
  tabActive: { backgroundColor: theme.colors.surfaceAlt, borderWidth:1, borderColor: theme.colors.border },
  tabText:   { ...theme.typography.label, color: theme.colors.textMuted, fontSize:12 },
  tabTextActive: { color: theme.colors.textPrimary },
  forgotBtn: { alignSelf:'flex-end', marginBottom: theme.spacing.md, marginTop:-theme.spacing.sm },
  forgotText:{ ...theme.typography.caption, color: theme.colors.gold, fontSize:12 },
  googleBtn: {
    height:54, backgroundColor: theme.colors.surface,
    borderRadius: theme.radius.lg,
    borderWidth:1, borderColor: theme.colors.border,
    flexDirection:'row', alignItems:'center', justifyContent:'center', gap:12,
  },
  googleIcon:{
    width:28, height:28, borderRadius:14,
    backgroundColor:'#4285F4',
    alignItems:'center', justifyContent:'center',
  },
  googleText:{ ...theme.typography.label, color: theme.colors.textPrimary, fontSize:13, letterSpacing:0.5 },
  privacyText:{ ...theme.typography.caption, textAlign:'center', marginTop: theme.spacing.lg, lineHeight:18 },
});

export default AuthScreen;

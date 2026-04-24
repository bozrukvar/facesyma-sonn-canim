// src/screens/ProfileScreen.tsx
import React from 'react';
import {
  View, Text, StyleSheet, ScrollView, TouchableOpacity, Alert,
} from 'react-native';
import { useDispatch, useSelector } from 'react-redux';
import { AppDispatch, RootState } from '../store';
import { logout } from '../store/authSlice';
import { Card, Badge, GoldButton, WarmAvatar, SectionLabel } from '../components/ui';
import theme from '../utils/theme';
const { colors, spacing, typography, radius } = theme;
import { useLanguage } from '../utils/LanguageContext';
import { t } from '../utils/i18n';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import type { ProfileNavProp } from '../navigation/types';

const ProfileScreen: React.FC<{ navigation: ProfileNavProp }> = ({ navigation }) => {
  const insets = useSafeAreaInsets();
  const dispatch = useDispatch<AppDispatch>();
  const { lang } = useLanguage();
  const user     = useSelector((s: RootState) => s.auth.user);

  const handleMenuPress = (screen: string) => {
    if (screen === 'Chat') {
      navigation.navigate('Chat');
    } else {
      Alert.alert(t('profile.coming_soon', lang), `${screen} ${t('profile.feature_coming', lang)}`);
    }
  };

  const handleLogout = () => Alert.alert(
    t('profile.logout', lang),
    t('profile.logout_confirm', lang),
    [
      { text: t('profile.cancel', lang), style:'cancel' },
      { text: t('profile.logout_action', lang), style:'destructive', onPress: async () => {
        try { await dispatch(logout()); } catch { /* ignore — navigate regardless */ }
        navigation.replace('Auth');
      }},
    ]
  );

  const MENU = [
    { icon:'📊', label: t('profile.my_analysis', lang),   screen:'History' },
    { icon:'💬', label: t('profile.my_chat', lang),       screen:'ChatHistory' },
    { icon:'🌍', label: t('profile.language', lang),      screen:'Language' },
    { icon:'🔔', label: t('profile.notifications', lang), screen:'Notifications' },
    { icon:'🔒', label: t('profile.privacy', lang),       screen:'Privacy' },
    { icon:'⭐', label: t('profile.rate_app', lang),      screen:'Rate' },
    { icon:'💬', label: t('profile.support', lang),       screen:'Support' },
  ];

  const userPlan = user?.plan;

  return (
    <View style={styles.container}>
      <View style={[styles.header, { paddingTop: insets.top + spacing.sm }]}>
        <TouchableOpacity onPress={() => navigation.goBack()}>
          <Text style={styles.back}>←</Text>
        </TouchableOpacity>
        <Text style={styles.headerTitle}>{t('profile.title', lang)}</Text>
        <View style={styles.spacer} />
      </View>

      <ScrollView contentContainerStyle={styles.scroll} showsVerticalScrollIndicator={false}>
        {/* Kullanıcı kartı */}
        <Card variant="warm" style={styles.userCard}>
          <View style={styles.userRow}>
            <WarmAvatar
              letter={user?.name?.[0]?.toUpperCase() || '?'}
              size={60}
            />
            <View style={styles.userInfo}>
              <Text style={styles.userName}>{user?.name || t('profile.default_user', lang)}</Text>
              <Text style={styles.userEmail}>{user?.email}</Text>
              <View style={styles.badgeWrap}>
                <Badge
                  label={userPlan === 'premium' ? t('profile.premium', lang) : t('profile.free', lang)}
                  color={userPlan === 'premium' ? colors.gold : colors.textMuted}
                />
              </View>
            </View>
          </View>
        </Card>

        {/* AI asistanla konuş */}
        <Card variant="gold" style={styles.aiPromptCard}>
          <View style={styles.aiPromptRow}>
            <Text style={styles.aiPromptIcon}>✨</Text>
            <View style={styles.aiPromptTextWrap}>
              <Text style={styles.aiPromptTitle}>{t('profile.talk_assistant', lang)}</Text>
              <Text style={styles.aiPromptDesc}>{t('profile.talk_desc', lang)}</Text>
            </View>
            <TouchableOpacity
              style={styles.aiPromptBtn}
              onPress={() => navigation.navigate('Chat', {})}
            >
              <Text style={styles.aiPromptBtnText}>{t('profile.start', lang)}</Text>
            </TouchableOpacity>
          </View>
        </Card>

        {/* Premium */}
        {userPlan !== 'premium' && (
          <TouchableOpacity style={styles.premiumBanner} activeOpacity={0.9}>
            <View>
              <Text style={styles.premiumTitle}>{t('profile.upgrade', lang)}</Text>
              <Text style={styles.premiumDesc}>{t('profile.upgrade_desc', lang)}</Text>
            </View>
            <Text style={styles.premiumPrice}>{t('profile.premium_price', lang)}</Text>
          </TouchableOpacity>
        )}

        <SectionLabel>{t('profile.settings', lang)}</SectionLabel>

        <Card style={styles.menuCard}>
          {MENU.map((item, i) => (
            <React.Fragment key={item.label}>
              <TouchableOpacity
                style={styles.menuItem}
                onPress={() => handleMenuPress(item.screen)}
                activeOpacity={0.7}
              >
                <Text style={styles.menuIcon}>{item.icon}</Text>
                <Text style={styles.menuLabel}>{item.label}</Text>
                <Text style={styles.menuArrow}>›</Text>
              </TouchableOpacity>
              {i < MENU.length - 1 && (
                <View style={styles.menuDivider} />
              )}
            </React.Fragment>
          ))}
        </Card>

        <Text style={styles.version}>{t('profile.version', lang)}</Text>

        <GoldButton
          title={t('profile.logout', lang)}
          onPress={handleLogout}
          variant="outline"
          style={styles.logoutBtn}
        />
      </ScrollView>
    </View>
  );
};

const styles = StyleSheet.create({
  container: { flex:1, backgroundColor: colors.background },
  header: {
    flexDirection:'row', alignItems:'center', justifyContent:'space-between',
    paddingHorizontal: spacing.lg,
    paddingBottom: spacing.md,
    borderBottomWidth:1, borderBottomColor: colors.border,
  },
  back:        { ...typography.body, color: colors.gold, fontSize:22 },
  headerTitle: { ...typography.h3, letterSpacing:0.5 },
  scroll: { padding: spacing.lg, paddingBottom: spacing.xxxl },

  userCard: { marginBottom: spacing.md },
  userRow:  { flexDirection:'row', alignItems:'center' },
  userName: { ...typography.h2 },
  userEmail:{ ...typography.caption, marginTop:2, color: colors.textWarm },

  aiPromptCard:     { marginBottom: spacing.md },
  aiPromptRow:      { flexDirection: 'row' as const, alignItems: 'center' as const, gap: 10 },
  aiPromptIcon:     { fontSize: 22 },
  aiPromptTextWrap: { flex: 1 },
  aiPromptTitle:    { ...typography.h3, fontSize:13, marginBottom:2 },
  aiPromptDesc:     { ...typography.caption, fontSize:11, color: colors.textWarm },
  aiPromptBtn:      {
    paddingHorizontal:12, paddingVertical:7,
    backgroundColor: colors.warmAmber,
    borderRadius: radius.full,
  },
  aiPromptBtnText:{ fontFamily:'System', fontSize:11, fontWeight:'700', color:'#000', letterSpacing:0.5 },

  premiumBanner: {
    backgroundColor: colors.goldGlow,
    borderRadius: radius.lg, borderWidth:1, borderColor: colors.goldDark,
    padding: spacing.md, flexDirection:'row', alignItems:'center',
    justifyContent:'space-between', marginBottom: spacing.sm,
  },
  premiumTitle: { ...typography.h3, color: colors.gold, fontSize:14, marginBottom:3 },
  premiumDesc:  { ...typography.caption, fontSize:11, color: colors.textWarm },
  premiumPrice: { ...typography.h3, color: colors.gold, fontSize:14 },

  menuItem:    { flexDirection:'row', alignItems:'center', padding: spacing.md },
  menuIcon:    { fontSize:18, marginRight: spacing.md, width:24, textAlign:'center' },
  menuLabel:   { ...typography.body, color: colors.textPrimary, flex:1, fontSize:14 },
  menuArrow:   { ...typography.h2, color: colors.textMuted, fontSize:18 },
  menuDivider: {
    height:1, backgroundColor: colors.border,
    marginLeft: spacing.md + 24 + spacing.md,
  },
  version: { ...typography.caption, textAlign:'center', marginTop: spacing.xl, marginBottom: spacing.sm },
  spacer:       { width: 40 },
  userInfo:     { marginLeft: spacing.md, flex: 1 },
  badgeWrap:    { marginTop: 6 },
  menuCard:     { padding: 0, overflow: 'hidden' as const },
  logoutBtn:    { marginTop: spacing.md },
});

export default ProfileScreen;

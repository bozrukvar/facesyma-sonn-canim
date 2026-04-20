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
import { useLanguage } from '../utils/LanguageContext';
import { t } from '../utils/i18n';

const ProfileScreen: React.FC<{ navigation: any }> = ({ navigation }) => {
  const dispatch = useDispatch<AppDispatch>();
  const { lang } = useLanguage();
  const user     = useSelector((s: RootState) => s.auth.user);

  const handleMenuPress = (screen: string) => {
    const implementedScreens = ['Chat'];
    if (implementedScreens.includes(screen)) {
      navigation.navigate(screen);
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
        await dispatch(logout()); navigation.replace('Auth');
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

  return (
    <View style={styles.container}>
      <View style={styles.header}>
        <TouchableOpacity onPress={() => navigation.goBack()}>
          <Text style={styles.back}>←</Text>
        </TouchableOpacity>
        <Text style={styles.headerTitle}>{t('profile.title', lang)}</Text>
        <View style={{ width:40 }} />
      </View>

      <ScrollView contentContainerStyle={styles.scroll} showsVerticalScrollIndicator={false}>
        {/* Kullanıcı kartı */}
        <Card variant="warm" style={styles.userCard}>
          <View style={styles.userRow}>
            <WarmAvatar
              letter={user?.name?.[0]?.toUpperCase() || '?'}
              size={60}
            />
            <View style={{ marginLeft: theme.spacing.md, flex:1 }}>
              <Text style={styles.userName}>{user?.name || t('profile.default_user', lang)}</Text>
              <Text style={styles.userEmail}>{user?.email}</Text>
              <View style={{ marginTop:6 }}>
                <Badge
                  label={user?.plan === 'premium' ? t('profile.premium', lang) : t('profile.free', lang)}
                  color={user?.plan === 'premium' ? theme.colors.gold : theme.colors.textMuted}
                />
              </View>
            </View>
          </View>
        </Card>

        {/* AI asistanla konuş */}
        <Card variant="gold" style={styles.aiPromptCard}>
          <View style={{ flexDirection:'row', alignItems:'center', gap:10 }}>
            <Text style={{ fontSize:22 }}>✨</Text>
            <View style={{ flex:1 }}>
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
        {user?.plan !== 'premium' && (
          <TouchableOpacity style={styles.premiumBanner} activeOpacity={0.9}>
            <View>
              <Text style={styles.premiumTitle}>{t('profile.upgrade', lang)}</Text>
              <Text style={styles.premiumDesc}>{t('profile.upgrade_desc', lang)}</Text>
            </View>
            <Text style={styles.premiumPrice}>{t('profile.premium_price', lang)}</Text>
          </TouchableOpacity>
        )}

        <SectionLabel>{t('profile.settings', lang)}</SectionLabel>

        <Card style={{ padding:0, overflow:'hidden' }}>
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
          style={{ marginTop: theme.spacing.md }}
        />
      </ScrollView>
    </View>
  );
};

const styles = StyleSheet.create({
  container: { flex:1, backgroundColor: theme.colors.background },
  header: {
    flexDirection:'row', alignItems:'center', justifyContent:'space-between',
    paddingHorizontal: theme.spacing.lg,
    paddingTop: theme.spacing.lg + 44,
    paddingBottom: theme.spacing.md,
    borderBottomWidth:1, borderBottomColor: theme.colors.border,
  },
  back:        { ...theme.typography.body, color: theme.colors.gold, fontSize:22 },
  headerTitle: { ...theme.typography.h3, letterSpacing:0.5 },
  scroll: { padding: theme.spacing.lg, paddingBottom: theme.spacing.xxxl },

  userCard: { marginBottom: theme.spacing.md },
  userRow:  { flexDirection:'row', alignItems:'center' },
  userName: { ...theme.typography.h2 },
  userEmail:{ ...theme.typography.caption, marginTop:2, color: theme.colors.textWarm },

  aiPromptCard: { marginBottom: theme.spacing.md },
  aiPromptTitle:{ ...theme.typography.h3, fontSize:13, marginBottom:2 },
  aiPromptDesc: { ...theme.typography.caption, fontSize:11, color: theme.colors.textWarm },
  aiPromptBtn:  {
    paddingHorizontal:12, paddingVertical:7,
    backgroundColor: theme.colors.warmAmber,
    borderRadius: theme.radius.full,
  },
  aiPromptBtnText:{ fontFamily:'System', fontSize:11, fontWeight:'700', color:'#000', letterSpacing:0.5 },

  premiumBanner: {
    backgroundColor: theme.colors.goldGlow,
    borderRadius: theme.radius.lg, borderWidth:1, borderColor: theme.colors.goldDark,
    padding: theme.spacing.md, flexDirection:'row', alignItems:'center',
    justifyContent:'space-between', marginBottom: theme.spacing.sm,
  },
  premiumTitle: { ...theme.typography.h3, color: theme.colors.gold, fontSize:14, marginBottom:3 },
  premiumDesc:  { ...theme.typography.caption, fontSize:11, color: theme.colors.textWarm },
  premiumPrice: { ...theme.typography.h3, color: theme.colors.gold, fontSize:14 },

  menuItem:    { flexDirection:'row', alignItems:'center', padding: theme.spacing.md },
  menuIcon:    { fontSize:18, marginRight: theme.spacing.md, width:24, textAlign:'center' },
  menuLabel:   { ...theme.typography.body, color: theme.colors.textPrimary, flex:1, fontSize:14 },
  menuArrow:   { ...theme.typography.h2, color: theme.colors.textMuted, fontSize:18 },
  menuDivider: {
    height:1, backgroundColor: theme.colors.border,
    marginLeft: theme.spacing.md + 24 + theme.spacing.md,
  },
  version: { ...theme.typography.caption, textAlign:'center', marginTop: theme.spacing.xl, marginBottom: theme.spacing.sm },
});

export default ProfileScreen;

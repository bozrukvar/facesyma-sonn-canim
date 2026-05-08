// src/screens/HomeScreen.tsx
import React, { useMemo } from 'react';
import {
  View, Text, StyleSheet, ScrollView, TouchableOpacity,
  Dimensions, StatusBar,
} from 'react-native';
import { useSelector } from 'react-redux';
import { RootState } from '../store';
import { Card, WarmAvatar } from '../components/ui';
import theme from '../utils/theme';
const { colors, spacing, typography, radius, shadow } = theme;
import { useLanguage } from '../utils/LanguageContext';
import { t } from '../utils/i18n';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import type { HomeNavProp } from '../navigation/types';

const { width } = Dimensions.get('window');
const CARD_W = (width - spacing.lg * 2 - spacing.sm) / 2;

const getFeatures = (lang: string) => {
  const reqBadge = t('common.required', lang).substring(0, 3);
  return [
    { id:'analysis', emoji:'👁', title: t('features.analysis', lang), desc: t('features.analysis_desc', lang), screen:'Analysis', accent: colors.gold },
    { id:'astrology',emoji:'✨', title: t('features.astrology', lang), desc: t('features.astrology_desc', lang), screen:'Astrology', accent:'#9B7AE0' },
    { id:'art',      emoji:'🎨', title: t('features.art', lang), desc: t('features.art_desc', lang), screen:'ArtMatch', accent:'#7AE0B0' },
    { id:'twins',    emoji:'👥', title: t('features.twins', lang), desc: t('features.twins_desc', lang), screen:'Twins', accent:'#E07A7A' },
    { id:'daily',    emoji:'🌟', title: t('features.daily', lang), desc: t('features.daily_desc', lang), screen:'Daily', accent:'#7AAEE0' },
    { id:'assessment',emoji:'📋', title: t('features.assessment', lang), desc: t('features.assessment_desc', lang), screen:'Assessment', accent:'#E0A17A', badge: reqBadge },
    { id:'fashion',  emoji:'👗', title: t('features.fashion', lang), desc: t('features.fashion_desc', lang), screen:'Fashion', accent:'#9B5DE5', badge: reqBadge },
    { id:'chat',     emoji:'💬', title: t('features.chat', lang), desc: t('features.chat_desc', lang), screen:'Chat', accent: colors.warmAmber, badge: reqBadge },
    { id:'diet',     emoji:'🥗', title: t('features.diet', lang), desc: t('features.diet_desc', lang), screen:'Diet', accent:'#7AE07A' },
    { id:'coach',    emoji:'🧠', title: t('coach.hub_title', lang), desc: t('coach.hub_desc', lang), screen:'CoachHub', accent:'#C07AE0' },
    { id:'partner',  emoji:'💑', title: t('features.partner', lang), desc: t('features.partner_desc', lang), screen:'Partner', accent:'#E0607A' },
  ];
};

const getGreetings = (lang: string) => [
  t('home.greeting_morning', lang),
  t('home.greeting_noon', lang),
  t('home.greeting_evening', lang),
];

const HomeScreen: React.FC<{ navigation: HomeNavProp }> = ({ navigation }) => {
  const insets = useSafeAreaInsets();
  const { lang } = useLanguage();
  const user           = useSelector((s: RootState) => s.auth.user);
  const lastAnalysis   = useSelector((s: RootState) => s.analysis.lastResult);
  const FEATURES = useMemo(() => getFeatures(lang), [lang]);
  const GREETINGS = useMemo(() => getGreetings(lang), [lang]);
  const _h = new Date().getHours();
  const greeting = _h >= 5 && _h < 12 ? GREETINGS[0] : _h >= 12 && _h < 18 ? GREETINGS[1] : GREETINGS[2];
  const firstName = user?.name?.split(' ')[0] || t('home.default_user', lang);

  return (
    <View style={styles.container}>
      <StatusBar barStyle="light-content" />
      <ScrollView
        showsVerticalScrollIndicator={false}
        contentContainerStyle={[styles.scroll, { paddingTop: insets.top + spacing.md }]}
      >
        {/* Header — sıcak karşılama */}
        <View style={styles.header}>
          <View style={styles.flex1}>
            <Text style={styles.greeting}>{greeting},</Text>
            <Text style={styles.name}>{firstName} 👋</Text>
          </View>
          <TouchableOpacity
            accessibilityRole="button"
            accessibilityLabel={t('nav.profile', lang)}
            accessibilityHint="Profil ekranını aç"
            onPress={() => navigation.navigate('Profile')}
            activeOpacity={0.85}
          >
            <WarmAvatar
              letter={user?.name?.[0]?.toUpperCase() || '?'}
              size={46}
            />
          </TouchableOpacity>
        </View>

        {/* Hero — AI Asistan çağrısı */}
        <Card variant="warm" onPress={() => navigation.navigate('Chat', lastAnalysis ? { analysisResult: lastAnalysis, lang } : { lang })} style={styles.heroCard}>
          <View style={styles.heroRow}>
            <View style={styles.heroBadge}>
              <Text style={styles.heroIcon}>💬</Text>
            </View>
            <View style={styles.heroBody}>
              <Text style={styles.heroTitle}>{t('home.hero_title', lang)}</Text>
              <Text style={styles.heroDesc}>
                {t('home.hero_desc', lang)}
              </Text>
            </View>
            <Text style={styles.heroArrow}>→</Text>
          </View>
        </Card>

        {/* Analiz başlat */}
        <TouchableOpacity
          accessibilityRole="button"
          accessibilityLabel={t('home.analyze_title', lang)}
          style={styles.analyzeBtn}
          onPress={() => navigation.navigate('Analysis')}
          activeOpacity={0.88}
        >
          <View style={styles.analyzeGlow} />
          <Text style={styles.analyzeIcon}>👁</Text>
          <View style={styles.analyzeBody}>
            <Text style={styles.analyzeTitle}>{t('home.analyze_title', lang)}</Text>
            <Text style={styles.analyzeDesc}>{t('home.analyze_desc', lang)}</Text>
          </View>
          <View style={styles.analyzeTag}><Text style={styles.analyzeTagText}>{t('home.analyze_cta', lang)}</Text></View>
        </TouchableOpacity>

        {/* Modüller */}
        <Text style={styles.sectionLabel}>{t('home.modules', lang)}</Text>
        <View style={styles.grid}>
          {FEATURES.map(({ id: fId, accent: fAccent, badge: fBadge, screen: fScreen, emoji: fEmoji, title: fTitle, desc: fDesc }) => (
            <TouchableOpacity
              accessibilityRole="button"
              accessibilityLabel={fTitle}
              key={fId}
              style={[styles.featureCard, { borderColor: `${fAccent}28` }]}
              onPress={() => (navigation.navigate as unknown as (screen: string, params?: object) => void)(fScreen, lastAnalysis ? { analysisResult: lastAnalysis, lang } : { lang })}
              activeOpacity={0.85}
            >
              {fBadge && (
                <View style={styles.featureBadge}>
                  <Text style={[styles.featureBadgeText, { color: fAccent }]}>{fBadge}</Text>
                </View>
              )}
              <View style={[styles.featureIconWrap, { backgroundColor: `${fAccent}12` }]}>
                <Text style={styles.featureIcon}>{fEmoji}</Text>
              </View>
              <Text style={styles.featureTitle}>{fTitle}</Text>
              <Text style={styles.featureDesc}>{fDesc}</Text>
            </TouchableOpacity>
          ))}
        </View>

        {/* Sosyal */}
        <Text style={styles.sectionLabel}>{t('home.social', lang)}</Text>
        <View style={styles.socialRow}>
          <TouchableOpacity
            accessibilityRole="button"
            accessibilityLabel={t('community.title', lang)}
            style={styles.socialCard}
            onPress={() => navigation.navigate('Communities' as any)}
            activeOpacity={0.85}
          >
            <Text style={styles.socialIcon}>🏘️</Text>
            <Text style={styles.socialTitle}>{t('community.title', lang)}</Text>
            <Text style={styles.socialDesc}>{t('home.communities_desc', lang)}</Text>
          </TouchableOpacity>
          <TouchableOpacity
            accessibilityRole="button"
            accessibilityLabel={t('home.chats', lang)}
            style={styles.socialCard}
            onPress={() => navigation.navigate('PeerChatList' as any)}
            activeOpacity={0.85}
          >
            <Text style={styles.socialIcon}>💬</Text>
            <Text style={styles.socialTitle}>{t('home.chats', lang)}</Text>
            <Text style={styles.socialDesc}>{t('home.chats_desc', lang)}</Text>
          </TouchableOpacity>
        </View>

        {/* Gamification */}
        <Text style={styles.sectionLabel}>{t('gamification.title', lang)}</Text>
        <TouchableOpacity
          accessibilityRole="button"
          accessibilityLabel={t('gamification.hub_title', lang)}
          style={styles.gamificationBanner}
          onPress={() => (navigation.navigate as any)('Gamification')}
          activeOpacity={0.85}
        >
          <View style={styles.gamRow}>
            <Text style={styles.gamEmoji}>🏆</Text>
            <View style={styles.gamBody}>
              <Text style={styles.gamTitle}>{t('gamification.hub_title', lang)}</Text>
              <Text style={styles.gamDesc}>{t('gamification.hub_desc', lang)}</Text>
            </View>
            <Text style={styles.gamArrow}>→</Text>
          </View>
          <View style={styles.gamChips}>
            {(['🪙', '🎖️', '⚔️', '🍽️', '🔍'].map((em, i) => (
              <View key={i} style={styles.gamChip}><Text style={styles.gamChipText}>{em}</Text></View>
            )))}
          </View>
        </TouchableOpacity>

        {/* Son analizler */}
        <Text style={styles.sectionLabel}>{t('home.recent_results', lang)}</Text>
        <TouchableOpacity
          accessibilityRole="button"
          accessibilityLabel={t('home.history_empty_cta', lang)}
          style={styles.historyEmpty}
          onPress={() => navigation.navigate('Analysis')}
        >
          <Text style={styles.historyIcon}>📷</Text>
          <Text style={styles.historyEmptyText}>
            {t('home.history_empty_cta', lang)}
          </Text>
        </TouchableOpacity>
      </ScrollView>
    </View>
  );
};

const styles = StyleSheet.create({
  container: { flex:1, backgroundColor: colors.background },
  scroll: {
    paddingHorizontal: spacing.lg,
    paddingTop:        spacing.lg,
    paddingBottom:     spacing.xxxl,
  },
  header:  { flexDirection:'row', alignItems:'center', marginBottom: spacing.lg },
  greeting:{ ...typography.body, color: colors.textMuted },
  name:    { ...typography.h1, marginTop:2 },

  // Hero
  heroCard: { marginBottom: spacing.md },
  heroRow:  { flexDirection:'row', alignItems:'center' },
  heroBadge:{
    width:52, height:52, borderRadius: radius.lg,
    backgroundColor: colors.warmAmberGlow,
    borderWidth:1, borderColor:`${colors.warmAmber}30`,
    alignItems:'center', justifyContent:'center',
  },
  heroTitle:{ ...typography.h3, marginBottom:3 },
  heroDesc: { ...typography.caption, fontSize:12, color: colors.textWarm },
  heroArrow:{ ...typography.h2, color: colors.warmAmber, fontSize:20 },

  // Analiz butonu
  analyzeBtn:{
    backgroundColor: colors.surface,
    borderRadius:    radius.xl,
    borderWidth:     1,
    borderColor:     colors.goldDark,
    padding:         spacing.lg,
    marginBottom:    spacing.xl,
    flexDirection:   'row',
    alignItems:      'center',
    overflow:        'hidden',
    ...shadow.gold,
  },
  analyzeGlow:{
    ...StyleSheet.absoluteFillObject,
    backgroundColor: colors.goldGlow,
  },
  analyzeTitle: { ...typography.h2, marginBottom:3 },
  analyzeDesc:  { ...typography.caption, fontSize:12, color: colors.textWarm },
  analyzeTag: {
    backgroundColor: colors.gold,
    borderRadius: radius.full,
    paddingHorizontal:10, paddingVertical:5,
  },
  analyzeTagText: { ...typography.goldLabel, color:'#000', fontSize:9 },

  // Section
  sectionLabel: { ...typography.goldLabel, marginBottom: spacing.md },

  // Grid
  grid: { flexDirection:'row', flexWrap:'wrap', gap: spacing.sm, marginBottom: spacing.xl },
  featureCard: {
    width:           CARD_W,
    backgroundColor: colors.surface,
    borderRadius:    radius.lg,
    borderWidth:     1,
    padding:         spacing.md,
    minHeight:       120,
    position:        'relative',
  },
  featureBadge: {
    position:'absolute', top:8, right:8,
    backgroundColor: colors.surface,
    paddingHorizontal:6, paddingVertical:2,
    borderRadius: radius.full,
  },
  featureBadgeText: { fontFamily:'System', fontSize:8, fontWeight:'700', letterSpacing:1 },
  featureIconWrap: {
    width:44, height:44, borderRadius: radius.md,
    alignItems:'center', justifyContent:'center',
    marginBottom: spacing.sm,
  },
  featureTitle: { ...typography.h3, fontSize:13, marginBottom:3 },
  featureDesc:  { ...typography.caption, fontSize:11, color: colors.textWarm },

  // History
  historyEmpty: {
    backgroundColor: colors.surface,
    borderRadius:    radius.lg,
    borderWidth:     1,
    borderColor:     colors.border,
    borderStyle:     'dashed',
    padding:         spacing.xl,
    alignItems:      'center',
  },
  historyEmptyText: { ...typography.body, color: colors.textMuted, fontSize:13 },
  flex1:       { flex: 1 },
  heroIcon:    { fontSize: 24 },
  heroBody:    { flex: 1, marginLeft: spacing.md },
  analyzeIcon: { fontSize: 28 },
  analyzeBody: { marginLeft: spacing.md, flex: 1 },
  featureIcon: { fontSize: 22 },
  historyIcon: { fontSize: 24, marginBottom: 6 },
  socialRow:  { flexDirection: 'row', gap: spacing.sm, marginBottom: spacing.xl },
  socialCard: {
    flex: 1,
    backgroundColor: colors.surface,
    borderRadius: radius.lg,
    borderWidth: 1,
    borderColor: colors.border,
    padding: spacing.md,
    alignItems: 'center',
    gap: 4,
  },
  socialIcon:  { fontSize: 28 },
  socialTitle: { ...typography.h3, fontSize: 13, textAlign: 'center' as const },
  socialDesc:  { ...typography.caption, fontSize: 11, color: colors.textMuted, textAlign: 'center' as const },

  // Gamification banner
  gamificationBanner: {
    backgroundColor: colors.surface, borderRadius: radius.lg,
    borderWidth: 1, borderColor: `${colors.gold}30`,
    padding: spacing.md, marginBottom: spacing.xl,
  },
  gamRow: { flexDirection: 'row', alignItems: 'center', marginBottom: spacing.sm },
  gamEmoji: { fontSize: 28, marginRight: spacing.sm },
  gamBody: { flex: 1 },
  gamTitle: { ...typography.h3, fontSize: 14, marginBottom: 2 },
  gamDesc: { ...typography.caption, color: colors.textMuted, fontSize: 11 },
  gamArrow: { fontSize: 18, color: colors.gold },
  gamChips: { flexDirection: 'row', gap: 8 },
  gamChip: {
    backgroundColor: `${colors.gold}15`, borderRadius: 8,
    width: 32, height: 32, alignItems: 'center', justifyContent: 'center',
  },
  gamChipText: { fontSize: 16 },
});

export default HomeScreen;

// src/screens/HomeScreen.tsx
import React, { useMemo } from 'react';
import {
  View, Text, StyleSheet, ScrollView, TouchableOpacity,
  Dimensions, StatusBar,
} from 'react-native';
import { useSelector } from 'react-redux';
import { RootState } from '../store';
import { Card, Badge, WarmAvatar } from '../components/ui';
import theme from '../utils/theme';
import { useLanguage } from '../utils/LanguageContext';
import { t } from '../utils/i18n';

const { width } = Dimensions.get('window');
const CARD_W = (width - theme.spacing.lg * 2 - theme.spacing.sm) / 2;

const getFeatures = (lang: string) => [
  { id:'analysis', emoji:'👁', title: t('features.analysis', lang), desc: t('features.analysis_desc', lang), screen:'Analysis', accent: theme.colors.gold },
  { id:'astrology',emoji:'✨', title: t('features.astrology', lang), desc: t('features.astrology_desc', lang), screen:'Astrology', accent:'#9B7AE0' },
  { id:'art',      emoji:'🎨', title: t('features.art', lang), desc: t('features.art_desc', lang), screen:'ArtMatch', accent:'#7AE0B0' },
  { id:'twins',    emoji:'👥', title: t('features.twins', lang), desc: t('features.twins_desc', lang), screen:'Twins', accent:'#E07A7A' },
  { id:'daily',    emoji:'🌟', title: t('features.daily', lang), desc: t('features.daily_desc', lang), screen:'Daily', accent:'#7AAEE0' },
  { id:'assessment',emoji:'📋', title: t('features.assessment', lang), desc: t('features.assessment_desc', lang), screen:'Assessment', accent:'#E0A17A', badge: t('common.required', lang).substring(0, 3) },
  { id:'fashion',  emoji:'👗', title: t('features.fashion', lang), desc: t('features.fashion_desc', lang), screen:'Fashion', accent:'#9B5DE5', badge: t('common.required', lang).substring(0, 3) },
  { id:'chat',     emoji:'💬', title: t('features.chat', lang), desc: t('features.chat_desc', lang), screen:'Chat', accent: theme.colors.warmAmber, badge: t('common.required', lang).substring(0, 3) },
];

const getGreetings = (lang: string) => [
  t('home.greeting_morning', lang),
  t('home.greeting_noon', lang),
  t('home.greeting_evening', lang),
];

const HomeScreen: React.FC<{ navigation: any }> = ({ navigation }) => {
  const { lang } = useLanguage();
  const user    = useSelector((s: RootState) => s.auth.user);
  const FEATURES = useMemo(() => getFeatures(lang), [lang]);
  const GREETINGS = useMemo(() => getGreetings(lang), [lang]);
  const greeting= GREETINGS[new Date().getHours() % 3];
  const firstName = user?.name?.split(' ')[0] || t('home.default_user', lang);

  return (
    <View style={styles.container}>
      <StatusBar barStyle="light-content" />
      <ScrollView
        showsVerticalScrollIndicator={false}
        contentContainerStyle={styles.scroll}
      >
        {/* Header — sıcak karşılama */}
        <View style={styles.header}>
          <View style={{ flex:1 }}>
            <Text style={styles.greeting}>{greeting},</Text>
            <Text style={styles.name}>{firstName} 👋</Text>
          </View>
          <TouchableOpacity
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
        <Card variant="warm" onPress={() => navigation.navigate('Chat')} style={styles.heroCard}>
          <View style={styles.heroRow}>
            <View style={styles.heroBadge}>
              <Text style={{ fontSize: 24 }}>💬</Text>
            </View>
            <View style={{ flex:1, marginLeft: theme.spacing.md }}>
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
          style={styles.analyzeBtn}
          onPress={() => navigation.navigate('Analysis')}
          activeOpacity={0.88}
        >
          <View style={styles.analyzeGlow} />
          <Text style={{ fontSize: 28 }}>👁</Text>
          <View style={{ marginLeft: theme.spacing.md, flex:1 }}>
            <Text style={styles.analyzeTitle}>{t('home.analyze_title', lang)}</Text>
            <Text style={styles.analyzeDesc}>{t('home.analyze_desc', lang)}</Text>
          </View>
          <View style={styles.analyzeTag}><Text style={styles.analyzeTagText}>{t('home.analyze_cta', lang)}</Text></View>
        </TouchableOpacity>

        {/* Modüller */}
        <Text style={styles.sectionLabel}>{t('home.modules', lang)}</Text>
        <View style={styles.grid}>
          {FEATURES.map(f => (
            <TouchableOpacity
              key={f.id}
              style={[styles.featureCard, { borderColor: `${f.accent}28` }]}
              onPress={() => navigation.navigate(f.screen)}
              activeOpacity={0.85}
            >
              {f.badge && (
                <View style={styles.featureBadge}>
                  <Text style={[styles.featureBadgeText, { color: f.accent }]}>{f.badge}</Text>
                </View>
              )}
              <View style={[styles.featureIconWrap, { backgroundColor: `${f.accent}12` }]}>
                <Text style={{ fontSize: 22 }}>{f.emoji}</Text>
              </View>
              <Text style={styles.featureTitle}>{f.title}</Text>
              <Text style={styles.featureDesc}>{f.desc}</Text>
            </TouchableOpacity>
          ))}
        </View>

        {/* Son analizler */}
        <Text style={styles.sectionLabel}>{t('home.recent_results', lang)}</Text>
        <TouchableOpacity
          style={styles.historyEmpty}
          onPress={() => navigation.navigate('Analysis')}
        >
          <Text style={{ fontSize: 24, marginBottom: 6 }}>📷</Text>
          <Text style={styles.historyEmptyText}>
            {t('home.history_empty_cta', lang)}
          </Text>
        </TouchableOpacity>
      </ScrollView>
    </View>
  );
};

const styles = StyleSheet.create({
  container: { flex:1, backgroundColor: theme.colors.background },
  scroll: {
    paddingHorizontal: theme.spacing.lg,
    paddingTop:        theme.spacing.lg + 48,
    paddingBottom:     theme.spacing.xxxl,
  },
  header:  { flexDirection:'row', alignItems:'center', marginBottom: theme.spacing.lg },
  greeting:{ ...theme.typography.body, color: theme.colors.textMuted },
  name:    { ...theme.typography.h1, marginTop:2 },

  // Hero
  heroCard: { marginBottom: theme.spacing.md },
  heroRow:  { flexDirection:'row', alignItems:'center' },
  heroBadge:{
    width:52, height:52, borderRadius: theme.radius.lg,
    backgroundColor: theme.colors.warmAmberGlow,
    borderWidth:1, borderColor:`${theme.colors.warmAmber}30`,
    alignItems:'center', justifyContent:'center',
  },
  heroTitle:{ ...theme.typography.h3, marginBottom:3 },
  heroDesc: { ...theme.typography.caption, fontSize:12, color: theme.colors.textWarm },
  heroArrow:{ ...theme.typography.h2, color: theme.colors.warmAmber, fontSize:20 },

  // Analiz butonu
  analyzeBtn:{
    backgroundColor: theme.colors.surface,
    borderRadius:    theme.radius.xl,
    borderWidth:     1,
    borderColor:     theme.colors.goldDark,
    padding:         theme.spacing.lg,
    marginBottom:    theme.spacing.xl,
    flexDirection:   'row',
    alignItems:      'center',
    overflow:        'hidden',
    ...theme.shadow.gold,
  },
  analyzeGlow:{
    ...StyleSheet.absoluteFillObject,
    backgroundColor: theme.colors.goldGlow,
  },
  analyzeTitle: { ...theme.typography.h2, marginBottom:3 },
  analyzeDesc:  { ...theme.typography.caption, fontSize:12, color: theme.colors.textWarm },
  analyzeTag: {
    backgroundColor: theme.colors.gold,
    borderRadius: theme.radius.full,
    paddingHorizontal:10, paddingVertical:5,
  },
  analyzeTagText: { ...theme.typography.goldLabel, color:'#000', fontSize:9 },

  // Section
  sectionLabel: { ...theme.typography.goldLabel, marginBottom: theme.spacing.md },

  // Grid
  grid: { flexDirection:'row', flexWrap:'wrap', gap: theme.spacing.sm, marginBottom: theme.spacing.xl },
  featureCard: {
    width:           CARD_W,
    backgroundColor: theme.colors.surface,
    borderRadius:    theme.radius.lg,
    borderWidth:     1,
    padding:         theme.spacing.md,
    minHeight:       120,
    position:        'relative',
  },
  featureBadge: {
    position:'absolute', top:8, right:8,
    backgroundColor: theme.colors.surface,
    paddingHorizontal:6, paddingVertical:2,
    borderRadius: theme.radius.full,
  },
  featureBadgeText: { fontFamily:'System', fontSize:8, fontWeight:'700', letterSpacing:1 },
  featureIconWrap: {
    width:44, height:44, borderRadius: theme.radius.md,
    alignItems:'center', justifyContent:'center',
    marginBottom: theme.spacing.sm,
  },
  featureTitle: { ...theme.typography.h3, fontSize:13, marginBottom:3 },
  featureDesc:  { ...theme.typography.caption, fontSize:11, color: theme.colors.textWarm },

  // History
  historyEmpty: {
    backgroundColor: theme.colors.surface,
    borderRadius:    theme.radius.lg,
    borderWidth:     1,
    borderColor:     theme.colors.border,
    borderStyle:     'dashed',
    padding:         theme.spacing.xl,
    alignItems:      'center',
  },
  historyEmptyText: { ...theme.typography.body, color: theme.colors.textMuted, fontSize:13 },
});

export default HomeScreen;

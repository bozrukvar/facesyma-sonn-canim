// src/navigation/AppNavigator.tsx
import React, { useEffect, useMemo, useRef } from 'react';
import { NavigationContainer } from '@react-navigation/native';
import { createNativeStackNavigator } from '@react-navigation/native-stack';
import { createBottomTabNavigator } from '@react-navigation/bottom-tabs';
import { View, Text, ActivityIndicator, StyleSheet, Image } from 'react-native';
import { useDispatch, useSelector } from 'react-redux';
import { AppDispatch, RootState } from '../store';
import { restoreSession, logout } from '../store/authSlice';
import { registerLogoutHandler } from '../services/api';
import theme from '../utils/theme';
const { colors, spacing, typography, shadow } = theme;
import { useLanguage } from '../utils/LanguageContext';
import { t } from '../utils/i18n';

import OnboardingScreen    from '../screens/OnboardingScreen';
import ProfileSetupScreen  from '../screens/ProfileSetupScreen';
import AuthScreen          from '../screens/AuthScreen';
import HomeScreen       from '../screens/HomeScreen';
import AnalysisScreen   from '../screens/AnalysisScreen';
import ProfileScreen    from '../screens/ProfileScreen';
import ChatScreen       from '../screens/ChatScreen';
import TwinsScreen      from '../screens/TwinsScreen';
import AstrologyScreen  from '../screens/AstrologyScreen';
import ArtMatchScreen   from '../screens/ArtMatchScreen';
import DailyScreen           from '../screens/DailyScreen';
import AssessmentScreen      from '../screens/AssessmentScreen';
import AssessmentHistoryScreen from '../screens/AssessmentHistoryScreen';
import FashionScreen    from '../screens/FashionScreen';
import AccountScreen       from '../screens/AccountScreen';
import CommunitiesScreen    from '../screens/CommunitiesScreen';
import PeerChatListScreen   from '../screens/PeerChatListScreen';
import PeerChatRequestScreen from '../screens/PeerChatRequestScreen';
import PeerChatScreen       from '../screens/PeerChatScreen';

import type { RootStackParamList, TabParamList } from './types';

const Stack = createNativeStackNavigator<RootStackParamList>();
const Tab   = createBottomTabNavigator<TabParamList>();
const StackScreen = Stack.Screen;
const TabScreen   = Tab.Screen;

const getTabs = (lang: string) => [
  { name:'Home',     icon:'🏠', label: t('nav.home', lang), component: HomeScreen },
  { name:'Analysis', icon:'👁',  label: t('nav.analysis', lang),   component: AnalysisScreen },
  { name:'Profile',  icon:'👤',  label: t('nav.profile', lang),   component: ProfileScreen },
];

const MainTabs = () => {
  const { lang } = useLanguage();
  const TABS = useMemo(() => getTabs(lang), [lang]);

  return (
    <Tab.Navigator
      screenOptions={({ route }) => ({
        headerShown:   false,
        tabBarStyle: {
          backgroundColor:   colors.surface,
          borderTopColor:    colors.borderWarm,
          borderTopWidth:    1,
          height:            82,
          paddingBottom:     16,
          paddingTop:        8,
        },
        tabBarActiveTintColor:   colors.gold,
        tabBarInactiveTintColor: colors.textMuted,
        tabBarLabel: ({ focused, color }) => {
          const tab = TABS.find(t => t.name === route.name);
          return (
            <Text style={{
              fontSize: 10, color,
              fontWeight: focused ? '700' : '400',
              letterSpacing: 0.3, marginTop: 2,
              fontFamily: 'System',
            }}>{tab?.label}</Text>
          );
        },
        tabBarIcon: ({ focused }) => {
          const tab = TABS.find(t => t.name === route.name);
          return (
            <View style={{
              alignItems:'center', justifyContent:'center',
              width:40, height:40, borderRadius:20,
              backgroundColor: focused ? colors.warmAmberGlow : 'transparent',
            }}>
              <Text style={{ fontSize: focused ? 21 : 18 }}>{tab?.icon}</Text>
            </View>
          );
        },
      })}
    >
      <TabScreen name="Home"     component={HomeScreen} />
      <TabScreen name="Analysis" component={AnalysisScreen} />
      <TabScreen name="Profile"  component={ProfileScreen} />
    </Tab.Navigator>
  );
};

const SplashScreen = () => (
  <View style={splashStyles.container}>
    <Image
      source={require('../assets/logo.png')}
      style={splashStyles.logo}
      resizeMode="contain"
    />
    <View style={splashStyles.titleRow}>
      <Text style={splashStyles.title}>FaceSyma</Text>
      <View style={splashStyles.aiBadge}>
        <Text style={splashStyles.aiBadgeText}>AI</Text>
      </View>
    </View>
    <ActivityIndicator color={colors.warmAmber} />
  </View>
);

const splashStyles = StyleSheet.create({
  container: {
    flex:1, backgroundColor: colors.background,
    alignItems:'center' as const, justifyContent:'center' as const, gap: spacing.lg,
  },
  logo: { width: 90, height: 90 },
  titleRow: { flexDirection: 'row' as const, alignItems: 'center' as const, gap: 7 },
  title: { fontFamily: 'Georgia', fontSize: 24, fontWeight: '700' as const, letterSpacing: 1, color: colors.gold },
  aiBadge: {
    backgroundColor: colors.gold,
    borderRadius: 5,
    paddingHorizontal: 7,
    paddingVertical: 3,
    alignSelf: 'center' as const,
  },
  aiBadgeText: { fontFamily: 'System', fontSize: 12, fontWeight: '800' as const, color: '#060F14', letterSpacing: 1 },
});

const AppNavigator = () => {
  const dispatch = useDispatch<AppDispatch>();
  const { isAuthenticated, isLoading, user } = useSelector((s: RootState) => s.auth);
  const [ready, setReady] = React.useState(false);
  const navRef = useRef<any>(null);

  useEffect(() => {
    dispatch(restoreSession()).finally(() => setReady(true));
    registerLogoutHandler(() => dispatch(logout()));
  }, []);

  useEffect(() => {
    if (ready && isAuthenticated && user && !user.onboarding_completed) {
      navRef.current?.navigate('ProfileSetup');
    }
  }, [ready]);

  if (!ready || isLoading) return <SplashScreen />;

  return (
    <NavigationContainer ref={navRef} theme={{
      dark: true,
      colors: {
        primary:      colors.gold,
        background:   colors.background,
        card:         colors.surface,
        text:         colors.textPrimary,
        border:       colors.border,
        notification: colors.warmAmber,
      },
    }}>
      <Stack.Navigator screenOptions={{ headerShown: false }}>
        {!isAuthenticated ? (
          <>
            <StackScreen name="Onboarding" component={OnboardingScreen} />
            <StackScreen name="Auth"       component={AuthScreen} />
            <StackScreen name="ProfileSetup" component={ProfileSetupScreen} />
          </>
        ) : (
          <>
            <StackScreen name="Main"              component={MainTabs} />
            <StackScreen name="ProfileSetup"      component={ProfileSetupScreen} />
            <StackScreen name="Chat"              component={ChatScreen} />
            <StackScreen name="Twins"             component={TwinsScreen} />
            <StackScreen name="Astrology"         component={AstrologyScreen} />
            <StackScreen name="ArtMatch"          component={ArtMatchScreen} />
            <StackScreen name="Daily"             component={DailyScreen} />
            <StackScreen name="Assessment"        component={AssessmentScreen} />
            <StackScreen name="AssessmentHistory" component={AssessmentHistoryScreen} />
            <StackScreen name="Account"           component={AccountScreen} />
            <StackScreen name="Fashion"           component={FashionScreen} />
            <StackScreen name="Communities"        component={CommunitiesScreen} />
            <StackScreen name="PeerChatList"       component={PeerChatListScreen} />
            <StackScreen name="PeerChatRequest"    component={PeerChatRequestScreen} />
            <StackScreen name="PeerChat"           component={PeerChatScreen} />
          </>
        )}
      </Stack.Navigator>
    </NavigationContainer>
  );
};

export default AppNavigator;

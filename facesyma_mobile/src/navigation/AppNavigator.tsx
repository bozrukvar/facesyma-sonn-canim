// src/navigation/AppNavigator.tsx
import React, { useEffect, useMemo } from 'react';
import { NavigationContainer } from '@react-navigation/native';
import { createNativeStackNavigator } from '@react-navigation/native-stack';
import { createBottomTabNavigator } from '@react-navigation/bottom-tabs';
import { View, Text, ActivityIndicator, StyleSheet } from 'react-native';
import { useDispatch, useSelector } from 'react-redux';
import { AppDispatch, RootState } from '../store';
import { restoreSession, logout } from '../store/authSlice';
import { registerLogoutHandler } from '../services/api';
import theme from '../utils/theme';
const { colors, spacing, typography, shadow } = theme;
import { useLanguage } from '../utils/LanguageContext';
import { t } from '../utils/i18n';

import OnboardingScreen from '../screens/OnboardingScreen';
import AuthScreen       from '../screens/AuthScreen';
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
    <View style={splashStyles.orb}>
      <Text style={splashStyles.orbIcon}>👁</Text>
    </View>
    <Text style={splashStyles.title}>FACESYMA</Text>
    <ActivityIndicator color={colors.warmAmber} />
  </View>
);

const splashStyles = StyleSheet.create({
  container: {
    flex:1, backgroundColor: colors.background,
    alignItems:'center' as const, justifyContent:'center' as const, gap: spacing.lg,
  },
  orb: {
    width:80, height:80, borderRadius:40,
    borderWidth:1.5, borderColor: colors.gold,
    backgroundColor: colors.goldGlow,
    alignItems:'center' as const, justifyContent:'center' as const,
    ...shadow.gold,
  },
  orbIcon: { fontSize: 36 },
  title: { ...typography.goldLabel, fontSize:16, letterSpacing:5, color: colors.gold },
});

const AppNavigator = () => {
  const dispatch = useDispatch<AppDispatch>();
  const { isAuthenticated, isLoading } = useSelector((s: RootState) => s.auth);
  const [ready, setReady] = React.useState(false);

  useEffect(() => {
    dispatch(restoreSession()).finally(() => setReady(true));
    // Token yenileme tamamen başarısız olursa Redux state'i temizle
    registerLogoutHandler(() => dispatch(logout()));
  }, []);

  if (!ready || isLoading) return <SplashScreen />;

  return (
    <NavigationContainer theme={{
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
          </>
        ) : (
          <>
            <StackScreen name="Main"              component={MainTabs} />
            <StackScreen name="Chat"              component={ChatScreen} />
            <StackScreen name="Twins"             component={TwinsScreen} />
            <StackScreen name="Astrology"         component={AstrologyScreen} />
            <StackScreen name="ArtMatch"          component={ArtMatchScreen} />
            <StackScreen name="Daily"             component={DailyScreen} />
            <StackScreen name="Assessment"        component={AssessmentScreen} />
            <StackScreen name="AssessmentHistory" component={AssessmentHistoryScreen} />
            <StackScreen name="Fashion"           component={FashionScreen} />
          </>
        )}
      </Stack.Navigator>
    </NavigationContainer>
  );
};

export default AppNavigator;

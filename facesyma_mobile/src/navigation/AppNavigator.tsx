// src/navigation/AppNavigator.tsx
import React, { useEffect, useMemo } from 'react';
import { NavigationContainer } from '@react-navigation/native';
import { createNativeStackNavigator } from '@react-navigation/native-stack';
import { createBottomTabNavigator } from '@react-navigation/bottom-tabs';
import { View, Text, ActivityIndicator } from 'react-native';
import { useDispatch, useSelector } from 'react-redux';
import { AppDispatch, RootState } from '../store';
import { restoreSession } from '../store/authSlice';
import theme from '../utils/theme';
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

const Stack = createNativeStackNavigator();
const Tab   = createBottomTabNavigator();

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
          backgroundColor:   theme.colors.surface,
          borderTopColor:    theme.colors.borderWarm,
          borderTopWidth:    1,
          height:            82,
          paddingBottom:     16,
          paddingTop:        8,
        },
        tabBarActiveTintColor:   theme.colors.gold,
        tabBarInactiveTintColor: theme.colors.textMuted,
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
              backgroundColor: focused ? theme.colors.warmAmberGlow : 'transparent',
            }}>
              <Text style={{ fontSize: focused ? 21 : 18 }}>{tab?.icon}</Text>
            </View>
          );
        },
      })}
    >
      {TABS.map(tab => <Tab.Screen key={tab.name} name={tab.name} component={tab.component} />)}
    </Tab.Navigator>
  );
};

const SplashScreen = () => (
  <View style={{
    flex:1, backgroundColor: theme.colors.background,
    alignItems:'center', justifyContent:'center', gap: theme.spacing.lg,
  }}>
    <View style={{
      width:80, height:80, borderRadius:40,
      borderWidth:1.5, borderColor: theme.colors.gold,
      backgroundColor: theme.colors.goldGlow,
      alignItems:'center', justifyContent:'center',
      ...theme.shadow.gold,
    }}>
      <Text style={{ fontSize: 36 }}>👁</Text>
    </View>
    <Text style={{
      ...theme.typography.goldLabel, fontSize:16,
      letterSpacing:5, color: theme.colors.gold,
    }}>FACESYMA</Text>
    <ActivityIndicator color={theme.colors.warmAmber} />
  </View>
);

const AppNavigator = () => {
  const dispatch = useDispatch<AppDispatch>();
  const { isAuthenticated, isLoading } = useSelector((s: RootState) => s.auth);
  const [ready, setReady] = React.useState(false);

  useEffect(() => {
    dispatch(restoreSession()).finally(() => setReady(true));
  }, []);

  if (!ready || isLoading) return <SplashScreen />;

  return (
    <NavigationContainer theme={{
      dark: true,
      colors: {
        primary:      theme.colors.gold,
        background:   theme.colors.background,
        card:         theme.colors.surface,
        text:         theme.colors.textPrimary,
        border:       theme.colors.border,
        notification: theme.colors.warmAmber,
      },
    }}>
      <Stack.Navigator screenOptions={{ headerShown: false }}>
        {!isAuthenticated ? (
          <>
            <Stack.Screen name="Onboarding" component={OnboardingScreen} />
            <Stack.Screen name="Auth"       component={AuthScreen} />
          </>
        ) : (
          <>
            <Stack.Screen name="Main"              component={MainTabs} />
            <Stack.Screen name="Chat"              component={ChatScreen} />
            <Stack.Screen name="Twins"             component={TwinsScreen} />
            <Stack.Screen name="Astrology"         component={AstrologyScreen} />
            <Stack.Screen name="ArtMatch"          component={ArtMatchScreen} />
            <Stack.Screen name="Daily"             component={DailyScreen} />
            <Stack.Screen name="Assessment"        component={AssessmentScreen} />
            <Stack.Screen name="AssessmentHistory" component={AssessmentHistoryScreen} />
            <Stack.Screen name="Fashion"           component={FashionScreen} />
          </>
        )}
      </Stack.Navigator>
    </NavigationContainer>
  );
};

export default AppNavigator;

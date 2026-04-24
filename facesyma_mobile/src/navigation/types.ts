// src/navigation/types.ts
import type { NativeStackNavigationProp, NativeStackScreenProps } from '@react-navigation/native-stack';
import type { BottomTabNavigationProp } from '@react-navigation/bottom-tabs';
import type { CompositeNavigationProp } from '@react-navigation/native';

export type RootStackParamList = {
  Onboarding:        undefined;
  Auth:              undefined;
  Main:              undefined;
  Chat:              { analysisResult?: unknown; lang?: string } | undefined;
  Twins:             undefined;
  Astrology:         undefined;
  ArtMatch:          undefined;
  Daily:             undefined;
  Assessment:        undefined;
  AssessmentHistory: undefined;
  Fashion:           { analysisResult?: unknown; lang?: string } | undefined;
};

export type TabParamList = {
  Home:     undefined;
  Analysis: undefined;
  Profile:  undefined;
};

export type AppNavProp = NativeStackNavigationProp<RootStackParamList>;

export type HomeNavProp = CompositeNavigationProp<
  BottomTabNavigationProp<TabParamList, 'Home'>,
  NativeStackNavigationProp<RootStackParamList>
>;

export type ProfileNavProp = CompositeNavigationProp<
  BottomTabNavigationProp<TabParamList, 'Profile'>,
  NativeStackNavigationProp<RootStackParamList>
>;

export type AnalysisNavProp = CompositeNavigationProp<
  BottomTabNavigationProp<TabParamList, 'Analysis'>,
  NativeStackNavigationProp<RootStackParamList>
>;

export type ScreenProps<T extends keyof RootStackParamList> = NativeStackScreenProps<RootStackParamList, T>;

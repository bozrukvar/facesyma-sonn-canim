// src/navigation/types.ts
import type { NativeStackNavigationProp, NativeStackScreenProps } from '@react-navigation/native-stack';
import type { BottomTabNavigationProp } from '@react-navigation/bottom-tabs';
import type { CompositeNavigationProp } from '@react-navigation/native';

export type RootStackParamList = {
  Onboarding:        undefined;
  Auth:              undefined;
  ProfileSetup:      undefined;
  Main:              undefined;
  Chat:              { analysisResult?: unknown; lang?: string } | undefined;
  Twins:             undefined;
  Astrology:         undefined;
  ArtMatch:          undefined;
  Daily:             undefined;
  Assessment:        undefined;
  AssessmentHistory: undefined;
  Account:           undefined;
  Fashion:           { analysisResult?: unknown; lang?: string } | undefined;
  Communities:       { communityType?: string } | undefined;
  CommunityChat:     { communityId: string; communityName: string };
  PeerChatList:      undefined;
  PeerChatRequest:   { requestId?: string; toUserId?: number; toUsername?: string; compatScore?: number; source?: string };
  PeerChat:          { roomId: string; otherUserId: number; otherUsername: string; compatScore?: number };
  Diet:              undefined;
  Gamification:      undefined;
  Leaderboard:       { tab?: 'global' | 'trending' } | undefined;
  Badges:            { badgeId?: string } | undefined;
  CoinWallet:        undefined;
  MealGame:          { countryCode?: string } | undefined;
  DiscoveryGame:     { gameType?: string } | undefined;
  Challenges:        undefined;
  Missions:          undefined;
  CoachHub:          undefined;
  CoachGoals:        undefined;
  CoachBirth:        undefined;
  Memories:          undefined;
  GoldenRatioOverlay:    { imageUri: string; lang: string; goldenScore: number; goldenGrade: string };
  GoldenTransform:       { imageUri: string; lang: string; realMeasurements?: any[] };
  Similarity:            { sifatlar: string[]; lang: string };
  Partner:               undefined;
  CompatibilityReport:   undefined;
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

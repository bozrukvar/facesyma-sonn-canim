// src/types/api.ts — API response shape interfaces

export interface AnalysisAttribute {
  name: string;
  score: number;
  description?: string;
}

export interface AnalysisResult {
  golden_ratio?: number;
  age_group?: string;
  gender?: string;
  attributes?: AnalysisAttribute[];
  kariyer?: string;
  liderlik?: string;
  daily?: string;
  face_shape?: string;
  sifatlar?: Array<{ sifat: string; score: number }>;
  [key: string]: unknown; // backend may add new fields
}

export interface ArtMatch {
  id: string | number;
  rank: number;
  title: string;
  artist: string;
  year: string | number;
  museum: string;
  style: string;
  similarity: number;
}

export interface ArtMatchResult {
  overall_score?: number;
  grade?: string;
  matches?: ArtMatch[];
  message?: string;
}

export interface TwinPerson {
  user_id?: number;
  name?: string;
  similarity: number;
  avatar?: string;
}

export interface TwinsDimensions {
  face_similarity: number;
  character_compat: number;
  complementarity: number;
  shared_strengths_score: number;
  shared_strengths_list: string[];
  eq_compat: number;
  romantic_compat: number;
  social_compat: number;
  teamwork_compat: number;
  positive_shared: string[];
  negative_shared: string[];
  activity_suggestions: string[];
  community_type: string;
}

export interface TwinsResult {
  group_score?: number;
  pair_scores?: Record<string, number>;
  similarity_scores?: TwinPerson[];
  average_similarity?: number;
  most_similar?: TwinPerson;
  dimensions?: TwinsDimensions;
}

export interface AstrologyResult {
  western_sign?: string;
  western_sign_label?: string;
  western_sign_emoji?: string;
  chinese_animal_label?: string;
  element_label?: string;
  face_reading?: string;
  daily_message?: string;
  astrology?: Record<string, string>;
  numerology?: Record<string, string>;
  sun_sign?: string;
  moon_sign?: string;
  rising_sign?: string;
  personality_summary?: string;
  traits?: string[];
  compatibility?: string[];
}

export interface AssessmentDomainScore {
  score: number;
  level?: string;
  level_tr?: string;
}

export interface AssessmentResult {
  overall_score: number;
  overall_level_tr: string;
  breakdown: Record<string, AssessmentDomainScore>;
  recommendations: string[];
  responses_counted: number;
}

// src/types/api.ts — API response shape interfaces

export interface AnalysisAttribute {
  name: string;
  score: number;
  description?: string;
}

export interface AnalysisResult {
  result?: string;          // Plain text personality trait summary
  golden_ratio?: number;
  age_group?: string;
  gender?: string;
  attributes?: AnalysisAttribute[];
  kisilik?: string;
  kariyer?: string;
  liderlik?: string;
  sosyal?: string;
  daily?: string;
  face_shape?: string;
  sifatlar?: Array<{ sifat: string; score: number }>;
  image_quality?: Record<string, unknown>;
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
  image_url?: string;
  reason?: string;
  primary_cluster?: string;
  emoji?: string;
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
  numerology?: {
    life_path_number: number;
    life_path_meaning: string;
    day_number: number;
    month_number: number;
    year_number: number;
    personal_year_number: number;
    personal_year_meaning: string;
    personal_year_label: string;
    current_year: number;
    is_master_number: boolean;
    master_label?: string;
  };
  name_numerology?: {
    name: string;
    expression_number: number;
    expression_meaning: string;
    soul_urge_number: number;
    soul_urge_meaning: string;
    personality_number: number;
    personality_meaning: string;
    ebced: { total: number; reduced: number; meaning: string; };
    kabala: { total: number; reduced: number; meaning: string; };
    labels: {
      title: string;
      expression: string;
      soul_urge: string;
      personality: string;
      ebced_title: string;
      kabala_title: string;
      total: string;
      reduced: string;
    };
  };
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
  description?: string;
}

export interface AssessmentResult {
  overall_score: number;
  overall_level_tr: string;
  breakdown: Record<string, AssessmentDomainScore>;
  recommendations: string[];
  responses_counted: number;
}

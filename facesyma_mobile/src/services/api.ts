// src/services/api.ts
// Microservis mimarisi — her servis ayrı endpoint
import axios, { AxiosInstance } from 'axios';
import AsyncStorage from '@react-native-async-storage/async-storage';

// ── Servis URL'leri ────────────────────────────────────────────────────────────
// Tek Django backend — tüm endpoint'ler /api/v1/ altında
const SERVICES = {
  analysis: 'https://api.facesyma.com/api/v1/analysis',
  auth:     'https://api.facesyma.com/api/v1/auth',
  chat:     'https://api.facesyma.com/api/v1/chat',
  twins:    'https://api.facesyma.com/api/v1/analysis',
  art:      'https://api.facesyma.com/api/v1/analysis',
};

// Geliştirme ortamı (local)
const DEV_SERVICES = {
  analysis: 'http://10.0.2.2:8000/api/v1/analysis',  // Android emülatör
  auth:     'http://10.0.2.2:8000/api/v1/auth',
  chat:     'http://10.0.2.2:8000/api/v1/chat',
  twins:    'http://10.0.2.2:8000/api/v1/analysis',
  art:      'http://10.0.2.2:8000/api/v1/analysis',
};

const IS_DEV = __DEV__;
const BASE = IS_DEV ? DEV_SERVICES : SERVICES;

// ── Axios instance fabrikası ────────────────────────────────────────────────────
function createClient(baseURL: string): AxiosInstance {
  const client = axios.create({
    baseURL,
    timeout: 30000,
    headers: { 'Content-Type': 'application/json' },
  });

  // JWT interceptor — her isteğe token ekle
  client.interceptors.request.use(async (config) => {
    const token = await AsyncStorage.getItem('access_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  });

  // Token yenileme interceptor
  client.interceptors.response.use(
    (res) => res,
    async (error) => {
      if (error.response?.status === 401) {
        try {
          const refresh = await AsyncStorage.getItem('refresh_token');
          if (refresh) {
            const res = await axios.post(`${BASE.auth}/token/refresh/`, {
              refresh,
            });
            const newToken = res.data.access;
            await AsyncStorage.setItem('access_token', newToken);
            error.config.headers.Authorization = `Bearer ${newToken}`;
            return client(error.config);
          }
        } catch {
          await AsyncStorage.multiRemove(['access_token', 'refresh_token', 'user']);
        }
      }
      return Promise.reject(error);
    }
  );

  return client;
}

// ── Servis client'ları ─────────────────────────────────────────────────────────
export const analysisClient = createClient(BASE.analysis);
export const authClient     = createClient(BASE.auth);
export const chatClient     = createClient(BASE.chat);
export const twinsClient    = createClient(BASE.twins);
export const artClient      = createClient(BASE.art);

// ── Auth API ──────────────────────────────────────────────────────────────────
export const AuthAPI = {
  // Email + şifre kayıt
  registerEmail: async (data: {
    email: string;
    password: string;
    name: string;
  }) => {
    const res = await authClient.post('/register/', data);
    return res.data;
  },

  // Email + şifre giriş
  loginEmail: async (email: string, password: string) => {
    const res = await authClient.post('/token/', { email, password });
    return res.data; // { access, refresh, user }
  },

  // Google Sign-In — token Google'dan alınır, backend'e gönderilir
  loginGoogle: async (idToken: string) => {
    const res = await authClient.post('/google/', { id_token: idToken });
    return res.data; // { access, refresh, user }
  },

  // Profil getir
  getProfile: async () => {
    const res = await authClient.get('/me/');
    return res.data;
  },

  // Şifre sıfırlama
  forgotPassword: async (email: string) => {
    const res = await authClient.post('/password/reset/', { email });
    return res.data;
  },

  // Token kaydet
  saveTokens: async (access: string, refresh: string) => {
    await AsyncStorage.multiSet([
      ['access_token', access],
      ['refresh_token', refresh],
    ]);
  },

  // Logout
  logout: async () => {
    await AsyncStorage.multiRemove(['access_token', 'refresh_token', 'user']);
  },

  // Mevcut kullanıcıyı kontrol et
  getCurrentUser: async () => {
    const userStr = await AsyncStorage.getItem('user');
    return userStr ? JSON.parse(userStr) : null;
  },
};

// ── Analysis API (mevcut Django backend ile uyumlu) ───────────────────────────
export const AnalysisAPI = {
  // Yüz analizi — fotoğraf gönder, sonuç al
  analyze: async (imageUri: string, lang = 'tr') => {
    const formData = new FormData();
    formData.append('image', {
      uri: imageUri,
      name: 'photo.jpg',
      type: 'image/jpeg',
    } as any);
    formData.append('lang', lang);

    const res = await analysisClient.post('/analyze/', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
      timeout: 60000,
    });
    return res.data;
  },

  // Astroloji analizi
  analyzeAstrology: async (imageUri: string, birthDate: string, birthTime?: string, lang = 'tr') => {
    const formData = new FormData();
    formData.append('image', { uri: imageUri, name: 'photo.jpg', type: 'image/jpeg' } as any);
    formData.append('lang', lang);
    formData.append('birth_date', birthDate);
    if (birthTime) formData.append('birth_time', birthTime);

    const res = await analysisClient.post('/analyze/astrology/', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
      timeout: 60000,
    });
    return res.data;
  },

  // Twins analizi
  analyzeTwins: async (imageUris: string[], lang = 'tr') => {
    const formData = new FormData();
    imageUris.forEach((uri, i) => {
      formData.append(`image_${i}`, { uri, name: `photo_${i}.jpg`, type: 'image/jpeg' } as any);
    });
    formData.append('lang', lang);
    formData.append('count', String(imageUris.length));

    const res = await twinsClient.post('/analyze/', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
      timeout: 90000,
    });
    return res.data;
  },

  // Art match
  analyzeArt: async (imageUri: string) => {
    const formData = new FormData();
    formData.append('image', { uri: imageUri, name: 'photo.jpg', type: 'image/jpeg' } as any);

    const res = await artClient.post('/match/', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
      timeout: 60000,
    });
    return res.data;
  },

  // Sonuç geçmişi
  getHistory: async () => {
    const res = await analysisClient.get('/history/');
    return res.data;
  },

  // Günlük motivasyon
  getDailyMotivation: async (lang = 'tr') => {
    const res = await analysisClient.get(`/daily/?lang=${lang}`);
    return res.data;
  },
};

// ── Assessment API (Questionnaires & Tests) ───────────────────────────────────
export const AssessmentAPI = {
  // Get questions for a test type
  getQuestions: async (testType: string, lang = 'tr') => {
    const res = await analysisClient.get(`/assessment/questions/${testType}/?lang=${lang}`);
    return res.data;
  },

  // Submit responses and get scoring + recommendations
  submitAssessment: async (testType: string, responses: Array<{ q_id: string; score: number }>, lang = 'tr') => {
    const res = await analysisClient.post(`/assessment/submit/${testType}/`, {
      lang,
      responses,
    });
    return res.data;
  },

  // Save assessment result to MongoDB
  saveResult: async (testType: string, result: any) => {
    const res = await analysisClient.post(`/assessment/results/${testType}/`, {
      overall_score: result.data.overall_score,
      overall_level_tr: result.data.overall_level_tr,
      breakdown: result.data.breakdown,
      recommendations: result.data.recommendations,
      responses_counted: result.data.responses_counted,
    });
    return res.data;
  },

  // Get assessment history
  getHistory: async (limit = 10) => {
    const res = await analysisClient.get(`/assessment/history/?limit=${limit}`);
    return res.data;
  },
};

// ── Chat API ──────────────────────────────────────────────────────────────────
// ── AI Chat API (FastAPI :8002) ───────────────────────────────────────────────
const AI_CHAT_BASE = __DEV__
  ? 'http://10.0.2.2:8002'
  : 'https://api.facesyma.com/ai';

const aiChatAxios = axios.create({ baseURL: AI_CHAT_BASE, timeout: 60000 });
aiChatAxios.interceptors.request.use(async (cfg) => {
  const t = await AsyncStorage.getItem('access_token');
  if (t) cfg.headers.Authorization = `Bearer ${t}`;
  return cfg;
});

export const ChatAPI = {
  startChat: async (analysisResult: object, lang = 'tr', firstMessage?: string) => {
    const res = await aiChatAxios.post('/v1/chat/analyze', {
      analysis_result: analysisResult, lang, first_message: firstMessage,
    });
    return res.data as { conversation_id: string; assistant_message: string; lang: string };
  },
  sendMessage: async (conversationId: string, message: string, lang = 'tr') => {
    const res = await aiChatAxios.post('/v1/chat/message', {
      conversation_id: conversationId, message, lang,
    });
    return res.data as { conversation_id: string; assistant_message: string };
  },
  getHistory: async () => {
    const res = await aiChatAxios.get('/v1/chat/history');
    return res.data as { conversations: object[] };
  },
  getConversation: async (id: string) => {
    const res = await aiChatAxios.get(`/chat/${id}`);
    return res.data;
  },
  deleteConversation: async (id: string) => {
    await aiChatAxios.delete(`/chat/${id}`);
  },
  getLanguages: async () => {
    const res = await aiChatAxios.get('/languages');
    return res.data as { languages: Record<string, object> };
  },
};

// ── Coach API (FastAPI :8003) ─────────────────────────────────────────────────
const COACH_BASE = __DEV__
  ? 'http://10.0.2.2:8003'
  : 'https://api.facesyma.com/coach';

const coachAxios = axios.create({ baseURL: COACH_BASE, timeout: 30000 });
coachAxios.interceptors.request.use(async (cfg) => {
  const t = await AsyncStorage.getItem('access_token');
  if (t) cfg.headers.Authorization = `Bearer ${t}`;
  return cfg;
});

export const CoachAPI = {
  getModules: async () => (await coachAxios.get('/coach/modules')).data,
  createProfile: async (data: {
    lang: string; birth_date?: string; birth_time?: string;
    birth_city?: string; dominant_sifatlar?: string[];
  }) => (await coachAxios.post('/coach/profile', data)).data,
  getProfile: async (userId: number) => (await coachAxios.get(`/coach/profile/${userId}`)).data,
  analyzeWithCoach: async (analysisResult: object, lang = 'tr', modules?: string[]) =>
    (await coachAxios.post('/coach/analyze', { analysis_result: analysisResult, lang, include_modules: modules })).data,
  birthAnalysis: async (birthDate: string, birthTime?: string, lang = 'tr') =>
    (await coachAxios.post('/coach/birth', { birth_date: birthDate, birth_time: birthTime, lang })).data,
  getGoals: async (userId: number, status?: string) =>
    (await coachAxios.get(`/coach/goals/${userId}`, { params: status ? { status } : {} })).data,
  addGoal: async (data: { title: string; module?: string; target_date?: string; priority?: string }) =>
    (await coachAxios.post('/coach/goals', data)).data,
  updateGoal: async (goalId: string, status: string) =>
    (await coachAxios.put(`/coach/goals/${goalId}`, null, { params: { status } })).data,
  getFashionAdvice: async (
    analysisResult: object,
    lang = 'tr',
    mevsim?: string,
    kategori?: string
  ) => (await coachAxios.post('/coach/giyim', {
    analysis_result: analysisResult,
    lang,
    mevsim,
    kategori,
    top_n: 3,
  })).data,
};

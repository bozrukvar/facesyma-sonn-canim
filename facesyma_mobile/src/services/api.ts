// src/services/api.ts
// Microservis mimarisi — her servis ayrı endpoint
import axios, { AxiosInstance } from 'axios';
import AsyncStorage from '@react-native-async-storage/async-storage';
import type { AssessmentResult } from '../types/api';

export interface CommunityItem {
  _id: string;
  name: string;
  type: string;
  trait_name?: string;
  member_count: number;
  description?: string;
  is_member?: boolean;
  created_at?: string | number;
}

// ── Force-logout callback ──────────────────────────────────────────────────────
// Circular import'u önlemek için: App.tsx'te registerLogoutHandler ile set edilir.
// Token yenileme tamamen başarısız olursa Redux state + navigation sıfırlanır.
let _logoutHandler: (() => void) | null = null;
export const registerLogoutHandler = (fn: () => void): void => {
  _logoutHandler = fn;
};

// ── In-memory token cache ──────────────────────────────────────────────────────
// AsyncStorage her istekte storage I/O yapar; bu cache bunu tek seferlik yapar.
let _cachedToken: string | null = undefined as unknown as string | null;

export const setCachedToken = (token: string | null): void => {
  _cachedToken = token;
};

const getToken = async (): Promise<string | null> => {
  if (_cachedToken !== (undefined as unknown as string | null)) return _cachedToken;
  _cachedToken = await AsyncStorage.getItem('access_token');
  return _cachedToken;
};

// ── Servis URL'leri ────────────────────────────────────────────────────────────
// Tek Django backend — tüm endpoint'ler /api/v1/ altında
const SERVICES = {
  analysis:      'https://api.facesyma.com/api/v1/analysis',
  auth:          'https://api.facesyma.com/api/v1/auth',
  chat:          'https://api.facesyma.com/api/v1/chat',
  twins:         'https://api.facesyma.com/api/v1/analysis',
  art:           'https://api.facesyma.com/api/v1/analysis',
  gamification:  'https://api.facesyma.com/api/v1/gamification',
};

// Geliştirme ortamı (local)
const DEV_SERVICES = {
  analysis:      'http://10.0.2.2/api/v1/analysis',  // Android emülatör → nginx port 80
  auth:          'http://10.0.2.2/api/v1/auth',
  chat:          'http://10.0.2.2/api/v1/chat',
  twins:         'http://10.0.2.2/api/v1/analysis',
  art:           'http://10.0.2.2/api/v1/analysis',
  gamification:  'http://10.0.2.2/api/v1/gamification',
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

  // JWT interceptor — her isteğe token ekle (in-memory cache kullanır)
  client.interceptors.request.use(async (config) => {
    const token = await getToken();
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  });

  // Token yenileme interceptor
  client.interceptors.response.use(
    (res) => res,
    async (error) => {
      const cfg = error.config;
      if (error.response?.status === 401 && !cfg._retried) {
        cfg._retried = true;
        try {
          const refresh = await AsyncStorage.getItem('refresh_token');
          if (refresh) {
            const res = await axios.post(`${BASE.auth}/token/refresh/`, {
              refresh,
            });
            const newToken = res.data.access;
            await AsyncStorage.setItem('access_token', newToken);
            setCachedToken(newToken);
            cfg.headers.Authorization = `Bearer ${newToken}`;
            return client(cfg);
          }
        } catch {
          setCachedToken(null);
          await AsyncStorage.multiRemove(['access_token', 'refresh_token', 'user']);
          _logoutHandler?.();
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
    terms_accepted: boolean;
    gdpr_consent: boolean;
  }) => {
    const res = await authClient.post('/register/', data);
    return res.data;
  },

  // Profil güncelle (onboarding + genel)
  updateProfile: async (data: Record<string, unknown>) => {
    const res = await authClient.patch('/me/', data);
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

  // Şifre sıfırlama (e-posta gönderir)
  forgotPassword: async (email: string) => {
    const res = await authClient.post('/password/reset/', { email });
    return res.data;
  },

  // Şifre sıfırlama onayı (e-postadan alınan token + yeni şifre)
  confirmResetPassword: async (token: string, newPassword: string) => {
    const res = await authClient.post('/password/reset/confirm/', {
      token,
      new_password: newPassword,
    });
    return res.data;
  },

  // Şifre değiştir (authenticated — eski şifre gerekli)
  changePassword: async (oldPassword: string, newPassword: string) => {
    const res = await authClient.post('/password/change/', {
      old_password: oldPassword,
      new_password: newPassword,
    });
    return res.data;
  },

  // Token kaydet
  saveTokens: async (access: string, refresh: string) => {
    setCachedToken(access);
    await AsyncStorage.multiSet([
      ['access_token', access],
      ['refresh_token', refresh],
    ]);
  },

  // Logout
  logout: async () => {
    setCachedToken(null);
    await AsyncStorage.multiRemove(['access_token', 'refresh_token', 'user']);
  },

  // Hesap sil (GDPR — kalıcı silme)
  deleteAccount: async () => {
    const res = await authClient.delete('/me/delete/');
    return res.data;
  },

  // Veri dışa aktar (GDPR Madde 20)
  exportData: async () => {
    const res = await authClient.get('/me/export/');
    return res.data;
  },

  // Mevcut kullanıcıyı kontrol et
  getCurrentUser: async () => {
    const userStr = await AsyncStorage.getItem('user');
    if (!userStr) return null;
    try {
      return JSON.parse(userStr);
    } catch {
      return null;
    }
  },

  // FCM push token kaydet / güncelle
  registerDeviceToken: async (token: string, platform: 'ios' | 'android' | string) => {
    const res = await authClient.post('/device-token/', { device_token: token, platform });
    return res.data;
  },

  // FCM push token kaldır (logout'ta çağrılır)
  removeDeviceToken: async () => {
    const res = await authClient.delete('/device-token/');
    return res.data;
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
    } as unknown as Blob);
    formData.append('lang', lang);

    const res = await analysisClient.post('/analyze/', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
      timeout: 60000,
    });
    return res.data?.data ?? res.data;
  },

  // Yüz merkezi tespiti — scanner overlay konumlandırması için
  detectFace: async (imageUri: string): Promise<{ cx: number; cy: number; fw?: number; fh?: number; found: boolean }> => {
    try {
      const formData = new FormData();
      formData.append('image', { uri: imageUri, name: 'face.jpg', type: 'image/jpeg' } as unknown as Blob);
      const res = await analysisClient.post('/detect-face/', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
        timeout: 8000,
      });
      return res.data;
    } catch {
      return { cx: 0.50, cy: 0.38, found: false };
    }
  },

  // Astroloji analizi
  analyzeAstrology: async (imageUri: string, birthDate: string, birthTime?: string, lang = 'tr') => {
    const formData = new FormData();
    formData.append('image', { uri: imageUri, name: 'photo.jpg', type: 'image/jpeg' } as unknown as Blob);
    formData.append('lang', lang);
    formData.append('birth_date', birthDate);
    if (birthTime) formData.append('birth_time', birthTime);

    const res = await analysisClient.post('/analyze/astrology/', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
      timeout: 60000,
    });
    return res.data?.data ?? res.data;
  },

  // Twins analizi
  analyzeTwins: async (imageUris: string[], lang = 'tr') => {
    const formData = new FormData();
    imageUris.forEach((uri, i) => {
      formData.append(`image_${i}`, { uri, name: `photo_${i}.jpg`, type: 'image/jpeg' } as unknown as Blob);
    });
    formData.append('lang', lang);
    formData.append('count', String(imageUris.length));

    const res = await twinsClient.post('/twins/', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
      timeout: 90000,
    });
    return res.data?.data ?? res.data;
  },

  // Art match
  analyzeArt: async (imageUri: string, lang = 'tr') => {
    const formData = new FormData();
    formData.append('image', { uri: imageUri, name: 'photo.jpg', type: 'image/jpeg' } as unknown as Blob);
    formData.append('lang', lang);

    const res = await artClient.post('/analyze/art/', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
      timeout: 60000,
    });
    return res.data?.data ?? res.data;
  },

  // Sonuç geçmişi
  getHistory: async () => {
    const res = await analysisClient.get('/history/');
    return res.data;
  },

  // Tek analiz kaydını sil
  deleteHistory: async (recordId: string) => {
    const res = await analysisClient.delete(`/history/${encodeURIComponent(recordId)}/`);
    return res.data;
  },

  // Tüm analiz geçmişini sil
  deleteAllHistory: async () => {
    const res = await analysisClient.delete('/history/all/');
    return res.data;
  },

  // Günlük motivasyon
  getDailyMotivation: async (lang = 'tr') => {
    const res = await analysisClient.get('/daily/', { params: { lang } });
    return res.data;
  },

  // Altın oran overlay (annotated face image + measurements)
  analyzeGoldenOverlay: async (imageUri: string, lang = 'tr') => {
    const formData = new FormData();
    formData.append('image', { uri: imageUri, name: 'photo.jpg', type: 'image/jpeg' } as unknown as Blob);
    formData.append('lang', lang);
    const res = await analysisClient.post('/analyze/golden/', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
      timeout: 60000,
    });
    return res.data?.data ?? res.data;
  },

  // Altın oran before/after transform (gerçek ölçümler ile)
  analyzeGoldenTransform: async (imageUri: string, lang = 'tr', realMeasurements?: any[]) => {
    const formData = new FormData();
    formData.append('image', { uri: imageUri, name: 'photo.jpg', type: 'image/jpeg' } as unknown as Blob);
    formData.append('lang', lang);
    if (realMeasurements) formData.append('real_measurements', JSON.stringify(realMeasurements));
    const res = await analysisClient.post('/analyze/golden/transform/', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
      timeout: 60000,
    });
    return res.data?.data ?? res.data;
  },

  // Karakter benzerliği — arketip sistemi
  getSimilarities: async (sifatlar: string[], lang = 'tr') => {
    const res = await analysisClient.post('/analyze/similarity/', { sifatlar, lang }, {
      headers: { 'Content-Type': 'application/json' },
    });
    return res.data?.data ?? res.data;
  },

  // Topluluklar
  listCommunities: async (type?: string, limit = 30) => {
    const params: Record<string, unknown> = { limit };
    if (type) params.type = type;
    const res = await analysisClient.get('/communities/', { params });
    return res.data as { success: boolean; data: CommunityItem[]; count: number };
  },
  joinCommunity: async (communityId: string) => {
    const res = await analysisClient.post(`/communities/${encodeURIComponent(communityId)}/join/`);
    return res.data as { success: boolean; data: { membership_status: string; harmony_level: number } };
  },
  getCommunityMembers: async (communityId: string, limit = 20) => {
    const res = await analysisClient.get(`/communities/${encodeURIComponent(communityId)}/members/`, { params: { limit } });
    return res.data;
  },
};

// ── Assessment API (Questionnaires & Tests) ───────────────────────────────────
export const AssessmentAPI = {
  // Get questions for a test type
  getQuestions: async (testType: string, lang = 'tr') => {
    const res = await analysisClient.get(`/assessment/questions/${encodeURIComponent(testType)}/`, { params: { lang } });
    return res.data;
  },

  // Submit responses and get scoring + recommendations
  submitAssessment: async (testType: string, responses: Array<{ q_id: string; score: number }>, lang = 'tr') => {
    const res = await analysisClient.post(`/assessment/submit/${encodeURIComponent(testType)}/`, {
      lang,
      responses,
    });
    return res.data;
  },

  // Save assessment result to MongoDB
  saveResult: async (testType: string, result: { data: AssessmentResult }) => {
    const res = await analysisClient.post(`/assessment/results/${encodeURIComponent(testType)}/`, {
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

// ── AI Chat API (FastAPI :8002, routed through nginx /chat/) ─────────────────
// DEV: direct to port 8002. PROD: via nginx location /chat/ → ai_chat:8002
const AI_CHAT_BASE = __DEV__
  ? 'http://10.0.2.2'  // Android emülatör → nginx port 80 → /chat/ → ai_chat:8002
  : 'https://api.facesyma.com';

const aiChatAxios = axios.create({ baseURL: AI_CHAT_BASE, timeout: 60000 });
aiChatAxios.interceptors.request.use(async (cfg) => {
  const token = await AsyncStorage.getItem('access_token');
  if (token) cfg.headers.Authorization = `Bearer ${token}`;
  return cfg;
});
aiChatAxios.interceptors.response.use(
  (res) => res,
  async (error) => {
    const cfg = error.config;
    if (error.response?.status === 401 && !cfg._retried) {
      cfg._retried = true;
      try {
        const refresh = await AsyncStorage.getItem('refresh_token');
        if (refresh) {
          const res = await axios.post(`${BASE.auth}/token/refresh/`, { refresh });
          const newToken = res.data.access;
          await AsyncStorage.setItem('access_token', newToken);
          cfg.headers.Authorization = `Bearer ${newToken}`;
          return aiChatAxios(cfg);
        }
      } catch {
        await AsyncStorage.multiRemove(['access_token', 'refresh_token', 'user']);
        _logoutHandler?.();
      }
    }
    return Promise.reject(error);
  }
);

export const ChatAPI = {
  startChat: async (analysisResult: object, lang = 'tr', firstMessage?: string) => {
    const res = await aiChatAxios.post('/chat/start', {
      analysis_result: analysisResult, lang, first_message: firstMessage,
    });
    return res.data as { conversation_id: string; assistant_message: string; lang: string; usage: { daily_used: number; daily_limit: number; plan: string } };
  },
  sendMessage: async (conversationId: string, message: string, lang = 'tr') => {
    const res = await aiChatAxios.post('/chat/message', {
      conversation_id: conversationId, message, lang,
    });
    return res.data as { conversation_id: string; assistant_message: string; usage: { daily_used: number; daily_limit: number; plan: string } };
  },
  getHistory: async () => {
    const res = await aiChatAxios.get('/chat/history');
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

// ── Peer Chat API (Django backend /api/v1/analysis/peer-chat/) ───────────────
export interface PeerChatRequest {
  _id: string;
  from_user_id: number;
  from_username: string;
  to_user_id: number;
  compatibility_score: number;
  source: string;
  status: string;
  created_at: number;
  expires_at: number;
}

export interface PeerChatRoom {
  _id: string;
  room_id: string;
  user_ids: number[];
  other_user: { id: number; username: string };
  source: string;
  compatibility_score: number;
  last_message_at: number | null;
  last_message_preview: string;
  my_unread: number;
  is_active: boolean;
}

export interface PeerMessage {
  _id: string;
  room_id: string;
  sender_id: number;
  content: string;
  type: 'text' | 'image' | 'file';
  file_url: string | null;
  file_name: string | null;
  file_size_bytes: number | null;
  created_at: number;
  read_by: number[];
}

const peerChatBase = IS_DEV
  ? 'http://10.0.2.2/api/v1/analysis'
  : 'https://api.facesyma.com/api/v1/analysis';
const peerChatClient = createClient(peerChatBase);

export const PeerChatAPI = {
  sendRequest: async (toUserId: number, compatScore?: number) => {
    const res = await peerChatClient.post('/peer-chat/request/', {
      to_user_id: toUserId,
      compatibility_score: compatScore ?? 0,
    });
    return res.data as { success: boolean; request_id?: string; room_id?: string; message: string };
  },

  respondRequest: async (requestId: string, action: 'accept' | 'reject') => {
    const res = await peerChatClient.post(`/peer-chat/request/${encodeURIComponent(requestId)}/respond/`, { action });
    return res.data as { success: boolean; status: string; room_id?: string };
  },

  getPendingRequests: async () => {
    const res = await peerChatClient.get('/peer-chat/request/pending/');
    return res.data as { success: boolean; data: PeerChatRequest[]; count: number };
  },

  getRooms: async () => {
    const res = await peerChatClient.get('/peer-chat/rooms/');
    return res.data as { success: boolean; data: PeerChatRoom[]; count: number };
  },

  getMessages: async (roomId: string, before?: number, limit = 50) => {
    const params: Record<string, unknown> = { limit };
    if (before) params.before = before;
    const res = await peerChatClient.get(`/peer-chat/rooms/${encodeURIComponent(roomId)}/messages/`, { params });
    return res.data as { success: boolean; data: PeerMessage[]; count: number; has_more: boolean };
  },

  sendMessage: async (roomId: string, content: string) => {
    const res = await peerChatClient.post(`/peer-chat/rooms/${encodeURIComponent(roomId)}/messages/`, { content });
    return res.data as { success: boolean; message: PeerMessage };
  },

  markRead: async (roomId: string) => {
    await peerChatClient.post(`/peer-chat/rooms/${encodeURIComponent(roomId)}/read/`);
  },

  leaveRoom: async (roomId: string) => {
    await peerChatClient.delete(`/peer-chat/rooms/${encodeURIComponent(roomId)}/`);
  },

  uploadFile: async (roomId: string, fileUri: string, fileName: string, fileType: string) => {
    const formData = new FormData();
    formData.append('file', { uri: fileUri, name: fileName, type: fileType } as unknown as Blob);
    formData.append('room_id', roomId);
    const res = await peerChatClient.post('/peer-chat/upload/', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
      timeout: 60000,
    });
    return res.data as { success: boolean; file_url: string; message?: PeerMessage };
  },

  getWsUrl: (roomId: string, token: string): string => {
    const host = IS_DEV ? '10.0.2.2' : 'api.facesyma.com';
    const protocol = IS_DEV ? 'ws' : 'wss';
    return `${protocol}://${host}/ws/chat/${roomId}/?token=${token}`;
  },
};

// ── Coach API (FastAPI :8003, routed through nginx /coach/) ──────────────────
// nginx location /coach/ → coach:8003 — full path preserved, no rewrite
const COACH_BASE = __DEV__
  ? 'http://10.0.2.2'  // Android emülatör → nginx port 80 → /coach/ → coach:8003
  : 'https://api.facesyma.com';

const coachAxios = axios.create({ baseURL: COACH_BASE, timeout: 30000 });
coachAxios.interceptors.request.use(async (cfg) => {
  const token = await AsyncStorage.getItem('access_token');
  if (token) cfg.headers.Authorization = `Bearer ${token}`;
  return cfg;
});
coachAxios.interceptors.response.use(
  (res) => res,
  async (error) => {
    const cfg = error.config;
    if (error.response?.status === 401 && !cfg._retried) {
      cfg._retried = true;
      try {
        const refresh = await AsyncStorage.getItem('refresh_token');
        if (refresh) {
          const res = await axios.post(`${BASE.auth}/token/refresh/`, { refresh });
          const newToken = res.data.access;
          await AsyncStorage.setItem('access_token', newToken);
          cfg.headers.Authorization = `Bearer ${newToken}`;
          return coachAxios(cfg);
        }
      } catch {
        await AsyncStorage.multiRemove(['access_token', 'refresh_token', 'user']);
        _logoutHandler?.();
      }
    }
    return Promise.reject(error);
  }
);

export const CoachAPI = {
  getModules: async () => (await coachAxios.get('/coach/modules')).data,
  createProfile: async (data: {
    lang: string; birth_date?: string; birth_time?: string;
    birth_city?: string; dominant_sifatlar?: string[];
  }) => (await coachAxios.post('/coach/profile', data)).data,
  getProfile: async (userId: number) => (await coachAxios.get(`/coach/profile/${encodeURIComponent(userId)}`)).data,
  analyzeWithCoach: async (analysisResult: object, lang = 'tr', modules?: string[]) =>
    (await coachAxios.post('/coach/analyze', { analysis_result: analysisResult, lang, include_modules: modules })).data,
  birthAnalysis: async (birthDate: string, birthTime?: string, lang = 'tr', name?: string, birthCity?: string) =>
    (await coachAxios.post('/coach/birth', { birth_date: birthDate, birth_time: birthTime, lang, name: name || undefined, birth_city: birthCity || undefined })).data,
  getGoals: async (userId: number, status?: string) =>
    (await coachAxios.get(`/coach/goals/${encodeURIComponent(userId)}`, { params: status ? { status } : {} })).data,
  addGoal: async (data: { title: string; module?: string; target_date?: string; priority?: string }) =>
    (await coachAxios.post('/coach/goals', data)).data,
  updateGoal: async (goalId: string, status: string) =>
    (await coachAxios.put(`/coach/goals/${encodeURIComponent(goalId)}`, null, { params: { status } })).data,
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

// ── Diet Coaching API (FastAPI :8002, routed through nginx /diet/) ───────────
// Serves meal recommendations per country (120 ISO-3166 country codes)
const dietAxios = axios.create({ baseURL: AI_CHAT_BASE, timeout: 30000 });
dietAxios.interceptors.request.use(async (cfg) => {
  const token = await AsyncStorage.getItem('access_token');
  if (token) cfg.headers.Authorization = `Bearer ${token}`;
  return cfg;
});
dietAxios.interceptors.response.use(
  (res) => res,
  async (error) => {
    const cfg = error.config;
    if (error.response?.status === 401 && !cfg._retried) {
      cfg._retried = true;
      try {
        const refresh = await AsyncStorage.getItem('refresh_token');
        if (refresh) {
          const res = await axios.post(`${BASE.auth}/token/refresh/`, { refresh });
          const newToken = res.data.access;
          await AsyncStorage.setItem('access_token', newToken);
          cfg.headers.Authorization = `Bearer ${newToken}`;
          return dietAxios(cfg);
        }
      } catch {
        await AsyncStorage.multiRemove(['access_token', 'refresh_token', 'user']);
        _logoutHandler?.();
      }
    }
    return Promise.reject(error);
  }
);

export interface DietSifat { sifat: string; score: number; }
export interface DietRecommendationRequest {
  user_id: number;
  country_code: string;
  country?: string;
  language_code?: string;
  sifats: DietSifat[];
  vegetarian?: boolean;
  vegan?: boolean;
  gluten_free?: boolean;
}

export const DietAPI = {
  getRecommendation: async (req: DietRecommendationRequest) => {
    const res = await dietAxios.post('/diet/recommendation/', req);
    return res.data as {
      status: string;
      data: {
        date: string;
        breakfast: { name: string; description?: string; reason: string; nutrition?: object; prep_time_min?: number };
        lunch:     { name: string; description?: string; reason: string; nutrition?: object; prep_time_min?: number };
        dinner:    { name: string; description?: string; reason: string; nutrition?: object; prep_time_min?: number };
        user_sifats: string[];
      };
      nutrition?: object;
      explanation?: string;
    };
  },

  getAlternatives: async (req: DietRecommendationRequest & { meal_type: string; count?: number }) => {
    const res = await dietAxios.post('/diet/alternatives/', req);
    return res.data as { status: string; meal_type: string; alternatives: object[]; count: number };
  },

  getMeals: async (country_code: string, meal_type?: string) => {
    const params: Record<string, string> = { country_code };
    if (meal_type) params.meal_type = meal_type;
    const res = await dietAxios.get('/diet/meals/', { params });
    return res.data as { status: string; country: string; meal_type: string; meals: object[]; count: number };
  },

  getCountries: async () => {
    const res = await dietAxios.get('/diet/countries/');
    return res.data as { status: string; countries: { name: string; country_code: string; meal_count: number }[]; count: number };
  },

  submitFeedback: async (userId: number, mealId: string, date: string, mealType: string, feedback: 'liked' | 'disliked' | 'neutral') => {
    const res = await dietAxios.post('/diet/feedback/', { user_id: userId, meal_id: mealId, date, meal_type: mealType, feedback });
    return res.data as { status: string; message: string };
  },
};

// ── Test Module API (FastAPI :8004, routed through nginx /test/) ─────────────
const TEST_BASE = __DEV__ ? 'http://10.0.2.2' : 'https://api.facesyma.com';

const testAxios = axios.create({ baseURL: TEST_BASE, timeout: 30000 });
testAxios.interceptors.request.use(async (cfg) => {
  const token = await AsyncStorage.getItem('access_token');
  if (token) cfg.headers.Authorization = `Bearer ${token}`;
  return cfg;
});
testAxios.interceptors.response.use(
  (res) => res,
  async (error) => {
    const cfg = error.config;
    if (error.response?.status === 401 && !cfg._retried) {
      cfg._retried = true;
      try {
        const refresh = await AsyncStorage.getItem('refresh_token');
        if (refresh) {
          const res = await axios.post(`${BASE.auth}/token/refresh/`, { refresh });
          const newToken = res.data.access;
          await AsyncStorage.setItem('access_token', newToken);
          cfg.headers.Authorization = `Bearer ${newToken}`;
          return testAxios(cfg);
        }
      } catch {
        await AsyncStorage.multiRemove(['access_token', 'refresh_token', 'user']);
        _logoutHandler?.();
      }
    }
    return Promise.reject(error);
  }
);

export interface TestQuestion {
  q_id: string;
  order: number;
  text: string;
  scale: { min: number; max: number; labels: string[] };
}

export interface StressDetails {
  depression_severity: string;
  anxiety_severity: string;
  crisis_flag: boolean;
  crisis_resource?: string;
}

export interface NonverbalDetails {
  congruent_accuracy?: number;
  incongruent_accuracy?: number;
  interference_effect?: number;
  avg_reaction_ms?: number;
  [key: string]: number | undefined;
}

export interface NonverbalAnswer {
  q_id: string;
  score: number;
  selected_option?: string;
  response_time_ms?: number;
}

export interface SpotlightItem { name: string; score: number; }

export interface TestSubmitResponse {
  result_id: string;
  test_type: string;
  domain_scores: Record<string, number>;
  ai_interpretation: string;
  strengths?: SpotlightItem[];
  growth_areas?: SpotlightItem[];
  pdf_url?: string;
  stress_details?: StressDetails;
  nonverbal_details?: NonverbalDetails | null;
}

export const TestAPI = {
  startTest: async (testType: string, lang = 'tr') => {
    const res = await testAxios.post('/test/start', { test_type: testType, lang });
    return res.data as {
      session_id: string;
      test_type: string;
      lang: string;
      questions: TestQuestion[];
      requires_health_consent?: boolean;
      is_clinical?: boolean;
      disclaimer?: string;
    };
  },

  submitTest: async (
    sessionId: string,
    testType: string,
    lang: string,
    answers: Array<NonverbalAnswer>
  ): Promise<TestSubmitResponse> => {
    const res = await testAxios.post('/test/submit', {
      session_id: sessionId,
      test_type: testType,
      lang,
      answers,
    });
    return res.data;
  },

  getHistory: async (userId: number) => {
    const res = await testAxios.get(`/test/results/${encodeURIComponent(userId)}`);
    return res.data as { results: object[] };
  },
};

// ── Community Chat API ────────────────────────────────────────────────────────
export interface CommunityMessage {
  _id: string;
  community_id: string;
  sender_id: number;
  sender_username: string;
  content: string;
  type: 'text' | 'image' | 'file';
  file_url: string | null;
  file_name: string | null;
  file_size_bytes: number | null;
  created_at: number;
  read_by: number[];
}

export const CommunityChatAPI = {
  getMessages: async (communityId: string, before?: number, limit = 50) => {
    const params: Record<string, unknown> = { limit };
    if (before) params.before = before;
    const res = await analysisClient.get(
      `/communities/${encodeURIComponent(communityId)}/chat/messages/`,
      { params }
    );
    return res.data as { success: boolean; data: CommunityMessage[]; count: number; has_more: boolean };
  },

  sendMessage: async (communityId: string, content: string) => {
    const res = await analysisClient.post(
      `/communities/${encodeURIComponent(communityId)}/chat/messages/`,
      { content }
    );
    return res.data as { success: boolean; message: CommunityMessage };
  },

  markRead: async (communityId: string) => {
    await analysisClient.post(`/communities/${encodeURIComponent(communityId)}/chat/read/`);
  },

  getWsUrl: (communityId: string, token: string): string => {
    const host = IS_DEV ? '10.0.2.2' : 'api.facesyma.com';
    const protocol = IS_DEV ? 'ws' : 'wss';
    return `${protocol}://${host}/ws/community/${communityId}/chat/?token=${token}`;
  },
};

// ── Gamification API (Django backend /api/v1/gamification/) ──────────────────
const gamAxios = createClient(BASE.gamification);

export interface CoinTransaction {
  transaction_id: string;
  amount: number;
  reason: string;
  created_at: string;
}

export interface LeaderboardEntry {
  rank: number;
  user_id: number;
  username: string;
  avatar?: string;
  coins: number;
  total_earned?: number;
}

export interface Badge {
  badge_id: string;
  name: string;
  description: string;
  category: string;
  icon_emoji: string;
  tiers: Array<{ tier: string; threshold: number; label: string }>;
  coin_reward_per_tier: number;
}

export interface UserBadge {
  badge_id: string;
  current_tier: string;
  current_progress: number;
  unlocked_at: string;
  tier_unlocks: Record<string, string>;
  total_coins_earned: number;
}

export interface Challenge {
  challenge_id: string;
  title: string;
  description?: string;
  status: string;
  max_participants: number;
  start_time: string;
  end_time: string;
  coin_reward: number;
  participants?: Array<{ user_id: number; username: string; score: number }>;
}

export interface CommunityMission {
  mission_id: string;
  title: string;
  description?: string;
  status: string;
  target_value: number;
  total_contributed: number;
  end_time: string;
  participants?: Array<{ user_id: number; username: string; contributed: number }>;
}

export interface MealItem {
  id: string;
  name: string;
  description?: string;
  calories?: number;
  coin_cost?: number;
}

export interface DiscoveryQuestion {
  question_id: string;
  text_en: string;
  text_tr: string;
  choices_en: string[];
  choices_tr: string[];
  correct_index: number;
  time_limit_seconds: number;
}

export const GamificationAPI = {
  // ── Coin ──────────────────────────────────────────────────────────────────
  getCoinBalance: async () => {
    const res = await gamAxios.get('/coins/balance/');
    return res.data as { balance: number; total_earned: number; daily_quest_coins: number };
  },

  getCoinHistory: async (limit = 20, offset = 0) => {
    const res = await gamAxios.get('/coins/history/', { params: { limit, offset } });
    return res.data as { transactions: CoinTransaction[]; total: number };
  },

  claimDailyQuest: async () => {
    const res = await gamAxios.post('/coins/daily-quest/');
    return res.data as { coins_earned: number; message: string; balance: number };
  },

  // ── Leaderboard ───────────────────────────────────────────────────────────
  getLeaderboard: async (type = 'global', limit = 50, offset = 0) => {
    const res = await gamAxios.get('/leaderboard/', { params: { type, limit, offset } });
    return res.data as { entries: LeaderboardEntry[]; total: number; user_rank?: number };
  },

  getTrendingUsers: async (days = 7, limit = 20) => {
    const res = await gamAxios.get('/leaderboard/trending/', { params: { days, limit } });
    return res.data as { trending: Array<{ user_id: number; username: string; rank_improvement: number; coins_gained: number; current_rank: number }> };
  },

  getUserTrend: async (days = 30) => {
    const res = await gamAxios.get('/leaderboard/trend/', { params: { days } });
    return res.data as { rank_change: number; coins_gained: number; current_rank: number; current_coins: number };
  },

  // ── Badges ────────────────────────────────────────────────────────────────
  getAllBadges: async () => {
    const res = await gamAxios.get('/badges/');
    return res.data as { badges: Badge[] };
  },

  getUserBadges: async () => {
    const res = await gamAxios.get('/badges/user/');
    return res.data as { badges: Record<string, UserBadge> };
  },

  getBadgeLeaderboard: async (badgeId: string, limit = 50) => {
    const res = await gamAxios.get(`/badges/${encodeURIComponent(badgeId)}/leaderboard/`, { params: { limit } });
    return res.data as { entries: Array<{ rank: number; user_id: number; username: string; current_tier: string; current_progress: number }> };
  },

  // ── Challenges ────────────────────────────────────────────────────────────
  getActiveChallenges: async (limit = 20) => {
    const res = await gamAxios.get('/challenges/', { params: { limit } });
    return res.data as { challenges: Challenge[]; total: number };
  },

  createChallenge: async (data: { title: string; description?: string; max_participants?: number; duration_hours?: number; coin_reward?: number }) => {
    const res = await gamAxios.post('/challenges/create/', data);
    return res.data as { challenge_id: string; challenge: Challenge };
  },

  joinChallenge: async (challengeId: string) => {
    const res = await gamAxios.post(`/challenges/${encodeURIComponent(challengeId)}/join/`);
    return res.data as { success: boolean; challenge: Challenge };
  },

  updateScore: async (challengeId: string, score: number) => {
    const res = await gamAxios.post(`/challenges/${encodeURIComponent(challengeId)}/score/`, { score });
    return res.data as { success: boolean; new_score: number };
  },

  getChallengeLeaderboard: async (challengeId: string) => {
    const res = await gamAxios.get(`/challenges/${encodeURIComponent(challengeId)}/leaderboard/`);
    return res.data as { entries: Array<{ rank: number; user_id: number; username: string; score: number }> };
  },

  abandonChallenge: async (challengeId: string) => {
    const res = await gamAxios.post(`/challenges/${encodeURIComponent(challengeId)}/abandon/`);
    return res.data as { success: boolean; penalty: number };
  },

  // ── Community Missions ────────────────────────────────────────────────────
  getActiveMissions: async (limit = 10) => {
    const res = await gamAxios.get('/missions/', { params: { limit } });
    return res.data as { missions: CommunityMission[] };
  },

  joinMission: async (missionId: string) => {
    const res = await gamAxios.post(`/missions/${encodeURIComponent(missionId)}/join/`);
    return res.data as { success: boolean; mission: CommunityMission };
  },

  contributeMission: async (missionId: string, amount: number) => {
    const res = await gamAxios.post(`/missions/${encodeURIComponent(missionId)}/contribute/`, { contribution: amount });
    return res.data as { new_progress: number; progress_percent: number; is_complete: boolean; coins_earned?: number };
  },

  getMissionLeaderboard: async (missionId: string) => {
    const res = await gamAxios.get(`/missions/${encodeURIComponent(missionId)}/leaderboard/`);
    return res.data as { entries: Array<{ rank: number; user_id: number; username: string; contributed: number }> };
  },

  // ── Meal Game ─────────────────────────────────────────────────────────────
  getWeeklyMeals: async (countryCode?: string) => {
    const res = await gamAxios.get('/meal-game/weekly/', { params: countryCode ? { country: countryCode } : {} });
    return res.data as { country: string; country_code: string; meals: MealItem[]; week_key: string };
  },

  selectMeal: async (mealId: string, countryCode: string) => {
    const res = await gamAxios.post('/meal-game/select/', { meal_id: mealId, country: countryCode });
    return res.data as { success: boolean; new_balance: number; transaction_id: string };
  },

  guessSifat: async (mealId: string, countryCode: string, guess: string) => {
    const res = await gamAxios.post('/meal-game/guess-sifat/', { meal_id: mealId, country: countryCode, guess });
    return res.data as { correct: boolean; coins_earned: number; correct_sifat?: string; new_balance: number };
  },

  getMealLeaderboard: async (countryCode?: string, limit = 20) => {
    const res = await gamAxios.get('/meal-game/leaderboard/', { params: { country: countryCode, limit } });
    return res.data as { entries: Array<{ rank: number; user_id: number; username: string; coins_earned: number; accuracy_percent: number }> };
  },

  // ── Discovery Games ───────────────────────────────────────────────────────
  getGameTypes: async () => {
    const res = await gamAxios.get('/discovery/types/');
    return res.data as { game_types: Array<{ game_type_id: string; name: string; description: string; coin_reward_play: number; coin_reward_win: number }> };
  },

  startGame: async (gameType: string, difficulty = 'normal', language = 'en') => {
    const res = await gamAxios.post('/discovery/start/', { game_type: gameType, difficulty, language });
    return res.data as { session_id: string; game_type_id: string; current_question: DiscoveryQuestion | null; total_questions: number };
  },

  submitAnswer: async (sessionId: string, questionId: string, answer: number) => {
    const res = await gamAxios.post('/discovery/answer/', { session_id: sessionId, question_id: questionId, answer });
    return res.data as {
      correct: boolean;
      next_question?: DiscoveryQuestion;
      completed?: boolean;
      accuracy_percent?: number;
      coins_earned?: number;
      insights?: string;
    };
  },

  abandonGame: async (sessionId: string) => {
    const res = await gamAxios.post('/discovery/abandon/', { session_id: sessionId });
    return res.data as { success: boolean };
  },
};

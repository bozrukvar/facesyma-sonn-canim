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
  analysis: 'https://api.facesyma.com/api/v1/analysis',
  auth:     'https://api.facesyma.com/api/v1/auth',
  chat:     'https://api.facesyma.com/api/v1/chat',
  twins:    'https://api.facesyma.com/api/v1/analysis',
  art:      'https://api.facesyma.com/api/v1/analysis',
};

// Geliştirme ortamı (local)
const DEV_SERVICES = {
  analysis: 'http://10.0.2.2/api/v1/analysis',  // Android emülatör → nginx port 80
  auth:     'http://10.0.2.2/api/v1/auth',
  chat:     'http://10.0.2.2/api/v1/chat',
  twins:    'http://10.0.2.2/api/v1/analysis',
  art:      'http://10.0.2.2/api/v1/analysis',
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
    return res.data;
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
    return res.data;
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
    return res.data;
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
  birthAnalysis: async (birthDate: string, birthTime?: string, lang = 'tr') =>
    (await coachAxios.post('/coach/birth', { birth_date: birthDate, birth_time: birthTime, lang })).data,
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

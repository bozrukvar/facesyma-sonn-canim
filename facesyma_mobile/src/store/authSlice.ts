// src/store/authSlice.ts
import { createSlice, createAsyncThunk, PayloadAction } from '@reduxjs/toolkit';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { AuthAPI } from '../services/api';

export interface User {
  id: number;
  email: string;
  name: string;
  avatar?: string;
  plan: 'free' | 'premium';
  created_at: string;
}

interface AuthState {
  user: User | null;
  isLoading: boolean;
  isAuthenticated: boolean;
  error: string | null;
}

const initialState: AuthState = {
  user: null,
  isLoading: false,
  isAuthenticated: false,
  error: null,
};

// ── Thunks ────────────────────────────────────────────────────────────────────

export const loginWithEmail = createAsyncThunk(
  'auth/loginEmail',
  async ({ email, password }: { email: string; password: string }, { rejectWithValue }) => {
    try {
      const data = await AuthAPI.loginEmail(email, password);
      await AuthAPI.saveTokens(data.access, data.refresh);
      await AsyncStorage.setItem('user', JSON.stringify(data.user));
      return data.user as User;
    } catch (e: any) {
      return rejectWithValue(e.response?.data?.detail || 'Giriş başarısız');
    }
  }
);

export const loginWithGoogle = createAsyncThunk(
  'auth/loginGoogle',
  async (idToken: string, { rejectWithValue }) => {
    try {
      const data = await AuthAPI.loginGoogle(idToken);
      await AuthAPI.saveTokens(data.access, data.refresh);
      await AsyncStorage.setItem('user', JSON.stringify(data.user));
      return data.user as User;
    } catch (e: any) {
      return rejectWithValue(e.response?.data?.detail || 'Google girişi başarısız');
    }
  }
);

export const registerWithEmail = createAsyncThunk(
  'auth/register',
  async (data: { email: string; password: string; name: string }, { rejectWithValue }) => {
    try {
      const res = await AuthAPI.registerEmail(data);
      await AuthAPI.saveTokens(res.access, res.refresh);
      await AsyncStorage.setItem('user', JSON.stringify(res.user));
      return res.user as User;
    } catch (e: any) {
      return rejectWithValue(e.response?.data?.email?.[0] || 'Kayıt başarısız');
    }
  }
);

export const restoreSession = createAsyncThunk(
  'auth/restore',
  async (_, { rejectWithValue }) => {
    try {
      const userStr = await AsyncStorage.getItem('user');
      const token   = await AsyncStorage.getItem('access_token');
      if (userStr && token) {
        return JSON.parse(userStr) as User;
      }
      return null;
    } catch {
      return rejectWithValue('Oturum yüklenemedi');
    }
  }
);

export const logout = createAsyncThunk('auth/logout', async () => {
  await AuthAPI.logout();
});

// ── Slice ─────────────────────────────────────────────────────────────────────

const authSlice = createSlice({
  name: 'auth',
  initialState,
  reducers: {
    clearError: (state) => { state.error = null; },
    setUser:    (state, action: PayloadAction<User>) => {
      state.user = action.payload;
      state.isAuthenticated = true;
    },
  },
  extraReducers: (builder) => {
    const pending   = (state: AuthState) => { state.isLoading = true; state.error = null; };
    const fulfilled = (state: AuthState, action: PayloadAction<User | null>) => {
      state.isLoading = false;
      state.user = action.payload;
      state.isAuthenticated = !!action.payload;
    };
    const rejected  = (state: AuthState, action: any) => {
      state.isLoading = false;
      state.error = action.payload as string;
    };

    builder
      .addCase(loginWithEmail.pending,   pending)
      .addCase(loginWithEmail.fulfilled, fulfilled)
      .addCase(loginWithEmail.rejected,  rejected)
      .addCase(loginWithGoogle.pending,   pending)
      .addCase(loginWithGoogle.fulfilled, fulfilled)
      .addCase(loginWithGoogle.rejected,  rejected)
      .addCase(registerWithEmail.pending,   pending)
      .addCase(registerWithEmail.fulfilled, fulfilled)
      .addCase(registerWithEmail.rejected,  rejected)
      .addCase(restoreSession.fulfilled, fulfilled)
      .addCase(logout.fulfilled, (state) => {
        state.user = null;
        state.isAuthenticated = false;
      });
  },
});

export const { clearError, setUser } = authSlice.actions;
export default authSlice.reducer;

// src/store/authSlice.ts
import { createSlice, createAsyncThunk, PayloadAction } from '@reduxjs/toolkit';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { AuthAPI, setCachedToken } from '../services/api';

export interface User {
  id: number;
  email: string;
  name: string;
  avatar?: string;
  plan: 'free' | 'premium';
  created_at: string;
  birth_year?: number;
  gender?: string;
  country?: string;
  skin_tone?: string;
  hair_color?: string;
  eye_color?: string;
  goal?: string;
  onboarding_completed?: boolean;
  terms_accepted?: boolean;
  gdpr_consent?: boolean;
  last_login?: string;
  premium_expires_at?: string;
  premium_days_left?: number;
  premium_hours_left?: number;
  cosmetic_surgery_regions?: string[];
}

interface AuthState {
  user: User | null;
  isLoading: boolean;
  isAuthenticated: boolean;
  error: string | null;
  modulesUsed: string[];
}

const MODULES_KEY = '@facesyma_modules_used';

const initialState: AuthState = {
  user: null,
  isLoading: false,
  isAuthenticated: false,
  error: null,
  modulesUsed: [],
};

// ── Thunks ────────────────────────────────────────────────────────────────────

export const loginWithEmail = createAsyncThunk(
  'auth/loginEmail',
  async ({ email, password }: { email: string; password: string }, { rejectWithValue }) => {
    try {
      const data = await AuthAPI.loginEmail(email, password);
      await AuthAPI.saveTokens(data.access, data.refresh);
      const user = data.user as User;
      await AsyncStorage.setItem('user', JSON.stringify(user));
      return user;
    } catch (e: any) {
      return rejectWithValue(e.response?.data?.detail || 'Login failed');
    }
  }
);

export const loginWithGoogle = createAsyncThunk(
  'auth/loginGoogle',
  async (idToken: string, { rejectWithValue }) => {
    try {
      const data = await AuthAPI.loginGoogle(idToken);
      await AuthAPI.saveTokens(data.access, data.refresh);
      const user = data.user as User;
      await AsyncStorage.setItem('user', JSON.stringify(user));
      return user;
    } catch (e: any) {
      return rejectWithValue(e.response?.data?.detail || 'Google login failed');
    }
  }
);

export const registerWithEmail = createAsyncThunk(
  'auth/register',
  async (data: { email: string; password: string; name: string; terms_accepted: boolean; gdpr_consent: boolean }, { rejectWithValue }) => {
    try {
      const res = await AuthAPI.registerEmail(data);
      await AuthAPI.saveTokens(res.access, res.refresh);
      await AsyncStorage.setItem('user', JSON.stringify(res.user));
      return res.user as User;
    } catch (e: any) {
      return rejectWithValue(e.response?.data?.detail || e.response?.data?.email?.[0] || 'Registration failed');
    }
  }
);

export const restoreSession = createAsyncThunk(
  'auth/restore',
  async (_, { rejectWithValue }) => {
    try {
      const [userStr, token, modulesStr] = await AsyncStorage.multiGet(
        ['user', 'access_token', MODULES_KEY]
      );
      const modules: string[] = modulesStr[1] ? JSON.parse(modulesStr[1]) : [];
      if (userStr[1] && token[1]) {
        setCachedToken(token[1]);
        return { user: JSON.parse(userStr[1]) as User, modules };
      }
      return { user: null, modules };
    } catch {
      return rejectWithValue('Session could not be restored');
    }
  }
);

export const logout = createAsyncThunk('auth/logout', async () => {
  await AuthAPI.logout();
});

export const updateProfile = createAsyncThunk(
  'auth/updateProfile',
  async (data: Record<string, unknown>, { rejectWithValue }) => {
    try {
      const res = await AuthAPI.updateProfile(data);
      await AsyncStorage.setItem('user', JSON.stringify(res));
      return res as User;
    } catch (e: any) {
      return rejectWithValue(e.response?.data?.detail || 'Profile update failed');
    }
  }
);

// ── Slice ─────────────────────────────────────────────────────────────────────

export const CHAT_MIN_MODULES = 3;

const authSlice = createSlice({
  name: 'auth',
  initialState,
  reducers: {
    clearError: (state) => { state.error = null; },
    setUser:    (state, action: PayloadAction<User>) => {
      state.user = action.payload;
      state.isAuthenticated = true;
    },
    markModuleUsed: (state, action: PayloadAction<string>) => {
      if (!state.modulesUsed.includes(action.payload)) {
        state.modulesUsed = [...state.modulesUsed, action.payload];
        // Fire-and-forget persist
        AsyncStorage.setItem(MODULES_KEY, JSON.stringify(state.modulesUsed)).catch(() => {});
      }
    },
  },
  extraReducers: (builder) => {
    const pending   = (state: AuthState) => { state.isLoading = true; state.error = null; };
    const fulfilled = (state: AuthState, action: PayloadAction<User | null>) => {
      const p = action.payload;
      state.isLoading = false;
      state.user = p;
      state.isAuthenticated = !!p;
    };
    const rejected  = (state: AuthState, action: { payload: unknown }) => {
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
      .addCase(restoreSession.fulfilled, (state, action) => {
        const p = action.payload as { user: User | null; modules: string[] };
        state.isLoading = false;
        state.user = p.user;
        state.isAuthenticated = !!p.user;
        state.modulesUsed = p.modules;
      })
      .addCase(updateProfile.pending,   pending)
      .addCase(updateProfile.fulfilled, fulfilled)
      .addCase(updateProfile.rejected,  (state, action) => {
        state.isLoading = false;
        state.error = action.payload as string;
      })
      .addCase(logout.fulfilled, (state) => {
        state.user = null;
        state.isAuthenticated = false;
        state.modulesUsed = [];
        AsyncStorage.removeItem(MODULES_KEY).catch(() => {});
      });
  },
});

export const { clearError, setUser, markModuleUsed } = authSlice.actions;
export default authSlice.reducer;

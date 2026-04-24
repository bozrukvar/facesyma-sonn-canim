// src/store/analysisSlice.ts
// Son analiz sonucunu Redux'ta tutar — navigasyon sırasında kaybolmaz.
import { createSlice, PayloadAction } from '@reduxjs/toolkit';
import type { AnalysisResult } from '../types/api';

interface AnalysisState {
  lastResult: AnalysisResult | null;
  lastImageUri: string | null;
}

const initialState: AnalysisState = {
  lastResult:   null,
  lastImageUri: null,
};

const analysisSlice = createSlice({
  name: 'analysis',
  initialState,
  reducers: {
    setAnalysisResult: (state, action: PayloadAction<{ result: AnalysisResult; imageUri: string }>) => {
      const p = action.payload;
      state.lastResult   = p.result;
      state.lastImageUri = p.imageUri;
    },
    clearAnalysisResult: (state) => {
      state.lastResult   = null;
      state.lastImageUri = null;
    },
  },
});

export const { setAnalysisResult, clearAnalysisResult } = analysisSlice.actions;
export default analysisSlice.reducer;

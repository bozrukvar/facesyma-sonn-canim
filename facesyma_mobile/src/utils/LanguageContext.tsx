import React, { createContext, useState, useEffect, ReactNode } from 'react';
import { NativeModules, Platform } from 'react-native';
import AsyncStorage from '@react-native-async-storage/async-storage';

export const AVAILABLE_LANGS = [
  { code: 'tr', flag: '🇹🇷', name: 'Türkçe' },
  { code: 'en', flag: '🇬🇧', name: 'English' },
  { code: 'de', flag: '🇩🇪', name: 'Deutsch' },
  { code: 'ru', flag: '🇷🇺', name: 'Русский' },
  { code: 'ar', flag: '🇸🇦', name: 'العربية' },
  { code: 'es', flag: '🇪🇸', name: 'Español' },
  { code: 'ko', flag: '🇰🇷', name: '한국어' },
  { code: 'ja', flag: '🇯🇵', name: '日本語' },
  { code: 'zh', flag: '🇨🇳', name: '中文' },
  { code: 'hi', flag: '🇮🇳', name: 'हिन्दी' },
  { code: 'fr', flag: '🇫🇷', name: 'Français' },
  { code: 'pt', flag: '🇵🇹', name: 'Português' },
  { code: 'bn', flag: '🇧🇩', name: 'বাংলা' },
  { code: 'id', flag: '🇮🇩', name: 'Bahasa Indonesia' },
  { code: 'ur', flag: '🇵🇰', name: 'اردو' },
  { code: 'it', flag: '🇮🇹', name: 'Italiano' },
  { code: 'vi', flag: '🇻🇳', name: 'Tiếng Việt' },
  { code: 'pl', flag: '🇵🇱', name: 'Polski' },
];

const LANG_STORAGE_KEY = '@facesyma_lang';
const SUPPORTED = new Set(AVAILABLE_LANGS.map(l => l.code));

const getDeviceLang = (): string => {
  try {
    let raw = '';
    if (Platform.OS === 'ios') {
      raw = NativeModules.SettingsManager?.settings?.AppleLocale
        || (NativeModules.SettingsManager?.settings?.AppleLanguages ?? [])[0]
        || '';
    } else {
      raw = NativeModules.I18nManager?.localeIdentifier || '';
    }
    const code = raw.split(/[-_]/)[0].toLowerCase();
    return SUPPORTED.has(code) ? code : 'en';
  } catch {
    return 'en';
  }
};

interface LanguageContextType {
  lang: string;
  setLang: (lang: string) => void;
  availableLangs: typeof AVAILABLE_LANGS;
}

export const LanguageContext = createContext<LanguageContextType>({
  lang: 'en',
  setLang: () => {},
  availableLangs: AVAILABLE_LANGS,
});

export const LanguageProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  // Synchronous initial value from device locale (no flash)
  const [lang, setLangState] = useState<string>(getDeviceLang);

  useEffect(() => {
    // Override with saved preference if it exists
    AsyncStorage.getItem(LANG_STORAGE_KEY).then(saved => {
      if (saved && SUPPORTED.has(saved)) setLangState(saved);
    }).catch(() => {});
  }, []);

  const setLang = (code: string) => {
    setLangState(code);
    AsyncStorage.setItem(LANG_STORAGE_KEY, code).catch(() => {});
  };

  return (
    <LanguageContext.Provider value={{ lang, setLang, availableLangs: AVAILABLE_LANGS }}>
      {children}
    </LanguageContext.Provider>
  );
};

export const useLanguage = () => {
  const context = React.useContext(LanguageContext);
  if (!context) throw new Error('useLanguage must be used within LanguageProvider');
  return context;
};

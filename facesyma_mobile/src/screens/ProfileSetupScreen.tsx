// src/screens/ProfileSetupScreen.tsx
import React, { useState, useMemo } from 'react';
import {
  View, Text, StyleSheet, ScrollView, TouchableOpacity,
  Dimensions, ActivityIndicator, Alert, TextInput,
} from 'react-native';
import { useDispatch, useSelector } from 'react-redux';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { AppDispatch, RootState } from '../store';
import { updateProfile } from '../store/authSlice';
import theme from '../utils/theme';
const { colors, spacing, typography, radius, shadow } = theme;
import { useLanguage } from '../utils/LanguageContext';
import { t } from '../utils/i18n';
import type { ScreenProps } from '../navigation/types';

const { width } = Dimensions.get('window');

const CURRENT_YEAR = new Date().getFullYear();
const BIRTH_YEARS  = Array.from({ length: CURRENT_YEAR - 1924 }, (_, i) => CURRENT_YEAR - 13 - i); // 13+ yaş

const GENDERS = [
  { key: 'female',            icon: '♀',  label: 'Kadın' },
  { key: 'male',              icon: '♂',  label: 'Erkek' },
  { key: 'prefer_not_to_say', icon: '—', label: 'Belirtmek istemiyorum' },
];

const SKIN_TONES = [
  { key: '1', color: '#FDDBB4', label: 'I' },
  { key: '2', color: '#EBB98A', label: 'II' },
  { key: '3', color: '#C68642', label: 'III' },
  { key: '4', color: '#8D5524', label: 'IV' },
  { key: '5', color: '#5C3317', label: 'V' },
  { key: '6', color: '#3B1E08', label: 'VI' },
];

const HAIR_COLORS = [
  { key: 'black',      color: '#111111', label: 'Siyah' },
  { key: 'brown',      color: '#6B3A2A', label: 'Kahve' },
  { key: 'blonde',     color: '#F5D76E', label: 'Sarı' },
  { key: 'red',        color: '#C0392B', label: 'Kızıl' },
  { key: 'white_gray', color: '#CCCCCC', label: 'Gri/Beyaz' },
  { key: 'other',      color: '#9B59B6', label: 'Diğer' },
];

const EYE_COLORS = [
  { key: 'brown',      color: '#6B3A2A', label: 'Kahve' },
  { key: 'black',      color: '#111111', label: 'Siyah' },
  { key: 'blue',       color: '#2E86C1', label: 'Mavi' },
  { key: 'green',      color: '#1E8449', label: 'Yeşil' },
  { key: 'hazel',      color: '#7D6608', label: 'Ela' },
  { key: 'gray',       color: '#808B96', label: 'Gri' },
];

const GOALS = [
  { key: 'self_discovery', icon: '🔮', label: 'Kendimi keşfet' },
  { key: 'style',          icon: '👗', label: 'Stil & Moda' },
  { key: 'career',         icon: '💼', label: 'Kariyer' },
  { key: 'fun',            icon: '🎉', label: 'Eğlence' },
];

const COUNTRIES: { code: string; flag: string; name: string }[] = [
  // Türkçe
  { code: 'TR', flag: '🇹🇷', name: 'Türkiye' },
  { code: 'AZ', flag: '🇦🇿', name: 'Azerbaycan' },
  { code: 'CY', flag: '🇨🇾', name: 'Kıbrıs' },
  // İngilizce
  { code: 'US', flag: '🇺🇸', name: 'United States' },
  { code: 'GB', flag: '🇬🇧', name: 'United Kingdom' },
  { code: 'CA', flag: '🇨🇦', name: 'Canada' },
  { code: 'AU', flag: '🇦🇺', name: 'Australia' },
  { code: 'NZ', flag: '🇳🇿', name: 'New Zealand' },
  { code: 'IE', flag: '🇮🇪', name: 'Ireland' },
  { code: 'ZA', flag: '🇿🇦', name: 'South Africa' },
  { code: 'NG', flag: '🇳🇬', name: 'Nigeria' },
  { code: 'KE', flag: '🇰🇪', name: 'Kenya' },
  { code: 'GH', flag: '🇬🇭', name: 'Ghana' },
  { code: 'PH', flag: '🇵🇭', name: 'Philippines' },
  { code: 'SG', flag: '🇸🇬', name: 'Singapore' },
  // Almanca
  { code: 'DE', flag: '🇩🇪', name: 'Germany' },
  { code: 'AT', flag: '🇦🇹', name: 'Austria' },
  { code: 'CH', flag: '🇨🇭', name: 'Switzerland' },
  { code: 'LU', flag: '🇱🇺', name: 'Luxembourg' },
  { code: 'LI', flag: '🇱🇮', name: 'Liechtenstein' },
  // Rusça
  { code: 'RU', flag: '🇷🇺', name: 'Russia' },
  { code: 'UA', flag: '🇺🇦', name: 'Ukraine' },
  { code: 'BY', flag: '🇧🇾', name: 'Belarus' },
  { code: 'KZ', flag: '🇰🇿', name: 'Kazakhstan' },
  { code: 'KG', flag: '🇰🇬', name: 'Kyrgyzstan' },
  { code: 'TJ', flag: '🇹🇯', name: 'Tajikistan' },
  // Arapça
  { code: 'SA', flag: '🇸🇦', name: 'Saudi Arabia' },
  { code: 'EG', flag: '🇪🇬', name: 'Egypt' },
  { code: 'AE', flag: '🇦🇪', name: 'UAE' },
  { code: 'JO', flag: '🇯🇴', name: 'Jordan' },
  { code: 'LB', flag: '🇱🇧', name: 'Lebanon' },
  { code: 'IQ', flag: '🇮🇶', name: 'Iraq' },
  { code: 'SY', flag: '🇸🇾', name: 'Syria' },
  { code: 'KW', flag: '🇰🇼', name: 'Kuwait' },
  { code: 'QA', flag: '🇶🇦', name: 'Qatar' },
  { code: 'BH', flag: '🇧🇭', name: 'Bahrain' },
  { code: 'OM', flag: '🇴🇲', name: 'Oman' },
  { code: 'YE', flag: '🇾🇪', name: 'Yemen' },
  { code: 'PS', flag: '🇵🇸', name: 'Palestine' },
  { code: 'LY', flag: '🇱🇾', name: 'Libya' },
  { code: 'TN', flag: '🇹🇳', name: 'Tunisia' },
  { code: 'DZ', flag: '🇩🇿', name: 'Algeria' },
  { code: 'MA', flag: '🇲🇦', name: 'Morocco' },
  { code: 'SD', flag: '🇸🇩', name: 'Sudan' },
  { code: 'MR', flag: '🇲🇷', name: 'Mauritania' },
  { code: 'SO', flag: '🇸🇴', name: 'Somalia' },
  { code: 'DJ', flag: '🇩🇯', name: 'Djibouti' },
  { code: 'KM', flag: '🇰🇲', name: 'Comoros' },
  // İspanyolca
  { code: 'ES', flag: '🇪🇸', name: 'Spain' },
  { code: 'MX', flag: '🇲🇽', name: 'Mexico' },
  { code: 'CO', flag: '🇨🇴', name: 'Colombia' },
  { code: 'AR', flag: '🇦🇷', name: 'Argentina' },
  { code: 'PE', flag: '🇵🇪', name: 'Peru' },
  { code: 'VE', flag: '🇻🇪', name: 'Venezuela' },
  { code: 'CL', flag: '🇨🇱', name: 'Chile' },
  { code: 'EC', flag: '🇪🇨', name: 'Ecuador' },
  { code: 'BO', flag: '🇧🇴', name: 'Bolivia' },
  { code: 'PY', flag: '🇵🇾', name: 'Paraguay' },
  { code: 'UY', flag: '🇺🇾', name: 'Uruguay' },
  { code: 'CU', flag: '🇨🇺', name: 'Cuba' },
  { code: 'DO', flag: '🇩🇴', name: 'Dominican Rep.' },
  { code: 'GT', flag: '🇬🇹', name: 'Guatemala' },
  { code: 'HN', flag: '🇭🇳', name: 'Honduras' },
  { code: 'SV', flag: '🇸🇻', name: 'El Salvador' },
  { code: 'NI', flag: '🇳🇮', name: 'Nicaragua' },
  { code: 'CR', flag: '🇨🇷', name: 'Costa Rica' },
  { code: 'PA', flag: '🇵🇦', name: 'Panama' },
  // Korece
  { code: 'KR', flag: '🇰🇷', name: 'South Korea' },
  // Japonca
  { code: 'JP', flag: '🇯🇵', name: 'Japan' },
  // Çince
  { code: 'CN', flag: '🇨🇳', name: 'China' },
  { code: 'TW', flag: '🇹🇼', name: 'Taiwan' },
  { code: 'HK', flag: '🇭🇰', name: 'Hong Kong' },
  // Hintçe / Urduca / Bengalce
  { code: 'IN', flag: '🇮🇳', name: 'India' },
  { code: 'PK', flag: '🇵🇰', name: 'Pakistan' },
  { code: 'BD', flag: '🇧🇩', name: 'Bangladesh' },
  // Fransızca
  { code: 'FR', flag: '🇫🇷', name: 'France' },
  { code: 'BE', flag: '🇧🇪', name: 'Belgium' },
  { code: 'MC', flag: '🇲🇨', name: 'Monaco' },
  { code: 'SN', flag: '🇸🇳', name: 'Senegal' },
  { code: 'CI', flag: '🇨🇮', name: "Côte d'Ivoire" },
  { code: 'CM', flag: '🇨🇲', name: 'Cameroon' },
  { code: 'MG', flag: '🇲🇬', name: 'Madagascar' },
  { code: 'CD', flag: '🇨🇩', name: 'DR Congo' },
  { code: 'CG', flag: '🇨🇬', name: 'Congo' },
  { code: 'ML', flag: '🇲🇱', name: 'Mali' },
  { code: 'BF', flag: '🇧🇫', name: 'Burkina Faso' },
  { code: 'NE', flag: '🇳🇪', name: 'Niger' },
  { code: 'TD', flag: '🇹🇩', name: 'Chad' },
  { code: 'GN', flag: '🇬🇳', name: 'Guinea' },
  { code: 'BJ', flag: '🇧🇯', name: 'Benin' },
  { code: 'TG', flag: '🇹🇬', name: 'Togo' },
  { code: 'RW', flag: '🇷🇼', name: 'Rwanda' },
  { code: 'BI', flag: '🇧🇮', name: 'Burundi' },
  { code: 'HT', flag: '🇭🇹', name: 'Haiti' },
  { code: 'GA', flag: '🇬🇦', name: 'Gabon' },
  { code: 'CF', flag: '🇨🇫', name: 'Cent. African Rep.' },
  // Portekizce
  { code: 'PT', flag: '🇵🇹', name: 'Portugal' },
  { code: 'BR', flag: '🇧🇷', name: 'Brazil' },
  { code: 'AO', flag: '🇦🇴', name: 'Angola' },
  { code: 'MZ', flag: '🇲🇿', name: 'Mozambique' },
  { code: 'CV', flag: '🇨🇻', name: 'Cape Verde' },
  { code: 'GW', flag: '🇬🇼', name: 'Guinea-Bissau' },
  { code: 'TL', flag: '🇹🇱', name: 'Timor-Leste' },
  // Endonezce
  { code: 'ID', flag: '🇮🇩', name: 'Indonesia' },
  // Vietnamca
  { code: 'VN', flag: '🇻🇳', name: 'Vietnam' },
  // İtalyanca
  { code: 'IT', flag: '🇮🇹', name: 'Italy' },
  { code: 'SM', flag: '🇸🇲', name: 'San Marino' },
  // Lehçe
  { code: 'PL', flag: '🇵🇱', name: 'Poland' },
  // Diğer
  { code: 'OTHER', flag: '🌍', name: 'Other' },
];

type Step = 'birth_year' | 'gender' | 'country' | 'skin_tone' | 'hair_color' | 'eye_color' | 'goal';
const STEPS: Step[] = ['birth_year', 'gender', 'country', 'skin_tone', 'hair_color', 'eye_color', 'goal'];
const REQUIRED_STEPS = 3; // birth_year, gender, country zorunlu

const ProfileSetupScreen = ({ navigation }: ScreenProps<'ProfileSetup'>) => {
  const insets   = useSafeAreaInsets();
  const dispatch = useDispatch<AppDispatch>();
  const { lang } = useLanguage();
  const isLoading = useSelector((s: RootState) => s.auth.isLoading);

  const [stepIdx,    setStepIdx]    = useState(0);
  const [birthYear,  setBirthYear]  = useState<number | null>(null);
  const [gender,     setGender]     = useState<string | null>(null);
  const [country,    setCountry]    = useState<string | null>(null);
  const [skinTone,   setSkinTone]   = useState<string | null>(null);
  const [hairColor,  setHairColor]  = useState<string | null>(null);
  const [eyeColor,   setEyeColor]   = useState<string | null>(null);
  const [goal,       setGoal]       = useState<string | null>(null);

  const step = STEPS[stepIdx];
  const isLast = stepIdx === STEPS.length - 1;
  const isOptionalStep = stepIdx >= REQUIRED_STEPS;

  const canProceed = () => {
    if (step === 'birth_year') return birthYear !== null;
    if (step === 'gender')     return gender !== null;
    if (step === 'country')    return country !== null;
    return true; // optional steps always passable
  };

  const handleNext = async () => {
    if (!canProceed()) return;
    if (isLast) {
      await handleFinish();
    } else {
      setStepIdx(i => i + 1);
    }
  };

  const handleSkip = () => {
    if (isLast) { handleFinish(); return; }
    setStepIdx(i => i + 1);
  };

  const handleFinish = async () => {
    const payload: Record<string, unknown> = { onboarding_completed: true };
    if (birthYear)  payload.birth_year  = birthYear;
    if (gender)     payload.gender      = gender;
    if (country)    payload.country     = country;
    if (skinTone)   payload.skin_tone   = skinTone;
    if (hairColor)  payload.hair_color  = hairColor;
    if (eyeColor)   payload.eye_color   = eyeColor;
    if (goal)       payload.goal        = goal;

    const r = await dispatch(updateProfile(payload));
    if (updateProfile.fulfilled.match(r)) {
      navigation.replace('Main');
    } else {
      Alert.alert('Hata', 'Bilgiler kaydedilemedi. Daha sonra profilden tamamlayabilirsiniz.');
      navigation.replace('Main');
    }
  };

  return (
    <View style={[styles.container, { paddingTop: insets.top }]}>
      {/* Başlık */}
      <View style={styles.header}>
        <Text style={styles.title}>Seni tanıyalım ✨</Text>
        <Text style={styles.subtitle}>
          {stepIdx + 1} / {STEPS.length}
          {isOptionalStep ? '  (isteğe bağlı)' : ''}
        </Text>
        {/* İlerleme çubuğu */}
        <View style={styles.progressBar}>
          <View style={[styles.progressFill, { width: `${((stepIdx + 1) / STEPS.length) * 100}%` }]} />
        </View>
      </View>

      <ScrollView
        style={styles.scroll}
        contentContainerStyle={styles.scrollContent}
        showsVerticalScrollIndicator={false}
      >
        {step === 'birth_year' && (
          <StepBirthYear value={birthYear} onChange={setBirthYear} />
        )}
        {step === 'gender' && (
          <StepGender value={gender} onChange={setGender} />
        )}
        {step === 'country' && (
          <StepCountry value={country} onChange={setCountry} />
        )}
        {step === 'skin_tone' && (
          <StepSkinTone value={skinTone} onChange={setSkinTone} />
        )}
        {step === 'hair_color' && (
          <StepHairColor value={hairColor} onChange={setHairColor} />
        )}
        {step === 'eye_color' && (
          <StepEyeColor value={eyeColor} onChange={setEyeColor} />
        )}
        {step === 'goal' && (
          <StepGoal value={goal} onChange={setGoal} />
        )}
      </ScrollView>

      {/* Alt butonlar */}
      <View style={[styles.footer, { paddingBottom: insets.bottom + spacing.md }]}>
        {isOptionalStep && (
          <TouchableOpacity style={styles.skipBtn} onPress={handleSkip}>
            <Text style={styles.skipText}>Atla</Text>
          </TouchableOpacity>
        )}
        <TouchableOpacity
          style={[styles.nextBtn, !canProceed() && styles.nextBtnDisabled]}
          onPress={handleNext}
          disabled={!canProceed() || isLoading}
          activeOpacity={0.85}
        >
          {isLoading ? (
            <ActivityIndicator color="#000" />
          ) : (
            <Text style={styles.nextText}>{isLast ? 'Başla 🚀' : 'Devam Et'}</Text>
          )}
        </TouchableOpacity>
      </View>
    </View>
  );
};

// ── Step bileşenleri ──────────────────────────────────────────────────────────

const StepBirthYear = ({ value, onChange }: { value: number | null; onChange: (v: number) => void }) => (
  <View>
    <Text style={styles.stepTitle}>Doğum yılın nedir?</Text>
    <Text style={styles.stepHint}>Kişiselleştirilmiş analizler için kullanılır.</Text>
    <ScrollView style={styles.yearScroll} showsVerticalScrollIndicator={false}>
      {BIRTH_YEARS.map(y => (
        <TouchableOpacity
          key={y}
          style={[styles.yearItem, value === y && styles.yearItemSelected]}
          onPress={() => onChange(y)}
          activeOpacity={0.7}
        >
          <Text style={[styles.yearText, value === y && styles.yearTextSelected]}>{y}</Text>
        </TouchableOpacity>
      ))}
    </ScrollView>
  </View>
);

const StepGender = ({ value, onChange }: { value: string | null; onChange: (v: string) => void }) => (
  <View>
    <Text style={styles.stepTitle}>Cinsiyetin nedir?</Text>
    <View style={styles.genderGrid}>
      {GENDERS.map(g => (
        <TouchableOpacity
          key={g.key}
          style={[styles.genderCard, value === g.key && styles.cardSelected]}
          onPress={() => onChange(g.key)}
          activeOpacity={0.8}
        >
          <Text style={styles.genderIcon}>{g.icon}</Text>
          <Text style={[styles.cardLabel, value === g.key && styles.cardLabelSelected]}>{g.label}</Text>
        </TouchableOpacity>
      ))}
    </View>
  </View>
);

const StepCountry = ({ value, onChange }: { value: string | null; onChange: (v: string) => void }) => {
  const [query, setQuery] = useState('');
  const q = query.trim().toLowerCase();

  const filtered = useMemo(() =>
    q ? COUNTRIES.filter(c =>
      c.name.toLowerCase().includes(q) || c.code.toLowerCase().includes(q)
    ) : COUNTRIES,
  [q]);

  // If user typed something not matched by any country code, show custom option
  const hasExact = filtered.some(c => c.code === value);
  const customCode = `CUSTOM:${query.trim()}`;
  const showCustom = q.length >= 2 && filtered.length === 0;

  return (
    <View>
      <Text style={styles.stepTitle}>Hangi ülkedesin?</Text>
      <Text style={styles.stepHint}>Bölgeye özgü içerikler için kullanılır.</Text>
      <TextInput
        style={styles.countrySearch}
        placeholder="Ülke ara..."
        placeholderTextColor={colors.textMuted}
        value={query}
        onChangeText={setQuery}
        autoCorrect={false}
        autoCapitalize="words"
      />
      <View style={styles.countryGrid}>
        {filtered.map(c => (
          <TouchableOpacity
            key={c.code}
            style={[styles.countryChip, value === c.code && styles.chipSelected]}
            onPress={() => onChange(c.code)}
            activeOpacity={0.8}
          >
            <Text style={styles.countryFlag}>{c.flag}</Text>
            <Text style={[styles.chipText, value === c.code && styles.chipTextSelected]}>{c.name}</Text>
          </TouchableOpacity>
        ))}
        {showCustom && (
          <TouchableOpacity
            style={[styles.countryChip, value === customCode && styles.chipSelected]}
            onPress={() => onChange(customCode)}
            activeOpacity={0.8}
          >
            <Text style={styles.countryFlag}>🌍</Text>
            <Text style={[styles.chipText, value === customCode && styles.chipTextSelected]}>
              {query.trim()}
            </Text>
          </TouchableOpacity>
        )}
      </View>
    </View>
  );
};

const StepSkinTone = ({ value, onChange }: { value: string | null; onChange: (v: string) => void }) => (
  <View>
    <Text style={styles.stepTitle}>Cilt tonun hangisi?</Text>
    <Text style={styles.stepHint}>Renk analizi ve makyaj önerileri için kullanılır.</Text>
    <View style={styles.skinGrid}>
      {SKIN_TONES.map(s => (
        <TouchableOpacity
          key={s.key}
          style={[styles.skinCircle, { backgroundColor: s.color }, value === s.key && styles.skinCircleSelected]}
          onPress={() => onChange(s.key)}
          activeOpacity={0.8}
        >
          {value === s.key && <Text style={styles.skinCheck}>✓</Text>}
        </TouchableOpacity>
      ))}
    </View>
    <View style={styles.skinLabels}>
      {SKIN_TONES.map(s => (
        <Text key={s.key} style={[styles.skinLabel, value === s.key && { color: colors.gold }]}>{s.label}</Text>
      ))}
    </View>
  </View>
);

const StepHairColor = ({ value, onChange }: { value: string | null; onChange: (v: string) => void }) => (
  <View>
    <Text style={styles.stepTitle}>Saç rengin nedir?</Text>
    <View style={styles.skinGrid}>
      {HAIR_COLORS.map(h => (
        <TouchableOpacity
          key={h.key}
          style={[styles.skinCircle, { backgroundColor: h.color }, value === h.key && styles.skinCircleSelected]}
          onPress={() => onChange(h.key)}
          activeOpacity={0.8}
        >
          {value === h.key && <Text style={styles.skinCheck}>✓</Text>}
        </TouchableOpacity>
      ))}
    </View>
    <View style={styles.skinLabels}>
      {HAIR_COLORS.map(h => (
        <Text key={h.key} style={[styles.skinLabel, value === h.key && { color: colors.gold }]}>{h.label}</Text>
      ))}
    </View>
  </View>
);

const StepEyeColor = ({ value, onChange }: { value: string | null; onChange: (v: string) => void }) => (
  <View>
    <Text style={styles.stepTitle}>Göz rengin nedir?</Text>
    <Text style={styles.stepHint}>Renk analizi ve makyaj önerileri için kullanılır.</Text>
    <View style={styles.skinGrid}>
      {EYE_COLORS.map(e => (
        <TouchableOpacity
          key={e.key}
          style={[styles.skinCircle, { backgroundColor: e.color }, value === e.key && styles.skinCircleSelected]}
          onPress={() => onChange(e.key)}
          activeOpacity={0.8}
        >
          {value === e.key && <Text style={styles.skinCheck}>✓</Text>}
        </TouchableOpacity>
      ))}
    </View>
    <View style={styles.skinLabels}>
      {EYE_COLORS.map(e => (
        <Text key={e.key} style={[styles.skinLabel, value === e.key && { color: colors.gold }]}>{e.label}</Text>
      ))}
    </View>
  </View>
);

const StepGoal = ({ value, onChange }: { value: string | null; onChange: (v: string) => void }) => (
  <View>
    <Text style={styles.stepTitle}>Facesyma'yı ne için kullanacaksın?</Text>
    <View style={styles.goalGrid}>
      {GOALS.map(g => (
        <TouchableOpacity
          key={g.key}
          style={[styles.goalCard, value === g.key && styles.cardSelected]}
          onPress={() => onChange(g.key)}
          activeOpacity={0.8}
        >
          <Text style={styles.goalIcon}>{g.icon}</Text>
          <Text style={[styles.cardLabel, value === g.key && styles.cardLabelSelected]}>{g.label}</Text>
        </TouchableOpacity>
      ))}
    </View>
  </View>
);

// ── Stiller ───────────────────────────────────────────────────────────────────

const styles = StyleSheet.create({
  container:   { flex: 1, backgroundColor: colors.background },
  header:      { paddingHorizontal: spacing.lg, paddingTop: spacing.lg, paddingBottom: spacing.md },
  title:       { ...typography.display, fontSize: 22, color: colors.textPrimary, marginBottom: 4 },
  subtitle:    { ...typography.caption, color: colors.textMuted, marginBottom: spacing.md },
  progressBar: { height: 3, backgroundColor: colors.border, borderRadius: 2, overflow: 'hidden' },
  progressFill:{ height: 3, backgroundColor: colors.gold, borderRadius: 2 },
  scroll:      { flex: 1 },
  scrollContent: { paddingHorizontal: spacing.lg, paddingBottom: spacing.xl },
  footer: {
    paddingHorizontal: spacing.lg, paddingTop: spacing.md,
    borderTopWidth: 1, borderColor: colors.border,
    gap: spacing.sm,
  },
  nextBtn: {
    height: 54, backgroundColor: colors.gold,
    borderRadius: radius.lg, alignItems: 'center', justifyContent: 'center',
    ...shadow.gold,
  },
  nextBtnDisabled: { opacity: 0.4 },
  nextText:    { ...typography.label, color: '#000', fontSize: 14, letterSpacing: 1 },
  skipBtn:     { alignItems: 'center', paddingVertical: spacing.xs },
  skipText:    { ...typography.caption, color: colors.textMuted },
  stepTitle:   { ...typography.h2, fontSize: 18, color: colors.textPrimary, marginTop: spacing.lg, marginBottom: spacing.sm },
  stepHint:    { ...typography.caption, color: colors.textMuted, marginBottom: spacing.lg },
  // Yıl seçici
  yearScroll:  { maxHeight: 300 },
  yearItem:    {
    height: 48, justifyContent: 'center', paddingHorizontal: spacing.md,
    borderRadius: radius.md, marginBottom: 4,
  },
  yearItemSelected: { backgroundColor: colors.goldGlow, borderWidth: 1, borderColor: colors.gold },
  yearText:         { ...typography.body, color: colors.textMuted, fontSize: 16 },
  yearTextSelected: { color: colors.gold, fontWeight: '700' as const },
  // Cinsiyet
  genderGrid:  { gap: spacing.sm, marginTop: spacing.md },
  genderCard:  {
    flexDirection: 'row', alignItems: 'center', gap: spacing.md,
    padding: spacing.md, borderRadius: radius.lg,
    backgroundColor: colors.surface, borderWidth: 1, borderColor: colors.border,
  },
  genderIcon:  { fontSize: 24, width: 32, textAlign: 'center' as const },
  cardSelected:    { borderColor: colors.gold, backgroundColor: colors.goldGlow },
  cardLabel:       { ...typography.body, color: colors.textMuted },
  cardLabelSelected: { color: colors.gold, fontWeight: '700' as const },
  // Ülke
  countrySearch: {
    height: 44, backgroundColor: colors.surface,
    borderRadius: radius.md, borderWidth: 1, borderColor: colors.border,
    paddingHorizontal: spacing.md, marginBottom: spacing.md,
    ...typography.body, color: colors.textPrimary, fontSize: 14,
  },
  countryGrid:  { flexDirection: 'row', flexWrap: 'wrap', gap: 8 },
  countryChip:  {
    flexDirection: 'row', alignItems: 'center', gap: 6,
    paddingHorizontal: spacing.md, paddingVertical: spacing.sm,
    borderRadius: radius.full, borderWidth: 1, borderColor: colors.border,
    backgroundColor: colors.surface,
  },
  countryFlag:  { fontSize: 16 },
  chipSelected: { borderColor: colors.gold, backgroundColor: colors.goldGlow },
  chipText:     { ...typography.caption, color: colors.textMuted, fontSize: 12 },
  chipTextSelected: { color: colors.gold, fontWeight: '700' as const },
  // Cilt tonu & saç rengi
  skinGrid:    { flexDirection: 'row', gap: spacing.md, marginTop: spacing.xl, justifyContent: 'center' },
  skinCircle:  {
    width: 52, height: 52, borderRadius: 26,
    alignItems: 'center', justifyContent: 'center',
    borderWidth: 2, borderColor: 'transparent',
  },
  skinCircleSelected: { borderColor: colors.gold, ...shadow.gold },
  skinCheck:   { color: '#fff', fontSize: 18, fontWeight: '900' as const, textShadowColor: '#0008', textShadowRadius: 4 },
  skinLabels:  { flexDirection: 'row', gap: spacing.md, marginTop: spacing.sm, justifyContent: 'center' },
  skinLabel:   { ...typography.caption, color: colors.textMuted, fontSize: 10, width: 52, textAlign: 'center' as const },
  // Hedef
  goalGrid: { flexDirection: 'row', flexWrap: 'wrap', gap: spacing.md, marginTop: spacing.md },
  goalCard: {
    width: (width - spacing.lg * 2 - spacing.md) / 2,
    padding: spacing.lg, borderRadius: radius.lg,
    backgroundColor: colors.surface, borderWidth: 1, borderColor: colors.border,
    alignItems: 'center', gap: spacing.sm,
  },
  goalIcon: { fontSize: 36 },
});

export default ProfileSetupScreen;

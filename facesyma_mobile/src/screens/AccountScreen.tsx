// src/screens/AccountScreen.tsx
import React, { useState, useEffect, useCallback } from 'react';
import {
  View, Text, StyleSheet, ScrollView, TouchableOpacity,
  Alert, ActivityIndicator, Linking,
} from 'react-native';
import { useDispatch, useSelector } from 'react-redux';
import { AppDispatch, RootState } from '../store';
import { logout, updateProfile, setUser } from '../store/authSlice';
import { AuthAPI } from '../services/api';
import { InputField, GoldButton, SectionLabel } from '../components/ui';
import theme from '../utils/theme';
const { colors, spacing, typography, radius, shadow } = theme;
import { useLanguage } from '../utils/LanguageContext';
import { t } from '../utils/i18n';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import type { ScreenProps } from '../navigation/types';

const TERMS_URL   = 'https://facesyma.com/wp-content/uploads/2024/07/maula-en.pdf';
const PRIVACY_URL = 'https://facesyma.com/wp-content/uploads/2024/07/ppa-en.pdf';

const COUNTRY_MAP: Record<string, { flag: string; name: string }> = {
  TR:{flag:'🇹🇷',name:'Türkiye'},AZ:{flag:'🇦🇿',name:'Azerbaycan'},CY:{flag:'🇨🇾',name:'Kıbrıs'},
  US:{flag:'🇺🇸',name:'United States'},GB:{flag:'🇬🇧',name:'United Kingdom'},CA:{flag:'🇨🇦',name:'Canada'},
  AU:{flag:'🇦🇺',name:'Australia'},NZ:{flag:'🇳🇿',name:'New Zealand'},IE:{flag:'🇮🇪',name:'Ireland'},
  ZA:{flag:'🇿🇦',name:'South Africa'},NG:{flag:'🇳🇬',name:'Nigeria'},KE:{flag:'🇰🇪',name:'Kenya'},
  GH:{flag:'🇬🇭',name:'Ghana'},PH:{flag:'🇵🇭',name:'Philippines'},SG:{flag:'🇸🇬',name:'Singapore'},
  DE:{flag:'🇩🇪',name:'Germany'},AT:{flag:'🇦🇹',name:'Austria'},CH:{flag:'🇨🇭',name:'Switzerland'},
  LU:{flag:'🇱🇺',name:'Luxembourg'},LI:{flag:'🇱🇮',name:'Liechtenstein'},
  RU:{flag:'🇷🇺',name:'Russia'},UA:{flag:'🇺🇦',name:'Ukraine'},BY:{flag:'🇧🇾',name:'Belarus'},
  KZ:{flag:'🇰🇿',name:'Kazakhstan'},KG:{flag:'🇰🇬',name:'Kyrgyzstan'},TJ:{flag:'🇹🇯',name:'Tajikistan'},
  SA:{flag:'🇸🇦',name:'Saudi Arabia'},EG:{flag:'🇪🇬',name:'Egypt'},AE:{flag:'🇦🇪',name:'UAE'},
  JO:{flag:'🇯🇴',name:'Jordan'},LB:{flag:'🇱🇧',name:'Lebanon'},IQ:{flag:'🇮🇶',name:'Iraq'},
  SY:{flag:'🇸🇾',name:'Syria'},KW:{flag:'🇰🇼',name:'Kuwait'},QA:{flag:'🇶🇦',name:'Qatar'},
  BH:{flag:'🇧🇭',name:'Bahrain'},OM:{flag:'🇴🇲',name:'Oman'},YE:{flag:'🇾🇪',name:'Yemen'},
  PS:{flag:'🇵🇸',name:'Palestine'},LY:{flag:'🇱🇾',name:'Libya'},TN:{flag:'🇹🇳',name:'Tunisia'},
  DZ:{flag:'🇩🇿',name:'Algeria'},MA:{flag:'🇲🇦',name:'Morocco'},SD:{flag:'🇸🇩',name:'Sudan'},
  MR:{flag:'🇲🇷',name:'Mauritania'},SO:{flag:'🇸🇴',name:'Somalia'},DJ:{flag:'🇩🇯',name:'Djibouti'},
  KM:{flag:'🇰🇲',name:'Comoros'},ES:{flag:'🇪🇸',name:'Spain'},MX:{flag:'🇲🇽',name:'Mexico'},
  CO:{flag:'🇨🇴',name:'Colombia'},AR:{flag:'🇦🇷',name:'Argentina'},PE:{flag:'🇵🇪',name:'Peru'},
  VE:{flag:'🇻🇪',name:'Venezuela'},CL:{flag:'🇨🇱',name:'Chile'},EC:{flag:'🇪🇨',name:'Ecuador'},
  BO:{flag:'🇧🇴',name:'Bolivia'},PY:{flag:'🇵🇾',name:'Paraguay'},UY:{flag:'🇺🇾',name:'Uruguay'},
  CU:{flag:'🇨🇺',name:'Cuba'},DO:{flag:'🇩🇴',name:'Dominican Rep.'},GT:{flag:'🇬🇹',name:'Guatemala'},
  HN:{flag:'🇭🇳',name:'Honduras'},SV:{flag:'🇸🇻',name:'El Salvador'},NI:{flag:'🇳🇮',name:'Nicaragua'},
  CR:{flag:'🇨🇷',name:'Costa Rica'},PA:{flag:'🇵🇦',name:'Panama'},KR:{flag:'🇰🇷',name:'South Korea'},
  JP:{flag:'🇯🇵',name:'Japan'},CN:{flag:'🇨🇳',name:'China'},TW:{flag:'🇹🇼',name:'Taiwan'},
  HK:{flag:'🇭🇰',name:'Hong Kong'},IN:{flag:'🇮🇳',name:'India'},PK:{flag:'🇵🇰',name:'Pakistan'},
  BD:{flag:'🇧🇩',name:'Bangladesh'},FR:{flag:'🇫🇷',name:'France'},BE:{flag:'🇧🇪',name:'Belgium'},
  MC:{flag:'🇲🇨',name:'Monaco'},SN:{flag:'🇸🇳',name:'Senegal'},CI:{flag:'🇨🇮',name:"Côte d'Ivoire"},
  CM:{flag:'🇨🇲',name:'Cameroon'},MG:{flag:'🇲🇬',name:'Madagascar'},CD:{flag:'🇨🇩',name:'DR Congo'},
  CG:{flag:'🇨🇬',name:'Congo'},ML:{flag:'🇲🇱',name:'Mali'},BF:{flag:'🇧🇫',name:'Burkina Faso'},
  NE:{flag:'🇳🇪',name:'Niger'},TD:{flag:'🇹🇩',name:'Chad'},GN:{flag:'🇬🇳',name:'Guinea'},
  BJ:{flag:'🇧🇯',name:'Benin'},TG:{flag:'🇹🇬',name:'Togo'},RW:{flag:'🇷🇼',name:'Rwanda'},
  BI:{flag:'🇧🇮',name:'Burundi'},HT:{flag:'🇭🇹',name:'Haiti'},GA:{flag:'🇬🇦',name:'Gabon'},
  CF:{flag:'🇨🇫',name:'Cent. African Rep.'},PT:{flag:'🇵🇹',name:'Portugal'},BR:{flag:'🇧🇷',name:'Brazil'},
  AO:{flag:'🇦🇴',name:'Angola'},MZ:{flag:'🇲🇿',name:'Mozambique'},CV:{flag:'🇨🇻',name:'Cape Verde'},
  GW:{flag:'🇬🇼',name:'Guinea-Bissau'},TL:{flag:'🇹🇱',name:'Timor-Leste'},
  ID:{flag:'🇮🇩',name:'Indonesia'},VN:{flag:'🇻🇳',name:'Vietnam'},IT:{flag:'🇮🇹',name:'Italy'},
  SM:{flag:'🇸🇲',name:'San Marino'},PL:{flag:'🇵🇱',name:'Poland'},OTHER:{flag:'🌍',name:'Other'},
};
const getCountryDisplay = (code: string) => {
  if (code.startsWith('CUSTOM:')) return `🌍 ${code.slice(7)}`;
  const c = COUNTRY_MAP[code];
  return c ? `${c.flag} ${c.name}` : `🌍 ${code}`;
};

const SURGERY_REGIONS = [
  { key: 'nose',     label: 'Burun',   emoji: '👃' },
  { key: 'eyes',     label: 'Gözler',  emoji: '👁' },
  { key: 'lips',     label: 'Dudaklar',emoji: '💋' },
  { key: 'cheeks',   label: 'Yanaklar',emoji: '🫦' },
  { key: 'jawline',  label: 'Çene',    emoji: '💎' },
  { key: 'forehead', label: 'Alın',    emoji: '🧠' },
  { key: 'chin',     label: 'Çene Ucu',emoji: '✨' },
];

const AccountScreen = ({ navigation }: ScreenProps<'Account'>) => {
  const insets   = useSafeAreaInsets();
  const dispatch = useDispatch<AppDispatch>();
  const { lang } = useLanguage();
  const user     = useSelector((s: RootState) => s.auth.user);

  // Edit states
  const [editName,     setEditName]     = useState(user?.name || '');
  const [nameLoading,  setNameLoading]  = useState(false);

  // Password
  const [oldPw,        setOldPw]        = useState('');
  const [newPw,        setNewPw]        = useState('');
  const [pwLoading,    setPwLoading]    = useState(false);

  // Surgery regions
  const [surgeryRegions, setSurgeryRegions] = useState<string[]>(user?.cosmetic_surgery_regions || []);
  const [surgeryLoading,  setSurgeryLoading]  = useState(false);

  // Export loading
  const [exportLoading, setExportLoading] = useState(false);

  // Premium countdown
  const [premiumLabel, setPremiumLabel] = useState('');

  useEffect(() => {
    if (!user?.plan || user.plan !== 'premium') { setPremiumLabel(''); return; }
    const days  = user.premium_days_left  ?? 0;
    const hours = user.premium_hours_left ?? 0;
    if (days > 0)       setPremiumLabel(`${days} gün ${hours} saat kaldı`);
    else if (hours > 0) setPremiumLabel(`${hours} saat kaldı`);
    else                setPremiumLabel('Süresi doldu');
  }, [user]);

  // Refresh profile from API
  useEffect(() => {
    AuthAPI.getProfile()
      .then((u) => dispatch(setUser(u)))
      .catch(() => {});
  }, []);

  const handleSaveName = async () => {
    if (!editName.trim()) return;
    setNameLoading(true);
    try {
      const result = await dispatch(updateProfile({ username: editName.trim() }));
      if (updateProfile.fulfilled.match(result)) {
        Alert.alert('', 'Ad güncellendi.');
      }
    } finally {
      setNameLoading(false);
    }
  };

  const handleChangePassword = async () => {
    if (!oldPw || !newPw) { Alert.alert('', 'Tüm alanları doldurun.'); return; }
    if (newPw.length < 6)  { Alert.alert('', 'Yeni şifre en az 6 karakter olmalı.'); return; }
    setPwLoading(true);
    try {
      await AuthAPI.changePassword(oldPw, newPw);
      setOldPw(''); setNewPw('');
      Alert.alert('', 'Şifre değiştirildi.');
    } catch (e: any) {
      Alert.alert('Hata', e.response?.data?.detail || 'Şifre değiştirilemedi.');
    } finally {
      setPwLoading(false);
    }
  };

  const toggleSurgeryRegion = (key: string) => {
    setSurgeryRegions(prev =>
      prev.includes(key) ? prev.filter(r => r !== key) : [...prev, key]
    );
  };

  const handleSaveSurgeryRegions = async () => {
    setSurgeryLoading(true);
    try {
      const result = await dispatch(updateProfile({ cosmetic_surgery_regions: surgeryRegions }));
      if (updateProfile.fulfilled.match(result)) {
        Alert.alert('', 'Estetik operasyon bölgeleri kaydedildi. Bu bölgeler analizden muaf tutulacak.');
      }
    } finally {
      setSurgeryLoading(false);
    }
  };

  const handleExportData = async () => {
    Alert.alert(
      'Verileri Dışa Aktar',
      'Tüm kişisel verileriniz (GDPR Madde 20) JSON formatında hazırlanacak.',
      [
        { text: 'İptal', style: 'cancel' },
        {
          text: 'Dışa Aktar', onPress: async () => {
            setExportLoading(true);
            try {
              const data = await AuthAPI.exportData();
              Alert.alert('Hazır', `Verileriniz hazırlandı.\n\nKayıt: ${data?.data?.analysis_history?.length || 0} analiz, ${data?.data?.assessment_results?.length || 0} test sonucu.`);
            } catch (e: any) {
              Alert.alert('Hata', e.response?.data?.detail || 'Dışa aktarma başarısız.');
            } finally {
              setExportLoading(false);
            }
          },
        },
      ]
    );
  };

  const handleDeleteAccount = () => {
    Alert.alert(
      'Hesabı Sil',
      'Bu işlem geri alınamaz. Tüm verileriniz kalıcı olarak silinecek. Devam etmek istiyor musunuz?',
      [
        { text: 'İptal', style: 'cancel' },
        {
          text: 'Evet, Hesabımı Sil', style: 'destructive',
          onPress: () => {
            Alert.alert(
              'Son Onay',
              'Hesabınız ve tüm verileriniz kalıcı olarak silinecek.',
              [
                { text: 'Geri Dön', style: 'cancel' },
                {
                  text: 'Kalıcı Olarak Sil', style: 'destructive',
                  onPress: async () => {
                    try {
                      await AuthAPI.deleteAccount();
                      await dispatch(logout());
                      navigation.replace('Auth');
                    } catch (e: any) {
                      Alert.alert('Hata', e.response?.data?.detail || 'Hesap silinemedi.');
                    }
                  },
                },
              ]
            );
          },
        },
      ]
    );
  };

  const isPremium = user?.plan === 'premium';

  return (
    <View style={styles.container}>
      {/* Header */}
      <View style={[styles.header, { paddingTop: insets.top + spacing.sm }]}>
        <TouchableOpacity onPress={() => navigation.goBack()}>
          <Text style={styles.back}>←</Text>
        </TouchableOpacity>
        <Text style={styles.headerTitle}>Hesabım</Text>
        <View style={{ width: 40 }} />
      </View>

      <ScrollView contentContainerStyle={styles.scroll} showsVerticalScrollIndicator={false}>

        {/* ─── 1. Kişisel Bilgiler ─────────────────────────────────────────── */}
        <SectionLabel>Kişisel Bilgiler</SectionLabel>
        <View style={styles.card}>
          <InputField
            label="Ad Soyad"
            value={editName}
            onChangeText={setEditName}
            placeholder="Adınızı girin"
            icon="👤"
          />
          <GoldButton
            title="Kaydet"
            onPress={handleSaveName}
            loading={nameLoading}
            style={styles.smallBtn}
          />
          <View style={styles.infoRow}>
            <Text style={styles.infoLabel}>E-posta</Text>
            <Text style={styles.infoValue}>{user?.email}</Text>
          </View>
          {user?.birth_year && (
            <View style={styles.infoRow}>
              <Text style={styles.infoLabel}>Doğum Yılı</Text>
              <Text style={styles.infoValue}>{user.birth_year}</Text>
            </View>
          )}
          {user?.country && (
            <View style={styles.infoRow}>
              <Text style={styles.infoLabel}>Ülke</Text>
              <Text style={styles.infoValue}>{getCountryDisplay(user.country)}</Text>
            </View>
          )}
        </View>

        {/* ─── 2. Görünüm — Estetik Operasyon ─────────────────────────────── */}
        <SectionLabel>Görünüm & Estetik Operasyon</SectionLabel>
        <View style={styles.card}>
          <Text style={styles.sectionNote}>
            Estetik operasyon geçirdiğiniz bölgeleri işaretleyin. Bu bölgeler yüz analizinden muaf tutulur.
          </Text>
          <View style={styles.regionGrid}>
            {SURGERY_REGIONS.map(region => {
              const selected = surgeryRegions.includes(region.key);
              return (
                <TouchableOpacity
                  key={region.key}
                  style={[styles.regionChip, selected && styles.regionChipSelected]}
                  onPress={() => toggleSurgeryRegion(region.key)}
                  activeOpacity={0.8}
                >
                  <Text style={styles.regionEmoji}>{region.emoji}</Text>
                  <Text style={[styles.regionLabel, selected && styles.regionLabelSelected]}>
                    {region.label}
                  </Text>
                </TouchableOpacity>
              );
            })}
          </View>
          <GoldButton
            title="Bölgeleri Kaydet"
            onPress={handleSaveSurgeryRegions}
            loading={surgeryLoading}
            style={styles.smallBtn}
          />
        </View>

        {/* ─── 3. Hedef ────────────────────────────────────────────────────── */}
        <SectionLabel>Hedefim</SectionLabel>
        <View style={styles.card}>
          {user?.goal ? (
            <View style={styles.infoRow}>
              <Text style={styles.infoLabel}>Seçili Hedef</Text>
              <Text style={styles.infoValue}>{user.goal}</Text>
            </View>
          ) : (
            <Text style={styles.sectionNote}>Henüz bir hedef belirlenmedi.</Text>
          )}
          <TouchableOpacity
            style={styles.linkRow}
            onPress={() => navigation.replace('ProfileSetup')}
          >
            <Text style={styles.linkText}>Profil Bilgilerini Düzenle →</Text>
          </TouchableOpacity>
        </View>

        {/* ─── 4. Hesap Bilgileri ───────────────────────────────────────────── */}
        <SectionLabel>Hesap Bilgileri</SectionLabel>
        <View style={styles.card}>
          <View style={styles.planRow}>
            <View>
              <Text style={styles.planLabel}>Plan</Text>
              <Text style={[styles.planValue, isPremium && styles.premiumText]}>
                {isPremium ? 'Premium' : 'Ücretsiz'}
              </Text>
            </View>
            {isPremium && premiumLabel ? (
              <View style={styles.premiumBadge}>
                <Text style={styles.premiumBadgeText}>{premiumLabel}</Text>
              </View>
            ) : !isPremium ? (
              <TouchableOpacity style={styles.upgradeBtn}>
                <Text style={styles.upgradeBtnText}>Premium'a Geç</Text>
              </TouchableOpacity>
            ) : null}
          </View>
          <View style={styles.infoRow}>
            <Text style={styles.infoLabel}>Kayıt Tarihi</Text>
            <Text style={styles.infoValue}>
              {user?.created_at ? new Date(user.created_at).toLocaleDateString('tr-TR') : '-'}
            </Text>
          </View>
          {user?.last_login && (
            <View style={styles.infoRow}>
              <Text style={styles.infoLabel}>Son Giriş</Text>
              <Text style={styles.infoValue}>
                {new Date(user.last_login).toLocaleString('tr-TR')}
              </Text>
            </View>
          )}
        </View>

        {/* ─── 5. Güvenlik ─────────────────────────────────────────────────── */}
        <SectionLabel>Güvenlik</SectionLabel>
        <View style={styles.card}>
          <InputField
            label="Mevcut Şifre"
            value={oldPw}
            onChangeText={setOldPw}
            secureTextEntry
            placeholder="Mevcut şifreniz"
            icon="🔒"
          />
          <InputField
            label="Yeni Şifre"
            value={newPw}
            onChangeText={setNewPw}
            secureTextEntry
            placeholder="En az 6 karakter"
            icon="🔑"
          />
          <GoldButton
            title="Şifreyi Değiştir"
            onPress={handleChangePassword}
            loading={pwLoading}
            style={styles.smallBtn}
          />
        </View>

        {/* ─── 6. Yasal ────────────────────────────────────────────────────── */}
        <SectionLabel>Yasal</SectionLabel>
        <View style={styles.card}>
          <TouchableOpacity style={styles.legalRow} onPress={() => Linking.openURL(TERMS_URL)}>
            <Text style={styles.legalIcon}>📄</Text>
            <Text style={styles.legalText}>Kullanım Koşulları</Text>
            <Text style={styles.legalArrow}>›</Text>
          </TouchableOpacity>
          <View style={styles.divider} />
          <TouchableOpacity style={styles.legalRow} onPress={() => Linking.openURL(PRIVACY_URL)}>
            <Text style={styles.legalIcon}>🔐</Text>
            <Text style={styles.legalText}>Gizlilik Politikası</Text>
            <Text style={styles.legalArrow}>›</Text>
          </TouchableOpacity>
        </View>

        {/* ─── 7. Veri & Hesap Silme ───────────────────────────────────────── */}
        <SectionLabel>Verilerim</SectionLabel>
        <View style={styles.card}>
          <Text style={styles.sectionNote}>
            GDPR Madde 20 kapsamında tüm kişisel verilerinizi dışa aktarabilirsiniz.
          </Text>
          {exportLoading ? (
            <ActivityIndicator color={colors.gold} style={{ marginVertical: spacing.md }} />
          ) : (
            <TouchableOpacity style={styles.exportBtn} onPress={handleExportData}>
              <Text style={styles.exportBtnText}>Verilerimi Dışa Aktar (JSON)</Text>
            </TouchableOpacity>
          )}
        </View>

        <View style={[styles.card, styles.deleteCard]}>
          <Text style={styles.deleteTitle}>Hesabı Sil</Text>
          <Text style={styles.deleteNote}>
            Hesabınızı ve tüm verilerinizi kalıcı olarak silebilirsiniz. Bu işlem geri alınamaz.
          </Text>
          <TouchableOpacity style={styles.deleteBtn} onPress={handleDeleteAccount}>
            <Text style={styles.deleteBtnText}>Hesabımı Kalıcı Olarak Sil</Text>
          </TouchableOpacity>
        </View>

        <View style={{ height: spacing.xxxl }} />
      </ScrollView>

    </View>
  );
};

const styles = StyleSheet.create({
  container:   { flex: 1, backgroundColor: colors.background },
  header: {
    flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between',
    paddingHorizontal: spacing.lg,
    paddingBottom: spacing.md,
    borderBottomWidth: 1, borderBottomColor: colors.border,
  },
  back:        { ...typography.body, color: colors.gold, fontSize: 22 },
  headerTitle: { ...typography.h3, letterSpacing: 0.5 },
  scroll:      { padding: spacing.lg },

  card: {
    backgroundColor: colors.surface,
    borderRadius: radius.lg,
    borderWidth: 1,
    borderColor: colors.border,
    padding: spacing.md,
    marginBottom: spacing.md,
  },

  sectionNote: { ...typography.caption, color: colors.textMuted, marginBottom: spacing.md, lineHeight: 18 },

  smallBtn: { marginTop: spacing.sm },

  infoRow: {
    flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center',
    paddingVertical: spacing.sm,
    borderTopWidth: 1, borderTopColor: colors.border,
    marginTop: spacing.xs,
  },
  infoLabel: { ...typography.caption, color: colors.textMuted },
  infoValue: { ...typography.caption, color: colors.textPrimary, flex: 1, textAlign: 'right' },

  regionGrid: {
    flexDirection: 'row', flexWrap: 'wrap', gap: 8, marginBottom: spacing.md,
  },
  regionChip: {
    flexDirection: 'row', alignItems: 'center', gap: 4,
    paddingHorizontal: 10, paddingVertical: 6,
    borderRadius: radius.full,
    borderWidth: 1, borderColor: colors.border,
    backgroundColor: colors.surfaceAlt,
  },
  regionChipSelected: {
    borderColor: colors.gold,
    backgroundColor: colors.goldGlow,
  },
  regionEmoji:        { fontSize: 14 },
  regionLabel:        { ...typography.caption, color: colors.textMuted, fontSize: 12 },
  regionLabelSelected:{ color: colors.gold },

  linkRow:    { paddingTop: spacing.sm },
  linkText:   { ...typography.caption, color: colors.gold, textDecorationLine: 'underline' },

  planRow: {
    flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center',
    marginBottom: spacing.sm,
  },
  planLabel:    { ...typography.caption, color: colors.textMuted, marginBottom: 2 },
  planValue:    { ...typography.h3, color: colors.textPrimary },
  premiumText:  { color: colors.gold },
  premiumBadge: {
    backgroundColor: colors.goldGlow,
    borderRadius: radius.full,
    borderWidth: 1, borderColor: colors.goldDark,
    paddingHorizontal: 10, paddingVertical: 4,
  },
  premiumBadgeText: { ...typography.caption, color: colors.gold, fontSize: 11 },
  upgradeBtn: {
    backgroundColor: colors.gold,
    borderRadius: radius.full,
    paddingHorizontal: 14, paddingVertical: 6,
  },
  upgradeBtnText: { fontFamily: 'System', fontSize: 12, fontWeight: '700', color: '#000' },

  legalRow:   { flexDirection: 'row', alignItems: 'center', paddingVertical: spacing.sm },
  legalIcon:  { fontSize: 16, marginRight: spacing.sm },
  legalText:  { ...typography.body, color: colors.textPrimary, flex: 1, fontSize: 14 },
  legalArrow: { ...typography.h2, color: colors.textMuted, fontSize: 18 },
  divider:    { height: 1, backgroundColor: colors.border, marginVertical: 2 },

  exportBtn: {
    borderWidth: 1, borderColor: colors.gold,
    borderRadius: radius.md,
    paddingVertical: spacing.md,
    alignItems: 'center',
    marginTop: spacing.xs,
  },
  exportBtnText: { ...typography.label, color: colors.gold, fontSize: 13 },

  deleteCard: { borderColor: colors.error + '44' },
  deleteTitle:{ ...typography.h3, color: colors.error, marginBottom: spacing.xs },
  deleteNote: { ...typography.caption, color: colors.textMuted, marginBottom: spacing.md, lineHeight: 18 },
  deleteBtn: {
    backgroundColor: colors.error + '22',
    borderWidth: 1, borderColor: colors.error,
    borderRadius: radius.md,
    paddingVertical: spacing.md,
    alignItems: 'center',
  },
  deleteBtnText: { ...typography.label, color: colors.error, fontSize: 13 },

});

export default AccountScreen;

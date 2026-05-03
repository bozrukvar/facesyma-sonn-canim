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
const getLocale = (lang: string): string => {
  const localeMap: Record<string, string> = {
    tr:'tr-TR', en:'en-US', de:'de-DE', ru:'ru-RU', ar:'ar-SA', es:'es-ES',
    ko:'ko-KR', ja:'ja-JP', zh:'zh-CN', hi:'hi-IN', fr:'fr-FR', pt:'pt-PT',
    bn:'bn-IN', id:'id-ID', ur:'ur-PK', it:'it-IT', vi:'vi-VN', pl:'pl-PL',
  };
  return localeMap[lang] || 'en-US';
};

const getCountryDisplay = (code: string) => {
  if (code.startsWith('CUSTOM:')) return `🌍 ${code.slice(7)}`;
  const c = COUNTRY_MAP[code];
  return c ? `${c.flag} ${c.name}` : `🌍 ${code}`;
};

const SURGERY_REGIONS = [
  { key: 'nose',     emoji: '👃' },
  { key: 'eyes',     emoji: '👁' },
  { key: 'lips',     emoji: '💋' },
  { key: 'cheeks',   emoji: '🫦' },
  { key: 'jawline',  emoji: '💎' },
  { key: 'forehead', emoji: '🧠' },
  { key: 'chin',     emoji: '✨' },
];

const AccountScreen = ({ navigation }: ScreenProps<'Account'>) => {
  const insets   = useSafeAreaInsets();
  const dispatch = useDispatch<AppDispatch>();
  const { lang } = useLanguage();
  const user     = useSelector((s: RootState) => s.auth.user);

  const [editName,     setEditName]     = useState(user?.name || '');
  const [nameLoading,  setNameLoading]  = useState(false);

  const [oldPw,        setOldPw]        = useState('');
  const [newPw,        setNewPw]        = useState('');
  const [pwLoading,    setPwLoading]    = useState(false);

  const [surgeryRegions, setSurgeryRegions] = useState<string[]>(user?.cosmetic_surgery_regions || []);
  const [surgeryLoading,  setSurgeryLoading]  = useState(false);

  const [exportLoading, setExportLoading] = useState(false);

  const [premiumLabel, setPremiumLabel] = useState('');

  useEffect(() => {
    if (!user?.plan || user.plan !== 'premium') { setPremiumLabel(''); return; }
    const days  = user.premium_days_left  ?? 0;
    const hours = user.premium_hours_left ?? 0;
    if (days > 0)
      setPremiumLabel(t('account.premium_days', lang).replace('{days}', String(days)).replace('{hours}', String(hours)));
    else if (hours > 0)
      setPremiumLabel(t('account.premium_hours', lang).replace('{hours}', String(hours)));
    else
      setPremiumLabel(t('account.premium_expired', lang));
  }, [user, lang]);

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
        Alert.alert('', t('account.name_updated', lang));
      }
    } finally {
      setNameLoading(false);
    }
  };

  const handleChangePassword = async () => {
    if (!oldPw || !newPw) { Alert.alert('', t('account.fill_all', lang)); return; }
    if (newPw.length < 6)  { Alert.alert('', t('account.pw_min', lang)); return; }
    setPwLoading(true);
    try {
      await AuthAPI.changePassword(oldPw, newPw);
      setOldPw(''); setNewPw('');
      Alert.alert('', t('account.pw_changed', lang));
    } catch (e: any) {
      Alert.alert('', e.response?.data?.detail || t('account.pw_error', lang));
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
        Alert.alert('', t('account.surgery_saved', lang));
      }
    } finally {
      setSurgeryLoading(false);
    }
  };

  const handleExportData = async () => {
    Alert.alert(
      t('account.export_title', lang),
      t('account.export_confirm', lang),
      [
        { text: t('account.export_cancel', lang), style: 'cancel' },
        {
          text: t('account.export_action', lang), onPress: async () => {
            setExportLoading(true);
            try {
              const data = await AuthAPI.exportData();
              Alert.alert(
                t('account.export_ready_title', lang),
                `${t('account.export_ready_title', lang)}.\n\n${data?.data?.analysis_history?.length || 0} / ${data?.data?.assessment_results?.length || 0}`
              );
            } catch (e: any) {
              Alert.alert('', e.response?.data?.detail || t('account.export_error', lang));
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
      t('account.delete_title', lang),
      t('account.delete_confirm_msg', lang),
      [
        { text: t('account.export_cancel', lang), style: 'cancel' },
        {
          text: t('account.delete_yes', lang), style: 'destructive',
          onPress: () => {
            Alert.alert(
              t('account.delete_final_title', lang),
              t('account.delete_final_msg', lang),
              [
                { text: t('account.delete_back', lang), style: 'cancel' },
                {
                  text: t('account.delete_permanent', lang), style: 'destructive',
                  onPress: async () => {
                    try {
                      await AuthAPI.deleteAccount();
                      await dispatch(logout());
                      navigation.replace('Auth');
                    } catch (e: any) {
                      Alert.alert('', e.response?.data?.detail || t('account.delete_error', lang));
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
        <Text style={styles.headerTitle}>{t('account.title', lang)}</Text>
        <View style={{ width: 40 }} />
      </View>

      <ScrollView contentContainerStyle={styles.scroll} showsVerticalScrollIndicator={false}>

        {/* ─── 1. Kişisel Bilgiler ─────────────────────────────────────────── */}
        <SectionLabel>{t('account.personal_info', lang)}</SectionLabel>
        <View style={styles.card}>
          <InputField
            label={t('account.full_name', lang)}
            value={editName}
            onChangeText={setEditName}
            placeholder={t('account.name_placeholder', lang)}
            icon="👤"
          />
          <GoldButton
            title={t('account.save', lang)}
            onPress={handleSaveName}
            loading={nameLoading}
            style={styles.smallBtn}
          />
          <View style={styles.infoRow}>
            <Text style={styles.infoLabel}>{t('account.email', lang)}</Text>
            <Text style={styles.infoValue}>{user?.email}</Text>
          </View>
          {user?.birth_year && (
            <View style={styles.infoRow}>
              <Text style={styles.infoLabel}>{t('account.birth_year', lang)}</Text>
              <Text style={styles.infoValue}>{user.birth_year}</Text>
            </View>
          )}
          {user?.country && (
            <View style={styles.infoRow}>
              <Text style={styles.infoLabel}>{t('account.country', lang)}</Text>
              <Text style={styles.infoValue}>{getCountryDisplay(user.country)}</Text>
            </View>
          )}
        </View>

        {/* ─── 2. Görünüm — Estetik Operasyon ─────────────────────────────── */}
        <SectionLabel>{t('account.surgery_section', lang)}</SectionLabel>
        <View style={styles.card}>
          <Text style={styles.sectionNote}>{t('account.surgery_note', lang)}</Text>
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
                    {t(`account.surgery_${region.key}` as any, lang)}
                  </Text>
                </TouchableOpacity>
              );
            })}
          </View>
          <GoldButton
            title={t('account.save_regions', lang)}
            onPress={handleSaveSurgeryRegions}
            loading={surgeryLoading}
            style={styles.smallBtn}
          />
        </View>

        {/* ─── 3. Hedef ────────────────────────────────────────────────────── */}
        <SectionLabel>{t('account.my_goal', lang)}</SectionLabel>
        <View style={styles.card}>
          {user?.goal ? (
            <View style={styles.infoRow}>
              <Text style={styles.infoLabel}>{t('account.goal_selected', lang)}</Text>
              <Text style={styles.infoValue}>{user.goal}</Text>
            </View>
          ) : (
            <Text style={styles.sectionNote}>{t('account.goal_none', lang)}</Text>
          )}
          <TouchableOpacity
            style={styles.linkRow}
            onPress={() => navigation.replace('ProfileSetup')}
          >
            <Text style={styles.linkText}>{t('account.edit_profile', lang)}</Text>
          </TouchableOpacity>
        </View>

        {/* ─── 4. Hesap Bilgileri ───────────────────────────────────────────── */}
        <SectionLabel>{t('account.account_info', lang)}</SectionLabel>
        <View style={styles.card}>
          <View style={styles.planRow}>
            <View>
              <Text style={styles.planLabel}>{t('account.plan', lang)}</Text>
              <Text style={[styles.planValue, isPremium && styles.premiumText]}>
                {isPremium ? 'Premium' : t('account.free_plan', lang)}
              </Text>
            </View>
            {isPremium && premiumLabel ? (
              <View style={styles.premiumBadge}>
                <Text style={styles.premiumBadgeText}>{premiumLabel}</Text>
              </View>
            ) : !isPremium ? (
              <TouchableOpacity style={styles.upgradeBtn}>
                <Text style={styles.upgradeBtnText}>{t('account.upgrade_btn', lang)}</Text>
              </TouchableOpacity>
            ) : null}
          </View>
          <View style={styles.infoRow}>
            <Text style={styles.infoLabel}>{t('account.join_date', lang)}</Text>
            <Text style={styles.infoValue}>
              {user?.created_at ? new Date(user.created_at).toLocaleDateString(getLocale(lang)) : '-'}
            </Text>
          </View>
          {user?.last_login && (
            <View style={styles.infoRow}>
              <Text style={styles.infoLabel}>{t('account.last_login', lang)}</Text>
              <Text style={styles.infoValue}>
                {new Date(user.last_login).toLocaleString(getLocale(lang))}
              </Text>
            </View>
          )}
        </View>

        {/* ─── 5. Güvenlik ─────────────────────────────────────────────────── */}
        <SectionLabel>{t('account.security', lang)}</SectionLabel>
        <View style={styles.card}>
          <InputField
            label={t('account.current_password', lang)}
            value={oldPw}
            onChangeText={setOldPw}
            secureTextEntry
            placeholder={t('account.current_pw_placeholder', lang)}
            icon="🔒"
          />
          <InputField
            label={t('account.new_password', lang)}
            value={newPw}
            onChangeText={setNewPw}
            secureTextEntry
            placeholder={t('account.new_pw_placeholder', lang)}
            icon="🔑"
          />
          <GoldButton
            title={t('account.change_password', lang)}
            onPress={handleChangePassword}
            loading={pwLoading}
            style={styles.smallBtn}
          />
        </View>

        {/* ─── 6. Yasal ────────────────────────────────────────────────────── */}
        <SectionLabel>{t('account.legal', lang)}</SectionLabel>
        <View style={styles.card}>
          <TouchableOpacity style={styles.legalRow} onPress={() => Linking.openURL(TERMS_URL)}>
            <Text style={styles.legalIcon}>📄</Text>
            <Text style={styles.legalText}>{t('account.terms', lang)}</Text>
            <Text style={styles.legalArrow}>›</Text>
          </TouchableOpacity>
          <View style={styles.divider} />
          <TouchableOpacity style={styles.legalRow} onPress={() => Linking.openURL(PRIVACY_URL)}>
            <Text style={styles.legalIcon}>🔐</Text>
            <Text style={styles.legalText}>{t('account.privacy_policy', lang)}</Text>
            <Text style={styles.legalArrow}>›</Text>
          </TouchableOpacity>
        </View>

        {/* ─── 7. Veri & Hesap Silme ───────────────────────────────────────── */}
        <SectionLabel>{t('account.my_data', lang)}</SectionLabel>
        <View style={styles.card}>
          <Text style={styles.sectionNote}>{t('account.gdpr_note', lang)}</Text>
          {exportLoading ? (
            <ActivityIndicator color={colors.gold} style={{ marginVertical: spacing.md }} />
          ) : (
            <TouchableOpacity style={styles.exportBtn} onPress={handleExportData}>
              <Text style={styles.exportBtnText}>{t('account.export_btn', lang)}</Text>
            </TouchableOpacity>
          )}
        </View>

        <View style={[styles.card, styles.deleteCard]}>
          <Text style={styles.deleteTitle}>{t('account.delete_title', lang)}</Text>
          <Text style={styles.deleteNote}>{t('account.delete_note', lang)}</Text>
          <TouchableOpacity style={styles.deleteBtn} onPress={handleDeleteAccount}>
            <Text style={styles.deleteBtnText}>{t('account.delete_btn', lang)}</Text>
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

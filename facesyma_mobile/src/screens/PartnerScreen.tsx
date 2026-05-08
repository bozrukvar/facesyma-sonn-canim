// src/screens/PartnerScreen.tsx
import React, { useEffect, useState, useCallback } from 'react';
import {
  View, Text, StyleSheet, ScrollView, TouchableOpacity,
  TextInput, Alert, ActivityIndicator, Share,
} from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { useLanguage } from '../utils/LanguageContext';
import { PartnerAPI, PartnerStatus } from '../services/api';
import theme from '../utils/theme';
const { colors, spacing, typography, radius, shadow } = theme;
import type { AppNavProp } from '../navigation/types';

const TR: Record<string, Record<string, string>> = {
  tr: {
    title:          'Partner Modu',
    subtitle:       'İlişki uyumluluğunuzu keşfedin',
    loading:        'Yükleniyor...',
    no_partner:     'Henüz bir partneriniz yok',
    no_partner_sub: 'Partner davet edin veya bir davet koduna katılın',
    invite_btn:     '💌 Davet Kodu Oluştur',
    join_btn:       '🔑 Koda Katıl',
    join_placeholder: '6 haneli kodu girin',
    join_action:    'Katıl',
    invite_section: 'Davet Kodunuz',
    invite_copy:    '↑ Paylaş / Kopyala',
    invite_copied:  '↑ Paylaş / Kopyala',
    invite_wait:    'Partnerinizin kodu girmesini bekleyin',
    active_title:   'Bağlı Partner',
    active_sub:     'Uyumluluk raporu hazır',
    compat_score:   'Uyumluluk Skoru',
    view_report:    '📊 Raporu Görüntüle',
    disconnect:     '🔓 Bağlantıyı Kes',
    disconnect_confirm: 'Emin misiniz?',
    disconnect_msg: 'Partnerinizle bağlantınız kesilecek. Bu işlem geri alınamaz.',
    disconnect_ok:  'Evet, Kes',
    disconnect_cancel: 'Vazgeç',
    privacy_note:   '🔒 Her iki tarafın rızası gereklidir. İstediğiniz zaman bağlantıyı kesebilirsiniz.',
    error_invite:   'Davet kodu oluşturulamadı. Tekrar deneyin.',
    error_join:     'Kod geçersiz veya süresi dolmuş. Kontrol edin.',
    error_disconnect: 'Bağlantı kesilemedi. Tekrar deneyin.',
    pending_badge:  'Bekleniyor',
    active_badge:   'Aktif',
    back:           '←',
  },
  en: {
    title:          'Partner Mode',
    subtitle:       'Discover your relationship compatibility',
    loading:        'Loading...',
    no_partner:     'No partner yet',
    no_partner_sub: 'Invite a partner or join an invite',
    invite_btn:     '💌 Create Invite Code',
    join_btn:       '🔑 Join a Code',
    join_placeholder: 'Enter 6-character code',
    join_action:    'Join',
    invite_section: 'Your Invite Code',
    invite_copy:    '↑ Share / Copy',
    invite_copied:  '↑ Share / Copy',
    invite_wait:    'Waiting for your partner to enter the code',
    active_title:   'Connected Partner',
    active_sub:     'Compatibility report is ready',
    compat_score:   'Compatibility Score',
    view_report:    '📊 View Report',
    disconnect:     '🔓 Disconnect',
    disconnect_confirm: 'Are you sure?',
    disconnect_msg: 'Your connection will be removed. This cannot be undone.',
    disconnect_ok:  'Yes, Disconnect',
    disconnect_cancel: 'Cancel',
    privacy_note:   '🔒 Both parties must consent. You can disconnect at any time.',
    error_invite:   'Could not create invite code. Try again.',
    error_join:     'Invalid or expired code. Please check.',
    error_disconnect: 'Could not disconnect. Try again.',
    pending_badge:  'Pending',
    active_badge:   'Active',
    back:           '←',
  },
};

const L = (lang: string, key: string) => (TR[lang] || TR['en'])[key] ?? (TR['en'][key] ?? key);

const ScoreRing: React.FC<{ score: number }> = ({ score }) => {
  const color = score >= 70 ? '#4CAF50' : score >= 50 ? colors.gold : '#E07A7A';
  return (
    <View style={[ringStyles.wrap, { borderColor: color }]}>
      <Text style={[ringStyles.score, { color }]}>{score}</Text>
      <Text style={ringStyles.pct}>/ 100</Text>
    </View>
  );
};

const ringStyles = StyleSheet.create({
  wrap: { width: 88, height: 88, borderRadius: 44, borderWidth: 5, alignItems: 'center', justifyContent: 'center', backgroundColor: colors.surface },
  score: { fontSize: 28, fontWeight: '800', fontFamily: 'System' },
  pct:   { fontSize: 11, color: colors.textMuted, fontFamily: 'System' },
});

const PartnerScreen: React.FC<{ navigation: any }> = ({ navigation }) => {
  const insets = useSafeAreaInsets();
  const { lang } = useLanguage();

  const [status, setStatus]   = useState<PartnerStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [joining, setJoining] = useState(false);
  const [showJoin, setShowJoin] = useState(false);
  const [joinCode, setJoinCode] = useState('');

  const load = useCallback(async () => {
    try {
      const res = await PartnerAPI.getStatus();
      setStatus(res);
    } catch {
      setStatus({ success: false, status: 'none' });
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { load(); }, [load]);

  const handleInvite = async () => {
    try {
      setLoading(true);
      const res = await PartnerAPI.invite();
      setStatus(prev => ({ ...(prev || { success: true }), status: 'pending', invite_code: res.invite_code, is_inviter: true }));
    } catch (e: any) {
      const detail = e?.response?.data?.detail || L(lang, 'error_invite');
      Alert.alert('', detail);
    } finally {
      setLoading(false);
    }
  };

  const handleJoin = async () => {
    if (joinCode.trim().length !== 6) return;
    try {
      setJoining(true);
      const res = await PartnerAPI.join(joinCode.trim().toUpperCase(), lang);
      setStatus({
        success: true,
        status: 'active',
        partner_name: res.partner_name,
        compatibility_score: res.compatibility_score,
      });
      setShowJoin(false);
    } catch (e: any) {
      const detail = e?.response?.data?.detail || L(lang, 'error_join');
      Alert.alert('', detail);
    } finally {
      setJoining(false);
    }
  };

  const handleCopy = async () => {
    if (status?.invite_code) {
      await Share.share({ message: status.invite_code });
    }
  };

  const handleDisconnect = () => {
    Alert.alert(
      L(lang, 'disconnect_confirm'),
      L(lang, 'disconnect_msg'),
      [
        { text: L(lang, 'disconnect_cancel'), style: 'cancel' },
        {
          text: L(lang, 'disconnect_ok'), style: 'destructive',
          onPress: async () => {
            try {
              await PartnerAPI.disconnect();
              setStatus({ success: true, status: 'none' });
            } catch {
              Alert.alert('', L(lang, 'error_disconnect'));
            }
          },
        },
      ],
    );
  };

  return (
    <View style={[styles.container, { paddingTop: insets.top }]}>
      {/* Header */}
      <View style={styles.header}>
        <TouchableOpacity onPress={() => navigation.goBack()} style={styles.backBtn}
          accessibilityRole="button"
          accessibilityLabel="L(lang, 'back')"
        >
          <Text style={styles.backText}>{L(lang, 'back')}</Text>
        </TouchableOpacity>
        <View style={styles.headerCenter}>
          <Text style={styles.title}>{L(lang, 'title')}</Text>
          <Text style={styles.subtitle}>{L(lang, 'subtitle')}</Text>
        </View>
        <View style={styles.backBtn} />
      </View>

      {loading ? (
        <View style={styles.center}>
          <ActivityIndicator color={colors.warmAmber} size="large" />
          <Text style={styles.loadingText}>{L(lang, 'loading')}</Text>
        </View>
      ) : (
        <ScrollView
          contentContainerStyle={styles.scroll}
          showsVerticalScrollIndicator={false}
          keyboardShouldPersistTaps="handled"
        >
          {/* Hero emoji */}
          <View style={styles.heroWrap}>
            <Text style={styles.heroEmoji}>💑</Text>
          </View>

          {/* ── NONE: davet oluştur / koda katıl ── */}
          {(!status || status.status === 'none') && (
            <View style={styles.section}>
              <Text style={styles.noPartnerTitle}>{L(lang, 'no_partner')}</Text>
              <Text style={styles.noPartnerSub}>{L(lang, 'no_partner_sub')}</Text>

              <TouchableOpacity style={styles.primaryBtn} onPress={handleInvite} activeOpacity={0.85}
                accessibilityRole="button"
                accessibilityLabel="L(lang, 'invite_btn')"
              >
                <Text style={styles.primaryBtnText}>{L(lang, 'invite_btn')}</Text>
              </TouchableOpacity>

              <TouchableOpacity style={styles.secondaryBtn} onPress={() => setShowJoin(v => !v)} activeOpacity={0.85}
                accessibilityRole="button"
                accessibilityLabel="L(lang, 'join_btn')"
              >
                <Text style={styles.secondaryBtnText}>{L(lang, 'join_btn')}</Text>
              </TouchableOpacity>

              {showJoin && (
                <View style={styles.joinRow}>
                  <TextInput
                    style={styles.codeInput}
                    value={joinCode}
                    onChangeText={t => setJoinCode(t.toUpperCase())}
                    placeholder={L(lang, 'join_placeholder')}
                    placeholderTextColor={colors.textMuted}
                    autoCapitalize="characters"
                    maxLength={6}
                  />
                  <TouchableOpacity
                    accessibilityRole="button"
                    accessibilityLabel="L(lang, 'join_action')"
                    style={[styles.joinActionBtn, joinCode.length === 6 && styles.joinActionActive]}
                    onPress={handleJoin}
                    disabled={joinCode.length !== 6 || joining}
                  >
                    {joining
                      ? <ActivityIndicator color="#fff" size="small" />
                      : <Text style={styles.joinActionText}>{L(lang, 'join_action')}</Text>
                    }
                  </TouchableOpacity>
                </View>
              )}
            </View>
          )}

          {/* ── PENDING: davet kodu göster ── */}
          {status?.status === 'pending' && (
            <View style={styles.section}>
              <View style={styles.badgeRow}>
                <View style={[styles.badge, styles.badgePending]}>
                  <Text style={styles.badgeText}>{L(lang, 'pending_badge')}</Text>
                </View>
              </View>

              <Text style={styles.sectionTitle}>{L(lang, 'invite_section')}</Text>

              <View style={styles.codeCard}>
                <Text style={styles.codeDisplay}>{status.invite_code}</Text>
              </View>

              <TouchableOpacity style={styles.copyBtn} onPress={handleCopy} activeOpacity={0.8}
                accessibilityRole="button"
                accessibilityLabel="L(lang, 'invite_copy')"
              >
                <Text style={styles.copyBtnText}>{L(lang, 'invite_copy')}</Text>
              </TouchableOpacity>

              <Text style={styles.waitText}>{L(lang, 'invite_wait')}</Text>

              <TouchableOpacity style={styles.disconnectBtn} onPress={handleDisconnect} activeOpacity={0.8}
                accessibilityRole="button"
                accessibilityLabel="L(lang, 'disconnect')"
              >
                <Text style={styles.disconnectBtnText}>{L(lang, 'disconnect')}</Text>
              </TouchableOpacity>
            </View>
          )}

          {/* ── ACTIVE: partner bağlı ── */}
          {status?.status === 'active' && (
            <View style={styles.section}>
              <View style={styles.badgeRow}>
                <View style={[styles.badge, styles.badgeActive]}>
                  <Text style={styles.badgeText}>{L(lang, 'active_badge')}</Text>
                </View>
              </View>

              <Text style={styles.sectionTitle}>{L(lang, 'active_title')}</Text>
              <Text style={styles.partnerName}>{status.partner_name || '—'}</Text>

              {status.compatibility_score != null && (
                <View style={styles.scoreRow}>
                  <Text style={styles.scoreLabel}>{L(lang, 'compat_score')}</Text>
                  <ScoreRing score={status.compatibility_score} />
                </View>
              )}

              <TouchableOpacity
                accessibilityRole="button"
                accessibilityLabel="L(lang, 'view_report')"
                style={styles.primaryBtn}
                onPress={() => (navigation.navigate as any)('CompatibilityReport')}
                activeOpacity={0.85}
              >
                <Text style={styles.primaryBtnText}>{L(lang, 'view_report')}</Text>
              </TouchableOpacity>

              <TouchableOpacity style={styles.disconnectBtn} onPress={handleDisconnect} activeOpacity={0.8}
                accessibilityRole="button"
                accessibilityLabel="L(lang, 'disconnect')"
              >
                <Text style={styles.disconnectBtnText}>{L(lang, 'disconnect')}</Text>
              </TouchableOpacity>
            </View>
          )}

          {/* Privacy note */}
          <View style={styles.privacyCard}>
            <Text style={styles.privacyText}>{L(lang, 'privacy_note')}</Text>
          </View>
        </ScrollView>
      )}
    </View>
  );
};

const styles = StyleSheet.create({
  container:    { flex: 1, backgroundColor: colors.background },
  scroll:       { paddingHorizontal: spacing.lg, paddingBottom: 60 },
  center:       { flex: 1, alignItems: 'center', justifyContent: 'center', gap: spacing.md },
  loadingText:  { ...typography.body, color: colors.textMuted },

  header: {
    flexDirection: 'row', alignItems: 'center',
    paddingHorizontal: spacing.md, paddingTop: spacing.md, paddingBottom: spacing.sm,
    borderBottomWidth: 1, borderBottomColor: colors.border,
  },
  backBtn:      { width: 40 },
  backText:     { color: colors.gold, fontSize: 22 },
  headerCenter: { flex: 1, alignItems: 'center' },
  title:        { ...typography.h2, fontSize: 18 },
  subtitle:     { ...typography.caption, color: colors.textMuted, fontSize: 11 },

  heroWrap:  { alignItems: 'center', paddingVertical: spacing.xl },
  heroEmoji: { fontSize: 72 },

  section:         { marginBottom: spacing.xl },
  noPartnerTitle:  { ...typography.h2, textAlign: 'center', marginBottom: spacing.sm },
  noPartnerSub:    { ...typography.body, color: colors.textMuted, textAlign: 'center', marginBottom: spacing.xl, fontSize: 13 },

  primaryBtn: {
    backgroundColor: '#E0607A', borderRadius: radius.xl,
    paddingVertical: spacing.md, alignItems: 'center', marginBottom: spacing.md,
  },
  primaryBtnText: { color: '#fff', fontWeight: '700', fontSize: 15, fontFamily: 'System' },

  secondaryBtn: {
    borderWidth: 1, borderColor: colors.borderWarm, borderRadius: radius.xl,
    paddingVertical: spacing.md, alignItems: 'center', marginBottom: spacing.md,
  },
  secondaryBtnText: { color: colors.textPrimary, fontWeight: '600', fontSize: 15, fontFamily: 'System' },

  joinRow:       { flexDirection: 'row', gap: spacing.sm, marginTop: spacing.sm },
  codeInput: {
    flex: 1, backgroundColor: colors.surface, borderRadius: radius.md,
    borderWidth: 1, borderColor: colors.border,
    paddingHorizontal: spacing.md, paddingVertical: spacing.sm,
    color: colors.textPrimary, fontSize: 18, fontWeight: '700',
    textAlign: 'center', letterSpacing: 4, fontFamily: 'System',
  },
  joinActionBtn: {
    backgroundColor: colors.surface, borderRadius: radius.md,
    borderWidth: 1, borderColor: colors.border,
    paddingHorizontal: spacing.md, justifyContent: 'center', minWidth: 64,
  },
  joinActionActive: { backgroundColor: '#E0607A', borderColor: '#E0607A' },
  joinActionText:   { color: '#fff', fontWeight: '700', fontSize: 13, fontFamily: 'System' },

  badgeRow:    { flexDirection: 'row', justifyContent: 'center', marginBottom: spacing.md },
  badge: {
    borderRadius: radius.full, paddingHorizontal: spacing.md, paddingVertical: 4,
  },
  badgePending: { backgroundColor: `${colors.gold}25` },
  badgeActive:  { backgroundColor: '#4CAF5025' },
  badgeText:    { ...typography.caption, fontSize: 11, fontWeight: '700', color: colors.gold, letterSpacing: 1 },

  sectionTitle: { ...typography.h2, textAlign: 'center', marginBottom: spacing.md },

  codeCard: {
    backgroundColor: colors.surface, borderRadius: radius.lg,
    borderWidth: 1, borderColor: `#E0607A30`,
    paddingVertical: spacing.lg, alignItems: 'center', marginBottom: spacing.md,
  },
  codeDisplay: { fontSize: 36, fontWeight: '800', letterSpacing: 8, color: '#E0607A', fontFamily: 'System' },

  copyBtn: {
    borderWidth: 1, borderColor: colors.border, borderRadius: radius.xl,
    paddingVertical: spacing.sm, alignItems: 'center', marginBottom: spacing.md,
  },
  copyBtnText: { ...typography.body, color: colors.textPrimary, fontSize: 13 },

  waitText: { ...typography.body, color: colors.textMuted, textAlign: 'center', fontSize: 12, marginBottom: spacing.xl },

  partnerName: { ...typography.h1, textAlign: 'center', color: '#E0607A', marginBottom: spacing.lg },

  scoreRow:   { alignItems: 'center', marginBottom: spacing.lg, gap: spacing.sm },
  scoreLabel: { ...typography.caption, color: colors.textMuted, fontSize: 12 },

  disconnectBtn: {
    paddingVertical: spacing.sm, alignItems: 'center',
  },
  disconnectBtnText: { color: colors.textMuted, fontSize: 13, fontFamily: 'System' },

  privacyCard: {
    backgroundColor: colors.surface, borderRadius: radius.lg,
    borderWidth: 1, borderColor: colors.border,
    padding: spacing.md, marginBottom: spacing.xl,
  },
  privacyText: { ...typography.caption, color: colors.textMuted, fontSize: 11, textAlign: 'center' },
});

export default PartnerScreen;

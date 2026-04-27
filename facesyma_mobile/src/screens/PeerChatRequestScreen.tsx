// src/screens/PeerChatRequestScreen.tsx
import React, { useState } from 'react';
import {
  View, Text, TouchableOpacity, StyleSheet,
  SafeAreaView, ActivityIndicator, Alert,
} from 'react-native';
import { useNavigation, useRoute } from '@react-navigation/native';
import { PeerChatAPI } from '../services/api';
import type { AppNavProp, ScreenProps } from '../navigation/types';
import theme from '../utils/theme';

const { colors, spacing, typography, radius } = theme;

export default function PeerChatRequestScreen() {
  const nav = useNavigation<AppNavProp>();
  const route = useRoute<ScreenProps<'PeerChatRequest'>['route']>();
  const { requestId, toUserId, toUsername, compatScore, source } = route.params ?? {};

  const [loading, setLoading] = useState(false);

  const handleSendRequest = async () => {
    if (!toUserId) return;
    setLoading(true);
    try {
      const res = await PeerChatAPI.sendRequest(toUserId, compatScore);
      if (res.room_id) {
        // Zaten aktif oda var
        nav.replace('PeerChat', {
          roomId: res.room_id,
          otherUserId: toUserId!,
          otherUsername: toUsername ?? 'Kullanıcı',
          compatScore,
        });
      } else {
        Alert.alert(
          'İstek Gönderildi',
          `${toUsername ?? 'Kullanıcı'} isteğini onayladığında sohbet başlayacak.`,
          [{ text: 'Tamam', onPress: () => nav.goBack() }]
        );
      }
    } catch (err: any) {
      const msg = err?.response?.data?.detail ?? 'İstek gönderilemedi.';
      Alert.alert('Hata', msg);
    } finally {
      setLoading(false);
    }
  };

  const handleRespond = async (action: 'accept' | 'reject') => {
    if (!requestId) return;
    setLoading(true);
    try {
      const res = await PeerChatAPI.respondRequest(requestId, action);
      if (action === 'accept' && res.room_id) {
        nav.replace('PeerChat', {
          roomId: res.room_id,
          otherUserId: toUserId!,
          otherUsername: toUsername ?? 'Kullanıcı',
          compatScore,
        });
      } else {
        nav.goBack();
      }
    } catch (err: any) {
      const msg = err?.response?.data?.detail ?? 'İşlem başarısız.';
      Alert.alert('Hata', msg);
    } finally {
      setLoading(false);
    }
  };

  const isIncoming = !!requestId;
  const username = toUsername ?? 'Kullanıcı';
  const initial = (username[0] ?? '?').toUpperCase();

  return (
    <SafeAreaView style={s.safe}>
      <View style={s.header}>
        <TouchableOpacity onPress={() => nav.goBack()} style={s.backBtn}>
          <Text style={s.backTxt}>←</Text>
        </TouchableOpacity>
        <Text style={s.title}>{isIncoming ? 'Sohbet İsteği' : 'Sohbet Başlat'}</Text>
      </View>

      <View style={s.body}>
        {/* Profil kartı */}
        <View style={s.card}>
          <View style={s.avatar}>
            <Text style={s.avatarTxt}>{initial}</Text>
          </View>
          <Text style={s.username}>{username}</Text>

          {compatScore !== undefined && compatScore > 0 && (
            <View style={s.compatRow}>
              <Text style={s.compatLabel}>Uyum Skoru</Text>
              <Text style={s.compatValue}>%{Math.round(compatScore)}</Text>
            </View>
          )}

          <View style={s.sourceTag}>
            <Text style={s.sourceText}>
              {source === 'community'
                ? '👥 Ortak Topluluk Üyesi'
                : '🔗 Uyumluluk Analizinden'}
            </Text>
          </View>
        </View>

        {/* Açıklama */}
        <View style={s.infoBox}>
          {isIncoming ? (
            <Text style={s.infoText}>
              <Text style={s.infoName}>{username}</Text> seninle sohbet etmek istiyor.
              Kabul edersen iki yönlü sohbet başlayacak.
            </Text>
          ) : (
            <Text style={s.infoText}>
              <Text style={s.infoName}>{username}</Text> adlı kişiye sohbet isteği gönderilecek.
              Karşı taraf kabul ettiğinde sohbet başlayacak.
            </Text>
          )}
        </View>

        {/* Butonlar */}
        {loading ? (
          <ActivityIndicator color={colors.gold} size="large" style={{ marginTop: spacing.xl }} />
        ) : isIncoming ? (
          <View style={s.btnRow}>
            <TouchableOpacity
              style={[s.btn, s.btnReject]}
              onPress={() => handleRespond('reject')}
            >
              <Text style={s.btnRejectTxt}>Reddet</Text>
            </TouchableOpacity>
            <TouchableOpacity
              style={[s.btn, s.btnAccept]}
              onPress={() => handleRespond('accept')}
            >
              <Text style={s.btnAcceptTxt}>Kabul Et</Text>
            </TouchableOpacity>
          </View>
        ) : (
          <TouchableOpacity style={s.btnSend} onPress={handleSendRequest}>
            <Text style={s.btnSendTxt}>İstek Gönder</Text>
          </TouchableOpacity>
        )}
      </View>
    </SafeAreaView>
  );
}

const s = StyleSheet.create({
  safe:          { flex: 1, backgroundColor: colors.background },
  header:        { flexDirection: 'row', alignItems: 'center', paddingHorizontal: spacing.md, paddingVertical: spacing.sm, borderBottomWidth: 1, borderBottomColor: colors.border },
  backBtn:       { padding: spacing.sm, marginRight: spacing.sm },
  backTxt:       { fontSize: 22, color: colors.gold },
  title:         { ...typography.h2, flex: 1 },
  body:          { flex: 1, padding: spacing.lg, alignItems: 'center' },
  card:          { backgroundColor: colors.surface, borderRadius: radius.lg, padding: spacing.xl, alignItems: 'center', width: '100%', marginBottom: spacing.lg, borderWidth: 1, borderColor: colors.border },
  avatar:        { width: 80, height: 80, borderRadius: 40, backgroundColor: colors.goldDark, alignItems: 'center', justifyContent: 'center', marginBottom: spacing.md },
  avatarTxt:     { color: colors.white, fontWeight: '700', fontSize: 32 },
  username:      { ...typography.h2, marginBottom: spacing.md, textAlign: 'center' },
  compatRow:     { flexDirection: 'row', alignItems: 'center', gap: spacing.sm, marginBottom: spacing.sm },
  compatLabel:   { ...typography.caption, color: colors.textSecondary },
  compatValue:   { ...typography.h3, color: colors.gold },
  sourceTag:     { backgroundColor: colors.warmAmberGlow, borderRadius: radius.sm, paddingHorizontal: spacing.md, paddingVertical: 4, borderWidth: 1, borderColor: colors.warmAmber },
  sourceText:    { color: colors.warmAmber, fontSize: 12, fontWeight: '600' },
  infoBox:       { backgroundColor: colors.surfaceWarm, borderRadius: radius.md, padding: spacing.md, width: '100%', marginBottom: spacing.xl },
  infoText:      { ...typography.body, textAlign: 'center', lineHeight: 22 },
  infoName:      { color: colors.gold, fontWeight: '600' },
  btnRow:        { flexDirection: 'row', gap: spacing.md, width: '100%' },
  btn:           { flex: 1, borderRadius: radius.md, paddingVertical: spacing.md, alignItems: 'center' },
  btnReject:     { backgroundColor: colors.surfaceAlt, borderWidth: 1, borderColor: colors.error },
  btnRejectTxt:  { color: colors.error, fontWeight: '700', fontSize: 16 },
  btnAccept:     { backgroundColor: colors.gold },
  btnAcceptTxt:  { color: colors.black, fontWeight: '700', fontSize: 16 },
  btnSend:       { backgroundColor: colors.gold, borderRadius: radius.md, paddingVertical: spacing.md, paddingHorizontal: spacing.xl * 2, alignItems: 'center' },
  btnSendTxt:    { color: colors.black, fontWeight: '700', fontSize: 16 },
});

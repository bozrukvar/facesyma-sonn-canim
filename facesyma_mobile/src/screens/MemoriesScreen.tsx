// src/screens/MemoriesScreen.tsx
import React, { useCallback, useEffect, useState } from 'react';
import {
  View, Text, StyleSheet, FlatList, TouchableOpacity,
  Alert, ActivityIndicator, StatusBar,
} from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { AiChatAPI } from '../services/api';
import type { UserMemory } from '../types/api';
import type { ScreenProps } from '../navigation/types';
import { useLanguage } from '../utils/LanguageContext';

// ── i18n strings ─────────────────────────────────────────────────────────────
const STR: Record<string, Record<string, string>> = {
  title:        { tr: 'Hafızam', en: 'My Memories', de: 'Meine Erinnerungen', ru: 'Мои воспоминания', ar: 'ذكرياتي', es: 'Mis Recuerdos', ko: '나의 기억', ja: '私の記憶', zh: '我的记忆', fr: 'Mes Souvenirs', pt: 'Minhas Memórias', hi: 'मेरी यादें', id: 'Kenangan Saya', it: 'I Miei Ricordi', pl: 'Moje Wspomnienia', bn: 'আমার স্মৃতি', ur: 'میری یادیں', vi: 'Ký Ức Của Tôi' },
  subtitle:     { tr: 'AI koçun seninle önceki konuşmalardan öğrendikleri', en: 'What your AI coach learned from previous chats', de: 'Was dein KI-Coach aus früheren Gesprächen gelernt hat', ru: 'Что ваш ИИ-тренер узнал из прошлых разговоров', ar: 'ما تعلّمه مدربك الذكي من المحادثات السابقة', es: 'Lo que tu coach de IA aprendió de conversaciones anteriores', ko: 'AI 코치가 이전 대화에서 배운 것', ja: 'AIコーチが以前の会話から学んだこと', zh: 'AI教练从之前对话中了解到的', fr: 'Ce que votre coach IA a appris des conversations précédentes', pt: 'O que seu coach de IA aprendeu das conversas anteriores', hi: 'आपके AI कोच ने पिछली बातचीत से क्या सीखा', id: 'Apa yang dipelajari coach AI dari percakapan sebelumnya', it: 'Cosa ha imparato il tuo coach AI dalle conversazioni precedenti', pl: 'Czego nauczył się twój coach AI z poprzednich rozmów', bn: 'আপনার AI কোচ আগের কথোপকথন থেকে কী শিখেছে', ur: 'آپ کے AI کوچ نے پچھلی گفتگو سے کیا سیکھا', vi: 'Những gì AI coach học được từ cuộc trò chuyện trước' },
  empty:        { tr: 'Henüz hafıza kaydı yok.\nAI koçunla konuşmaya başla!', en: 'No memories yet.\nStart chatting with your AI coach!', de: 'Noch keine Erinnerungen.\nChatte mit deinem KI-Coach!', ru: 'Воспоминаний пока нет.\nНачни общаться с ИИ-тренером!', ar: 'لا توجد ذكريات بعد.\nابدأ الحديث مع مدربك الذكي!', es: '¡Aún no hay recuerdos.\nEmpieza a chatear con tu coach IA!', ko: '아직 기억이 없습니다.\nAI 코치와 대화를 시작하세요!', ja: 'まだ記憶がありません。\nAIコーチとチャットを始めましょう！', zh: '还没有记忆。\n开始与AI教练聊天吧！', fr: 'Pas encore de souvenirs.\nCommencez à chatter avec votre coach IA !', pt: 'Nenhuma memória ainda.\nComece a conversar com seu coach IA!', hi: 'अभी कोई यादें नहीं।\nAI कोच से बात करना शुरू करें!', id: 'Belum ada kenangan.\nMulai chat dengan coach AI Anda!', it: 'Nessun ricordo ancora.\nInizia a chattare con il tuo coach IA!', pl: 'Brak wspomnień.\nZacznij rozmawiać ze swoim coachem AI!', bn: 'এখনো কোনো স্মৃতি নেই।\nআপনার AI কোচের সাথে কথা শুরু করুন!', ur: 'ابھی کوئی یادیں نہیں۔\nاپنے AI کوچ سے بات شروع کریں!', vi: 'Chưa có ký ức nào.\nBắt đầu trò chuyện với AI coach của bạn!' },
  delete:       { tr: 'Sil', en: 'Delete', de: 'Löschen', ru: 'Удалить', ar: 'حذف', es: 'Eliminar', ko: '삭제', ja: '削除', zh: '删除', fr: 'Supprimer', pt: 'Excluir', hi: 'हटाएं', id: 'Hapus', it: 'Elimina', pl: 'Usuń', bn: 'মুছুন', ur: 'حذف کریں', vi: 'Xóa' },
  confirm_del:  { tr: 'Bu hafıza kaydını silmek istediğine emin misin?', en: 'Are you sure you want to delete this memory?', de: 'Möchten Sie diese Erinnerung wirklich löschen?', ru: 'Вы уверены, что хотите удалить это воспоминание?', ar: 'هل أنت متأكد من حذف هذه الذاكرة؟', es: '¿Estás seguro de que quieres eliminar este recuerdo?', ko: '이 기억을 삭제하시겠습니까?', ja: 'この記憶を削除しますか？', zh: '您确定要删除这段记忆吗？', fr: 'Êtes-vous sûr de vouloir supprimer ce souvenir ?', pt: 'Tem certeza de que deseja excluir esta memória?', hi: 'क्या आप इस याद को हटाना चाहते हैं?', id: 'Apakah Anda yakin ingin menghapus kenangan ini?', it: 'Sei sicuro di voler eliminare questo ricordo?', pl: 'Czy na pewno chcesz usunąć to wspomnienie?', bn: 'আপনি কি এই স্মৃতি মুছতে চান?', ur: 'کیا آپ یہ یاد حذف کرنا چاہتے ہیں؟', vi: 'Bạn có chắc muốn xóa ký ức này không?' },
  ai_badge:     { tr: 'AI Özet', en: 'AI Summary', de: 'KI-Zusammenfassung', ru: 'ИИ-сводка', ar: 'ملخص ذكاء', es: 'Resumen IA', ko: 'AI 요약', ja: 'AI要約', zh: 'AI摘要', fr: 'Résumé IA', pt: 'Resumo IA', hi: 'AI सारांश', id: 'Ringkasan AI', it: 'Riepilogo IA', pl: 'Podsumowanie AI', bn: 'AI সারসংক্ষেপ', ur: 'AI خلاصہ', vi: 'Tóm tắt AI' },
};

const s = (key: keyof typeof STR, lang: string): string =>
  STR[key]?.[lang] ?? STR[key]?.en ?? key;

const CAT_META: Record<string, { emoji: string; color: string }> = {
  goal:       { emoji: '🎯', color: '#7AE07A' },
  preference: { emoji: '💙', color: '#7AB0E0' },
  emotion:    { emoji: '💛', color: '#F5C842' },
  concern:    { emoji: '🟠', color: '#E0A17A' },
  insight:    { emoji: '💡', color: '#C07AE0' },
};

const MemoriesScreen: React.FC<ScreenProps<'Memories'>> = ({ navigation }) => {
  const insets = useSafeAreaInsets();
  const { lang } = useLanguage();

  const [memories, setMemories] = useState<UserMemory[]>([]);
  const [loading, setLoading]   = useState(true);
  const [deleting, setDeleting] = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const res = await AiChatAPI.getMemories();
      setMemories((res.memories || []).slice().reverse()); // newest first
    } catch {
      setMemories([]);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { load(); }, [load]);

  const handleDelete = useCallback((mem: UserMemory) => {
    Alert.alert(
      s('delete', lang),
      s('confirm_del', lang),
      [
        { text: lang === 'tr' ? 'İptal' : 'Cancel', style: 'cancel' },
        {
          text: s('delete', lang),
          style: 'destructive',
          onPress: async () => {
            setDeleting(mem.id);
            try {
              await AiChatAPI.deleteMemory(mem.id);
              setMemories(prev => prev.filter(m => m.id !== mem.id));
            } finally {
              setDeleting(null);
            }
          },
        },
      ],
    );
  }, [lang]);

  const renderItem = useCallback(({ item }: { item: UserMemory }) => {
    const meta  = CAT_META[item.category] ?? { emoji: '📌', color: '#aaa' };
    const isDel = deleting === item.id;
    return (
      <View style={[st.card, { borderLeftColor: meta.color }]}>
        <View style={st.cardTop}>
          <Text style={st.catEmoji}>{meta.emoji}</Text>
          <Text style={[st.catLabel, { color: meta.color }]}>{item.category}</Text>
          {item.source === 'ai_summary' && (
            <View style={[st.aiBadge, { backgroundColor: meta.color + '33' }]}>
              <Text style={[st.aiBadgeText, { color: meta.color }]}>{s('ai_badge', lang)}</Text>
            </View>
          )}
          <View style={{ flex: 1 }} />
          <TouchableOpacity
            accessibilityRole="button"
            accessibilityLabel="s('delete', lang)"
            onPress={() => handleDelete(item)}
            disabled={isDel}
            hitSlop={{ top: 8, bottom: 8, left: 8, right: 8 }}
          >
            {isDel
              ? <ActivityIndicator size="small" color="#E07A7A" />
              : <Text style={st.delBtn}>{s('delete', lang)}</Text>
            }
          </TouchableOpacity>
        </View>
        <Text style={st.content}>{item.content}</Text>
        <Text style={st.date}>{new Date(item.created_at).toLocaleDateString()}</Text>
      </View>
    );
  }, [lang, deleting, handleDelete]);

  return (
    <View style={[st.root, { paddingTop: insets.top }]}>
      <StatusBar barStyle="light-content" backgroundColor="#0A0A1A" />

      {/* Header */}
      <View style={st.header}>
        <TouchableOpacity onPress={() => navigation.goBack()} style={st.back}
          accessibilityRole="button"
          accessibilityLabel="s('title', lang)"
        >
          <Text style={st.backArrow}>←</Text>
        </TouchableOpacity>
        <View style={{ flex: 1 }}>
          <Text style={st.title}>{s('title', lang)}</Text>
          <Text style={st.sub}>{s('subtitle', lang)}</Text>
        </View>
      </View>

      {loading ? (
        <ActivityIndicator style={{ marginTop: 60 }} color="#C07AE0" size="large" />
      ) : memories.length === 0 ? (
        <View style={st.empty}>
          <Text style={st.emptyEmoji}>🧠</Text>
          <Text style={st.emptyText}>{s('empty', lang)}</Text>
        </View>
      ) : (
        <FlatList
          data={memories}
          keyExtractor={item => item.id}
          renderItem={renderItem}
          contentContainerStyle={{ padding: 16, paddingBottom: insets.bottom + 24 }}
          ItemSeparatorComponent={() => <View style={{ height: 10 }} />}
        />
      )}
    </View>
  );
};

const st = StyleSheet.create({
  root:       { flex: 1, backgroundColor: '#0A0A1A' },
  header:     { flexDirection: 'row', alignItems: 'flex-start', paddingHorizontal: 16, paddingVertical: 12, gap: 12 },
  back:       { paddingTop: 2 },
  backArrow:  { fontSize: 22, color: '#C07AE0' },
  title:      { fontSize: 20, fontWeight: '700', color: '#FFFFFF' },
  sub:        { fontSize: 12, color: '#999', marginTop: 2 },
  card:       { backgroundColor: '#14142A', borderRadius: 14, padding: 14, borderLeftWidth: 4 },
  cardTop:    { flexDirection: 'row', alignItems: 'center', gap: 6, marginBottom: 8 },
  catEmoji:   { fontSize: 16 },
  catLabel:   { fontSize: 12, fontWeight: '600', textTransform: 'capitalize' },
  aiBadge:    { paddingHorizontal: 7, paddingVertical: 2, borderRadius: 8 },
  aiBadgeText:{ fontSize: 10, fontWeight: '700' },
  delBtn:     { fontSize: 12, color: '#E07A7A' },
  content:    { fontSize: 14, color: '#E0E0E0', lineHeight: 20 },
  date:       { fontSize: 11, color: '#666', marginTop: 6 },
  empty:      { flex: 1, alignItems: 'center', justifyContent: 'center', padding: 32 },
  emptyEmoji: { fontSize: 48, marginBottom: 16 },
  emptyText:  { fontSize: 15, color: '#888', textAlign: 'center', lineHeight: 22 },
});

export default MemoriesScreen;

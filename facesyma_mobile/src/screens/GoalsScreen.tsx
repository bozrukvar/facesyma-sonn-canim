// src/screens/GoalsScreen.tsx
import React, { useState, useEffect, useCallback } from 'react';
import {
  View, Text, StyleSheet, ScrollView, TouchableOpacity,
  ActivityIndicator, RefreshControl, Modal, TextInput,
  KeyboardAvoidingView, Platform, Alert,
} from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import theme from '../utils/theme';
const { colors, spacing, typography, radius } = theme;
import { useLanguage } from '../utils/LanguageContext';
import { GoalsAPI, type Goal } from '../services/api';
import type { ScreenProps } from '../navigation/types';

type Props = ScreenProps<'Goals'>;

// ── Inline translations ───────────────────────────────────────────────────────
const TR: Record<string, Record<string, string>> = {
  title:        { tr:'Hedeflerim', en:'My Goals', de:'Meine Ziele', ru:'Мои цели', ar:'أهدافي', es:'Mis metas', ko:'내 목표', ja:'目標', zh:'我的目标', hi:'मेरे लक्ष्य', fr:'Mes objectifs', pt:'Meus objetivos', bn:'আমার লক্ষ্য', id:'Tujuan Saya', ur:'میرے اہداف', it:'I miei obiettivi', vi:'Mục tiêu', pl:'Moje cele' },
  subtitle:     { tr:'Assessment sonuçlarını eyleme dönüştür', en:'Turn test results into action', de:'Ergebnisse in Aktionen umsetzen', ru:'Результаты → действия', ar:'حوّل نتائجك إلى أفعال', es:'Convierte resultados en acción', ko:'결과를 행동으로', ja:'結果を行動に', zh:'将结果转化为行动', hi:'परिणामों को कार्यों में बदलें', fr:'Transformez vos résultats', pt:'Transforme resultados em ação', bn:'ফলাফলকে কার্যে রূপান্তর করুন', id:'Ubah hasil menjadi tindakan', ur:'نتائج کو اعمال میں بدلیں', it:'Trasforma i risultati in azioni', vi:'Biến kết quả thành hành động', pl:'Zamień wyniki w działania' },
  new_goal:     { tr:'Yeni Hedef', en:'New Goal', de:'Neues Ziel', ru:'Новая цель', ar:'هدف جديد', es:'Nueva meta', ko:'새 목표', ja:'新しい目標', zh:'新目标', hi:'नया लक्ष्य', fr:'Nouvel objectif', pt:'Nova meta', bn:'নতুন লক্ষ্য', id:'Tujuan Baru', ur:'نیا ہدف', it:'Nuovo obiettivo', vi:'Mục tiêu mới', pl:'Nowy cel' },
  empty:        { tr:'Henüz aktif hedef yok. Yeni bir hedef ekle!', en:'No active goals yet. Add one!', de:'Noch keine Ziele. Füge eines hinzu!', ru:'Нет активных целей', ar:'لا أهداف نشطة بعد', es:'No hay metas activas aún', ko:'활성 목표 없음', ja:'アクティブな目標なし', zh:'还没有活跃目标', hi:'कोई सक्रिय लक्ष्य नहीं', fr:'Aucun objectif actif', pt:'Nenhum objetivo ativo', bn:'কোনো সক্রিয় লক্ষ্য নেই', id:'Belum ada tujuan aktif', ur:'کوئی فعال ہدف نہیں', it:'Nessun obiettivo attivo', vi:'Chưa có mục tiêu', pl:'Brak aktywnych celów' },
  progress:     { tr:'İlerleme', en:'Progress', de:'Fortschritt', ru:'Прогресс', ar:'التقدم', es:'Progreso', ko:'진행', ja:'進捗', zh:'进度', hi:'प्रगति', fr:'Progrès', pt:'Progresso', bn:'অগ্রগতি', id:'Kemajuan', ur:'ترقی', it:'Progresso', vi:'Tiến độ', pl:'Postęp' },
  deadline:     { tr:'Hedef tarih', en:'Deadline', de:'Frist', ru:'Срок', ar:'الموعد النهائي', es:'Plazo', ko:'마감일', ja:'期限', zh:'截止日期', hi:'समय-सीमा', fr:'Échéance', pt:'Prazo', bn:'সময়সীমা', id:'Tenggat waktu', ur:'آخری تاریخ', it:'Scadenza', vi:'Hạn chót', pl:'Termin' },
  completed:    { tr:'Tamamlandı', en:'Completed', de:'Abgeschlossen', ru:'Завершено', ar:'مكتمل', es:'Completado', ko:'완료', ja:'完了', zh:'已完成', hi:'पूर्ण', fr:'Terminé', pt:'Concluído', bn:'সম্পন্ন', id:'Selesai', ur:'مکمل', it:'Completato', vi:'Hoàn thành', pl:'Ukończono' },
  abandoned:    { tr:'Bırakıldı', en:'Abandoned', de:'Aufgegeben', ru:'Отменено', ar:'متروك', es:'Abandonado', ko:'포기', ja:'放棄', zh:'已放弃', hi:'छोड़ दिया', fr:'Abandonné', pt:'Abandonado', bn:'পরিত্যক্ত', id:'Ditinggalkan', ur:'ترک کردہ', it:'Abbandonato', vi:'Từ bỏ', pl:'Porzucone' },
  create_title: { tr:'Hedef Başlığı', en:'Goal Title', de:'Ziel-Titel', ru:'Название цели', ar:'عنوان الهدف', es:'Título del objetivo', ko:'목표 제목', ja:'目標タイトル', zh:'目标标题', hi:'लक्ष्य शीर्षक', fr:'Titre de l\'objectif', pt:'Título do objetivo', bn:'লক্ষ্যের শিরোনাম', id:'Judul tujuan', ur:'ہدف کا عنوان', it:'Titolo obiettivo', vi:'Tiêu đề mục tiêu', pl:'Tytuł celu' },
  create_test:  { tr:'Test Tipi', en:'Test Type', de:'Testtyp', ru:'Тип теста', ar:'نوع الاختبار', es:'Tipo de prueba', ko:'테스트 유형', ja:'テスト種類', zh:'测试类型', hi:'परीक्षण प्रकार', fr:'Type de test', pt:'Tipo de teste', bn:'টেস্টের ধরন', id:'Jenis tes', ur:'ٹیسٹ کی قسم', it:'Tipo di test', vi:'Loại bài kiểm tra', pl:'Typ testu' },
  create_target:{ tr:'Hedef Skor (1-100)', en:'Target Score (1-100)', de:'Zielpunktzahl (1-100)', ru:'Целевой балл (1-100)', ar:'الدرجة المستهدفة (1-100)', es:'Puntuación objetivo (1-100)', ko:'목표 점수 (1-100)', ja:'目標スコア (1-100)', zh:'目标分数 (1-100)', hi:'लक्ष्य स्कोर (1-100)', fr:'Score cible (1-100)', pt:'Pontuação alvo (1-100)', bn:'লক্ষ্য স্কোর (১-১০০)', id:'Skor target (1-100)', ur:'ہدف سکور (1-100)', it:'Punteggio target (1-100)', vi:'Điểm mục tiêu (1-100)', pl:'Wynik docelowy (1-100)' },
  create_curr:  { tr:'Mevcut Skor (opsiyonel)', en:'Current Score (optional)', de:'Aktueller Score (optional)', ru:'Текущий балл (необяз.)', ar:'الدرجة الحالية (اختياري)', es:'Puntuación actual (opcional)', ko:'현재 점수 (선택)', ja:'現在のスコア (任意)', zh:'当前分数（可选）', hi:'वर्तमान स्कोर (वैकल्पिक)', fr:'Score actuel (optionnel)', pt:'Pontuação atual (opcional)', bn:'বর্তমান স্কোর (ঐচ্ছিক)', id:'Skor saat ini (opsional)', ur:'موجودہ سکور (اختیاری)', it:'Punteggio attuale (facoltativo)', vi:'Điểm hiện tại (tùy chọn)', pl:'Aktualny wynik (opcjonalny)' },
  create_dl:    { tr:'Bitiş Tarihi (YYYY-AA-GG)', en:'Deadline (YYYY-MM-DD)', de:'Frist (JJJJ-MM-TT)', ru:'Срок (ГГГГ-ММ-ДД)', ar:'الموعد النهائي (YYYY-MM-DD)', es:'Fecha límite (AAAA-MM-DD)', ko:'마감일 (YYYY-MM-DD)', ja:'期限 (YYYY-MM-DD)', zh:'截止日期 (YYYY-MM-DD)', hi:'समय-सीमा (YYYY-MM-DD)', fr:'Échéance (AAAA-MM-JJ)', pt:'Prazo (AAAA-MM-DD)', bn:'শেষ তারিখ (YYYY-MM-DD)', id:'Tenggat (YYYY-MM-DD)', ur:'آخری تاریخ (YYYY-MM-DD)', it:'Scadenza (AAAA-MM-GG)', vi:'Hạn chót (YYYY-MM-DD)', pl:'Termin (RRRR-MM-DD)' },
  save:         { tr:'Kaydet', en:'Save', de:'Speichern', ru:'Сохранить', ar:'حفظ', es:'Guardar', ko:'저장', ja:'保存', zh:'保存', hi:'सहेजें', fr:'Enregistrer', pt:'Salvar', bn:'সংরক্ষণ', id:'Simpan', ur:'محفوظ کریں', it:'Salva', vi:'Lưu', pl:'Zapisz' },
  cancel:       { tr:'İptal', en:'Cancel', de:'Abbrechen', ru:'Отмена', ar:'إلغاء', es:'Cancelar', ko:'취소', ja:'キャンセル', zh:'取消', hi:'रद्द करें', fr:'Annuler', pt:'Cancelar', bn:'বাতিল', id:'Batal', ur:'منسوخ', it:'Annulla', vi:'Hủy', pl:'Anuluj' },
  view_all:     { tr:'Tümünü Gör', en:'View All', de:'Alle ansehen', ru:'Все', ar:'عرض الكل', es:'Ver todo', ko:'전체 보기', ja:'すべて見る', zh:'查看全部', hi:'सभी देखें', fr:'Voir tout', pt:'Ver tudo', bn:'সব দেখুন', id:'Lihat semua', ur:'سب دیکھیں', it:'Vedi tutto', vi:'Xem tất cả', pl:'Pokaż wszystkie' },
};
const tl = (k: string, l: string) => TR[k]?.[l] ?? TR[k]?.en ?? k;

const TEST_TYPE_LABELS: Record<string, string> = {
  personality:'🧠 Kişilik', skills:'🎯 Beceriler', hr:'👥 İK', career:'💼 Kariyer',
  relationship:'❤️ İlişki', vocation:'🏢 Meslek', attachment:'🔗 Bağlanma',
  grit:'💪 Kararlılık', growth_mindset:'🌱 Büyüme Zihniyeti', life_satisfaction:'😊 Yaşam Doyumu',
  self_compassion:'🌸 Öz-şefkat', body_image:'🪞 Beden İmajı', self_efficacy:'⚡ Öz-yeterlik',
  stress:'🧘 Stres', finance:'💰 Finans', finance_anxiety:'😰 Finans Kaygısı',
};

const TEST_TYPES = Object.keys(TEST_TYPE_LABELS);

const scoreColor = (pct: number) => {
  if (pct >= 70) return '#4CAF50';
  if (pct >= 40) return '#FFC107';
  return '#F44336';
};

const statusBadgeColor = (status: string) => {
  if (status === 'completed') return '#4CAF50';
  if (status === 'abandoned') return '#9E9E9E';
  return colors.gold;
};

// ── Goal Card ─────────────────────────────────────────────────────────────────
const GoalCard: React.FC<{ goal: Goal; lang: string; onPress: () => void }> = ({ goal, lang, onPress }) => {
  const gap   = goal.target_score - goal.current_score;
  const pct   = goal.target_score > 0
    ? Math.min(100, Math.round((goal.current_score / goal.target_score) * 100))
    : 0;
  const tasksDone  = goal.weekly_tasks.filter(t => t.done).length;
  const tasksTotal = goal.weekly_tasks.length;
  const barColor   = scoreColor(pct);

  return (
    <TouchableOpacity style={styles.goalCard} onPress={onPress} activeOpacity={0.85}
      accessibilityRole="button"
      accessibilityLabel={goal.title}
    >
      <View style={styles.goalCardHeader}>
        <Text style={styles.goalTitle} numberOfLines={2}>{goal.title}</Text>
        {goal.status !== 'active' && (
          <View style={[styles.statusBadge, { backgroundColor: statusBadgeColor(goal.status) + '22' }]}>
            <Text style={[styles.statusBadgeText, { color: statusBadgeColor(goal.status) }]}>
              {tl(goal.status, lang)}
            </Text>
          </View>
        )}
      </View>
      <Text style={styles.goalTestType}>{TEST_TYPE_LABELS[goal.test_type] ?? goal.test_type}</Text>

      {/* Progress bar */}
      <View style={styles.progressRow}>
        <Text style={styles.progressLabel}>{goal.current_score} → {goal.target_score}</Text>
        <Text style={[styles.progressPct, { color: barColor }]}>{pct}%</Text>
      </View>
      <View style={styles.barBg}>
        <View style={[styles.barFill, { width: `${pct}%` as any, backgroundColor: barColor }]} />
      </View>

      {/* Tasks + deadline */}
      <View style={styles.goalMeta}>
        <Text style={styles.goalMetaText}>✅ {tasksDone}/{tasksTotal} {tl('progress', lang)}</Text>
        {goal.deadline ? (
          <Text style={styles.goalMetaText}>📅 {goal.deadline}</Text>
        ) : null}
      </View>
    </TouchableOpacity>
  );
};

// ── Main Screen ───────────────────────────────────────────────────────────────
export default function GoalsScreen({ navigation }: Props) {
  const insets = useSafeAreaInsets();
  const { lang } = useLanguage();
  const [goals, setGoals]           = useState<Goal[]>([]);
  const [loading, setLoading]       = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [showModal, setShowModal]   = useState(false);
  const [saving, setSaving]         = useState(false);
  const [filterStatus, setFilterStatus] = useState<'active' | 'all'>('active');

  // Form state
  const [fTitle,    setFTitle]    = useState('');
  const [fTestType, setFTestType] = useState(TEST_TYPES[0]);
  const [fTarget,   setFTarget]   = useState('');
  const [fCurrent,  setFCurrent]  = useState('');
  const [fDeadline, setFDeadline] = useState('');

  const load = useCallback(async () => {
    try {
      const res = await GoalsAPI.list(filterStatus);
      setGoals(res.goals ?? []);
    } catch {
      // silent
    }
  }, [filterStatus]);

  useEffect(() => {
    load().finally(() => setLoading(false));
  }, [load]);

  const onRefresh = useCallback(async () => {
    setRefreshing(true);
    await load();
    setRefreshing(false);
  }, [load]);

  const resetForm = () => {
    setFTitle(''); setFTestType(TEST_TYPES[0]);
    setFTarget(''); setFCurrent(''); setFDeadline('');
  };

  const handleCreate = async () => {
    if (!fTitle.trim()) return;
    const target = parseInt(fTarget, 10);
    if (isNaN(target) || target < 1 || target > 100) {
      Alert.alert('', lang === 'tr' ? 'Hedef skor 1-100 arasında olmalı.' : 'Target score must be 1-100.');
      return;
    }
    setSaving(true);
    try {
      await GoalsAPI.create({
        title:         fTitle.trim(),
        test_type:     fTestType,
        target_score:  target,
        current_score: parseInt(fCurrent, 10) || 0,
        deadline:      fDeadline || undefined,
      });
      resetForm();
      setShowModal(false);
      await load();
    } catch {
      Alert.alert('', lang === 'tr' ? 'Kayıt başarısız.' : 'Save failed.');
    } finally {
      setSaving(false);
    }
  };

  return (
    <View style={[styles.container, { paddingTop: insets.top }]}>
      {/* Header */}
      <View style={styles.header}>
        <TouchableOpacity onPress={() => navigation.goBack()} style={styles.backBtn}
          accessibilityRole="button"
          accessibilityLabel="tl('title', lang)"
        >
          <Text style={styles.backText}>←</Text>
        </TouchableOpacity>
        <View style={styles.headerBody}>
          <Text style={styles.headerTitle}>{tl('title', lang)}</Text>
          <Text style={styles.headerSub}>{tl('subtitle', lang)}</Text>
        </View>
        <TouchableOpacity style={styles.newBtn} onPress={() => setShowModal(true)}
          accessibilityRole="button"
          accessibilityLabel='+'
        >
          <Text style={styles.newBtnText}>+</Text>
        </TouchableOpacity>
      </View>

      {/* Filter tabs */}
      <View style={styles.filterRow}>
        {(['active', 'all'] as const).map(s => (
          <TouchableOpacity
            accessibilityRole="button"
            accessibilityLabel='Filter Tab'
            key={s}
            style={[styles.filterTab, filterStatus === s && styles.filterTabActive]}
            onPress={() => setFilterStatus(s)}
          >
            <Text style={[styles.filterTabText, filterStatus === s && styles.filterTabTextActive]}>
              {s === 'active' ? (lang === 'tr' ? 'Aktif' : 'Active') : tl('view_all', lang)}
            </Text>
          </TouchableOpacity>
        ))}
      </View>

      {loading ? (
        <View style={styles.loadingWrap}>
          <ActivityIndicator color={colors.gold} />
        </View>
      ) : (
        <ScrollView
          contentContainerStyle={styles.scroll}
          refreshControl={<RefreshControl refreshing={refreshing} onRefresh={onRefresh} tintColor={colors.gold} />}
          showsVerticalScrollIndicator={false}
        >
          {goals.length === 0 ? (
            <View style={styles.empty}>
              <Text style={styles.emptyEmoji}>🎯</Text>
              <Text style={styles.emptyText}>{tl('empty', lang)}</Text>
              <TouchableOpacity style={styles.emptyBtn} onPress={() => setShowModal(true)}
                accessibilityRole="button"
                accessibilityLabel="+ tl('new_goal', lang)"
              >
                <Text style={styles.emptyBtnText}>+ {tl('new_goal', lang)}</Text>
              </TouchableOpacity>
            </View>
          ) : (
            goals.map(g => (
              <GoalCard
                key={g.goal_id}
                goal={g}
                lang={lang}
                onPress={() => navigation.navigate('GoalDetail', { goalId: g.goal_id, goalTitle: g.title })}
              />
            ))
          )}
          <View style={{ height: insets.bottom + spacing.xl }} />
        </ScrollView>
      )}

      {/* Create Goal Modal */}
      <Modal visible={showModal} transparent animationType="slide">
        <KeyboardAvoidingView behavior={Platform.OS === 'ios' ? 'padding' : undefined} style={styles.modalOverlay}>
          <View style={styles.modalBox}>
            <Text style={styles.modalTitle}>🎯 {tl('new_goal', lang)}</Text>

            <TextInput
              style={styles.input}
              placeholder={tl('create_title', lang)}
              placeholderTextColor={colors.textMuted}
              value={fTitle}
              onChangeText={setFTitle}
            />

            {/* Test type picker (horizontal scroll) */}
            <Text style={styles.inputLabel}>{tl('create_test', lang)}</Text>
            <ScrollView horizontal showsHorizontalScrollIndicator={false} style={styles.typeScroll}>
              {TEST_TYPES.map(tt => (
                <TouchableOpacity
                  accessibilityRole="button"
                  accessibilityLabel='TEST_TYPE_LABELS[tt]'
                  key={tt}
                  style={[styles.typeChip, fTestType === tt && styles.typeChipSelected]}
                  onPress={() => setFTestType(tt)}
                >
                  <Text style={[styles.typeChipText, fTestType === tt && styles.typeChipTextSelected]}>
                    {TEST_TYPE_LABELS[tt]}
                  </Text>
                </TouchableOpacity>
              ))}
            </ScrollView>

            <TextInput
              style={styles.input}
              placeholder={tl('create_target', lang)}
              placeholderTextColor={colors.textMuted}
              keyboardType="numeric"
              value={fTarget}
              onChangeText={setFTarget}
            />
            <TextInput
              style={styles.input}
              placeholder={tl('create_curr', lang)}
              placeholderTextColor={colors.textMuted}
              keyboardType="numeric"
              value={fCurrent}
              onChangeText={setFCurrent}
            />
            <TextInput
              style={styles.input}
              placeholder={tl('create_dl', lang)}
              placeholderTextColor={colors.textMuted}
              value={fDeadline}
              onChangeText={setFDeadline}
            />

            <View style={styles.modalBtns}>
              <TouchableOpacity
                accessibilityRole="button"
                accessibilityLabel="tl('cancel', lang)"
                style={styles.cancelBtn}
                onPress={() => { setShowModal(false); resetForm(); }}
              >
                <Text style={styles.cancelBtnText}>{tl('cancel', lang)}</Text>
              </TouchableOpacity>
              <TouchableOpacity style={styles.saveBtn} onPress={handleCreate} disabled={saving}
                accessibilityRole="button"
                accessibilityLabel="tl('save', lang)"
              >
                {saving
                  ? <ActivityIndicator color="#1A1A2E" size="small" />
                  : <Text style={styles.saveBtnText}>{tl('save', lang)}</Text>
                }
              </TouchableOpacity>
            </View>
          </View>
        </KeyboardAvoidingView>
      </Modal>
    </View>
  );
}

const styles = StyleSheet.create({
  container:     { flex: 1, backgroundColor: colors.background },
  loadingWrap:   { flex: 1, alignItems: 'center', justifyContent: 'center' },

  header: {
    flexDirection: 'row', alignItems: 'center',
    paddingHorizontal: spacing.lg, paddingVertical: spacing.md,
    borderBottomWidth: 1, borderBottomColor: colors.border,
  },
  backBtn:    { padding: spacing.sm, marginRight: spacing.sm },
  backText:   { ...typography.h2, color: colors.textPrimary },
  headerBody: { flex: 1 },
  headerTitle:{ ...typography.h2 },
  headerSub:  { ...typography.caption, marginTop: 2 },
  newBtn: {
    width: 36, height: 36, borderRadius: 18,
    backgroundColor: colors.gold,
    alignItems: 'center', justifyContent: 'center',
  },
  newBtnText: { color: '#1A1A2E', fontSize: 22, fontWeight: '700', lineHeight: 26 },

  filterRow: {
    flexDirection: 'row',
    paddingHorizontal: spacing.lg,
    paddingVertical: spacing.sm,
    gap: spacing.sm,
  },
  filterTab: {
    paddingHorizontal: 16, paddingVertical: 6,
    borderRadius: radius.full,
    borderWidth: 1.5, borderColor: colors.border,
  },
  filterTabActive: { borderColor: colors.gold, backgroundColor: colors.gold + '18' },
  filterTabText:   { ...typography.caption, color: colors.textMuted },
  filterTabTextActive: { color: colors.gold, fontWeight: '700' },

  scroll: { paddingHorizontal: spacing.lg, paddingTop: spacing.sm },

  goalCard: {
    backgroundColor: colors.surface,
    borderRadius: 16,
    borderWidth: 1, borderColor: colors.border,
    padding: spacing.md,
    marginBottom: spacing.md,
  },
  goalCardHeader: {
    flexDirection: 'row', alignItems: 'flex-start',
    justifyContent: 'space-between', marginBottom: 4,
  },
  goalTitle:     { ...typography.h3, flex: 1, marginRight: spacing.sm },
  goalTestType:  { ...typography.caption, color: colors.textMuted, marginBottom: spacing.sm },
  statusBadge: {
    borderRadius: 8, paddingHorizontal: 8, paddingVertical: 3,
  },
  statusBadgeText: { fontSize: 11, fontWeight: '700' },

  progressRow: {
    flexDirection: 'row', justifyContent: 'space-between',
    alignItems: 'center', marginBottom: 6,
  },
  progressLabel: { ...typography.caption, color: colors.textMuted },
  progressPct:   { ...typography.label, fontSize: 13 },
  barBg:  { height: 6, backgroundColor: colors.border, borderRadius: 3, marginBottom: spacing.sm },
  barFill:{ height: 6, borderRadius: 3 },

  goalMeta:     { flexDirection: 'row', justifyContent: 'space-between', marginTop: 4 },
  goalMetaText: { ...typography.caption, color: colors.textMuted },

  empty:       { alignItems: 'center', paddingVertical: spacing.xxl },
  emptyEmoji:  { fontSize: 48, marginBottom: spacing.md },
  emptyText:   { ...typography.body, textAlign: 'center', marginBottom: spacing.lg, color: colors.textMuted },
  emptyBtn: {
    backgroundColor: colors.gold,
    borderRadius: radius.xl,
    paddingHorizontal: spacing.xl, paddingVertical: 12,
  },
  emptyBtnText: { color: '#1A1A2E', fontWeight: '700', fontSize: 15 },

  // Modal
  modalOverlay: {
    flex: 1, backgroundColor: 'rgba(0,0,0,0.6)',
    justifyContent: 'flex-end',
  },
  modalBox: {
    backgroundColor: colors.surface,
    borderTopLeftRadius: 24, borderTopRightRadius: 24,
    padding: spacing.lg,
    paddingBottom: spacing.xxl,
  },
  modalTitle: { ...typography.h2, marginBottom: spacing.lg, textAlign: 'center' },
  inputLabel: { ...typography.caption, color: colors.textMuted, marginBottom: 6, marginTop: spacing.sm },
  input: {
    backgroundColor: colors.background,
    borderRadius: 12, borderWidth: 1, borderColor: colors.border,
    color: colors.textPrimary,
    paddingHorizontal: 14, paddingVertical: 12,
    fontSize: 14, marginBottom: 10,
  },
  typeScroll:  { marginBottom: 10 },
  typeChip: {
    paddingHorizontal: 12, paddingVertical: 6,
    borderRadius: 20, borderWidth: 1.5, borderColor: colors.border,
    marginRight: 8,
  },
  typeChipSelected: { borderColor: colors.gold, backgroundColor: colors.gold + '18' },
  typeChipText:     { color: colors.textMuted, fontSize: 13 },
  typeChipTextSelected: { color: colors.gold, fontWeight: '700' },

  modalBtns: { flexDirection: 'row', gap: 10, marginTop: spacing.md },
  cancelBtn: {
    flex: 1, borderWidth: 1.5, borderColor: colors.border,
    borderRadius: 12, paddingVertical: 13, alignItems: 'center',
  },
  cancelBtnText: { color: colors.textMuted, fontSize: 15 },
  saveBtn: {
    flex: 2, backgroundColor: colors.gold,
    borderRadius: 12, paddingVertical: 13, alignItems: 'center',
  },
  saveBtnText: { color: '#1A1A2E', fontWeight: '700', fontSize: 15 },
});

// src/screens/GoalDetailScreen.tsx
import React, { useState, useEffect, useCallback } from 'react';
import {
  View, Text, StyleSheet, ScrollView, TouchableOpacity,
  ActivityIndicator, RefreshControl, Alert,
} from 'react-native';
import Svg, { Circle } from 'react-native-svg';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import theme from '../utils/theme';
const { colors, spacing, typography, radius } = theme;
import { useLanguage } from '../utils/LanguageContext';
import { GoalsAPI, type Goal, type WeeklyTask } from '../services/api';
import type { ScreenProps } from '../navigation/types';

type Props = ScreenProps<'GoalDetail'>;

const TR: Record<string, Record<string, string>> = {
  tasks:      { tr:'Haftalık Görevler', en:'Weekly Tasks', de:'Wöchentliche Aufgaben', ru:'Еженедельные задачи', ar:'المهام الأسبوعية', es:'Tareas semanales', ko:'주간 과제', ja:'週次タスク', zh:'每周任务', hi:'साप्ताहिक कार्य', fr:'Tâches hebdomadaires', pt:'Tarefas semanais', bn:'সাপ্তাহিক কাজ', id:'Tugas mingguan', ur:'ہفتہ وار کام', it:'Attività settimanali', vi:'Nhiệm vụ hàng tuần', pl:'Zadania tygodniowe' },
  week:       { tr:'Hafta', en:'Week', de:'Woche', ru:'Неделя', ar:'أسبوع', es:'Semana', ko:'주', ja:'週', zh:'周', hi:'सप्ताह', fr:'Semaine', pt:'Semana', bn:'সপ্তাহ', id:'Minggu', ur:'ہفتہ', it:'Settimana', vi:'Tuần', pl:'Tydzień' },
  mark_done:  { tr:'Tamamla', en:'Mark done', de:'Erledigt', ru:'Выполнено', ar:'إنجاز', es:'Completar', ko:'완료', ja:'完了', zh:'完成', hi:'पूर्ण करें', fr:'Terminer', pt:'Concluir', bn:'সম্পন্ন', id:'Tandai selesai', ur:'مکمل کریں', it:'Segna fatto', vi:'Đánh dấu xong', pl:'Oznacz jako wykonane' },
  complete_goal: { tr:'Hedefi Tamamla', en:'Complete Goal', de:'Ziel abschließen', ru:'Завершить цель', ar:'إكمال الهدف', es:'Completar meta', ko:'목표 완료', ja:'目標達成', zh:'完成目标', hi:'लक्ष्य पूरा करें', fr:'Objectif atteint', pt:'Concluir meta', bn:'লক্ষ্য সম্পন্ন', id:'Selesaikan tujuan', ur:'ہدف مکمل', it:'Completa obiettivo', vi:'Hoàn thành mục tiêu', pl:'Ukończ cel' },
  abandon:    { tr:'Hedeften Vazgeç', en:'Abandon Goal', de:'Ziel aufgeben', ru:'Отказаться', ar:'التخلي عن الهدف', es:'Abandonar meta', ko:'목표 포기', ja:'目標を諦める', zh:'放弃目标', hi:'लक्ष्य छोड़ें', fr:'Abandonner l\'objectif', pt:'Abandonar meta', bn:'লক্ষ্য ত্যাগ করুন', id:'Tinggalkan tujuan', ur:'ہدف چھوڑیں', it:'Abbandona obiettivo', vi:'Từ bỏ mục tiêu', pl:'Porzuć cel' },
  progress:   { tr:'İlerleme', en:'Progress', de:'Fortschritt', ru:'Прогресс', ar:'التقدم', es:'Progreso', ko:'진행', ja:'進捗', zh:'进度', hi:'प्रगति', fr:'Progrès', pt:'Progresso', bn:'অগ্রগতি', id:'Kemajuan', ur:'ترقی', it:'Progresso', vi:'Tiến độ', pl:'Postęp' },
  current:    { tr:'Mevcut', en:'Current', de:'Aktuell', ru:'Текущий', ar:'الحالي', es:'Actual', ko:'현재', ja:'現在', zh:'当前', hi:'वर्तमान', fr:'Actuel', pt:'Atual', bn:'বর্তমান', id:'Saat ini', ur:'موجودہ', it:'Attuale', vi:'Hiện tại', pl:'Aktualny' },
  target:     { tr:'Hedef', en:'Target', de:'Ziel', ru:'Цель', ar:'الهدف', es:'Objetivo', ko:'목표', ja:'目標', zh:'目标', hi:'लक्ष्य', fr:'Cible', pt:'Meta', bn:'লক্ষ্য', id:'Target', ur:'ہدف', it:'Target', vi:'Mục tiêu', pl:'Cel' },
  deadline:   { tr:'Bitiş', en:'Deadline', de:'Frist', ru:'Срок', ar:'الموعد', es:'Plazo', ko:'마감', ja:'期限', zh:'截止', hi:'समय-सीमा', fr:'Échéance', pt:'Prazo', bn:'সময়সীমা', id:'Tenggat', ur:'آخری تاریخ', it:'Scadenza', vi:'Hạn', pl:'Termin' },
  confirm_complete: { tr:'Hedefi tamamlandı olarak işaret etmek istiyor musun?', en:'Mark this goal as completed?', de:'Ziel als abgeschlossen markieren?', ru:'Отметить цель как выполненную?', ar:'هل تريد وضع علامة اكتمال على هذا الهدف؟', es:'¿Marcar esta meta como completada?', ko:'이 목표를 완료로 표시하시겠습니까?', ja:'この目標を完了にしますか？', zh:'将此目标标记为已完成？', hi:'इस लक्ष्य को पूर्ण के रूप में चिह्नित करें?', fr:'Marquer cet objectif comme atteint ?', pt:'Marcar meta como concluída?', bn:'এই লক্ষ্য সম্পন্ন হিসেবে চিহ্নিত করবেন?', id:'Tandai tujuan ini sebagai selesai?', ur:'اس ہدف کو مکمل کے طور پر نشان لگائیں؟', it:'Contrassegnare questo obiettivo come completato?', vi:'Đánh dấu mục tiêu này là hoàn thành?', pl:'Oznaczyć cel jako ukończony?' },
  confirm_abandon: { tr:'Bu hedeften vazgeçmek istiyor musun?', en:'Abandon this goal?', de:'Dieses Ziel aufgeben?', ru:'Отказаться от цели?', ar:'هل تريد التخلي عن هذا الهدف؟', es:'¿Abandonar esta meta?', ko:'이 목표를 포기하시겠습니까?', ja:'この目標を諦めますか？', zh:'放弃这个目标？', hi:'इस लक्ष्य को छोड़ें?', fr:'Abandonner cet objectif ?', pt:'Abandonar esta meta?', bn:'এই লক্ষ্য ত্যাগ করবেন?', id:'Tinggalkan tujuan ini?', ur:'اس ہدف سے دستبردار ہوں؟', it:'Abbandonare questo obiettivo?', vi:'Từ bỏ mục tiêu này?', pl:'Porzucić cel?' },
  yes:        { tr:'Evet', en:'Yes', de:'Ja', ru:'Да', ar:'نعم', es:'Sí', ko:'네', ja:'はい', zh:'是', hi:'हाँ', fr:'Oui', pt:'Sim', bn:'হ্যাঁ', id:'Ya', ur:'ہاں', it:'Sì', vi:'Có', pl:'Tak' },
  no:         { tr:'Hayır', en:'No', de:'Nein', ru:'Нет', ar:'لا', es:'No', ko:'아니요', ja:'いいえ', zh:'否', hi:'नहीं', fr:'Non', pt:'Não', bn:'না', id:'Tidak', ur:'نہیں', it:'No', vi:'Không', pl:'Nie' },
};
const tl = (k: string, l: string) => TR[k]?.[l] ?? TR[k]?.en ?? k;

// ── Circular progress ring ─────────────────────────────────────────────────
const RING_R = 54;
const RING_STROKE = 8;
const RING_SIZE = (RING_R + RING_STROKE) * 2;
const RING_CIRC = 2 * Math.PI * RING_R;

const ProgressRing: React.FC<{ pct: number; color: string; label: string }> = ({ pct, color, label }) => {
  const offset = RING_CIRC * (1 - Math.min(1, pct / 100));
  return (
    <View style={styles.ringWrap}>
      <Svg width={RING_SIZE} height={RING_SIZE}>
        <Circle
          cx={RING_SIZE / 2} cy={RING_SIZE / 2} r={RING_R}
          stroke={colors.border} strokeWidth={RING_STROKE} fill="none"
        />
        <Circle
          cx={RING_SIZE / 2} cy={RING_SIZE / 2} r={RING_R}
          stroke={color} strokeWidth={RING_STROKE} fill="none"
          strokeDasharray={RING_CIRC}
          strokeDashoffset={offset}
          strokeLinecap="round"
          rotation="-90"
          origin={`${RING_SIZE / 2}, ${RING_SIZE / 2}`}
        />
      </Svg>
      <View style={styles.ringCenter}>
        <Text style={[styles.ringPct, { color }]}>{pct}%</Text>
        <Text style={styles.ringLabel}>{label}</Text>
      </View>
    </View>
  );
};

// ── Task row ──────────────────────────────────────────────────────────────────
const TaskRow: React.FC<{
  task: WeeklyTask; lang: string;
  onToggle: (id: number, done: boolean) => void;
  toggling: boolean;
}> = ({ task, lang, onToggle, toggling }) => (
  <TouchableOpacity
    style={[styles.taskRow, task.done && styles.taskRowDone]}
    onPress={() => !toggling && onToggle(task.id, !task.done)}
    activeOpacity={0.75}
  >
    <View style={[styles.taskCheck, task.done && styles.taskCheckDone]}>
      {task.done && <Text style={styles.taskCheckMark}>✓</Text>}
    </View>
    <View style={styles.taskBody}>
      <Text style={styles.taskWeek}>{tl('week', lang)} {task.week}</Text>
      <Text style={[styles.taskText, task.done && styles.taskTextDone]}>{task.text}</Text>
    </View>
    {toggling && <ActivityIndicator size="small" color={colors.gold} />}
  </TouchableOpacity>
);

// ── Main Screen ───────────────────────────────────────────────────────────────
export default function GoalDetailScreen({ navigation, route }: Props) {
  const insets = useSafeAreaInsets();
  const { lang } = useLanguage();
  const { goalId } = route.params;

  const [goal, setGoal]         = useState<Goal | null>(null);
  const [loading, setLoading]   = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [toggling, setToggling] = useState<number | null>(null);

  const load = useCallback(async () => {
    try {
      const res = await GoalsAPI.get(goalId);
      setGoal(res.goal);
    } catch {
      // silent
    }
  }, [goalId]);

  useEffect(() => {
    load().finally(() => setLoading(false));
  }, [load]);

  const onRefresh = useCallback(async () => {
    setRefreshing(true);
    await load();
    setRefreshing(false);
  }, [load]);

  const toggleTask = useCallback(async (taskId: number, done: boolean) => {
    setToggling(taskId);
    try {
      const res = await GoalsAPI.update(goalId, { task_id: taskId, done });
      setGoal(res.goal);
    } catch {
      // silent
    } finally {
      setToggling(null);
    }
  }, [goalId]);

  const confirmStatusChange = (newStatus: 'completed' | 'abandoned') => {
    const msgKey = newStatus === 'completed' ? 'confirm_complete' : 'confirm_abandon';
    Alert.alert('', tl(msgKey, lang), [
      { text: tl('no', lang), style: 'cancel' },
      {
        text: tl('yes', lang),
        style: newStatus === 'abandoned' ? 'destructive' : 'default',
        onPress: async () => {
          try {
            const res = await GoalsAPI.update(goalId, { status: newStatus });
            setGoal(res.goal);
          } catch { /* silent */ }
        },
      },
    ]);
  };

  if (loading) {
    return (
      <View style={[styles.container, { paddingTop: insets.top }, styles.center]}>
        <ActivityIndicator color={colors.gold} />
      </View>
    );
  }

  if (!goal) {
    return (
      <View style={[styles.container, { paddingTop: insets.top }, styles.center]}>
        <Text style={styles.errorText}>Goal not found.</Text>
      </View>
    );
  }

  const pct = goal.target_score > 0
    ? Math.min(100, Math.round((goal.current_score / goal.target_score) * 100))
    : 0;
  const ringColor = pct >= 70 ? '#4CAF50' : pct >= 40 ? '#FFC107' : '#F44336';
  const tasksDone = goal.weekly_tasks.filter(t => t.done).length;
  const isActive  = goal.status === 'active';

  return (
    <View style={[styles.container, { paddingTop: insets.top }]}>
      {/* Header */}
      <View style={styles.header}>
        <TouchableOpacity onPress={() => navigation.goBack()} style={styles.backBtn}>
          <Text style={styles.backText}>←</Text>
        </TouchableOpacity>
        <Text style={styles.headerTitle} numberOfLines={2}>{goal.title}</Text>
      </View>

      <ScrollView
        contentContainerStyle={styles.scroll}
        refreshControl={<RefreshControl refreshing={refreshing} onRefresh={onRefresh} tintColor={colors.gold} />}
        showsVerticalScrollIndicator={false}
      >
        {/* Progress ring + stats */}
        <View style={styles.statsCard}>
          <ProgressRing pct={pct} color={ringColor} label={tl('progress', lang)} />
          <View style={styles.statsRight}>
            <View style={styles.statItem}>
              <Text style={styles.statLabel}>{tl('current', lang)}</Text>
              <Text style={[styles.statValue, { color: ringColor }]}>{goal.current_score}</Text>
            </View>
            <View style={styles.statItem}>
              <Text style={styles.statLabel}>{tl('target', lang)}</Text>
              <Text style={[styles.statValue, { color: colors.gold }]}>{goal.target_score}</Text>
            </View>
            <View style={styles.statItem}>
              <Text style={styles.statLabel}>✅</Text>
              <Text style={styles.statValue}>{tasksDone}/{goal.weekly_tasks.length}</Text>
            </View>
            {goal.deadline ? (
              <View style={styles.statItem}>
                <Text style={styles.statLabel}>{tl('deadline', lang)}</Text>
                <Text style={styles.statValue}>{goal.deadline}</Text>
              </View>
            ) : null}
          </View>
        </View>

        {/* Status banner for non-active goals */}
        {!isActive && (
          <View style={[styles.statusBanner, { backgroundColor: goal.status === 'completed' ? '#4CAF5022' : '#9E9E9E22' }]}>
            <Text style={[styles.statusBannerText, { color: goal.status === 'completed' ? '#4CAF50' : '#9E9E9E' }]}>
              {goal.status === 'completed' ? `🎉 ${lang === 'tr' ? 'Tamamlandı' : 'Completed'}` : `😔 ${lang === 'tr' ? 'Bırakıldı' : 'Abandoned'}`}
            </Text>
          </View>
        )}

        {/* Weekly tasks */}
        <Text style={styles.sectionTitle}>{tl('tasks', lang)}</Text>
        {goal.weekly_tasks.map(task => (
          <TaskRow
            key={task.id}
            task={task}
            lang={lang}
            onToggle={toggleTask}
            toggling={toggling === task.id}
          />
        ))}

        {/* Action buttons (active goals only) */}
        {isActive && (
          <View style={styles.actionBtns}>
            <TouchableOpacity
              style={styles.completeBtn}
              onPress={() => confirmStatusChange('completed')}
            >
              <Text style={styles.completeBtnText}>🎉 {tl('complete_goal', lang)}</Text>
            </TouchableOpacity>
            <TouchableOpacity
              style={styles.abandonBtn}
              onPress={() => confirmStatusChange('abandoned')}
            >
              <Text style={styles.abandonBtnText}>{tl('abandon', lang)}</Text>
            </TouchableOpacity>
          </View>
        )}

        <View style={{ height: insets.bottom + spacing.xl }} />
      </ScrollView>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: colors.background },
  center:    { alignItems: 'center', justifyContent: 'center' },
  errorText: { color: colors.textMuted },

  header: {
    flexDirection: 'row', alignItems: 'center',
    paddingHorizontal: spacing.lg, paddingVertical: spacing.md,
    borderBottomWidth: 1, borderBottomColor: colors.border,
  },
  backBtn:     { padding: spacing.sm, marginRight: spacing.sm },
  backText:    { ...typography.h2, color: colors.textPrimary },
  headerTitle: { ...typography.h2, flex: 1 },

  scroll: { paddingHorizontal: spacing.lg, paddingTop: spacing.md },

  statsCard: {
    backgroundColor: colors.surface,
    borderRadius: 20, borderWidth: 1, borderColor: colors.border,
    padding: spacing.lg,
    flexDirection: 'row', alignItems: 'center',
    marginBottom: spacing.lg,
    gap: spacing.lg,
  },
  ringWrap:   { position: 'relative', alignItems: 'center', justifyContent: 'center' },
  ringCenter: { position: 'absolute', alignItems: 'center' },
  ringPct:    { fontSize: 20, fontWeight: '800' },
  ringLabel:  { fontSize: 10, color: colors.textMuted, marginTop: 2 },
  statsRight: { flex: 1, gap: 10 },
  statItem:   { flexDirection: 'row', justifyContent: 'space-between' },
  statLabel:  { ...typography.caption, color: colors.textMuted },
  statValue:  { ...typography.label, fontSize: 13, color: colors.textPrimary },

  statusBanner: {
    borderRadius: 12, padding: spacing.md,
    marginBottom: spacing.lg, alignItems: 'center',
  },
  statusBannerText: { fontSize: 15, fontWeight: '700' },

  sectionTitle: { ...typography.h3, marginBottom: spacing.md },

  taskRow: {
    flexDirection: 'row', alignItems: 'flex-start',
    backgroundColor: colors.surface,
    borderRadius: 14, borderWidth: 1, borderColor: colors.border,
    padding: spacing.md, marginBottom: spacing.sm, gap: spacing.sm,
  },
  taskRowDone: { opacity: 0.6 },
  taskCheck: {
    width: 24, height: 24, borderRadius: 12,
    borderWidth: 2, borderColor: colors.border,
    alignItems: 'center', justifyContent: 'center',
    marginTop: 2,
  },
  taskCheckDone: { backgroundColor: colors.gold, borderColor: colors.gold },
  taskCheckMark: { color: '#1A1A2E', fontSize: 13, fontWeight: '900' },
  taskBody:  { flex: 1 },
  taskWeek:  { ...typography.caption, color: colors.gold, marginBottom: 3 },
  taskText:  { ...typography.body, fontSize: 14 },
  taskTextDone: { textDecorationLine: 'line-through', color: colors.textMuted },

  actionBtns: { gap: spacing.sm, marginTop: spacing.lg },
  completeBtn: {
    backgroundColor: '#4CAF50',
    borderRadius: radius.xl, paddingVertical: 14,
    alignItems: 'center',
  },
  completeBtnText: { color: '#fff', fontWeight: '700', fontSize: 15 },
  abandonBtn: {
    backgroundColor: 'transparent',
    borderRadius: radius.xl, paddingVertical: 12,
    alignItems: 'center',
    borderWidth: 1.5, borderColor: colors.border,
  },
  abandonBtnText: { color: colors.textMuted, fontSize: 14 },
});

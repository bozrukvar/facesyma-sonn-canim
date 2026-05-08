import React, { useEffect, useState } from 'react';
import {
  View, Text, StyleSheet, TouchableOpacity, ScrollView,
} from 'react-native';
import theme from '../utils/theme';
const { colors, spacing, typography, radius } = theme;
import { GoalsAPI, type Goal } from '../services/api';

const LABELS: Record<string, { title: string; see_all: string; active: string }> = {
  tr: { title: 'Aktif Hedeflerim', see_all: 'Tümü →', active: 'aktif' },
  en: { title: 'Active Goals',     see_all: 'All →',  active: 'active' },
  de: { title: 'Aktive Ziele',     see_all: 'Alle →', active: 'aktiv' },
  ru: { title: 'Активные цели',    see_all: 'Все →',  active: 'актив' },
  ar: { title: 'الأهداف النشطة',   see_all: 'الكل →', active: 'نشط' },
  es: { title: 'Metas activas',    see_all: 'Todo →', active: 'activo' },
  ko: { title: '활성 목표',         see_all: '전체 →', active: '활성' },
  ja: { title: 'アクティブな目標',   see_all: 'すべて →', active: 'アクティブ' },
  zh: { title: '活跃目标',          see_all: '全部 →', active: '活跃' },
  hi: { title: 'सक्रिय लक्ष्य',   see_all: 'सभी →',  active: 'सक्रिय' },
  fr: { title: 'Objectifs actifs', see_all: 'Tout →', active: 'actif' },
  pt: { title: 'Metas ativas',     see_all: 'Tudo →', active: 'ativo' },
  bn: { title: 'সক্রিয় লক্ষ্য',  see_all: 'সব →',   active: 'সক্রিয়' },
  id: { title: 'Tujuan aktif',     see_all: 'Semua →', active: 'aktif' },
  ur: { title: 'فعال اہداف',      see_all: 'سب →',   active: 'فعال' },
  it: { title: 'Obiettivi attivi', see_all: 'Tutti →', active: 'attivo' },
  vi: { title: 'Mục tiêu đang hoạt động', see_all: 'Tất cả →', active: 'đang hoạt động' },
  pl: { title: 'Aktywne cele',     see_all: 'Wszystko →', active: 'aktywny' },
};
const L = (lang: string) => LABELS[lang] ?? LABELS.en;

interface Props {
  lang: string;
  onGoalPress: (goalId: string, goalTitle: string) => void;
  onViewAll: () => void;
}

export default function ActiveGoalsWidget({ lang, onGoalPress, onViewAll }: Props) {
  const [goals, setGoals] = useState<Goal[]>([]);

  useEffect(() => {
    GoalsAPI.list('active')
      .then(r => setGoals((r.goals ?? []).slice(0, 3)))
      .catch(() => {});
  }, []);

  if (goals.length === 0) return null;

  const lb = L(lang);

  return (
    <View style={styles.wrap}>
      <View style={styles.rowHeader}>
        <Text style={styles.sectionLabel}>🎯 {lb.title}</Text>
        <TouchableOpacity onPress={onViewAll}>
          <Text style={styles.seeAll}>{lb.see_all}</Text>
        </TouchableOpacity>
      </View>
      <ScrollView
        horizontal
        showsHorizontalScrollIndicator={false}
        contentContainerStyle={styles.row}
      >
        {goals.map(g => {
          const pct = g.target_score > 0
            ? Math.min(100, Math.round((g.current_score / g.target_score) * 100))
            : 0;
          const barColor = pct >= 70 ? '#4CAF50' : pct >= 40 ? '#FFC107' : '#F44336';
          const tasksDone  = g.weekly_tasks.filter(t => t.done).length;
          const tasksTotal = g.weekly_tasks.length;
          return (
            <TouchableOpacity
              key={g.goal_id}
              style={styles.card}
              onPress={() => onGoalPress(g.goal_id, g.title)}
              activeOpacity={0.85}
            >
              <Text style={styles.cardTitle} numberOfLines={2}>{g.title}</Text>
              <View style={styles.barBg}>
                <View style={[styles.barFill, { width: `${pct}%` as any, backgroundColor: barColor }]} />
              </View>
              <View style={styles.cardMeta}>
                <Text style={[styles.cardPct, { color: barColor }]}>{pct}%</Text>
                <Text style={styles.cardTasks}>✅ {tasksDone}/{tasksTotal}</Text>
              </View>
            </TouchableOpacity>
          );
        })}
      </ScrollView>
    </View>
  );
}

const CARD_W = 180;

const styles = StyleSheet.create({
  wrap:        { marginBottom: spacing.sm },
  rowHeader:   { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', paddingHorizontal: spacing.lg, marginBottom: spacing.sm },
  sectionLabel:{ ...typography.label, color: colors.textPrimary, fontSize: 13 },
  seeAll:      { ...typography.caption, color: colors.gold, fontWeight: '600' },
  row:         { paddingHorizontal: spacing.lg, gap: spacing.sm },
  card: {
    width: CARD_W,
    backgroundColor: colors.surface,
    borderRadius: 14, borderWidth: 1, borderColor: colors.border,
    padding: spacing.md,
  },
  cardTitle:  { ...typography.label, fontSize: 13, marginBottom: spacing.sm, lineHeight: 18 },
  barBg:      { height: 5, backgroundColor: colors.border, borderRadius: 3, marginBottom: 6 },
  barFill:    { height: 5, borderRadius: 3 },
  cardMeta:   { flexDirection: 'row', justifyContent: 'space-between' },
  cardPct:    { fontSize: 12, fontWeight: '700' },
  cardTasks:  { ...typography.caption, fontSize: 11 },
});

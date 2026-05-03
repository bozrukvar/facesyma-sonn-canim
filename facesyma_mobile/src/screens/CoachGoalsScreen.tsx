// src/screens/CoachGoalsScreen.tsx
import React, { useEffect, useState, useCallback } from 'react';
import {
  View, Text, StyleSheet, FlatList, TouchableOpacity,
  ActivityIndicator, StatusBar, Modal, TextInput, Alert,
} from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { useSelector } from 'react-redux';
import { RootState } from '../store';
import { CoachAPI } from '../services/api';
import theme from '../utils/theme';
import { useLanguage } from '../utils/LanguageContext';
import { t } from '../utils/i18n';
import type { ScreenProps } from '../navigation/types';

const { colors, spacing, typography, radius, shadow } = theme;

type Props = ScreenProps<'CoachGoals'>;

interface Goal {
  id: string;
  title: string;
  module: string;
  status: string;
  priority: string;
  target_date?: string;
}

const STATUS_COLOR: Record<string, string> = {
  aktif:    colors.gold,
  active:   colors.gold,
  completed:'#7AE07A',
  tamamlandi:'#7AE07A',
  paused:   '#7AAEE0',
  beklemede:'#7AAEE0',
  failed:   '#E07A7A',
  cancelled:'#888',
};

const PRIORITY_EMOJI: Record<string, string> = {
  düşük: '🟢', low: '🟢',
  orta: '🟡',  medium: '🟡',
  yüksek: '🔴', high: '🔴',
};

const CoachGoalsScreen: React.FC<Props> = ({ navigation }) => {
  const insets   = useSafeAreaInsets();
  const { lang } = useLanguage();
  const user     = useSelector((s: RootState) => s.auth.user);

  const [goals,   setGoals]   = useState<Goal[]>([]);
  const [loading, setLoading] = useState(true);
  const [tab,     setTab]     = useState<'all' | 'active' | 'completed'>('all');
  const [modal,   setModal]   = useState(false);
  const [saving,  setSaving]  = useState(false);

  // Add goal form
  const [newTitle,    setNewTitle]    = useState('');
  const [newPriority, setNewPriority] = useState<'düşük' | 'orta' | 'yüksek'>('orta');

  const loadGoals = useCallback(async () => {
    if (!user?.id) return;
    setLoading(true);
    try {
      const statusParam = tab === 'active' ? 'aktif' : tab === 'completed' ? 'tamamlandi' : undefined;
      const res = await CoachAPI.getGoals(user.id, statusParam);
      setGoals(res.goals ?? []);
    } catch {
      setGoals([]);
    } finally {
      setLoading(false);
    }
  }, [user?.id, tab]);

  useEffect(() => { loadGoals(); }, [loadGoals]);

  const handleAddGoal = async () => {
    if (!newTitle.trim()) return;
    setSaving(true);
    try {
      await CoachAPI.addGoal({ title: newTitle.trim(), priority: newPriority });
      setModal(false);
      setNewTitle('');
      setNewPriority('orta');
      loadGoals();
    } catch {
      Alert.alert('', t('common.error', lang));
    } finally {
      setSaving(false);
    }
  };

  const handleComplete = async (goal: Goal) => {
    try {
      await CoachAPI.updateGoal(goal.id, 'completed');
      loadGoals();
    } catch {
      Alert.alert('', t('common.error', lang));
    }
  };

  const TABS = [
    { key: 'all',       label: t('coach.status_all', lang) },
    { key: 'active',    label: t('coach.status_active', lang) },
    { key: 'completed', label: t('coach.status_completed', lang) },
  ] as const;

  const renderGoal = ({ item }: { item: Goal }) => (
    <View style={styles.goalCard}>
      <View style={styles.goalTop}>
        <Text style={styles.goalPriority}>{PRIORITY_EMOJI[item.priority] ?? '⚪'}</Text>
        <Text style={styles.goalTitle} numberOfLines={2}>{item.title}</Text>
        <View style={[styles.statusBadge, { backgroundColor: `${STATUS_COLOR[item.status] ?? colors.border}28` }]}>
          <Text style={[styles.statusText, { color: STATUS_COLOR[item.status] ?? colors.textMuted }]}>
            {item.status}
          </Text>
        </View>
      </View>
      {item.target_date && (
        <Text style={styles.goalDate}>📅 {item.target_date}</Text>
      )}
      {(item.status === 'aktif' || item.status === 'active') && (
        <TouchableOpacity style={styles.completeBtn} onPress={() => handleComplete(item)} activeOpacity={0.8}>
          <Text style={styles.completeBtnText}>✓ {t('coach.status_completed', lang)}</Text>
        </TouchableOpacity>
      )}
    </View>
  );

  return (
    <View style={styles.container}>
      <StatusBar barStyle="light-content" />
      <View style={[styles.topBar, { paddingTop: insets.top + spacing.sm }]}>
        <TouchableOpacity onPress={() => navigation.goBack()} style={styles.backBtn}>
          <Text style={styles.backArrow}>←</Text>
        </TouchableOpacity>
        <Text style={styles.topTitle}>{t('coach.goals_title', lang)}</Text>
        <TouchableOpacity style={styles.addBtn} onPress={() => setModal(true)} activeOpacity={0.85}>
          <Text style={styles.addBtnText}>+</Text>
        </TouchableOpacity>
      </View>

      {/* Tabs */}
      <View style={styles.tabs}>
        {TABS.map((tb) => (
          <TouchableOpacity
            key={tb.key}
            style={[styles.tab, tab === tb.key && styles.tabActive]}
            onPress={() => setTab(tb.key)}
            activeOpacity={0.85}
          >
            <Text style={[styles.tabText, tab === tb.key && styles.tabTextActive]}>
              {tb.label}
            </Text>
          </TouchableOpacity>
        ))}
      </View>

      {loading ? (
        <View style={styles.center}>
          <ActivityIndicator color={colors.gold} />
        </View>
      ) : goals.length === 0 ? (
        <View style={styles.center}>
          <Text style={styles.emptyEmoji}>🎯</Text>
          <Text style={styles.emptyText}>{t('coach.no_goals', lang)}</Text>
          <TouchableOpacity style={styles.emptyAddBtn} onPress={() => setModal(true)} activeOpacity={0.85}>
            <Text style={styles.emptyAddBtnText}>+ {t('coach.add_goal', lang)}</Text>
          </TouchableOpacity>
        </View>
      ) : (
        <FlatList
          data={goals}
          keyExtractor={(g) => g.id}
          renderItem={renderGoal}
          contentContainerStyle={styles.list}
          showsVerticalScrollIndicator={false}
        />
      )}

      {/* Add Goal Modal */}
      <Modal visible={modal} transparent animationType="slide" onRequestClose={() => setModal(false)}>
        <View style={styles.modalOverlay}>
          <View style={styles.modalSheet}>
            <Text style={styles.modalTitle}>{t('coach.add_goal', lang)}</Text>

            <Text style={styles.fieldLabel}>{t('coach.goal_title_label', lang)}</Text>
            <TextInput
              style={styles.input}
              value={newTitle}
              onChangeText={setNewTitle}
              placeholder={t('coach.goal_title_label', lang)}
              placeholderTextColor={colors.textMuted}
              maxLength={120}
            />

            <Text style={styles.fieldLabel}>{t('coach.goal_priority_medium', lang)}</Text>
            <View style={styles.priorityRow}>
              {(['düşük', 'orta', 'yüksek'] as const).map((p) => (
                <TouchableOpacity
                  key={p}
                  style={[styles.priorityChip, newPriority === p && styles.priorityChipActive]}
                  onPress={() => setNewPriority(p)}
                  activeOpacity={0.85}
                >
                  <Text style={[styles.priorityChipText, newPriority === p && styles.priorityChipTextActive]}>
                    {p === 'düşük' ? t('coach.goal_priority_low', lang) :
                     p === 'orta'  ? t('coach.goal_priority_medium', lang) :
                                     t('coach.goal_priority_high', lang)}
                  </Text>
                </TouchableOpacity>
              ))}
            </View>

            <View style={styles.modalActions}>
              <TouchableOpacity style={styles.cancelBtn} onPress={() => setModal(false)} activeOpacity={0.85}>
                <Text style={styles.cancelBtnText}>{t('common.cancel', lang)}</Text>
              </TouchableOpacity>
              <TouchableOpacity
                style={[styles.saveBtn, saving && styles.saveBtnDisabled]}
                onPress={handleAddGoal}
                disabled={saving || !newTitle.trim()}
                activeOpacity={0.85}
              >
                {saving ? <ActivityIndicator color="#000" size="small" />
                        : <Text style={styles.saveBtnText}>{t('coach.goal_save', lang)}</Text>}
              </TouchableOpacity>
            </View>
          </View>
        </View>
      </Modal>
    </View>
  );
};

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: colors.background },

  topBar: {
    flexDirection:  'row', alignItems: 'center',
    paddingHorizontal: spacing.lg,
    paddingBottom:  spacing.md,
    gap:            spacing.md,
  },
  backBtn: {
    width: 40, height: 40, borderRadius: radius.full,
    backgroundColor: colors.surface,
    alignItems: 'center', justifyContent: 'center',
    ...shadow.sm,
  },
  backArrow: { ...typography.h2, color: colors.textPrimary, fontSize: 20 },
  topTitle: { ...typography.h2, flex: 1 },
  addBtn: {
    width: 40, height: 40, borderRadius: radius.full,
    backgroundColor: colors.gold,
    alignItems: 'center', justifyContent: 'center',
  },
  addBtnText: { fontSize: 24, color: '#000', fontWeight: '700', lineHeight: 26 },

  // Tabs
  tabs: {
    flexDirection: 'row', gap: spacing.sm,
    paddingHorizontal: spacing.lg, marginBottom: spacing.md,
  },
  tab: {
    flex: 1, paddingVertical: spacing.sm,
    borderRadius: radius.full, borderWidth: 1,
    borderColor: colors.border, alignItems: 'center',
  },
  tabActive: { backgroundColor: colors.gold, borderColor: colors.gold },
  tabText: { ...typography.label, color: colors.textMuted, fontSize: 11 },
  tabTextActive: { color: '#000' },

  // List
  list: { paddingHorizontal: spacing.lg, paddingBottom: spacing.xxxl },
  goalCard: {
    backgroundColor: colors.surface,
    borderRadius:    radius.lg,
    borderWidth:     1,
    borderColor:     colors.border,
    padding:         spacing.md,
    marginBottom:    spacing.sm,
    ...shadow.sm,
  },
  goalTop: { flexDirection: 'row', alignItems: 'flex-start', gap: spacing.sm },
  goalPriority: { fontSize: 16, marginTop: 2 },
  goalTitle: { ...typography.body, flex: 1, fontWeight: '600' },
  statusBadge: {
    borderRadius: radius.full,
    paddingHorizontal: spacing.sm,
    paddingVertical: 3,
  },
  statusText: { fontFamily: 'System', fontSize: 10, fontWeight: '700' },
  goalDate: { ...typography.caption, color: colors.textMuted, marginTop: spacing.sm, fontSize: 11 },
  completeBtn: {
    alignSelf:    'flex-start',
    marginTop:    spacing.sm,
    backgroundColor: `${colors.gold}20`,
    borderRadius: radius.full,
    borderWidth:  1,
    borderColor:  colors.gold,
    paddingHorizontal: spacing.md,
    paddingVertical: 5,
  },
  completeBtnText: { ...typography.label, color: colors.gold, fontSize: 11 },

  // Empty
  center: { flex: 1, alignItems: 'center', justifyContent: 'center', gap: spacing.md },
  emptyEmoji: { fontSize: 40 },
  emptyText:  { ...typography.body, color: colors.textMuted },
  emptyAddBtn: {
    backgroundColor: colors.gold, borderRadius: radius.full,
    paddingHorizontal: spacing.xl, paddingVertical: spacing.sm,
  },
  emptyAddBtnText: { ...typography.goldLabel, color: '#000' },

  // Modal
  modalOverlay: {
    flex: 1, backgroundColor: 'rgba(0,0,0,0.7)',
    justifyContent: 'flex-end',
  },
  modalSheet: {
    backgroundColor: colors.surface,
    borderTopLeftRadius: radius.xxl,
    borderTopRightRadius: radius.xxl,
    padding: spacing.xl,
    paddingBottom: spacing.xxxl,
    gap: spacing.md,
  },
  modalTitle: { ...typography.h2, marginBottom: spacing.sm },
  fieldLabel: { ...typography.goldLabel, fontSize: 11 },
  input: {
    backgroundColor: colors.background,
    borderRadius:    radius.md,
    borderWidth:     1,
    borderColor:     colors.border,
    padding:         spacing.md,
    ...typography.body,
    color:           colors.textPrimary,
  },
  priorityRow: { flexDirection: 'row', gap: spacing.sm },
  priorityChip: {
    flex: 1, paddingVertical: spacing.sm,
    borderRadius: radius.full, borderWidth: 1,
    borderColor: colors.border, alignItems: 'center',
  },
  priorityChipActive: { backgroundColor: colors.gold, borderColor: colors.gold },
  priorityChipText: { ...typography.label, color: colors.textMuted, fontSize: 12 },
  priorityChipTextActive: { color: '#000' },
  modalActions: { flexDirection: 'row', gap: spacing.sm, marginTop: spacing.sm },
  cancelBtn: {
    flex: 1, paddingVertical: spacing.md,
    borderRadius: radius.lg, borderWidth: 1,
    borderColor: colors.border, alignItems: 'center',
  },
  cancelBtnText: { ...typography.body, color: colors.textMuted },
  saveBtn: {
    flex: 1, paddingVertical: spacing.md,
    borderRadius: radius.lg,
    backgroundColor: colors.gold, alignItems: 'center',
  },
  saveBtnDisabled: { opacity: 0.5 },
  saveBtnText: { ...typography.goldLabel, color: '#000' },
});

export default CoachGoalsScreen;

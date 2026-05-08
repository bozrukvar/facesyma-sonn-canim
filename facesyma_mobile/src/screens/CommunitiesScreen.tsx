// src/screens/CommunitiesScreen.tsx
import React, { useState, useEffect, useCallback } from 'react';
import {
  View, Text, StyleSheet, FlatList, TouchableOpacity,
  ActivityIndicator, Alert, RefreshControl, ScrollView,
} from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import theme from '../utils/theme';
const { colors, spacing, typography, radius, shadow } = theme;
import { useLanguage } from '../utils/LanguageContext';
import { t } from '../utils/i18n';
import { AnalysisAPI, CommunityItem } from '../services/api';
import type { ScreenProps } from '../navigation/types';

const TYPE_FILTERS = [
  { key: undefined,    labelKey: 'community.filter_all'       },
  { key: 'TRAIT',      labelKey: 'community.filter_trait'     },
  { key: 'MODULE',     labelKey: 'community.filter_module'    },
  { key: 'CATEGORY',   labelKey: 'community.filter_category'  },
  { key: 'ASTRO',      labelKey: 'community.filter_astro'     },
  { key: 'INTEREST',   labelKey: 'community.filter_interest'  },
  { key: 'LIFESTYLE',  labelKey: 'community.filter_lifestyle' },
  { key: 'GOAL',       labelKey: 'community.filter_goal'      },
];

const CommunitiesScreen = ({ navigation, route }: ScreenProps<'Communities'>) => {
  const insets    = useSafeAreaInsets();
  const { lang }  = useLanguage();

  const initialType = route.params?.communityType ?? undefined;

  const [communities, setCommunities] = useState<CommunityItem[]>([]);
  const [loading,     setLoading]     = useState(true);
  const [refreshing,  setRefreshing]  = useState(false);
  const [typeFilter,  setTypeFilter]  = useState<string | undefined>(undefined);
  const [joined,      setJoined]      = useState<Set<string>>(new Set());
  const [joining,     setJoining]     = useState<string | null>(null);
  const [membersOpen, setMembersOpen] = useState<string | null>(null);
  const [members,     setMembers]     = useState<any[]>([]);
  const [membersLoading, setMembersLoading] = useState(false);

  // If navigated with a communityType hint, highlight matching communities
  const highlightName = initialType ?? '';

  const load = useCallback(async (isRefresh = false) => {
    if (isRefresh) setRefreshing(true); else setLoading(true);
    try {
      const res = await AnalysisAPI.listCommunities(typeFilter, 50);
      setCommunities(res.data ?? []);
    } catch {
      if (!isRefresh) Alert.alert(t('common.error', lang), t('common.generic_error', lang));
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, [typeFilter, lang]);

  useEffect(() => { load(); }, [load]);

  const handleJoin = async (item: CommunityItem) => {
    if (joined.has(item._id)) return;
    setJoining(item._id);
    try {
      await AnalysisAPI.joinCommunity(item._id);
      setJoined(prev => new Set([...prev, item._id]));
    } catch (e: any) {
      const msg = e?.response?.data?.detail ?? t('common.generic_error', lang);
      Alert.alert(t('common.error', lang), msg);
    } finally {
      setJoining(null);
    }
  };

  const handleOpenMembers = async (communityId: string) => {
    if (membersOpen === communityId) { setMembersOpen(null); return; }
    setMembersOpen(communityId);
    setMembersLoading(true);
    try {
      const res = await AnalysisAPI.getCommunityMembers(communityId, 30);
      setMembers(res.data ?? []);
    } catch {
      setMembers([]);
    } finally {
      setMembersLoading(false);
    }
  };

  const renderItem = ({ item }: { item: CommunityItem }) => {
    const isJoined   = joined.has(item._id) || !!item.is_member;
    const isJoining  = joining === item._id;
    const isHighlight = highlightName && item.name.toLowerCase().includes(highlightName.toLowerCase());
    const showMembers = membersOpen === item._id;

    return (
      <View style={[styles.card, isHighlight ? styles.cardHighlight : null]}>
        {isHighlight && (
          <View style={styles.matchBadge}>
            <Text style={styles.matchBadgeText}>✨ {t('community.suggested', lang)}</Text>
          </View>
        )}
        <View style={styles.cardHeader}>
          <Text style={styles.communityName}>{item.name}</Text>
          <View style={styles.memberPill}>
            <Text style={styles.memberCount}>👥 {item.member_count.toLocaleString()}</Text>
          </View>
        </View>
        {item.description ? (
          <Text style={styles.communityDesc} numberOfLines={2}>{item.description}</Text>
        ) : null}
        {item.trait_name ? (
          <View style={styles.traitTag}>
            <Text style={styles.traitTagText}>#{item.trait_name}</Text>
          </View>
        ) : null}
        <View style={styles.cardBtnRow}>
          <TouchableOpacity
            accessibilityRole="button"
            accessibilityLabel='isJoined'
            style={[styles.joinBtn, isJoined && styles.joinBtnDone, { flex: 1 }]}
            onPress={() => handleJoin(item)}
            disabled={isJoined || isJoining}
            activeOpacity={0.85}
          >
            {isJoining ? (
              <ActivityIndicator color="#000" size="small" />
            ) : (
              <Text style={[styles.joinBtnText, isJoined && styles.joinBtnTextDone]}>
                {isJoined
                  ? `✓ ${t('community.joined', lang)}`
                  : t('community.join', lang)}
              </Text>
            )}
          </TouchableOpacity>
          {isJoined && (
            <TouchableOpacity
              accessibilityRole="button"
              accessibilityLabel={t('community.meet', lang)}
              style={styles.meetBtn}
              onPress={() => handleOpenMembers(item._id)}
              activeOpacity={0.85}
            >
              <Text style={styles.meetBtnTxt}>
                {showMembers ? '▲' : '👥'} {t('community.meet', lang)}
              </Text>
            </TouchableOpacity>
          )}
          {isJoined && (
            <TouchableOpacity
              accessibilityRole="button"
              accessibilityLabel={t('community.chat', lang)}
              style={styles.chatBtn}
              onPress={() => navigation.navigate('CommunityChat', {
                communityId: item._id,
                communityName: item.name,
              })}
              activeOpacity={0.85}
            >
              <Text style={styles.chatBtnTxt}>💬 {t('community.chat', lang)}</Text>
            </TouchableOpacity>
          )}
        </View>

        {/* Üye listesi — genişletilebilir */}
        {showMembers && (
          <View style={styles.membersBox}>
            {membersLoading ? (
              <ActivityIndicator color={colors.gold} />
            ) : members.length === 0 ? (
              <Text style={styles.noMembersTxt}>{t('community.no_members', lang)}</Text>
            ) : (
              members.map((m: any) => (
                <View key={String(m.user_id)} style={styles.memberRow}>
                  <View style={styles.memberAvatar}>
                    <Text style={styles.memberAvatarTxt}>
                      {(m.username?.[0] ?? '?').toUpperCase()}
                    </Text>
                  </View>
                  <View style={styles.memberInfo}>
                    <Text style={styles.memberName}>{m.username}</Text>
                    <Text style={styles.memberHarmony}>{t('community.compatibility', lang)}: %{m.harmony_level ?? '—'}</Text>
                  </View>
                  {m.can_request_chat && (
                    <TouchableOpacity
                      accessibilityRole="button"
                      accessibilityLabel='Chat Req'
                      style={styles.chatReqBtn}
                      onPress={() => navigation.navigate('PeerChatRequest', {
                        toUserId: m.user_id,
                        toUsername: m.username,
                        source: 'community',
                      })}
                    >
                      <Text style={styles.chatReqTxt}>💬</Text>
                    </TouchableOpacity>
                  )}
                </View>
              ))
            )}
          </View>
        )}
      </View>
    );
  };

  return (
    <View style={[styles.container, { paddingTop: insets.top }]}>
      {/* Header */}
      <View style={styles.header}>
        <TouchableOpacity onPress={() => navigation.goBack()} style={styles.backBtn}
          accessibilityRole="button"
          accessibilityLabel={t('community.title', lang)}
        >
          <Text style={styles.backText}>←</Text>
        </TouchableOpacity>
        <Text style={styles.title}>{t('community.title', lang)}</Text>
        <TouchableOpacity
          accessibilityRole="button"
          accessibilityLabel='Chat Header'
          style={styles.chatHeaderBtn}
          onPress={() => navigation.navigate('PeerChatList')}
        >
          <Text style={styles.chatHeaderTxt}>💬</Text>
        </TouchableOpacity>
      </View>

      {/* Type filter chips */}
      <ScrollView
        horizontal
        showsHorizontalScrollIndicator={false}
        style={styles.filterRow}
        contentContainerStyle={styles.filterRowContent}
      >
        {TYPE_FILTERS.map(f => (
          <TouchableOpacity
            accessibilityRole="button"
            accessibilityLabel='t(f.labelKey, lang)'
            key={String(f.key)}
            style={[styles.filterChip, typeFilter === f.key && styles.filterChipActive]}
            onPress={() => setTypeFilter(f.key)}
            activeOpacity={0.8}
          >
            <Text style={[styles.filterChipText, typeFilter === f.key && styles.filterChipTextActive]}>
              {t(f.labelKey, lang)}
            </Text>
          </TouchableOpacity>
        ))}
      </ScrollView>

      {loading ? (
        <View style={styles.center}>
          <ActivityIndicator color={colors.gold} size="large" />
        </View>
      ) : (
        <FlatList
          data={communities}
          keyExtractor={item => item._id}
          renderItem={renderItem}
          contentContainerStyle={styles.list}
          showsVerticalScrollIndicator={false}
          refreshControl={
            <RefreshControl
              refreshing={refreshing}
              onRefresh={() => load(true)}
              tintColor={colors.gold}
            />
          }
          ListEmptyComponent={
            <View style={styles.center}>
              <Text style={styles.emptyText}>
                {t('community.empty', lang)}
              </Text>
            </View>
          }
        />
      )}
    </View>
  );
};

const styles = StyleSheet.create({
  container:   { flex: 1, backgroundColor: colors.background },
  header:      {
    flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between',
    paddingHorizontal: spacing.lg, paddingVertical: spacing.md,
    borderBottomWidth: 1, borderColor: colors.border,
  },
  backBtn:     { width: 36, height: 36, justifyContent: 'center' },
  backText:    { ...typography.h2, color: colors.gold },
  title:       { ...typography.h2, color: colors.textPrimary, textAlign: 'center' as const },
  filterRow:        { paddingVertical: spacing.sm },
  filterRowContent: {
    flexDirection: 'row', gap: 8,
    paddingHorizontal: spacing.lg, paddingRight: spacing.lg,
  },
  filterChip:  {
    paddingHorizontal: spacing.md, paddingVertical: 6,
    borderRadius: radius.full, borderWidth: 1, borderColor: colors.border,
    backgroundColor: colors.surface,
  },
  filterChipActive:     { borderColor: colors.gold, backgroundColor: colors.goldGlow },
  filterChipText:       { ...typography.caption, color: colors.textMuted, fontSize: 12 },
  filterChipTextActive: { color: colors.gold, fontWeight: '700' as const },
  list:        { padding: spacing.lg, gap: spacing.md },
  center:      { flex: 1, alignItems: 'center', justifyContent: 'center', padding: spacing.xl },
  emptyText:   { ...typography.body, color: colors.textMuted },
  // Cards
  card:        {
    backgroundColor: colors.surface, borderRadius: radius.lg,
    borderWidth: 1, borderColor: colors.border,
    padding: spacing.lg, gap: spacing.sm,
  },
  cardHighlight: { borderColor: colors.gold, backgroundColor: colors.goldGlow },
  matchBadge:  {
    alignSelf: 'flex-start' as const,
    backgroundColor: colors.gold, borderRadius: radius.full,
    paddingHorizontal: spacing.sm, paddingVertical: 2, marginBottom: 4,
  },
  matchBadgeText: { ...typography.caption, color: '#000', fontSize: 10, fontWeight: '700' as const },
  cardHeader:  { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between' },
  communityName: { ...typography.h2, fontSize: 15, color: colors.textPrimary, flex: 1 },
  memberPill:  {
    backgroundColor: colors.background, borderRadius: radius.full,
    paddingHorizontal: spacing.sm, paddingVertical: 3,
  },
  memberCount: { ...typography.caption, color: colors.textMuted, fontSize: 11 },
  communityDesc: { ...typography.caption, color: colors.textSecondary, fontSize: 13, lineHeight: 18 },
  traitTag:    {
    alignSelf: 'flex-start' as const,
    backgroundColor: colors.background, borderRadius: radius.sm,
    paddingHorizontal: spacing.sm, paddingVertical: 3,
  },
  traitTagText: { ...typography.caption, color: colors.gold, fontSize: 11 },
  joinBtn:     {
    marginTop: 4, height: 40, backgroundColor: colors.gold,
    borderRadius: radius.md, alignItems: 'center', justifyContent: 'center',
    ...shadow.gold,
  },
  joinBtnDone: { backgroundColor: colors.surface, borderWidth: 1, borderColor: colors.gold, ...({} as object) },
  joinBtnText:     { ...typography.label, color: '#000', fontSize: 13 },
  joinBtnTextDone: { color: colors.gold },
  chatHeaderBtn:   { width: 36, height: 36, justifyContent: 'center', alignItems: 'center', backgroundColor: colors.goldGlow, borderRadius: radius.sm, borderWidth: 1, borderColor: colors.gold },
  chatHeaderTxt:   { fontSize: 18 },
  cardBtnRow:      { flexDirection: 'row', gap: spacing.sm, marginTop: 4 },
  meetBtn:         { backgroundColor: colors.warmAmberGlow, borderRadius: radius.md, paddingHorizontal: spacing.md, paddingVertical: 10, borderWidth: 1, borderColor: colors.warmAmber, alignItems: 'center', justifyContent: 'center' },
  meetBtnTxt:      { color: colors.warmAmber, fontWeight: '700', fontSize: 12 },
  membersBox:      { backgroundColor: colors.background, borderRadius: radius.md, padding: spacing.sm, borderWidth: 1, borderColor: colors.border, gap: spacing.xs },
  noMembersTxt:    { ...typography.caption, color: colors.textMuted, textAlign: 'center', padding: spacing.sm },
  memberRow:       { flexDirection: 'row', alignItems: 'center', paddingVertical: spacing.xs, gap: spacing.sm },
  memberAvatar:    { width: 34, height: 34, borderRadius: 17, backgroundColor: colors.goldDark, alignItems: 'center', justifyContent: 'center' },
  memberAvatarTxt: { color: colors.white, fontWeight: '700', fontSize: 13 },
  memberInfo:      { flex: 1 },
  memberName:      { ...typography.label, fontSize: 13, color: colors.textPrimary },
  memberHarmony:   { ...typography.caption, fontSize: 11, color: colors.gold },
  chatReqBtn:      { width: 34, height: 34, borderRadius: 17, backgroundColor: colors.goldGlow, borderWidth: 1, borderColor: colors.gold, alignItems: 'center', justifyContent: 'center' },
  chatReqTxt:      { fontSize: 15 },
  chatBtn:         { backgroundColor: colors.goldGlow, borderRadius: radius.md, paddingHorizontal: spacing.md, paddingVertical: 10, borderWidth: 1, borderColor: colors.gold, alignItems: 'center', justifyContent: 'center' },
  chatBtnTxt:      { color: colors.gold, fontWeight: '700' as const, fontSize: 12 },
});

export default CommunitiesScreen;

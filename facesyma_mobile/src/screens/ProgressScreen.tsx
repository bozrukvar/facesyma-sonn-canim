// src/screens/ProgressScreen.tsx
import React, { useState, useEffect, useCallback } from 'react';
import {
  View, Text, StyleSheet, ScrollView, TouchableOpacity,
  ActivityIndicator, Dimensions, RefreshControl,
} from 'react-native';
import Svg, {
  Path, Line, Circle,
  Text as SvgText, Defs, LinearGradient, Stop,
} from 'react-native-svg';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import theme from '../utils/theme';
const { colors, spacing, typography, radius } = theme;
import { useLanguage } from '../utils/LanguageContext';
import { t } from '../utils/i18n';
import { AssessmentAPI, CheckinAPI, type CheckinHistoryItem } from '../services/api';
import type { ScreenProps } from '../navigation/types';

const { width } = Dimensions.get('window');

// ── Chart geometry ────────────────────────────────────────────────────────────
const CARD_PAD   = spacing.md;
const CHART_W    = width - spacing.lg * 2 - CARD_PAD * 2;
const CHART_H    = 180;
const PAD_LEFT   = 36;
const PAD_BOTTOM = 28;
const PAD_TOP    = 12;
const PAD_RIGHT  = 12;
const PLOT_W     = CHART_W - PAD_LEFT - PAD_RIGHT;
const PLOT_H     = CHART_H - PAD_BOTTOM - PAD_TOP;

const yFor = (score: number) => PAD_TOP + PLOT_H - (score / 100) * PLOT_H;
const xFor = (i: number, n: number) =>
  PAD_LEFT + (n <= 1 ? PLOT_W / 2 : (i / (n - 1)) * PLOT_W);

// ── Test list (shared with AssessmentScreen) ──────────────────────────────────
const TEST_TYPES = [
  { id: 'personality',       key: 'assessment.personality',       emoji: '🧠' },
  { id: 'skills',            key: 'assessment.skills',            emoji: '🎯' },
  { id: 'hr',                key: 'assessment.hr',                emoji: '👥' },
  { id: 'career',            key: 'assessment.career',            emoji: '💼' },
  { id: 'relationship',      key: 'assessment.relationship',      emoji: '❤️' },
  { id: 'vocation',          key: 'assessment.vocation',          emoji: '🏢' },
  { id: 'attachment',        key: 'assessment.attachment',        emoji: '🔗' },
  { id: 'grit',              key: 'assessment.grit',              emoji: '💪' },
  { id: 'growth_mindset',    key: 'assessment.growth_mindset',    emoji: '🌱' },
  { id: 'life_satisfaction', key: 'assessment.life_satisfaction', emoji: '😊' },
  { id: 'self_compassion',   key: 'assessment.self_compassion',   emoji: '🌸' },
  { id: 'body_image',        key: 'assessment.body_image',        emoji: '🪞' },
  { id: 'self_efficacy',     key: 'assessment.self_efficacy',     emoji: '⚡' },
  { id: 'stress',            key: 'assessment.stress',            emoji: '🧘' },
  { id: 'finance',           key: 'finance.title',                emoji: '💰' },
  { id: 'finance_anxiety',   key: 'assessment.finance_anxiety',   emoji: '😰' },
] as const;

// ── Inline translations (progress-specific) ───────────────────────────────────
const TR: Record<string, Record<string, string>> = {
  title:       { tr:'İlerleme', en:'Progress', de:'Fortschritt', ru:'Прогресс', ar:'التقدم', es:'Progreso', ko:'진행', ja:'進捗', zh:'进度', hi:'प्रगति', fr:'Progrès', pt:'Progresso', bn:'অগ্রগতি', id:'Kemajuan', ur:'ترقی', it:'Progressi', vi:'Tiến độ', pl:'Postęp' },
  subtitle:    { tr:'Testlerdeki gelişimini takip et', en:'Track your growth across tests', de:'Verfolge deinen Fortschritt', ru:'Отслеживай прогресс', ar:'تابع تقدمك', es:'Sigue tu crecimiento', ko:'성장 추적', ja:'進捗を追跡', zh:'追踪成长', hi:'प्रगति ट्रैक करें', fr:'Suivez votre progression', pt:'Acompanhe seu crescimento', bn:'অগ্রগতি ট্র্যাক করুন', id:'Lacak perkembanganmu', ur:'ترقی ٹریک کریں', it:'Monitora la tua crescita', vi:'Theo dõi tiến bộ', pl:'Śledź postęp' },
  no_data:     { tr:'Bu test için henüz sonuç yok', en:'No results yet for this test', de:'Noch keine Ergebnisse', ru:'Результатов пока нет', ar:'لا توجد نتائج بعد', es:'Sin resultados aún', ko:'아직 결과 없음', ja:'結果がありません', zh:'暂无结果', hi:'कोई परिणाम नहीं', fr:'Pas encore de résultats', pt:'Sem resultados ainda', bn:'কোনো ফলাফল নেই', id:'Belum ada hasil', ur:'کوئی نتیجہ نہیں', it:'Nessun risultato', vi:'Chưa có kết quả', pl:'Brak wyników' },
  take_test:   { tr:'Testi başlat', en:'Take test', de:'Test starten', ru:'Пройти тест', ar:'ابدأ الاختبار', es:'Hacer test', ko:'테스트 시작', ja:'テストを受ける', zh:'开始测试', hi:'टेस्ट शुरू करें', fr:'Passer le test', pt:'Fazer teste', bn:'টেস্ট শুরু করুন', id:'Mulai tes', ur:'ٹیسٹ شروع کریں', it:'Inizia il test', vi:'Bắt đầu kiểm tra', pl:'Rozpocznij test' },
  since_start: { tr:'ilk testten bu yana', en:'since first test', de:'seit erstem Test', ru:'с первого теста', ar:'منذ أول اختبار', es:'desde primer test', ko:'첫 테스트 이후', ja:'初回テストから', zh:'自第一次测试', hi:'पहले टेस्ट से', fr:'depuis le 1er test', pt:'desde o 1º teste', bn:'প্রথম টেস্ট থেকে', id:'sejak tes pertama', ur:'پہلے ٹیسٹ سے', it:'dal primo test', vi:'từ bài test đầu', pl:'od pierwszego testu' },
  domains:     { tr:'Alan Dağılımı', en:'Domain Breakdown', de:'Bereichsaufteilung', ru:'По областям', ar:'تفصيل المجالات', es:'Desglose por área', ko:'영역 분석', ja:'ドメイン内訳', zh:'领域细分', hi:'क्षेत्र विश्लेषण', fr:'Détail par domaine', pt:'Detalhamento', bn:'ডোমেইন বিশ্লেষণ', id:'Rincian domain', ur:'ڈومین تفصیل', it:'Dettaglio area', vi:'Phân tích lĩnh vực', pl:'Podział obszarów' },
  latest:      { tr:'Son skor', en:'Latest score', de:'Letzter Score', ru:'Последний балл', ar:'آخر نتيجة', es:'Última puntuación', ko:'최신 점수', ja:'最新スコア', zh:'最新得分', hi:'नवीनतम स्कोर', fr:'Dernier score', pt:'Último score', bn:'সর্বশেষ স্কোর', id:'Skor terakhir', ur:'آخری اسکور', it:'Ultimo score', vi:'Điểm mới nhất', pl:'Ostatni wynik' },
  points:      { tr:'puan', en:'pts', de:'Pkt.', ru:'очк.', ar:'نق.', es:'pts', ko:'점', ja:'点', zh:'分', hi:'अंक', fr:'pts', pt:'pts', bn:'পয়েন্ট', id:'poin', ur:'پوائنٹس', it:'pti', vi:'điểm', pl:'pkt' },
  mood_title:  { tr:'Duygu Trendim (30 Gün)', en:'Mood Trend (30 Days)', de:'Stimmungstrend (30 Tage)', ru:'Тренд настроения', ar:'اتجاه المزاج (30 يومًا)', es:'Tendencia emocional', ko:'감정 트렌드 (30일)', ja:'気分トレンド（30日）', zh:'情绪趋势（30天）', hi:'मूड ट्रेंड (30 दिन)', fr:'Tendance humeur (30 j.)', pt:'Tendência de humor', bn:'মুড ট্রেন্ড (৩০ দিন)', id:'Tren suasana hati', ur:'موڈ ٹرینڈ (30 دن)', it:'Trend umore (30 gg)', vi:'Xu hướng cảm xúc', pl:'Trend nastroju (30 dni)' },
  mood_empty:  { tr:'Henüz check-in yapılmadı', en:'No check-ins yet', de:'Noch kein Check-in', ru:'Нет записей', ar:'لا توجد تسجيلات بعد', es:'Sin registros aún', ko:'아직 체크인 없음', ja:'チェックインなし', zh:'暂无记录', hi:'कोई चेक-इन नहीं', fr:'Pas de check-ins', pt:'Sem registros ainda', bn:'কোনো চেক-ইন নেই', id:'Belum ada check-in', ur:'ابھی تک کوئی چیک-ان نہیں', it:'Nessun check-in', vi:'Chưa có check-in', pl:'Brak check-inów' },
};
const tr_ = (key: string, lang: string) => TR[key]?.[lang] ?? TR[key]?.en ?? key;

// ── Month abbreviations ───────────────────────────────────────────────────────
const MONTHS: Record<string, string[]> = {
  tr: ['Oca','Şub','Mar','Nis','May','Haz','Tem','Ağu','Eyl','Eki','Kas','Ara'],
  en: ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'],
};
const dateLabel = (iso: string, lang: string): string => {
  const d = new Date(iso);
  const m = (MONTHS[lang] ?? MONTHS.en)[d.getMonth()];
  return `${d.getDate()} ${m}`;
};

// ── Score color helper ────────────────────────────────────────────────────────
const scoreColor = (score: number) => {
  if (score >= 70) return colors.success;
  if (score >= 45) return colors.warmAmber;
  return colors.error;
};

const formatDomain = (key: string) =>
  key.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase());

// ── SVG Line Chart ────────────────────────────────────────────────────────────
type ChartPoint = { score: number; date: string };

const LineChart: React.FC<{ points: ChartPoint[]; accentColor: string; lang: string }> = ({
  points, accentColor, lang,
}) => {
  const n = points.length;
  if (n === 0) return null;

  const pts = points.map((p, i) => ({
    x: xFor(i, n),
    y: yFor(p.score),
    score: p.score,
    label: dateLabel(p.date, lang),
  }));

  const linePath = pts.map((p, i) => `${i === 0 ? 'M' : 'L'}${p.x},${p.y}`).join(' ');
  const fillPath = `${linePath} L${pts[n-1].x},${PAD_TOP + PLOT_H} L${pts[0].x},${PAD_TOP + PLOT_H} Z`;

  // Show at most 5 x-axis labels
  const maxLabels = 5;
  const labelIdxs: number[] = n <= maxLabels
    ? pts.map((_, i) => i)
    : Array.from({ length: maxLabels }, (_, i) => Math.round((i / (maxLabels - 1)) * (n - 1)));

  return (
    <Svg width={CHART_W} height={CHART_H}>
      <Defs>
        <LinearGradient id="lineGrad" x1="0" y1="0" x2="0" y2="1">
          <Stop offset="0" stopColor={accentColor} stopOpacity="0.28" />
          <Stop offset="1" stopColor={accentColor} stopOpacity="0.02" />
        </LinearGradient>
      </Defs>

      {/* Horizontal grid lines + y-axis labels */}
      {[0, 25, 50, 75, 100].map(score => {
        const y = yFor(score);
        return (
          <React.Fragment key={score}>
            <Line
              x1={PAD_LEFT} y1={y} x2={PAD_LEFT + PLOT_W} y2={y}
              stroke={colors.border}
              strokeWidth={score === 0 ? 1 : 0.5}
              strokeDasharray={score === 0 ? undefined : '3,4'}
            />
            <SvgText
              x={PAD_LEFT - 4} y={y + 4}
              textAnchor="end" fill={colors.textMuted}
              fontSize={9} fontFamily="System"
            >
              {score}
            </SvgText>
          </React.Fragment>
        );
      })}

      {/* Filled area under line */}
      <Path d={fillPath} fill="url(#lineGrad)" />

      {/* Line */}
      <Path
        d={linePath} stroke={accentColor}
        strokeWidth={2} fill="none"
        strokeLinecap="round" strokeLinejoin="round"
      />

      {/* Data points */}
      {pts.map((p, i) => {
        const isLast = i === n - 1;
        return (
          <Circle
            key={i}
            cx={p.x} cy={p.y}
            r={isLast ? 5 : 3}
            fill={isLast ? accentColor : colors.surface}
            stroke={accentColor}
            strokeWidth={isLast ? 0 : 1.5}
          />
        );
      })}

      {/* Score on last point */}
      {n > 0 && (
        <SvgText
          x={pts[n-1].x} y={pts[n-1].y - 8}
          textAnchor="middle" fill={accentColor}
          fontSize={10} fontWeight="700" fontFamily="System"
        >
          {pts[n-1].score}
        </SvgText>
      )}

      {/* X-axis date labels */}
      {labelIdxs.map(i => (
        <SvgText
          key={i}
          x={pts[i].x} y={CHART_H - 5}
          textAnchor="middle" fill={colors.textMuted}
          fontSize={9} fontFamily="System"
        >
          {pts[i].label}
        </SvgText>
      ))}
    </Svg>
  );
};

// ── Mood mini bar chart ───────────────────────────────────────────────────────
const MOOD_W = width - spacing.lg * 2 - CARD_PAD * 2;
const MOOD_H = 80;
const MOOD_BAR_H = 50;

const MoodMiniChart: React.FC<{ items: CheckinHistoryItem[] }> = ({ items }) => {
  const n = items.length;
  if (n === 0) return null;
  const barW = Math.max(4, Math.min(16, (MOOD_W - 8) / n - 3));
  const spacing_ = (MOOD_W - barW * n) / (n + 1);

  return (
    <Svg width={MOOD_W} height={MOOD_H}>
      {items.map((item, i) => {
        const pct = item.mood_score / 5;
        const barHeight = Math.max(4, pct * MOOD_BAR_H);
        const x = spacing_ + i * (barW + spacing_);
        const y = MOOD_H - barHeight - 4;
        const barColor = item.mood_score >= 4 ? colors.success : item.mood_score >= 3 ? colors.warmAmber : colors.error;
        return (
          <React.Fragment key={item.date}>
            <Path
              d={`M${x},${y + barHeight} L${x},${y + 4} Q${x},${y} ${x + 4},${y} L${x + barW - 4},${y} Q${x + barW},${y} ${x + barW},${y + 4} L${x + barW},${y + barHeight} Z`}
              fill={barColor}
              opacity="0.75"
            />
            {n <= 14 && (
              <SvgText
                x={x + barW / 2} y={MOOD_H - 1}
                textAnchor="middle"
                fill={colors.textMuted}
                fontSize={7}
                fontFamily="System"
              >
                {item.date.slice(8)}
              </SvgText>
            )}
          </React.Fragment>
        );
      })}
    </Svg>
  );
};

// ── Main Screen ───────────────────────────────────────────────────────────────
interface HistoryResult {
  id: string;
  test_type: string;
  overall_score: number;
  overall_level_tr: string;
  created_at: string;
}

const ProgressScreen = ({ navigation }: ScreenProps<'Progress'>) => {
  const insets = useSafeAreaInsets();
  const { lang } = useLanguage();
  const [loading, setLoading]   = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [allResults, setAllResults] = useState<HistoryResult[]>([]);
  const [latestScores, setLatestScores] = useState<Record<string, Record<string, number>>>({});
  const [selectedType, setSelectedType] = useState<string>('personality');
  const [moodHistory, setMoodHistory] = useState<CheckinHistoryItem[]>([]);

  const load = useCallback(async () => {
    try {
      const [histRes, scoresRes, moodRes] = await Promise.all([
        AssessmentAPI.getHistory(100),
        AssessmentAPI.getLatestScores(),
        CheckinAPI.getHistory(30).catch(() => ({ success: false, history: [], streak: 0 })),
      ]);
      const results: HistoryResult[] = histRes?.data?.results ?? [];
      setAllResults(results);
      setLatestScores(scoresRes ?? {});
      setMoodHistory(moodRes.history ?? []);

      // Auto-select first type that has data
      const firstWithData = TEST_TYPES.find(tt => results.some(r => r.test_type === tt.id));
      if (firstWithData) setSelectedType(firstWithData.id);
    } catch {
      // silent — empty state will show
    }
  }, []);

  useEffect(() => {
    load().finally(() => setLoading(false));
  }, [load]);

  const onRefresh = useCallback(async () => {
    setRefreshing(true);
    await load();
    setRefreshing(false);
  }, [load]);

  // Results for selected test type, sorted oldest→newest
  const typeResults = allResults
    .filter(r => r.test_type === selectedType)
    .sort((a, b) => new Date(a.created_at).getTime() - new Date(b.created_at).getTime());

  const chartPoints: ChartPoint[] = typeResults.map(r => ({
    score: r.overall_score,
    date:  r.created_at,
  }));

  const latestScore = typeResults[typeResults.length - 1]?.overall_score ?? null;
  const firstScore  = typeResults[0]?.overall_score ?? null;
  const delta       = latestScore !== null && firstScore !== null && typeResults.length >= 2
    ? Math.round(latestScore - firstScore) : null;

  const domainScores = latestScores[selectedType] ?? {};
  const domainEntries = Object.entries(domainScores).filter(([k]) => k !== 'overall');

  const selectedTestInfo = TEST_TYPES.find(tt => tt.id === selectedType);
  const accentColor = colors.gold;

  return (
    <View style={[styles.container, { paddingTop: insets.top }]}>
      {/* Header */}
      <View style={styles.header}>
        <TouchableOpacity onPress={() => navigation.goBack()} style={styles.backBtn} activeOpacity={0.7}
          accessibilityRole="button"
          accessibilityLabel="tr_('title', lang)"
        >
          <Text style={styles.backText}>←</Text>
        </TouchableOpacity>
        <View style={styles.headerBody}>
          <Text style={styles.headerTitle}>{tr_('title', lang)}</Text>
          <Text style={styles.headerSubtitle}>{tr_('subtitle', lang)}</Text>
        </View>
      </View>

      {loading ? (
        <View style={styles.loadingWrap}>
          <ActivityIndicator color={colors.gold} />
        </View>
      ) : (
        <ScrollView
          showsVerticalScrollIndicator={false}
          contentContainerStyle={styles.scroll}
          refreshControl={
            <RefreshControl refreshing={refreshing} onRefresh={onRefresh} tintColor={colors.gold} />
          }
        >
          {/* Test type chips */}
          <ScrollView
            horizontal
            showsHorizontalScrollIndicator={false}
            contentContainerStyle={styles.chipsRow}
            style={styles.chipsScroll}
          >
            {TEST_TYPES.map(tt => {
              const hasData = allResults.some(r => r.test_type === tt.id);
              const selected = tt.id === selectedType;
              return (
                <TouchableOpacity
                  accessibilityRole="button"
                  accessibilityLabel={tt.emoji}
                  key={tt.id}
                  style={[
                    styles.chip,
                    selected && styles.chipSelected,
                    !hasData && styles.chipNoData,
                  ]}
                  onPress={() => setSelectedType(tt.id)}
                  activeOpacity={0.75}
                >
                  <Text style={styles.chipEmoji}>{tt.emoji}</Text>
                  <Text style={[styles.chipText, selected && styles.chipTextSelected]}>
                    {t(tt.key, lang)}
                  </Text>
                  {hasData && !selected && <View style={styles.chipDot} />}
                </TouchableOpacity>
              );
            })}
          </ScrollView>

          {typeResults.length === 0 ? (
            /* Empty state */
            <View style={styles.emptyCard}>
              <Text style={styles.emptyEmoji}>{selectedTestInfo?.emoji ?? '📊'}</Text>
              <Text style={styles.emptyTitle}>{t(selectedTestInfo?.key ?? 'assessment.personality', lang)}</Text>
              <Text style={styles.emptyText}>{tr_('no_data', lang)}</Text>
              <TouchableOpacity
                accessibilityRole="button"
                accessibilityLabel="tr_('take_test', lang)"
                style={styles.emptyBtn}
                onPress={() => navigation.navigate('Assessment')}
                activeOpacity={0.85}
              >
                <Text style={styles.emptyBtnText}>{tr_('take_test', lang)}</Text>
              </TouchableOpacity>
            </View>
          ) : (
            <>
              {/* Delta + latest score row */}
              <View style={styles.metaRow}>
                <View style={styles.metaCard}>
                  <Text style={styles.metaLabel}>{tr_('latest', lang)}</Text>
                  <Text style={[styles.metaScore, { color: scoreColor(latestScore ?? 0) }]}>
                    {latestScore} <Text style={styles.metaUnit}>{tr_('points', lang)}</Text>
                  </Text>
                </View>
                {delta !== null && (
                  <View style={[styles.metaCard, styles.deltaCard]}>
                    <Text style={styles.metaLabel}>{tr_('since_start', lang)}</Text>
                    <Text style={[styles.deltaValue, { color: delta >= 0 ? colors.success : colors.error }]}>
                      {delta >= 0 ? '+' : ''}{delta} {tr_('points', lang)}
                    </Text>
                  </View>
                )}
              </View>

              {/* Line chart card */}
              <View style={styles.chartCard}>
                <LineChart
                  points={chartPoints}
                  accentColor={accentColor}
                  lang={lang}
                />
              </View>

              {/* Domain breakdown */}
              {domainEntries.length > 0 && (
                <View style={styles.domainCard}>
                  <Text style={styles.domainTitle}>{tr_('domains', lang)}</Text>
                  {domainEntries.map(([key, val]) => {
                    const pct = Math.min(100, Math.max(0, val));
                    const barColor = scoreColor(pct);
                    return (
                      <View key={key} style={styles.domainRow}>
                        <Text style={styles.domainKey} numberOfLines={1}>
                          {formatDomain(key)}
                        </Text>
                        <View style={styles.barBg}>
                          <View style={[styles.barFill, { width: `${pct}%`, backgroundColor: barColor }]} />
                        </View>
                        <Text style={[styles.domainVal, { color: barColor }]}>{Math.round(pct)}</Text>
                      </View>
                    );
                  })}
                </View>
              )}
            </>
          )}

          {/* Mood trend mini-chart */}
          <View style={styles.moodCard}>
            <Text style={styles.domainTitle}>{tr_('mood_title', lang)}</Text>
            {moodHistory.length === 0 ? (
              <Text style={styles.moodEmpty}>{tr_('mood_empty', lang)}</Text>
            ) : (
              <MoodMiniChart items={moodHistory} />
            )}
          </View>

          <View style={{ height: insets.bottom + spacing.xl }} />
        </ScrollView>
      )}
    </View>
  );
};

// ── Styles ────────────────────────────────────────────────────────────────────
const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: colors.background },
  loadingWrap: { flex: 1, alignItems: 'center', justifyContent: 'center' },

  header: {
    flexDirection: 'row', alignItems: 'center',
    paddingHorizontal: spacing.lg, paddingVertical: spacing.md,
    borderBottomWidth: 1, borderBottomColor: colors.border,
  },
  backBtn:      { padding: spacing.sm, marginRight: spacing.sm },
  backText:     { ...typography.h2, color: colors.textPrimary },
  headerBody:   { flex: 1 },
  headerTitle:  { ...typography.h2 },
  headerSubtitle: { ...typography.caption, marginTop: 2 },

  scroll: { paddingHorizontal: spacing.lg, paddingTop: spacing.md },

  chipsScroll: { marginBottom: spacing.lg },
  chipsRow:    { paddingRight: spacing.lg, gap: spacing.sm, flexDirection: 'row' },
  chip: {
    flexDirection: 'row', alignItems: 'center',
    gap: 5,
    paddingHorizontal: 12, paddingVertical: 7,
    backgroundColor: colors.surface,
    borderRadius: radius.full,
    borderWidth: 1, borderColor: colors.border,
    position: 'relative',
  },
  chipSelected: {
    backgroundColor: `${colors.gold}18`,
    borderColor: colors.gold,
  },
  chipNoData: { opacity: 0.45 },
  chipEmoji:  { fontSize: 14 },
  chipText:   { ...typography.caption, fontSize: 11 },
  chipTextSelected: { color: colors.gold, fontWeight: '700' },
  chipDot: {
    position: 'absolute', top: 4, right: 4,
    width: 5, height: 5, borderRadius: 2.5,
    backgroundColor: colors.gold,
  },

  metaRow:   { flexDirection: 'row', gap: spacing.sm, marginBottom: spacing.md },
  metaCard: {
    flex: 1,
    backgroundColor: colors.surface,
    borderRadius: radius.lg,
    borderWidth: 1, borderColor: colors.border,
    padding: spacing.md,
  },
  deltaCard: { borderColor: `${colors.gold}30` },
  metaLabel: { ...typography.caption, marginBottom: 4 },
  metaScore: { fontFamily: 'Georgia', fontSize: 24, fontWeight: '700' },
  metaUnit:  { ...typography.caption, fontSize: 12 },
  deltaValue:{ fontFamily: 'Georgia', fontSize: 22, fontWeight: '700' },

  chartCard: {
    backgroundColor: colors.surface,
    borderRadius: radius.lg,
    borderWidth: 1, borderColor: colors.border,
    padding: CARD_PAD,
    marginBottom: spacing.md,
    overflow: 'hidden',
  },

  domainCard: {
    backgroundColor: colors.surface,
    borderRadius: radius.lg,
    borderWidth: 1, borderColor: colors.border,
    padding: spacing.md,
    marginBottom: spacing.md,
  },
  domainTitle: { ...typography.goldLabel, marginBottom: spacing.md },
  domainRow: {
    flexDirection: 'row', alignItems: 'center',
    marginBottom: spacing.sm, gap: 8,
  },
  domainKey: { ...typography.caption, fontSize: 11, width: 110 },
  barBg: {
    flex: 1, height: 6, borderRadius: 3,
    backgroundColor: colors.border, overflow: 'hidden',
  },
  barFill: { height: 6, borderRadius: 3 },
  domainVal: { ...typography.caption, fontSize: 11, width: 28, textAlign: 'right', fontWeight: '600' },

  emptyCard: {
    alignItems: 'center', justifyContent: 'center',
    padding: spacing.xxl,
    backgroundColor: colors.surface,
    borderRadius: radius.xl, borderWidth: 1, borderColor: colors.border,
    marginTop: spacing.xl,
  },
  emptyEmoji: { fontSize: 48, marginBottom: spacing.md },
  emptyTitle: { ...typography.h2, marginBottom: spacing.sm },
  emptyText:  { ...typography.body, textAlign: 'center', marginBottom: spacing.xl },
  emptyBtn: {
    backgroundColor: colors.gold,
    borderRadius: radius.xl,
    paddingHorizontal: spacing.xl, paddingVertical: 12,
  },
  emptyBtnText: { ...typography.label, color: '#000', letterSpacing: 1.5 },

  moodCard: {
    backgroundColor: colors.surface,
    borderRadius: radius.xl,
    borderWidth: 1, borderColor: colors.border,
    padding: CARD_PAD,
    marginTop: spacing.lg,
  },
  moodEmpty: { ...typography.caption, textAlign: 'center', paddingVertical: spacing.lg },
});

export default ProgressScreen;

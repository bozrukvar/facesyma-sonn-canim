// src/screens/MonthlyReportScreen.tsx
import React, { useState, useEffect, useCallback, useRef } from 'react';
import {
  View, Text, StyleSheet, ScrollView, TouchableOpacity,
  ActivityIndicator, Share, RefreshControl, Dimensions,
} from 'react-native';
import Svg, { Circle, Rect } from 'react-native-svg';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import theme from '../utils/theme';
const { colors, spacing, typography, radius } = theme;
import { useLanguage } from '../utils/LanguageContext';
import { ReportsAPI, type MonthlyReport } from '../services/api';
import type { ScreenProps } from '../navigation/types';

type Props = ScreenProps<'MonthlyReport'>;

const { width } = Dimensions.get('window');

// ── Inline translations ───────────────────────────────────────────────────────
const TR: Record<string, Record<string, string>> = {
  title:       { tr:'Aylık Raporum', en:'Monthly Report', de:'Monatsbericht', ru:'Ежемесячный отчёт', ar:'التقرير الشهري', es:'Informe Mensual', ko:'월간 리포트', ja:'月次レポート', zh:'月度报告', hi:'मासिक रिपोर्ट', fr:'Rapport Mensuel', pt:'Relatório Mensal', bn:'মাসিক প্রতিবেদন', id:'Laporan Bulanan', ur:'ماہانہ رپورٹ', it:'Rapporto Mensile', vi:'Báo cáo tháng', pl:'Raport Miesięczny' },
  tests:       { tr:'Tamamlanan Testler', en:'Completed Tests', de:'Abgeschlossene Tests', ru:'Завершённые тесты', ar:'الاختبارات المكتملة', es:'Tests completados', ko:'완료된 테스트', ja:'完了したテスト', zh:'完成的测试', hi:'पूर्ण परीक्षण', fr:'Tests complétés', pt:'Testes concluídos', bn:'সম্পন্ন পরীক্ষা', id:'Tes selesai', ur:'مکمل ٹیسٹ', it:'Test completati', vi:'Bài kiểm tra hoàn thành', pl:'Ukończone testy' },
  strongest:   { tr:'En Güçlü Alan', en:'Strongest Area', de:'Stärkster Bereich', ru:'Сильнейшая область', ar:'أقوى مجال', es:'Área más fuerte', ko:'가장 강한 영역', ja:'最強エリア', zh:'最强领域', hi:'सबसे मजबूत क्षेत्र', fr:'Domaine le plus fort', pt:'Área mais forte', bn:'সবচেয়ে শক্তিশালী ক্ষেত্র', id:'Area terkuat', ur:'سب سے مضبوط شعبہ', it:'Area più forte', vi:'Lĩnh vực mạnh nhất', pl:'Najmocniejszy obszar' },
  growth:      { tr:'Gelişim Alanı', en:'Growth Area', de:'Entwicklungsbereich', ru:'Область роста', ar:'مجال النمو', es:'Área de crecimiento', ko:'성장 영역', ja:'成長エリア', zh:'成长领域', hi:'विकास क्षेत्र', fr:'Zone de croissance', pt:'Área de crescimento', bn:'বিকাশের ক্ষেত্র', id:'Area pertumbuhan', ur:'ترقی کا شعبہ', it:'Area di crescita', vi:'Lĩnh vực cần phát triển', pl:'Obszar wzrostu' },
  mood:        { tr:'Duygu Ortalaması', en:'Mood Average', de:'Stimmungsdurchschnitt', ru:'Среднее настроение', ar:'متوسط المزاج', es:'Promedio de humor', ko:'평균 감정', ja:'平均気分', zh:'情绪平均', hi:'औसत मनोदशा', fr:'Humeur moyenne', pt:'Média de humor', bn:'গড় মেজাজ', id:'Rata-rata suasana hati', ur:'اوسط موڈ', it:'Umore medio', vi:'Tâm trạng trung bình', pl:'Średni nastrój' },
  checkin_days:{ tr:'Check-in Günü', en:'Check-in Days', de:'Check-in-Tage', ru:'Дней с чек-ином', ar:'أيام تسجيل الدخول', es:'Días de registro', ko:'체크인 일수', ja:'チェックイン日数', zh:'打卡天数', hi:'चेक-इन दिन', fr:'Jours de check-in', pt:'Dias de check-in', bn:'চেক-ইন দিন', id:'Hari check-in', ur:'چیک-ان دن', it:'Giorni check-in', vi:'Ngày check-in', pl:'Dni check-in' },
  goals_sec:   { tr:'Hedef Durumu', en:'Goal Status', de:'Zielstatus', ru:'Статус целей', ar:'حالة الأهداف', es:'Estado de metas', ko:'목표 상태', ja:'目標ステータス', zh:'目标状态', hi:'लक्ष्य स्थिति', fr:'Statut des objectifs', pt:'Status das metas', bn:'লক্ষ্যের অবস্থা', id:'Status tujuan', ur:'اہداف کی حیثیت', it:'Stato obiettivi', vi:'Trạng thái mục tiêu', pl:'Status celów' },
  active:      { tr:'Aktif', en:'Active', de:'Aktiv', ru:'Активно', ar:'نشط', es:'Activo', ko:'활성', ja:'アクティブ', zh:'活跃', hi:'सक्रिय', fr:'Actif', pt:'Ativo', bn:'সক্রিয়', id:'Aktif', ur:'فعال', it:'Attivo', vi:'Đang hoạt động', pl:'Aktywne' },
  completed:   { tr:'Tamamlandı', en:'Completed', de:'Abgeschlossen', ru:'Завершено', ar:'مكتمل', es:'Completado', ko:'완료', ja:'完了', zh:'完成', hi:'पूर्ण', fr:'Terminé', pt:'Concluído', bn:'সম্পন্ন', id:'Selesai', ur:'مکمل', it:'Completato', vi:'Hoàn thành', pl:'Ukończono' },
  percentile:  { tr:'Sıralama', en:'Ranking', de:'Rangfolge', ru:'Рейтинг', ar:'الترتيب', es:'Clasificación', ko:'순위', ja:'ランキング', zh:'排名', hi:'रैंकिंग', fr:'Classement', pt:'Classificação', bn:'র‍্যাংকিং', id:'Peringkat', ur:'درجہ بندی', it:'Classifica', vi:'Xếp hạng', pl:'Ranking' },
  coach:       { tr:'Koç Özeti', en:'Coach Summary', de:'Coach-Zusammenfassung', ru:'Итог коуча', ar:'ملخص المدرب', es:'Resumen del coach', ko:'코치 요약', ja:'コーチサマリー', zh:'教练总结', hi:'कोच सारांश', fr:'Résumé du coach', pt:'Resumo do coach', bn:'কোচ সারসংক্ষেপ', id:'Ringkasan pelatih', ur:'کوچ خلاصہ', it:'Riepilogo coach', vi:'Tóm tắt huấn luyện viên', pl:'Podsumowanie coacha' },
  share:       { tr:'Paylaş', en:'Share', de:'Teilen', ru:'Поделиться', ar:'مشاركة', es:'Compartir', ko:'공유', ja:'共有', zh:'分享', hi:'साझा करें', fr:'Partager', pt:'Compartilhar', bn:'শেয়ার করুন', id:'Bagikan', ur:'شیئر کریں', it:'Condividi', vi:'Chia sẻ', pl:'Udostępnij' },
  no_data:     { tr:'Bu ay için yeterli veri yok. Test yap, duygu gir ve hedef belirle!', en:'Not enough data for this month. Take tests, log moods, and set goals!', de:'Nicht genug Daten. Mach Tests, tracke deine Stimmung!', ru:'Недостаточно данных. Пройди тесты, отмечай настроение!', ar:'لا توجد بيانات كافية. أكمل الاختبارات وسجّل مزاجك!', es:'Datos insuficientes. ¡Haz tests, registra tu estado de ánimo!', ko:'이번 달 데이터가 부족합니다. 테스트, 감정 기록, 목표 설정을 해보세요!', ja:'今月のデータが不足しています。テストを受け、気分を記録しましょう！', zh:'本月数据不足。完成测试、记录情绪、设定目标！', hi:'इस महीने पर्याप्त डेटा नहीं है। टेस्ट करें, मूड लॉग करें!', fr:'Pas assez de données ce mois-ci. Faites des tests, enregistrez votre humeur !', pt:'Dados insuficientes. Faça testes, registre seu humor e defina metas!', bn:'এই মাসে যথেষ্ট ডেটা নেই। পরীক্ষা করুন, মুড লগ করুন!', id:'Data bulan ini tidak cukup. Lakukan tes, catat suasana hati!', ur:'اس ماہ کافی ڈیٹا نہیں۔ ٹیسٹ کریں، موڈ درج کریں!', it:'Dati insufficienti. Fai test, registra il tuo umore!', vi:'Không đủ dữ liệu tháng này. Làm bài kiểm tra, ghi lại cảm xúc!', pl:'Niewystarczające dane. Rób testy, zapisuj nastrój i ustalaj cele!' },
  improving:   { tr:'Yükseliyor', en:'Improving', de:'Verbessernd', ru:'Улучшается', ar:'يتحسن', es:'Mejorando', ko:'향상 중', ja:'改善中', zh:'上升', hi:'सुधार हो रहा है', fr:'En amélioration', pt:'Melhorando', bn:'উন্নতি হচ্ছে', id:'Membaik', ur:'بہتر ہو رہا ہے', it:'In miglioramento', vi:'Đang cải thiện', pl:'Poprawiający się' },
  declining:   { tr:'Düşüyor', en:'Declining', de:'Abnehmend', ru:'Снижается', ar:'ينخفض', es:'Bajando', ko:'하락 중', ja:'低下中', zh:'下降', hi:'घट रहा है', fr:'En baisse', pt:'Caindo', bn:'হ্রাস পাচ্ছে', id:'Menurun', ur:'گھٹ رہا ہے', it:'In calo', vi:'Đang giảm', pl:'Spadający' },
  stable:      { tr:'Dengeli', en:'Stable', de:'Stabil', ru:'Стабильно', ar:'مستقر', es:'Estable', ko:'안정적', ja:'安定', zh:'稳定', hi:'स्थिर', fr:'Stable', pt:'Estável', bn:'স্থিতিশীল', id:'Stabil', ur:'مستحکم', it:'Stabile', vi:'Ổn định', pl:'Stabilny' },
  prev_month:  { tr:'Önceki ay', en:'Prev. month', de:'Vormonat', ru:'Предыдущий месяц', ar:'الشهر الماضي', es:'Mes anterior', ko:'전월', ja:'先月', zh:'上个月', hi:'पिछले महीने', fr:'Mois précédent', pt:'Mês anterior', bn:'গত মাস', id:'Bulan lalu', ur:'گزشتہ مہینہ', it:'Mese precedente', vi:'Tháng trước', pl:'Poprzedni miesiąc' },
  next_month:  { tr:'Sonraki ay', en:'Next month', de:'Nächster Monat', ru:'Следующий месяц', ar:'الشهر القادم', es:'Mes siguiente', ko:'다음 달', ja:'来月', zh:'下个月', hi:'अगले महीने', fr:'Mois suivant', pt:'Próximo mês', bn:'পরের মাস', id:'Bulan depan', ur:'اگلا مہینہ', it:'Mese prossimo', vi:'Tháng sau', pl:'Następny miesiąc' },
};
const tl = (k: string, l: string) => TR[k]?.[l] ?? TR[k]?.en ?? k;

const TEST_TYPE_EMOJI: Record<string, string> = {
  personality:'🧠', skills:'🎯', hr:'👥', career:'💼', relationship:'❤️',
  vocation:'🏢', attachment:'🔗', grit:'💪', growth_mindset:'🌱',
  life_satisfaction:'😊', self_compassion:'🌸', body_image:'🪞',
  self_efficacy:'⚡', stress:'🧘', finance:'💰', finance_anxiety:'😰',
};

const MOOD_EMOJI: Record<number, string> = { 1:'😔', 2:'😕', 3:'😐', 4:'🙂', 5:'😄' };

const scoreColor = (s: number) => s >= 70 ? '#4CAF50' : s >= 45 ? '#FFC107' : '#F44336';
const moodColor  = (m: number) => m >= 4 ? '#4CAF50' : m >= 3 ? '#FFC107' : '#F44336';

// ── Circular progress ring ─────────────────────────────────────────────────
const RING_R = 40, RING_SW = 7;
const RING_SIZE = (RING_R + RING_SW) * 2;
const RING_CIRC = 2 * Math.PI * RING_R;

const SmallRing: React.FC<{ pct: number; color: string; label: string }> = ({ pct, color, label }) => {
  const offset = RING_CIRC * (1 - Math.min(1, pct / 100));
  return (
    <View style={styles.ringWrap}>
      <Svg width={RING_SIZE} height={RING_SIZE}>
        <Circle cx={RING_SIZE/2} cy={RING_SIZE/2} r={RING_R} stroke={colors.border} strokeWidth={RING_SW} fill="none" />
        <Circle cx={RING_SIZE/2} cy={RING_SIZE/2} r={RING_R} stroke={color} strokeWidth={RING_SW} fill="none"
          strokeDasharray={RING_CIRC} strokeDashoffset={offset}
          strokeLinecap="round" rotation="-90" origin={`${RING_SIZE/2},${RING_SIZE/2}`}
        />
      </Svg>
      <View style={styles.ringCenter}>
        <Text style={[styles.ringPct, { color }]}>{pct}%</Text>
      </View>
      <Text style={styles.ringLabel} numberOfLines={2}>{label}</Text>
    </View>
  );
};

// ── Mood bar chart ─────────────────────────────────────────────────────────
const CHART_W = width - spacing.lg * 2 - 32;
const BAR_H   = 60;

const MoodBarChart: React.FC<{ hist: Record<string, number> }> = ({ hist }) => {
  const maxVal = Math.max(1, ...Object.values(hist).map(Number));
  return (
    <View style={styles.moodChart}>
      {[1,2,3,4,5].map(i => {
        const count = hist[String(i)] ?? 0;
        const pct   = count / maxVal;
        const bH    = Math.max(2, Math.round(pct * BAR_H));
        const col   = moodColor(i);
        return (
          <View key={i} style={styles.moodBarCol}>
            <Text style={styles.moodBarCount}>{count}</Text>
            <View style={[styles.moodBarFill, { height: bH, backgroundColor: col }]} />
            <Text style={styles.moodBarEmoji}>{MOOD_EMOJI[i]}</Text>
          </View>
        );
      })}
    </View>
  );
};

// ── Main screen ────────────────────────────────────────────────────────────
export default function MonthlyReportScreen({ navigation, route }: Props) {
  const insets = useSafeAreaInsets();
  const { lang } = useLanguage();

  const todayStr   = new Date().toISOString().slice(0, 7); // YYYY-MM
  const [month, setMonth] = useState<string>(route.params?.month ?? todayStr);
  const [report,   setReport]     = useState<MonthlyReport | null>(null);
  const [loading,  setLoading]    = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [sharing,  setSharing]    = useState(false);

  const load = useCallback(async (m: string) => {
    try {
      const res = await ReportsAPI.getMonthly(m, lang);
      setReport(res.report);
    } catch {
      setReport(null);
    }
  }, [lang]);

  useEffect(() => {
    setLoading(true);
    load(month).finally(() => setLoading(false));
  }, [month, load]);

  const onRefresh = useCallback(async () => {
    setRefreshing(true);
    await load(month);
    setRefreshing(false);
  }, [month, load]);

  const changeMonth = (delta: number) => {
    const [y, m_] = month.split('-').map(Number);
    const d = new Date(y, m_ - 1 + delta, 1);
    const newMonth = `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}`;
    if (newMonth <= todayStr) setMonth(newMonth);
  };

  const handleShare = async () => {
    if (!report) return;
    setSharing(true);
    try {
      const lines = [
        `📊 ${tl('title', lang)} — ${report.month}`,
        '',
        `✅ ${tl('tests', lang)}: ${report.tests_completed}`,
        report.strongest_domain.label ? `💪 ${tl('strongest', lang)}: ${report.strongest_domain.label} (${report.strongest_domain.score}/100)` : '',
        report.mood_avg > 0 ? `😊 ${tl('mood', lang)}: ${report.mood_avg}/5 — ${tl(report.mood_trend, lang)}` : '',
        report.goals_completed > 0 ? `🎯 ${tl('completed', lang)}: ${report.goals_completed}` : '',
        '',
        report.coach_summary,
        '',
        '— facesyma.com',
      ].filter(Boolean).join('\n');
      await Share.share({ message: lines, title: `facesyma ${report.month}` });
    } catch { /* user dismissed */ }
    finally { setSharing(false); }
  };

  const hasData = report && (
    report.tests_completed > 0 || report.checkin_days > 0 || report.goals_active > 0
  );

  return (
    <View style={[styles.container, { paddingTop: insets.top }]}>
      {/* Header */}
      <View style={styles.header}>
        <TouchableOpacity onPress={() => navigation.goBack()} style={styles.backBtn}>
          <Text style={styles.backText}>←</Text>
        </TouchableOpacity>
        <View style={styles.headerCenter}>
          <Text style={styles.headerTitle}>{tl('title', lang)}</Text>
          {/* Month navigator */}
          <View style={styles.monthNav}>
            <TouchableOpacity onPress={() => changeMonth(-1)} style={styles.monthArrow}>
              <Text style={styles.monthArrowText}>‹</Text>
            </TouchableOpacity>
            <Text style={styles.monthLabel}>{month}</Text>
            <TouchableOpacity
              onPress={() => changeMonth(1)}
              style={[styles.monthArrow, month >= todayStr && styles.monthArrowDisabled]}
              disabled={month >= todayStr}
            >
              <Text style={[styles.monthArrowText, month >= todayStr && { opacity: 0.3 }]}>›</Text>
            </TouchableOpacity>
          </View>
        </View>
        <TouchableOpacity onPress={handleShare} style={styles.shareBtn} disabled={sharing || !hasData}>
          {sharing
            ? <ActivityIndicator size="small" color={colors.gold} />
            : <Text style={styles.shareBtnText}>↑</Text>
          }
        </TouchableOpacity>
      </View>

      {loading ? (
        <View style={styles.center}>
          <ActivityIndicator color={colors.gold} size="large" />
        </View>
      ) : !hasData ? (
        <View style={styles.center}>
          <Text style={styles.emptyEmoji}>📊</Text>
          <Text style={styles.emptyText}>{tl('no_data', lang)}</Text>
        </View>
      ) : (
        <ScrollView
          contentContainerStyle={styles.scroll}
          refreshControl={<RefreshControl refreshing={refreshing} onRefresh={onRefresh} tintColor={colors.gold} />}
          showsVerticalScrollIndicator={false}
        >
          {/* ── Coach summary banner ── */}
          {report!.coach_summary && (
            <View style={styles.coachBanner}>
              <Text style={styles.coachBannerLabel}>🤖 {tl('coach', lang)}</Text>
              <Text style={styles.coachBannerText}>{report!.coach_summary}</Text>
            </View>
          )}

          {/* ── Stats overview row ── */}
          <View style={styles.overviewRow}>
            <View style={styles.overviewCard}>
              <Text style={styles.overviewValue}>{report!.tests_completed}</Text>
              <Text style={styles.overviewLabel}>{tl('tests', lang)}</Text>
            </View>
            <View style={styles.overviewCard}>
              <Text style={[styles.overviewValue, { color: moodColor(report!.mood_avg) }]}>
                {report!.mood_avg > 0 ? report!.mood_avg.toFixed(1) : '—'}
              </Text>
              <Text style={styles.overviewLabel}>{tl('mood', lang)}</Text>
            </View>
            <View style={styles.overviewCard}>
              <Text style={styles.overviewValue}>{report!.checkin_days}</Text>
              <Text style={styles.overviewLabel}>{tl('checkin_days', lang)}</Text>
            </View>
            <View style={styles.overviewCard}>
              <Text style={[styles.overviewValue, { color: '#4CAF50' }]}>{report!.goals_completed}</Text>
              <Text style={styles.overviewLabel}>{tl('completed', lang)}</Text>
            </View>
          </View>

          {/* ── Strongest + Growth ── */}
          {(report!.strongest_domain.label || report!.growth_area.label) && (
            <View style={styles.twoCol}>
              {report!.strongest_domain.label ? (
                <View style={[styles.highlightCard, styles.strongCard]}>
                  <Text style={styles.highlightIcon}>💪</Text>
                  <Text style={styles.highlightLabel}>{tl('strongest', lang)}</Text>
                  <Text style={styles.highlightDomain}>{report!.strongest_domain.label}</Text>
                  <Text style={[styles.highlightScore, { color: '#4CAF50' }]}>{report!.strongest_domain.score}/100</Text>
                </View>
              ) : null}
              {report!.growth_area.label ? (
                <View style={[styles.highlightCard, styles.growthCard]}>
                  <Text style={styles.highlightIcon}>🌱</Text>
                  <Text style={styles.highlightLabel}>{tl('growth', lang)}</Text>
                  <Text style={styles.highlightDomain}>{report!.growth_area.label}</Text>
                  <Text style={[styles.highlightScore, { color: '#FFC107' }]}>{report!.growth_area.score}/100</Text>
                </View>
              ) : null}
            </View>
          )}

          {/* ── Test scores ── */}
          {report!.test_scores.length > 0 && (
            <>
              <Text style={styles.sectionTitle}>📋 {tl('tests', lang)}</Text>
              <ScrollView
                horizontal showsHorizontalScrollIndicator={false}
                contentContainerStyle={styles.ringRow}
              >
                {report!.test_scores.map(ts => (
                  <View key={ts.test_type} style={styles.ringCardWrap}>
                    <SmallRing
                      pct={ts.percentile}
                      color={scoreColor(ts.score)}
                      label={`${TEST_TYPE_EMOJI[ts.test_type] ?? '📊'} ${ts.test_type.replace(/_/g,' ')}`}
                    />
                    <Text style={[styles.ringScore, { color: scoreColor(ts.score) }]}>{ts.score}/100</Text>
                    {ts.change !== undefined && (
                      <Text style={[styles.ringDelta, { color: ts.change >= 0 ? '#4CAF50' : '#F44336' }]}>
                        {ts.change >= 0 ? '+' : ''}{ts.change}
                      </Text>
                    )}
                  </View>
                ))}
              </ScrollView>
            </>
          )}

          {/* ── Percentile hints ── */}
          {report!.percentile_hints.length > 0 && (
            <>
              <Text style={styles.sectionTitle}>🏆 {tl('percentile', lang)}</Text>
              {report!.percentile_hints.map(ph => (
                <View key={ph.test_type} style={styles.percentileRow}>
                  <Text style={styles.percentileEmoji}>{TEST_TYPE_EMOJI[ph.test_type] ?? '📊'}</Text>
                  <Text style={styles.percentileText}>
                    {lang === 'tr'
                      ? `${ph.test_type.replace(/_/g,' ')} alanında kullanıcıların %${ph.percentile}'inden iyisin`
                      : `You outperform ${ph.percentile}% of users in ${ph.test_type.replace(/_/g,' ')}`}
                  </Text>
                  <Text style={[styles.percentileVal, { color: scoreColor(ph.score) }]}>%{ph.percentile}</Text>
                </View>
              ))}
            </>
          )}

          {/* ── Mood histogram ── */}
          {report!.checkin_days > 0 && (
            <>
              <Text style={styles.sectionTitle}>
                😊 {tl('mood', lang)} — {tl(report!.mood_trend, lang)} {report!.mood_trend === 'improving' ? '↑' : report!.mood_trend === 'declining' ? '↓' : '→'}
              </Text>
              <View style={styles.card}>
                <MoodBarChart hist={report!.mood_histogram} />
              </View>
            </>
          )}

          {/* ── Goals ── */}
          {report!.goals_progress.length > 0 && (
            <>
              <Text style={styles.sectionTitle}>🎯 {tl('goals_sec', lang)}</Text>
              <View style={styles.card}>
                <View style={styles.goalStatRow}>
                  <View style={styles.goalStat}>
                    <Text style={[styles.goalStatVal, { color: colors.gold }]}>{report!.goals_active}</Text>
                    <Text style={styles.goalStatLabel}>{tl('active', lang)}</Text>
                  </View>
                  <View style={styles.goalStat}>
                    <Text style={[styles.goalStatVal, { color: '#4CAF50' }]}>{report!.goals_completed}</Text>
                    <Text style={styles.goalStatLabel}>{tl('completed', lang)}</Text>
                  </View>
                </View>
                {report!.goals_progress.map((g, i) => {
                  const barColor = g.status === 'completed' ? '#4CAF50' : scoreColor(g.pct);
                  return (
                    <View key={i} style={styles.goalRow}>
                      <Text style={styles.goalTitle} numberOfLines={1}>{g.title}</Text>
                      <View style={styles.goalBarBg}>
                        <View style={[styles.goalBarFill, { width: `${g.pct}%` as any, backgroundColor: barColor }]} />
                      </View>
                      <Text style={[styles.goalPct, { color: barColor }]}>{g.pct}%</Text>
                    </View>
                  );
                })}
              </View>
            </>
          )}

          {/* Share CTA */}
          <TouchableOpacity style={styles.shareCta} onPress={handleShare} disabled={sharing}>
            {sharing
              ? <ActivityIndicator color="#1A1A2E" size="small" />
              : <Text style={styles.shareCtaText}>↑ {tl('share', lang)}</Text>
            }
          </TouchableOpacity>

          <View style={{ height: insets.bottom + spacing.xl }} />
        </ScrollView>
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  container:  { flex: 1, backgroundColor: colors.background },
  center:     { flex: 1, alignItems: 'center', justifyContent: 'center', padding: spacing.xl },
  emptyEmoji: { fontSize: 48, marginBottom: spacing.md },
  emptyText:  { ...typography.body, textAlign: 'center', color: colors.textMuted },

  header: {
    flexDirection: 'row', alignItems: 'center',
    paddingHorizontal: spacing.lg, paddingVertical: spacing.sm,
    borderBottomWidth: 1, borderBottomColor: colors.border,
  },
  backBtn:  { padding: spacing.sm, marginRight: spacing.xs },
  backText: { ...typography.h2, color: colors.textPrimary },
  headerCenter: { flex: 1, alignItems: 'center' },
  headerTitle:  { ...typography.h3, marginBottom: 4 },
  monthNav:     { flexDirection: 'row', alignItems: 'center', gap: spacing.sm },
  monthArrow:   { padding: 4 },
  monthArrowDisabled: { opacity: 0.3 },
  monthArrowText:     { color: colors.gold, fontSize: 20, fontWeight: '700' },
  monthLabel:         { ...typography.label, fontSize: 14, color: colors.textPrimary, minWidth: 70, textAlign: 'center' },
  shareBtn:  { padding: spacing.sm, marginLeft: spacing.xs },
  shareBtnText: { color: colors.gold, fontSize: 20, fontWeight: '700' },

  scroll: { paddingHorizontal: spacing.lg, paddingTop: spacing.md },

  coachBanner: {
    backgroundColor: '#1E1E3A',
    borderRadius: 16, borderWidth: 1, borderColor: colors.gold + '40',
    padding: spacing.md, marginBottom: spacing.lg,
  },
  coachBannerLabel: { color: colors.gold, fontSize: 12, fontWeight: '700', marginBottom: 6 },
  coachBannerText:  { color: colors.textPrimary, fontSize: 14, lineHeight: 20 },

  overviewRow: {
    flexDirection: 'row', gap: spacing.sm, marginBottom: spacing.lg,
  },
  overviewCard: {
    flex: 1, backgroundColor: colors.surface, borderRadius: 14,
    borderWidth: 1, borderColor: colors.border,
    padding: spacing.sm, alignItems: 'center',
  },
  overviewValue: { ...typography.h2, fontSize: 22, color: colors.gold },
  overviewLabel: { ...typography.caption, textAlign: 'center', marginTop: 2 },

  twoCol:      { flexDirection: 'row', gap: spacing.sm, marginBottom: spacing.lg },
  highlightCard: {
    flex: 1, borderRadius: 16, borderWidth: 1.5,
    padding: spacing.md, alignItems: 'center',
  },
  strongCard:  { borderColor: '#4CAF5040', backgroundColor: '#4CAF5012' },
  growthCard:  { borderColor: '#FFC10740', backgroundColor: '#FFC10712' },
  highlightIcon:   { fontSize: 28, marginBottom: 6 },
  highlightLabel:  { ...typography.caption, marginBottom: 4, textAlign: 'center' },
  highlightDomain: { ...typography.label, textAlign: 'center', marginBottom: 4 },
  highlightScore:  { fontSize: 18, fontWeight: '800' },

  sectionTitle: { ...typography.h3, marginBottom: spacing.sm, marginTop: spacing.sm },

  ringRow:     { paddingRight: spacing.lg, gap: spacing.lg },
  ringCardWrap:{ alignItems: 'center', marginBottom: spacing.md },
  ringWrap:    { position: 'relative', alignItems: 'center', marginBottom: 4 },
  ringCenter:  { position: 'absolute', alignItems: 'center', justifyContent: 'center',
                 top: 0, bottom: 0, left: 0, right: 0 },
  ringPct:     { fontSize: 15, fontWeight: '800' },
  ringLabel:   { ...typography.caption, fontSize: 10, textAlign: 'center', maxWidth: 80, marginTop: 4 },
  ringScore:   { fontSize: 13, fontWeight: '700' },
  ringDelta:   { fontSize: 11, fontWeight: '600', marginTop: 2 },

  percentileRow: {
    flexDirection: 'row', alignItems: 'center',
    backgroundColor: colors.surface, borderRadius: 12,
    borderWidth: 1, borderColor: colors.border,
    padding: spacing.sm, marginBottom: spacing.sm, gap: spacing.sm,
  },
  percentileEmoji: { fontSize: 20 },
  percentileText:  { flex: 1, ...typography.caption, fontSize: 12 },
  percentileVal:   { fontSize: 16, fontWeight: '800' },

  card: {
    backgroundColor: colors.surface, borderRadius: 16,
    borderWidth: 1, borderColor: colors.border,
    padding: spacing.md, marginBottom: spacing.lg,
  },

  moodChart:    { flexDirection: 'row', justifyContent: 'space-around', alignItems: 'flex-end', height: BAR_H + 40 },
  moodBarCol:   { alignItems: 'center', gap: 4, flex: 1 },
  moodBarCount: { ...typography.caption, fontSize: 11 },
  moodBarFill:  { width: 28, borderRadius: 6, minHeight: 4 },
  moodBarEmoji: { fontSize: 18 },

  goalStatRow:  { flexDirection: 'row', marginBottom: spacing.md, gap: spacing.md },
  goalStat:     { alignItems: 'center', flex: 1 },
  goalStatVal:  { fontSize: 28, fontWeight: '800' },
  goalStatLabel:{ ...typography.caption },
  goalRow:      { flexDirection: 'row', alignItems: 'center', marginBottom: spacing.sm, gap: 8 },
  goalTitle:    { ...typography.caption, flex: 1, fontSize: 12 },
  goalBarBg:    { width: 80, height: 6, backgroundColor: colors.border, borderRadius: 3 },
  goalBarFill:  { height: 6, borderRadius: 3 },
  goalPct:      { fontSize: 12, fontWeight: '700', width: 36, textAlign: 'right' },

  shareCta: {
    backgroundColor: colors.gold, borderRadius: radius.xl,
    paddingVertical: 14, alignItems: 'center', marginTop: spacing.md,
  },
  shareCtaText: { color: '#1A1A2E', fontWeight: '700', fontSize: 16 },
});

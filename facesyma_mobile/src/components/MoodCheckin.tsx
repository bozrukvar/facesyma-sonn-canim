import React, { useEffect, useState } from 'react';
import {
  View, Text, TouchableOpacity, StyleSheet, ActivityIndicator,
} from 'react-native';
import { CheckinAPI } from '../services/api';

const MOODS = [
  { score: 1, emoji: '😔', label_tr: 'Kötü',    label_en: 'Bad' },
  { score: 2, emoji: '😕', label_tr: 'Vasat',   label_en: 'Meh' },
  { score: 3, emoji: '😐', label_tr: 'Normal',  label_en: 'Okay' },
  { score: 4, emoji: '🙂', label_tr: 'İyi',     label_en: 'Good' },
  { score: 5, emoji: '😄', label_tr: 'Harika',  label_en: 'Great' },
];

const TAGS_TR = ['stresli', 'yorgun', 'enerjik', 'sakin', 'mutlu'];
const TAGS_EN = ['stressed', 'tired', 'energetic', 'calm', 'happy'];
const TAG_LABELS: Record<string, string> = {
  stresli: '😰 Stresli', yorgun: '😴 Yorgun', enerjik: '⚡ Enerjik', sakin: '🌊 Sakin', mutlu: '😊 Mutlu',
  stressed: '😰 Stressed', tired: '😴 Tired', energetic: '⚡ Energetic', calm: '🌊 Calm', happy: '😊 Happy',
};

interface Props {
  lang?: string;
  onCheckinDone?: (streak: number) => void;
  compact?: boolean;
}

export default function MoodCheckin({ lang = 'tr', onCheckinDone, compact = false }: Props) {
  const isTr = lang === 'tr';
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [checkedIn, setCheckedIn] = useState(false);
  const [todayScore, setTodayScore] = useState<number | null>(null);
  const [streak, setStreak] = useState(0);
  const [selected, setSelected] = useState<number | null>(null);
  const [selectedTags, setSelectedTags] = useState<string[]>([]);
  const [step, setStep] = useState<'mood' | 'tags' | 'done'>('mood');

  useEffect(() => {
    CheckinAPI.getToday()
      .then((d) => {
        setCheckedIn(d.checked_in);
        setTodayScore(d.mood_score);
        setStreak(d.streak);
        if (d.checked_in) setStep('done');
      })
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  const toggleTag = (tag: string) => {
    setSelectedTags((prev) =>
      prev.includes(tag) ? prev.filter((t) => t !== tag) : prev.length < 3 ? [...prev, tag] : prev,
    );
  };

  const submitCheckin = async () => {
    if (selected === null) return;
    setSaving(true);
    try {
      const res = await CheckinAPI.save(selected, selectedTags);
      setCheckedIn(true);
      setTodayScore(res.mood_score);
      const s = await CheckinAPI.getStreak();
      setStreak(s.streak);
      setStep('done');
      onCheckinDone?.(s.streak);
    } catch {
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return (
      <View style={styles.card}>
        <ActivityIndicator color="#C9A96E" />
      </View>
    );
  }

  if (compact && step === 'done') {
    const mood = MOODS.find((m) => m.score === todayScore);
    return (
      <View style={styles.compactBadge}>
        <Text style={styles.compactEmoji}>{mood?.emoji ?? '✅'}</Text>
        <Text style={styles.compactText}>
          {isTr ? `${streak} günlük seri` : `${streak}-day streak`}
        </Text>
        {streak > 0 && <Text style={styles.fire}>🔥</Text>}
      </View>
    );
  }

  if (step === 'done') {
    const mood = MOODS.find((m) => m.score === todayScore);
    return (
      <View style={styles.card}>
        <Text style={styles.doneEmoji}>{mood?.emoji ?? '✅'}</Text>
        <Text style={styles.doneTitle}>
          {isTr ? 'Bugünkü ruh halin kaydedildi!' : "Today's mood saved!"}
        </Text>
        {streak > 0 && (
          <Text style={styles.streakText}>
            🔥 {isTr ? `${streak} günlük seri` : `${streak}-day streak`}
          </Text>
        )}
      </View>
    );
  }

  const tags = isTr ? TAGS_TR : TAGS_EN;

  return (
    <View style={styles.card}>
      <Text style={styles.title}>
        {isTr ? 'Bugün nasıl hissediyorsun?' : 'How are you feeling today?'}
      </Text>

      {step === 'mood' && (
        <>
          <View style={styles.moodRow}>
            {MOODS.map((m) => (
              <TouchableOpacity
                accessibilityRole="button"
                accessibilityLabel={m.emoji}
                key={m.score}
                onPress={() => setSelected(m.score)}
                style={[styles.moodBtn, selected === m.score && styles.moodBtnSel]}
              >
                <Text style={styles.moodEmoji}>{m.emoji}</Text>
                <Text style={[styles.moodLabel, selected === m.score && styles.moodLabelSel]}>
                  {isTr ? m.label_tr : m.label_en}
                </Text>
              </TouchableOpacity>
            ))}
          </View>
          <TouchableOpacity
            accessibilityRole="button"
            accessibilityLabel="isTr ? 'Devam' : 'Next' →"
            style={[styles.nextBtn, selected === null && styles.nextBtnDisabled]}
            onPress={() => selected !== null && setStep('tags')}
            disabled={selected === null}
          >
            <Text style={styles.nextBtnText}>{isTr ? 'Devam' : 'Next'} →</Text>
          </TouchableOpacity>
        </>
      )}

      {step === 'tags' && (
        <>
          <Text style={styles.tagsHint}>
            {isTr ? 'Etiket seç (opsiyonel, max 3)' : 'Add tags (optional, max 3)'}
          </Text>
          <View style={styles.tagsRow}>
            {tags.map((tag) => (
              <TouchableOpacity
                accessibilityRole="button"
                accessibilityLabel='TAG_LABELS[tag]'
                key={tag}
                onPress={() => toggleTag(tag)}
                style={[styles.tagChip, selectedTags.includes(tag) && styles.tagChipSel]}
              >
                <Text style={[styles.tagText, selectedTags.includes(tag) && styles.tagTextSel]}>
                  {TAG_LABELS[tag]}
                </Text>
              </TouchableOpacity>
            ))}
          </View>
          <View style={styles.tagsBtns}>
            <TouchableOpacity style={styles.backBtn} onPress={() => setStep('mood')}
              accessibilityRole="button"
              accessibilityLabel="← isTr ? 'Geri' : 'Back'"
            >
              <Text style={styles.backBtnText}>← {isTr ? 'Geri' : 'Back'}</Text>
            </TouchableOpacity>
            <TouchableOpacity
              accessibilityRole="button"
              accessibilityLabel="isTr ? 'Kaydet' : 'Save' ✓"
              style={[styles.nextBtn, { flex: 1 }]}
              onPress={submitCheckin}
              disabled={saving}
            >
              {saving
                ? <ActivityIndicator color="#1A1A2E" size="small" />
                : <Text style={styles.nextBtnText}>{isTr ? 'Kaydet' : 'Save'} ✓</Text>
              }
            </TouchableOpacity>
          </View>
        </>
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  card: {
    backgroundColor: '#1E1E3A',
    borderRadius: 16,
    padding: 20,
    marginVertical: 8,
    alignItems: 'center',
  },
  title: {
    color: '#E8E8F0',
    fontSize: 16,
    fontWeight: '600',
    marginBottom: 16,
    textAlign: 'center',
  },
  moodRow: {
    flexDirection: 'row',
    gap: 8,
    marginBottom: 16,
  },
  moodBtn: {
    alignItems: 'center',
    paddingVertical: 10,
    paddingHorizontal: 8,
    borderRadius: 12,
    borderWidth: 1.5,
    borderColor: '#2A2A4A',
    minWidth: 58,
  },
  moodBtnSel: {
    borderColor: '#C9A96E',
    backgroundColor: 'rgba(201,169,110,0.12)',
  },
  moodEmoji: { fontSize: 26 },
  moodLabel: { color: '#888', fontSize: 11, marginTop: 4 },
  moodLabelSel: { color: '#C9A96E' },
  nextBtn: {
    backgroundColor: '#C9A96E',
    borderRadius: 12,
    paddingVertical: 12,
    paddingHorizontal: 32,
    alignItems: 'center',
    marginTop: 4,
  },
  nextBtnDisabled: { opacity: 0.4 },
  nextBtnText: { color: '#1A1A2E', fontWeight: '700', fontSize: 15 },
  tagsHint: { color: '#888', fontSize: 13, marginBottom: 12, textAlign: 'center' },
  tagsRow: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 8,
    justifyContent: 'center',
    marginBottom: 16,
  },
  tagChip: {
    borderWidth: 1.5,
    borderColor: '#2A2A4A',
    borderRadius: 20,
    paddingVertical: 6,
    paddingHorizontal: 14,
  },
  tagChipSel: {
    borderColor: '#C9A96E',
    backgroundColor: 'rgba(201,169,110,0.12)',
  },
  tagText: { color: '#888', fontSize: 13 },
  tagTextSel: { color: '#C9A96E' },
  tagsBtns: { flexDirection: 'row', gap: 10, width: '100%' },
  backBtn: {
    borderWidth: 1.5,
    borderColor: '#2A2A4A',
    borderRadius: 12,
    paddingVertical: 12,
    paddingHorizontal: 18,
    alignItems: 'center',
  },
  backBtnText: { color: '#888', fontSize: 14 },
  doneEmoji: { fontSize: 48, marginBottom: 8 },
  doneTitle: { color: '#E8E8F0', fontSize: 15, fontWeight: '600', marginBottom: 8 },
  streakText: { color: '#C9A96E', fontSize: 14, fontWeight: '700' },
  compactBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#1E1E3A',
    borderRadius: 12,
    paddingVertical: 8,
    paddingHorizontal: 14,
    gap: 6,
  },
  compactEmoji: { fontSize: 20 },
  compactText: { color: '#C9A96E', fontSize: 13, fontWeight: '600' },
  fire: { fontSize: 16 },
});

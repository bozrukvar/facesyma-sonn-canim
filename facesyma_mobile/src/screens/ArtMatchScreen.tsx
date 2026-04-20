// src/screens/ArtMatchScreen.tsx
// Yüz → sanat eseri eşleşmesi
import React, { useState } from 'react';
import { View, Text, StyleSheet, ScrollView, TouchableOpacity, ActivityIndicator, Image } from 'react-native';
import { launchImageLibrary, launchCamera } from 'react-native-image-picker';
import { Card, GoldButton } from '../components/ui';
import { AnalysisAPI } from '../services/api';
import theme from '../utils/theme';
import { useLanguage } from '../utils/LanguageContext';
import { t } from '../utils/i18n';

const ArtMatchScreen: React.FC<{ navigation: any; route: any }> = ({ navigation, route }) => {
  const [imageUri, setImageUri] = useState<string | null>(null);
  const [result,   setResult]   = useState<any>(null);
  const [loading,  setLoading]  = useState(false);
  const { lang } = useLanguage();

  const pickImage = () => launchImageLibrary({ mediaType: 'photo', quality: 0.85 }, res => {
    if (res.assets?.[0]?.uri) { setImageUri(res.assets[0].uri); setResult(null); }
  });

  const analyze = async () => {
    if (!imageUri) return;
    setLoading(true);
    try {
      const data = await AnalysisAPI.analyzeArt(imageUri, lang);
      setResult(data);
    } catch (e) { console.error(e); }
    finally { setLoading(false); }
  };

  return (
    <View style={styles.container}>
      <View style={styles.header}>
        <TouchableOpacity onPress={() => navigation.goBack()}>
          <Text style={styles.back}>←</Text>
        </TouchableOpacity>
        <Text style={styles.title}>{t('artmatch.title', lang)}</Text>
        <View style={{ width: 40 }} />
      </View>
      <ScrollView contentContainerStyle={styles.scroll} showsVerticalScrollIndicator={false}>
        {imageUri
          ? <Image source={{ uri: imageUri }} style={styles.preview} />
          : (
            <Card style={styles.pickArea}>
              <Text style={{ fontSize: 48, marginBottom: 12 }}>🎨</Text>
              <Text style={styles.pickText}>{t('artmatch.question', lang)}</Text>
            </Card>
          )
        }
        <GoldButton title={t('artmatch.choose_gallery', lang)} onPress={pickImage} variant="outline" style={{ marginBottom: 10 }} />
        {imageUri && (
          <GoldButton title={t('artmatch.match', lang)} onPress={analyze} loading={loading} />
        )}
        {result && (
          <Card variant="gold" style={{ marginTop: 16 }}>
            <Text style={styles.resultText}>{JSON.stringify(result, null, 2)}</Text>
          </Card>
        )}
      </ScrollView>
    </View>
  );
};

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: theme.colors.background },
  header: {
    flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between',
    paddingHorizontal: theme.spacing.lg, paddingTop: theme.spacing.lg + 44,
    paddingBottom: theme.spacing.md, borderBottomWidth: 1, borderBottomColor: theme.colors.border,
  },
  back:       { ...theme.typography.body, color: theme.colors.gold, fontSize: 22 },
  title:      { ...theme.typography.h3 },
  scroll:     { padding: theme.spacing.lg, paddingBottom: theme.spacing.xxxl },
  preview:    { width: '100%', height: 280, borderRadius: theme.radius.xl, marginBottom: 16 },
  pickArea:   { alignItems: 'center', padding: theme.spacing.xxxl, marginBottom: 16, borderStyle: 'dashed' },
  pickText:   { ...theme.typography.body, textAlign: 'center', color: theme.colors.textWarm },
  resultText: { ...theme.typography.bodyWarm, fontSize: 12, fontFamily: 'System' },
});

export default ArtMatchScreen;

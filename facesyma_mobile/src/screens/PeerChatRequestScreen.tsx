import React from 'react';
import { View, Text, StyleSheet, TouchableOpacity } from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import type { ScreenProps } from '../navigation/types';
import theme from '../utils/theme';
const { colors, spacing, typography } = theme;

const PeerChatRequestScreen: React.FC<ScreenProps<'PeerChatRequest'>> = ({ navigation }) => {
  const insets = useSafeAreaInsets();
  return (
    <View style={[styles.container, { paddingTop: insets.top }]}>
      <View style={styles.header}>
        <TouchableOpacity onPress={() => navigation.goBack()}>
          <Text style={styles.back}>←</Text>
        </TouchableOpacity>
        <Text style={styles.title}>Sohbet İsteği</Text>
        <View style={{ width: 32 }} />
      </View>
      <View style={styles.body}>
        <Text style={styles.icon}>🤝</Text>
        <Text style={styles.heading}>Yakında</Text>
        <Text style={styles.sub}>Sohbet isteği özelliği çok yakında geliyor.</Text>
      </View>
    </View>
  );
};

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: colors.background },
  header: {
    flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between',
    paddingHorizontal: spacing.lg, paddingVertical: spacing.md,
    borderBottomWidth: 1, borderBottomColor: colors.border,
  },
  back: { fontSize: 22, color: colors.gold, paddingRight: spacing.sm },
  title: { ...typography.h3, color: colors.textPrimary },
  body: { flex: 1, alignItems: 'center', justifyContent: 'center', padding: spacing.xl },
  icon: { fontSize: 56, marginBottom: spacing.lg },
  heading: { ...typography.h2, color: colors.textPrimary, marginBottom: spacing.sm },
  sub: { ...typography.body, color: colors.textMuted, textAlign: 'center' },
});

export default PeerChatRequestScreen;

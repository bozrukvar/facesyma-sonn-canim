/**
 * OfflineBanner — slim bar that slides in at the top when the device loses
 * internet access, and slides back out when it reconnects.
 *
 * Mount once inside AppNavigator, above <NavigationContainer>.
 */
import React, { useEffect, useRef, useState } from 'react';
import { Animated, StyleSheet, Text, View } from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { useIsOffline } from '../utils/NetworkContext';
import { useLanguage } from '../utils/LanguageContext';
import { t } from '../utils/i18n';

const BANNER_H = 36;

const OfflineBanner: React.FC = () => {
  const offline    = useIsOffline();
  const { lang }   = useLanguage();
  const insets     = useSafeAreaInsets();
  const slideAnim  = useRef(new Animated.Value(-BANNER_H)).current;
  // Track whether we were ever offline so we can show "back online" briefly
  const [wasOffline, setWasOffline] = useState(false);
  const [showOnline, setShowOnline] = useState(false);
  const onlineTimer = useRef<ReturnType<typeof setTimeout> | null>(null);

  useEffect(() => {
    if (offline) {
      setWasOffline(true);
      setShowOnline(false);
      if (onlineTimer.current) clearTimeout(onlineTimer.current);
      Animated.spring(slideAnim, {
        toValue: 0,
        useNativeDriver: true,
        speed: 20,
        bounciness: 4,
      }).start();
    } else {
      if (wasOffline) {
        // Show "back online" message briefly before hiding
        setShowOnline(true);
        Animated.spring(slideAnim, {
          toValue: 0,
          useNativeDriver: true,
          speed: 20,
          bounciness: 4,
        }).start();
        onlineTimer.current = setTimeout(() => {
          Animated.timing(slideAnim, {
            toValue: -(BANNER_H + insets.top),
            duration: 300,
            useNativeDriver: true,
          }).start(() => {
            setShowOnline(false);
            setWasOffline(false);
          });
        }, 2500);
      } else {
        // Never went offline — keep hidden
        slideAnim.setValue(-(BANNER_H + insets.top));
      }
    }
    return () => {
      if (onlineTimer.current) clearTimeout(onlineTimer.current);
    };
  }, [offline]);

  const isVisible = offline || showOnline;
  if (!isVisible) return null;

  const bgColor  = showOnline ? '#27AE60' : '#C0392B';
  const icon     = showOnline ? '✓' : '⚠';
  const message  = showOnline
    ? t('offline.back_online', lang)
    : t('offline.no_connection', lang);

  return (
    <Animated.View
      style={[
        styles.banner,
        { backgroundColor: bgColor, paddingTop: insets.top, transform: [{ translateY: slideAnim }] },
      ]}
      accessibilityRole="alert"
      accessibilityLabel={message}
      accessibilityLiveRegion="polite"
    >
      <Text style={styles.text}>{icon}  {message}</Text>
    </Animated.View>
  );
};

const styles = StyleSheet.create({
  banner: {
    position:       'absolute',
    top:            0,
    left:           0,
    right:          0,
    zIndex:         9999,
    height:         BANNER_H + 44, // safe area + bar
    alignItems:     'center',
    justifyContent: 'flex-end',
    paddingBottom:  8,
  },
  text: {
    color:      '#fff',
    fontSize:   13,
    fontWeight: '600',
    fontFamily: 'System',
    letterSpacing: 0.2,
  },
});

export default OfflineBanner;

// App.tsx — Facesyma React Native Giriş Noktası
import React from 'react';
import { Provider } from 'react-redux';
import { GestureHandlerRootView } from 'react-native-gesture-handler';
import { SafeAreaProvider } from 'react-native-safe-area-context';
import { store } from './src/store';
import AppNavigator from './src/navigation/AppNavigator';
import { LanguageProvider } from './src/utils/LanguageContext';

const App = () => (
  <GestureHandlerRootView style={{ flex: 1, backgroundColor: '#0A0F14' }}>
    <SafeAreaProvider>
      <Provider store={store}>
        <LanguageProvider>
          <AppNavigator />
        </LanguageProvider>
      </Provider>
    </SafeAreaProvider>
  </GestureHandlerRootView>
);

export default App;

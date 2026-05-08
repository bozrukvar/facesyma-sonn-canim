/**
 * NetworkContext — global internet connection state.
 *
 * Usage:
 *   const { isConnected, isInternetReachable } = useNetwork();
 *
 * Both flags are null until the first NetInfo event fires (usually < 200ms).
 * Treat null as "unknown / assume connected" to avoid blocking the UI on startup.
 */
import React, { createContext, useContext, useEffect, useState } from 'react';
import NetInfo, { NetInfoState } from '@react-native-community/netinfo';

interface NetworkState {
  isConnected: boolean | null;
  isInternetReachable: boolean | null;
  type: string;
}

const NetworkContext = createContext<NetworkState>({
  isConnected: null,
  isInternetReachable: null,
  type: 'unknown',
});

export const NetworkProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [state, setState] = useState<NetworkState>({
    isConnected: null,
    isInternetReachable: null,
    type: 'unknown',
  });

  useEffect(() => {
    // Fetch once immediately
    NetInfo.fetch().then((s: NetInfoState) => {
      setState({
        isConnected:        s.isConnected,
        isInternetReachable: s.isInternetReachable,
        type: s.type,
      });
    });

    // Subscribe to changes
    const unsub = NetInfo.addEventListener((s: NetInfoState) => {
      setState({
        isConnected:        s.isConnected,
        isInternetReachable: s.isInternetReachable,
        type: s.type,
      });
    });

    return unsub;
  }, []);

  return (
    <NetworkContext.Provider value={state}>
      {children}
    </NetworkContext.Provider>
  );
};

export const useNetwork = () => useContext(NetworkContext);

/** Returns true when we're definitely offline (not null = unknown). */
export const useIsOffline = (): boolean => {
  const { isConnected, isInternetReachable } = useNetwork();
  // null means "not yet measured" — don't block
  if (isConnected === null) return false;
  // Connected to wifi/cellular but no internet (captive portal, etc.)
  if (isConnected === true && isInternetReachable === false) return true;
  return isConnected === false;
};

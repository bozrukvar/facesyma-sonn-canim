// React Native Metro global — injected at bundle time
declare const __DEV__: boolean;

// expo-file-system — types not bundled; minimal declaration for type checking
declare module 'expo-file-system' {
  export function getInfoAsync(uri: string, options?: { size?: boolean; md5?: boolean }): Promise<{ exists: boolean; uri: string; size?: number; isDirectory: boolean; md5?: string; modificationTime?: number }>;
  export function readAsStringAsync(uri: string, options?: { encoding?: string; position?: number; length?: number }): Promise<string>;
  export function writeAsStringAsync(uri: string, contents: string, options?: { encoding?: string }): Promise<void>;
  export function deleteAsync(uri: string, options?: { idempotent?: boolean }): Promise<void>;
  export function moveAsync(options: { from: string; to: string }): Promise<void>;
  export function copyAsync(options: { from: string; to: string }): Promise<void>;
  export function makeDirectoryAsync(uri: string, options?: { intermediates?: boolean }): Promise<void>;
  export const documentDirectory: string | null;
  export const cacheDirectory: string | null;
}

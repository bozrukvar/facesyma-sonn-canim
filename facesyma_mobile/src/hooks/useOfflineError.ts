/**
 * useOfflineError — maps API errors to user-facing messages.
 *
 * Usage in any screen:
 *   const getErrorMessage = useOfflineError();
 *   ...
 *   } catch (err) {
 *     setError(getErrorMessage(err));
 *   }
 */
import { useLanguage } from '../utils/LanguageContext';
import { t } from '../utils/i18n';

export const useOfflineError = () => {
  const { lang } = useLanguage();

  return (err: unknown): string => {
    if (!err || typeof err !== 'object') return t('common.generic_error', lang);

    const e = err as Record<string, unknown>;

    // Flagged by our axios retry interceptor after all retries failed
    if (e.isOfflineError) return t('offline.retry', lang);

    // Network error without response (DNS / connection refused / timeout)
    if (!e.response && e.request) return t('offline.retry', lang);

    // Explicit error codes
    const code = typeof e.code === 'string' ? e.code : '';
    if (['ECONNABORTED', 'ETIMEDOUT', 'ERR_NETWORK', 'ENOTFOUND', 'ECONNRESET'].includes(code)) {
      return t('offline.retry', lang);
    }

    // Server error with a detail message
    const resp = e.response as Record<string, unknown> | undefined;
    if (resp?.data && typeof resp.data === 'object') {
      const detail = (resp.data as Record<string, unknown>).detail;
      if (typeof detail === 'string' && detail) return detail;
    }

    return t('common.generic_error', lang);
  };
};

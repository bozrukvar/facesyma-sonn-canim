/**
 * PurchaseService.js
 * ==================
 * RevenueCat Integration for In-App Purchases
 * - iOS App Store
 * - Android Google Play Store
 * - Global pricing (150+ countries auto-configured)
 */

import Purchases, {
  CustomerInfo,
  LOG_LEVEL,
  PURCHASE_TYPE,
} from 'react-native-purchases';

// ── RevenueCat Configuration ────────────────────────────────────────────────
const RC_API_KEYS = {
  ios: 'appl_xxxxxxxxxxxxxxxxxxxxxx', // Set in env vars for production
  android: 'goog_xxxxxxxxxxxxxxxxxxxxxx',
};

class PurchaseService {
  constructor() {
    this.isInitialized = false;
    this.customerInfo = null;
    this.purchaseUpdatedListener = null;
  }

  /**
   * Initialize RevenueCat SDK
   * Must be called on app startup
   */
  async initialize() {
    if (this.isInitialized) return;

    try {
      // Enable debug logging in development
      if (__DEV__) {
        Purchases.setLogLevel(LOG_LEVEL.VERBOSE);
      }

      // Configure SDK with platform-specific API key
      const apiKey = Platform.OS === 'ios' ? RC_API_KEYS.ios : RC_API_KEYS.android;

      await Purchases.configure({
        apiKey,
        appUserID: null, // RevenueCat generates anonymous ID
        observerMode: false,
      });

      // Get initial customer info
      const info = await Purchases.getCustomerInfo();
      this.customerInfo = info;

      // Setup listener for purchase updates
      this.setupPurchaseListener();

      this.isInitialized = true;
      console.log('✅ RevenueCat initialized');
    } catch (error) {
      console.error('❌ RevenueCat init error:', error);
      throw error;
    }
  }

  /**
   * Set user ID (after login)
   */
  async setUserID(userID) {
    try {
      await Purchases.logIn(userID);
      console.log(`✅ RevenueCat user set: ${userID}`);
    } catch (error) {
      console.error('❌ Error setting user ID:', error);
    }
  }

  /**
   * Get available subscription packages
   * Returns auto-localized pricing for user's country
   */
  async getSubscriptionPackages() {
    try {
      const offerings = await Purchases.getOfferings();

      if (!offerings.current) {
        console.warn('No current offering available');
        return [];
      }

      // Format packages for UI
      return offerings.current.availablePackages.map((pkg) => ({
        id: pkg.identifier,
        price: pkg.product.priceString,
        currency: pkg.product.currencyCode,
        duration: pkg.packageType, // MONTHLY, THREE_MONTH, ANNUAL, etc.
        title: pkg.product.title,
        description: pkg.product.description,
        localizedPrice: pkg.product.priceString,
        countryCode: Purchases.getCountryCode?.(), // User's country
      }));
    } catch (error) {
      console.error('❌ Error fetching packages:', error);
      return [];
    }
  }

  /**
   * Purchase subscription
   * @param {String} packageID - RevenueCat package ID
   */
  async purchasePackage(packageID) {
    try {
      const offerings = await Purchases.getOfferings();
      const pkg = offerings.current?.availablePackages.find(
        (p) => p.identifier === packageID
      );

      if (!pkg) {
        throw new Error(`Package not found: ${packageID}`);
      }

      const customerInfo = await Purchases.purchasePackage(pkg);
      this.customerInfo = customerInfo;

      console.log('✅ Purchase successful:', customerInfo);
      return customerInfo;
    } catch (error) {
      if (error.userCancelled) {
        console.log('⚠️  User cancelled purchase');
      } else {
        console.error('❌ Purchase error:', error);
      }
      throw error;
    }
  }

  /**
   * Get current subscription status
   */
  async getSubscriptionStatus() {
    try {
      const info = await Purchases.getCustomerInfo();
      this.customerInfo = info;

      const activeSubscriptions = Object.keys(
        info.activeSubscriptions || {}
      );

      return {
        isPremium: activeSubscriptions.length > 0,
        activeSubscriptions,
        entitlements: info.entitlements.active,
        expirationDates: info.expirationDatesByEntitlement,
        originalPurchaseDate: info.originalPurchaseDate,
      };
    } catch (error) {
      console.error('❌ Error getting subscription status:', error);
      return { isPremium: false };
    }
  }

  /**
   * Check if user has specific entitlement
   * @param {String} entitlementID - e.g., "premium"
   */
  async hasEntitlement(entitlementID) {
    try {
      const status = await this.getSubscriptionStatus();
      return !!status.entitlements[entitlementID];
    } catch (error) {
      console.error('❌ Error checking entitlement:', error);
      return false;
    }
  }

  /**
   * Restore past purchases
   */
  async restorePurchases() {
    try {
      const customerInfo = await Purchases.restorePurchases();
      this.customerInfo = customerInfo;
      console.log('✅ Purchases restored');
      return customerInfo;
    } catch (error) {
      console.error('❌ Error restoring purchases:', error);
      throw error;
    }
  }

  /**
   * Get refund status or manage subscription
   */
  async manageSubscriptions() {
    try {
      await Purchases.beginRefundRequest();
      console.log('✅ Subscription management opened');
    } catch (error) {
      console.error('❌ Error managing subscriptions:', error);
    }
  }

  /**
   * Setup listener for purchase updates (background subscriptions)
   */
  setupPurchaseListener() {
    this.purchaseUpdatedListener = Purchases.purchaseUpdatedListener(
      (info) => {
        this.customerInfo = info;
        console.log('📱 Purchase updated:', info);
        // Notify listeners via Redux/Context
      }
    );
  }

  /**
   * Cleanup
   */
  cleanup() {
    if (this.purchaseUpdatedListener) {
      this.purchaseUpdatedListener.remove();
    }
  }
}

// Export singleton
export default new PurchaseService();

"""
admin_api/utils/payment_gateway_abstract.py
============================================
Abstract base classes for payment gateway integration.

Active providers:
  - GOOGLE_PAY  (client-side)
  - APPLE_PAY   (client-side)
  - VAKIFBANK_VPP (TODO: ileriki versiyon)
"""

from abc import ABC, abstractmethod
from enum import Enum
from typing import Dict, Optional, Any
from datetime import datetime
import logging

log = logging.getLogger(__name__)


class PaymentProviderType(Enum):
    """Supported payment providers"""
    REVENUECAT   = 'revenuecat'    # Mobile In-App Purchase
    GOOGLE_PAY   = 'google_pay'    # Google Pay (client-side)
    APPLE_PAY    = 'apple_pay'     # Apple Pay (client-side)
    VAKIFBANK_VPP = 'vakifbank_vpp' # Vakıfbank Sanal Pos (TODO: ileriki versiyon)


class PaymentStatus(Enum):
    """Payment transaction status"""
    PENDING = 'pending'
    PROCESSING = 'processing'
    COMPLETED = 'completed'
    FAILED = 'failed'
    CANCELLED = 'cancelled'
    REFUNDED = 'refunded'
    DISPUTED = 'disputed'


class SubscriptionStatus(Enum):
    """Subscription lifecycle status"""
    ACTIVE = 'active'
    PAUSED = 'paused'
    CANCELLED = 'cancelled'
    EXPIRED = 'expired'
    PAYMENT_FAILED = 'payment_failed'


class PaymentGatewayException(Exception):
    """Base exception for payment processing errors"""
    pass


class PaymentTransaction:
    """Immutable payment transaction record"""

    def __init__(
        self,
        user_id: int,
        provider: PaymentProviderType,
        amount: float,
        currency: str,
        status: PaymentStatus,
        transaction_id: str,
        reference_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        self.user_id = user_id
        self.provider = provider
        self.amount = amount
        self.currency = currency
        self.status = status
        self.transaction_id = transaction_id
        self.reference_id = reference_id
        self.metadata = metadata or {}
        self.created_at = datetime.utcnow().isoformat()

    def to_dict(self) -> Dict:
        return {
            'user_id': self.user_id,
            'provider': self.provider.value,
            'amount': self.amount,
            'currency': self.currency,
            'status': self.status.value,
            'transaction_id': self.transaction_id,
            'reference_id': self.reference_id,
            'metadata': self.metadata,
            'created_at': self.created_at,
        }


class BasePaymentGateway(ABC):
    """
    Abstract base class for all payment gateway implementations.
    Each concrete provider must implement these methods.
    """

    def __init__(self, api_key: str, api_secret: Optional[str] = None):
        self.api_key = api_key
        self.api_secret = api_secret
        self.provider_type = None

    @abstractmethod
    async def verify_payment(
        self,
        user_id: int,
        payment_id: str,
        amount: float,
        currency: str,
    ) -> PaymentTransaction:
        """
        Verify a payment was processed successfully.
        Must return a PaymentTransaction with status=COMPLETED or raise PaymentGatewayException.
        """
        pass

    @abstractmethod
    async def process_payment(
        self,
        user_id: int,
        amount: float,
        currency: str,
        payment_method_id: str,
        metadata: Optional[Dict] = None,
    ) -> PaymentTransaction:
        """
        Process a new payment transaction.
        Handles charge authorization, risk checks, and transaction creation.
        """
        pass

    @abstractmethod
    async def refund_payment(
        self,
        transaction_id: str,
        amount: Optional[float] = None,  # None = full refund
        reason: Optional[str] = None,
    ) -> PaymentTransaction:
        """
        Refund a completed payment (full or partial).
        Must return updated PaymentTransaction with status=REFUNDED.
        """
        pass

    @abstractmethod
    async def cancel_subscription(
        self,
        subscription_id: str,
    ) -> Dict[str, Any]:
        """Cancel an active subscription immediately."""
        pass

    @abstractmethod
    async def get_subscription_status(
        self,
        subscription_id: str,
    ) -> Dict[str, Any]:
        """
        Get current subscription status.
        Returns dict with keys: status, next_billing_date, plan_id, amount, currency
        """
        pass

    @abstractmethod
    async def health_check(self) -> bool:
        """Verify API connectivity to payment provider"""
        pass


class BaseEWalletGateway(BasePaymentGateway):
    """
    Abstract base for e-wallet integrations (Papara, Tuum, etc).
    E-wallets typically require user authentication/redirect flow.
    """

    @abstractmethod
    async def get_user_wallet_balance(self, user_wallet_id: str) -> float:
        """Get user's e-wallet balance"""
        pass

    @abstractmethod
    async def initiate_wallet_payment(
        self,
        user_id: int,
        user_wallet_id: str,
        amount: float,
        currency: str,
        return_url: str,
    ) -> Dict[str, str]:
        """
        Initiate payment from user's e-wallet.
        Returns dict with 'payment_id', 'redirect_url' (if needed), 'status'
        """
        pass


class BaseCryptoGateway(BasePaymentGateway):
    """
    Abstract base for cryptocurrency payment integrations.
    Supports Bitcoin, Ethereum, USDC, etc.
    """

    @abstractmethod
    async def create_payment_address(
        self,
        user_id: int,
        amount: float,
        cryptocurrency: str,  # 'bitcoin', 'ethereum', 'usdc', etc.
        expiry_minutes: int = 15,
    ) -> Dict[str, str]:
        """
        Create a unique payment address for user.
        Returns: {'address': '...', 'amount': '...', 'currency': '...', 'expires_at': '...'}
        """
        pass

    @abstractmethod
    async def check_payment_confirmation(
        self,
        payment_address: str,
        confirmations_required: int = 1,
    ) -> bool:
        """Check if payment to address has been confirmed on blockchain"""
        pass

    @abstractmethod
    async def get_conversion_rate(
        self,
        cryptocurrency: str,
        fiat_currency: str,  # 'USD', 'EUR', 'TRY', etc.
    ) -> float:
        """Get current conversion rate cryptocurrency -> fiat"""
        pass


class PaymentGatewayFactory:
    """
    Factory for creating and managing payment gateway instances.
    Supports runtime provider switching and multi-provider orchestration.
    """

    _gateways: Dict[PaymentProviderType, BasePaymentGateway] = {}

    @classmethod
    def register_gateway(
        cls,
        provider: PaymentProviderType,
        gateway: BasePaymentGateway,
    ) -> None:
        """Register a payment gateway implementation"""
        cls._gateways[provider] = gateway
        log.info(f'Registered payment gateway: {provider.value}')

    @classmethod
    def get_gateway(cls, provider: PaymentProviderType) -> BasePaymentGateway:
        """Get a registered gateway by provider type"""
        _cg = cls._gateways
        if provider not in _cg:
            raise PaymentGatewayException(
                f'Payment gateway not registered: {provider.value}'
            )
        return _cg[provider]

    @classmethod
    def list_available_gateways(cls) -> Dict[str, bool]:
        """List all available payment methods"""
        return {
            provider.value: provider in cls._gateways
            for provider in PaymentProviderType
        }

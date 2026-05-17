from __future__ import annotations

import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional


@dataclass
class PaymentResult:
    success: bool
    payment_ref: Optional[str] = None
    message: str = ""


class PaymentProvider(ABC):
    @abstractmethod
    def pay(self, order_id: int, amount: float, *, simulate_success: bool = True) -> PaymentResult:
        ...


class MockPaymentProvider(PaymentProvider):
    """本地模拟支付，便于教学与联调；真实网关可新增 WeChatPayProvider 等实现。"""

    def pay(self, order_id: int, amount: float, *, simulate_success: bool = True) -> PaymentResult:
        if not simulate_success:
            return PaymentResult(success=False, message="模拟支付失败")
        ref = f"MOCK-{order_id}-{uuid.uuid4().hex[:12].upper()}"
        return PaymentResult(success=True, payment_ref=ref, message="模拟支付成功")


def get_payment_provider() -> PaymentProvider:
    return MockPaymentProvider()

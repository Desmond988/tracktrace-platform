"""add FAILED_DELIVERY_ATTEMPT status

Data-only migration (no schema change). Added after a capability audit against FedEx, UPS, and
AfterShip's public documentation, all of which treat a failed delivery attempt as a distinct,
common milestone. Sorted between OUT_FOR_DELIVERY (110) and DELIVERED (120).

Revision ID: 9d4e2f7a1b3c
Revises: 271c71a84f45
"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB

revision = "9d4e2f7a1b3c"
down_revision = "271c71a84f45"
branch_labels = None
depends_on = None

LABEL = {
    "en": "Failed Delivery Attempt", "fr": "Tentative de livraison échouée", "es": "Intento de entrega fallido",
    "de": "Zustellversuch fehlgeschlagen", "pt": "Tentativa de entrega malsucedida", "it": "Tentativo di consegna fallito",
    "nl": "Mislukte bezorgpoging", "pl": "Nieudana próba doręczenia", "ru": "Неудачная попытка доставки",
    "tr": "Başarısız teslimat denemesi", "ar": "فشلت محاولة التسليم", "zh": "配送失败",
    "ja": "配達失敗", "ko": "배송 실패", "hi": "डिलीवरी प्रयास विफल", "sw": "Jaribio la Uwasilishaji Limeshindwa",
}


def upgrade() -> None:
    statuses = sa.table("shipment_statuses", sa.column("code"), sa.column("label", JSONB), sa.column("sort_order"),
                        sa.column("is_terminal"), sa.column("is_problem"), sa.column("is_active"), sa.column("notify_customer"))
    op.bulk_insert(statuses, [dict(code="FAILED_DELIVERY_ATTEMPT", label=LABEL, sort_order=115,
                                   is_terminal=False, is_problem=True, is_active=True, notify_customer=True)])


def downgrade() -> None:
    op.execute("DELETE FROM shipment_statuses WHERE code = 'FAILED_DELIVERY_ATTEMPT'")

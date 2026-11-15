"""add RETURNED_TO_SENDER status

Data-only migration (no schema change). Requested explicitly as a required milestone.

Semantics, chosen to match how the existing event logic already behaves:
- is_terminal=True: a returned shipment has no further forward movement. It leaves the "active"
  dashboard count, and (per add_event) only ADMIN/SUPER_ADMIN may reopen it afterwards.
- is_problem=True: the shipment was not delivered to the recipient, so the public page shows the
  what-happened / what-next banner instead of a progress bar.
- It never sets actual_delivery (that is reserved for DELIVERED), so a returned parcel can never
  appear delivered.

Revision ID: b7c1d9e84a52
Revises: 9d4e2f7a1b3c
"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB

revision = "b7c1d9e84a52"
down_revision = "9d4e2f7a1b3c"
branch_labels = None
depends_on = None

LABEL = {
    "en": "Returned to Sender", "fr": "Retourné à l'expéditeur", "es": "Devuelto al remitente",
    "de": "An Absender zurückgesendet", "pt": "Devolvido ao remetente", "it": "Restituito al mittente",
    "nl": "Teruggestuurd naar afzender", "pl": "Zwrócono do nadawcy", "ru": "Возвращено отправителю",
    "tr": "Gönderene iade edildi", "ar": "أُعيدت إلى المرسل", "zh": "已退回发件人",
    "ja": "差出人へ返送", "ko": "발송인에게 반송됨", "hi": "प्रेषक को लौटाया गया", "sw": "Imerudishwa kwa Mtumaji",
}


def upgrade() -> None:
    statuses = sa.table("shipment_statuses", sa.column("code"), sa.column("label", JSONB), sa.column("sort_order"),
                        sa.column("is_terminal"), sa.column("is_problem"), sa.column("is_active"), sa.column("notify_customer"))
    op.bulk_insert(statuses, [dict(code="RETURNED_TO_SENDER", label=LABEL, sort_order=145,
                                   is_terminal=True, is_problem=True, is_active=True, notify_customer=True)])


def downgrade() -> None:
    op.execute("DELETE FROM shipment_statuses WHERE code = 'RETURNED_TO_SENDER'")

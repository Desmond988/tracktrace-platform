"""fix stale users.preferred_language check constraint to allow all 16 supported languages

The constraint was hardcoded to ('en','fr') and never updated when the platform's supported
language set grew to 16 (see app.services.i18n.SUPPORTED_LANGUAGES). It silently rejected any of
the other 14 languages at the database layer even though API-level validation had already been
fixed to accept them - discovered via a real end-to-end HTTP test against a live server, not by
the unit test suite (which only exercised the Pydantic schema, never the database constraint).

Revision ID: 271c71a84f45
Revises: a1b2c3d4e5f6
"""
from alembic import op

from app.services.i18n import LANGUAGE_CODES

revision = "271c71a84f45"
down_revision = "a1b2c3d4e5f6"
branch_labels = None
depends_on = None

_OLD = "preferred_language IN ('en','fr')"
_NEW_LIST = ",".join(f"'{c}'" for c in sorted(LANGUAGE_CODES))
_NEW = f"preferred_language IN ({_NEW_LIST})"


def upgrade() -> None:
    op.drop_constraint("ck_users_language", "users", type_="check")
    op.create_check_constraint("ck_users_language", "users", _NEW)


def downgrade() -> None:
    op.drop_constraint("ck_users_language", "users", type_="check")
    op.create_check_constraint("ck_users_language", "users", _OLD)

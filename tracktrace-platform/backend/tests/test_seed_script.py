import pathlib
import re

from app.schemas.auth import LoginIn


def test_dev_seed_accounts_use_addresses_the_login_api_accepts():
    """Regression: the seed once created admin@example.test etc. The login schema rejects the reserved
    .test domain (422), so every seeded demo account was impossible to sign in to."""
    src = pathlib.Path(__file__).resolve().parents[1].joinpath("scripts/seed_dev.py").read_text()
    emails = re.findall(r'get_or_create_user\("([^"]+)"', src)
    assert len(emails) == 4
    for email in emails:
        LoginIn(email=email, password="x")  # raises ValidationError if /api/auth/login would reject this address

"""Role -> permission matrix. Enforced in the backend by `require_perms` dependencies."""
STAFF_PERMS = {"shipments:read", "shipments:write", "events:write", "documents:write", "customers:read", "customers:write",
               "quotes:manage", "messages:manage", "notifications:read"}
OPERATIONS_PERMS = STAFF_PERMS | {"reports:read", "statuses:manage", "locations:manage"}
ADMIN_PERMS = OPERATIONS_PERMS | {"users:read", "users:write", "audit:read", "settings:read", "settings:write", "legal:write", "faq:write"}
SUPER_ADMIN_PERMS = ADMIN_PERMS | {"settings:sensitive"}

ROLE_PERMISSIONS: dict[str, set[str]] = {
    "SUPER_ADMIN": SUPER_ADMIN_PERMS,
    "ADMIN": ADMIN_PERMS,
    "OPERATIONS": OPERATIONS_PERMS,
    "STAFF": STAFF_PERMS,
    "CUSTOMER": set(),
}
STAFF_ROLES = ("SUPER_ADMIN", "ADMIN", "OPERATIONS", "STAFF")
# Which roles each role may create/edit/delete (admins cannot mint or touch super admins)
MANAGEABLE_ROLES = {
    "SUPER_ADMIN": {"SUPER_ADMIN", "ADMIN", "OPERATIONS", "STAFF", "CUSTOMER"},
    "ADMIN": {"OPERATIONS", "STAFF", "CUSTOMER"},
}


def has_perm(role: str, perm: str) -> bool:
    return perm in ROLE_PERMISSIONS.get(role, set())

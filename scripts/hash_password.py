"""Print a bcrypt hash for ADMIN_PASSWORD_HASH. Usage: python -m scripts.hash_password"""

from __future__ import annotations

import getpass

import bcrypt


def main() -> None:
    password = getpass.getpass("New admin password: ")
    if len(password) < 10:
        raise SystemExit("Use at least 10 characters.")
    hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
    print(f"ADMIN_PASSWORD_HASH='{hashed}'")


if __name__ == "__main__":
    main()

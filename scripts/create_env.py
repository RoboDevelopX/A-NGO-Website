"""Create a local .env with a random SECRET_KEY and a random admin password.

Run once via ``make setup``. Prints the admin password a single time; only its bcrypt hash
is written to disk. Refuses to overwrite an existing .env.
"""

from __future__ import annotations

import secrets
import sys
from pathlib import Path

import bcrypt

ROOT = Path(__file__).resolve().parent.parent


def main() -> int:
    env_path = ROOT / ".env"
    if env_path.exists():
        print(".env already exists; leaving it unchanged.")
        return 0
    template = (ROOT / ".env.example").read_text(encoding="utf-8")
    password = secrets.token_urlsafe(12)
    password_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
    content = template.replace("SECRET_KEY=", f"SECRET_KEY={secrets.token_urlsafe(32)}", 1)
    # Single quotes stop dotenv from treating the "$" signs in the bcrypt hash as variables.
    content = content.replace("ADMIN_PASSWORD_HASH=", f"ADMIN_PASSWORD_HASH='{password_hash}'", 1)
    env_path.write_text(content, encoding="utf-8")
    print("Created .env")
    print(f"Admin login for /admin -> username: admin  password: {password}")
    print("(Shown once. Run `make admin-password` to set a new one.)")
    return 0


if __name__ == "__main__":
    sys.exit(main())

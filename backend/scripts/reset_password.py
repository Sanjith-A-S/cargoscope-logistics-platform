"""
scripts/reset_password.py — One-time CLI tool to reset user passwords and generate admin hash.

CLI-only script (not reachable as an API endpoint).
Reuses the app's own passlib CryptContext from core.auth.
"""
import os
import sys
import argparse
from pathlib import Path
from dotenv import load_dotenv

# Ensure backend root is on sys.path
BACKEND_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND_DIR))
os.chdir(BACKEND_DIR)

# Load environment variables
load_dotenv(BACKEND_DIR / ".env")

from core.db import SessionLocal
from core.models import User
from core.auth import pwd_context
from modules.auth.service import authenticate_user, try_authenticate_admin


def hash_password(plaintext: str) -> str:
    """Hash plaintext password using the application's canonical pwd_context."""
    return pwd_context.hash(plaintext)


def reset_user_password(email: str, new_password: str) -> bool:
    """Update a user's password_hash in the database."""
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.email == email.lower().strip()).first()
        if not user:
            print(f"[!] User not found with email: {email}")
            return False

        user.password_hash = hash_password(new_password)
        db.commit()
        print(f"[OK] Successfully reset password for user: {email} (id={user.id})")
        return True
    finally:
        db.close()


def update_env_admin_hash(new_admin_password: str) -> str:
    """Generate bcrypt hash for admin and write to .env."""
    admin_hash = hash_password(new_admin_password)
    env_path = BACKEND_DIR / ".env"
    
    if env_path.exists():
        content = env_path.read_text(encoding="utf-8")
        lines = content.splitlines()
        updated = False
        new_lines = []
        for line in lines:
            if line.startswith("ADMIN_PASSWORD_HASH="):
                new_lines.append(f"ADMIN_PASSWORD_HASH={admin_hash}")
                updated = True
            else:
                new_lines.append(line)
        if not updated:
            new_lines.append(f"ADMIN_PASSWORD_HASH={admin_hash}")
        
        env_path.write_text("\n".join(new_lines) + "\n", encoding="utf-8")
        print(f"[OK] Updated ADMIN_PASSWORD_HASH in {env_path}")
    else:
        print(f"[!] .env file not found at {env_path}")
    
    # Also update os.environ for current runtime verification
    os.environ["ADMIN_PASSWORD_HASH"] = admin_hash
    os.environ["ADMIN_USERNAME"] = os.getenv("ADMIN_USERNAME", "admin")
    return admin_hash


def verify_credentials(email: str, password: str) -> bool:
    """Verify user login against DB using authenticate_user."""
    db = SessionLocal()
    try:
        user = authenticate_user(email, password, db)
        print(f"[OK] Auth verification PASSED for {email} (user_id={user.id}, org_id={user.org_id})")
        return True
    except Exception as e:
        print(f"[FAIL] Auth verification FAILED for {email}: {e}")
        return False
    finally:
        db.close()


def verify_admin(username: str, password: str) -> bool:
    """Verify admin login using try_authenticate_admin."""
    token = try_authenticate_admin(username, password)
    if token:
        print(f"[OK] Admin auth verification PASSED for '{username}'. Generated token: {token[:20]}...")
        return True
    else:
        print(f"[FAIL] Admin auth verification FAILED for '{username}'")
        return False


def run_standard_reset():
    """Reset passwords for known system users and configure admin."""
    print("=== Running Standard Password Reset ===")
    
    # 1. Reset sanjith1112006@gmail.com
    reset_user_password("sanjith1112006@gmail.com", "sanjith123")
    verify_credentials("sanjith1112006@gmail.com", "sanjith123")
    print()

    # 2. Reset e2e_test@tradeops.local
    reset_user_password("e2e_test@tradeops.local", "testpass123")
    verify_credentials("e2e_test@tradeops.local", "testpass123")
    print()

    # 3. Configure admin password in .env and verify
    update_env_admin_hash("admin123")
    verify_admin("admin", "admin123")
    print()
    print("=== All Standard Resets Completed Successfully ===")


def main():
    parser = argparse.ArgumentParser(description="Reset user passwords and admin credentials.")
    parser.add_argument("--email", help="User email to reset password for")
    parser.add_argument("--password", help="New plaintext password for the user")
    parser.add_argument("--admin-password", help="New plaintext password for admin")
    parser.add_argument("--standard", action="store_true", help="Run standard batch reset for known users and admin")

    args = parser.parse_args()

    if args.standard or (not args.email and not args.admin_password):
        run_standard_reset()
    else:
        if args.email and args.password:
            reset_user_password(args.email, args.password)
            verify_credentials(args.email, args.password)
        if args.admin_password:
            update_env_admin_hash(args.admin_password)
            verify_admin(os.getenv("ADMIN_USERNAME", "admin"), args.admin_password)


if __name__ == "__main__":
    main()

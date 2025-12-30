#!/usr/bin/env python3
"""
Crée un compte admin.

Usage:
  ADMIN_EMAIL=x ADMIN_PASSWORD=y python scripts/create_admin.py  # Production
  python scripts/create_admin.py --interactive                    # Dev (prompt)
  python scripts/create_admin.py --generate                       # Dev (auto)
"""
import os
import sys
import secrets
import string
import asyncio
from getpass import getpass

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import select
from database import AsyncSessionLocal, init_db
from models import User, UserJourney, JourneyStage
from services.auth import hash_password


def generate_secure_password(length: int = 16) -> str:
    alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
    pwd = [
        secrets.choice(string.ascii_lowercase),
        secrets.choice(string.ascii_uppercase),
        secrets.choice(string.digits),
        secrets.choice("!@#$%^&*"),
    ]
    pwd += [secrets.choice(alphabet) for _ in range(length - 4)]
    secrets.SystemRandom().shuffle(pwd)
    return ''.join(pwd)


def validate_password(password: str) -> tuple[bool, str]:
    if len(password) < 12:
        return False, "Minimum 12 caractères"
    if not any(c.isupper() for c in password):
        return False, "Au moins 1 majuscule"
    if not any(c.islower() for c in password):
        return False, "Au moins 1 minuscule"
    if not any(c.isdigit() for c in password):
        return False, "Au moins 1 chiffre"
    if not any(c in "!@#$%^&*()_+-=" for c in password):
        return False, "Au moins 1 caractère spécial"
    return True, "OK"


async def create_admin(email: str, password: str):
    await init_db()

    async with AsyncSessionLocal() as db:
        existing = await db.scalar(select(User).where(User.email == email))
        if existing:
            if existing.role == "admin":
                print(f"⚠️  Admin existe déjà: {email}")
                return False
            existing.role = "admin"
            await db.commit()
            print(f"✅ {email} promu admin")
            return True

        admin = User(
            email=email,
            hashed_password=hash_password(password),
            full_name="Administrateur",
            role="admin",
            is_active=True,
            subscription_plan="enterprise",
            subscription_status="active"
        )
        db.add(admin)
        await db.flush()
        db.add(UserJourney(user_id=admin.id, stage=JourneyStage.POWER_USER.value))
        await db.commit()
        print(f"✅ Admin créé: {email}")
        return True


async def main():
    print("\n" + "=" * 50)
    print("   CRÉATION ADMIN")
    print("=" * 50 + "\n")

    email = os.getenv("ADMIN_EMAIL")
    password = os.getenv("ADMIN_PASSWORD")

    # Mode --generate
    if "--generate" in sys.argv or "-g" in sys.argv:
        email = email or input("Email: ").strip()
        password = generate_secure_password(16)
        print(f"\n🔐 Mot de passe: {password}")
        print("\n⚠️  NOTEZ-LE MAINTENANT !\n")

    # Mode --interactive
    elif "--interactive" in sys.argv or "-i" in sys.argv:
        email = email or input("Email: ").strip()
        print("\nMot de passe: 12+ chars, maj, min, chiffre, spécial")
        password = getpass("Password: ")
        if password != getpass("Confirmer: "):
            sys.exit("❌ Mots de passe différents")

    # Mode env vars (production)
    else:
        if not email or not password:
            print("Usage:")
            print("  ADMIN_EMAIL=x ADMIN_PASSWORD=y python scripts/create_admin.py")
            print("  python scripts/create_admin.py --interactive")
            print("  python scripts/create_admin.py --generate")
            sys.exit(1)

    valid, msg = validate_password(password)
    if not valid:
        sys.exit(f"❌ {msg}")

    await create_admin(email, password)

if __name__ == "__main__":
    asyncio.run(main())

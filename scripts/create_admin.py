"""
One-time script to create the first superuser.
Run: python scripts/create_admin.py
"""
import asyncio
import getpass
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from db.database import get_session
from src.auth.service import create_admin


async def main():
    print("=== Create CRM Admin User ===")
    username = input("Username: ").strip()
    email = input("Email: ").strip()
    password = getpass.getpass("Password (min 8 chars): ")
    confirm = getpass.getpass("Confirm password: ")

    if password != confirm:
        print("Passwords do not match.")
        sys.exit(1)
    if len(password) < 8:
        print("Password too short.")
        sys.exit(1)

    async with get_session() as session:
        admin = await create_admin(
            session,
            username=username,
            email=email,
            password=password,
            is_superuser=True,
        )
        print(f"\nAdmin created: id={admin.id}, username={admin.username}")


if __name__ == "__main__":
    asyncio.run(main())

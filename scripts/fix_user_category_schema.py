import asyncio
from sqlalchemy import text
from db.database import engine

async def main():
    print("Applying migration: fix users.category_id constraints...")
    async with engine.begin() as conn:
        # Drop UNIQUE constraint if exists
        await conn.execute(text("ALTER TABLE users DROP CONSTRAINT IF EXISTS users_category_id_key;"))
        # Allow NULLs in category_id
        await conn.execute(text("ALTER TABLE users ALTER COLUMN category_id DROP NOT NULL;"))
        # Drop server default if any
        await conn.execute(text("ALTER TABLE users ALTER COLUMN category_id DROP DEFAULT;"))
    print("Migration completed ✅")

if __name__ == "__main__":
    asyncio.run(main())

#!/usr/bin/env python3
"""
Check current database tables before migration
"""

import asyncio
from sqlalchemy import text
from src.core.database import AsyncSessionLocal

async def check_current_tables():
    """Display all current tables in the database."""
    async with AsyncSessionLocal() as db:
        try:
            result = await db.execute(text(
                "SELECT table_name FROM information_schema.tables WHERE table_schema = 'public' ORDER BY table_name"
            ))
            tables = [row[0] for row in result.fetchall()]
            
            print("📋 Current database tables:")
            for table in tables:
                print(f"  - {table}")
            
            print(f"\n📊 Total tables: {len(tables)}")
            
            # Check if tables we plan to drop have any data
            tables_to_check = ['warren_interactions', 'user_content_queue', 'conversation_messages', 'conversations']
            
            print("\n🔍 Checking data in tables we plan to drop:")
            for table in tables_to_check:
                if table in tables:
                    count_result = await db.execute(text(f"SELECT COUNT(*) FROM {table}"))
                    count = count_result.scalar()
                    print(f"  - {table}: {count} rows")
                else:
                    print(f"  - {table}: table doesn't exist")
            
        except Exception as e:
            print(f"❌ Error checking tables: {e}")

if __name__ == "__main__":
    asyncio.run(check_current_tables())

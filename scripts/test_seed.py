#!/usr/bin/env python
"""
Test the database seeding functionality
"""

import asyncio
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.migrations.seed_data import seed_database


async def test_seeding():
    """Test the seeding process"""
    print("🧪 Testing database seeding...")
    try:
        await seed_database()
        print("✅ Seeding test completed successfully!")
    except Exception as e:
        print(f"❌ Seeding test failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()
    
    asyncio.run(test_seeding())

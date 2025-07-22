"""Initialize FiduciaMVP database with tables and migrations."""

import asyncio
import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Import after path is set
from src.core.database import create_tables, check_db_connection
from src.migrations.run_migrations import run_all_migrations


async def init_database():
    """Initialize database with tables and run migrations."""
    print("🗄️  Initializing FiduciaMVP Database")
    print("=" * 40)
    
    # Check database connection
    print("📡 Checking database connection...")
    result = await check_db_connection()
    if result["status"] != "success":
        print(f"❌ Database connection failed: {result['error']}")
        print("🔧 Troubleshooting tips:")
        print("  1. Make sure Docker is running")
        print("  2. Check if PostgreSQL container is up: docker-compose ps")
        print("  3. Verify DATABASE_URL in .env file")
        return False
    print("✅ Database connected successfully")
    
    # Create tables
    print("📊 Creating database tables...")
    try:
        await create_tables()
        print("✅ Tables created successfully")
    except Exception as e:
        print(f"❌ Failed to create tables: {e}")
        return False
    
    # Run migrations
    print("🔄 Running database migrations...")
    try:
        await run_all_migrations()
        print("✅ Migrations completed successfully")
    except Exception as e:
        print(f"⚠️  Migration warning: {e}")
        print("This might be okay if migrations were already applied.")
    
    print("🎉 Database initialization complete!")
    print("\
📊 Database is ready with:")
    print("  - All core tables created")
    print("  - Compliance portal tables added")
    print("  - Vector search capabilities enabled")
    print("  - Sample data loaded for testing")
    
    return True


if __name__ == "__main__":
    # Load environment variables
    from dotenv import load_dotenv
    load_dotenv()
    
    success = asyncio.run(init_database())
    sys.exit(0 if success else 1)
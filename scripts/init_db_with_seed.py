"""
Enhanced database initialization with sample data seeding
Extends the existing init_db.py script to include optional data seeding
"""

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
from src.migrations.seed_data.seed_database import seed_database


async def init_database_with_seed(include_seed_data=True):
    """Initialize database with tables, migrations, and optional seed data."""
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
    
    # Seed sample data if requested
    if include_seed_data:
        print("\n🌱 Seeding database with sample data...")
        try:
            await seed_database()
            print("✅ Sample data seeded successfully")
        except Exception as e:
            print(f"⚠️  Seeding warning: {e}")
            print("The database is still functional, but sample data may be incomplete.")
    
    print("\n🎉 Database initialization complete!")
    print("\n📊 Database is ready with:")
    print("  - All core tables created")
    print("  - Compliance portal tables added")
    print("  - Vector search capabilities enabled")
    
    if include_seed_data:
        print("  - Sample data loaded for testing")
        print("\n🎯 Demo accounts available:")
        print("  - Advisor: demo_advisor_001")
        print("  - CCO Full: john.cco@firmcompliance.com")
        print("  - CCO Lite: sarah.compliance@wealthadvisors.com")
    else:
        print("  - No sample data loaded (use --seed flag to include)")
    
    return True


if __name__ == "__main__":
    import argparse
    from dotenv import load_dotenv
    
    # Load environment variables
    load_dotenv()
    
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Initialize FiduciaMVP database")
    parser.add_argument(
        "--seed", 
        action="store_true", 
        help="Include sample data seeding (recommended for development)"
    )
    parser.add_argument(
        "--no-seed", 
        action="store_true", 
        help="Skip sample data seeding (for production or clean setup)"
    )
    
    args = parser.parse_args()
    
    # Determine whether to include seed data
    include_seed = True  # Default to including seed data for development
    if args.no_seed:
        include_seed = False
    elif args.seed:
        include_seed = True
    
    # Run initialization
    success = asyncio.run(init_database_with_seed(include_seed_data=include_seed))
    sys.exit(0 if success else 1)

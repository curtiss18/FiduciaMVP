#!/bin/bash
# Reset database and reload fresh sample data

set -e  # Exit on error

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${RED}⚠️  WARNING: This will delete all existing data!${NC}"
echo -e "${YELLOW}Are you sure you want to reset the database? (y/N)${NC}"
read -r response

if [[ ! "$response" =~ ^[Yy]$ ]]; then
    echo "Cancelled."
    exit 0
fi

echo -e "\n${YELLOW}🔄 Resetting database...${NC}"

# Stop services
echo -e "${YELLOW}Stopping Docker services...${NC}"
docker-compose down

# Remove volume to ensure clean database
echo -e "${YELLOW}Removing database volume...${NC}"
docker volume rm fiduciamvp_postgres_data 2>/dev/null || true

# Start services
echo -e "${YELLOW}Starting Docker services...${NC}"
docker-compose up -d

# Wait for services to be ready
echo -e "${YELLOW}⏳ Waiting for PostgreSQL to be ready...${NC}"
sleep 10

# Activate virtual environment if not already active
if [[ "$VIRTUAL_ENV" == "" ]]; then
    echo -e "${YELLOW}Activating virtual environment...${NC}"
    source venv/bin/activate
fi

# Initialize database with seed data
echo -e "${YELLOW}🌱 Initializing database with fresh sample data...${NC}"
python scripts/init_db_with_seed.py --seed

# Verify the data
echo -e "\n${YELLOW}🔍 Verifying seed data...${NC}"
python scripts/verify_seed_data.py

echo -e "\n${GREEN}✅ Database reset complete!${NC}"
echo ""
echo -e "${GREEN}Demo Accounts Available:${NC}"
echo -e "  Advisor: ${YELLOW}demo_advisor_001${NC}"
echo -e "  CCO Full: ${YELLOW}john.cco@firmcompliance.com${NC}"
echo -e "  CCO Lite: ${YELLOW}sarah.compliance@wealthadvisors.com${NC}"
echo ""
echo "You can now start the development server with:"
echo -e "  ${YELLOW}./scripts/run_dev.sh${NC}"

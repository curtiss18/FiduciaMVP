#!/bin/bash
# FiduciaMVP Development Setup Script

set -e  # Exit on error

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Parse command line arguments
SKIP_SEED=false
if [[ "$1" == "--no-seed" ]]; then
    SKIP_SEED=true
fi

echo -e "${GREEN}🚀 FiduciaMVP Development Setup${NC}"
echo "==============================="
if [ "$SKIP_SEED" = true ]; then
    echo -e "${YELLOW}Note: Skipping database seeding (--no-seed flag detected)${NC}"
fi
echo ""

# Check if we're in the right directory
if [ ! -f "requirements.txt" ]; then
    echo -e "${RED}❌ Error: Not in FiduciaMVP directory${NC}"
    echo "Please run this script from the project root directory"
    exit 1
fi

# Check Python version
echo -e "\n${YELLOW}📌 Checking Python version...${NC}"
python_version=$(python3 --version 2>&1 | awk '{print $2}')
required_version="3.11"
if [ "$(printf '%s\n' "$required_version" "$python_version" | sort -V | head -n1)" != "$required_version" ]; then 
    echo -e "${RED}❌ Python 3.11+ required. Found: $python_version${NC}"
    exit 1
fi
echo -e "${GREEN}✅ Python $python_version${NC}"

# Check for system dependencies
echo -e "\n${YELLOW}📦 Checking system dependencies...${NC}"
dependencies=("build-essential" "python3-dev" "python3-venv" "postgresql-client" "curl")
missing_deps=()

for dep in "${dependencies[@]}"; do
    if ! dpkg -l | grep -q "^ii  $dep"; then
        missing_deps+=($dep)
    fi
done

if [ ${#missing_deps[@]} -ne 0 ]; then
    echo -e "${YELLOW}📦 Installing missing dependencies: ${missing_deps[*]}${NC}"
    sudo apt update
    sudo apt install -y "${missing_deps[@]}"
else
    echo -e "${GREEN}✅ All system dependencies installed${NC}"
fi

# Check if Rust is installed (needed for tiktoken)
if ! command -v rustc &> /dev/null; then
    echo -e "\n${YELLOW}🦀 Installing Rust compiler (needed for tiktoken)...${NC}"
    curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y
    source "$HOME/.cargo/env"
else
    echo -e "${GREEN}✅ Rust compiler found${NC}"
fi

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo -e "\n${YELLOW}🐍 Creating virtual environment...${NC}"
    python3 -m venv venv
else
    echo -e "${GREEN}✅ Virtual environment exists${NC}"
fi

# Activate virtual environment
echo -e "\n${YELLOW}🔄 Activating virtual environment...${NC}"
source venv/bin/activate

# Upgrade pip
echo -e "\n${YELLOW}📦 Upgrading pip...${NC}"
pip install --upgrade pip wheel setuptools

# Install Python dependencies
echo -e "\n${YELLOW}📚 Installing Python dependencies...${NC}"
pip install -r requirements.txt

# Setup environment file
if [ ! -f .env ]; then
    echo -e "\n${YELLOW}⚙️  Creating .env file...${NC}"
    cp .env.example .env
    echo -e "${YELLOW}⚠️  Please edit .env and add your API keys!${NC}"
    echo "Required keys:"
    echo "  - OPENAI_API_KEY"
    echo "  - ANTHROPIC_API_KEY"
    echo "  - DATABASE_URL (will be set automatically)"
else
    echo -e "${GREEN}✅ .env file exists${NC}"
fi

# Update DATABASE_URL in .env
echo -e "\n${YELLOW}🔧 Updating DATABASE_URL in .env...${NC}"
if grep -q "DATABASE_URL" .env; then
    sed -i 's|DATABASE_URL=.*|DATABASE_URL=postgresql+asyncpg://fiducia_user:fiducia_password@localhost:5432/fiducia_mvp|' .env
else
    echo "DATABASE_URL=postgresql+asyncpg://fiducia_user:fiducia_password@localhost:5432/fiducia_mvp" >> .env
fi

# Check Docker
echo -e "\n${YELLOW}🐳 Checking Docker...${NC}"
if ! command -v docker &> /dev/null; then
    echo -e "${RED}❌ Docker not found${NC}"
    echo "Please install Docker Desktop and enable WSL integration"
    echo "Visit: https://docs.docker.com/desktop/wsl/"
    exit 1
else
    echo -e "${GREEN}✅ Docker found${NC}"
fi

# Start Docker services
echo -e "\n${YELLOW}🐳 Starting Docker services...${NC}"
docker-compose up -d

# Wait for services to be ready
echo -e "\n${YELLOW}⏳ Waiting for services to be ready...${NC}"
sleep 5

# Initialize database
echo -e "\n${YELLOW}🗄️  Initializing database...${NC}"
python scripts/init_db.py

# Seed database with sample data (unless --no-seed flag is used)
if [ "$SKIP_SEED" = false ]; then
    echo -e "\n${YELLOW}🌱 Seeding database with sample data...${NC}"
    echo -e "${YELLOW}This will create demo accounts and sample content for testing${NC}"
    python scripts/init_db_with_seed.py --seed

    # Check if seeding was successful
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ Sample data loaded successfully!${NC}"
        echo ""
        echo -e "${GREEN}Demo Accounts Created:${NC}"
        echo -e "  Advisor: ${YELLOW}demo_advisor_001${NC}"
        echo -e "  CCO Full: ${YELLOW}john.cco@firmcompliance.com${NC}"
        echo -e "  CCO Lite: ${YELLOW}sarah.compliance@wealthadvisors.com${NC}"
    else
        echo -e "${YELLOW}⚠️  Sample data seeding failed, but setup is complete${NC}"
        echo -e "You can manually seed data later with: ${YELLOW}python scripts/init_db_with_seed.py --seed${NC}"
    fi
else
    echo -e "\n${YELLOW}ℹ️  Skipping sample data seeding${NC}"
    echo -e "You can seed data later with: ${YELLOW}python scripts/init_db_with_seed.py --seed${NC}"
fi

echo -e "\n${GREEN}✅ Setup complete!${NC}"
echo ""
echo "To start the development server:"
echo -e "  ${YELLOW}source venv/bin/activate${NC}"
echo -e "  ${YELLOW}python scripts/run_dev.py${NC}"
echo ""
echo "Or use the shortcut:"
echo -e "  ${YELLOW}./scripts/run_dev.sh${NC}"
echo ""
if [ "$SKIP_SEED" = false ]; then
    echo -e "${GREEN}📊 Sample data has been loaded!${NC}"
    echo "You can now test the system with pre-populated content and demo accounts."
    echo "See docs/database/seeding-guide.md for details about the sample data."
fi

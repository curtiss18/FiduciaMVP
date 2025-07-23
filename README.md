AI-powered platform for generating SEC/FINRA-compliant financial marketing content.

## Overview

FiduciaMVP enables financial advisors to create compliant marketing content in minutes instead of weeks, saving firms $120K-$250K annually compared to traditional compliance consultants.

**Key Features:**
- AI-powered content generation with built-in compliance
- Advanced RAG system with financial regulations knowledge base
- Multi-channel content distribution (LinkedIn, Twitter, Email, Website)
- Compliance review workflow with audit trails
- Enterprise-grade security and multi-tenant architecture

## Prerequisites

- Python 3.11+
- Docker & Docker Compose
- PostgreSQL 14+ (via Docker)
- Redis (via Docker)
- Ubuntu/WSL2 or macOS

## Quick Start

1. **Clone the repository**
   ```bash
   git clone https://github.com/curtiss18/FiduciaMVP.git
   cd FiduciaMVP
   ```
### Make sure docker desktop is running ###

2. **Run the automated setup**
   ```bash
   chmod +x scripts/setup.sh
   ./scripts/setup.sh
   ```
   
   The setup script will:
   - Install system dependencies
   - Create Python virtual environment
   - Install all Python packages
   - Start Docker services (PostgreSQL, Redis)
   - Initialize the database
   - **Load sample data with demo accounts** (use `--no-seed` to skip)

3. **Configure environment variables**
   ```bash
   # Edit .env file with your API keys
   nano .env
   ```
   
   Required keys:
   - `OPENAI_API_KEY` - For GPT-4 content generation
   - `ANTHROPIC_API_KEY` - For Claude integration
   - `SEARCHAPI_API_KEY` - For web search capabilities

4. **Start the development server**
   ```bash
   ./scripts/run_dev.sh
   ```

5. **Access the application**
   - API Documentation: http://localhost:8000/docs
   - Health Check: http://localhost:8000/api/v1/health

6. **Install and start the frontend**
   - In another terminal, navigate to FiduciaMVP
   ```bash
   # navigate to frontend
   cd frontend-advisor
   # activate virtual environment
   source venv/bin/activate
   # install
   npm install
   # run
   npm run dev
   ```
   - repeat these steps for the frontend-admin and frontend-compliance if you want to use those

## Development Commands

```bash
# Start all services
./scripts/run_dev.sh

# Initialize/reset database (without sample data)
python scripts/init_db.py

# Initialize database with sample data (recommended for development)
python scripts/init_db_with_seed.py --seed

# Run tests
pytest

# Database utilities
python scripts/verify_seed_data.py    # Check if seed data exists
python scripts/show_demo_data.py       # Display demo accounts and data
./scripts/reset_db_with_seed.sh       # Reset DB with fresh sample data

# Run with manual startup
source venv/bin/activate
docker-compose up -d
python scripts/run_dev.py
```

## Database Seeding

The project includes a comprehensive database seeding system that populates the database with realistic sample data for development and testing.

### Quick Start with Sample Data
```bash
# Initialize database with all sample data (recommended for new developers)
python scripts/init_db_with_seed.py --seed
```

### What Gets Seeded
- **Marketing Content**: Pre-approved compliant content examples
- **Compliance Rules**: SEC/FINRA regulations and requirements
- **Demo Accounts**: Test advisor and CCO accounts
- **Sample Workflows**: Content in various approval states
- **CRM Data**: Sample contacts and audience groups

### Demo Accounts Created
- **Advisor**: `demo_advisor_001`
- **CCO Full**: `john.cco@firmcompliance.com`
- **CCO Lite**: `sarah.compliance@wealthadvisors.com`

For detailed seeding documentation, see [docs/database/seeding-guide.md](docs/database/seeding-guide.md).

## Project Structure

```
FiduciaMVP/
├── src/                    # Backend application code
│   ├── api/               # API endpoints
│   ├── services/          # Business logic services
│   ├── models/            # Database models
│   └── core/              # Core utilities
├── config/                 # Configuration files
├── scripts/               # Development scripts
├── frontend-admin/        # Admin portal (Next.js)
├── frontend-advisor/      # Advisor portal (Next.js)
├── tests/                 # Test suite
└── docker-compose.yml     # Service orchestration
```

## API Documentation

Once the server is running, comprehensive API documentation is available at:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Troubleshooting

### Docker Issues
```bash
# Check if services are running
docker-compose ps

# View logs
docker-compose logs -f

# Restart services
docker-compose restart
```

### Database Issues
```bash
# Reset database (without sample data)
docker-compose down -v
docker-compose up -d
python scripts/init_db.py

# Reset database with fresh sample data
./scripts/reset_db_with_seed.sh

# Or manually seed existing database
python scripts/init_db_with_seed.py --seed

# Verify seed data
python scripts/verify_seed_data.py
```

### Python Dependencies
```bash
# Reinstall dependencies
source venv/bin/activate
pip install -r requirements.txt
```

## Contributing

1. Create a feature branch
2. Make your changes
3. Run tests: `pytest`
4. Submit a pull request

## License

Proprietary - All rights reserved

## Support

For issues or questions, contact the development team.

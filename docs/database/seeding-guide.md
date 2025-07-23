# FiduciaMVP Database Seeding Documentation

## Overview

The database seeding system provides realistic sample data for development and testing, allowing new developers to immediately start working with a populated database that demonstrates all key features of the FiduciaMVP platform.

## Quick Start

### Option 1: Initialize with Seed Data (Recommended for Development)
```bash
# From project root
python scripts/init_db_with_seed.py --seed
```

### Option 2: Initialize without Seed Data (Production/Clean Setup)
```bash
python scripts/init_db_with_seed.py --no-seed
```

### Option 3: Seed Existing Database
```bash
# If database already exists and you just want to add sample data
python -m src.migrations.seed_data.seed_database
```

## Seeded Data Overview

### 1. **Content Tags** (15 records)
- Topic tags: retirement_planning, tax_planning, estate_planning, etc.
- Tone tags: educational, professional, conversational, urgent
- Demographic tags: millennials, gen_x, baby_boomers, high_net_worth, business_owners

### 2. **Compliance Rules** (4 records)
- SEC Marketing Rule (206(4)-1)
- FINRA Rule 2210
- Investment Company Act
- SEC Testimonial Rule

### 3. **Marketing Content** (4+ records)
Pre-approved, compliant content examples:
- LinkedIn posts about retirement planning and tax strategies
- Email templates for client communication
- Blog posts about investment basics
- All with proper compliance scores and disclaimers

### 4. **Advisor Sessions & Messages**
Sample Warren AI conversations demonstrating:
- Retirement planning content creation
- Tax-efficient investment strategies
- Market commentary generation
- Complete conversation flow with Warren's compliance questions

### 5. **Advisor Content** (4 records)
Content in various approval states:
- **Approved**: Ready for distribution
- **In Review**: Awaiting CCO decision
- **Needs Revision**: CCO requested changes
- **Draft**: Work in progress

### 6. **Compliance CCO Accounts** (3 records)
Different subscription types:
- **Full Account**: john.cco@firmcompliance.com (with team members)
- **Lite Account**: sarah.compliance@wealthadvisors.com
- **Trial Account**: trial.cco@testfirm.com

### 7. **Content Reviews & Feedback**
Complete review workflows including:
- Approved content with high compliance scores
- Rejected content with specific violation feedback
- In-progress reviews
- Detailed feedback items with regulation references

### 8. **Advisor Contacts & Audiences**
CRM data for audience targeting:
- 5 sample contacts (prospects and clients)
- 3 audience groups: Medical Professionals, Business Owners, Tech Executives
- Contacts assigned to relevant audiences

### 9. **Warren Interactions**
Historical AI usage showing:
- Successful content generation
- User feedback and ratings
- Content modification tracking

### 10. **Content Distribution**
Records showing where approved content was posted:
- LinkedIn, email, website distributions
- View counts and engagement metrics

## Demo Accounts

After seeding, these accounts are available for testing:

### Advisor Account
- **ID**: demo_advisor_001
- **Has**: Active sessions, content in various states, contacts, and audiences

### CCO Accounts
1. **Full CCO**: john.cco@firmcompliance.com
   - Full dashboard access
   - Team members configured
   - Multiple content reviews
   
2. **Lite CCO**: sarah.compliance@wealthadvisors.com
   - Email-only access
   - Basic review capabilities

3. **Trial CCO**: trial.cco@testfirm.com
   - 14-day trial period
   - Full features during trial

## Seeding Details

### Data Relationships
The seeding script maintains proper relationships between:
- Content ↔ Reviews ↔ Feedback
- Sessions ↔ Messages ↔ Content
- Contacts ↔ Audiences (many-to-many)
- CCOs ↔ Team Members ↔ Reviews

### Realistic Scenarios
The seed data creates these realistic scenarios:

1. **Content Creation Workflow**
   - Advisor creates content with Warren
   - Content submitted for review
   - CCO reviews and provides feedback
   - Content approved and distributed

2. **Compliance Review Process**
   - Some content approved quickly
   - Some content needs revisions with specific feedback
   - Violation types and regulation references included

3. **Audience Targeting**
   - Contacts grouped by profession and characteristics
   - Audiences with detailed targeting information
   - Ready for Warren to use in content personalization

## Customization

To add more seed data, edit `src/migrations/seed_data/seed_database.py`:

```python
# Add new content types
content_data.append({
    "title": "Your New Content",
    "content_text": "Content text here...",
    "content_type": ContentType.LINKEDIN_POST,
    # ... other fields
})
```

## Troubleshooting

### Common Issues

1. **"Unique constraint violation"**
   - Database already has seed data
   - Solution: Drop and recreate database, or skip seeding

2. **"Foreign key constraint violation"**
   - Seeding order issue
   - Solution: Ensure parent records created before children

3. **"Enum value not found"**
   - Using string instead of enum
   - Solution: Use proper enum types (ContentType.LINKEDIN_POST)

### Reset Database
To completely reset and reseed:
```bash
# Stop services
docker-compose down

# Remove volume (WARNING: Deletes all data)
docker volume rm fiduciamvp_postgres_data

# Start services
docker-compose up -d

# Initialize with seed data
python scripts/init_db_with_seed.py --seed
```

## Development Workflow

1. **New Developer Setup**
   ```bash
   git clone <repo>
   cd FiduciaMVP
   docker-compose up -d
   python scripts/init_db_with_seed.py --seed
   ```

2. **Testing New Features**
   - Use seeded data to test workflows
   - Add specific test data as needed
   - Document any new seed data requirements

3. **Before Pull Requests**
   - Ensure seeding still works with schema changes
   - Update seed data if new fields added
   - Test both --seed and --no-seed options

## Best Practices

1. **Keep Seed Data Realistic**
   - Use actual compliance rules and requirements
   - Include edge cases for testing
   - Maintain data consistency

2. **Update Documentation**
   - Document new demo accounts
   - Explain test scenarios created
   - Note any dependencies

3. **Performance Considerations**
   - Seed data in batches
   - Use bulk operations where possible
   - Commit periodically for large datasets

## Future Enhancements

Planned improvements to the seeding system:
1. Configure seed data volume (light/medium/heavy)
2. Industry-specific seed data sets
3. Performance testing data generation
4. Export/import seed data snapshots

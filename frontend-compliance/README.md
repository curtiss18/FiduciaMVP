# Fiducia Compliance Portal

Professional content review and compliance management interface for Chief Compliance Officers (CCOs).

## Overview

The Compliance Portal provides a streamlined interface for CCOs to review marketing content from financial advisors, ensuring FINRA/SEC compliance while maintaining efficient workflows.

## Architecture

- **Lite Version**: Token-based access for individual content reviews
- **Full Version**: Account-based dashboard for multi-advisor management (future)
- **Tech Stack**: Next.js 14, TypeScript, Tailwind CSS, Shadcn/ui

## Getting Started

### Prerequisites

- Node.js 18 or higher
- npm or yarn package manager
- Access to FiduciaMVP backend API (running on localhost:8000)

### Installation

```bash
# Install dependencies
npm install

# Start development server
npm run dev
```

The compliance portal will be available at `http://localhost:3003`

### Development Scripts

```bash
npm run dev          # Start development server on port 3003
npm run build        # Build for production
npm run start        # Start production server
npm run lint         # Run ESLint
npm run type-check   # Run TypeScript compiler check
```

## Features

### Lite Version (Current)

- **Token-based Content Access**: Secure review links sent via email
- **Professional Review Interface**: Clean, mobile-responsive content viewer
- **Compliance Feedback System**: Section-specific comments with violation types
- **Regulatory Guidance**: Built-in FINRA/SEC rule references
- **Decision Workflow**: Approve/reject with detailed feedback requirements
- **Upgrade Prompts**: Contextual calls-to-action for full version

### Full Version (Future)

- **Multi-Advisor Dashboard**: Centralized oversight for multiple advisors
- **Advanced Analytics**: Review performance metrics and compliance trends
- **Warren AI Integration**: AI-powered violation detection and suggestions
- **Team Collaboration**: Multi-reviewer workflows and permissions
- **Automated Reporting**: Compliance reports for regulatory examinations

## Project Structure

```
frontend-compliance/
├── app/                    # Next.js 14 App Router
│   ├── (lite)/            # Lite version routes
│   │   ├── review/[token]/ # Token-based review page
│   │   └── upgrade/       # Upgrade to full version
│   ├── (full)/            # Full version routes (future)
│   ├── globals.css        # Global styles
│   ├── layout.tsx         # Root layout
│   └── page.tsx           # Landing page
├── components/            # React components
│   ├── lite/             # Lite version components
│   ├── full/             # Full version components (future)
│   ├── shared/           # Shared components
│   └── ui/               # Base UI components
├── lib/                  # Utilities and configurations
│   ├── api.ts            # API client
│   ├── types.ts          # TypeScript interfaces
│   └── utils.ts          # Utility functions
└── hooks/                # Custom React hooks
```

## API Integration

The compliance portal integrates with the FiduciaMVP backend API:

- **Base URL**: `http://localhost:8000/api/v1`
- **Lite Version Endpoints**:
  - `GET /compliance/content/{token}` - Access content for review
  - `POST /compliance/review/submit` - Submit review decision
  - `POST /compliance/ai/analyze-violation` - Warren AI assistance

## Security

- **Token-based Access**: Cryptographically secure tokens for content access
- **No Account Required**: Zero-friction access for CCO convenience
- **Audit Trail**: Complete logging of all review actions
- **HTTPS Required**: Secure data transmission in production

## Compliance Features

- **FINRA/SEC Knowledge Base**: Built-in regulatory guidance
- **Violation Type Classification**: Structured feedback categories
- **Required Disclaimers**: Automatic compliance language validation
- **Audit Documentation**: Complete review history for examinations
- **Source Attribution**: Transparency in content generation sources

## Browser Support

- Chrome 90+
- Firefox 88+
- Safari 14+
- Edge 90+

## Contributing

1. Follow existing code patterns and TypeScript conventions
2. Use Tailwind CSS for styling with design system tokens
3. Implement proper error handling and loading states
4. Add TypeScript interfaces for all data structures
5. Test on mobile devices for responsive design

## Deployment

The compliance portal is designed for deployment alongside other FiduciaMVP microservices:

```bash
# Production build
npm run build

# Start production server
npm start
```

## Environment Variables

```env
# API Configuration
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000/api/v1

# Application Configuration
NEXT_PUBLIC_APP_ENV=development
```

## Support

For technical support or questions about the compliance portal:

- Check the technical architecture documentation
- Review API design specifications
- Contact the development team

---

**Status**: Phase 1 (Lite Version) - Ready for Development
**Port**: 3003
**Dependencies**: FiduciaMVP backend API

# Fiducia Advisor Portal

Warren AI chat interface for financial advisors to create compliance-focused content.

## Getting Started

1. Install dependencies:
```bash
npm install
```

2. Start the development server:
```bash
npm run dev
```

3. Open [http://localhost:3002](http://localhost:3002) in your browser.

## Features

- **Warren AI Chat**: Conversational interface for content creation
- **Compliance Guidance**: Warren proactively asks for compliance requirements
- **Content Preview**: Live preview of generated compliant content
- **Professional UI**: Enterprise-grade interface matching admin portal

## Tech Stack

- **Next.js 14** with App Router
- **TypeScript** for type safety
- **Tailwind CSS** for styling
- **Shadcn/ui** for components
- **Axios** for API integration

## API Integration

Connects to FiduciaMVP backend at `http://localhost:8000/api/v1`

Main endpoint: `/warren/generate-v3` for conversational content generation

## Development Notes

- Port: 3002 (to avoid conflicts with admin portal on 3001)
- Responsive design for desktop and mobile
- Real-time chat interface with loading states
- Content persistence using localStorage (Phase 1)

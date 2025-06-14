# Fiducia Advisor Portal - Setup

Revolutionary Warren AI chat interface with intelligent refinement system for financial advisors.

## Quick Start

```bash
# Install dependencies
npm install

# Start development server (port 3002)
npm run dev

# Build for production
npm run build

# Start production server
npm start
```

## Access

- **Development**: http://localhost:3002
- **Features**: Warren AI chat, intelligent refinement, split-screen interface
- **Tech Stack**: Next.js 14, TypeScript, Tailwind CSS, Shadcn/ui

## Revolutionary Features

- **Context-Aware AI**: Warren automatically switches between creation and refinement modes
- **Split-Screen Design**: Chat on left, content preview on right
- **Clean Content Separation**: Marketing content isolated using delimiter system
- **Professional UX**: Enterprise-grade interface with real-time processing

## Development

- **API Integration**: Connects to FastAPI backend at `http://localhost:8000`
- **Refinement Detection**: Automatic switching between AI prompts based on conversation stage
- **Content Processing**: Delimiter-based extraction with `##MARKETINGCONTENT##` parsing
- **Debug Logging**: Console output for refinement detection during development

For complete documentation and architecture details, see the main project README.
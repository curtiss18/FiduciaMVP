# Fiducia Admin Portal Setup Script
# Run this from the FiduciaMVP directory

Write-Host "🚀 Setting up Fiducia Admin Portal..." -ForegroundColor Green

# Navigate to the admin frontend directory
Set-Location "frontend-admin"

Write-Host "📦 Installing dependencies..." -ForegroundColor Yellow
npm install

Write-Host "🎨 Installing additional dependencies..." -ForegroundColor Yellow
npm install tailwindcss-animate

Write-Host "✅ Setup complete!" -ForegroundColor Green
Write-Host ""
Write-Host "🎯 Next steps:" -ForegroundColor Cyan
Write-Host "1. Make sure your FastAPI backend is running on http://localhost:8000"
Write-Host "2. Start the admin portal:"
Write-Host "   cd frontend-admin"
Write-Host "   npm run dev"
Write-Host ""
Write-Host "3. Open http://localhost:3001 in your browser"
Write-Host ""
Write-Host "🔗 Endpoints:" -ForegroundColor Cyan
Write-Host "   Admin Portal: http://localhost:3001"
Write-Host "   FastAPI Backend: http://localhost:8000"
Write-Host "   API Docs: http://localhost:8000/docs"
Write-Host ""
Write-Host "🎉 Your admin portal is ready to showcase your vector search system!" -ForegroundColor Green
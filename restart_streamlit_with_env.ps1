Write-Host "======================================================================" -ForegroundColor Cyan
Write-Host "🔄 Restarting Streamlit with Environment Variables" -ForegroundColor Cyan
Write-Host "======================================================================" -ForegroundColor Cyan

# Kill any existing Streamlit processes
Write-Host "`n🛑 Stopping existing Streamlit processes..." -ForegroundColor Yellow
Get-Process streamlit -ErrorAction SilentlyContinue | Stop-Process -Force
Start-Sleep -Seconds 2

# Set environment variables
Write-Host "`n⚙️ Setting environment variables..." -ForegroundColor Green
# IMPORTANT: Set GITHUB_TOKEN in your environment or .env file, NOT here!
# $env:GITHUB_TOKEN = "your_token_here"
$env:GITHUB_DEFAULT_OWNER = "Hemesh11"
$env:GITHUB_DEFAULT_REPO = "Autotasker-AI"

Write-Host "✅ Environment configured:" -ForegroundColor Green
Write-Host "   - GITHUB_DEFAULT_OWNER: $env:GITHUB_DEFAULT_OWNER" -ForegroundColor White
Write-Host "   - GITHUB_DEFAULT_REPO: $env:GITHUB_DEFAULT_REPO" -ForegroundColor White
Write-Host "   - GITHUB_TOKEN: [SET]" -ForegroundColor White

# Start Streamlit
Write-Host "`n🚀 Starting Streamlit..." -ForegroundColor Green
Write-Host "Press Ctrl+C to stop`n" -ForegroundColor Yellow

conda activate autotasker
streamlit run frontend/streamlit_app.py

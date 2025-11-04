@echo off
echo ======================================================================
echo 🔄 Restarting Streamlit with Environment Variables
echo ======================================================================

REM Kill any existing Streamlit processes
echo 🛑 Stopping existing Streamlit processes...
taskkill /F /IM streamlit.exe 2>nul
timeout /t 2 /nobreak >nul

REM Set environment variables
echo ⚙️ Setting environment variables...
REM IMPORTANT: Set GITHUB_TOKEN in your environment or .env file, NOT here!
REM set GITHUB_TOKEN=your_token_here
set GITHUB_DEFAULT_OWNER=Hemesh11
set GITHUB_DEFAULT_REPO=Autotasker-AI

echo ✅ Environment configured:
echo    - GITHUB_DEFAULT_OWNER: %GITHUB_DEFAULT_OWNER%
echo    - GITHUB_DEFAULT_REPO: %GITHUB_DEFAULT_REPO%
echo    - GITHUB_TOKEN: [SET]

REM Activate conda environment and start Streamlit
echo 🚀 Starting Streamlit...
call conda activate autotasker
streamlit run frontend/streamlit_app.py

pause

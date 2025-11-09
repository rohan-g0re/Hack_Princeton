@echo off
REM Project Setup Script for Windows

echo ========================================
echo Grocery Super-App Setup
echo ========================================
echo.

REM Create Python virtual environment
echo [1/5] Creating Python virtual environment...
python -m venv venv
if errorlevel 1 (
    echo ERROR: Failed to create virtual environment
    exit /b 1
)
echo ✓ Virtual environment created
echo.

REM Activate virtual environment and install dependencies
echo [2/5] Installing backend dependencies...
call venv\Scripts\activate.bat
pip install --upgrade pip
pip install -r server\requirements.txt
if errorlevel 1 (
    echo ERROR: Failed to install dependencies
    exit /b 1
)
echo ✓ Backend dependencies installed
echo.

REM Create .env files if they don't exist
echo [3/5] Setting up environment files...
if not exist "server\.env" (
    copy server\.env.example server\.env
    echo ✓ Created server\.env from template
    echo ⚠️  Please edit server\.env with your credentials
) else (
    echo ✓ server\.env already exists
)
echo.

REM Create mobile folder structure
echo [4/5] Creating mobile app structure...
if not exist "mobile" mkdir mobile
echo ✓ Mobile folder ready
echo.

echo [5/5] Setup complete!
echo.
echo ========================================
echo Next Steps:
echo ========================================
echo 1. Edit server\.env with your Supabase and Gemini API keys
echo 2. Start backend: venv\Scripts\activate ^&^& cd server ^&^& python -m uvicorn server.main:app --reload
echo 3. Run tests: venv\Scripts\activate ^&^& pytest server/tests/ -v
echo 4. Setup mobile: cd mobile ^&^& npm install
echo.
echo Happy coding! 🚀
echo.
pause


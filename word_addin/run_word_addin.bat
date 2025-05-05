@echo off
REM FDA Oncology Copilot Word Add-in Setup Script for Windows

echo Setting up FDA Oncology Copilot Word Add-in...

REM Check if Python is installed
python --version >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo Error: Python is required but not installed.
    exit /b 1
)

REM Check if pip is installed
pip --version >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo Error: pip is required but not installed.
    exit /b 1
)

REM Install dependencies
echo Installing dependencies...
pip install -r requirements.txt

REM Check if .env file exists
if not exist .env (
    echo Creating .env file from template...
    copy .env.template .env
    echo Please edit the .env file to add your OpenAI API key.
    echo Press Enter to continue after editing the file...
    pause
)

REM Check if indices are built
if not exist data\indices\* (
    echo Building vector indices...
    python scripts\build_indices.py
)

REM Start the Word add-in backend service
echo Starting FDA Oncology Copilot Word Add-in backend service...
echo Please follow these steps to install the add-in in Word:
echo 1. Open Microsoft Word
echo 2. Go to 'Insert' ^> 'Get Add-ins' ^> 'Manage My Add-ins' ^> 'Upload My Add-in'
echo 3. Select the 'word_addin\manifest.xml' file
echo 4. Click 'Install'
echo.
echo Starting backend service...
python word_addin\run_server.py

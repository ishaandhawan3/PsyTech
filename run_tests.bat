@echo off
REM Script to run the JSON storage tests and the application

echo PsyTech Child Wellness Companion - JSON Storage Test Runner
echo ==========================================================
echo.

REM Check if Python is installed
where python >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo Error: Python is not installed or not in PATH
    echo Please install Python 3.7+ and try again
    exit /b 1
)

REM Check if we're in the right directory
if not exist "frontend" (
    echo Error: This script must be run from the psyTech directory
    echo Please navigate to the psyTech directory and try again
    exit /b 1
)

if not exist "backend" (
    echo Error: This script must be run from the psyTech directory
    echo Please navigate to the psyTech directory and try again
    exit /b 1
)

REM Create data directory if it doesn't exist
if not exist "data" (
    echo Creating data directory...
    mkdir data\sessions
)

REM Run the JSON storage tests
echo Running JSON storage tests...
echo ----------------------------
python test_json_storage.py
set test_result=%ERRORLEVEL%

echo.
if %test_result% equ 0 (
    echo ✅ Tests completed successfully!
) else (
    echo ❌ Tests failed with exit code %test_result%
    echo Please check the error messages above
    exit /b %test_result%
)

echo.
set /p run_app=Would you like to run the application now? (y/n): 

if /i "%run_app%"=="y" (
    echo.
    echo Starting the application...
    echo -------------------------
    
    REM Check if Streamlit is installed
    where streamlit >nul 2>&1
    if %ERRORLEVEL% neq 0 (
        echo Error: Streamlit is not installed
        echo Please install it with: pip install streamlit
        exit /b 1
    )
    
    REM Run the application
    streamlit run frontend/main_app.py
) else (
    echo.
    echo You can run the application later with:
    echo   streamlit run frontend/main_app.py
)

echo.
echo Thank you for using PsyTech Child Wellness Companion!

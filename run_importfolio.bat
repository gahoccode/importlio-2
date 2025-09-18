@echo off
REM Batch script to setup venv with UV, install dependencies, and run Importfolio
:MENU
echo.
echo === Importfolio Automation Menu (UV-powered) ===
echo 1. Setup environment with UV (auto-detect/create venv)
echo 2. Install dependencies with UV sync
echo 3. Run app
echo 4. Run tests
echo 5. Check UV and Python version
echo 6. Clean and reset environment
echo 7. Exit
set /p choice=Choose an option: 

if "%choice%"=="1" goto SETUP_ENV
if "%choice%"=="2" goto INSTALL_DEPS
if "%choice%"=="3" goto RUN_APP
if "%choice%"=="4" goto RUN_TESTS
if "%choice%"=="5" goto CHECK_VERSIONS
if "%choice%"=="6" goto CLEAN_ENV
if "%choice%"=="7" exit

:SETUP_ENV
echo Setting up environment with UV...
REM Check if UV is installed
uv --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: UV is not installed. Please install UV first:
    echo https://github.com/astral-sh/uv
    pause
    goto MENU
)

REM Check if virtual environment exists
if exist ".venv" (
    echo Virtual environment already exists at .venv
) else (
    echo Creating virtual environment with Python ≤3.12...
    uv venv --python 3.12
    if errorlevel 1 (
        echo Failed to create virtual environment
        pause
        goto MENU
    )
    echo Virtual environment created successfully
)
goto MENU

:INSTALL_DEPS
echo Installing dependencies with UV sync...
if not exist ".venv" (
    echo No virtual environment found. Creating one first...
    goto SETUP_ENV
)
uv sync
if errorlevel 1 (
    echo Failed to sync dependencies
    pause
)
goto MENU

:RUN_APP
echo Running Importfolio app...
if not exist ".venv" (
    echo No virtual environment found. Setting up first...
    goto SETUP_ENV
)
uv run python app.py
goto MENU

:RUN_TESTS
echo Running tests...
if not exist ".venv" (
    echo No virtual environment found. Setting up first...
    goto SETUP_ENV
)
uv run pytest
goto MENU

:CHECK_VERSIONS
echo Checking UV and Python versions...
echo UV version:
uv --version
echo.
echo Python version in virtual environment:
if exist ".venv" (
    uv run python --version
) else (
    echo No virtual environment found
)
echo.
echo Target: Python ≤3.12 for PyPortfolioOpt compatibility
pause
goto MENU

:CLEAN_ENV
echo Cleaning environment...
if exist ".venv" (
    rmdir /s /q ".venv"
    echo Virtual environment removed
) else (
    echo No virtual environment to clean
)
if exist "uv.lock" (
    echo UV lock file found (keeping for reproducible builds)
)
goto MENU

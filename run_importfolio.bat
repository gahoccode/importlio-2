@echo off
REM Batch script to setup venv, install dependencies, and run Importfolio
:MENU
echo.
echo === Importfolio Automation Menu ===
echo 1. Create virtual environment
echo 2. Activate virtual environment
echo 3. Install dependencies (pip)
echo 4. Install dependencies (poetry)
echo 5. Run app
echo 6. Run tests
echo 7. Exit
set /p choice=Choose an option: 
if "%choice%"=="1" python -m venv venv & goto MENU
if "%choice%"=="2" call venv\Scripts\activate & goto MENU
if "%choice%"=="3" pip install -r requirements.txt & goto MENU
if "%choice%"=="4" poetry install & goto MENU
if "%choice%"=="5" python app.py & goto MENU
if "%choice%"=="6" pytest & goto MENU
if "%choice%"=="7" exit

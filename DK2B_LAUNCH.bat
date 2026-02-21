@echo off
TITLE DK2B Enterprise - Auto Setup
COLOR 0B

echo ===================================================
echo       DK2B INTELLIGENCE ENGINE - STARTUP
echo ===================================================
echo.

:: 1. CHECK FOR PYTHON
echo [1/6] Checking for Python...
python --version >nul 2>&1
if errorlevel 1 goto NoPython
echo [OK] Python is installed.
goto CheckReqs

:NoPython
echo [!] Python is NOT installed on this system.
echo [*] Attempting silent installation via Windows Package Manager...
winget install -e --id Python.Python.3.11 --silent --accept-package-agreements --accept-source-agreements
echo.
echo ===================================================
echo [SUCCESS] Python has been installed!
echo [!] IMPORTANT: Windows needs to refresh its memory.
echo Please close this window and double-click start_dk2b.bat again.
echo ===================================================
pause
exit /b

:CheckReqs
:: 2. CHECK FOR REQUIREMENTS.TXT
echo.
echo [2/6] Checking for requirements.txt...
if not exist "requirements.txt" goto NoReqs
echo [OK] requirements.txt found.
goto CheckVenv

:NoReqs
echo [!] ERROR: requirements.txt not found in this folder!
echo Please ensure requirements.txt is in the same folder as this script.
pause
exit /b

:CheckVenv
:: 3. CHECK & CREATE VIRTUAL ENVIRONMENT
echo.
echo [3/6] Verifying Virtual Environment (venv)...
if not exist "venv\Scripts\activate.bat" goto MakeVenv
echo [OK] Virtual environment found.
goto InstallDeps

:MakeVenv
echo [*] Virtual environment not found. Building 'venv' now...
python -m venv venv
echo [OK] Virtual environment created.

:InstallDeps
:: 4. INSTALL/UPDATE DEPENDENCIES
echo.
echo [4/6] Verifying and Installing Dependencies...
call venv\Scripts\python.exe -m pip install --upgrade pip >nul 2>&1
call venv\Scripts\python.exe -m pip install -r requirements.txt
echo [OK] All dependencies are verified and ready.

:: 5. START BACKEND SERVER
echo.
echo [5/6] Igniting Backend AI Engine...
start "DK2B Backend Server" cmd /k "call venv\Scripts\activate.bat && python -m backend.main"

:: 6. OPEN INDEX.HTML DIRECTLY
echo.
echo [6/6] Launching Frontend Interface...

echo [*] Waiting 3 seconds for backend server to initialize...
timeout /t 3 /nobreak >nul

echo [*] Opening index.html...
start frontend_simple/index.html

echo.
echo ===================================================
echo  SYSTEM ONLINE. 
echo  (Keep the black backend terminal window open!)
echo ===================================================
pause
exit /b
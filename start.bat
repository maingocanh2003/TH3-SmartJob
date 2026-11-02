@echo off
REM SmartJob - Script khoi dong du an
REM Chay file nay de bat dau phat trien

echo ===================================
echo   SMARTJOB - STARTUP SCRIPT
echo ===================================
echo.

REM Kiem tra PostgreSQL dang chay
echo [1/3] Kiem tra PostgreSQL...
"C:\Program Files\PostgreSQL\18\bin\pg_ctl.exe" status -D "C:\Program Files\PostgreSQL\18\data" >nul 2>&1
if %errorlevel% neq 0 (
    echo   -> Dang khoi dong PostgreSQL...
    "C:\Program Files\PostgreSQL\18\bin\pg_ctl.exe" start -D "C:\Program Files\PostgreSQL\18\data" -w
    timeout /t 3 /nobreak >nul
) else (
    echo   -> PostgreSQL dang chay OK
)
echo.

REM Khoi dong Django backend
echo [2/3] Khoi dong Django Backend (port 8000)...
cd /d "%~dp0backend"
start "SmartJob Backend" cmd /k "C:\Users\NGUYEN\AppData\Local\Python\bin\python3.exe manage.py runserver 0.0.0.0:8000"
timeout /t 3 /nobreak >nul
echo   -> Backend: http://localhost:8000
echo   -> API Root: http://localhost:8000/api/
echo   -> Admin:    http://localhost:8000/admin/
echo.

REM Mo frontend
echo [3/3] Mo Frontend trong browser...
cd /d "%~dp0"
start "" "frontend\index.html"
echo   -> Frontend: file:///%~dp0frontend/index.html
echo.

echo ===================================
echo   SmartJob da khoi dong thanh cong!
echo ===================================
echo.
echo De dung: Dong cua so Backend hoac Ctrl+C trong terminal
pause

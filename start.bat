@echo off
REM SmartJob - Script khoi dong du an
REM Chay file nay de bat dau phat trien va chay demo

echo ===================================
echo   SMARTJOB - STARTUP SCRIPT
echo ===================================
echo.

REM 1. Xac dinh duong dan Python
set PYTHON_EXE=
if exist "%~dp0.venv\Scripts\python.exe" (
    set "PYTHON_EXE=%~dp0.venv\Scripts\python.exe"
) else (
    where python >nul 2>&1
    if %errorlevel% equ 0 (
        set "PYTHON_EXE=python"
    ) else if exist "C:\Users\%USERNAME%\AppData\Local\Python\bin\python3.exe" (
        set "PYTHON_EXE=C:\Users\%USERNAME%\AppData\Local\Python\bin\python3.exe"
    )
)

if "%PYTHON_EXE%"=="" (
    echo [ERROR] Khong tim thay Python! Vui long kiem tra virtualenv hoac cai dat Python.
    pause
    exit /b 1
)

REM 2. Kiem tra PostgreSQL
echo [1/3] Kiem tra PostgreSQL...
sc query postgresql-x64-18 >nul 2>&1
if %errorlevel% equ 0 (
    echo   -^> Dich vu PostgreSQL dang chay OK.
) else (
    if exist "C:\Program Files\PostgreSQL\18\bin\pg_ctl.exe" (
        "C:\Program Files\PostgreSQL\18\bin\pg_ctl.exe" status -D "C:\Program Files\PostgreSQL\18\data" >nul 2>&1
        if %errorlevel% neq 0 (
            echo   -^> Dang khoi dong PostgreSQL...
            "C:\Program Files\PostgreSQL\18\bin\pg_ctl.exe" start -D "C:\Program Files\PostgreSQL\18\data" -w
        )
    )
)
echo.

REM 3. Khoi dong Django backend
echo [2/3] Khoi dong Django Backend (port 8000)...
start "SmartJob Backend" cmd /k ""%PYTHON_EXE%" "%~dp0backend\manage.py" runserver 127.0.0.1:8000"
timeout /t 3 /nobreak >nul
echo   -^> Backend:  http://localhost:8000
echo   -^> API Root: http://localhost:8000/api/
echo   -^> Admin:    http://localhost:8000/admin/
echo.

REM 4. Khoi dong Frontend Server (port 5500) va mo Browser
echo [3/3] Khoi dong Frontend Web Server (port 5500)...
start "SmartJob Frontend" cmd /k ""%PYTHON_EXE%" -m http.server 5500 -d "%~dp0frontend""
timeout /t 2 /nobreak >nul
start http://localhost:5500
echo   -^> Frontend Web: http://localhost:5500
echo   -^> Trang chu:    http://localhost:5500/index.html
echo   -^> BI Dashboard: http://localhost:5500/bi-dashboard.html
echo.

echo ===================================
echo   SmartJob da khoi dong thanh cong!
echo ===================================
echo.
echo De dung: Dong cac cua so Backend va Frontend hoac nhan Ctrl+C trong terminal
pause

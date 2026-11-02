# SmartJob - PowerShell Startup Script
# Chay: .\start.ps1

Write-Host "===================================" -ForegroundColor Cyan
Write-Host "   SMARTJOB - STARTUP SCRIPT" -ForegroundColor Cyan
Write-Host "===================================" -ForegroundColor Cyan

$pythonExe = "C:\Users\NGUYEN\AppData\Local\Python\bin\python3.exe"
$pgCtl = "C:\Program Files\PostgreSQL\18\bin\pg_ctl.exe"
$pgData = "C:\Program Files\PostgreSQL\18\data"

# 1. Kiem tra va khoi dong PostgreSQL
Write-Host "`n[1/3] Kiem tra PostgreSQL..." -ForegroundColor Yellow
$pgStatus = & $pgCtl status -D $pgData 2>&1
if ($pgStatus -match "no server running") {
    Write-Host "  -> Dang khoi dong PostgreSQL..." -ForegroundColor Yellow
    & $pgCtl start -D $pgData -w 2>&1 | Out-Null
    Start-Sleep -Seconds 3
    Write-Host "  -> PostgreSQL da khoi dong!" -ForegroundColor Green
} else {
    Write-Host "  -> PostgreSQL dang chay OK" -ForegroundColor Green
}

# 2. Khoi dong Django Backend
Write-Host "`n[2/3] Khoi dong Django Backend..." -ForegroundColor Yellow
Set-Location (Join-Path $PSScriptRoot "backend")
$backendJob = Start-Process -FilePath $pythonExe -ArgumentList "manage.py runserver 0.0.0.0:8000" -PassThru -WindowStyle Normal
Start-Sleep -Seconds 3
Write-Host "  -> Backend dang chay tai: http://localhost:8000" -ForegroundColor Green
Write-Host "  -> API Explorer:          http://localhost:8000/api/" -ForegroundColor Green

# 3. Mo frontend
Write-Host "`n[3/3] Mo Frontend..." -ForegroundColor Yellow
$frontendPath = Join-Path $PSScriptRoot "frontend\index.html"
Start-Process $frontendPath
Write-Host "  -> Frontend da mo trong browser" -ForegroundColor Green

Write-Host "`n===================================" -ForegroundColor Cyan
Write-Host "   SmartJob da san sang!" -ForegroundColor Green
Write-Host "===================================" -ForegroundColor Cyan
Write-Host "`nNhan Enter de thoat script (backend van chay)..."
Read-Host

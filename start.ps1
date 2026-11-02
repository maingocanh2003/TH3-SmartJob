# SmartJob - PowerShell Startup Script
# Chay: .\start.ps1

Write-Host "===================================" -ForegroundColor Cyan
Write-Host "   SMARTJOB - STARTUP SCRIPT" -ForegroundColor Cyan
Write-Host "===================================" -ForegroundColor Cyan

# 1. Xac dinh Python
$pythonExe = Join-Path $PSScriptRoot ".venv\Scripts\python.exe"
if (-not (Test-Path $pythonExe)) {
    $pythonCmd = Get-Command python -ErrorAction SilentlyContinue
    if ($pythonCmd) {
        $pythonExe = $pythonCmd.Source
    } else {
        $fallback = "C:\Users\$env:USERNAME\AppData\Local\Python\bin\python3.exe"
        if (Test-Path $fallback) {
            $pythonExe = $fallback
        } else {
            Write-Host "[ERROR] Khong tim thay Python! Vui long cai dat hoac tao .venv" -ForegroundColor Red
            exit 1
        }
    }
}

# 2. Kiem tra va khoi dong PostgreSQL
Write-Host "`n[1/3] Kiem tra PostgreSQL..." -ForegroundColor Yellow
$pgService = Get-Service -Name *postgres* -ErrorAction SilentlyContinue | Select-Object -First 1
if ($pgService) {
    if ($pgService.Status -ne 'Running') {
        Write-Host "  -> Dang khoi dong PostgreSQL Service..." -ForegroundColor Yellow
        Start-Service $pgService.Name
    }
    Write-Host "  -> PostgreSQL dang chay OK ($($pgService.Name))" -ForegroundColor Green
} else {
    Write-Host "  -> Luu y: Khong tim thay Service PostgreSQL, gia dinh PostgreSQL dang chay cong 5432." -ForegroundColor Gray
}

# 3. Khoi dong Django Backend
Write-Host "`n[2/3] Khoi dong Django Backend (port 8000)..." -ForegroundColor Yellow
$managePy = Join-Path $PSScriptRoot "backend\manage.py"
Start-Process -FilePath $pythonExe -ArgumentList "$managePy runserver 127.0.0.1:8000" -WindowStyle Normal
Start-Sleep -Seconds 3
Write-Host "  -> Backend dang chay tai: http://localhost:8000" -ForegroundColor Green
Write-Host "  -> API Explorer:          http://localhost:8000/api/" -ForegroundColor Green
Write-Host "  -> Admin Panel:           http://localhost:8000/admin/" -ForegroundColor Green

# 4. Khoi dong Frontend HTTP Server va mo Browser
Write-Host "`n[3/3] Khoi dong Frontend (port 5500)..." -ForegroundColor Yellow
$frontendDir = Join-Path $PSScriptRoot "frontend"
Start-Process -FilePath $pythonExe -ArgumentList "-m http.server 5500 -d `"$frontendDir`"" -WindowStyle Normal
Start-Sleep -Seconds 2

Start-Process "http://localhost:5500"
Write-Host "  -> Frontend da san sang tai: http://localhost:5500" -ForegroundColor Green
Write-Host "  -> BI Dashboard:             http://localhost:5500/bi-dashboard.html" -ForegroundColor Green

Write-Host "`n===================================" -ForegroundColor Cyan
Write-Host "   SmartJob da khoi dong thanh cong!" -ForegroundColor Green
Write-Host "===================================" -ForegroundColor Cyan
Write-Host "`nDong cac cua so terminal de dung server hoac bam Enter de thoat script."

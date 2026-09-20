$Root = $PSScriptRoot

$Venv = if (Test-Path "$Root\.venv\Scripts\Activate.ps1") {
    "$Root\.venv\Scripts\Activate.ps1"
} elseif (Test-Path "$Root\backend\.venv\Scripts\Activate.ps1") {
    "$Root\backend\.venv\Scripts\Activate.ps1"
} else {
    Write-Host "[!] Virtual environment not found." -ForegroundColor Red
    exit 1
}

Write-Host ">>> Starting GCS Services..." -ForegroundColor Cyan

# 1. FastAPI Backend
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$Root\backend'; . '$Venv'; uvicorn app.main:app --reload --port 8080"

# 2. Vue Frontend
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$Root\frontend'; npm run dev"

# 3. Mock SITL Feeder
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$Root'; . '$Venv'; python scripts/mock_mavlink.py"

Write-Host "[OK] All nodes running." -ForegroundColor Green
Write-Host "HUD:     http://localhost:5173" -ForegroundColor White
Write-Host "Swagger: http://localhost:8080/docs" -ForegroundColor White

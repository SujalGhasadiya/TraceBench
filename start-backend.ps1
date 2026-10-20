# TraceBench Backend Starter
Set-Location -Path $PSScriptRoot

$pyExe = "C:\Users\HP\AppData\Local\Programs\Python\Python311\python.exe"
if (-not (Test-Path $pyExe)) {
    $pyExe = "python"
}

$env:PATH = "C:\Users\HP\AppData\Local\Programs\Python\Python311;C:\Users\HP\AppData\Local\Programs\Python\Python311\Scripts;" + $env:PATH
$env:PYTHONPATH = "."

Write-Host "========================================================" -ForegroundColor Cyan
Write-Host "Starting TraceBench FastAPI Backend on http://127.0.0.1:8000" -ForegroundColor Green
Write-Host "========================================================" -ForegroundColor Cyan

& $pyExe -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000

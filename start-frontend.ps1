# TraceBench Frontend Starter
Set-Location -Path "$PSScriptRoot\frontend"

Write-Host "========================================================" -ForegroundColor Cyan
Write-Host "Starting TraceBench Frontend UI on http://localhost:5173" -ForegroundColor Green
Write-Host "========================================================" -ForegroundColor Cyan

npm run dev

$ErrorActionPreference = 'Stop'
Set-Location $PSScriptRoot
$node24 = Join-Path $env:USERPROFILE '.cache\codex-runtimes\codex-primary-runtime\dependencies\node\bin\node.exe'
if (-not (Get-NetTCPConnection -LocalPort 8000 -State Listen -ErrorAction SilentlyContinue)) {
    Start-Process -FilePath "$PSScriptRoot\.venv-local\Scripts\python.exe" -ArgumentList '-m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000' -WorkingDirectory $PSScriptRoot -WindowStyle Hidden -RedirectStandardOutput "$PSScriptRoot\backend-server.log" -RedirectStandardError "$PSScriptRoot\backend-error.log"
}
if (-not (Get-NetTCPConnection -LocalPort 5173 -State Listen -ErrorAction SilentlyContinue)) {
    Start-Process -FilePath $node24 -ArgumentList 'node_modules/vite/bin/vite.js --host localhost --port 5173' -WorkingDirectory "$PSScriptRoot\frontend" -WindowStyle Hidden -RedirectStandardOutput "$PSScriptRoot\frontend-server.log" -RedirectStandardError "$PSScriptRoot\frontend-error.log"
}
Write-Host 'Frontend: http://localhost:5173'
Write-Host 'API docs: http://127.0.0.1:8000/docs'

# Windows setup. Run in PowerShell from the project folder:
#   powershell -ExecutionPolicy Bypass -File setup.ps1
$ErrorActionPreference = "Stop"
$ver = $null
foreach ($v in @("3.12", "3.11")) {
    & py "-$v" --version 2>$null
    if ($LASTEXITCODE -eq 0) { $ver = $v; break }
}
if (-not $ver) {
    Write-Host "Python 3.11 or 3.12 not found."
    Write-Host "Install Python 3.12 from https://www.python.org/downloads/ (tick 'Add python.exe to PATH'), then run this again."
    exit 1
}
& py "-$ver" -m venv .venv
& .\.venv\Scripts\python.exe -m pip install -U pip
& .\.venv\Scripts\python.exe -m pip install -e ".[dev]"
& .\.venv\Scripts\mudra.exe init
Write-Host ""
Write-Host "Setup done. Allow camera and microphone for desktop apps:"
Write-Host "  Settings > Privacy & security > Camera / Microphone > 'Let desktop apps access...' = On"
Write-Host ""
Write-Host "Run:  .\.venv\Scripts\mudra.exe"

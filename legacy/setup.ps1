# SIP Softphone Setup Script for Windows
# Automates project initialization

Write-Host "================================" -ForegroundColor Cyan
Write-Host "SIP Softphone Setup" -ForegroundColor Cyan
Write-Host "================================`n" -ForegroundColor Cyan

# Check Python installation
Write-Host "Checking Python installation..." -ForegroundColor Yellow
$python = Get-Command python -ErrorAction SilentlyContinue

if (-not $python) {
    Write-Host "ERROR: Python not found!" -ForegroundColor Red
    Write-Host "Please install Python 3.8+ from https://python.org" -ForegroundColor Red
    exit 1
}

$pythonVersion = python --version
Write-Host "Found: $pythonVersion`n" -ForegroundColor Green

# Create virtual environment
Write-Host "Creating virtual environment..." -ForegroundColor Yellow
if (Test-Path "venv") {
    Write-Host "Virtual environment already exists" -ForegroundColor Green
} else {
    python -m venv venv
    Write-Host "Virtual environment created" -ForegroundColor Green
}

# Activate virtual environment
Write-Host "`nActivating virtual environment..." -ForegroundColor Yellow
& ".\venv\Scripts\Activate.ps1"

# Upgrade pip
Write-Host "`nUpgrading pip..." -ForegroundColor Yellow
python -m pip install --upgrade pip

# Install dependencies
Write-Host "`nInstalling dependencies..." -ForegroundColor Yellow
Write-Host "This may take several minutes...`n" -ForegroundColor Yellow

pip install -r requirements.txt

# Create directories
Write-Host "`nCreating directories..." -ForegroundColor Yellow
$dirs = @("recordings", "static")
foreach ($dir in $dirs) {
    if (-not (Test-Path $dir)) {
        New-Item -ItemType Directory -Path $dir | Out-Null
        Write-Host "Created: $dir" -ForegroundColor Green
    } else {
        Write-Host "Exists: $dir" -ForegroundColor Green
    }
}

# Initialize database
Write-Host "`nInitializing database..." -ForegroundColor Yellow
python models.py

# Check PJSUA2 installation
Write-Host "`nChecking PJSUA2 installation..." -ForegroundColor Yellow
$pjsuaCheck = python -c "import pjsua2; print('OK')" 2>&1

if ($pjsuaCheck -match "OK") {
    Write-Host "PJSUA2 is installed!" -ForegroundColor Green
} else {
    Write-Host "`nWARNING: PJSUA2 not found!" -ForegroundColor Red
    Write-Host "You need to install PJSUA2 manually." -ForegroundColor Yellow
    Write-Host "See README.md for installation instructions.`n" -ForegroundColor Yellow
    Write-Host "Options:" -ForegroundColor Cyan
    Write-Host "1. Try: pip install pjsua2" -ForegroundColor Cyan
    Write-Host "2. Build from source (requires Visual Studio Build Tools)" -ForegroundColor Cyan
    Write-Host "3. Use Docker image (coming soon)`n" -ForegroundColor Cyan
}

Write-Host "`n================================" -ForegroundColor Cyan
Write-Host "Setup Complete!" -ForegroundColor Green
Write-Host "================================`n" -ForegroundColor Cyan

Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "1. Edit config.yaml with your SIP credentials (if not done)" -ForegroundColor White
Write-Host "2. Run: python call.py" -ForegroundColor White
Write-Host "3. Open: http://localhost:8000`n" -ForegroundColor White

Write-Host "Press any key to exit..."
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")

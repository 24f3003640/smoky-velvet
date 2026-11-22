# ==============================================================================
#  Smoky Velvet: Automated Windows One-Click Installer & Launcher
#  Usage in PowerShell (Run as Administrator not required):
#  irm https://raw.githubusercontent.com/24f3003640/smoky-velvet/main/install.ps1 | iex
# ==============================================================================

$ErrorActionPreference = "Stop"

Write-Host ""
Write-Host " ============================================================ " -ForegroundColor Magenta
Write-Host "   SMOKY VELVET RGB ENGINE - AUTOMATED WINDOWS INSTALLER     " -ForegroundColor Cyan
Write-Host "   Target: URX Core75 (81 LEDs)                               " -ForegroundColor Yellow
Write-Host " ============================================================ " -ForegroundColor Magenta
Write-Host ""

$installDir = "$env:USERPROFILE\smoky-velvet"

# 1. Check / Install Python
$pythonCmd = (Get-Command python -ErrorAction SilentlyContinue)
if (-not $pythonCmd) {
    Write-Host "[1/5] Python not found. Installing Python via Windows Package Manager (winget)..." -ForegroundColor Yellow
    try {
        winget install -e --id Python.Python.3.12 --silent --accept-source-agreements --accept-package-agreements
        # Refresh environment PATH
        $env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")
        $pythonCmd = (Get-Command python -ErrorAction SilentlyContinue)
    } catch {
        Write-Host "[!] Winget install failed or unavailable. Please install Python from https://www.python.org/downloads/ and check 'Add to PATH'." -ForegroundColor Red
        return
    }
} else {
    Write-Host "[1/5] Python is installed: $($pythonCmd.Source)" -ForegroundColor Green
}

# 2. Download / Clone Repository
Write-Host "[2/5] Fetching Smoky Velvet files..." -ForegroundColor Yellow
$gitCmd = (Get-Command git -ErrorAction SilentlyContinue)

if (Test-Path "$installDir\.git") {
    Write-Host "      Updating existing installation..." -ForegroundColor Cyan
    Set-Location "$installDir"
    git pull --quiet
} elseif ($gitCmd) {
    Write-Host "      Cloning repository via git..." -ForegroundColor Cyan
    git clone --quiet https://github.com/24f3003640/smoky-velvet.git "$installDir"
} else {
    Write-Host "      Git not found. Downloading release archive from GitHub..." -ForegroundColor Cyan
    $zipPath = "$env:TEMP\smoky-velvet.zip"
    $extractPath = "$env:TEMP\smoky-velvet-extracted"
    Invoke-WebRequest -Uri "https://github.com/24f3003640/smoky-velvet/archive/refs/heads/main.zip" -OutFile $zipPath
    if (Test-Path $extractPath) { Remove-Item $extractPath -Recurse -Force }
    Expand-Archive -Path $zipPath -DestinationPath $extractPath -Force
    $extractedFolder = (Get-ChildItem -Path $extractPath -Directory | Select-Object -First 1).FullName
    if (Test-Path $installDir) { Remove-Item $installDir -Recurse -Force }
    Move-Item "$extractedFolder" "$installDir" -Force
    Remove-Item $zipPath -Force -ErrorAction SilentlyContinue
    Remove-Item $extractPath -Recurse -Force -ErrorAction SilentlyContinue
}

Set-Location "$installDir"

# 3. Virtual Environment & Dependencies
Write-Host "[3/5] Setting up virtual environment & dependencies..." -ForegroundColor Yellow
$venvPython = "$installDir\.venv\Scripts\python.exe"
$venvPythonw = "$installDir\.venv\Scripts\pythonw.exe"

if (-not (Test-Path $venvPython)) {
    Write-Host "      Creating .venv..." -ForegroundColor Cyan
    python -m venv "$installDir\.venv"
}

Write-Host "      Installing hidapi, pynput, and PyQt6..." -ForegroundColor Cyan
& $venvPython -m pip install --upgrade pip --quiet
& $venvPython -m pip install -r "$installDir\requirements-windows.txt" --quiet

# 4. Create Desktop & Startup Shortcuts
Write-Host "[4/5] Creating Windows Desktop and Startup shortcuts..." -ForegroundColor Yellow
try {
    $WshShell = New-Object -ComObject WScript.Shell
    
    # Desktop Shortcut for GUI Studio
    $desktopPath = [System.Environment]::GetFolderPath("Desktop")
    $shortcutGui = $WshShell.CreateShortcut("$desktopPath\Smoky Velvet Studio.lnk")
    $shortcutGui.TargetPath = $venvPythonw
    $shortcutGui.Arguments = "`"$installDir\gui.py`""
    $shortcutGui.WorkingDirectory = "$installDir"
    $shortcutGui.Description = "Smoky Velvet Desktop Studio (URX Core75)"
    $shortcutGui.Save()

    # Startup Shortcut (Engine runs silently in background on Windows boot)
    $startupPath = [System.Environment]::GetFolderPath("Startup")
    $shortcutEngine = $WshShell.CreateShortcut("$startupPath\Smoky Velvet Background.lnk")
    $shortcutEngine.TargetPath = $venvPythonw
    $shortcutEngine.Arguments = "`"$installDir\main.py`""
    $shortcutEngine.WorkingDirectory = "$installDir"
    $shortcutEngine.Description = "Smoky Velvet Lighting Engine"
    $shortcutEngine.Save()

    Write-Host "      Created Desktop shortcut: Smoky Velvet Studio" -ForegroundColor Green
    Write-Host "      Created Auto-Start on Boot shortcut" -ForegroundColor Green
} catch {
    Write-Host "      Warning: Could not create shortcuts ($($_)). Continuing..." -ForegroundColor Yellow
}

# 5. Start Smoky Velvet Engine Immediately
Write-Host "[5/5] Launching Smoky Velvet on your URX Core75..." -ForegroundColor Green
Start-Process $venvPythonw -ArgumentList "`"$installDir\main.py`"" -WorkingDirectory "$installDir"

Write-Host ""
Write-Host " ============================================================ " -ForegroundColor Green
Write-Host "   [SUCCESS] SMOKY VELVET IS INSTALLED AND RUNNING! 🌌✨     " -ForegroundColor Green
Write-Host " ============================================================ " -ForegroundColor Green
Write-Host "  * Location: $installDir"
Write-Host "  * Desktop App: Double-click 'Smoky Velvet Studio' to customize."
Write-Host "  * Auto-Start: Enabled (starts silently whenever Windows boots)."
Write-Host ""

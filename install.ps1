# shift-this-version Windows PowerShell Installer
# Usage: irm https://raw.githubusercontent.com/snui1s/shift-this-version/main/install.ps1 | iex

$ErrorActionPreference = 'Stop'

Write-Host "Installing shift-this-version..." -ForegroundColor Cyan

# 1. Setup install directory
$InstallDir = Join-Path $HOME ".shift-this-version\bin"
if (-not (Test-Path $InstallDir)) {
    New-Item -ItemType Directory -Path $InstallDir -Force | Out-Null
}

$ExePath = Join-Path $InstallDir "shift-this-version.exe"

# 2. Download standalone executable from GitHub Releases
$DownloadUrl = "https://github.com/snui1s/shift-this-version/releases/latest/download/shift-this-version-windows-x64.exe"

try {
    [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
    $oldProgress = $ProgressPreference
    $ProgressPreference = 'SilentlyContinue'

    Write-Host "Downloading latest binary from GitHub Releases..." -ForegroundColor Gray
    Invoke-WebRequest -Uri $DownloadUrl -OutFile $ExePath -UseBasicParsing

    $ProgressPreference = $oldProgress
} catch {
    Write-Host "Error downloading binary: $_" -ForegroundColor Red
    Write-Host "Please ensure you have internet access or install via pip/npm: pip install shift-this-version" -ForegroundColor Yellow
    exit 1
}

# 3. Add to User PATH if not already present
$UserPath = [Environment]::GetEnvironmentVariable("Path", "User")
$PathEntries = $UserPath -split ';' | Where-Object { $_ -ne '' }

if ($PathEntries -notcontains $InstallDir) {
    Write-Host "Adding $InstallDir to User PATH..." -ForegroundColor Gray
    $NewPath = if ([string]::IsNullOrWhiteSpace($UserPath)) { $InstallDir } else { "$UserPath;$InstallDir" }
    [Environment]::SetEnvironmentVariable("Path", $NewPath, "User")
}

# 4. Refresh PATH in current session
if (($env:Path -split ';') -notcontains $InstallDir) {
    $env:Path = "$InstallDir;$env:Path"
}

Write-Host ""
Write-Host "✔ shift-this-version was installed successfully!" -ForegroundColor Green
Write-Host "Location: $ExePath" -ForegroundColor Gray
Write-Host "Run 'shift-this-version' to get started." -ForegroundColor Cyan

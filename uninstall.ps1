# shift-this-version Windows PowerShell Uninstaller
# Usage: irm https://raw.githubusercontent.com/snui1s/shift-this-version/main/uninstall.ps1 | iex

$ErrorActionPreference = 'Stop'

Write-Host "Uninstalling shift-this-version..." -ForegroundColor Cyan

$InstallDir = Join-Path $HOME ".shift-this-version\bin"
$ExePath = Join-Path $InstallDir "shift-this-version.exe"

# 1. Remove binary
if (Test-Path $ExePath) {
    Remove-Item -Path $ExePath -Force -ErrorAction SilentlyContinue
    Write-Host "Removed binary: $ExePath" -ForegroundColor Gray
} else {
    Write-Host "No binary found at $ExePath." -ForegroundColor Gray
}

# Remove bin folder if empty
if (Test-Path $InstallDir) {
    $remaining = Get-ChildItem -Path $InstallDir -Force
    if ($remaining.Count -eq 0) {
        Remove-Item -Path $InstallDir -Force -Recurse -ErrorAction SilentlyContinue
    }
}

# 2. Remove from User PATH environment variable
$UserPath = [Environment]::GetEnvironmentVariable("Path", "User")
if ($UserPath) {
    $PathEntries = $UserPath -split ';' | Where-Object { $_.Trim() -ne '' -and $_.Trim() -ne $InstallDir }
    $NewPath = $PathEntries -join ';'
    [Environment]::SetEnvironmentVariable("Path", $NewPath, "User")
    Write-Host "Removed $InstallDir from User PATH." -ForegroundColor Gray
}

# 3. Remove from current session PATH
$SessionPaths = $env:Path -split ';' | Where-Object { $_.Trim() -ne '' -and $_.Trim() -ne $InstallDir }
$env:Path = $SessionPaths -join ';'

Write-Host ""
Write-Host "✔ shift-this-version was uninstalled successfully!" -ForegroundColor Green
Write-Host "Note: Configuration files at '$HOME\.shift-this-version' were kept." -ForegroundColor Yellow
Write-Host "To completely remove all settings, delete: $HOME\.shift-this-version" -ForegroundColor Gray

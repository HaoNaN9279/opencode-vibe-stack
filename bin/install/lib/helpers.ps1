# ---- Helpers ----
function Write-Info  { Write-Host "[i] $args" -ForegroundColor Cyan }
function Write-OK    { Write-Host "[OK] $args" -ForegroundColor Green }
function Write-Warn  { Write-Host "[warn] $args" -ForegroundColor Yellow }
function Write-Error_ { Write-Host "[ERROR] $args" -ForegroundColor Red }
function Write-Bold  { Write-Host $args -ForegroundColor White }

function Show-InstallBanner {
    Write-Host ""
    Write-Host "======================================================" -ForegroundColor Cyan
    Write-Host "     OpenCode Vibe Stack - Windows Installer         " -ForegroundColor Cyan
    Write-Host "======================================================" -ForegroundColor Cyan
    Write-Host ""
}

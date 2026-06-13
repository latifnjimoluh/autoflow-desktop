<#
.SYNOPSIS
    Construit l'exécutable AutoFlow puis (si Inno Setup est présent) l'installeur.

.DESCRIPTION
    À lancer depuis la racine du dépôt :
        .\packaging\build.ps1

    Étapes :
      1. Construit dist\AutoFlow\AutoFlow.exe via PyInstaller.
      2. Si ISCC.exe (Inno Setup) est trouvé, génère dist\AutoFlow-Setup.exe.
#>

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
Set-Location $root

$python = Join-Path $root ".venv\Scripts\python.exe"
if (-not (Test-Path $python)) { $python = "python" }

Write-Host "==> Construction de l'exécutable (PyInstaller)..." -ForegroundColor Cyan
& $python -m PyInstaller packaging\autoflow.spec --noconfirm --clean

$exe = Join-Path $root "dist\AutoFlow\AutoFlow.exe"
if (Test-Path $exe) {
    Write-Host "==> Exécutable généré : $exe" -ForegroundColor Green
} else {
    throw "La construction a échoué : $exe introuvable."
}

# Recherche d'Inno Setup pour produire l'installeur.
$iscc = $null
foreach ($cand in @(
    "C:\Program Files (x86)\Inno Setup 6\ISCC.exe",
    "C:\Program Files\Inno Setup 6\ISCC.exe")) {
    if (Test-Path $cand) { $iscc = $cand; break }
}

if ($iscc) {
    Write-Host "==> Construction de l'installeur (Inno Setup)..." -ForegroundColor Cyan
    & $iscc "packaging\installer.iss"
    Write-Host "==> Installeur généré dans dist\." -ForegroundColor Green
} else {
    Write-Host "Inno Setup (ISCC.exe) introuvable : installeur non généré." -ForegroundColor Yellow
    Write-Host "Installez-le depuis https://jrsoftware.org/isdl.php puis relancez." -ForegroundColor Yellow
    Write-Host "L'application reste utilisable via dist\AutoFlow\AutoFlow.exe." -ForegroundColor Yellow
}

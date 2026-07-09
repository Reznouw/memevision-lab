param(
  [switch]$InstallDependencies
)

$ErrorActionPreference = "Stop"
$ProjectRoot = Resolve-Path -LiteralPath (Join-Path $PSScriptRoot "..")
$Python = Join-Path $ProjectRoot ".venv312\Scripts\python.exe"
if (-not (Test-Path -LiteralPath $Python)) {
  $Python = Join-Path $ProjectRoot ".venv\Scripts\python.exe"
}

if (-not (Test-Path -LiteralPath $Python)) {
  throw "Expected Python environment not found: $Python"
}

Push-Location -LiteralPath $ProjectRoot
try {
  if ($InstallDependencies) {
    & $Python -m pip install --upgrade pip
    & $Python -m pip install -e ".[vision,exe]"
  }

  & $Python -m PyInstaller `
    --noconfirm `
    --clean `
    --windowed `
    --name "MemeVision Lab" `
    --collect-all mediapipe `
    --collect-all cv2 `
    --collect-all pygame `
    --add-data "configs;configs" `
    --add-data "plugins;plugins" `
    --add-data "local_assets;local_assets" `
    "scripts\windows_entry.py"

  $DistRoot = Join-Path $ProjectRoot "dist\MemeVision Lab"
  foreach ($Name in @("configs", "plugins", "local_assets")) {
    $Source = Join-Path $ProjectRoot $Name
    $Destination = Join-Path $DistRoot $Name
    if (Test-Path -LiteralPath $Source) {
      if (Test-Path -LiteralPath $Destination) {
        Remove-Item -LiteralPath $Destination -Recurse -Force
      }
      Copy-Item -LiteralPath $Source -Destination $Destination -Recurse
    }
  }
} finally {
  Pop-Location
}

"Built: $ProjectRoot\dist\MemeVision Lab\MemeVision Lab.exe"

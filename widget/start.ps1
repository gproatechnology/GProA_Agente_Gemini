# Agente GProA Gemini Widget - Script de inicio rápido
$ErrorActionPreference = 'Stop'
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Definition
Set-Location -LiteralPath $scriptDir

Write-Host "Agente GProA Gemini Widget - Backend API" -ForegroundColor Cyan
Write-Host "===========================================" -ForegroundColor Cyan

# Crear .env si no existe
$envFile = Join-Path $scriptDir ".env"
$envExample = Join-Path $scriptDir ".env.example"
if (-not (Test-Path $envFile)) {
    if (Test-Path $envExample) {
        Copy-Item $envExample $envFile
        Write-Host "Se creó .env a partir de .env.example. Edita .env y agrega tu GOOGLE_API_KEY." -ForegroundColor Yellow
    } else {
        Write-Host "No se encontró .env.example" -ForegroundColor Red
    }
}

# Crear venv si no existe
$venvDir = Join-Path $scriptDir ".venv"
if (-not (Test-Path $venvDir)) {
    Write-Host "Creando entorno virtual..." -ForegroundColor Cyan
    python -m venv $venvDir
}

# Activar venv e instalar dependencias
$activateScript = Join-Path $venvDir "Scripts\Activate.ps1"
& $activateScript

Write-Host "Instalando dependencias..." -ForegroundColor Cyan
pip install -r requirements.txt

Write-Host ""
Write-Host "Listo. Ejecuta: python src/api/main.py" -ForegroundColor Green
Write-Host "El servidor estará en http://localhost:5000" -ForegroundColor Green
Write-Host "Recuerda editar .env y poner tu GOOGLE_API_KEY antes de correr el servidor." -ForegroundColor Yellow

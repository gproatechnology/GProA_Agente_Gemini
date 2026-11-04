# Agente GProA Gemini - Script de inicio rápido
$ErrorActionPreference = 'Stop'
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Definition
Set-Location -LiteralPath $scriptDir

Write-Host "Agente GProA Gemini" -ForegroundColor Cyan
Write-Host "=====================" -ForegroundColor Cyan

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
Write-Host "=== Opciones de ejecución ===" -ForegroundColor Cyan
Write-Host "1) Ejecutar interfaz web (Streamlit)"
Write-Host "2) Ejecutar consola (CLI)"
Write-Host ""
$opcion = Read-Host "Selecciona una opción (1 o 2)"

if ($opcion -eq "1") {
    Write-Host "Iniciando interfaz web en http://localhost:8501 ..." -ForegroundColor Green
    streamlit run ui/streamlit_app.py
} else {
    Write-Host "Iniciando consola..." -ForegroundColor Green
    python agente_gemini.py
}

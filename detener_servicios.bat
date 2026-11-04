@echo off
REM Agente_Ollama - Detener servicios (contenedores OpenClaw + Ollama + proxy SaIyDD)
set "COMPOSE_FILE=C:\Users\X1\openclaw-local\openclaw-local\docker-compose.yml"

echo Deteniendo proxy SaIyDD...
taskkill /FI "WINDOWTITLE eq saiydd_proxy*" /F >nul 2>&1
taskkill /FI "IMAGENAME eq python.exe" /FI "WINDOWTITLE eq *saiydd_proxy*" /F >nul 2>&1

echo Deteniendo contenedores (Ollama + OpenClaw)...
docker compose -f "%COMPOSE_FILE%" stop

echo.
echo Servicios detenidos. Los datos y modelos persisten en los volumenes.
echo.
pause

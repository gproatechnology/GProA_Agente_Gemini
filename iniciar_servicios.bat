@echo off
REM Agente_Ollama - Iniciar servicios (contenedores OpenClaw + Ollama + proxy SaIyDD)
set "COMPOSE_FILE=C:\Users\X1\openclaw-local\openclaw-local\docker-compose.yml"

echo Iniciando pila en contenedores (Ollama + OpenClaw)...
docker compose -f "%COMPOSE_FILE%" up -d

echo.
echo Iniciando proxy SaIyDD (HTTP -> Ollama)...
cd /d "%~dp0"
start /B python saiydd_proxy.py

echo.
echo Servicios iniciados:
echo - Ollama:        http://localhost:11434
echo - OpenClaw Web:  http://localhost:30001
echo - Gateway (WS):  ws://localhost:18789
echo - Proxy SaIyDD:  http://127.0.0.1:3000/api/chat
echo.
pause

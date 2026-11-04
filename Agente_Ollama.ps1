<#
.SYNOPSIS
    Agente_Ollama - Panel de control del auditor (OpenClaw + Telegram + Ollama)

.DESCRIPTION
    Gestiona la pila COMPLETAMENTE EN CONTENEDORES (Ollama + openclaw),
    verifica la comunicacion con Telegram y audita proyectos montados.
    No genera codigo: solo analiza.

.NOTES
    Requiere: Docker, PowerShell 5.1+ (Ollama corre en contenedor, no nativo)
#>

$ErrorActionPreference = "SilentlyContinue"

# Colores (escape ANSI compatible con PS 5.1)
$Verde    = "$([char]27)[32m"
$Amarillo = "$([char]27)[33m"
$Rojo      = "$([char]27)[31m"
$Azul      = "$([char]27)[34m"
$Cyan      = "$([char]27)[36m"
$DarkGray  = "$([char]27)[90m"
$Reset     = "$([char]27)[0m"

# Rutas
$proyectosPath = "C:\Users\X1\OneDrive\Documentos\Python_VS Code\GProA"
$agentePath    = "C:\Users\X1\OneDrive\Documentos\Python_VS Code\GProA\Agente_Ollama"
$openclawDir   = "C:\Users\X1\openclaw-local\openclaw-local"
$composeFile   = "C:\Users\X1\openclaw-local\openclaw-local\docker-compose.yml"
$ollamaHost    = "http://localhost:11434"
$ollamaModel    = "qwen2.5-coder:1.5b-16k"
$openclawUI    = "http://localhost:30001"
$contenedor    = "openclaw"
$ollamaCont    = "ollama"
$wsUri         = "ws://127.0.0.1:18791"

function Mostrar-Encabezado {
    Clear-Host
    Write-Host ""
    Write-Host "${Cyan}=== AGENTE OLLAMA - AUDITOR DE PROYECTOS (CONTENEDORES) ===${Reset}" -ForegroundColor Cyan
    Write-Host ""
}

function Test-OllamaAlcanzable {
    param([string]$url)
    try {
        $r = Invoke-WebRequest -Uri "$url/api/tags" -UseBasicParsing -TimeoutSec 5
        if ($r.StatusCode -eq 200) {
            $models = (($r.Content | ConvertFrom-Json).models | ForEach-Object { $_.name }) -join ", "
            return @{ Ok = $true; Models = $models }
        }
    } catch {}
    return @{ Ok = $false; Models = "" }
}

function Get-OpenClawGatewayToken {
    param([string]$cfg = (Join-Path $openclawDir "data\openclaw.json"))
    if (-not (Test-Path $cfg)) { return "" }
    try {
        $j = Get-Content $cfg -Raw | ConvertFrom-Json
        if ($j.gateway -and $j.gateway.auth -and $j.gateway.auth.token) {
            return $j.gateway.auth.token
        }
    } catch {}
    return ""
}

function Get-Estado-Contenedor {
    param([string]$nombre)
    if ([string]::IsNullOrWhiteSpace($nombre)) { return "Ausente" }
    try {
        $raw = docker inspect -f "{{.State.Status}}" $nombre 2>&1 | Out-String
        $est = ($raw -split "`r`n" | Where-Object { $_ -match "\S" } | Select-Object -First 1).Trim()
        if ($est) { return $est }
        $raw2 = docker ps -a --filter "name=$nombre" --format "{{.Status}}" 2>&1 | Out-String
        $est2 = ($raw2 -split "`r`n" | Where-Object { $_ -match "\S" } | Select-Object -First 1).Trim()
        if ($est2) {
            if ($est2 -match "^Up\s") { return "running" }
            if ($est2 -match "^Exited") { return "exited" }
            return $est2
        }
        return "Ausente"
    } catch { return "Ausente" }
}

function Get-Estado-Servicios {
    $estados = @{}

    # Docker
    docker info > $null 2>&1
    $estados.Docker = if ($LASTEXITCODE -eq 0) { "Ejecutando" } else { "Detenido" }

    # Contenedor Ollama
    $estados.OllamaCont = Get-Estado-Contenedor -nombre $ollamaCont

    # Ollama alcanzable (puerto publicado del contenedor)
    $a = Test-OllamaAlcanzable -url $ollamaHost
    $estados.OllamaHost = if ($a.Ok) { "OK ($($a.Models))" } else { "No alcanzable" }
    $estados.OllamaModels = $a.Models

    # Contenedor openclaw
    $estados.Contenedor = Get-Estado-Contenedor -nombre $contenedor

    # Skill auditor (ruta montada en host, mas robusto que docker exec)
    $skillPath = Join-Path $openclawDir "data\workspace\skills\auditor\SKILL.md"
    $estados.Skill = if (Test-Path $skillPath) { "Presente" } else { "No encontrado" }

    # Telegram configurado (en data/openclaw.json, que es el efectivo)
    $estados.Telegram = "No"
    $cfg = Join-Path $openclawDir "data\openclaw.json"
    if (Test-Path $cfg) {
        try {
            $j = Get-Content $cfg -Raw | ConvertFrom-Json
            if ($j.channels -and $j.channels.telegram -and $j.channels.telegram.enabled) {
                $tok = $j.channels.telegram.botToken
                $allow = $j.channels.telegram.allowFrom
                if ($tok -and $allow -and $allow.Count -gt 0) {
                    $estados.Telegram = "OK (allowFrom: $($allow -join ', '))"
                } else { $estados.Telegram = "Config incompleta" }
            }
        } catch { $estados.Telegram = "Error lectura JSON" }
    }

    return $estados
}

function Start-Pila {
    Write-Host "Iniciando pila en contenedores (Ollama + OpenClaw)..." -ForegroundColor Yellow
    Write-Host "Compose: $composeFile" -ForegroundColor DarkGray
    docker compose -f "$composeFile" up -d 2>&1 | ForEach-Object { Write-Host $_ -ForegroundColor DarkGray }
    if ($LASTEXITCODE -ne 0) {
        Write-Host "${Rojo}docker compose falló (LASTEXITCODE=$LASTEXITCODE).${Reset}" -ForegroundColor Red
        return
    }
    Write-Host "Esperando contenedores (openclaw + ollama)..." -ForegroundColor Yellow
    $tries = 0
    do {
        Start-Sleep -Seconds 2
        $oc = Get-Estado-Contenedor -nombre $contenedor
        $ol = Get-Estado-Contenedor -nombre $ollamaCont
        $tries++
        if ($tries -ge 30) {
            Write-Host "${Rojo}Timeout esperando contenedores. Estado actual: openclaw=$oc  ollama=$ol${Reset}" -ForegroundColor Red
            return
        }
    } while ($oc -ne "running" -or $ol -ne "running")
    Write-Host "${Verde}Pila iniciada${Reset}" -ForegroundColor Green
}

function Stop-Pila {
    Write-Host "Deteniendo contenedores (Ollama + OpenClaw)..." -ForegroundColor Yellow
    docker compose -f "$composeFile" stop
    Write-Host "${Verde}Pila detenida (los datos persisten en volumenes)${Reset}" -ForegroundColor Green
}

function Get-AnalisisProyecto {
    param([string]$ruta)
    if (-not (Test-Path $ruta)) {
        Write-Host "${Rojo}Error: La ruta no existe${Reset}" -ForegroundColor Red
        return
    }
    Write-Host ""
    Write-Host "${Azul}=== ANALISIS DE PROYECTO (estructura local) ===${Reset}" -ForegroundColor Cyan
    Write-Host "Ruta: $ruta"
    Write-Host ""
    Write-Host "${Amarillo}Subdirectorios:${Reset}" -ForegroundColor Yellow
    Get-ChildItem $ruta -Directory | ForEach-Object { Write-Host "  - $($_.Name)" }
    Write-Host ""
    Write-Host "${Amarillo}Archivos principales:${Reset}" -ForegroundColor Yellow
    Get-ChildItem $ruta -File | Select-Object -First 10 | ForEach-Object { Write-Host "  - $($_.Name)" }
    Write-Host ""
    $clave = @("package.json","pyproject.toml","requirements.txt","Cargo.toml","go.mod","pom.xml")
    foreach ($archivo in $clave) {
        $encontrado = Get-ChildItem -Path $ruta -Filter $archivo -Recurse -Depth 1 -ErrorAction SilentlyContinue | Select-Object -First 1
        if ($encontrado) { Write-Host "${Verde}Encontrado: $archivo${Reset}" -ForegroundColor Green }
    }
    Write-Host ""
    Write-Host "${Amarillo}(La auditoria con IA se hace desde Telegram: 'audita el proyecto <nombre>')${Reset}" -ForegroundColor Yellow
}

function Start-ChatWebSocket {
    param([string]$Uri = $wsUri)
    $token = Get-OpenClawGatewayToken
    if (-not $token) {
        Write-Host "${Rojo}No se encontro el token de gateway en data/openclaw.json${Reset}" -ForegroundColor Red
        return
    }

    $script = Join-Path $agentePath "chat_openclaw.py"
    if (-not (Test-Path $script)) {
        Write-Host "${Rojo}Falta chat_openclaw.py en $agentePath${Reset}" -ForegroundColor Red
        return
    }

    Write-Host ""
    Write-Host "${Azul}=== CHAT WEBSOCKET (OpenClaw) ===${Reset}" -ForegroundColor Cyan
    Write-Host "${Amarillo}Abriendo chat via contenedor (cliente WebSocket puro)...${Reset}" -ForegroundColor Yellow
    Write-Host "${Amarillo}Escribe 'salir' para volver al menu.${Reset}" -ForegroundColor Yellow
    Write-Host ""

    $tmpPath = "/tmp/chat_openclaw.py"
    try {
        docker cp $script openclaw:$tmpPath | Out-Null
        docker exec -i openclaw python3 $tmpPath
    } catch {
        Write-Host "${Rojo}Error ejecutando chat dentro del contenedor: $_${Reset}" -ForegroundColor Red
    } finally {
        docker exec openclaw rm -f $tmpPath 2>$null | Out-Null
    }
}

function Start-SaiyDDProxy {
    $proxyScript = Join-Path $agentePath "saiydd_proxy.py"
    if (-not (Test-Path $proxyScript)) {
        Write-Host "${Rojo}Falta saiydd_proxy.py en $agentePath${Reset}" -ForegroundColor Red
        return
    }

    $logFile = Join-Path $agentePath "saiydd_proxy.log"
    $procName = "saiydd_proxy"

    $existing = Get-Process -Name $procName -ErrorAction SilentlyContinue
    if ($existing) {
        Write-Host "${Amarillo}Proxy SaIyDD ya esta corriendo (PID $($existing.Id)).${Reset}" -ForegroundColor Yellow
        return
    }

    Write-Host "${Azul}Iniciando proxy SaIyDD (HTTP -> Ollama) en puerto 3000...${Reset}" -ForegroundColor Cyan

    $psi = New-Object System.Diagnostics.ProcessStartInfo
    $psi.FileName = "python"
    $psi.Arguments = "`"$proxyScript`""
    $psi.WorkingDirectory = $agentePath
    $psi.UseShellExecute = $false
    $psi.RedirectStandardOutput = $true
    $psi.RedirectStandardError = $true
    $psi.CreateNoWindow = $true

    $proc = [System.Diagnostics.Process]::Start($psi)
    if (-not $proc) {
        Write-Host "${Rojo}No se pudo iniciar el proxy.${Reset}" -ForegroundColor Red
        return
    }

    Start-Sleep -Seconds 2
    if ($proc.HasExited) {
        Write-Host "${Rojo}El proxy se cerró inmediatamente. Codigo: $($proc.ExitCode)${Reset}" -ForegroundColor Red
        return
    }

    Write-Host "${Verde}Proxy SaIyDD iniciado (PID $($proc.Id)).${Reset}" -ForegroundColor Green
    Write-Host "${Amarillo}Endpoint: http://127.0.0.1:3000/api/chat${Reset}" -ForegroundColor Yellow
    Write-Host "${Amarillo}Log: $logFile${Reset}" -ForegroundColor Yellow
    Write-Host "${Amarillo}Recorda tener Ollama corriendo en http://localhost:11434${Reset}" -ForegroundColor Yellow
}

function Start-ChatOllama {
    Write-Host ""
    Write-Host "${Azul}=== CHAT OLLAMA (HTTP) ===${Reset}" -ForegroundColor Cyan
    Write-Host "${Amarillo}Modelo: $ollamaModel${Reset}" -ForegroundColor Yellow
    Write-Host "${Amarillo}Escribe 'salir' para volver al menu.${Reset}" -ForegroundColor Yellow
    Write-Host ""

    while ($true) {
        $prompt = Read-Host "> "
        if ($prompt -eq "salir") { break }
        if ([string]::IsNullOrWhiteSpace($prompt)) { continue }

        try {
            $body = @{
                model = $ollamaModel
                prompt = $prompt
                stream = $false
            } | ConvertTo-Json -Compress

            $r = Invoke-WebRequest -Uri "$ollamaHost/api/generate" -Method Post -ContentType "application/json" -Body $body -TimeoutSec 300 -UseBasicParsing
            $data = $r.Content | ConvertFrom-Json
            $text = $data.response
            if ([string]::IsNullOrWhiteSpace($text)) {
                $text = $r.Content
            }
            Write-Host ""
            Write-Host $text
            Write-Host ""
        } catch {
            Write-Host "${Rojo}Error: $_${Reset}" -ForegroundColor Red
            Write-Host ""
        }
    }
}

function Invoke-Verificacion {
    $e = Get-Estado-Servicios
    Write-Host ""
    Write-Host "${Azul}=== DIAGNOSTICO END-TO-END (CONTENEDORES) ===${Reset}" -ForegroundColor Cyan
    function Line($label, $val, $ok) {
        $c = if ($ok) { $Verde } else { $Rojo }
        $m = if ($ok) { "OK " } else { "MAL" }
        Write-Host "  [$c$m${Reset}] $label : $val"
    }
    Line "Docker"                       $e.Docker        ($e.Docker -eq "Ejecutando")
    Line "Contenedor ollama"            $e.OllamaCont    ($e.OllamaCont -eq "running")
    Line "Ollama (red $ollamaHost)"     $e.OllamaHost    ($e.OllamaHost -like "OK*")
    try { $oc = Get-Content (Join-Path $openclawDir "data\openclaw.json") -Raw | ConvertFrom-Json; $primary = ($oc.agents.defaults.model.primary -replace "^ollama/","") } catch { $primary = "qwen2.5-coder:0.5b-16k" }
    Line "Modelo config ($primary)"     $e.OllamaModels  ($e.OllamaModels -like "*$primary*")
    Line "Contenedor openclaw"          $e.Contenedor    ($e.Contenedor -like "running*")
    Line "Skill 'auditor'"              $e.Skill         ($e.Skill -eq "Presente")
    Line "Telegram"                     $e.Telegram      ($e.Telegram -like "OK*")
    Write-Host ""
    $listo = ($e.Docker -eq "Ejecutando") -and ($e.OllamaCont -eq "running") -and ($e.OllamaHost -like "OK*") -and ($e.Contenedor -like "running*") -and ($e.Skill -eq "Presente") -and ($e.Telegram -like "OK*")
    if ($listo) {
        Write-Host "${Verde}PILA LISTA: escribe a tu bot de Telegram (@GProA_Claw_bot).${Reset}" -ForegroundColor Green
    } else {
        Write-Host "${Rojo}Hay componentes por levantar/arreglar (opciones 1 y 4).${Reset}" -ForegroundColor Red
    }
}

function Show-Menu {
    param([hashtable]$e)
    Mostrar-Encabezado
    Write-Host "${Azul}Estado:${Reset}" -ForegroundColor Cyan
    Write-Host "  Docker:      $($e.Docker)"
    Write-Host "  Ollama:      contenedor $($e.OllamaCont)  |  Red: $($e.OllamaHost)"
    Write-Host "  Contenedor:  $($e.Contenedor)"
    Write-Host "  Skill:       $($e.Skill)"
    Write-Host "  Telegram:    $($e.Telegram)"
    Write-Host ""
    Write-Host "${Cyan}--- MENU ---${Reset}" -ForegroundColor Cyan
    Write-Host "  1. Iniciar pila (Ollama + openclaw)"
    Write-Host "  2. Detener pila"
    Write-Host "  3. Ver estado"
    Write-Host "  4. Verificar (diagnostico completo)"
    Write-Host "  5. Auditar proyecto (estructura local)"
    Write-Host "  6. Ver proyectos disponibles"
    Write-Host "  7. Abrir OpenClaw Web UI ($openclawUI)"
    Write-Host "  8. Ver prompts disponibles"
    Write-Host "  9. Chat WebSocket (Python bridge)"
    Write-Host "  10. Chat Ollama (HTTP directo)"
    Write-Host "  11. Iniciar proxy SaIyDD (HTTP -> Ollama)"
    Write-Host "  0. Salir"
    Write-Host ""
}

# ============================================
# PROGRAMA PRINCIPAL
# ============================================

do {
    $e = Get-Estado-Servicios
    Show-Menu -e $e
    $opcion = Read-Host "Selecciona una opcion"
    Write-Host ""

    switch ($opcion) {
        "1" {
            if ($e.Docker -eq "Ejecutando") {
                Start-Pila
                Write-Host ""
                Write-Host "${Verde}Pila iniciada. Verifica con la opcion 4.${Reset}" -ForegroundColor Green
            } else {
                Write-Host "${Rojo}Docker no esta ejecutandose. Inicialo primero.${Reset}" -ForegroundColor Red
            }
        }
        "2" {
            Stop-Pila
            Write-Host "${Verde}Pila detenida.${Reset}" -ForegroundColor Green
        }
        "3" {
            $e | Format-List
        }
        "4" {
            Invoke-Verificacion
        }
        "5" {
            Write-Host "Proyectos disponibles:" -ForegroundColor Cyan
            $i = 1; $proys = @()
            Get-ChildItem $proyectosPath -Directory | ForEach-Object {
                Write-Host "  $i. $($_.Name)"; $proys += $_.Name; $i++
            }
            Write-Host ""
            $sel = Read-Host "Selecciona proyecto (numero)"
            if ($sel -match '^\d+$' -and $sel -gt 0 -and $sel -le $proys.Count) {
                Get-AnalisisProyecto -ruta (Join-Path $proyectosPath $proys[$sel - 1])
            }
        }
        "6" {
            Write-Host "${Azul}Proyectos en GProA (montados en el contenedor):${Reset}" -ForegroundColor Cyan
            Get-ChildItem $proyectosPath -Directory | ForEach-Object { Write-Host "  - $($_.Name)" }
        }
        "7" {
            if ($e.Contenedor -like "running*") {
                Start-Process $openclawUI
                Write-Host "${Verde}Abriendo OpenClaw Web UI...${Reset}" -ForegroundColor Green
            } else {
                Write-Host "${Rojo}El contenedor no esta ejecutandose.${Reset}" -ForegroundColor Red
            }
        }
        "8" {
            Write-Host "${Azul}Prompts disponibles:${Reset}" -ForegroundColor Cyan
            Get-ChildItem "$agentePath\prompts" -File | ForEach-Object { Write-Host "  - $($_.Name)" }
        }
        "9" {
            if ($e.Contenedor -like "running*") {
                Start-ChatWebSocket -Uri $wsUri
            } else {
                Write-Host "${Rojo}El contenedor openclaw no esta ejecutandose. Inicia la pila (opcion 1).${Reset}" -ForegroundColor Red
            }
        }
        "10" {
            if ($e.OllamaHost -like "OK*") {
                Start-ChatOllama
            } else {
                Write-Host "${Rojo}Ollama no esta alcanzable en $ollamaHost. Verifica la opcion 4.${Reset}" -ForegroundColor Red
            }
        }
        "11" {
            Start-SaiyDDProxy
        }
        "0" {
            Write-Host "Hasta luego." -ForegroundColor Green
            break
        }
        default {
            Write-Host "${Rojo}Opcion invalida${Reset}" -ForegroundColor Red
        }
    }

    if ($opcion -ne "0") {
        Write-Host ""
        Read-Host "Presiona Enter para continuar"
    }
} while ($opcion -ne "0")

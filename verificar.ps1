<#
.SYNOPSIS
    Verificacion rapida de la pila Agente_Ollama (sin menu).

.DESCRIPTION
    Comprueba Docker, contenedores Ollama y OpenClaw, modelo disponible,
    skill 'auditor' y Telegram. Sale con codigo 0 si todo esta listo, 1 si falta algo.
    Todo corre en contenedores (Ollama ya NO es nativo).
#>

$ErrorActionPreference = "SilentlyContinue"

$openclawDir = "C:\Users\X1\openclaw-local\openclaw-local"
$ollamaHost  = "http://localhost:11434"
$contOllama  = "ollama"
$contClaw    = "openclaw"

function Test-Ollama { param([string]$u); try { $r = Invoke-WebRequest -Uri "$u/api/tags" -UseBasicParsing -TimeoutSec 5; if ($r.StatusCode -eq 200) { return (($r.Content | ConvertFrom-Json).models | ForEach-Object { $_.name }) -join ", " } } catch {} ; return $null }

docker info > $null 2>&1
$docker = ($LASTEXITCODE -eq 0)
$models = Test-Ollama -u $ollamaHost
$ollamaOk = ($null -ne $models)
try { $estO = docker inspect -f "{{.State.Status}}" $contOllama 2>$null } catch { $estO = "" }
$ollamaContOk = ($estO -eq "running")
try { $estC = docker inspect -f "{{.State.Status}}" $contClaw 2>$null } catch { $estC = "" }
$contOk = ($estC -eq "running")
$skillPath = Join-Path $openclawDir "data\workspace\skills\auditor\SKILL.md"
$skillOk = Test-Path $skillPath
try { $oc = Get-Content (Join-Path $openclawDir "data\openclaw.json") -Raw | ConvertFrom-Json; $primary = ($oc.agents.defaults.model.primary -replace "^ollama/","") } catch { $primary = "qwen2.5-coder:0.5b-16k" }

$tg = "No"
$cfg = Join-Path $openclawDir "data\openclaw.json"
if (Test-Path $cfg) {
    try {
        $j = Get-Content $cfg -Raw | ConvertFrom-Json
        if ($j.channels.telegram.enabled -and $j.channels.telegram.botToken -and $j.channels.telegram.allowFrom.Count -gt 0) {
            $tg = "OK (allowFrom: $($j.channels.telegram.allowFrom -join ', '))"
        }
    } catch {}
}
$tgOk = $tg.StartsWith("OK")

Write-Host "=== DIAGNOSTICO AGENTE_OLLAMA (contenedores) ==="
function L($l,$v,$ok){ $m = if($ok){"OK " }else{"MAL"}; Write-Host "  [$m] $l : $v" }
$dockerS     = if($docker){"Ejecutando"}else{"Detenido"}
$ollamaContS = if($ollamaContOk){$estO}else{"Ausente"}
$ollamaRedS  = if($ollamaOk){"OK ($models)"}else{"No alcanzable en $ollamaHost"}
$contS       = if($contOk){$estC}else{"Ausente"}
$skillS      = if($skillOk){"Presente"}else{"No encontrado"}
L "Docker"                     $dockerS     $docker
L "Contenedor ollama"          $ollamaContS $ollamaContOk
L "Ollama (red $ollamaHost)"   $ollamaRedS  $ollamaOk
L "Modelo config ($primary)"   $models      ($models -like "*$primary*")
L "Contenedor openclaw"        $contS       $contOk
L "Skill 'auditor'"            $skillS      $skillOk
L "Telegram"                   $tg          $tgOk
Write-Host ""

$listo = $docker -and $ollamaContOk -and $ollamaOk -and $contOk -and $skillOk -and $tgOk
if ($listo) { Write-Host "RESULTADO: PILA LISTA. Escribe a @GProA_Claw_bot."; exit 0 }
else { Write-Host "RESULTADO: Faltan componentes. Ejecuta iniciar_servicios.bat."; exit 1 }

# Auditoria Forense de OpenClaw: Estado Actual (2026-07-06)

Documento de diagnostico de la instalacion de OpenClaw en
`C:\Users\X1\openclaw-local\openclaw-local`. Basado en evidencia viva
(contenedor, logs, configuracion montada y pruebas de inferencia).

---

## 1. Estado por Componente

### Docker / Contenedor
- **Estado:** VERDE. Contenedor `openclaw` `Up` y `healthy`.
- **Puertos:** `18789` (gateway WS), `30001` (OpenClaw Web UI), `18791`
  (browser control).
- **Evidencia:** `docker ps` + `docker logs openclaw`.

### Ollama (LLM)
- **Estado:** VERDE. Contenedor `ollama` `Up` (publicado en `localhost:11434` y
  accesible por el contenedor `openclaw` vía DNS interno `http://ollama:11434`).
- **Modelos:** `qwen2.5-coder:0.5b-16k` (primario del agente), `qwen2.5-coder:1.5b-16k`,
  `llama3.2:latest`, entre otros, en el volumen `ollama_data`.
- **Prueba de inferencia:** `api/generate` desde el contenedor `openclaw` devolvió
  respuesta válida ("Hi") vía Node/fetch. Funciona.
- **Riesgo histórico resuelto:** los timeouts `LLM request timed out` de logs
  antiguos se debían a la ruta contenedor→host (WinNAT/RSC) que perdía el body
  de los POST. Se resolvió moviendo Ollama a un contenedor en la misma red
  Docker (ruta interna `ollama:11434`), sin tocar la red del host.

### OpenClaw Gateway
- **Estado:** VERDE. `gateway listening on ws://127.0.0.1:18789`.
- **Modelo del agente:** `ollama/qwen2.5-coder:0.5b-16k`.

### Skill `auditor`
- **Estado:** VERDE. Desplegado en
  `data/workspace/skills/auditor/` con `SKILL.md` y
  `references/{auditar_proyecto,explicar_codigo}.md`.
- Verificado presente dentro del contenedor en
  `/home/node/.openclaw/workspace/skills/auditor/SKILL.md`.

### Telegram
- **Estado:** VERDE (configurado). Bot `@GProA_Claw_bot` con `botToken` y
  `allowFrom`. El proveedor arranca y envia mensajes (evidencia en logs:
  `sendMessage ok chat=...`).
- **Nota:** el `allowFrom` efectivo vive en `data/openclaw.json` (el mount de
  `./data` sombrea a `./openclaw.json`). Se sincronizo para incluir ambos IDs
  conocidos (8062595618 y 8748287677).

### Proyectos montados
- **Estado:** VERDE. `GProA` montado en
  `/home/node/.openclaw/workspace/projects` (`:ro`).
- Proyectos actuales: `NeumatiQ`, `Pagina_web`, `Sistema_Humpty`,
  `Memoria Ricardo Corona`, `Agente_Ollama`.

---

## 2. Hallazgos y Recomendaciones

| # | Hallazgo | Severidad | Accion |
|---|----------|-----------|--------|
| 1 | `low context window: ollama/llama3.2 ctx=16384 (warn<32000)` | Info | Solo warning. Opcional: subir `contextWindow` en `models.json`. |
| 2 | `telegram: restarting (reason: stale-socket)` | Baja | Reconexion automatica del proveedor; no afecta uso. |
| 3 | `botToken` de Telegram en texto plano | Media | Mover a `.env` si el producto lo soporta. |
| 4 | Dos `openclaw.json` (raiz vs `data`) con `allowFrom` distinto | Baja | Ya sincronizados; usar `data/openclaw.json` como canonico. |

---

## 3. Conclusion

La pila esta **funcional de extremo a extremo**: Ollama responde, el skill
`auditor` esta desplegado, los proyectos estan montados y Telegram esta
configurado. Para usarla: arranca la pila (`iniciar_servicios.bat` o
`Agente_Ollama.ps1` opcion 1) y escribe a `@GProA_Claw_bot`.

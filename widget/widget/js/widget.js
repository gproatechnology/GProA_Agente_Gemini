/*
 * GProA Gemini Widget - Lógica JavaScript
 * Widget embebible para inserción en cualquier página web
 */

(function() {
    'use strict';

    // Configuración
    const CONFIG = {
        API_BASE_URL: 'https://gproa-agente-gemini.onrender.com',
        ENDPOINT_CHAT: '/api/chat',
        ENDPOINT_MODELS: '/api/modelos',
        MODELO_PREDETERMINADO: 'models/gemini-2.5-flash'
    };

    // Estado del widget
    let estado = {
        abierto: false,
        pestaña: 'chat',
        historial: [],
        modelo: CONFIG.MODELO_PREDETERMINADO,
        escribiendo: false
    };

    // Elementos DOM
    let elementos = {};

    // Inicializar widget
    function init() {
        crearHTML();
        cargarEstilos();
        agregarEventos();
        console.log('🤖 GProA Gemini Widget inicializado');
    }

    // Crear estructura HTML del widget
    function crearHTML() {
        const widgetHTML = `
            <!-- Botón flotante -->
            <button id="gproa-gemini-toggle" aria-label="Abrir asistente GProA">
                <i class="fab fa-whatsapp"></i>
            </button>

            <!-- Panel del chat -->
            <div id="gproa-gemini-panel" style="display: none;">
                <button class="gemini-close-panel" id="gproa-close" aria-label="Cerrar">&times;</button>
                
                <!-- Header -->
                <div class="gemini-header">
                    <div class="gemini-logo">
                        <i class="fab fa-whatsapp"></i>
                        <span>GProA Asistente</span>
                    </div>
                </div>
                
                <!-- Pestañas -->
                <div class="gemini-tabs">
                    <button class="gemini-tab active" id="tab-chat">Chat</button>
                    <button class="gemini-tab" id="tab-auditar">Auditar Archivo</button>
                    <button class="gemini-tab" id="tab-proyecto">Auditar Proyecto</button>
                </div>
                
                <!-- Contenido de pestañas -->
                <div class="gemini-contenido">
                    <!-- Chat -->
                    <div id="gproa-tab-chat" class="gemini-tab-content activo">
                        <div class="gemini-messages" id="gproa-mensajes">
                            <div class="gemini-empty">
                                <h3>Asistente GProA</h3>
                                <p>¿En qué puedo ayudarte hoy?</p>
                            </div>
                        </div>
                        <div class="gemini-input-area">
                            <input type="text" id="gproa-input" placeholder="Escribe tu pregunta..." autocomplete="off" />
                            <button id="gproa-enviar">Enviar</button>
                        </div>
                    </div>
                    
                    <!-- Auditar archivo -->
                    <div id="gproa-tab-auditar" class="gemini-tab-content oculto">
                        <div class="gemini-formulario">
                            <label>Ruta del proyecto:</label>
                            <input type="text" id="audit-ruta" placeholder="Ej: ./src/js/main.js" />
                            <label style="margin-top: 1rem;">Archivo:</label>
                            <input type="text" id="audit-archivo" placeholder="Ej: src/js/main.js" />
                            <button id="gproa-auditar-archivo">Analizar Archivo</button>
                            <div id="gproa-resultado-auditar" style="margin-top: 1rem;"></div>
                        </div>
                    </div>
                    
                    <!-- Auditar proyecto -->
                    <div id="gproa-tab-proyecto" class="gemini-tab-content oculto">
                        <div class="gemini-formulario">
                            <label>Ruta del proyecto:</label>
                            <input type="text" id="audit-proyecto-ruta" placeholder="Ej: ./" />
                            <button id="gproa-auditar-proyecto">Analizar Proyecto</button>
                            <div id="gproa-resultado-proyecto" style="margin-top: 1rem;"></div>
                        </div>
                    </div>
                </div>
            </div>
        `;

        // Insertar al final del body
        const contenedor = document.createElement('div');
        contenedor.innerHTML = widgetHTML;
        document.body.appendChild(contenedor);

        // Guardar referencias a elementos
        elementos = {
            toggle: document.getElementById('gproa-gemini-toggle'),
            panel: document.getElementById('gproa-gemini-panel'),
            cerrar: document.getElementById('gproa-close'),
            mensajes: document.getElementById('gproa-mensajes'),
            input: document.getElementById('gproa-input'),
            enviar: document.getElementById('gproa-enviar'),
            estado: document.getElementById('gproa-estado'),
            pestañas: document.querySelectorAll('.gemini-tab'),
            contenidos: document.querySelectorAll('.gemini-tab-content')
        };
    }

    // Cargar estilos CSS
    function cargarEstilos() {
        // Verificar si ya están cargados
        if (document.getElementById('gproa-widget-css')) return;

        const link = document.createElement('link');
        link.id = 'gproa-widget-css';
        link.rel = 'stylesheet';
        link.href = 'https://gproa-agente-gemini.onrender.com/widget.css';
        document.head.appendChild(link);

        // Fallback: insertar CSS directamente si no carga
        link.onerror = function() {
            insertarCSS();
        };
    }

    function insertarCSS() {
        const css = `
            :root {
                --gproa-dark: #050812;
                --gproa-darker: #0a0f1c;
                --gproa-primary: #00e0ff;
                --gproa-secondary: #8a2be2;
                --gproa-gray: #b8c5d6;
                --gproa-bg-card: rgba(20, 30, 50, 0.9);
                --gproa-border: rgba(0, 224, 255, 0.15);
            }
            * { box-sizing: border-box; margin: 0; padding: 0; }
            body { font-family: 'Segoe UI', 'Exo 2', sans-serif; }
            
            /* Botón flotante */
            #gproa-gemini-toggle {
                position: fixed;
                bottom: 20px;
                right: 20px;
                width: 60px;
                height: 60px;
                background: linear-gradient(135deg, var(--gproa-primary), var(--gproa-secondary));
                border-radius: 50%;
                border: none;
                color: #0a0f1c;
                font-weight: 700;
                font-size: 24px;
                cursor: pointer;
                box-shadow: 0 4px 20px rgba(0, 224, 255, 0.4);
                z-index: 9999;
                display: flex;
                align-items: center;
                justify-content: center;
                transition: transform 0.3s ease;
            }
            #gproa-gemini-toggle:hover { transform: translateY(-3px); box-shadow: 0 6px 25px rgba(0, 224, 255, 0.5); }
            
            /* Panel principal */
            #gproa-gemini-panel {
                position: fixed;
                bottom: 90px;
                right: 20px;
                width: 380px;
                height: 550px;
                background: linear-gradient(145deg, rgba(20, 30, 50, 0.95), rgba(10, 20, 35, 0.98));
                border: 1px solid var(--gproa-border);
                border-radius: 16px;
                box-shadow: 0 10px 40px rgba(0, 0, 0, 0.5);
                overflow: hidden;
                display: none;
                flex-direction: column;
                z-index: 9999;
                animation: slideUp 0.3s ease;
            }
            @keyframes slideUp { from { opacity: 0; transform: translateY(20px); } to { opacity: 1; transform: translateY(0); } }
            
            /* Header */
            .gemini-header {
                background: linear-gradient(180deg, #0a0f1c 0%, #050812 100%);
                border-bottom: 1px solid var(--gproa-border);
                padding: 1rem;
                display: flex;
                align-items: center;
                justify-content: space-between;
            }
            .gemini-logo {
                display: flex;
                align-items: center;
                gap: 8px;
                color: #ffffff;
                font-family: 'Orbitron', monospace;
                font-size: 1.1rem;
                font-weight: 700;
                letter-spacing: 1px;
            }
            .gemini-logo i { color: var(--gproa-primary); }
            .gemini-close-panel {
                background: none;
                border: none;
                color: var(--gproa-gray);
                font-size: 1.5rem;
                cursor: pointer;
                padding: 0.5rem;
                border-radius: 6px;
            }
            .gemini-close-panel:hover { background: rgba(255, 255, 255, 0.1); color: #ffffff; }
            
            /* Pestañas */
            .gemini-tabs {
                display: flex;
                gap: 0;
                border-bottom: 1px solid var(--gproa-border);
            }
            .gemini-tab {
                flex: 1;
                padding: 0.8rem;
                background: rgba(0, 0, 0, 0.2);
                border: none;
                color: var(--gproa-gray);
                font-size: 0.85rem;
                font-weight: 600;
                cursor: pointer;
                transition: all 0.3s ease;
                text-transform: uppercase;
            }
            .gemini-tab:hover { background: rgba(0, 224, 255, 0.1); color: #ffffff; }
            .gemini-tab.active {
                background: rgba(0, 224, 255, 0.15);
                color: var(--gproa-primary);
                border-bottom: 2px solid var(--gproa-primary);
            }
            
            /* Contenido de pestañas */
            .gemini-contenido {
                flex: 1;
                overflow-y: auto;
                background: rgba(5, 8, 12, 0.9);
            }
            .gemini-tab-content {
                display: none;
                padding: 1.5rem;
                height: 100%;
                overflow-y: auto;
            }
            .gemini-tab-content.activo {
                display: block;
            }
            .gemini-tab-content.oculto {
                display: none;
            }
            
            /* Estilos generales de contenido */
            .gemini-messages {
                flex: 1;
                padding: 1rem;
                overflow-y: auto;
                display: flex;
                flex-direction: column;
                gap: 1rem;
                background: rgba(0, 0, 0, 0.2);
            }
            .gemini-msg-user {
                display: flex;
                justify-content: flex-end;
                align-items: flex-end;
                gap: 0.5rem;
            }
            .gemini-msg-user .msg-content {
                background: linear-gradient(135deg, var(--gproa-primary), var(--gproa-secondary));
                color: #0a0f1c;
                padding: 0.8rem 1rem;
                border-radius: 12px 12px 4px 12px;
                max-width: 75%;
                font-size: 0.9rem;
                line-height: 1.4;
                box-shadow: 0 2px 10px rgba(0, 224, 255, 0.2);
            }
            .gemini-msg-assistant {
                display: flex;
                align-items: flex-start;
                gap: 0.5rem;
            }
            .gemini-msg-assistant .msg-avatar {
                width: 32px;
                height: 32px;
                background: linear-gradient(135deg, var(--gproa-secondary), var(--gproa-primary));
                border-radius: 50%;
                display: flex;
                align-items: center;
                justify-content: center;
                color: #0a0f1c;
                font-weight: 700;
                font-size: 0.9rem;
                flex-shrink: 0;
            }
            .gemini-msg-assistant .msg-content {
                background: rgba(0, 0, 0, 0.3);
                color: #ffffff;
                padding: 0.8rem 1rem;
                border-radius: 12px 12px 12px 4px;
                max-width: 75%;
                font-size: 0.9rem;
                line-height: 1.4;
                border-left: 3px solid var(--gproa-primary);
            }
            .gemini-empty {
                display: flex;
                flex-direction: column;
                align-items: center;
                justify-content: center;
                height: 100%;
                color: var(--gproa-gray);
                text-align: center;
            }
            .gemini-empty h3 { color: #ffffff; margin-bottom: 0.5rem; }
            .gemini-empty p { font-size: 0.9rem; line-height: 1.5; }
            
            /* Formularios */
            .gemini-formulario {
                display: flex;
                flex-direction: column;
                gap: 1rem;
                color: #ffffff;
                font-size: 0.9rem;
            }
            .gemini-formulario label {
                font-weight: 600;
                margin-bottom: 0.3rem;
            }
            .gemini-formulario input {
                background: rgba(0, 0, 0, 0.3);
                border: 1px solid var(--gproa-border);
                border-radius: 8px;
                color: #ffffff;
                padding: 0.8rem 1rem;
                font-size: 0.9rem;
                font-family: inherit;
                outline: none;
                width: 100%;
            }
            .gemini-formulario input:focus {
                border-color: var(--gproa-primary);
                outline: none;
            }
            .gemini-formulario button {
                background: linear-gradient(135deg, var(--gproa-primary), var(--gproa-secondary));
                border: none;
                border-radius: 8px;
                color: #0a0f1c;
                font-weight: 700;
                padding: 0.8rem 1.2rem;
                cursor: pointer;
                transition: transform 0.2s;
                margin-top: 0.5rem;
            }
            .gemini-formulario button:hover {
                transform: translateY(-2px);
            }
            
            /* Área de entrada */
            .gemini-input-area {
                background: rgba(10, 15, 28, 0.9);
                border-top: 1px solid var(--gproa-border);
                padding: 1rem;
                display: flex;
                gap: 0.5rem;
            }
            .gemini-input {
                flex: 1;
                background: rgba(0, 0, 0, 0.3);
                border: 1px solid var(--gproa-border);
                border-radius: 8px;
                color: #ffffff;
                padding: 0.8rem 1rem;
                font-size: 0.9rem;
                font-family: inherit;
                outline: none;
            }
            .gemini-input:focus {
                border-color: var(--gproa-primary);
                outline: none;
            }
            .gemini-send {
                background: linear-gradient(135deg, var(--gproa-primary), var(--gproa-secondary));
                border: none;
                border-radius: 8px;
                color: #0a0f1c;
                font-weight: 700;
                padding: 0.8rem 1.2rem;
                cursor: pointer;
                transition: transform 0.2s;
            }
            .gemini-send:hover { transform: translateY(-2px); }
            .gemini-send:disabled { opacity: 0.6; cursor: not-allowed; }
            
            /* Resultado de auditoría */
            #gproa-resultado-auditar, #gproa-resultado-proyecto {
                background: rgba(0, 0, 0, 0.3);
                border: 1px solid var(--gproa-border);
                border-radius: 8px;
                padding: 1rem;
                margin-top: 1rem;
                color: #ffffff;
                font-size: 0.85rem;
                line-height: 1.5;
                overflow-y: auto;
                max-height: 200px;
            }
            
            /* Escapar HTML para prevenir XSS */
            
            /* Responsivo */
            @media (max-width: 480px) {
                #gproa-gemini-panel {
                    width: calc(100vw - 20px);
                    right: 10px;
                    bottom: 90px;
                    height: 60vh;
                }
                #gproa-gemini-toggle {
                    bottom: 15px;
                    right: 15px;
                }
            }
        `;
        const style = document.createElement('style');
        style.textContent = css;
        document.head.appendChild(style);
    }

    // Agregar eventos
    function agregarEventos() {
        // Abrir/cerrar panel
        elementos.toggle.addEventListener('click', togglePanel);
        elementos.cerrar.addEventListener('click', togglePanel);

        // Pestañas
        elementos.pestañas.forEach(btn => {
            btn.addEventListener('click', function() {
                // Remover clase activa de todas
                elementos.pestañas.forEach(p => p.classList.remove('active'));
                elementos.contenidos.forEach(c => c.classList.remove('activo'));
                elementos.contenidos.forEach(c => c.classList.add('oculto'));
                
                // Activar seleccionada
                btn.classList.add('active');
                const tabId = btn.id.replace('tab-', '');
                document.getElementById('gproa-tab-' + tabId).classList.remove('oculto');
                document.getElementById('gproa-tab-' + tabId).classList.add('activo');
                estado.pestaña = tabId;
            });
        });

        // Enviar mensaje con Enter
        elementos.input.addEventListener('keypress', function(e) {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                enviarMensaje();
            }
        });

        // Botón enviar
        elementos.enviar.addEventListener('click', enviarMensaje);

        // Botón auditar archivo
        const btnAuditarArchivo = document.getElementById('gproa-auditar-archivo');
        if (btnAuditarArchivo) {
            btnAuditarArchivo.addEventListener('click', function() {
                const ruta = document.getElementById('audit-ruta').value.trim();
                const archivo = document.getElementById('audit-archivo').value.trim();
                if (!ruta || !archivo) {
                    document.getElementById('gproa-resultado-auditar').innerHTML = '<span style="color:#e74c3c;">Ingresa ruta y archivo</span>';
                    return;
                }
                auditarArchivo(ruta, archivo);
            });
        }

        // Botón auditar proyecto
        const btnAuditarProyecto = document.getElementById('gproa-auditar-proyecto');
        if (btnAuditarProyecto) {
            btnAuditarProyecto.addEventListener('click', function() {
                const ruta = document.getElementById('audit-proyecto-ruta').value.trim();
                if (!ruta) {
                    document.getElementById('gproa-resultado-proyecto').innerHTML = '<span style="color:#e74c3c;">Ingresa ruta del proyecto</span>';
                    return;
                }
                auditarProyecto(ruta);
            });
        }

        // Cerrar al hacer clic fuera (opcional)
        document.addEventListener('click', function(e) {
            if (!elementos.panel.contains(e.target) && !elementos.toggle.contains(e.target) && estado.abierto) {
                // No cerrar automáticamente al hacer clic fuera
            }
        });
    }

    // Toggle panel
    function togglePanel() {
        estado.abierto = !estado.abierto;
        if (estado.abierto) {
            elementos.panel.style.display = 'flex';
            elementos.input.focus();
        } else {
            elementos.panel.style.display = 'none';
        }
    }

    // Enviar mensaje
    async function enviarMensaje() {
        const texto = elementos.input.value.trim();
        if (!texto || estado.escribiendo) return;

        // Agregar mensaje del usuario
        agregarMensajeUsuario(texto);
        elementos.input.value = '';
        estado.escribiendo = true;

        try {
            const respuesta = await llamarAPI(texto);
            agregarMensajeAgente(respuesta.respuesta);
        } catch (error) {
            console.error('Error:', error);
            agregarMensajeAgente('Lo siento, ocurrió un error al procesar tu mensaje. Inténtalo de nuevo.');
        } finally {
            estado.escribiendo = false;
        }
    }

    // Agregar mensaje de usuario
    function agregarMensajeUsuario(texto) {
        const div = document.createElement('div');
        div.className = 'gemini-msg-user';
        div.innerHTML = `<div class="msg-content">${escapeHTML(texto)}</div>`;
        elementos.mensajes.appendChild(div);
        scrollAlFinal();
    }

    // Agregar mensaje del agente
    function agregarMensajeAgente(texto) {
        const div = document.createElement('div');
        div.className = 'gemini-msg-assistant';
        div.innerHTML = `
            <div class="msg-avatar">G</div>
            <div class="msg-content">${escapeHTML(texto)}</div>
        `;
        elementos.mensajes.appendChild(div);
        scrollAlFinal();
    }

    // Auditar archivo
    async function auditarArchivo(ruta, archivo) {
        const contenedor = document.getElementById('gproa-resultado-auditar');
        contenedor.innerHTML = '<span style="color:var(--gproa-primary);">Analizando archivo...</span>';
        
        try {
            const respuesta = await fetch(`${CONFIG.API_BASE_URL}/api/chat`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    mensaje: `Analiza este archivo: ${ruta}${archivo}. ¿Qué hace? ¿Tiene problemas o sugerencias de mejora?`,
                    modelo: estado.modelo
                })
            });
            const data = await response.json();
            if (!response.ok) throw new Error(data.error || 'Error en la respuesta');
            contenedor.innerHTML = `<div style="color:#ffffff; line-height:1.5;">${escapeHTML(data.respuesta)}</div>`;
        } catch (error) {
            contenedor.innerHTML = `<span style="color:#e74c3c;">Error: ${error.message}</span>`;
        }
    }

    // Auditar proyecto
    async function auditarProyecto(ruta) {
        const contenedor = document.getElementById('gproa-resultado-proyecto');
        contenedor.innerHTML = '<span style="color:var(--gproa-primary);">Analizando proyecto...</span>';
        
        try {
            const respuesta = await fetch(`${CONFIG.API_BASE_URL}/api/chat`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    mensaje: `Haz un resumen ejecutivo del proyecto en ${ruta}. ¿Qué hace? ¿Qué tecnologías usa? ¿Qué mejorarías?`,
                    modelo: estado.modelo
                })
            });
            const data = await response.json();
            if (!response.ok) throw new Error(data.error || 'Error en la respuesta');
            contenedor.innerHTML = `<div style="color:#ffffff; line-height:1.5;">${escapeHTML(data.respuesta)}</div>`;
        } catch (error) {
            contenedor.innerHTML = `<span style="color:#e74c3c;">Error: ${error.message}</span>`;
        }
    }

    // Escapar HTML para prevenir XSS
    function escapeHTML(texto) {
        const div = document.createElement('div');
        div.textContent = texto;
        return div.innerHTML;
    }

    // Scroll al final
    function scrollAlFinal() {
        elementos.mensajes.scrollTop = elementos.mensajes.scrollHeight;
    }

    // Exponer API pública
    window.gproaGemini = {
        abrir: function() { if (!estado.abierto) togglePanel(); },
        cerrar: function() { if (estado.abierto) togglePanel(); },
        alternar: togglePanel,
        enviar: function(texto) {
            if (texto) {
                elementos.input.value = texto;
                enviarMensaje();
            }
        }
    };

    // Inicializar cuando el DOM esté listo
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
})();

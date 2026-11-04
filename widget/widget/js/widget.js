/*
 * GProA Gemini Widget - Lógica JavaScript
 * Widget embebible para inserción en cualquier página web
 */

(function() {
    'use strict';

    // Configuración
    const CONFIG = {
        API_BASE_URL: 'https://gproa-glucai.onrender.com', // Cambiar por tu URL de Render
        ENDPOINT_CHAT: '/api/chat',
        ENDPOINT_MODELS: '/api/modelos',
        MODELO_PREDETERMINADO: 'models/gemini-2.5-flash'
    };

    // Estado del widget
    let estado = {
        abierto: false,
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
                <i>🤖</i>
            </button>

            <!-- Panel del chat -->
            <div id="gproa-gemini-panel" style="display: none;">
                <button class="gemini-close-panel" id="gproa-close" aria-label="Cerrar">&times;</button>
                <div class="gemini-header">
                    <h2>🤖 GProA Gemini</h2>
                    <div id="gproa-estado" style="font-size: 0.75rem; color: var(--gproa-primary);"></div>
                </div>
                
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
            estado: document.getElementById('gproa-estado')
        };
    }

    // Cargar estilos CSS
    function cargarEstilos() {
        // Verificar si ya están cargados
        if (document.getElementById('gproa-widget-css')) return;

        const link = document.createElement('link');
        link.id = 'gproa-widget-css';
        link.rel = 'stylesheet';
        link.href = 'https://gproa-glucai.onrender.com/widget/css/widget.css';
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
            #gproa-gemini-widget { position: fixed; bottom: 20px; right: 20px; z-index: 9999; font-family: 'Segoe UI', 'Exo 2', sans-serif; font-size: 14px; }
            #gproa-gemini-toggle { position: fixed; bottom: 20px; right: 20px; width: 60px; height: 60px; background: linear-gradient(135deg, var(--gproa-primary), var(--gproa-secondary)); border-radius: 50%; border: none; color: #0a0f1c; font-weight: 700; font-size: 24px; cursor: pointer; box-shadow: 0 4px 20px rgba(0, 224, 255, 0.4); z-index: 10000; display: flex; align-items: center; justify-content: center; transition: transform 0.3s ease; }
            #gproa-gemini-toggle:hover { transform: translateY(-3px); box-shadow: 0 6px 25px rgba(0, 224, 255, 0.5); }
            #gproa-gemini-panel { position: fixed; bottom: 90px; right: 20px; width: 380px; height: 500px; background: linear-gradient(145deg, rgba(20, 30, 50, 0.95), rgba(10, 20, 35, 0.98)); border: 1px solid var(--gproa-border); border-radius: 16px; box-shadow: 0 10px 40px rgba(0, 0, 0, 0.5); overflow: hidden; display: flex; flex-direction: column; z-index: 9999; animation: slideUp 0.3s ease; }
            @keyframes slideUp { from { opacity: 0; transform: translateY(20px); } to { opacity: 1; transform: translateY(0); } }
            .gemini-header { background: linear-gradient(180deg, #0a0f1c 0%, #050812 100%); border-bottom: 1px solid var(--gproa-border); padding: 1rem; display: flex; align-items: center; justify-content: space-between; }
            .gemini-header h2 { margin: 0; color: #ffffff; font-family: 'Orbitron', monospace; font-size: 1.1rem; letter-spacing: 1px; display: flex; align-items: center; gap: 8px; }
            .gemini-header h2 i { color: var(--gproa-primary); }
            .gemini-close { background: none; border: none; color: var(--gproa-gray); font-size: 1.2rem; cursor: pointer; padding: 0.5rem; border-radius: 6px; transition: background 0.2s; }
            .gemini-close:hover { background: rgba(255, 255, 255, 0.1); color: #ffffff; }
            .gemini-messages { flex: 1; padding: 1rem; overflow-y: auto; display: flex; flex-direction: column; gap: 1rem; background: rgba(0, 0, 0, 0.2); }
            .gemini-msg-user { display: flex; justify-content: flex-end; align-items: flex-end; gap: 0.5rem; }
            .gemini-msg-user .msg-content { background: linear-gradient(135deg, var(--gproa-primary), var(--gproa-secondary)); color: #0a0f1c; padding: 0.8rem 1rem; border-radius: 12px 12px 4px 12px; max-width: 75%; font-size: 0.9rem; line-height: 1.4; box-shadow: 0 2px 10px rgba(0, 224, 255, 0.2); }
            .gemini-msg-assistant { display: flex; align-items: flex-start; gap: 0.5rem; }
            .gemini-msg-assistant .msg-avatar { width: 32px; height: 32px; background: linear-gradient(135deg, var(--gproa-secondary), var(--gproa-primary)); border-radius: 50%; display: flex; align-items: center; justify-content: center; color: #0a0f1c; font-weight: 700; font-size: 0.9rem; flex-shrink: 0; }
            .gemini-msg-assistant .msg-content { background: rgba(0, 0, 0, 0.3); color: #ffffff; padding: 0.8rem 1rem; border-radius: 12px 12px 12px 4px; max-width: 75%; font-size: 0.9rem; line-height: 1.4; border-left: 3px solid var(--gproa-primary); }
            .gemini-input-area { background: rgba(10, 15, 28, 0.9); border-top: 1px solid var(--gproa-border); padding: 1rem; display: flex; gap: 0.5rem; }
            .gemini-input { flex: 1; background: rgba(0, 0, 0, 0.3); border: 1px solid var(--gproa-border); border-radius: 8px; color: #ffffff; padding: 0.8rem 1rem; font-size: 0.9rem; font-family: inherit; outline: none; }
            .gemini-input:focus { border-color: var(--gproa-primary); outline: none; }
            .gemini-send { background: linear-gradient(135deg, var(--gproa-primary), var(--gproa-secondary)); border: none; border-radius: 8px; color: #0a0f1c; font-weight: 700; padding: 0.8rem 1.2rem; cursor: pointer; transition: transform 0.2s; }
            .gemini-send:hover { transform: translateY(-2px); }
            .gemini-send:disabled { opacity: 0.6; cursor: not-allowed; }
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

        // Enviar mensaje con Enter
        elementos.input.addEventListener('keypress', function(e) {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                enviarMensaje();
            }
        });

        // Botón enviar
        elementos.enviar.addEventListener('click', enviarMensaje);

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

    // Mostrar indicador de escritura
    function mostrarEscribiendo() {
        const div = document.createElement('div');
        div.className = 'gemini-typing';
        div.id = 'gproa-typing';
        div.innerHTML = `
            <div class="msg-avatar">G</div>
            <div class="typing-dots">
                <div class="typing-dot"></div>
                <div class="typing-dot"></div>
                <div class="typing-dot"></div>
            </div>
        `;
        elementos.mensajes.appendChild(div);
        scrollAlFinal();
    }

    // Ocultar indicador de escritura
    function ocultarEscribiendo() {
        const typing = document.getElementById('gproa-typing');
        if (typing) typing.remove();
    }

    // Llamar a la API
    async function llamarAPI(mensaje) {
        mostrarEscribiendo();
        try {
            const response = await fetch(`${CONFIG.API_BASE_URL}${CONFIG.ENDPOINT_CHAT}`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    mensaje: mensaje,
                    modelo: estado.modelo
                })
            });

            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.error || 'Error en la respuesta del servidor');
            }

            return data;
        } catch (error) {
            throw error;
        } finally {
            ocultarEscribiendo();
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

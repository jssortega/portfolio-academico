/*
 * ═══════════════════════════════════════════════════════════════════════════
 *  Dashboard del agente supervisor del profesor — Villa Olivar (Nivel 2)
 *  Sistemas Multiagente · Universidad de Jaén · Departamento de Informática
 * ═══════════════════════════════════════════════════════════════════════════
 *
 *  Carga el estado completo desde /supervisor/api/state, se suscribe a
 *  /supervisor/api/stream (SSE) para recibir actualizaciones en vivo,
 *  y permite seleccionar cualquier ejecución pasada del almacén SQLite
 *  desde el selector de la cabecera. Replica los patrones del
 *  supervisor de TicTacToe.
 */

(() => {
    "use strict";

    const VALOR_EN_VIVO = "live";
    const URL_STATE          = "/supervisor/api/state";
    const URL_STREAM         = "/supervisor/api/stream";
    const URL_FINALIZAR      = "/supervisor/api/finalizar";
    const URL_INYECTAR       = "/supervisor/api/inyectar";
    const URL_ESCENARIOS     = "/supervisor/api/escenarios";
    const URL_LISTA_EJEC     = "/supervisor/api/ejecuciones";
    const URL_DETALLE_EJEC   = (id) => `/supervisor/api/ejecuciones/${id}`;
    const URL_CSV_VIVO       = (t) => `/supervisor/api/csv/${t}`;
    const URL_CSV_EJEC       = (id, t) => `/supervisor/api/ejecuciones/${id}/csv/${t}`;

    // ── Estado global del cliente ─────────────────────────────────

    const estado = {
        supervisor: { jid: "", modo: "consulta", es_vivo: true },
        grupos: [],
        seguimientos: [],
        resumen: { total: 0, ok: 0, ko: 0,
                   por_estado: {}, por_grupo: {}, por_tipo: {},
                   latencia_agree_ms: { mediana: 0, p95: 0, maximo: 0 },
                   latencia_informe_ms: { mediana: 0, p95: 0, maximo: 0 } },
        estados_agentes: [],
        log: [],
        timestamp: "",
    };
    let grupoActivo = "";
    let pestanaActiva = "seguimientos";
    let ejecucionSeleccionada = VALOR_EN_VIVO;
    let fuenteSSE = null;
    let supervisorFinalizado = false;

    const TABS = [
        { id: "seguimientos", etiqueta: "Seguimientos" },
        { id: "estados",      etiqueta: "Estados de agentes" },
        { id: "resumen",      etiqueta: "Resumen" },
        { id: "log",          etiqueta: "Registro" },
    ];

    // ── Inicialización ────────────────────────────────────────────

    document.addEventListener("DOMContentLoaded", async () => {
        inicializarTema();
        inicializarReloj();
        inicializarBotonInyectar();
        inicializarBotonFinalizar();
        inicializarSelectorEjecucion();
        renderizarTabs();

        await cargarListaEjecuciones();
        await cargarEstadoEnVivo();

        // Si el supervisor está en modo consulta y hay ejecuciones,
        // auto-seleccionamos la más reciente para que el usuario vea
        // datos sin tener que tocar el selector.
        if (!estado.supervisor.es_vivo) {
            const select = document.getElementById("sv-ejecucion-select");
            const primeraHistorica = Array.from(select.options).find(
                (o) => o.value !== VALOR_EN_VIVO,
            );
            if (primeraHistorica) {
                select.value = primeraHistorica.value;
                ejecucionSeleccionada = primeraHistorica.value;
                await cargarEjecucionHistorica(primeraHistorica.value);
            }
        } else {
            conectarSSE();
        }
    });

    // ── Tema diurno/nocturno ─────────────────────────────────────

    function inicializarTema() {
        const guardado = localStorage.getItem("sv-tema") || "dark";
        document.documentElement.setAttribute("data-theme", guardado);
        actualizarIconoTema();

        const boton = document.getElementById("theme-toggle");
        boton.addEventListener("click", () => {
            const actual = document.documentElement.getAttribute("data-theme");
            const nuevo = actual === "dark" ? "light" : "dark";
            document.documentElement.setAttribute("data-theme", nuevo);
            localStorage.setItem("sv-tema", nuevo);
            actualizarIconoTema();
        });
    }

    function actualizarIconoTema() {
        const tema = document.documentElement.getAttribute("data-theme");
        const knob = document.getElementById("theme-toggle-knob");
        knob.textContent = tema === "dark" ? "🌙" : "☀️";
    }

    // ── Reloj de cabecera ────────────────────────────────────────

    function inicializarReloj() {
        const reloj = document.getElementById("sv-clock");
        const tick = () => {
            const ahora = new Date();
            const hh = String(ahora.getHours()).padStart(2, "0");
            const mm = String(ahora.getMinutes()).padStart(2, "0");
            const ss = String(ahora.getSeconds()).padStart(2, "0");
            reloj.textContent = `${hh}:${mm}:${ss}`;
        };
        tick();
        setInterval(tick, 1000);
    }

    // ── Botón Inyectar incidente ──────────────────────────────────
    //
    // Al pulsar el botón se abre un mini formulario en modal donde
    // el profesor escoge el grupo destino y el escenario del
    // catálogo. Si deja "Aleatorio", el backend elige un escenario
    // al azar (compatibilidad con el comportamiento previo).

    let escenariosCache = null;

    async function cargarEscenariosUnaVez() {
        if (escenariosCache !== null) return escenariosCache;
        try {
            const resp = await fetch(URL_ESCENARIOS);
            const datos = await resp.json();
            escenariosCache = datos.escenarios || [];
        } catch (err) {
            console.error("Fallo al cargar escenarios:", err);
            escenariosCache = [];
        }
        return escenariosCache;
    }

    function rellenarSelectGrupo() {
        const select = document.getElementById("inyectar-grupo");
        select.innerHTML = "";
        estado.grupos.forEach((grupo) => {
            const opcion = document.createElement("option");
            opcion.value = grupo.id;
            opcion.textContent = grupo.nombre
                ? `${grupo.id} — ${grupo.nombre}`
                : grupo.id;
            select.appendChild(opcion);
        });
    }

    function rellenarSelectEscenario(escenarios) {
        const select = document.getElementById("inyectar-escenario");
        // Limpiamos todo menos la opción "aleatorio" que ya está en el HTML.
        const opcionAleatorio = select.options[0];
        select.innerHTML = "";
        select.appendChild(opcionAleatorio);
        escenarios.forEach((esc) => {
            const opcion = document.createElement("option");
            opcion.value = esc.clave;
            opcion.textContent =
                `${esc.clave} · ${esc.tipo_emergencia}/${esc.prioridad}`;
            opcion.title = `${esc.ubicacion} — ${esc.descripcion}`;
            select.appendChild(opcion);
        });
    }

    function abrirDialogoInyectar() {
        const overlay = document.getElementById("inyectar-overlay");
        document.getElementById("inyectar-mensaje").textContent = "";
        rellenarSelectGrupo();
        overlay.classList.remove("hidden");
        document.getElementById("inyectar-grupo").focus();
    }

    function cerrarDialogoInyectar() {
        document.getElementById("inyectar-overlay")
            .classList.add("hidden");
    }

    async function enviarInyeccion(evento) {
        evento.preventDefault();
        const idGrupo = document.getElementById("inyectar-grupo").value;
        const claveEscenario =
            document.getElementById("inyectar-escenario").value;
        const boton = document.getElementById("inyectar-confirmar");
        const mensajeEl = document.getElementById("inyectar-mensaje");

        boton.disabled = true;
        boton.textContent = "Inyectando…";
        mensajeEl.textContent = "";

        const cuerpo = { grupo: idGrupo };
        if (claveEscenario) cuerpo.clave_escenario = claveEscenario;

        try {
            const resp = await fetch(URL_INYECTAR, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(cuerpo),
            });
            const datos = await resp.json().catch(() => ({}));
            if (resp.ok) {
                mensajeEl.textContent =
                    `Inyectado: ${datos.tipo_emergencia}/`
                    + `${datos.prioridad} a ${datos.grupo}`;
                mensajeEl.dataset.tono = "ok";
                setTimeout(cerrarDialogoInyectar, 900);
            } else {
                mensajeEl.textContent =
                    "Error: " + (datos.error || resp.statusText);
                mensajeEl.dataset.tono = "ko";
            }
        } catch (err) {
            console.error("Fallo al inyectar:", err);
            mensajeEl.textContent = "Fallo de red al inyectar.";
            mensajeEl.dataset.tono = "ko";
        } finally {
            boton.disabled = false;
            boton.textContent = "Inyectar";
        }
    }

    function inicializarBotonInyectar() {
        const boton = document.getElementById("sv-inyectar");
        if (boton === null) return;

        boton.addEventListener("click", async () => {
            if (estado.supervisor.modo !== "activo") {
                alert(
                    "El supervisor está en modo consulta. Para "
                    + "inyectar incidentes arráncalo con --modo activo.",
                );
                return;
            }
            if (estado.grupos.length === 0) {
                alert(
                    "No hay grupos configurados en "
                    + "agente_profesor/config_profesor.yaml.",
                );
                return;
            }
            const escenarios = await cargarEscenariosUnaVez();
            rellenarSelectEscenario(escenarios);
            abrirDialogoInyectar();
        });

        document.getElementById("inyectar-form")
            .addEventListener("submit", enviarInyeccion);
        document.getElementById("inyectar-cerrar")
            .addEventListener("click", cerrarDialogoInyectar);
        document.getElementById("inyectar-cancelar")
            .addEventListener("click", cerrarDialogoInyectar);
        document.getElementById("inyectar-overlay")
            .addEventListener("click", (ev) => {
                if (ev.target.id === "inyectar-overlay") {
                    cerrarDialogoInyectar();
                }
            });
    }

    // ── Botón Finalizar ───────────────────────────────────────────

    function inicializarBotonFinalizar() {
        const boton = document.getElementById("sv-finalizar");
        boton.addEventListener("click", async () => {
            if (supervisorFinalizado) return;

            const confirmar = confirm(
                "¿Finalizar el supervisor? Se cerrará el servidor "
                + "y el panel dejará de actualizarse."
            );
            if (!confirmar) return;

            boton.disabled = true;
            boton.textContent = "Finalizando…";

            let carpetaCsv = "";
            try {
                const respuesta = await fetch(
                    URL_FINALIZAR, { method: "POST" },
                );
                const datos = await respuesta.json().catch(() => ({}));
                if (datos.csv_exportados) {
                    carpetaCsv = datos.csv_carpeta || "";
                }
            } catch (err) {
                console.error("Fallo al finalizar:", err);
            }

            // El servidor activa el evento de parada en ~300 ms.
            // Cerramos nosotros la suscripción SSE para no provocar
            // reintentos automáticos de EventSource.
            cerrarSSE();
            mostrarOverlayFinalizado(carpetaCsv);
        });
    }

    function mostrarOverlayFinalizado(carpetaCsv) {
        supervisorFinalizado = true;
        const overlay = document.getElementById("sv-fin-overlay");
        overlay.classList.remove("hidden");
        document.getElementById("sv-online-dot").style.background
            = "var(--ko)";

        // Si el servidor ha guardado los CSV automáticos, mostramos
        // la ruta al usuario para que sepa dónde encontrarlos sin
        // tener que ir al terminal.
        const aviso = document.getElementById("sv-fin-csv");
        if (aviso) {
            if (carpetaCsv) {
                aviso.classList.remove("hidden");
                aviso.querySelector(".sv-fin-csv-ruta").textContent
                    = carpetaCsv;
            } else {
                aviso.classList.add("hidden");
            }
        }
    }

    // ── Selector de ejecuciones ──────────────────────────────────

    function inicializarSelectorEjecucion() {
        const select = document.getElementById("sv-ejecucion-select");
        select.addEventListener("change", async (evento) => {
            const valor = evento.target.value;
            ejecucionSeleccionada = valor;
            if (valor === VALOR_EN_VIVO) {
                await cargarEstadoEnVivo();
                conectarSSE();
            } else {
                cerrarSSE();
                await cargarEjecucionHistorica(valor);
            }
        });
    }

    async function cargarListaEjecuciones() {
        try {
            const respuesta = await fetch(URL_LISTA_EJEC);
            const datos = await respuesta.json();
            const select = document.getElementById("sv-ejecucion-select");

            // Limpiamos opciones excepto "En vivo"
            select.innerHTML = "";
            const opLive = document.createElement("option");
            opLive.value = VALOR_EN_VIVO;
            opLive.textContent = "En vivo";
            select.appendChild(opLive);

            for (const ejec of (datos.ejecuciones || [])) {
                const op = document.createElement("option");
                op.value = String(ejec.id);
                op.textContent = ejec.etiqueta
                    || `#${ejec.id} · ${ejec.modo}`;
                select.appendChild(op);
            }
        } catch (err) {
            console.error("Fallo al cargar ejecuciones:", err);
        }
    }

    // ── Carga de estado ──────────────────────────────────────────

    async function cargarEstadoEnVivo() {
        try {
            const respuesta = await fetch(URL_STATE);
            const datos = await respuesta.json();
            actualizarEstado(datos);
        } catch (err) {
            console.error("Fallo al cargar estado en vivo:", err);
        }
    }

    async function cargarEjecucionHistorica(idEjec) {
        try {
            const respuesta = await fetch(URL_DETALLE_EJEC(idEjec));
            if (!respuesta.ok) {
                console.warn("Ejecución no disponible:", idEjec);
                return;
            }
            const datos = await respuesta.json();
            actualizarEstado(datos);
        } catch (err) {
            console.error("Fallo al cargar ejecución:", err);
        }
    }

    // ── Suscripción SSE para actualizaciones en vivo ────────────

    function conectarSSE() {
        cerrarSSE();
        if (supervisorFinalizado) return;

        fuenteSSE = new EventSource(URL_STREAM);

        fuenteSSE.addEventListener("state", (evento) => {
            try {
                actualizarEstado(JSON.parse(evento.data));
            } catch (err) {
                console.error("Fallo al procesar SSE state:", err);
            }
        });

        fuenteSSE.addEventListener("seguimiento", (evento) => {
            try {
                aplicarActualizacionSeguimiento(JSON.parse(evento.data));
            } catch (err) {
                console.error("Fallo al procesar SSE seguimiento:", err);
            }
        });

        fuenteSSE.addEventListener("log", (evento) => {
            try {
                const datos = JSON.parse(evento.data);
                estado.log.unshift(datos);
                if (pestanaActiva === "log") renderizarPanel();
            } catch (err) {
                console.error("Fallo al procesar SSE log:", err);
            }
        });

        fuenteSSE.addEventListener("cierre", () => {
            cerrarSSE();
            mostrarOverlayFinalizado();
        });

        fuenteSSE.onerror = () => {
            const dot = document.getElementById("sv-online-dot");
            if (dot) dot.style.background = "var(--warn)";
        };
    }

    function cerrarSSE() {
        if (fuenteSSE) {
            fuenteSSE.close();
            fuenteSSE = null;
        }
    }

    // ── Actualización del estado y re-render ────────────────────

    function actualizarEstado(datos) {
        Object.assign(estado, datos);
        if (!grupoActivo && estado.grupos.length > 0) {
            grupoActivo = estado.grupos[0].id;
        }
        renderizarTodo();
    }

    function aplicarActualizacionSeguimiento(seguimiento) {
        const idx = estado.seguimientos.findIndex(
            (s) => s.id_emergencia === seguimiento.id_emergencia,
        );
        if (idx >= 0) {
            estado.seguimientos[idx] = seguimiento;
        } else {
            estado.seguimientos.unshift(seguimiento);
        }
        renderizarTodo();
    }

    function renderizarTodo() {
        renderizarHeaderInfo();
        renderizarSidebar();
        renderizarStats();
        renderizarPanel();
    }

    // ── Cabecera ─────────────────────────────────────────────────

    function renderizarHeaderInfo() {
        document.getElementById("sv-supervisor-jid").textContent
            = estado.supervisor.jid || "profesor_emergencias@—";
        document.getElementById("sv-modo").textContent
            = estado.supervisor.modo || "consulta";
        const stats = `${estado.grupos.length} grupos · `
            + `${estado.seguimientos.length} seguimientos`;
        document.getElementById("sv-global-stats").textContent = stats;

        // El dot se vuelve gris en vista histórica para que el
        // usuario sepa que no hay flujo en vivo.
        const dot = document.getElementById("sv-online-dot");
        if (dot && !supervisorFinalizado) {
            const enVivo = ejecucionSeleccionada === VALOR_EN_VIVO
                && estado.supervisor.es_vivo;
            dot.style.background = enVivo ? "var(--ok)" : "var(--muted)";
        }
    }

    // ── Sidebar de grupos ────────────────────────────────────────

    function renderizarSidebar() {
        const cont = document.getElementById("sv-grupos-list");
        cont.innerHTML = "";

        const vistaGeneral = crearItemGrupo({
            id: "",
            nombre: "Vista general",
            descripcion: "Resumen agregado de todos los grupos",
        }, totalSeguimientos(), totalOK(), totalKO());
        cont.appendChild(vistaGeneral);

        for (const grupo of estado.grupos) {
            const seguimientos = seguimientosDeGrupo(grupo.id);
            const ok = seguimientos.filter(esOK).length;
            const ko = seguimientos.filter(esKO).length;
            cont.appendChild(
                crearItemGrupo(grupo, seguimientos.length, ok, ko),
            );
        }
    }

    function crearItemGrupo(grupo, total, ok, ko) {
        const div = document.createElement("div");
        div.className = "sv-grupo-item";
        if (grupoActivo === grupo.id) div.classList.add("active");

        const nombre = grupo.nombre || grupo.id || "Vista general";
        const meta = grupo.jid_centralita || grupo.descripcion || "—";

        div.innerHTML = `
            <div class="sv-grupo-nombre">${escaparHTML(nombre)}</div>
            <div class="sv-grupo-meta">${escaparHTML(meta)}</div>
            <div class="sv-grupo-pills">
                <span class="sv-pill">${total} segs</span>
                <span class="sv-pill ok">${ok} OK</span>
                <span class="sv-pill ko">${ko} KO</span>
            </div>
        `;
        div.addEventListener("click", () => {
            grupoActivo = grupo.id;
            renderizarTodo();
        });
        return div;
    }

    // ── Métricas (cabecera del panel) ────────────────────────────

    function renderizarStats() {
        const cont = document.getElementById("sv-stats");
        cont.innerHTML = "";

        const seguimientos = seguimientosVisibles();
        const ok = seguimientos.filter(esOK).length;
        const ko = seguimientos.filter(esKO).length;
        const enCurso = seguimientos.length - ok - ko;

        const latAgree = mediana(
            seguimientos.map((s) => s.latencia_agree_ms)
                .filter((v) => v != null),
        );
        const latInforme = mediana(
            seguimientos.map((s) => s.latencia_informe_ms)
                .filter((v) => v != null),
        );

        const tarjetas = [
            { label: "Seguimientos", value: seguimientos.length,
              sub: estado.timestamp },
            { label: "Resueltos", value: ok, claseExtra: "ok",
              sub: porcentaje(ok, seguimientos.length) },
            { label: "En error", value: ko, claseExtra: "ko",
              sub: porcentaje(ko, seguimientos.length) },
            { label: "En curso", value: enCurso, claseExtra: "warn",
              sub: porcentaje(enCurso, seguimientos.length) },
            { label: "Latencia agree (mediana)",
              value: formatearMs(latAgree),
              sub: "request → agree" },
            { label: "Latencia informe (mediana)",
              value: formatearMs(latInforme),
              sub: "agree → inform" },
        ];

        for (const t of tarjetas) {
            const div = document.createElement("div");
            div.className = "sv-stat" + (t.claseExtra ? " " + t.claseExtra : "");
            div.innerHTML = `
                <div class="sv-stat-label">${escaparHTML(t.label)}</div>
                <div class="sv-stat-value">${escaparHTML(String(t.value))}</div>
                <div class="sv-stat-sub">${escaparHTML(t.sub || "")}</div>
            `;
            cont.appendChild(div);
        }

        document.getElementById("sv-grupo-nombre").textContent
            = grupoActivo ? grupoActivo : "Vista general";

        let descripcion = "Resumen agregado de todos los grupos";
        if (grupoActivo) {
            descripcion = "Seguimientos del grupo seleccionado";
        }
        if (ejecucionSeleccionada !== VALOR_EN_VIVO) {
            const select = document.getElementById("sv-ejecucion-select");
            const opcion = Array.from(select.options).find(
                (o) => o.value === ejecucionSeleccionada,
            );
            if (opcion) {
                descripcion += ` · ${opcion.textContent}`;
            }
        }
        document.getElementById("sv-grupo-desc").textContent = descripcion;
    }

    // ── Pestañas ─────────────────────────────────────────────────

    function renderizarTabs() {
        const cont = document.getElementById("sv-tabs");
        cont.innerHTML = "";
        for (const tab of TABS) {
            const btn = document.createElement("button");
            btn.className = "sv-tab";
            if (tab.id === pestanaActiva) btn.classList.add("active");
            btn.setAttribute("role", "tab");
            btn.innerHTML = `${escaparHTML(tab.etiqueta)}`
                + `<span class="sv-tab-badge" id="badge-${tab.id}">0</span>`;
            btn.addEventListener("click", () => {
                pestanaActiva = tab.id;
                renderizarTabs();
                renderizarPanel();
            });
            cont.appendChild(btn);
        }
        actualizarBadgesTabs();
    }

    function actualizarBadgesTabs() {
        const segs = seguimientosVisibles();
        const set = (id, valor) => {
            const el = document.getElementById(`badge-${id}`);
            if (el) el.textContent = String(valor);
        };
        set("seguimientos", segs.length);
        set("estados", estado.grupos.length);
        set("resumen", Object.keys(estado.resumen.por_estado || {}).length);
        set("log", estado.log.length);
    }

    // ── Panel central ────────────────────────────────────────────

    function renderizarPanel() {
        actualizarBadgesTabs();
        const cont = document.getElementById("sv-panel-content");
        cont.innerHTML = "";

        const acciones = document.createElement("div");
        acciones.className = "sv-panel-actions";
        const csv = (tipo) =>
            ejecucionSeleccionada === VALOR_EN_VIVO
                ? URL_CSV_VIVO(tipo)
                : URL_CSV_EJEC(ejecucionSeleccionada, tipo);
        acciones.innerHTML = `
            <a class="sv-btn" href="${csv('seguimientos')}" download>⤓ CSV seguimientos</a>
            <a class="sv-btn" href="${csv('resumen')}" download>⤓ CSV resumen</a>
            <a class="sv-btn" href="${csv('log')}" download>⤓ CSV log</a>
        `;
        cont.appendChild(acciones);

        if (pestanaActiva === "seguimientos") {
            cont.appendChild(crearTablaSeguimientos());
        } else if (pestanaActiva === "estados") {
            cont.appendChild(crearTablaEstados());
        } else if (pestanaActiva === "resumen") {
            cont.appendChild(crearPanelResumen());
        } else if (pestanaActiva === "log") {
            cont.appendChild(crearPanelLog());
        }
    }

    function crearTablaSeguimientos() {
        const seguimientos = seguimientosVisibles();
        if (seguimientos.length === 0) {
            return crearVacio(
                "Aún no hay seguimientos en este grupo.",
            );
        }

        const wrap = document.createElement("div");
        wrap.className = "sv-table-wrap";
        wrap.innerHTML = `
            <table class="sv-table">
                <thead>
                    <tr>
                        <th>ID</th>
                        <th>Grupo</th>
                        <th>Tipo</th>
                        <th>Prioridad</th>
                        <th>Estado</th>
                        <th>Latencia agree</th>
                        <th>Latencia inform</th>
                    </tr>
                </thead>
                <tbody></tbody>
            </table>
        `;
        const tbody = wrap.querySelector("tbody");
        for (const s of seguimientos) {
            const tr = document.createElement("tr");
            const idCorto = (s.id_emergencia || "").slice(0, 8);
            tr.innerHTML = `
                <td><span class="sv-id">${escaparHTML(idCorto)}</span></td>
                <td>${escaparHTML(s.grupo)}</td>
                <td>${escaparHTML(s.tipo_emergencia)}</td>
                <td>${escaparHTML(s.prioridad)}</td>
                <td><span class="sv-estado-tag ${s.estado}">${s.estado}</span></td>
                <td>${formatearMs(s.latencia_agree_ms)}</td>
                <td>${formatearMs(s.latencia_informe_ms)}</td>
            `;
            tr.addEventListener("click", () => abrirModalSeguimiento(s));
            tbody.appendChild(tr);
        }
        return wrap;
    }

    function crearTablaEstados() {
        if (estado.grupos.length === 0) {
            return crearVacio(
                "No hay grupos configurados. Añade grupos en "
                + "agente_profesor/config_profesor.yaml para "
                + "empezar a sondearlos.",
            );
        }
        const filas = (estado.estados_agentes || [])
            .filter((e) => !grupoActivo || e.grupo === grupoActivo);
        if (filas.length === 0) {
            return crearVacio(
                "Aún no se han recibido respuestas de sondeo. "
                + "El supervisor envía un query-ref periódico a cada "
                + "agente del grupo; aquí aparecerán las respuestas.",
            );
        }
        const wrap = document.createElement("div");
        wrap.className = "sv-table-wrap";
        wrap.innerHTML = `
            <table class="sv-table">
                <thead>
                    <tr>
                        <th>Grupo</th>
                        <th>Rol</th>
                        <th>JID</th>
                        <th>Estado</th>
                        <th>Emergencia actual</th>
                        <th>Latencia</th>
                        <th>Último sondeo</th>
                    </tr>
                </thead>
                <tbody></tbody>
            </table>
        `;
        const tbody = wrap.querySelector("tbody");
        for (const e of filas) {
            const tr = document.createElement("tr");
            tr.innerHTML = `
                <td>${escaparHTML(e.grupo)}</td>
                <td>${escaparHTML(e.rol)}</td>
                <td><span class="sv-id">${escaparHTML(e.jid)}</span></td>
                <td>${escaparHTML(e.estado)}</td>
                <td>${escaparHTML(e.emergencia_actual || "—")}</td>
                <td>${formatearMs(e.latencia_ms)}</td>
                <td>${escaparHTML(formatearISO(e.marca_temporal))}</td>
            `;
            tbody.appendChild(tr);
        }
        return wrap;
    }

    function crearPanelResumen() {
        const r = estado.resumen;
        const wrap = document.createElement("div");

        const filaTotales = `
            <div class="sv-stats-grid">
                <div class="sv-stat ok">
                    <div class="sv-stat-label">Resueltos</div>
                    <div class="sv-stat-value">${r.ok}</div>
                </div>
                <div class="sv-stat ko">
                    <div class="sv-stat-label">En error</div>
                    <div class="sv-stat-value">${r.ko}</div>
                </div>
                <div class="sv-stat">
                    <div class="sv-stat-label">Latencia agree (P95)</div>
                    <div class="sv-stat-value">${formatearMs(r.latencia_agree_ms.p95)}</div>
                </div>
                <div class="sv-stat">
                    <div class="sv-stat-label">Latencia informe (P95)</div>
                    <div class="sv-stat-value">${formatearMs(r.latencia_informe_ms.p95)}</div>
                </div>
            </div>
        `;

        wrap.innerHTML = filaTotales
            + crearTablaReparto("Por estado", r.por_estado)
            + crearTablaReparto("Por grupo", r.por_grupo)
            + crearTablaReparto("Por tipo de emergencia", r.por_tipo);
        return wrap;
    }

    function crearTablaReparto(titulo, datos) {
        const filas = Object.entries(datos || {}).map(
            ([k, v]) => `<tr><td>${escaparHTML(k)}</td><td>${v}</td></tr>`,
        ).join("");
        if (!filas) return "";
        return `
            <h3 style="color:var(--primary);margin:18px 0 8px 0;font-size:1rem">
                ${escaparHTML(titulo)}
            </h3>
            <div class="sv-table-wrap">
                <table class="sv-table">
                    <thead><tr><th>Clave</th><th>Total</th></tr></thead>
                    <tbody>${filas}</tbody>
                </table>
            </div>
        `;
    }

    function crearPanelLog() {
        const cont = document.createElement("div");
        cont.className = "sv-log";
        if (estado.log.length === 0) {
            cont.innerHTML = `<div style="color:var(--muted);padding:14px">
                Sin eventos registrados todavía.
            </div>`;
            return cont;
        }
        for (const evento of estado.log) {
            const fila = document.createElement("div");
            fila.className = "sv-log-row";
            const tipo = (evento.tipo || "").toLowerCase();
            fila.innerHTML = `
                <span class="sv-log-ts">${escaparHTML(evento.ts || "")}</span>
                <span class="sv-log-tipo ${tipo}">${escaparHTML(evento.tipo || "")}</span>
                <span class="sv-log-detalle">
                    <strong>${escaparHTML(evento.de || "")}</strong> —
                    ${escaparHTML(evento.detalle || "")}
                </span>
            `;
            cont.appendChild(fila);
        }
        return cont;
    }

    function crearVacio(mensaje) {
        const div = document.createElement("div");
        div.className = "sv-empty";
        div.textContent = mensaje;
        return div;
    }

    // ── Modal de detalle ─────────────────────────────────────────

    function abrirModalSeguimiento(s) {
        const overlay = document.getElementById("modal-overlay");
        const body = document.getElementById("modal-body");

        const eventosHTML = (s.eventos || []).map((ev) => `
            <div class="sv-timeline-event">
                <span class="sv-timeline-ts">${escaparHTML(formatearISO(ev.instante))}</span>
                <span class="sv-timeline-tipo">${escaparHTML(ev.tipo)}</span>
                <div class="sv-timeline-detalle">
                    ${escaparHTML(ev.detalle || "")}
                </div>
            </div>
        `).join("");

        const informeHTML = s.informe
            ? renderizarInforme(s.informe)
            : "";

        const errorHTML = s.error
            ? `<div style="margin-top:14px;color:var(--ko);font-weight:600">
                 Error: ${escaparHTML(s.error)}
               </div>`
            : "";

        body.innerHTML = `
            <h3>Seguimiento ${escaparHTML(s.tipo_emergencia)}
                <span class="sv-estado-tag ${s.estado}"
                      style="margin-left:6px">${s.estado}</span></h3>
            <div class="sv-modal-meta">
                ${escaparHTML(s.id_emergencia)} · grupo
                ${escaparHTML(s.grupo)} · prioridad
                ${escaparHTML(s.prioridad)}
            </div>
            <div style="color:var(--secondary);margin-bottom:12px">
                ${escaparHTML(s.descripcion || "")}
            </div>
            <h4 style="color:var(--primary);font-size:0.95rem">Línea de tiempo</h4>
            <div class="sv-timeline">${eventosHTML}</div>
            ${errorHTML}
            ${informeHTML}
        `;

        overlay.classList.remove("hidden");
        overlay.addEventListener("click", cerrarModal, { once: true });
        document.getElementById("modal-close")
            .addEventListener("click", cerrarModal, { once: true });
    }

    function cerrarModal() {
        document.getElementById("modal-overlay").classList.add("hidden");
    }

    // ── Render del InformeResolucion ─────────────────────────────
    //
    // El informe llega como dict con campos del modelo Pydantic
    // InformeResolucion (ver ontologia/modelos_compartidos.py).
    // En vez de volcar JSON crudo, lo presentamos como ficha
    // legible: resumen destacado, metadatos en cuadrícula, agentes
    // como chips y acciones como lista numerada.
    //
    // Campos conocidos que ya tienen su propio bloque visual:
    const CAMPOS_INFORME_CONOCIDOS = new Set([
        "tipo_mensaje", "id_emergencia", "tipo_emergencia",
        "prioridad", "estado_final", "resumen",
        "agentes_participantes", "acciones_realizadas",
        "marca_temporal",
    ]);

    function renderizarInforme(informe) {
        const resumen = informe.resumen || "";
        const estadoFinal = informe.estado_final || "—";
        const marca = informe.marca_temporal
            ? formatearFechaCompleta(informe.marca_temporal)
            : "—";

        const agentes = Array.isArray(informe.agentes_participantes)
            ? informe.agentes_participantes : [];
        const acciones = Array.isArray(informe.acciones_realizadas)
            ? informe.acciones_realizadas : [];

        const chipsAgentes = agentes.length === 0
            ? `<span class="sv-informe-vacio">
                 No se ha indicado ningún agente.
               </span>`
            : agentes.map((jid) => {
                const nombre = String(jid).split("@")[0] || jid;
                return `<span class="sv-chip-agente"
                              title="${escaparHTML(jid)}">
                          ${escaparHTML(nombre)}
                        </span>`;
            }).join("");

        const listaAcciones = acciones.length === 0
            ? `<li class="sv-informe-vacio">
                 No se han registrado acciones.
               </li>`
            : acciones.map((accion) => `
                <li>${escaparHTML(accion)}</li>
            `).join("");

        // Campos que vengan en el informe pero que no encajen en
        // ninguna sección dedicada se muestran en una tabla genérica
        // para que no se pierda información.
        const camposExtra = Object.entries(informe)
            .filter(([clave]) => !CAMPOS_INFORME_CONOCIDOS.has(clave));
        const tablaExtra = camposExtra.length === 0 ? "" : `
            <h5 class="sv-informe-subtitulo">Datos adicionales</h5>
            <table class="sv-informe-tabla">
                ${camposExtra.map(([clave, valor]) => `
                    <tr>
                        <th>${escaparHTML(clave)}</th>
                        <td>${escaparHTML(formatearValorInforme(valor))}</td>
                    </tr>
                `).join("")}
            </table>
        `;

        const jsonOriginal = escaparHTML(
            JSON.stringify(informe, null, 2),
        );

        const resultado = `
            <h4 class="sv-informe-titulo">
                Informe de resolución
                <span class="sv-informe-estado">
                    ${escaparHTML(estadoFinal)}
                </span>
            </h4>

            ${resumen ? `
                <div class="sv-informe-resumen">
                    ${escaparHTML(resumen)}
                </div>
            ` : ""}

            <dl class="sv-informe-meta">
                <div>
                    <dt>Tipo de emergencia</dt>
                    <dd>${escaparHTML(informe.tipo_emergencia || "—")}</dd>
                </div>
                <div>
                    <dt>Prioridad</dt>
                    <dd>${escaparHTML(informe.prioridad || "—")}</dd>
                </div>
                <div>
                    <dt>Cierre</dt>
                    <dd>${escaparHTML(marca)}</dd>
                </div>
                <div>
                    <dt>ID de emergencia</dt>
                    <dd class="sv-informe-mono">
                        ${escaparHTML(informe.id_emergencia || "—")}
                    </dd>
                </div>
            </dl>

            <h5 class="sv-informe-subtitulo">
                Agentes participantes
                <span class="sv-informe-contador">
                    (${agentes.length})
                </span>
            </h5>
            <div class="sv-chips-agentes">${chipsAgentes}</div>

            <h5 class="sv-informe-subtitulo">
                Acciones realizadas
                <span class="sv-informe-contador">
                    (${acciones.length})
                </span>
            </h5>
            <ol class="sv-informe-acciones">${listaAcciones}</ol>

            ${tablaExtra}

            <details class="sv-informe-json">
                <summary>Ver JSON original</summary>
                <pre class="sv-json">${jsonOriginal}</pre>
            </details>
        `;
        return resultado;
    }

    function formatearFechaCompleta(iso) {
        const fecha = new Date(iso);
        if (isNaN(fecha.getTime())) return iso;
        const dd = String(fecha.getDate()).padStart(2, "0");
        const mm = String(fecha.getMonth() + 1).padStart(2, "0");
        const yyyy = fecha.getFullYear();
        const hh = String(fecha.getHours()).padStart(2, "0");
        const mi = String(fecha.getMinutes()).padStart(2, "0");
        const ss = String(fecha.getSeconds()).padStart(2, "0");
        return `${dd}/${mm}/${yyyy} ${hh}:${mi}:${ss}`;
    }

    function formatearValorInforme(valor) {
        if (valor == null) return "—";
        if (Array.isArray(valor)) return valor.join(", ");
        if (typeof valor === "object") return JSON.stringify(valor);
        return String(valor);
    }

    // ── Helpers ──────────────────────────────────────────────────

    function seguimientosVisibles() {
        const resultado = grupoActivo
            ? seguimientosDeGrupo(grupoActivo)
            : estado.seguimientos.slice();
        return resultado;
    }

    function seguimientosDeGrupo(grupoId) {
        return estado.seguimientos.filter((s) => s.grupo === grupoId);
    }

    const ESTADOS_OK_JS = new Set(["RESUELTO"]);
    const ESTADOS_KO_JS = new Set(["RECHAZADO", "TIMEOUT", "FALLIDO"]);

    function esOK(s) { return ESTADOS_OK_JS.has(s.estado); }
    function esKO(s) { return ESTADOS_KO_JS.has(s.estado); }

    function totalSeguimientos() { return estado.seguimientos.length; }
    function totalOK() { return estado.seguimientos.filter(esOK).length; }
    function totalKO() { return estado.seguimientos.filter(esKO).length; }

    function mediana(valores) {
        if (!valores.length) return null;
        const orden = valores.slice().sort((a, b) => a - b);
        const idx = Math.floor(orden.length / 2);
        return orden[idx];
    }

    function formatearMs(valor) {
        if (valor == null) return "—";
        if (valor < 1000) return `${valor} ms`;
        return `${(valor / 1000).toFixed(2)} s`;
    }

    function formatearISO(iso) {
        if (!iso) return "";
        const fecha = new Date(iso);
        if (isNaN(fecha.getTime())) return iso;
        const hh = String(fecha.getHours()).padStart(2, "0");
        const mm = String(fecha.getMinutes()).padStart(2, "0");
        const ss = String(fecha.getSeconds()).padStart(2, "0");
        return `${hh}:${mm}:${ss}`;
    }

    function porcentaje(parte, total) {
        if (!total) return "0%";
        return `${Math.round((parte / total) * 100)}%`;
    }

    function escaparHTML(texto) {
        return String(texto)
            .replaceAll("&", "&amp;")
            .replaceAll("<", "&lt;")
            .replaceAll(">", "&gt;")
            .replaceAll('"', "&quot;")
            .replaceAll("'", "&#39;");
    }

})();

// ==============================
// ESTADO GLOBAL
// ==============================

let currentPage = 1;
const perPage = 50;
let currentFilters = {};

// ==============================
// INIT
// ==============================

document.addEventListener("DOMContentLoaded", () => {
    cargarEstadisticas();
    cargarFiltros();
    cargarLetras();

    const buscadorFTS = document.getElementById("buscadorFTS");
    if (buscadorFTS) {
        buscadorFTS.addEventListener("keydown", e => {
            if (e.key === "Enter") buscarFullText();
        });
    }

    document.addEventListener("keydown", e => {
        if (e.key === "Escape") cerrarModal();
    });
});

// ==============================
// TABS
// ==============================

function switchTab(tab) {
    document.querySelectorAll(".tab").forEach(t => t.classList.remove("active"));
    document.querySelectorAll(".tab-content").forEach(t => t.classList.remove("active"));

    document.querySelector(`[data-tab="${tab}"]`).classList.add("active");
    document.getElementById(`tab-${tab}`).classList.add("active");

    if (tab === "estadisticas") cargarCharts();
    if (tab === "explorar") cargarLetras();
    if (tab === "descubrir") cargarNubePalabras();
    if (tab === "cronologia") cargarTimeline();
    if (tab === "poetica") iniciarTabPoetica();
}

// ==============================
// ESTADISTICAS HEADER
// ==============================

function cargarEstadisticas() {
    fetch("/api/estadisticas")
        .then(r => r.json())
        .then(stats => {
            document.getElementById("statTotal").textContent = stats.total_letras.toLocaleString("es-ES");
            document.getElementById("statAnios").textContent = stats.total_anios;
            document.getElementById("statModalidades").textContent = stats.total_modalidades;
            document.getElementById("statAgrupaciones").textContent = stats.total_agrupaciones.toLocaleString("es-ES");
            window._stats = stats;
        });
}

// ==============================
// FILTROS
// ==============================

function cargarFiltros() {
    fetch("/api/filtros")
        .then(r => r.json())
        .then(data => {
            const selAnio = document.getElementById("filtroAnio");
            data.anios.forEach(a => {
                const opt = document.createElement("option");
                opt.value = a;
                opt.textContent = a;
                selAnio.appendChild(opt);
            });

            const selMod = document.getElementById("filtroModalidad");
            data.modalidades.forEach(m => {
                const opt = document.createElement("option");
                opt.value = m;
                opt.textContent = m;
                selMod.appendChild(opt);
            });

            const selTipo = document.getElementById("filtroTipo");
            data.tipos_pieza.forEach(t => {
                const opt = document.createElement("option");
                opt.value = t;
                opt.textContent = t;
                selTipo.appendChild(opt);
            });
        });
}

function aplicarFiltros() {
    currentPage = 1;
    currentFilters = {};

    const anio = document.getElementById("filtroAnio").value;
    const modalidad = document.getElementById("filtroModalidad").value;
    const tipo = document.getElementById("filtroTipo").value;
    const agrupacion = document.getElementById("filtroAgrupacion").value.trim();

    if (anio) currentFilters["anio"] = anio;
    if (modalidad) currentFilters["modalidad"] = modalidad;
    if (tipo) currentFilters["tipo_pieza"] = tipo;
    if (agrupacion) currentFilters["agrupacion"] = agrupacion;

    cargarLetras();
}

function limpiarFiltros() {
    document.getElementById("filtroAnio").value = "";
    document.getElementById("filtroModalidad").value = "";
    document.getElementById("filtroTipo").value = "";
    document.getElementById("filtroAgrupacion").value = "";
    currentFilters = {};
    currentPage = 1;
    cargarLetras();
}

// ==============================
// CARGAR LETRAS
// ==============================

function cargarLetras() {
    const params = new URLSearchParams(currentFilters);
    params.set("page", currentPage);
    params.set("per_page", perPage);

    const lista = document.getElementById("lista");
    lista.innerHTML = '<div class="loading">Cargando...</div>';

    fetch("/api/letras?" + params)
        .then(r => r.json())
        .then(data => {
            document.getElementById("totalResultados").textContent =
                `${data.total.toLocaleString("es-ES")} letras encontradas`;
            document.getElementById("paginaInfo").textContent =
                `P\u00e1gina ${data.page} de ${data.total_pages}`;

            mostrarLetras(data.letras);
            renderPaginacion(data.page, data.total_pages);
        });
}

function mostrarLetras(letras) {
    const contenedor = document.getElementById("lista");
    contenedor.innerHTML = "";

    if (!letras.length) {
        contenedor.innerHTML = '<div class="empty-state">No se encontraron letras con esos filtros</div>';
        return;
    }

    letras.forEach(l => {
        const card = document.createElement("div");
        card.className = "letra-card";
        card.onclick = () => cargarDetalle(l.id);

        let metaHTML = "";
        if (l.anio) metaHTML += `<span class="tag anio">${escapeHtml(String(l.anio))}</span>`;
        if (l.modalidad) metaHTML += `<span class="tag modalidad">${escapeHtml(l.modalidad)}</span>`;
        if (l.tipo_pieza) metaHTML += `<span class="tag tipo">${escapeHtml(l.tipo_pieza)}</span>`;

        card.innerHTML = `
            <div class="titulo">${escapeHtml(l.titulo)}</div>
            <div class="meta">
                ${metaHTML}
                ${l.agrupacion ? `<span class="tag">${escapeHtml(l.agrupacion)}</span>` : ""}
            </div>
        `;
        contenedor.appendChild(card);
    });
}

// ==============================
// PAGINACION
// ==============================

function renderPaginacion(page, totalPages) {
    const cont = document.getElementById("paginacion");
    cont.innerHTML = "";

    if (totalPages <= 1) return;

    const btnPrev = document.createElement("button");
    btnPrev.textContent = "\u2190 Anterior";
    btnPrev.disabled = page <= 1;
    btnPrev.onclick = () => { currentPage = page - 1; cargarLetras(); };
    cont.appendChild(btnPrev);

    const rango = calcularRangoPaginas(page, totalPages);
    rango.forEach(p => {
        if (p === "...") {
            const dots = document.createElement("button");
            dots.textContent = "...";
            dots.disabled = true;
            cont.appendChild(dots);
        } else {
            const btn = document.createElement("button");
            btn.textContent = p;
            if (p === page) btn.className = "active";
            btn.onclick = () => { currentPage = p; cargarLetras(); };
            cont.appendChild(btn);
        }
    });

    const btnNext = document.createElement("button");
    btnNext.textContent = "Siguiente \u2192";
    btnNext.disabled = page >= totalPages;
    btnNext.onclick = () => { currentPage = page + 1; cargarLetras(); };
    cont.appendChild(btnNext);
}

function calcularRangoPaginas(current, total) {
    if (total <= 7) return Array.from({length: total}, (_, i) => i + 1);

    const pages = [1];
    if (current > 3) pages.push("...");

    const start = Math.max(2, current - 1);
    const end = Math.min(total - 1, current + 1);

    for (let i = start; i <= end; i++) pages.push(i);

    if (current < total - 2) pages.push("...");
    pages.push(total);

    return pages;
}

// ==============================
// BUSQUEDA FULL-TEXT
// ==============================

function buscarFullText() {
    const q = document.getElementById("buscadorFTS").value.trim();
    if (!q) return;

    const cont = document.getElementById("resultadosBusqueda");
    cont.innerHTML = '<div class="loading">Buscando...</div>';

    fetch("/api/buscar?q=" + encodeURIComponent(q))
        .then(r => r.json())
        .then(data => {
            cont.innerHTML = "";

            if (!data.resultados.length) {
                cont.innerHTML = '<div class="empty-state">No se encontraron resultados</div>';
                return;
            }

            const header = document.createElement("div");
            header.className = "info-bar";
            header.textContent = `${data.total} resultados para "${data.query}"`;
            cont.appendChild(header);

            data.resultados.forEach(r => {
                const item = document.createElement("div");
                item.className = "resultado-item";
                item.onclick = () => cargarDetalle(r.id);

                let metaHTML = "";
                if (r.anio) metaHTML += `<span class="tag anio">${escapeHtml(String(r.anio))}</span>`;
                if (r.modalidad) metaHTML += `<span class="tag modalidad">${escapeHtml(r.modalidad)}</span>`;

                item.innerHTML = `
                    <div class="titulo">${escapeHtml(r.titulo)}</div>
                    <div class="meta">${metaHTML}</div>
                    <div class="fragmento">${r.fragmento || ""}</div>
                `;
                cont.appendChild(item);
            });
        });
}

// ==============================
// DETALLE (MODAL)
// ==============================

function cargarDetalle(id) {
    fetch("/api/letra/" + id)
        .then(r => r.json())
        .then(data => {
            const detalle = document.getElementById("detalle");

            let metaHTML = "";
            if (data.anio) metaHTML += `<span class="tag anio">${escapeHtml(String(data.anio))}</span>`;
            if (data.modalidad) metaHTML += `<span class="tag modalidad">${escapeHtml(data.modalidad)}</span>`;
            if (data.tipo_pieza) metaHTML += `<span class="tag tipo">${escapeHtml(data.tipo_pieza)}</span>`;
            if (data.agrupacion) metaHTML += `<span class="tag">${escapeHtml(data.agrupacion)}</span>`;
            if (data.autor) metaHTML += `<span class="tag autor">Autor: ${escapeHtml(data.autor)}</span>`;

            // Score poético si está disponible
            let scoreHTML = "";
            if (data.score_poetico > 0) {
                const scoreColor = data.score_poetico >= 70 ? "var(--success)" : data.score_poetico >= 40 ? "var(--gold)" : "var(--text-muted)";
                scoreHTML = `<span class="tag" style="color:${scoreColor};border-color:${scoreColor}">Score poético: ${data.score_poetico}/100</span>`;
                if (data.nombre_metro) scoreHTML += `<span class="tag">${escapeHtml(data.nombre_metro)}</span>`;
                if (data.tipo_rima) scoreHTML += `<span class="tag">Rima ${escapeHtml(data.tipo_rima)}</span>`;
            }

            let fuenteHTML = "";
            if (data.url) {
                fuenteHTML = `<div class="detalle-fuente">Fuente: <a href="${escapeHtml(data.url)}" target="_blank" rel="noopener">${escapeHtml(data.fuente || "Original")}</a></div>`;
            }

            // Versos destacados si están guardados
            let versosHTML = "";
            if (data.versos_destacados) {
                try {
                    const versos = JSON.parse(data.versos_destacados);
                    if (versos && versos.length > 0) {
                        versosHTML = `
                            <div class="detalle-versos-destacados">
                                <span class="versos-label">Versos destacados:</span>
                                ${versos.map(v => `<blockquote class="verso-destacado">${escapeHtml(v)}</blockquote>`).join("")}
                            </div>
                        `;
                    }
                } catch(e) {}
            }

            // Links a perfiles de autor y agrupación
            let perfilLinks = "";
            if (data.autor) {
                perfilLinks += `<a href="/autor/${encodeURIComponent(data.autor)}" class="perfil-link" target="_blank">👤 ${escapeHtml(data.autor)}</a>`;
            }
            if (data.agrupacion) {
                perfilLinks += `<a href="/agrupacion/${encodeURIComponent(data.agrupacion)}" class="perfil-link" target="_blank">🎭 ${escapeHtml(data.agrupacion)}</a>`;
            }

            detalle.innerHTML = `
                <h2>${escapeHtml(data.titulo)}</h2>
                <div class="detalle-meta">${metaHTML}</div>
                ${scoreHTML ? `<div class="detalle-poetica-tags">${scoreHTML}</div>` : ""}
                ${perfilLinks ? `<div class="detalle-perfil-links">${perfilLinks}</div>` : ""}
                ${versosHTML}
                <div class="detalle-texto">${escapeHtml(data.contenido || "Sin contenido disponible")}</div>
                ${fuenteHTML}
                <div class="detalle-acciones">
                    <button class="btn-poetico" onclick="abrirAnalisisPoeta(${data.id})">
                        &#9997; Análisis poético
                    </button>
                </div>
            `;

            document.getElementById("modalOverlay").classList.add("open");
        });
}

function cerrarModal() {
    document.getElementById("modalOverlay").classList.remove("open");
}

// ==============================
// BUSQUEDA TEMATICA
// ==============================

function buscarTematica(tema) {
    document.getElementById("buscadorFTS").value = tema;
    const cont = document.getElementById("resultadosBusqueda");
    cont.innerHTML = '<div class="loading">Buscando por tematica...</div>';

    fetch("/api/buscar_tematica?q=" + encodeURIComponent(tema))
        .then(r => r.json())
        .then(data => {
            cont.innerHTML = "";

            if (!data.resultados.length) {
                cont.innerHTML = '<div class="empty-state">No se encontraron resultados para esa tematica</div>';
                return;
            }

            const header = document.createElement("div");
            header.className = "info-bar";
            header.textContent = `${data.total} resultados para "${data.query_original}"`;
            cont.appendChild(header);

            data.resultados.forEach(r => {
                const item = document.createElement("div");
                item.className = "resultado-item";
                item.onclick = () => cargarDetalle(r.id);

                let metaHTML = "";
                if (r.anio) metaHTML += `<span class="tag anio">${escapeHtml(String(r.anio))}</span>`;
                if (r.modalidad) metaHTML += `<span class="tag modalidad">${escapeHtml(r.modalidad)}</span>`;

                item.innerHTML = `
                    <div class="titulo">${escapeHtml(r.titulo)}</div>
                    <div class="meta">${metaHTML}</div>
                    <div class="fragmento">${r.fragmento || ""}</div>
                `;
                cont.appendChild(item);
            });
        });
}

// ==============================
// COMPARADOR DE ESTILOS
// ==============================

function compararEstilos() {
    const a1 = document.getElementById("comp1").value.trim();
    const a2 = document.getElementById("comp2").value.trim();
    const cont = document.getElementById("resultadoComparar");

    if (!a1 || !a2) {
        cont.innerHTML = '<div class="empty-state">Introduce dos agrupaciones para comparar</div>';
        return;
    }

    cont.innerHTML = '<div class="loading">Comparando...</div>';

    fetch(`/api/comparar?a1=${encodeURIComponent(a1)}&a2=${encodeURIComponent(a2)}`)
        .then(r => r.json())
        .then(data => {
            if (data.error) {
                cont.innerHTML = `<div class="empty-state">${escapeHtml(data.error)}</div>`;
                return;
            }

            const [s1, s2] = data.comparacion;
            cont.innerHTML = `
                <div class="comparar-grid">
                    ${renderCompCard(s1)}
                    ${renderCompCard(s2)}
                </div>
            `;
        })
        .catch(() => {
            cont.innerHTML = '<div class="empty-state">Error al comparar</div>';
        });
}

function renderCompCard(s) {
    let tiposHTML = (s.tipos_pieza || []).map(t =>
        `<span class="tag tipo">${escapeHtml(t.tipo)} (${t.cantidad})</span>`
    ).join(" ");

    return `
        <div class="comp-card">
            <h4>${escapeHtml(s.nombre)}</h4>
            <div class="comp-row"><span class="label">Total letras</span><span class="value">${s.total_letras}</span></div>
            <div class="comp-row"><span class="label">A&ntilde;os activos</span><span class="value">${s.anios_activos}</span></div>
            <div class="comp-row"><span class="label">Periodo</span><span class="value">${s.primer_anio || '?'} - ${s.ultimo_anio || '?'}</span></div>
            <div class="comp-row"><span class="label">Modalidad</span><span class="value">${escapeHtml(s.modalidades || 'N/A')}</span></div>
            <div class="comp-row"><span class="label">Autores</span><span class="value">${escapeHtml(s.autores || 'N/A')}</span></div>
            <div class="comp-row"><span class="label">Longitud media</span><span class="value">${s.longitud_media} chars</span></div>
            <div class="comp-row"><span class="label">Calidad media</span><span class="value">${s.calidad_media}/100</span></div>
            <div class="comp-row"><span class="label">Tipos de pieza</span><span class="value">${tiposHTML || 'N/A'}</span></div>
        </div>
    `;
}

// ==============================
// CHARTS (ESTADISTICAS)
// ==============================

function cargarCharts() {
    // Cargar stats basicas
    const loadBasic = window._stats
        ? Promise.resolve(window._stats)
        : fetch("/api/estadisticas").then(r => r.json()).then(s => { window._stats = s; return s; });

    // Cargar stats avanzadas
    const loadAdvanced = fetch("/api/estadisticas_avanzadas").then(r => r.json());

    Promise.all([loadBasic, loadAdvanced]).then(([stats, avanzadas]) => {
        renderBarChart("chartAnios", stats.por_anio.map(d => ({label: d.anio, value: d.cantidad})));
        renderBarChart("chartModalidad", stats.por_modalidad.map(d => ({label: d.modalidad, value: d.cantidad})));
        renderBarChart("chartTipo", stats.por_tipo_pieza.map(d => ({label: d.tipo, value: d.cantidad})));
        renderBarChart("chartAgrupaciones", stats.top_agrupaciones.slice(0, 15).map(d => ({label: d.agrupacion, value: d.cantidad})));
        renderBarChart("chartAutores", avanzadas.top_autores.map(d => ({label: d.autor, value: d.letras})));
        renderBarChart("chartCalidad", avanzadas.distribucion_calidad.map(d => ({label: d.rango, value: d.cantidad})));
    });
}

function renderBarChart(containerId, data) {
    const container = document.getElementById(containerId);
    if (!container || !data || !data.length) return;

    container.innerHTML = "";
    const maxVal = Math.max(...data.map(d => d.value));

    data.forEach(d => {
        const pct = (d.value / maxVal * 100).toFixed(1);
        const row = document.createElement("div");
        row.className = "bar-row";
        row.innerHTML = `
            <span class="bar-label">${escapeHtml(String(d.label || "N/A"))}</span>
            <div class="bar-track"><div class="bar-fill" style="width:${pct}%"></div></div>
            <span class="bar-value">${d.value}</span>
        `;
        container.appendChild(row);
    });
}

// ==============================
// UTILS
// ==============================

function escapeHtml(text) {
    if (!text) return "";
    const div = document.createElement("div");
    div.textContent = text;
    return div.innerHTML;
}


// ==============================
// LETRA ALEATORIA
// ==============================

function letraAleatoria() {
    const modalidad = document.getElementById("aleatorioModalidad").value;
    const cont = document.getElementById("aleatorioResultado");
    cont.innerHTML = '<div class="loading">Buscando...</div>';

    const params = modalidad ? `?modalidad=${encodeURIComponent(modalidad)}` : "";

    fetch("/api/aleatorio" + params)
        .then(r => r.json())
        .then(data => {
            if (data.error) {
                cont.innerHTML = '<div class="empty-state">No hay letras disponibles</div>';
                return;
            }

            let metaHTML = "";
            if (data.anio) metaHTML += `<span class="tag anio">${escapeHtml(String(data.anio))}</span>`;
            if (data.modalidad) metaHTML += `<span class="tag modalidad">${escapeHtml(data.modalidad)}</span>`;
            if (data.tipo_pieza) metaHTML += `<span class="tag tipo">${escapeHtml(data.tipo_pieza)}</span>`;
            if (data.agrupacion) metaHTML += `<span class="tag">${escapeHtml(data.agrupacion)}</span>`;

            // Truncar texto para la preview
            const textoPreview = data.contenido && data.contenido.length > 500
                ? data.contenido.substring(0, 500) + "..."
                : data.contenido || "";

            cont.innerHTML = `
                <div class="ale-titulo">${escapeHtml(data.titulo)}</div>
                <div class="ale-meta">${metaHTML}</div>
                <div class="ale-texto">${escapeHtml(textoPreview)}</div>
                <div class="ale-footer">
                    ${data.autor ? `<span class="text-muted">Autor: ${escapeHtml(data.autor)}</span>` : '<span></span>'}
                    <button class="btn-ver" onclick="cargarDetalle(${data.id})">Ver completa</button>
                </div>
            `;
        })
        .catch(() => {
            cont.innerHTML = '<div class="empty-state">Error al cargar</div>';
        });
}


// ==============================
// NUBE DE PALABRAS
// ==============================

let _nubeLoaded = false;

function cargarNubePalabras() {
    const modalidad = document.getElementById("nubeModalidad").value;
    const cont = document.getElementById("nubePalabras");

    if (_nubeLoaded && !modalidad && cont.children.length > 0) return;

    cont.innerHTML = '<div class="loading">Analizando vocabulario...</div>';

    const params = modalidad ? `?modalidad=${encodeURIComponent(modalidad)}` : "";

    fetch("/api/palabras_frecuentes" + params)
        .then(r => r.json())
        .then(data => {
            cont.innerHTML = "";
            if (!data.palabras.length) {
                cont.innerHTML = '<div class="empty-state">No hay datos</div>';
                return;
            }

            const maxFreq = data.palabras[0].frecuencia;
            const minFreq = data.palabras[data.palabras.length - 1].frecuencia;

            // Colores por rango
            const colores = [
                "var(--accent)",
                "var(--accent-light)",
                "var(--gold)",
                "var(--success)",
                "var(--text-secondary)",
                "var(--text-muted)"
            ];

            // Mezclar orden para que sea mas visual
            const mezcladas = [...data.palabras].sort(() => Math.random() - 0.5);

            mezcladas.forEach(item => {
                const ratio = (item.frecuencia - minFreq) / (maxFreq - minFreq || 1);
                const fontSize = 0.7 + ratio * 1.8; // 0.7rem a 2.5rem
                const colorIndex = Math.floor((1 - ratio) * (colores.length - 1));

                const span = document.createElement("span");
                span.className = "nube-word";
                span.textContent = item.palabra;
                span.style.fontSize = fontSize + "rem";
                span.style.color = colores[colorIndex];
                span.style.fontWeight = ratio > 0.5 ? "700" : "400";
                span.title = `${item.palabra}: ${item.frecuencia} veces`;
                span.onclick = () => {
                    switchTab("buscar");
                    document.getElementById("buscadorFTS").value = item.palabra;
                    buscarFullText();
                };
                cont.appendChild(span);
            });

            _nubeLoaded = !modalidad;
        })
        .catch(() => {
            cont.innerHTML = '<div class="empty-state">Error al cargar</div>';
        });
}


// ==============================
// TIMELINE / CRONOLOGIA
// ==============================

let _timelineLoaded = false;

function cargarTimeline() {
    if (_timelineLoaded) return;

    const cont = document.getElementById("timelineContainer");
    cont.innerHTML = '<div class="loading">Cargando cronologia...</div>';

    fetch("/api/timeline")
        .then(r => r.json())
        .then(data => {
            cont.innerHTML = "";

            if (!data.timeline.length) {
                cont.innerHTML = '<div class="empty-state">No hay datos cronologicos</div>';
                return;
            }

            const maxLetras = Math.max(...data.timeline.map(d => d.total_letras));

            data.timeline.forEach(item => {
                const div = document.createElement("div");
                const isHighlight = item.total_letras > maxLetras * 0.7;
                div.className = "timeline-item" + (isHighlight ? " highlight" : "");

                let agrupHTML = item.top_agrupaciones.map(a =>
                    `<span class="tag">${escapeHtml(a)}</span>`
                ).join("");

                div.innerHTML = `
                    <div class="timeline-card" onclick="explorarAnio('${item.anio}')">
                        <div>
                            <span class="timeline-anio">${escapeHtml(String(item.anio))}</span>
                            <span class="timeline-stats">
                                <span>${item.total_letras} letras</span>
                                <span>${item.agrupaciones} agrupaciones</span>
                                <span>${item.modalidades || ''}</span>
                            </span>
                        </div>
                        <div class="timeline-agrupaciones">${agrupHTML}</div>
                    </div>
                `;
                cont.appendChild(div);
            });

            _timelineLoaded = true;
        })
        .catch(() => {
            cont.innerHTML = '<div class="empty-state">Error al cargar cronologia</div>';
        });
}

function explorarAnio(anio) {
    switchTab("explorar");
    document.getElementById("filtroAnio").value = anio;
    currentFilters = { anio: anio };
    currentPage = 1;
    cargarLetras();
}

// También rellenar filtro de año en poética
document.addEventListener("DOMContentLoaded", () => {
    fetch("/api/filtros")
        .then(r => r.json())
        .then(data => {
            const selAnioP = document.getElementById("poeticaAnio");
            if (selAnioP) {
                data.anios.forEach(a => {
                    const opt = document.createElement("option");
                    opt.value = a;
                    opt.textContent = a;
                    selAnioP.appendChild(opt);
                });
            }
        });
});

// ==============================
// TAB POÉTICA - CORPUS
// ==============================

let _poeticaCargada = false;

function iniciarTabPoetica() {
    // Cargar estadísticas del corpus analizado previamente (si las hay)
    if (_poeticaCargada) return;
    cargarEstadisticasPoéticas();
}

function cargarEstadisticasPoéticas() {
    const dash = document.getElementById("poeticaDashboard");
    const loader = document.getElementById("poeticaLoader");
    const aviso = document.getElementById("poeticaAviso");

    fetch("/api/estadisticas_poeticas")
        .then(r => r.json())
        .then(data => {
            if (data.total_analizadas === 0) {
                if (aviso) aviso.textContent = "No hay letras analizadas aún. Haz clic en 'Analizar corpus' o ve al Admin para analizar el archivo completo.";
                return;
            }
            renderDashboardPoético(data);
        })
        .catch(() => {
            if (aviso) aviso.textContent = "Error al cargar estadísticas poéticas.";
        });
}

function cargarPoética() {
    const modalidad = document.getElementById("poeticaModalidad").value;
    const anio = document.getElementById("poeticaAnio").value;
    const tipo = document.getElementById("poeticaTipo").value;
    const loader = document.getElementById("poeticaLoader");
    const dash = document.getElementById("poeticaDashboard");
    const aviso = document.getElementById("poeticaAviso");

    if (loader) loader.style.display = "block";
    if (dash) dash.style.display = "none";
    if (aviso) aviso.textContent = "";

    const body = {};
    if (modalidad) body.modalidad = modalidad;
    if (anio) body.anio = anio;
    if (tipo) body.tipo_pieza = tipo;
    body.limit = 300;

    fetch("/api/analizar_corpus", {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify(body)
    })
        .then(r => r.json())
        .then(data => {
            if (loader) loader.style.display = "none";
            if (data.error) {
                if (aviso) aviso.textContent = data.error;
                return;
            }
            renderDashboardPoéticoCorpus(data);
        })
        .catch(() => {
            if (loader) loader.style.display = "none";
            if (aviso) aviso.textContent = "Error al analizar corpus.";
        });
}

function renderDashboardPoético(data) {
    // Transforma stats guardadas al mismo formato que renderDashboardPoéticoCorpus
    const corpus = {
        total_analizadas: data.total_analizadas,
        score_medio: data.score_medio,
        densidad_lexica_media: data.densidad_lexica_media,
        metros_dominantes: data.metros_dominantes,
        tipos_rima: data.tipos_rima,
        esquemas_frecuentes: data.esquemas_frecuentes,
        figuras_frecuentes: data.figuras_frecuentes,
        lexico_gaditano_top: data.lexico_gaditano_top || [],
        palabras_clave_corpus: data.palabras_clave_corpus || [],
        muestra: data.total_analizadas,
        desde_stats: true,
        top_letras: data.top_letras_poeticas || [],
    };
    renderDashboardPoéticoCorpus(corpus);
}

function renderDashboardPoéticoCorpus(data) {
    const dash = document.getElementById("poeticaDashboard");
    if (!dash) return;
    dash.style.display = "block";
    _poeticaCargada = true;

    // KPIs
    const kpis = document.getElementById("poeticaKpis");
    if (kpis) {
        kpis.innerHTML = `
            <div class="kpi-card">
                <div class="kpi-num">${(data.total_analizadas || data.muestra || 0).toLocaleString("es-ES")}</div>
                <div class="kpi-label">Letras analizadas</div>
            </div>
            <div class="kpi-card">
                <div class="kpi-num">${data.score_medio || 0}</div>
                <div class="kpi-label">Score poético medio</div>
            </div>
            <div class="kpi-card">
                <div class="kpi-num">${data.densidad_lexica_media || 0}%</div>
                <div class="kpi-label">Densidad léxica media</div>
            </div>
            <div class="kpi-card">
                <div class="kpi-num">${(data.metros_dominantes || [])[0]?.metro || "—"}</div>
                <div class="kpi-label">Metro más usado</div>
            </div>
            <div class="kpi-card">
                <div class="kpi-num">${(data.tipos_rima || [])[0]?.tipo || "—"}</div>
                <div class="kpi-label">Tipo de rima dominante</div>
            </div>
            <div class="kpi-card">
                <div class="kpi-num">${(data.figuras_frecuentes || [])[0]?.figura?.split(" ")[0] || "—"}</div>
                <div class="kpi-label">Figura retórica más frecuente</div>
            </div>
        `;
    }

    // Charts
    renderBarChart("chartMetros",
        (data.metros_dominantes || []).map(d => ({label: d.metro, value: d.count}))
    );
    renderBarChart("chartRima",
        (data.tipos_rima || []).map(d => ({label: d.tipo, value: d.count}))
    );
    renderBarChart("chartEsquemas",
        (data.esquemas_frecuentes || []).map(d => ({label: d.esquema, value: d.count}))
    );
    renderBarChart("chartFiguras",
        (data.figuras_frecuentes || []).map(d => ({label: d.figura, value: d.count}))
    );

    // Léxico gaditano como nube
    renderMiniNube("chartLexico", data.lexico_gaditano_top || [], "apariciones");
    renderMiniNube("chartPalabrasClave", data.palabras_clave_corpus || [], "frecuencia");

    // Top letras poéticas (si hay)
    if (data.top_letras && data.top_letras.length > 0) {
        const existing = document.getElementById("poeticaTopLetras");
        if (!existing) {
            const section = document.createElement("div");
            section.id = "poeticaTopLetras";
            section.className = "poetica-top-letras";
            section.innerHTML = `
                <h4>Letras con mayor score poético</h4>
                <div class="letras-grid">
                    ${data.top_letras.map(l => `
                        <div class="letra-card poetica-card" onclick="cargarDetalle(${l.id})">
                            <div class="titulo">${escapeHtml(l.titulo)}</div>
                            <div class="meta">
                                ${l.anio ? `<span class="tag anio">${escapeHtml(String(l.anio))}</span>` : ""}
                                ${l.modalidad ? `<span class="tag modalidad">${escapeHtml(l.modalidad)}</span>` : ""}
                                ${l.nombre_metro ? `<span class="tag">${escapeHtml(l.nombre_metro)}</span>` : ""}
                                ${l.tipo_rima ? `<span class="tag">Rima ${escapeHtml(l.tipo_rima)}</span>` : ""}
                                <span class="tag score-tag">Score: ${l.score_poetico}/100</span>
                            </div>
                        </div>
                    `).join("")}
                </div>
            `;
            dash.appendChild(section);
        }
    }
}

function renderMiniNube(containerId, items, freqKey) {
    const cont = document.getElementById(containerId);
    if (!cont || !items.length) return;
    cont.innerHTML = "";

    const maxFreq = Math.max(...items.map(d => d[freqKey]));
    const minFreq = Math.min(...items.map(d => d[freqKey]));
    const colores = ["var(--accent)", "var(--gold)", "var(--accent-light)", "var(--success)", "var(--text-secondary)"];
    const mezcladas = [...items].sort(() => Math.random() - 0.5);

    mezcladas.forEach(item => {
        const ratio = (item[freqKey] - minFreq) / (maxFreq - minFreq || 1);
        const fontSize = 0.65 + ratio * 1.3;
        const colorIndex = Math.floor((1 - ratio) * (colores.length - 1));
        const palabra = item.palabra || item.metro || item.tipo || item.figura || item.esquema || "?";

        const span = document.createElement("span");
        span.className = "nube-word";
        span.textContent = palabra;
        span.style.fontSize = fontSize + "rem";
        span.style.color = colores[colorIndex];
        span.title = `${palabra}: ${item[freqKey]}`;
        span.onclick = () => {
            switchTab("buscar");
            document.getElementById("buscadorFTS").value = palabra;
            buscarFullText();
        };
        cont.appendChild(span);
    });
}

// ==============================
// ANÁLISIS POÉTICO INDIVIDUAL
// ==============================

function abrirAnalisisPoeta(id) {
    const overlay = document.getElementById("modalPoetaOverlay");
    const detalle = document.getElementById("detallePoeta");
    if (!overlay || !detalle) return;

    detalle.innerHTML = '<div class="loading">Analizando métricamente la letra...</div>';
    overlay.classList.add("open");

    fetch(`/api/analisis_poetico/${id}`)
        .then(r => r.json())
        .then(data => {
            if (data.error) {
                detalle.innerHTML = `<div class="empty-state">${escapeHtml(data.error)}</div>`;
                return;
            }
            renderAnalisisPoeta(detalle, data);
        })
        .catch(() => {
            detalle.innerHTML = '<div class="empty-state">Error al analizar la letra</div>';
        });
}

function cerrarModalPoeta() {
    document.getElementById("modalPoetaOverlay").classList.remove("open");
}

function renderAnalisisPoeta(cont, d) {
    const metrica = d.metrica || {};
    const rima = d.rima || {};
    const vocab = d.vocabulario || {};
    const figuras = d.figuras_retoricas || [];
    const versos = d.versos_destacados || [];

    // Score color
    const score = d.score_poetico || 0;
    const scoreColor = score >= 70 ? "var(--success)" : score >= 40 ? "var(--gold)" : "var(--text-muted)";

    // Figuras HTML
    let figurasHTML = "";
    if (figuras.length > 0) {
        figurasHTML = figuras.map(f => {
            let ejemplosHTML = "";
            if (f.ejemplos && f.ejemplos.length) {
                ejemplosHTML = f.ejemplos.map(e => {
                    if (e.versos) return `<blockquote class="figura-ejemplo">${escapeHtml(e.versos.join(" / "))}</blockquote>`;
                    return "";
                }).join("");
            }
            const countHTML = f.count !== undefined ? ` <span class="figura-count">(${f.count})</span>` : "";
            const palabrasHTML = f.palabras ? ` — <em>${f.palabras.map(p => escapeHtml(p.palabra)).join(", ")}</em>` : "";
            return `<div class="figura-item"><strong>${escapeHtml(f.figura)}</strong>${countHTML}${palabrasHTML}${ejemplosHTML}</div>`;
        }).join("");
    } else {
        figurasHTML = '<span class="text-muted">No detectadas</span>';
    }

    // Versos destacados
    let versosHTML = versos.length
        ? versos.map(v => `<blockquote class="verso-destacado">${escapeHtml(v)}</blockquote>`).join("")
        : '<span class="text-muted">No disponibles</span>';

    // Léxico gaditano
    const lexicoList = (vocab.lexico_gaditano || []).slice(0, 20).join(", ");

    // Distribución de metros
    const distrib = metrica.distribucion || {};
    const distribHTML = Object.entries(distrib).length
        ? Object.entries(distrib).map(([metro, cnt]) =>
            `<span class="tag">${escapeHtml(metro)}: ${cnt}</span>`
          ).join(" ")
        : '<span class="text-muted">No analizado</span>';

    // Estrofas con esquema
    const estrofas = rima.estrofas || [];
    const estrofasHTML = estrofas.slice(0, 6).map(e => `
        <div class="estrofa-row">
            <span class="estrofa-esquema">${escapeHtml(e.esquema || "—")}</span>
            <span class="estrofa-info">${e.n_versos} versos · rima ${escapeHtml(e.tipo_rima || "?")}${e.forma_estrofica ? " · " + escapeHtml(e.forma_estrofica) : ""}</span>
        </div>
    `).join("") || '<span class="text-muted">No analizado</span>';

    // Palabras clave
    const pkHTML = (vocab.palabras_clave || []).slice(0, 12).map(p =>
        `<span class="tag">${escapeHtml(p.palabra)}</span>`
    ).join(" ");

    cont.innerHTML = `
        <div class="analisis-poetico">
            <div class="analisis-header">
                <h2>Análisis Poético</h2>
                <div class="score-circle" style="border-color:${scoreColor};color:${scoreColor}">
                    <span class="score-num">${score}</span>
                    <span class="score-label">/ 100</span>
                </div>
            </div>

            <div class="analisis-grid">
                <!-- MÉTRICA -->
                <div class="analisis-card">
                    <h4>Métrica</h4>
                    <div class="analisis-row"><span>Metro dominante</span><strong>${escapeHtml(metrica.nombre_metro || "libre")}</strong></div>
                    <div class="analisis-row"><span>Sílabas</span><strong>${metrica.metro_dominante || "—"}</strong></div>
                    <div class="analisis-row"><span>Coherencia métrica</span><strong>${metrica.coherencia_pct || 0}%</strong></div>
                    <div class="analisis-row"><span>Distribución</span><div>${distribHTML}</div></div>
                    <div class="analisis-row"><span>Estrofas</span><strong>${d.n_estrofas}</strong></div>
                    <div class="analisis-row"><span>Versos totales</span><strong>${d.n_versos}</strong></div>
                    <div class="analisis-row"><span>Longitud media verso</span><strong>${d.longitud_media_verso} chars</strong></div>
                </div>

                <!-- RIMA -->
                <div class="analisis-card">
                    <h4>Rima</h4>
                    <div class="analisis-row"><span>Tipo de rima</span><strong>${escapeHtml(rima.tipo_rima || "libre")}</strong></div>
                    <div class="analisis-row"><span>Esquema predominante</span><strong class="esquema-badge">${escapeHtml(rima.esquema_predominante || "—")}</strong></div>
                    <h5 style="margin-top:1rem;margin-bottom:.5rem">Por estrofa:</h5>
                    <div class="estrofas-lista">${estrofasHTML}</div>
                </div>

                <!-- VOCABULARIO -->
                <div class="analisis-card">
                    <h4>Vocabulario</h4>
                    <div class="analisis-row"><span>Total palabras</span><strong>${vocab.total_palabras || 0}</strong></div>
                    <div class="analisis-row"><span>Vocabulario único</span><strong>${vocab.vocabulario_unico || 0}</strong></div>
                    <div class="analisis-row"><span>Densidad léxica</span><strong>${vocab.densidad_lexica || 0}%</strong>
                        <em class="text-muted"> (${escapeHtml(vocab.riqueza || "—")})</em>
                    </div>
                    <div class="analisis-row"><span>Léxico gaditano</span>
                        <span class="text-muted">${lexicoList || "ninguno detectado"}</span>
                    </div>
                    <div class="analisis-row palabras-clave-row"><span>Palabras clave</span>
                        <div>${pkHTML || '<span class="text-muted">—</span>'}</div>
                    </div>
                </div>

                <!-- FIGURAS RETÓRICAS -->
                <div class="analisis-card">
                    <h4>Figuras Retóricas</h4>
                    ${figurasHTML}
                </div>
            </div>

            <!-- VERSOS DESTACADOS -->
            <div class="analisis-card analisis-full">
                <h4>Versos Destacados</h4>
                ${versosHTML}
            </div>
        </div>
    `;
}

document.addEventListener("keydown", e => {
    if (e.key === "Escape") {
        cerrarModalPoeta();
    }
});

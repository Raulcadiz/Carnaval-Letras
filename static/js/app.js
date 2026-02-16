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

            let fuenteHTML = "";
            if (data.url) {
                fuenteHTML = `<div class="detalle-fuente">Fuente: <a href="${escapeHtml(data.url)}" target="_blank" rel="noopener">${escapeHtml(data.fuente || "Original")}</a></div>`;
            }

            detalle.innerHTML = `
                <h2>${escapeHtml(data.titulo)}</h2>
                <div class="detalle-meta">${metaHTML}</div>
                <div class="detalle-texto">${escapeHtml(data.contenido || "Sin contenido disponible")}</div>
                ${fuenteHTML}
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

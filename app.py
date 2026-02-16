from flask import Flask, render_template, jsonify, request
import os
import json
import shutil
from database import (
    get_db, init_db, migrate_db, buscar_duplicados, eliminar_duplicados,
    obtener_estadisticas, busqueda_fulltext, reconstruir_fts, generar_hash, DB_NAME
)
from metadata_extractor import extraer_metadata, normalizar_letra, evaluar_calidad
from scraper import ejecutar_scraper

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
app = Flask(__name__)

# Inicializar y migrar DB
init_db()
migrate_db()


# =========================
# RUTAS WEB
# =========================

@app.route("/")
def index():
    return render_template("index.html")


@app.route("/admin")
def admin():
    return render_template("admin.html")


# =========================
# API: LETRAS (PAGINADA)
# =========================

@app.route("/api/letras")
def obtener_letras():
    anio = request.args.get("anio")
    modalidad = request.args.get("modalidad")
    tipo_pieza = request.args.get("tipo_pieza")
    agrupacion = request.args.get("agrupacion")
    page = int(request.args.get("page", 1))
    per_page = int(request.args.get("per_page", 50))
    orden = request.args.get("orden", "titulo")

    conn = get_db()
    cursor = conn.cursor()

    query = "SELECT id, titulo, anio, modalidad, tipo_pieza, agrupacion, calidad FROM letras WHERE 1=1"
    count_query = "SELECT COUNT(*) as total FROM letras WHERE 1=1"
    params = []

    if anio:
        query += " AND anio=?"
        count_query += " AND anio=?"
        params.append(anio)
    if modalidad:
        query += " AND modalidad=?"
        count_query += " AND modalidad=?"
        params.append(modalidad)
    if tipo_pieza:
        query += " AND tipo_pieza=?"
        count_query += " AND tipo_pieza=?"
        params.append(tipo_pieza)
    if agrupacion:
        query += " AND agrupacion LIKE ?"
        count_query += " AND agrupacion LIKE ?"
        params.append(f"%{agrupacion}%")

    # Total
    cursor.execute(count_query, params)
    total = cursor.fetchone()["total"]

    # Orden
    ordenes_validos = {"titulo": "titulo", "anio": "anio", "modalidad": "modalidad", "calidad": "calidad DESC"}
    orden_sql = ordenes_validos.get(orden, "titulo")
    query += f" ORDER BY {orden_sql}"

    # Paginacion
    offset = (page - 1) * per_page
    query += " LIMIT ? OFFSET ?"
    params.extend([per_page, offset])

    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()

    letras = [dict(r) for r in rows]

    return jsonify({
        "letras": letras,
        "total": total,
        "page": page,
        "per_page": per_page,
        "total_pages": max(1, (total + per_page - 1) // per_page)
    })


@app.route("/api/letra/<int:letra_id>")
def obtener_letra(letra_id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM letras WHERE id=?", (letra_id,))
    row = cursor.fetchone()
    conn.close()

    if not row:
        return jsonify({"error": "No encontrada"}), 404

    return jsonify(dict(row))


# =========================
# API: BUSQUEDA FULL-TEXT
# =========================

@app.route("/api/buscar")
def buscar():
    q = request.args.get("q", "").strip()
    limit = int(request.args.get("limit", 50))
    offset = int(request.args.get("offset", 0))

    if not q or len(q) < 2:
        return jsonify({"resultados": [], "total": 0})

    resultados = busqueda_fulltext(q, limit, offset)
    return jsonify({
        "resultados": resultados,
        "total": len(resultados),
        "query": q
    })


# =========================
# API: ESTADISTICAS
# =========================

@app.route("/api/estadisticas")
def estadisticas():
    stats = obtener_estadisticas()
    return jsonify(stats)


# =========================
# API: FILTROS DISPONIBLES
# =========================

@app.route("/api/filtros")
def obtener_filtros():
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("SELECT DISTINCT anio FROM letras WHERE anio IS NOT NULL ORDER BY anio DESC")
    anios = [r["anio"] for r in cursor.fetchall()]

    cursor.execute("SELECT DISTINCT modalidad FROM letras WHERE modalidad IS NOT NULL ORDER BY modalidad")
    modalidades = [r["modalidad"] for r in cursor.fetchall()]

    cursor.execute("SELECT DISTINCT tipo_pieza FROM letras WHERE tipo_pieza IS NOT NULL ORDER BY tipo_pieza")
    tipos = [r["tipo_pieza"] for r in cursor.fetchall()]

    conn.close()

    return jsonify({
        "anios": anios,
        "modalidades": modalidades,
        "tipos_pieza": tipos
    })


# =========================
# API: SCRAPER
# =========================

@app.route("/api/scraper", methods=["POST"])
def lanzar_scraper():
    data = request.json or {}
    max_paginas = data.get("max_paginas")
    resultado = ejecutar_scraper(max_paginas=max_paginas)
    return jsonify(resultado)


# =========================
# API: ENRIQUECER METADATA
# =========================

@app.route("/api/enriquecer", methods=["POST"])
def enriquecer_metadata():
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("SELECT id, titulo, etiquetas, contenido, url FROM letras")
    rows = cursor.fetchall()

    actualizados = 0
    limpiados = 0
    autores_encontrados = 0

    for row in rows:
        # Extraccion inteligente: titulo + etiquetas + URL
        metadata = extraer_metadata(row["titulo"], row["etiquetas"], row["url"])
        calidad = evaluar_calidad(row["contenido"])
        contenido_hash = generar_hash(row["contenido"])

        # Limpiar texto si es necesario
        contenido_limpio = normalizar_letra(row["contenido"]) if row["contenido"] else None
        if contenido_limpio and contenido_limpio != row["contenido"]:
            limpiados += 1

        if metadata.get("autor"):
            autores_encontrados += 1

        cursor.execute("""
            UPDATE letras
            SET anio=?, modalidad=?, tipo_pieza=?, agrupacion=?,
                autor=?, calidad=?, contenido_hash=?, contenido=?
            WHERE id=?
        """, (
            metadata["anio"],
            metadata["modalidad"],
            metadata["tipo_pieza"],
            metadata["agrupacion"],
            metadata.get("autor"),
            calidad,
            contenido_hash,
            contenido_limpio or row["contenido"],
            row["id"]
        ))
        actualizados += 1

    conn.commit()
    conn.close()

    reconstruir_fts()

    return jsonify({
        "actualizados": actualizados,
        "limpiados": limpiados,
        "autores_encontrados": autores_encontrados
    })


# =========================
# API: DEDUPLICACION
# =========================

@app.route("/api/duplicados")
def ver_duplicados():
    resultado = buscar_duplicados()
    return jsonify(resultado)


@app.route("/api/deduplicar", methods=["POST"])
def deduplicar():
    eliminados = eliminar_duplicados()
    reconstruir_fts()
    return jsonify({"eliminados": eliminados})


# =========================
# API: DATASET IA
# =========================

@app.route("/api/generar_dataset", methods=["POST"])
def generar_dataset():
    data = request.json or {}
    modalidad = data.get("modalidad")
    anio = data.get("anio")
    tipo_pieza = data.get("tipo_pieza")
    formato = data.get("formato", "simple")

    conn = get_db()
    cursor = conn.cursor()

    query = "SELECT titulo, contenido, anio, modalidad, tipo_pieza, agrupacion FROM letras WHERE contenido IS NOT NULL"
    params = []

    if modalidad:
        query += " AND modalidad=?"
        params.append(modalidad)
    if anio:
        query += " AND anio=?"
        params.append(anio)
    if tipo_pieza:
        query += " AND tipo_pieza=?"
        params.append(tipo_pieza)

    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()

    os.makedirs(os.path.join(BASE_DIR, "data"), exist_ok=True)

    if formato == "instruction":
        dataset = []
        for r in rows:
            if not r["contenido"] or len(r["contenido"].strip()) < 50:
                continue

            parts = ["Escribe"]
            if r["tipo_pieza"]:
                parts.append(f"un {r['tipo_pieza'].lower()}")
            else:
                parts.append("una letra")
            if r["modalidad"]:
                parts.append(f"de {r['modalidad'].lower()}")
            parts.append("del Carnaval de Cadiz")
            if r["anio"]:
                parts.append(f"del anio {r['anio']}")

            dataset.append({
                "instruction": " ".join(parts),
                "input": "",
                "output": r["contenido"].strip(),
                "metadata": {
                    "titulo": r["titulo"],
                    "anio": r["anio"],
                    "modalidad": r["modalidad"],
                    "tipo_pieza": r["tipo_pieza"],
                    "agrupacion": r["agrupacion"]
                }
            })

        path = os.path.join(BASE_DIR, "data", "dataset_instruction.json")
    else:
        dataset = []
        for r in rows:
            if not r["contenido"] or len(r["contenido"].strip()) < 50:
                continue
            dataset.append({
                "texto": r["contenido"].strip(),
                "titulo": r["titulo"],
                "anio": r["anio"],
                "modalidad": r["modalidad"],
                "tipo_pieza": r["tipo_pieza"],
                "agrupacion": r["agrupacion"]
            })

        path = os.path.join(BASE_DIR, "data", "dataset_ia.json")

    with open(path, "w", encoding="utf-8") as f:
        json.dump(dataset, f, ensure_ascii=False, indent=2)

    return jsonify({
        "registros": len(dataset),
        "archivo": path,
        "formato": formato
    })


# =========================
# API: EXPORTACION ESTRUCTURADA
# =========================

@app.route("/api/export_static", methods=["POST"])
def export_static():
    export_dir = os.path.join(BASE_DIR, "static_export")

    if os.path.exists(export_dir):
        shutil.rmtree(export_dir)

    os.makedirs(export_dir)
    os.makedirs(os.path.join(export_dir, "css"))
    os.makedirs(os.path.join(export_dir, "js"))
    os.makedirs(os.path.join(export_dir, "api"))

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT id, titulo, anio, modalidad, tipo_pieza, agrupacion, contenido, url FROM letras")
    rows = cursor.fetchall()
    conn.close()

    letras = [dict(r) for r in rows]

    # JSON completo
    with open(os.path.join(export_dir, "api", "letras.json"), "w", encoding="utf-8") as f:
        json.dump(letras, f, ensure_ascii=False, indent=2)

    # Exportacion estructurada
    por_anio = {}
    por_modalidad = {}

    for l in letras:
        anio = l.get("anio") or "sin_anio"
        mod = (l.get("modalidad") or "sin_modalidad").lower().replace(" ", "_")

        por_anio.setdefault(anio, []).append(l)
        por_modalidad.setdefault(mod, []).append(l)

    # Por anio
    anio_dir = os.path.join(export_dir, "api", "por_anio")
    os.makedirs(anio_dir, exist_ok=True)
    for anio, items in por_anio.items():
        with open(os.path.join(anio_dir, f"{anio}.json"), "w", encoding="utf-8") as f:
            json.dump(items, f, ensure_ascii=False, indent=2)

    # Por modalidad
    mod_dir = os.path.join(export_dir, "api", "por_modalidad")
    os.makedirs(mod_dir, exist_ok=True)
    for mod, items in por_modalidad.items():
        with open(os.path.join(mod_dir, f"{mod}.json"), "w", encoding="utf-8") as f:
            json.dump(items, f, ensure_ascii=False, indent=2)

    # Estadisticas JSON
    stats = obtener_estadisticas()
    with open(os.path.join(export_dir, "api", "estadisticas.json"), "w", encoding="utf-8") as f:
        json.dump(stats, f, ensure_ascii=False, indent=2)

    # Indice
    indice = {
        "total_letras": len(letras),
        "archivos": {
            "todas": "api/letras.json",
            "estadisticas": "api/estadisticas.json",
            "por_anio": {a: f"api/por_anio/{a}.json" for a in por_anio},
            "por_modalidad": {m: f"api/por_modalidad/{m}.json" for m in por_modalidad}
        }
    }
    with open(os.path.join(export_dir, "api", "index.json"), "w", encoding="utf-8") as f:
        json.dump(indice, f, ensure_ascii=False, indent=2)

    # Copiar frontend
    shutil.copy(os.path.join(BASE_DIR, "templates", "index.html"), os.path.join(export_dir, "index.html"))
    shutil.copy(os.path.join(BASE_DIR, "static", "css", "style.css"), os.path.join(export_dir, "css", "style.css"))
    shutil.copy(os.path.join(BASE_DIR, "static", "js", "app.js"), os.path.join(export_dir, "js", "app.js"))

    return jsonify({
        "exportadas": len(letras),
        "carpeta": export_dir,
        "archivos_anio": len(por_anio),
        "archivos_modalidad": len(por_modalidad)
    })


# =========================
# API: LIMPIAR TEXTOS
# =========================

@app.route("/api/limpiar_textos", methods=["POST"])
def limpiar_textos():
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("SELECT id, contenido FROM letras WHERE contenido IS NOT NULL")
    rows = cursor.fetchall()

    limpiados = 0
    for row in rows:
        limpia = normalizar_letra(row["contenido"])
        if limpia != row["contenido"]:
            calidad = evaluar_calidad(limpia)
            cursor.execute("UPDATE letras SET contenido=?, calidad=? WHERE id=?", (limpia, calidad, row["id"]))
            limpiados += 1

    conn.commit()
    conn.close()
    return jsonify({"limpiados": limpiados, "total": len(rows)})


# =========================
# API: CREDITOS Y LEGAL
# =========================

@app.route("/api/creditos")
def creditos():
    return jsonify({
        "proyecto": "Archivo Digital del Carnaval de Cadiz",
        "transcripcion": "Letras Desde el Paraiso",
        "fuente": "https://letrasdesdeelparaiso.blogspot.com/",
        "aviso_legal": (
            "Transcripcion realizada por Letras Desde el Paraiso. "
            "2026. Prohibida su reproduccion integra sin autorizacion. "
            "Para citar, incluya enlace directo a la publicacion original."
        ),
        "licencia": "Uso educativo y de investigacion. Contenido original propiedad de sus autores.",
        "tecnologia": "Flask + SQLite + FTS5"
    })


# =========================
# API: BUSQUEDA TEMATICA INTELIGENTE
# =========================

@app.route("/api/buscar_tematica")
def buscar_tematica():
    """Busqueda inteligente por tematica natural.
    Ej: 'Cadiz nostalgia', 'critica politica', 'amor madre'
    """
    q = request.args.get("q", "").strip()
    limit = int(request.args.get("limit", 30))

    if not q or len(q) < 2:
        return jsonify({"resultados": [], "total": 0})

    # Expandir sinonimos tematicos comunes del carnaval
    sinonimos = {
        "nostalgia": "recuerdo memoria tiempo pasado antigua vieja",
        "politica": "gobierno politico alcalde ministro rey congreso",
        "amor": "querer corazon cariño te quiero enamorado",
        "cadiz": "gaditano bahia caleta catedral tacita plata",
        "madre": "mama madre vieja casa familia",
        "mar": "oceano playa barco marinero ola puerto",
        "carnaval": "febrero disfraz mascara copla fiesta concurso",
        "muerte": "morir muerto cementerio cielo adios perder",
        "libertad": "libre cadena luchar lucha derecho",
        "humor": "risa gracia chiste comico gracioso",
    }

    # Expandir la query con sinonimos
    palabras = q.lower().split()
    expanded_terms = list(palabras)
    for palabra in palabras:
        if palabra in sinonimos:
            expanded_terms.extend(sinonimos[palabra].split()[:3])

    # Construir query FTS con OR
    fts_query = " OR ".join(expanded_terms)

    resultados = busqueda_fulltext(fts_query, limit, 0)

    return jsonify({
        "resultados": resultados,
        "total": len(resultados),
        "query_original": q,
        "query_expandida": fts_query,
        "tematicas_disponibles": list(sinonimos.keys())
    })


# =========================
# API: COMPARADOR DE ESTILOS
# =========================

@app.route("/api/comparar")
def comparar_estilos():
    """Compara estadisticas entre dos agrupaciones o autores."""
    agrupacion1 = request.args.get("a1", "").strip()
    agrupacion2 = request.args.get("a2", "").strip()

    if not agrupacion1 or not agrupacion2:
        return jsonify({"error": "Necesitas dos agrupaciones (a1 y a2)"}), 400

    conn = get_db()
    cursor = conn.cursor()

    def stats_agrupacion(nombre):
        cursor.execute("""
            SELECT COUNT(*) as total,
                   COUNT(DISTINCT anio) as anios,
                   GROUP_CONCAT(DISTINCT modalidad) as modalidades,
                   GROUP_CONCAT(DISTINCT tipo_pieza) as tipos,
                   GROUP_CONCAT(DISTINCT autor) as autores,
                   AVG(LENGTH(contenido)) as longitud_media,
                   AVG(calidad) as calidad_media,
                   MIN(anio) as primer_anio,
                   MAX(anio) as ultimo_anio
            FROM letras WHERE agrupacion LIKE ?
        """, (f"%{nombre}%",))
        row = cursor.fetchone()
        if not row or row["total"] == 0:
            return None

        cursor.execute("""
            SELECT tipo_pieza, COUNT(*) as cnt
            FROM letras WHERE agrupacion LIKE ? AND tipo_pieza IS NOT NULL
            GROUP BY tipo_pieza ORDER BY cnt DESC
        """, (f"%{nombre}%",))
        tipos_detalle = [{"tipo": r["tipo_pieza"], "cantidad": r["cnt"]} for r in cursor.fetchall()]

        return {
            "nombre": nombre,
            "total_letras": row["total"],
            "anios_activos": row["anios"],
            "modalidades": row["modalidades"],
            "tipos_pieza": tipos_detalle,
            "autores": row["autores"],
            "longitud_media": round(row["longitud_media"] or 0),
            "calidad_media": round(row["calidad_media"] or 0, 1),
            "primer_anio": row["primer_anio"],
            "ultimo_anio": row["ultimo_anio"]
        }

    stats1 = stats_agrupacion(agrupacion1)
    stats2 = stats_agrupacion(agrupacion2)

    conn.close()

    if not stats1:
        return jsonify({"error": f"No se encontro '{agrupacion1}'"}), 404
    if not stats2:
        return jsonify({"error": f"No se encontro '{agrupacion2}'"}), 404

    return jsonify({
        "comparacion": [stats1, stats2]
    })


# =========================
# API: ESTADISTICAS AVANZADAS
# =========================

@app.route("/api/estadisticas_avanzadas")
def estadisticas_avanzadas():
    conn = get_db()
    cursor = conn.cursor()

    stats = {}

    # Top autores
    cursor.execute("""
        SELECT autor, COUNT(*) as cantidad, COUNT(DISTINCT agrupacion) as agrupaciones
        FROM letras WHERE autor IS NOT NULL AND autor != ''
        GROUP BY autor ORDER BY cantidad DESC LIMIT 15
    """)
    stats["top_autores"] = [{"autor": r["autor"], "letras": r["cantidad"], "agrupaciones": r["agrupaciones"]} for r in cursor.fetchall()]

    # Evolucion por anio y modalidad
    cursor.execute("""
        SELECT anio, modalidad, COUNT(*) as cantidad
        FROM letras WHERE anio IS NOT NULL AND modalidad IS NOT NULL
        GROUP BY anio, modalidad ORDER BY anio
    """)
    evolucion = {}
    for r in cursor.fetchall():
        anio = r["anio"]
        if anio not in evolucion:
            evolucion[anio] = {}
        evolucion[anio][r["modalidad"]] = r["cantidad"]
    stats["evolucion"] = evolucion

    # Longitud media por modalidad
    cursor.execute("""
        SELECT modalidad, AVG(LENGTH(contenido)) as media, COUNT(*) as total
        FROM letras WHERE modalidad IS NOT NULL AND contenido IS NOT NULL
        GROUP BY modalidad
    """)
    stats["longitud_por_modalidad"] = [
        {"modalidad": r["modalidad"], "longitud_media": round(r["media"] or 0), "total": r["total"]}
        for r in cursor.fetchall()
    ]

    # Distribucion de calidad
    cursor.execute("""
        SELECT
            CASE
                WHEN calidad >= 80 THEN 'Excelente (80-100)'
                WHEN calidad >= 60 THEN 'Buena (60-79)'
                WHEN calidad >= 40 THEN 'Regular (40-59)'
                WHEN calidad >= 20 THEN 'Baja (20-39)'
                ELSE 'Sin evaluar (0-19)'
            END as rango,
            COUNT(*) as cantidad
        FROM letras GROUP BY rango ORDER BY calidad DESC
    """)
    stats["distribucion_calidad"] = [{"rango": r["rango"], "cantidad": r["cantidad"]} for r in cursor.fetchall()]

    conn.close()
    return jsonify(stats)


# =========================
# API: LETRA ALEATORIA
# =========================

@app.route("/api/aleatorio")
def letra_aleatoria():
    """Devuelve una letra aleatoria, opcionalmente filtrada."""
    modalidad = request.args.get("modalidad")
    anio = request.args.get("anio")

    conn = get_db()
    cursor = conn.cursor()

    query = "SELECT id, titulo, anio, modalidad, tipo_pieza, agrupacion, contenido, autor FROM letras WHERE contenido IS NOT NULL AND LENGTH(contenido) > 100"
    params = []

    if modalidad:
        query += " AND modalidad=?"
        params.append(modalidad)
    if anio:
        query += " AND anio=?"
        params.append(anio)

    query += " ORDER BY RANDOM() LIMIT 1"
    cursor.execute(query, params)
    row = cursor.fetchone()
    conn.close()

    if not row:
        return jsonify({"error": "No hay letras disponibles"}), 404

    return jsonify(dict(row))


# =========================
# API: TIMELINE
# =========================

@app.route("/api/timeline")
def timeline():
    """Cronologia del carnaval: eventos por anio con resumen."""
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT anio,
               COUNT(*) as total_letras,
               COUNT(DISTINCT agrupacion) as agrupaciones,
               COUNT(DISTINCT modalidad) as modalidades,
               GROUP_CONCAT(DISTINCT modalidad) as lista_modalidades,
               AVG(calidad) as calidad_media
        FROM letras
        WHERE anio IS NOT NULL
        GROUP BY anio
        ORDER BY anio
    """)

    timeline_data = []
    for r in cursor.fetchall():
        # Top agrupacion de ese anio
        cursor.execute("""
            SELECT agrupacion, COUNT(*) as cnt
            FROM letras WHERE anio=? AND agrupacion IS NOT NULL
            GROUP BY agrupacion ORDER BY cnt DESC LIMIT 3
        """, (r["anio"],))
        top_agrup = [row["agrupacion"] for row in cursor.fetchall()]

        timeline_data.append({
            "anio": r["anio"],
            "total_letras": r["total_letras"],
            "agrupaciones": r["agrupaciones"],
            "modalidades": r["lista_modalidades"],
            "calidad_media": round(r["calidad_media"] or 0, 1),
            "top_agrupaciones": top_agrup
        })

    conn.close()
    return jsonify({"timeline": timeline_data})


# =========================
# API: PALABRAS FRECUENTES
# =========================

@app.route("/api/palabras_frecuentes")
def palabras_frecuentes():
    """Analisis de frecuencia de palabras por modalidad/anio."""
    import re
    from collections import Counter

    modalidad = request.args.get("modalidad")
    anio = request.args.get("anio")
    limit = int(request.args.get("limit", 60))

    conn = get_db()
    cursor = conn.cursor()

    query = "SELECT contenido FROM letras WHERE contenido IS NOT NULL"
    params = []

    if modalidad:
        query += " AND modalidad=?"
        params.append(modalidad)
    if anio:
        query += " AND anio=?"
        params.append(anio)

    cursor.execute(query, params)

    # Stopwords del espanol + palabras muy comunes en letras
    stopwords = {
        "de", "la", "el", "en", "que", "y", "a", "los", "las", "del", "un",
        "una", "por", "con", "no", "es", "se", "su", "al", "lo", "como",
        "mas", "pero", "sus", "le", "ya", "o", "fue", "este", "ha", "si",
        "me", "mi", "te", "tu", "nos", "yo", "era", "son", "ser", "muy",
        "tan", "para", "ni", "sin", "hay", "eso", "esta", "ese", "esa",
        "estos", "estas", "esos", "esas", "todo", "toda", "todos", "todas",
        "otro", "otra", "otros", "he", "han", "cada", "donde", "cuando",
        "quien", "porque", "aunque", "entre", "hasta", "desde", "sobre",
        "tiene", "puede", "hace", "van", "voy", "viene", "dio", "da",
        "ser", "ver", "ir", "hoy", "dia", "vez", "bien", "aqui", "alli",
        "asi", "solo", "dos", "tres", "uno", "dos", "les", "cual"
    }

    counter = Counter()
    total_textos = 0

    for row in cursor.fetchall():
        texto = row["contenido"].lower()
        palabras = re.findall(r'[a-záéíóúñü]+', texto)
        palabras_filtradas = [p for p in palabras if len(p) > 3 and p not in stopwords]
        counter.update(palabras_filtradas)
        total_textos += 1

    conn.close()

    top_palabras = [{"palabra": p, "frecuencia": c} for p, c in counter.most_common(limit)]

    return jsonify({
        "palabras": top_palabras,
        "total_textos": total_textos,
        "filtros": {"modalidad": modalidad, "anio": anio}
    })


# =========================
# API: AUTORES DESTACADOS
# =========================

@app.route("/api/autor/<nombre>")
def detalle_autor(nombre):
    """Ficha completa de un autor con todas sus obras."""
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT COUNT(*) as total,
               COUNT(DISTINCT agrupacion) as agrupaciones,
               COUNT(DISTINCT anio) as anios,
               GROUP_CONCAT(DISTINCT modalidad) as modalidades,
               MIN(anio) as primer_anio,
               MAX(anio) as ultimo_anio,
               AVG(LENGTH(contenido)) as longitud_media
        FROM letras WHERE autor LIKE ?
    """, (f"%{nombre}%",))
    stats = cursor.fetchone()

    if not stats or stats["total"] == 0:
        conn.close()
        return jsonify({"error": "Autor no encontrado"}), 404

    cursor.execute("""
        SELECT id, titulo, anio, modalidad, tipo_pieza, agrupacion
        FROM letras WHERE autor LIKE ?
        ORDER BY anio DESC, titulo
    """, (f"%{nombre}%",))
    obras = [dict(r) for r in cursor.fetchall()]

    conn.close()

    return jsonify({
        "autor": nombre,
        "total_obras": stats["total"],
        "agrupaciones": stats["agrupaciones"],
        "anios_activos": stats["anios"],
        "modalidades": stats["modalidades"],
        "periodo": f"{stats['primer_anio'] or '?'} - {stats['ultimo_anio'] or '?'}",
        "longitud_media": round(stats["longitud_media"] or 0),
        "obras": obras
    })


if __name__ == "__main__":
    app.run(debug=True, port=8080)

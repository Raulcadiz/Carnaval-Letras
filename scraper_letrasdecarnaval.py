"""
Scraper para letrasdecarnaval.com
Estrategia: Descarga sitemap.xml -> extrae URLs de /letra/ -> scrape individual con metadata de URL
~15,337 letras disponibles (Comparsa, Chirigota, Coro, Cuarteto) desde 1885 hasta actualidad.

Ejecuta en hilo de fondo con progreso en tiempo real via SSE.
"""

import requests
from bs4 import BeautifulSoup
import sqlite3
import re
import time
import threading
import xml.etree.ElementTree as ET
from metadata_extractor import normalizar_letra
from database import DB_NAME, generar_hash

SITEMAP_URL = "https://letrasdecarnaval.com/sitemap.xml"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "es-ES,es;q=0.9,en;q=0.5",
}

MODALIDAD_MAP = {
    "comparsa": "Comparsa",
    "chirigota": "Chirigota",
    "coro": "Coro",
    "cuarteto": "Cuarteto",
}

TIPO_PIEZA_MAP = {
    "pasodoble": "Pasodoble",
    "cuple": "Cuplé",
    "tango": "Tango",
    "presentacion": "Presentación",
    "popurri": "Popurrí",
    "estribillo": "Estribillo",
    "cuarteta": "Cuarteta",
}


# =============================================
# Estado global del scraper (hilo de fondo)
# =============================================
class ScraperState:
    def __init__(self):
        self.running = False
        self.should_stop = False
        self.nuevas = 0
        self.duplicadas = 0
        self.errores = 0
        self.procesadas = 0
        self.total = 0
        self.mensaje = "Inactivo"
        self.ultima_letra = ""
        self.terminado = False
        self.lock = threading.Lock()

    def reset(self):
        self.running = False
        self.should_stop = False
        self.nuevas = 0
        self.duplicadas = 0
        self.errores = 0
        self.procesadas = 0
        self.total = 0
        self.mensaje = "Inactivo"
        self.ultima_letra = ""
        self.terminado = False

    def to_dict(self):
        with self.lock:
            pct = round(self.procesadas / self.total * 100, 1) if self.total > 0 else 0
            return {
                "running": self.running,
                "nuevas": self.nuevas,
                "duplicadas": self.duplicadas,
                "errores": self.errores,
                "procesadas": self.procesadas,
                "total": self.total,
                "porcentaje": pct,
                "mensaje": self.mensaje,
                "ultima_letra": self.ultima_letra,
                "terminado": self.terminado,
            }


scraper_state = ScraperState()


# =============================================
# Funciones de scraping
# =============================================

def parsear_metadata_url(url_slug):
    """Extrae modalidad, agrupacion, anio, tipo_pieza y titulo del slug de URL."""
    metadata = {
        "modalidad": None,
        "agrupacion": None,
        "anio": None,
        "tipo_pieza": None,
        "titulo_extraido": None,
    }

    match = re.search(r'/letra/(.+)$', url_slug)
    if not match:
        return metadata

    slug = match.group(1).rstrip('/')
    parts = slug.split('-')

    if not parts:
        return metadata

    if parts[0] in MODALIDAD_MAP:
        metadata["modalidad"] = MODALIDAD_MAP[parts[0]]

    anio_idx = None
    for i, part in enumerate(parts):
        if re.match(r'^(18|19|20)\d{2}$', part):
            anio_idx = i
            metadata["anio"] = part

    if anio_idx is None:
        return metadata

    agrupacion_parts = parts[1:anio_idx]
    if agrupacion_parts:
        metadata["agrupacion"] = ' '.join(agrupacion_parts).replace('-', ' ').title()

    remaining = parts[anio_idx + 1:]
    if remaining:
        tipo_key = remaining[0]
        if tipo_key in TIPO_PIEZA_MAP:
            metadata["tipo_pieza"] = TIPO_PIEZA_MAP[tipo_key]
            titulo_parts = remaining[1:]
            if titulo_parts:
                metadata["titulo_extraido"] = ' '.join(titulo_parts).replace('-', ' ').title()

    return metadata


def obtener_urls_sitemap():
    """Descarga y parsea el sitemap.xml para obtener todas las URLs de /letra/."""
    response = requests.get(SITEMAP_URL, headers=HEADERS, timeout=60)
    response.raise_for_status()

    root = ET.fromstring(response.content)

    ns = {'sm': 'http://www.sitemaps.org/schemas/sitemap/0.9'}

    urls_letras = []
    for url_elem in root.findall('.//sm:url', ns):
        loc = url_elem.find('sm:loc', ns)
        if loc is not None and '/letra/' in loc.text:
            urls_letras.append(loc.text)

    if not urls_letras:
        for url_elem in root.iter():
            if url_elem.tag.endswith('loc') and url_elem.text and '/letra/' in url_elem.text:
                urls_letras.append(url_elem.text)

    return urls_letras


def scrape_letra_page(url):
    """Descarga una pagina individual de letra y extrae el contenido."""
    response = requests.get(url, headers=HEADERS, timeout=15)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")

    h1 = soup.find("h1")
    titulo = h1.get_text(strip=True) if h1 else None

    contenido_tag = soup.find("p", class_=re.compile(r"user-select-none"))

    if not contenido_tag:
        container = soup.find("div", class_=re.compile(r"bg-light.*text-gray"))
        if container:
            contenido_tag = container.find("p")

    if not contenido_tag:
        return titulo, None

    for br in contenido_tag.find_all("br"):
        br.replace_with("\n")
    contenido = contenido_tag.get_text()

    return titulo, contenido


# =============================================
# Ejecucion en hilo de fondo
# =============================================

def _worker_scraper():
    """Hilo de fondo que ejecuta el scraper completo."""
    global scraper_state
    state = scraper_state

    try:
        state.mensaje = "Descargando sitemap.xml..."
        urls = obtener_urls_sitemap()
    except Exception as e:
        state.mensaje = f"Error descargando sitemap: {e}"
        state.running = False
        state.terminado = True
        return

    # Filtrar URLs que ya estan en la DB
    state.mensaje = "Filtrando URLs ya descargadas..."
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute("SELECT url FROM letras WHERE fuente='letrasdecarnaval'")
    urls_existentes = {row["url"] for row in cursor.fetchall()}
    conn.close()

    urls_nuevas = [u for u in urls if u not in urls_existentes]

    with state.lock:
        state.total = len(urls_nuevas)
        state.mensaje = f"Sitemap: {len(urls)} totales, {len(urls_nuevas)} nuevas por descargar"

    if not urls_nuevas:
        state.mensaje = f"Todo al dia. Las {len(urls)} letras del sitemap ya estan descargadas."
        state.running = False
        state.terminado = True
        return

    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    for i, url in enumerate(urls_nuevas):
        # Comprobar si se pidio parar
        if state.should_stop:
            state.mensaje = f"Detenido por el usuario. Guardadas {state.nuevas} letras nuevas."
            break

        with state.lock:
            state.procesadas = i + 1

        meta = parsear_metadata_url(url)

        # Rate limiting
        time.sleep(1.0)

        try:
            titulo_pagina, contenido_raw = scrape_letra_page(url)
        except Exception:
            with state.lock:
                state.errores += 1
            continue

        if not contenido_raw:
            with state.lock:
                state.errores += 1
            continue

        contenido = normalizar_letra(contenido_raw)

        if not contenido or len(contenido) < 30:
            with state.lock:
                state.errores += 1
            continue

        contenido_hash = generar_hash(contenido)
        cursor.execute("SELECT id FROM letras WHERE contenido_hash=?", (contenido_hash,))
        if cursor.fetchone():
            with state.lock:
                state.duplicadas += 1
            continue

        titulo_final = titulo_pagina or meta.get("titulo_extraido") or "Sin titulo"
        agrupacion = meta.get("agrupacion")

        try:
            cursor.execute("""
                INSERT INTO letras
                (titulo, anio, modalidad, tipo_pieza, agrupacion, autor, contenido, contenido_hash, url, fuente, fecha_scraping)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'))
            """, (
                titulo_final,
                meta.get("anio"),
                meta.get("modalidad"),
                meta.get("tipo_pieza"),
                agrupacion,
                None,
                contenido,
                contenido_hash,
                url,
                "letrasdecarnaval",
            ))
            conn.commit()
            with state.lock:
                state.nuevas += 1
                state.ultima_letra = titulo_final
                state.mensaje = f"[{state.procesadas}/{state.total}] +{state.nuevas} nuevas | {state.duplicadas} dup | {state.errores} err"
        except sqlite3.IntegrityError:
            with state.lock:
                state.duplicadas += 1
        except Exception:
            with state.lock:
                state.errores += 1

    conn.close()

    if not state.should_stop:
        state.mensaje = f"Completado: {state.nuevas} nuevas, {state.duplicadas} duplicadas, {state.errores} errores"

    state.running = False
    state.terminado = True


def iniciar_scraper():
    """Inicia el scraper en un hilo de fondo. Devuelve False si ya esta corriendo."""
    global scraper_state
    if scraper_state.running:
        return False

    scraper_state.reset()
    scraper_state.running = True
    scraper_state.mensaje = "Iniciando..."

    t = threading.Thread(target=_worker_scraper, daemon=True)
    t.start()
    return True


def detener_scraper():
    """Pide al scraper que se detenga limpiamente."""
    global scraper_state
    if scraper_state.running:
        scraper_state.should_stop = True
        scraper_state.mensaje = "Deteniendo... (esperando letra actual)"
        return True
    return False


def obtener_progreso():
    """Devuelve el estado actual del scraper."""
    return scraper_state.to_dict()

import re
import unicodedata

MODALIDADES = {
    "comparsa": "Comparsa",
    "comparsas": "Comparsa",
    "chirigota": "Chirigota",
    "chirigotas": "Chirigota",
    "coro": "Coro",
    "coros": "Coro",
    "cuarteto": "Cuarteto",
    "cuartetos": "Cuarteto",
    "romancero": "Romancero",
    "cancion libre": "Cancion Libre",
}

TIPOS_PIEZA = {
    "pasodoble": "Pasodoble",
    "pasodobles": "Pasodoble",
    "cupl\u00e9": "Cupl\u00e9",
    "cuple": "Cupl\u00e9",
    "cuples": "Cupl\u00e9",
    "cupl\u00e9s": "Cupl\u00e9",
    "popurr\u00ed": "Popurr\u00ed",
    "popurri": "Popurr\u00ed",
    "potpourri": "Popurr\u00ed",
    "presentaci\u00f3n": "Presentaci\u00f3n",
    "presentacion": "Presentaci\u00f3n",
    "tango": "Tango",
    "tangos": "Tango",
    "estribillo": "Estribillo",
    "parodia": "Parodia",
    "tema libre": "Tema Libre",
}


def normalizar_texto(texto):
    """Normaliza acentos, espacios y caracteres especiales."""
    if not texto:
        return ""
    texto = unicodedata.normalize("NFC", texto)
    texto = re.sub(r"\s+", " ", texto)
    texto = re.sub(r'[\u201c\u201d\u00ab\u00bb]', '"', texto)
    texto = re.sub(r"[\u2018\u2019]", "'", texto)
    texto = re.sub(r"\.{2,}", "...", texto)
    return texto.strip()


def normalizar_letra(texto):
    """Limpieza profesional del contenido de una letra."""
    if not texto:
        return ""
    texto = normalizar_texto(texto)

    # Eliminar cabeceras repetidas del blog
    patrones_basura = [
        r"Letras Desde el Para[i\u00ed]so",
        r"Carnaval de C[a\u00e1]diz",
        r"www\..*\.com",
        r"http\S+",
        r"Publicado por.*",
        r"Enviar por correo.*",
        r"Compartir con.*",
        r"Etiquetas:.*",
        r"No hay comentarios.*",
        r"Entrada m[a\u00e1]s reciente.*",
        r"Entrada antigua.*",
        r"P[a\u00e1]gina principal.*",
        r"Suscribirse a:.*",
        r"\d+ comentarios?:?",
        r"Publicar un comentario.*",
    ]
    for patron in patrones_basura:
        texto = re.sub(patron, "", texto, flags=re.IGNORECASE)

    # Normalizar saltos de linea
    texto = re.sub(r"\n{3,}", "\n\n", texto)
    texto = re.sub(r"[ \t]+\n", "\n", texto)
    texto = re.sub(r"\n[ \t]+", "\n", texto)

    # Eliminar espacios dobles
    lineas = texto.split("\n")
    lineas = [re.sub(r"  +", " ", l.strip()) for l in lineas]
    texto = "\n".join(lineas)

    return texto.strip()


# ==========================================
# DETECCION DESDE TITULO
# ==========================================

def detectar_anio_titulo(titulo):
    match = re.search(r"\b(19[5-9]\d|20[0-2]\d)\b", titulo)
    return match.group(0) if match else None


def detectar_modalidad_titulo(titulo):
    t = titulo.lower()
    for clave, valor in MODALIDADES.items():
        if clave in t:
            return valor
    return None


def detectar_tipo_pieza_titulo(titulo):
    t = titulo.lower()
    for clave, valor in TIPOS_PIEZA.items():
        # Buscar como palabra al inicio o despues de espacio
        if re.search(r'(?:^|\s)' + re.escape(clave), t):
            return valor
    return None


def detectar_agrupacion_titulo(titulo):
    """Extrae nombre de agrupacion del titulo.
    Patron tipico: Pasodoble "Texto" NombreAgrupacion (Letra)
    """
    limpio = titulo
    # Quitar (Letra) (Letras) del final
    limpio = re.sub(r'\s*\(Letras?\)\s*$', '', limpio, flags=re.IGNORECASE)
    # Quitar tipo de pieza del inicio
    limpio = re.sub(r'^(Pasodoble|Cupl[e\u00e9]s?|Popurr[i\u00ed]|Tango|Tangos|Presentaci[o\u00f3]n|Estribillo|Parodia)\s+', '', limpio, flags=re.IGNORECASE)
    # Si hay comillas, la agrupacion esta despues de las comillas
    match = re.search(r'["\u201d]\s+(.+)$', limpio)
    if match:
        agrupacion = match.group(1).strip()
        if len(agrupacion) > 1:
            return agrupacion
    return None


# ==========================================
# DETECCION DESDE ETIQUETAS
# ==========================================

def detectar_anio_etiquetas(etiquetas_str):
    if not etiquetas_str:
        return None
    for tag in etiquetas_str.split(","):
        tag = tag.strip()
        if re.match(r'^(19[5-9]\d|20[0-2]\d)$', tag):
            return tag
    return None


def detectar_modalidad_etiquetas(etiquetas_str):
    if not etiquetas_str:
        return None
    for tag in etiquetas_str.split(","):
        tag = tag.strip().lower()
        if tag in MODALIDADES:
            return MODALIDADES[tag]
    return None


def detectar_autor_etiquetas(etiquetas_str):
    if not etiquetas_str:
        return None
    for tag in etiquetas_str.split(","):
        tag = tag.strip()
        if tag.startswith("A:") or tag.startswith("a:"):
            return tag[2:].strip()
    return None


def detectar_agrupacion_etiquetas(etiquetas_str, modalidad=None):
    """La agrupacion en las etiquetas es el tag que NO es anio, modalidad, autor ni tipo."""
    if not etiquetas_str:
        return None
    skip_lower = set(MODALIDADES.keys()) | set(TIPOS_PIEZA.keys())
    for tag in etiquetas_str.split(","):
        tag = tag.strip()
        if not tag:
            continue
        t = tag.lower()
        # Saltar anios
        if re.match(r'^(19|20)\d{2}$', tag):
            continue
        # Saltar autores
        if tag.startswith("A:") or tag.startswith("a:"):
            continue
        # Saltar modalidades y tipos
        if t in skip_lower:
            continue
        # Lo que queda es probablemente la agrupacion
        if len(tag) > 1:
            return tag
    return None


# ==========================================
# DETECCION DESDE URL
# ==========================================

def detectar_anio_url(url):
    """El blog publica letras en el ano del carnaval, con ajustes."""
    if not url:
        return None
    match = re.search(r'blogspot\.com/(\d{4})/', url)
    if match:
        return match.group(1)
    return None


# ==========================================
# EXTRACCION COMPLETA CON PRIORIDADES
# ==========================================

def extraer_metadata(titulo, etiquetas=None, url=None):
    """Extrae metadata combinando titulo + etiquetas + URL con prioridades inteligentes."""

    # ANIO: prioridad etiquetas > titulo > URL
    anio = detectar_anio_etiquetas(etiquetas)
    if not anio:
        anio = detectar_anio_titulo(titulo)
    if not anio:
        anio = detectar_anio_url(url)

    # MODALIDAD: prioridad etiquetas > titulo
    modalidad = detectar_modalidad_etiquetas(etiquetas)
    if not modalidad:
        modalidad = detectar_modalidad_titulo(titulo)

    # TIPO PIEZA: prioridad titulo (siempre esta ahi)
    tipo_pieza = detectar_tipo_pieza_titulo(titulo)

    # AGRUPACION: prioridad titulo (mas preciso) > etiquetas
    agrupacion = detectar_agrupacion_titulo(titulo)
    if not agrupacion:
        agrupacion = detectar_agrupacion_etiquetas(etiquetas, modalidad)

    # AUTOR: solo en etiquetas
    autor = detectar_autor_etiquetas(etiquetas)

    return {
        "anio": anio,
        "modalidad": modalidad,
        "tipo_pieza": tipo_pieza,
        "agrupacion": agrupacion,
        "autor": autor,
    }


# ==========================================
# CALIDAD
# ==========================================

def evaluar_calidad(contenido):
    """Puntua la calidad del texto de 0 a 100."""
    if not contenido:
        return 0

    puntos = 0
    lineas = contenido.strip().split("\n")
    lineas_no_vacias = [l for l in lineas if l.strip()]

    # Longitud minima
    if len(lineas_no_vacias) >= 5:
        puntos += 20
    elif len(lineas_no_vacias) >= 2:
        puntos += 10

    # Longitud del texto
    chars = len(contenido)
    if chars > 500:
        puntos += 20
    elif chars > 200:
        puntos += 10

    # Sin basura web
    basura = ["http", "www.", "Publicado por", "Enviar por correo"]
    tiene_basura = any(b.lower() in contenido.lower() for b in basura)
    if not tiene_basura:
        puntos += 20

    # Estructura (estrofas separadas)
    bloques = contenido.split("\n\n")
    if len(bloques) >= 2:
        puntos += 20

    # Sin exceso de mayusculas
    mayusculas = sum(1 for c in contenido if c.isupper())
    ratio_mayus = mayusculas / max(len(contenido), 1)
    if ratio_mayus < 0.3:
        puntos += 20

    return min(puntos, 100)

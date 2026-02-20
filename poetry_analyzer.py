"""
Analizador poético para el Carnaval de Cádiz.

Módulos:
  - Conteo silábico con sinalefa, hiato y diptongo
  - Detección de esquema de rima (consonante/asonante)
  - Identificación de tipo estrófico
  - Detección de figuras retóricas (anáfora, epífora, enumeración, interrogación, exclamación)
  - Análisis de vocabulario y densidad léxica
  - Detección de léxico gaditano y carnavalesco
  - Extracción de versos destacados
"""

import re
import unicodedata
from collections import Counter


# ---------------------------------------------------------------------------
# STOPWORDS ESPAÑOL (básicas)
# ---------------------------------------------------------------------------

STOPWORDS = {
    "de", "la", "el", "en", "y", "a", "los", "que", "se", "del", "las", "un",
    "por", "con", "una", "su", "para", "es", "al", "lo", "como", "mas", "o",
    "pero", "sus", "le", "ya", "ha", "si", "me", "mi", "te", "tu", "no", "ni",
    "fue", "ser", "he", "hay", "tan", "bien", "vez", "cuando", "hasta", "sobre",
    "sin", "son", "entre", "yo", "era", "muy", "todo", "esta", "este", "ese",
    "eso", "esa", "nos", "les", "dos", "tres", "más", "más", "él", "ella",
    "nuestro", "nuestra", "nuestros", "nuestras", "vuestro", "vuestra",
    "también", "así", "donde", "quien", "porque", "aunque", "solo", "sólo",
    "ahí", "allí", "aquí", "ahora", "siempre", "nunca", "cada", "otro",
    "otra", "unos", "unas", "tanto", "tanta", "tanto", "poco", "mucho",
    "algo", "nada", "todo", "toda", "todos", "todas", "mismo", "misma",
}

# ---------------------------------------------------------------------------
# LÉXICO GADITANO Y CARNAVALESCO
# ---------------------------------------------------------------------------

LEXICO_GADITANO = {
    # Habla gaditana
    "arsa", "jaleo", "olé", "ole", "venga", "anda", "coña", "coñas",
    "tio", "tia", "chaval", "chavala", "mira", "oye", "vamos", "bueno",
    "joer", "joder", "ostia", "ostias", "hombre", "mujer", "niño", "niña",
    "peaso", "pedazo", "guiri", "gaditano", "gaditana", "gaditanos",
    "callejuela", "barrio", "la viña", "viña", "santa maria", "el pópulo",
    "pópulo", "populo", "almadraba", "pesquero", "pescaito", "pescao",
    "fritura", "menudo", "papas", "patatas", "chicharrones",
    # Carnaval
    "carnaval", "chirigota", "comparsa", "coro", "cuarteto", "agrupacion",
    "agrupación", "pasodoble", "cuplé", "cuple", "popurri", "popurrí",
    "tango", "estribillo", "parodia", "presentacion", "presentación",
    "concurso", "falla", "teatro", "gran teatro", "falla",
    "antifaz", "disfraz", "careta", "mascaras", "mascara", "carnavalero",
    "carnavalera", "carnavaleros", "carnavaleras",
    "autor", "directora", "director", "tipo", "letra", "musica", "música",
    "ensayo", "actuacion", "actuación", "pregon", "pregón", "pregonero",
    # Mar y Cádiz
    "bahia", "bahía", "océano", "mar", "playa", "marisma", "caño",
    "levante", "poniente", "vendaval", "brisa", "marea", "ola", "olas",
    "barco", "barca", "barcas", "velero", "marinero", "marinera",
    "cádiz", "cadiz", "gaditan", "gaditanos", "gaditanas",
    # Expresiones populares
    "duende", "gracia", "salero", "salera", "ole", "arsa",
    "jaleos", "copla", "coplas", "cantaor", "bailaor",
}


# ---------------------------------------------------------------------------
# VOCALES Y FONÉTICA
# ---------------------------------------------------------------------------

VOCALES = set("aeiouáéíóúàèìòùäëïöüâêîôûAEIOUÁÉÍÓÚÀÈÌÒÙÄËÏÖÜÂÊÎÔÛ")
VOCALES_FUERTES = set("aeoáéóàèòäëöâêô")
VOCALES_DEBILES = set("iuíúïüîû")

DIPTONGOS_CRECIENTES = {
    "ia", "ie", "io", "ua", "ue", "uo",
    "iá", "ié", "ió", "uá", "ué", "uó",
}
DIPTONGOS_DECRECIENTES = {
    "ai", "au", "ei", "eu", "oi", "ou",
    "ái", "áu", "éi", "éu", "ói",
}
DIPTONGOS = DIPTONGOS_CRECIENTES | DIPTONGOS_DECRECIENTES

# Palabras agudas comunes (terminan en consonante ≠ n/s, o en vocal tónica)
# Para simplificar: detectamos por acento gráfico o terminación estándar
TERMINACIONES_AGUDAS = re.compile(
    r"[^aeiouáéíóúns]$|[aeiouáéíóú]$",
)


def quitar_tildes(s):
    return "".join(
        c for c in unicodedata.normalize("NFD", s)
        if unicodedata.category(c) != "Mn"
    )


def tiene_acento_grafico(palabra):
    return any(c in "áéíóú" for c in palabra.lower())


def es_diptongo(v1, v2):
    par = (quitar_tildes(v1) + quitar_tildes(v2)).lower()
    return par in {quitar_tildes(d) for d in DIPTONGOS}


def es_hiato(v1, v2):
    """Hiato: dos vocales que NO forman diptongo, o vocal débil tónica."""
    # Si alguna lleva tilde y son fuerte+débil o débil+fuerte → hiato
    if v1.lower() in "íú" or v2.lower() in "íú":
        return True
    # Si ambas son fuertes → hiato
    if quitar_tildes(v1).lower() in "aeo" and quitar_tildes(v2).lower() in "aeo":
        return True
    return False


def contar_silabas_palabra(palabra):
    """Cuenta sílabas de una palabra aplicando reglas básicas de diptongo/hiato."""
    if not palabra:
        return 0
    palabra = quitar_tildes(palabra.lower())
    # Quitar caracteres no alfabéticos
    palabra = re.sub(r"[^a-z]", "", palabra)
    if not palabra:
        return 0

    silabas = 0
    i = 0
    vocales_encontradas = []

    while i < len(palabra):
        c = palabra[i]
        if c in "aeiou":
            # Comprobar diptongo
            if i + 1 < len(palabra) and palabra[i + 1] in "aeiou":
                par = palabra[i] + palabra[i + 1]
                sin_tilde_par = par  # ya sin tildes
                if sin_tilde_par in {quitar_tildes(d) for d in DIPTONGOS}:
                    # Es diptongo → una sílaba
                    silabas += 1
                    i += 2
                    continue
                else:
                    # Hiato → dos sílabas
                    silabas += 1
                    i += 1
                    continue
            else:
                silabas += 1
        i += 1

    return max(silabas, 1)


def ajuste_final_verso(silabas_base, verso):
    """
    Aplica ajuste por posición final del verso:
    - Verso llano (paroxítono): sin ajuste
    - Verso agudo (oxítono): +1
    - Verso esdrújulo (proparoxítono): -1
    Heurística simplificada por la última palabra.
    """
    palabras = [p for p in re.split(r"\s+", verso.strip()) if p]
    if not palabras:
        return silabas_base

    ultima = re.sub(r"[^a-záéíóúñü]", "", palabras[-1].lower())
    if not ultima:
        return silabas_base

    # Tiene acento gráfico propio → oxítona si el acento está en la última sílaba
    # Simplificación: terminaciones típicas agudas sin tilde
    terminaciones_agudas = r"(ad|al|an|ar|az|ed|el|en|er|ez|id|il|in|ir|iz|od|ol|on|or|oz|ud|ul|un|ur|uz|ión|ón)$"
    terminaciones_esdrujulas = r"(ísimo|ísima|ísimos|ísimas|ábamos|íamos|éramos|ábais|íais|érais)$"

    if re.search(terminaciones_esdrujulas, ultima):
        return silabas_base - 1
    if re.search(terminaciones_agudas, ultima) and not tiene_acento_grafico(ultima):
        # Puede ser aguda (terminación sin tilde)
        # Solo marcamos aguda si NO termina en vocal/n/s
        if not re.search(r"[aeiounsáéíóú]$", ultima):
            return silabas_base + 1
    # Acento gráfico en la última vocal → aguda
    if ultima and ultima[-1] in "áéíóú":
        return silabas_base + 1

    return silabas_base


def contar_silabas_verso(verso):
    """
    Cuenta sílabas de un verso completo.
    Aplica sinalefa: la vocal final de una palabra y la inicial de la siguiente
    se fusionan en una sílaba.
    """
    verso_limpio = re.sub(r"[¿¡!?.,;:\"'«»()\-_]", "", verso).strip()
    palabras = verso_limpio.split()
    if not palabras:
        return 0

    silabas_totales = 0
    silabas_por_palabra = [contar_silabas_palabra(p) for p in palabras]
    silabas_totales = sum(silabas_por_palabra)

    # Sinalefa: si palabra[i] termina en vocal y palabra[i+1] empieza en vocal → -1
    for i in range(len(palabras) - 1):
        fin = re.sub(r"[^a-záéíóúü]", "", palabras[i].lower())
        inicio = re.sub(r"[^a-záéíóúü]", "", palabras[i + 1].lower())
        if fin and inicio and fin[-1] in "aeiouáéíóú" and inicio[0] in "aeiouáéíóú":
            silabas_totales -= 1

    silabas_totales = ajuste_final_verso(silabas_totales, verso)
    return max(silabas_totales, 1)


# ---------------------------------------------------------------------------
# CLASIFICACIÓN DE METRO
# ---------------------------------------------------------------------------

NOMBRES_METRO = {
    2: "bisílabo",
    3: "trisílabo",
    4: "tetrasílabo",
    5: "pentasílabo",
    6: "hexasílabo",
    7: "heptasílabo",
    8: "octosílabo",
    9: "eneasílabo",
    10: "decasílabo",
    11: "endecasílabo",
    12: "dodecasílabo",
    14: "alejandrino",
}


def clasificar_metro(silabas):
    return NOMBRES_METRO.get(silabas, f"{silabas} sílabas")


def analizar_metrica(versos):
    """
    Analiza la métrica de una lista de versos.
    Devuelve conteo por metro y metro dominante.
    """
    conteo = Counter()
    medidas = []
    for v in versos:
        v_limpio = v.strip()
        if len(v_limpio) < 3:
            continue
        n = contar_silabas_verso(v_limpio)
        if 2 <= n <= 20:
            conteo[n] += 1
            medidas.append(n)

    if not conteo:
        return {"metro_dominante": None, "medidas": [], "distribucion": {}}

    metro_dom = conteo.most_common(1)[0][0]
    nombre = clasificar_metro(metro_dom)

    # Coherencia: % de versos que coinciden con el metro dominante (±1 sílaba)
    coherentes = sum(v for k, v in conteo.items() if abs(k - metro_dom) <= 1)
    coherencia = round(coherentes / len(medidas) * 100) if medidas else 0

    return {
        "metro_dominante": metro_dom,
        "nombre_metro": nombre,
        "coherencia_pct": coherencia,
        "medidas": medidas,
        "distribucion": {clasificar_metro(k): v for k, v in sorted(conteo.items())},
    }


# ---------------------------------------------------------------------------
# ANÁLISIS DE RIMA
# ---------------------------------------------------------------------------

def obtener_terminacion_rima(verso, n_consonante=3, n_asonante=2):
    """
    Extrae la terminación para calcular rima.
    - Consonante: últimas n_consonante letras (sin tildes)
    - Asonante: solo vocales de la terminación
    """
    verso = re.sub(r"[¿¡!?.,;:\"'«»()\-_]", "", verso).strip().lower()
    palabras = verso.split()
    if not palabras:
        return None, None

    ultima = re.sub(r"[^a-záéíóúñü]", "", palabras[-1])
    if len(ultima) < 2:
        return None, None

    sin_tilde = quitar_tildes(ultima)
    consonante = sin_tilde[-n_consonante:] if len(sin_tilde) >= n_consonante else sin_tilde
    asonante = "".join(c for c in sin_tilde[-4:] if c in "aeiou")

    return consonante, asonante


def calcular_esquema_rima(versos_estrofa):
    """
    Dado un grupo de versos (estrofa), calcula el esquema de rima.
    Ejemplo: ["A", "B", "A", "B"] → "ABAB"
    También indica si es consonante o asonante.
    """
    if not versos_estrofa:
        return {"esquema": "", "tipo": None}

    terminaciones_cons = []
    terminaciones_ason = []

    for v in versos_estrofa:
        cons, ason = obtener_terminacion_rima(v)
        terminaciones_cons.append(cons)
        terminaciones_ason.append(ason)

    # Asignar letras
    mapa_cons = {}
    mapa_ason = {}
    esquema_cons = []
    esquema_ason = []
    letra_idx = 0

    for t in terminaciones_cons:
        if t is None or t == "":
            esquema_cons.append("-")
            continue
        if t not in mapa_cons:
            mapa_cons[t] = chr(ord("A") + letra_idx % 26)
            letra_idx += 1
        esquema_cons.append(mapa_cons[t])

    letra_idx = 0
    for t in terminaciones_ason:
        if t is None or t == "":
            esquema_ason.append("-")
            continue
        if t not in mapa_ason:
            mapa_ason[t] = chr(ord("A") + letra_idx % 26)
            letra_idx += 1
        esquema_ason.append(mapa_ason[t])

    esquema_c = "".join(esquema_cons)
    esquema_a = "".join(esquema_ason)

    # Determinar tipo: si consonante tiene más rimas que asonante → consonante
    rimas_cons = len(set(mapa_cons.values()))
    rimas_ason = len(set(mapa_ason.values()))

    # Si hay pocas terminaciones distintas en consonante → es consonante
    if rimas_cons <= max(1, len(versos_estrofa) // 2):
        tipo = "consonante"
        esquema = esquema_c
    elif rimas_ason <= max(1, len(versos_estrofa) // 2):
        tipo = "asonante"
        esquema = esquema_a
    else:
        tipo = "libre"
        esquema = esquema_c

    return {
        "esquema": esquema,
        "tipo": tipo,
        "esquema_consonante": esquema_c,
        "esquema_asonante": esquema_a,
    }


FORMAS_ESTROFICAS = {
    # (n_versos, esquema_consonante) → nombre
    (4, "ABBA"): "serventesio",
    (4, "ABAB"): "cuarteto",
    (4, "AABB"): "pareado doble",
    (4, "ABCB"): "romance (cuarteta)",
    (4, "AAAA"): "cuarteta monorrima",
    (2, "AA"):   "pareado",
    (3, "ABA"):  "terceto",
    (3, "AAB"):  "terceto encadenado",
    (8, "ABABABCC"): "octava real",
    (10, "ABBAACCDDC"): "décima (espinela)",
}


def identificar_forma_estrofica(esquema, n_versos):
    clave = (n_versos, esquema)
    if clave in FORMAS_ESTROFICAS:
        return FORMAS_ESTROFICAS[clave]
    # Detectar romance por asonancia en versos pares
    if n_versos >= 4 and len(esquema) >= 4:
        pares = esquema[1::2]
        impares = esquema[0::2]
        if len(set(pares)) == 1 and len(set(impares)) > 1:
            return "romance"
    return None


def analizar_rima_completa(estrofas):
    """
    Analiza rima estrofa por estrofa.
    Devuelve esquema de cada estrofa y el esquema global más frecuente.
    """
    resultados = []
    esquemas = []

    for estrofa in estrofas:
        versos = [v for v in estrofa if v.strip() and len(v.strip()) > 3]
        if len(versos) < 2:
            continue
        rima = calcular_esquema_rima(versos)
        forma = identificar_forma_estrofica(rima["esquema"], len(versos))
        resultados.append({
            "n_versos": len(versos),
            "esquema": rima["esquema"],
            "tipo_rima": rima["tipo"],
            "forma_estrofica": forma,
        })
        esquemas.append(rima["esquema"])

    if not esquemas:
        return {"estrofas": [], "esquema_predominante": None, "tipo_rima": None}

    esquema_pred = Counter(esquemas).most_common(1)[0][0]
    tipos = [r["tipo_rima"] for r in resultados if r["tipo_rima"]]
    tipo_pred = Counter(tipos).most_common(1)[0][0] if tipos else None

    return {
        "estrofas": resultados,
        "esquema_predominante": esquema_pred,
        "tipo_rima": tipo_pred,
    }


# ---------------------------------------------------------------------------
# FIGURAS RETÓRICAS
# ---------------------------------------------------------------------------

def detectar_anafora(versos, min_palabras=2):
    """Detecta anáfora: mismo inicio en versos consecutivos."""
    anaforas = []
    for i in range(len(versos) - 1):
        v1 = versos[i].strip().lower().split()
        v2 = versos[i + 1].strip().lower().split()
        if not v1 or not v2:
            continue
        # Comparar primeras n palabras
        coinciden = 0
        for j in range(min(min_palabras, len(v1), len(v2))):
            if quitar_tildes(v1[j]) == quitar_tildes(v2[j]):
                coinciden += 1
            else:
                break
        if coinciden >= min_palabras:
            anaforas.append({
                "versos": [versos[i].strip(), versos[i + 1].strip()],
                "inicio": " ".join(v1[:coinciden]),
            })
    return anaforas


def detectar_epifora(versos, min_palabras=2):
    """Detecta epífora: mismo final en versos consecutivos."""
    epiforas = []
    for i in range(len(versos) - 1):
        v1 = versos[i].strip().lower().split()
        v2 = versos[i + 1].strip().lower().split()
        if not v1 or not v2:
            continue
        coinciden = 0
        for j in range(1, min(min_palabras + 1, len(v1) + 1, len(v2) + 1)):
            if quitar_tildes(v1[-j]) == quitar_tildes(v2[-j]):
                coinciden += 1
            else:
                break
        if coinciden >= min_palabras:
            epiforas.append({
                "versos": [versos[i].strip(), versos[i + 1].strip()],
                "final": " ".join(v1[-coinciden:]),
            })
    return epiforas


def detectar_enumeracion(verso):
    """Detecta enumeraciones: 3+ elementos separados por comas."""
    partes = [p.strip() for p in verso.split(",") if p.strip()]
    return len(partes) >= 3


def detectar_interrogacion(verso):
    return bool(re.search(r"[¿?]", verso))


def detectar_exclamacion(verso):
    return bool(re.search(r"[¡!]", verso))


def detectar_repeticion_palabras(versos, min_freq=3):
    """Detecta palabras con alta frecuencia relativa (posible paronomasia o repetición enfática)."""
    palabras = []
    for v in versos:
        for p in re.findall(r"\b[a-záéíóúñü]{4,}\b", v.lower()):
            if p not in STOPWORDS:
                palabras.append(quitar_tildes(p))

    total = len(palabras)
    if total < 10:
        return []

    conteo = Counter(palabras)
    umbral = max(min_freq, total * 0.04)  # 4% del total o min_freq
    repetidas = [
        {"palabra": p, "frecuencia": f}
        for p, f in conteo.most_common(10)
        if f >= umbral
    ]
    return repetidas


def analizar_figuras(versos):
    """Analiza figuras retóricas en la lista de versos."""
    anaforas = detectar_anafora(versos)
    epiforas = detectar_epifora(versos)

    enumeraciones = sum(1 for v in versos if detectar_enumeracion(v))
    interrogaciones = sum(1 for v in versos if detectar_interrogacion(v))
    exclamaciones = sum(1 for v in versos if detectar_exclamacion(v))
    palabras_repetidas = detectar_repeticion_palabras(versos)

    figuras = []
    if anaforas:
        figuras.append({"figura": "Anáfora", "ejemplos": anaforas[:3]})
    if epiforas:
        figuras.append({"figura": "Epífora", "ejemplos": epiforas[:3]})
    if enumeraciones > 0:
        figuras.append({"figura": "Enumeración", "count": enumeraciones})
    if interrogaciones > 0:
        figuras.append({"figura": "Interrogación retórica", "count": interrogaciones})
    if exclamaciones > 0:
        figuras.append({"figura": "Exclamación", "count": exclamaciones})
    if palabras_repetidas:
        figuras.append({"figura": "Palabras clave recurrentes", "palabras": palabras_repetidas[:5]})

    return figuras


# ---------------------------------------------------------------------------
# VOCABULARIO Y LÉXICO
# ---------------------------------------------------------------------------

def analizar_vocabulario(versos):
    """
    Analiza riqueza léxica y presencia de léxico gaditano/carnavalero.
    """
    todas_palabras = []
    for v in versos:
        for p in re.findall(r"\b[a-záéíóúñü]{3,}\b", v.lower()):
            todas_palabras.append(quitar_tildes(p))

    total_tokens = len(todas_palabras)
    vocabulario = set(todas_palabras)
    total_types = len(vocabulario)

    # Type-Token Ratio (densidad léxica)
    ttr = round(total_types / total_tokens * 100, 1) if total_tokens > 0 else 0

    # Palabras más frecuentes (sin stopwords)
    sin_stop = [p for p in todas_palabras if p not in STOPWORDS and len(p) >= 3]
    conteo = Counter(sin_stop)
    palabras_clave = [{"palabra": p, "frecuencia": f} for p, f in conteo.most_common(15)]

    # Léxico gaditano
    gaditanas = []
    for p in vocabulario:
        if p in LEXICO_GADITANO or quitar_tildes(p) in {quitar_tildes(g) for g in LEXICO_GADITANO}:
            gaditanas.append(p)

    return {
        "total_palabras": total_tokens,
        "vocabulario_unico": total_types,
        "densidad_lexica": ttr,
        "palabras_clave": palabras_clave,
        "lexico_gaditano": sorted(gaditanas),
        "riqueza": "alta" if ttr > 60 else ("media" if ttr > 40 else "baja"),
    }


# ---------------------------------------------------------------------------
# VERSOS DESTACADOS
# ---------------------------------------------------------------------------

def extraer_versos_destacados(versos, n=3):
    """
    Extrae los versos más destacados usando:
    - Longitud óptima (no demasiado cortos ni largos)
    - Presencia de palabras clave (no stopwords)
    - Presencia de signos de énfasis
    """
    scored = []
    conteo_palabras = Counter()
    for v in versos:
        for p in re.findall(r"\b[a-záéíóúñü]{4,}\b", v.lower()):
            if p not in STOPWORDS:
                conteo_palabras[quitar_tildes(p)] += 1

    for v in versos:
        v_limpio = v.strip()
        if len(v_limpio) < 15:
            continue

        score = 0
        # Longitud óptima: entre 20 y 60 caracteres
        if 20 <= len(v_limpio) <= 60:
            score += 3
        elif len(v_limpio) > 60:
            score += 1

        # Signos de énfasis
        if re.search(r"[¡!¿?]", v_limpio):
            score += 2

        # Palabras con alta frecuencia en la letra
        palabras = re.findall(r"\b[a-záéíóúñü]{4,}\b", v_limpio.lower())
        for p in palabras:
            if p not in STOPWORDS:
                freq = conteo_palabras.get(quitar_tildes(p), 0)
                if freq >= 2:
                    score += 1

        # Presencia de léxico gaditano/carnavalero
        if any(quitar_tildes(p) in {quitar_tildes(g) for g in LEXICO_GADITANO}
               for p in palabras):
            score += 2

        scored.append((score, v_limpio))

    scored.sort(key=lambda x: -x[0])
    return [v for _, v in scored[:n]]


# ---------------------------------------------------------------------------
# ANÁLISIS COMPLETO DE UNA LETRA
# ---------------------------------------------------------------------------

def segmentar_estrofas(contenido):
    """Divide el contenido en estrofas (bloques separados por líneas en blanco)."""
    bloques = re.split(r"\n\s*\n", contenido.strip())
    estrofas = []
    for bloque in bloques:
        versos = [l for l in bloque.split("\n") if l.strip()]
        if versos:
            estrofas.append(versos)
    return estrofas


def analizar_letra(contenido, titulo=""):
    """
    Análisis poético completo de una letra.
    Devuelve un dict con todos los sub-análisis.
    """
    if not contenido or len(contenido.strip()) < 20:
        return {"error": "Contenido insuficiente para analizar"}

    estrofas = segmentar_estrofas(contenido)
    todos_versos = [v for est in estrofas for v in est if v.strip()]

    if not todos_versos:
        return {"error": "No se encontraron versos"}

    # Sub-análisis
    metrica = analizar_metrica(todos_versos)
    rima = analizar_rima_completa(estrofas)
    figuras = analizar_figuras(todos_versos)
    vocabulario = analizar_vocabulario(todos_versos)
    versos_destacados = extraer_versos_destacados(todos_versos)

    # Estadísticas básicas
    n_estrofas = len(estrofas)
    n_versos = len(todos_versos)
    longitud_media_verso = round(
        sum(len(v) for v in todos_versos) / max(n_versos, 1), 1
    )

    # Score poético (0-100) combinando métricas
    score = 0
    if metrica["coherencia_pct"]:
        score += min(30, metrica["coherencia_pct"] * 0.3)
    if rima["tipo_rima"] in ("consonante", "asonante"):
        score += 25
    if figuras:
        score += min(20, len(figuras) * 5)
    if vocabulario["densidad_lexica"] > 40:
        score += 15
    if n_estrofas >= 2:
        score += 10

    return {
        "n_estrofas": n_estrofas,
        "n_versos": n_versos,
        "longitud_media_verso": longitud_media_verso,
        "metrica": metrica,
        "rima": rima,
        "figuras_retoricas": figuras,
        "vocabulario": vocabulario,
        "versos_destacados": versos_destacados,
        "score_poetico": round(score),
    }


# ---------------------------------------------------------------------------
# ANÁLISIS DE CORPUS (estadísticas agregadas)
# ---------------------------------------------------------------------------

def analizar_corpus(letras):
    """
    Analiza un conjunto de letras y devuelve estadísticas agregadas del corpus.
    letras: list de dicts con campos 'contenido', 'modalidad', 'anio', etc.
    """
    metros_globales = Counter()
    tipos_rima_global = Counter()
    esquemas_globales = Counter()
    figuras_globales = Counter()
    lexico_gaditano_global = Counter()
    scores = []
    palabras_clave_global = Counter()

    for l in letras:
        contenido = l.get("contenido", "")
        if not contenido or len(contenido.strip()) < 30:
            continue

        analisis = analizar_letra(contenido)
        if "error" in analisis:
            continue

        scores.append(analisis["score_poetico"])

        metro = analisis["metrica"].get("nombre_metro")
        if metro:
            metros_globales[metro] += 1

        tipo_rima = analisis["rima"].get("tipo_rima")
        if tipo_rima:
            tipos_rima_global[tipo_rima] += 1

        esquema = analisis["rima"].get("esquema_predominante")
        if esquema:
            esquemas_globales[esquema] += 1

        for fig in analisis.get("figuras_retoricas", []):
            figuras_globales[fig["figura"]] += 1

        for p in analisis["vocabulario"].get("lexico_gaditano", []):
            lexico_gaditano_global[p] += 1

        for pk in analisis["vocabulario"].get("palabras_clave", []):
            palabras_clave_global[pk["palabra"]] += pk["frecuencia"]

    n_analizadas = len(scores)

    return {
        "total_analizadas": n_analizadas,
        "score_medio": round(sum(scores) / max(n_analizadas, 1), 1),
        "metros_dominantes": [
            {"metro": k, "count": v}
            for k, v in metros_globales.most_common(8)
        ],
        "tipos_rima": [
            {"tipo": k, "count": v}
            for k, v in tipos_rima_global.most_common()
        ],
        "esquemas_frecuentes": [
            {"esquema": k, "count": v}
            for k, v in esquemas_globales.most_common(10)
        ],
        "figuras_frecuentes": [
            {"figura": k, "count": v}
            for k, v in figuras_globales.most_common(8)
        ],
        "lexico_gaditano_top": [
            {"palabra": k, "apariciones": v}
            for k, v in lexico_gaditano_global.most_common(20)
        ],
        "palabras_clave_corpus": [
            {"palabra": k, "frecuencia": v}
            for k, v in palabras_clave_global.most_common(25)
        ],
    }

"""
Importador para el dataset de HuggingFace: IES-Rafael-Alberti/letras-carnaval-cadiz
Descarga directamente los JSON del dataset (sin necesidad de scraping web).
~1,184 registros (958 accurate + 226 midaccurate) con licencia CC BY-SA 4.0.
"""

import requests
import sqlite3
from database import DB_NAME, generar_hash
from metadata_extractor import normalizar_letra

# URLs directas del dataset en HuggingFace
DATASET_URLS = {
    "accurate": "https://huggingface.co/datasets/IES-Rafael-Alberti/letras-carnaval-cadiz/raw/main/data/accurate-00000-of-00001.json",
    "midaccurate": "https://huggingface.co/datasets/IES-Rafael-Alberti/letras-carnaval-cadiz/raw/main/data/midaccurate-00000-of-00001.json",
}

HEADERS = {
    "User-Agent": "CarnavalSaaS/1.0 (Archivo Digital Carnaval de Cadiz)",
}

# Mapeo de group_type (numérico → texto)
GROUP_TYPE_MAP = {
    1: "Coro",
    2: "Comparsa",
    3: "Chirigota",
    4: "Cuarteto",
}

# Mapeo de song_type (numérico → texto)
SONG_TYPE_MAP = {
    1: "Presentación",
    2: "Pasodoble",  # Para comparsa/chirigota; en coro sería Tango
    3: "Cuplé",
    4: "Estribillo",
    5: "Popurrí",
    6: "Cuarteta",
}


def decodificar_song_type(song_type, group_type):
    """Decodifica el tipo de pieza teniendo en cuenta la modalidad.
    En Coro, song_type 2 = Tango (no Pasodoble).
    """
    if song_type == 2 and group_type == 1:
        return "Tango"
    return SONG_TYPE_MAP.get(song_type, f"Tipo {song_type}")


def ejecutar_importador_huggingface(solo_accurate=False, callback=None):
    """Importa el dataset de HuggingFace a la base de datos local.

    Args:
        solo_accurate: Si True, solo importa los registros "accurate" (más fiables)
        callback: Función para reportar progreso

    Returns:
        dict con estadísticas
    """
    def log(msg):
        if callback:
            callback(msg)

    conjuntos = ["accurate"] if solo_accurate else ["accurate", "midaccurate"]

    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    nuevas = 0
    duplicadas = 0
    errores = 0
    total_descargados = 0

    for conjunto in conjuntos:
        url = DATASET_URLS[conjunto]
        log(f"Descargando conjunto '{conjunto}' desde HuggingFace...")

        try:
            response = requests.get(url, headers=HEADERS, timeout=60)
            response.raise_for_status()
            datos = response.json()
        except requests.RequestException as e:
            log(f"Error descargando {conjunto}: {str(e)}")
            errores += 1
            continue
        except ValueError:
            log(f"Error parseando JSON de {conjunto}")
            errores += 1
            continue

        log(f"Descargados {len(datos)} registros del conjunto '{conjunto}'")
        total_descargados += len(datos)

        for i, item in enumerate(datos):
            if (i + 1) % 100 == 0:
                log(f"Procesando {conjunto}: {i+1}/{len(datos)}...")

            try:
                # Extraer campos del formato HuggingFace
                group = item.get("group", "").strip()
                year = str(item.get("year", "")).strip()
                group_type = item.get("group_type", 0)
                song_type = item.get("song_type", 0)
                authors = item.get("authors", [])
                lyrics = item.get("lyrics", [])

                if not lyrics or not group:
                    errores += 1
                    continue

                # Decodificar campos
                modalidad = GROUP_TYPE_MAP.get(group_type, f"Tipo {group_type}")
                tipo_pieza = decodificar_song_type(song_type, group_type)
                autor = ", ".join(authors) if authors else None
                contenido_raw = "\n".join(lyrics)

                # Normalizar contenido
                contenido = normalizar_letra(contenido_raw)
                if not contenido or len(contenido) < 20:
                    errores += 1
                    continue

                # Generar hash para deduplicación
                contenido_hash = generar_hash(contenido)

                # Verificar duplicado por hash
                cursor.execute("SELECT id FROM letras WHERE contenido_hash=?", (contenido_hash,))
                if cursor.fetchone():
                    duplicadas += 1
                    continue

                # Construir título
                titulo = f"{tipo_pieza} - {group}"
                if year:
                    titulo += f" ({year})"

                # URL única para este registro (usando el ID del dataset)
                dataset_id = item.get("id", f"hf_{conjunto}_{i}")
                url_unica = f"huggingface://letras-carnaval-cadiz/{conjunto}/{dataset_id}"

                # Verificar duplicado por URL
                cursor.execute("SELECT id FROM letras WHERE url=?", (url_unica,))
                if cursor.fetchone():
                    duplicadas += 1
                    continue

                cursor.execute("""
                    INSERT INTO letras
                    (titulo, anio, modalidad, tipo_pieza, agrupacion, autor, contenido, contenido_hash, url, fuente, fecha_scraping, verificado)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'), ?)
                """, (
                    titulo,
                    year if year else None,
                    modalidad,
                    tipo_pieza,
                    group,
                    autor,
                    contenido,
                    contenido_hash,
                    url_unica,
                    "huggingface",
                    1 if conjunto == "accurate" else 0,
                ))
                conn.commit()
                nuevas += 1

            except sqlite3.IntegrityError:
                duplicadas += 1
            except Exception:
                errores += 1

    conn.close()

    log(f"Importación finalizada: {nuevas} nuevas, {duplicadas} duplicadas, {errores} errores")

    return {
        "nuevas": nuevas,
        "duplicadas": duplicadas,
        "errores": errores,
        "total_descargados": total_descargados,
        "conjuntos": conjuntos,
    }

import requests
from bs4 import BeautifulSoup
import sqlite3
import re
import time
from metadata_extractor import normalizar_letra
from database import DB_NAME, generar_hash

BASE_URL = "https://letrasdesdeelparaiso.blogspot.com/"

HEADERS = {
    "User-Agent": "CarnavalSaaS/1.0 (Archivo Digital Carnaval de Cadiz)"
}


def ejecutar_scraper(max_paginas=None):
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    pagina = BASE_URL
    nuevas = 0
    duplicadas = 0
    errores = 0
    paginas_procesadas = 0

    while pagina:
        if max_paginas and paginas_procesadas >= max_paginas:
            break

        try:
            response = requests.get(pagina, headers=HEADERS, timeout=15)
            response.raise_for_status()
        except requests.RequestException:
            errores += 1
            break

        soup = BeautifulSoup(response.text, "html.parser")
        enlaces = soup.select("h3.post-title a")

        for enlace_tag in enlaces:
            enlace = enlace_tag.get("href", "")
            titulo = enlace_tag.text.strip()

            if not enlace or not titulo:
                continue

            # Duplicado por URL
            cursor.execute("SELECT id FROM letras WHERE url=?", (enlace,))
            if cursor.fetchone():
                duplicadas += 1
                continue

            try:
                time.sleep(0.3)
                post = requests.get(enlace, headers=HEADERS, timeout=15)
                post.raise_for_status()
                post_soup = BeautifulSoup(post.text, "html.parser")
                contenido_tag = post_soup.select_one(".post-body")

                if not contenido_tag:
                    continue

                texto_raw = contenido_tag.get_text("\n")
                texto = normalizar_letra(texto_raw)

                if not texto or len(texto) < 50:
                    continue

                # Duplicado por contenido
                texto_hash = generar_hash(texto)
                cursor.execute("SELECT id FROM letras WHERE contenido_hash=?", (texto_hash,))
                if cursor.fetchone():
                    duplicadas += 1
                    continue

                # Extraer fecha de publicacion
                fecha_pub = None
                fecha_tag = post_soup.select_one(".date-header span, .published, time")
                if fecha_tag:
                    fecha_pub = fecha_tag.text.strip()

                cursor.execute("""
                    INSERT INTO letras
                    (titulo, anio, modalidad, tipo_pieza, agrupacion, autor, contenido, contenido_hash, url, fuente, fecha_publicacion)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (titulo, None, None, None, None, None, texto, texto_hash, enlace, "letrasdesdeelparaiso", fecha_pub))

                conn.commit()
                nuevas += 1

            except requests.RequestException:
                errores += 1
            except Exception:
                errores += 1

        paginas_procesadas += 1

        siguiente = soup.select_one("a.blog-pager-older-link")
        if siguiente:
            pagina = siguiente.get("href")
        else:
            pagina = None

        time.sleep(0.5)

    conn.close()

    return {
        "nuevas": nuevas,
        "duplicadas": duplicadas,
        "errores": errores,
        "paginas": paginas_procesadas
    }

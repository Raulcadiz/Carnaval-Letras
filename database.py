import sqlite3
import hashlib
import os
from difflib import SequenceMatcher

DB_NAME = os.path.join(os.path.dirname(os.path.abspath(__file__)), "database.db")


def get_db():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def init_db():
    conn = get_db()
    cursor = conn.cursor()

    # Verificar si la tabla existe
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='letras'")
    if not cursor.fetchone():
        cursor.execute("""
            CREATE TABLE letras (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                titulo TEXT NOT NULL,
                anio TEXT,
                modalidad TEXT,
                tipo_pieza TEXT,
                agrupacion TEXT,
                autor TEXT,
                contenido TEXT,
                contenido_hash TEXT,
                url TEXT UNIQUE,
                fuente TEXT DEFAULT 'letrasdesdeelparaiso',
                fecha_scraping TEXT DEFAULT (datetime('now')),
                fecha_publicacion TEXT,
                verificado INTEGER DEFAULT 0,
                calidad INTEGER DEFAULT 0
            )
        """)

    conn.commit()
    conn.close()


def migrate_db():
    """Migra la base de datos existente al nuevo esquema sin perder datos."""
    conn = get_db()
    cursor = conn.cursor()

    # Verificar columnas existentes
    cursor.execute("PRAGMA table_info(letras)")
    columnas = {row["name"] for row in cursor.fetchall()}

    nuevas_columnas = {
        "tipo_pieza": "TEXT",
        "autor": "TEXT",
        "contenido_hash": "TEXT",
        "fuente": "TEXT DEFAULT 'letrasdesdeelparaiso'",
        "fecha_scraping": "TEXT",
        "fecha_publicacion": "TEXT",
        "verificado": "INTEGER DEFAULT 0",
        "calidad": "INTEGER DEFAULT 0",
    }

    for col, tipo in nuevas_columnas.items():
        if col not in columnas:
            try:
                cursor.execute(f"ALTER TABLE letras ADD COLUMN {col} {tipo}")
            except sqlite3.OperationalError:
                pass

    # Crear indices
    indices = [
        ("idx_anio", "anio"),
        ("idx_modalidad", "modalidad"),
        ("idx_tipo_pieza", "tipo_pieza"),
        ("idx_agrupacion", "agrupacion"),
        ("idx_contenido_hash", "contenido_hash"),
        ("idx_fuente", "fuente"),
    ]
    for idx_name, col in indices:
        if col in columnas or col in nuevas_columnas:
            try:
                cursor.execute(f"CREATE INDEX IF NOT EXISTS {idx_name} ON letras({col})")
            except sqlite3.OperationalError:
                pass

    # FTS5 para busqueda full-text
    try:
        cursor.execute("""
            CREATE VIRTUAL TABLE IF NOT EXISTS letras_fts USING fts5(
                titulo,
                contenido,
                agrupacion,
                content='letras',
                content_rowid='id',
                tokenize='unicode61 remove_diacritics 2'
            )
        """)
    except sqlite3.OperationalError:
        pass

    # Triggers para mantener FTS sincronizado
    triggers = [
        ("letras_ai", """
            CREATE TRIGGER IF NOT EXISTS letras_ai AFTER INSERT ON letras BEGIN
                INSERT INTO letras_fts(rowid, titulo, contenido, agrupacion)
                VALUES (new.id, new.titulo, new.contenido, new.agrupacion);
            END
        """),
        ("letras_ad", """
            CREATE TRIGGER IF NOT EXISTS letras_ad AFTER DELETE ON letras BEGIN
                INSERT INTO letras_fts(letras_fts, rowid, titulo, contenido, agrupacion)
                VALUES ('delete', old.id, old.titulo, old.contenido, old.agrupacion);
            END
        """),
        ("letras_au", """
            CREATE TRIGGER IF NOT EXISTS letras_au AFTER UPDATE ON letras BEGIN
                INSERT INTO letras_fts(letras_fts, rowid, titulo, contenido, agrupacion)
                VALUES ('delete', old.id, old.titulo, old.contenido, old.agrupacion);
                INSERT INTO letras_fts(rowid, titulo, contenido, agrupacion)
                VALUES (new.id, new.titulo, new.contenido, new.agrupacion);
            END
        """),
    ]
    for name, sql in triggers:
        try:
            cursor.execute(sql)
        except sqlite3.OperationalError:
            pass

    # Tabla de estadisticas cache
    try:
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS stats_cache (
                clave TEXT PRIMARY KEY,
                valor TEXT,
                actualizado TEXT DEFAULT (datetime('now'))
            )
        """)
    except sqlite3.OperationalError:
        pass

    conn.commit()
    conn.close()


def generar_hash(texto):
    if not texto:
        return None
    normalizado = texto.lower().strip()
    normalizado = " ".join(normalizado.split())
    return hashlib.md5(normalizado.encode("utf-8")).hexdigest()


def calcular_similitud(texto1, texto2):
    if not texto1 or not texto2:
        return 0.0
    return SequenceMatcher(None, texto1.lower(), texto2.lower()).ratio()


def buscar_duplicados(umbral=0.90):
    """Detecta letras duplicadas por hash exacto."""
    conn = get_db()
    cursor = conn.cursor()

    # Actualizar hashes faltantes
    cursor.execute("SELECT id, contenido FROM letras WHERE contenido_hash IS NULL AND contenido IS NOT NULL")
    for row in cursor.fetchall():
        h = generar_hash(row["contenido"])
        cursor.execute("UPDATE letras SET contenido_hash = ? WHERE id = ?", (h, row["id"]))
    conn.commit()

    # Duplicados exactos por hash
    cursor.execute("""
        SELECT contenido_hash, GROUP_CONCAT(id) as ids, COUNT(*) as cnt
        FROM letras
        WHERE contenido_hash IS NOT NULL
        GROUP BY contenido_hash
        HAVING cnt > 1
    """)
    duplicados_exactos = []
    for row in cursor.fetchall():
        ids = [int(x) for x in row["ids"].split(",")]
        duplicados_exactos.append({
            "tipo": "exacto",
            "ids": ids,
            "hash": row["contenido_hash"]
        })

    conn.close()
    return {
        "duplicados_exactos": duplicados_exactos,
        "total_grupos": len(duplicados_exactos)
    }


def eliminar_duplicados():
    """Elimina duplicados conservando el registro mas antiguo."""
    conn = get_db()
    cursor = conn.cursor()

    # Actualizar hashes
    cursor.execute("SELECT id, contenido FROM letras WHERE contenido_hash IS NULL AND contenido IS NOT NULL")
    for row in cursor.fetchall():
        h = generar_hash(row["contenido"])
        cursor.execute("UPDATE letras SET contenido_hash = ? WHERE id = ?", (h, row["id"]))
    conn.commit()

    # Eliminar duplicados exactos (mantener el de menor id)
    cursor.execute("""
        DELETE FROM letras WHERE id NOT IN (
            SELECT MIN(id) FROM letras
            WHERE contenido_hash IS NOT NULL
            GROUP BY contenido_hash
        ) AND contenido_hash IN (
            SELECT contenido_hash FROM letras
            WHERE contenido_hash IS NOT NULL
            GROUP BY contenido_hash
            HAVING COUNT(*) > 1
        )
    """)
    eliminados = cursor.rowcount
    conn.commit()
    conn.close()
    return eliminados


def obtener_estadisticas():
    conn = get_db()
    cursor = conn.cursor()

    stats = {}

    cursor.execute("SELECT COUNT(*) as total FROM letras")
    stats["total_letras"] = cursor.fetchone()["total"]

    cursor.execute("SELECT COUNT(DISTINCT anio) as total FROM letras WHERE anio IS NOT NULL")
    stats["total_anios"] = cursor.fetchone()["total"]

    cursor.execute("SELECT COUNT(DISTINCT modalidad) as total FROM letras WHERE modalidad IS NOT NULL")
    stats["total_modalidades"] = cursor.fetchone()["total"]

    cursor.execute("SELECT COUNT(DISTINCT agrupacion) as total FROM letras WHERE agrupacion IS NOT NULL")
    stats["total_agrupaciones"] = cursor.fetchone()["total"]

    # Por anio
    cursor.execute("""
        SELECT anio, COUNT(*) as cantidad
        FROM letras WHERE anio IS NOT NULL
        GROUP BY anio ORDER BY anio
    """)
    stats["por_anio"] = [{"anio": r["anio"], "cantidad": r["cantidad"]} for r in cursor.fetchall()]

    # Por modalidad
    cursor.execute("""
        SELECT modalidad, COUNT(*) as cantidad
        FROM letras WHERE modalidad IS NOT NULL
        GROUP BY modalidad ORDER BY cantidad DESC
    """)
    stats["por_modalidad"] = [{"modalidad": r["modalidad"], "cantidad": r["cantidad"]} for r in cursor.fetchall()]

    # Por tipo de pieza
    cursor.execute("""
        SELECT tipo_pieza, COUNT(*) as cantidad
        FROM letras WHERE tipo_pieza IS NOT NULL
        GROUP BY tipo_pieza ORDER BY cantidad DESC
    """)
    stats["por_tipo_pieza"] = [{"tipo": r["tipo_pieza"], "cantidad": r["cantidad"]} for r in cursor.fetchall()]

    # Top agrupaciones
    cursor.execute("""
        SELECT agrupacion, COUNT(*) as cantidad
        FROM letras WHERE agrupacion IS NOT NULL
        GROUP BY agrupacion ORDER BY cantidad DESC LIMIT 20
    """)
    stats["top_agrupaciones"] = [{"agrupacion": r["agrupacion"], "cantidad": r["cantidad"]} for r in cursor.fetchall()]

    # Calidad
    cursor.execute("SELECT COUNT(*) as total FROM letras WHERE verificado = 1")
    stats["verificadas"] = cursor.fetchone()["total"]

    cursor.execute("SELECT AVG(calidad) as media FROM letras WHERE calidad > 0")
    row = cursor.fetchone()
    stats["calidad_media"] = round(row["media"], 1) if row["media"] else 0

    conn.close()
    return stats


def busqueda_fulltext(query, limit=50, offset=0):
    conn = get_db()
    cursor = conn.cursor()

    try:
        cursor.execute("""
            SELECT l.id, l.titulo, l.anio, l.modalidad, l.tipo_pieza, l.agrupacion,
                   highlight(letras_fts, 1, '<mark>', '</mark>') as fragmento,
                   rank
            FROM letras_fts
            JOIN letras l ON l.id = letras_fts.rowid
            WHERE letras_fts MATCH ?
            ORDER BY rank
            LIMIT ? OFFSET ?
        """, (query, limit, offset))
        resultados = [dict(r) for r in cursor.fetchall()]
    except sqlite3.OperationalError:
        resultados = []

    conn.close()
    return resultados


def reconstruir_fts():
    """Reconstruye el indice FTS5 completo."""
    conn = get_db()
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM letras_fts")
        cursor.execute("""
            INSERT INTO letras_fts(rowid, titulo, contenido, agrupacion)
            SELECT id, titulo, contenido, agrupacion FROM letras
        """)
        conn.commit()
    except (sqlite3.OperationalError, sqlite3.DatabaseError):
        # Si esta corrupta, recrear desde cero
        conn.rollback()
        try:
            cursor.execute("DROP TABLE IF EXISTS letras_fts")
            cursor.execute("""
                CREATE VIRTUAL TABLE letras_fts USING fts5(
                    titulo, contenido, agrupacion,
                    content='letras', content_rowid='id',
                    tokenize='unicode61 remove_diacritics 2'
                )
            """)
            cursor.execute("""
                INSERT INTO letras_fts(rowid, titulo, contenido, agrupacion)
                SELECT id, titulo, contenido, agrupacion FROM letras
            """)
            conn.commit()
        except (sqlite3.OperationalError, sqlite3.DatabaseError):
            pass
    conn.close()

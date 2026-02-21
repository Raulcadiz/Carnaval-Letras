# 🎭 Carnaval de Cádiz — Archivo Literario Digital

> El mayor archivo digital de letras del Carnaval de Cádiz, con análisis poético, perfiles de autores y agrupaciones, y evolución histórica de 140 años de patrimonio oral.

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue?logo=python)](https://python.org)
[![Flask](https://img.shields.io/badge/Flask-3.0-black?logo=flask)](https://flask.palletsprojects.com)
[![SQLite](https://img.shields.io/badge/SQLite-FTS5-green?logo=sqlite)](https://sqlite.org)
[![License](https://img.shields.io/badge/Código-MIT-yellow)](LICENSE)
[![Data](https://img.shields.io/badge/Datos-CC%20BY--SA%204.0-orange)](CREDITS.md)

---

## ¿Qué es esto?

Este proyecto nace del amor al Carnaval de Cádiz y de la convicción de que sus letras merecen el mismo rigor académico y la misma visibilidad que cualquier otra forma de poesía española contemporánea.

Es un **archivo vivo** que combina:
- Scraping ético de las principales fuentes públicas de letras
- Análisis literario y poético automatizado (métrica, rima, figuras retóricas)
- Perfiles de autores y agrupaciones con toda su trayectoria
- Evolución temática diacrónica (1885–hoy)
- API pública para investigadores y desarrolladores

---

## Números clave

| Métrica | Valor |
|---|---|
| **Total de letras** | ~17.700 |
| **Agrupaciones** | 1.121+ |
| **Años cubiertos** | 1885–2026 |
| **Fuentes** | 3 (letrasdecarnaval.com, letrasdesdeelparaiso.blogspot.com, HuggingFace/IES-Rafael-Alberti) |
| **Modalidades** | Comparsa, Chirigota, Coro, Cuarteto |
| **Tipos de pieza** | Presentación, Pasodoble, Cuplé, Estribillo, Popurrí, Romance... |

---

## Características principales

### 🔍 Búsqueda y Exploración
- **Búsqueda full-text** con SQLite FTS5 (índice invertido sobre título + contenido)
- **Filtros combinables**: año, modalidad, tipo de pieza, agrupación, fuente
- **Paginación** y exportación de resultados
- **Vista modal** de cada letra con metadatos completos

### 📊 Estadísticas y Visualización
- Dashboard con distribución por modalidad, año, tipo de pieza
- Gráficos de barras interactivos con datos en tiempo real
- Cronología navegable (timeline)
- Comparador de agrupaciones

### 🔤 Análisis Poético (tab "Poética")
Motor de análisis literario implementado en Python puro (`poetry_analyzer.py`):
- **Métrica**: conteo silábico con sinalefa, hiato y diptongo; metro dominante (octosílabo, endecasílabo, alejandrino...)
- **Rima**: esquema estrófico (ABAB, ABBA, AABB...), tipo (consonante/asonante/libre), forma estrófica (romance, cuarteto, décima, serventesio...)
- **Figuras retóricas**: anáfora, epífora, enumeración, interrogación retórica, exclamación, palabras recurrentes
- **Vocabulario**: densidad léxica (TTR), palabras clave, léxico gaditano/carnavalesco (100+ términos especializados)
- **Score poético 0–100** ponderando métricas, rima, figuras y vocabulario
- Análisis individual por letra (con caché en BD) y análisis de corpus con filtros

### 👤 Perfiles de Autores y Agrupaciones
Páginas dedicadas en `/autor/<nombre>` y `/agrupacion/<nombre>`:
- Ficha biográfica: actividad por año, modalidades, score poético medio
- Análisis poético agregado: metros frecuentes, tipos de rima, léxico característico
- Top letras más valoradas
- Versos icónicos
- Obra completa filtrable

### 🗂️ Directorio (tab "Directorio")
- Buscador de autores y agrupaciones con tarjetas navegables
- Filtrado por modalidad y ordenación por obras, score o trayectoria
- Acceso directo a todos los perfiles desde un único punto

### 📜 Historia / Evolución Temática (tab "Historia")
- Análisis diacrónico por épocas: Orígenes, Franquismo, Democracia, Siglo XXI, Presente
- Vocabulario característico de cada época (nube de palabras ponderada)
- Metro dominante, tipo de rima y score poético medio por período
- Top agrupaciones de cada era

### ⚙️ Panel de Administración (`/admin`)
- Ejecución de scrapers con progreso en tiempo real
- Enriquecimiento de metadatos con extracción de regex
- Deduplicación por hash de contenido (cross-fuente)
- Análisis poético masivo del corpus completo
- Exportación a dataset JSON (formato simple e instruction-tuning)
- Estadísticas por fuente

---

## Arquitectura

```
carnaval_saas/
├── app.py                        # Flask app — API REST + rutas web
├── database.py                   # Capa de datos: SQLite FTS5, migración, dedup, stats
├── metadata_extractor.py         # Extracción de metadatos con regex + scoring de calidad
├── poetry_analyzer.py            # Motor de análisis poético (métrica, rima, figuras)
├── scraper.py                    # Scraper de letrasdesdeelparaiso.blogspot.com
├── scraper_letrasdecarnaval.py   # Scraper de letrasdecarnaval.com (sitemap-driven)
├── scraper_huggingface.py        # Importador del dataset HuggingFace
├── templates/
│   ├── index.html                # Frontend público (SPA con 9 pestañas)
│   ├── admin.html                # Panel de administración
│   ├── perfil_autor.html         # Página de perfil de autor
│   └── perfil_agrupacion.html    # Página de perfil de agrupación
├── static/
│   ├── css/style.css             # Dark theme con CSS variables
│   ├── css/perfil.css            # Estilos para páginas de perfil
│   └── js/app.js                 # SPA JS: tabs, modales, gráficos, análisis
└── database.db                   # SQLite (no incluido en repo → generado en instalación)
```

### Stack tecnológico

| Capa | Tecnología |
|---|---|
| Backend | Python 3.10+, Flask 3.0 |
| Base de datos | SQLite con extensión FTS5 |
| Scrapers | requests + BeautifulSoup4 |
| Frontend | HTML/CSS/JS vanilla (sin frameworks) |
| Gráficos | Canvas API nativa |
| Análisis poético | Python puro (sin dependencias ML) |
| Dataset externo | HuggingFace `datasets` |

---

## Instalación

### Requisitos previos
- Python 3.10 o superior
- `pip`
- (Opcional) entorno virtual

### Pasos

```bash
# 1. Clona el repositorio
git clone https://github.com/TU_USUARIO/carnaval-saas.git
cd carnaval-saas

# 2. Crea y activa entorno virtual
python -m venv venv
source venv/bin/activate        # Linux/Mac
# venv\Scripts\activate         # Windows

# 3. Instala dependencias
pip install -r requirements.txt

# 4. Arranca el servidor
python app.py
```

El servidor arranca en `http://localhost:8080`.

### Para el importador de HuggingFace (opcional)

```bash
pip install datasets
```

---

## Primeros pasos

### 1. Importar datos

Accede al panel de administración en `http://localhost:8080/admin` y usa alguno de los scrapers:

| Fuente | Registros | Notas |
|---|---|---|
| `letrasdesdeelparaiso.blogspot.com` | ~4.185 | Scraper con paginación |
| `letrasdecarnaval.com` | ~12.500 | Sitemap-driven; respeta delays |
| HuggingFace (IES-Rafael-Alberti) | ~1.184 | Licencia CC BY-SA 4.0 |

### 2. Enriquecer metadatos

Desde el admin: **"Enriquecer Metadatos"** → extrae tipo de pieza, autor, año desde el texto con regex y recalcula el score de calidad.

### 3. Ejecutar análisis poético

Desde el admin: **"Análisis Poético del Corpus"** → analiza todas las letras y guarda los resultados en la BD. Esto habilita las estadísticas de la pestaña "Poética".

---

## API REST

Base URL: `http://localhost:8080`

### Letras

| Método | Endpoint | Descripción |
|---|---|---|
| `GET` | `/api/letras` | Listado paginado. Params: `page`, `per_page`, `modalidad`, `anio`, `tipo_pieza`, `agrupacion` |
| `GET` | `/api/buscar?q=` | Búsqueda full-text FTS5 |
| `GET` | `/api/filtros` | Valores disponibles para filtros |

### Estadísticas

| Método | Endpoint | Descripción |
|---|---|---|
| `GET` | `/api/estadisticas` | Stats globales del corpus |
| `GET` | `/api/estadisticas_fuentes` | Stats por fuente de datos |
| `GET` | `/api/estadisticas_poeticas` | Stats poéticas del corpus (requiere análisis previo) |

### Análisis poético

| Método | Endpoint | Descripción |
|---|---|---|
| `GET` | `/api/analisis_poetico/<id>` | Análisis individual de una letra (con caché en BD) |
| `POST` | `/api/analizar_corpus` | Análisis de muestra con filtros (body JSON: `modalidad`, `anio`, `limit`) |
| `POST` | `/api/analizar_todo` | Analiza todo el corpus y guarda en BD |

### Perfiles

| Método | Endpoint | Descripción |
|---|---|---|
| `GET` | `/api/autores` | Listado de autores |
| `GET` | `/api/agrupaciones` | Listado de agrupaciones |
| `GET` | `/api/autor/<nombre>` | Perfil completo de un autor |
| `GET` | `/api/agrupacion/<nombre>` | Perfil completo de una agrupación |

### Directorio e Historia

| Método | Endpoint | Descripción |
|---|---|---|
| `GET` | `/api/directorio` | Directorio navegable. Params: `tipo` (autores/agrupaciones), `q`, `modalidad`, `ordenar` |
| `GET` | `/api/evolucion_tematica` | Análisis diacrónico por épocas. Param: `modalidad` |

### Administración

| Método | Endpoint | Descripción |
|---|---|---|
| `POST` | `/api/scraper` | Lanza scraper de letrasdesdeelparaiso |
| `POST` | `/api/scraper_letrasdecarnaval` | Lanza scraper de letrasdecarnaval.com |
| `POST` | `/api/importar_huggingface` | Importa dataset HuggingFace |
| `POST` | `/api/enriquecer` | Enriquecimiento de metadatos |
| `POST` | `/api/deduplicar` | Deduplicación por hash |
| `POST` | `/api/generar_dataset` | Exporta dataset para entrenamiento AI |
| `POST` | `/api/export_static` | Exporta estructura por año/modalidad |
| `GET` | `/api/cross_reference` | Análisis cruzado entre fuentes |

### Ejemplo de uso

```bash
# Buscar letras sobre Cádiz
curl "http://localhost:8080/api/buscar?q=Cadiz"

# Letras de Comparsa de 2024
curl "http://localhost:8080/api/letras?modalidad=Comparsa&anio=2024"

# Análisis poético de la letra con ID 42
curl "http://localhost:8080/api/analisis_poetico/42"

# Directorio de autores ordenado por score poético
curl "http://localhost:8080/api/directorio?tipo=autores&ordenar=score"

# Evolución temática de la Comparsa
curl "http://localhost:8080/api/evolucion_tematica?modalidad=Comparsa"
```

---

## Modelo de datos

### Tabla `letras`

| Campo | Tipo | Descripción |
|---|---|---|
| `id` | INTEGER PK | Identificador único |
| `titulo` | TEXT | Título de la letra |
| `fecha` | TEXT | Fecha de publicación original |
| `anio` | INTEGER | Año del Carnaval |
| `modalidad` | TEXT | Comparsa / Chirigota / Coro / Cuarteto |
| `tipo_pieza` | TEXT | Presentación / Pasodoble / Cuplé / Estribillo... |
| `agrupacion` | TEXT | Nombre de la agrupación |
| `autor` | TEXT | Autor(es) de la letra |
| `contenido` | TEXT | Texto completo de la letra |
| `contenido_hash` | TEXT | MD5 del contenido normalizado (para dedup) |
| `url` | TEXT | URL de origen |
| `fuente` | TEXT | Identificador de la fuente |
| `calidad` | INTEGER | Score de calidad 0–100 |
| `verificado` | INTEGER | 1 si verificado manualmente |
| **Campos poéticos** | | Rellenados por `poetry_analyzer.py` |
| `metro_dominante` | INTEGER | Nº de sílabas del metro dominante |
| `nombre_metro` | TEXT | Nombre del metro (octosílabo, endecasílabo...) |
| `coherencia_metrica` | INTEGER | % de versos con el metro dominante |
| `esquema_rima` | TEXT | Esquema ABAB, ABBA... |
| `tipo_rima` | TEXT | consonante / asonante / libre / mixta |
| `score_poetico` | INTEGER | Score poético 0–100 |
| `n_estrofas` | INTEGER | Número de estrofas |
| `n_versos` | INTEGER | Número de versos |
| `densidad_lexica` | REAL | TTR (type-token ratio) en % |
| `versos_destacados` | TEXT | JSON: versos más relevantes |
| `figuras_retoricas` | TEXT | JSON: figuras detectadas |
| `lexico_gaditano` | TEXT | JSON: términos gaditanos presentes |
| `analisis_poetico` | TEXT | JSON: análisis completo |
| `fecha_analisis` | TEXT | Timestamp del análisis |

---

## Uso ético y legal

Este proyecto se desarrolla con **fines culturales, educativos y de investigación**. Ver [CREDITS.md](CREDITS.md) para información detallada sobre fuentes y licencias.

**Resumen:**
- El **código** se distribuye bajo licencia **MIT** (ver [LICENSE](LICENSE))
- Los **datos literarios** pertenecen a sus autores originales — este archivo no reivindica propiedad sobre las letras
- El scraping se realiza con delays respetuosos y User-Agent identificado
- El dataset de HuggingFace (IES-Rafael-Alberti) se usa bajo **CC BY-SA 4.0**

---

## Contribuir

¡Las contribuciones son bienvenidas! Ver [CONTRIBUTING.md](CONTRIBUTING.md) para guías de contribución.

Áreas donde más se necesita ayuda:
- 🧪 Tests unitarios para `poetry_analyzer.py`
- 🔤 Mejora del léxico gaditano (actualmente ~100 términos)
- 🎯 Mejora del scoring de calidad de letras
- 📱 Mejoras de diseño responsive
- 🌍 Internacionalización (castellano/inglés)
- 📚 Documentación de la API con OpenAPI/Swagger

---

## Roadmap

- [ ] Búsqueda semántica con embeddings (sentence-transformers)
- [ ] Comparador de estilos entre autores
- [ ] API pública con autenticación y rate limiting
- [ ] Exportación a formatos académicos (BibTeX, TEI-XML)
- [ ] Mapa geográfico de agrupaciones por barrio
- [ ] Integración con BVMC (Biblioteca Virtual Miguel de Cervantes)
- [ ] App móvil

---

## Reconocimientos

Este proyecto no sería posible sin el trabajo de quienes han preservado estas letras:

- **Los autores** del Carnaval de Cádiz, que llevan más de un siglo poniendo en verso la memoria colectiva de una ciudad
- **letrasdesdeelparaiso.blogspot.com** — pionero en la digitalización de letras
- **letrasdecarnaval.com** — el archivo más completo disponible en la web
- **IES Rafael Alberti (Cádiz)** — por el dataset estructurado publicado en HuggingFace

Ver [CREDITS.md](CREDITS.md) para los créditos completos.

---

## Licencia

- **Código fuente**: MIT License — ver [LICENSE](LICENSE)
- **Datos literarios**: Propiedad de sus autores originales — este proyecto no reclama derechos sobre el contenido literario
- **Dataset HuggingFace**: CC BY-SA 4.0 — ver atribución en [CREDITS.md](CREDITS.md)

---

*Hecho con ❤️ en Cádiz para el mundo*

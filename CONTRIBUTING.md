# Guía de Contribución

¡Gracias por querer mejorar el Archivo Literario del Carnaval de Cádiz! Este documento explica cómo colaborar de manera efectiva.

---

## Tipos de contribuciones

### 🐛 Reportar errores
Usa el [sistema de Issues de GitHub](https://github.com/TU_USUARIO/carnaval-saas/issues). Incluye:
- Descripción clara del problema
- Pasos para reproducirlo
- Comportamiento esperado vs. comportamiento real
- Versión de Python y sistema operativo

### 💡 Proponer mejoras
Abre un Issue con la etiqueta `enhancement`. Describe:
- Qué problema resuelve
- Cómo lo implementarías
- Alternativas consideradas

### 🔤 Mejorar el léxico gaditano
El archivo `poetry_analyzer.py` contiene un diccionario `LEXICO_GADITANO` con ~100 términos del español gaditano y carnavalesco. Si eres de Cádiz o conoces el carnaval, tu aportación es invaluable.

Para contribuir términos:
1. Abre un Issue con etiqueta `lexicon`
2. Lista los términos con su significado
3. O directamente envía un PR modificando `LEXICO_GADITANO` en `poetry_analyzer.py`

### 🧪 Tests
Actualmente el proyecto carece de tests unitarios. Las áreas prioritarias son:
- `poetry_analyzer.py` — conteo silábico, detección de rima, score poético
- `metadata_extractor.py` — extracción de regex, normalización
- `database.py` — funciones de deduplicación y estadísticas

### 📖 Documentación
- Mejorar docstrings en el código
- Añadir ejemplos a la API
- Traducir documentación al inglés

---

## Proceso de Pull Request

### 1. Fork y setup

```bash
# Fork el repo en GitHub, luego:
git clone https://github.com/TU_USUARIO/carnaval-saas.git
cd carnaval-saas
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 2. Crea una rama descriptiva

```bash
git checkout -b feature/busqueda-semantica
# o
git checkout -b fix/sinalefa-vocales-hiato
# o
git checkout -b docs/mejorar-readme
```

Convenciones de nombre de rama:
- `feature/` — nueva funcionalidad
- `fix/` — corrección de error
- `docs/` — solo documentación
- `refactor/` — refactorización sin cambio de comportamiento
- `lexicon/` — mejoras al léxico gaditano

### 3. Haz tus cambios

- Mantén cada PR enfocado en una sola cosa
- Usa nombres descriptivos en español para funciones y variables
- Comenta el código en español (coherencia con el proyecto)
- No rompas la compatibilidad de la API sin consultar antes

### 4. Prueba tus cambios

```bash
# Comprobación básica de que la app arranca
python -c "from app import app; print('OK')"

# Si modificas el analizador poético, prueba con una letra real:
python -c "
from poetry_analyzer import analizar_letra
resultado = analizar_letra(
    'Cádiz, ciudad de la bahía,\nte canto con el corazón.\nEn tu Carnaval hay alegría\ny en tu gente mucha pasión.',
    'Prueba'
)
print('Score:', resultado['score_poetico'])
print('Metro:', resultado['nombre_metro'])
print('Rima:', resultado['tipo_rima'])
"
```

### 5. Commit y push

```bash
git add .
git commit -m "feat: añadir búsqueda por verso destacado"
# o
git commit -m "fix: corregir sinalefa en vocales con h intercalada"
```

Convenciones de mensaje de commit (en español):
- `feat:` nueva funcionalidad
- `fix:` corrección de error
- `docs:` solo documentación
- `style:` formato, sin cambio lógico
- `refactor:` refactorización
- `test:` añadir tests
- `lexicon:` mejoras al léxico

### 6. Abre el Pull Request

En GitHub, desde tu fork → "Compare & pull request".

En la descripción del PR explica:
- ¿Qué hace este cambio?
- ¿Por qué es necesario?
- ¿Cómo lo probaste?
- ¿Hay efectos secundarios o migraciones de BD necesarias?

---

## Convenciones de código

### Python
- Sigue PEP 8 (líneas de máximo ~100 caracteres)
- Docstrings en español para las funciones principales
- Nombres de funciones: `snake_case` en español (`analizar_letra`, `obtener_estadisticas`)
- Constantes: `UPPER_CASE` en español (`LEXICO_GADITANO`, `FORMAS_ESTROFICAS`)

### HTML/CSS/JS
- Clases CSS en `kebab-case` con prefijos descriptivos (`dir-card`, `hist-epoca`, `poetica-kpi`)
- Variables CSS en `:root` para el sistema de diseño
- JavaScript sin frameworks — vanilla JS organizado por tab/funcionalidad
- Comentarios de sección con `// ==============================`

### API
- Endpoints en español (`/api/evolucion_tematica`, `/api/analizar_todo`)
- Respuestas JSON siempre con `Content-Type: application/json`
- Errores devueltos con `{"error": "mensaje descriptivo"}` y código HTTP apropiado
- Paginación: `page` y `per_page` como parámetros GET

### Base de datos
- Nombres de columnas en ASCII (`anio` no `año`, `contenido` no `letra`)
- Nuevas columnas siempre vía el mecanismo de migración en `database.py` → `nuevas_columnas`
- Nunca eliminar columnas en migraciones (solo añadir)

---

## Áreas prioritarias de desarrollo

Ordenadas por impacto esperado:

1. **Tests** — cobertura mínima para `poetry_analyzer.py` y `metadata_extractor.py`
2. **Léxico gaditano** — ampliar de ~100 a 500+ términos con ejemplos contextuales
3. **Mejora de métrica** — casos especiales: versos con elisión, grupos consonánticos, palabras compuestas
4. **Búsqueda semántica** — embeddings con `sentence-transformers` para búsqueda por significado
5. **Responsive móvil** — la UI actual no está optimizada para pantallas pequeñas
6. **API pública** — rate limiting, autenticación con API key, documentación OpenAPI
7. **Exportación TEI-XML** — formato estándar para humanidades digitales

---

## Preguntas frecuentes

**¿Puedo añadir un nuevo scraper para otra fuente?**
Sí, si la fuente es pública y el scraping está permitido por sus términos de uso. Crea el scraper en un archivo separado (`scraper_NOMBRE.py`) y añade el endpoint en `app.py`. Asegúrate de documentar la licencia de la fuente en `CREDITS.md`.

**¿Puedo cambiar el esquema de la base de datos?**
Las nuevas columnas sí, añadiéndolas al diccionario `nuevas_columnas` en `database.py`. Los cambios de tipo de columna existente o eliminaciones requieren discusión previa en un Issue.

**¿Hay tests automáticos que deban pasar?**
Actualmente no hay CI/CD configurado. Mientras no haya, la revisión es manual. Si añades tests, mejor aún.

**¿Puedo usar este código en mi propio proyecto?**
Sí, bajo los términos de la licencia MIT. Si usas también los datos del IES Rafael Alberti (HuggingFace), recuerda que están bajo CC BY-SA 4.0 y debes mantener esa licencia.

---

## Código de conducta

Este proyecto sigue los principios básicos del espíritu del Carnaval de Cádiz: **libertad de expresión, crítica constructiva, respeto a la diversidad y mucho humor**.

En la práctica:
- Sé respetuoso con los demás colaboradores
- Critica el código, no a la persona
- Acepta los comentarios de revisión como oportunidades de mejora
- No hay preguntas tontas — si algo no está claro en el código, es un error de documentación

---

*¡A los chiquirritines les gusta que los traten bien!*

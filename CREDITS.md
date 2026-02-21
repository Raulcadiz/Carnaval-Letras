# Créditos y Atribuciones

Este proyecto es un archivo digital de acceso libre construido sobre el trabajo colectivo de muchas personas. Aquí se reconoce explícitamente la procedencia de cada fuente de datos, las licencias aplicables y las condiciones de uso.

---

## Fuentes de datos

### 1. letrasdesdeelparaiso.blogspot.com

- **URL**: https://letrasdesdeelparaiso.blogspot.com
- **Tipo**: Blog público de digitalización de letras de Carnaval
- **Registros**: ~4.185 letras
- **Período**: Diversas décadas, con énfasis en el Carnaval moderno
- **Licencia**: El contenido del blog está sujeto a los derechos de autor de sus respectivos autores y del administrador del blog. Este proyecto lo indexa con fines de preservación cultural y uso no comercial.
- **Condiciones de uso**: Scraping realizado con respeto a los delays de carga. No se redistribuye el contenido en bloque. Enlace de retorno a la fuente original en cada letra.

### 2. letrasdecarnaval.com

- **URL**: https://www.letrasdecarnaval.com
- **Tipo**: Archivo web especializado, scrapeado mediante sitemap XML
- **Registros**: ~12.531 letras
- **Período**: 1885 – presente
- **Licencia**: Contenido propiedad de letrasdecarnaval.com y de los autores originales. Este proyecto lo indexa con fines de preservación cultural y uso no comercial.
- **Condiciones de uso**: Scraping con User-Agent identificado y delay mínimo de 1 segundo entre peticiones. No se redistribuye el contenido de forma masiva. Se incluye URL de origen en cada registro.
- **Nota**: letrasdecarnaval.com implementa protecciones anti-bot. El scraper de este proyecto utiliza cabeceras de navegador estándar y respeta los tiempos de respuesta del servidor.

### 3. HuggingFace — IES Rafael Alberti (Cádiz)

- **URL del dataset**: https://huggingface.co/datasets/IES-Rafael-Alberti/carnaval-de-cadiz
- **Institución**: IES Rafael Alberti, Cádiz (España)
- **Registros**: ~1.184 letras (accuracy: accurate + midaccurate)
- **Período**: Varias décadas del Carnaval contemporáneo
- **Licencia**: **Creative Commons Attribution-ShareAlike 4.0 International (CC BY-SA 4.0)**
- **Condiciones de uso CC BY-SA 4.0**:
  - ✅ Puedes usar, copiar y redistribuir el material
  - ✅ Puedes adaptar, transformar y construir sobre el material
  - ⚠️ **Debes dar crédito** al IES Rafael Alberti como autor del dataset
  - ⚠️ **Debes indicar** si realizaste cambios
  - ⚠️ **Debes distribuir** tus contribuciones bajo la misma licencia CC BY-SA 4.0
  - ❌ No puedes aplicar restricciones legales adicionales
- **Atribución requerida**: Si usas datos derivados de este dataset, debes mencionar: *"Basado en el dataset 'Carnaval de Cádiz' del IES Rafael Alberti, publicado bajo licencia CC BY-SA 4.0 en HuggingFace"*

---

## Derechos de autor sobre las letras

Las letras de Carnaval de Cádiz son **obras literarias protegidas por derechos de autor**. Sus autores son compositores, letristas y artistas gaditanos que han contribuido durante más de un siglo a esta tradición cultural.

Este proyecto:
- **No reclama propiedad** sobre ninguna letra
- **No permite el uso comercial** del contenido literario sin autorización de los autores
- Mantiene los **metadatos de autoría** en todos los registros
- Incluye **enlace de retorno** a la fuente original de cada letra
- Está pensado para **investigación, educación y preservación cultural**

Si eres autor o titular de derechos de alguna letra incluida en este archivo y deseas que se retire o modifique su tratamiento, escríbenos.

---

## Créditos del software

### Código fuente
Desarrollado con la colaboración de herramientas de IA asistidas por Claude (Anthropic).
Licencia: **MIT** — ver [LICENSE](LICENSE)

### Dependencias de código abierto

| Biblioteca | Licencia | Uso |
|---|---|---|
| [Flask](https://flask.palletsprojects.com) | BSD-3-Clause | Framework web |
| [SQLite](https://sqlite.org) | Dominio público | Base de datos + FTS5 |
| [requests](https://requests.readthedocs.io) | Apache 2.0 | Scrapers HTTP |
| [BeautifulSoup4](https://www.crummy.com/software/BeautifulSoup/) | MIT | Parsing HTML |
| [datasets (HuggingFace)](https://huggingface.co/docs/datasets) | Apache 2.0 | Importador HF |
| Python stdlib (`re`, `json`, `hashlib`, `sqlite3`...) | PSF License | Análisis y utilidades |

---

## Reconocimientos especiales

- A **todos los autores del Carnaval de Cádiz** — sin su genio creativo este archivo no tendría razón de ser
- A los **aficionados y archiveros anónimos** que durante décadas han copiado, publicado y preservado letras en blogs y foros de internet
- Al **pueblo de Cádiz**, que ha sabido hacer de su carnaval una forma única de democracia poética y crítica social
- Al **COAC (Concurso Oficial de Agrupaciones Carnavalescas)** y al Ayuntamiento de Cádiz por mantener viva esta institución
- Al **IES Rafael Alberti** por sistematizar y publicar bajo licencia abierta el primer dataset estructurado de letras de Carnaval

---

## Condiciones de uso del archivo

### Uso permitido (sin restricciones)
- Consulta, búsqueda y lectura personal
- Investigación académica y periodística con cita de la fuente
- Educación en todos sus niveles
- Desarrollo de aplicaciones no comerciales con atribución

### Uso permitido (con condiciones)
- **Proyectos derivados**: deben mantener la cadena de atribución a las fuentes originales y al IES Rafael Alberti para los datos CC BY-SA 4.0
- **Publicaciones académicas**: citar este archivo como fuente secundaria; citar a los autores originales de las letras como fuente primaria
- **Modelos de IA/ML**: los datasets generados con datos de HuggingFace deben heredar la licencia CC BY-SA 4.0

### Uso no permitido
- ❌ Uso comercial del contenido literario sin autorización de los autores
- ❌ Reclamar autoría sobre las letras
- ❌ Redistribución masiva del contenido sin mantener atribuciones
- ❌ Eliminar metadatos de autoría o fuente de los registros

---

## Contacto

Para cuestiones relacionadas con derechos de autor, atribuciones incorrectas o retirada de contenido, abre un [Issue en GitHub](https://github.com/TU_USUARIO/carnaval-saas/issues) o contacta directamente al mantenedor del proyecto.

---

*"El pueblo que canta no puede ser esclavo"* — Dicho del Carnaval de Cádiz

# Estado del proyecto: determinantes de hospitalizaciones prolongadas

Actualizado: 2026-10-20. Curso: Análisis de Datos (IIP316W-1). Entrega Avance 1: lunes 26-oct-2026 23:59 (Canvas).

## 1. Qué pide el enunciado

- Tema 7, "Egresos hospitalarios – GRD (MINSAL / FONASA)": determinantes de hospitalizaciones prolongadas.
  1. ¿Qué factores clínicos y demográficos predicen hospitalizaciones prolongadas?
  2. ¿Hay diagnósticos asociados a estancias atípicamente largas?
  3. ¿La complejidad clínica (peso relativo GRD) explica completamente la duración?
- Requisito obligatorio: dataset de 700.000 a 1.000.000 de registros.
- Avance 1 (20%): pregunta e hipótesis (H0/H1), 5–10 referencias con gap, metodología, diagrama metodológico (Problema → Datos → Procesamiento → Modelado → Evaluación), y pruebas de relaciones entre variables con tabla resumen: normalidad (Shapiro–Wilk, Lilliefors, Anderson–Darling, histograma, Q-Q), Pearson/Spearman, t/Welch/ANOVA+Tukey o Mann–Whitney/Kruskal–Wallis, chi-cuadrado con V de Cramér.
- Avance 2 (3-nov): EDA, limpieza, modelos, discusión. Certamen 2 (10-nov): paper 8–12 págs. + código. Examen (17-nov): dashboard interactivo (Streamlit, Dash, etc.) + presentación.

## 2. Lo que se descubrió sobre las fuentes

### Portal FONASA (datosabiertos.fonasa.cl)
- Es WordPress. Devuelve 403 a `curl` sin User-Agent; con User-Agent de navegador responde 200. No requiere Playwright.
- Páginas revisadas por la API `wp-json`: Régimen de Prestaciones, Financiamientos, Cotizaciones, Beneficiarios, Biblioteca y otras. Solo hay PDF y XLSX (boletines, cuentas públicas, estudios). **No hay base GRD desagregada.** GRD aparece solo en un tablero Tableau (`PropuestaTableroGRD`) y en noticias del seminario GRD 2024.

### Base GRD histórica de FONASA (retirada)
- Un post de 2020 en Foro Salud Digital confirma que FONASA publicó tablas planas de egresos 2019 y 2020 con codificación GRD (830.632 egresos en 2020, 1.042 grupos GRD).
- Estaba en `fonasa.cl/sites/fonasa/datos-abiertos`, sección "Base de datos", botón "Ir a sitio de descarga" → `https://www.fonasa.cl/sites/fonasa/bases_grd`.
- Esa URL hoy da 404. La URL antigua redirige al portal nuevo, sin sección GRD.
- Wayback Machine: la página `datos-abiertos` está capturada (14 capturas, 2021–2026) pero `bases_grd` **nunca fue archivada** (CDX vacío; replay da 404).
- Los archivos del sitio antiguo se servían como `.../sites/fonasa/adjuntos/<nombre>`. CDX muestra capturas de: `Diccionariogrd` (11 KB, 2024-09-14), `Tablasmaestrasgrd` (48 KB, 2024-09-14) y `ProfGRDDZCN` (329 KB, 2022-01-24). Ninguno es un archivo de datos de egresos. No se pudo listar todo `adjuntos` (CDX dio 504).
- Pendiente: bajar el diccionario y las tablas maestras (el replay dio 429 desde esta IP; hacerlo desde Firefox).

### Wayback Machine: límites
- Internet Archive no publica cifras oficiales. Fuentes comunitarias hablan de ~15 req/min en CDX y Save Page Now, y de filtros extra contra tráfico automatizado.
- Experiencia aquí: las consultas CDX pasan con una pausa de 15 s; el replay de archivos (`id_`) da 429. Una visita puntual con Playwright a una página archivada funcionó. Se aborta ante el primer 429.

### DEIS-MINSAL (egresos hospitalarios)
- Página `https://deis.minsal.cl/` (carga con JavaScript; se leyó con Playwright).
- Archivos: `https://repositoriodeis.minsal.cl/DatosAbiertos/EGRESOS/EGRESOS_<año>.zip`. Existen 2011–2025. Descargados: 2019–2024 (9–23 MB cada zip). Cada zip trae un CSV y `Diccionario BD egresos hospitalario.xlsx`.
- Formato: separador `;`, encoding `latin-1` (hay que confirmar si es `cp1252`: se vio `�` en "De Tarapac�").
- Filas 2020: 1.330.477 en total; 968.495 con previsión FONASA; 816.463 en establecimientos del SNSS.
- Líneas por CSV (con encabezado): 2019 1.667.181; 2020 1.330.478; 2021 1.467.063; 2022 1.597.119; 2023 1.612.268; 2024 1.667.350.
- Columnas (18): `PERTENENCIA_ESTABLECIMIENTO_SALUD, SEXO, GRUPO_EDAD, ETNIA, GLOSA_PAIS_ORIGEN, COMUNA_RESIDENCIA, GLOSA_COMUNA_RESIDENCIA, REGION_RESIDENCIA, GLOSA_REGION_RESIDENCIA, PREVISION, GLOSA_PREVISION, ANO_EGRESO, DIAG1 (CIE-10 principal), DIAG2 (causa externa), DIAS_ESTADA, CONDICION_EGRESO (1 vivo, 2 fallecido), INTERV_Q, PROCED`.
- `*` es marcador de dato faltante. `COMUNA_RESIDENCIA` se lee como entero y pierde el cero inicial; leer como texto.
- **No incluye:** peso relativo GRD, hospital o servicio de salud, fechas de ingreso/egreso, tipo de ingreso, número de diagnósticos secundarios, edad en años (solo `GRUPO_EDAD`).
- Ningún filtro probado reproduce exactamente 830.632 (SNSS: 816.463; FONASA sin obstétricos: 771.475; SNSS sin obstétricos: 657.587).

## 3. Decisión pendiente y recomendación

| Opción | Filas 2020 | Comentario |
|---|---|---|
| A. DEIS 2020, solo FONASA | 968.495 | Recomendada. Cumple el rango y mantiene el foco FONASA. |
| B. DEIS 2020, solo SNSS | 816.463 | Más cercana a la cifra 830.632, pero mezcla "red pública" con "beneficiario FONASA". |
| C. Base GRD real | n/d | No hay fuente pública hoy. Hay que encontrar archivos en Wayback o pedir al profesor. |

Cobertura de las preguntas con DEIS:
- P1 (factores que predicen estadías prolongadas): sí. Objetivo `DIAS_ESTADA` (regresión) o binaria "prolongada" (> percentil 90 o > Q3 + 1,5·RIC). Predictores: edad (grupo), sexo, región, previsión, categoría CIE-10, `INTERV_Q`, `PROCED`.
- P2 (diagnósticos con estancias atípicas): sí, por capítulo/categoría CIE-10 (Kruskal–Wallis con post-hoc, proporción de prolongadas).
- P3 (peso relativo GRD): **no** con DEIS. Alternativa: complejidad clínica aproximada (capítulo CIE-10, cirugía, procedimientos, edad) y medir la varianza explicada; hay que declararlo como limitación.

Limitaciones a declarar en el paper: sin GRD ni hospital; p-valores ≈ 0 con n ≈ 968k (reportar tamaños de efecto: V de Cramér, r de Spearman, d de Cohen); un año como base de modelado (los otros años para comparar o validar; juntar años supera 1M).

## 4. Lo que falta (en orden)

1. Confirmar con el profesor si aceptan egresos DEIS sin peso GRD, y de dónde sale la base GRD que esperan (revisar también `Proyectos de investigación_2026-1.docx`).
2. Desde Firefox: abrir `https://web.archive.org/web/20240914195438/https://www.fonasa.cl/sites/fonasa/adjuntos/Diccionariogrd` y el listado `https://web.archive.org/web/*/https://www.fonasa.cl/sites/fonasa/adjuntos/*`; buscar nombres con "egres", "2019", "2020", ".zip", ".csv". Guardar lo útil en `data/raw/fonasa_wayback/`.
3. Decidir A, B o C.
4. Escribir `scripts/01_descarga.py` o `notebooks/01_descarga_y_exploracion.ipynb`: descarga, detección de separador/encoding, carga.
5. Generar `data/reporte_inicial.md`: filas/columnas por año, tipos, % nulos, únicos, 3 ejemplos, columnas clave, descriptivos de `DIAS_ESTADA` (media, mediana, percentiles 1/5/95/99, máximo, casos con 0 y >365 días; hay 494 con >365 en 2020), y filtros justificados.
6. Guardar `data/processed/egresos_<año>.parquet` con columnas en `snake_case`, más derivadas: `edad_media` (punto medio de `GRUPO_EDAD`), capítulo y categoría CIE-10 (diccionario), `es_obstetrico`, `es_neonatal`, `estadia_prolongada` (umbral parametrizable).
7. Avance 1: pregunta e hipótesis, revisión de literatura (5–10 referencias con gap), metodología, diagrama, pruebas de la sección 5 y tabla resumen. Entrega 26-oct.
8. Avance 2, paper y dashboard (calendario arriba).

## 5. Estructura de la carpeta

- `data/raw/EGRESOS_2019..2024.zip`: originales descargados (no modificar).
- `data/raw/x2019..x2024/`: CSV y diccionario extraídos.
- `data/raw/fonasa_wayback/`: vacío; pendiente de archivos de Wayback.
- `data/processed/`: vacío.
- `scripts/00_explorar_deis.py`: lista enlaces de una página con Playwright (usado en `deis.minsal.cl`).
- `scripts/00_wayback_visita.py`: una visita con Playwright a una URL archivada; lista enlaces.
- `scripts/wayback_polite.py`: peticiones con pausa de 15 s que abortan ante 429.
- `requirements.txt`: dependencias. Entorno: `python3 -m venv .venv && .venv/bin/pip install -r requirements.txt && .venv/bin/playwright install chromium`.

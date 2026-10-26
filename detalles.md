Guía del Proyecto de Investigación
 

Descripción general
El proyecto consiste en desarrollar, en equipo, una investigación aplicada de análisis de datos sobre uno de los temas propuestos en el documento Proyectos de investigación_2026-1.docxDescargar Proyectos de investigación_2026-1.docx (ciencia y política científica, medio ambiente, educación, desigualdad social, mercado laboral, salud hospitalaria — GRD, o temas interdisciplinarios). Requerimiento obligatorio el data set debe ser entre 700-000 -  1.000.000 de registros

El trabajo debe partir de una pregunta de investigación clara, sustentarse en literatura, aplicar métodos estadísticos de inferencia y modelamiento, y culminar en un paper y un dashboard interactivo que comunique los hallazgos.

El proyecto será evaluado en cuatro hitos:

Hito	Entregable	Fecha	Ponderación
Avance 1	Diseño del estudio y análisis de relaciones entre variables	20 de octubre	20%
Avance 2	Ejecución del análisis y modelamiento	3 de noviembre	20%
Certamen 2	Paper y Presentación	10 de noviembre	60%
Examen	Presentación del proyecto en dashboard interactivo	17 de noviembre	30%
La evaluación global se basa en la siguiente rúbrica:

Criterio	Ponderación
Pregunta de investigación	10%
Revisión de literatura	20%
Metodología de análisis de datos	25%
Interpretación de resultados	20%
Calidad del paper	15%
Estructura del paper	10%
AVANCE 1 (20%) — Entrega: 20 de octubre
Enfocado en el diseño del estudio y las relaciones entre variables

Objetivo
Construir una base sólida del proyecto: problema, hipótesis, diseño metodológico y una primera caracterización estadística de las relaciones entre las variables seleccionadas.

Debe contener:
1. Pregunta de investigación (15%)
Clara, específica y medible
Bien contextualizada
No ambigua
Hipótesis nula 
 y alternativa 
 formuladas explícitamente
Error común: preguntas muy generales o descriptivas.

2. Revisión de literatura (20%)
5–10 referencias mínimo
Síntesis crítica (no solo resumen)
Identificación de un gap
Error común: copiar papers sin conectar con el proyecto.

3. Metodología (30%) (nivel diseño)
Tipo de análisis (predictivo, descriptivo, inferencial, etc.)
Fuente de datos, unidad de análisis y período
Variables seleccionadas, su tipo (numérica / categórica) y justificación
Modelos propuestos
Métricas de evaluación
4. Diagrama metodológico (OBLIGATORIO)
Debe mostrar claramente el flujo:

Problema → Datos → Procesamiento → Modelado → Evaluación

5. Análisis de relaciones entre variables (35%)
Esta sección es la base inferencial del proyecto. Cada equipo debe caracterizar estadísticamente las relaciones entre las variables que utilizará, aplicando el test adecuado según el tipo de cada variable. Para cada prueba se debe reportar: hipótesis (
 / 
), estadístico, valor-p, nivel de significancia (
), decisión e interpretación en el contexto del problema.

5.1 Pruebas de bondad de ajuste (supuesto de normalidad)
Antes de aplicar pruebas paramétricas se debe verificar si las variables numéricas se distribuyen normalmente:

Shapiro–Wilk (recomendado para muestras pequeñas y medianas, 
)
Kolmogorov–Smirnov (con corrección de Lilliefors cuando se estiman los parámetros desde la muestra)
Anderson–Darling (mayor sensibilidad en las colas de la distribución)
Complementar con histograma y gráfico Q-Q. El resultado de esta etapa determina si se usan pruebas paramétricas o no paramétricas en los puntos siguientes.

5.2 Numérica vs. numérica
Correlación de Pearson (
): relación lineal; requiere normalidad en ambas variables
Correlación de Spearman (
): relación monótona; no requiere normalidad y es robusta a outliers
Reportar el coeficiente, su significancia y un gráfico de dispersión. Interpretar la dirección y la fuerza de la relación.

5.3 Numérica vs. categórica
t de Student: comparación de medias entre dos grupos (verificar homogeneidad de varianzas con Levene; usar la corrección de Welch si no se cumple)
ANOVA de un factor: comparación de medias entre tres o más grupos; si resulta significativo, aplicar pruebas post-hoc (Tukey HSD)
Si no se cumple normalidad, utilizar las alternativas no paramétricas: Mann–Whitney U (dos grupos) o Kruskal–Wallis (tres o más grupos). Acompañar con boxplots por grupo.

5.4 Categórica vs. categórica
Chi-cuadrado de independencia (
) sobre la tabla de contingencia (frecuencias esperadas 
; en tablas 2×2 con frecuencias pequeñas usar el test exacto de Fisher)
Reportar la tabla de contingencia, el estadístico 
, los grados de libertad, el valor-p y una medida de fuerza de asociación (V de Cramér). Acompañar con gráfico de barras apiladas o mapa de calor.

5.5 Tabla resumen (OBLIGATORIA)
Variable 1	Variable 2	Test aplicado	Valor-p	Conclusión
…	…	…	…	…
Error común: aplicar un test sin verificar sus supuestos, o reportar el valor-p sin interpretarlo en el contexto del problema.

Evaluación en este avance
Pregunta e hipótesis (15%)
Literatura (20%)
Metodología y diagrama (30%)
Análisis de relaciones entre variables (35%)
Este avance representa la base conceptual e inferencial del proyecto.

AVANCE 2 (20%) — Entrega: 3 de noviembre
Enfocado en ejecución y análisis

Objetivo
Implementar el análisis completo y generar resultados interpretables.

Debe contener:
1. Exploración y preparación de datos (25%)
EDA con visualizaciones
Limpieza de datos (valores faltantes, outliers, codificación de variables)
Justificación de decisiones
2. Resultados y modelamiento (40%)
Implementación de los modelos propuestos en el Avance 1
Comparación de modelos si aplica
Métricas claras
Tablas y gráficos claros
Resultados coherentes con la metodología y con los tests del Avance 1
3. Discusión y conclusiones (35%)
Explicación de hallazgos
Relación con las hipótesis planteadas
Coherencia con la literatura
Posibles sesgos y limitaciones
Implicancias
Error común: mostrar gráficos sin interpretarlos.

Evaluación en este avance
Metodología aplicada (25%)
Resultados (40%)
Interpretación (35%)
CERTAMEN 2 (30%) — Entrega: 10 de noviembre
Entrega del paper y presentación

Objetivo
Consolidar todo el trabajo en un documento tipo paper científico, integrando las correcciones recibidas en los avances.

Debe contener:
1. Estructura (40%)
Formato tipo paper:

Resumen (abstract)
Introducción
Revisión de literatura
Metodología
Resultados
Discusión
Conclusiones
Referencias (formato APA)
2. Calidad del paper (60%)
Claridad en la redacción
Coherencia lógica entre pregunta, hipótesis, métodos y conclusiones
Uso adecuado de figuras y tablas (numeradas, con título y fuente)
Correcto reporte estadístico (estadístico, valor-p, tamaño del efecto)
Buen nivel técnico
Reproducibilidad: código o notebook adjunto
Formato de entrega
Extensión: 8–12 páginas (sin contar anexos)
Entrega vía Canvas en formato PDF, junto con el código o notebook utilizado
EXAMEN (30%) — Presentación: 17 de noviembre
Presentación del proyecto en un dashboard interactivo

Objetivo
Comunicar los resultados de la investigación mediante un dashboard interactivo que permita explorar los datos, las relaciones entre variables y los resultados de los modelos, defendiendo oralmente las conclusiones.

Debe contener:
1. Dashboard interactivo (50%)
Construido Streamlit, Plotly Dash, Shiny u otra herramienta equivalente. Debe incluir, como mínimo:

Portada / contexto: problema, pregunta de investigación e hipótesis
Exploración de datos: distribuciones y descriptivos con filtros interactivos (por ejemplo, región, año, grupo)
Relaciones entre variables: visualización de las correlaciones y comparaciones entre grupos, con los resultados de los tests estadísticos
Resultados del modelo: métricas, comparación de modelos y gráficos de desempeño
Conclusiones: hallazgos principales e implicancias
Criterios: interactividad real (filtros, selectores, tooltips), claridad visual, coherencia con el paper y correcta elección de gráficos.

2. Presentación oral (50%)
10–12 minutos por equipo, más preguntas. Debe cubrir:

Problema
Hipótesis
Datos
Metodología
Resultados
Conclusiones
Criterios: dominio del tema, capacidad de responder preguntas, uso del dashboard como apoyo (no lectura de diapositivas), participación de todos los integrantes y manejo del tiempo.

Formato de entrega
Enlace al dashboard publicado o archivo fuente (.pbix, .py, etc.) entregado vía Canvas antes de la presentación
Todos los integrantes deben participar en la exposición
Evaluación final incluye
Dashboard interactivo (50%)
Presentación oral (50%)
Coherencia global del proyecto
Escala de evaluación
Nivel	Descripción
Excelente	Claro, profundo, bien justificado, reproducible
Bueno	Correcto, con pequeñas debilidades
Suficiente	Cumple mínimamente
Insuficiente	Incompleto o incorrecto
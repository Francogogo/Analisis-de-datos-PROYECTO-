# Cobertura del informe en el dashboard

Cada `\caption{` de `paper/informe_v5.tex` (25, incluidos los `\captionof`: figuras y tablas, cuerpo y anexos) y cada `\includegraphics` con el elemento del dashboard que lo reproduce.
La primera columna parte con las cuatro primeras palabras del caption. Estado: cubierto, parcial o falta.

| Caption | Tipo | Pestaña | Elemento | Estado |
|---|---|---|---|---|
| Diagrama metodológico. | figura | Contexto | `_flujo` (salida `flujo`), cajas HTML/CSS en flecha | cubierto |
| Variables del estudio. | tabla | Contexto | `salida variables` (`_tabla` con `TEXTOS["vars"]`) | cubierto |
| Hipótesis de cada prueba. beta | tabla | Contexto | `_hipotesis` (tabla `TEXTOS["pruebas"]`, más H0a a H0d) | cubierto |
| Estadísticos descriptivos (n=968.098). | tabla | Exploración | salida `tabla` (`tabla_desc`), reactiva a los filtros | cubierto |
| Distribución de los días | figura | Exploración | `h_dias`, `h_ln`, `h_conc` (recorte a 60 días, ln(días), concentración) | cubierto |
| Resumen de las pruebas de | tabla | Relaciones | salida `pruebas` (`tabla_pruebas`): incluye las filas de normalidad y el tamaño del efecto con su magnitud | cubierto |
| Distribución de ln(días) por | figura | Relaciones | salida `grafico` (`fig_prueba`) con capítulo, establecimiento y sexo en el selector | cubierto |
| Modelos anidados M0 a M3 | tabla | Modelos | salida `tabla_modelos` y `graf_metrica` | cubierto |
| Coeficientes principales de M3 | tabla | Modelos | salida `tabla_coef` (EE clásico o HC3 con el selector `se`) | cubierto |
| Ranking de los factores según | tabla | Modelos | salida `tabla_ranking` y `graf_ranking`; recapitulado en Conclusiones (`_svg_ranking`) | cubierto |
| Contraste de las hipótesis por | tabla | Conclusiones | `filas_hipotesis` (salida `cuerpo`) | cubierto |
| Hipótesis, estadístico, valor-p, decisión | tabla | Relaciones | salida `pruebas` (`tabla_pruebas`, `filas_pruebas`): las 20 pruebas con variable, prueba, estadístico, gl, valor-p, efecto y decisión; las hipótesis nula y alternativa están en la ficha y en Contexto | cubierto |
| Histograma de la edad y | figura | Relaciones | `fig_normalidad` vía `grafico`: histograma de la variable y Q-Q de días, ln(días) y edad | cubierto |
| Distribución de ln(días) por tramo | figura | Relaciones | `fig_prueba` vía `grafico` para tramo de edad, región, cirugía, condición de egreso, nacionalidad y etnia | cubierto |
| Porcentaje de estadías prolongadas (más | figura | Relaciones | `fig_prueba` con respuesta "prolongada" (nueve factores en el selector) | cubierto |
| Tablas de contingencia de cada | tabla | Relaciones | salida `extra` (`tabla_contingencia`): categoría, No prolongada, Prolongada, Total y % prolongadas, un factor a la vez | cubierto |
| Coeficientes de M3 con error | tabla | Modelos | salida `tabla_coef` con "todos" los factores (los 42 coeficientes) y EE clásico o HC3 | cubierto |
| Cambio porcentual en la media | figura | Modelos | `graf_forest` (`fig_forest`), con IC 95 % y filtro por factor | cubierto |
| Residuos frente a valores ajustados | figura | Diagnósticos | `g_resid`, `g_hist`, `g_qq` | cubierto |
| Media observada de ln(días) por | figura | Diagnósticos | `g_edad` (`fig_edad`) | cubierto |
| Media geométrica ajustada y observada | figura | Diagnósticos | `g_decil` (`fig_deciles`) y `tabla_decil` | cubierto |
| Media de ln(días) observada y | tabla | Diagnósticos | salida `tabla_edad` (`html_edad`): ln(días) observado y ajustado por tramo y su media geométrica en días | cubierto |
| Especificaciones M3 a M6 en | tabla | Modelos | salida `tabla_espec` y `espec_texto` | cubierto |
| Selección forward por BIC | tabla | Modelos | salida `tabla_forward` | cubierto |
| V de Cramér entre las | figura | Relaciones | salida `cramer` (`matriz_cramer` y `graficos.calor`) con la nota `cramer_nota` | cubierto |

## Archivos de figura del informe

| Archivo | Tipo | Pestaña | Elemento | Estado |
|---|---|---|---|---|
| figs/avance2_distribucion.pdf | figura | Exploración | `h_dias`, `h_ln`, `h_conc` | cubierto |
| figs/avance2_bivariado.pdf | figura | Relaciones | salida `grafico` (`fig_prueba`) | cubierto |
| figs/avance2_cramer.pdf | figura | Relaciones | salida `cramer` (mapa de calor de la V de Cramér) | cubierto |
| figs/anexo_normalidad.pdf | figura | Relaciones | `fig_normalidad` vía `grafico` | cubierto |
| figs/anexo_cajas.pdf | figura | Relaciones | `fig_prueba` vía `grafico` | cubierto |
| figs/anexo_prolongadas.pdf | figura | Relaciones | `fig_prueba` con respuesta "prolongada" | cubierto |
| figs/forest.pdf | figura | Modelos | `graf_forest` (`fig_forest`) | cubierto |
| figs/avance2_residuos.pdf | figura | Diagnósticos | `g_resid`, `g_hist`, `g_qq` | cubierto |
| figs/avance2_edad.pdf | figura | Diagnósticos | `g_edad` (`fig_edad`) | cubierto |

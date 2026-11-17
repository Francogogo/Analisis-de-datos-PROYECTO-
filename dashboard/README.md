# Dashboard de estadías FONASA 2020

Aplicación Shiny para Python que reúne el contenido del informe (`paper/informe_v5.tex`) y agrega una simulación con el modelo M3. Tiene siete pestañas: Contexto, Exploración, Relaciones, Diagnósticos, Modelos, What if y Conclusiones. Los números salen de `datos_app/cifras.json` o se calculan desde la base; no se recalculan las pruebas del informe.

## Ejecutar en local

Desde la raíz del repositorio:

```
.venv/bin/shiny run dashboard/app.py
```

Las fórmulas usan MathJax incluido en `dashboard/www/mathjax/tex-svg.js` y los gráficos, plotly.js en `dashboard/www/plotly/plotly-cartesian.min.js`; no requiere conexión a internet.

## Rendimiento

- Los gráficos se envían como JSON de la figura (`render_plotly` y `salida` en `graficos.py`, dibujados por `www/js/graficos.js`). No se usa shinywidgets: cada widget mandaba por el websocket su propia copia de plotly.js, de unos 5 MB.
- plotly.js se carga una sola vez, fuera del camino crítico: cuando llega el primer gráfico o cuando el navegador queda libre tras el arranque. Es el bundle *cartesian* (bar, box, heatmap y scatter, entre otros), de la misma versión que el `plotly.min.js` de plotly.py. Si se actualiza plotly.py o se usa otro tipo de traza, hay que reemplazar el bundle; `tests/dashboard/test_rendimiento_y_activos.py` avisa si las versiones no coinciden.
- Las respuestas van comprimidas con gzip. Los archivos de `www/` se enlazan con `estatico()` (`app.py`), que agrega `?v=<huella del contenido>`. Esas URL y las de `lib/` de Shiny se cachean un año como inmutables; el resto se revalida.
- Las fuentes están en WOFF2. Subconjuntarlas ahorraba solo unos 25 KB, porque casi todo el peso está en los ejes variables, así que no se hizo.

## Regenerar los datos

Los archivos de `dashboard/datos_app/` se generan con:

```
.venv/bin/python dashboard/datos.py
```

Necesita `results/base_figuras.parquet` y `results/cifras_avance2_v8.json`, que produce el cuaderno `avance2_v8.ipynb`.

## Verificación

```
.venv/bin/python dashboard/verificar.py
.venv/bin/python -m pytest tests/dashboard -q
```

`verificar.py` revisa el vocabulario de los textos, que cada tabla y figura del informe tenga su fila en `COBERTURA.md`, que no haya imágenes estáticas y que las cifras sin filtro coincidan con las del informe. Sale con error si algo falla.

## Publicar en shinyapps.io

shinyapps.io acepta Python 3.12 (no 3.14), así que el despliegue usa un entorno aparte. Desde la raíz del repositorio:

```
python3.12 -m venv .venv312
.venv312/bin/pip install -r dashboard/requirements.txt rsconnect-python
.venv312/bin/rsconnect add --account <cuenta> --name <cuenta> --token <token> --secret <secreto>
.venv312/bin/rsconnect deploy shiny dashboard -p .venv312/bin/python --name <cuenta> --title dashboard-fonasa
```

La carpeta `dashboard/` es el paquete que se sube; `requirements.txt` lista las dependencias. Versión publicada: https://helix128.shinyapps.io/dashboard-fonasa/.

## Mapa de archivos

| Archivo | Contenido |
|---|---|
| `app.py` | Arma la página con las siete pestañas y el estilo. |
| `datos.py` | Carga y prepara la base, las cifras y el modelo M3. |
| `resumen.py` | Filtros, descriptivos, cajas, histogramas y concentración. |
| `modelo.py` | Días estimados e intervalos de M3 para un perfil. |
| `graficos.py` | Gráficos Plotly, formato de números y la salida de gráficos (`salida`, `render_plotly`, ver `www/js/graficos.js`). |
| `componente.py` | Contenedor de gráfico o tabla con botón "Detalles" que lo abre en un modal con su explicación (`www/js/componentes.js`). |
| `glosario.py` | Glosario único de términos (63). `www/js/glosario.js` los marca en el texto y en las fórmulas: tooltip al pasar el mouse y modal con la explicación completa al hacer click. |
| `p_contexto.py` | Pestaña Contexto. |
| `p_exploracion.py` | Pestaña Exploración. |
| `p_relaciones.py` | Pestaña Relaciones. |
| `p_diagnosticos.py` | Pestaña Diagnósticos. |
| `p_modelos.py` | Pestaña Modelos. |
| `p_whatif.py` | Pestaña What if. |
| `p_conclusiones.py` | Pestaña Conclusiones. |
| `verificar.py` | Verificaciones automáticas. |
| `COBERTURA.md` | Qué parte del informe cubre cada pestaña. |
| `datos_app/` | Datos que usa la aplicación. |

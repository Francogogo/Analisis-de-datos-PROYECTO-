# Estadías hospitalarias en FONASA, 2020

Proyecto de Análisis de Datos (IIP316W-1). Estudiamos qué factores clínicos, demográficos y del sistema de salud se asocian con la duración de la estadía en beneficiarios FONASA durante 2020.

El enfoque es analítico y estadístico: estimamos asociaciones ajustadas, intervalos y tamaños de efecto con la base completa. No hay partición entrenamiento/prueba ni objetivo predictivo, y las medidas de ajuste describen únicamente los datos analizados.

## Datos

Usamos los egresos hospitalarios abiertos del DEIS (`https://repositoriodeis.minsal.cl/DatosAbiertos/EGRESOS/`). En `data/raw/` están los años 2019 a 2024. El análisis toma los 968.098 egresos FONASA de 2020 con estadías de hasta un año. La base no trae peso GRD ni hospital, y la edad viene en tramos de 10 años.

## Cómo correrlo

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt jupyter
.venv/bin/jupyter nbconvert --to notebook --execute --inplace avance2_v8.ipynb
```

Hay que correrlo desde la raíz del repo. El notebook lee directo del zip en `data/raw/`, no hace falta descomprimir.

## Dashboard del examen

Publicado en https://helix128.shinyapps.io/dashboard-fonasa/. El código está en `dashboard/` (Shiny para Python): lleva a formato interactivo el contenido del informe y agrega la simulación what if sobre el modelo M3.

```bash
.venv/bin/pip install -r dashboard/requirements.txt
.venv/bin/shiny run dashboard/app.py
```

`dashboard/README.md` explica cómo regenerar los datos, verificar y publicar, y `dashboard/COBERTURA.md` indica dónde está cada figura y tabla del informe dentro del dashboard.

## Estructura

- `avance2_v8.ipynb`: notebook del análisis entregado en el Certamen 2. Escribe `results/cifras_avance2_v8.json`, que usan el informe y el dashboard.
- `paper/informe_v5.tex` y `paper/informe_v5.pdf`: informe del Certamen 2. Se compila desde `paper/` con `python3 gen_anexos.py` y tres pasadas de `xelatex informe_v5.tex`. `paper/figuras.py` genera las figuras de `paper/figs/`.
- `paper/informe*.tex` y `paper/paper.tex` (otras versiones): borradores anteriores del informe.
- `dashboard/`: dashboard del examen.
- `tests/dashboard/`: pruebas del dashboard (`.venv/bin/python -m pytest tests/dashboard -q`).
- `data/raw/`: egresos DEIS 2019 a 2024 y sus diccionarios.
- `pauta/`: pauta del proyecto y documento de temas, tal como se publicaron en Canvas.
- `versiones_anteriores/`: notebooks de los avances 1 y 2, incluido `avance2_v7.ipynb`.

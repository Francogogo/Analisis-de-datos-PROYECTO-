# Estadías hospitalarias en FONASA, 2020

Proyecto de Análisis de Datos (IIP316W-1). Estudiamos qué factores clínicos, demográficos y del sistema de salud se asocian con la duración de la estadía y con las hospitalizaciones prolongadas (más de 15 días) en beneficiarios FONASA durante 2020.

El enfoque es analítico y estadístico: estimamos asociaciones ajustadas, intervalos, razones de odds y tamaños de efecto con la base completa. No hay partición entrenamiento/prueba ni objetivo predictivo, y las medidas de ajuste describen únicamente los datos analizados.

## Datos

Usamos los egresos hospitalarios abiertos del DEIS (`https://repositoriodeis.minsal.cl/DatosAbiertos/EGRESOS/`). En `data/raw/` están los años 2019 a 2024. El análisis toma los 968.098 egresos FONASA de 2020 con estadías de hasta un año. La base no trae peso GRD ni hospital, y la edad viene en tramos de 10 años.

## Cómo correrlo

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt jupyter
.venv/bin/jupyter notebook avance2_v7.ipynb
```

Para ejecutarlo sin abrir la interfaz: `.venv/bin/jupyter nbconvert --to notebook --execute --inplace avance2_v7.ipynb`.

Hay que abrirlo desde la raíz del repo. El notebook lee directo del zip en `data/raw/`, no hace falta descomprimir. Tarda unos 7 minutos en ejecutarse completo.

## Archivos principales

- `avance2_v7.ipynb`: entregable vigente del **Avance 2** y notebook del paper. Reproduce las cifras, tablas y figuras del paper, incluidas las 20 pruebas de a pares del Avance 1 y los errores HC3. Incluye la exploración en 5 etapas, los modelos lineales anidados ($M_0 \to M_3$) con $\eta^2$ parcial, los coeficientes y su lectura como cambio porcentual en la media geométrica, la revisión de supuestos, la sensibilidad a la especificación, la regresión logística de la estadía prolongada, la selección forward de factores y la discusión con la literatura. Guarda las figuras en `paper/figs/` y las cifras en `results/cifras_avance2_v7.json`, y termina con una verificación contra el paper.
- `paper/paper.tex` y `paper/paper.pdf`: paper del proyecto, escrito sobre las cifras de `avance2_v7.ipynb`. `paper/figs/` tiene las figuras con tamaño de impresión. Se compila con `xelatex` (dos pasadas) desde `paper/`; usa TeX Gyre Pagella (texto y fórmulas) y Figtree (títulos).
- `versiones_anteriores/`: versiones previas de los avances 1 y 2, incluido el Avance 1 consolidado (`avance1_v5.ipynb`) y el Avance 2 con enfoque predictivo (`avance2_v5_final.ipynb`), que ya no es la referencia, y `avance2_v6.ipynb` (versión de Franco, base de v7).
- `detalles.md`: la pauta y rúbrica oficial del proyecto, tal como se publicó en Canvas.

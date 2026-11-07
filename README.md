# Hospitalizaciones prolongadas en FONASA

Proyecto de Análisis de Datos (IIP316W-1). Estudiamos qué factores clínicos, demográficos y del sistema de salud se asocian con las hospitalizaciones prolongadas en beneficiarios FONASA durante 2020.

## Datos

Usamos los egresos hospitalarios abiertos del DEIS (`https://repositoriodeis.minsal.cl/DatosAbiertos/EGRESOS/`). En `data/raw/` están los años 2019 a 2024. El análisis toma los 968.098 egresos FONASA de 2020 con estadías de hasta un año. La base no trae peso GRD ni hospital, y la edad viene en tramos de 10 años.

## Cómo correrlo

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt jupyter
.venv/bin/jupyter notebook avance2_v5_final.ipynb
```

Hay que abrirlo desde la raíz del repo. El notebook lee directo del zip en `data/raw/`, no hace falta descomprimir.

## Archivos principales

- `avance2_v5_final.ipynb`: entregable del **Avance 2**. Incluye el EDA en 5 etapas, los modelos anidados ($M_0 \to M_3$), la evaluación en test (R² ajustado = 0,198), el diagnóstico de los supuestos y el tamaño del efecto con η² parcial, una mejora del modelo con edad en tramos e interacciones ($M_4 \to M_6$, R² ajustado = 0,215), una regresión logística para la estadía prolongada (AUC = 0,770 en test) y la discusión con la literatura. Trabaja con 968.098 egresos. Con el diagnóstico, la edad y las demás variables controladas, la mediana de días es 69,7 % mayor en establecimientos del SNSS y 11,4 % mayor en hombres. Las figuras se generan en `figures/`.
- `versiones_anteriores/`: versiones previas de los avances 1 y 2.
- `avance1_v5.ipynb`: entregable consolidado del Avance 1 con la inferencia bivariada y selección por BIC.
- `detalles.md`: la pauta y rúbrica oficial del proyecto.

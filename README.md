# Hospitalizaciones prolongadas en FONASA

Proyecto de Análisis de Datos (IIP316W-1). Estudiamos qué factores se asocian a las hospitalizaciones largas en beneficiarios FONASA durante 2020.

## Datos

Usamos los egresos hospitalarios abiertos del DEIS (`https://repositoriodeis.minsal.cl/DatosAbiertos/EGRESOS/`). En `data/raw/` están los años 2019 a 2024. El análisis toma los 968.098 egresos FONASA de 2020 con estadías de hasta un año. La base no trae peso GRD ni hospital, y la edad viene en tramos de 10 años.

## Cómo correrlo

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt jupyter
.venv/bin/jupyter notebook avance1.ipynb
```

Hay que abrirlo desde la raíz del repo. El notebook lee directo del zip, no hace falta descomprimir.

## Archivos

- `avance1.ipynb`: el Avance 1, con sus figuras y resultados.
- `detalles.md`: la pauta del proyecto.
- `scripts/`: scripts de exploración.

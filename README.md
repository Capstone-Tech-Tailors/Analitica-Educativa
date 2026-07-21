# Analítica Educativa — Evaluaciones Docentes

Proyecto capstone del reto **Analítica Educativa** (Samsung Innovation Campus). El objetivo es
evolucionar el análisis de evaluaciones docentes de un sistema basado en reglas hacia uno
predictivo y accionable, incorporando **análisis de sentimiento** de los comentarios y un
**modelo de clasificación** de la tendencia de desempeño (`Mejora` / `Estable` / `En riesgo`).

## Estructura del proyecto

```
.
├── data/
│   ├── raw/            # dataset original de la universidad (evaluaciones_docentes.csv)
│   └── processed/      # datasets derivados (sentimiento, gold standard)
├── analisis_sentimientos/
│   └── notebooks/
│       ├── 01_catalogo_modelos_espanol.ipynb   # catálogo de modelos de sentimiento en español
│       └── 02_sentimiento_evaluaciones.ipynb   # pipeline: clasifica los comentarios → data/processed
├── analisis_datos/
│   ├── notebooks/
│   │   ├── 01_eda_techtailors_referencia.ipynb # EDA de referencia (de un compañero de equipo)
│   │   ├── 02_integracion_sentimiento_eda.ipynb# integra el sentimiento al EDA y revisa sus hallazgos
│   │   └── 03_modelado_tendencia_docente.ipynb # entrena, valida y exporta el modelo campeón
│   ├── reports/        # INFORME_Revision_EDA_TechTailors.md
│   └── models/         # artefactos del modelo (.pkl ignorado por git; se regenera al ejecutar)
├── src/                # código reutilizable (rutas.py, modelo_utils.py)
├── requirements.txt
└── .gitignore
```

## Puesta en marcha

```bash
python -m venv .venv && source .venv/bin/activate     # opcional
pip install -r requirements.txt
jupyter lab            # o abrir los notebooks en VS Code
```

Los notebooks localizan solos la raíz del proyecto (celda de arranque que añade `src/` al
path), así que **funcionan desde cualquier carpeta** mientras estén dentro del repositorio.

## Orden de ejecución

1. `analisis_sentimientos/notebooks/02_sentimiento_evaluaciones.ipynb` — clasifica el sentimiento
   de los comentarios (3 modelos en español + votación por mayoría + *gold standard* validado a
   mano) y escribe los CSV en `data/processed/`.
2. `analisis_datos/notebooks/02_integracion_sentimiento_eda.ipynb` — integra ese sentimiento al
   análisis de datos y contrasta los hallazgos del EDA de referencia.
3. `analisis_datos/notebooks/03_modelado_tendencia_docente.ipynb` — compara candidatos (regla,
   logística, RandomForest, Gradient Boosting), valida (partición + temporal), calibra y
   **exporta el modelo** a `analisis_datos/models/`.

`analisis_sentimientos/notebooks/01_catalogo_modelos_espanol.ipynb` y
`analisis_datos/notebooks/01_eda_techtailors_referencia.ipynb` son material de referencia/apoyo.

## Sobre los datos

Dataset entregado por la universidad, **anonimizado / plantillado**: 3.000 evaluaciones de 50
docentes en 7 asignaturas y 8 semestres (2020–2023). El campo `comentario` usa **20 plantillas**
repetidas (no texto libre), y la etiqueta `tendencia_desempeno` está derivada por reglas. Esto
acota lo que el análisis de sentimiento del texto puede aportar y hace que las métricas de
modelado sean un **techo** más que un resultado extrapolable a datos reales (ver el informe en
`analisis_datos/reports/`). No cambia la validez de la metodología.

## Créditos

- Pipeline de sentimiento, integración, modelado e informe de revisión: trabajo de este repositorio.
- `01_eda_techtailors_referencia.ipynb`: EDA elaborado por un compañero del equipo Tech Tailors;
  se incluye como referencia para comparación y solo se ajustó la ruta de carga de datos.

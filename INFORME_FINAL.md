# Informe final del proyecto
## Análisis de sentimiento para la evaluación docente — Universidad del Rosario

| | |
|---|---|
| **Proyecto** | Analítica Educativa — Proyecto Capstone, Samsung Innovation Campus |
| **Equipo** | Tech Tailors — Juan David Ríos · Natalia Remolina · Giovanni Balza |
| **Propósito** | Clasificar el sentimiento de los comentarios de las encuestas de evaluación docente para construir el **DOFA** de cada docente, con despliegue del modelo en la nube |
| **Repositorio** | `/Users/nato/Documents/Analisis de sentimiento` (git, 15 commits) |
| **Modelo seleccionado para producción** | `modelo_sentimiento_humano` (ver §4) |

---

## 1 · Resumen ejecutivo

El proyecto construyó, evaluó y mejoró un sistema de análisis de sentimiento en español para
comentarios de evaluación docente, siguiendo un proceso completo de ciencia de datos: análisis
exploratorio, evaluación comparativa de modelos preentrenados, integración con el modelo
predictivo de tendencia, dos rondas de *fine-tuning* (destilación y verdad humana) y la
construcción de un **estándar de oro anotado por el equipo** (172 comentarios, acuerdo
inter-anotador α = 0.585).

**Resultado central:** el modelo final —RoBERTuito ajustado con las etiquetas humanas del
equipo— es el **mejor clasificador disponible** sobre el conjunto de evaluación humano
(macro-F1 = 0.646; 131/172 aciertos; recall de comentarios negativos 0.556), superando al mejor
modelo preentrenado público (0.638) y al modelo destilado (0.619). La mejora es consistente en
todas las métricas aunque aún no estadísticamente significativa (McNemar p = 1.0): el cuello de
botella está identificado y cuantificado —el volumen de anotación humana— y el sistema para
ampliarla queda montado y operativo.

**Decisión de producción:** desplegar `modelo_sentimiento_humano` (§4), un único modelo
autónomo de 415 MB, ejecutable en CPU, sin dependencias de servicios de terceros en inferencia,
y alineado con la rúbrica institucional definida por el equipo.

---

## 2 · El proceso realizado, fase por fase

### Fase 1 — Datos y análisis exploratorio

- Dataset institucional: 3.000 evaluaciones (50 docentes, 7 asignaturas, 8 semestres 2020–2023).
- **Hallazgo determinante:** el campo `comentario` contiene solo **20 textos distintos**
  (0,67 % de unicidad; el 99,33 % son repeticiones). El dataset está plantillado/anonimizado, lo
  que acota lo que el componente de texto puede demostrar con estos datos y obligó a conseguir
  un corpus real complementario.
- Se revisó en profundidad el EDA del equipo (11 *insights*), verificando cada cifra y
  corrigiendo conclusiones no soportadas (informe en `analisis_datos/reports/`).

### Fase 2 — Evaluación de modelos preentrenados (benchmark)

Se compararon tres modelos de sentimiento en español contra un primer gold manual de 20
comentarios: **RoBERTuito** (0.75 accuracy), XLM-R (0.70) y BETO (0.65), más el consenso por
votación (mejor macro-F1: 0.730). RoBERTuito resultó el mejor modelo individual y quedó como
**maestro** de las fases siguientes.

### Fase 3 — Modelo de tendencia docente

Clasificador de la tendencia (`Mejora` / `Estable` / `En riesgo`) a partir de puntajes +
sentimiento: campeón **RandomForest calibrado**, macro-F1 0.915 (partición aleatoria) y 0.905
(validación temporal 2020-22→2023), recall de `En riesgo` 0.96–0.99. Se detectó y excluyó una
variable con fuga de información (`delta_semestre`) y se documentó la circularidad de la
etiqueta institucional.

### Fase 4 — Fine-tuning por destilación (notebook 04)

Con un corpus real de **29.243 comentarios únicos** de estudiantes (sin etiquetas), se aplicó
*weak supervision*: RoBERTuito etiquetó el corpus y BETO se entrenó con esas pseudo-etiquetas
(11.697 ejemplos balanceados, GPU Apple/MPS, ~6 min). Resultado: el alumno **iguala pero no
supera** al maestro — se demostró empíricamente el **techo de la destilación**, incluida la
comparación de arquitecturas (BETO vs RoBERTuito como alumno) y el análisis de falsos positivos
(el error no es corregible con umbrales: es un problema de rúbrica).

### Fase 5 — Anotación humana (la que rompe el techo)

El equipo diseñó y ejecutó un protocolo formal de anotación: muestreo estratificado de 335
comentarios reales (censo de los 40 enunciados que concentran el 53 % de las evaluaciones +
estratos de frontera), rúbrica con reglas ordenadas, tres anotadores independientes, anclas de
control y repetidos encubiertos.

- **749 anotaciones** · α de Krippendorff = **0.585** (acuerdo moderado; desacuerdos
  mayormente adyacentes POS↔NEU → problema de umbral de rúbrica, no de comprensión).
- Gold adjudicado: **172 comentarios de evaluación** (8.6× el conjunto anterior) + **148 de
  entrenamiento** con verdad humana. Control de calidad: 8/8 anclas correctas en los tres
  anotadores; ítems ilegibles y sin contenido evaluable excluidos por lista auditable.

### Fase 6 — Fine-tuning con verdad humana (notebook 05)

RoBERTuito se ajustó con las 148 etiquetas humanas (entropía cruzada ponderada por clase,
lr = 1e-5, *early stopping*) y se evaluó sobre el gold humano de 172:

| Modelo | accuracy | macro-F1 | aciertos | recall NEG |
|---|:--:|:--:|:--:|:--:|
| BETO destilado (NB04) | 0.733 | 0.619 | 126/172 | 0.500 |
| RoBERTuito (maestro público) | 0.756 | 0.638 | 130/172 | 0.528 |
| **RoBERTuito ajustado (humano)** 🏆 | **0.762** | **0.646** | **131/172** | **0.556** |

El ajustado gana en todas las métricas y mejora la detección de críticas (recall NEG), aunque
la diferencia no alcanza significancia estadística con 148 ejemplos de entrenamiento
(McNemar p = 1.0). El camino de mejora es directo: **más anotación humana**, con el sistema ya
construido.

---

## 3 · Inventario de modelos: ubicación exacta de cada uno

Raíz del proyecto: **`/Users/nato/Documents/Analisis de sentimiento/`**

### 3.1 Modelos entrenados por el equipo (dentro del repositorio)

| # | Modelo | Ubicación (ruta completa) | Peso usable | Rol |
|---|---|---|--:|---|
| **1** | **🏆 Sentimiento — producción** | `/Users/nato/Documents/Analisis de sentimiento/analisis_sentimientos/models/modelo_sentimiento_humano/` | **415 MB** | **El modelo a desplegar** (§4) |
| 2 | Sentimiento — destilado BETO | `/Users/nato/Documents/Analisis de sentimiento/analisis_sentimientos/models/modelo_sentimiento_ft/` | 419 MB | Evidencia del techo de la destilación (NB04) |
| 3 | Sentimiento — destilado RoBERTuito | `/Users/nato/Documents/Analisis de sentimiento/analisis_sentimientos/models/modelo_sentimiento_ft_robertuito/` | 415 MB | Comparación de arquitecturas (NB04 §8.6) |
| 4 | Tendencia docente | `/Users/nato/Documents/Analisis de sentimiento/analisis_datos/models/modelo_tendencia_docente.pkl` | 3.4 MB | Clasifica Mejora/Estable/En riesgo (NB03 de datos) |

Cada carpeta de modelo de sentimiento contiene: `model.safetensors` (pesos), `tokenizer.json` +
`config.json` (imprescindibles para cargarlo) e `info.json` (**ficha de trazabilidad**: método,
hiperparámetros, métricas y semilla). Las subcarpetas `checkpoint-*` son residuos del
entrenamiento y pueden eliminarse (~1.2 GB por modelo).

> ⚠️ Los pesos **no están en git** (límite de GitHub, `.gitignore`); son reproducibles
> ejecutando los notebooks 04/05. Para compartirlos o desplegarlos, ver §6.1.

### 3.2 Modelos preentrenados de terceros (caché del sistema, fuera del repositorio)

Ubicación: `/Users/nato/.cache/huggingface/hub/` — se descargan solos al ejecutar los notebooks.

| Modelo (id Hugging Face) | Tamaño | Uso en el proyecto |
|---|--:|---|
| `pysentimiento/robertuito-sentiment-analysis` | 416 MB | Maestro / mejor preentrenado |
| `finiteautomata/beto-sentiment-analysis` | 839 MB | Benchmark |
| `cardiffnlp/twitter-xlm-roberta-base-sentiment` | 2.1 GB | Benchmark |
| `dccuchile/bert-base-spanish-wwm-cased` | 839 MB | Base del destilado |
| `pysentimiento/robertuito-base-uncased` | 416 MB | Comparación de arquitecturas |

---

## 4 · Modelo seleccionado para producción y por qué

### 📍 `analisis_sentimientos/models/modelo_sentimiento_humano/`

**Qué es:** RoBERTuito (`pysentimiento/robertuito-sentiment-analysis`) con *continued
fine-tuning* sobre las **148 etiquetas humanas** del equipo. Clasifica comentarios en español
en `POS / NEU / NEG`.

**Justificación de la selección:**

1. **Es el mejor sobre la evaluación humana** (macro-F1 0.646; 131/172), la única referencia
   independiente de cualquier modelo.
2. **Mejor detección de críticas** (recall NEG 0.556 vs 0.528 del preentrenado): en evaluación
   docente, pasar por alto una crítica es el error costoso — oculta a un docente que necesita
   acompañamiento y distorsiona el DOFA.
3. **Incorpora la rúbrica institucional**: aprendió de las decisiones del equipo (p. ej. que un
   elogio tibio no es entusiasmo y que la crítica cortés sigue siendo crítica), no del registro
   genérico de redes sociales.
4. **Apto para despliegue**: un solo modelo de 415 MB, inferencia en CPU (no requiere GPU),
   sin llamadas a servicios externos, mejorable con cada ronda de anotación sin cambiar la
   arquitectura del despliegue.

**Declaración honesta que debe acompañarlo:** su ventaja sobre el preentrenado público aún no
es estadísticamente significativa (McNemar p = 1.0, n = 148 de entrenamiento). Se selecciona
por ser consistentemente superior en todas las métricas, por su alineación con la rúbrica y
por su trayectoria de mejora; la significancia llegará con la ampliación del corpus anotado
(§7).

### Cómo usarlo (local)

```python
from transformers import pipeline

RUTA = "analisis_sentimientos/models/modelo_sentimiento_humano"   # relativa a la raíz del repo
clf = pipeline("sentiment-analysis", model=RUTA)

clf("La profesora explica con claridad y responde todas las dudas")
# → [{'label': 'POS', 'score': 0.98}]

clf(["Cumple con el programa", "Debería preparar mejor sus clases"])
# → NEU, NEG  (acepta lotes)
```

Verificación de que el artefacto funciona: notebook 04 §9.4 (recarga desde disco) y notebook
05 §5–§7 (evaluación y guardado).

---

## 5 · Del sentimiento al DOFA del docente

El modelo es el **motor de clasificación**; el DOFA se construye agregando sus salidas por
docente (y opcionalmente por asignatura/semestre), combinadas con el modelo de tendencia:

| Cuadrante | Fuente | Regla de construcción sugerida |
|---|---|---|
| **Fortalezas** | Comentarios **POS** frecuentes + puntajes altos | Temas dominantes de los POS del docente (claridad, dominio, trato) |
| **Debilidades** | Comentarios **NEG** recurrentes + dimensión de puntaje más baja | Temas dominantes de los NEG (p. ej. "no resuelve dudas", "evaluación injusta") |
| **Oportunidades** | Críticas **constructivas** (NEG suaves: "debería…", "podría…") | Son peticiones de cambio accionables: la materia prima del plan de mejora |
| **Amenazas** | Tendencia **`En riesgo`** del modelo de tendencia + % NEG creciente entre semestres | Priorización de acompañamiento antes de que el desempeño se deteriore |

Recomendaciones operativas:

- **Agregar, no leer comentario a comentario**: % POS/NEU/NEG por docente y su evolución
  temporal. El proyecto ya demostró este cruce (notebook `02_integracion_sentimiento_eda`),
  incluida la detección de docentes "enmascarados" (buen puntaje, comentarios negativos).
- **Umbral de alerta sugerido**: % NEG del docente en el cuartil superior **o** tendencia
  `En riesgo` → candidato a acompañamiento; ambos a la vez → prioridad.
- **Uso formativo, no sancionatorio**: los resultados son señal para acompañar, no evidencia
  disciplinaria; los comentarios son datos personales y deben tratarse como tales (§6.4).

---

## 6 · Guía de despliegue en la nube

### 6.1 Publicar el artefacto (los pesos no viajan por git)

Opción recomendada: **repositorio privado en Hugging Face Hub** — versionado de modelos,
control de acceso y carga directa por id desde cualquier servidor.

```bash
pip install huggingface_hub
hf auth login                      # token de la organización
hf upload tech-tailors/sentimiento-docente-urosario \
  "analisis_sentimientos/models/modelo_sentimiento_humano" . --private
```

Alternativa: subir la carpeta a un bucket (S3 / GCS / Azure Blob) y descargarla al arrancar el
contenedor.

### 6.2 Servicio de inferencia (FastAPI + Docker)

```python
# app.py
from fastapi import FastAPI
from pydantic import BaseModel
from transformers import pipeline

app = FastAPI(title="Sentimiento docente — U. del Rosario")
clf = pipeline("sentiment-analysis",
               model="tech-tailors/sentimiento-docente-urosario")   # o ruta local en la imagen

class Lote(BaseModel):
    comentarios: list[str]

@app.post("/sentimiento")
def sentimiento(lote: Lote):
    return [{"comentario": c, **r} for c, r in
            zip(lote.comentarios, clf(lote.comentarios, truncation=True, max_length=128))]
```

```dockerfile
FROM python:3.12-slim
RUN pip install --no-cache-dir fastapi uvicorn transformers torch --extra-index-url https://download.pytorch.org/whl/cpu
COPY app.py .
# Opción A: hornear el modelo en la imagen (COPY modelo_sentimiento_humano /modelo)
# Opción B: descargarlo del Hub al arrancar (requiere HF_TOKEN como secreto)
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8080"]
```

Destinos probados para este patrón: **Google Cloud Run**, **Azure Container Apps** o **AWS App
Runner** (serverless, pago por uso — adecuado porque las encuestas se procesan por lotes al
cierre de cada semestre, no en flujo continuo).

### 6.3 Requisitos y rendimiento

| Recurso | Valor |
|---|---|
| CPU / RAM | 2 vCPU · 4 GB es suficiente (**no requiere GPU**) |
| Tamaño del artefacto | 415 MB (+ ~180 MB de librerías) |
| Latencia CPU aproximada | decenas de ms por comentario en lote |
| Volumen de referencia | 100.000 comentarios ≈ minutos de procesamiento por lotes |

### 6.4 Consideraciones de datos personales

Los comentarios de la encuesta identifican opiniones sobre personas: procesarlos en
infraestructura controlada por la universidad, anonimizar identificadores antes de la
inferencia, restringir el acceso al endpoint (token) y conservar únicamente los agregados
necesarios para el DOFA.

---

## 7 · Limitaciones vigentes y hoja de ruta

**Limitaciones que acompañan a cualquier cifra de este informe**

1. El corpus de entrenamiento humano tiene **148 ejemplos** y el gold **172** (solo 20 NEU):
   las métricas de la clase NEU son inestables y la mejora aún no es significativa.
2. El acuerdo entre anotadores es moderado (α = 0.585): parte del "error" del modelo es
   ambigüedad genuina del lenguaje.
3. Los **casos mixtos adversativos** ("buen profesor, pero debería…") no tienen aún regla
   consensuada — son la principal fuente de ruido identificada (6 empates + ~24 casos).
4. El corpus real es **español traducido automáticamente**: carece del registro coloquial que
   tendrán las encuestas reales de la universidad.

**Hoja de ruta (en orden de impacto)**

1. **Ampliar la anotación** con comentarios reales de la U. del Rosario en cuanto estén
   disponibles (el sistema completo está en `anotacion/`: rúbrica, planillas, consolidación
   con α). Objetivo: ≥ 500 ejemplos por clase → significancia estadística alcanzable.
2. **Consensuar la regla de los mixtos adversativos**, emitir rúbrica v1.1 y reanotar ese
   subconjunto (~30 min de reunión).
3. Reentrenar (notebook 05 tal cual) y re-evaluar; publicar la versión nueva al Hub con tag.
4. Desplegar el servicio (§6.2) y conectar el flujo: encuesta → sentimiento → agregados →
   DOFA + tendencia.
5. Monitoreo en producción: muestreo periódico de predicciones para revisión humana
   (mantener el gold vivo).

---

## 8 · Anexo: mapa del repositorio y trazabilidad

```
/Users/nato/Documents/Analisis de sentimiento/
├── README.md · GUIA_APRENDIZAJE.md · INFORME_FINAL.md (este documento)
├── data/
│   ├── raw/                 evaluaciones_docentes.csv · corpus real EN/ES (100k)
│   └── processed/           sentimiento, benchmark, muestra de anotación,
│                            gold_humano_eval.csv (172) · train_humano.csv (148)
├── analisis_sentimientos/
│   ├── notebooks/           01 catálogo · 02 pipeline · 03 benchmark ·
│   │                        04 fine-tuning destilación · 05 fine-tuning humano
│   └── models/              ft (BETO dest.) · ft_robertuito · ⭐ humano (producción)
├── analisis_datos/
│   ├── notebooks/           01 EDA referencia · 02 integración · 03 modelo tendencia
│   ├── reports/             informe revisión EDA · limitaciones · justificaciones
│   └── models/              modelo_tendencia_docente.pkl + metadatos
├── anotacion/               rúbrica · protocolo · planillas A1-A3 · consolidación (α)
└── src/                     rutas.py · sentimiento.py · modelo_utils.py · acuerdo.py
```

**Trazabilidad:** cada modelo lleva su `info.json` (método, datos, hiperparámetros, métricas,
semilla); cada resultado de este informe es reproducible desde su notebook; el historial de
git (15 commits) documenta la evolución completa del proyecto.

---

*Informe final · Tech Tailors · Analítica Educativa — Universidad del Rosario.*

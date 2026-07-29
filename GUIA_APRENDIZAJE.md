# Guía de aprendizaje del proyecto

> **Propósito.** Este documento explica, en lenguaje accesible, qué se hizo en el proyecto, por
> qué se tomó cada decisión y qué conceptos hay detrás. Está dirigido a integrantes del equipo que
> deseen comprender el trabajo en profundidad o retomarlo, y sirve como preparación para exponer
> el proyecto ante un jurado técnico.
>
> Los detalles formales (fórmulas, hiperparámetros, métricas) están en los notebooks; aquí se
> explica **el razonamiento**.

## Contenido

1. [Visión general: qué construimos](#1-visión-general-qué-construimos)
2. [El hallazgo que condicionó todo el proyecto](#2-el-hallazgo-que-condicionó-todo-el-proyecto)
3. [Etapa 1 · Análisis de sentimiento](#3-etapa-1--análisis-de-sentimiento)
4. [Etapa 2 · Modelado de la tendencia](#4-etapa-2--modelado-de-la-tendencia)
5. [Etapa 3 · Fine-tuning](#5-etapa-3--fine-tuning)
6. [Conceptos clave explicados](#6-conceptos-clave-explicados)
7. [Decisiones metodológicas y su justificación](#7-decisiones-metodológicas-y-su-justificación)
8. [Preguntas frecuentes](#8-preguntas-frecuentes)
9. [Cómo continuar el proyecto](#9-cómo-continuar-el-proyecto)

---

## 1. Visión general: qué construimos

El reto pedía evolucionar la evaluación docente **de un sistema de reglas a uno predictivo**. El
proyecto se organizó como una cadena de cuatro etapas:

```
   Datos              Sentimiento           Integración          Modelo
evaluaciones  →   clasificar comentarios  →  ¿aporta el     →  predecir la
  docentes         (modelos en español)       texto señal?      tendencia
```

A cada etapa corresponde uno o varios notebooks:

| Etapa | Notebook | Pregunta que responde |
|---|---|---|
| Exploración | `analisis_datos/01_eda_techtailors_referencia` | ¿Cómo son los datos? |
| Sentimiento | `analisis_sentimientos/02_sentimiento_evaluaciones` | ¿Qué opinan los estudiantes? |
| Selección de modelo | `analisis_sentimientos/03_benchmark_modelos` | ¿Qué modelo de sentimiento es mejor? |
| Integración | `analisis_datos/02_integracion_sentimiento_eda` | ¿El texto aporta información útil? |
| Modelado | `analisis_datos/03_modelado_tendencia_docente` | ¿Podemos predecir la tendencia? |
| Fine-tuning | `analisis_sentimientos/04_finetuning_sentimiento` | ¿Podemos entrenar un modelo propio? |

---

## 2. El hallazgo que condicionó todo el proyecto

Al explorar el dataset encontramos algo determinante: el archivo tiene **3.000 filas, pero solo
20 comentarios distintos**. Cada frase se repite en promedio 150 veces.

| Métrica | Valor |
|---|---|
| Filas | 3.000 |
| Comentarios **distintos** | 20 (0,67 %) |
| Filas que son repetición | 99,33 % |

**Por qué importa.** Para evaluar un modelo de sentimiento cuentan los **textos distintos**:
darle 165 veces la misma frase produce 165 veces la misma respuesta. Es decir, el conjunto real
de evaluación del texto es de **20 elementos**, no de 3.000.

**Qué implicó.** Que el componente de texto no puede demostrar su valor con estos datos, y que
las métricas deben presentarse como *orientativas*. Reconocerlo y documentarlo —en lugar de
presentar cifras infladas— es parte del rigor del proyecto.

📄 Documentado en: `analisis_datos/reports/justificacion_comentarios_repetidos.md` y
`seccion_naturaleza_limitaciones_datos.md`.

---

## 3. Etapa 1 · Análisis de sentimiento

### Qué se hizo

Se clasificó cada comentario en **positivo / neutro / negativo** usando tres modelos de lenguaje
en español, y se combinaron por **votación por mayoría**.

| Modelo | Origen |
|---|---|
| RoBERTuito | Entrenado con ~500 millones de tuits en español |
| BETO | BERT entrenado con ~3.000 millones de palabras en español |
| XLM-R (Twitter) | Multilingüe: 100 idiomas + tuits |

### Cómo se eligió el mejor

No basta con usar un modelo: hay que **medir**. Para ello se construyó un *gold standard*
—etiquetado manual de los 20 comentarios según una rúbrica escrita— y se midió cada modelo
contra él:

| Modelo | Accuracy | macro-F1 | En comentarios claros |
|---|:--:|:--:|:--:|
| **RoBERTuito** | 0,75 | 0,706 | **0,94** |
| XLM-R | 0,70 | 0,664 | 0,75 |
| BETO | 0,65 | 0,626 | 0,69 |
| Consenso | 0,75 | **0,730** | 0,81 |

**Conclusión:** RoBERTuito es el mejor modelo individual; el consenso de los tres obtiene el
mejor macro-F1 global.

### Dónde están los errores

Todos los modelos fallan en los **mismos cuatro comentarios fronterizos**: elogios tibios
("La clase estuvo bien"), críticas constructivas ("Se podría mejorar el material") y comentarios
mixtos ("Asistencia puntual, pero falta dinamismo"). Los comentarios claros se clasifican casi
perfectamente.

Esto es informativo: **la dificultad no está en el modelo, está en la ambigüedad del lenguaje**.
Dos personas razonables etiquetarían esos casos de forma distinta.

📄 Notebooks `02_sentimiento_evaluaciones` y `03_benchmark_modelos`.

---

## 4. Etapa 2 · Modelado de la tendencia

### Qué se hizo

Se entrenó un clasificador que predice `Mejora` / `Estable` / `En riesgo` a partir de los
puntajes numéricos y del sentimiento del comentario. Se compararon cinco enfoques (desde una
regla de dos umbrales hasta Gradient Boosting) y ganó **RandomForest** con calibración de
probabilidades.

| Métrica | Partición aleatoria | Validación temporal (2023) |
|---|:--:|:--:|
| macro-F1 | 0,915 | 0,905 |
| Recall de `En riesgo` | 0,96 | 0,99 |

### Las dos decisiones importantes

**1. Se excluyeron variables con fuga de información.** La variable `delta_semestre` parecía
predictiva, pero incorporaba información del semestre que se estaba clasificando: el modelo
"veía la respuesta". Detectarlo y excluirlo evita un resultado engañoso.

**2. Se validó también en el tiempo.** Además de la partición aleatoria, se entrenó con
2020–2022 y se probó con 2023. Que ambos resultados coincidan indica que el desempeño no era
optimista por mezclar semestres.

### La conclusión incómoda pero honesta

La ventaja del modelo sobre una simple regla de dos umbrales **no es estadísticamente
significativa** (0,915 frente a 0,910; prueba de McNemar p = 0,28). La razón: la etiqueta
`tendencia_desempeno` se generó por reglas a partir de los puntajes, de modo que existe
**circularidad** entre la etiqueta y las variables predictoras. Las métricas son un **techo
artificial** de este dataset, no una medida del valor del ML.

📄 Notebook `03_modelado_tendencia_docente` e informe `INFORME_Revision_EDA_TechTailors.md`.

---

## 5. Etapa 3 · Fine-tuning

### La distinción fundamental

| | Qué es | Dónde se hizo |
|---|---|---|
| **Usar un modelo** (inferencia) | Pedirle predicciones a un modelo ya entrenado | Notebooks 01–03 |
| **Fine-tuning** | Modificar los pesos del modelo entrenándolo con datos propios | Notebook 04 |

Hasta el notebook 03 **no se entrenó ningún modelo de sentimiento**: se aprovechó el trabajo de
sus autores. Eso es correcto y es la práctica recomendada cuando no hay datos etiquetados
suficientes. El notebook 04 es el primero donde se entrena.

### El obstáculo y la solución

El fine-tuning requiere pares `(texto, etiqueta)`. Se consiguió un corpus de **29.243 comentarios
reales únicos**, pero **sin etiquetas de sentimiento**. Se aplicó **destilación de conocimiento**:

```
RoBERTuito (maestro)  →  etiqueta los 29.243 comentarios  →  BETO (alumno) aprende de esas etiquetas
```

### El resultado y su lectura

| Modelo | macro-F1 (vs etiquetas humanas) |
|---|:--:|
| BETO sin ajustar | 0,626 |
| **BETO ajustado** | **0,708** |
| RoBERTuito (maestro) | 0,706 |

- ✅ **El fine-tuning mejoró el modelo base** en 0,082 puntos: el modelo se especializó.
- ⚖️ **Igualó al maestro sin superarlo** (diferencia de 0,002 = empate técnico).

Esto **confirma la teoría**: un alumno entrenado con las etiquetas de un maestro hereda su techo
de calidad. Al ampliar el corpus mejoró la *fidelidad* de la imitación (0,870 → 0,899), no la
calidad absoluta.

### El análisis de falsos positivos

Se investigó si podían eliminarse los falsos positivos (comentarios tibios clasificados como
positivos, el error costoso en este dominio) exigiendo mayor confianza para la clase POS.
**Conclusión: no es viable.** El falso positivo se predice con 99,7 % de confianza —más que
varios aciertos reales—, de modo que cualquier umbral que lo elimine destruye también los
verdaderos positivos. El error no proviene de incertidumbre, sino de la **frontera POS/NEU
heredada del maestro**.

La vía efectiva es **anotación humana de casos fronterizos**, no ajuste de umbrales.

📄 Notebook `04_finetuning_sentimiento`, secciones 8 y 8.5.

---

## 6. Conceptos clave explicados

### Transfer learning (aprendizaje por transferencia)

Un modelo de lenguaje se construye en dos fases:

1. **Preentrenamiento** — lee millones de textos y aprende *el idioma*. Costosísimo; lo hacen
   universidades y empresas. *Analogía: una persona que ya sabe español.*
2. **Fine-tuning** — se le enseña *la tarea* concreta con ejemplos etiquetados. *Analogía: un
   curso corto de "clasificar opiniones".*

Transferir el conocimiento de la fase 1 es lo que permite entrenar con miles de ejemplos en lugar
de millones.

### Los tres conjuntos de datos

| Conjunto | Proporción | Para qué sirve |
|---|:--:|---|
| Entrenamiento | 70 % | El modelo ajusta sus pesos con él |
| Validación | 15 % | Vigilar el aprendizaje y decidir cuándo parar |
| Prueba | 15 % | Medición final; se usa **una sola vez** |

**Por qué tres y no dos:** como la validación guía decisiones (qué época conservar), el
desempeño sobre ella queda optimista. Solo un conjunto nunca usado para decidir da una
estimación honesta.

### Sobreajuste (*overfitting*)

El modelo **memoriza** el entrenamiento en vez de aprender patrones generalizables. Se detecta
cuando la pérdida de entrenamiento sigue bajando pero la de validación empieza a subir. Se
combate con pocas épocas, regularización y *early stopping*.

### macro-F1 y por qué no accuracy

El **accuracy** engaña cuando las clases están desbalanceadas: si el 70 % de los comentarios son
positivos, un modelo que responda siempre "positivo" acierta el 70 % sin haber aprendido nada.
El **macro-F1** promedia el desempeño de las tres clases con el mismo peso, de modo que ignorar
una clase penaliza la métrica.

### Destilación de conocimiento

Entrenar un modelo *alumno* para que reproduzca las salidas de un modelo *maestro*. Es útil
cuando no hay etiquetas humanas, pero tiene un límite: **el alumno hereda los errores del
maestro y no puede superarlo sistemáticamente**.

### Tasa de aprendizaje baja en fine-tuning

Se usa un valor pequeño (2e-5) porque el modelo **ya sabe algo valioso** (el idioma). Una tasa
alta destruiría ese conocimiento previo —fenómeno llamado *catastrophic forgetting*—.

---

## 7. Decisiones metodológicas y su justificación

| Decisión | Alternativa descartada | Justificación |
|---|---|---|
| Usar modelos preentrenados (no entrenar desde cero) | Entrenar un modelo propio desde cero | Se requerirían millones de textos; con transfer learning bastan miles |
| Votación por mayoría entre 3 modelos | Confiar en un solo modelo | Reduce el efecto de errores individuales; mejora el macro-F1 |
| *Gold standard* independiente de los modelos | Usar el consenso como referencia | Evita circularidad: no se puede elegir el mejor modelo con una referencia derivada de los propios modelos |
| Deduplicar el corpus de entrenamiento | Entrenar con las 100.000 filas | Los duplicados sesgan el modelo y provocan fuga entre particiones |
| Balancear las clases | Entrenar con la distribución original (69 % positivos) | Evita que el modelo aprenda a responder siempre la clase mayoritaria |
| Validación temporal además de aleatoria | Solo partición aleatoria | La partición aleatoria mezcla semestres del mismo docente y puede ser optimista |
| Excluir `delta_semestre` | Conservarla por ser "significativa" | Contenía fuga de información del presente |
| Documentar las limitaciones del dataset | Presentar solo las métricas favorables | Las métricas son un techo artificial; ocultarlo invalidaría las conclusiones |

---

## 8. Preguntas frecuentes

**¿Por qué no se entrenó un modelo con los 20 comentarios del dataset?**
Un transformer necesita cientos o miles de ejemplos variados. Con 20 frases el modelo las
memorizaría sin aprender nada generalizable.

**¿Los resultados sirven si el dataset está plantillado?**
Sirven para **validar la metodología**, no como medida de desempeño en producción. La
distinción está documentada en todos los entregables.

**¿Cuál modelo debería usar la institución?**
RoBERTuito o el consenso de los tres. El modelo ajustado (notebook 04) aporta autonomía —un solo
modelo, menor latencia— con calidad equivalente, no superior.

**¿Por qué el modelo ajustado no superó a RoBERTuito?**
Porque aprendió de etiquetas generadas por RoBERTuito. Es el límite de la destilación. Para
superarlo se necesitan etiquetas humanas.

**¿Se puede reproducir todo el proyecto?**
Sí. Todas las semillas están fijadas, las dependencias están en `requirements.txt` y los
notebooks localizan sus rutas automáticamente. Los pesos del modelo no se versionan por tamaño,
pero se regeneran ejecutando el notebook 04.

**¿Cuánto tarda entrenar el modelo?**
Aproximadamente 6 minutos en un Mac con Apple Silicon usando la GPU (MPS).

---

## 9. Cómo continuar el proyecto

En orden de impacto:

1. **Anotación humana de comentarios fronterizos.** Es el cuello de botella de todo el componente
   de texto. Con 300–500 comentarios etiquetados por dos o tres personas (midiendo el acuerdo
   mediante κ de Cohen) se podría entrenar un modelo que supere a RoBERTuito y fijar una rúbrica
   institucional para los casos ambiguos.
2. **Conseguir comentarios de texto libre reales** de la institución, en español nativo. El corpus
   actual de entrenamiento es traducción automática del inglés y carece de registro coloquial
   regional.
3. **Redefinir la variable objetivo.** `tendencia_desempeno` proviene de reglas sobre los
   puntajes; una etiqueta basada en la trayectoria real del docente entre semestres eliminaría la
   circularidad y haría significativa la comparación entre reglas y aprendizaje automático.
4. **Construir el tablero de priorización** a partir de las probabilidades calibradas del modelo,
   incorporando la detección de docentes con buen puntaje pero comentarios negativos.
5. **Validación cruzada y intervalos de confianza** para cuantificar la incertidumbre de todas las
   métricas reportadas.

---

*Equipo Tech Tailors · Reto Analítica Educativa · Samsung Innovation Campus.*

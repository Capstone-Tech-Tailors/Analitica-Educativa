# INFORME TÉCNICO
## Dataset para análisis de sentimiento en evaluación del desempeño docente
### Caracterización, idoneidad para fine-tuning, riesgos y controles de calidad

| Campo | Descripción |
|---|---|
| **Dataset fuente** | *A Novel Dataset for ABSA for Teacher Performance Evaluation* |
| **Publicador** | American International University-Bangladesh / Mendeley Data |
| **Ámbito** | Bangladesh · educación universitaria |
| **Archivo efectivamente utilizado** | `ReadyToTrain_comentarios_EN_ES_completo.xlsx` — subconjunto de 100.000 filas, traducido al español por el equipo |
| **Tarea implementada** | Clasificación de sentimiento en tres polaridades (POS / NEU / NEG) |
| **Proyecto** | Analítica Educativa · equipo Tech Tailors · Samsung Innovation Campus |
| **Fecha del informe** | 4 de agosto de 2026 |
| **Estado** | **Verificado sobre el archivo real.** Perfil estadístico calculado; entrenamiento y evaluación ejecutados |

> **Conclusión principal.** El corpus fuente es pertinente por estar centrado en comentarios
> estudiantiles sobre docentes. El archivo efectivamente utilizado es un **subconjunto de 100.000
> filas traducido al español**, que **no conserva las etiquetas ni los aspectos** del recurso
> original. Esa ausencia condicionó todo el diseño: obligó a generar etiquetas mediante
> *weak supervision* y, después, mediante **anotación humana del equipo**. Las verificaciones de
> idioma, duplicación, longitud y ausencia de fuga entre particiones están **resueltas y
> documentadas** en este informe.

---

## 1. Propósito y alcance

Este informe documenta el conjunto de datos utilizado para ajustar el modelo de sentimiento
aplicado a la evaluación del desempeño docente. Deja trazabilidad técnica del origen del corpus,
de las transformaciones aplicadas, de la tarea de aprendizaje efectivamente implementada y de los
riesgos que afectan la interpretación del modelo.

A diferencia de la versión preliminar de este documento —redactada únicamente con la ficha de
selección—, **todas las cifras que siguen se calcularon sobre el archivo real**. Cuando un dato no
pudo verificarse, se indica de forma explícita.

## 2. Identificación y cadena de derivación

### 2.1 Recurso fuente

| Elemento | Valor | Evidencia |
|---|---|---|
| Nombre | A Novel Dataset for ABSA for Teacher Performance Evaluation | Ficha de selección |
| Institución / repositorio | American International University-Bangladesh / Mendeley Data | Ficha de selección |
| País y nivel | Bangladesh / universidad | Ficha de selección |
| Población temática | Comentarios de estudiantes sobre desempeño docente | Ficha de selección |
| Cobertura reportada | Más de 2.000.000 de instancias | Cifra del depósito; **no corresponde al archivo usado** |
| Acceso | https://data.mendeley.com/datasets/b2yhc95rnx/1 | Enlace identificado |
| Licencia | CC BY-NC 3.0 | Reportada en la ficha |

### 2.2 Cadena de derivación hasta el archivo utilizado

```
Mendeley — dataset original (ABSA, >2.000.000 instancias reportadas, con etiquetas y aspectos)
   │
   ├─ [1] Selección de un subconjunto de 100.000 filas          (realizado por el equipo)
   │
   └─ [2] Traducción automática inglés → español                (realizado por el equipo)
        │
        └─ ReadyToTrain_comentarios_EN_ES_completo.xlsx   ← ARCHIVO UTILIZADO
             columnas: id · StudentComments_EN · Comentarios_ES
             SIN columna de etiqueta · SIN columna de aspecto
```

> **Consecuencia metodológica.** Al no conservarse las etiquetas del recurso original, el archivo
> no es directamente utilizable para aprendizaje supervisado. Esta es la razón por la que el
> proyecto recurrió primero a *weak supervision* (etiquetado automático con RoBERTuito) y después
> a **anotación humana**, que es la fuente de etiquetas del modelo final.

## 3. Perfil estadístico del archivo utilizado

Verificado sobre `data/raw/ReadyToTrain_comentarios_EN_ES_completo.xlsx` (3,3 MB;
SHA-256 `21637107cebf941a3aab9f397983c123b1676f5f4488d2d1…`).

| Indicador | Valor |
|---|---|
| Filas | **100.000** |
| Columnas | 3 — `id` (int), `StudentComments_EN` (texto), `Comentarios_ES` (texto) |
| Valores nulos | 8 en cada columna de texto |
| Comentarios en español no vacíos | 99.992 |
| **Textos únicos (español)** | **29.243** → unicidad **29,2 %** |
| Casi duplicados (tras normalización) | 28.147 grupos; 1.096 variantes colapsan |
| Repetición máxima | La frase más frecuente aparece **9.741 veces** |
| Longitud (palabras) | media 6,8 · mediana 4 · p5 1 · p95 22 · máx 199 |
| Longitud (caracteres) | media 39 · mediana 20 · p95 129 · máx 1.121 |
| **Etiquetas de sentimiento** | ❌ **ausentes** |
| **Aspectos ABSA** | ❌ **ausentes** |

**Idioma (verificación explícita).** Sobre una muestra aleatoria de 3.000 textos de
`Comentarios_ES`: **80,2 %** contienen marcadores léxicos del español frente a **5,7 %** con
marcadores del inglés (columna de control `StudentComments_EN`: 89,6 % marcadores ingleses).
**Se confirma que la columna utilizada está en español.**

**Textos muy cortos.** La mediana de 4 palabras indica un corpus de comentarios breves
(*"Bueno."*, *"Buen profesor."*), lo que explica que la clase neutra sea la más difícil de
delimitar.

## 4. Tarea implementada y esquema de clases

El recurso original está planteado para **ABSA** (análisis de sentimiento basado en aspectos).
Dado que el archivo utilizado **no conserva la variable de aspecto**, la tarea implementada es
**clasificación de polaridad global**, no ABSA.

> **Declaración de consistencia.** El resultado debe describirse como *clasificación de
> sentimiento sobre datos provenientes de un corpus ABSA*, **no** como un modelo ABSA.

| Clase | Interpretación operativa (rúbrica del proyecto) | Riesgo de anotación |
|---|---|---|
| **POS** | Elogio explícito con contenido valorativo | La cortesía puede confundirse con valoración real |
| **NEU** | Descriptivo, administrativo o elogio tibio sin entusiasmo | Funciona como clase residual y pierde coherencia |
| **NEG** | Queja, carencia o petición de cambio, **incluso si es cortés** | La negación y la ironía invierten la polaridad |

**Mapeo de etiquetas.** El modelo entregado incorpora el mapeo en su `config.json` (`id2label`),
de modo que la API devuelve directamente `POS` / `NEU` / `NEG`. **No existe riesgo de
desalineación numérica** al desplegar.

## 5. Matriz de evidencia — estado actualizado

| Variable | Estado | Resultado |
|---|---|---|
| Nombre, institución y enlace | ✅ Disponible | Registrado en §2.1 |
| Volumen | ✅ **Verificado** | 100.000 filas · 29.243 textos únicos |
| Idioma | ✅ **Verificado** | Español (traducción del inglés) |
| Columnas y tipos | ✅ **Verificado** | Diccionario de datos en §3 |
| Aspectos ABSA | ✅ **Verificado** | **Ausentes** en el archivo utilizado |
| Etiquetas originales | ✅ **Verificado** | **Ausentes**; sustituidas por anotación propia |
| Balance de clases | ✅ **Verificado** (sobre las etiquetas propias) | Entrenamiento: NEG 52 · NEU 22 · POS 74 |
| Calidad de anotación | ✅ **Auditada** | 3 anotadores · α de Krippendorff = **0,585** (moderado) |
| Particiones | ✅ **Documentadas** | 118 train / 30 validación / 172 evaluación · semilla 42 · **0 fuga verificada** |
| Duplicación | ✅ **Verificada y mitigada** | Deduplicado a 29.243 únicos **antes** de particionar |
| Licencia | ⚠️ Reportada | CC BY-NC 3.0 — archivar la versión del depósito |
| **Sistema de traducción** | ❌ **Pendiente** | **Debe documentarse** (véase §8) |

## 6. Preparación aplicada al fine-tuning

1. **Copia inmutable** del archivo, con su suma de comprobación SHA-256 registrada (§3).
2. **Deduplicación previa a la partición**: agrupación por texto normalizado (minúsculas, sin
   tildes ni puntuación) para impedir que el mismo contenido apareciera en entrenamiento y prueba.
3. **Muestreo estratificado** de 335 comentarios para anotación: censo de los 40 enunciados más
   frecuentes (concentran el 53 % de las apariciones) más estratos por dificultad lingüística.
4. **Anotación humana independiente** por tres personas, con rúbrica escrita, ítems ancla de
   control y repetidos encubiertos para medir autoconsistencia.
5. **Particiones sin fuga**: bloque de evaluación (triple anotación, 172 ítems) y bloque de
   entrenamiento (anotación simple, 148 ítems), **disjuntos por diseño y verificados**.
6. **Tokenización** con el tokenizador del modelo base, `max_length` = 128.
7. **Evaluación** con macro-F1, F1 por clase, matriz de confusión y prueba de McNemar frente al
   modelo base.

## 7. Riesgos de validez y controles aplicados

| Riesgo | Control aplicado | Estado |
|---|---|---|
| Desbalance de clases | Macro-F1 como métrica principal + entropía cruzada ponderada por clase | ✅ Aplicado |
| Duplicación masiva (9.741 repeticiones de una frase) | Deduplicación antes de particionar | ✅ Aplicado |
| Anotación inconsistente | Auditoría con 3 anotadores; α = 0,585; anclas y repetidos de control | ✅ Medido |
| Fuga entre particiones | Verificación explícita: intersección train ∩ evaluación = **0** | ✅ Verificado |
| Idioma incompatible con el modelo base | Idioma confirmado como español; modelo base en español | ✅ Verificado |
| Cambio de dominio | Documentado: corpus de Bangladesh traducido ≠ encuestas de la U. del Rosario | ⚠️ Vigente |
| Sesgo estudiantil | Uso agregado por docente; no como juicio individual automático | ⚠️ Control de uso |

## 8. Compatibilidad con RoBERTuito — resuelto

La versión preliminar de este informe señalaba como **punto crítico** verificar el idioma antes de
justificar el uso de RoBERTuito. **Queda resuelto**: los textos utilizados están en español (§3),
de modo que no existe incompatibilidad entre el preentrenamiento del modelo y los datos.

Adicionalmente, y siguiendo la recomendación de comparar contra alternativas, se evaluaron **tres
modelos con la misma partición y las mismas métricas**:

| Modelo | macro-F1 sobre el gold humano (n = 172) |
|---|:--:|
| BETO destilado | 0,619 |
| RoBERTuito (base público) | 0,638 |
| **RoBERTuito ajustado con etiquetas humanas** | **0,646** |

**Punto pendiente de documentar.** Los textos **fueron traducidos** por el equipo, por lo que debe
registrarse: (i) el **sistema de traducción** empleado; (ii) que la traducción se realizó **antes**
de cualquier partición; y (iii) una auditoría de preservación de polaridad y negaciones sobre una
muestra. La traducción produce un registro estándar sin variación coloquial regional, lo que
constituye una limitación frente al español que tendrán las encuestas reales.

## 9. Evaluación del modelo — registro efectivo

| Componente | Valor registrado |
|---|---|
| Modelo base | `pysentimiento/robertuito-sentiment-analysis` (~110 M parámetros) |
| Método | *Continued fine-tuning* con etiquetas humanas (sin destilación) |
| Origen de las etiquetas | Anotación humana del equipo · 3 anotadores · α = 0,585 |
| Entrenamiento | 4 épocas · lr 1e-5 · batch 8 · `max_length` 128 · entropía cruzada ponderada · *early stopping* |
| Reproducibilidad | Semilla 42 · dispositivo MPS (Apple Silicon) |
| Datos | 118 entrenamiento / 30 validación / 172 evaluación |
| Resultados | macro-F1 **0,646** · accuracy 0,762 · recall NEG 0,556 |
| Comparación | Frente al modelo base: 0,638 → 0,646 (**McNemar p = 1,000**: mejora **no significativa**) |
| Análisis de errores | Matriz de confusión y revisión de casos fronterizos en el notebook 05 |

> **Lectura honesta del resultado.** El ajuste con verdad humana mejora al modelo base en todas
> las métricas, pero con 148 ejemplos de entrenamiento la diferencia **no alcanza significancia
> estadística**. El cuello de botella está identificado y cuantificado: el volumen de anotación.

## 10. Licencia, ética y protección de datos

El recurso fuente se distribuye bajo **CC BY-NC 3.0**: la reutilización exige mantener la
atribución, indicar los cambios realizados —en este caso, **selección de subconjunto y
traducción**— y respetar la restricción de **uso no comercial**. La versión y el texto de la
licencia deben archivarse junto con el experimento.

Aunque se trate de datos públicos, los comentarios estudiantiles pueden contener nombres o
identificadores. Se recomienda seudonimizar referencias personales, restringir la publicación de
ejemplos textuales y reportar resultados de forma agregada. **Un clasificador de sentimiento no
debe ser el único insumo para decisiones laborales sobre docentes**; su uso previsto en este
proyecto es la construcción de un DOFA orientado al acompañamiento formativo.

## 11. Conclusiones

El dataset fuente presenta alineación temática alta con la evaluación docente. Sin embargo, el
archivo efectivamente utilizado es un **subconjunto de 100.000 filas traducido al español que no
conserva las etiquetas ni los aspectos del recurso original**, lo que redefinió el proyecto: de un
ajuste supervisado directo a un proceso de **generación de etiquetas propias**, primero
automáticas y después humanas.

Las verificaciones que la versión preliminar dejaba pendientes —idioma, volumen, estructura,
duplicación, balance, calidad de anotación e independencia de las particiones— **están resueltas y
documentadas**. Persisten dos limitaciones vigentes: el volumen reducido de etiquetas humanas
(148 ejemplos), que impide alcanzar significancia estadística, y el **cambio de dominio** entre un
corpus traducido de Bangladesh y las encuestas reales de la Universidad del Rosario.

> **Dictamen técnico.** El corpus fue **adecuado como fuente de textos** para el ajuste, pero
> **insuficiente como fuente de etiquetas**. El modelo resultante es apto para despliegue como
> línea base; su mejora depende de ampliar la anotación humana con comentarios propios de la
> institución.

---

## Anexo A. Texto metodológico (completado)

> Se utilizó un subconjunto de 100.000 registros del conjunto de datos *"A Novel Dataset for ABSA
> for Teacher Performance Evaluation"*, publicado por American International University-Bangladesh
> a través de Mendeley Data. Los comentarios, originalmente en inglés, fueron **traducidos al
> español** por el equipo antes de cualquier partición. El archivo resultante contiene 99.992
> comentarios no vacíos, de los cuales **29.243 son textos únicos** (unicidad 29,2 %), con una
> longitud mediana de 4 palabras. El subconjunto **no conserva las etiquetas de polaridad ni los
> aspectos** del recurso original.
>
> Ante la ausencia de etiquetas se aplicaron dos estrategias sucesivas. Primero,
> *weak supervision*: el modelo `pysentimiento/robertuito-sentiment-analysis` etiquetó el corpus
> deduplicado y esas pseudo-etiquetas se emplearon para un ajuste por destilación, que confirmó
> empíricamente el techo de este método. Después, el equipo realizó una **anotación humana** de 335
> comentarios seleccionados mediante muestreo estratificado, con tres anotadores independientes,
> rúbrica escrita e ítems de control; el acuerdo inter-anotador fue de **α de Krippendorff = 0,585**
> (moderado).
>
> El conjunto anotado se dividió en 148 ejemplos de entrenamiento (118 train / 30 validación) y 172
> de evaluación, **disjuntos y verificados sin fuga**. Se ajustó
> `pysentimiento/robertuito-sentiment-analysis` con longitud máxima de 128 tokens, tasa de
> aprendizaje 1e-5, batch size 8, 4 épocas con *early stopping* y entropía cruzada ponderada por
> clase, con semilla 42. El rendimiento se evaluó mediante macro-F1, F1 por clase, matriz de
> confusión y prueba de McNemar frente al modelo base: **macro-F1 0,646 frente a 0,638**
> (p = 1,000, diferencia no significativa).

**Pendiente de completar por el equipo:** el **sistema de traducción** utilizado en el paso inglés
→ español, y una auditoría de preservación de polaridad sobre una muestra traducida.

## Anexo B. Referencia de la fuente

*A Novel Dataset for ABSA for Teacher Performance Evaluation*. Mendeley Data, versión 1. American
International University-Bangladesh. https://data.mendeley.com/datasets/b2yhc95rnx/1

**Nota de evidencia.** La autoría individual, la fecha de publicación y el DOI del depósito no se
verificaron en esta ejecución y deben incorporarse desde la ficha oficial antes de la entrega
académica definitiva. Todas las cifras relativas al **archivo utilizado** sí fueron calculadas
directamente sobre él y son reproducibles con el notebook `INFORME_FINAL.ipynb` (§2).

---

*Informe técnico del dataset · Tech Tailors · Analítica Educativa — Universidad del Rosario.*

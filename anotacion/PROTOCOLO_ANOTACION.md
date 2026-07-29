# Protocolo de anotación humana

**Proyecto** Analítica Educativa — equipo Tech Tailors
**Objetivo** construir un *gold standard* con verdad humana que permita (a) fijar la rúbrica
institucional en los casos ambiguos y (b) entrenar un modelo capaz de **superar** al maestro
actual (RoBERTuito), rompiendo el techo de la destilación.

---

## 1 · Por qué hace falta

El componente de texto del proyecto está limitado por un techo demostrado: el modelo ajustado
aprende de etiquetas generadas por RoBERTuito, de modo que **no puede superarlo**. El análisis
de falsos positivos (notebook 04, §8.5) mostró además que el error no es corregible con umbrales
—el modelo se equivoca con 99,6 % de confianza— porque el problema es **dónde está la frontera
POS/NEU**, es decir, una decisión de rúbrica.

Solo la anotación humana rompe ese techo. Y el conjunto de evaluación actual son **20
comentarios**, insuficiente: la propia variación entre corridas del entrenamiento (±0,04 de
macro-F1) es del mismo orden que las diferencias entre modelos.

## 2 · Roles

| Rol | Responsabilidad |
|---|---|
| **Coordinador** | Genera las planillas, custodia las claves, consolida los resultados y dirige la reunión de adjudicación |
| **Anotadores A1, A2, A3** | Reciben su planilla, anotan **en solitario** y la devuelven |

> La **independencia** entre anotadores no es una formalidad: sin ella el acuerdo medido carece
> de sentido y el gold pierde su valor como referencia.

## 3 · Composición de la muestra

335 comentarios seleccionados del corpus real (29.243 textos únicos) mediante muestreo
estratificado. **No es una muestra aleatoria simple**: está deliberadamente enriquecida en casos
fronterizos, que es donde se decide la rúbrica.

| Bloque | Ítems | Anotación | Destino |
|---|--:|---|---|
| **EVAL** | 185 | Los 3 anotadores (triple) | Conjunto de **evaluación** + medición de acuerdo |
| **TRAIN** | 150 | Un anotador cada tercio (50 c/u) | Datos de **entrenamiento** con verdad humana |

Estratos del bloque EVAL:

| Estrato | Ítems | Qué contiene |
|---|--:|---|
| `H0_CENSO` | 40 | Los 40 enunciados más frecuentes del corpus (concentran el **53 %** de todas las evaluaciones) — se anotan por censo, no por sorteo |
| `H1_CORTO` | 20 | Textos de 1–2 palabras (*"Bueno."*), que pesan el 30 % de las filas |
| `H2a_T0` | 30 | Casos triviales (control de calidad del estimador) |
| `H2b_F1` | 40 | Frontera débil — **contiene el error tipo §8.5**: POS con alta confianza y léxico tibio |
| `H3_F2` | 55 | Frontera fuerte — máxima ambigüedad |

**Por qué el censo de los 40 más frecuentes:** dos solos enunciados (*"Es un buen profesor"*
15.826 filas y *"Bueno."* 9.745) determinan el 25,6 % del corpus. Un sorteo tendría probabilidad
casi nula de tocarlos, y sin ellos ninguna métrica podría traducirse a desempeño real.

**Cómo se corrige el sesgo de sobre-representación:** los estratos forman una partición completa
con tamaños conocidos, así que las métricas poblacionales se estiman con **pesos**
`w_h = N_h / n_h` (estimador estratificado). Sobre-muestrear la frontera no sesga nada mientras
se pondere al estimar.

## 4 · Formato de las planillas

**Un archivo XLSX por anotador**: `anotacion_A1.xlsx`, `anotacion_A2.xlsx`, `anotacion_A3.xlsx`.

> **Por qué XLSX y no CSV:** el 30 % de los textos contienen comas y el 51 % llevan tildes. El
> viaje Excel → CSV → pandas corrompe los acentos y un separador mal interpretado deja el
> archivo inservible. El CSV se usa **solo a la salida**, escrito y leído por Python.

Columnas de la hoja `ANOTACION`:

| Columna | Contenido | Quién rellena |
|---|---|---|
| `anotador` · `orden` · `clave` | Identificación (clave opaca) | pre-rellenado, bloqueado |
| `comentario` | El texto a etiquetar | pre-rellenado, bloqueado |
| **`etiqueta`** | **POS / NEU / NEG** | **anotador (obligatorio)** |
| **`dificil`** | **0 / 1** | **anotador (obligatorio)** |
| `motivo` | Categoría de la dificultad | anotador, si `dificil = 1` |
| `nota` | Texto libre | opcional |

Dos decisiones de diseño, con su fundamento:

- **No se muestra la predicción del modelo.** RoBERTuito acierta 15/16 en los casos claros pero
  **0/4 en los fronterizos**, y la muestra está enriquecida precisamente en fronterizos. Mostrar
  su predicción induciría *anchoring bias* justo donde importa, reproduciendo el empate con el
  maestro por construcción.
- **Orden aleatorizado independiente por anotador**, con claves opacas: impide comparar planillas
  entre anotadores y reparte el efecto de la fatiga.

Se incluyen además **8 ítems ancla** de etiqueta obvia (control de atención) y **8 repetidos
encubiertos** (miden la autoconsistencia de cada anotador). Ninguno es identificable en la
planilla.

## 5 · Instrucciones para el anotador

1. Lea la **rúbrica** (`RUBRICA_ANOTACION.md`) una vez, completa. Son 5 minutos bien invertidos.
2. Abra su archivo y rellene **solo las columnas de fondo blanco**: `etiqueta`, `dificil`,
   `motivo`, `nota`.
3. Trabaje **de arriba a abajo**, en el orden dado. **No ordene ni filtre** la hoja.
4. Elija la etiqueta del desplegable. **No deje ninguna fila vacía.**
5. Si duda más de 15 segundos: decida, marque `dificil = 1` y continúe.
6. **No consulte con los otros anotadores.** La independencia es requisito del método.
7. Hágalo de una sola sentada (~35 min). La fatiga degrada la calidad más que la prisa.
8. Devuelva el archivo al coordinador sin renombrarlo.

## 6 · Consolidación y métricas de acuerdo

El coordinador ejecuta:

```bash
python anotacion/consolidar_anotacion.py
```

El script calcula:

| Métrica | Rol | Por qué |
|---|---|---|
| **α de Krippendorff (nominal)** | **Titular** | Es la única que admite un diseño incompleto (3 anotadores en EVAL, 1 en TRAIN) y anotadores variables por ítem |
| α de Krippendorff (ordinal) | Diagnóstico | Compara con la nominal: la **brecha** revela el tipo de desacuerdo |
| Fleiss κ | Secundario | Convención de la literatura NLP; solo sobre el bloque de triple anotación |
| Cohen κ por pares | Diagnóstico | Detecta un **anotador atípico**: si κ(A,B) y κ(A,C) son altos pero κ(B,C) es bajo, el problema es C, no la rúbrica |
| Acuerdo observado `P_o` | **Obligatorio junto a κ** | Por la *paradoja de kappa*: con clases desbalanceadas κ se hunde aunque el acuerdo real sea alto |

**Interpretación (Landis & Koch):** < 0,20 pobre · 0,21–0,40 aceptable · 0,41–0,60 moderado ·
0,61–0,80 sustancial · > 0,80 casi perfecto.

**El diagnóstico clave del proyecto** es la brecha `α_ordinal − α_nominal`:

- **α_ordinal ≫ α_nominal** → los desacuerdos son **adyacentes** (POS↔NEU, NEU↔NEG): es un
  problema de **umbral de rúbrica**, se corrige escribiendo reglas más precisas. Es el caso
  esperado.
- **Ambos bajos** → desacuerdos **polares** (POS↔NEG): los anotadores no entienden la tarea; hay
  que reformar la formación o el espacio de etiquetas.

Si el acuerdo resulta bajo (< 0,40), **no se descarta el trabajo**: se revisa la rúbrica en la
reunión, se emite la versión 1.1 y se re-anota únicamente el subconjunto afectado.

## 7 · Adjudicación del gold

| Situación | Resolución |
|---|---|
| Unanimidad (3/3) | Etiqueta directa |
| Mayoría (2/1) | Etiqueta mayoritaria; se revisa en reunión si estaba marcada `dificil` |
| Sin mayoría (1/1/1) | **Reunión de adjudicación obligatoria**; si no hay consenso, el ítem se marca `ambiguo` y **se excluye del conjunto de evaluación**, conservándose como evidencia de ambigüedad genuina |

Los ítems sin mayoría no son un problema: son **el hallazgo**. Indican dónde el lenguaje es
genuinamente ambiguo y ninguna métrica automática debería penalizar al modelo.

## 8 · Uso posterior de los datos

1. **Bloque EVAL** (185 ítems, gold adjudicado) → conjunto de evaluación. Sustituye a los 20
   comentarios actuales: **9× más grande**, con potencia estadística para distinguir modelos.
2. **Bloque TRAIN** (150 ítems, anotación simple) → fine-tuning con verdad humana, combinable con
   las pseudo-etiquetas mediante ponderación (las humanas pesan más).
3. **Comparación final**: reentrenar el modelo del notebook 04 con estas etiquetas y medirlo
   contra RoBERTuito **sobre el nuevo conjunto de evaluación**. Solo entonces la afirmación
   "superamos al maestro" será defendible.

> **Sin fuga de información**: los bloques EVAL y TRAIN son disjuntos, y ninguno de los 335 ítems
> coincide (ni normalizado) con los 20 comentarios del benchmark actual — verificado.

---

*Protocolo v1.0 · Tech Tailors · muestra generada con semilla registrada y orden por hash
determinista, reproducible byte a byte.*

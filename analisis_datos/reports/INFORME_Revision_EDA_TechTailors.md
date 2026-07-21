# Informe de revisión — `EDA_Analitica_Educativa_TechTailors.ipynb`

**Proyecto:** Analítica Educativa · Samsung Innovation Campus 2025 · equipo Tech Tailors
**Objeto revisado:** notebook de EDA (11 insights, SCRUM-5 y SCRUM-8) + datos procesados con sentimiento transformer
**Fecha:** 2026-07-20

## Cómo se hizo esta revisión

Se ejecutó una copia del notebook en un entorno controlado (con el CSV renombrado, ver §1) para obtener sus salidas reales, y luego un **enjambre de 67 agentes** organizado en dos frentes: (a) revisión del notebook en 5 dimensiones —metodología estadística, fuga de información, verificación numérica de insights, código/reproducibilidad y coherencia del sentimiento— con **verificación adversarial** de cada hallazgo (3 refutadores con lentes distintos: correctitud, reproducibilidad numérica e impacto práctico); (b) 6 análisis sobre los datos procesados, cada uno con un chequeo independiente que recomputó sus números.

Todos los números de este informe provienen de código ejecutado, no de estimaciones. Cada hallazgo lleva su nivel de evidencia:

- **✅✅ Confirmado adversarialmente** — sobrevivió a 3 refutadores independientes.
- **✅ Verificado por mí** — la verificación adversarial se cortó por límite de sesión; recomputé el hallazgo con mi propio script (`scratchpad/verificar_metodologia.py`) y lo confirmé.
- **◑ Con evidencia propia** — reportado con script ejecutado por el agente, sin segunda verificación.

---

## Veredicto general

El EDA es **sólido en forma y ejecución** (identidad visual cuidada, batería estadística amplia, diagnóstico de calidad correcto, hallazgos de negocio bien presentados). Sin embargo, la revisión encontró **un error factual que debe corregirse antes de entregar**, **cuatro conclusiones sobre-afirmadas** que el instrumento estadístico no soporta, y **una debilidad de fondo**: casi toda la "señal del sentimiento" y la ventaja del ML que el notebook celebra son **artefactos del dataset plantillado (anonimizado por la universidad)**, cuya etiqueta se generó alineada con la polaridad léxica de las 20 plantillas. Nada de esto invalida la metodología; sí obliga a reformular varias conclusiones y a moderar las expectativas de la fase de modelado.

---

## 1 · Error que impide reproducir el notebook  ✅✅

**El notebook no corre en la carpeta del proyecto.** Espera `evaluaciones_docentes.csv`, pero el archivo real se llama `Evaluaciones docentes - Evaluaciones docentes.csv`. En local lanza `FileNotFoundError` (la rama de Colab pide subida manual). Además, **se entregó sin ejecutar** (0 salidas): ningún insight es verificable en el entregable tal cual está. Y la celda de features de §10.1 **no es idempotente**: re-ejecutarla lanza `KeyError` porque hace `merge` de columnas que ya existen.

> **Acción:** corregir el nombre de archivo (o normalizarlo), ejecutar el notebook de punta a punta antes de entregar, y hacer la celda de features re-ejecutable (p. ej. `drop` previo de las columnas o comprobación de existencia).

---

## 2 · Error factual en el Insight 10  ✅✅ / ✅

El texto del Insight 10 señala como prioridad de acompañamiento *"el superior-izquierdo (Docente_4, Docente_50, **Docente_16**)"*. Recomputado:

| Top-5 real por % En riesgo | % |
|---|---|
| **Docente_37** | **29.2 %** |
| Docente_4 | 26.9 % |
| Docente_50 | 26.7 % |
| Docente_21 | 26.4 % |
| Docente_28 | 26.4 % |

**Docente_16 está en el puesto 14 (23.4 %), no en el grupo prioritario, y el docente de mayor riesgo real —Docente_37— no se menciona.** Es un error de lectura del gráfico que invierte parcialmente el mensaje de negocio.

> **Acción:** reemplazar la terna por Docente_37 / Docente_4 / Docente_50 (o citar el top-5 completo).

---

## 3 · Conclusiones sobre-afirmadas (el instrumento no las soporta)

### 3.1 · "El puntaje promedio resume el 80 % de la señal; los puntajes individuales son redundantes" — artefacto de colinealidad  ✅

`puntaje_promedio` **es por construcción** la media de los tres puntajes (r = 0.87 con cada uno). La importancia de permutación con features casi idénticas reparte la señal de forma engañosa. Recomputado con el mismo split y semilla:

- RF **con** `puntaje_promedio`: importancias = promedio +0.485, individuales +0.002 a +0.017 (parecen "redundantes").
- RF **sin** `puntaje_promedio`: macro-F1 = **0.917** (vs 0.920, prácticamente igual) y los individuales **saltan a +0.14 – +0.16**, al nivel del sentimiento (+0.16).

Lo correcto es: **el bloque de puntajes es intercambiable**, no que el promedio "domine" y los individuales sobren. Conservarlos por interpretabilidad es válido; la justificación de la tabla 10.5 no.

### 3.2 · "id_docente tiene señal débil de perfil (V ≈ 0.12)" — puro sesgo de tamaño de tabla  ✅

La V de Cramér sin corregir crece con el número de categorías. Para `id_docente × clase` (50×3): **V observada = 0.119, pero p = 0.813 y la V esperada bajo independencia pura es 0.127** (mayor que la observada). La V corregida por sesgo es ≈ 0. No hay asociación real docente↔clase; el 0.12 es exactamente el ruido esperado. Solo `sentimiento` (V = 0.352, p ≈ 10⁻¹⁵⁹) tiene asociación genuina; comparar V entre tablas 3×3 y 50×3 sin corrección no es válido.

### 3.3 · "El RandomForest (0.920) supera al sistema de reglas (0.910)" — diferencia no significativa  ✅

Con un único split de 649 filas de test, Δ = +0.010 macro-F1 **no es distinguible de cero**: McNemar p = 0.280; en 15 semillas de partición el Δ medio es +0.011 pero **la regla supera al RF en 2 de 15**. El notebook presenta 0.920 vs 0.910 como cuantificación de "reglas vs ML" sin ninguna medida de incertidumbre. Con estos datos **no puede afirmarse que el ML supere a la regla de 2 umbrales.** (El Insight 11 además cita "≈0.90" para la regla cuando su propio output da 0.910, lo que infla la ventaja aparente del ML.)

### 3.4 · `delta_semestre` "estadísticamente significativa" — fuga del presente  ✅✅

`delta_semestre` usa `prom_docente_sem` del **semestre actual**, que promedia las mismas filas que se están clasificando (en grupos docente-semestre de tamaño 1, la feature *es* el puntaje propio). Su significancia (H = 141) es un **artefacto de fuga**: a nivel de grupo cae a H = 68 y su importancia predictiva marginal es ≈ 0. El comentario del código *"solo con información PASADA"* es **falso** para esta feature (sí es correcto para `hist_prom_previo`, que se verificó y solo usa pasado ✅✅).

> **Acciones §3:** reformular la tabla 10.5 y los Insights 5, 7 y 11; reportar la comparación regla-vs-ML con intervalo/prueba de significancia; corregir el comentario de `delta_semestre` o excluirla; y, para reportar generalización real, usar un **split que agrupe por docente y por comentario** (hoy las mismas 20 plantillas y los 50 docentes están en train y test, así que el test mide interpolación, no generalización ✅✅).

---

## 4 · El sentimiento: Insight 9 es un artefacto, y el "valor del texto" no sobrevive al gold  ✅✅

Este es el hallazgo de fondo, y toca directamente la línea NLP del proyecto.

**El Insight 9 ("comentario negativo ⇒ nunca Mejora; positivo ⇒ nunca En riesgo, 0 casos") solo se cumple con las listas léxicas exactas del EDA.** Al reclasificar los mismos 20 comentarios con el pipeline de 3 transformers + gold standard validado a mano:

- La mitad "positivo ⇒ nunca En riesgo" **sí sobrevive** (0 de 677 filas POS).
- La mitad "negativo ⇒ nunca Mejora" **se rompe**: 154 filas NEG-gold caen en Mejora (82 de *"Se podría mejorar el material"* + 72 de *"Asistencia puntual, pero falta dinamismo"*).

Todas las violaciones vienen de comentarios que el léxico del EDA metió en el cajón "neutro" pese a tener carga (críticas suaves o mixtas). Es decir, el EDA eligió como POS/NEG justo los 14 comentarios que nunca coexisten con la clase opuesta. **La "restricción determinística" es una propiedad de las listas, no de los datos.**

**Y lo más importante para el equipo:** el sentimiento léxico del EDA predice la etiqueta *mejor* que el sentimiento transformer, lingüísticamente más correcto. Recomputado con el score gold en lugar del léxico:

| Métrica (SCRUM-8) | Score léxico EDA | Score gold transformer |
|---|---|---|
| Kruskal-Wallis H | 641.6 | 443.3 |
| Información mutua* | 0.206 | 0.100 |
| V de Cramér | 0.352 | 0.280 |
| Importancia de permutación | +0.083 (#2 de 9) | +0.002 (#4, ≈ ruido) |
| macro-F1 del RF | 0.917 | 0.898 |

*(\*Los valores exactos de información mutua y de importancia de permutación varían levemente según la semilla y el orden de columnas —es uno de los hallazgos de §6—; la dirección, gold < léxico en las cuatro métricas, es estable. Estas cifras son las que reproduce `Integracion_Sentimiento_EDA.ipynb`.)*

El score léxico está **alineado por construcción** con la etiqueta (derivada por reglas) (concuerda con el gold solo en el 76.5 % de las filas). La conclusión "el sentimiento es la segunda señal y la única complementaria" **depende de usar esa partición léxica**; con etiquetas de sentimiento realistas, el aporte marginal casi desaparece.

> **Implicación:** este dataset **no sirve para demostrar el valor del NLP**. Cualquier métrica favorable al "sentimiento" aquí mide alineación con el generador de la etiqueta, no comprensión del texto. La clasificación léxica del EDA no es defendible como estándar del equipo frente a 3 transformers + validación humana; adóptese `gold_standard_comentarios.csv` como fuente única del score, documentando que el valor del transformer se argumenta cualitativamente y se validará con **texto libre real**.

*(Nota menor sobre el gold que construimos en fases previas: la adjudicación humana dejó sin corregir 2 de 5 desacuerdos modelo-vs-referencia — "Resuelve las dudas con paciencia" y "Se nota que sabe mucho" quedaron NEU cuando son elogios. No afecta las conclusiones, pero conviene cerrarlo si el gold se publica ◑.)*

---

## 5 · Dónde está realmente el valor del ML (corrige el Insight 4)  ✅

El Insight 4 sitúa la "zona gris" en el promedio 3.4–3.9. Recomputado: esa franja es **98.5 % Estable** (845 de 858 filas) y la regla acierta ahí el 99 %. **No es zona gris.** Las fronteras de decisión reales, donde se concentran los errores de la regla, son:

- **[3.9, 4.5]** (frontera Estable/Mejora): 84.6 % de los errores. Ahí el sentimiento **sí** separa (P(Mejora|POS)=0.49 vs P(Mejora|NEG)=0.18) y el RF con sentimiento gana +0.04 de macro-F1 sobre el RF sin él.
- **[2.9, 3.5]** (frontera Estable/En riesgo): 11.5 % de los errores.

Además, una **regla híbrida dura** (override por sentimiento) colapsa exactamente en la regla de 2 umbrales: las reglas duras no explotan la señal textual, solo un modelo probabilístico lo hace. El argumento de valor del ML debe construirse sobre **estas fronteras + probabilidades calibradas + señal NLP en texto real**, no sobre el accuracy global.

---

## 6 · Veredicto por insight

| # | Insight | Veredicto |
|---|---|---|
| 1 | Clases desbalanceadas (En riesgo ≈ 20 %) | ✅ Correcto |
| 2 | `puntaje_evaluacion` la dimensión más débil (μ=3.69) | ✅ Correcto |
| 3 | Tamaño de grupo sin relación con desempeño | ✅ Correcto |
| 4 | Zona gris en 3.4–3.9 | ⚠️ **Mal ubicada**: esa franja es 98.5 % Estable; las fronteras reales son [3.9,4.5] y [2.9,3.5] |
| 5 | Puntajes correlacionados pero no redundantes | ◑ Correcto en conclusión, pero la evidencia de permutación es un artefacto de colinealidad (§3.1) |
| 6 | Sin deriva temporal institucional | ✅ Correcto |
| 7 | La etiqueta no depende del historial del docente | ✅ Correcto (y refuerza que `delta_semestre` no debe usarse, §3.4) |
| 8 | La asignatura pesa poco | ✅ Correcto (delta real 0.10, no 0.11 — menor) |
| 9 | Negativo ⇒ nunca Mejora; positivo ⇒ nunca En riesgo | ❌ **Artefacto léxico**: la mitad "negativo⇒nunca Mejora" se rompe (154 casos) con el gold (§4) |
| 10 | Docentes prioritarios | ❌ **Error factual**: nombra Docente_16 y omite Docente_37 (§2) |
| 11 | Señal = puntajes + sentimiento; resto sin aporte | ⚠️ **Depende del léxico**: con score gold el sentimiento cae a #4 (≈ ruido); la ventaja del ML no es significativa (§3.3, §4) |

Detalles numéricos menores a corregir: la tabla 10.5 cita MI del sentimiento ≈0.21 (real 0.179) e importancia de `puntaje_evaluacion` fuera del rango declarado; `mutual_info_classif` trata `asignatura_cod` como continua y los valores ≈0 de las features débiles dependen de la semilla; el `dropna` de §10.1 excluye 406 filas (todo el semestre 2020-1) de MI/RF/comparación sin advertirlo.

---

## 7 · Recomendaciones para la fase de modelado

1. **Baseline campeón = regla híbrida interpretable** (2 umbrales + ajuste por sentimiento), macro-F1 ≈ 0.92, recall En riesgo ≥ 0.99. Exigir que cualquier modelo la supere **de forma significativa** antes de complejizar.
2. **Fijar recall de `En riesgo` ≥ 0.985 como restricción dura** (métrica de negocio) y priorizar modelos mínimos e interpretables (logística multinomial con `class_weight='balanced'` ya alcanza ≈0.90 con 2 features).
3. **Validación temporal** (entrenar 2020–2022, probar 2023) además del split aleatorio, y agrupar por docente/comentario para no medir interpolación.
4. **Dos scores de sentimiento separados y documentados**: el léxico (reproduce la etiqueta actual generada por reglas) y el gold transformer (el que escala a texto libre real). No mezclarlos; usar el gold como oficial de producción.
5. **No presupuestar el salto de +0.08 de macro-F1 por el canal de texto**: con etiquetas realistas no aparece. El valor del NLP se demuestra con datos reales, no con este dataset.
6. **Producto**: el aporte inmediato del gold está en el **tablero por docente**, no en la métrica — detecta docentes "enmascarados" (buen puntaje, comentarios negativos): Docente_31, Docente_3, Docente_12, Docente_43. Docente_3 aparece incluso en el top-5 de "mejores" del EDA pese a tener 45 % de comentarios negativos. Un ranking combinado (riesgo + %NEG + sentimiento medio) prioriza mejor que `tendencia_desempeno` sola.

---

## 8 · Lo que está bien (para balance)

Diagnóstico de calidad correcto y honesto (0 nulos/duplicados, rangos válidos, y —notablemente— el propio EDA documenta el carácter plantillado/anonimizado de los datos como limitación). Identidad visual excelente y accesible (paleta validada para daltonismo, ΔE CVD ≥ 23.8). Batería estadística amplia y bien intencionada. Integridad de los datos procesados **perfecta**: `evaluaciones_con_sentimiento.csv` es un espejo fiel del original (9/9 columnas idénticas, mismo orden, 0 NaN, mapeo 20/20 con el gold). `hist_prom_previo` está correctamente construida sin fuga. La tesis central —que el valor del proyecto está en la zona de solapamiento y en la señal textual— es acertada; solo hay que corregir *dónde* está esa zona y *cuánto* aporta el texto.

---

## 9 · Alcance de esta revisión

15 hallazgos pasaron verificación adversarial de 3 refutadores; los 4 hallazgos de metodología de mayor severidad (§3) quedaron sin esa segunda vuelta por un límite de sesión y **los verifiqué yo mismo** recomputándolos (`scratchpad/verificar_metodologia.py`). Los 6 análisis de datos procesados (§4–§7) llevan cada uno un chequeo independiente que recomputó sus cifras (todos `coincide=True`). Scripts de auditoría de cada análisis en `scratchpad/eda_sandbox/analisis_*.py`. El material de apoyo cuantitativo, con todos estos números ya ejecutados y graficados, está en **`Integracion_Sentimiento_EDA.ipynb`**.

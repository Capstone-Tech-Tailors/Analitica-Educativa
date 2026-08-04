# Informe de acuerdo y consolidación

*Anotadores: 3 · anotaciones totales: 749*

## 1 · Control de calidad por anotador

| Anotador | Anotados | Sin etiqueta | Anclas correctas | Autoconsistencia | % difíciles |
|---|--:|--:|--:|--:|--:|
| A1 | 249 | 0 | 8/8 | 7/8 | 19 % |
| A2 | 250 | 0 | 8/8 | 6/8 | 3 % |
| A3 | 250 | 0 | 8/8 | 8/8 | 31 % |

> Anclas < 7/8 o autoconsistencia < 6/8 indican un anotador descuidado: revisar su planilla antes de consolidar.

## 2 · Ítems excluidos por no ser evaluables

Se excluyen **7** comentarios del gold. La lista es explícita y auditable (`NO_EVALUABLE` en este script), apoyada en el motivo `sin_sentido` marcado por los anotadores.

| Comentario | Motivo | Votos `sin_sentido` |
|---|---|--:|
| `No.` | sin_contenido_evaluable | 3/3 |
| `Profesor.` | sin_contenido_evaluable | 1/3 |
| `Ninguno.` | sin_contenido_evaluable | 2/3 |
| `Está dibujando.` | sin_contenido_evaluable | 1/3 |
| `considérenos, por favor.` | sin_contenido_evaluable | 1/3 |
| `Nada.` | sin_contenido_evaluable | 1/3 |
| `No tengo nada que decir sobre ella.` | sin_contenido_evaluable | 1/3 |

> **No se excluyen** los comentarios que los anotadores marcaron difíciles pero que sí tienen polaridad (sarcasmo, metáfora, elogio tibio). Eliminarlos dejaría el gold solo con casos fáciles e inflaría artificialmente las métricas.

## 3 · Acuerdo entre anotadores

**α de Krippendorff (nominal) = 0.585** → acuerdo *moderado* (métrica titular)

| Métrica | Valor | Rol |
|---|--:|---|
| α Krippendorff nominal | 0.585 | titular |
| α Krippendorff ordinal | 0.728 | diagnóstico |
| Fleiss κ | 0.584 | convención NLP |
| Cohen κ medio por pares | 0.585 | diagnóstico |
| Acuerdo observado P_o | 0.787 | obligatorio junto a κ |
| Acuerdo esperado por azar P_e | 0.487 | explica la paradoja de κ |

**Reparto del acuerdo en el bloque de triple anotación:** unanimidad 69.7% · mayoría 2/1 27.0% · sin mayoría 3.4%

> ⚠️ **Paradoja de kappa**: el acuerdo observado es alto (78.7%) pero κ queda en 0.584 porque el azar esperado es elevado (0.487) debido al desbalance de clases. **Interpretar κ junto a P_o**, nunca por separado.

**Cohen κ por pares** (detecta anotadores atípicos): A1–A2 = 0.521 · A1–A3 = 0.581 · A2–A3 = 0.654

**Diagnóstico — brecha α_ordinal − α_nominal = +0.143**

> Acuerdo homogéneo entre tipos de desacuerdo.

## 4 · Adjudicación del gold

| Situación | Ítems |
|---|--:|
| Unanimidad (3/3) | 124 |
| Mayoría (2/1) | 48 |
| Sin mayoría (1/1/1) → ambiguos | 6 |
| **Gold utilizable** | **172** |

**Distribución del gold:** NEG 36 · NEU 20 · POS 116

> Los 6 ítems sin mayoría requieren **reunión de adjudicación**. Si no hay consenso se conservan como evidencia de ambigüedad genuina, excluidos de la evaluación.

## 5 · Archivos generados

- `data/processed/gold_humano_eval.csv` — 172 ítems adjudicados (evaluación)
- `data/processed/train_humano.csv` — 148 ítems (entrenamiento con verdad humana)

## 6 · Siguiente paso

Reentrenar el notebook 04 sustituyendo las pseudo-etiquetas por `train_humano.csv` y evaluar contra `gold_humano_eval.csv`. Solo entonces la afirmación *«superamos al maestro»* será defendible.

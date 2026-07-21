# ¿Cuántos comentarios distintos hay realmente en el dataset?

**Resumen para el equipo:** el archivo `evaluaciones_docentes.csv` tiene **3.000 filas**, pero
solo **20 textos de comentario distintos**. Cada uno se repite muchas veces (en promedio 150
veces). Es decir, los textos únicos son apenas el **0,67 %** de las filas; el **99,33 % son
repeticiones**.

| Métrica | Valor |
|---|---|
| Filas (comentarios escritos) | 3.000 |
| Comentarios **distintos** | 20 |
| Ratio de unicidad | 20 / 3.000 = **0,67 %** |
| Filas que son repetición | 2.980 = **99,33 %** |
| Repeticiones por comentario | promedio 150 (mín. 101, máx. 233) |

## Por qué importa

Para el **análisis de sentimiento** lo que cuenta son los **textos distintos**: darle al modelo
165 veces la frase *"Excelente profesor, muy claro."* produce 165 veces la misma respuesta y no
aporta información nueva. Por eso el conjunto de evaluación real de este dataset es de **20
comentarios**, no de 3.000. (Para el modelado de `tendencia_desempeno` sí se usan las 3.000
filas, porque ahí varían los puntajes; la limitación es específica del canal de texto.)

Esto no es un error del equipo: el dataset entregado por la universidad está **plantillado /
anonimizado** (el comentario proviene de un conjunto fijo de 20 frases), algo habitual para
proteger datos reales de estudiantes y docentes.

## Detalle por comentario

Ver el gráfico [`repeticion_comentarios.png`](repeticion_comentarios.png). Frecuencia de cada
uno de los 20 textos:

| # | Veces | % del total | Comentario |
|--:|--:|--:|---|
| 1 | 233 | 7,77 % | Los temas son difíciles pero se entienden. |
| 2 | 211 | 7,03 % | La clase estuvo bien. |
| 3 | 210 | 7,00 % | Se podría mejorar un poco el material de estudio. |
| 4 | 201 | 6,70 % | Asistencia puntual, pero falta dinamismo. |
| 5 | 180 | 6,00 % | El profesor es normal, ni muy bueno ni muy malo. |
| 6 | 179 | 5,97 % | Cumple con el programa. |
| 7 | 165 | 5,50 % | Excelente profesor, muy claro. |
| 8 | 149 | 4,97 % | Resuelve las dudas con mucha paciencia. |
| 9 | 145 | 4,83 % | Se nota que sabe mucho de la materia. |
| 10 | 143 | 4,77 % | La clase es muy dinámica y entretenida. |
| 11 | 133 | 4,43 % | Los talleres son muy útiles para aprender. |
| 12 | 133 | 4,43 % | Califica de forma injusta. |
| 13 | 127 | 4,23 % | La clase es muy aburrida y monótona. |
| 14 | 126 | 4,20 % | Me inspiró a seguir aprendiendo sobre este tema. |
| 15 | 124 | 4,13 % | Los parciales no tienen nada que ver con lo visto en clase. |
| 16 | 123 | 4,10 % | No explica bien, me siento perdido. |
| 17 | 110 | 3,67 % | Explica muy bien los temas. |
| 18 | 106 | 3,53 % | Falta mucha pedagogía. |
| 19 | 101 | 3,37 % | No resuelve las dudas de los estudiantes. |
| 20 | 101 | 3,37 % | Llega tarde a las clases frecuentemente. |
| | **3.000** | **100 %** | **20 textos = todas las filas** |

## Cómo reproducir el número (para quien quiera verificarlo)

```python
import pandas as pd
df = pd.read_csv("data/raw/evaluaciones_docentes.csv")
len(df)                      # 3000 filas
df["comentario"].nunique()   # 20 textos distintos
df["comentario"].value_counts()   # cuántas veces se repite cada uno
```

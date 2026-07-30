# Rúbrica de anotación de sentimiento · v1.0

**Proyecto** Analítica Educativa — equipo Tech Tailors (Samsung Innovation Campus)
**Destinatarios** los tres anotadores del equipo
**Tiempo estimado** 30–35 minutos · ~250 comentarios
**Corpus** comentarios de estudiantes sobre docentes, en español

---

## 1 · Qué está etiquetando

No etiqueta la emoción del estudiante. **Etiqueta la señal que recibe la institución.**

Para cada comentario, una sola pregunta:

> *Si el coordinador académico leyera esto, ¿qué haría?*
>
> | Respuesta | Etiqueta |
> |---|---|
> | Reconocer al docente | **POS** |
> | Nada, no hay información sobre la que actuar | **NEU** |
> | Mirarlo más de cerca / ofrecer acompañamiento | **NEG** |

Este encuadre es deliberado. Los modelos automáticos fallan porque leen *"la clase estuvo
bien"* como entusiasmo (registro genérico de redes sociales). En un formulario de evaluación
docente, *"estuvo bien"* es el mínimo de cortesía. **Corregir eso es precisamente el objetivo
de esta anotación.** Si usted etiqueta como lo haría el modelo, el proyecto no avanza.

## 2 · Definiciones operativas

| Etiqueta | Definición | Test rápido |
|---|---|---|
| **POS** | Elogio explícito con contenido valorativo, o el docente presentado como modelo a imitar | ¿Hay una palabra que **valora**? (bueno, excelente, claro, aprendí, paciente, dinámico, el mejor) |
| **NEU** | Ni queja ni elogio: descriptivo, administrativo, cumplimiento de mínimos, elogio tibio o polaridad anulada | ¿Se limita a decir que **hubo** clase y que **pasó**? |
| **NEG** | Queja, carencia o petición de cambio dirigida al docente o su clase — **también si es suave, cortés o "constructiva"** | ¿Hay algo que el docente **debería hacer distinto**? |

## 3 · Procedimiento ordenado

**El orden es obligatorio.** La primera regla que dispara cierra el caso: no siga leyendo.

### R1 · ¿De quién habla?

- Del docente o su clase → **siga a R2**.
- De la institución, usando al docente como **modelo a imitar** → **POS**
  *"La universidad necesita más profesores como él"* → POS (aunque diga "necesita").
- Caso inverso: *"deberían reemplazarlo"* → el objeto evaluado es el docente → **NEG**.

### R2 · ¿Hay negación? (asimetría — memorícela)

| Forma | Lectura | Etiqueta |
|---|---|---|
| `no` + término **negativo** (*no está mal, no es malo, no tan malo*) | Elogio débil, tibio | **NEU** |
| `no` + término **positivo** (*no es bueno, no muy bueno, no explica bien*) | Veredicto de insuficiencia | **NEG** |

La misma partícula, direcciones opuestas: *"no está mal"* no mueve al coordinador a actuar;
*"no es bueno"* sí.

### R3 · ¿Hay queja, carencia o petición de cambio? → **NEG**

Dispara con: *falta · no explica · no resuelve · debería · podría · necesita mejorar · sería
bueno que · injusto · aburrido · confuso · llega tarde · demasiado…*

**Cuenta igual si está atenuada.** *"un poco"*, *"tal vez"*, *"se podría"* no cambian la
etiqueta: la cortesía es registro, no ausencia de crítica. Los estudiantes suavizan la crítica
hacia quien los califica; si dejamos que la suavidad mueva la etiqueta, perdemos justamente la
crítica dirigida a los docentes más temidos.

**No cuenta como queja:**
- **Comparativo sin contenido**: *"pero no el mejor"*, *"puede ser mejor"* → siga a R4.
- **Dificultad atribuida a la materia**, no al docente: *"los temas son difíciles"* → siga a R4.

**Adversativa** (*pero · aunque · sin embargo*): **evalúe solo la cláusula posterior**.
*"Buen profesor, pero no resuelve dudas"* → NEG. *"Es exigente, pero explica muy bien"* → POS.

### R4 · ¿Hay elogio con contenido valorativo? → **POS**

Dispara con: *excelente · muy bueno · explica bien · claro · aprendí mucho · paciente ·
dinámico · el mejor · me inspiró · recomendable*.

**Un intensificador convierte lo tibio en elogio**: *"es un buen profesor"* → POS ·
*"muy buen profesor"* → POS · pero *"estuvo bien"* → NEU (véase R5).

### R5 · Todo lo demás → **NEU**

- **Elogio tibio**: *estuvo bien · normal · cumple · aceptable · regular · promedio · ok*
- **Descriptivo/administrativo**: *cumple con el programa · usa diapositivas · es puntual*
- **Sin contenido evaluable**: *sin comentarios · ninguno · no aplica*
- **Mixto sin polaridad dominante**: *los temas son difíciles pero se entienden*

## 4 · Ejemplos ancla

| Comentario | Etiqueta | Regla | Por qué |
|---|:--:|:--:|---|
| Excelente profesor, muy claro. | POS | R4 | Elogio explícito con valoración |
| Explica muy bien los temas. | POS | R4 | Valora la capacidad docente |
| Es un buen profesor. | POS | R4 | "buen" es valorativo, no tibio |
| La universidad necesita más profesores como él. | POS | R1 | Modelo a imitar |
| **La clase estuvo bien.** | **NEU** | **R5** | **Elogio tibio: mínimo de cortesía, no entusiasmo** |
| Cumple con el programa. | NEU | R5 | Descriptivo, cumplimiento de mínimos |
| El profesor es normal, ni muy bueno ni muy malo. | NEU | R5 | Polaridad anulada explícitamente |
| Los temas son difíciles pero se entienden. | NEU | R3 | Dificultad de la materia, no del docente |
| No está mal. | NEU | R2 | Negación de término negativo = tibio |
| **Se podría mejorar un poco el material.** | **NEG** | **R3** | **Petición de cambio, aunque esté atenuada** |
| Asistencia puntual, pero falta dinamismo. | NEG | R3 | Adversativa: manda la cláusula posterior |
| No explica bien, me siento perdido. | NEG | R3 | Carencia explícita |
| Califica de forma injusta. | NEG | R3 | Queja directa |
| No es un buen profesor. | NEG | R2 | Negación de término positivo |

## 5 · Los dos casos que decide esta rúbrica

El proyecto detectó que todos los errores de los modelos se concentran en dos patrones. La
rúbrica los resuelve de forma explícita, y esa es la decisión que permite que el gold humano
aporte información que el modelo no tiene:

| Caso | Decisión | Fundamento |
|---|:--:|---|
| *"La clase estuvo bien"* (elogio tibio) | **NEU** | En un formulario de evaluación es cortesía mínima. Marcarlo POS infla la percepción de desempeño. |
| *"Se podría mejorar el material"* (crítica suave) | **NEG** | Es una petición de cambio. Marcarla NEU oculta una señal accionable. |

En ambos casos la lógica es la misma: **ante la duda, prevalece la utilidad para el
coordinador académico.**

## 6 · Si duda

1. Vuelva a la pregunta del §1: *¿qué haría el coordinador?*
2. Aplique las reglas **en orden**; la primera que dispara decide.
3. Marque la casilla **`dificil = 1`** y siga. No relea, no se detenga más de 15 segundos.

> Las filas marcadas como difíciles se revisan en la reunión de adjudicación. Marcar la duda es
> **información valiosa**, no un fallo: identifica dónde la rúbrica necesita afinarse.

## 7 · Errores frecuentes que debe evitar

| Error | Corrección |
|---|---|
| Etiquetar POS un comentario tibio porque "no es negativo" | Tibio es NEU. POS exige valoración explícita. |
| Etiquetar NEU una crítica suave porque "es amable" | La cortesía no cancela la crítica: es NEG. |
| Etiquetar por la primera mitad de una adversativa | Manda la cláusula **posterior** al *pero*. |
| Dejar filas en blanco | Toda fila debe tener etiqueta. Si duda, decida y marque `dificil = 1`. |
| Consultar con otro anotador | La independencia es obligatoria: sin ella no se puede medir el acuerdo. |

---

*Rúbrica v1.0 · si tras la reunión de adjudicación se modifica alguna regla, se emite v1.1 y se
re-anota solo el subconjunto afectado.*

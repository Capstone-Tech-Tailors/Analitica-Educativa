# Naturaleza y limitaciones de los datos

> Sección lista para pegar en el informe del capstone.

El conjunto de datos `evaluaciones_docentes.csv` contiene 3.000 registros de evaluación
docente (50 docentes, 7 asignaturas y 8 semestres del período 2020–2023). El diagnóstico de
calidad confirma que los datos están completos —sin valores nulos ni duplicados exactos— y
dentro de los rangos válidos, por lo que no requieren limpieza estructural.

No obstante, el campo `comentario` presenta una limitación relevante para el componente de
procesamiento de lenguaje natural. Aunque se registran 3.000 comentarios, **solo 20 son textos
distintos** (el 0,67 % de los registros); el 99,33 % restante corresponde a repeticiones, con
una frecuencia media de 150 apariciones por texto (mínimo 101, máximo 233). Varias señales
indican que este campo no proviene de escritura libre de los estudiantes, sino de un conjunto
cerrado de frases o de un proceso de generación/plantillado: (i) no existen comentarios vacíos
ni variaciones ortográficas, algo impropio de texto redactado por personas; (ii) cada una de
las 20 frases se repite de forma casi uniforme en 48 de los 50 docentes, en los 8 semestres y
en las 7 asignaturas; y (iii) el contenido del comentario y los puntajes numéricos de una misma
evaluación varían de forma independiente (por ejemplo, el comentario *"Llega tarde a las clases
frecuentemente"* coexiste con puntajes de hasta 4,4 sobre 5). Este comportamiento es coherente
con un dataset **anonimizado o preparado con fines académicos** para el reto, práctica habitual
para proteger información sensible de estudiantes y docentes.

De lo anterior se derivan tres implicaciones metodológicas: (a) el análisis de sentimiento del
texto se evalúa, en la práctica, sobre 20 plantillas, por lo que sus métricas deben
interpretarse como **validación del método** y no como desempeño extrapolable a comentarios de
texto libre reales; (b) la variable objetivo `tendencia_desempeno` está derivada por reglas y
alineada con dichas plantillas, lo que introduce cierta **circularidad** entre la etiqueta y las
variables predictoras; y (c) en consecuencia, las métricas de clasificación obtenidas
constituyen un **techo optimista** sobre datos controlados. Se recomienda confirmar la
naturaleza de los comentarios con los organizadores del reto y, para dimensionar el aporte real
del componente de NLP, validarlo con comentarios de texto libre reales cuando estén
disponibles. Estas limitaciones no comprometen la validez de la metodología propuesta, la cual
es plenamente aplicable a datos reales.

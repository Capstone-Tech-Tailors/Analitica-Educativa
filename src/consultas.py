# %%
# %pip install unidecode
# %%
import pandas as pd
import unidecode
# %%
valid_days = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado"]
get_valid_day = lambda day: next(filter(lambda valid_day: unidecode.unidecode(day.strip()).startswith(unidecode.unidecode(valid_day)), valid_days), None)
is_valid_day = lambda day: any(filter(lambda valid_day: unidecode.unidecode(day.strip()).startswith(unidecode.unidecode(valid_day)), valid_days))

df = pd.read_csv("../data/evaluaciones_docentes_sintetica_ampliada.csv", sep=",", encoding="utf-8", header="infer", dtype={
    "id_docente": "category",
    "tendencia_desempeno": "category",
    "comentario": "category",
    "asignatura": "category",
    "franja_horaria": "category",
    "id_curso_grupo": "category",
    "clases_dictadas": "Int64",
    "clases_pactadas": "Int64",
    "numero_estudiantes_aprobaron": "Int64",
    "numero_estudiantes_perdieron": "Int64",
    "numero_estudiantes_desistieron": "Int64",
    "promedio_asistencias_estudiantes": "Float64",
}, converters={
    # Hay semestres donde el docente deja de dictar una materia y necesita agregarse el semestre artificialmente.
    # Por tanto, se agrega esta transformación para más adelante apoyar a la completacion de ceros en semestres faltantes.
    "semestre": lambda s: pd.Period(s.strip().replace("-1", "Q1").replace("-2", "Q3"), freq="2Q-DEC"),
    "hora_inicio": lambda val: pd.to_datetime(val, format="%H:%M").time(),
    "hora_fin": lambda val: pd.to_datetime(val, format="%H:%M").time(),
    "dias_clase": lambda dias: tuple(get_valid_day(dia) for dia in dias.split("-") if is_valid_day(dia)),
})
df = df.convert_dtypes()

df["Cantidad de Clases Semanales"] = df["dias_clase"].apply(lambda dias: len(dias)).astype("Int64")
df["Horas Por Clase"] = ((pd.to_timedelta(df["hora_fin"].astype(str)) - pd.to_timedelta(df["hora_inicio"].astype(str))).dt.total_seconds() / 3600).astype("Int64")

# Horas efectivas de operación dirigidas a los estudiantes en el aula
df["Horas Lectivas Totales"] = df["clases_dictadas"] * df["Horas Por Clase"]
df["Horas Lectivas Por Semana"] = df["Cantidad de Clases Semanales"] * df["Horas Por Clase"]

df.dtypes
# %% [markdown]
#
# **Se evidencia que la cantidad de clases pactadas es igual a 16 veces la cantidad de clases semanales, es decir que hay 16 semanas proyectadas para cada grupo.**
#
# **En la práctica quizás reponen una o varias semanas adicionales para garantizar el cumplimiento de horas: bien sea para reponer días compensados del docente, días festivos, situaciones de fuerza mayor, etc.**
#
#
# %%
df["Horas Lectivas Teóricas"] = 16 * df["Horas Lectivas Por Semana"]
df["Horas Lectivas Planeadas"] = df["clases_pactadas"] * df["Horas Por Clase"]

(df["Horas Lectivas Teóricas"] == df["Horas Lectivas Planeadas"]).all()

# %% [markdown]
#
# **Validando la relación de horas efectivas y planeadas, se aprecia un 64% de casos en donde se incumplió con lo pactado.**
#
# %%
porcentaje_casos_incumplimiento = 100 * len(df[df["Horas Lectivas Totales"] < df["Horas Lectivas Planeadas"]]) / len(df)

porcentaje_casos_incumplimiento
# %% [markdown]
# **Se aprecia que el 41.4% de los grupos habrían subsanado la brecha de horas con 1 semana extra de clases, ya que corresponden a plazos alcanzables según el horario lectivo.**
#
# **Así mismo, existe un 16.3% de grupos que habrían necesitado dos semanas más para dar cumplimiento a las horas faltantes.**
#
# **Por último, el 6.3% de grupos habrían necesitado mucho más tiempo para cumplir.**
#
# %%
df["Discrepancia de Horas Lectivas"] = (df["Horas Lectivas Planeadas"] - df["Horas Lectivas Totales"]).astype("Int64")

mask_viabilidad_subsanado_una_semana = (
    (df["Discrepancia de Horas Lectivas"] > 0)
    # Discrepancia NO puede superar las horas máximas de una semana
    & (df["Discrepancia de Horas Lectivas"] <= df["Horas Lectivas Por Semana"])
)

mask_viabilidad_subsanado_dos_semanas = (
    (df["Discrepancia de Horas Lectivas"] > 0)
    & (df["Discrepancia de Horas Lectivas"] > df["Horas Lectivas Por Semana"])
    & (df["Discrepancia de Horas Lectivas"] <= (2 * df["Horas Lectivas Por Semana"]))
)

mask_no_viables = (
    (df["Discrepancia de Horas Lectivas"] > 0)
    & (df["Discrepancia de Horas Lectivas"] > (2 * df["Horas Lectivas Por Semana"]))
)

grupos_una_semana_mas = len(df[mask_viabilidad_subsanado_una_semana])
grupos_dos_semanas_mas = len(df[mask_viabilidad_subsanado_dos_semanas])
grupos_no_viables = len(df[mask_no_viables])

porcentaje_casos_remediables_una_semana = 100 *  grupos_una_semana_mas / len(df)
porcentaje_casos_remediables_dos_semanas = 100 *  grupos_dos_semanas_mas / len(df)
porcentaje_casos_no_viables = 100 *  grupos_no_viables / len(df)

print(
    f"Cantidad de Grupos que habrían necesitado 1 semana mas: {grupos_una_semana_mas } (el {porcentaje_casos_remediables_una_semana:.2f}%)", "\n",
    f"Cantidad de Grupos que habrían necesitado 2 semanas mas: {grupos_dos_semanas_mas } (el {porcentaje_casos_remediables_dos_semanas:.2f}%)", "\n",
    f"Cantidad de Grupos que habrían necesitado mucho mas tiempo: {grupos_no_viables} (el {porcentaje_casos_no_viables:.2f}%)"
)
# %%
seguimiento_general_docentes = (
    df.groupby(["id_docente", "semestre"], as_index=False)
    .agg(
        Cantidad_de_Materias=("asignatura", "nunique"),
        Cantidad_de_Grupos=("semestre", "size"), # Counts rows per group
        numero_estudiantes=("numero_estudiantes", "sum"),
        Asignaturas=("asignatura", lambda x: tuple(x.dropna().unique())),
        # Comentarios=("comentario", lambda x: tuple(x.dropna().unique())),
        Horas_Lectivas=("Horas Lectivas Totales", "sum"),
        Numero_Comentarios_Estables=("tendencia_desempeno", lambda x: len([tendencia for tendencia in x.dropna() if tendencia == "Estable"])),
        Numero_Comentarios_En_Riesgo=("tendencia_desempeno", lambda x: len([tendencia for tendencia in x.dropna() if tendencia == "En riesgo"])),
        Numero_Comentarios_En_Mejora=("tendencia_desempeno", lambda x: len([tendencia for tendencia in x.dropna() if tendencia == "Mejora"])),
    )
    .rename(columns={
        "Cantidad_de_Grupos": "Cantidad de Grupos",
        "Cantidad_de_Materias": "Cantidad de Materias",
        "Horas_Lectivas": "Horas Lectivas",

        "Numero_Comentarios_Estables": "Numero Comentarios Estables",
        "Numero_Comentarios_En_Riesgo": "Numero Comentarios En Riesgo",
        "Numero_Comentarios_En_Mejora": "Numero Comentarios En Mejora"
    })
    .sort_values(by=["id_docente", "semestre"], ascending=[True, True])
)

seguimiento_general_docentes["Cantidad de Materias"] = seguimiento_general_docentes["Cantidad de Materias"].astype("Int64")
seguimiento_general_docentes["Cantidad de Grupos"] = seguimiento_general_docentes["Cantidad de Grupos"].astype("Int64")
seguimiento_general_docentes["numero_estudiantes"] = seguimiento_general_docentes["numero_estudiantes"].astype("Int64")

seguimiento_general_docentes["Numero Comentarios Estables"] = seguimiento_general_docentes["Numero Comentarios Estables"].astype("Int64")
seguimiento_general_docentes["Numero Comentarios En Riesgo"] = seguimiento_general_docentes["Numero Comentarios En Riesgo"].astype("Int64")
seguimiento_general_docentes["Numero Comentarios En Mejora"] = seguimiento_general_docentes["Numero Comentarios En Mejora"].astype("Int64")

# cantidad_de_materias_que_el_docente_maneja_por_cada_semestre["Comentarios"] = cantidad_de_materias_que_el_docente_maneja_por_cada_semestre["Comentarios"].apply(list)
# cantidad_de_materias_que_el_docente_maneja_por_cada_semestre["Asignaturas"] = cantidad_de_materias_que_el_docente_maneja_por_cada_semestre["Asignaturas"].apply(list)

def agregar_metricas_generales_docente(muestras_docente):
    muestras = muestras_docente.copy(deep=True)
    muestras.reset_index(inplace=True) # drop multi-index

    muestras.reset_index(inplace=True)  # creates 'index' column with original positions
    muestras["Max Acumulado Cantidad de Materias"] = muestras["Cantidad de Materias"].cummax()
    muestras["Max Acumulado Cantidad de Grupos"] = muestras["Cantidad de Grupos"].cummax()
    muestras["Max Acumulado Numero Comentarios En Mejora"] = muestras["Numero Comentarios En Mejora"].cummax()
    muestras["Max Acumulado Horas Lectivas"] = muestras["Horas Lectivas"].cummax()

    # Campos temporales para hacerle seguimiento a la primera occurencia de maximos locales
    mask_materias = (muestras["Cantidad de Materias"] == muestras["Max Acumulado Cantidad de Materias"])
    mask_grupos = (muestras["Cantidad de Grupos"] == muestras["Max Acumulado Cantidad de Grupos"])
    mask_comentarios_en_mejora = (muestras["Numero Comentarios En Mejora"] == muestras["Max Acumulado Numero Comentarios En Mejora"])
    mask_horas_lectivas = (muestras["Horas Lectivas"] == muestras["Max Acumulado Horas Lectivas"])
    muestras["last_max_idx_materias"] = muestras["index"].where(mask_materias).ffill().astype(int)
    muestras["last_max_idx_grupos"] = muestras["index"].where(mask_grupos).ffill().astype(int)
    muestras["last_max_idx_comentarios_en_mejora"] = muestras["index"].where(mask_comentarios_en_mejora).ffill().astype(int)
    muestras["last_max_idx_horas_lectivas"] = muestras["index"].where(mask_horas_lectivas).ffill().astype(int)

    muestras["Cantidad de Semestres sin Sobrecarga de Asignaturas"] = muestras["index"] - muestras["last_max_idx_materias"]
    muestras["Cantidad de Semestres sin Sobrecarga de Grupos"] = muestras["index"] - muestras["last_max_idx_grupos"]
    # muestras["Cantidad de Semestres sin Milestone En Comentarios"] = muestras["index"] - muestras["last_max_idx_comentarios_en_mejora"]
    muestras["Cantidad de Semestres sin Sobrecarga Horaria"] = muestras["index"] - muestras["last_max_idx_horas_lectivas"]

    muestras["Indice de Carga Asignaturas"] = muestras["Cantidad de Materias"] / muestras["Max Acumulado Cantidad de Materias"]
    muestras["Indice de Carga Grupos"] = muestras["Cantidad de Grupos"] / muestras["Max Acumulado Cantidad de Grupos"]
    muestras["Indice de Carga Horaria"] = muestras["Horas Lectivas"] / muestras["Max Acumulado Horas Lectivas"]
    # muestras["Indice de Mejora Comentarios"] = muestras["Numero Comentarios En Mejora"] / muestras["Max Acumulado Numero Comentarios En Mejora"]

    muestras.drop(columns=["index", "Max Acumulado Cantidad de Materias", "Max Acumulado Cantidad de Grupos", "Max Acumulado Numero Comentarios En Mejora", "Max Acumulado Horas Lectivas", "last_max_idx_materias", "last_max_idx_grupos", "last_max_idx_comentarios_en_mejora", "last_max_idx_horas_lectivas"], inplace=True)
    muestras.set_index(["id_docente"], inplace=True)
    return muestras

seguimiento_general_docentes = (
    seguimiento_general_docentes
    .set_index(["id_docente"], append=False)
    .groupby(level=["id_docente"], group_keys=False)
    .apply(agregar_metricas_generales_docente, include_groups=False)
    .reset_index()
)

# %%
seguimiento_general_docentes
# %%
# Función para devolver la representación de un periodo a formato año-semestre (para visualizaciones, resultados finales, etc)
def period_to_string(periodo: pd.Period):
    return f"{periodo.year}-{(periodo.quarter+1)//2}"

# Más adelante para completar semestres, solo sería revisar el número de periodos entre 2 muestras.
def numero_de_periodos_entre_semestres(semestre_final: pd.Period, semestre_inicial: pd.Period):
    if pd.isna(semestre_final) or pd.isna(semestre_inicial):
        return 0
    return 1 + (semestre_final - semestre_inicial).n//2

seguimiento_docente_en_cada_asignatura = (
    df.groupby(["id_docente", "semestre", "asignatura"], as_index=False)
    .agg(
        Cantidad_de_Grupos=("semestre", "size"), # Counts rows per group
        numero_estudiantes=("numero_estudiantes", "sum"),
        puntaje_claridad=("puntaje_claridad", "mean"),
        puntaje_metodologia=("puntaje_metodologia", "mean"),
        puntaje_evaluacion=("puntaje_evaluacion", "mean"),
        Comentarios=("comentario", lambda x: tuple(x.dropna().unique())),
        Horas_Lectivas=("Horas Lectivas Totales", "sum"),
        Estudiantes_Aprobados=("numero_estudiantes_aprobaron", "sum"),
        Numero_Comentarios_Estables=("tendencia_desempeno", lambda x: len([tendencia for tendencia in x.dropna() if tendencia == "Estable"])),
        Numero_Comentarios_En_Riesgo=("tendencia_desempeno", lambda x: len([tendencia for tendencia in x.dropna() if tendencia == "En riesgo"])),
        Numero_Comentarios_En_Mejora=("tendencia_desempeno", lambda x: len([tendencia for tendencia in x.dropna() if tendencia == "Mejora"])),
    )
    .rename(columns={
        "Cantidad_de_Grupos": "Cantidad de Grupos",
        "Horas_Lectivas": "Horas Lectivas",
        "Estudiantes_Aprobados": "Estudiantes Aprobados",

        "Numero_Comentarios_Estables": "Numero Comentarios Estables",
        "Numero_Comentarios_En_Riesgo": "Numero Comentarios En Riesgo",
        "Numero_Comentarios_En_Mejora": "Numero Comentarios En Mejora"
    })
    .sort_values(by=["id_docente", "asignatura", "semestre"], ascending=[True, True, True])
)

seguimiento_docente_en_cada_asignatura["Cantidad de Grupos"] = seguimiento_docente_en_cada_asignatura["Cantidad de Grupos"].astype("Int64")
seguimiento_docente_en_cada_asignatura["numero_estudiantes"] = seguimiento_docente_en_cada_asignatura["numero_estudiantes"].astype("Int64")
seguimiento_docente_en_cada_asignatura["Horas Lectivas"] = seguimiento_docente_en_cada_asignatura["Horas Lectivas"].astype("Int64")
seguimiento_docente_en_cada_asignatura["Estudiantes Aprobados"] = seguimiento_docente_en_cada_asignatura["Estudiantes Aprobados"].astype("Int64")

seguimiento_docente_en_cada_asignatura["Numero Comentarios Estables"] = seguimiento_docente_en_cada_asignatura["Numero Comentarios Estables"].astype("Int64")
seguimiento_docente_en_cada_asignatura["Numero Comentarios En Riesgo"] = seguimiento_docente_en_cada_asignatura["Numero Comentarios En Riesgo"].astype("Int64")
seguimiento_docente_en_cada_asignatura["Numero Comentarios En Mejora"] = seguimiento_docente_en_cada_asignatura["Numero Comentarios En Mejora"].astype("Int64")

def completar_semestres(muestras_docente):

    muestras = muestras_docente.copy(deep=True)
    muestras.reset_index(inplace=True)

    # Campos auxiliares para completación de semestres
    muestras["semestre previo"] = muestras.semestre.shift(1)
    muestras["Numero de Periodos entre Semestres"] = muestras.apply(lambda row: numero_de_periodos_entre_semestres(row["semestre"], row["semestre previo"]), axis=1)

    # Util para darle más contexto al área usuaria y a modelos de inteligencia artificial
    muestras["Semestres Desde Ultima Calificación"] = pd.NA
    muestras.iloc[1:, muestras.columns.get_loc("Semestres Desde Ultima Calificación")] = 1

    gaps = muestras[muestras["Numero de Periodos entre Semestres"] > 2].index.tolist()
    if len(gaps) == 0:
        return muestras_docente

    fields = [
        "semestre",
        "Numero de Periodos entre Semestres",
        "semestre previo",
        "Cantidad de Grupos",
        "Semestres Desde Ultima Calificación",
        "numero_estudiantes",
        "puntaje_claridad",
        "puntaje_metodologia",
        "puntaje_evaluacion",

        "Comentarios",
        "Horas Lectivas",
        "Estudiantes Aprobados",
        "Numero Comentarios Estables",
        "Numero Comentarios En Riesgo",
        "Numero Comentarios En Mejora",
    ]

    # Limita hasta cuantos semestres puedo completar hacia atrás, de momento deja hasta 1000.
    step = 1e-3
    for idx_grupito in gaps:
        semestres_faltantes = muestras.loc[idx_grupito]["Numero de Periodos entre Semestres"] - 2
        muestras.loc[idx_grupito, ["Semestres Desde Ultima Calificación"]] = [muestras.loc[idx_grupito]["Numero de Periodos entre Semestres"] - 1]

        idx_semestre = idx_grupito
        for sem_faltante in range(semestres_faltantes):
            # Clonado y sobre-escritura de campos, asignando el 0 en Cantidad de Grupos y fijando la Última Vez Que Fué Calificado.
            muestras.loc[idx_semestre - step] = muestras.loc[idx_semestre].copy()
            muestras.loc[idx_semestre - step, fields] = [
                muestras.loc[idx_semestre].semestre - 1,
                0,
                pd.NaT,
                pd.NA,
                semestres_faltantes - sem_faltante,
                pd.NA,
                pd.NA,
                pd.NA,
                pd.NA,

                pd.NA,
                pd.NA,
                pd.NA,
                pd.NA,
                pd.NA,
                pd.NA,
            ]
            idx_semestre = idx_semestre - step

    # Estos 2 pasos ordenan correctamente lo que se agregó
    muestras.sort_index(inplace=True)
    muestras.reset_index(drop=True, inplace=True)

    # Ya podemos eliminar los campos auxiliares
    muestras.drop(columns=["semestre previo", "Numero de Periodos entre Semestres"], inplace=True)
    muestras.set_index(["id_docente", "asignatura"], inplace=True)

    muestras["Semestres Desde Ultima Calificación"] = muestras["Semestres Desde Ultima Calificación"].astype("Int64")
    muestras["Cantidad de Grupos"] = muestras["Cantidad de Grupos"].astype("Int64")

    return muestras

seguimiento_docente_en_cada_asignatura = (
    seguimiento_docente_en_cada_asignatura
    .set_index(["id_docente", "asignatura"], append=False)
    .groupby(level=["id_docente", "asignatura"], group_keys=False)
    .apply(completar_semestres, include_groups=False)
    .reset_index()
)

def agregar_metricas_docente_por_asignatura(muestras_docente):
    muestras = muestras_docente.copy(deep=True)

    muestras.reset_index(inplace=True)

    muestras["Diferencia en Cantidad de Grupos con Semestre Anterior"] = (
            muestras["Cantidad de Grupos"]
            - muestras["Cantidad de Grupos"].shift(1)
    )

    muestras["Diferencia en Semestres Desde Ultima Calificación"] = (
            muestras["Semestres Desde Ultima Calificación"]
            - muestras["Semestres Desde Ultima Calificación"].shift(1)
    )

    muestras["Reingreso"] = (
            ( ~ muestras["Cantidad de Grupos"].isna() )
            & muestras["Diferencia en Cantidad de Grupos con Semestre Anterior"].isna()
            & (muestras["Diferencia en Semestres Desde Ultima Calificación"] > 0)
    )

    muestras["Reingreso"] = muestras.apply(lambda row: pd.NA if row["Reingreso"] is False and pd.isna(row["Cantidad de Grupos"]) else row["Reingreso"], axis=1)

    reingresos_acumulados = muestras["Reingreso"].cumsum()
    indice_rotacion = reingresos_acumulados / (reingresos_acumulados.index + 1)

    muestras["Indice de Reingreso"] = indice_rotacion

    muestras.drop(columns=["Diferencia en Cantidad de Grupos con Semestre Anterior", "Diferencia en Semestres Desde Ultima Calificación"], inplace=True)

    muestras.set_index(["id_docente", "asignatura"], inplace=True)

    return muestras

seguimiento_docente_en_cada_asignatura = (
    seguimiento_docente_en_cada_asignatura
    .set_index(["id_docente", "asignatura"], append=False)
    .groupby(level=["id_docente", "asignatura"], group_keys=False)
    .apply(agregar_metricas_docente_por_asignatura, include_groups=False)
    .reset_index()
)

seguimiento_docente_en_cada_asignatura = seguimiento_docente_en_cada_asignatura.dropna(subset=["Reingreso"])

# %%
seguimiento_docente_en_cada_asignatura
# %%
seguimiento_asignaturas = (
    df.groupby(["asignatura", "semestre"], as_index=False)
    .agg(
        Cantidad_de_Docentes=("id_docente", "nunique"),
        Cantidad_de_Grupos=("semestre", "size"), # Counts rows per group
        numero_estudiantes=("numero_estudiantes", "sum"),
        Asistencia_Tipica_Estudiantes=("promedio_asistencias_estudiantes", "sum"),
        Horas_Lectivas=("Horas Lectivas Totales", "sum"),
        Estudiantes_Aprobados=("numero_estudiantes_aprobaron", "sum"),
        Estudiantes_Perdieron=("numero_estudiantes_perdieron", "sum"),
        Estudiantes_Desistieron=("numero_estudiantes_desistieron", "sum"),
        Clases_Dictadas=("clases_dictadas", "sum"),
        # Franja_Horaria=("franja_horaria", lambda x: "Mixta" if len(x.dropna().unique()) > 1 else x[0]),
    )
    .rename(columns={
        "Cantidad_de_Grupos": "Cantidad de Grupos",
        "Cantidad_de_Docentes": "Cantidad de Docentes",
        "Asistencia_Tipica_Estudiantes": "Asistencia Típica de Estudiantes",
        "Horas_Lectivas": "Horas Lectivas",
        "Estudiantes_Aprobados": "Estudiantes Aprobados",
        "Estudiantes_Perdieron": "Estudiantes Que Perdieron",
        "Estudiantes_Desistieron": "Estudiantes Que Desistieron",
        "Clases_Dictadas": "Clases Dictadas",
        # "Franja_Horaria": "Franja Horaria",
    })
    .sort_values(by=["asignatura", "semestre"], ascending=[True, True])
)

seguimiento_asignaturas["Cantidad de Docentes"] = seguimiento_asignaturas["Cantidad de Docentes"].astype("Int64")
seguimiento_asignaturas["Cantidad de Grupos"] = seguimiento_asignaturas["Cantidad de Grupos"].astype("Int64")
seguimiento_asignaturas["numero_estudiantes"] = seguimiento_asignaturas["numero_estudiantes"].astype("Int64")

seguimiento_asignaturas["Asistencia Típica de Estudiantes"] = seguimiento_asignaturas["Asistencia Típica de Estudiantes"].astype("Float64")
seguimiento_asignaturas["Horas Lectivas"] = seguimiento_asignaturas["Horas Lectivas"].astype("Int64")
seguimiento_asignaturas["Estudiantes Aprobados"] = seguimiento_asignaturas["Estudiantes Aprobados"].astype("Int64")
seguimiento_asignaturas["Clases Dictadas"] = seguimiento_asignaturas["Clases Dictadas"].astype("Int64")

# seguimiento_asignaturas["Franja Horaria"] = seguimiento_asignaturas["Franja Horaria"].astype("category")

seguimiento_asignaturas

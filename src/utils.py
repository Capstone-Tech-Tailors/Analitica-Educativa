import pandas as pd

def agregar_metricas_generales_docente(muestras_docente: pd.DataFrame) -> pd.DataFrame:
    muestras = muestras_docente.copy(deep=True)
    muestras.reset_index(inplace=True) # drop multi-index

    muestras.reset_index(inplace=True)  # creates 'index' column with original positions
    muestras["Max Acumulado Cantidad Asignaturas"] = muestras["Cantidad Asignaturas"].cummax()
    muestras["Max Acumulado Cantidad Grupos"] = muestras["Cantidad Grupos"].cummax()
    muestras["Max Acumulado Horas Lectivas"] = muestras["Horas Lectivas"].cummax()

    # Campos temporales para hacerle seguimiento a la primera occurencia de maximos locales
    mask_materias = (muestras["Cantidad Asignaturas"] == muestras["Max Acumulado Cantidad Asignaturas"])
    mask_grupos = (muestras["Cantidad Grupos"] == muestras["Max Acumulado Cantidad Grupos"])
    mask_horas_lectivas = (muestras["Horas Lectivas"] == muestras["Max Acumulado Horas Lectivas"])
    muestras["last_max_idx_materias"] = muestras["index"].where(mask_materias).ffill().astype(int)
    muestras["last_max_idx_grupos"] = muestras["index"].where(mask_grupos).ffill().astype(int)
    muestras["last_max_idx_horas_lectivas"] = muestras["index"].where(mask_horas_lectivas).ffill().astype(int)

    muestras["Semestres Sin Sobrecarga de Asignaturas"] = muestras["index"] - muestras["last_max_idx_materias"]
    muestras["Semestres Sin Sobrecarga de Grupos"] = muestras["index"] - muestras["last_max_idx_grupos"]
    muestras["Semestres Sin Sobrecarga Horaria"] = muestras["index"] - muestras["last_max_idx_horas_lectivas"]

    muestras["Indice Carga Asignaturas"] = muestras["Cantidad Asignaturas"] / muestras["Max Acumulado Cantidad Asignaturas"]
    muestras["Indice Carga Grupos"] = muestras["Cantidad Grupos"] / muestras["Max Acumulado Cantidad Grupos"]
    muestras["Indice Carga Horaria"] = muestras["Horas Lectivas"] / muestras["Max Acumulado Horas Lectivas"]

    muestras.drop(columns=[
        "index",
        "Max Acumulado Cantidad Asignaturas",
        "Max Acumulado Cantidad Grupos",
        "Max Acumulado Horas Lectivas",
        "last_max_idx_materias", "last_max_idx_grupos", "last_max_idx_horas_lectivas"
    ], inplace=True)
    muestras.set_index(["Docente"], inplace=True)
    return muestras

def period_to_string(periodo: pd.Period):
    return f"{periodo.year}-{(periodo.quarter+1)//2}"

def numero_de_periodos_entre_semestres(semestre_final: pd.Period, semestre_inicial: pd.Period):
    if pd.isna(semestre_final) or pd.isna(semestre_inicial):
        return 0
    return 1 + (semestre_final - semestre_inicial).n//2

def completar_semestres(muestras_docente: pd.DataFrame) -> pd.DataFrame:

    muestras = muestras_docente.copy(deep=True)
    muestras.reset_index(inplace=True)

    # Campos auxiliares para completación de semestres
    muestras["Semestre Previo"] = muestras.Semestre.shift(1)
    muestras["Numero Periodos entre Semestres"] = muestras.apply(lambda row: numero_de_periodos_entre_semestres(row["Semestre"], row["Semestre Previo"]), axis=1)

    # Util para darle más contexto al área usuaria y a modelos de inteligencia artificial
    muestras["Semestres Desde Ultima Calificación"] = pd.NA
    muestras.iloc[1:, muestras.columns.get_loc("Semestres Desde Ultima Calificación")] = 1

    gaps = muestras[muestras["Numero Periodos entre Semestres"] > 2].index.tolist()
    if len(gaps) == 0:
        return muestras_docente

    fields = [
        "Semestre",
        "Numero Periodos entre Semestres",
        "Semestre Previo",
        "Cantidad Grupos",
        "Semestres Desde Ultima Calificación",
        "Numero Estudiantes",
        "Puntaje Claridad",
        "Puntaje Metodología",
        "Puntaje Evaluación",

        "Comentarios",
        "Horas Lectivas",
        "Estudiantes Aprobados",
        "Comentarios Estables",
        "Comentarios En Riesgo",
        "Comentarios En Mejora",
    ]

    # Limita hasta cuantos semestres puedo completar hacia atrás, de momento deja hasta 1000.
    step = 1e-3
    for idx_grupito in gaps:
        semestres_faltantes = muestras.loc[idx_grupito]["Numero Periodos entre Semestres"] - 2
        muestras.loc[idx_grupito, ["Semestres Desde Ultima Calificación"]] = [muestras.loc[idx_grupito]["Numero Periodos entre Semestres"] - 1]

        idx_semestre = idx_grupito
        for sem_faltante in range(semestres_faltantes):
            # Clonado y sobre-escritura de campos, asignando el 0 en Cantidad de Grupos y fijando la Última Vez Que Fué Calificado.
            muestras.loc[idx_semestre - step] = muestras.loc[idx_semestre].copy()
            muestras.loc[idx_semestre - step, fields] = [
                muestras.loc[idx_semestre].Semestre - 1,
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
    muestras.drop(columns=["Semestre Previo", "Numero Periodos entre Semestres"], inplace=True)
    muestras.set_index(["Docente", "Asignatura"], inplace=True)

    muestras["Semestres Desde Ultima Calificación"] = muestras["Semestres Desde Ultima Calificación"].astype("Int64")
    muestras["Cantidad Grupos"] = muestras["Cantidad Grupos"].astype("Int64")

    return muestras

def agregar_metricas_docente_por_asignatura(muestras_docente: pd.DataFrame) -> pd.DataFrame:
    muestras = muestras_docente.copy(deep=True)

    muestras.reset_index(inplace=True)

    muestras["Diferencia Cantidad Grupos con Semestre Anterior"] = (
        muestras["Cantidad Grupos"]
        - muestras["Cantidad Grupos"].shift(1)
    )

    muestras["Diferencia Semestres Desde Ultima Calificación"] = (
        muestras["Semestres Desde Ultima Calificación"]
        - muestras["Semestres Desde Ultima Calificación"].shift(1)
    )

    muestras["Reingreso"] = (
        ( ~ muestras["Cantidad Grupos"].isna() )
        & muestras["Diferencia Cantidad Grupos con Semestre Anterior"].isna()
        & (muestras["Diferencia Semestres Desde Ultima Calificación"] > 0)
    )

    muestras["Reingreso"] = muestras.apply(lambda row: pd.NA if row["Reingreso"] is False and pd.isna(row["Cantidad Grupos"]) else row["Reingreso"], axis=1)

    reingresos_acumulados = muestras["Reingreso"].cumsum()
    indice_rotacion = reingresos_acumulados / (reingresos_acumulados.index + 1)

    muestras["Indice Reingreso"] = indice_rotacion

    muestras.drop(columns=["Diferencia Cantidad Grupos con Semestre Anterior", "Diferencia Semestres Desde Ultima Calificación"], inplace=True)

    muestras.set_index(["Docente", "Asignatura"], inplace=True)

    return muestras

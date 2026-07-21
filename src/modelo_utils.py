"""Utilidades del modelo de tendencia docente (equipo Tech Tailors).

Este módulo se importa desde el notebook de modelado y desde producción, para que
el artefacto `.pkl` del campeón sea cargable sin depender del notebook.
"""
from __future__ import annotations
import numpy as np
from sklearn.base import BaseEstimator, ClassifierMixin
from sklearn.metrics import f1_score

CLASES = np.array(["En riesgo", "Estable", "Mejora"])
MAPA_SENTIMIENTO = {"NEG": -1, "NEU": 0, "POS": 1}

# Gold standard de los 20 comentarios plantilla (consenso de 3 transformers + corrección
# manual). Se embebe aquí para que el notebook de modelado sea autónomo: puede reconstruir
# `sentimiento_final` a partir del dataset crudo sin depender de notebooks previos.
GOLD_COMENTARIOS = {
    "No resuelve las dudas de los estudiantes.": "NEG",
    "Falta mucha pedagogía.": "NEG",
    "Califica de forma injusta.": "NEG",
    "No explica bien, me siento perdido.": "NEG",
    "Asistencia puntual, pero falta dinamismo.": "NEG",
    "Llega tarde a las clases frecuentemente.": "NEG",
    "La clase es muy aburrida y monótona.": "NEG",
    "Se podría mejorar un poco el material de estudio.": "NEG",
    "Los temas son difíciles pero se entienden.": "NEU",
    "El profesor es normal, ni muy bueno ni muy malo.": "NEU",
    "Los parciales no tienen nada que ver con lo visto en clase.": "NEG",
    "Se nota que sabe mucho de la materia.": "NEU",
    "Resuelve las dudas con mucha paciencia.": "NEU",
    "Cumple con el programa.": "NEU",
    "Excelente profesor, muy claro.": "POS",
    "La clase estuvo bien.": "NEU",
    "Los talleres son muy útiles para aprender.": "POS",
    "Explica muy bien los temas.": "POS",
    "Me inspiró a seguir aprendiendo sobre este tema.": "POS",
    "La clase es muy dinámica y entretenida.": "POS",
}

# Nombres posibles del CSV de evaluaciones (procesado o crudo), en orden de preferencia.
CANDIDATOS_CSV = [
    "evaluaciones_con_sentimiento.csv",
    "Evaluaciones docentes - Evaluaciones docentes.csv",
    "evaluaciones_docentes.csv",
]


def cargar_dataset(ruta=None):
    """Carga el dataset y garantiza la columna `sentimiento_final` (gold), sin depender
    de notebooks previos ni del directorio de trabajo.

    Estrategia: usa `ruta` si se indica; si no, prueba los nombres conocidos y, como último
    recurso, cualquier CSV del directorio con las columnas `comentario` y
    `tendencia_desempeno`. Si al CSV le falta `sentimiento_final`, la reconstruye desde
    `GOLD_COMENTARIOS`. Funciona igual en local y en Google Colab.
    """
    import os
    import glob
    import pandas as pd

    candidatos = [ruta] if ruta else []
    # Rutas del proyecto (data/processed y data/raw) si el módulo se usa dentro del repo.
    try:
        from . import rutas
        candidatos += [str(rutas.datos_processed("evaluaciones_con_sentimiento.csv")),
                       str(rutas.datos_raw("evaluaciones_docentes.csv"))]
    except Exception:
        pass
    candidatos += CANDIDATOS_CSV
    elegido = next((c for c in candidatos if c and os.path.exists(c)), None)
    if elegido is None:
        for f in sorted(glob.glob("*.csv")):
            try:
                cols = pd.read_csv(f, nrows=1).columns
            except Exception:
                continue
            if {"comentario", "tendencia_desempeno"}.issubset(cols):
                elegido = f
                break
    if elegido is None:
        raise FileNotFoundError(
            "No encuentro el CSV de evaluaciones en el directorio actual. Coloca "
            "'evaluaciones_con_sentimiento.csv' o 'Evaluaciones docentes - Evaluaciones "
            "docentes.csv' junto al notebook (en Colab, súbelo con files.upload()).")

    df = pd.read_csv(elegido)
    if "sentimiento_final" not in df.columns:
        df["sentimiento_final"] = df["comentario"].map(GOLD_COMENTARIOS)
    faltan = int(df["sentimiento_final"].isna().sum())
    if faltan:
        sin = df.loc[df["sentimiento_final"].isna(), "comentario"].unique()[:3]
        raise ValueError(
            f"{faltan} filas sin etiqueta gold (comentarios nuevos no vistos: {list(sin)}). "
            "Amplía GOLD_COMENTARIOS o regenera el sentimiento con el pipeline transformer.")
    return df, elegido


class ReglaUmbrales(BaseEstimator, ClassifierMixin):
    """Sistema de reglas de 2 umbrales sobre el puntaje promedio, con override
    opcional por sentimiento. Interfaz sklearn (fit/predict) para compararlo y
    exportarlo igual que los modelos de ML.

    - Si `usar_sentimiento=False`: reproduce el sistema de reglas actual.
    - Si `usar_sentimiento=True`: un comentario negativo no puede clasificarse
      'Mejora' (se degrada a 'Estable') y uno positivo no puede ser 'En riesgo'
      (sube a 'Estable').

    Los umbrales se optimizan en `fit` maximizando macro-F1.
    """

    def __init__(self, col_promedio="puntaje_promedio",
                 col_sentimiento="sentimiento_gold_score", usar_sentimiento=False,
                 paso=0.05):
        self.col_promedio = col_promedio
        self.col_sentimiento = col_sentimiento
        self.usar_sentimiento = usar_sentimiento
        self.paso = paso

    def _aplicar(self, prom, sent, t_bajo, t_alto):
        pred = np.where(prom < t_bajo, "En riesgo",
                        np.where(prom > t_alto, "Mejora", "Estable"))
        if self.usar_sentimiento and sent is not None:
            pred = np.where((pred == "Mejora") & (sent < 0), "Estable", pred)
            pred = np.where((pred == "En riesgo") & (sent > 0), "Estable", pred)
        return pred

    def fit(self, X, y):
        prom = np.asarray(X[self.col_promedio])
        sent = np.asarray(X[self.col_sentimiento]) if self.usar_sentimiento else None
        y = np.asarray(y)
        mejor = (-1.0, (3.2, 4.2))
        for t_bajo in np.arange(2.6, 3.9, self.paso):
            for t_alto in np.arange(t_bajo + 0.1, 4.8, self.paso):
                f1 = f1_score(y, self._aplicar(prom, sent, t_bajo, t_alto), average="macro")
                if f1 > mejor[0]:
                    mejor = (f1, (round(float(t_bajo), 2), round(float(t_alto), 2)))
        self.t_bajo_, self.t_alto_ = mejor[1]
        self.f1_train_ = mejor[0]
        self.classes_ = CLASES.copy()
        return self

    def predict(self, X):
        prom = np.asarray(X[self.col_promedio])
        sent = np.asarray(X[self.col_sentimiento]) if self.usar_sentimiento else None
        return self._aplicar(prom, sent, self.t_bajo_, self.t_alto_)


class ClasificadorConUmbralRiesgo(BaseEstimator, ClassifierMixin):
    """Envuelve un clasificador probabilístico y aplica un umbral de decisión propio para
    la clase 'En riesgo': predice 'En riesgo' si P(En riesgo) >= umbral_riesgo; si no,
    la clase más probable entre las demás. Sirve para subir el recall de 'En riesgo'
    (métrica de negocio) a costa de algo de precisión. `predict_proba` queda intacto.
    """

    def __init__(self, base, umbral_riesgo=0.5):
        self.base = base
        self.umbral_riesgo = umbral_riesgo

    def fit(self, X, y):
        self.base.fit(X, y)
        self.classes_ = np.asarray(self.base.classes_)
        self.idx_riesgo_ = int(np.where(self.classes_ == "En riesgo")[0][0])
        return self

    def predict_proba(self, X):
        return self.base.predict_proba(X)

    def predict(self, X):
        P = self.base.predict_proba(X)
        pr = P[:, self.idx_riesgo_]
        otras = [i for i in range(len(self.classes_)) if i != self.idx_riesgo_]
        pred = np.where(
            pr >= self.umbral_riesgo, "En riesgo",
            self.classes_[np.array(otras)[np.argmax(P[:, otras], axis=1)]])
        return pred


def umbral_para_recall(y_true, p_riesgo, objetivo=0.985):
    """Mayor umbral sobre P(En riesgo) que aún alcanza el recall objetivo de 'En riesgo'.
    Devolver el mayor umbral que cumple minimiza las falsas alarmas manteniendo la
    sensibilidad pedida."""
    from sklearn.metrics import recall_score
    y_bin = np.where(np.asarray(y_true) == "En riesgo", "En riesgo", "otro")
    mejor = 0.01
    for t in np.linspace(0.01, 0.95, 95):
        pred = np.where(np.asarray(p_riesgo) >= t, "En riesgo", "otro")
        r = recall_score(y_bin, pred, labels=["En riesgo"], average=None)[0]
        if r >= objetivo:
            mejor = float(t)
    return round(mejor, 3)


def construir_features(df, columna_sentimiento="sentimiento_final"):
    """Devuelve el DataFrame de features del modelo a partir del dataset crudo.

    Excluidas a propósito (ver informe de revisión):
      - delta_semestre: fuga del semestre actual.
      - hist_prom_previo / id_docente / semestre: sin poder predictivo / alta cardinalidad.
      - puntaje_promedio se conserva SOLO para la regla; los modelos de ML usan los
        3 puntajes individuales para no duplicar la señal.
    """
    X = df.copy()
    X["puntaje_promedio"] = X[["puntaje_claridad", "puntaje_metodologia",
                                "puntaje_evaluacion"]].mean(axis=1)
    X["sentimiento_gold_score"] = X[columna_sentimiento].map(MAPA_SENTIMIENTO)
    cols = ["puntaje_claridad", "puntaje_metodologia", "puntaje_evaluacion",
            "puntaje_promedio", "numero_estudiantes", "sentimiento_gold_score",
            "asignatura"]
    return X[cols]


def predecir_tendencia(modelo, puntaje_claridad, puntaje_metodologia,
                       puntaje_evaluacion, sentimiento, numero_estudiantes=30,
                       asignatura="Matemáticas Básicas"):
    """Predicción de una evaluación individual con el modelo campeón cargado.

    `sentimiento` admite 'POS'/'NEU'/'NEG' o -1/0/1.
    Devuelve (clase, probabilidades|None).
    """
    import pandas as pd
    score = MAPA_SENTIMIENTO.get(sentimiento, sentimiento)
    prom = (puntaje_claridad + puntaje_metodologia + puntaje_evaluacion) / 3
    fila = pd.DataFrame([{
        "puntaje_claridad": puntaje_claridad,
        "puntaje_metodologia": puntaje_metodologia,
        "puntaje_evaluacion": puntaje_evaluacion,
        "puntaje_promedio": prom,
        "numero_estudiantes": numero_estudiantes,
        "sentimiento_gold_score": score,
        "asignatura": asignatura,
    }])
    clase = modelo.predict(fila)[0]
    proba = None
    if hasattr(modelo, "predict_proba"):
        p = modelo.predict_proba(fila)[0]
        proba = dict(zip(modelo.classes_, np.round(p, 3)))
    return clase, proba

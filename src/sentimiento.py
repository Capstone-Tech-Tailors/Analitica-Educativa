"""Análisis de sentimiento en español consolidando 3 modelos preentrenados.

Envuelve los tres modelos que el proyecto evalúa y expone una interfaz única con
votación por mayoría. No entrena nada: usa modelos ya entrenados (transfer learning).

Uso:
    from src.sentimiento import AnalizadorSentimiento
    an = AnalizadorSentimiento()
    an.clasificar("Excelente profesor, muy claro.")
    # {'texto': ..., 'robertuito': 'POS', 'beto': 'POS', 'xlmr': 'POS', 'consenso': 'POS'}
"""
from __future__ import annotations
from collections import Counter

# Modelos de sentimiento en español evaluados en el proyecto.
MODELOS = {
    "robertuito": "pysentimiento/robertuito-sentiment-analysis",
    "beto": "finiteautomata/beto-sentiment-analysis",
    "xlmr": "cardiffnlp/twitter-xlm-roberta-base-sentiment",
}

# Normalización de etiquetas al esquema común POS / NEU / NEG.
_MAPA = {
    "POS": "POS", "POSITIVE": "POS", "P": "POS",
    "NEU": "NEU", "NEUTRAL": "NEU",
    "NEG": "NEG", "NEGATIVE": "NEG", "N": "NEG",
}


def normalizar(label):
    """Lleva la etiqueta de cualquier modelo al esquema POS/NEU/NEG."""
    return _MAPA.get(str(label).upper(), str(label).upper())


class AnalizadorSentimiento:
    """Clasificador de sentimiento por consenso de 3 modelos (carga perezosa)."""

    def __init__(self, modelos=None, desempate="robertuito"):
        self.nombres = list(modelos) if modelos else list(MODELOS)
        self.desempate = desempate
        self._pipes = {}

    def _cargar(self):
        if self._pipes:
            return
        from transformers import pipeline
        for n in self.nombres:
            self._pipes[n] = pipeline("sentiment-analysis", model=MODELOS[n])

    def clasificar(self, textos):
        """Clasifica un texto o una lista. Devuelve dict (o lista de dicts) con la
        etiqueta de cada modelo y el consenso por mayoría (desempate configurable
        cuando los tres discrepan)."""
        unico = isinstance(textos, str)
        lista = [textos] if unico else list(textos)
        self._cargar()
        preds = {n: [normalizar(r["label"]) for r in self._pipes[n](lista)] for n in self.nombres}
        filas = []
        for i, t in enumerate(lista):
            votos = {n: preds[n][i] for n in self.nombres}
            conteo = Counter(votos.values())
            etiqueta, maxv = conteo.most_common(1)[0]
            if maxv == 1:  # los tres discrepan -> desempate
                etiqueta = votos.get(self.desempate, etiqueta)
            filas.append({"texto": t, **votos, "consenso": etiqueta})
        return filas[0] if unico else filas

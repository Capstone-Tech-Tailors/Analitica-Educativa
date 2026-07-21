"""Resolución de rutas del proyecto, independiente del directorio de trabajo.

Permite que los notebooks —ubicados en subcarpetas— encuentren `data/`, `models/` y `src/`
sin rutas relativas frágiles. Uso típico desde un notebook:

    import sys, pathlib
    RAIZ = next(p for p in [pathlib.Path.cwd(), *pathlib.Path.cwd().parents] if (p / 'src').is_dir())
    sys.path.insert(0, str(RAIZ))
    from src import rutas
    df = pd.read_csv(rutas.datos_raw())
"""
from __future__ import annotations
from pathlib import Path

# Marcadores que identifican la raíz del proyecto.
_MARCADORES = ("src", "data")


def raiz_proyecto(inicio=None):
    """Sube desde `inicio` (o el CWD) hasta la carpeta que contiene `src/` y `data/`."""
    p = Path(inicio or Path.cwd()).resolve()
    for d in [p, *p.parents]:
        if all((d / m).is_dir() for m in _MARCADORES):
            return d
    raise FileNotFoundError(
        "No encuentro la raíz del proyecto (una carpeta con 'src/' y 'data/'). "
        "Ejecuta el notebook dentro del repositorio.")


def datos_raw(nombre="evaluaciones_docentes.csv"):
    """Ruta a un archivo dentro de data/raw/."""
    return raiz_proyecto() / "data" / "raw" / nombre


def datos_processed(nombre="evaluaciones_con_sentimiento.csv"):
    """Ruta a un archivo dentro de data/processed/."""
    return raiz_proyecto() / "data" / "processed" / nombre


def dir_modelos():
    """Carpeta de artefactos de modelo (analisis_datos/models/), creada si no existe."""
    d = raiz_proyecto() / "analisis_datos" / "models"
    d.mkdir(parents=True, exist_ok=True)
    return d

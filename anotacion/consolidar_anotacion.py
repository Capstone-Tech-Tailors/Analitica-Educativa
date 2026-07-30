"""Consolida las planillas anotadas: control de calidad, acuerdo entre anotadores y gold final.

Lee   : anotacion/anotacion_A*.xlsx (devueltas por los anotadores) + _clave_maestra.csv
Escribe: data/processed/gold_humano_eval.csv   (bloque EVAL adjudicado -> evaluación)
         data/processed/train_humano.csv       (bloque TRAIN -> entrenamiento)
         anotacion/reporte_acuerdo.md          (informe de acuerdo y control de calidad)

Métricas (ver PROTOCOLO_ANOTACION.md §6):
  - α de Krippendorff nominal .... TITULAR (admite diseño incompleto)
  - α de Krippendorff ordinal .... diagnóstico: la brecha con la nominal revela el tipo de desacuerdo
  - Fleiss κ ..................... secundario, convención de la literatura NLP
  - Cohen κ por pares ............ detecta anotadores atípicos
  - Acuerdo observado P_o ........ obligatorio junto a κ (paradoja de kappa)

Uso:  python anotacion/consolidar_anotacion.py
"""
from __future__ import annotations

import sys
from collections import Counter
from pathlib import Path

import numpy as np
import pandas as pd

RAIZ = next(p for p in [Path.cwd(), *Path.cwd().parents] if (p / "src").is_dir())
sys.path.insert(0, str(RAIZ))
from src import rutas  # noqa: E402
from src.acuerdo import (fleiss_kappa, krippendorff_alpha,  # noqa: E402
                         mean_pairwise_cohen, observed_agreement_triples)

ETIQUETAS = ["NEG", "NEU", "POS"]          # orden ordinal: NEG < NEU < POS
IDX = {e: i for i, e in enumerate(ETIQUETAS)}
DIR = RAIZ / "anotacion"

# Interpretación de Landis & Koch
ESCALA = [(0.20, "pobre"), (0.40, "aceptable"), (0.60, "moderado"),
          (0.80, "sustancial"), (1.01, "casi perfecto")]


# ─────────────────────────── Exclusión de ítems no evaluables ───────────────────────────
# Lista explícita y auditable (preferida a una heurística frágil: son pocos ítems y la
# decisión debe poder revisarse). Se apoya en el motivo "sin_sentido" marcado por los
# anotadores, pero la clasificación final es una decisión metodológica documentada.
#
# NO se excluyen los comentarios que confundieron al anotador pero SÍ tienen polaridad
# (sarcasmo, metáfora, elogio tibio): eliminarlos dejaría el gold solo con casos fáciles
# e inflaría artificialmente las métricas.

ILEGIBLE = {                      # secuencias sin significado: nadie puede etiquetarlas
    "gseb ndfg",
    "fgfhdo kruyriewto87to87ruirtrierui rfiuoe yreg irye ire iid ore oy iierw ie re yror yuryureyoiryoe",
}
SIN_CONTENIDO = {                 # legibles, pero no dicen nada del docente
    "No.", "Ninguno.", "Nada.", "Profesor.", "Está dibujando.",
    "considérenos, por favor.", "No tengo nada que decir sobre ella.",
}
NO_EVALUABLE = ILEGIBLE | SIN_CONTENIDO


def motivo_exclusion(texto: str) -> str | None:
    t = str(texto).strip()
    if t in ILEGIBLE:
        return "ilegible"
    if t in SIN_CONTENIDO:
        return "sin_contenido_evaluable"
    return None


def interpretar(v: float) -> str:
    return next(txt for lim, txt in ESCALA if v < lim)


def cargar() -> pd.DataFrame:
    """Une las planillas devueltas con la clave maestra (tipo de ítem)."""
    partes = []
    for f in sorted(DIR.glob("anotacion_A*.xlsx")):
        d = pd.read_excel(f, sheet_name="ANOTACION")
        d["archivo"] = f.name
        partes.append(d)
    if not partes:
        raise FileNotFoundError(
            "No hay planillas anotadas en anotacion/. Genera las planillas con "
            "generar_planillas.py y espera a que el equipo las devuelva.")
    df = pd.concat(partes, ignore_index=True)

    km = pd.read_csv(DIR / "_clave_maestra.csv")
    df = df.merge(km[["anotador", "orden", "tipo", "esperada"]],
                  on=["anotador", "orden"], how="left")
    df["etiqueta"] = df["etiqueta"].astype(str).str.strip().str.upper()
    df["exclusion"] = df["comentario"].map(motivo_exclusion)
    return df


def control_calidad(df: pd.DataFrame) -> list[str]:
    """Anclas (atención) y repetidos encubiertos (autoconsistencia)."""
    lineas = ["## 1 · Control de calidad por anotador\n",
              "| Anotador | Anotados | Sin etiqueta | Anclas correctas | Autoconsistencia | % difíciles |",
              "|---|--:|--:|--:|--:|--:|"]
    for a, g in df.groupby("anotador"):
        vacias = int((~g["etiqueta"].isin(ETIQUETAS)).sum())
        anc = g[g["tipo"] == "ancla"]
        ok = int((anc["etiqueta"] == anc["esperada"]).sum())

        rep = g[g["tipo"].isin(["eval", "repetido"])]
        pares = rep.groupby("comentario")["etiqueta"].agg(list)
        pares = pares[pares.map(len) == 2]
        consis = f"{sum(1 for v in pares if v[0] == v[1])}/{len(pares)}" if len(pares) else "—"

        dif = g["dificil"].fillna(0).astype(float).mean() * 100
        lineas.append(f"| {a} | {len(g)} | {vacias} | {ok}/{len(anc)} | {consis} | {dif:.0f} % |")
    lineas += ["",
               "> Anclas < 7/8 o autoconsistencia < 6/8 indican un anotador descuidado: revisar "
               "su planilla antes de consolidar.\n"]
    return lineas


def reporte_exclusiones(df: pd.DataFrame) -> list[str]:
    """Documenta qué ítems se excluyen del gold y por qué."""
    exc = df[df["exclusion"].notna()].drop_duplicates("comentario")
    votos = (df[df["motivo"].astype(str).str.strip() == "sin_sentido"]
               .groupby("comentario").size())

    L = ["## 2 · Ítems excluidos por no ser evaluables\n",
         f"Se excluyen **{len(exc)}** comentarios del gold. La lista es explícita y auditable "
         "(`NO_EVALUABLE` en este script), apoyada en el motivo `sin_sentido` marcado por los "
         "anotadores.\n",
         "| Comentario | Motivo | Votos `sin_sentido` |", "|---|---|--:|"]
    for _, r in exc.iterrows():
        v = int(votos.get(r["comentario"], 0))
        L.append(f"| `{str(r['comentario'])[:60]}` | {r['exclusion']} | {v}/3 |")
    L += ["",
          "> **No se excluyen** los comentarios que los anotadores marcaron difíciles pero que "
          "sí tienen polaridad (sarcasmo, metáfora, elogio tibio). Eliminarlos dejaría el gold "
          "solo con casos fáciles e inflaría artificialmente las métricas.\n"]
    return L


def matriz_eval(df: pd.DataFrame) -> tuple[np.ndarray, list[str], list[str]]:
    """Matriz (anotadores x ítems) del bloque EVAL, con NaN en los faltantes."""
    ev = df[(df["tipo"] == "eval") & df["etiqueta"].isin(ETIQUETAS) & df["exclusion"].isna()]
    textos = sorted(ev["comentario"].unique())
    anot = sorted(ev["anotador"].unique())
    M = np.full((len(anot), len(textos)), np.nan)
    pos = {t: j for j, t in enumerate(textos)}
    for i, a in enumerate(anot):
        for _, r in ev[ev["anotador"] == a].iterrows():
            M[i, pos[r["comentario"]]] = IDX[r["etiqueta"]]
    return M, textos, anot


def acuerdo(M: np.ndarray, anot: list[str]) -> list[str]:
    a_nom = krippendorff_alpha(M, level="nominal")
    a_ord = krippendorff_alpha(M, level="ordinal")
    brecha = a_ord - a_nom

    completos = ~np.isnan(M).any(axis=0)
    counts = np.zeros((int(completos.sum()), 3))
    for j, col in enumerate(M[:, completos].T):
        for v in col:
            counts[j, int(v)] += 1
    fk, p_obs, p_esp = fleiss_kappa(counts)          # (kappa, acuerdo observado, esperado)
    unan, may, sin_may = observed_agreement_triples(M[:, completos])
    media, detalle = mean_pairwise_cohen(M, labels=list(range(3)))

    L = ["## 3 · Acuerdo entre anotadores\n",
         f"**α de Krippendorff (nominal) = {a_nom:.3f}** → acuerdo *{interpretar(a_nom)}* "
         "(métrica titular)\n",
         "| Métrica | Valor | Rol |", "|---|--:|---|",
         f"| α Krippendorff nominal | {a_nom:.3f} | titular |",
         f"| α Krippendorff ordinal | {a_ord:.3f} | diagnóstico |",
         f"| Fleiss κ | {fk:.3f} | convención NLP |",
         f"| Cohen κ medio por pares | {media:.3f} | diagnóstico |",
         f"| Acuerdo observado P_o | {p_obs:.3f} | obligatorio junto a κ |",
         f"| Acuerdo esperado por azar P_e | {p_esp:.3f} | explica la paradoja de κ |",
         "",
         f"**Reparto del acuerdo en el bloque de triple anotación:** unanimidad {unan:.1%} · "
         f"mayoría 2/1 {may:.1%} · sin mayoría {sin_may:.1%}\n"]

    if p_obs - fk > 0.15:
        L.append(f"> ⚠️ **Paradoja de kappa**: el acuerdo observado es alto ({p_obs:.1%}) pero κ "
                 f"queda en {fk:.3f} porque el azar esperado es elevado ({p_esp:.3f}) debido al "
                 "desbalance de clases. **Interpretar κ junto a P_o**, nunca por separado.\n")

    pares_txt = " · ".join(f"{anot[i]}–{anot[j]} = {v:.3f}" for (i, j), v in detalle.items())
    L.append(f"**Cohen κ por pares** (detecta anotadores atípicos): {pares_txt}\n")
    if detalle:
        peor = min(detalle, key=detalle.get)
        mejor = max(detalle, key=detalle.get)
        if detalle[mejor] - detalle[peor] > 0.15:
            comunes = set(peor) & set(mejor)
            atipico = anot[next(iter(set(peor) - comunes))] if len(set(peor) - comunes) == 1 else None
            if atipico:
                L.append(f"> El par {anot[peor[0]]}–{anot[peor[1]]} concuerda mucho menos que "
                         f"{anot[mejor[0]]}–{anot[mejor[1]]}: revisar a **{atipico}** antes de "
                         "atribuir el desacuerdo a la rúbrica.\n")

    L += ["**Diagnóstico — brecha α_ordinal − α_nominal = "
          f"{brecha:+.3f}**\n"]
    if brecha > 0.15:
        L.append("> Los desacuerdos son **adyacentes** (POS↔NEU, NEU↔NEG): es un problema de "
                 "**umbral de rúbrica**, no de comprensión de la tarea. Se corrige precisando "
                 "las reglas de decisión. Es el caso esperado.\n")
    elif a_nom < 0.40:
        L.append("> Acuerdo bajo **sin** brecha ordinal: los desacuerdos son **polares** "
                 "(POS↔NEG). Los anotadores no comparten la definición de la tarea: revisar la "
                 "formación antes de reanotar.\n")
    else:
        L.append("> Acuerdo homogéneo entre tipos de desacuerdo.\n")

    if a_nom < 0.40:
        L.append("> ⚠️ **Acuerdo por debajo de 0.40.** No se descarta el trabajo: revisar la "
                 "rúbrica en la reunión, emitir la v1.1 y reanotar solo el subconjunto "
                 "afectado.\n")
    return L


def adjudicar(df: pd.DataFrame, textos: list[str]) -> tuple[pd.DataFrame, list[str]]:
    """Gold por mayoría; los ítems sin mayoría se marcan ambiguos y se excluyen."""
    ev = df[(df["tipo"] == "eval") & df["etiqueta"].isin(ETIQUETAS) & df["exclusion"].isna()]
    filas = []
    for t, g in ev.groupby("comentario"):
        votos = Counter(g["etiqueta"])
        top, n = votos.most_common(1)[0]
        empate = sum(1 for v in votos.values() if v == n) > 1
        filas.append({
            "comentario": t,
            "gold": None if empate else top,
            "acuerdo": "unanime" if n == len(g) else ("mayoria" if not empate else "sin_mayoria"),
            "votos": dict(votos),
            "marcado_dificil": int(g["dificil"].fillna(0).astype(float).sum()),
            "ambiguo": empate,
        })
    gold = pd.DataFrame(filas)
    n_amb = int(gold["ambiguo"].sum())
    dist = gold[~gold["ambiguo"]]["gold"].value_counts().reindex(ETIQUETAS).fillna(0).astype(int)

    L = ["## 4 · Adjudicación del gold\n",
         "| Situación | Ítems |", "|---|--:|",
         f"| Unanimidad (3/3) | {int((gold['acuerdo']=='unanime').sum())} |",
         f"| Mayoría (2/1) | {int((gold['acuerdo']=='mayoria').sum())} |",
         f"| Sin mayoría (1/1/1) → ambiguos | {n_amb} |",
         f"| **Gold utilizable** | **{len(gold)-n_amb}** |", "",
         "**Distribución del gold:** " +
         " · ".join(f"{k} {v}" for k, v in dist.items()) + "\n"]
    if n_amb:
        L.append(f"> Los {n_amb} ítems sin mayoría requieren **reunión de adjudicación**. Si no "
                 "hay consenso se conservan como evidencia de ambigüedad genuina, excluidos de "
                 "la evaluación.\n")
    return gold, L


def main() -> None:
    df = cargar()
    print(f"Planillas cargadas: {df['anotador'].nunique()} anotadores · {len(df)} anotaciones\n")

    L = ["# Informe de acuerdo y consolidación\n",
         f"*Anotadores: {df['anotador'].nunique()} · anotaciones totales: {len(df)}*\n"]
    L += control_calidad(df)
    L += reporte_exclusiones(df)

    M, textos, anot = matriz_eval(df)
    L += acuerdo(M, anot)

    gold, Lg = adjudicar(df, textos)
    L += Lg

    # Exportar
    util = gold[~gold["ambiguo"]][["comentario", "gold", "acuerdo", "marcado_dificil"]]
    util.to_csv(rutas.datos_processed("gold_humano_eval.csv"), index=False)

    tr = df[(df["tipo"] == "train") & df["etiqueta"].isin(ETIQUETAS) & df["exclusion"].isna()]
    tr[["comentario", "etiqueta", "anotador", "dificil"]].to_csv(
        rutas.datos_processed("train_humano.csv"), index=False)

    L += ["## 5 · Archivos generados\n",
          f"- `data/processed/gold_humano_eval.csv` — {len(util)} ítems adjudicados (evaluación)",
          f"- `data/processed/train_humano.csv` — {len(tr)} ítems (entrenamiento con verdad humana)",
          "",
          "## 6 · Siguiente paso\n",
          "Reentrenar el notebook 04 sustituyendo las pseudo-etiquetas por `train_humano.csv` y "
          "evaluar contra `gold_humano_eval.csv`. Solo entonces la afirmación *«superamos al "
          "maestro»* será defendible.\n"]

    (DIR / "reporte_acuerdo.md").write_text("\n".join(L), encoding="utf-8")
    print("\n".join(L[1:]).replace("|", " ").replace("#", ""))
    print(f"\nInforme escrito en anotacion/reporte_acuerdo.md")


if __name__ == "__main__":
    main()

"""Convierte INFORME_TECNICO.md en un HTML paginado y, si Chrome está disponible, en PDF.

Uso:
    python3 informe_tecnico/generar_pdf.py

Produce INFORME_TECNICO.html (autocontenido, con las figuras embebidas en base64) y
INFORME_TECNICO.pdf. Si Chrome no está instalado, el HTML puede imprimirse a PDF desde
el navegador con Archivo → Imprimir → Guardar como PDF.
"""

from __future__ import annotations

import base64
import mimetypes
import re
import subprocess
import sys
from pathlib import Path

import markdown

AQUI = Path(__file__).resolve().parent
MD = AQUI / "INFORME_TECNICO.md"
HTML = AQUI / "INFORME_TECNICO.html"
PDF = AQUI / "INFORME_TECNICO.pdf"

CHROME = Path("/Applications/Google Chrome.app/Contents/MacOS/Google Chrome")

CSS = """
@page { size: A4; margin: 20mm 18mm 18mm 18mm; }

:root {
  --tinta: #1a1a1a;
  --tenue: #5a5a5a;
  --linea: #d8d8d8;
  --acento: #1f4e79;
  --fondo-suave: #f5f7fa;
}

* { box-sizing: border-box; }

body {
  font-family: "Charter", "Georgia", "Times New Roman", serif;
  font-size: 10.5pt;
  line-height: 1.55;
  color: var(--tinta);
  max-width: 190mm;
  margin: 0 auto;
  padding: 0 4mm;
  hyphens: auto;
  text-align: justify;
}

h1, h2, h3, h4 {
  font-family: "Helvetica Neue", "Arial", sans-serif;
  color: var(--acento);
  line-height: 1.25;
  text-align: left;
  hyphens: none;
}

h1 { font-size: 26pt; letter-spacing: -0.5px; margin: 0 0 4pt; }
h2 {
  font-size: 15pt;
  margin: 20pt 0 8pt;
  padding-bottom: 4pt;
  border-bottom: 1.5pt solid var(--acento);
  break-after: avoid;
}
h3 { font-size: 12pt; margin: 14pt 0 5pt; color: #2c5f8a; break-after: avoid; }
h4 { font-size: 10.5pt; margin: 10pt 0 4pt; color: var(--tinta); break-after: avoid; }

p { margin: 0 0 7pt; orphans: 3; widows: 3; }

/* ---- tablas ---- */
table {
  border-collapse: collapse;
  width: 100%;
  margin: 9pt 0 12pt;
  font-size: 9pt;
  break-inside: avoid;
  font-family: "Helvetica Neue", "Arial", sans-serif;
}
th, td {
  border: 0.5pt solid var(--linea);
  padding: 4pt 6pt;
  text-align: left;
  vertical-align: top;
  hyphens: none;
}
th { background: var(--acento); color: #fff; font-weight: 600; }
th code { background: rgba(255, 255, 255, 0.2); color: #fff; }
tbody tr:nth-child(even) { background: var(--fondo-suave); }

/* ---- código ---- */
code {
  font-family: "SF Mono", "Menlo", "Consolas", monospace;
  font-size: 8.5pt;
  background: var(--fondo-suave);
  padding: 1pt 3pt;
  border-radius: 2pt;
  hyphens: none;
}
pre {
  background: #f8f9fb;
  border: 0.5pt solid var(--linea);
  border-left: 2.5pt solid var(--acento);
  padding: 7pt 9pt;
  overflow-x: auto;
  break-inside: avoid;
  margin: 8pt 0 11pt;
}
pre code { background: none; padding: 0; font-size: 8pt; line-height: 1.4; }

/* ---- citas / notas destacadas ---- */
blockquote {
  margin: 10pt 0;
  padding: 7pt 11pt;
  background: var(--fondo-suave);
  border-left: 2.5pt solid var(--acento);
  color: #2a2a2a;
  break-inside: avoid;
}
blockquote p:last-child { margin-bottom: 0; }

/* ---- figuras ---- */
img {
  max-width: 100%;
  height: auto;
  display: block;
  margin: 10pt auto 4pt;
  border: 0.5pt solid var(--linea);
  break-inside: avoid;
}
/* pie de figura: el párrafo en cursiva que sigue a una imagen */
p > em:only-child {
  display: block;
  text-align: center;
  font-size: 8.5pt;
  color: var(--tenue);
  margin: 0 auto 12pt;
  max-width: 88%;
}

ul, ol { margin: 0 0 8pt; padding-left: 18pt; }
li { margin-bottom: 3pt; }

hr { border: none; border-top: 0.5pt solid var(--linea); margin: 16pt 0; }

a { color: var(--acento); text-decoration: none; }

/* ---- portada ---- */
.portada { text-align: center; padding-top: 32mm; }
.portada h1 { font-size: 30pt; margin-bottom: 10pt; }
.portada h2 { border: none; font-size: 15pt; color: var(--tinta); font-weight: 400; }
.portada h3 { font-size: 11.5pt; color: var(--tenue); font-weight: 400; font-style: italic; }
.portada thead { display: none; }
.portada table { width: 74%; margin: 22pt auto; font-size: 10pt; }
.portada th, .portada td { border: none; border-bottom: 0.5pt solid var(--linea); padding: 6pt 8pt; }
.portada tbody tr:nth-child(even) { background: none; }
.portada table td:first-child { width: 38%; }

.cierre { text-align: center; margin-top: 24pt; color: var(--tenue); font-size: 10pt; }
.cierre p { text-align: center; }

@media screen {
  body { padding: 24pt 30pt; background: #fff; }
}
"""


def incrustar_imagenes(html: str) -> str:
    """Sustituye src relativos por data URIs para que el HTML sea autocontenido."""

    def _reemplazo(m: re.Match) -> str:
        src = m.group(1)
        if src.startswith(("http://", "https://", "data:")):
            return m.group(0)
        ruta = (AQUI / src).resolve()
        if not ruta.exists():
            print(f"  ⚠️  figura no encontrada: {src}", file=sys.stderr)
            return m.group(0)
        mime = mimetypes.guess_type(ruta.name)[0] or "image/png"
        b64 = base64.b64encode(ruta.read_bytes()).decode()
        return f'src="data:{mime};base64,{b64}"'

    return re.sub(r'src="([^"]+)"', _reemplazo, html)


def main() -> int:
    if not MD.exists():
        print(f"No se encuentra {MD}", file=sys.stderr)
        return 1

    texto = MD.read_text(encoding="utf-8")

    # GitHub procesa markdown dentro de <div>; Python-Markdown exige markdown="1".
    texto = re.sub(r'<div align="center">', '<div align="center" markdown="1">', texto)

    cuerpo = markdown.markdown(
        texto,
        extensions=["tables", "fenced_code", "attr_list", "md_in_html", "sane_lists"],
    )
    cuerpo = incrustar_imagenes(cuerpo)

    # La portada es el primer <div align="center"> del documento.
    cuerpo = re.sub(r'<div align="center"[^>]*>', '<div class="portada">', cuerpo, count=1)
    cuerpo = re.sub(r'<div align="center"[^>]*>', '<div class="cierre">', cuerpo)

    documento = (
        "<!doctype html>\n"
        '<html lang="es">\n<head>\n<meta charset="utf-8">\n'
        "<title>Informe técnico — Analítica Educativa · Tech Tailors</title>\n"
        f"<style>{CSS}</style>\n</head>\n<body>\n{cuerpo}\n</body>\n</html>\n"
    )
    HTML.write_text(documento, encoding="utf-8")
    print(f"✅ HTML: {HTML}  ({HTML.stat().st_size / 1024:.0f} KB)")

    if not CHROME.exists():
        print("ℹ️  Chrome no encontrado. Abre el HTML e imprime a PDF desde el navegador.")
        return 0

    resultado = subprocess.run(
        [
            str(CHROME),
            "--headless",
            "--disable-gpu",
            "--no-pdf-header-footer",
            f"--print-to-pdf={PDF}",
            HTML.as_uri(),
        ],
        capture_output=True,
        text=True,
        timeout=180,
    )
    if PDF.exists() and PDF.stat().st_size > 0:
        print(f"✅ PDF:  {PDF}  ({PDF.stat().st_size / 1024 / 1024:.1f} MB)")
        return 0

    print(f"⚠️  Chrome no generó el PDF:\n{resultado.stderr[-500:]}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())

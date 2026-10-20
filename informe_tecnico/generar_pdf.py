"""Convierte un informe en Markdown en un HTML paginado y, si Chrome está disponible, en PDF.

Uso:
    python3 informe_tecnico/generar_pdf.py                          # INFORME_TECNICO.md
    python3 informe_tecnico/generar_pdf.py INFORME_TECNICO_COMPLETO.md

El HTML y el PDF toman el nombre del .md de entrada. El HTML es autocontenido (figuras
embebidas en base64); si Chrome no está instalado, puede imprimirse a PDF desde el navegador
con Archivo → Imprimir → Guardar como PDF.
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

# El .md de entrada se puede pasar como argumento; el HTML y el PDF heredan su nombre.
MD = Path(sys.argv[1]) if len(sys.argv) > 1 else AQUI / "INFORME_TECNICO.md"
if not MD.is_absolute():
    MD = (AQUI / MD) if not MD.exists() else MD.resolve()
HTML = MD.with_suffix(".html")
PDF = MD.with_suffix(".pdf")

CHROME = Path("/Applications/Google Chrome.app/Contents/MacOS/Google Chrome")

CSS = """
@page { size: A4; margin: 14mm 15mm 13mm 15mm; }

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
  font-size: 9.3pt;
  line-height: 1.33;
  color: var(--tinta);
  max-width: 200mm;
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

h1 { font-size: 24pt; letter-spacing: -0.5px; margin: 0 0 4pt; }
h2 {
  font-size: 12.5pt;
  margin: 10pt 0 4pt;
  padding-bottom: 2.5pt;
  border-bottom: 1.5pt solid var(--acento);
  break-after: avoid;
}
h3 { font-size: 10.4pt; margin: 7pt 0 2.5pt; color: #2c5f8a; break-after: avoid; }
h4 { font-size: 9.4pt; margin: 6pt 0 2pt; color: var(--tinta); break-after: avoid; }

p { margin: 0 0 4pt; orphans: 2; widows: 2; }

/* ---- tablas ---- */
table {
  border-collapse: collapse;
  width: 100%;
  margin: 4pt 0 6pt;
  font-size: 7.9pt;
  break-inside: auto;
  font-family: "Helvetica Neue", "Arial", sans-serif;
}
th, td {
  border: 0.5pt solid var(--linea);
  padding: 2.2pt 4pt;
  text-align: left;
  vertical-align: top;
  hyphens: none;
}
th { background: var(--acento); color: #fff; font-weight: 600; }
th code { background: rgba(255, 255, 255, 0.2); color: #fff; }
tbody tr:nth-child(even) { background: var(--fondo-suave); }
thead { display: table-header-group; }
tr { break-inside: avoid; }

/* ---- código ---- */
code {
  font-family: "SF Mono", "Menlo", "Consolas", monospace;
  font-size: 7.8pt;
  background: var(--fondo-suave);
  padding: 0.5pt 2pt;
  border-radius: 2pt;
  hyphens: none;
}
pre {
  background: #f8f9fb;
  border: 0.5pt solid var(--linea);
  border-left: 2.5pt solid var(--acento);
  padding: 4pt 6pt;
  overflow-x: auto;
  break-inside: avoid;
  margin: 5pt 0 7pt;
}
pre code { background: none; padding: 0; font-size: 7pt; line-height: 1.3; }

/* ---- citas / notas destacadas ---- */
blockquote {
  margin: 6pt 0;
  padding: 4.5pt 8pt;
  background: var(--fondo-suave);
  border-left: 2.5pt solid var(--acento);
  color: #2a2a2a;
  break-inside: avoid;
}
blockquote p:last-child { margin-bottom: 0; }

/* ---- figuras ---- */
img {
  max-width: 68%;
  height: auto;
  display: block;
  margin: 6pt auto 2pt;
  border: 0.5pt solid var(--linea);
  break-inside: avoid;
}
img.fig-s { max-width: 44%; }
/* pie de figura: el párrafo en cursiva que sigue a una imagen */
body > p > em:only-child {
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

/* ---- portada: ocupa toda la primera página, contenido distribuido ---- */
.portada {
  text-align: center;
  height: 256mm;
  display: flex;
  flex-direction: column;
  padding-top: 24mm;
}
.portada h1, .portada h2, .portada h3 { text-align: center; }
.portada h1 { font-size: 31pt; margin-bottom: 10pt; }
.portada h2 { border: none; font-size: 15.5pt; color: var(--tinta); font-weight: 400; }
.portada h3 { font-size: 11.5pt; color: var(--tenue); font-weight: 400; font-style: italic; }
.portada thead { display: none; }
/* márgenes verticales automáticos: la tabla queda centrada en el espacio restante */
.portada table { width: 76%; margin: auto; font-size: 10.5pt; }
.portada th, .portada td { border: none; border-bottom: 0.5pt solid var(--linea); padding: 7.5pt 9pt; }
.portada tbody tr:nth-child(even) { background: none; }
.portada table td:first-child { width: 38%; }

.cierre { text-align: center; margin-top: 84pt; color: var(--tenue); font-size: 10pt; }
.cierre p { text-align: center; }

/* ---- referencias a dos columnas ---- */
.refs { column-count: 2; column-gap: 8mm; font-size: 7.6pt; }
.refs ol { margin: 0 0 4pt; padding-left: 13pt; }
.refs li { margin-bottom: 2pt; break-inside: avoid; }
.refs p { break-after: avoid; margin: 4pt 0 2pt; }

/* ---- compactación para reducir el número de páginas ---- */
div[style*="page-break"] { page-break-after: auto !important; break-after: auto !important; height: 0; }
.portada { break-after: page; }   /* la portada sí ocupa su propia página */
ul, ol { margin: 0 0 5pt; padding-left: 15pt; }
li { margin-bottom: 1.5pt; }
hr { margin: 9pt 0; }
body > p > em:only-child { font-size: 7.6pt; margin: 0 auto 6pt; }

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

"""Exportación DOCX con runtime documental. Ejecutar con Python del runtime de artefactos."""

from pathlib import Path
from io import BytesIO
from zipfile import ZipFile, ZIP_DEFLATED
import re

from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_CELL_VERTICAL_ALIGNMENT

ROOT = Path("entrega_academica")


def plain(value):
    value = re.sub(r"\[([^]]+)\]\(([^)]+)\)", r"\1 — \2", value)
    return value.replace("**", "").replace("`", "").replace(r"\(", "").replace(r"\)", "")


def paragraph(doc, value, style=None):
    p = doc.add_paragraph(style=style)
    for chunk in re.split(r"(\*\*.*?\*\*|`[^`]+`)", value):
        run = p.add_run(plain(chunk))
        if chunk.startswith("**"):
            run.bold = True
        if chunk.startswith("`"):
            run.font.name = "Consolas"
            run.font.size = Pt(9)
    return p


def table(doc, rows):
    headers = rows[0]
    headers = ["Prior." if value == "Prioridad" else value for value in headers]
    data = (
        rows[2:]
        if len(rows) > 1 and all(set(c.strip()) <= set(":- ") for c in rows[1])
        else rows[1:]
    )
    if len(headers) > 5:
        # Matrices anchas de PERT/riesgo: representación vertical legible, sin microtipografía.
        for record in data:
            p = paragraph(doc, plain(record[0]))
            p.runs[0].bold = True
            p.paragraph_format.keep_with_next = True
            for key, value in zip(headers[1:], record[1:]):
                paragraph(doc, f"**{plain(key)}:** {plain(value)}")
        return
    t = doc.add_table(rows=1, cols=len(headers))
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    t.autofit = False
    # Primer ID compacto, resto distribuido por longitud media del contenido.
    weights = [
        max(8, sum(len(plain(r[i])) for r in [headers, *data] if len(r) > i) / (len(data) + 1))
        for i in range(len(headers))
    ]
    if len(headers) > 2:
        weights[0] = min(weights[0], 12)
    if len(headers) > 2 and (
        headers[0].strip() == "ID" or all(re.match(r"[A-Z]+_\d", r[0]) for r in data if r)
    ):
        widths = [0.85] + [6.15 * w / sum(weights[1:]) for w in weights[1:]]
    else:
        widths = [7 * w / sum(weights) for w in weights]
    if headers[:2] == ["ID", "Requerimiento"] and len(headers) == 4:
        widths = [0.85, 1.9, 0.65, 3.6]
    elif len(headers) == 3 and headers[0] == "ID":
        widths = [0.85, 1.45, 4.7]
        if headers[1] == "Fuente primaria":
            widths = [0.85, 4.7, 1.45]
        elif headers[1] == "Objetivo":
            widths = [0.85, 3.6, 2.55]
    for c, w in zip(t.columns, widths):
        c.width = Inches(w)
    for j, header in enumerate(headers):
        t.rows[0].cells[j].text = plain(header)
    for row in data:
        cells = t.add_row().cells
        for j, cell in enumerate(cells):
            cell.text = plain(row[j]) if j < len(row) else ""
    for i, row in enumerate(t.rows):
        trpr = row._tr.get_or_add_trPr()
        cannot = OxmlElement("w:cantSplit")
        trpr.append(cannot)
        if i == 0:
            repeat = OxmlElement("w:tblHeader")
            trpr.append(repeat)
        for j, cell in enumerate(row.cells):
            cell.width = Inches(widths[j])
            cell.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER
            pr = cell._tc.get_or_add_tcPr()
            shading = OxmlElement("w:shd")
            shading.set(qn("w:fill"), "174765" if i == 0 else ("F1F5F7" if i % 2 else "FFFFFF"))
            pr.append(shading)
            borders = OxmlElement("w:tcBorders")
            for edge in ("top", "left", "bottom", "right"):
                node = OxmlElement("w:" + edge)
                node.set(qn("w:val"), "single")
                node.set(qn("w:sz"), "4")
                node.set(qn("w:color"), "D9D9D9")
                borders.append(node)
            pr.append(borders)
            margins = OxmlElement("w:tcMar")
            for edge in ("top", "left", "bottom", "right"):
                node = OxmlElement("w:" + edge)
                node.set(qn("w:w"), "90")
                node.set(qn("w:type"), "dxa")
                margins.append(node)
            pr.append(margins)
            for p in cell.paragraphs:
                p.paragraph_format.space_after = Pt(3)
                p.paragraph_format.space_before = Pt(3)
                if j == 0 and len(headers) > 2:
                    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
                for r in p.runs:
                    r.font.name = "Arial"
                    r.font.size = Pt(9)
                    if i == 0:
                        r.font.bold = True
                        r.font.color.rgb = RGBColor(255, 255, 255)
    doc.add_paragraph().paragraph_format.space_after = Pt(2)


def convert(source):
    doc = Document()
    sec = doc.sections[0]
    sec.page_width = Inches(8.5)
    sec.page_height = Inches(11)
    sec.top_margin = sec.bottom_margin = Inches(0.7)
    sec.left_margin = sec.right_margin = Inches(0.75)
    for name in ("Normal", "Title", "Heading 1", "Heading 2", "Heading 3", "Heading 4"):
        style = doc.styles[name]
        style.font.name = "Arial"
        style.font.color.rgb = RGBColor(0, 0, 0)
        style.font.size = Pt(
            10.5
            if name == "Normal"
            else {
                "Title": 22,
                "Heading 1": 17,
                "Heading 2": 13,
                "Heading 3": 11.5,
                "Heading 4": 11,
            }[name]
        )
        style.paragraph_format.space_after = Pt(7)
    doc.styles["Normal"].paragraph_format.line_spacing = 1.12
    if source.stem == "DOC_003_Manual":
        doc.styles["Normal"].paragraph_format.line_spacing = 1.04
    for border in list(doc.styles.element.xpath("//w:pBdr")):
        border.getparent().remove(border)
    header = sec.header.paragraphs[0]
    header.text = (
        "SGT Cuauhtémoc | Prototipo académico simulado | "
        + source.stem.split("_")[0]
        + "_"
        + source.stem.split("_")[1]
    )
    for r in header.runs:
        r.font.name = "Arial"
        r.font.size = Pt(8)
    footer = sec.footer.paragraphs[0]
    footer.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    field = OxmlElement("w:fldSimple")
    field.set(qn("w:instr"), "PAGE")
    footer._p.append(field)
    content = source.read_text(encoding="utf-8")

    def math(m):
        if "EMV" in m[1]:
            return "\nEMV = probabilidad × pérdida adicional.\n"
        if "g" in m[1] and "clip" in m[1]:
            return "\ng_NS = clip(80 × d_NS / (d_NS + d_EO), 20, 60); g_EO = 80 − g_NS.\n"
        return "\nTE = (To + 4 Tn + Tp) / 6; varianza = ((Tp − To) / 6)².\n"

    content = re.sub(r"\\\[(.*?)\\\]", math, content, flags=re.S)
    lines = content.splitlines()
    i = 0
    code = False
    pending = []

    def flush():
        if pending:
            paragraph(doc, " ".join(pending))
            pending.clear()

    while i < len(lines):
        line = lines[i].strip()
        if line.startswith("```"):
            flush()
            code = not code
            i += 1
            continue
        if code:
            p = paragraph(doc, line)
            p.paragraph_format.left_indent = Inches(0.12)
            p.paragraph_format.space_after = Pt(2)
            for r in p.runs:
                r.font.name = "Consolas"
                r.font.size = Pt(8.5)
        elif line.startswith("|"):
            flush()
            rows = []
            while i < len(lines) and lines[i].strip().startswith("|"):
                rows.append([v.strip() for v in lines[i].strip().strip("|").split("|")])
                i += 1
            table(doc, rows)
            continue
        elif line.startswith("#"):
            flush()
            level = len(line) - len(line.lstrip("#"))
            label = plain(line[level:].strip())
            label = re.sub(r"[—–·:;()]+", " ", label)
            if level == 1:
                doc.add_paragraph(label, "Title")
            else:
                p = doc.add_paragraph(label, f"Heading {min(level - 1, 4)}")
                if label.startswith("CAP_"):
                    p.paragraph_format.page_break_before = True
        elif line.startswith("!["):
            flush()
            match = re.match(r"!\[([^]]*)\]\(([^)]+)\)", line)
            if match:
                image = ROOT / match[2]
                if not image.exists():
                    raise FileNotFoundError(image)
                p = paragraph(doc, match[1])
                p.paragraph_format.keep_with_next = True
                doc.add_picture(str(image), width=Inches(6.85))
        elif not line:
            flush()
        elif line.startswith("- ") or re.match(r"\d+\. ", line):
            flush()
            paragraph(doc, line)
        elif line.startswith("**TAB_"):
            flush()
            p = paragraph(doc, line)
            p.paragraph_format.keep_with_next = True
        else:
            pending.append(line)
        i += 1
    flush()
    for border in list(doc.element.xpath("//w:pBdr")):
        border.getparent().remove(border)
    doc.save(source.with_suffix(".docx"))
    # Word también consulta stylesWithEffects; su plantilla puede reintroducir la línea azul.
    destination = source.with_suffix(".docx")
    with ZipFile(destination) as archive:
        members = {name: archive.read(name) for name in archive.namelist()}
    if "word/stylesWithEffects.xml" in members:
        members["word/stylesWithEffects.xml"] = re.sub(
            rb"<w:pBdr\b[^>]*>.*?</w:pBdr>", b"", members["word/stylesWithEffects.xml"], flags=re.S
        )
    buffer = BytesIO()
    with ZipFile(buffer, "w", ZIP_DEFLATED) as archive:
        for name, data in members.items():
            archive.writestr(name, data)
    destination.write_bytes(buffer.getvalue())


if __name__ == "__main__":
    for source in sorted(ROOT.glob("DOC_*.md")):
        convert(source)
        print("Exportado", source.with_suffix(".docx"))

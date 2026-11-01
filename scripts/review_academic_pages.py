"""Renderiza todos los PDF para QA y crea planchas de inspección sin modificar entregables."""

from pathlib import Path
import subprocess
import json

from PIL import Image, ImageDraw
from pypdf import PdfReader

ROOT = Path("entrega_academica")
QA = Path("data/academic-build/qa")
POPPLER = Path(
    "C:/Users/diego/.cache/codex-runtimes/codex-primary-runtime/dependencies/native/poppler/Library/bin"
)


def main():
    QA.mkdir(parents=True, exist_ok=True)
    findings = {}
    for pdf in ROOT.glob("DOC_*.pdf"):
        target = QA / pdf.stem
        target.mkdir(exist_ok=True)
        subprocess.run(
            [
                str(POPPLER / "pdftoppm.exe"),
                "-scale-to",
                "1100",
                "-png",
                str(pdf),
                str(target / "page"),
            ],
            check=True,
        )
        pages = PdfReader(pdf).pages
        findings[pdf.name] = {
            "pages": len(pages),
            "text_chars": [len(p.extract_text()) for p in pages],
        }
        images = sorted(target.glob("page-*.png"))[: len(pages)]
        for start in range(0, len(images), 12):
            sheet = Image.new("RGB", (1200, 1200), "#dce4e8")
            for j, path in enumerate(images[start : start + 12]):
                pic = Image.open(path).convert("RGB")
                pic.thumbnail((290, 365))
                x = (j % 4) * 300 + (300 - pic.width) // 2
                y = (j // 4) * 400 + 22
                sheet.paste(pic, (x, y))
                ImageDraw.Draw(sheet).text(
                    ((j % 4) * 300 + 8, (j // 4) * 400 + 4),
                    f"{pdf.stem} p{start + j + 1}",
                    fill="black",
                )
            sheet.save(QA / f"{pdf.stem}-sheet-{start // 12 + 1}.png")
    (QA / "pages.json").write_text(json.dumps(findings, indent=2), encoding="utf-8")
    # Revisar secuencia completa de diapositivas además de los PNG individuales.
    slides = sorted((ROOT / "diapositivas").glob("DIA_*.png"))
    for start in range(0, len(slides), 8):
        sheet = Image.new("RGB", (1280, 800), "#dce4e8")
        for j, path in enumerate(slides[start : start + 8]):
            im = Image.open(path)
            im.thumbnail((630, 180))
            sheet.paste(im, ((j % 2) * 640, (j // 2) * 200 + 16))
            ImageDraw.Draw(sheet).text(((j % 2) * 640 + 6, (j // 2) * 200), path.stem, fill="black")
        sheet.save(QA / f"slides-sheet-{start // 8 + 1}.png")
    print(json.dumps({k: v["pages"] for k, v in findings.items()}, indent=2))


if __name__ == "__main__":
    main()

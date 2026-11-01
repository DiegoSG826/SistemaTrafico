"""VID_001: presentación MP4 subtitulada y demostración determinista del controlador."""

import json
from pathlib import Path
import textwrap

import imageio_ffmpeg
from PIL import Image, ImageDraw, ImageFont

from backend.app.controller import Timing, phase

OUT = Path("entrega_academica")
FPS = 6
FONT = ImageFont.truetype("C:/Windows/Fonts/arial.ttf", 25)
TITLE = ImageFont.truetype("C:/Windows/Fonts/arialbd.ttf", 36)
BIG = ImageFont.truetype("C:/Windows/Fonts/arialbd.ttf", 64)


def stamp(seconds):
    ms = round(seconds * 1000)
    h, ms = divmod(ms, 3600000)
    m, ms = divmod(ms, 60000)
    s, ms = divmod(ms, 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def base(image, caption):
    result = Image.new("RGB", (1280, 840), "#13394d")
    result.paste(image.resize((1280, 720)), (0, 0))
    draw = ImageDraw.Draw(result)
    lines = textwrap.wrap(caption, width=98)
    for i, line in enumerate(lines[:3]):
        draw.text((35, 735 + i * 30), line, font=FONT, fill="white")
    return result


def animation(second):
    t = min(119, int(second * 4))
    state = phase(Timing(45, 35), t)
    image = Image.new("RGB", (1280, 720), "white")
    d = ImageDraw.Draw(image)
    d.rectangle((0, 0, 1280, 12), fill="#087f82")
    d.text((55, 50), "DEM_001  Un ciclo adaptativo completo", font=TITLE, fill="#13394d")
    d.text((55, 130), f"Segundo simulado {t:03d} / 120", font=BIG, fill="#087f82")
    d.text((55, 240), "Plan aplicado al iniciar el ciclo", font=FONT, fill="#13394d")
    for i, (code, label) in enumerate(
        (("NS", "Norte–Sur"), ("EO", "Este–Oeste"), ("PEATON", "Peatones"))
    ):
        x = 200 + i * 430
        d.text((x - 100, 335), label, font=TITLE, fill="#13394d")
        colors = {"RED": "#b33b42", "GREEN": "#17826c", "YELLOW": "#d5a52b"}
        d.ellipse((x - 65, 410, x + 65, 540), fill=colors[state[code]])
        d.text((x - 75, 565), state[code], font=FONT, fill="#13394d")
    d.text(
        (55, 650),
        f"Fase: {state['phase']}  |  Verde NS 45 s / EO 35 s / peatón 20 s",
        font=FONT,
        fill="#13394d",
    )
    return image


def main():
    slides = json.loads((OUT / "PRE_001_Guion.json").read_text(encoding="utf-8"))
    writer = imageio_ffmpeg.write_frames(
        str(OUT / "VID_001_Presentacion.mp4"),
        (1280, 840),
        fps=FPS,
        codec="libx264",
        pix_fmt_in="rgb24",
        pix_fmt_out="yuv420p",
        macro_block_size=2,
        output_params=["-preset", "veryfast", "-crf", "23", "-movflags", "+faststart"],
    )
    writer.send(None)
    clock = 0.0
    subtitles = []
    index = 1
    try:
        for number, slide in enumerate(slides, 1):
            picture = Image.open(OUT / "diapositivas" / f"DIA_{number:03d}.png").convert("RGB")
            words = slide["notes"].split()
            chunks = []
            while words:
                chunk = []
                while words and (len(" ".join(chunk)) + len(words[0]) < 190 or not chunk):
                    chunk.append(words.pop(0))
                chunks.append(" ".join(chunk))
            for chunk in chunks:
                frames = max(5 * FPS, round(len(chunk.split()) / 2.5 * FPS))
                duration = frames / FPS
                frame = base(picture, chunk).tobytes()
                for _ in range(frames):
                    writer.send(frame)
                subtitles.append(
                    f"{index}\n{stamp(clock)} --> {stamp(clock + duration)}\n{chunk}\n"
                )
                clock += duration
                index += 1
            if number == 4:
                caption = "Demostración sintética generada con controller.phase: verde 45/35, peatones exclusivos y despejes. No es una grabación de tráfico real."
                start = clock
                for n in range(30 * FPS):
                    writer.send(base(animation(n / FPS), caption).tobytes())
                clock += 30
                subtitles.append(f"{index}\n{stamp(start)} --> {stamp(clock)}\n{caption}\n")
                index += 1
        (OUT / "VID_001_Subtitulos.srt").write_text("\n".join(subtitles), encoding="utf-8")
    finally:
        writer.close()
    (OUT / "VID_001_Ficha.json").write_text(
        json.dumps(
            {
                "id": "VID_001",
                "duration_s": clock,
                "fps": FPS,
                "resolution": [1280, 840],
                "audio": "Sin locución; subtítulos en español incrustados y SRT",
                "content": "14 diapositivas, capturas reales de instancia temporal y demostración sintética del controlador",
                "real_world_traffic_footage": False,
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    print(f"MP4 generado: {clock:.1f} s, subtítulos y demo de un ciclo")


if __name__ == "__main__":
    main()

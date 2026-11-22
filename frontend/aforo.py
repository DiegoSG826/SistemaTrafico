"""Validación de aforos por minuto para su reproducción en el dashboard."""

import csv
import io
from datetime import UTC, datetime, timedelta

COLUMNAS = ("inicio", "llegadas_ns", "llegadas_eo")
MAX_MINUTOS = 1440


def cargar_aforo(contenido: bytes) -> list[tuple[datetime, int, int]]:
    try:
        texto = contenido.decode("utf-8-sig")
    except UnicodeError as exc:
        raise ValueError("Guarda el CSV con codificación UTF-8.") from exc

    lector = csv.reader(io.StringIO(texto, newline=""), strict=True)
    filas: list[tuple[datetime, int, int]] = []
    try:
        if tuple(next(lector, ())) != COLUMNAS:
            raise ValueError("El encabezado debe ser inicio,llegadas_ns,llegadas_eo.")
        for fila in lector:
            if not fila:
                continue
            if len(filas) == MAX_MINUTOS:
                raise ValueError(f"Carga hasta {MAX_MINUTOS} minutos por reproducción.")
            try:
                inicio, norte_sur, este_oeste = fila
                minuto = datetime.fromisoformat(inicio.strip())
                ns, eo = int(norte_sur), int(este_oeste)
                if minuto.utcoffset() is None or not (0 <= ns <= 300 and 0 <= eo <= 300):
                    raise ValueError()
                minuto = minuto.astimezone(UTC)
                if minuto.second or minuto.microsecond:
                    raise ValueError()
            except (ValueError, OverflowError) as exc:
                raise ValueError(
                    f"Línea {lector.line_num}. Usa una fecha ISO 8601 con zona horaria, "
                    "alineada al minuto, y dos conteos enteros entre 0 y 300."
                ) from exc
            if filas and minuto - filas[-1][0] != timedelta(minutes=1):
                raise ValueError(f"Línea {lector.line_num}. Los minutos deben ser consecutivos y ordenados.")
            filas.append((minuto, ns, eo))
    except csv.Error as exc:
        raise ValueError(f"Línea {lector.line_num}. El CSV tiene un formato inválido.") from exc

    if not filas:
        raise ValueError("El CSV debe incluir al menos un minuto de aforo.")
    return filas

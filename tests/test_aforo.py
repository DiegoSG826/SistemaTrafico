from datetime import UTC, datetime

import pytest

from frontend.aforo import cargar_aforo


def test_aforo_normaliza_zona_y_conserva_cero_y_conteos():
    csv = ("\ufeffinicio,llegadas_ns,llegadas_eo\n"
           "2026-11-21T08:00:00-06:00,0,21\n"
           "2026-11-21T14:01:00Z,32,0\n")
    assert cargar_aforo(csv.encode("utf-8")) == [
        (datetime(2026, 11, 21, 14, 0, tzinfo=UTC), 0, 21),
        (datetime(2026, 11, 21, 14, 1, tzinfo=UTC), 32, 0),
    ]


@pytest.mark.parametrize(("filas", "error"), [
    ("", "al menos un minuto"),
    ("2026-11-21T08:00:00,1,2", "zona horaria"),
    ("2026-11-21T08:00:30Z,1,2", "alineada al minuto"),
    ("2026-11-21T08:00:00Z,-1,2", "entre 0 y 300"),
    ("2026-11-21T08:00:00Z,1,2\n2026-11-21T08:02:00Z,3,4", "consecutivos"),
    ("2026-11-21T08:00:00Z,1,2\n2026-11-21T08:00:00Z,3,4", "consecutivos"),
])
def test_aforo_rechaza_ventanas_invalidas(filas, error):
    csv = f"inicio,llegadas_ns,llegadas_eo\n{filas}"
    with pytest.raises(ValueError, match=error):
        cargar_aforo(csv.encode("utf-8"))

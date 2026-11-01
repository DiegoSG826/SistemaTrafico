"""Crear configuración local una sola vez, sin sobrescribir secretos existentes."""
from pathlib import Path
import secrets


def configure():
    path = Path(".env")
    if path.exists():
        print(".env ya existe; se conserva")
        return
    template = Path(".env.example").read_text(encoding="utf-8")
    for marker in ("CAMBIAR-por-una-clave-larga", "CAMBIAR-por-un-secreto-aleatorio-de-al-menos-32-caracteres",
                   "CAMBIAR-por-otra-clave", "CAMBIAR-clave-del-usuario-runtime"):
        template = template.replace(marker, secrets.token_hex(32))
    path.write_text(template, encoding="utf-8")
    print(".env creado. Consulta ADMIN_EMAIL y ADMIN_PASSWORD en ese archivo para entrar al dashboard.")


if __name__ == "__main__":
    configure()

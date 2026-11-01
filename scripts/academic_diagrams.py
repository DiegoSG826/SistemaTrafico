"""Figuras PNG/SVG reproducibles con IDs; no usa imágenes de infraestructura real."""

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, Rectangle, Ellipse, Circle

from scripts.pert import calculate

OUT = Path("entrega_academica/figuras")
BLUE, TEAL, INK = "#174765", "#087f82", "#172b3a"


def canvas(title, width=15, height=9):
    fig, ax = plt.subplots(figsize=(width, height), facecolor="white")
    ax.set_xlim(0, 15)
    ax.set_ylim(0, 9)
    ax.axis("off")
    ax.text(0.3, 8.6, title, fontsize=17, weight="bold", color=INK)
    return fig, ax


def box(ax, x, y, w, h, label, fs=10, fill="#edf4f6"):
    ax.add_patch(Rectangle((x, y), w, h, facecolor=fill, edgecolor=BLUE, linewidth=1.2))
    ax.text(x + w / 2, y + h / 2, label, ha="center", va="center", fontsize=fs, color=INK)


def arrow(ax, a, b, label="", dashed=False):
    ax.add_patch(
        FancyArrowPatch(
            a,
            b,
            arrowstyle="-|>",
            mutation_scale=12,
            linewidth=1,
            linestyle="--" if dashed else "-",
            color=BLUE,
            connectionstyle="arc3,rad=0",
        )
    )
    if label:
        ax.text(
            (a[0] + b[0]) / 2,
            (a[1] + b[1]) / 2 + 0.12,
            label,
            fontsize=8,
            color=INK,
            ha="center",
            bbox={"facecolor": "white", "edgecolor": "none", "pad": 0.5},
        )


def save(fig, name):
    fig.savefig(OUT / (name + ".png"), dpi=150, bbox_inches="tight", facecolor="white")
    fig.savefig(OUT / (name + ".svg"), bbox_inches="tight", facecolor="white")
    plt.close(fig)


def gantt_pert():
    result = calculate()
    fig, ax = plt.subplots(figsize=(14, 8))
    names = list(result["tasks"])
    for i, (name, row) in enumerate(result["tasks"].items()):
        ax.barh(i, row["TE"], left=row["ES"], color=TEAL if row["slack"] else BLUE, height=0.65)
        ax.text(
            row["ES"] + 0.15, i, f"{name}: {row['TE']:g} d", va="center", fontsize=9, color="white"
        )
    ax.set_yticks(range(15), [f"ACTIV_{i + 1:03d} ({n})" for i, n in enumerate(names)])
    ax.invert_yaxis()
    ax.set_xlim(0, 50)
    ax.axvspan(45, 50, color="#f6ead4", label="Reserva")
    ax.set_xlabel("Días hábiles relativos; inicio del proyecto = 0")
    ax.set_title("FIG_001  Gantt de la línea base — Cuauhtémoc simulado", loc="left", fontsize=16)
    ax.grid(axis="x", alpha=0.15)
    fig.tight_layout()
    save(fig, "FIG_001_gantt")
    fig, ax = canvas("FIG_002  Red PERT — 45 días hábiles y 5 de reserva", 17, 7)
    positions = {
        "A": (0.2, 4),
        "B": (1.6, 4),
        "C": (3, 5.3),
        "D": (3, 2.5),
        "E": (4.4, 5.3),
        "F": (3, 0.4),
        "G": (5.8, 2.5),
        "H": (5.8, 5.3),
        "I": (5.8, 0.4),
        "J": (7.3, 4),
        "K": (8.8, 4),
        "L": (10.3, 5.3),
        "M": (10.3, 2.5),
        "N": (11.8, 4),
        "O": (13.3, 4),
    }
    for n, row in result["tasks"].items():
        x, y = positions[n]
        for parent in row["predecessors"]:
            px, py = positions[parent]
            arrow(ax, (px + 1.1, py + 0.7), (x, y + 0.7))
    for i, (n, row) in enumerate(result["tasks"].items()):
        x, y = positions[n]
        box(
            ax,
            x,
            y,
            1.15,
            1.35,
            f"ACTIV_{i + 1:03d}\n{n} · TE {row['TE']:g}\nES {row['ES']:g} / EF {row['EF']:g}\nH {row['slack']:g}",
            8,
            "#d5e7ed" if row["slack"] == 0 else "#edf4f6",
        )
    ax.text(0.3, 7.6, "TE=(To+4Tn+Tp)/6 · H=LS−ES · Ruta crítica A–B–C–E–H–J–K–L–N–O", fontsize=12)
    save(fig, "FIG_002_pert")


def actor(ax, x, y, label):
    ax.add_patch(Circle((x, y + 0.65), 0.16, fill=False, color=INK))
    ax.plot([x, x], [y + 0.48, y], color=INK)
    ax.plot([x - 0.28, x + 0.28], [y + 0.3, y + 0.3], color=INK)
    ax.plot([x - 0.25, x, x + 0.25], [y - 0.4, y, y - 0.4], color=INK)
    ax.text(x, y - 0.65, label, ha="center", va="top", fontsize=9)


def use_cases():
    fig, ax = canvas("FIG_003  Diagrama UML de casos de uso", 16, 10)
    ax.add_patch(Rectangle((3, 0.3), 9, 7.7, fill=False, edgecolor=BLUE))
    ax.text(7.5, 7.7, "SGT Cuauhtémoc — semáforos simulados", ha="center", fontsize=12)
    labels = [
        "Acceder",
        "Gestionar catálogo",
        "Registrar datos",
        "Consultar tráfico",
        "Obtener propuesta",
        "Aplicar plan",
        "Intervenir / retornar",
        "Comparar estrategias",
        "Supervisar / exportar",
        "Consultar auditoría",
    ]
    coords = {i + 1: (5.1 if i < 5 else 9.8, 6.8 - (i % 5) * 1.35) for i in range(10)}
    actor(ax, 1.1, 4.1, "ACT_001\nAdministrador")
    actor(ax, 13.9, 6.2, "ACT_002\nProveedor")
    actor(ax, 13.9, 1.9, "ACT_003\nEvaluador")
    for i in (1, 2, 4, 5, 6, 7, 9, 10):
        x, y = coords[i]
        ax.plot([1.4, x - 1.85], [4.25, y], color="#849ca9", lw=0.8, zorder=0)
    ax.plot([13.6, coords[3][0] + 1.85], [6.35, coords[3][1]], color=BLUE, lw=1)
    ax.plot([13.6, coords[8][0] + 1.85], [2.05, coords[8][1]], color=BLUE, lw=1)
    for i, label in enumerate(labels, 1):
        x, y = coords[i]
        ax.add_patch(Ellipse((x, y), 3.75, 0.9, facecolor="white", edgecolor=BLUE, zorder=2))
        ax.text(x, y, f"CU_{i:03d}\n{label}", ha="center", va="center", fontsize=10, zorder=3)
    # Obligación del caso de aplicar, sin invertir include.
    arrow(ax, (8, 6.65), (6.9, 1.55), "«include»", True)
    ax.text(
        3.2,
        0.45,
        "Las invariantes forman parte de CU_005/CU_006/CU_007. IA y trabajador son internos.",
        fontsize=8,
    )
    save(fig, "FIG_003_casos_uso")


def er_diagram():
    fig, ax = canvas("FIG_004  Entidad relación — esquema ejecutable PostgreSQL", 19, 12)
    entities = [
        ("Intersecciones", "PK id\nconfig_version, plan_version", 0.2, 6.6),
        ("Grupos_movimiento", "PK id · FK interseccion_id\ncodigo, carriles, descarga", 3.8, 6.6),
        ("Semaforos", "PK id · FK grupo_id\ncabezal, operativo", 7.4, 6.6),
        ("Registros_trafico", "PK id · FK grupo_id\nventana, llegadas, fuente", 11, 6.6),
        (
            "Planes_semaforicos",
            "PK id · FK interseccion_id\nFK usuario_id · modo, estado",
            0.2,
            4.25,
        ),
        ("Detalles_plan", "PK/FK plan_id + grupo_id\norden, verde, amarillo, despeje", 3.8, 4.25),
        ("Predicciones", "PK id · FK grupo_id/modelo_id\nflujo, horizonte, entradas", 7.4, 4.25),
        ("Modelos", "PK id · version UNIQUE\nhashes, métricas, estado", 11, 4.25),
        ("Usuarios", "PK id · correo UNIQUE\nhash_password, rol, activo", 0.2, 1.85),
        ("Auditoria", "PK id · FK usuario_id\nactor, antes/después, correlación", 3.8, 1.85),
        ("Plan_prediccion", "PK/FK plan_id + prediccion_id", 7.4, 1.85),
        ("Experimentos", "PK id · FK modelo_id\nconfiguración y métricas", 11, 1.85),
    ]
    # Conectores por corredores entre filas; etiquetas de cardinalidad explícitas.
    links = [
        ((3.4, 7.25), (3.8, 7.25), "1 : N"),
        ((7, 7.25), (7.4, 7.25), "1 : N"),
        ((5.4, 7.9), (12.6, 7.9), "Grupo 1 : N registros"),
        ((1.8, 6.6), (1.8, 5.55), "1 : N"),
        ((3.4, 4.9), (3.8, 4.9), "1 : N"),
        ((5.4, 6.6), (5.4, 5.55), "Grupo 1 : N"),
        ((10.6, 4.9), (11, 4.9), "N : 1"),
        ((9, 6.6), (9, 5.55), "Grupo 1 : N"),
        ((1.8, 3.15), (1.8, 4.25), "Usuario 1 : N"),
        ((3.4, 2.5), (3.8, 2.5), "1 : N"),
        ((9, 3.15), (9, 4.25), "N : 1"),
        ((12.6, 3.15), (12.6, 4.25), "N : 1"),
    ]
    for a, b, label in links:
        arrow(ax, a, b, label)
    for i, (name, fields, x, y) in enumerate(entities, 1):
        box(ax, x, y, 3.2, 1.3, f"ENTBD_{i:03d}  {name}\n{fields}", 9)
    ax.text(
        0.3,
        0.9,
        "Plan_prediccion: planes N:M predicciones. Auditoría identifica actor humano o servicio.",
        fontsize=11,
    )
    ax.text(
        0.3,
        0.45,
        "Técnicas: ENTBD_013 control_worker (PK id, owner, heartbeat); ENTBD_014 schema_versions (PK version).",
        fontsize=10,
    )
    save(fig, "FIG_004_bd")


def architecture():
    fig, ax = canvas("FIG_005  Arquitectura lógica y flujo de decisión", 16, 9)
    box(ax, 0.4, 5.2, 3, 1.4, "COMP_006\nDashboard Streamlit")
    box(ax, 5.7, 5.2, 3.6, 1.4, "COMP_001\nBackend FastAPI\nautorización / validación")
    box(ax, 11.2, 5.2, 3.3, 1.4, "COMP_005\nServicio IA\npronóstico sin actuación")
    box(ax, 5.7, 1.3, 3.6, 1.4, "COMP_007\nPostgreSQL\nhistórico / planes / auditoría")
    box(ax, 0.4, 1.3, 3, 1.4, "COMP_003\nTrabajador único\ncontrol / colas / reloj")
    box(ax, 11.2, 1.3, 3.3, 1.4, "FUENTE_001\nGenerador sintético\nseed / ventanas 60 s")
    arrow(ax, (3.4, 5.9), (5.7, 5.9), "JWT + REST")
    arrow(ax, (9.3, 5.9), (11.2, 5.9), "timeout 2 s")
    arrow(ax, (7.5, 5.2), (7.5, 2.7), "transacción")
    arrow(ax, (3.4, 2), (5.7, 2), "aplicar al ciclo")
    arrow(ax, (1.9, 2.7), (11.2, 5.2), "inferencia al ciclo")
    arrow(ax, (11.2, 1.6), (3.4, 1.6), "llegadas exógenas")
    ax.text(
        0.5,
        0.45,
        "La IA estima demanda. Las reglas autorizan fases. El trabajador confirma aplicación.",
        fontsize=12,
    )
    save(fig, "FIG_005_arquitectura")
    fig, ax = canvas("FIG_006  Despliegue local y alternativa Compose", 16, 9)
    ax.add_patch(Rectangle((0.2, 1), 14.5, 6.8, fill=False, edgecolor=BLUE))
    ax.text(0.5, 7.4, "NODO_001  Equipo de laboratorio", fontsize=13)
    box(ax, 0.7, 5, 3.4, 1.5, "PROC_001\nNavegador\nlocalhost:8501")
    box(ax, 5.3, 5, 3.4, 1.5, "PROC_002\nStreamlit\nAPI_URL interno")
    box(ax, 10, 5, 4, 1.5, "PROC_003\nFastAPI :8000\nJWT y API")
    box(ax, 0.7, 1.8, 3.4, 1.5, "PROC_004\nWorker independiente\nlease exclusivo")
    box(ax, 5.3, 1.8, 3.4, 1.5, "PROC_005\nIA interna :8001\nmodelo solo lectura")
    box(ax, 10, 1.8, 4, 1.5, "PROC_006\nPostgreSQL :5432\nvolumen persistente")
    arrow(ax, (4.1, 5.75), (5.3, 5.75))
    arrow(ax, (8.7, 5.75), (10, 5.75))
    arrow(ax, (12, 5), (12, 3.3), "SQL")
    arrow(ax, (10, 5), (8.7, 3.3), "inferencia")
    arrow(ax, (4.1, 2.55), (5.3, 2.55), "inferencia")
    arrow(ax, (4.1, 1.6), (10, 1.6), "SQL / auditoría")
    ax.text(
        0.4,
        0.4,
        "Compose: red interna para BD/IA; API y dashboard publicados solo en localhost. SQLite es perfil auxiliar.",
        fontsize=10,
    )
    save(fig, "FIG_006_despliegue")


if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    gantt_pert()
    use_cases()
    er_diagram()
    architecture()

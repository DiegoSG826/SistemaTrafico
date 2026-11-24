"""Figuras PNG/SVG reproducibles con IDs; no usa imágenes de infraestructura real."""

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, Rectangle, Ellipse, Circle

from scripts.pert import MILESTONES, TOMTOM_LABELS, TOMTOM_TASKS, calculate

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
    svg = OUT / (name + ".svg")
    fig.savefig(svg, bbox_inches="tight", facecolor="white")
    svg.write_text("\n".join(line.rstrip() for line in svg.read_text(encoding="utf-8").splitlines()) + "\n",
                   encoding="utf-8")
    plt.close(fig)


def gantt_pert():
    result = calculate()
    extension = calculate(TOMTOM_TASKS, reserve=0)
    fig, (base, added) = plt.subplots(1, 2, figsize=(15, 7), gridspec_kw={"width_ratios": [1, 1]})
    fig.suptitle("FIG_001  Gantt del plan base y la ampliación TomTom", fontsize=17, weight="bold")
    for ax, plan, start, title in (
        (base, result, 1, "Plan base · 45 días + 5 de reserva"),
        (added, extension, 16, f"TomTom y comparador · {extension['duration_workdays']:g} días estimados"),
    ):
        for i, (name, row) in enumerate(plan["tasks"].items(), start):
            ax.barh(i, row["TE"], left=row["ES"], color=TEAL if row["slack"] else BLUE, height=0.63)
            ax.text(row["ES"] + row["TE"]/2, i, f"{row['TE']:g} d",
                    ha="center", va="center", fontsize=9, color="white")
        ax.set_yticks(range(start, start + len(plan["tasks"])),
                      [f"{n} · {TOMTOM_LABELS[n]}" if n in TOMTOM_LABELS else f"ACTIV_{i:03d} · {n}"
                       for i, n in enumerate(plan["tasks"], start)])
        ax.invert_yaxis()
        ax.set_xlim(0, plan["duration_workdays"] + plan["calendar_reserve_workdays"])
        ax.set_xlabel("Días hábiles relativos al inicio de esta etapa")
        ax.set_title(title, loc="left", fontsize=13, weight="bold")
        ax.grid(axis="x", alpha=0.15)
    base.axvspan(45, 50, color="#f6ead4")
    milestones = "   ·   ".join(f"{item['date_cdmx']} · {item['description']}" for item in MILESTONES)
    fig.text(0.5, 0.055, "Azul oscuro: ruta crítica   ·   Verde: holgura   ·   Las barras representan estimaciones.",
             ha="center", fontsize=10)
    fig.text(0.5, 0.022, f"Hitos de Git · {milestones}", ha="center", color=INK, fontsize=10)
    fig.tight_layout(rect=(0, 0.095, 1, 0.94))
    save(fig, "FIG_001_gantt")
    fig, (ax, added) = plt.subplots(2, 1, figsize=(16, 8), gridspec_kw={"height_ratios": [2, 1]})
    fig.suptitle("FIG_002  Red PERT del plan base y la ampliación TomTom", fontsize=17, weight="bold")
    ax.set(xlim=(0, 15), ylim=(0, 8))
    ax.axis("off")
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
    ax.text(0.3, 7.45, "Plan base · 45 días hábiles + 5 de reserva   |   Ruta A–B–C–E–H–J–K–L–N–O",
            fontsize=12, weight="bold")
    added.set(xlim=(0, 15), ylim=(0, 4.5))
    added.axis("off")
    positions = {
        "P": (0.2, 1.45), "Q": (2.3, 2.3), "R": (2.3, 0.55),
        "S": (4.42, 1.45), "T": (6.5, 1.45), "U": (8.6, 1.45),
        "V": (10.67, 2.3), "W": (10.67, 0.55), "X": (12.9, 1.45),
    }
    for i, (n, row) in enumerate(extension["tasks"].items(), 16):
        x, y = positions[n]
        for parent in row["predecessors"]:
            px, py = positions[parent]
            arrow(added, (px + 1.72, py + 0.58), (x, y + 0.58))
        box(added, x, y, 1.72, 1.15,
            f"ACTIV_{i:03d} · {n}\nTE {row['TE']:g} · H {row['slack']:g}\nES {row['ES']:g} / EF {row['EF']:g}",
            9, "#d5e7ed" if row["slack"] == 0 else "#edf4f6")
    route = "–".join(extension["critical_path"])
    added.text(0.3, 4.02, f"TomTom y comparador · {extension['duration_workdays']:g} días hábiles estimados   |   Ruta {route}",
               fontsize=12, weight="bold")
    added.text(0.3, 0.08, "TE: duración esperada · ES/EF: inicio/fin tempranos · H: holgura", fontsize=9)
    fig.tight_layout(rect=(0, 0, 1, 0.94))
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
    ax.text(7.5, 7.7, "SGT Cuauhtémoc — simulación y monitoreo", ha="center", fontsize=12)
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
        "Visualizar tráfico real",
        "Comparar demoras",
    ]
    coords = {i + 1: (5.1 if i < 5 else 9.8, 6.8 - (i % 5) * 1.2) for i in range(10)}
    coords[11] = (9.8, 0.8)
    coords[12] = (5.1, 0.8)
    actor(ax, 1.1, 4.6, "ACT_001\nAdministrador")
    actor(ax, 1.1, 1.8, "ACT_005\nUsuario lector")
    actor(ax, 13.9, 6.2, "ACT_002\nProveedor")
    actor(ax, 13.9, 3.75, "ACT_003\nEvaluador")
    actor(ax, 13.9, 1.5, "ACT_004\nTomTom")
    for i in (1, 2, 3, 4, 5, 6, 7, 9, 10, 11, 12):
        x, y = coords[i]
        ax.plot([1.4, x - 1.85], [4.75, y], color="#849ca9", lw=0.8, zorder=0)
    for i in (1, 4, 9, 11, 12):
        x, y = coords[i]
        ax.plot([1.4, x - 1.85], [1.95, y], color=TEAL, lw=0.8, zorder=0)
    ax.plot([13.6, 12.4, 7.2, coords[3][0] + 1.85], [6.35, 5.0, 5.0, coords[3][1]],
            color=BLUE, lw=1)
    ax.plot([13.6, coords[8][0] + 1.85], [3.9, coords[8][1]], color=BLUE, lw=1)
    ax.plot([13.6, coords[11][0] + 1.85], [1.65, coords[11][1]], color=BLUE, lw=1)
    arrow(ax, (7, 0.8), (7.92, 0.8), "«extend»", dashed=True)
    for i, label in enumerate(labels, 1):
        x, y = coords[i]
        ax.add_patch(Ellipse((x, y), 3.75, 0.9, facecolor="white", edgecolor=BLUE, zorder=2))
        ax.text(x, y, f"CU_{i:03d}\n{label}", ha="center", va="center", fontsize=10, zorder=3)
    ax.text(
        3.2,
        8.15,
        "CU_006 requiere una propuesta registrada y la versión vigente.",
        fontsize=8,
    )
    save(fig, "FIG_003_casos_uso")


def er_diagram():
    fig, ax = canvas("FIG_004  Entidad relación — esquema ejecutable PostgreSQL", 19, 12)
    entities = [
        ("intersecciones", "PK id\nlatitude, longitude, plan_version", 0.2, 6.6),
        ("grupos_movimiento", "PK id · FK intersection_id\ncode, lanes, discharge_vps", 3.8, 6.6),
        ("semaforos", "PK id · FK group_id\nhead, operational", 7.4, 6.6),
        ("registros_trafico", "PK id · FK group_id\nwindow_end, arrivals, source", 11, 6.6),
        (
            "planes_semaforicos",
            "PK id · FK intersection_id\nFK user_id opcional · mode, status",
            0.2,
            4.25,
        ),
        ("detalles_plan", "PK/FK plan_id + group_id\norder, green_s, yellow_s, clearance_s", 3.8, 4.25),
        ("predicciones", "PK id · FK group_id + model_id\nflow_vpm, horizon_min, inputs", 7.4, 4.25),
        ("modelos", "PK id · version UNIQUE\nartifact_hash, dataset_hash, status", 11, 4.25),
        ("usuarios", "PK id · email UNIQUE\npassword_hash, role, active", 0.2, 1.85),
        ("auditoria", "PK id · FK user_id opcional\nactor, before, after, correlation_id", 3.8, 1.85),
        ("plan_prediccion", "PK/FK plan_id + prediction_id", 7.4, 1.85),
        ("experimentos", "PK id · FK model_id opcional\nconfiguration, metrics", 11, 1.85),
    ]
    # Conectores por corredores entre filas; etiquetas de cardinalidad explícitas.
    links = [
        ((3.4, 7.25), (3.8, 7.25), "1 : N"),
        ((7, 7.25), (7.4, 7.25), "1 : N"),
        ((1.8, 6.6), (1.8, 5.55), "1 : N"),
        ((3.4, 4.9), (3.8, 4.9), "1 : N"),
        ((5.4, 6.6), (5.4, 5.55), "Grupo 1 : N"),
        ((10.6, 4.9), (11, 4.9), "N : 1"),
        ((6.55, 6.6), (8.55, 5.55), "Grupo 1 : N"),
        ((1.8, 3.15), (1.8, 4.25), "FK opcional"),
        ((3.4, 2.5), (3.8, 2.5), ""),
        ((9, 3.15), (9, 4.25), "N : 1"),
        ((12.6, 3.15), (12.6, 4.25), "FK opcional"),
    ]
    for a, b, label in links:
        arrow(ax, a, b, label)
    ax.plot([5.4, 5.4, 12.6], [7.9, 8.19, 8.19], color=BLUE, lw=1)
    arrow(ax, (12.6, 8.19), (12.6, 7.9))
    ax.text(9, 8.26, "Grupo 1 : N registros", ha="center", fontsize=8, color=INK)
    ax.plot([2.9, 2.9, 8.2], [4.25, 3.62, 3.62], color=BLUE, lw=1)
    arrow(ax, (8.2, 3.62), (8.2, 3.15))
    ax.text(4.2, 3.72, "Plan 1 : N vínculos", fontsize=8, color=INK)
    for i, (name, fields, x, y) in enumerate(entities, 1):
        box(ax, x, y, 3.2, 1.3, f"ENTBD_{i:03d}  {name}\n{fields}", 9)
    ax.text(
        0.3,
        0.9,
        "El mapa y el comparador usan coordenadas del catálogo. Las lecturas TomTom se conservan en memoria de FastAPI.",
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
    fig, ax = canvas("FIG_005  Arquitectura de control simulado y monitoreo", 16, 9)
    box(ax, 0.4, 5.2, 3, 1.4, "COMP_006\nStreamlit · barra superior\nMapa Leaflet · KPIs · pestañas")
    box(ax, 5.7, 5.2, 3.6, 1.4, "COMP_001\nBackend FastAPI\nlecturas y cuota en memoria")
    box(ax, 11.2, 5.2, 3.3, 1.4, "COMP_005\nServicio IA\npronóstico sin actuación")
    box(ax, 5.7, 1.3, 3.6, 1.4, "COMP_007\nPostgreSQL\nhistórico / planes / auditoría")
    box(ax, 0.4, 1.3, 3, 1.4, "COMP_003\nTrabajador único\ncontrol / colas / reloj")
    box(ax, 11.2, 1.3, 3.3, 1.4, "FUENTE_001\nGenerador sintético\nseed / ventanas 60 s")
    box(ax, 0.4, 7.3, 3, 0.85, "Leaflet y teselas\nCDN · OpenStreetMap y Esri", fill="#e9f5f0")
    box(ax, 5.7, 7.3, 3.6, 0.85, "TomTom Traffic API\nFlow Segment Data", fill="#e9f5f0")
    arrow(ax, (1.9, 6.6), (1.9, 7.3), "navegador")
    arrow(ax, (3.4, 5.9), (5.7, 5.9), "JWT + REST")
    arrow(ax, (9.3, 5.9), (11.2, 5.9), "timeout 2 s")
    arrow(ax, (7.5, 5.2), (7.5, 2.7))
    ax.text(7.7, 4.65, "transacción", fontsize=8, color=INK)
    arrow(ax, (7.5, 6.6), (7.5, 7.3), "HTTPS · COMP_009")
    arrow(ax, (3.4, 2), (5.7, 2), "aplicar al ciclo")
    arrow(ax, (1.9, 2.7), (11.2, 5.2))
    ax.text(3.8, 3.45, "inferencia al ciclo", fontsize=8, color=INK)
    ax.plot([12.85, 12.85, 1.9], [1.3, 0.85, 0.85], color=BLUE, lw=1)
    arrow(ax, (1.9, 0.85), (1.9, 1.3))
    ax.text(7.5, 0.97, "llegadas exógenas", ha="center", fontsize=8, color=INK)
    ax.text(
        0.5,
        0.45,
        "El mapa y el comparador comparten lecturas TomTom durante 120 s. El trabajador aplica los planes simulados.",
        fontsize=12,
    )
    save(fig, "FIG_005_arquitectura")
    fig, ax = canvas("FIG_006  Despliegue local y alternativa Compose", 16, 9)
    ax.add_patch(Rectangle((0.2, 1), 14.5, 6.8, fill=False, edgecolor=BLUE))
    ax.text(0.5, 7.4, "NODO_001  Equipo de laboratorio", fontsize=13)
    box(ax, 0.7, 5, 3.4, 1.5, "PROC_001\nNavegador\nlocalhost:8501")
    box(ax, 5.3, 5, 3.4, 1.5, "PROC_002\nStreamlit · acceso y tablero\nAPI_URL del backend")
    box(ax, 10, 5, 4, 1.5, "PROC_003\nFastAPI :8000\nJWT y API")
    box(ax, 0.7, 1.8, 3.4, 1.5, "PROC_004\nWorker independiente\nlease exclusivo")
    box(ax, 5.3, 1.8, 3.4, 1.5, "PROC_005\nIA interna :8001\nmodelo solo lectura")
    box(ax, 10, 1.8, 4, 1.5, "PROC_006\nPostgreSQL :5432\nvolumen persistente")
    box(ax, 10, 8.05, 4, 0.75, "TomTom Traffic API · externo", fill="#e9f5f0")
    arrow(ax, (4.1, 5.75), (5.3, 5.75))
    arrow(ax, (8.7, 5.75), (10, 5.75))
    arrow(ax, (12, 5), (12, 3.3), "SQL")
    arrow(ax, (12, 6.5), (12, 8.05), "HTTPS · clave y cuota en FastAPI")
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

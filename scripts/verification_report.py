"""Consolidar evidencias existentes; no ejecuta ni inventa pruebas faltantes."""
from datetime import datetime
import json
from pathlib import Path
import platform
from xml.etree import ElementTree
from zoneinfo import ZoneInfo


def main():
    suites = list(ElementTree.parse("reports/tests.xml").getroot().iter("testsuite"))
    tests = sum(int(s.get("tests", 0)) for s in suites)
    failures = sum(int(s.get("failures", 0))+int(s.get("errors", 0)) for s in suites)
    skipped = sum(int(s.get("skipped", 0)) for s in suites)
    coverage = json.loads(Path("reports/coverage.json").read_text(encoding="utf-8"))
    model = json.loads(Path("reports/model_evaluation.json").read_text(encoding="utf-8"))
    experiment = json.loads(Path("reports/experiment.json").read_text(encoding="utf-8"))
    smoke = json.loads(Path("reports/smoke.json").read_text(encoding="utf-8"))
    branches = []
    for name, value in coverage["files"].items():
        summary = value["summary"]
        branches.append(f"| {name.replace(chr(92), '/')} | {summary['covered_branches']}/{summary['num_branches']} "
                        f"({summary['covered_branches']/summary['num_branches']:.0%}) |")
    rows = []
    for scenario in dict.fromkeys(r["scenario"] for r in experiment["runs"]):
        runs = [r for r in experiment["runs"] if r["scenario"] == scenario]
        reduction = sum((r["fixed"]["delay_vehicle_s"]-r["adaptive"]["delay_vehicle_s"])
                        /r["fixed"]["delay_vehicle_s"] for r in runs)/len(runs)
        rows.append(f"| {scenario} | {len(runs)} | {reduction:.2%} |")
    metrics = model["metrics"]["test"]
    stamp = datetime.now(ZoneInfo("America/Mexico_City")).isoformat(timespec="seconds")
    text = f"""# Evidencia de verificación de FASE 2

Generado: {stamp}. Entorno observado: {platform.system()}, Python {platform.python_version()}.

## Pruebas y ejecución

- JUnit: **{tests} pruebas**, {failures} fallas/errores, {skipped} omitidas.
- Incluye PostgreSQL **17.4 real**, instalado localmente, en un clúster de laboratorio temporal;
  el perfil Compose fija 17.6 y no fue ejecutado en esta máquina.
- Cobertura combinada de controlador/esquemas: **{coverage['totals']['percent_covered']:.2f}%**.
- Prueba de humo de cuatro procesos: **{smoke['status']}**, cinco cruces, HTTP autenticado,
  aplicación diferida confirmada, conservación de vehículos y salud HTTP de Streamlit.
- Ruff y compilación Python verificados. YAML de Compose parseado correctamente;
  Docker no estaba instalado y no se afirma haber construido la imagen ni ejecutado Compose.

| Módulo | Ramas cubiertas |
|---|---|
{chr(10).join(branches)}

Los archivos originales de evidencia son `tests.xml`, `coverage.json` y `smoke.json`.
Las pruebas usan inferencia controlada para contratos y un Random Forest real pequeño en el
servicio interno; el experimento siguiente utiliza el candidato entrenado con 90 días completos.

## Entrenamiento observado

Versión: `{model['version']}`. Generador `{model['generator']}`, semilla {model['seed']},
{model['days']} días, {model['train_rows']:,} filas elegibles de entrenamiento y
{model['sampled_rows']:,} filas muestreadas por bloques. Prueba futura: {metrics['rows']:,} filas.

| Métrica de prueba | Random Forest | Persistencia |
|---|---:|---:|
| MAE (veh/min) | {metrics['model']['mae']:.4f} | {metrics['persistence']['mae']:.4f} |
| RMSE (veh/min) | {metrics['model']['rmse']:.4f} | {metrics['persistence']['rmse']:.4f} |

Reducción de MAE: **{1-metrics['model']['mae']/metrics['persistence']['mae']:.2%}**.
Ficha íntegra: `model_evaluation.json`; artefacto y dataset locales en `ml_model/artifacts/`,
excluidos de Git por tamaño. El código permite regenerarlos y registra sus hashes.

## Comparación de control observada

50 pares, 10 semillas distintas por escenario; 900 s de calentamiento y 7,200 s de medición.
Cada par conserva las mismas llegadas. IC por bootstrap de corridas pareadas estratificado
por escenario, manteniendo fija la composición del experimento.

| Escenario | Pares | Reducción media de demora |
|---|---:|---:|
{chr(10).join(rows)}

Promedio de los cuatro escenarios no sobresaturados: **{experiment['mean_delay_reduction']:.2%}**;
IC95% **[{experiment['ci95'][0]:.2%}, {experiment['ci95'][1]:.2%}]**. El guardián de cola p95
pasó en cada corrida no sobresaturada. Cero conflictos y cero omisiones peatonales en ciclos
completos, según `experiment.json`. En sobresaturación se conserva la física de colas; no se
afirma resolver demanda superior a capacidad.

Los escenarios valle y pico presentan un empeoramiento pequeño de demora: el beneficio agregado
se concentra en desbalance y lluvia/incidente. No se afirma mejora universal. El intervalo describe
estas cuatro condiciones sintéticas predefinidas, no una población de calles reales.

## Estado de entrega y aceptación pendiente

El candidato supera los umbrales automáticos predictivo y de control. **No fue promovido ni
se registraron nombres de revisores ficticios.** La ejecución inicial utiliza fijo/degradado
hasta que IA y QA revisen evidencia y ejecuten `ml_model.promote` con sus identidades reales.
La inferencia de un modelo promovido sí se verificó mediante fixture aislado.

Quedan pendientes para aceptación formal: carga de 10 minutos con 5/50 cruces, restauración
cronometrada y RPO/RTO, auditoría de dependencias/TLS, reversión operativa, revisión cruzada,
Alpha/Beta con cinco evaluadores y acta académica. La conectividad real con Waze queda fuera
del MVP y depende de autorización y datos disponibles. Ninguna prueba implica operación vial real.

PERT recalculado: **45 días hábiles**, cinco de reserva, ruta
A–B–C–E–H–J–K–L–N–O, varianza 2.7778 días². Son estimaciones heredadas, no tiempo ejecutado.
"""
    Path("reports/VERIFICACION.md").write_text(text, encoding="utf-8")


if __name__ == "__main__":
    main()

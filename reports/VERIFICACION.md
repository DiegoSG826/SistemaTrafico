# Evidencia de verificación de FASE 2

Generado: 2026-10-31T02:54:51-06:00. Entorno observado: Windows, Python 3.13.9.

## Pruebas y ejecución

- JUnit: **38 pruebas**, 0 fallas/errores, 0 omitidas.
- Incluye PostgreSQL **17.4 real**, instalado localmente, en un clúster de laboratorio temporal;
  el perfil Compose fija 17.6 y no fue ejecutado en esta máquina.
- Cobertura combinada de controlador/esquemas: **98.02%**.
- Prueba de humo de cuatro procesos: **passed**, cinco cruces, HTTP autenticado,
  aplicación diferida confirmada, conservación de vehículos y salud HTTP de Streamlit.
- Ruff y compilación Python verificados. YAML de Compose parseado correctamente;
  Docker no estaba instalado y no se afirma haber construido la imagen ni ejecutado Compose.

| Módulo | Ramas cubiertas |
|---|---|
| backend/app/controller.py | 9/10 (90%) |
| backend/app/schemas.py | 10/10 (100%) |

Los archivos originales de evidencia son `tests.xml`, `coverage.json` y `smoke.json`.
Las pruebas usan inferencia controlada para contratos y un Random Forest real pequeño en el
servicio interno; el experimento siguiente utiliza el candidato entrenado con 90 días completos.

## Entrenamiento observado

Versión: `rf-v1-90d-s42-ba0ba6390f`. Generador `synth-v1`, semilla 42,
90 días, 777,500 filas elegibles de entrenamiento y
300,000 filas muestreadas por bloques. Prueba futura: 259,160 filas.

| Métrica de prueba | Random Forest | Persistencia |
|---|---:|---:|
| MAE (veh/min) | 1.1914 | 1.4475 |
| RMSE (veh/min) | 1.5551 | 1.9066 |

Reducción de MAE: **17.69%**.
Ficha íntegra: `model_evaluation.json`; artefacto y dataset locales en `ml_model/artifacts/`,
excluidos de Git por tamaño. El código permite regenerarlos y registra sus hashes.

## Comparación de control observada

50 pares, 10 semillas distintas por escenario; 900 s de calentamiento y 7,200 s de medición.
Cada par conserva las mismas llegadas. IC por bootstrap de corridas pareadas estratificado
por escenario, manteniendo fija la composición del experimento.

| Escenario | Pares | Reducción media de demora |
|---|---:|---:|
| valley | 10 | -1.58% |
| peak | 10 | -2.48% |
| imbalance | 10 | 44.92% |
| rain_incident | 10 | 76.63% |
| oversaturation | 10 | -0.07% |

Promedio de los cuatro escenarios no sobresaturados: **29.37%**;
IC95% **[28.64%, 30.10%]**. El guardián de cola p95
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

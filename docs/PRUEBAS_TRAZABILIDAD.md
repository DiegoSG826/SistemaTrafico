# Plan de pruebas, trazabilidad y aceptación

## 1. Procedimiento reproducible

Ejecutar desde la raíz con dependencias fijadas y Python 3.13. Las pruebas crean bases SQLite
aisladas por caso y no usan el histórico del dashboard. `TEST_DATABASE_URL`, cuando existe,
debe apuntar a PostgreSQL de laboratorio con permiso de crear esquemas. La fixture crea un
esquema UUID, ejecuta el SQL real y elimina únicamente ese esquema al terminar.

```powershell
.\.venv\Scripts\python.exe -m pytest --cov=backend.app.controller --cov=backend.app.schemas --cov-branch --cov-fail-under=80 --junitxml=reports/tests.xml
$env:TEST_DATABASE_URL='postgresql+psycopg://usuario:clave@localhost:5432/traffic_test'
.\.venv\Scripts\python.exe -m pytest
.\.venv\Scripts\python.exe -m scripts.smoke_test
```

La prueba de humo usa puertos locales 18000, 18001 y 18501, SQLite temporal, credenciales
efímeras y cuatro procesos ocultos en Windows; los termina al concluir. No requiere un modelo
promovido: comprueba fallback confirmado. `test_model_service.py` verifica además una inferencia
real con Random Forest en un fixture aislado, sin fingir aprobación del candidato operativo.

El ejemplo unitario pedido se encuentra en
`tests/test_api.py::test_prediction_is_persisted_proposal_not_application`:

```python
response = client.post('/predict_light', json={
    'intersection_id': 1, 'previous_version': 0
})
assert response.status_code == 201
assert response.json()['green_s'] == {'ns': 45, 'eo': 35}
assert response.json()['status'] == 'PROPOSED'
assert response.json()['applied_at'] is None
```

El servicio simulado de esa prueba devuelve 30/10 veh/min; no se usa ese mock para medir el
error del modelo. Las métricas predictivas proceden del entrenamiento real y el periodo futuro
reservado. La prueba de servicio usa un pipeline real pequeño para evitar reentrenar 90 días
en cada ejecución de CI.

## 2. Familias de prueba de Fase 1

| ID | Evidencia implementada | Ejecución/pendiente |
|---|---|---|
| P-01 | test_api.py: contratos, permisos, recursos y conflictos | Automatizada |
| P-02 | test_data_ml.py: semillas, atributos y normalización | Automatizada |
| P-03 | API/SQLite y test_postgres.py: SQL, rollback e índice parcial | Automatizada; PostgreSQL opcional local y obligatorio en CI |
| P-04 | 3,000 demandas y todos los segundos de 41 repartos válidos | Automatizada; cero incompatibilidades y 20 s peatonales |
| P-05 | Cortes/purga, ficha del entrenamiento y 50 pares del experimento | Automatizada + revisión IA/QA pendiente |
| P-06 | Datos vencidos/ausentes, timeout, caducidad manual, lease y recuperación local | Automatizada; inyección operativa de caída real de BD adicional pendiente |
| P-07 | test_model_service.py, test_dashboard.py y scripts.smoke_test | Integración controlada y procesos HTTP reales |
| P-08 | 401/403, validación de entradas, hashes y promoción rechazada | Automatizada parcial; revisión de dependencias y TLS pendiente |
| P-09 | Script de backup y manual de restauración | Ejercicio cronometrado de restauración pendiente |
| P-10 | Guion Alpha/Beta y formulario de evidencia | Evaluación humana pendiente |
| P-11 | Verificación de hash/estado y promoción con revisión/protocolo | Automatizada parcial; revisión humana y reversión operativa pendientes |
| P-12 | scripts/load_test.py, 10 usuarios y 600 s por defecto | Ejecución completa 5/50 cruces pendiente |
| P-13 | Puertos de inferencia/fuente y configuración de capacidad | Sustitución por fixture probada; evaluación formal de modificabilidad pendiente |

## 3. Trazabilidad funcional

Estados: **implementado/verificado** significa evidencia automatizada en el alcance descrito;
**parcial** identifica una parte funcional o de aceptación que aún debe cerrar el equipo.
Ningún estado constituye aceptación por el representante académico.

| Requisito | Código | Prueba/evidencia | Estado y alcance |
|---|---|---|---|
| RF-01 Acceso | security.py, main.py | test_permissions | Implementado/verificado: admin y viewer, JWT y Argon2 |
| RF-02 Catálogo/configuración | main.py, manage.py | test_unknown_and_config_conflict | Parcial: alta, edición, activación, carriles/capacidad; fases y límites fijados por línea base |
| RF-03 Escenarios | synthetic.py | test_generator_reproducible... | Implementado/verificado para fuente sintética |
| RF-04 Registro normalizado | schemas.py, main.py, models.py | test_ingest_idempotent_mixed_batch | Implementado/verificado |
| RF-05 Calidad y vigencia | schemas.py, services.py | test_fallback, test_timezone_normalization... | Implementado/verificado: negativos, ventanas, ausencia y antigüedad |
| RF-06 Consulta | main.py | test_traffic_filters_and_dates | Implementado/verificado: catálogo y tráfico paginados |
| RF-07 Pronóstico | train_model.py, service.py | test_model_service.py y model_evaluation.json | Implementado/verificado; activación exige promoción |
| RF-08 Plan restringido | controller.py, services.py | test_controller.py, test_postgres.py | Implementado/verificado |
| RF-09 Aplicación | worker.py, services.py | test_apply_only_at_boundary..., smoke.json | Implementado/verificado con confirmación diferida |
| RF-10 Manual/retorno | main.py, worker.py | test_manual_invariants..., test_manual_expiry... | Implementado; validación de tareas humanas pendiente |
| RF-11 Degradación | services.py, worker.py | test_fallback, test_offline_fallback... | Implementado/verificado con fallas inyectadas |
| RF-12 Visualización | dashboard.py | test_dashboard.py y humo HTTP | Implementado; usabilidad/accesibilidad humana pendiente |
| RF-13 Comparación | evaluate.py, simulation.py | experiment.json | Implementado: 50 pares reproducibles |
| RF-14 Auditoría | services.py, models.py | pruebas de flujo y /audit | Implementado; rol PostgreSQL de solo inserción de bitácora |
| RF-15 Modelos | registry.py, promote.py | test_model_service.py, manifiestos | Parcial: control técnico listo; revisión y reversión operativa pendientes |
| RF-16 Exportar | dashboard.py, evaluate.py | JSON con unidades/metadatos | Implementado en JSON; CSV no expuesto |

## 4. Reglas de negocio y requisitos no funcionales

| Reglas | Verificación |
|---|---|
| RB-01 a RB-06 | Estados excluyentes, ciclo completo y plan fijo en test_controller.py; trigger real PostgreSQL |
| RB-07 | 3,000 combinaciones comprueban variación automática ≤5 s |
| RB-08 | Propuestas no aplican; transición exclusivamente en límite de ciclo |
| RB-09 | Ausencia, ventana vieja y timeout → fijo, incluyendo worker |
| RB-10/RB-11 | Motivo, vigencia y caducidad; fallback tiene precedencia sobre automático/manual |
| RB-12 | Registros de entrada, predicciones ligadas a plan, auditoría y correlación |
| RB-13 | Conflicto 409 y reserva simultánea real en PostgreSQL |

| RNF | Evidencia y condición de cierre |
|---|---|
| RNF-01 Rendimiento | Ejecutar carga 10 usuarios/10 min; exigir p95 consultas ≤500 ms y propuestas ≤1 s |
| RNF-02 Escalabilidad | Preparar 50 cruces con POST /intersections, 100 grupos vehiculares y una observación/grupo/min; mismo perfil de carga y conteo sin pérdidas |
| RNF-03 Modificabilidad | Modelo/fuente separados y capacidades editables; demostrar sustitución en revisión |
| RNF-04 Resiliencia | Timeout IA 2 s, circuito abierto 5 s y fallback en límite; medir detección/recuperación real además de fallas inyectadas |
| RNF-05 Seguridad | Autorización, hashes, secretos y red local implementados; revisión de dependencias/TLS/hallazgos pendiente |
| RNF-06 Integridad/tiempo | Unicidad, transacciones, UTC y conflictos PostgreSQL verificados |
| RNF-07 Usabilidad | Evaluación con cinco personas pendiente; ≥4 completan cada tarea en ≤3 min |
| RNF-08 Mantenibilidad | Cobertura combinada con ramas de controlador/esquemas ≥80%; revisión cruzada pendiente |
| RNF-09 Reproducibilidad | Dependencias, semillas, dataset, hashes y cortes registrados; tolerancia 1e-6 veh/min |
| RNF-10 Recuperación | Respaldos y procedimiento; medir RPO≤24 h/RTO≤30 min en restauración real |
| RNF-11 Observabilidad | Correlation-ID, entradas, versión y auditoría; perfilar tiempos de inferencia con carga |
| RNF-12 Transparencia | UI/catálogo/fuentes sintéticas y etiqueta de heurística; sin afirmaciones sobre calles reales |

El porcentaje general usa `coverage --branch`: combina sentencias y ramas. El JSON permite
ver separadamente las ramas. La CI exige 80% combinado y `scripts.check_coverage` comprueba
además al menos 80% de ramas en cada módulo de controlador y validaciones, según RNF-08.

## 5. Carga, recuperación y aceptación humana

```text
python -m scripts.load_test --users 10 --seconds 600 --output reports/load-5.json
```

Ejecutar después del calentamiento de servicios; repetir para 50 cruces. El script separa
latencias de consultas y propuestas, registra errores y conflictos, y no solicita aplicar planes.
La preparación del catálogo y las observaciones se realiza antes; verificar conteos aceptados
contra BD además de los tiempos. Las escrituras de propuestas generan auditoría, por lo que
debe medirse el tamaño de BD y ejecutarse en un entorno descartable.

Alpha: los cuatro integrantes recorren el guion de operación, fallas, intervención, comparación
y reversión; QA registra defecto, severidad, requisito y evidencia. Salida: ningún crítico/alto
abierto y regresión aprobada. Beta: cinco evaluadores académicos realizan consulta de tráfico,
identificación de una alerta e intervención. Registrar por persona/tarea: éxito, tiempo, ayuda
recibida y observación. Exigir al menos cuatro éxitos sin ayuda en ≤180 s por tarea. No se
prellenan actas ni se inventan evaluadores.

Antes del cierre, el representante académico revisa resultados positivos o negativos, limitaciones,
restauración, trazabilidad y manuales. Promover un modelo, aprobar un PR y aceptar el proyecto
son decisiones distintas. El equipo conserva la línea base si una hipótesis experimental falla.

## 6. Gestión de cambios y regresión

Cada PR debe identificar RF/RNF/RB afectados, riesgo, pruebas y efecto en configuración/PERT.
En controlador, autenticación y evaluación del modelo se requiere revisión de otro integrante.
Ejecutar las familias relacionadas antes de integrar y la CI completa al abrir el PR. La CI
publica JUnit; no realiza despliegues, promociones ni aceptación humana. Nuevas métricas de prueba
final no deben utilizarse para ajustar repetidamente el mismo candidato; crear una nueva versión
y reservar nuevos escenarios/periodos si cambia el experimento.

"""Manual de usuario ilustrado, guiones verificables y consolidación de resultados reales."""

from pathlib import Path
import json
from xml.etree import ElementTree

from scripts.build_academic_content import write, OUT

TESTS = [
    (
        "Contratos y permisos",
        "Unidad/API",
        "RF_001, RF_007",
        "Líder y QA",
        "BD aislada; admin/viewer; entradas válidas e inválidas",
        "Autenticar admin; solicitar propuesta; repetir sin token; repetir como viewer; enviar ID negativo y atributo extra",
        "201 con propuesta válida; 401/403 para accesos no autorizados; 422 contrato",
        "tests/test_api.py",
    ),
    (
        "Reproducibilidad y datos",
        "Unidad/datos",
        "RF_003, RF_005",
        "IA y QA",
        "Semilla fija 123, cinco días, fuente sintética",
        "Generar dos datasets; comparar filas; reconstruir atributos; probar clima ausente, ventanas sin zona y duración inválida",
        "Datasets idénticos; atributos concordantes; contrato inválido rechazado",
        "tests/test_data_ml.py",
    ),
    (
        "Persistencia e idempotencia",
        "Integración/BD",
        "RF_004, RNF_006",
        "Líder y QA",
        "BD temporal, lote con repetido y negativo",
        "Registrar lote; reenviar; consultar conteo; cambiar zona de la misma ventana; provocar rollback PostgreSQL",
        "Una observación por clave; UTC preservado; ninguna confirmación de transacción fallida",
        "tests/test_api.py; tests/test_postgres.py",
    ),
    (
        "Invariantes semafóricas",
        "Unidad/propiedades",
        "RF_008, RB_001 a RB_008",
        "Líder y QA",
        "3000 demandas y 41 repartos válidos",
        "Sugerir planes desde diferentes anteriores; recorrer 120 segundos de cada reparto; contar autorizaciones y peatones",
        "Suma vehicular 80; verdes 20–60; cambio ≤5 en automático; 20 s peatón; cero conflicto",
        "tests/test_controller.py",
    ),
    (
        "Modelo y experimento",
        "Validación ML/control",
        "RF_007, RF_013",
        "IA y QA",
        "Modelo propio, hash, dataset y semillas reservadas",
        "Inspeccionar cortes/purga; comparar MAE/RMSE contra persistencia; ejecutar 50 pares; calcular IC por corridas; revisar cada escenario",
        "Sin fuga; meta predictiva −10% MAE; control −10% demora con IC inferior >0 y cola p95 ≤+10%; conservar negativos",
        "reports/model_evaluation.json; reports/experiment.json",
    ),
    (
        "Fallas y concurrencia",
        "Sistema/resiliencia",
        "RF_009, RF_010, RF_011",
        "QA",
        "Timeout inyectado, dato viejo, dos solicitudes simultáneas",
        "Vencer observación 121 s; simular timeout/NaN; aplicar manual; hacerlo caducar; competir por versión; avanzar offline y reconciliar",
        "Fallback fijo al límite; manual no omite reglas; una reserva gana; se conservan vehículos",
        "tests/test_worker.py; tests/test_postgres.py",
    ),
    (
        "Flujo de extremo a extremo",
        "Sistema/humo",
        "RF_003 a RF_014",
        "QA y Frontend",
        "Puertos 18000/18001/18501 libres; datos efímeros",
        "Iniciar procesos de prueba; autenticar; consultar cinco cruces; proponer; solicitar aplicación; esperar ACTIVE; consultar auditoría; cerrar procesos",
        "Cuatro servicios responden; propuesta no aplica sola; aplicación confirmada; cola=llegadas−salidas",
        "scripts/smoke_test.py; reports/smoke.json",
    ),
    (
        "Seguridad e integridad de modelos",
        "Seguridad/negativas",
        "RF_001, RF_015, RNF_005",
        "Líder y QA",
        "Usuario viewer, artefacto alterado y candidato no elegible",
        "Intentar escritura sin permiso; alterar bytes de modelo; promover sin revisores distintos; observar logs; ejecutar revisión de dependencias separada",
        "401/403; hash inválido bloqueado; no promoción inválida; ningún secreto en auditoría",
        "tests/test_model_service.py; revisión manual de dependencias pendiente",
    ),
    (
        "Respaldo y recuperación",
        "Operación/recuperación",
        "RNF_010",
        "QA y Líder",
        "BD PostgreSQL de laboratorio y destino nuevo vacío",
        "Detener escritores de fuente; pg_dump custom; crear destino; pg_restore sin clean; comparar conteos; cronometrar; validar reinicio desde despeje",
        "Restauración íntegra en laboratorio; objetivo RPO≤24 h/RTO≤30 min se evalúa con alcance explícito",
        "scripts/academic_validation.py; reports/academico/recovery.json",
    ),
    (
        "Aceptación Alpha y Beta",
        "Aceptación/usabilidad",
        "RNF_007, RF_012",
        "QA y cinco evaluadores reales",
        "Build estable, instrucciones y consentimiento académico",
        "Alpha: cuatro integrantes recorren operación/fallas; Beta: cinco personas consultan tráfico, identifican alerta e intervienen; medir tiempo y ayuda",
        "Al menos 4/5 completan cada tarea sin ayuda en ≤180 s; cero defectos críticos/altos abiertos",
        "Formulario ACTA_001 de este documento; pendiente evaluación humana",
    ),
    (
        "Promoción y reversión",
        "Integración/modelos",
        "RF_015",
        "IA, Líder y QA",
        "Dos modelos propios elegibles y evidencia independiente",
        "Promover con autor/revisor reales; reiniciar IA; obtener inferencia versionada; volver a modelo previo; comprobar auditabilidad",
        "Hash/versiones correctos y posibilidad de volver al anterior; no simular firmas humanas",
        "tests/test_model_service.py; ejercicio operativo de reversión pendiente",
    ),
    (
        "Rendimiento y escala",
        "Carga/capacidad",
        "RNF_001, RNF_002",
        "QA y Líder",
        "5 y 50 cruces, 10 usuarios, 600 s por perfil tras calentamiento",
        "Iniciar perfiles de laboratorio; recorrer catálogo completo en round-robin; medir consultas/propuestas; conservar conflictos/errores; comparar aceptados con BD",
        "p95 consulta≤500 ms y predicción≤1000 ms; sin pérdida de entradas aceptadas; resultados negativos se reportan",
        "scripts/academic_validation.py; reports/academico/load-5.json y load-50.json",
    ),
    (
        "Modificabilidad",
        "Mantenibilidad/regresión",
        "RNF_003, RNF_008",
        "Frontend, IA y QA",
        "Adaptador de inferencia alterno y configuración de descarga",
        "Sustituir inferencia por fixture; modificar carriles/capacidad mediante API; repetir propiedades sin editar máquina de fases; revisar cobertura de ramas",
        "Contrato estable; fases seguras; ramas ≥80% en controlador y esquemas; límites semafóricos requieren cambio revisado",
        "tests/test_model_service.py; tests/test_controller.py; cobertura",
    ),
]


def manual():
    write(
        "DOC_003_Manual.md",
        r"""# DOC_003 Manual de instalación y usuario

Versión 1.0 · Cuauhtémoc · ENT_003 · 1 de noviembre de 2026.
Para el administrador y equipo de desarrollo. Todos los cruces, colas y semáforos son simulados.

## MAN_001 Requisitos previos

Python 3.13, equipo de desarrollo con 8 GB RAM mínimo y directorio del repositorio completo.
PostgreSQL es la base principal; SQLite permite demostración local sin servidor adicional.
Docker y Compose son opcionales. Acceso a internet solo para instalar dependencias o fuente
externa autorizada. GPU no requerida. No conectar el prototipo a infraestructura física.

## MAN_002 Instalación local en Windows

Abrir PowerShell en la raíz del repositorio. Ejecutar:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.lock
.\.venv\Scripts\python.exe -m scripts.configure
.\.venv\Scripts\python.exe -m scripts.select_cuauhtemoc
.\.venv\Scripts\python.exe -m scripts.run_local
```

No cerrar esa terminal mientras se usa el sistema. Abrir http://127.0.0.1:8501 y verificar
http://127.0.0.1:8000/health. Swagger está en http://127.0.0.1:8000/docs; visitar / puede
devolver 404 porque no existe página de inicio de API. El lanzador inicia cuatro procesos y
comprueba puertos 8000, 8001 y 8501. No iniciar Uvicorn por separado al usar el lanzador.

El selector usa una BD nueva data/cuauhtemoc.db y conserva data/traffic.db. Si hay URL
personalizada, preparar una base nueva explícitamente en lugar de sobrescribir configuración.
Las capturas de este manual proceden de una instancia temporal con credenciales efímeras.

## MAN_003 Acceso

Consultar ADMIN_EMAIL y ADMIN_PASSWORD en .env; copiar solo el valor a la derecha del signo
igual, sin espacios ni comillas adicionales. La contraseña generada es larga; conservarla de
forma privada. No compartir .env. Pulsar Entrar. Una sesión vence tras una hora.
Modificar ADMIN_PASSWORD en .env no cambia por sí solo el hash de un usuario ya existente;
el inicializador solo crea usuarios ausentes. Para restablecer una cuenta existente se necesita
un procedimiento administrativo controlado, sin borrar la BD.

![FIG_007 Acceso a la instancia temporal](figuras/FIG_007_acceso.png)

## MAN_004 Consultar circulación y tiempos

Elegir CUA_001 a CUA_005 en el menú lateral. Revisar reloj simulado, ciclo, modo confirmado,
colas NS/EO y colores con texto. La tabla indica verde, amarillo y rojo en segundos; el gráfico
presenta llegadas veh/min. La fecha de observación y la procedencia acompañan cada fila.
El reloj simulado puede avanzar más rápido que el real según SIM_SPEED. No comparar su
antigüedad con la hora del navegador para decidir si la fuente está vigente.

![FIG_008 Monitor y tabla de tiempos](figuras/FIG_008_monitor.png)

## MAN_005 Interpretar los modos

Automático: demanda pronosticada y control restringido. Manual: intervención validada vigente.
Degradado: plan fijo 40/40 por datos ausentes/vencidos, IA indisponible o recuperación.
Sin heartbeat por más de cinco segundos: estado desconocido; los colores antiguos no acreditan
la fase actual. La demanda puede modificar verdes, pero no suprime peatones ni transiciones.
Con NS=30 y EO=10 veh/min desde 40/40, el siguiente ciclo propone 45/35 por el límite de ±5 s.

## MAN_006 Pedir una propuesta

Pulsar Obtener propuesta del modelo. La respuesta muestra modo, motivo, demanda y tiempos.
PROPOSED significa que no se aplicó. Para solicitar aplicación mediante API usar POST
/plans/{id}/apply con previous_version y target_cycle de la propuesta. PENDING tampoco es
confirmación: esperar ACTIVE y applied_at. Si la versión cambió, refrescar antes de reintentar.
El trabajador genera también sus propias propuestas al decidir ciclos automáticamente.

## MAN_007 Intervención manual y retorno

Usar el deslizador de verde NS; EO es el complemento para sumar 80. Escribir un motivo
descriptivo de al menos cinco caracteres; seleccionar 1 a 10 ciclos y solicitar intervención.
Comprobar confirmación en un ciclo posterior. El modo degradado tiene precedencia: una
intervención no evita fallback por IA/fuente inválida. Pulsar Volver al automático para cancelar
la intervención desde el siguiente ciclo; la solicitud no cambia una fase a mitad.

![FIG_009 Intervención administrativa](figuras/FIG_009_intervencion.png)

## MAN_008 Exportación y auditoría

Exportar observaciones JSON descarga datos con fechas, unidades y procedencia. No hay CSV
arbitrario que permita fórmulas de hoja de cálculo. Abrir Auditoría reciente y pulsar Consultar
auditoría para ver actor, acción, antes/después, motivo y correlación. Viewer no puede escribir.

![FIG_010 Auditoría de la instancia de demostración](figuras/FIG_010_auditoria.png)

## MAN_009 Solución de errores

| ID | Mensaje | Acción |
|---|---|---|
| ERR_001 | Sin comunicación con API | Comprobar /health y reports/local/api.log; mantener lanzador abierto |
| ERR_002 | LocalProtocolError | Actualizar el código; el login no debe enviar Bearer vacío; recargar Ctrl+F5 |
| ERR_003 | Puerto ocupado / WinError 10048 | Detener ejecución anterior con Ctrl+C; no arrancar dos lanzadores; identificar PID antes de cerrar un proceso |
| ERR_004 | Credenciales inválidas / 401 | Comprobar valores de .env y cuenta existente; volver a iniciar sesión si venció |
| ERR_005 | 403 | Solicitar una cuenta con permiso administrativo para modificar |
| ERR_006 | 409 | Refrescar versión/ciclo; no repetir ciegamente aplicación antigua |
| ERR_007 | 422 | Revisar contrato, duración, sumas, motivo y zona horaria |
| ERR_008 | IA 503 / loaded=false | Revisar modelo promovido, hash, versión y reiniciar IA; fijo sigue disponible |
| ERR_009 | forrtl tras Ctrl+C | El mensaje corresponde al cierre de librerías numéricas; comprobar que los puertos queden libres antes de reiniciar |
| ERR_010 | Trabajador sin telemetría | Revisar worker.log y lease; reiniciar desde despeje, no asumir color anterior |

Para diagnosticar un puerto usar netstat -ano, sin cerrar procesos desconocidos. Los registros
no deben contener contraseñas/tokens. Los servicios de prueba usan otros puertos y credenciales.

## MAN_010 Instalación PostgreSQL o Compose

Crear BD nueva de laboratorio y configurar DATABASE_URL con postgresql+psycopg. Ejecutar
database.manage con propietario para migrar, luego usar traffic_app con permisos restringidos
de database/runtime_permissions.sql. APP_DB_PASSWORD permite provisionar ese rol en el
inicializador. Codificar caracteres reservados si se usan contraseñas manuales en una URL.
En Compose ejecutar docker compose up --build; el inicializador usa propietario y runtime
rol restringido. Solo dashboard/API se publican en localhost; BD/IA permanecen internos.
Para exposición externa se requiere TLS, acceso de red y revisión de seguridad adicionales.

## MAN_011 Entrenamiento promoción y reversión

```text
python -m ml_model.train_model --days 90 --seed 42
python -m ml_model.evaluate VERSION
python -m ml_model.promote VERSION --experiment reports/experiment.json --author NOMBRE_IA --reviewer NOMBRE_QA --reason REVISION_REAL_DOCUMENTADA
```

VERSION es el identificador impreso al entrenar. Revisores diferentes deben ser personas reales,
no nombres inventados. Reiniciar IA para cargar el modelo elegido. Revertir usa una versión
previa con su evidencia y motivo. No cargar artefactos de origen desconocido ni modificar modelos
en caliente. El nuevo alcance territorial no convierte modelos sintéticos en modelos calibrados.

## MAN_012 Respaldo recuperación y retiro

Ejecutar scripts.backup con pg_dump autorizado. Copiar también manifiestos y configuración
protegida. Restaurar con pg_restore --no-owner --no-acl a una BD nueva vacía, sin --clean;
comparar conteos/hashes y medir tiempo antes de cambiar URL. Ver DOC_004 PRU_009.
El ensayo de laboratorio no sustituye una política diaria de respaldos ni RTO integral de operación.
Detener con Ctrl+C. docker compose down conserva volumen; no borrar datos sin decisión explícita.
Reiniciar trabajador desde diez segundos de despeje. Revocar credenciales al retirar el prototipo.
""",
    )


def testing():
    parts = [
        """# DOC_004 Documento y guiones de pruebas

Versión 1.0 · ENT_004 · 1 de noviembre de 2026. Estrategia: unidad → integración → sistema
→ validación/aceptación. QA prepara datos y consolida evidencia; otro integrante revisa cambios
de control, seguridad y ML. No usar datos productivos ni secretos de usuario en pruebas.

## PLAN_001 Entrada salida y severidad

Entrada: dependencias fijadas, esquema aislado, requisito y versión identificados. Salida:
resultados reproducibles, sin defectos críticos/altos abiertos y criterios de aceptación revisados.
Crítico: permite fases incompatibles, acceso administrativo indebido o pérdida silenciosa de
integridad. Alto: impide función obligatoria sin alternativa. Medio/bajo: efecto acotado con
alternativa. Registrar ID DEF_###, requisito, pasos, esperado/obtenido, evidencia, severidad,
responsable y prueba de regresión. No clasificar automáticamente un criterio fallido como aprobado.

## PLAN_002 Comandos reproducibles

```text
python -m pytest --cov=backend.app.controller --cov=backend.app.schemas --cov-branch
python -m scripts.smoke_test
python -m ml_model.evaluate VERSION
python -m scripts.academic_validation
```

TEST_DATABASE_URL debe apuntar a PostgreSQL aislado para las pruebas específicas. La suite
crea/elimina únicamente esquemas UUID propios. academic_validation utiliza bases nuevas,
puertos 28000/28100 y 600 s con diez usuarios para cada escala; no toca la BD Cuauhtémoc.
No confundir la verificación del contrato con mocks con la evaluación del modelo entrenado.
"""
    ]
    for i, (name, kind, req, owner, data, steps, expected, evidence) in enumerate(TESTS, 1):
        parts.append(
            f"## PRU_{i:03d} {name}\n\n**Tipo:** {kind}. **Requisitos:** {req}. **Responsable:** {owner}.\n\n**Precondición y datos:** {data}.\n\n### GUI_{i:03d} Pasos\n"
        )
        parts.extend(
            f"{n}. {step.strip().capitalize()}." for n, step in enumerate(steps.split(";"), 1)
        )
        parts.append(
            f"\n**Resultado esperado y criterio:** {expected}.\n\n**Evidencia a conservar:** `{evidence}`; versión, fecha, semilla/configuración y resultado obtenido.\n\n**Resultado obtenido:** consultar DOC_005 y el archivo indicado; si no hay ejecución registrada, marcar PENDIENTE, no APROBADO.\n"
        )
    parts.append("""## ACTA_001 Formato de evaluación humana sin prefirmar

Registrar ID EVAL_001..005, fecha, versión, tarea, tiempo en segundos, ayuda recibida, éxito,
evidencia y observación. Tareas TAR_001 consultar tráfico/tiempos; TAR_002 identificar alerta
y causa; TAR_003 solicitar intervención y comprobar aplicación. Al menos cuatro de cinco
evaluadores deben completar cada tarea sin ayuda en ≤180 s. Un fallo de seguridad/control
impide aceptación aunque el promedio de tiempos sea favorable.

| ID | Evaluador real | TAR_001 | TAR_002 | TAR_003 | Evidencia y firma |
|---|---|---|---|---|---|
| EVAL_001 | Por asignar | Pendiente | Pendiente | Pendiente | Pendiente |
| EVAL_002 | Por asignar | Pendiente | Pendiente | Pendiente | Pendiente |
| EVAL_003 | Por asignar | Pendiente | Pendiente | Pendiente | Pendiente |
| EVAL_004 | Por asignar | Pendiente | Pendiente | Pendiente | Pendiente |
| EVAL_005 | Por asignar | Pendiente | Pendiente | Pendiente | Pendiente |

## ACTA_002 Transferencia y aceptación

El docente revisa alcance, evidencia, limitaciones y correcciones. Registrar fecha, versión,
participantes reales, observaciones, defectos abiertos y decisión (aceptado/condicionado/rechazado).
No completar nombres, tiempos ni firmas por inferencia. Las plantillas son parte de la entrega;
la participación y aceptación humana permanecen pendientes hasta ejecutarlas.
""")
    write("DOC_004_Pruebas.md", "\n".join(parts))


def results():
    parts = [
        "# DOC_005 Resultados de verificación y límites de aceptación\n\nENT_005 · 1 de noviembre de 2026. Se consolidan archivos reales; no se inventan resultados ausentes.\n"
    ]
    junit = Path("reports/academico/tests.xml")
    if junit.exists():
        suites = list(ElementTree.parse(junit).getroot().iter("testsuite"))
        values = {
            k: sum(int(s.get(k, 0)) for s in suites)
            for k in ("tests", "failures", "errors", "skipped")
        }
        parts.append(
            "## RES_001 Batería automatizada actual\n\n"
            + "; ".join(f"{k}: **{v}**" for k, v in values.items())
            + ". Fuente: reports/academico/tests.xml.\n"
        )
    cov = Path("reports/academico/coverage.json")
    if cov.exists():
        c = json.loads(cov.read_text())
        parts.append(
            f"Cobertura combinada en controlador/esquemas: **{c['totals']['percent_covered']:.2f}%**. No es cobertura global de toda la aplicación.\n"
        )
        for file, v in c["files"].items():
            s = v["summary"]
            parts.append(f"- {file}: ramas {s['covered_branches']}/{s['num_branches']}.\n")
    regression = Path("reports/academico/regression-concurrency.xml")
    if regression.exists():
        suites = list(ElementTree.parse(regression).getroot().iter("testsuite"))
        total = sum(int(s.get("tests", 0)) for s in suites)
        failed = sum(int(s.get("failures", 0)) + int(s.get("errors", 0)) for s in suites)
        parts.append(
            f"Regresión posterior de la corrección de concurrencia: **{total} pruebas**, {failed} fallas/errores. Es una ejecución independiente, no se suma a la batería completa anterior. Fuente: reports/academico/regression-concurrency.xml.\n"
        )
    parts.append(
        "## RES_002 Carga real de laboratorio\n\nLos dos perfiles se ejecutan simultáneamente en el mismo equipo; comparten CPU y PostgreSQL. Durante el ensayo también se generaron artefactos documentales, por lo que no es un benchmark de hardware aislado. Se recorren todos los cruces por usuario; no se demuestra coordinación vial. El conteo de ingesta comprueba entradas test aceptadas, mientras el trabajador continúa observaciones sintéticas.\n"
    )
    for count in (5, 50):
        file = Path(f"reports/academico/load-{count}.json")
        if file.exists():
            r = json.loads(file.read_text())
            parts.append(
                f"### RES_CARGA_{count:03d} Perfil de {count} cruces\n\n10 usuarios, {r['duration_s']} s, {r.get('database', 'ver reporte')}. Consultas: {r['query']['requests']} con p95 {r['query']['p95_ms']:.2f} ms; propuestas: {r['prediction']['requests']} con p95 {r['prediction']['p95_ms']:.2f} ms. Errores: {r['errors']}; conflictos de versión registrados: {r['conflicts']}.\n\nMeta de latencia: **{'CUMPLE' if r.get('latency_targets_passed') else 'NO CUMPLE'}**. Entradas aceptadas/persistidas: {r.get('accepted_test_records')}/{r.get('persisted_test_records')}. Preservación: {r.get('accepted_records_preserved')}. Fuente: `{file.as_posix()}`. Un resultado negativo exige corrección/perfilado y repetición; no se redefine el umbral para aprobar.\n"
            )
        else:
            parts.append(f"Perfil {count}: PENDIENTE; todavía no existe {file.as_posix()}.\n")
    if Path("reports/academico/ensayo-inicial/load-5.json").exists():
        parts.append(
            "### RES_006 Comparación con el ensayo inicial\n\nEl ensayo inicial no cumplió latencia de predicción y registró errores. Se conserva en reports/academico/ensayo-inicial. La corrección limita el modelo a un hilo por inferencia HTTP, precarga grupos para evitar consultas N+1 y usa FOR NO KEY UPDATE en el trabajador para permitir referencias FK concurrentes sin perder exclusión de escritores. No cambia las reglas semafóricas ni las predicciones del modelo. Se repitió el protocolo con bases nuevas; comparar ambos resultados, sin ocultar el negativo.\n"
        )
    rec = Path("reports/academico/recovery.json")
    parts.append("## RES_003 Respaldo y restauración\n")
    if rec.exists():
        r = json.loads(rec.read_text())
        parts.append(
            f"pg_dump: {r['backup_s']:.2f} s; pg_restore: {r['restore_s']:.2f} s. Comparación de conteos: **{r['counts_match']}**. Restauración menor de 30 min: {r['restore_target_30min_passed']}. RPO observado en fuente detenida: {r['rpo_measured_s']} s. Fuente: reports/academico/recovery.json.\n\nEste ensayo verifica restauración de laboratorio, no política diaria ni RTO integral incluyendo reanudación y validación humana.\n"
        )
    else:
        parts.append("PENDIENTE: no hay aún reporte del ejercicio de restauración.\n")
    model = json.loads(Path("reports/model_evaluation.json").read_text())
    e = json.loads(Path("reports/experiment.json").read_text())
    parts.append(
        f"## RES_004 Modelo y control de referencia\n\nModelo {model['version']}; MAE {model['metrics']['test']['model']['mae']:.4f} frente a persistencia {model['metrics']['test']['persistence']['mae']:.4f} veh/min. 50 pares; reducción media de demora no sobresaturada {e['mean_delay_reduction']:.2%}; IC95 [{e['ci95'][0]:.2%}, {e['ci95'][1]:.2%}]. Resultados sintéticos generales de la línea base; no aforos ni validación territorial de Cuauhtémoc.\n"
    )
    parts.append(
        "## RES_005 Estado de cierre\n\nLos documentos, diagramas y guiones están entregados. Permanecen sujetos a revisión humana: Alpha/Beta, identidad/aprobación de revisores de modelos, revisión de dependencias/TLS, reversión operativa y aceptación del docente. Docker no estaba instalado: su perfil está preparado, sin afirmar ejecución. Los criterios de rendimiento/recuperación se juzgan con los resultados anteriores, no por existencia de scripts. Si hay fallas de meta, el prototipo sigue siendo demostrable pero no se declara RNF aceptado.\n"
    )
    write("DOC_005_Resultados.md", "\n".join(parts))


if __name__ == "__main__":
    OUT.mkdir(exist_ok=True)
    manual()
    testing()
    results()

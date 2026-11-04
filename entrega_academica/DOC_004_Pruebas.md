# DOC_004 Documento y guiones de pruebas

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

## PRU_001 Contratos y permisos

**Tipo:** Unidad/API. **Requisitos:** RF_001, RF_007. **Responsable:** Líder y QA.

**Precondición y datos:** BD aislada; admin/viewer; entradas válidas e inválidas.

### GUI_001 Pasos

1. Autenticar admin.
2. Solicitar propuesta.
3. Repetir sin token.
4. Repetir como viewer.
5. Enviar id negativo y atributo extra.

**Resultado esperado y criterio:** 201 con propuesta válida; 401/403 para accesos no autorizados; 422 contrato.

**Evidencia a conservar:** `tests/test_api.py`; versión, fecha, semilla/configuración y resultado obtenido.

**Resultado obtenido:** consultar DOC_005 y el archivo indicado; si no hay ejecución registrada, marcar PENDIENTE, no APROBADO.

## PRU_002 Reproducibilidad y datos

**Tipo:** Unidad/datos. **Requisitos:** RF_003, RF_005. **Responsable:** IA y QA.

**Precondición y datos:** Semilla fija 123, cinco días, fuente sintética.

### GUI_002 Pasos

1. Generar dos datasets.
2. Comparar filas.
3. Reconstruir atributos.
4. Probar clima ausente, ventanas sin zona y duración inválida.

**Resultado esperado y criterio:** Datasets idénticos; atributos concordantes; contrato inválido rechazado.

**Evidencia a conservar:** `tests/test_data_ml.py`; versión, fecha, semilla/configuración y resultado obtenido.

**Resultado obtenido:** consultar DOC_005 y el archivo indicado; si no hay ejecución registrada, marcar PENDIENTE, no APROBADO.

## PRU_003 Persistencia e idempotencia

**Tipo:** Integración/BD. **Requisitos:** RF_004, RNF_006. **Responsable:** Líder y QA.

**Precondición y datos:** BD temporal, lote con repetido y negativo.

### GUI_003 Pasos

1. Registrar lote.
2. Reenviar.
3. Consultar conteo.
4. Cambiar zona de la misma ventana.
5. Provocar rollback postgresql.

**Resultado esperado y criterio:** Una observación por clave; UTC preservado; ninguna confirmación de transacción fallida.

**Evidencia a conservar:** `tests/test_api.py; tests/test_postgres.py`; versión, fecha, semilla/configuración y resultado obtenido.

**Resultado obtenido:** consultar DOC_005 y el archivo indicado; si no hay ejecución registrada, marcar PENDIENTE, no APROBADO.

## PRU_004 Invariantes semafóricas

**Tipo:** Unidad/propiedades. **Requisitos:** RF_008, RB_001 a RB_008. **Responsable:** Líder y QA.

**Precondición y datos:** 3000 demandas y 41 repartos válidos.

### GUI_004 Pasos

1. Sugerir planes desde diferentes anteriores.
2. Recorrer 120 segundos de cada reparto.
3. Contar autorizaciones y peatones.

**Resultado esperado y criterio:** Suma vehicular 80; verdes 20–60; cambio ≤5 en automático; 20 s peatón; cero conflicto.

**Evidencia a conservar:** `tests/test_controller.py`; versión, fecha, semilla/configuración y resultado obtenido.

**Resultado obtenido:** consultar DOC_005 y el archivo indicado; si no hay ejecución registrada, marcar PENDIENTE, no APROBADO.

## PRU_005 Modelo y experimento

**Tipo:** Validación ML/control. **Requisitos:** RF_007, RF_013. **Responsable:** IA y QA.

**Precondición y datos:** Modelo propio, hash, dataset y semillas reservadas.

### GUI_005 Pasos

1. Inspeccionar cortes/purga.
2. Comparar mae/rmse contra persistencia.
3. Ejecutar 50 pares.
4. Calcular ic por corridas.
5. Revisar cada escenario.

**Resultado esperado y criterio:** Sin fuga; meta predictiva −10% MAE; control −10% demora con IC inferior >0 y cola p95 ≤+10%; conservar negativos.

**Evidencia a conservar:** `reports/model_evaluation.json; reports/experiment.json`; versión, fecha, semilla/configuración y resultado obtenido.

**Resultado obtenido:** consultar DOC_005 y el archivo indicado; si no hay ejecución registrada, marcar PENDIENTE, no APROBADO.

## PRU_006 Fallas y concurrencia

**Tipo:** Sistema/resiliencia. **Requisitos:** RF_009, RF_010, RF_011. **Responsable:** QA.

**Precondición y datos:** Timeout inyectado, dato viejo, dos solicitudes simultáneas.

### GUI_006 Pasos

1. Vencer observación 121 s.
2. Simular timeout/nan.
3. Aplicar manual.
4. Hacerlo caducar.
5. Competir por versión.
6. Avanzar offline y reconciliar.

**Resultado esperado y criterio:** Fallback fijo al límite; manual no omite reglas; una reserva gana; se conservan vehículos.

**Evidencia a conservar:** `tests/test_worker.py; tests/test_postgres.py`; versión, fecha, semilla/configuración y resultado obtenido.

**Resultado obtenido:** consultar DOC_005 y el archivo indicado; si no hay ejecución registrada, marcar PENDIENTE, no APROBADO.

## PRU_007 Flujo de extremo a extremo

**Tipo:** Sistema/humo. **Requisitos:** RF_003 a RF_014. **Responsable:** QA y Frontend.

**Precondición y datos:** Puertos 18000/18001/18501 libres; datos efímeros.

### GUI_007 Pasos

1. Iniciar procesos de prueba.
2. Autenticar.
3. Consultar cinco cruces.
4. Proponer.
5. Solicitar aplicación.
6. Esperar active.
7. Consultar auditoría.
8. Cerrar procesos.

**Resultado esperado y criterio:** Cuatro servicios responden; propuesta no aplica sola; aplicación confirmada; cola=llegadas−salidas.

**Evidencia a conservar:** `scripts/smoke_test.py; reports/smoke.json`; versión, fecha, semilla/configuración y resultado obtenido.

**Resultado obtenido:** consultar DOC_005 y el archivo indicado; si no hay ejecución registrada, marcar PENDIENTE, no APROBADO.

## PRU_008 Seguridad e integridad de modelos

**Tipo:** Seguridad/negativas. **Requisitos:** RF_001, RF_015, RNF_005. **Responsable:** Líder y QA.

**Precondición y datos:** Usuario viewer, artefacto alterado y candidato no elegible.

### GUI_008 Pasos

1. Intentar escritura sin permiso.
2. Alterar bytes de modelo.
3. Promover sin revisores distintos.
4. Observar logs.
5. Ejecutar revisión de dependencias separada.

**Resultado esperado y criterio:** 401/403; hash inválido bloqueado; no promoción inválida; ningún secreto en auditoría.

**Evidencia a conservar:** `tests/test_model_service.py; revisión manual de dependencias pendiente`; versión, fecha, semilla/configuración y resultado obtenido.

**Resultado obtenido:** consultar DOC_005 y el archivo indicado; si no hay ejecución registrada, marcar PENDIENTE, no APROBADO.

## PRU_009 Respaldo y recuperación

**Tipo:** Operación/recuperación. **Requisitos:** RNF_010. **Responsable:** QA y Líder.

**Precondición y datos:** BD PostgreSQL de laboratorio y destino nuevo vacío.

### GUI_009 Pasos

1. Detener escritores de fuente.
2. Pg_dump custom.
3. Crear destino.
4. Pg_restore sin clean.
5. Comparar conteos.
6. Cronometrar.
7. Validar reinicio desde despeje.

**Resultado esperado y criterio:** Restauración íntegra en laboratorio; objetivo RPO≤24 h/RTO≤30 min se evalúa con alcance explícito.

**Evidencia a conservar:** `scripts/academic_validation.py; reports/academico/recovery.json`; versión, fecha, semilla/configuración y resultado obtenido.

**Resultado obtenido:** consultar DOC_005 y el archivo indicado; si no hay ejecución registrada, marcar PENDIENTE, no APROBADO.

## PRU_010 Aceptación Alpha y Beta

**Tipo:** Aceptación/usabilidad. **Requisitos:** RNF_007, RF_012. **Responsable:** QA y cinco evaluadores reales.

**Precondición y datos:** Build estable, instrucciones y consentimiento académico.

### GUI_010 Pasos

1. Alpha: cuatro integrantes recorren operación/fallas.
2. Beta: cinco personas consultan tráfico, identifican alerta e intervienen.
3. Medir tiempo y ayuda.

**Resultado esperado y criterio:** Al menos 4/5 completan cada tarea sin ayuda en ≤180 s; cero defectos críticos/altos abiertos.

**Evidencia a conservar:** `Formulario ACTA_001 de este documento; pendiente evaluación humana`; versión, fecha, semilla/configuración y resultado obtenido.

**Resultado obtenido:** consultar DOC_005 y el archivo indicado; si no hay ejecución registrada, marcar PENDIENTE, no APROBADO.

## PRU_011 Promoción y reversión

**Tipo:** Integración/modelos. **Requisitos:** RF_015. **Responsable:** IA, Líder y QA.

**Precondición y datos:** Dos modelos propios elegibles y evidencia independiente.

### GUI_011 Pasos

1. Promover con autor/revisor reales.
2. Reiniciar ia.
3. Obtener inferencia versionada.
4. Volver a modelo previo.
5. Comprobar auditabilidad.

**Resultado esperado y criterio:** Hash/versiones correctos y posibilidad de volver al anterior; no simular firmas humanas.

**Evidencia a conservar:** `tests/test_model_service.py; ejercicio operativo de reversión pendiente`; versión, fecha, semilla/configuración y resultado obtenido.

**Resultado obtenido:** consultar DOC_005 y el archivo indicado; si no hay ejecución registrada, marcar PENDIENTE, no APROBADO.

## PRU_012 Rendimiento y escala

**Tipo:** Carga/capacidad. **Requisitos:** RNF_001, RNF_002. **Responsable:** QA y Líder.

**Precondición y datos:** 5 y 50 cruces, 10 usuarios, 600 s por perfil tras calentamiento.

### GUI_012 Pasos

1. Iniciar perfiles de laboratorio.
2. Recorrer catálogo completo en round-robin.
3. Medir consultas/propuestas.
4. Conservar conflictos/errores.
5. Comparar aceptados con bd.

**Resultado esperado y criterio:** p95 consulta≤500 ms y predicción≤1000 ms; sin pérdida de entradas aceptadas; resultados negativos se reportan.

**Evidencia a conservar:** `scripts/academic_validation.py; reports/academico/load-5.json y load-50.json`; versión, fecha, semilla/configuración y resultado obtenido.

**Resultado obtenido:** consultar DOC_005 y el archivo indicado; si no hay ejecución registrada, marcar PENDIENTE, no APROBADO.

## PRU_013 Modificabilidad

**Tipo:** Mantenibilidad/regresión. **Requisitos:** RNF_003, RNF_008. **Responsable:** Frontend, IA y QA.

**Precondición y datos:** Adaptador de inferencia alterno y configuración de descarga.

### GUI_013 Pasos

1. Sustituir inferencia por fixture.
2. Modificar carriles/capacidad mediante api.
3. Repetir propiedades sin editar máquina de fases.
4. Revisar cobertura de ramas.

**Resultado esperado y criterio:** Contrato estable; fases seguras; ramas ≥80% en controlador y esquemas; límites semafóricos requieren cambio revisado.

**Evidencia a conservar:** `tests/test_model_service.py; tests/test_controller.py; cobertura`; versión, fecha, semilla/configuración y resultado obtenido.

**Resultado obtenido:** consultar DOC_005 y el archivo indicado; si no hay ejecución registrada, marcar PENDIENTE, no APROBADO.

## ACTA_001 Formato de evaluación humana sin prefirmar

Registrar ID EVAL_001..005, fecha, versión, tarea, tiempo en segundos, ayuda recibida, éxito,
evidencia y observación. Tareas TAR_001 consultar tráfico/tiempos; TAR_002 identificar alerta
y causa; TAR_003 solicitar intervención y comprobar aplicación. Al menos cuatro de cinco
evaluadores deben completar cada tarea sin ayuda en ≤180 s. Un fallo de seguridad/control
impide aceptación aunque el promedio de tiempos sea favorable.

**TAB_DOC_004_PRUEBAS_001**

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

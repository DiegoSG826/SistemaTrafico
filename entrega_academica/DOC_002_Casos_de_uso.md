# DOC_002 Especificación de casos de uso

Versión 1.0 · Cuauhtémoc · 1 de noviembre de 2026.

Todos los casos operan sobre semáforos simulados. ACT_001: administrador; ACT_002: proveedor de datos; ACT_003: evaluador académico que ejecuta herramientas de evaluación. El trabajador y la IA son componentes internos, no actores de interfaz.

## CU_001 Acceder

**Actor:** ACT_001. **Requisitos:** RF_001.

**Disparador:** el actor solicita acceder. **Precondiciones:** Credenciales y API disponibles.

**Entradas:** datos del contrato OpenAPI o parámetros CLI del caso. **Resultado:** Sesión válida de una hora o rechazo explícito.

### FLU_001 Flujo principal

1. Ingresar correo y contraseña.
2. Enviar formulario.
3. Verificar hash y usuario activo.
4. Emitir jwt.
5. Abrir monitor.

### ALT_001 Alternativas y excepciones

Credenciales inválidas: 401 sin sesión; API ausente: mensaje de conexión; token vencido: volver a entrar.

**Postcondición y criterio de aceptación:** No hay credenciales en registros ni encabezado Bearer vacío.

**Evidencia asociada:** `test_permissions, test_login_does_not_send_empty_bearer`. La existencia de una prueba no equivale a la aceptación humana del caso.

## CU_002 Gestionar catálogo

**Actor:** ACT_001. **Requisitos:** RF_002.

**Disparador:** el actor solicita gestionar catálogo. **Precondiciones:** Administrador autenticado y BD disponible.

**Entradas:** datos del contrato OpenAPI o parámetros CLI del caso. **Resultado:** Catálogo y configuración versionados.

### FLU_002 Flujo principal

1. Consultar versión.
2. Enviar alta/edición.
3. Validar coordenadas/capacidad.
4. Crear grupos ns/eo/peaton o editar.
5. Auditar y confirmar transacción.

### ALT_002 Alternativas y excepciones

Versión obsoleta: 409; valores inválidos: 422; fallo de BD: 503 sin éxito; catálogo referido se desactiva en vez de borrarse.

**Postcondición y criterio de aceptación:** Solo administra cruces del estudio sintético; no acredita geocerca oficial.

**Evidencia asociada:** `test_unknown_and_config_conflict, test_cuauhtemoc_catalog_is_idempotent_and_separate`. La existencia de una prueba no equivale a la aceptación humana del caso.

## CU_003 Registrar observaciones

**Actor:** ACT_002. **Requisitos:** RF_003, RF_004, RF_005.

**Disparador:** el actor solicita registrar observaciones. **Precondiciones:** Fuente identificada, grupo existente y lote de 1 a 1000 objetos.

**Entradas:** datos del contrato OpenAPI o parámetros CLI del caso. **Resultado:** Resultados aceptado/duplicado/rechazado por elemento.

### FLU_003 Flujo principal

1. Enviar ventanas de 60 s.
2. Validar estructura/unidades/utc.
3. Identificar faltantes y retraso.
4. Deduplicar por fuente/grupo/ventana.
5. Guardar elementos válidos.
6. Auditar resultados.

### ALT_003 Alternativas y excepciones

Duplicado: no crear otra fila; negativo/futuro/ventana inválida: rechazo individual; Waze sin aforo: guardar ausente y no habilitar adaptación.

**Postcondición y criterio de aceptación:** Cada observación aceptada conserva origen y ventana; no inventar conteos.

**Evidencia asociada:** `test_ingest_idempotent_mixed_batch, test_timezone_normalization_and_duplicate`. La existencia de una prueba no equivale a la aceptación humana del caso.

## CU_004 Consultar tráfico

**Actor:** ACT_001. **Requisitos:** RF_006.

**Disparador:** el actor solicita consultar tráfico. **Precondiciones:** Usuario autenticado.

**Entradas:** datos del contrato OpenAPI o parámetros CLI del caso. **Resultado:** Datos con unidad, fecha, fuente y calidad.

### FLU_004 Flujo principal

1. Elegir cruce/grupo.
2. Enviar rango temporal y paginación.
3. Consultar histórico.
4. Calcular antigüedad con reloj simulado.
5. Mostrar demanda y origen.

### ALT_004 Alternativas y excepciones

Fecha sin zona: 422; cruce desconocido: 404; falta de comunicación: estado desconocido.

**Postcondición y criterio de aceptación:** Una fila histórica no se presenta como observación vigente.

**Evidencia asociada:** `test_traffic_filters_and_dates`. La existencia de una prueba no equivale a la aceptación humana del caso.

## CU_005 Obtener pronóstico y propuesta

**Actor:** ACT_001. **Requisitos:** RF_007, RF_008.

**Disparador:** el actor solicita obtener pronóstico y propuesta. **Precondiciones:** Cruce activo, versión previa y observaciones registradas.

**Entradas:** datos del contrato OpenAPI o parámetros CLI del caso. **Resultado:** Propuesta persistida y sin cambio de color.

### FLU_005 Flujo principal

1. Solicitar propuesta.
2. Verificar versión.
3. Construir atributos de cinco ventanas.
4. Consultar ia con timeout.
5. Calcular verdes/restricciones.
6. Persistir modelo/predicciones/plan.
7. Devolver proposed.

### ALT_005 Alternativas y excepciones

Versión obsoleta: 409; IA o datos inválidos: 40/40 con modo degradado y causa; BD caída: 503.

**Postcondición y criterio de aceptación:** Demanda 30/10 desde 40/40 produce 45/35, rojo 72/82.

**Evidencia asociada:** `test_prediction_is_persisted_proposal_not_application, test_real_pipeline_through_internal_service_and_api`. La existencia de una prueba no equivale a la aceptación humana del caso.

## CU_006 Aplicar plan semafórico

**Actor:** ACT_001. **Requisitos:** RF_008, RF_009, RF_011.

**Disparador:** el actor solicita aplicar plan semafórico. **Precondiciones:** Plan PROPOSED, trabajador vigente y versión esperada.

**Entradas:** datos del contrato OpenAPI o parámetros CLI del caso. **Resultado:** Un único plan activo confirmado, con fase peatonal.

### FLU_006 Flujo principal

1. Solicitar aplicación al siguiente ciclo.
2. Reservar versión atómicamente.
3. Marcar pending.
4. Al límite volver a validar prioridad/datos.
5. Sustituir activo y confirmar aplicado_en.
6. Publicar estado.

### ALT_006 Alternativas y excepciones

Doble reserva o ciclo obsoleto: 409; trabajador vencido: 503; falla fuente/IA: prevalece fijo; caída BD: control local sin aceptar cambios humanos.

**Postcondición y criterio de aceptación:** Nunca aplicar a mitad de fase; la propuesta no implica aplicación.

**Evidencia asociada:** `test_queue_is_deferred_and_rejects_stale_version, test_apply_only_at_boundary_and_automatic_slew`. La existencia de una prueba no equivale a la aceptación humana del caso.

## CU_007 Intervenir y retornar al automático

**Actor:** ACT_001. **Requisitos:** RF_010, RF_011.

**Disparador:** el actor solicita intervenir y retornar al automático. **Precondiciones:** Administrador, motivo, versión y duración de 1 a 10 ciclos.

**Entradas:** datos del contrato OpenAPI o parámetros CLI del caso. **Resultado:** Intervención temporal y retorno controlado.

### FLU_007 Flujo principal

1. Introducir verdes complementarios.
2. Validar invariantes.
3. Reservar para siguiente ciclo.
4. Confirmar.
5. Respetar vigencia.
6. Caducar o solicitar retorno automático.
7. Auditar.

### ALT_007 Alternativas y excepciones

Verdes incompatibles o 11 ciclos: 422; versión antigua: 409; fuente/IA ausente: fallback tiene precedencia; no omitir peatones.

**Postcondición y criterio de aceptación:** Motivo obligatorio, suma 80 y ningún ciclo sin peatones.

**Evidencia asociada:** `test_manual_invariants_and_expiry, test_manual_expiry_and_fallback_precedence`. La existencia de una prueba no equivale a la aceptación humana del caso.

## CU_008 Comparar estrategias

**Actor:** ACT_003. **Requisitos:** RF_013, RF_015, RF_016.

**Disparador:** el actor solicita comparar estrategias. **Precondiciones:** Candidato y manifiesto propios; protocolo y semillas fijados.

**Entradas:** datos del contrato OpenAPI o parámetros CLI del caso. **Resultado:** Informe reproducible con resultados positivos o negativos.

### FLU_008 Flujo principal

1. Verificar hash.
2. Generar llegadas exógenas.
3. Ejecutar par fijo/adaptativo.
4. Medir tras calentamiento.
5. Agregar por escenario.
6. Remuestrear corridas.
7. Exportar json.
8. Decidir elegibilidad sin promover automáticamente.

### ALT_008 Alternativas y excepciones

Artefacto alterado: rechazo; criterio no superado: conservar fijo; sobresaturación: reportar colas pendientes; revisión humana no sustituida por CLI.

**Postcondición y criterio de aceptación:** 50 pares, 900 s de calentamiento, 7200 s de medición; mismas llegadas por par.

**Evidencia asociada:** `test_hash_tamper_and_unpromoted_refused, reports/experiment.json`. La existencia de una prueba no equivale a la aceptación humana del caso.

## CU_009 Supervisar y exportar

**Actor:** ACT_001. **Requisitos:** RF_012, RF_016.

**Disparador:** el actor solicita supervisar y exportar. **Precondiciones:** Sesión válida y dashboard disponible.

**Entradas:** datos del contrato OpenAPI o parámetros CLI del caso. **Resultado:** Monitor y exportación con datos sintéticos identificados.

### FLU_009 Flujo principal

1. Seleccionar cruce.
2. Actualizar cada 2 s.
3. Leer modo, colas y tiempos.
4. Revisar frescura.
5. Exportar json.
6. Distinguir solicitud pendiente de plan activo.

### ALT_009 Alternativas y excepciones

Más de 5 s sin heartbeat: colores desconocidos; token vencido: iniciar sesión; API ausente: mostrar dirección y tipo de error.

**Postcondición y criterio de aceptación:** Texto acompaña estados; nunca confirmar una fase sin telemetría.

**Evidencia asociada:** `test_login_dashboard_renders_without_backend, reports/smoke.json`. La existencia de una prueba no equivale a la aceptación humana del caso.

## CU_010 Consultar auditoría

**Actor:** ACT_001. **Requisitos:** RF_014.

**Disparador:** el actor solicita consultar auditoría. **Precondiciones:** Administrador autenticado.

**Entradas:** datos del contrato OpenAPI o parámetros CLI del caso. **Resultado:** Trazabilidad de decisiones y cambios.

### FLU_010 Flujo principal

1. Abrir auditoría.
2. Pedir página.
3. Mostrar actor, entidad, antes/después, motivo, instante y correlación.
4. Seguir referencia a plan.

### ALT_010 Alternativas y excepciones

Viewer: 403; API/BD caída: no mostrar éxito; no permitir editar/borrar desde rol runtime.

**Postcondición y criterio de aceptación:** No registrar contraseñas ni tokens.

**Evidencia asociada:** `test_permissions, reports/smoke.json`. La existencia de una prueba no equivale a la aceptación humana del caso.

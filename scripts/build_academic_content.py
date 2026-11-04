"""Memoria y anexos editables; conserva las evidencias originales y normaliza identificadores."""

from pathlib import Path
import json
import re

OUT = Path("entrega_academica")
SOURCE = Path("docs/FASE_1_Documento_Tecnico_Trafico_CDMX.md").read_text(encoding="utf-8")


def normalized(text):
    for family in ("RNF", "RF", "RT", "RB", "OE", "CU", "P", "R"):
        target = {"P": "PRU", "R": "RIE"}.get(family, family)
        text = re.sub(rf"\b{family}-(\d+)\b", lambda m: f"{target}_{int(m[1]):03d}", text)
    return text


def extract(start, end):
    return normalized(SOURCE[SOURCE.index(start) : SOURCE.index(end)].split("\n", 1)[1].strip())


def write(name, text):
    # Identificar todas las tablas y títulos sin alterar los IDs de requisitos.
    count = 0
    lines = []
    in_table = False
    for line in text.strip().splitlines():
        if line.startswith("|") and not in_table:
            count += 1
            lines.extend([f"**TAB_{Path(name).stem.upper()}_{count:03d}**", ""])
        in_table = line.startswith("|")
        lines.append(line)
    (OUT / name).write_text("\n".join(lines) + "\n", encoding="utf-8")


CASES = [
    (
        "Acceder",
        "ACT_001",
        "RF_001",
        "Credenciales y API disponibles",
        "Ingresar correo y contraseña; enviar formulario; verificar hash y usuario activo; emitir JWT; abrir monitor",
        "Credenciales inválidas: 401 sin sesión; API ausente: mensaje de conexión; token vencido: volver a entrar",
        "Sesión válida de una hora o rechazo explícito",
        "test_permissions, test_login_does_not_send_empty_bearer",
        "No hay credenciales en registros ni encabezado Bearer vacío",
    ),
    (
        "Gestionar catálogo",
        "ACT_001",
        "RF_002",
        "Administrador autenticado y BD disponible",
        "Consultar versión; enviar alta/edición; validar coordenadas/capacidad; crear grupos NS/EO/PEATON o editar; auditar y confirmar transacción",
        "Versión obsoleta: 409; valores inválidos: 422; fallo de BD: 503 sin éxito; catálogo referido se desactiva en vez de borrarse",
        "Catálogo y configuración versionados",
        "test_unknown_and_config_conflict, test_cuauhtemoc_catalog_is_idempotent_and_separate",
        "Solo administra cruces del estudio sintético; no acredita geocerca oficial",
    ),
    (
        "Registrar observaciones",
        "ACT_002",
        "RF_003, RF_004, RF_005",
        "Fuente identificada, grupo existente y lote de 1 a 1000 objetos",
        "Enviar ventanas de 60 s; validar estructura/unidades/UTC; identificar faltantes y retraso; deduplicar por fuente/grupo/ventana; guardar elementos válidos; auditar resultados",
        "Duplicado: no crear otra fila; negativo/futuro/ventana inválida: rechazo individual; Waze sin aforo: guardar ausente y no habilitar adaptación",
        "Resultados aceptado/duplicado/rechazado por elemento",
        "test_ingest_idempotent_mixed_batch, test_timezone_normalization_and_duplicate",
        "Cada observación aceptada conserva origen y ventana; no inventar conteos",
    ),
    (
        "Consultar tráfico",
        "ACT_001",
        "RF_006",
        "Usuario autenticado",
        "Elegir cruce/grupo; enviar rango temporal y paginación; consultar histórico; calcular antigüedad con reloj simulado; mostrar demanda y origen",
        "Fecha sin zona: 422; cruce desconocido: 404; falta de comunicación: estado desconocido",
        "Datos con unidad, fecha, fuente y calidad",
        "test_traffic_filters_and_dates",
        "Una fila histórica no se presenta como observación vigente",
    ),
    (
        "Obtener pronóstico y propuesta",
        "ACT_001",
        "RF_007, RF_008",
        "Cruce activo, versión previa y observaciones registradas",
        "Solicitar propuesta; verificar versión; construir atributos de cinco ventanas; consultar IA con timeout; calcular verdes/restricciones; persistir modelo/predicciones/plan; devolver PROPOSED",
        "Versión obsoleta: 409; IA o datos inválidos: 40/40 con modo degradado y causa; BD caída: 503",
        "Propuesta persistida y sin cambio de color",
        "test_prediction_is_persisted_proposal_not_application, test_real_pipeline_through_internal_service_and_api",
        "Demanda 30/10 desde 40/40 produce 45/35, rojo 72/82",
    ),
    (
        "Aplicar plan semafórico",
        "ACT_001",
        "RF_008, RF_009, RF_011",
        "Plan PROPOSED, trabajador vigente y versión esperada",
        "Solicitar aplicación al siguiente ciclo; reservar versión atómicamente; marcar PENDING; al límite volver a validar prioridad/datos; sustituir activo y confirmar aplicado_en; publicar estado",
        "Doble reserva o ciclo obsoleto: 409; trabajador vencido: 503; falla fuente/IA: prevalece fijo; caída BD: control local sin aceptar cambios humanos",
        "Un único plan activo confirmado, con fase peatonal",
        "test_queue_is_deferred_and_rejects_stale_version, test_apply_only_at_boundary_and_automatic_slew",
        "Nunca aplicar a mitad de fase; la propuesta no implica aplicación",
    ),
    (
        "Intervenir y retornar al automático",
        "ACT_001",
        "RF_010, RF_011",
        "Administrador, motivo, versión y duración de 1 a 10 ciclos",
        "Introducir verdes complementarios; validar invariantes; reservar para siguiente ciclo; confirmar; respetar vigencia; caducar o solicitar retorno automático; auditar",
        "Verdes incompatibles o 11 ciclos: 422; versión antigua: 409; fuente/IA ausente: fallback tiene precedencia; no omitir peatones",
        "Intervención temporal y retorno controlado",
        "test_manual_invariants_and_expiry, test_manual_expiry_and_fallback_precedence",
        "Motivo obligatorio, suma 80 y ningún ciclo sin peatones",
    ),
    (
        "Comparar estrategias",
        "ACT_003",
        "RF_013, RF_015, RF_016",
        "Candidato y manifiesto propios; protocolo y semillas fijados",
        "Verificar hash; generar llegadas exógenas; ejecutar par fijo/adaptativo; medir tras calentamiento; agregar por escenario; remuestrear corridas; exportar JSON; decidir elegibilidad sin promover automáticamente",
        "Artefacto alterado: rechazo; criterio no superado: conservar fijo; sobresaturación: reportar colas pendientes; revisión humana no sustituida por CLI",
        "Informe reproducible con resultados positivos o negativos",
        "test_hash_tamper_and_unpromoted_refused, reports/experiment.json",
        "50 pares, 900 s de calentamiento, 7200 s de medición; mismas llegadas por par",
    ),
    (
        "Supervisar y exportar",
        "ACT_001",
        "RF_012, RF_016",
        "Sesión válida y dashboard disponible",
        "Seleccionar cruce; actualizar cada 2 s; leer modo, colas y tiempos; revisar frescura; exportar JSON; distinguir solicitud pendiente de plan activo",
        "Más de 5 s sin heartbeat: colores desconocidos; token vencido: iniciar sesión; API ausente: mostrar dirección y tipo de error",
        "Monitor y exportación con datos sintéticos identificados",
        "test_login_dashboard_renders_without_backend, reports/smoke.json",
        "Texto acompaña estados; nunca confirmar una fase sin telemetría",
    ),
    (
        "Consultar auditoría",
        "ACT_001",
        "RF_014",
        "Administrador autenticado",
        "Abrir auditoría; pedir página; mostrar actor, entidad, antes/después, motivo, instante y correlación; seguir referencia a plan",
        "Viewer: 403; API/BD caída: no mostrar éxito; no permitir editar/borrar desde rol runtime",
        "Trazabilidad de decisiones y cambios",
        "test_permissions, reports/smoke.json",
        "No registrar contraseñas ni tokens",
    ),
]


def cases_document():
    parts = [
        "# DOC_002 Especificación de casos de uso\n\nVersión 1.0 · Cuauhtémoc · 1 de noviembre de 2026.\n\nTodos los casos operan sobre semáforos simulados. ACT_001: administrador; ACT_002: proveedor de datos; ACT_003: evaluador académico que ejecuta herramientas de evaluación. El trabajador y la IA son componentes internos, no actores de interfaz.\n"
    ]
    for i, (title, actor, req, pre, steps, exceptions, post, evidence, acceptance) in enumerate(
        CASES, 1
    ):
        parts.append(
            f"## CU_{i:03d} {title}\n\n**Actor:** {actor}. **Requisitos:** {req}.\n\n**Disparador:** el actor solicita {title.lower()}. **Precondiciones:** {pre}.\n\n**Entradas:** datos del contrato OpenAPI o parámetros CLI del caso. **Resultado:** {post}.\n\n### FLU_{i:03d} Flujo principal\n"
        )
        parts.extend(
            f"{n}. {step.strip().capitalize()}." for n, step in enumerate(steps.split(";"), 1)
        )
        parts.append(
            f"\n### ALT_{i:03d} Alternativas y excepciones\n\n{exceptions}.\n\n**Postcondición y criterio de aceptación:** {acceptance}.\n\n**Evidencia asociada:** `{evidence}`. La existencia de una prueba no equivale a la aceptación humana del caso.\n"
        )
    return "\n".join(parts)


def main():
    OUT.mkdir(exist_ok=True)
    (OUT / "figuras").mkdir(exist_ok=True)
    model = json.loads(Path("reports/model_evaluation.json").read_text())
    exp = json.loads(Path("reports/experiment.json").read_text())
    memo = """# DOC_001 Memoria técnica del sistema de semáforos simulados de Cuauhtémoc

Versión 1.0 · 1 de noviembre de 2026 · ENT_001. Proyecto académico para cuatro integrantes.

Esta memoria reúne descripción, fundamentos, análisis, diseño, desarrollo y verificación de un
prototipo que adapta semáforos **simulados** a la demanda vehicular pronosticada. El alcance es
ALC_001 Cuauhtémoc, con CUA_001 a CUA_005 sintéticos, sin aforos ni controladores físicos.
Los documentos DOC_002 a DOC_005 y figuras FIG_001 a FIG_006 forman parte de esta memoria.
La entrega documental está preparada; la aceptación por docente y evaluadores no se presume.
No se afirma certificación ISO. Los resultados de la línea base se identifican como sintéticos.

## IDX_001 Índice y numeración

Capítulo 2 Descripción general; capítulo 3 Marco teórico; capítulo 4 Análisis y diseño;
capítulo 5 Modelado; capítulo 6 Desarrollo; capítulo 7 Pruebas; anexos A a D.
Se corrigió la repetición de capítulo 5 de la lista recibida. Si una plantilla institucional exige
otra numeración, conservar los identificadores estables y cambiar solo los números de capítulo.

## CAP_002 Descripción general del proyecto

### DES_001 Descripción del sistema

Un plan fijo distribuye verde sin observar cambios de demanda. El prototipo estudia si anticipar
llegadas y repartir el verde de manera restringida reduce demora frente al mismo plan fijo.
Un generador emite observaciones por grupo y minuto; PostgreSQL conserva histórico; un modelo
pronostica cinco minutos; el controlador valida y el trabajador aplica al siguiente ciclo.
Streamlit permite consultar demanda, cola, colores, tiempos, alertas e intervenciones temporales.
La IA pronostica, no autoriza movimientos. La política no es una optimización matemática demostrada.
Las colas son resultado del simulador y no un campo recibido de Waze.

### OG_001 Objetivo general

Desarrollar y verificar un prototipo reproducible de gestión adaptativa de semáforos simulados
para un escenario académico de Cuauhtémoc, utilizando pronóstico de llegadas y una política
restringida, y comparar su desempeño con un plan fijo mediante experimentos pareados.

### OBJ_001 Objetivos específicos

| ID | Objetivo | Evidencia de verificación |
|---|---|---|
| OE_001 | Representar cinco cruces NS/EO y peatones | Catálogo CUA_001..005 y prueba de inicialización |
| OE_002 | Generar llegadas reproducibles con clima y estacionalidad | Dataset, semilla y hash |
| OE_003 | Predecir promedio de llegadas de los próximos cinco minutos | MAE/RMSE temporal frente a persistencia |
| OE_004 | Aplicar ciclos válidos sin movimientos incompatibles | Propiedades y triggers PostgreSQL |
| OE_005 | Comparar demora/colas con plan fijo | Informe de 50 pares e intervalos por corrida |
| OE_006 | Supervisar y permitir intervención temporal | Dashboard y CU_007/CU_009 |
| OE_007 | Vincular requisitos, decisiones y pruebas | Matriz de trazabilidad y auditoría |

### ALC_001 Alcance y exclusiones

Cinco cruces independientes del escenario Cuauhtémoc, sin giros ni propagación entre cruces.
Las coordenadas son referencias esquemáticas: no son un inventario municipal ni una geocerca.
Se incluyen fuente sintética, API, IA, BD, control/simulación y dashboard. Se excluyen hardware,
cámaras, placas, prioridad de emergencias y coordinación de corredores. Una integración Waze
efectiva requiere autorización; el puerto entregado conserva ausentes los conteos/clima que el
feed no proporciona. Su ubicación central se usa como contexto del estudio, no como prueba
de representatividad de la demanda [REF_010].

### MET_001 Metodología y realización por etapa

Scrum organiza incrementos; CRISP-DM estructura el trabajo de datos. El backlog liga requisitos
y pruebas; el equipo planea por capacidad, inspecciona incrementos y ajusta prioridades. Se
planifican cinco sprints de dos semanas. No se inventan reuniones, asistencia ni actas históricas.
El líder mantiene prioridades, QA facilita seguimiento y los cuatro desarrollan/revisan [REF_002].

| ID | Etapa CRISP-DM | Realización y artefacto |
|---|---|---|
| MET_002 | Comprensión del problema | OG_001, objetivos, hipótesis, alcance y comparación fija |
| MET_003 | Comprensión de datos | Unidades veh/min, calidad, estacionalidad y límites sintéticos |
| MET_004 | Preparación | Ventanas, atributos históricos, cortes temporales y purga |
| MET_005 | Modelado | Pipeline de imputación y Random Forest, dos profundidades y CV expansiva |
| MET_006 | Evaluación | Persistencia, MAE/RMSE y experimentos pareados; resultados negativos conservados |
| MET_007 | Despliegue | Manifiesto/hash, promoción revisada, servicio IA, fallback y reversión |

| ID | Sprint planificado | Elementos y evidencia realizable |
|---|---|---|
| SPR_001 | Días 1–10 | Alcance, requisitos, riesgos y primeras observaciones |
| SPR_002 | Días 11–20 | Esquema, ingesta, referencia predictiva y contrato de dashboard |
| SPR_003 | Días 21–30 | API, control, entrenamiento e integración |
| SPR_004 | Días 31–40 | Fallas, pruebas, experimento y revisión de métricas |
| SPR_005 | Días 41–50 | Aceptación, manuales, transferencia; reserva días 46–50 |

Definición de terminado MET_008: revisión por otro integrante, pruebas pertinentes, documentación
y matriz actualizadas, sin defectos críticos abiertos. Autenticación, controlador y evaluación
requieren revisión cruzada. La generación de estos artefactos no acredita por sí sola esa revisión.

### NEG_001 Terminología del negocio

| ID | Palabra | Significado dentro del sistema |
|---|---|---|
| TER_001 | Intersección | Cruce sintético con dos grupos vehiculares y una fase peatonal |
| TER_002 | Grupo | Movimientos compatibles NS, EO o peatones |
| TER_003 | Demanda | Vehículos que llegan por minuto, distintos de los que salen |
| TER_004 | Cola | Vehículos acumulados pendientes de servicio |
| TER_005 | Ciclo | Secuencia completa de fases de 120 segundos |
| TER_006 | Fase | Intervalo que autoriza un grupo compatible |
| TER_007 | Despeje | Intervalo sin autorización conflictiva antes de otra fase |
| TER_008 | Reparto de verde | Distribución de 80 segundos entre NS y EO |
| TER_009 | Pronóstico | Estimación del promedio de llegadas de los próximos cinco minutos |
| TER_010 | Plan fijo | Referencia vehicular 40/40, con peatones y transiciones |
| TER_011 | Plan adaptativo | Reparto calculado con pronóstico y restricciones |
| TER_012 | Degradado | Continuidad mediante plan fijo por datos o IA no disponibles |
| TER_013 | Intervención | Plan manual validado, con motivo y caducidad |
| TER_014 | Ventana | Observación completa de 60 segundos |
| TER_015 | Propuesta | Plan persistido aún no solicitado/aplicado |
| TER_016 | Pendiente | Aplicación reservada para un límite futuro de ciclo |
| TER_017 | Activo | Plan cuya aplicación fue confirmada por el trabajador |
| TER_018 | Trazabilidad | Vínculo de entrada, modelo, decisión, actor y prueba |
| TER_019 | Fuente sintética | Datos generados por algoritmo y semilla, sin medición vial |
| TER_020 | Waze | Fuente externa opcional autorizada; no equivale a aforo por acceso |

## CAP_003 Marco teórico

### TEOR_001 Flujo y capacidad vehicular

El flujo es una tasa de llegadas; la cola acumula demanda no atendida y la capacidad expresa
servicio posible. La distribución de verde afecta la oportunidad de descargar esa cola. Un
análisis vial real depende de geometría, movimientos, peatones y saturación; no basta conocer
el número total de vehículos. FHWA distingue estos conceptos en su manual histórico de
temporización; se usa como antecedente técnico, no como norma vigente de CDMX [REF_003].

En este modelo didáctico, cola siguiente = cola actual + llegadas − salidas. Las salidas son
enteras y no superan vehículos disponibles ni capacidad durante verde. Con tasa 0.5 veh/s y
40 s de verde hay hasta 20 oportunidades de servicio por ciclo. Con ciclo 120 s eso equivale
a 10 veh/min de capacidad media idealizada por grupo, sin representar una calibración de calle.
Demanda superior a capacidad hace crecer la cola: alargar un verde no crea capacidad infinita.

### TEOR_002 Control fijo y adaptativo

El control fijo mantiene repartos; el adaptativo responde a información de demanda. Aquí se
conserva el ciclo y se modifica únicamente su reparto vehicular. Una máquina de estados
codifica exclusión: NS verde/amarillo/despeje, EO verde/amarillo/despeje, peatones y despeje.
Verde NS + verde EO = 80; cada uno entre 20 y 60; peatones 20 y transiciones 20 adicionales.
Rojo vehicular = 120 − verde − 3. Son restricciones académicas de este simulador, no parámetros
reglamentarios. La aplicación al límite de ciclo separa cálculo de autorización efectiva.

### TEOR_003 Aprendizaje supervisado y regresión

Una observación de entrenamiento relaciona atributos conocidos X con una etiqueta futura y.
La regresión estima una cantidad continua. En este proyecto X contiene hora cíclica, día,
clima conocido, última demanda, media de cinco ventanas, velocidad y grupo; y es la media de
las cinco ventanas siguientes. Predecir colores sería otro problema y no es la formulación usada.
No se utilizan atributos futuros ni se deduce una cuenta vehicular a partir de velocidad.

### TEOR_004 Árboles y Random Forest

Un árbol divide el espacio de atributos mediante reglas y predice un valor por región. Random
Forest combina árboles entrenados con variación de muestras y atributos; en regresión agrega
sus predicciones. La diversidad reduce la sensibilidad frente a un solo árbol, pero no elimina
sesgo de datos o extrapolación. Profundidad, número de árboles y mínimo de muestras por hoja
controlan capacidad/costo. El pipeline conserva la transformación de entrenamiento para inferir
con el mismo contrato [REF_004]. La elección frente a Deep Learning responde a datos tabulares,
CPU y alcance de cuatro personas; no se afirma superioridad universal.

### TEOR_005 Dependencia temporal y fuga de información

Filas próximas comparten contexto. Separarlas al azar permite evaluar con información demasiado
cercana a entrenamiento. Se reservan días futuros comunes a todos los grupos y se purgan
etiquetas que crucen fronteras. La imputación se ajusta solo con entrenamiento. Son medidas
de aislamiento del experimento; validación final no debe reutilizarse indefinidamente para ajustar
el candidato [REF_005]. Persistencia predice con la media de las últimas cinco ventanas y
constituye una referencia explícita que la IA debe superar.

### TEOR_006 Métricas y experimento pareado

MAE = media de |y − predicción|; RMSE = raíz de la media del error cuadrático. Ambas se
expresan en veh/min; RMSE penaliza más errores grandes. La precisión del pronóstico no prueba
que un controlador reduzca demora. La evaluación de control integra colas en veh·s, cuenta
salidas y pendientes, y compara políticas bajo las mismas llegadas. Las semillas se fijan antes
del experimento. El intervalo bootstrap remuestrea corridas pareadas dentro de cada escenario,
no segundos autocorrelacionados. La inferencia solo describe las condiciones sintéticas ensayadas.

### TEOR_007 Ingeniería de software y persistencia

Los requisitos definen comportamiento verificable; los casos de uso describen interacciones;
los modelos de datos y arquitectura asignan responsabilidades. Transacciones, FK, unicidad y
versiones evitan estados contradictorios. Un índice parcial expresa un solo plan activo por cruce;
un trigger diferido valida el conjunto de fases al confirmar. El rol runtime no modifica auditoría.
Los hashes detectan alteraciones de artefactos, pero no autentican al autor si el directorio es
malicioso. Joblib solo debe cargar modelos propios y confiables [REF_006].

## CAP_004 Análisis y diseño

### ACTORES_001 Actores e interesados

| ID | Actor o interesado | Relación con el sistema |
|---|---|---|
| ACT_001 | Administrador | Consulta, configura, interviene y revisa auditoría |
| ACT_002 | Proveedor de observaciones | Generador o adaptador externo autorizado; registra lotes |
| ACT_003 | Evaluador académico | Ejecuta evaluación y revisa reportes exportados |
| INT_001 | Conductores simulados | Generan demanda; no usan interfaz |
| INT_002 | Peatones simulados | Requieren fase exclusiva; no usan interfaz |
| INT_003 | Docente | Acepta entrega y limitaciones; no se atribuye aprobación automática |

El servicio IA, la BD y el trabajador están dentro del sistema. Los cuatro desarrolladores son
responsables del proyecto, no cuatro actores adicionales de interfaz. Proveedor sintético y Waze
son alternativas del mismo puerto; Waze efectivo permanece fuera del MVP sin autorización.

### REQ_001 Requerimientos funcionales

{functional}

### REQ_002 Requerimientos no funcionales

{nonfunctional}

### REQ_003 Requerimientos técnicos

{technical}

### NEG_002 Reglas de negocio

{rules}

### CAL_001 Calendarización Gantt y PERT

FIG_001 es el Gantt relativo a días hábiles, no fechas prometidas. FIG_002 es la red PERT
con actividades ACTIV_001 a ACTIV_015, alias A..O. TE=(To+4Tn+Tp)/6 y varianza=((Tp−To)/6)^2.
El recorrido temprano usa el mayor fin de predecesoras; el tardío el menor inicio de sucesoras.
Holgura=LS−ES. Ruta crítica A–B–C–E–H–J–K–L–N–O, duración 45 días hábiles, varianza
2.7778 días² y reserva de cinco días. No dividir el calendario entre cuatro personas.
La red no sustituye nivelación de recursos ni registra ejecución de ceremonias.

![FIG_001 Gantt relativo](figuras/FIG_001_gantt.png)

![FIG_002 Red PERT](figuras/FIG_002_pert.png)

{pert}

### FACT_001 Factibilidad técnica

{feasibility_tech}

### FACT_002 Factibilidad operativa

{feasibility_ops}

### FACT_003 Factibilidad económica

{feasibility_cost}

### RIESGOS_001 Análisis de riesgo

{risks}

CAM_001 agrega riesgo RIE_009: interpretar el nuevo nombre como calibración real de Cuauhtémoc
(P=4, I=4, nivel=16). Tratamiento: catálogo explícitamente sintético, BD nueva separada y
resultados históricos identificados. Responsable IA+QA; revisión antes de aceptación. No se
asigna pérdida monetaria inventada; recalcular exposición con el equipo si cambia el alcance.

### NOR_001 Normas y obligaciones de evidencia

ISO/IEC/IEEE 12207:2026 es el referente de ciclo de vida; admite aplicación iterativa y no
impone Scrum. Esta adaptación identifica procesos y evidencias, sin afirmar conformidad formal
por cláusula ni certificación. Una auditoría formal exige texto autorizado y evaluación competente
[REF_001]. ISO/IEC 23894, 42001 y 5338 son referentes complementarios para riesgo/gobierno/
ciclo de IA ya propuestos en Fase 1; no se presume certificación a ninguna de ellas.

| ID | Proceso adaptado | Evidencia | Cierre |
|---|---|---|---|
| NOR_002 | Requisitos y arquitectura | OG/OE/RF/RNF/RT/RB, CU y figuras | Revisión cruzada |
| NOR_003 | Planificación y riesgo | Gantt, PERT, capacidad y RIE | Revisión por sprint |
| NOR_004 | Implementación e integración | Código, SQL, contratos y Compose | Pruebas y revisión |
| NOR_005 | Configuración | Versiones, semillas, hashes y migración | Integridad verificable |
| NOR_006 | Verificación | JUnit, cobertura, carga y experimento | Resultado reproducible |
| NOR_007 | Validación | Guiones Alpha/Beta y acta sin prefirmar | Evaluadores reales |
| NOR_008 | Operación y retiro | Manual, respaldo/reversión y cierre | Ejercicio registrado |

## CAP_005 Modelado de casos de uso

### MOD_001 Diagrama de casos de uso

FIG_003 representa el límite del sistema, actores externos y diez casos. Las flechas include
se limitan a relaciones obligatorias: ajustar requiere propuesta/validación; no se interpreta
que consultar el monitor aplique un plan. DOC_002 especifica entradas, precondiciones, flujo,
alternativas, postcondiciones, criterios y evidencia de los diez CU.

![FIG_003 Casos de uso](figuras/FIG_003_casos_uso.png)

### MOD_002 Diagrama entidad relación

FIG_004 identifica entidades ENTBD_001..014, PK/FK y cardinalidades. El esquema SQL es la
autoridad ejecutable; no se introduce otro historial duplicado. Detalles y plan_prediccion son
relaciones asociativas. Las tablas técnicas schema_versions/control_worker soportan migración
y exclusión del trabajador. No hay actuadores físicos representados en la BD.

![FIG_004 Modelo entidad relación](figuras/FIG_004_bd.png)

### MOD_003 Arquitectura y despliegue

FIG_005 muestra las responsabilidades y FIG_006 los procesos desplegables. El dashboard solo
consume API; IA no aplica fases; trabajador independiente aplica planes y conserva colas. El
backend verifica permisos/versiones y persiste auditoría. PostgreSQL es principal, SQLite
auxiliar local. REST/JSON permite sustituir fuente/modelo conservando contratos.

![FIG_005 Arquitectura](figuras/FIG_005_arquitectura.png)

![FIG_006 Despliegue](figuras/FIG_006_despliegue.png)

## CAP_006 Desarrollo del sistema

### DEV_001 Componentes implementados

| ID | Componente | Código | Comportamiento |
|---|---|---|---|
| COMP_001 | Backend | backend/app/main.py | JWT, catálogo, ingesta, consulta, propuestas y auditoría |
| COMP_002 | Controlador | backend/app/controller.py | Reparto proporcional, límites y secuencia |
| COMP_003 | Simulador | backend/worker.py | Reloj, fuente, aplicación al ciclo y fallback |
| COMP_004 | Colas | backend/app/simulation.py | Conservación y esperas por política |
| COMP_005 | IA | ml_model/ | Generación, entrenamiento, servicio, evaluación y registro |
| COMP_006 | Interfaz | frontend/dashboard.py | Monitor, tabla de tiempos, gráfico e intervención |
| COMP_007 | BD | database/ | Migración, restricciones, catálogo y rol runtime |
| COMP_008 | Operación | scripts/, compose.yaml | Inicio, carga, respaldo y evidencia |

### DEV_002 Flujo de implementación

El backend recibe ventanas canónicas y rechaza datos negativos, futuros o sin zona. Una
restricción única impide duplicados. Construye atributos de cinco ventanas consecutivas, llama
IA con timeout 2 s y guarda una propuesta. La solicitud de aplicación reserva versión y estado
PENDING. El trabajador valida prioridad al siguiente ciclo, sustituye el activo en transacción
y publica aplicado_en. Se conservan referencias a observaciones, modelo y correlación.

El plan fijo es 40/40. Si d_NS=30 y d_EO=10 desde 40/40, la política objetivo 60/20 se limita
a 45/35 por ciclo. La intervención manual dura hasta diez ciclos y no altera peatones ni
despejes. Ante BD caída continúa un estado local no confirmado y buffer acotado; recuperar
reconcilia registros y audita. Reiniciar proceso comienza con diez segundos de despeje.

### DEV_003 Entrenamiento y configuración

90 días sintéticos, semilla 42, partición 54/18/18 días, purga de cinco minutos y hasta
300000 filas de entrenamiento por bloques. El pipeline aplica imputación y Random Forest.
Se comparan profundidades dentro de entrenamiento; prueba final no participa en ajuste.
El artefacto se carga solo si hash, atributos, versión de scikit-learn y estado corresponden.
La promoción requiere criterios predictivo/control y revisión real de personas distintas.
Encontrar un manifiesto promoted local no acredita esa revisión ni funcionamiento actual del servicio.

### DEV_004 Instalación y uso

DOC_003 contiene instalación local y PostgreSQL, acceso, operación por tarea, capturas, errores,
respaldo, reversión y retiro. `.env` guarda secretos y no entra en Git. `scripts.select_cuauhtemoc`
prepara un escenario nuevo conservando el histórico anterior. Compose entrega procesos separados;
la ausencia de Docker en el entorno de autoría impide afirmar que su ejecución fue probada.

## CAP_007 Pruebas

### VER_001 Plan y procedimientos

DOC_004 identifica PRU_001..013, nivel/tipo, responsable, entrada, pasos, resultado esperado,
evidencia y criterio de salida. Sus guiones separan ejecución automatizada de evaluación humana.
Las suites están en tests/ y la CI usa PostgreSQL aislado. Los ensayos actuales y los históricos
se identifican por archivo y fecha; no se suman como si fueran una única ejecución.

### VER_002 Resultados disponibles

Modelo de referencia: {model_version}. MAE de prueba {mae:.4f} veh/min frente a persistencia
{baseline:.4f}. Experimento: 50 pares con reducción media no sobresaturada {reduction:.2%},
IC95% [{low:.2%}, {high:.2%}]. Valle y pico muestran empeoramientos pequeños; el beneficio
agregado se concentra en desbalance y lluvia/incidente. No hay mejora uniforme ni evidencia vial real.
Estos resultados pertenecen al experimento sintético de referencia previo a calibración territorial.

El anexo de resultados DOC_005 lee JUnit/cobertura, carga 5/50 y restauración si los reportes
existen; un criterio fallido se conserva como resultado negativo. La cobertura no mide utilidad
vial. La aceptación Alpha/Beta requiere cinco evaluadores reales y queda abierta hasta obtenerla.

## ANX_A Glosario técnico

| ID | Término | Definición |
|---|---|---|
| GLO_001 | API | Contrato HTTP/JSON entre componentes |
| GLO_002 | FastAPI | Framework de API Python y contrato OpenAPI |
| GLO_003 | PostgreSQL | Motor relacional principal |
| GLO_004 | ORM | Mapeo de entidades Python a relaciones SQL |
| GLO_005 | JWT | Token firmado con expiración y audiencia |
| GLO_006 | Hash | Resumen para detectar cambios de datos/artefactos |
| GLO_007 | Pipeline | Transformaciones y predictor persistidos juntos |
| GLO_008 | MAE | Error absoluto medio, veh/min |
| GLO_009 | RMSE | Raíz del error cuadrático medio, veh/min |
| GLO_010 | Fuga temporal | Uso indebido de información futura al evaluar |
| GLO_011 | Bootstrap | Remuestreo de corridas para estimar incertidumbre |
| GLO_012 | PERT | Estimación de tres puntos y red de dependencias |
| GLO_013 | Gantt | Barras de actividades sobre calendario relativo |
| GLO_014 | RPO | Antigüedad máxima tolerable de datos perdidos |
| GLO_015 | RTO | Tiempo objetivo de recuperación operativa |
| GLO_016 | Lease | Arrendamiento para un único trabajador |
| GLO_017 | Idempotencia | Repetir una entrada no duplica su efecto |
| GLO_018 | IC95 | Intervalo condicionado al protocolo de remuestreo |

## ANX_B Referencias

Consulta: 1 de noviembre de 2026. Las fuentes sustentan conceptos; los parámetros de control,
estimaciones y experimentos son decisiones propias. Fase 1 conserva además sus referencias R1..R12.

| ID | Fuente primaria | Uso |
|---|---|---|
| REF_001 | [ISO/IEC/IEEE 12207:2026](https://www.iso.org/standard/90219.html) | Marco del ciclo de vida; consulta pública |
| REF_002 | [Scrum Guide 2020](https://scrumguides.org/scrum-guide.html) | Responsabilidades e incrementos |
| REF_003 | [FHWA Traffic Signal Timing Manual, capítulo 3](https://ops.fhwa.dot.gov/publications/fhwahop08024/chapter3.htm) | Antecedente histórico de flujo/capacidad; publicación archivada |
| REF_004 | [scikit-learn, ensembles](https://scikit-learn.org/stable/modules/ensemble.html) | Árboles y bosques aleatorios |
| REF_005 | [scikit-learn, common pitfalls](https://scikit-learn.org/stable/common_pitfalls.html) | Aislamiento del pipeline y prevención de fuga |
| REF_006 | [scikit-learn, model persistence](https://scikit-learn.org/stable/model_persistence.html) | Persistencia y límites de carga |
| REF_007 | [Waze Data Feed specifications](https://support.google.com/waze/partners/answer/13458165?hl=en) | Acceso autorizado y ausencia de aforos garantizados |
| REF_008 | [FastAPI testing](https://fastapi.tiangolo.com/tutorial/testing/) | TestClient y pytest |
| REF_009 | [IBM CRISP-DM](https://www.ibm.com/docs/en/SS3RA7_18.5.0/pdf/ModelerCRISPDM.pdf) | Etapas del trabajo analítico |
| REF_010 | [Alcaldía Cuauhtémoc](https://cuauhtemoc.cdmx.gob.mx/inicio/conocenos/) | Contexto territorial; no calibra el modelo |

## ANX_C Identificadores y equivalencias

RF-01 ↔ RF_001; RNF-01 ↔ RNF_001; RT-01 ↔ RT_001; RB-01 ↔ RB_001;
CU-01 ↔ CU_001; OE-01 ↔ OE_001; P-01 ↔ PRU_001; R-01 ↔ RIE_001.
La regla se aplica a todos los números de cada familia. OG_001 es el objetivo general;
ACT_001..003 son actores; INT_001..003 interesados; TER/GLO son términos; REF fuentes;
DOC documentos; FIG figuras; TAB tablas; ENT entregables; COMP componentes.
ACTIV_001..015 corresponden por orden a A..O en PERT y se conservan en el código histórico.
Los IDs de base de datos son claves técnicas y no sustituyen identificadores de requisitos.

## ANX_D Relación de entregables

| ID | Artefacto | Contenido |
|---|---|---|
| ENT_001 | DOC_001 Memoria | Capítulos 2 a 7, glosario, referencias e IDs |
| ENT_002 | DOC_002 Casos de uso | Diez especificaciones completas |
| ENT_003 | DOC_003 Manual | Instalación, usuario, errores, recuperación |
| ENT_004 | DOC_004 Pruebas | Tipos, guiones y criterios |
| ENT_005 | DOC_005 Resultados | Evidencias y límites de aceptación |
| ENT_006 | PRE_001 Presentación | Diapositivas editables y notas |
| ENT_007 | VID_001 Video | Presentación audiovisual con títulos y demostración sintética |
| ENT_008 | Código del repositorio | Implementación reproducible y pruebas |

El cierre académico requiere revisión del docente y del equipo. La autoría de esta documentación
no constituye un acta de aceptación ni una validación municipal.
"""
    replacements = {
        "functional": extract("### 2.2.", "### 2.3."),
        "nonfunctional": extract("### 2.3.", "### 2.4."),
        "technical": extract("### 2.4.", "### 2.5."),
        "rules": extract("### 2.5.", "### 2.6."),
        "pert": extract("### 2.7.", "### 2.8."),
        "feasibility_tech": extract("#### 2.8.1.", "#### 2.8.2."),
        "feasibility_ops": extract("#### 2.8.2.", "#### 2.8.3."),
        "feasibility_cost": extract("#### 2.8.3.", "### 2.9."),
        "risks": extract("### 2.9.", "### 2.10."),
        "model_version": model["version"],
        "mae": model["metrics"]["test"]["model"]["mae"],
        "baseline": model["metrics"]["test"]["persistence"]["mae"],
        "reduction": exp["mean_delay_reduction"],
        "low": exp["ci95"][0],
        "high": exp["ci95"][1],
    }
    # format_map solo sobre la plantilla, antes de insertar fórmulas LaTeX de la fuente.
    write("DOC_001_Memoria.md", memo.format_map(replacements))
    write("DOC_002_Casos_de_uso.md", cases_document())


if __name__ == "__main__":
    main()

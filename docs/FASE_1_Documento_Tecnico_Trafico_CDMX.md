# Sistema inteligente de gestión de tráfico vehicular para la CDMX

## FASE 1. Documento técnico del proyecto

| Control documental | Valor |
|---|---|
| Identificador | SGT-CDMX-DTP-001 |
| Versión | 1.0 — propuesta de línea base académica |
| Fecha | 31 de octubre de 2026 |
| Naturaleza | Proyecto académico de ingeniería de software e inteligencia artificial |
| Entrega actual | Especificación, análisis, diseño, estimaciones y plan de verificación |
| Alcance de operación | Intersecciones y semáforos exclusivamente simulados |
| Equipo | Cuatro integrantes: Líder/Backend, Frontend, IA/Data Science y QA/Soporte |
| Entrega posterior | Fase 2: implementación; no se incluye código en este documento |

**Resumen ejecutivo.** Se propone desarrollar un prototipo que genere o ingiera observaciones de tráfico, pronostique la demanda vehicular y adapte los tiempos de verde mediante una política con restricciones explícitas. Un simulador permitirá comparar el control adaptativo con un plan fijo bajo las mismas llegadas de vehículos. El administrador podrá supervisar los resultados, configurar límites, intervenir y revisar la auditoría.

La planificación comprende **10 semanas, 1,280 horas-persona y un presupuesto de referencia de $331,080 MXN**, incluidas reservas. La ruta crítica calculada con las duraciones esperadas PERT es de **45 días hábiles**; se añaden cinco días de reserva de calendario. Todas las cantidades económicas son hipótesis de planeación, no cotizaciones. Los beneficios de movilidad son objetivos experimentales, todavía sin resultados de implementación.

## 1. Descripción general del proyecto

### 1.1. Problema y descripción del sistema

Una programación semafórica fija puede distribuir el tiempo de verde de manera poco conveniente cuando cambia la demanda entre accesos. El problema académico consiste en determinar si un pronóstico de demanda, combinado con una política de asignación restringida, mejora el desempeño frente a un plan fijo comparable.

El sistema tendrá cinco funciones principales: adquisición de observaciones, almacenamiento histórico, pronóstico, asignación de tiempos y visualización. Los cambios se ejecutarán únicamente en el simulador, mediante una máquina de estados que impida fases incompatibles.

**Distinción de diseño:** el modelo de ML pronostica llegadas; el controlador calcula y valida el plan semafórico. Un pronóstico preciso no demuestra por sí solo que el controlador reduzca las demoras. Ambos componentes tendrán evaluaciones independientes.

### 1.2. Objetivo general

Diseñar y especificar un sistema académico reproducible que utilice aprendizaje automático para anticipar la demanda vehicular y ajustar semáforos simulados, evaluando su desempeño, resiliencia y trazabilidad en un conjunto acotado de intersecciones representativas de escenarios urbanos de la CDMX.

### 1.3. Objetivos específicos

| ID | Objetivo | Indicador o evidencia prevista |
|---|---|---|
| OE-01 | Representar cinco intersecciones sintéticas con dos grupos vehiculares y una fase peatonal exclusiva | Catálogo y simulaciones reproducibles |
| OE-02 | Producir observaciones de tráfico con temporalidad, clima, incidentes y ruido | Dataset versionado, diccionario y reporte de calidad |
| OE-03 | Pronosticar el promedio de llegadas de los próximos cinco minutos | MAE y RMSE sobre periodos futuros reservados |
| OE-04 | Asignar tiempos sin infringir las restricciones del simulador | Cero violaciones en toda la batería de pruebas |
| OE-05 | Comparar el controlador adaptativo con el plan fijo | Informe de experimentos pareados y sus intervalos de confianza |
| OE-06 | Facilitar supervisión e intervención del administrador | Dashboard, control de acceso y registro de cambios |
| OE-07 | Mantener trazabilidad desde los requisitos hasta las pruebas | Matriz actualizada y evidencias de aceptación |

### 1.4. Alcance y supuestos

| Elemento | Definición de alcance |
|---|---|
| Geografía | Contexto de CDMX; identificadores y configuraciones sintéticos, sin afirmar calibración con aforos oficiales |
| Red inicial | Cinco cruces independientes; no se modela propagación entre cruces ni coordinación de corredores |
| Movimientos | Grupos norte-sur y este-oeste, sin giros, más fase peatonal exclusiva |
| Datos principales | Generador propio; operación local sin credenciales de servicios externos |
| Waze | Puerto de integración y contrato conceptual; la conexión efectiva depende de autorización y datos disponibles |
| ML inicial | Random Forest de regresión; Deep Learning queda como alternativa experimental posterior |
| Operación | Automática, manual y degradada, exclusivamente en simulación |
| Incluido | Usuarios, parámetros, históricos, predicciones, planes, auditoría, pruebas y documentación |
| Excluido | Actuación física, cámaras, reconocimiento de placas, prioridad de emergencias, despliegue municipal y optimización de corredores |
| Restricción académica | No se afirma certificación ISO, validación vial ni aptitud para operación pública |

**Acceso a Waze.** La documentación oficial describe un feed GeoRSS JSON/XML para socios de Waze for Cities, con información compartida según el acuerdo y el área autorizada. Esto no equivale a una API pública de libre acceso. El feed de tráfico puede aportar velocidades, congestión e incidentes; no se asumirá que entrega conteos por acceso, colas o demandas peatonales. La documentación para enviar incidentes a Waze corresponde a otra dirección de integración y no sustituye el feed de consulta. [R3, R4]

En consecuencia, el generador sintético es la fuente obligatoria del prototipo. Un futuro adaptador Waze conservará como ausentes los atributos que no existan en el origen. No convertirá una velocidad en un conteo vehicular sin un método de estimación y validación adicional.

### 1.5. Metodología: Scrum con ciclo analítico CRISP-DM

Se utilizará **Scrum para gestionar el producto completo y CRISP-DM para organizar el trabajo de datos y modelado**. Scrum permite inspeccionar incrementos y ajustar el alcance en un equipo pequeño; CRISP-DM distingue la comprensión del problema, los datos, la preparación, el modelado, la evaluación y el despliegue. No son alternativas excluyentes. [R5, R6]

Se planifican cinco sprints de dos semanas. Cada sprint deberá producir un incremento verificable, incluso cuando consista en un generador, una línea base o una evaluación y no en una interfaz terminada. La secuencia PERT representa dependencias y puntos de terminación; no obliga a trabajar en cascada ni impide iniciar análisis y pruebas desde el primer sprint.

| Elemento de gestión | Aplicación al equipo |
|---|---|
| Product Owner | Líder/Backend: prioriza y mantiene el objetivo del producto; recibe retroalimentación del docente |
| Scrum Master | QA/Soporte: facilita eventos y remueve impedimentos; también participa como desarrollador |
| Developers | Los cuatro integrantes, con especialización y revisión cruzada |
| Product Backlog | Historias ligadas a requisitos RF/RNF, riesgos y criterios de aceptación |
| Sprint Planning | Selección por capacidad, dependencias, incertidumbre y objetivo del sprint |
| Daily Scrum | Máximo 15 minutos; bloqueos y ajuste del plan diario |
| Sprint Review | Demostración del incremento y revisión de métricas con el docente o representante académico |
| Retrospectiva | Acuerdos concretos sobre colaboración, calidad y estimaciones |
| Definition of Done | Revisión, pruebas pertinentes, trazabilidad y documentación actualizadas; sin defectos críticos abiertos |

La acumulación de responsabilidades permite mantener cuatro integrantes; no constituye independencia de auditoría. Ningún integrante aprobará en solitario su propia modificación en autenticación, controlador o evaluación del modelo.

| Fase CRISP-DM | Trabajo previsto | Evidencia |
|---|---|---|
| Comprensión del negocio | Problema, objetivos, restricciones y comparación con plan fijo | Objetivos y protocolo experimental |
| Comprensión de datos | Unidades, distribución, estacionalidad, faltantes y procedencia | Diccionario y perfilado |
| Preparación | Limpieza, ventanas temporales, atributos y particiones | Pipeline y manifiesto del dataset |
| Modelado | Persistencia, Random Forest y ajuste acotado | Experimentos versionados |
| Evaluación | Error predictivo, desempeño del controlador y escenarios adversos | Informe y decisión de promoción |
| Despliegue | Servicio de inferencia, monitoreo y reversión | Procedimiento de operación del prototipo |

### 1.6. Gestión de requisitos y ciclo de vida según ISO/IEC/IEEE 12207

Se adopta como referencia **ISO/IEC/IEEE 12207:2026**, edición vigente consultada, para organizar el ciclo de vida. La edición 2017 fue sustituida. La norma admite procesos iterativos y no impone Scrum ni una metodología específica. [R1, R2]

La siguiente correspondencia es una adaptación del proyecto, no una transcripción de cláusulas ni una declaración de conformidad.

| Área del ciclo de vida | Aplicación | Responsable | Evidencia |
|---|---|---|---|
| Necesidades y requisitos | Entrevistar al representante académico; definir escenarios y criterios medibles | Líder + QA | Especificación y backlog |
| Arquitectura y diseño | Contratos, estados semafóricos, datos y decisiones arquitectónicas | Líder + IA | Diseño y registros de decisión |
| Planificación y control | PERT, presupuesto, capacidad, seguimiento y riesgos | Líder | Plan y reportes por sprint |
| Configuración | Versionar código, parámetros, esquemas, datasets y modelos | Líder + IA | Tags, migraciones y manifiestos |
| Implementación e integración | Construir y verificar componentes mediante contratos | Cada responsable | Incrementos y revisión cruzada |
| Verificación | Comprobar requisitos y restricciones mediante pruebas | QA + equipo | Reportes automatizados |
| Validación | Evaluar utilidad académica y comparación experimental | QA + representante académico | Actas Alpha/Beta e informe |
| Operación y mantenimiento | Monitoreo, respaldo, reversión y corrección de defectos | QA + Líder | Manuales y bitácora |
| Retiro | Desactivar servicios, exportar resultados y eliminar credenciales | Líder + QA | Lista de cierre y archivo final |

**Procedimiento de requisitos.** Cada requisito tendrá ID, fuente, prioridad, descripción, criterio de aceptación, responsable, versión y prueba asociada. El flujo será: propuesto → analizado → aprobado → implementado → verificado → aceptado. La versión 1.0 constituirá una propuesta de línea base para revisión académica.

Todo cambio se registrará con justificación y análisis de impacto en arquitectura, datos, pruebas, ruta crítica, esfuerzo y riesgos. El Product Owner decidirá su prioridad; los cambios que alteren el objetivo o las condiciones de aceptación se revisarán con el representante académico. Se actualizará la matriz de trazabilidad antes de cerrar el cambio. Una historia del backlog no sustituirá un requisito verificable.

### 1.7. Organización y responsabilidades

| Rol | Responsabilidad principal | Revisiones y colaboración | Horas previstas |
|---|---|---|---:|
| Líder/Backend (LB) | Gestión, requisitos, API, BD, controlador y configuración | Revisa seguridad e integración; apoya despliegue | 360 |
| Frontend (FE) | Dashboard, visualización, interacción y accesibilidad | Revisa contratos y pruebas de interfaz | 300 |
| IA/Data Science (IA) | Generador, calidad de datos, pronóstico y experimentos | Revisa lógica de asignación y métricas | 340 |
| QA/Soporte (QA) | Estrategia de pruebas, automatización, soporte y manuales | Facilita Scrum y revisa aceptación | 280 |
| **Total** | **Incluye gestión, revisiones y documentación** | **No sumar nuevamente ceremonias** | **1,280** |

El docente o representante académico revisa aceptación como interesado externo; no se agrega un quinto desarrollador ni se presupuesta su tiempo.

### 1.8. Terminología del negocio

| Término | Definición aplicada |
|---|---|
| Waze Data | Información de tráfico compartida mediante el mecanismo autorizado para socios |
| Intersección | Cruce simulado con grupos de movimientos y un plan de fases |
| Semáforo inteligente | Controlador simulado que modifica repartos de verde con base en información y restricciones |
| Grupo de movimientos | Movimientos compatibles que reciben autorización simultánea |
| Fase | Intervalo que autoriza un grupo compatible de usuarios |
| Ciclo | Secuencia completa de fases; en el MVP dura 120 segundos |
| Reparto de verde | Segundos de verde asignados a cada grupo por ciclo |
| Despeje | Intervalo destinado a vaciar una zona de conflicto antes de otra autorización |
| Flujo o demanda de llegada | Vehículos que llegan por unidad de tiempo; distinto de los que logran cruzar |
| Cola | Vehículos acumulados pendientes de servicio |
| Capacidad de descarga | Ritmo supuesto al que una fase puede servir vehículos durante su verde |
| Horizonte de predicción | Periodo futuro sobre el que se pronostica; cinco minutos |
| Plan fijo | Referencia con repartos constantes y las mismas restricciones peatonales |
| Plan adaptativo | Repartos propuestos a partir del pronóstico y validados por reglas |
| Modo degradado | Continuación del simulador con un plan fijo ante fallas |
| Deriva de datos | Cambio de distribución respecto a los datos de entrenamiento |
| Trazabilidad | Vínculo entre necesidades, requisitos, componentes, riesgos y pruebas |

## 2. Análisis y diseño

### 2.1. Actores e interesados

| Actor/interesado | Tipo | Interacción o interés |
|---|---|---|
| Administrador de Tráfico | Usuario directo | Consulta, configura, autoriza intervención y revisa auditoría |
| Sistema Waze | Sistema externo opcional | Proporciona observaciones mediante acceso autorizado; reemplazado por generador en el MVP |
| Generador de tráfico | Sistema externo al núcleo | Emite datos y escenarios reproducibles |
| Conductores | Usuarios viales simulados e interesados indirectos | Generan demanda y reciben los efectos de los tiempos; no utilizan la aplicación |
| Peatones | Usuarios viales simulados e interesados indirectos | Requieren una oportunidad de cruce exclusiva y periódica; no utilizan la aplicación |
| Evaluador académico | Interesado de aceptación | Revisa evidencia, utilidad y limitaciones; utiliza reportes exportados |

Los conductores y peatones no se contabilizan como actores de interfaz para UCP porque no intercambian mensajes directamente con el software. Sus necesidades sí originan reglas y pruebas.

### 2.2. Requerimientos funcionales

Todos los criterios son compromisos del prototipo propuesto y deberán comprobarse en Fase 2. «M» significa obligatorio y «S», deseable.

| ID | Requerimiento | Prioridad | Criterio de aceptación resumido |
|---|---|---|---|
| RF-01 | Autenticar al administrador y restringir operaciones por permisos | M | Credenciales válidas permiten acceso; llamadas sin permiso devuelven 401/403 |
| RF-02 | Administrar intersecciones, grupos y parámetros | M | Alta/edición válida persiste; identificadores y configuraciones inválidas se rechazan |
| RF-03 | Generar escenarios sintéticos reproducibles | M | Misma semilla y versión producen las mismas llegadas exógenas |
| RF-04 | Registrar observaciones normalizadas | M | Guarda fuente, ventana, unidad, grupo y calidad; un duplicado no crea otra observación |
| RF-05 | Detectar datos inválidos, tardíos y ausentes | M | Rechaza negativos/imposibles; marca datos vencidos y no los usa como actuales |
| RF-06 | Consultar tráfico actual e histórico | M | Filtra por cruce y periodo; pagina y presenta fecha y procedencia |
| RF-07 | Predecir llegadas a cinco minutos | M | Devuelve valores no negativos, horizonte, modelo y condición de validez |
| RF-08 | Proponer un plan semafórico restringido | M | Satisface duración de ciclo, verdes, exclusión y transiciones; conserva motivo y versión |
| RF-09 | Aplicar planes en el simulador | M | Solo activa planes válidos en el límite de ciclo y registra la transición |
| RF-10 | Permitir intervención manual y retorno al automático | M | Solo administrador; exige motivo, duración y validación de las mismas restricciones |
| RF-11 | Activar y comunicar el modo degradado | M | Ante fuente vencida o IA indisponible activa el plan fijo al siguiente límite de ciclo |
| RF-12 | Visualizar estado, colas, demanda y alertas | M | Dashboard muestra dato, fecha, modo y estado; avisa si la información está desactualizada |
| RF-13 | Comparar plan fijo y adaptativo | M | Ejecuta escenarios pareados con las mismas llegadas y exporta métricas |
| RF-14 | Auditar decisiones y cambios | M | Cada cambio identifica actor, antes/después, momento, motivo y correlación |
| RF-15 | Versionar y promover modelos | M | Modelo, dataset, métricas y aprobación quedan ligados; permite revertir |
| RF-16 | Exportar resultados académicos | S | CSV/JSON con unidades y metadatos; se neutralizan fórmulas peligrosas en CSV |

### 2.3. Requerimientos no funcionales

| ID | Atributo | Especificación medible |
|---|---|---|
| RNF-01 | Rendimiento | API: p95 ≤ 500 ms para consultas y ≤ 1 s para predicción/plan, en prueba de 10 usuarios concurrentes, 10 minutos y cinco cruces, tras calentamiento |
| RNF-02 | Escalabilidad | Ensayo con 50 cruces, 100 grupos y una observación por grupo/minuto, sin pérdida de observaciones aceptadas y conservando RNF-01 bajo la misma concurrencia |
| RNF-03 | Moldeabilidad/modificabilidad | Cambiar límites o sustituir la fuente/modelo mediante configuración o adaptador, sin editar el controlador de fases; demostrarlo con un adaptador de prueba |
| RNF-04 | Resiliencia | La caída de IA no detiene la máquina de estados; detección en ≤ 5 s tras el timeout y activación de fallback en el siguiente ciclo, como máximo 120 s después |
| RNF-05 | Seguridad | Hash robusto de contraseñas, autorización en servidor, secretos fuera del repositorio y acceso externo cifrado; cero hallazgos críticos abiertos al entregar |
| RNF-06 | Integridad y tiempo | Transacciones y unicidad impiden planes activos duplicados y observaciones duplicadas; UTC en persistencia y America/Mexico_City en presentación |
| RNF-07 | Usabilidad y accesibilidad | Al menos 4 de 5 evaluadores completan consulta, identificación de alerta e intervención en ≤ 3 min por tarea, sin ayuda; estados con texto además de color |
| RNF-08 | Mantenibilidad | Cobertura de ramas ≥ 80% en validación/controlador, revisión por otro integrante y contratos de API documentados |
| RNF-09 | Reproducibilidad | Dataset, semillas, parámetros y dependencias fijadas permiten repetir el experimento; tolerancias numéricas documentadas |
| RNF-10 | Recuperación | RPO ≤ 24 h para datos persistidos y RTO ≤ 30 min en restauración de laboratorio; evidencia de un ejercicio de recuperación |
| RNF-11 | Observabilidad | Toda predicción y aplicación de plan es correlacionable con entrada, versión de modelo, tiempos y estado de fallback |
| RNF-12 | Transparencia | Dataset e interfaz identifican datos sintéticos; recomendaciones se presentan como heurísticas, sin afirmar optimalidad ni validación real |

El ensayo de 50 cruces evalúa capacidad informática, no coordinación vial. Las metas de latencia se medirán en una máquina de referencia de 4 núcleos lógicos y 8 GB de RAM, sin entrenamiento concurrente; se documentará el entorno efectivo.

### 2.4. Requerimientos técnicos

| ID | Decisión de diseño | Criterio técnico |
|---|---|---|
| RT-01 | Python + FastAPI para API e inferencia | Entorno reproducible, validación de esquemas y contrato OpenAPI versionado |
| RT-02 | PostgreSQL | Migraciones, restricciones, claves foráneas e índices por grupo/fecha |
| RT-03 | scikit-learn y Random Forest | Pipeline completo de transformación + predictor; carga de artefactos propios verificados |
| RT-04 | Streamlit para dashboard inicial | Consume exclusivamente la API; sin credenciales directas de BD en el navegador |
| RT-05 | Generador y simulador propios | Semillas separadas para demanda, entrenamiento y evaluación; reloj de simulación explícito |
| RT-06 | Servicios contenedorizados con Docker Compose | API, IA, dashboard y PostgreSQL; comprobaciones de salud y volúmenes persistentes |
| RT-07 | pytest y pruebas de contrato | Ejecución automatizada en integración continua; datos de prueba aislados |
| RT-08 | Contrato de observación canónico | Intersección, grupo, ventana, conteo de llegadas, velocidad opcional, clima, fuente y calidad |
| RT-09 | Gestión de configuración | Parámetros por cruce, perfiles de entorno y versiones de esquema, modelo y plan |

Streamlit reduce el alcance de interfaz para cuatro personas. React queda como alternativa de evolución; no se incluyen ambos frontends en el presupuesto. TensorFlow/PyTorch solo se justificarían después de demostrar una ventaja frente a la línea base de ML y disponer de datos suficientes. Las versiones exactas de dependencias se fijarán al iniciar la implementación y se conservarán en los archivos de bloqueo.

### 2.5. Reglas de negocio y control semafórico

Los valores siguientes son **parámetros didácticos del simulador**, no tiempos reglamentarios de la CDMX ni parámetros habilitados para infraestructura real.

| ID | Regla |
|---|---|
| RB-01 | Nunca podrán coexistir autorizaciones de movimientos incompatibles, incluida la fase peatonal |
| RB-02 | Cada ciclo durará 120 s: dos verdes vehiculares, dos amarillos de 3 s, dos despejes de 2 s y una fase peatonal de 20 s más 10 s de despeje |
| RB-03 | Los verdes vehiculares sumarán 80 s; cada grupo recibirá entre 20 y 60 s |
| RB-04 | El orden será NS → amarillo → despeje → EO → amarillo → despeje → peatones → despeje peatonal → nuevo ciclo |
| RB-05 | Todo ciclo contendrá la fase peatonal; ninguna intervención podrá omitirla ni reiniciar indefinidamente el ciclo |
| RB-06 | El plan fijo será NS=40 s y EO=40 s, con las mismas transiciones y fase peatonal |
| RB-07 | En automático, el verde de un grupo cambiará como máximo 5 s entre ciclos consecutivos |
| RB-08 | Los planes se activan al comenzar un ciclo; no se interrumpe una fase a mitad por una recomendación |
| RB-09 | Si la observación más reciente tiene más de 120 s, falta un dato obligatorio o falla IA, se usa fallback fijo al siguiente ciclo |
| RB-10 | Una intervención manual válida tiene motivo y caduca tras un máximo de 10 ciclos; no invalida RB-01 a RB-05 ni RB-08 |
| RB-11 | Precedencia: restricciones del simulador → fallback por datos/falla → intervención manual vigente → control automático |
| RB-12 | Cada decisión conserva el plan previo, entradas o su referencia, pronóstico, restricciones, versión y resultado de aplicación |
| RB-13 | La adaptación o intervención no puede aceptar una versión de plan obsoleta; se exige control de concurrencia por cruce |

Para dos demandas pronosticadas no negativas, d_NS y d_EO, se propone la política inicial:

\[
g^{*}_{NS}=\operatorname{clip}\left(80\frac{d_{NS}}{d_{NS}+d_{EO}},20,60\right),
\qquad g^{*}_{EO}=80-g^{*}_{NS}.
\]

Si la demanda total es cero se propone 40/40. Después se limita el cambio respecto al ciclo anterior a ±5 s, se redondea g_NS a segundos enteros y se calcula g_EO como complemento para conservar exactamente 80 s. Las validaciones se repiten sobre el plan final. La transición a fallback puede exceptuar el límite de variación RB-07, registrando el motivo; conserva las demás restricciones aplicables.

Esta política es una **heurística proporcional**, no una solución óptima demostrada. En cada grupo el tiempo rojo se deriva de la máquina de estados: rojo = 120 − verde − amarillo propio. Por ejemplo, con verde de 40 s y amarillo de 3 s, el rojo es de 77 s. No se predicen verde y rojo de forma independiente.

### 2.6. Diseño de datos, ML y evaluación científica

| Elemento | Especificación |
|---|---|
| Observación | Una ventana de 60 s por grupo; simulación interna con paso de 1 s |
| Variables de entrada | Hora cíclica, día de semana, clima conocido al decidir, historial de llegadas y velocidad disponible; configuración del grupo |
| Variable objetivo | Promedio de llegadas por minuto en las cinco ventanas siguientes, calculado a partir de conteos futuros reservados como etiquetas |
| Inferencia | Una propuesta por cruce al planificar el siguiente ciclo; no recalcular y aplicar a cada petición del dashboard |
| Datos iniciales | 90 días × 1,440 min × 5 cruces × 2 grupos = 1,296,000 observaciones |
| Generación | Intensidades por horario/día, ruido aleatorio, autocorrelación, lluvia e incidentes; llegadas independientes de la política comparada |
| Particiones | Días 1–54 entrenamiento; 55–72 validación; 73–90 prueba final |
| Prevención de fuga | Eliminar muestras cuya etiqueta futura cruce una frontera; construir atributos solo con información conocida al decidir |
| Ajuste | Validación temporal expansiva dentro del entrenamiento, con separación mínima de cinco minutos; preprocesamiento ajustado solo con entrenamiento |
| Línea base predictiva | Persistencia del promedio de llegadas de los cinco minutos anteriores |
| Modelo candidato | Random Forest; presupuesto inicial limitado de hiperparámetros y tamaño de muestra para mantener factibilidad |
| Registro | Hash del dataset, semillas, rangos temporales, código, entorno, atributos, métricas y limitaciones |

Todos los grupos se separarán usando los mismos cortes de tiempo; no se hará una división aleatoria de filas que mezcle observaciones vecinas. Se podrán usar hasta 300,000 filas del tramo de entrenamiento en el primer experimento, con muestreo documentado por bloques y escenarios; validación y prueba conservarán periodos completos. La documentación de scikit-learn respalda el aislamiento del preprocesamiento y las particiones temporales para reducir fugas de información. [R7, R8]

El simulador conservará vehículos: cola siguiente = cola actual + llegadas − salidas; las salidas estarán limitadas por vehículos disponibles y capacidad durante la fase autorizada. Se parametrizarán carriles y tasa de descarga. La cola sintética del simulador no se etiquetará como un campo obtenido de Waze.

| Dimensión | Protocolo y criterio de evaluación |
|---|---|
| Calidad predictiva | MAE y RMSE globales y por grupo/escenario; meta de MAE al menos 10% menor que persistencia en la prueba final |
| Control | Comparar plan adaptativo y fijo con iguales llegadas, capacidades, duración de ciclo y oportunidades peatonales |
| Escenarios | Valle, pico, desbalance entre grupos, lluvia/incidente y sobresaturación |
| Repeticiones | Diez semillas inéditas por escenario: 50 comparaciones pareadas; 15 min de calentamiento y 2 h de medición por ejecución |
| Métricas de movilidad | Demora acumulada, espera de vehículos servidos, vehículos pendientes, cola media/p95, salidas y espera peatonal |
| Meta experimental | En escenarios no sobresaturados: reducción media de demora ≥ 10%, intervalo de confianza pareado del 95% que excluya cero y cola p95 no más de 10% peor que el plan fijo |
| Sobresaturación | Reportar crecimiento de cola y capacidad insuficiente; exigir invariantes y continuidad, sin prometer resolver demanda superior a la capacidad |
| Invariantes | Cero conflictos y cero omisiones peatonales en todas las ejecuciones |
| Promoción | Si no supera la referencia, conservar el modelo para análisis y operar el plan fijo; documentar el resultado negativo |

Se contabilizarán vehículos pendientes al final para evitar que una política aparente menor espera por servir únicamente a los vehículos fáciles. Las diferencias se resumirán por corrida pareada; los intervalos se calcularán por remuestreo de corridas, no de segundos correlacionados. Las semillas experimentales y los escenarios de evaluación se fijarán antes de comparar políticas. No se usarán los resultados de prueba final para seguir ajustando el modelo.

No se inferirá mejora en calles reales a partir de datos sintéticos. La aceptación funcional del prototipo y el éxito de la hipótesis de mejora son decisiones distintas: una evaluación negativa bien ejecutada sigue siendo un resultado académico, pero no habilita afirmar que el control adaptativo es superior.

### 2.7. Calendarización: PERT y ruta crítica

Las duraciones son días hábiles de ocho horas y representan tiempo transcurrido, no horas de esfuerzo. Se utiliza una estimación de tres puntos: optimista To, más probable Tn y pesimista Tp.

\[
TE=\frac{To+4Tn+Tp}{6},\qquad \sigma_i^2=\left(\frac{Tp-To}{6}\right)^2.
\]

Todas las precedencias son fin–inicio sin retraso. El tiempo cero es el inicio del proyecto. Las dependencias técnicas gobiernan la terminación de cada paquete, aunque sus borradores puedan evolucionar antes.

| ID | Actividad y entrega | Predecesoras | Responsable | To | Tn | Tp | TE | Inicio temprano | Fin temprano | Holgura |
|---|---|---|---|---:|---:|---:|---:|---:|---:|---:|
| A | Alcance, objetivos y plan inicial | — | LB + equipo | 3 | 4 | 5 | 4 | 0 | 4 | 0 |
| B | Requisitos, riesgos y aceptación | A | LB + QA | 3 | 5 | 7 | 5 | 4 | 9 | 0 |
| C | Arquitectura, contratos y diseño BD | B | LB | 3 | 4 | 5 | 4 | 9 | 13 | 0 |
| D | Generador y perfilado inicial | B | IA | 3 | 5 | 7 | 5 | 9 | 14 | 2 |
| E | Esquema, migraciones y acceso a datos | C | LB | 3 | 4 | 5 | 4 | 13 | 17 | 0 |
| F | Diseño de interacción y dashboard | B | FE | 2 | 4 | 6 | 4 | 9 | 13 | 7 |
| G | Pipeline, entrenamiento y referencia | D | IA | 5 | 7 | 9 | 7 | 14 | 21 | 2 |
| H | API, autenticación e ingesta | E | LB | 4 | 6 | 8 | 6 | 17 | 23 | 0 |
| I | Dashboard funcional conectado a contrato | C, F | FE | 6 | 8 | 10 | 8 | 13 | 21 | 7 |
| J | Controlador, simulador e inferencia integrada | H, G | LB + IA | 3 | 5 | 7 | 5 | 23 | 28 | 0 |
| K | Integración y observabilidad de extremo a extremo | J, I | Equipo | 3 | 4 | 5 | 4 | 28 | 32 | 0 |
| L | Cierre de pruebas funcionales, fallas y carga | K | QA + equipo | 4 | 6 | 8 | 6 | 32 | 38 | 0 |
| M | Evaluación experimental y revisión del modelo | K | IA + QA | 3 | 5 | 7 | 5 | 32 | 37 | 1 |
| N | Alpha/Beta, correcciones y aceptación | L, M | QA + equipo | 2 | 4 | 6 | 4 | 38 | 42 | 0 |
| O | Empaquetado, manuales finales y transferencia | N | QA + LB | 2 | 3 | 4 | 3 | 42 | 45 | 0 |

Para el cálculo hacia adelante, el inicio temprano es el mayor fin temprano de los predecesores. En el recorrido inverso, el fin tardío es el menor inicio tardío de los sucesores. La holgura es inicio tardío menos inicio temprano.

**Ruta crítica:** A → B → C → E → H → J → K → L → N → O.

**Duración esperada:** 4 + 5 + 4 + 4 + 6 + 5 + 4 + 6 + 4 + 3 = **45 días hábiles**, equivalentes a nueve semanas. La suma de varianzas de esa ruta es 2.78 días², con desviación aproximada de 1.67 días si se aceptan independencia y ruta estable. Esa aproximación no garantiza una probabilidad de terminación: puede haber correlaciones, retrabajo y cambios de ruta.

Se reserva una décima semana parcial: **cinco días hábiles adicionales**, para un horizonte de 50 días. La red anterior identifica la ruta crítica por precedencias; la planificación de cada sprint deberá comprobar carga individual y recalcularla si la disponibilidad genera nuevas dependencias. No se divide la ruta crítica entre cuatro integrantes.

| Sprint | Días | Objetivo y salida verificable |
|---|---|---|
| 1 | 1–10 | Alcance, requisitos, riesgos; primeras decisiones, datos y boceto de interfaz |
| 2 | 11–20 | Esquema/ingesta, generador, referencia predictiva y dashboard con contrato de prueba |
| 3 | 21–30 | API, controlador e integración; comparación preliminar |
| 4 | 31–40 | Pruebas del sistema, experimentos y comienzo de aceptación |
| 5 | 41–50 | Cierre de aceptación y manuales hasta día 45; reserva del día 46 al 50 |

Capacidad bruta: 4 personas × 10 semanas × 40 h = **1,600 h**. El trabajo presupuestado ocupa **1,280 h, 80%**; las 320 h de capacidad restante cubren disponibilidad desigual y contingencias. Esta capacidad no se factura automáticamente ni sustituye la reserva monetaria. La validación detallada por persona se hará antes de comprometer cada sprint; la duración PERT es una estimación, no un calendario de recursos ya contractualizado.

### 2.8. Estudio de factibilidad

#### 2.8.1. Factibilidad técnica

| Recurso | Configuración de referencia | Justificación y límite |
|---|---|---|
| Desarrollo | Cuatro computadoras existentes, 4 núcleos, 8 GB RAM mínimo y 20 GB libres | API, dashboard y pruebas locales |
| Entrenamiento | Una computadora con 8 núcleos, 16 GB RAM y 50 GB libres recomendados | Entrenamiento acotado y procesamiento por bloques; medir consumo real |
| GPU | No requerida para la línea base | Random Forest permite comenzar con CPU; Deep Learning requeriría otro estudio |
| Plataforma | Python, FastAPI, PostgreSQL, scikit-learn y Streamlit | Compatibilidad mediante contratos y entorno fijado |
| Contenedores | Docker Compose en entorno compatible | Reproducción local sin Kubernetes |
| Red | Solo necesaria para instalar dependencias y para un adaptador externo opcional | Demostración sintética operativa sin Waze |
| Almacenamiento | Datos de observaciones, resultados y modelos con retención configurable | Medir tamaño antes de ampliar; índices y JSON pueden superar al dato bruto |

Como referencia, 1,296,000 observaciones a 300 bytes representarían unos 389 MB de datos lógicos, sin índices ni sobrecargas de PostgreSQL. No es una medida de almacenamiento real. Se reserva margen para réplicas experimentales y artefactos; se evitará guardar cada segundo de estado indefinidamente.

**Dictamen técnico:** factible para simulación acotada y ML tabular, condicionado a limitar el entrenamiento y verificar recursos en el primer experimento. No se ha demostrado factibilidad de despliegue municipal.

#### 2.8.2. Factibilidad operativa

No se dispone de un levantamiento del proceso real de la CDMX. El «proceso actual» siguiente es una referencia académica asumida, que deberá validarse si el proyecto cambia de alcance.

| Aspecto | Referencia asumida | Proceso propuesto |
|---|---|---|
| Programación | Plan fijo definido por horario | Plan fijo de referencia y propuesta adaptativa por ciclo |
| Supervisión | Revisión manual de estados | Dashboard con fecha, procedencia, colas y alertas |
| Intervención | Ajuste manual de parámetros | Intervención autenticada, validada y con caducidad |
| Fuente ausente | Información insuficiente para adaptar | Continuar con plan fijo y registrar degradación |
| Modelo erróneo | No existe componente predictivo | Bloquear promoción, revertir versión y conservar referencia |
| Incidente de BD | Registro interrumpido | Máquina de estados conserva plan local; bloquear cambios no auditables y recuperar el historial |
| Caída del controlador | Simulación detenida | Mostrar estado desconocido, detener el avance y reiniciar desde un estado de despeje validado |
| Adopción | Conocimiento individual | Manual de operación, sesión de transferencia y guion de demostración |

**Dictamen operativo:** factible con un administrador capacitado y procedimientos de reinicio, fallback y respaldo. El indicador visual nunca mostrará como actual un estado cuya telemetría se haya perdido.

#### 2.8.3. Factibilidad económica

Las tarifas son valores internos de planeación en MXN por hora, sin IVA; no representan salarios oficiales ni precios de mercado. Se asume disponibilidad previa de equipos. Se considera el costo de oportunidad del trabajo aunque no exista desembolso salarial.

| Rol | Horas-persona | Tarifa supuesta MXN/h | Subtotal MXN |
|---|---:|---:|---:|
| Líder/Backend | 360 | 250 | 90,000 |
| Frontend | 300 | 200 | 60,000 |
| IA/Data Science | 340 | 280 | 95,200 |
| QA/Soporte | 280 | 180 | 50,400 |
| **Total de trabajo** | **1,280** | **230.94 promedio ponderado** | **295,600** |

| Concepto | Importe MXN | Supuesto |
|---|---:|---|
| Trabajo del equipo | 295,600 | Incluye gestión, revisión, pruebas y documentación |
| Recursos temporales de pruebas | 5,000 | Tope presupuestario para cómputo auxiliar, no cotización |
| Respaldo y almacenamiento | 2,000 | Tope para el periodo del proyecto |
| Materiales y conectividad incremental | 1,000 | Consumos adicionales de laboratorio |
| **Costo base** | **303,600** | Sin compras de hardware ni despliegue físico |
| Reserva de contingencia | 12,300 | Exposición residual estimada de riesgos identificados |
| **Línea base de costo** | **315,900** | Base más contingencia |
| Reserva de gestión | 15,180 | 5% del costo base para incertidumbre no identificada |
| **Presupuesto total de referencia** | **331,080** | No sumar nuevamente la exposición inicial |

No se presupuestan licencias comerciales obligatorias para el stack propuesto; se revisarán las licencias de sus versiones concretas. Se asume consulta de normas mediante acceso institucional; adquirir textos normativos, hardware o servicios adicionales exigiría una partida nueva. El acceso a Waze no se considera garantizado ni se asigna un precio inventado.

**Dictamen económico:** viable como proyecto académico si se dispone de equipo y tiempo institucional. No existe evidencia suficiente para calcular ROI municipal, ahorro de combustible o recuperación de inversión. Antes de ese cálculo harían falta aforos reales, calibración y costos de infraestructura/operación.

### 2.9. Análisis de riesgos

Se aplican escalas de 1 a 5. Para convertir la probabilidad ordinal a exposición monetaria se utiliza un mapeo explícito de planeación; no se multiplica directamente la puntuación ordinal por dinero.

| Puntuación P | Descripción | Probabilidad usada en EMV |
|---:|---|---:|
| 1 | Muy baja | 10% |
| 2 | Baja | 25% |
| 3 | Media | 50% |
| 4 | Alta | 70% |
| 5 | Muy alta | 90% |

| Puntuación I | Impacto sobre el proyecto |
|---:|---|
| 1 | Menor: corrección local sin afectar aceptación |
| 2 | Moderado: retrabajo acotado en un componente |
| 3 | Relevante: afecta un sprint o una función principal |
| 4 | Grave: compromete un hito o la validez experimental |
| 5 | Crítico: invalida restricciones esenciales o la entrega |

Nivel = P × I: bajo 1–4, medio 5–9, alto 10–16 y crítico 17–25. Un riesgo I=5 requiere revisión obligatoria aunque su producto no sea crítico.

\[
EMV_i=p_i\times L_i
\]

L es la pérdida económica adicional por ocurrencia: retrabajo, recuperación o retraso. Las pérdidas son hipótesis presupuestarias y no equivalen a daños viales reales, que están fuera del alcance.

| ID | Riesgo y disparador | P | I | Nivel | Estrategia y respuesta | Dueño | Pérdida L MXN | EMV inicial MXN |
|---|---|---:|---:|---:|---|---|---:|---:|
| R-01 | Acceso Waze no disponible al necesitar integración | 4 | 3 | 12 alto | Evitar dependencia: sintéticos obligatorios y adaptador opcional | LB | 12,000 | 8,400 |
| R-02 | Datos sintéticos poco representativos; fallan escenarios inéditos | 4 | 4 | 16 alto | Mitigar: escenarios diversos, ruido, semillas externas y declaración de límites | IA | 20,000 | 14,000 |
| R-03 | Fuga temporal o sobreajuste; error sospechosamente bajo | 3 | 4 | 12 alto | Mitigar: cortes temporales, purga de etiquetas y revisión independiente | IA + QA | 16,000 | 8,000 |
| R-04 | Plan incompatible, omisión peatonal o transición inválida | 2 | 5 | 10 alto | Mitigar: invariantes, máquina de estados, pruebas generativas y rechazo previo | LB + QA | 24,000 | 6,000 |
| R-05 | Pérdida de fuente, IA o BD; timeout o dato vencido | 3 | 3 | 9 medio | Mitigar: timeout, fallback, respaldo y simulacros de restauración | QA | 10,000 | 5,000 |
| R-06 | Acceso indebido o exposición de secretos detectada | 2 | 4 | 8 medio | Mitigar: permisos, secretos externos, revisión de dependencias y logs depurados | LB | 20,000 | 5,000 |
| R-07 | Ausencia de integrante o sobrecarga en la ruta crítica | 3 | 4 | 12 alto | Mitigar: revisión cruzada, manuales, respaldo de rol y ajuste de alcance | LB | 18,000 | 9,000 |
| R-08 | No se alcanzan latencia o beneficio experimental | 3 | 3 | 9 medio | Mitigar y aceptar resultado negativo: perfilar, acotar carga y conservar plan fijo | IA + FE | 12,000 | 6,000 |
| **Total** | | | | | | | | **61,400** |

| ID | P residual | I residual | Nivel residual | Pérdida residual MXN | EMV residual MXN | Evidencia exigida para reconocer reducción |
|---|---:|---:|---:|---:|---:|---|
| R-01 | 1 | 2 | 2 | 2,000 | 200 | Demostración completa sin red ni Waze |
| R-02 | 2 | 3 | 6 | 12,000 | 3,000 | Evaluación de escenarios y límites documentados |
| R-03 | 1 | 3 | 3 | 8,000 | 800 | Inspección de particiones y pipeline |
| R-04 | 1 | 5 | 5 | 24,000 | 2,400 | Cero violaciones en la batería; revisión obligatoria por I=5 |
| R-05 | 1 | 2 | 2 | 4,000 | 400 | Fallback y restauración comprobados |
| R-06 | 1 | 3 | 3 | 10,000 | 1,000 | Pruebas de permisos y revisión de secretos |
| R-07 | 2 | 3 | 6 | 12,000 | 3,000 | Transferencia y capacidad revisadas por sprint |
| R-08 | 2 | 2 | 4 | 6,000 | 1,500 | Pruebas de carga e informe comparativo |
| **Total** | | | | | **12,300** | **Reserva propuesta de contingencia** |

La exposición residual es una previsión posterior al tratamiento, no un resultado ya observado. Las mitigaciones preventivas están incluidas en las 1,280 h; las pérdidas representan trabajo adicional. La suma EMV orienta la reserva y no es un máximo de pérdida; se revisará por dependencias y consecuencias compartidas. No se elige transferencia porque no existe un tercero que asuma estos riesgos mediante contrato. Evitar, mitigar, transferir o aceptar son opciones de tratamiento, no casillas que deban usarse todas.

### 2.10. Matriz de trazabilidad

La matriz conecta todos los RF del alcance y los RNF con componentes, riesgos y familias de prueba. Los IDs P se especifican en el plan de pruebas.

| Objetivo/necesidad | Requisitos | Componente | Riesgos | Verificación |
|---|---|---|---|---|
| Acceso y configuración controlados | RF-01, RF-02; RNF-05; RT-01, RT-02 | API, usuarios y catálogo | R-06 | P-01, P-08 |
| Datos reproducibles y válidos | OE-02; RF-03, RF-04, RF-05; RNF-06, RNF-09; RT-05, RT-08 | Generador, ingesta y BD | R-01, R-02, R-03 | P-02, P-03, P-05 |
| Consulta y supervisión | RF-06, RF-12, RF-16; RNF-07, RNF-12; RT-04 | API y dashboard | R-05, R-08 | P-03, P-07, P-10 |
| Pronóstico verificable | OE-03; RF-07, RF-15; RNF-09, RNF-11; RT-03 | Pipeline y servicio IA | R-02, R-03, R-08 | P-05, P-11 |
| Control coherente y prioridad peatonal | OE-04; RF-08, RF-09; RB-01 a RB-08, RB-13 | Controlador y simulador | R-04 | P-04, P-06 |
| Intervención y continuidad | RF-10, RF-11; RB-09 a RB-11; RNF-04, RNF-10 | API, controlador y respaldo | R-04, R-05, R-06 | P-06, P-08, P-09 |
| Demostración de utilidad | OE-05; RF-13; RNF-12 | Evaluador experimental | R-02, R-03, R-08 | P-05, P-07, P-10 |
| Auditoría y versiones | OE-07; RF-14, RF-15; RB-12; RNF-06, RNF-11; RT-09 | BD, bitácora y registro de modelos | R-03, R-05, R-06 | P-03, P-11 |
| Capacidad y tiempos de respuesta | RNF-01, RNF-02; RT-06 | API, IA y BD | R-08 | P-12 |
| Modificación y mantenibilidad | RNF-03, RNF-08; RT-07 | Adaptadores, módulos y CI | R-07, R-08 | P-01, P-13 |

### 2.11. Normas y referentes

La solicitud menciona «ISO 42000». Para evitar una referencia ambigua se utiliza **ISO/IEC 42001:2023**, que especifica un sistema de gestión de IA. No se atribuyen requisitos a una supuesta ISO 42000 sin una identificación documental precisa. [R9]

| Referencia | Aplicación prevista | Evidencia del proyecto |
|---|---|---|
| ISO/IEC/IEEE 12207:2026 | Organización y adaptación del ciclo de vida del software | Requisitos, diseño, gestión, configuración, verificación, validación y mantenimiento |
| ISO/IEC 42001:2023 | Gobierno de IA: responsabilidades, riesgos, transparencia y mejora | Política de uso académico, registro de modelos, limitaciones y decisión de promoción |
| ISO/IEC 23894:2023 | Orientación complementaria para riesgo de IA | Identificación, tratamiento, seguimiento y riesgo residual |
| ISO/IEC 5338:2023 | Referente complementario de procesos del ciclo de vida de IA | Versionado de datos/modelos y evaluación continua |

La ficha de ISO/IEC 42001 identifica también ISO/IEC 23894 como referente de riesgo de IA; su edición consultada es 2023. ISO/IEC 5338 aborda procesos de ciclo de vida de sistemas de IA y su relación con los procesos tradicionales de software. [R9, R10, R12]

Este documento establece **alineación propuesta**, no certificación ni conformidad exhaustiva por cláusula. Una evaluación formal requeriría los textos completos autorizados, una matriz de obligaciones aplicables y evidencias de ejecución. Las tablas propias no se presentan como requisitos textuales de ISO.

## 3. Modelado de casos de uso y arquitectura

### 3.1. Diagrama de casos de uso: descripción textual

El límite del sistema se denomina «SGT-CDMX simulado». El Administrador se sitúa fuera del límite y se asocia con los casos de acceso, catálogo, consulta, supervisión, intervención y auditoría. El proveedor de datos, implementado por el generador y opcionalmente por Waze, se asocia con el registro de observaciones.

Dentro del límite, el ajuste semafórico utiliza la obtención de predicción, la validación de restricciones y la aplicación al simulador. El comportamiento de fallback extiende el ajuste cuando falla la fuente o IA. Los conductores y peatones se representan como interesados del entorno simulado, sin asociación de interfaz directa; sus restricciones anotan los casos de ajuste e intervención.

| Caso | Nombre y actor primario | Alcance | Transacciones estimadas para UCP |
|---|---|---|---:|
| CU-01 | Acceder — Administrador | Autenticarse y obtener sesión | 3 |
| CU-02 | Gestionar catálogo — Administrador | Cruces, grupos y límites | 6 |
| CU-03 | Registrar datos — Proveedor | Validar, normalizar, deduplicar y persistir | 6 |
| CU-04 | Consultar tráfico — Administrador | Datos actuales e históricos paginados | 3 |
| CU-05 | Obtener predicción — Administrador/API | Validar ventana y obtener pronóstico versionado | 5 |
| CU-06 | Ajustar semáforo — Administrador que habilita automático | Pronóstico, política, validación, aplicación y alternativas | 9 |
| CU-07 | Intervenir manualmente — Administrador | Validación, vigencia, concurrencia y reversión | 8 |
| CU-08 | Comparar estrategias — Administrador | Selección, ejecución pareada y resultados | 6 |
| CU-09 | Supervisar dashboard — Administrador | Estado, fecha y alertas | 3 |
| CU-10 | Revisar auditoría — Administrador | Consulta de decisiones y cambios | 3 |

Una transacción UCP representa una interacción significativa actor–sistema, no cada función interna o llamada SQL. Los conteos incluyen alternativas relevantes y son estimaciones que deberán revisarse al detallar las historias. La gestión técnica de modelos es un proceso interno de configuración en este alcance, no un caso de interfaz adicional contado en UCP.

### 3.2. Especificación CU-03: Registrar datos

| Campo | Especificación |
|---|---|
| Objetivo | Incorporar una observación íntegra, trazable y utilizable |
| Actor principal | Proveedor de datos: generador; adaptador Waze si estuviera habilitado |
| Disparador | Arribo de un lote de observaciones de ventanas de 60 s |
| Precondiciones | Fuente configurada; cruce/grupo existente; canal autorizado cuando aplique |
| Entradas | IDs, inicio/fin de ventana, conteo de llegadas, atributos opcionales, fuente, ID externo y calidad |
| Resultado exitoso | Observaciones guardadas una sola vez y resultado individual por elemento |
| Postcondición | Cada registro aceptado conserva procedencia y tiempo de recepción; no se pierde evidencia de rechazo |
| Requisitos | RF-03, RF-04, RF-05, RB-09, RNF-06, RNF-09 |

| Paso | Flujo principal |
|---:|---|
| 1 | El proveedor envía el lote con su identificación y ventanas |
| 2 | El sistema confirma permisos, estructura y tamaño permitido |
| 3 | Valida unidades, pertenencia al cruce/grupo y coherencia temporal |
| 4 | Normaliza datos, identifica duplicados y asigna calidad |
| 5 | Persiste los elementos válidos en transacciones y actualiza la disponibilidad |
| 6 | Devuelve aceptados, duplicados y rechazados con códigos trazables |

| Alternativa/excepción | Respuesta |
|---|---|
| A1: Registro duplicado | Confirma procesamiento previo; no crea otra fila |
| A2: Valor negativo, grupo desconocido o ventana inválida | Rechaza el elemento con motivo; no se usa para inferencia |
| A3: Dato tardío | Puede guardarse como histórico, pero no reactiva la fuente como actual |
| A4: Fuente sin conteos | Conserva atributos disponibles; no inventa demanda y no habilita el modo adaptativo |
| E1: Error de BD | No informa éxito sin confirmación; reintento idempotente y alerta |
| E2: Proveedor indisponible | Caducidad de observaciones conduce al fallback según RB-09 |

**Aceptación:** al reenviar el mismo lote dos veces, cada observación válida existe una sola vez; las inválidas tienen motivos; los datos tardíos no se presentan como actuales.

### 3.3. Especificación CU-06: Ajustar semáforo

| Campo | Especificación |
|---|---|
| Objetivo | Aplicar al siguiente ciclo un plan válido y auditable |
| Actor principal | Administrador que habilita el modo automático |
| Disparador | El controlador interno solicita el plan antes del límite de ciclo |
| Precondiciones | Cruce activo, máquina de estados operativa, configuración válida y plan fijo disponible |
| Entradas | Estado anterior, datos de demanda, restricciones y versiones |
| Resultado exitoso | Un plan propuesto se valida y se activa una sola vez en el ciclo previsto |
| Postcondición | Quedan registrados plan, modo, versión, causa y aplicación efectiva |
| Requisitos | RF-07 a RF-11, RF-14; RB-01 a RB-13 |

| Paso | Flujo principal |
|---:|---|
| 1 | El administrador mantiene habilitado el control automático |
| 2 | El sistema informa o conserva el modo y ciclo actualmente activos |
| 3 | El administrador solicita o recibe el detalle del próximo ajuste |
| 4 | El sistema verifica actualidad y completitud de los datos y obtiene el pronóstico |
| 5 | El sistema calcula el reparto de verde, limita variación y redondea sin alterar el ciclo |
| 6 | El sistema valida conflictos, tiempos, fase peatonal y versión de plan previa |
| 7 | El sistema registra el plan como pendiente y lo comunica al administrador |
| 8 | En el límite de ciclo, el sistema confirma estado y aplica el plan una sola vez |
| 9 | El sistema comunica aplicación, causa y métricas disponibles |

| Alternativa/excepción | Respuesta |
|---|---|
| A1: Demanda cero | Proponer 40/40 |
| A2: IA en timeout, predicción inválida o datos vencidos | Registrar causa y programar plan fijo, sin detener las transiciones vigentes |
| A3: Intervención manual vigente y condiciones válidas | Aplicar plan manual validado, con fecha de caducidad |
| A4: Violación de restricciones | Rechazar propuesta y utilizar fallback validado |
| A5: Otro plan modificó la versión | Rechazar aplicación obsoleta; volver a planificar contra el estado vigente |
| E1: Sin confirmación del simulador | Mostrar pendiente/fallido; no declarar un cambio efectivo |
| E2: Sin registro transaccional disponible | Conservar operación local con plan fijo; bloquear cambios no auditables |

**Aceptación:** con demandas de prueba 30 y 10 veh/min y plan anterior 40/40, la política propone inicialmente 60/20 y el limitador produce 45/35 para el ciclo siguiente. El ciclo conserva 120 s, fase peatonal y transiciones; el dashboard distingue propuesta de aplicación. Con fuente vencida, se programa 40/40 y se registra fallback.

### 3.4. Estimación mediante puntos de caso de uso — UCP

Se usa el esquema clásico de ponderación como estimación independiente del esfuerzo, no como una medida de precisión garantizada. La literatura de estimación con UCP distingue actores, casos, complejidad técnica y entorno; la productividad requiere calibración. [R11]

\[
UCP=(UAW+UUCW)\times TCF\times EF.
\]

#### 3.4.1. Actores y casos sin ajustar

| Actor técnico | Clasificación | Cantidad | Peso | Aporte UAW |
|---|---|---:|---:|---:|
| Administrador con interfaz gráfica | Complejo | 1 | 3 | 3 |
| Proveedor por API — generador o Waze, alternativas del mismo puerto | Simple | 1 | 1 | 1 |
| **Total** | | **2** | | **4** |

No se cuentan nuevamente los microservicios internos, el programador de ciclos ni los usuarios viales indirectos. Generador y Waze representan implementaciones alternativas de un actor lógico; habilitar ambos con casos propios exigiría revisar el cálculo.

| Complejidad del caso | Regla por transacciones | Casos | Cantidad | Peso | Aporte UUCW |
|---|---|---|---:|---:|---:|
| Simple | 1–3 | CU-01, CU-04, CU-09, CU-10 | 4 | 5 | 20 |
| Medio | 4–7 | CU-02, CU-03, CU-05, CU-08 | 4 | 10 | 40 |
| Complejo | Más de 7 | CU-06, CU-07 | 2 | 15 | 30 |
| **Total** | | | **10** | | **90** |

UUCP = 4 + 90 = **94**.

#### 3.4.2. Factor técnico

Las valoraciones son hipótesis entre 0 y 5: 0 indica ausencia y 5 relevancia alta.

| Factor | Peso | Valoración | Producto |
|---|---:|---:|---:|
| T1 Sistema distribuido | 2 | 3 | 6 |
| T2 Rendimiento | 1 | 3 | 3 |
| T3 Eficiencia del usuario | 1 | 3 | 3 |
| T4 Complejidad interna | 1 | 4 | 4 |
| T5 Reutilización | 1 | 3 | 3 |
| T6 Instalación sencilla | 0.5 | 4 | 2 |
| T7 Facilidad de uso | 0.5 | 4 | 2 |
| T8 Portabilidad | 2 | 2 | 4 |
| T9 Facilidad de cambio | 1 | 3 | 3 |
| T10 Concurrencia | 1 | 3 | 3 |
| T11 Seguridad | 1 | 3 | 3 |
| T12 Acceso de terceros | 1 | 2 | 2 |
| T13 Capacitación especial | 1 | 2 | 2 |
| **Suma técnica** | | | **40** |

TCF = 0.6 + 0.01 × 40 = **1.00**.

#### 3.4.3. Factor de entorno

| Factor | Peso | Valoración | Producto |
|---|---:|---:|---:|
| E1 Familiaridad con el proceso | 1.5 | 2 | 3 |
| E2 Experiencia en el dominio | 0.5 | 2 | 1 |
| E3 Experiencia orientada a objetos | 1 | 3 | 3 |
| E4 Capacidad del analista líder | 0.5 | 4 | 2 |
| E5 Motivación | 1 | 4 | 4 |
| E6 Estabilidad de requisitos | 2 | 3 | 6 |
| E7 Integrantes a tiempo parcial | −1 | 0 | 0 |
| E8 Dificultad del lenguaje | −1 | 1 | −1 |
| **Suma de entorno** | | | **18** |

EF = 1.4 − 0.03 × 18 = **0.86**.

**Resultado:** UCP = 94 × 1.00 × 0.86 = **80.84 UCP**.

Se propone inicialmente una productividad de **16 h/UCP**, supuesto local sin calibración histórica: 80.84 × 16 = **1,293.44 h**, aproximadamente 1,293 h. Difiere en 13.44 h, alrededor de 1.1%, de las 1,280 h estimadas por roles; esa cercanía no demuestra exactitud. La capacidad disponible absorbe esa diferencia, pero el trabajo adicional deberá presupuestarse si se confirma.

Sensibilidad con 12–20 h/UCP: **970.08–1,616.80 h**. En el extremo de 20 h/UCP se supera la capacidad de 1,600 h, por lo que habría que reducir alcance, ampliar plazo o modificar disponibilidad. Se recalibrará al completar el segundo sprint. El valor E7=0 depende de la disponibilidad de 40 h/semana asumida; si el equipo estudia o trabaja en paralelo se revisarán EF, costos y calendario.

UCP es una comprobación alternativa de esfuerzo; **no se suma** a las horas del presupuesto ni convierte automáticamente esfuerzo en duración PERT.

### 3.5. Modelo lógico de base de datos

El modelo se normaliza alrededor de intersección, grupo de movimientos y ventana de observación. Se mantiene `Registros_Trafico` como histórico; no se crea otro historial redundante con la misma información.

| Tabla | Clave y relaciones | Campos principales y propósito |
|---|---|---|
| Intersecciones | PK id | nombre, latitud, longitud, zona_horaria, activa y version_configuracion |
| Grupos_Movimiento | PK id; FK interseccion_id | codigo NS/EO/PEATON, tipo, carriles, capacidad_descarga y limites |
| Semaforos | PK id; FK grupo_id | identificador de cabezal, estado_operativo y metadatos; estado de color actual derivado del controlador |
| Registros_Trafico | PK id; FK grupo_id | ventana_inicio, ventana_fin, conteo_llegadas, velocidad_kmh opcional, clima, fuente, id_externo, calidad y recibido_en |
| Usuarios | PK id | correo único, hash_password, rol, activo y creado_en |
| Modelos | PK id | version única, hash_artefacto, hash_dataset, atributos, corte_entrenamiento, metricas, estado y creado_en |
| Predicciones | PK id; FK grupo_id, modelo_id | instante_decision, horizonte_min, flujo_predicho, referencias_entrada y calidad |
| Planes_Semaforicos | PK id; FK interseccion_id, usuario_id opcional | ciclo_objetivo, version_previa, modo, causa, estado, creado_en y aplicado_en |
| Detalles_Plan | PK plan_id + grupo_id; FK a ambos | orden, verde_s, amarillo_s y despeje_s; fases peatonales identificadas por tipo |
| Auditoria | PK id; FK usuario_id opcional | instante, actor_servicio, accion, entidad, antes, despues, motivo y correlation_id |
| Experimentos | PK id; FK modelo_id opcional | semillas, escenario, configuracion, politica, periodo y metricas |

**Relaciones textuales:** una intersección contiene varios grupos; un grupo tiene uno o varios cabezales y muchos registros/predicciones; un modelo produce muchas predicciones; una intersección acumula planes; cada plan contiene detalles de fases y se vincula a predicciones mediante una tabla puente `Plan_Prediccion(plan_id, prediccion_id)`. Los cambios humanos se relacionan con usuario; los automáticos identifican el servicio.

| Restricción | Aplicación |
|---|---|
| Unicidad de catálogo | Código de grupo único por intersección y correo único de usuario |
| Idempotencia | UNIQUE(fuente, grupo_id, ventana_inicio, ventana_fin) en observaciones normalizadas |
| Dominios | Conteos y velocidades no negativos; coordenadas válidas; ventana_fin > ventana_inicio |
| Integridad referencial | No borrar catálogo referenciado por históricos; desactivar elementos |
| Un solo plan vigente | Índice único parcial por cruce para estado ACTIVO y transición transaccional |
| Control de concurrencia | Comparación de versión previa antes de aceptar/aplicar un plan |
| Consistencia de ciclo | Suma de detalles y exclusiones validada por controlador y prueba transaccional; no asumir que un CHECK por fila valida toda la suma |
| Tiempo e índices | TIMESTAMPTZ en UTC; índice compuesto grupo_id/ventana_inicio y paginación |
| Retención | Conservar dataset académico versionado; depurar telemetría de alta frecuencia y resultados redundantes según configuración |
| Auditoría | Usuario de aplicación sin permisos de actualización/borrado de bitácora; no registrar contraseñas, tokens o secretos |

### 3.6. Arquitectura propuesta

Se propone una arquitectura pequeña de servicios: **Backend API, servicio de IA y dashboard**, con un trabajador del simulador y una base PostgreSQL. La separación permite sustituir el modelo o la interfaz sin modificar la máquina de estados. Para cuatro personas se evita crear un servicio independiente por entidad o intersección.

| Componente | Responsabilidad | Tecnología | Responsable |
|---|---|---|---|
| Backend API | Acceso, catálogo, consulta, validación, auditoría y solicitudes de plan | FastAPI | LB |
| Servicio IA | Preprocesamiento e inferencia con modelo promovido; sin autoridad para aplicar fases | Python + scikit-learn + FastAPI interno | IA |
| Trabajador de control/simulación | Reloj, estados, capacidad de descarga, aplicación y fallback | Módulo Python del backend, proceso único dedicado | LB + IA |
| Dashboard | Estado, comparativas, alertas e intervención | Streamlit | FE |
| Ingesta/adaptadores | Contrato de datos; generador obligatorio y Waze opcional | Python | IA + LB |
| Persistencia | Históricos, configuración, predicciones, planes y auditoría | PostgreSQL | LB |
| Verificación/operación | CI, pruebas, métricas, respaldo y manuales | pytest y herramientas de entorno | QA |

**Flujo de información.** El generador entrega observaciones al backend; este valida y persiste. El trabajador, antes de un ciclo, solicita inferencia al servicio IA usando datos vigentes; calcula un plan, lo valida y registra. En el límite de ciclo, el único trabajador autorizado aplica el plan y confirma el estado. El dashboard consulta al backend; nunca cambia directamente la BD ni el modelo.

| Decisión arquitectónica | Justificación y manejo de fallas |
|---|---|
| REST/JSON y contratos versionados | Facilita pruebas y sustitución de componentes; esquemas y errores consistentes |
| IA como servicio interno sin acceso público | El backend conserva la autorización; timeout de 2 s y fallback ante error |
| Un único escritor de estado por intersección | Evita dobles aplicaciones; bloqueo/arrendamiento y versión de plan en BD al ampliar réplicas |
| Trabajador independiente del servidor HTTP | Evita iniciar un simulador por cada worker de FastAPI |
| Reloj simulado diferenciado del real | Antigüedad y ciclos se calculan con tiempo simulado; latencia informática con reloj real |
| Aplicación transaccional y confirmación | El estado PROPUESTO/PENDIENTE no se presenta como APLICADO |
| Fallback local en memoria | IA o BD pueden fallar sin producir cambios de fase arbitrarios; no se aceptan nuevos cambios sin auditoría |
| Entrenamiento fuera de línea | Evita competir con inferencia y cambiar silenciosamente el comportamiento |
| Despliegue local con Compose | Reduce carga operativa; autenticación y aislamiento de red para servicios internos |

#### 3.6.1. Contratos previstos para Fase 2

Esta tabla especifica interfaces, sin incluir código de implementación.

| Método y ruta | Entrada | Salida o comportamiento |
|---|---|---|
| GET /intersections | Filtros y paginación | Catálogo de cruces/grupos y versión de configuración |
| GET /traffic_data | interseccion, grupo y rango opcional | Observaciones con unidades, origen y antigüedad |
| POST /predict_light | Cruce, versión previa y referencia a datos/ventana | Pronóstico y propuesta válida con ID, verdes, rojos derivados, modelo y modo; no aplica por sí sola |
| POST /traffic_records | Lote normalizado y clave idempotente | Resultado individual aceptado/duplicado/rechazado |
| POST /plans/{id}/apply | ID, versión y ciclo objetivo | Solicitud autenticada de aplicación al simulador; confirmación diferida |
| POST /manual_override | Plan validable, motivo y vigencia | Intervención pendiente o rechazo |
| GET /health | — | Estado mínimo; detalle interno separado de la consulta pública |

Errores previstos: 401 sin autenticación; 403 sin permiso; 404 recurso desconocido; 409 conflicto de versión; 422 entrada inválida; 503 cuando no puede ofrecerse una operación requerida. Si la predicción falla pero existe fallback válido, la respuesta de recomendación podrá devolver ese plan con `modo=degradado` y la causa explícita. El cliente no decidirá ignorar las reglas ni enviará un tiempo para ser aceptado sin validación.

### 3.7. Plan de pruebas

#### 3.7.1. Estrategia, niveles y responsables

Se probarán reglas de dominio antes de la integración; después, contratos, persistencia, escenarios completos y aceptación. Los datos de pruebas no compartirán el entorno de entrenamiento ni los secretos de operación.

| ID | Nivel/tipo | Prueba y resultado esperado | Responsable |
|---|---|---|---|
| P-01 | Unidad | Esquemas, permisos, errores y lógica de API; entradas inválidas rechazadas | LB, revisa QA |
| P-02 | Unidad/datos | Generador reproducible, unidades, valores y ventanas; semillas producen llegadas esperadas | IA, revisa QA |
| P-03 | Integración | API–BD: unicidad, transacciones, rollback, filtros y paginación; ningún falso éxito | LB + QA |
| P-04 | Unidad/propiedades | Miles de combinaciones de demandas y planes previos; ciclo=120, verdes 20–60, suma=80, incompatibilidad imposible | LB + QA |
| P-05 | Validación ML/experimento | Cortes temporales, purga, referencia, semillas inéditas y comparación pareada | IA + QA |
| P-06 | Sistema/fallas | Caída de IA/fuente, datos viejos, intervención vencida y solicitudes simultáneas; fallback y único plan aplicado | QA |
| P-07 | Sistema extremo a extremo | Generar → registrar → predecir → aplicar → observar → exportar; estados y metadatos coherentes | QA + FE |
| P-08 | Seguridad | Intentos sin permiso, acceso a otro recurso, entrada maliciosa, secretos y CSV; acceso bloqueado y salida neutralizada | LB + QA |
| P-09 | Recuperación | Restaurar respaldo y reiniciar trabajador; RPO/RTO comprobados y sin asumir color no confirmado | QA + LB |
| P-10 | Aceptación Alpha/Beta | Tareas del administrador y revisión del representante académico; satisfacción de criterios funcionales | QA + FE |
| P-11 | Integración/modelos | Promoción, hash de artefacto, reversión y auditoría; toda predicción identifica su modelo | IA + LB + QA |
| P-12 | Rendimiento/carga | Perfiles de 5 y 50 cruces, 10 usuarios; p95, errores y recursos medidos, sin pérdida de registros aceptados | QA + LB |
| P-13 | Modificabilidad | Cambiar parámetros y fuente mediante configuración/adaptador; ejecutar regresión del controlador sin modificarlo | FE + IA + QA |

#### 3.7.2. Casos de prueba representativos

| Caso | Condición o estímulo | Resultado esperado |
|---|---|---|
| CP-01 | Demandas iguales y plan anterior 40/40 | Propuesta 40/40; ciclo completo de 120 s |
| CP-02 | Demandas 30/10 y anterior 40/40 | Reparto inicial 60/20; final limitado 45/35 |
| CP-03 | Demandas cero | 40/40; sin división por cero |
| CP-04 | Llegadas negativas o número no finito | Rechazo 422; ningún plan aplicado |
| CP-05 | Dato con antigüedad > 120 s | Plan fijo para siguiente ciclo y alerta visible |
| CP-06 | Timeout de IA | Fallback registrado; simulación continúa con secuencia válida |
| CP-07 | Reenvío de lote | No se duplica la observación |
| CP-08 | Dos solicitudes con versión previa idéntica | Solo una modificación aceptada; la otra recibe conflicto |
| CP-09 | Manual intenta omitir fase peatonal | Rechazo aunque provenga de un administrador |
| CP-10 | Dashboard pierde comunicación | Estado desactualizado/desconocido; no simula confirmación |
| CP-11 | Modelo no supera persistencia | No se promueve; conserva operación con plan fijo y reporte negativo |
| CP-12 | Demanda superior a capacidad | Se registra acumulación sin inventar salidas ni violar fases |

#### 3.7.3. Alpha y Beta

| Etapa | Participantes y entorno | Criterios de salida |
|---|---|---|
| Alpha | Cuatro integrantes, entorno local controlado, posterior al cierre de L y M | RF obligatorios verificados; sin defectos críticos; fallas y regresión ejecutadas |
| Beta | Cinco evaluadores académicos en un laboratorio o instancia aislada, incluyendo un administrador representativo | Criterio de usabilidad RNF-07; observaciones clasificadas; acta de aceptación y limitaciones |

Los evaluadores Beta no se agregan al equipo de desarrollo. Su disponibilidad deberá confirmarse al planear N. Ni Alpha ni Beta implican pruebas con tráfico real.

**Entrada a aceptación:** integración estable, datos y modelos identificados, resultados de pruebas disponibles y manual preliminar. **Salida:** cero defectos de severidad crítica o alta abiertos; todos los RF obligatorios y restricciones aprobados; requisitos deseables pendientes identificados; respaldo y reversión demostrados; informe experimental entregado con resultados positivos o negativos.

Un defecto crítico permite conflicto de fases, pérdida silenciosa de integridad o acceso administrativo indebido. Un defecto alto impide una función obligatoria sin alternativa aceptable. QA registra severidad, evidencia y regresión; la corrección debe ser revisada por otra persona.

### 3.8. Entregables y criterios de cierre

| Entregable previsto | Responsable principal | Criterio de cierre |
|---|---|---|
| Documento técnico y trazabilidad | LB + QA | Versionado y revisado por el representante académico |
| Generador y diccionario | IA | Semillas, unidades, escenarios y limitaciones identificados |
| BD y contratos | LB | Migraciones reproducibles e integridad verificada |
| Modelo y ficha de evaluación | IA | Artefacto versionado, métricas sin fuga y decisión de promoción |
| API, controlador y simulador | LB + IA | Planes aplicados una vez, invariantes y fallback comprobados |
| Dashboard | FE | Estado, antigüedad, modo e intervención comprensibles |
| Pruebas e informe experimental | QA + IA | Evidencias reproducibles y comparación con plan fijo |
| Manuales y transferencia | QA + equipo | Instalación, operación, recuperación, mantenimiento y retiro documentados |

**Decisión de Fase 1:** existe una propuesta técnicamente consistente para un prototipo académico. El paso siguiente será construir y verificar los artefactos de Fase 2. La entrega actual no contiene implementación, métricas observadas ni afirmaciones de mejora real.

## 4. Referencias y base de la información

Consulta de fuentes públicas: **31 de octubre de 2026**. Las referencias sustentan identificación de estándares, metodologías y características de fuentes de datos. Los requisitos, arquitectura, tiempos, tarifas, puntuaciones de riesgo y metas experimentales son propuestas propias de este proyecto.

| ID | Fuente primaria | Uso en el documento |
|---|---|---|
| R1 | [ISO/IEC/IEEE 12207:2026 — ISO](https://www.iso.org/standard/90219.html) | Edición vigente y alcance general del ciclo de vida |
| R2 | [ISO/IEC/IEEE 12207:2017 — ISO](https://www.iso.org/standard/63712.html) | Estado sustituido y referencia histórica |
| R3 | [Waze Data Feed specifications — Waze Partners Help](https://support.google.com/waze/partners/answer/13458165?hl=en) | Acceso para socios, GeoRSS y naturaleza de los datos |
| R4 | [Partner data feeds — Google for Developers](https://developers.google.com/waze/data-feed/overview) | Diferenciar envío de incidentes a Waze de consulta del feed |
| R5 | [The Scrum Guide, 2020 — Schwaber y Sutherland](https://scrumguides.org/scrum-guide.html) | Responsabilidades, eventos e incrementos |
| R6 | [IBM SPSS Modeler CRISP-DM Guide](https://www.ibm.com/docs/en/SS3RA7_18.5.0/pdf/ModelerCRISPDM.pdf) | Fases y naturaleza iterativa del proceso analítico |
| R7 | [Common pitfalls and recommended practices — scikit-learn](https://scikit-learn.org/stable/common_pitfalls.html) | Preprocesamiento consistente y prevención de fuga |
| R8 | [TimeSeriesSplit — scikit-learn](https://scikit-learn.org/stable/modules/generated/sklearn.model_selection.TimeSeriesSplit.html) | Separación temporal y parámetro de separación |
| R9 | [ISO/IEC 42001:2023 — ISO](https://www.iso.org/standard/42001) | Sistema de gestión de IA y referencia complementaria a riesgo |
| R10 | [ISO/IEC 5338:2023 — ISO, vista pública](https://www.iso.org/obp/ui#iso:std:iso-iec:5338:ed-1:v1:en) | Ciclo de vida de IA y relación con ingeniería de software |
| R11 | [Urbanek et al., 2015, Prediction accuracy measurements as a fitness function for software effort estimation](https://link.springer.com/article/10.1186/s40064-015-1555-9) | Estimación UCP y necesidad de calibrar productividad |
| R12 | [ISO/IEC 23894:2023 — ISO](https://www.iso.org/es/contents/data/standard/07/73/77304.html) | Orientación para gestión de riesgos de IA |


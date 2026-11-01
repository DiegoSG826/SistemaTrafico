# REV_001 — Revisión de entrega académica y alcance Cuauhtémoc

**Actualización de entrega:** esta auditoría inicial se conserva como historial. Los apartados
documentales faltantes se desarrollaron en [la entrega académica integrada](../entrega_academica/LEEME.md),
con memoria, marco teórico, diagramas, diez CU, manual ilustrado, guiones, resultados, presentación
y video. La matriz MAT_002 y DOC_005 indican el estado actual; aceptación humana y metas de
latencia pendientes no se presentan como aprobadas.

Fecha: 1 de noviembre de 2026. Dictamen: **cumplimiento parcial** de la lista solicitada.
El código funcional de simulación y los documentos de Fases 1/2 existen; no equivalen todavía
a una memoria académica final organizada según todos los capítulos y anexos requeridos.

## CAM_001 — Cambio de alcance territorial

Título propuesto: **Sistema inteligente de gestión de semáforos simulados para la alcaldía
Cuauhtémoc, Ciudad de México**. Alcance ALC_001: cinco intersecciones sintéticas CUA_001 a
CUA_005, con accesos NS/EO y fase peatonal. El nombre de la alcaldía no acredita calibración
territorial, datos municipales ni cobertura de todos sus semáforos. El catálogo usa referencias
esquemáticas, sin inventar nombres de cruces reales o un inventario oficial.

Se sustituyó el catálogo inicial y el título del dashboard, se expone el ámbito en la API y
se agregó una tabla de verdes/amarillos/rojos del plan confirmado. Para instalaciones existentes:

```text
python -m scripts.select_cuauhtemoc
python -m scripts.run_local
```

Detener antes las ejecuciones anteriores. El selector prepara `data/cuauhtemoc.db`, conserva
`data/traffic.db` y cambia únicamente la URL del perfil SQLite estándar en `.env`. No reescribe
históricos para atribuirlos a otro territorio. Con PostgreSQL o una URL personalizada se debe
preparar una BD nueva explícitamente. Las extensiones administrativas de catálogo siguen siendo
sintéticas dentro del mismo estudio; no hay geocerca oficial ni soporte multialcaldía.

Las Fases 1/2 y los reportes previos se conservan como evidencia de la línea base anterior.
Esta adenda prevalece en el alcance territorial. El entrenamiento y los resultados anteriores
son sintéticos generales: **no prueban una reducción de tráfico real en Cuauhtémoc**. La nueva
delimitación requiere nueva revisión de objetivos, riesgos, catálogo y validación académica.

## EXP_001 — Qué gestiona el sistema

1. Genera o recibe observaciones por minuto: llegadas, velocidad y clima.
2. El modelo estima la demanda de los próximos cinco minutos.
3. El controlador asigna verdes según esa demanda, preservando sus restricciones.
4. El trabajador aplica el plan al siguiente inicio de ciclo y simula colores, colas y salidas.
5. El dashboard presenta lo confirmado; pedir una predicción no aplica por sí solo un plan.

Ejemplo EXP_002: demanda prevista NS=30 y EO=10 veh/min, con plan anterior 40/40. La proporción
sin suavizado sería 60/20, pero el límite de cambio automático de cinco segundos produce
45/35 en el siguiente ciclo. Los rojos respectivos son 72/82 s; amarillos 3 s. El ciclo total
con despejes y peatones es 120 s. Si la demanda persiste, el controlador puede acercarse
gradualmente a 60/20 en ciclos sucesivos. No se promete un tiempo matemáticamente óptimo.

En automático y con modelo promovido/datos vigentes, adapta. En manual usa la intervención
validada. En degradado usa 40/40 por ausencia/falla de fuente o IA. Es un gestor funcional de
**semáforos simulados**, sin conexión con controladores físicos, aforos oficiales ni Waze real.
La decisión se basa en demanda pronosticada; las colas se monitorizan, pero no entran como
variable directa en la fórmula proporcional actual. Tampoco se coordinan corredores entre cruces.

Evidencia REV_TEC_001 del cambio: diez pruebas dirigidas de catálogo, API territorial,
dashboard y controlador aprobadas. Se detectó un manifiesto local `active.json` con estado
`promoted`; ese estado indica selección local del modelo, no sustituye comprobar disponibilidad
del servicio IA, vigencia de datos ni revisión humana. El reporte anterior de 38 pruebas se
conserva fechado como evidencia de la línea base; no se presenta como una nueva ejecución completa.

## MAT_001 — Comprobación elemento por elemento

«Existe» significa contenido o artefacto localizado, no aprobación del docente. «Parcial» implica
completar forma, profundidad, integración o evidencia. Los identificadores REV_* son los de
esta auditoría, no reemplazan los identificadores RF/RNF/CU de los documentos originales.

| ID | Apartado solicitado | Estado | Evidencia y faltante |
|---|---|---|---|
| REV_201 | Cap. 2: descripción del sistema | Existe | Fase 1 §1.1; actualizar memoria a Cuauhtémoc con CAM_001 |
| REV_202 | Objetivo general/específicos | Parcial | Fase 1 §1.2–1.3; OE-01..07; falta objetivo general con ID y alcance nuevo consolidado |
| REV_203 | Metodología y elementos por etapa | Parcial | Scrum, CRISP-DM y adaptación 12207 en Fases 1/2; falta memoria de ejecución por sprint/etapa |
| REV_204 | Terminología del negocio | Existe | Fase 1 §1.8; falta asignar ID individual a cada término |
| REV_301 | Cap. 3: elementos teóricos | Falta capítulo integrado | Hay fundamentos dispersos; desarrollar tráfico, flujo/cola/capacidad, control y simulación con fuentes |
| REV_302 | Teoría del elemento IA | Parcial | Random Forest, atributos, cortes y métricas descritos; falta marco teórico completo con regresión, árboles, ensamble y generalización |
| REV_401 | Cap. 4: actores | Parcial | Fase 1 §2.1; faltan ACT_* y trazabilidad individual |
| REV_402 | Requerimientos funcionales | Existe | RF-01..16 y matriz de verificación; varios cierres de aceptación pendientes |
| REV_403 | Requerimientos no funcionales | Existe | RNF-01..12; rendimiento, recuperación y evaluación humana aún no acreditados |
| REV_404 | Requerimientos técnicos | Existe | RT-01..09 y stack implementado |
| REV_405 | Reglas de negocio | Existe | RB-01..13, controlador y pruebas |
| REV_406 | Gantt | Falta diagrama | Hay sprints y actividades; no un Gantt formal |
| REV_407 | PERT | Parcial | Actividades A..O, dependencias, holguras y ruta calculadas; falta diagrama de red formal |
| REV_408 | Factibilidad técnica | Existe | Fase 1 §2.8.1; supuestos y recursos |
| REV_409 | Factibilidad operativa | Existe | Fase 1 §2.8.2; no constituye estudio de operación municipal |
| REV_410 | Factibilidad económica | Existe | Fase 1 §2.8.3; presupuesto hipotético, no cotización |
| REV_411 | Análisis de riesgo | Existe | R-01..08, exposición y tratamientos; revisar por cambio CAM_001 |
| REV_412 | Normas a seguir | Parcial | Fase 1 §2.11 y Fase 2; alineación propuesta, sin conformidad formal por cláusula |
| REV_501 | Cap. 5: diagrama de casos de uso | Falta diagrama formal | Hay descripción textual y listado CU-01..10; no figura UML |
| REV_502 | Especificaciones de casos de uso | Parcial | CU-03 detallado; faltan especificaciones completas de los demás |
| REV_503 | Diagrama BD | Falta diagrama ER | Existen SQL, entidades y relaciones textuales |
| REV_504 | Arquitectura | Parcial | Componentes, decisiones y figura Mermaid de Fase 2; faltan IDs y figuras integradas de despliegue/datos |
| REV_601 | Desarrollo | Existe | Código de backend, IA, simulador, frontend y BD; documentado en Fase 2 |
| REV_701 | Pruebas a realizar | Existe | P-01..13, tipos, procedimientos y pendientes en PRUEBAS_TRAZABILIDAD.md |
| REV_702 | Resultados de pruebas | Parcial | JUnit, cobertura, humo y experimento; no están cerradas carga, restauración, Alpha/Beta ni revisión humana |
| REV_801 | Glosarios anexos | Parcial | Terminología existente; faltan anexo unificado e IDs por entrada |
| REV_802 | Referencias anexas | Parcial | R1..R12 y enlaces de Fase 2; unificar formato, IDs y citas del marco teórico |
| REV_901 | Implementación final | Parcial | Prototipo ejecutable en simulación; no aceptación académica final ni infraestructura real |
| REV_902 | Manual de usuario/instalación | Parcial | README y OPERACION.md; ampliar manual de usuario ilustrado por tarea y mensajes de error |
| REV_903 | Documento de pruebas/guiones/tipos | Existe | PRUEBAS_TRAZABILIDAD.md; ampliar guiones manuales con ID, pasos y resultados obtenidos |
| REV_904 | Presentación del sistema | Falta | No hay presentación PPTX ni equivalente entregada |
| REV_905 | Video de presentación | Falta | No hay video grabado/editado ni evidencia audiovisual entregada |
| REV_906 | NOTA 1: todos los elementos con ID | Parcial | RF/RNF/RT/RB/CU/OE/P/R tienen IDs; faltan actores, figuras, términos, objetivos y artefactos individuales |
| REV_907 | NOTA 2: especificar pruebas a realizar | Existe | P-01..13 separa pruebas previstas, automatizadas y pendientes |

## IDX_001 — Numeración recomendada e identificadores

La lista original repite «Capítulo 5». Propuesta para confirmar con el docente:
2 Descripción general; 3 Marco teórico; 4 Análisis/diseño; 5 Casos de uso/modelado;
6 Desarrollo; 7 Pruebas; anexos. Esta propuesta no cambia automáticamente una plantilla institucional.

Convención propuesta para la memoria final: `OG_001`, `OE_001`, `ACT_001`, `RF_001`,
`RNF_001`, `RT_001`, `RB_001`, `CU_001`, `RIE_001`, `PRU_001`, `FIG_001`, `TAB_001`,
`TER_001`, `REF_001` y `ENT_001`. Mantener una tabla de alias con los IDs actuales:
por ejemplo CU-01 ↔ CU_001 y RF-01 ↔ RF_001. No cambiar IDs históricos sin actualizar
referencias, pruebas, requisitos y matriz. Las secciones/tablas de la auditoría no implican
que los elementos faltantes ya estén desarrollados.

## SIG_001 — Trabajo que falta para declarar entrega completa

Consolidar la memoria con alcance Cuauhtémoc, marco teórico, IDs uniformes, Gantt/red PERT,
UML de casos de uso, ER y especificaciones faltantes; completar aceptación y manual ilustrado;
crear presentación y grabar video usando una ejecución verificada. No certificar resultados,
revisiones humanas ni datos reales que no se hayan obtenido.

Referencia territorial REF_TERR_001: [Alcaldía Cuauhtémoc — sitio oficial](https://cuauhtemoc.cdmx.gob.mx/inicio/conocenos/).
Este referente contextual no valida las coordenadas ni los parámetros sintéticos del catálogo.

# ENT_009 Entrega académica de Cuauhtémoc

**Versión documental 1.0 · 1 de noviembre de 2026.** Proyecto de cuatro integrantes.
La memoria, anexos, diagramas y guiones completan los apartados solicitados para un prototipo
de **semáforos simulados**. Los resultados de rendimiento y aceptación se presentan con su
estado real; entregar la documentación no convierte un criterio fallido en aprobado.

## ENT_010 Archivos para revisar

| ID | Archivo | Contenido |
|---|---|---|
| DOC_001 | DOC_001_Memoria.pdf / .docx / .md | Capítulos 2–7, marco teórico, análisis, diseño, desarrollo, resultados y anexos |
| DOC_002 | DOC_002_Casos_de_uso.pdf / .docx / .md | Diez especificaciones, actores, flujos, alternativas y criterios |
| DOC_003 | DOC_003_Manual.pdf / .docx / .md | Instalación y operación ilustradas con capturas reales del prototipo |
| DOC_004 | DOC_004_Pruebas.pdf / .docx / .md | Trece familias de pruebas, guiones y formatos Alpha/Beta |
| DOC_005 | DOC_005_Resultados.pdf / .docx / .md | Batería, regresión, dos ensayos de carga, restauración y limitaciones |
| PRE_001 | PRE_001_Presentacion.pptx | 14 diapositivas editables con notas y gráficos vinculados a datos incrustados |
| VID_001 | VID_001_Presentacion.mp4 | Video explicativo sin locución, con subtítulos en español y demostración de un ciclo |
| VID_002 | VID_001_Subtitulos.srt | Subtítulos externos, además de los incrustados en el MP4 |
| FIG_001..006 | figuras/*.png y .svg | Gantt, PERT, UML de casos, ER, arquitectura y despliegue |
| FIG_007..010 | figuras/*.png | Acceso, monitor, intervención y auditoría de una instancia temporal |
| REG_001 | MANIFIESTO.json | Archivos, hashes y estado de la entrega |

Las imágenes del dashboard utilizan una BD de prueba y credenciales efímeras. No muestran
aforos, semáforos físicos ni contraseñas. La demostración animada del video ejecuta las reglas
del controlador con 45/35; no se presenta como grabación de una calle.

## MAT_002 Cobertura de la lista académica

| ID | Elemento solicitado | Entregable y sección |
|---|---|---|
| MAT_201 | Descripción del sistema | DOC_001 DES_001 |
| MAT_202 | Objetivo general y específicos | DOC_001 OG_001 y OE_001..007 |
| MAT_203 | Metodología por etapa y realización | DOC_001 MET_001..008 y SPR_001..005; sin actas ficticias |
| MAT_204 | Terminología del negocio | DOC_001 TER_001..020 |
| MAT_301 | Elementos teóricos | DOC_001 TEOR_001, TEOR_002 y TEOR_007 |
| MAT_302 | Aspectos teóricos de IA | DOC_001 TEOR_003..006 |
| MAT_401 | Actores | DOC_001 ACT_001..003 e INT_001..003 |
| MAT_402 | Requerimientos funcionales | DOC_001 REQ_001; RF_001..016 |
| MAT_403 | Requerimientos no funcionales | DOC_001 REQ_002; RNF_001..012 |
| MAT_404 | Requerimientos técnicos | DOC_001 REQ_003; RT_001..009 |
| MAT_405 | Reglas de negocio | DOC_001 NEG_002; RB_001..013 |
| MAT_406 | Gantt y PERT | DOC_001 CAL_001; FIG_001 y FIG_002; ACTIV_001..015 |
| MAT_407 | Factibilidad técnica | DOC_001 FACT_001 |
| MAT_408 | Factibilidad operativa | DOC_001 FACT_002 |
| MAT_409 | Factibilidad económica | DOC_001 FACT_003 |
| MAT_410 | Riesgos | DOC_001 RIESGOS_001; RIE_001..009 |
| MAT_411 | Normas a seguir | DOC_001 NOR_001..008; alineación sin certificación |
| MAT_501 | Diagrama de casos de uso | DOC_001 MOD_001; FIG_003 |
| MAT_502 | Especificación de casos de uso | DOC_002 CU_001..010 |
| MAT_503 | Diagrama BD | DOC_001 MOD_002; FIG_004 y ENTBD_001..014 |
| MAT_504 | Arquitectura | DOC_001 MOD_003; FIG_005 y FIG_006 |
| MAT_601 | Desarrollo | DOC_001 DEV_001..004 y código del repositorio |
| MAT_701 | Pruebas a realizar | DOC_004 PRU_001..013; tipo, datos, pasos y criterio |
| MAT_702 | Resultados de pruebas | DOC_005 RES_001..006 y reports/academico |
| MAT_801 | Glosarios | DOC_001 NEG_001 y ANX_A |
| MAT_802 | Referencias | DOC_001 ANX_B; REF_001..010 |
| MAT_901 | Implementación final | Código empaquetado, prototipo de simulación; aceptación pendiente |
| MAT_902 | Manual de usuario e instalación | DOC_003 MAN_001..012 y ERR_001..010 |
| MAT_903 | Documento de pruebas y guiones | DOC_004 PLAN_001..002, GUI_001..013 y actas |
| MAT_904 | Presentación | PRE_001 PPTX y guion |
| MAT_905 | Video | VID_001 MP4, ficha y SRT |
| MAT_906 | Identificadores para elementos | Familias OG/OE/ACT/RF/RNF/RT/RB/CU/PRU/FIG/TAB/TER/GLO/REF/DOC/ENT |
| MAT_907 | Pruebas previstas explícitas | DOC_004 y distinción entre resultado esperado, obtenido y pendiente |

La numeración repetida de «Capítulo 5» se resolvió usando capítulo 6 para Desarrollo y 7 para
Pruebas. La tabla de alias conserva los IDs históricos RF-01/CU-01/P-01 frente a RF_001/CU_001/PRU_001.

## ACEPT_001 Límites de aceptación

La batería actual aprobó **42 pruebas**, incluida PostgreSQL real. Una regresión intermedia
aprobó 25; no se suman ambas como pruebas diferentes. El controlador y las validaciones
mantienen cobertura de ramas de 90% y 100%. La restauración de laboratorio conservó conteos.

Las consultas cumplieron el umbral de 500 ms p95 en la segunda carga; las **predicciones no
cumplieron 1 s p95**, y hubo errores bajo carga. DOC_005 conserva ambos ensayos y la corrección
parcial realizada. RNF_001/RNF_002 no se declaran aceptados. Los ensayos compartieron equipo
con generación documental, por lo que se requiere perfilar y repetir en entorno controlado.

Permanecen fuera de una conclusión automática: evaluación Alpha/Beta con cinco personas,
firmas/revisión del equipo, aceptación del docente, revisión de dependencias/TLS, reversión
operativa y RTO integral. Hay formatos e instrucciones completos para ejecutar esas actividades.
Docker no estaba instalado y no se afirma haber ejecutado Compose. Los resultados sintéticos
no constituyen calibración territorial ni autorización para operación vial real.

## REP_001 Uso y regeneración

Desde la raíz del código: crear .venv, instalar requirements.lock, ejecutar scripts.configure,
scripts.select_cuauhtemoc y scripts.run_local. Mantener la terminal abierta. Ver DOC_003.
El paquete excluye .env, contraseñas, bases de usuario, .git y datasets grandes. Si no se copia
un modelo promovido, inicia en degradado 40/40; entrenar/evaluar/promover según el manual.

Los scripts build_academic_content, build_academic_support y academic_diagrams regeneran
Markdown y figuras. export_academic_documents utiliza el runtime documental de Codex;
build_academic_deck utiliza Artifact Tool del runtime. Esas rutas de autoría deben resolverse
en cada equipo con load_workspace_dependencies; no son requisitos para abrir los entregables.
Para regenerar MP4, instalar requirements-academic.txt además del entorno de aplicación.

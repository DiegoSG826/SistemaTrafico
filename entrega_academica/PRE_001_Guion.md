# PRE_001 Guion de presentación y narración

## DIA_001 Gestión inteligente de semáforos en Cuauhtémoc

Presentamos un gestor de semáforos simulados para Cuauhtémoc. La IA anticipa llegadas; el controlador reparte verde y el simulador aplica el plan. No controla semáforos físicos ni usa aforos oficiales.

## DIA_002 Del dato al plan confirmado

El generador registra observaciones por minuto. La API consulta la IA, valida tiempos y guarda una propuesta. Solo el trabajador aplica al inicio del ciclo. El dashboard presenta estados confirmados. Fuente: memoria DOC_001, COMP_001 a COMP_008.

## DIA_003 Datos sintéticos y evaluación temporal

El dataset incluye horario, día, clima, historial y velocidad. La etiqueta es el promedio de llegadas de cinco minutos futuros. El pipeline separa entrenamiento y prueba. Los datos no fueron calibrados con Cuauhtémoc. Fuente: reports/model_evaluation.json y REF_005.

## DIA_004 Más demanda recibe más verde

Con demanda prevista de treinta vehículos por minuto en norte sur y diez en este oeste, el objetivo proporcional es sesenta veinte. Desde cuarenta cuarenta se limita a cuarenta y cinco treinta y cinco. El rojo se deriva del ciclo. Este es un ejemplo de las reglas, no un resultado medido de calle.

## DIA_005 Las restricciones siempre prevalecen

El ciclo conserva exclusión de movimientos y una oportunidad peatonal. Automático limita la variación. Si faltan datos o IA, prevalece un plan fijo cuarenta cuarenta. Manual tiene motivo y caducidad. Los tiempos son didácticos, no reglamentarios.

## DIA_006 Casos de uso y trazabilidad

El diagrama UML y las diez especificaciones están en DOC_002 y FIG_003. Los actores tienen identificadores ACT y los casos CU. La nota de identificación de todos los elementos se materializa también en requisitos, tablas y figuras.

## DIA_007 Persistencia que protege la decisión

El esquema SQL contiene intersecciones, grupos, observaciones, predicciones, modelos y planes. Un índice parcial impide dos activos y los triggers comprueban todas las fases de un plan al confirmar. El modelo entidad relación completo está en FIG_004.

## DIA_008 Plan de trabajo con cuatro integrantes

La línea base estima mil doscientas ochenta horas persona y diez semanas. PERT calcula cuarenta y cinco días hábiles más reserva. Es planificación, no un registro de horas ejecutadas. Fuentes: reports/pert.json y DOC_001 CAL_001.

## DIA_009 El monitor muestra lo confirmado

Esta captura procede de una instancia real temporal del dashboard con datos sintéticos y credenciales efímeras. Permite observar demanda, colas y tiempos, y distinguir una solicitud pendiente de un plan activo.

## DIA_010 El modelo supera la persistencia

En la prueba sintética reservada, el error absoluto medio fue uno punto diecinueve vehículos por minuto, frente a uno punto cuarenta y cinco de persistencia. Esto evalúa predicción; el control requiere otro experimento. Fuente: reports/model_evaluation.json.

## DIA_011 El beneficio depende del escenario

La evaluación usó cincuenta pares con las mismas llegadas. En escenarios no sobresaturados la reducción media de demora fue veintinueve punto treinta y siete por ciento. El resultado no es uniforme ni representa una medición en calles de Cuauhtémoc. Fuente: reports/experiment.json.

## DIA_012 Pruebas y resultados reproducibles

La batería actual aprobó cuarenta y dos pruebas, incluyendo PostgreSQL real. Se entregan guiones de trece familias y resultados de carga y restauración. La latencia de predicción aún no cumple la meta y permanece reportada. La evaluación humana no se sustituye por pruebas automáticas. Fuentes: reports/academico y DOC_004/DOC_005.

## DIA_013 Demostración en tres pasos

El manual contiene instalación, acceso, interpretación de modos, intervención, exportación y solución de errores. El lanzador requiere permanecer abierto y evita dos ejecuciones sobre los mismos puertos. No se muestran contraseñas en el material audiovisual.

## DIA_014 Entrega académica y límites

La entrega incluye memoria completa, casos de uso, manual, documento de pruebas, figuras, presentación y video. Sigue siendo un prototipo académico de simulación. La aceptación del docente, pruebas con personas, calibración real y despliegue municipal requieren trabajo y decisiones externas.
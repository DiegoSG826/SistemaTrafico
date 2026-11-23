# PRE_001 Guion de presentación y narración

## DIA_001 Gestión inteligente de semáforos en Cuauhtémoc

Presentamos un gestor de semáforos simulados para Cuauhtémoc. La IA anticipa llegadas; el controlador reparte verde y el simulador aplica el plan. No controla semáforos físicos ni usa aforos oficiales.

## DIA_002 Control simulado y tráfico real

El generador aporta observaciones al controlador simulado. El trabajador aplica los planes al inicio del ciclo. Para mostrar tráfico real, FastAPI consulta TomTom Traffic API por separado. Fuente: DOC_001, DEV_005 y FIG_005.

## DIA_003 Datos sintéticos y evaluación temporal

El dataset incluye horario, día, clima, historial y velocidad. La etiqueta es el promedio de llegadas de cinco minutos futuros. El pipeline separa entrenamiento y prueba. Los datos no fueron calibrados con Cuauhtémoc. Fuente: reports/model_evaluation.json y REF_005.

## DIA_004 Más demanda recibe más verde

Con demanda prevista de treinta vehículos por minuto en norte sur y diez en este oeste, el objetivo proporcional es sesenta veinte. Desde cuarenta cuarenta se limita a cuarenta y cinco treinta y cinco. El rojo se deriva del ciclo. Este es un ejemplo de las reglas, no un resultado medido de calle.

## DIA_005 Las restricciones siempre prevalecen

El ciclo conserva exclusión de movimientos y una oportunidad peatonal. Automático limita la variación. Si faltan datos o IA, prevalece un plan fijo cuarenta cuarenta. Manual tiene motivo y caducidad. Los tiempos son didácticos, no reglamentarios.

## DIA_006 Casos de uso y trazabilidad

DOC_002 y FIG_003 describen once casos y cinco actores. El lector consulta, supervisa y exporta. En CU_011, el backend solicita a TomTom el tramo cercano y muestra el resultado al usuario autenticado.

## DIA_007 Persistencia que protege la decisión

El esquema SQL contiene intersecciones, grupos, observaciones, predicciones, modelos y planes. Un índice parcial impide dos activos y los triggers comprueban todas las fases de un plan al confirmar. El modelo entidad relación completo está en FIG_004.

## DIA_008 Plan base y ampliación TomTom

El Gantt y PERT presentan dos órdenes de trabajo estimados. Git registra el mapa actualizado el dieciséis de noviembre y TomTom integrado el veintidós. Esas fechas acreditan hitos. Fuentes: reports/pert.json y DOC_001 CAL_001 y CAL_002.

## DIA_009 El monitor de simulación

La captura FIG_008 muestra la versión actual del dashboard en una instancia temporal. El mapa permite seleccionar un cruce y el monitor muestra la animación, las fases y los tiempos del plan.

## DIA_010 El modelo supera la persistencia

En la prueba sintética reservada, el error absoluto medio fue uno punto diecinueve vehículos por minuto, frente a uno punto cuarenta y cinco de persistencia. Esto evalúa predicción; el control requiere otro experimento. Fuente: reports/model_evaluation.json.

## DIA_011 El beneficio depende del escenario

La evaluación usó cincuenta pares con las mismas llegadas. En escenarios no sobresaturados la reducción media de demora fue veintinueve punto treinta y siete por ciento. El resultado no es uniforme ni representa una medición en calles de Cuauhtémoc. Fuente: reports/experiment.json.

## DIA_012 Pruebas y resultados reproducibles

La línea base incluyó PostgreSQL, carga y restauración. La verificación TomTom obtuvo datos para los cinco puntos y recorrió ambas vistas en Edge. En esa ejecución se omitieron las pruebas PostgreSQL por falta de una base de laboratorio. Fuentes: DOC_004 y DOC_005.

## DIA_013 Consulta de tráfico con TomTom

La captura FIG_011 muestra una consulta en vivo en la rama actual. El usuario elige un punto y puede pulsar Actualizar ahora. El backend conserva la clave de TomTom. Los planes semafóricos siguen usando las llegadas del simulador. Fuente: DOC_003 MAN_013.

## DIA_014 Entrega académica y límites

La entrega cubre la simulación y la consulta de tráfico real por tramo con TomTom. Las cifras de demora siguen siendo de un experimento sintético. La aceptación del docente, las pruebas con personas y la calibración territorial siguen pendientes.
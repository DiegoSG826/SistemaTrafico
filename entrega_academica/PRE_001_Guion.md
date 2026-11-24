# PRE_001 Guion de presentación y narración

## DIA_001 Gestión inteligente de semáforos en Cuauhtémoc

Presentamos un gestor de semáforos simulados para Cuauhtémoc. La IA anticipa llegadas; el controlador reparte verde y el simulador aplica el plan. No controla semáforos físicos ni usa aforos oficiales.

## DIA_002 Control simulado y tráfico real

La barra superior alterna entre Simulación y TomTom. El generador aporta observaciones al controlador simulado. FastAPI comparte las lecturas de TomTom entre el mapa y el comparador por ciento veinte segundos y aplica el presupuesto de consultas. Fuente: DOC_001 DEV_004 a DEV_006, FIG_005.

## DIA_003 Datos sintéticos y evaluación temporal

El dataset incluye horario, día, clima, historial y velocidad. La etiqueta es el promedio de llegadas de cinco minutos futuros. El pipeline separa entrenamiento y prueba. Los datos no fueron calibrados con Cuauhtémoc. Fuente: reports/model_evaluation.json y REF_005.

## DIA_004 Más demanda recibe más verde

Con demanda prevista de treinta vehículos por minuto en norte sur y diez en este oeste, el objetivo proporcional es sesenta veinte. Desde cuarenta cuarenta se limita a cuarenta y cinco treinta y cinco. El rojo se deriva del ciclo. Este es un ejemplo de las reglas, no un resultado medido de calle.

## DIA_005 Las restricciones siempre prevalecen

El ciclo conserva exclusión de movimientos y una oportunidad peatonal. Automático limita la variación. Si faltan datos o IA, prevalece un plan fijo cuarenta cuarenta. Manual tiene motivo y caducidad. Los tiempos son didácticos, no reglamentarios.

## DIA_006 Casos de uso y trazabilidad

DOC_002 y FIG_003 describen doce casos y cinco actores. CU_012 extiende la vista TomTom cuando el usuario pulsa Comparar puntos. Seleccionar una fila abre el tramo correspondiente en el mapa.

## DIA_007 Persistencia que protege la decisión

El esquema SQL contiene intersecciones, grupos, observaciones, predicciones, modelos y planes. Un índice parcial impide dos activos y los triggers comprueban todas las fases de un plan al confirmar. El modelo entidad relación completo está en FIG_004.

## DIA_008 Plan base y ampliación TomTom

El Gantt y PERT estiman ocho días para el visor y cinco para el comparador. La ruta crítica de la ampliación es P–Q–S–T–U–V–X. Git registra el comparador el veintitrés de noviembre. Fuentes: reports/pert.json y DOC_001 CAL_002.

## DIA_009 El monitor de simulación

FIG_008 muestra el tablero actual. El mapa y los indicadores siguen visibles al desplazarse por el panel derecho. En Monitor en vivo se ven la animación y los tiempos del plan. La pestaña Intervención y Modelo concentra las acciones administrativas.

## DIA_010 El modelo supera la persistencia

En la prueba sintética reservada, el error absoluto medio fue uno punto diecinueve vehículos por minuto, frente a uno punto cuarenta y cinco de persistencia. Esto evalúa predicción; el control requiere otro experimento. Fuente: reports/model_evaluation.json.

## DIA_011 El beneficio depende del escenario

La evaluación usó cincuenta pares con las mismas llegadas. En escenarios no sobresaturados la reducción media de demora fue veintinueve punto treinta y siete por ciento. El resultado no es uniforme ni representa una medición en calles de Cuauhtémoc. Fuente: reports/experiment.json.

## DIA_012 Pruebas del tablero y el comparador

La revisión actual aprobó cuarenta y siete pruebas. En el ensayo previo con proveedor simulado se registraron cinco llamadas en total al comparar, repetir y seleccionar un tramo. Las capturas en vivo pertenecen a una comprobación separada. Fuentes: DOC_004 PRU_015 y DOC_005 RES_009 y RES_010.

## DIA_013 Comparación de demoras con TomTom

FIG_012 muestra la comparación con datos en vivo. En Comparador y Auditoría, la tabla ordena por tiempo adicional y seleccionar una fila actualiza el mapa y los indicadores del tramo. El mapa y la tabla reutilizan lecturas por ciento veinte segundos y comparten el presupuesto de consultas. Fuente: DOC_003 MAN_014.

## DIA_014 Entrega académica y límites

La entrega cubre el simulador, el visor TomTom y el comparador. Los indicadores de FIG_012 corresponden al momento de la consulta. La evaluación del controlador procede de experimentos sintéticos. La aceptación del docente y la calibración territorial siguen pendientes.
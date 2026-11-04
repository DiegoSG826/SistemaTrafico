# DOC_005 Resultados de verificación y límites de aceptación

ENT_005 · 1 de noviembre de 2026. Se consolidan archivos reales; no se inventan resultados ausentes.

## RES_001 Batería automatizada actual

tests: **42**; failures: **0**; errors: **0**; skipped: **0**. Fuente: reports/academico/tests.xml.

Cobertura combinada en controlador/esquemas: **98.02%**. No es cobertura global de toda la aplicación.

- backend\app\controller.py: ramas 9/10.

- backend\app\schemas.py: ramas 10/10.

Regresión posterior de la corrección de concurrencia: **25 pruebas**, 0 fallas/errores. Es una ejecución independiente, no se suma a la batería completa anterior. Fuente: reports/academico/regression-concurrency.xml.

## RES_002 Carga real de laboratorio

Los dos perfiles se ejecutan simultáneamente en el mismo equipo; comparten CPU y PostgreSQL. Durante el ensayo también se generaron artefactos documentales, por lo que no es un benchmark de hardware aislado. Se recorren todos los cruces por usuario; no se demuestra coordinación vial. El conteo de ingesta comprueba entradas test aceptadas, mientras el trabajador continúa observaciones sintéticas.

### RES_CARGA_005 Perfil de 5 cruces

10 usuarios, 600 s, PostgreSQL 17.4. Consultas: 2213 con p95 43.11 ms; propuestas: 2191 con p95 3727.14 ms. Errores: 20; conflictos de versión registrados: 2.

Meta de latencia: **NO CUMPLE**. Entradas aceptadas/persistidas: 10/10. Preservación: True. Fuente: `reports/academico/load-5.json`. Un resultado negativo exige corrección/perfilado y repetición; no se redefine el umbral para aprobar.

### RES_CARGA_050 Perfil de 50 cruces

10 usuarios, 600 s, PostgreSQL 17.4. Consultas: 2107 con p95 115.02 ms; propuestas: 2092 con p95 3828.93 ms. Errores: 14; conflictos de versión registrados: 1.

Meta de latencia: **NO CUMPLE**. Entradas aceptadas/persistidas: 100/100. Preservación: True. Fuente: `reports/academico/load-50.json`. Un resultado negativo exige corrección/perfilado y repetición; no se redefine el umbral para aprobar.

### RES_006 Comparación con el ensayo inicial

El ensayo inicial no cumplió latencia de predicción y registró errores. Se conserva en reports/academico/ensayo-inicial. La corrección limita el modelo a un hilo por inferencia HTTP, precarga grupos para evitar consultas N+1 y usa FOR NO KEY UPDATE en el trabajador para permitir referencias FK concurrentes sin perder exclusión de escritores. No cambia las reglas semafóricas ni las predicciones del modelo. Se repitió el protocolo con bases nuevas; comparar ambos resultados, sin ocultar el negativo.

## RES_003 Respaldo y restauración

pg_dump: 0.89 s; pg_restore: 0.89 s. Comparación de conteos: **True**. Restauración menor de 30 min: True. RPO observado en fuente detenida: 0 s. Fuente: reports/academico/recovery.json.

Este ensayo verifica restauración de laboratorio, no política diaria ni RTO integral incluyendo reanudación y validación humana.

## RES_004 Modelo y control de referencia

Modelo rf-v1-90d-s42-ba0ba6390f; MAE 1.1914 frente a persistencia 1.4475 veh/min. 50 pares; reducción media de demora no sobresaturada 29.37%; IC95 [28.64%, 30.10%]. Resultados sintéticos generales de la línea base; no aforos ni validación territorial de Cuauhtémoc.

## RES_005 Estado de cierre

Los documentos, diagramas y guiones están entregados. Permanecen sujetos a revisión humana: Alpha/Beta, identidad/aprobación de revisores de modelos, revisión de dependencias/TLS, reversión operativa y aceptación del docente. Docker no estaba instalado: su perfil está preparado, sin afirmar ejecución. Los criterios de rendimiento/recuperación se juzgan con los resultados anteriores, no por existencia de scripts. Si hay fallas de meta, el prototipo sigue siendo demostrable pero no se declara RNF aceptado.

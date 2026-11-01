# Instalación, operación, mantenimiento y retiro

## Instalación local

Desde la raíz, crear entorno Python 3.13 e instalar `requirements.lock`. Ejecutar
`python -m scripts.configure`: genera `.env` con tres secretos independientes y contraseña de
administrador; no imprime sus valores ni sobrescribe una configuración existente. Ejecutar
`python -m scripts.run_local` para inicializar SQLite y lanzar API, IA, trabajador y Streamlit.
Consultar `.env` para iniciar sesión. Los procesos escuchan únicamente en localhost.

Para PostgreSQL local, crear una BD vacía propia y cambiar `DATABASE_URL` a
`postgresql+psycopg://USUARIO:CLAVE@127.0.0.1:5432/traffic`. El inicializador requiere permisos
de migración. Ejecutar `python -m database.manage`; después usar una URL de ejecución con
rol no propietario, creado con contraseña externa y permisos de `database/runtime_permissions.sql`.
`APP_DB_PASSWORD` permite al inicializador crear/actualizar `traffic_app` automáticamente.
La contraseña de PostgreSQL debe codificarse para URL si contiene caracteres reservados.

En Compose, `docker compose up --build` hace esa separación automáticamente: el inicializador
usa el propietario, y API/trabajador el rol restringido. `db` e `ml` no publican puertos.
El volumen `postgres_data` conserva datos entre reinicios. El archivo `.env` no entra en la imagen.
Para exposición fuera de localhost se debe configurar proxy TLS, control de acceso de red,
rate limiting de autenticación y revisión de dependencias; el perfil entregado es local.

## Ejecución de servicios por separado

```text
python -m database.manage
python -m uvicorn ml_model.service:app --host 127.0.0.1 --port 8001
python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000
python -m backend.worker
python -m streamlit run frontend/dashboard.py --server.address=127.0.0.1
```

Cada comando de servicio se ejecuta en una terminal distinta, desde la raíz y usando el mismo
entorno virtual. No iniciar otro trabajador mientras el lease esté vigente. El lease vence a
los 15 s sin heartbeat real. Reiniciar el trabajador inicia un despeje peatonal de 10 s y cancela
planes activos/pendientes antiguos para no afirmar estados previos no confirmados.

## Guion de demostración

1. Iniciar sesión y seleccionar uno de los cinco cruces sintéticos.
2. Comprobar fechas, fuente, tabla, demanda y colas. `SIM_SPEED=10` avanza diez segundos
   simulados por segundo real como máximo; no promete tiempo real si los servicios tardan.
3. Sin modelo promovido, observar `degraded`, razón y plan fijo 40/40. El peatón conserva su fase.
4. Entrenar/evaluar con los comandos del README. Revisar la ficha y experimentos con otro
   integrante. Promover solo después de revisión real y reiniciar IA.
5. Consultar `/predict_light`; comprobar que una propuesta no cambia colores. Solicitar aplicar
   con versión y siguiente ciclo; consultar `/plans/{id}` para confirmar.
6. Con IA y datos válidos, pedir intervención 50/30 por dos ciclos y motivo. Observar aplicación
   diferida, caducidad y retorno al automático. Si hay fallback, prevalece sobre la intervención.
7. Detener IA: el siguiente ciclo usa fijo. Detener trabajador: después de 5 s el dashboard marca
   estado desconocido. Reiniciar y observar despeje. Registrar evidencia de la demostración.
8. Consultar auditoría y exportar JSON. Ningún paso actúa sobre semáforos físicos.

El cliente `python -m scripts.simulate_waze --once` reenvía cinco ventanas sintéticas al backend
y sirve para demostrar idempotencia. El trabajador ya es la fuente sintética integrada; este
cliente opcional no requiere Waze ni debe ejecutarse con otra semilla contra el mismo histórico.

## Modelos y reversión

Conservar cada `.joblib`, ficha JSON, dataset/hash y reporte. `active.json` identifica el artefacto
promovido. No cargar archivos descargados de orígenes no confiables. La promoción verifica
MAE, control, protocolo, hashes y nombres de autor/revisor diferentes; la revisión humana se
documenta antes de ejecutar el CLI. Copiar candidatos entre equipos exige conservar su manifiesto.

Para revertir, ejecutar el comando `ml_model.promote` con una versión previa y su experimento,
motivo de reversión y revisión del equipo; luego reiniciar IA. No se cambia el archivo del modelo
en caliente. La ausencia/corrupción detectada del artefacto mantiene fallback. En Compose:
`docker compose restart ml`. No borrar el modelo previo hasta cerrar la revisión del nuevo.

## Respaldo y recuperación de laboratorio

Meta de Fase 1: RPO ≤24 h y RTO ≤30 min. Son criterios pendientes de un ejercicio cronometrado,
no resultados acreditados por la existencia de un script.

```text
python -m scripts.backup --pg-dump "RUTA/pg_dump"
```

Se genera `data/backups/traffic-FECHA.dump` en formato custom. La contraseña viaja por
`PGPASSWORD` solo en el entorno del proceso. Para respaldo completo usar una cuenta autorizada;
el rol de ejecución no es propietario y puede no incluir metadatos de permisos completos.
Guardar también configuración protegida, artefactos y manifiestos en un respaldo externo.
Programar un respaldo diario según el sistema operativo y comprobar su resultado; no se instala
una tarea programada automáticamente.

Restauración: detener trabajador/API, crear una **BD nueva y vacía de laboratorio**, restaurar
con `pg_restore --no-owner --no-acl -h HOST -U USUARIO -d traffic_restore ARCHIVO.dump`,
reaplicar permisos de ejecución, verificar conteos/hashes y cambiar la URL solo después de la
validación. No usar `--clean` contra una BD existente. Mantener contraseñas fuera de argumentos.
Iniciar trabajador desde despeje y registrar tiempos, último dato recuperado, RPO/RTO y resultado.
En SQLite se deben detener todos los procesos antes de copiar la BD; no copiar una BD abierta
como procedimiento de respaldo confiable.

## Fallas y observabilidad

| Síntoma | Diagnóstico y acción |
|---|---|
| /health responde pero no hay datos | Es salud del proceso, no de toda la cadena; revisar trabajador y BD |
| IA loaded=false | Falta promoción, hash no coincide o entorno incompatible; revisar artefactos |
| 401 | Sesión vencida o credenciales inválidas; iniciar sesión otra vez |
| 409 | Refrescar versión, ciclo y estado; no reintentar ciegamente una aplicación |
| 503 | Persistencia o trabajador no disponible; ningún éxito sin confirmación |
| Dato viejo | Comparar ventana con reloj simulado, no con hora local del navegador |
| Telemetría vencida | Estado desconocido; revisar lease/logs antes de reiniciar |
| BD interrumpida | Continúa control local; buffer volátil y reconciliación al recuperar |
| Buffer lleno | Reloj local detenido; recuperar BD antes de agotar almacenamiento de emergencia |

Toda respuesta de API incorpora `X-Correlation-ID`; propuestas y cambios lo conservan en
auditoría. El trabajador registra aplicación y recuperación con correlación propia. Los registros
operativos no deben copiar tokens ni contraseñas. Los modelos preservan referencias de las
cinco ventanas por grupo y atributos exactos utilizados para reproducir una inferencia.

## Mantenimiento y retiro

Revisar fallas, capacidad, distribución de datos y métricas por sprint; no reentrenar ni promover
automáticamente ante deriva. El MVP conserva la ficha base pero no incorpora un monitor
estadístico continuo de deriva. Para cambios de esquema, agregar migración y probar respaldo/
restauración antes de aplicarla. La retención automática de telemetría no está habilitada: definir
un periodo revisado antes de una ejecución prolongada; no borrar el dataset académico versionado.

Retiro: detener servicios con Ctrl+C o `docker compose down`, exportar resultados, respaldar
artefactos, revocar credenciales y retirar recursos de prueba. `docker compose down` conserva
el volumen; eliminarlo es una decisión posterior explícita. No se ejecutan borrados de datos ni
credenciales de otras aplicaciones.

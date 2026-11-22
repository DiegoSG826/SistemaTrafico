# Sistema inteligente de gestión de tráfico vehicular para la CDMX

**Entrega académica integrada:** [memoria, manuales, diagramas, presentación y video](entrega_academica/LEEME.md).
La revisión final documenta los criterios que cumplen y los que siguen abiertos, incluidos los
resultados negativos de latencia bajo carga.

**Ámbito actualizado: alcaldía Cuauhtémoc.** Cinco cruces sintéticos y dos tramos piloto de
tráfico real cerca de Metro Cuauhtémoc. Consulta el
[alcance y la revisión de la entrega académica](docs/REVISION_ENTREGA_ACADEMICA.md).
Para cambiar desde el escenario local anterior, detener servicios y ejecutar
`python -m scripts.select_cuauhtemoc` antes de volver a iniciar; se conserva la BD anterior.

FASE 2: base funcional de un **prototipo académico de control simulado**. Incluye FastAPI,
PostgreSQL, servicio interno de Random Forest, Streamlit, generador de observaciones, trabajador
de control, pruebas y documentación. No controla infraestructura vial.

- [Documento técnico de FASE 2](docs/FASE_2_Desarrollo_Implementacion.md)
- [FASE 1 de referencia](docs/FASE_1_Documento_Tecnico_Trafico_CDMX.md)
- [Operación y recuperación](docs/OPERACION.md)
- [Pruebas, trazabilidad y pendientes de aceptación](docs/PRUEBAS_TRAZABILIDAD.md)
- [Evidencia de verificación](reports/VERIFICACION.md)
- [Contrato OpenAPI](docs/openapi.json)

## Inicio local en Windows

Requiere Python **3.13**. Ejecutar desde la raíz del repositorio:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.lock
.\.venv\Scripts\python.exe -m scripts.configure
.\.venv\Scripts\python.exe -m scripts.run_local
```

Abrir [dashboard](http://127.0.0.1:8501) y [Swagger de la API](http://127.0.0.1:8000/docs).
Las credenciales generadas están en `.env`, en `ADMIN_EMAIL` y `ADMIN_PASSWORD`.
Ctrl+C en el lanzador termina sus cuatro procesos. Los registros quedan en `reports/local/`.
SQLite permite esta demostración sin instalar PostgreSQL. Para Linux/macOS se usa
`.venv/bin/python` en lugar de `.\.venv\Scripts\python.exe`.

Al inicio, sin modelo promovido, se utiliza **modo degradado 40/40**. El simulador funciona,
registra observaciones, incluye peatones y muestra la causa. El entrenamiento no activa
silenciosamente un candidato.

## Fuente de tráfico

En la barra lateral del dashboard, **Fuente de tráfico** ofrece **Simulado** y **Real (TomTom)**.
Ambos modos muestran el mapa interactivo y la animación de coches, colas y semáforos.
El modo real permite reproducir un aforo medido en el entorno de Metro Cuauhtémoc y comparar
el plan elegido con el fijo 40/40 usando las mismas llegadas.

1. Selecciona **Real (TomTom)**, adjunta el CSV del cruce piloto y pulsa **Cargar aforo**.
2. Ajusta el verde Norte–Sur y pulsa **Reproducir aforo**. Volver a pulsarlo inicia un nuevo ensayo.

El CSV debe estar en UTF-8, con una fila por minuto consecutivo y conteos enteros de llegadas
para los grupos Norte–Sur y Este–Oeste. Usa fechas ISO 8601 con zona horaria. Ejemplo de formato
con cifras ilustrativas.

```csv
inicio,llegadas_ns,llegadas_eo
2026-11-21T08:00:00-06:00,24,13
2026-11-21T08:01:00-06:00,26,11
```

La reproducción parte de colas vacías, reparte cada conteo dentro de su minuto y usa
`SIM_SPEED` (10× por defecto). Los marcadores y las colas corresponden al ensayo. Las líneas
y la tabla de TomTom muestran lecturas recientes de velocidad, demora, cierres y confianza.

Para activar TomTom, añade `TOMTOM_API_KEY` a `.env` y reinicia la API. En Docker Compose,
recrea el servicio `api` para cargar el cambio. La clave se usa en FastAPI y el mapa muestra la
geometría devuelta por el proveedor. `TOMTOM_REFRESH_SECONDS` vale 300 s por defecto. La API
comparte las lecturas entre sesiones y consulta al proveedor bajo demanda. Si una consulta
falla, la última lectura se marca como vencida y se descarta al superar tres intervalos.

## Entrenamiento y evaluación

```powershell
.\.venv\Scripts\python.exe -m ml_model.train_model --days 90 --seed 42
# Sustituir VERSION por la versión que imprime el entrenamiento:
.\.venv\Scripts\python.exe -m ml_model.evaluate VERSION
```

El entrenamiento guarda dataset comprimido, modelo `.joblib` y ficha JSON en
`ml_model/artifacts/`. El experimento guarda `reports/experiment.json`.
La promoción requiere superar ambos criterios y registrar revisión real por otra persona:

```powershell
.\.venv\Scripts\python.exe -m ml_model.promote VERSION --experiment reports/experiment.json --author "Nombre IA" --reviewer "Nombre QA" --reason "Revisión del experimento y del controlador"
```

Reiniciar el servicio IA después de promover o revertir. La reversión usa el mismo comando
con una versión anterior y su evidencia. Sin promoción, `/predict_light` devuelve un plan fijo
con causa de degradación. Los artefactos grandes y los secretos se excluyen de Git.

## PostgreSQL y contenedores

Con Docker y Compose instalados, después de `python -m scripts.configure`:

```powershell
docker compose up --build
```

Compose inicia PostgreSQL, inicializador de esquema, API, IA, trabajador y dashboard.
Solo API y dashboard se publican en localhost. El inicializador usa el propietario; API y
trabajador usan `traffic_app`, sin permisos para alterar la auditoría o los usuarios.
El modelo se monta como solo lectura. El sistema también inicia sin modelo promovido.
Las contraseñas generadas son hexadecimales, seguras para la URL de conexión; si se sustituyen,
se deben codificar los caracteres reservados de URL.

## Pruebas

```powershell
.\.venv\Scripts\python.exe -m pytest --cov=backend.app.controller --cov=backend.app.schemas --cov-branch --cov-fail-under=80
# Opcional: BD PostgreSQL de laboratorio; crea/elimina únicamente esquemas UUID propios:
$env:TEST_DATABASE_URL='postgresql+psycopg://usuario:clave@localhost:5432/traffic_test'
.\.venv\Scripts\python.exe -m pytest
```

La CI ejecuta también las pruebas PostgreSQL. La matriz de aceptación distingue evidencia
automatizada de las pruebas de carga, restauración y evaluación humana pendientes.

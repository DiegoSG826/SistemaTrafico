# Sistema inteligente de gestión de tráfico vehicular para la CDMX

**Entrega académica integrada:** [memoria, manuales, diagramas, presentación y video](entrega_academica/LEEME.md).
La revisión final documenta los criterios que cumplen y los que siguen abiertos, incluidos los
resultados negativos de latencia bajo carga.

**Ámbito actualizado: alcaldía Cuauhtémoc.** Cinco cruces sintéticos, sin conexión a semáforos
reales. Consulta [alcance y revisión de la entrega académica](docs/REVISION_ENTREGA_ACADEMICA.md).
Para cambiar desde el escenario local anterior, detener servicios y ejecutar
`python -m scripts.select_cuauhtemoc` antes de volver a iniciar; se conserva la BD anterior.

FASE 2: base funcional de un **prototipo académico exclusivamente simulado**. Incluye FastAPI,
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

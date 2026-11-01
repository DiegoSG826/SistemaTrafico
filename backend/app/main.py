from contextlib import asynccontextmanager
from uuid import uuid4

from fastapi import Depends, FastAPI, HTTPException, Query, Request
from fastapi.responses import JSONResponse
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import ValidationError
from sqlalchemy import select, update
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from database.manage import add_groups
from . import schemas, services
from .config import Settings, settings
from .controller import Timing
from .database import aware, connect
from .models import Audit, Group, Intersection, Plan, TrafficRecord, User
from .security import decode, token_for, verify
from .study_area import STUDY_AREA

bearer = HTTPBearer(auto_error=False)


def create_app(config: Settings | None = None, factory=None, infer=None):
    config = config or settings()
    engine = None

    @asynccontextmanager
    async def lifespan(app):
        nonlocal factory, engine
        if len(config.jwt_secret) < 32 or config.jwt_secret.startswith("CAMBIAR"):
            raise RuntimeError("JWT_SECRET propio de al menos 32 caracteres obligatorio")
        if factory is None:
            engine, factory = connect(config.database_url)
        yield
        if engine:
            engine.dispose()

    app = FastAPI(title="SGT Cuauhtémoc · simulación", version="0.2.0", lifespan=lifespan)
    app.state.infer = infer or (lambda rows: services.infer_http(config.ml_service_url, rows))

    @app.middleware("http")
    async def correlate(request, call_next):
        request.state.correlation_id = str(uuid4())
        response = await call_next(request)
        response.headers["X-Correlation-ID"] = request.state.correlation_id
        return response

    @app.exception_handler(IntegrityError)
    async def conflict(_, exc):
        return JSONResponse(status_code=409, content={"detail": "Conflicto de integridad o concurrencia"})

    @app.exception_handler(SQLAlchemyError)
    async def storage_failure(_, exc):
        return JSONResponse(status_code=503, content={"detail": "Persistencia indisponible; sin cambio confirmado"})

    def session():
        with factory() as db:
            try:
                yield db
                db.commit()
            except Exception:
                db.rollback()
                raise

    def user(credentials: HTTPAuthorizationCredentials | None = Depends(bearer), db=Depends(session, scope="function")):
        if credentials is None:
            raise HTTPException(401, "Autenticación requerida", headers={"WWW-Authenticate": "Bearer"})
        current = db.get(User, decode(credentials.credentials, config.jwt_secret))
        if current is None or not current.active:
            raise HTTPException(401, "Usuario inactivo")
        return current

    def admin(current=Depends(user)):
        if current.role != "admin":
            raise HTTPException(403, "Permiso de administrador requerido")
        return current

    @app.get("/health")
    def health():
        return {"status": "ok", "version": "0.2.0", "simulation_only": True,
                "study_area": STUDY_AREA}

    @app.post("/auth/token")
    def login(body: schemas.Login, db=Depends(session, scope="function")):
        current = db.scalar(select(User).where(User.email == body.email))
        if not current or not current.active or not verify(body.password, current.password_hash):
            raise HTTPException(401, "Credenciales inválidas")
        return {"access_token": token_for(current, config.jwt_secret), "token_type": "bearer",
                "expires_in": 3600}

    def intersection_json(db, item, groups=None):
        return {"id": item.id, "name": item.name, "latitude": item.latitude,
                "longitude": item.longitude, "active": item.active,
                "config_version": item.config_version, "plan_version": item.plan_version,
                "state": item.state, "telemetry_current": services.is_live(item),
                "groups": [{"id": g.id, "code": g.code, "lanes": g.lanes,
                            "discharge_vps": g.discharge_vps}
                           for g in (groups if groups is not None else services.groups_for(db, item.id))]}

    @app.get("/intersections")
    def intersections(offset: int = Query(0, ge=0), limit: int = Query(50, ge=1, le=100),
                      current=Depends(user), db=Depends(session, scope="function")):
        items = list(db.scalars(select(Intersection).order_by(Intersection.id).offset(offset).limit(limit)))
        grouped = {i.id: [] for i in items}
        for group in db.scalars(select(Group).where(Group.intersection_id.in_(grouped)).order_by(Group.id)):
            grouped[group.intersection_id].append(group)
        return {"items": [intersection_json(db, i, grouped[i.id]) for i in items], "offset": offset, "limit": limit,
                "study_area": STUDY_AREA}

    @app.post("/intersections", status_code=201)
    def create_intersection(body: schemas.IntersectionInput, request: Request,
                            current=Depends(admin), db=Depends(session, scope="function")):
        item = Intersection(name=body.name, latitude=body.latitude, longitude=body.longitude, state={})
        db.add(item)
        db.flush()
        add_groups(db, item, body.lanes, body.discharge_vps)
        services.audit(db, "create", f"intersection:{item.id}", "Alta de cruce sintético",
                       after=body.model_dump(), user=current, correlation=request.state.correlation_id)
        return intersection_json(db, item)

    @app.put("/intersections/{identifier}")
    def edit_intersection(identifier: int, body: schemas.IntersectionEdit, request: Request,
                          current=Depends(admin), db=Depends(session, scope="function")):
        item = services.get_intersection(db, identifier)
        before = intersection_json(db, item)
        result = db.execute(update(Intersection).where(Intersection.id == identifier,
            Intersection.config_version == body.config_version).values(name=body.name,
            latitude=body.latitude, longitude=body.longitude, active=body.active,
            config_version=body.config_version+1))
        if result.rowcount != 1:
            raise HTTPException(409, "Versión de configuración obsoleta")
        for group in services.groups_for(db, identifier):
            if group.code != "PEATON":
                group.lanes, group.discharge_vps = body.lanes, body.discharge_vps
        services.audit(db, "configure", f"intersection:{item.id}", "Edición de configuración",
                       before=before, after=body.model_dump(), user=current,
                       correlation=request.state.correlation_id)
        return intersection_json(db, item)

    @app.post("/traffic_records")
    def ingest(body: list[dict], request: Request, current=Depends(admin), db=Depends(session, scope="function")):
        if not 1 <= len(body) <= 1000:
            raise HTTPException(422, "Lote de 1..1000 registros")
        results = []
        for raw in body:
            try:
                obs = schemas.Observation.model_validate(raw)
                group = db.get(Group, obs.group_id)
                if not group or group.code == "PEATON":
                    raise ValueError("Grupo vehicular desconocido")
                item = services.get_intersection(db, group.intersection_id)
                now = services.decision_clock(item)
                if aware(obs.window_end) > now:
                    raise ValueError("Observación futura respecto al reloj de simulación")
                quality = "missing" if obs.arrivals is None else "late" \
                    if (now-aware(obs.window_end)).total_seconds() > 120 else "valid"
                duplicate = db.scalar(select(TrafficRecord.id).where(
                    TrafficRecord.source == obs.source, TrafficRecord.group_id == obs.group_id,
                    TrafficRecord.window_start == aware(obs.window_start),
                    TrafficRecord.window_end == aware(obs.window_end)))
                if duplicate:
                    results.append({"status": "duplicate", "id": duplicate})
                    continue
                try:
                    with db.begin_nested():
                        values = {**obs.model_dump(), "window_start": aware(obs.window_start),
                                  "window_end": aware(obs.window_end)}
                        record = TrafficRecord(**values, quality=quality)
                        db.add(record)
                        db.flush()
                    results.append({"status": "accepted", "id": record.id, "quality": quality})
                except IntegrityError:
                    results.append({"status": "duplicate"})
            except (ValidationError, ValueError):
                # No copiar valores crudos o secretos dentro de la auditoría.
                results.append({"status": "rejected", "reason": "Contrato de observación inválido"})
        services.audit(db, "ingest", "traffic", "Resultado de lote normalizado",
                       after={"results": results}, user=current, correlation=request.state.correlation_id)
        return {"results": results}

    @app.get("/traffic_data")
    def traffic_data(intersection_id: int | None = None, group_id: int | None = None,
                     start: str | None = None, end: str | None = None,
                     offset: int = Query(0, ge=0), limit: int = Query(100, ge=1, le=1000),
                     current=Depends(user), db=Depends(session, scope="function")):
        from datetime import datetime
        query = select(TrafficRecord, Group).join(Group, TrafficRecord.group_id == Group.id)
        if intersection_id is not None:
            services.get_intersection(db, intersection_id)
            query = query.where(Group.intersection_id == intersection_id)
        if group_id is not None:
            query = query.where(Group.id == group_id)
        for value, column, after in ((start, TrafficRecord.window_start, True),
                                     (end, TrafficRecord.window_end, False)):
            if value:
                try:
                    timestamp = datetime.fromisoformat(value)
                    if timestamp.utcoffset() is None:
                        raise ValueError()
                except ValueError:
                    raise HTTPException(422, "Fecha ISO 8601 con zona requerida")
                query = query.where(column >= timestamp if after else column <= timestamp)
        results = []
        for row, group in db.execute(query.order_by(TrafficRecord.window_end.desc(),
            TrafficRecord.id.desc()).offset(offset).limit(limit)):
            item = db.get(Intersection, group.intersection_id)
            age = (services.decision_clock(item)-aware(row.window_end)).total_seconds()
            results.append({"id": row.id, "intersection_id": item.id, "group_id": group.id,
                "group": group.code, "window_start": aware(row.window_start),
                "window_end": aware(row.window_end), "arrivals_vpm": row.arrivals,
                "speed_kmh": row.speed_kmh, "weather": row.weather, "source": row.source,
                "quality": row.quality, "age_sim_s": age, "current": 0 <= age <= 120,
                "synthetic": row.source == "synthetic"})
        return {"items": results, "offset": offset, "limit": limit}

    @app.post("/predict_light", status_code=201)
    def predict_light(body: schemas.PredictionRequest, request: Request,
                      current=Depends(admin), db=Depends(session, scope="function")):
        item = services.get_intersection(db, body.intersection_id)
        if item.plan_version != body.previous_version:
            raise HTTPException(409, "Versión de plan obsoleta")
        if not item.active:
            raise HTTPException(409, "Cruce inactivo")
        plan, forecasts = services.propose(db, item, app.state.infer, user=current,
                                          correlation=request.state.correlation_id)
        return services.export_plan(db, plan, forecasts)

    @app.get("/plans/{identifier}")
    def get_plan(identifier: int, current=Depends(user), db=Depends(session, scope="function")):
        plan = db.get(Plan, identifier)
        if not plan:
            raise HTTPException(404, "Plan desconocido")
        return services.export_plan(db, plan)

    @app.post("/plans/{identifier}/apply", status_code=202)
    def apply(identifier: int, body: schemas.ApplyRequest, request: Request,
              current=Depends(admin), db=Depends(session, scope="function")):
        plan = db.get(Plan, identifier)
        if not plan:
            raise HTTPException(404, "Plan desconocido")
        item = services.get_intersection(db, plan.intersection_id)
        services.queue_plan(db, item, plan, body.previous_version, body.target_cycle,
                            current, request.state.correlation_id)
        return services.export_plan(db, plan)

    @app.post("/manual_override", status_code=202)
    def manual(body: schemas.ManualRequest, request: Request,
               current=Depends(admin), db=Depends(session, scope="function")):
        try:
            timing = Timing(body.green_ns, body.green_eo).validate()
        except ValueError as exc:
            raise HTTPException(422, str(exc))
        item = services.get_intersection(db, body.intersection_id)
        target = item.state.get("cycle", -1)+1
        plan = services.create_plan(db, item, timing, "manual", body.reason, user=current,
            expires=target+body.duration_cycles, correlation=request.state.correlation_id)
        services.queue_plan(db, item, plan, body.previous_version, target, current,
                            request.state.correlation_id)
        return services.export_plan(db, plan)

    @app.post("/automatic")
    def automatic(body: schemas.PredictionRequest, request: Request,
                  current=Depends(admin), db=Depends(session, scope="function")):
        item = services.get_intersection(db, body.intersection_id)
        changed = db.execute(update(Intersection).where(Intersection.id == item.id,
            Intersection.plan_version == body.previous_version).values(plan_version=body.previous_version+1))
        if changed.rowcount != 1:
            raise HTTPException(409, "Versión obsoleta")
        db.execute(update(Plan).where(Plan.intersection_id == item.id, Plan.mode == "manual").values(
            expires_cycle=item.state.get("cycle", -1)+1))
        db.execute(update(Plan).where(Plan.intersection_id == item.id, Plan.status == "PENDING").values(
            status="CANCELLED"))
        services.audit(db, "automatic", f"intersection:{item.id}", "Retorno al automático al siguiente ciclo",
                       user=current, correlation=request.state.correlation_id)
        return {"status": "requested", "version": body.previous_version+1}

    @app.get("/audit")
    def audit_log(offset: int = Query(0, ge=0), limit: int = Query(50, ge=1, le=200),
                  current=Depends(admin), db=Depends(session, scope="function")):
        rows = db.scalars(select(Audit).order_by(Audit.id.desc()).offset(offset).limit(limit))
        return {"items": [{"id": r.id, "actor": r.actor, "action": r.action, "entity": r.entity,
                           "reason": r.reason, "at": aware(r.at), "before": r.before, "after": r.after,
                           "correlation_id": r.correlation_id} for r in rows]}

    # Contrato descargable para revisión, sin conexión de BD al importar.
    return app


app = create_app()

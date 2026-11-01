-- Esquema v1 generado desde backend/app/models.py. No ejecutar en BD con datos previos.

-- Las sumas de fases se validan transaccionalmente en el controlador; CHECK por fila no basta.

CREATE TABLE control_worker (
	id SERIAL NOT NULL, 
	owner VARCHAR(80) NOT NULL, 
	heartbeat TIMESTAMP WITH TIME ZONE NOT NULL, 
	PRIMARY KEY (id)
);

CREATE TABLE intersecciones (
	id SERIAL NOT NULL, 
	name VARCHAR(160) NOT NULL, 
	latitude FLOAT NOT NULL, 
	longitude FLOAT NOT NULL, 
	timezone VARCHAR(50) NOT NULL, 
	active BOOLEAN NOT NULL, 
	config_version INTEGER NOT NULL, 
	plan_version INTEGER NOT NULL, 
	state JSON NOT NULL, 
	PRIMARY KEY (id), 
	CHECK (latitude BETWEEN -90 AND 90), 
	CHECK (longitude BETWEEN -180 AND 180)
);

CREATE TABLE modelos (
	id SERIAL NOT NULL, 
	version VARCHAR(80) NOT NULL, 
	artifact_hash VARCHAR(64) NOT NULL, 
	dataset_hash VARCHAR(64) NOT NULL, 
	metadata JSON NOT NULL, 
	status VARCHAR(20) NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	UNIQUE (version)
);

CREATE TABLE usuarios (
	id SERIAL NOT NULL, 
	email VARCHAR(254) NOT NULL, 
	password_hash VARCHAR(512) NOT NULL, 
	role VARCHAR(16) NOT NULL, 
	active BOOLEAN NOT NULL, 
	PRIMARY KEY (id), 
	UNIQUE (email)
);

CREATE TABLE auditoria (
	id SERIAL NOT NULL, 
	user_id INTEGER, 
	actor VARCHAR(80) NOT NULL, 
	action VARCHAR(50) NOT NULL, 
	entity VARCHAR(80) NOT NULL, 
	before JSON NOT NULL, 
	after JSON NOT NULL, 
	reason VARCHAR(300) NOT NULL, 
	correlation_id VARCHAR(80) NOT NULL, 
	at TIMESTAMP WITH TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(user_id) REFERENCES usuarios (id)
);

CREATE INDEX ix_auditoria_correlation_id ON auditoria (correlation_id);

CREATE TABLE experimentos (
	id SERIAL NOT NULL, 
	model_id INTEGER, 
	configuration JSON NOT NULL, 
	metrics JSON NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(model_id) REFERENCES modelos (id)
);

CREATE TABLE grupos_movimiento (
	id SERIAL NOT NULL, 
	intersection_id INTEGER NOT NULL, 
	code VARCHAR(10) NOT NULL, 
	lanes INTEGER NOT NULL, 
	discharge_vps FLOAT NOT NULL, 
	PRIMARY KEY (id), 
	UNIQUE (intersection_id, code), 
	CHECK (code IN ('NS','EO','PEATON')), 
	CHECK (lanes > 0 AND discharge_vps > 0), 
	FOREIGN KEY(intersection_id) REFERENCES intersecciones (id)
);

CREATE TABLE planes_semaforicos (
	id SERIAL NOT NULL, 
	intersection_id INTEGER NOT NULL, 
	user_id INTEGER, 
	previous_version INTEGER NOT NULL, 
	target_cycle INTEGER NOT NULL, 
	mode VARCHAR(16) NOT NULL, 
	reason VARCHAR(300) NOT NULL, 
	status VARCHAR(16) NOT NULL, 
	expires_cycle INTEGER, 
	created_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	applied_at TIMESTAMP WITH TIME ZONE, 
	PRIMARY KEY (id), 
	CHECK (mode IN ('automatic','manual','degraded','fixed')), 
	CHECK (status IN ('PROPOSED','PENDING','ACTIVE','SUPERSEDED','CANCELLED')), 
	FOREIGN KEY(intersection_id) REFERENCES intersecciones (id), 
	FOREIGN KEY(user_id) REFERENCES usuarios (id)
);

CREATE UNIQUE INDEX uq_active_plan ON planes_semaforicos (intersection_id) WHERE status = 'ACTIVE';

CREATE UNIQUE INDEX uq_pending_plan ON planes_semaforicos (intersection_id) WHERE status = 'PENDING';

CREATE TABLE detalles_plan (
	plan_id INTEGER NOT NULL, 
	group_id INTEGER NOT NULL, 
	"order" INTEGER NOT NULL, 
	green_s INTEGER NOT NULL, 
	yellow_s INTEGER NOT NULL, 
	clearance_s INTEGER NOT NULL, 
	PRIMARY KEY (plan_id, group_id), 
	CHECK (green_s >= 0 AND yellow_s >= 0 AND clearance_s >= 0), 
	FOREIGN KEY(plan_id) REFERENCES planes_semaforicos (id), 
	FOREIGN KEY(group_id) REFERENCES grupos_movimiento (id)
);

CREATE TABLE predicciones (
	id SERIAL NOT NULL, 
	group_id INTEGER NOT NULL, 
	model_id INTEGER NOT NULL, 
	decision_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	horizon_min INTEGER NOT NULL, 
	flow_vpm FLOAT NOT NULL, 
	inputs JSON NOT NULL, 
	PRIMARY KEY (id), 
	CHECK (flow_vpm >= 0 AND horizon_min = 5), 
	FOREIGN KEY(group_id) REFERENCES grupos_movimiento (id), 
	FOREIGN KEY(model_id) REFERENCES modelos (id)
);

CREATE TABLE registros_trafico (
	id SERIAL NOT NULL, 
	group_id INTEGER NOT NULL, 
	window_start TIMESTAMP WITH TIME ZONE NOT NULL, 
	window_end TIMESTAMP WITH TIME ZONE NOT NULL, 
	arrivals INTEGER, 
	speed_kmh FLOAT, 
	weather VARCHAR(12), 
	source VARCHAR(40) NOT NULL, 
	external_id VARCHAR(160), 
	quality VARCHAR(16) NOT NULL, 
	received_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	UNIQUE (source, group_id, window_start, window_end), 
	CHECK (arrivals IS NULL OR arrivals BETWEEN 0 AND 300), 
	CHECK (speed_kmh IS NULL OR speed_kmh BETWEEN 0 AND 150), 
	CHECK (window_end > window_start), 
	FOREIGN KEY(group_id) REFERENCES grupos_movimiento (id)
);

CREATE INDEX ix_traffic_group_time ON registros_trafico (group_id, window_end);

CREATE TABLE semaforos (
	id SERIAL NOT NULL, 
	group_id INTEGER NOT NULL, 
	head VARCHAR(80) NOT NULL, 
	operational BOOLEAN NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(group_id) REFERENCES grupos_movimiento (id), 
	UNIQUE (head)
);

CREATE TABLE plan_prediccion (
	plan_id INTEGER NOT NULL, 
	prediction_id INTEGER NOT NULL, 
	PRIMARY KEY (plan_id, prediction_id), 
	FOREIGN KEY(plan_id) REFERENCES planes_semaforicos (id), 
	FOREIGN KEY(prediction_id) REFERENCES predicciones (id)
);

-- Restricción diferida: comprueba el conjunto de fases al confirmar una transacción.
CREATE FUNCTION validate_active_plan() RETURNS trigger LANGUAGE plpgsql AS $$
DECLARE
    pid integer;
    state_value text;
    row_count integer;
    duration_sum integer;
    valid_count integer;
BEGIN
    IF TG_TABLE_NAME = 'planes_semaforicos' THEN
        pid := NEW.id;
    ELSIF TG_OP = 'DELETE' THEN
        pid := OLD.plan_id;
    ELSE
        pid := NEW.plan_id;
    END IF;
    SELECT status INTO state_value FROM planes_semaforicos WHERE id=pid;
    IF state_value = 'ACTIVE' THEN
        SELECT count(*), sum(d.green_s+d.yellow_s+d.clearance_s),
               count(*) FILTER (WHERE g.intersection_id=p.intersection_id AND
                 ((g.code='NS' AND d."order"=0 AND d.green_s BETWEEN 20 AND 60 AND d.yellow_s=3 AND d.clearance_s=2) OR
                  (g.code='EO' AND d."order"=1 AND d.green_s BETWEEN 20 AND 60 AND d.yellow_s=3 AND d.clearance_s=2) OR
                  (g.code='PEATON' AND d."order"=2 AND d.green_s=20 AND d.yellow_s=0 AND d.clearance_s=10)))
          INTO row_count, duration_sum, valid_count
          FROM detalles_plan d JOIN grupos_movimiento g ON g.id=d.group_id
               JOIN planes_semaforicos p ON p.id=d.plan_id WHERE d.plan_id=pid;
        IF row_count<>3 OR duration_sum<>120 OR valid_count<>3 THEN
            RAISE EXCEPTION 'Plan activo % viola ciclo, pertenencia o fases', pid USING ERRCODE='23514';
        END IF;
    END IF;
    RETURN NULL;
END;
$$;

CREATE CONSTRAINT TRIGGER validate_plan_header
AFTER INSERT OR UPDATE ON planes_semaforicos
DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION validate_active_plan();

CREATE CONSTRAINT TRIGGER validate_plan_details
AFTER INSERT OR UPDATE OR DELETE ON detalles_plan
DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION validate_active_plan();


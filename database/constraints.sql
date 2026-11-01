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

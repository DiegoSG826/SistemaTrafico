-- Ejecutar como propietario después de crear traffic_app con contraseña fuera del repositorio.
-- El usuario de la aplicación no debe ser propietario ni superusuario.
GRANT USAGE ON SCHEMA public TO traffic_app;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO traffic_app;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO traffic_app;
REVOKE UPDATE, DELETE, TRUNCATE ON auditoria FROM traffic_app;
REVOKE INSERT, UPDATE, DELETE, TRUNCATE ON usuarios FROM traffic_app;
REVOKE ALL ON schema_versions FROM traffic_app;

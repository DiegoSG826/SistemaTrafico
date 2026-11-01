"""Ámbito académico único; no representa un inventario municipal ni una geocerca oficial."""
STUDY_AREA = {
    "id": "ALC_001", "name": "Cuauhtémoc", "city": "Ciudad de México",
    "simulation_only": True, "catalog_version": "cuauhtemoc-synthetic-v1",
    "geographic_validation": "Referencias esquemáticas; sin aforos ni inventario oficial",
}

# Referencias esquemáticas en el sector central; no son ubicaciones de semáforos reales.
CATALOG = [("Cuauhtémoc · Cruce sintético CUA_001", 19.432, -99.145),
           ("Cuauhtémoc · Cruce sintético CUA_002", 19.434, -99.147),
           ("Cuauhtémoc · Cruce sintético CUA_003", 19.436, -99.149),
           ("Cuauhtémoc · Cruce sintético CUA_004", 19.438, -99.151),
           ("Cuauhtémoc · Cruce sintético CUA_005", 19.440, -99.153)]

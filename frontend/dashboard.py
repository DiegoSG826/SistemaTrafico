"""Ejecutar: streamlit run frontend/dashboard.py"""
import json
import os

import httpx
from dotenv import load_dotenv
import pandas as pd
import streamlit as st

st.set_page_config(page_title="SGT CDMX · simulación", page_icon="🚦", layout="wide")
st.title("Sistema inteligente de tráfico · CDMX")
st.caption("Prototipo académico · datos y semáforos sintéticos · tiempos sugeridos por heurística")
load_dotenv()
API = os.getenv("API_URL", "http://127.0.0.1:8000").rstrip("/")


def api(method, path, **kwargs):
    token = st.session_state.get("token")
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    try:
        result = httpx.request(method, f"{API}{path}", headers=headers, timeout=5,
                               trust_env=False, **kwargs)
        if result.status_code == 401:
            st.session_state.pop("token", None)
            st.error("Sesión inválida o vencida. Inicia sesión de nuevo.")
            st.stop()
        result.raise_for_status()
        return result.json()
    except httpx.HTTPStatusError as exc:
        st.error(f"Operación rechazada ({exc.response.status_code}): {exc.response.text[:300]}")
    except httpx.HTTPError as exc:
        st.error(f"Sin comunicación con la API ({API}). Estado actual desconocido.")
        st.caption(f"Detalle de conexión: {type(exc).__name__}. Comprueba que el backend siga ejecutándose.")
    return None


if "token" not in st.session_state:
    with st.form("login"):
        email = st.text_input("Correo", value="admin@example.test")
        password = st.text_input("Contraseña", type="password")
        submit = st.form_submit_button("Entrar")
    if submit:
        response = api("POST", "/auth/token", json={"email": email, "password": password})
        if response:
            st.session_state.token = response["access_token"]
            st.rerun()
    st.stop()

if st.sidebar.button("Cerrar sesión"):
    st.session_state.clear()
    st.rerun()

catalog = api("GET", "/intersections")
if not catalog or not catalog["items"]:
    st.stop()
options = {f"{i['id']} · {i['name']}": i for i in catalog["items"]}
selection = st.sidebar.selectbox("Intersección simulada", options)
identifier = options[selection]["id"]
st.sidebar.caption("Las fechas se presentan en America/Mexico_City; persistencia en UTC.")


@st.fragment(run_every="2s")
def monitor():
    latest = api("GET", "/intersections")
    if not latest:
        st.warning("Telemetría DESCONOCIDA. No hay confirmación actual del simulador.")
        return
    item = next(i for i in latest["items"] if i["id"] == identifier)
    state = item["state"]
    live = item["telemetry_current"]
    if not live:
        st.warning("Telemetría DESACTUALIZADA. Los últimos colores no representan el estado actual.")
    cols = st.columns(4)
    cols[0].metric("Modo confirmado" if live else "Último modo", state.get("mode", "desconocido"))
    cols[1].metric("Ciclo simulado", state.get("cycle", "—"))
    cols[2].metric("Cola NS (veh)", state.get("queues", [0, 0])[0])
    cols[3].metric("Cola EO (veh)", state.get("queues", [0, 0])[1])
    if state.get("sim_time"):
        stamp = pd.Timestamp(state["sim_time"]).tz_convert("America/Mexico_City")
        st.write(f"Reloj simulado: {stamp} · versión {item['plan_version']}")
    st.write("Estado semafórico:", state.get("colors", {}) if live else "DESCONOCIDO")
    st.caption(state.get("reason", "Sin plan aplicado"))
    traffic = api("GET", "/traffic_data", params={"intersection_id": identifier, "limit": 60})
    if traffic and traffic["items"]:
        table = pd.DataFrame(traffic["items"])
        table["window_end"] = pd.to_datetime(table.window_end, utc=True).dt.tz_convert("America/Mexico_City")
        st.dataframe(table[["group", "window_end", "arrivals_vpm", "speed_kmh", "weather",
                            "source", "quality", "current"]], width="stretch", hide_index=True)
        chart = table.pivot_table(index="window_end", columns="group", values="arrivals_vpm", aggfunc="first")
        st.line_chart(chart, y_label="Llegadas (veh/min)")
        st.download_button("Exportar observaciones JSON", json.dumps(traffic, ensure_ascii=False, indent=2),
                           file_name=f"trafico-sintetico-{identifier}.json", mime="application/json")


monitor()
st.subheader("Intervención del administrador")
with st.form("manual"):
    green_ns = st.slider("Verde NS (s)", 20, 60, 40)
    st.write(f"Verde EO: {80-green_ns} s · fase peatonal obligatoria: 20 s · ciclo: 120 s")
    reason = st.text_input("Motivo de la intervención", max_chars=300)
    cycles = st.number_input("Vigencia en ciclos", min_value=1, max_value=10, value=1)
    submit = st.form_submit_button("Solicitar intervención al siguiente ciclo")
if submit:
    # Consultar versión en el momento del envío para reducir conflictos evitables.
    current = api("GET", "/intersections")
    if current:
        item = next(i for i in current["items"] if i["id"] == identifier)
        result = api("POST", "/manual_override", json={"intersection_id": identifier,
            "previous_version": item["plan_version"], "green_ns": green_ns, "green_eo": 80-green_ns,
            "reason": reason, "duration_cycles": int(cycles)})
        if result:
            st.success(f"Solicitud {result['id']}: {result['status']}. La aplicación requiere confirmación del trabajador.")
            st.json(result)

left, right = st.columns(2)
if left.button("Obtener propuesta del modelo"):
    current = api("GET", "/intersections")
    if current:
        item = next(i for i in current["items"] if i["id"] == identifier)
        result = api("POST", "/predict_light", json={"intersection_id": identifier,
                                                    "previous_version": item["plan_version"]})
        if result:
            st.json(result)
if right.button("Volver al automático al siguiente ciclo"):
    current = api("GET", "/intersections")
    if current:
        item = next(i for i in current["items"] if i["id"] == identifier)
        result = api("POST", "/automatic", json={"intersection_id": identifier,
                                                "previous_version": item["plan_version"]})
        if result:
            st.success("Retorno solicitado; el modo confirmado cambiará al siguiente ciclo.")

with st.expander("Auditoría reciente"):
    if st.button("Consultar auditoría"):
        result = api("GET", "/audit", params={"limit": 30})
        if result:
            st.dataframe(pd.DataFrame(result["items"]), width="stretch")

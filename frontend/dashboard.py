"""Ejecutar: python -m streamlit run frontend/dashboard.py"""
import json
import os
import time
from pathlib import Path
from uuid import uuid4

import httpx
import pandas as pd
import streamlit as st
import streamlit.components.v1 as components
from dotenv import load_dotenv

from frontend.aforo import cargar_aforo

st.set_page_config(page_title="SGT CDMX · Cuauhtémoc", page_icon="🚦", layout="wide")
st.title("Sistema inteligente de tráfico · Cuauhtémoc")
st.caption("Alcaldía Cuauhtémoc, CDMX · prototipo académico de gestión de tráfico")
st.markdown("""<style>
.kp-fila{display:flex;gap:10px;flex-wrap:wrap;margin:6px 0 4px}
.kp{flex:1 1 130px;min-width:120px;background:rgba(128,128,128,.14);border-radius:10px;padding:8px 12px}
.kp span{display:block;font-size:.78rem;opacity:.75}
.kp b{font-size:1.1rem}
</style>""", unsafe_allow_html=True)
load_dotenv()
# Dirección de la API del backend. Se puede cambiar en .env o con la variable API_URL.
API = os.getenv("API_URL", "http://127.0.0.1:8000").rstrip("/")
SIM_SPEED = float(os.getenv("SIM_SPEED", "10"))

# Cada cuántos segundos reales se vuelve a sincronizar el mapa/animación con el backend.
# Entre sincronizaciones, las luces corren solas en el navegador (sin parpadeo).
RESYNC_S = 30

ESTILOS = ["Calles", "Claro", "Oscuro", "Satélite"]
MOTOR_JS = Path(__file__).with_name("motor_trafico.js").read_text(encoding="utf-8")
FASES = {
    "NS_GREEN": "Verde Norte–Sur", "NS_YELLOW": "Amarillo Norte–Sur", "NS_CLEAR": "Despeje Norte–Sur",
    "EO_GREEN": "Verde Este–Oeste", "EO_YELLOW": "Amarillo Este–Oeste", "EO_CLEAR": "Despeje Este–Oeste",
    "PEDESTRIAN": "Fase peatonal", "PEDESTRIAN_CLEAR": "Despeje peatonal",
}
NOMBRE_LUZ = {"GREEN": "🟢 Verde", "YELLOW": "🟡 Amarillo", "RED": "🔴 Rojo"}
MODOS = {"degraded": "Degradado (fijo 40/40)", "automatic": "Automático", "manual": "Manual"}


# ---------------------------------------------------------------------------
# Comunicación con la API
# ---------------------------------------------------------------------------
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


# ---------------------------------------------------------------------------
# Login
# ---------------------------------------------------------------------------
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


def seguro_json(datos):
    return json.dumps(datos, ensure_ascii=False).replace("</", "<\\/")


def datos_tomtom(segmentos):
    estados = {"current": "Vigente", "stale": "Datos vencidos", "unavailable": "Sin datos"}
    tramos, filas = [], []
    for segmento in segmentos:
        flujo = segmento["flow"]
        estado = estados[segmento["status"]]
        color = "#64748b"
        if flujo and segmento["status"] == "current":
            referencia = flujo["free_flow_speed_kmh"]
            proporcion = flujo["speed_kmh"] / referencia if referencia else None
            if flujo["closed"] or (proporcion is not None and proporcion < 0.5):
                color = "#c2413b"
            elif proporcion is not None:
                color = "#b45309" if proporcion < 0.8 else "#16805d"
        hora = segmento["retrieved_at"]
        hora_local = (pd.Timestamp(hora).tz_convert("America/Mexico_City")
                      .strftime("%d/%m/%Y %H:%M:%S")) if hora else "—"
        etiqueta = f"{segmento['label']} · {estado}"
        if flujo:
            etiqueta += f" · {flujo['speed_kmh']} km/h"
            if flujo["closed"]:
                etiqueta += " · Cierre reportado"
        tramos.append({
            "label": etiqueta,
            "path": [[p["latitude"], p["longitude"]] for p in flujo["geometry"]] if flujo else [],
            "color": color,
        })
        filas.append({
            "Tramo": segmento["label"],
            "Estado": estado,
            "Velocidad (km/h)": flujo["speed_kmh"] if flujo else None,
            "Referencia (km/h)": flujo["free_flow_speed_kmh"] if flujo else None,
            "Demora (s)": (max(0, flujo["travel_time_s"] - flujo["free_flow_travel_time_s"])
                           if flujo else None),
            "Cierre reportado": ("Sí" if flujo["closed"] else "No") if flujo else "—",
            "Confianza": f"{flujo['confidence']:.0%}" if flujo else "—",
            "Última consulta": hora_local,
        })

    return tramos, filas


def _elegir(identificador):
    st.session_state.sel_id = identificador


def item_actual(items):
    return next((i for i in items if i["id"] == identifier), None)


def html_cacheado(clave, firma, construir, vigencia):
    """Reutiliza el mismo HTML mientras no cambie la firma ni venza la vigencia.

    Si el texto del HTML no cambia, Streamlit no recarga el iframe: el mapa se queda quieto
    y su animación sigue corriendo en el navegador.
    """
    ahora = time.time()
    previo = st.session_state.get(clave)
    if previo and previo["firma"] == firma and ahora - previo["t"] < vigencia:
        return previo["html"]
    html = construir()
    st.session_state[clave] = {"firma": firma, "t": ahora, "html": html}
    return html


def verdes_de(estado):
    verdes = (estado or {}).get("green_s") or {"ns": 40, "eo": 40}
    return int(verdes["ns"]), int(verdes["eo"])


# ---------------------------------------------------------------------------
# Mapa (Leaflet dentro de un iframe; las luces se animan en el navegador)
# ---------------------------------------------------------------------------
MAPA_HTML = """<!DOCTYPE html><html><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/leaflet.min.css">
<style>
html,body{margin:0;height:100%;background:#1b1f27;font-family:system-ui,Segoe UI,sans-serif}
#map{height:100%;width:100%;border-radius:12px;--s:1;background:#cfd6e2}
.mkwrap{background:none;border:none}
.mk{position:relative;width:46px;height:46px;transform:scale(var(--s));transform-origin:50% 50%;cursor:pointer}
.ring{position:absolute;inset:0;border-radius:50%;border:3px solid transparent;box-sizing:border-box;
 transition:background .4s,border-color .2s}
.d{position:absolute;width:13px;height:13px;border-radius:50%;border:1.5px solid rgba(0,0,0,.55);
 box-sizing:border-box;transition:background .15s,box-shadow .15s}
.ns{left:16.5px;top:2px}.eo{right:2px;top:16.5px}.pe{left:16.5px;bottom:2px}
.tag{position:absolute;left:-5px;top:-5px;width:15px;height:15px;border-radius:50%;color:#fff;
 font:700 9px/15px system-ui,sans-serif;text-align:center;border:1.5px solid #fff}
.lb{position:absolute;left:0;right:0;top:15px;text-align:center;font:700 12px system-ui,sans-serif;
 color:#111;text-shadow:0 0 3px #fff,0 0 3px #fff}
body.dark .lb{color:#fff;text-shadow:0 0 3px #000,0 0 3px #000}
.leg{background:rgba(255,255,255,.92);padding:7px 10px;border-radius:8px;font:12px system-ui,sans-serif;color:#222;line-height:1.5}
.leg i{display:inline-block;width:11px;height:11px;border-radius:50%;margin-right:5px;vertical-align:-1px}
.btn{background:#fff;color:#222;padding:5px 9px;border-radius:6px;font:12px system-ui,sans-serif;cursor:pointer;
 box-shadow:0 1px 4px rgba(0,0,0,.4);margin-bottom:6px}
.btn:hover{background:#eef}
.leaflet-tooltip{font:12px system-ui,sans-serif}
</style></head><body><div id="map"></div>
<script src="https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/leaflet.min.js"></script>
<script>
__MOTOR__
const {data:D, selected:SEL, speed:SPEED, style:BASE, replay:REPLAY,
       segments:TRAMOS, mode:VISTA} = __MAPCFG__;
const reloj=REPLAY ? relojAforo(REPLAY,SPEED) : null;
const aforo=REPLAY ? REPLAY.conteos : null;
const DARK=(BASE===2||BASE===3);
if(DARK) document.body.classList.add('dark');
const COL={GREEN:'#00e676',YELLOW:'#ffd600',RED:'#ff1744'}, OFF='#8a93a3';
const FASES={NS_GREEN:'Verde Norte–Sur',NS_YELLOW:'Amarillo Norte–Sur',NS_CLEAR:'Despeje Norte–Sur',
 EO_GREEN:'Verde Este–Oeste',EO_YELLOW:'Amarillo Este–Oeste',EO_CLEAR:'Despeje Este–Oeste',
 PEDESTRIAN:'Fase peatonal',PEDESTRIAN_CLEAR:'Despeje peatonal'};
const MODO={degraded:['D','#607d8b','Degradado (plan fijo 40/40)'],automatic:['A','#2e7d32','Automático'],
 manual:['M','#6a1b9a','Manual']};
const esc=t=>String(t).replace(/[&<>"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));

const map=L.map('map',{preferCanvas:true});

// Mosaicos sin API key. Si el proveedor elegido falla, se pasa al siguiente automáticamente.
const ESRI='https://server.arcgisonline.com/ArcGIS/rest/services/';
const TILES=[
 {u:'https://tile.openstreetmap.org/{z}/{x}/{y}.png',o:{maxZoom:19,attribution:'&copy; OpenStreetMap'}},
 {u:ESRI+'Canvas/World_Light_Gray_Base/MapServer/tile/{z}/{y}/{x}',o:{maxNativeZoom:16,maxZoom:19,attribution:'Tiles &copy; Esri'}},
 {u:ESRI+'Canvas/World_Dark_Gray_Base/MapServer/tile/{z}/{y}/{x}',o:{maxNativeZoom:16,maxZoom:19,attribution:'Tiles &copy; Esri'}},
 {u:ESRI+'World_Imagery/MapServer/tile/{z}/{y}/{x}',o:{maxZoom:19,attribution:'Tiles &copy; Esri'}},
 {u:ESRI+'World_Street_Map/MapServer/tile/{z}/{y}/{x}',o:{maxZoom:19,attribution:'Tiles &copy; Esri'}}];
const ORDER=[BASE,4,0,1].filter((v,i,a)=>a.indexOf(v)===i);
let ti=0, capa=null, errs=0;
function usaMosaicos(i){
  if(capa) map.removeLayer(capa);
  const t=TILES[ORDER[i]]; errs=0;
  capa=L.tileLayer(t.u,t.o).addTo(map);
  capa.on('tileerror',()=>{ errs++; if(errs===8 && ti<ORDER.length-1){ ti++; usaMosaicos(ti); } });
}
usaMosaicos(0);

// Vista: se conserva entre sincronizaciones (localStorage) para que el mapa no "salte".
const bounds=L.latLngBounds(D.map(c=>[c.lat,c.lon]));
function ajusta(){ map.invalidateSize(); map.fitBounds(bounds.pad(0.25),{maxZoom:18,animate:false}); }
let saved=null, prevSel=null;
const claveVista='sgt_view2_'+VISTA, claveCruce='sgt_sel_'+VISTA;
try{ saved=JSON.parse(localStorage.getItem(claveVista)||'null'); prevSel=localStorage.getItem(claveCruce); }catch(e){}
if(saved && isFinite(saved.lat) && isFinite(saved.lng) && isFinite(saved.z))
  map.setView([saved.lat,saved.lng],saved.z,{animate:false});
else ajusta();
const selC=D.find(c=>c.id===SEL);
if(String(SEL)!==prevSel){
  try{ localStorage.setItem(claveCruce,String(SEL)); }catch(e){}
  if(selC && prevSel!==null) map.setView([selC.lat,selC.lon],Math.max(map.getZoom(),17),{animate:false});
}
map.on('moveend',()=>{ try{ const p=map.getCenter();
  localStorage.setItem(claveVista,JSON.stringify({lat:p.lat,lng:p.lng,z:map.getZoom()})); }catch(e){} });
function escala(){ const z=map.getZoom(); const s=Math.min(2.2,Math.max(.45,.25+(z-13)*.22));
  document.getElementById('map').style.setProperty('--s',s); }
map.on('zoomend',escala); escala();
setTimeout(()=>{ map.invalidateSize(); if(!saved) ajusta(); },300);

function pick(id){
  try{
    const b=[...window.parent.document.querySelectorAll('.st-key-selbtns button')]
      .find(e=>e.textContent.trim()==='sel-'+id);
    if(b) b.click();
  }catch(e){}
}

if(TRAMOS.length) map.attributionControl.addAttribution('Tráfico &copy; TomTom');
for(const tramo of TRAMOS){
  if(tramo.path.length < 2) continue;
  const label=document.createElement('span');
  label.textContent=tramo.label;
  L.polyline(tramo.path,{color:tramo.color,weight:5,opacity:.7}).addTo(map).bindTooltip(label);
}

const S=D.map(c=>({c,sec:c.sec,elapsed:0,q:[c.q[0],c.q[1]],credit:[0,0],G:{ns:c.gns,eo:c.geo}}));
function tip(s){
  const ph=phase(s.G,s.sec), m=MODO[s.c.mode];
  if(!s.c.live && VISTA==='aforo') return '<b>'+esc(s.c.name)+'</b><br>Esperando reproducción del aforo';
  const estado=s.c.live?esc(FASES[ph.n]||ph.n)+' · '+ph.left+' s':'Telemetría desactualizada';
  return '<b>'+esc(s.c.name)+'</b><br>'+estado+'<br>Cola NS '+s.q[0]+' · EO '+s.q[1]+' veh<br>'+
    'Modo: '+(m?m[2]:'—')+'<br>Verde N–S '+s.G.ns+' s · E–O '+s.G.eo+' s';
}
S.forEach(s=>{
  const m=MODO[s.c.mode]||['?','#999',''];
  const icon=L.divIcon({className:'mkwrap',iconSize:[46,46],iconAnchor:[23,23],
    html:'<div class="mk"><div class="ring"></div><div class="d ns"></div><div class="d eo"></div>'+
         '<div class="d pe"></div><div class="lb">'+s.c.id+'</div>'+
         '<div class="tag" style="background:'+m[1]+'">'+m[0]+'</div></div>'});
  s.m=L.marker([s.c.lat,s.c.lon],{icon}).addTo(map);
  s.m.bindTooltip(()=>tip(s),{direction:'top',offset:[0,-24]});
  s.m.on('click',()=>pick(s.c.id));
  const el=s.m.getElement();
  s.ring=el.querySelector('.ring'); s.dns=el.querySelector('.ns'); s.deo=el.querySelector('.eo');
  s.dpe=el.querySelector('.pe');
});

const Ctl=L.Control.extend({options:{position:'topright'},onAdd:function(){
  const d=L.DomUtil.create('div'); L.DomEvent.disableClickPropagation(d);
  const b1=L.DomUtil.create('div','btn',d); b1.textContent='Ver todos';
  b1.onclick=()=>map.fitBounds(bounds.pad(0.25),{maxZoom:18});
  const b2=L.DomUtil.create('div','btn',d); b2.textContent='Ir al cruce elegido';
  b2.onclick=()=>{ if(selC) map.setView([selC.lat,selC.lon],18); };
  return d; }});
map.addControl(new Ctl());
const Leg=L.Control.extend({options:{position:'bottomleft'},onAdd:function(){
  const d=L.DomUtil.create('div','leg');
  d.innerHTML='<b>Congestión</b><br><i style="background:#00c878"></i>Fluido<br>'+
   '<i style="background:#ffbe00"></i>Moderado<br><i style="background:#eb3232"></i>Congestionado<br>'+
   '<i style="background:#969696"></i>Sin datos vigentes<br>'+
   '<small>Luces: ↑ N–S · → E–O · ↓ peatón<br>Modo: D degradado · A automático · M manual</small>';
  return d; }});
map.addControl(new Leg());

function step(s){
  const ph=phase(s.G,s.sec), colors=[ph.ns,ph.eo];
  for(let i=0;i<2;i++){
    const arr=llegadas(s.c.rate[i],aforo,s.elapsed,i);
    avanzarCola(s.q,s.credit,i,arr,s.c.dis[i],colors[i]);
  }
  s.sec=(s.sec+1)%120;
  s.elapsed++;
}
function pinta(s){
  const live=s.c.live, ph=phase(s.G,s.sec), tot=s.q[0]+s.q[1];
  let ring='rgba(150,150,150,.30)';
  if(live){ ring=tot<10?'rgba(0,200,120,.35)':tot<25?'rgba(255,190,0,.40)':'rgba(235,50,50,.42)'; }
  s.ring.style.background=ring;
  s.ring.style.borderColor=s.c.id===SEL?'#fff':'transparent';
  s.ring.style.boxShadow=s.c.id===SEL?'0 0 0 3px #1976d2, 0 0 14px #1976d2':'none';
  const set=(el,col)=>{ el.style.background=col; el.style.boxShadow=col===OFF?'none':'0 0 9px '+col; };
  set(s.dns,live?COL[ph.ns]:OFF); set(s.deo,live?COL[ph.eo]:OFF);
  set(s.dpe,live&&ph.ped==='GREEN'?'#50a0ff':OFF);
  if(s.m.isTooltipOpen()) s.m.setTooltipContent(tip(s));
}
let acc=0, last=performance.now();
function actualiza(){
  if(reloj){
    const objetivo=reloj();
    S.forEach(s=>{ while(s.elapsed<objetivo) step(s); });
    S.forEach(pinta);
    return;
  }
  const now=performance.now(); acc+=SPEED*(now-last)/1000; last=now; if(acc>240) acc=240;
  while(acc>=1){ S.forEach(s=>{ if(s.c.live) step(s); }); acc-=1; }
  S.forEach(pinta);
}
actualiza();
setInterval(actualiza,200);
</script></body></html>"""


def datos_cruce(item, vpm):
    estado = item.get("state") or {}
    gns, geo = verdes_de(estado)
    colas = estado.get("queues") or [0, 0]
    grupos = {g["code"]: g for g in item.get("groups", [])}
    descarga = [grupos[c]["lanes"] * grupos[c]["discharge_vps"] if c in grupos else 0.5 for c in ("NS", "EO")]
    tasa = [vpm.get((item["id"], c), 10) / 60 for c in ("NS", "EO")]
    return {"id": item["id"], "name": item["name"], "lat": item["latitude"], "lon": item["longitude"],
            "gns": gns, "geo": geo, "sec": int(estado.get("second", 0)),
            "q": [int(colas[0]), int(colas[1])], "rate": tasa, "dis": descarga,
            "live": bool(item.get("telemetry_current")), "mode": estado.get("mode") or ""}


def html_mapa(datos, seleccionado, estilo_mapa, *, replay=None, segmentos=(), modo="sim"):
    config = {"data": datos, "selected": seleccionado, "speed": SIM_SPEED,
              "style": ESTILOS.index(estilo_mapa), "replay": replay,
              "segments": segmentos, "mode": modo}
    return MAPA_HTML.replace("__MOTOR__", MOTOR_JS).replace("__MAPCFG__", seguro_json(config))


def construir_mapa(items):
    trafico = api("GET", "/traffic_data", params={"limit": 100})
    vpm = {}  # observación más reciente por (cruce, grupo), en veh/min
    for fila in (trafico or {}).get("items", []):
        clave = (fila["intersection_id"], fila["group"])
        if clave not in vpm and fila["arrivals_vpm"] is not None:
            vpm[clave] = fila["arrivals_vpm"]
    datos = [datos_cruce(i, vpm) for i in items]
    return html_mapa(datos, identifier, estilo)


@st.fragment(run_every="5s")
def panel_mapa():
    datos = api("GET", "/intersections")
    if not datos:
        st.warning("Telemetría DESCONOCIDA. No hay confirmación actual del simulador.")
        return
    items = datos["items"]
    firma = (identifier, estilo,
             tuple((i["id"], bool(i["telemetry_current"]), verdes_de(i.get("state")),
                    (i.get("state") or {}).get("mode")) for i in items))
    html = html_cacheado("html_mapa", firma, lambda: construir_mapa(items), RESYNC_S)
    components.html(html, height=560)


@st.fragment(run_every="2s")
def panel_metricas():
    datos = api("GET", "/intersections")
    if not datos:
        return
    item = item_actual(datos["items"])
    if item is None:
        return
    estado = item.get("state") or {}
    vigente = item["telemetry_current"]
    if not vigente:
        st.warning("Telemetría DESACTUALIZADA. Los últimos colores no representan el estado actual.")
    colores = estado.get("colors") or {}
    colas = estado.get("queues") or [0, 0]
    gns, geo = verdes_de(estado)
    tarjetas = [
        ("Fase", FASES.get(colores.get("phase"), "—") if vigente else "Desconocida"),
        ("Norte–Sur", NOMBRE_LUZ.get(colores.get("NS"), "—") if vigente else "—"),
        ("Este–Oeste", NOMBRE_LUZ.get(colores.get("EO"), "—") if vigente else "—"),
        ("Cola Norte–Sur", f"{colas[0]} veh"),
        ("Cola Este–Oeste", f"{colas[1]} veh"),
        ("Modo", MODOS.get(estado.get("mode"), "—")),
        ("Verde N–S / E–O", f"{gns} s / {geo} s"),
    ]
    st.markdown('<div class="kp-fila">' + "".join(
        f'<div class="kp"><span>{t}</span><b>{v}</b></div>' for t, v in tarjetas) + "</div>",
        unsafe_allow_html=True)
    st.caption(f"Cruce {nombres[identifier]} · segundo {estado.get('second', '—')} de 120 del ciclo "
               f"{estado.get('cycle', '—')}. El reloj simulado corre más rápido que el real (SIM_SPEED).")
    modos = {(i.get("state") or {}).get("mode") for i in datos["items"] if i["telemetry_current"]}
    if modos == {"degraded"}:
        st.info("Todos los cruces están en **modo degradado** (plan fijo 40/40 s) porque todavía no hay un "
                "modelo promovido. Por eso los semáforos de todos los cruces se ven iguales. Para ver el "
                "control adaptativo hay que entrenar, evaluar y promover el modelo (sección «Entrenamiento "
                "y evaluación» del README) y reiniciar el servicio de IA.")


# ---------------------------------------------------------------------------
# Simulación del cruce seleccionado (coches y peatones dibujados en canvas)
# ---------------------------------------------------------------------------
SIM_HTML = """
<canvas id="c" width="420" height="420"
 style="background:#1d222c;border-radius:12px;display:block;width:100%;max-width:420px;height:auto"></canvas>
<div id="cmp" style="font:12px system-ui,sans-serif;color:#cfd6e2;margin-top:8px;line-height:1.5"></div>
<script>
__MOTOR__
const {cruce:C, speed:SPEED, replay:REPLAY, waiting:ESPERA} = __SIMCFG__;
const LIVE=C.live;
const G={ns:C.gns, eo:C.geo};
const G0={ns:40, eo:40};            // plan fijo de referencia
const RATE=C.rate, DIS=C.dis;
const reloj=REPLAY ? relojAforo(REPLAY,SPEED) : null;
const aforo=REPLAY ? REPLAY.conteos : null;
const finAforo=aforo ? aforo.length*60 : Infinity;
let second=C.sec, elapsed=0, q=C.q, credit=[0,0];
let qF=[q[0],q[1]], creditF=[0,0];  // misma demanda, pero con el plan fijo 40/40
const cv=document.getElementById('c'), x=cv.getContext('2d');
const W=420, LINE=144, GAP=28, MAXVIS=5;
const COL={GREEN:'#00e676',YELLOW:'#ffd600',RED:'#ff1744'};
const FASES={NS_GREEN:'Verde N–S',NS_YELLOW:'Amarillo N–S',NS_CLEAR:'Despeje N–S',EO_GREEN:'Verde E–O',
 EO_YELLOW:'Amarillo E–O',EO_CLEAR:'Despeje E–O',PEDESTRIAN:'Fase peatonal',PEDESTRIAN_CLEAR:'Despeje peatonal'};
const PAL=['#e53935','#1e88e5','#fdd835','#43a047','#fb8c00','#8e24aa','#eceff1','#26c6da','#90a4ae'];
const PEDC=['#ffcc80','#80cbc4','#ce93d8','#fff59d','#ef9a9a'];
const rnd=a=>a[Math.floor(Math.random()*a.length)];

function rr(a,b,w,h,r){x.beginPath();x.moveTo(a+r,b);x.arcTo(a+w,b,a+w,b+h,r);x.arcTo(a+w,b+h,a,b+h,r);
  x.arcTo(a,b+h,a,b,r);x.arcTo(a,b,a+w,b,r);x.closePath();}

const vis=[[],[]];   // coches esperando (0 = Norte–Sur, 1 = Este–Oeste)
let go=[];           // coches cruzando
let walkers=[];
const CW=[{x0:172,y0:156,x1:228,y1:156,ox:0,oy:1},{x0:172,y0:244,x1:228,y1:244,ox:0,oy:1},
          {x0:156,y0:172,x1:156,y1:228,ox:1,oy:0},{x0:244,y0:172,x1:244,y1:228,ox:1,oy:0}];
function newCar(d,p){return {d,p,v:0,color:rnd(PAL),brake:false};}
for(let i=0;i<2;i++){ const n=Math.min(q[i],MAXVIS); for(let k=0;k<n;k++) vis[i].push(newCar(i,LINE-14-GAP*k)); }

function simStep(animar=true){
  const ph=phase(G,second), colors=[ph.ns,ph.eo];
  const phF=phase(G0,second), colorsF=[phF.ns,phF.eo];
  for(let i=0;i<2;i++){
    const arr=llegadas(RATE[i],aforo,elapsed,i);
    const served=avanzarCola(q,credit,i,arr,DIS[i],colors[i]);
    avanzarCola(qF,creditF,i,arr,DIS[i],colorsF[i]);
    if(!animar) continue;
    for(let k=0;k<served && vis[i].length;k++){
      const car=vis[i].shift();
      const first=go.filter(g=>g.d===i).reduce((m,g)=>Math.min(m,g.p),9999);
      if(first-car.p>=GAP){ car.v=Math.max(car.v,1.5); go.push(car); }
    }
    while(vis[i].length<Math.min(q[i],MAXVIS)) vis[i].push(newCar(i,-30));
  }
  second=(second+1)%120;
  elapsed++;
}

function drawCar(cx,cy,ang,color,brake){
  x.save(); x.translate(cx,cy); x.rotate(ang);
  x.fillStyle='rgba(0,0,0,.35)'; rr(-12,-4,25,13,4); x.fill();                 // sombra
  x.fillStyle='#0b0b0d';                                                         // llantas
  x.fillRect(-9,-8,6,3); x.fillRect(5,-8,6,3); x.fillRect(-9,5,6,3); x.fillRect(5,5,6,3);
  x.fillStyle=color; rr(-12,-6,24,12,4); x.fill();                               // carrocería
  x.fillStyle='rgba(255,255,255,.18)'; rr(-12,-6,24,5,3); x.fill();              // brillo
  x.fillStyle='rgba(18,28,42,.92)'; rr(-5,-4.5,11,9,2); x.fill();                // cristales
  x.fillStyle=color; rr(-3.5,-3,7,6,2); x.fill();                                // techo
  x.fillStyle='#fff7b0'; x.fillRect(10,-5,2,3); x.fillRect(10,2,2,3);            // faros
  if(brake){ x.shadowColor='#ff2020'; x.shadowBlur=8; }
  x.fillStyle=brake?'#ff3030':'#7a1010'; x.fillRect(-12,-5,2,3); x.fillRect(-12,2,2,3);  // luces traseras
  x.restore();
}
function housing(cx,cy,vertical,state){
  x.save(); x.fillStyle='#0d0f14'; x.strokeStyle='#555b66'; x.lineWidth=1;
  if(vertical) rr(cx-9,cy-23,18,46,5); else rr(cx-23,cy-9,46,18,5);
  x.fill(); x.stroke();
  const names=['RED','YELLOW','GREEN'], dim={RED:'#3a1a1a',YELLOW:'#3a3515',GREEN:'#153a22'};
  names.forEach((n,k)=>{
    const px=vertical?cx:cx+(k-1)*14, py=vertical?cy+(k-1)*14:cy, on=(state===n);
    x.beginPath(); x.arc(px,py,5.5,0,7);
    if(on){ x.shadowColor=COL[n]; x.shadowBlur=14; x.fillStyle=COL[n]; } else { x.shadowBlur=0; x.fillStyle=dim[n]; }
    x.fill(); x.shadowBlur=0;
  });
  x.restore();
}

function scene(ph){
  x.fillStyle='#1d222c'; x.fillRect(0,0,W,W);
  x.fillStyle='#272e3b';
  [[10,10],[250,10],[10,250],[250,250]].forEach(([a,b])=>{ rr(a,b,150,150,12); x.fill(); });
  x.fillStyle='rgba(255,255,255,.05)';                                           // ventanas
  [[10,10],[250,10],[10,250],[250,250]].forEach(([a,b])=>{
    for(let i=0;i<5;i++)for(let j=0;j<5;j++) x.fillRect(a+14+i*27,b+14+j*27,14,14); });
  x.fillStyle='#3a4150'; x.fillRect(160,0,80,W); x.fillRect(0,160,W,80);          // aceras
  x.fillStyle='#2b2f3a'; x.fillRect(170,0,60,W); x.fillRect(0,170,W,60);          // calzada
  x.strokeStyle='#e0b400'; x.lineWidth=2; x.setLineDash([10,8]); x.beginPath();
  x.moveTo(200,0); x.lineTo(200,144); x.moveTo(200,256); x.lineTo(200,W);
  x.moveTo(0,200); x.lineTo(144,200); x.moveTo(256,200); x.lineTo(W,200); x.stroke(); x.setLineDash([]);
  x.fillStyle='#f2f2f2';                                                         // líneas de alto
  x.fillRect(170,LINE,30,3); x.fillRect(LINE,200,3,30); x.fillRect(200,254,30,3); x.fillRect(254,170,3,30);
  x.fillStyle=ph.ped==='GREEN'?'rgba(255,255,255,.75)':'rgba(255,255,255,.30)';  // cebras
  for(let i=0;i<6;i++){ x.fillRect(172+i*10,150,6,12); x.fillRect(172+i*10,238,6,12);
                        x.fillRect(150,172+i*10,12,6); x.fillRect(238,172+i*10,12,6); }
}

const cmp=document.getElementById('cmp');
function pintaCmp(){
  if(ESPERA) return;
  const a=q[0]+q[1], b=qF[0]+qF[1];
  let t='Cola total con las <b>mismas llegadas</b>: plan en ejecución (N–S '+G.ns+' s / E–O '+G.eo+' s) <b>'+a+
        '</b> veh · plan fijo 40/40 <b>'+b+'</b> veh.<br>';
  if(G.ns===G0.ns && G.eo===G0.eo) t+='Es el mismo plan, por eso no hay diferencia.';
  else { const d=b-a;
    t+=d>0?'El plan en ejecución tiene '+d+' veh menos en cola.':d<0?'El plan fijo tendría '+(-d)+' veh menos en cola.':'Sin diferencia por ahora.'; }
  if(REPLAY){
    const duracion=elapsed+' / '+finAforo+' s del aforo';
    t+='<br><span style="opacity:.75">'+
       (elapsed===finAforo?'Reproducción finalizada · ':'Reproduciendo · ')+duracion+'</span>';
  } else {
    t+=' <span style="opacity:.6">(se reinicia en cada sincronización)</span>';
  }
  cmp.innerHTML=t;
}

let acc=0, n=0;
function avanzarReloj(){
  if(!LIVE) return;
  if(reloj){
    const objetivo=reloj(), salto=objetivo-elapsed>20;
    while(elapsed<objetivo) simStep(!salto);
    if(salto){
      go=[]; walkers=[];
      for(let i=0;i<2;i++) vis[i]=Array.from({length:Math.min(q[i],MAXVIS)},
        (_,k)=>newCar(i,LINE-14-GAP*k));
    }
  } else {
    acc+=SPEED*0.033; if(acc>200) acc=200;
    while(acc>=1){ simStep(); acc-=1; }
  }
}
function frame(){
  avanzarReloj();
  const ph=phase(G,second), colors=[ph.ns,ph.eo];
  if(LIVE && elapsed<finAforo){
    for(let i=0;i<2;i++) vis[i].forEach((car,k)=>{
      const tp=LINE-14-GAP*k, dx=tp-car.p;
      car.p+=Math.max(-4,Math.min(4,dx*0.2));
      car.brake=(colors[i]!=='GREEN' && dx<10) || dx>1.5;
    });
    go.forEach(g=>{ g.v=Math.min(g.v+0.3,5.5); g.p+=g.v; g.brake=false; });
    go=go.filter(g=>g.p<W+40);
    if(ph.ped==='GREEN' && Math.random()<0.10){
      walkers.push({w:rnd(CW),t:0,dir:Math.random()<.5,sp:0.012+Math.random()*0.006,off:(Math.random()-.5)*8,color:rnd(PEDC)});
    }
    walkers.forEach(p=>p.t+=p.sp); walkers=walkers.filter(p=>p.t<1);
  }
  scene(ph);
  housing(240,112,true,ph.ns); housing(112,238,false,ph.eo);
  x.fillStyle='#9aa4b2'; x.font='10px system-ui,sans-serif'; x.textAlign='center';
  x.fillText('N–S',240,82); x.fillText('E–O',112,262); x.textAlign='left';
  for(let i=0;i<2;i++){
    vis[i].forEach(c=>{ if(i===0) drawCar(185,c.p,Math.PI/2,c.color,c.brake); else drawCar(c.p,215,0,c.color,c.brake); });
    if(q[i]>MAXVIS){ x.fillStyle='#fff'; x.font='bold 12px system-ui,sans-serif';
      if(i===0) x.fillText('+'+(q[i]-MAXVIS),150,12); else x.fillText('+'+(q[i]-MAXVIS),4,168); }
  }
  go.forEach(c=>{ if(c.d===0) drawCar(185,c.p,Math.PI/2,c.color,false); else drawCar(c.p,215,0,c.color,false); });
  walkers.forEach(p=>{
    const f=p.dir?p.t:1-p.t, px=p.w.x0+(p.w.x1-p.w.x0)*f+p.w.ox*p.off, py=p.w.y0+(p.w.y1-p.w.y0)*f+p.w.oy*p.off;
    x.fillStyle='rgba(0,0,0,.4)'; x.beginPath(); x.arc(px+1,py+1,4,0,7); x.fill();
    x.fillStyle=p.color; x.beginPath(); x.arc(px,py,3.6,0,7); x.fill();
  });
  x.fillStyle='rgba(0,0,0,.55)'; rr(8,W-34,W-16,26,8); x.fill();
  x.fillStyle=ph.ped==='GREEN'?'#50a0ff':(ph.ns!=='RED'?COL[ph.ns]:(ph.eo!=='RED'?COL[ph.eo]:'#ff1744'));
  x.beginPath(); x.arc(24,W-21,6,0,7); x.fill();
  x.fillStyle='#fff'; x.font='13px system-ui,sans-serif';
  x.fillText((FASES[ph.n]||ph.n)+' · '+ph.left+' s · seg '+second+'/120',38,W-16);
  if(!LIVE){ x.fillStyle='rgba(0,0,0,.6)'; x.fillRect(0,0,W,W); x.fillStyle='#fff';
    x.font='16px system-ui,sans-serif'; x.textAlign='center';
    x.fillText(ESPERA||'Telemetría desactualizada',210,210); x.textAlign='left'; }
  if(++n%10===0) pintaCmp();
}
frame();
pintaCmp();
setInterval(frame,33);
</script>
"""


def html_sim(datos, *, replay=None, espera=None):
    config = {"cruce": datos, "speed": SIM_SPEED, "replay": replay, "waiting": espera}
    return SIM_HTML.replace("__MOTOR__", MOTOR_JS).replace("__SIMCFG__", seguro_json(config))


def construir_sim(item):
    trafico = api("GET", "/traffic_data", params={"intersection_id": identifier, "limit": 60})
    vpm = {}
    for fila in (trafico or {}).get("items", []):
        if fila["group"] in ("NS", "EO") and fila["arrivals_vpm"] is not None:
            vpm.setdefault((identifier, fila["group"]), fila["arrivals_vpm"])
    return html_sim(datos_cruce(item, vpm))


def mostrar_tiempos(verdes, titulo):
    st.write(titulo)
    st.dataframe(pd.DataFrame([
        {"Dirección": nombre, "Verde (s)": verdes[clave], "Amarillo (s)": 3,
         "Rojo (s)": 117 - verdes[clave]}
        for nombre, clave in (("Norte–Sur", "ns"), ("Este–Oeste", "eo"))
    ]), hide_index=True, width="stretch")


@st.fragment(run_every="5s")
def panel_detalle():
    datos = api("GET", "/intersections")
    if not datos:
        return
    item = item_actual(datos["items"])
    if item is None:
        return
    st.markdown(f"**Simulación del cruce {nombres[identifier]}**")
    firma = (identifier, bool(item["telemetry_current"]), verdes_de(item.get("state")))
    components.html(html_cacheado("html_sim", firma, lambda: construir_sim(item), RESYNC_S), height=490)
    estado = item.get("state") or {}
    verdes = estado.get("green_s")
    if verdes:
        mostrar_tiempos(verdes, "Tiempos del plan en ejecución" if item["telemetry_current"]
                        else "Tiempos del último plan confirmado")
        st.caption(estado.get("reason", "Sin plan aplicado"))
        st.caption("Ciclo de 120 s y fase peatonal exclusiva de 20 s. En automático, la demanda "
                   "pronosticada ajusta los verdes; en degradado se conserva el plan fijo 40/40.")


# ---------------------------------------------------------------------------
# Datos de tráfico (tabla, gráfica, exportación)
# ---------------------------------------------------------------------------
@st.fragment(run_every="5s")
def panel_datos():
    trafico = api("GET", "/traffic_data", params={"intersection_id": identifier, "limit": 60})
    if not (trafico and trafico["items"]):
        st.info("Aún no hay observaciones de tráfico para este cruce.")
        return
    tabla = pd.DataFrame(trafico["items"])
    tabla["window_end"] = pd.to_datetime(tabla.window_end, utc=True).dt.tz_convert("America/Mexico_City")
    grafica = tabla.pivot_table(index="window_end", columns="group", values="arrivals_vpm", aggfunc="first")
    st.line_chart(grafica, y_label="Llegadas (veh/min)")
    st.dataframe(tabla[["group", "window_end", "arrivals_vpm", "speed_kmh", "weather",
                        "source", "quality", "current"]], width="stretch", hide_index=True)
    st.download_button("Exportar observaciones JSON", json.dumps(trafico, ensure_ascii=False, indent=2),
                       file_name=f"trafico-sintetico-{identifier}.json", mime="application/json")


def controles_aforo():
    with st.sidebar.form("cargar_aforo"):
        archivo = st.file_uploader("CSV de aforo del cruce piloto", type="csv")
        st.caption("Columnas `inicio,llegadas_ns,llegadas_eo`. Incluye la zona horaria en cada minuto.")
        if st.form_submit_button("Cargar aforo"):
            try:
                if archivo is None:
                    raise ValueError("Selecciona el CSV de aforo.")
                if archivo.size > 1_000_000:
                    raise ValueError("El CSV debe pesar como máximo 1 MB.")
                filas = cargar_aforo(archivo.getvalue())
            except ValueError as exc:
                st.error(str(exc))
            else:
                st.session_state.aforo_filas = filas
                st.session_state.pop("aforo_replay", None)
    filas = st.session_state.get("aforo_filas", [])
    if filas:
        st.sidebar.caption(f"Aforo cargado · {len(filas)} min")
    verde = st.sidebar.slider("Verde Norte–Sur del próximo ensayo (s)", 20, 60, 40)
    st.sidebar.caption(f"Verde Este–Oeste · {80 - verde} s")
    if st.sidebar.button("Reproducir aforo", disabled=not filas):
        st.session_state.aforo_replay = {
            "id": uuid4().hex, "verde_ns": verde, "conteos": [[ns, eo] for _, ns, eo in filas],
        }
    return filas


@st.fragment(run_every="30s")
def panel_aforo(estilo_mapa):
    tomtom = api("GET", "/traffic/live")
    centro = tomtom["center"] if tomtom else {"latitude": 19.42568, "longitude": -99.15462}
    nombre = tomtom["location"] if tomtom else "Entorno de Metro Cuauhtémoc"
    segmentos = tomtom["segments"] if tomtom and tomtom["configured"] else []
    tramos, filas_tomtom = datos_tomtom(segmentos)

    replay = st.session_state.get("aforo_replay")
    verde_ns = replay["verde_ns"] if replay else 40
    verdes = {"ns": verde_ns, "eo": 80 - verde_ns}
    cruce = datos_cruce({
        "id": 1, "name": nombre, "telemetry_current": bool(replay), **centro,
        "state": {"green_s": verdes, "mode": "manual" if replay else ""},
    }, {})

    col_mapa, col_detalle = st.columns([3, 2])
    with col_mapa:
        components.html(html_mapa([cruce], cruce["id"], estilo_mapa, replay=replay,
                                  segmentos=tramos, modo="aforo"), height=560)
        st.caption("El marcador muestra el semáforo y las colas del ensayo. "
                   "Las líneas muestran las últimas velocidades consultadas a TomTom.")
    with col_detalle:
        st.markdown(f"**Simulación del cruce · {nombre}**")
        espera = None if replay else (
            "Pulsa Reproducir aforo" if st.session_state.get("aforo_filas") else "Carga un aforo CSV"
        )
        components.html(html_sim(cruce, replay=replay, espera=espera), height=490)
        if replay:
            mostrar_tiempos(verdes, "Tiempos del plan de ensayo")
            st.caption(f"Reproducción a {SIM_SPEED:g}×. Colas iniciales en cero y capacidad supuesta de "
                       "0.5 veh/s por grupo para ambos planes.")

    st.subheader("Tráfico reciente · TomTom")
    if filas_tomtom:
        if any(segmento["status"] != "current" for segmento in segmentos):
            st.warning("TomTom no entregó datos vigentes para todos los tramos.")
        st.dataframe(pd.DataFrame(filas_tomtom), hide_index=True, width="stretch")
        st.caption("Colores por velocidad respecto a la referencia. Verde ≥ 80 %, naranja de 50 % a menos de "
                   "80 %, rojo < 50 % o cierre y gris para lecturas vencidas o sin referencia.")
    elif tomtom:
        st.info("Configura TOMTOM_API_KEY en el backend y reinicia la API para consultar los tramos.")


# ---------------------------------------------------------------------------
# Distribución de la página
# ---------------------------------------------------------------------------
fuente_trafico = st.sidebar.radio("Fuente de tráfico", ["Simulado", "Real (TomTom)"],
                                  key="fuente_trafico")
if fuente_trafico == "Real (TomTom)":
    estilo_aforo = st.sidebar.selectbox("Estilo del mapa", ESTILOS)
    filas_aforo = controles_aforo()
    panel_aforo(estilo_aforo)
    if filas_aforo:
        st.subheader("Llegadas del aforo")
        tabla_aforo = pd.DataFrame(filas_aforo, columns=["Inicio", "Norte–Sur", "Este–Oeste"])
        tabla_aforo["Inicio"] = tabla_aforo["Inicio"].dt.tz_convert("America/Mexico_City")
        st.line_chart(tabla_aforo, x="Inicio", y=["Norte–Sur", "Este–Oeste"], y_label="Llegadas (veh/min)")
        st.dataframe(tabla_aforo, hide_index=True, width="stretch")
    st.stop()

catalog = api("GET", "/intersections")
if not catalog or not catalog["items"]:
    st.info("No hay intersecciones disponibles. Comprueba que el backend y el simulador estén iniciados.")
    st.stop()

ids = [i["id"] for i in catalog["items"]]
nombres = {i["id"]: f"{i['id']} · {i['name']}" for i in catalog["items"]}
if st.session_state.get("sel_id") not in ids:
    st.session_state.sel_id = ids[0]
identifier = st.sidebar.selectbox("Intersección simulada", ids, key="sel_id", format_func=nombres.get)
estilo = st.sidebar.selectbox("Estilo del mapa", ESTILOS)
st.sidebar.caption("Las fechas se presentan en America/Mexico_City; persistencia en UTC.")
st.sidebar.markdown(
    "**Cómo leer el mapa**\n\n"
    "- Luz superior para Norte–Sur, derecha para Este–Oeste e inferior para peatones. "
    "El azul indica paso peatonal.\n"
    "- El anillo indica la congestión. Verde para fluido, amarillo para moderado, rojo para "
    "congestionado y gris para datos vencidos.\n"
    "- La letra indica el modo. **D** degradado (plan fijo 40/40), **A** automático y **M** manual.\n"
    "- Arrastra para moverte, usa la rueda para acercar y haz clic en un cruce para seleccionarlo."
)

# El mapa pulsa el botón oculto del cruce elegido.
with st.container(key="selbtns"):
    for _id in ids:
        st.button(f"sel-{_id}", key=f"selbtn_{_id}", on_click=_elegir, args=(_id,))
st.markdown("<style>.st-key-selbtns{display:none}</style>", unsafe_allow_html=True)

col_mapa, col_detalle = st.columns([3, 2])
with col_mapa:
    panel_mapa()
    panel_metricas()
with col_detalle:
    panel_detalle()

st.subheader("Observaciones de tráfico")
panel_datos()

st.subheader("Intervención del administrador")
with st.form("manual"):
    green_ns = st.slider("Verde NS (s)", 20, 60, 40)
    st.write(f"Verde EO: {80-green_ns} s · fase peatonal obligatoria: 20 s · ciclo: 120 s")
    reason = st.text_input("Motivo de la intervención", max_chars=300)
    cycles = st.number_input("Vigencia en ciclos", min_value=1, max_value=10, value=1)
    submit = st.form_submit_button("Solicitar intervención al siguiente ciclo")
if submit:
    # Consultar la versión en el momento del envío para reducir conflictos evitables.
    current = api("GET", "/intersections")
    if current:
        item = item_actual(current["items"])
        result = api("POST", "/manual_override", json={
            "intersection_id": identifier, "previous_version": item["plan_version"],
            "green_ns": green_ns, "green_eo": 80 - green_ns,
            "reason": reason, "duration_cycles": int(cycles)})
        if result:
            st.success(f"Solicitud {result['id']}: {result['status']}. "
                       "La aplicación requiere confirmación del trabajador.")
            st.json(result)

left, right = st.columns(2)
if left.button("Obtener propuesta del modelo"):
    current = api("GET", "/intersections")
    if current:
        item = item_actual(current["items"])
        result = api("POST", "/predict_light", json={"intersection_id": identifier,
                                                    "previous_version": item["plan_version"]})
        if result:
            st.json(result)
if right.button("Volver al automático al siguiente ciclo"):
    current = api("GET", "/intersections")
    if current:
        item = item_actual(current["items"])
        result = api("POST", "/automatic", json={"intersection_id": identifier,
                                                "previous_version": item["plan_version"]})
        if result:
            st.success("Retorno solicitado; el modo confirmado cambiará al siguiente ciclo.")

with st.expander("Auditoría reciente"):
    if st.button("Consultar auditoría"):
        result = api("GET", "/audit", params={"limit": 30})
        if result:
            st.dataframe(pd.DataFrame(result["items"]), width="stretch")

function phase(G, s) {
  const phases = [
    ["NS_GREEN", G.ns, "GREEN", "RED", "RED"], ["NS_YELLOW", 3, "YELLOW", "RED", "RED"],
    ["NS_CLEAR", 2, "RED", "RED", "RED"], ["EO_GREEN", G.eo, "RED", "GREEN", "RED"],
    ["EO_YELLOW", 3, "RED", "YELLOW", "RED"], ["EO_CLEAR", 2, "RED", "RED", "RED"],
    ["PEDESTRIAN", 20, "RED", "RED", "GREEN"], ["PEDESTRIAN_CLEAR", 10, "RED", "RED", "RED"],
  ];
  for (const [n, duration, ns, eo, ped] of phases) {
    if (s < duration) return {n, ns, eo, ped, left: duration-s};
    s -= duration;
  }
  return {n: "?", ns: "RED", eo: "RED", ped: "RED", left: 0};
}

function llegadas(tasa, aforo, segundo, direccion) {
  if (aforo === null) return Math.floor(tasa) + (Math.random() < tasa % 1 ? 1 : 0);
  const total = aforo[Math.floor(segundo / 60)][direccion];
  const dentro = segundo % 60;
  // Distribución determinista con el mismo total del minuto aforado.
  return Math.floor((dentro + 1) * total / 60) - Math.floor(dentro * total / 60);
}

function avanzarCola(cola, credito, i, llegan, descarga, color) {
  cola[i] += llegan;
  if (color !== "GREEN") {
    credito[i] = 0;
    return 0;
  }
  credito[i] += descarga;
  const capacidad = Math.floor(credito[i]);
  credito[i] -= capacidad;
  const salen = Math.min(cola[i], capacidad);
  cola[i] -= salen;
  return salen;
}

function relojAforo(replay, velocidad) {
  const ahora = () => performance.timeOrigin + performance.now();
  let inicio = ahora();
  try {
    const previo = JSON.parse(sessionStorage.getItem("sgt_aforo") || "null");
    if (previo && previo.id === replay.id) inicio = previo.inicio;
    else sessionStorage.setItem("sgt_aforo", JSON.stringify({id: replay.id, inicio}));
  } catch {
    // En un iframe con almacenamiento bloqueado, usar su propio reloj.
  }
  const duracion = replay.conteos.length * 60;
  return () => Math.min(duracion, Math.floor(Math.max(0, ahora() - inicio) * velocidad / 1000));
}

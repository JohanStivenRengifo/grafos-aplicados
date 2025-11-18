
//  MAPA Y MARCADORES

const map = L.map('map').setView([2.4448, -76.6147], 14);

L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    maxZoom: 19
}).addTo(map);

// Datos enviados desde Flask
const ambulancias = window.DATA.ambulancias;
const hospitales = window.DATA.hospitales;

// Icono ambulancia
const iconAmb = L.icon({
    iconUrl: "https://cdn-icons-png.flaticon.com/512/296/296214.png",
    iconSize: [32, 32]
});

// Icono hospital
const iconHos = L.icon({
    iconUrl: "https://cdn-icons-png.flaticon.com/512/296/296071.png",
    iconSize: [32, 32]
});

// Guardar marcadores de ambulancias
const markersAmb = {};

// Crear marcadores de ambulancias
ambulancias.forEach(a => {
    markersAmb[a.id] = L.marker([a.pos.lat, a.pos.lon], { icon: iconAmb })
        .addTo(map)
        .bindPopup(`Ambulancia ${a.id}`);
});

// Crear marcadores de hospitales
hospitales.forEach(h => {
    L.marker([h.lat, h.lon], { icon: iconHos })
        .addTo(map)
        .bindPopup(`${h.nombre} (Espera: ${h.tiempo_espera} min)`);
});

// Capa para las rutas
const rutasLayer = L.layerGroup().addTo(map);


//  SOCKET.IO


const socket = io();

// Actualiza posiciones
socket.on("update_position", data => {
    const m = markersAmb[data.ambulancia];
    if (m) {
        m.setLatLng([data.lat, data.lon]);
        m.bindPopup(`${data.ambulancia} → ${data.hospital}`).openPopup();
    }
});

// Dibuja rutas nuevas
socket.on("update_rutas", rutas => {
    rutasLayer.clearLayers();

    rutas.forEach(r => {
        L.polyline(r.nodos, {
            color: r.color,
            weight: 4
        })
        .bindTooltip(`${r.ambulancia} → ${r.hospital}<br>Tiempo total: ${r.tiempo_total} min`)
        .addTo(rutasLayer);
    });
});

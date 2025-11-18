
//  MAPA Y MARCADORES

const map = L.map('map', {
    center: [2.4448, -76.6147],
    zoom: 14,
    zoomControl: true
});

const osmLayer = L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
    maxZoom: 19
}).addTo(map);

setTimeout(() => {
    const tilePane = map.getPane('tilePane');
    if (tilePane) {
        tilePane.style.filter = 'invert(1) hue-rotate(180deg) brightness(0.85)';
    }
}, 100);

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
    markersAmb[a.id] = L.marker([a.lat, a.lon], { icon: iconAmb })
        .addTo(map)
        .bindPopup(`Ambulancia ${a.id}<br>Especialidad: ${a.especialidad || 'N/A'}`);
});

// Crear marcadores de hospitales
hospitales.forEach(h => {
    const ocupacion = h.porcentaje_ocupacion || 0;
    const puedeRecibir = h.puede_recibir !== undefined ? h.puede_recibir : true;
    const estadoColor = puedeRecibir ? (ocupacion < 70 ? 'green' : 'orange') : 'red';
    
    L.marker([h.lat, h.lon], { 
        icon: iconHos,
        zIndexOffset: 500
    })
    .addTo(map)
    .bindPopup(`
        <strong>${h.nombre}</strong><br>
        Espera: ${h.espera} min<br>
        Capacidad: ${h.pacientes_actuales || 0}/${h.capacidad_max || 'N/A'}<br>
        Ocupación: ${ocupacion}%<br>
        Estado: <span style="color: ${estadoColor}">${puedeRecibir ? 'Disponible' : 'Lleno'}</span>
    `);
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
        m.bindPopup(`${data.ambulancia} -> ${data.hospital}`).openPopup();
    }
});

// Caché de rutas en el cliente
const cacheRutas = new Map();
const MAX_CACHE_SIZE = 200;
const CACHE_TTL = 300000;

function generarClaveCache(origen, destino) {
    return `${origen[0].toFixed(6)},${origen[1].toFixed(6)};${destino[0].toFixed(6)},${destino[1].toFixed(6)}`;
}

function obtenerDeCache(origen, destino) {
    const clave = generarClaveCache(origen, destino);
    const cached = cacheRutas.get(clave);
    if (cached && Date.now() - cached.timestamp < CACHE_TTL) {
        return cached.resultado;
    }
    if (cached) {
        cacheRutas.delete(clave);
    }
    return null;
}

function guardarEnCache(origen, destino, resultado) {
    const clave = generarClaveCache(origen, destino);
    if (cacheRutas.size >= MAX_CACHE_SIZE) {
        const primeraClave = cacheRutas.keys().next().value;
        cacheRutas.delete(primeraClave);
    }
    cacheRutas.set(clave, {
        resultado: resultado,
        timestamp: Date.now()
    });
}

let debounceTimer = null;

function obtenerRutaDetallada(origen, destino, callback) {
    const resultadoCache = obtenerDeCache(origen, destino);
    if (resultadoCache) {
        callback(...resultadoCache);
        return;
    }
    
    if (debounceTimer) {
        clearTimeout(debounceTimer);
    }
    
    debounceTimer = setTimeout(() => {
        const url = `https://router.project-osrm.org/route/v1/driving/${origen[1]},${origen[0]};${destino[1]},${destino[0]}?overview=full&geometries=geojson`;
        
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), 10000);
        
        fetch(url, {
            method: 'GET',
            mode: 'cors',
            headers: {
                'Accept': 'application/json'
            },
            signal: controller.signal
        })
            .then(response => {
                clearTimeout(timeoutId);
                if (!response.ok) return null;
                return response.json();
            })
            .then(data => {
                if (data && data.code === 'Ok' && data.routes && data.routes.length > 0) {
                    const route = data.routes[0];
                    const geometry = route.geometry;
                    if (geometry && geometry.coordinates && geometry.coordinates.length > 2) {
                        const coords = geometry.coordinates.map(c => [c[1], c[0]]);
                        const distancia = route.distance / 1000;
                        const tiempo = route.duration / 60;
                        const resultado = [coords, distancia, tiempo];
                        guardarEnCache(origen, destino, resultado);
                        callback(coords, distancia, tiempo);
                    } else {
                        callback(null, null, null);
                    }
                } else {
                    callback(null, null, null);
                }
            })
            .catch((error) => {
                clearTimeout(timeoutId);
                if (error.name !== 'AbortError') {
                    console.warn('Error obteniendo ruta OSRM:', error);
                }
                callback(null, null, null);
            });
    }, 300);
}

let rutasPendientes = new Set();

socket.on("update_rutas", rutas => {
    rutasLayer.clearLayers();
    rutasPendientes.clear();
    
    if (!rutas || rutas.length === 0) {
        return;
    }
    
    rutas.forEach(r => {
        if (!r.nodos || r.nodos.length < 2) {
            return;
        }
        
        const dibujarRuta = (nodos, tiempo) => {
            if (!nodos || nodos.length < 2) {
                return;
            }
            
            try {
                const polyline = L.polyline(nodos, {
                    color: r.color || 'blue',
                    weight: 5,
                    opacity: 0.8,
                    dashArray: '10, 5'
                })
                .bindTooltip(`${r.ambulancia} -> ${r.hospital}<br>Tiempo total: ${tiempo ? tiempo.toFixed(1) : r.tiempo_total} min`, {
                    permanent: false,
                    direction: 'auto'
                })
                .addTo(rutasLayer);
            } catch (error) {
                console.error(`Error dibujando ruta:`, error);
            }
        };
        
        if (r.nodos.length === 2) {
            const amb = ambulancias.find(a => a.id === r.ambulancia);
            const hosp = hospitales.find(h => h.nombre === r.hospital);
            
            if (amb && hosp) {
                const claveRuta = `${r.ambulancia}-${r.hospital}`;
                if (!rutasPendientes.has(claveRuta)) {
                    rutasPendientes.add(claveRuta);
                    obtenerRutaDetallada(
                        [amb.lon, amb.lat],
                        [hosp.lon, hosp.lat],
                        (coords, distancia, tiempo) => {
                            rutasPendientes.delete(claveRuta);
                            if (coords && coords.length > 2) {
                                dibujarRuta(coords, tiempo);
                            } else {
                                dibujarRuta(r.nodos, null);
                            }
                        }
                    );
                } else {
                    dibujarRuta(r.nodos, null);
                }
            } else {
                dibujarRuta(r.nodos, null);
            }
        } else {
            dibujarRuta(r.nodos, null);
        }
    });
});

// Capa para el grafo
const grafoLayer = L.layerGroup().addTo(map);

// Actualizar grafo
socket.on("update_grafo", grafoData => {
    grafoLayer.clearLayers();
    
    if (!grafoData || grafoData.length === 0) {
        return;
    }
    
    grafoData.forEach(g => {
        if (g.ruta && Array.isArray(g.ruta) && g.ruta.length > 1) {
            try {
                L.polyline(g.ruta, {
                    color: g.color || 'red',
                    weight: 4,
                    opacity: 0.7
                }).addTo(grafoLayer);
                
                if (g.origen && g.destino) {
                    L.marker([g.origen.lat, g.origen.lon], {
                        icon: iconAmb,
                        zIndexOffset: 1000
                    }).addTo(grafoLayer).bindPopup(`Origen: ${g.origen.id}`);
                    
                    L.marker([g.destino.lat, g.destino.lon], {
                        icon: iconHos,
                        zIndexOffset: 1000
                    }).addTo(grafoLayer).bindPopup(`Destino: ${g.destino.id}`);
                }
            } catch (error) {
                console.error("Error dibujando grafo:", error);
            }
        }
    });
});

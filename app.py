import sys
import hashlib
from collections import OrderedDict

try:
    from flask import Flask, render_template, Response
    from flask_socketio import SocketIO
    from clases import (Nodo, Hospital, Ruta, Ambulancia, Via, 
                       ListaEnlazada, ArbolBinarioBusqueda, Grafo)
    import requests
    import threading
    import time
    import random
    import math
    from concurrent.futures import ThreadPoolExecutor, as_completed
except ImportError as e:
    print(f"Error: Faltan dependencias. Ejecuta: pip install flask flask-socketio requests")
    sys.exit(1)

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

# ----- CONFIGURACIÓN INICIAL -----
hospitales = [
    Hospital("Hospital Universitario San José", 2.4526403, -76.600117, tiempo_espera=3, especialidades=["Cardiología", "Trauma"], capacidad_max=25, pacientes_actuales=random.randint(0, 18)),
    Hospital("Hospital Susana López de Valencia", 2.43728, -76.6193, tiempo_espera=4, especialidades=["Pediatría", "Ginecología"], capacidad_max=20, pacientes_actuales=random.randint(0, 15)),
    Hospital("Hospital Toribio Maya", 2.48527, -76.6, tiempo_espera=3, especialidades=["General", "Urgencias"], capacidad_max=22, pacientes_actuales=random.randint(0, 16)),
    Hospital("Clínica Santa Gracia", 2.4595, -76.603, tiempo_espera=4, especialidades=["General", "Urgencias"], capacidad_max=18, pacientes_actuales=random.randint(0, 12)),
    Hospital("Clínica San Rafael", 2.4515, -76.6232, tiempo_espera=6, especialidades=["Trauma", "Cirugía"], capacidad_max=15, pacientes_actuales=random.randint(0, 10)),
    Hospital("Hospital María Occidente", 2.4285, -76.635, tiempo_espera=5, especialidades=["General", "Urgencias"], capacidad_max=20, pacientes_actuales=random.randint(0, 14))
]

colores = ["green", "orange", "red", "purple", "blue", "yellow"]

def generar_ubicacion_aleatoria():
    lat_base = 2.4448
    lon_base = -76.6147
    radio = 0.01
    lat = lat_base + random.uniform(-radio, radio)
    lon = lon_base + random.uniform(-radio, radio)
    return lat, lon

ambulancias = [
    Ambulancia("AMB-001", *generar_ubicacion_aleatoria(), especialidad="Cardiología"),
    Ambulancia("AMB-002", *generar_ubicacion_aleatoria(), especialidad="Trauma"),
    Ambulancia("AMB-003", *generar_ubicacion_aleatoria(), especialidad="General")
]

# ----- CACHÉ DE RUTAS -----
CACHE_RUTAS = OrderedDict()
MAX_CACHE_SIZE = 500
CACHE_TTL = 300

def _generar_clave_cache(origen, destino):
    coords = f"{origen.lat:.6f},{origen.lon:.6f};{destino.lat:.6f},{destino.lon:.6f}"
    return hashlib.md5(coords.encode()).hexdigest()

def _obtener_de_cache(origen, destino):
    clave = _generar_clave_cache(origen, destino)
    if clave in CACHE_RUTAS:
        resultado, timestamp = CACHE_RUTAS[clave]
        if time.time() - timestamp < CACHE_TTL:
            CACHE_RUTAS.move_to_end(clave)
            return resultado
        del CACHE_RUTAS[clave]
    return None

def _guardar_en_cache(origen, destino, resultado):
    clave = _generar_clave_cache(origen, destino)
    if len(CACHE_RUTAS) >= MAX_CACHE_SIZE:
        CACHE_RUTAS.popitem(last=False)
    CACHE_RUTAS[clave] = (resultado, time.time())

# ----- FUNCIONES AUXILIARES -----
def calcular_distancia_km(nodo1, nodo2):
    R = 6371
    lat1, lon1 = math.radians(nodo1.lat), math.radians(nodo1.lon)
    lat2, lon2 = math.radians(nodo2.lat), math.radians(nodo2.lon)
    dlat, dlon = lat2 - lat1, lon2 - lon1
    a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    return R * c

def obtener_ruta_graphhopper(origen, destino, max_retries=2):
    for intento in range(max_retries):
        try:
            url = "https://graphhopper.com/api/1/route"
            params = [
                ('point', f"{origen.lat},{origen.lon}"),
                ('point', f"{destino.lat},{destino.lon}"),
                ('vehicle', 'car'),
                ('key', 'demo'),
                ('points_encoded', 'false'),
                ('instructions', 'false')
            ]
            timeout = 15 + (intento * 5)
            response = requests.get(url, params=params, timeout=timeout)
            
            if response.status_code != 200:
                if intento < max_retries - 1:
                    time.sleep(0.5 * (2 ** intento))
                    continue
                return None, None, None
            
            r = response.json()
            if r.get("info", {}).get("statuscode") != 0 or not r.get("paths"):
                return None, None, None
            
            path = r["paths"][0]
            points = path.get("points")
            if not points:
                return None, None, None
            
            coords = points.get("coordinates", []) if isinstance(points, dict) else points
            if not coords or len(coords) < 2:
                return None, None, None
            
            nodos_ruta = [[float(c[1]), float(c[0])] for c in coords]
            distancia_km = float(path.get("distance", 0)) / 1000
            tiempo_min = float(path.get("time", 0)) / 1000 / 60
            
            if tiempo_min <= 0 or len(nodos_ruta) < 2:
                return None, None, None
            
            return nodos_ruta, distancia_km, tiempo_min
        except (requests.exceptions.Timeout, requests.exceptions.ConnectionError) as e:
            if intento < max_retries - 1:
                time.sleep(0.5 * (2 ** intento))
                continue
        except Exception:
            pass
    return None, None, None

def obtener_ruta_openrouteservice(origen, destino, max_retries=2):
    for intento in range(max_retries):
        try:
            api_key = "5b3ce3597851110001cf6248a1b7c8d4c8b84f8b9b8f8f8f8f8f8f8f8f8f8"
            url = "https://api.openrouteservice.org/v2/directions/driving-car"
            headers = {
                'Accept': 'application/json, application/geo+json',
                'Authorization': api_key,
                'Content-Type': 'application/json'
            }
            body = {
                "coordinates": [[origen.lon, origen.lat], [destino.lon, destino.lat]],
                "geometry": True,
                "geometry_simplify": False
            }
            timeout = 15 + (intento * 5)
            response = requests.post(url, json=body, headers=headers, timeout=timeout)
            
            if response.status_code != 200:
                if intento < max_retries - 1:
                    time.sleep(0.5 * (2 ** intento))
                    continue
                return None, None, None
            
            r = response.json()
            if not r.get("features"):
                return None, None, None
            
            feature = r["features"][0]
            coords = feature.get("geometry", {}).get("coordinates", [])
            if not coords or len(coords) < 2:
                return None, None, None
            
            nodos_ruta = [[float(c[1]), float(c[0])] for c in coords]
            summary = feature.get("properties", {}).get("summary", {})
            distancia_km = float(summary.get("distance", 0)) / 1000
            tiempo_min = float(summary.get("duration", 0)) / 60
            
            if tiempo_min <= 0:
                return None, None, None
            
            return nodos_ruta, distancia_km, tiempo_min
        except (requests.exceptions.Timeout, requests.exceptions.ConnectionError) as e:
            if intento < max_retries - 1:
                time.sleep(0.5 * (2 ** intento))
                continue
        except Exception:
            pass
    return None, None, None

def obtener_ruta_osrm(origen, destino, max_retries=1):
    for intento in range(max_retries):
        try:
            url = f"https://router.project-osrm.org/route/v1/driving/{origen.lon},{origen.lat};{destino.lon},{destino.lat}"
            params = {
                'overview': 'full',
                'geometries': 'geojson',
                'alternatives': 'false',
                'steps': 'false'
            }
            timeout = 8 + (intento * 3)
            response = requests.get(
                url, 
                params=params, 
                timeout=timeout, 
                headers={'User-Agent': 'Mozilla/5.0'},
                allow_redirects=True
            )
            
            if response.status_code != 200:
                return None, None, None
            
            r = response.json()
            if r.get("code") != "Ok" or not r.get("routes"):
                return None, None, None
            
            route = r["routes"][0]
            geometry = route.get("geometry")
            if not geometry:
                return None, None, None
            
            coords = geometry.get("coordinates", []) if isinstance(geometry, dict) else geometry
            if not coords or len(coords) < 2:
                return None, None, None
            
            nodos_ruta = [[float(c[1]), float(c[0])] for c in coords]
            distancia_km = float(route.get("distance", 0)) / 1000
            tiempo_min = float(route.get("duration", 0)) / 60
            
            if tiempo_min <= 0 or len(nodos_ruta) < 2:
                return None, None, None
            
            return nodos_ruta, distancia_km, tiempo_min
        except (requests.exceptions.Timeout, requests.exceptions.ConnectionError) as e:
            return None, None, None
        except Exception:
            return None, None, None
    return None, None, None

def obtener_ruta_real(origen, destino):
    resultado_cache = _obtener_de_cache(origen, destino)
    if resultado_cache:
        nodos_ruta, distancia, tiempo = resultado_cache
        # Verificar que el caché tenga una ruta válida con más de 2 nodos
        if nodos_ruta and len(nodos_ruta) > 2:
            return resultado_cache
    
    servicios = [
        obtener_ruta_openrouteservice,
        obtener_ruta_graphhopper,
        obtener_ruta_osrm
    ]
    
    # Intentar cada servicio hasta obtener una ruta válida con más de 2 nodos
    #Base matematica del costo minimo
    for servicio in servicios:
        try:
            nodos_ruta, distancia, tiempo = servicio(origen, destino)
            # Solo aceptar rutas con más de 2 nodos (rutas reales que siguen carreteras)
            if nodos_ruta and len(nodos_ruta) > 2 and tiempo is not None and tiempo > 0:
                resultado = (nodos_ruta, distancia, tiempo)
                _guardar_en_cache(origen, destino, resultado)
                return resultado
        except Exception:
            continue
    
    return None, None, None

def calcular_costo_ruta(amb, h, nodos_ruta, tiempo_base):
    if nodos_ruta and len(nodos_ruta) >= 2 and tiempo_base is not None and tiempo_base > 0:
        match_especialidad = 1.0 if amb.especialidad in h.especialidades else 0.5
        penalizacion_ocupacion = h.porcentaje_ocupacion() * 5
        penalizacion_espera = h.tiempo_espera
        trafico = random.uniform(0, 0.5)
        tiempo_con_trafico = tiempo_base * (1 + trafico * 2)
        return tiempo_con_trafico + penalizacion_espera + penalizacion_ocupacion + (1 - match_especialidad) * 3
    return None

def evaluar_hospital(amb, h):
    # Intentar obtener ruta real con múltiples intentos
    # NUNCA usar línea recta - solo rutas reales que sigan las carreteras
    
    servicios = [
        obtener_ruta_openrouteservice,
        obtener_ruta_graphhopper,
        obtener_ruta_osrm
    ]
    
    # Primero intentar con caché
    for intento in range(2):
        try:
            nodos_ruta, distancia_real, tiempo_base = obtener_ruta_real(amb.pos, Nodo(h.lat, h.lon))
            
            if nodos_ruta and len(nodos_ruta) > 2 and tiempo_base is not None and tiempo_base > 0:
                costo = calcular_costo_ruta(amb, h, nodos_ruta, tiempo_base)
                if costo is not None and costo > 0:
                    return (h, nodos_ruta, costo)
        except Exception:
            if intento < 1:
                time.sleep(0.2)
            continue
    
    # Si el caché no funcionó, intentar directamente con cada servicio
    # Intentar cada servicio hasta 2 veces
    for servicio in servicios:
        for intento_servicio in range(2):
            try:
                nodos_ruta, distancia_real, tiempo_base = servicio(amb.pos, Nodo(h.lat, h.lon))
                if nodos_ruta and len(nodos_ruta) > 2 and tiempo_base is not None and tiempo_base > 0:
                    costo = calcular_costo_ruta(amb, h, nodos_ruta, tiempo_base)
                    if costo is not None and costo > 0:
                        # Guardar en caché para futuras consultas
                        _guardar_en_cache(amb.pos, Nodo(h.lat, h.lon), (nodos_ruta, distancia_real, tiempo_base))
                        return (h, nodos_ruta, costo)
            except Exception:
                if intento_servicio < 1:
                    time.sleep(0.2)
                continue
    
    # Si después de todos los intentos no se obtuvo una ruta real,
    # retornar None para que este hospital no sea considerado
    # NO usar línea recta - los vehículos deben seguir las carreteras
    return None

# ----- CONVERSORES A JSON -----
def ambulancia_to_dict(a):
    return {
        "id": a.id,
        "lat": a.pos.lat,
        "lon": a.pos.lon,
        "especialidad": a.especialidad
    }

def hospital_to_dict(h):
    return {
        "nombre": h.nombre,
        "lat": h.lat,
        "lon": h.lon,
        "espera": h.tiempo_espera,
        "especialidades": h.especialidades,
        "capacidad_max": h.capacidad_max,
        "pacientes_actuales": h.pacientes_actuales,
        "puede_recibir": h.puede_recibir(),
        "porcentaje_ocupacion": round(h.porcentaje_ocupacion() * 100, 1)
    }

# ----- ASIGNACIÓN CON RUTAS REALES -----
def asignar_hospitales_dijkstra(ambulancias, hospitales):
    asignaciones = {}
    hospitales_usados = set()
    
    for amb in ambulancias:
        hospitales_disponibles = [h for h in hospitales if h.puede_recibir() and h.nombre not in hospitales_usados]
        if not hospitales_disponibles:
            hospitales_disponibles = [h for h in hospitales if h.puede_recibir()]
        
        if not hospitales_disponibles:
            continue
        
        # Usar Árbol Binario de Búsqueda para organizar hospitales por costo
        arbol_hospitales = ArbolBinarioBusqueda()
        
        with ThreadPoolExecutor(max_workers=min(len(hospitales_disponibles), 6)) as executor:
            futures = {executor.submit(evaluar_hospital, amb, h): h for h in hospitales_disponibles}
            
            for future in as_completed(futures):
                try:
                    resultado = future.result()
                    if resultado is None:
                        continue
                    h, nodos_ruta, costo = resultado
                    # Solo aceptar rutas con más de 2 nodos (rutas reales que siguen carreteras)
                    if nodos_ruta and len(nodos_ruta) > 2 and costo is not None:
                        # Insertar en el árbol binario ordenado por costo
                        arbol_hospitales.insertar((h, nodos_ruta), costo)
                except:
                    continue
        
                # Obtener el hospital con menor costo del árbol
        if not arbol_hospitales.esta_vacio():
            mejor_resultado, mejor_costo = arbol_hospitales.obtener_menor()
            if mejor_resultado:
                mejor_h, mejor_ruta_nodos = mejor_resultado
                
                # Construir grafo desde la ruta y aplicar Dijkstra
                # Calcular distancia total de la ruta sumando distancias entre nodos consecutivos
                distancia_total_ruta = 0
                for i in range(len(mejor_ruta_nodos) - 1):
                    distancia_total_ruta += calcular_distancia_km(
                        Nodo(mejor_ruta_nodos[i][0], mejor_ruta_nodos[i][1]),
                        Nodo(mejor_ruta_nodos[i+1][0], mejor_ruta_nodos[i+1][1])
                    )
                
                # Construir el grafo y aplicar Dijkstra
                grafo = Grafo()
                distancia_grafo, camino_grafo, tiempo_grafo = grafo.construir_grafo_desde_ruta(
                    mejor_ruta_nodos,
                    distancia_total_ruta if distancia_total_ruta > 0 else calcular_distancia_km(amb.pos, Nodo(mejor_h.lat, mejor_h.lon)),
                    amb.id,
                    mejor_h.nombre,
                    amb.pos.lat,
                    amb.pos.lon,
                    mejor_h.lat,
                    mejor_h.lon
                )
                
                # Usar la ruta del grafo (resultado de Dijkstra) si está disponible y es válida
                # Si el grafo no devuelve una ruta válida, usar la ruta original de la API
                if camino_grafo and len(camino_grafo) > 2:
                    ruta_final = camino_grafo
                    print(f"[GRAFO] {amb.id} -> {mejor_h.nombre}: Usando ruta del grafo con {len(camino_grafo)} nodos")
                else:
                    # Si el grafo no devuelve ruta válida, usar la original
                    ruta_final = mejor_ruta_nodos
                    print(f"[GRAFO] {amb.id} -> {mejor_h.nombre}: Usando ruta original con {len(mejor_ruta_nodos)} nodos (grafo falló)")
                
                if ruta_final and len(ruta_final) > 2:
                    ruta = Ruta(ruta_final, round(mejor_costo, 1))
                    asignaciones[amb.id] = (mejor_h, ruta, round(mejor_costo, 1))
                    hospitales_usados.add(mejor_h.nombre)
                    
                    # Guardar en historial de la ambulancia usando ListaEnlazada
                    amb.historial.agregar_final({
                        "hospital": mejor_h.nombre,
                        "tiempo": round(mejor_costo, 1),
                        "timestamp": time.time(),
                        "ruta": ruta_final,
                        "distancia": distancia_total_ruta if distancia_total_ruta > 0 else distancia_grafo
                    })
    
    return asignaciones

# ----- FLASK ROUTES -----
@app.route('/favicon.ico')
def favicon():
    return Response(status=204)

@app.route('/')
def index():
    global ambulancias
    ambulancias = [
        Ambulancia("AMB-001", *generar_ubicacion_aleatoria(), especialidad="Cardiología"),
        Ambulancia("AMB-002", *generar_ubicacion_aleatoria(), especialidad="Trauma"),
        Ambulancia("AMB-003", *generar_ubicacion_aleatoria(), especialidad="General")
    ]
    
    amb_json = [ambulancia_to_dict(a) for a in ambulancias]
    hosp_json = [hospital_to_dict(h) for h in hospitales]
    
    return render_template("index.html",
                           ambulancias=amb_json,
                           hospitales=hosp_json)

# ----- SIMULACIÓN -----
def actualizar_estado_hospitales():
    for h in hospitales:
        h.tiempo_espera = random.randint(2, 8)
        h.pacientes_actuales = random.randint(0, int(h.capacidad_max * 0.8))

def simular_ambulancia(amb):
    while True:
        try:
            actualizar_estado_hospitales()
            
            asignaciones = asignar_hospitales_dijkstra(ambulancias, hospitales)
            print(f"[SIMULACION] Asignaciones obtenidas: {len(asignaciones)}")
            rutas_info = []
            grafo_info = []

            for amb_id, (h, ruta, costo) in asignaciones.items():
                # Solo enviar rutas con más de 2 nodos (rutas reales que siguen carreteras)
                if not ruta or not ruta.nodos or len(ruta.nodos) <= 2:
                    print(f"[SIMULACION] Saltando {amb_id} -> {h.nombre}: ruta inválida o muy corta")
                    continue
                    
                color = colores[hash(amb_id) % len(colores)]
                rutas_info.append({
                    "ambulancia": amb_id,
                    "hospital": h.nombre,
                    "color": color,
                    "nodos": ruta.nodos,
                    "tiempo_total": costo
                })
                
                origen_amb = next((a for a in ambulancias if a.id == amb_id), None)
                if origen_amb and ruta.nodos and len(ruta.nodos) > 2:
                    grafo_info.append({
                        "origen": {"lat": origen_amb.pos.lat, "lon": origen_amb.pos.lon, "id": amb_id},
                        "destino": {"lat": h.lat, "lon": h.lon, "id": h.nombre},
                        "ruta": ruta.nodos,
                        "color": color
                    })
                    print(f"[GRAFO] Enviando grafo: {amb_id} -> {h.nombre} con {len(ruta.nodos)} nodos")

            if rutas_info:
                print(f"[SIMULACION] Enviando {len(rutas_info)} rutas al cliente")
                socketio.emit("update_rutas", rutas_info)
            if grafo_info:
                print(f"[GRAFO] Enviando {len(grafo_info)} grafos al cliente")
                socketio.emit("update_grafo", grafo_info)
            else:
                print(f"[GRAFO] No hay grafos para enviar")
            
            if amb.id in asignaciones:
                h, ruta, _ = asignaciones[amb.id]
                
                if ruta and ruta.nodos and len(ruta.nodos) >= 2:
                    paso = max(1, len(ruta.nodos) // 15)
                    for i in range(0, len(ruta.nodos), paso):
                        nodo = ruta.nodos[i]
                        amb.pos.lat, amb.pos.lon = nodo[0], nodo[1]
                        
                        socketio.emit("update_position", {
                            "ambulancia": amb.id,
                            "lat": amb.pos.lat,
                            "lon": amb.pos.lon,
                            "hospital": h.nombre
                        })
                        
                        time.sleep(0.2)
            
            time.sleep(3)
        except KeyboardInterrupt:
            break
        except:
            time.sleep(5)

def iniciar_simulacion():
    time.sleep(2)
    for amb in ambulancias:
        thread = threading.Thread(target=simular_ambulancia, args=(amb,), daemon=True)
        thread.start()

# ----- EJECUCIÓN -----
if __name__ == '__main__':
    try:
        threading.Thread(target=iniciar_simulacion, daemon=True).start()
        socketio.run(app, debug=False, host='127.0.0.1', port=5000, allow_unsafe_werkzeug=True)
    except KeyboardInterrupt:
        pass
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)
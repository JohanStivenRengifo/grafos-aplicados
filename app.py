from flask import Flask, render_template
from flask_socketio import SocketIO
from clases import Nodo, Hospital, Ruta, Ambulancia
import requests, threading, time, random, datetime

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app)

# ----- CONFIGURACIÓN INICIAL -----
hospitales = [
    Hospital("San José", 2.441981, -76.612537, tiempo_espera=5, especialidades=["Cardiología"]),
    Hospital("La Estancia", 2.451490, -76.623228, tiempo_espera=3, especialidades=["Trauma"]),
    Hospital("Susana López", 2.455510, -76.619900, tiempo_espera=4, especialidades=["Pediatría"]),
    Hospital("Santa Gracia", 2.448185, -76.610145, tiempo_espera=6, especialidades=["General"])
]

ambulancias = [
    Ambulancia("A1", 2.4448, -76.6147, especialidad="Cardiología"),
    Ambulancia("A2", 2.4490, -76.6150, especialidad="Trauma"),
    Ambulancia("A3", 2.4460, -76.6120, especialidad="General")
]

colores = ["green", "orange", "red", "purple"]

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
        "especialidades": h.especialidades
    }

# ----- MAPEO DE RUTAS (OSRM) -----
def obtener_ruta_osrm(origen, destino):
    url = f"http://router.project-osrm.org/route/v1/driving/{origen.lon},{origen.lat};{destino.lon},{destino.lat}?overview=full&geometries=geojson"

    r = requests.get(url).json()
    coords = r["routes"][0]["geometry"]["coordinates"]  # [lon, lat]
    nodos = [[c[1], c[0]] for c in coords]

    tiempo_min = r["routes"][0]["duration"] / 60
    return Ruta(nodos, tiempo_min)

# ----- ASIGNACIÓN GLOBAL -----
def asignar_hospitales_global(ambulancias, hospitales):
    asignaciones = {}
    alpha = 1.0
    beta = 5.0
    ocupados = set()

    for amb in ambulancias:
        mejor_costo = float('inf')
        mejor_h = None
        mejor_ruta = None

        for h in hospitales:
            if h.nombre in ocupados:
                continue

            try:
                ruta = obtener_ruta_osrm(amb.pos, Nodo(h.lat, h.lon))
            except:
                distancia = ((amb.pos.lat - h.lat)**2 + (amb.pos.lon - h.lon)**2)**0.5
                ruta = Ruta([[amb.pos.lat, amb.pos.lon], [h.lat, h.lon]], distancia * 60)

            match = 1.0 if amb.especialidad in h.especialidades else 0.0
            penalizacion = random.uniform(0, 3)

            costo_total = ruta.tiempo_total + alpha*h.tiempo_espera + beta*(1-match) + penalizacion

            if costo_total < mejor_costo:
                mejor_costo = costo_total
                mejor_h = h
                mejor_ruta = ruta

        if mejor_h:
            asignaciones[amb.id] = (mejor_h, mejor_ruta, round(mejor_costo, 1))
            ocupados.add(mejor_h.nombre)

    return asignaciones

# ----- FLASK ROUTE -----
@app.route('/')
def index():
    amb_json = [ambulancia_to_dict(a) for a in ambulancias]
    hosp_json = [hospital_to_dict(h) for h in hospitales]

    return render_template("index.html",
                           ambulancias=amb_json,
                           hospitales=hosp_json)

# ----- SIMULACIÓN -----
def simular_ambulancia(amb):
    while True:

        for h in hospitales:
            h.tiempo_espera = random.randint(2, 6)

        asignaciones = asignar_hospitales_global(ambulancias, hospitales)
        rutas_info = []

        for amb_id, (h, ruta, costo) in asignaciones.items():

            rutas_info.append({
                "ambulancia": amb_id,
                "hospital": h.nombre,
                "color": colores[hash(amb_id) % len(colores)],
                "nodos": ruta.nodos,
                "tiempo_total": costo
            })

        socketio.emit("update_rutas", rutas_info)

        if amb.id in asignaciones:
            h, ruta, _ = asignaciones[amb.id]

            for nodo in ruta.nodos:
                amb.pos.lat, amb.pos.lon = nodo

                socketio.emit("update_position", {
                    "ambulancia": amb.id,
                    "lat": amb.pos.lat,
                    "lon": amb.pos.lon,
                    "hospital": h.nombre
                })

                time.sleep(2)

        time.sleep(3)

# ----- INICIAR HILOS -----
for amb in ambulancias:
    threading.Thread(target=simular_ambulancia, args=(amb,), daemon=True).start()

# ----- EJECUCIÓN -----
if __name__ == '__main__':
    socketio.run(app, debug=True)

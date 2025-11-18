class Nodo:
    def __init__(self, lat, lon):
        self.lat = lat
        self.lon = lon

class Ruta:
    def __init__(self, nodos, tiempo_total):
        self.nodos = nodos
        self.tiempo_total = tiempo_total

class Hospital:
    def __init__(self, nombre, lat, lon, tiempo_espera=0, especialidades=None):
        self.nombre = nombre
        self.lat = lat
        self.lon = lon
        self.tiempo_espera = tiempo_espera
        self.especialidades = especialidades or []

class Ambulancia:
    def __init__(self, id, lat, lon, especialidad=None):
        self.id = id
        self.pos = Nodo(lat, lon)
        self.especialidad = especialidad
        self.historial = []  # Almacena rutas y hospitales asignados

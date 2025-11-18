class Nodo:
    def __init__(self, lat, lon, id=None):
        self.lat = lat
        self.lon = lon
        self.id = id

class Ruta:
    def __init__(self, nodos, tiempo_total):
        self.nodos = nodos
        self.tiempo_total = tiempo_total

class Via:
    def __init__(self, origen, destino, distancia_km, trafico=0, bloqueada=False):
        self.origen = origen
        self.destino = destino
        self.distancia_km = distancia_km
        self.trafico = trafico  # 0-1: 0 sin tráfico, 1 tráfico máximo
        self.bloqueada = bloqueada
    
    def calcular_peso(self):
        if self.bloqueada:
            return float('inf')
        tiempo_base = (self.distancia_km / 60) * 60  # minutos asumiendo 60 km/h
        multiplicador_trafico = 1 + (self.trafico * 2)  # hasta 3x más tiempo
        return tiempo_base * multiplicador_trafico

class Hospital:
    def __init__(self, nombre, lat, lon, tiempo_espera=0, especialidades=None, capacidad_max=10, pacientes_actuales=0):
        self.nombre = nombre
        self.lat = lat
        self.lon = lon
        self.tiempo_espera = tiempo_espera
        self.especialidades = especialidades or []
        self.capacidad_max = capacidad_max
        self.pacientes_actuales = pacientes_actuales
    
    def puede_recibir(self):
        return self.pacientes_actuales < self.capacidad_max
    
    def porcentaje_ocupacion(self):
        return self.pacientes_actuales / self.capacidad_max if self.capacidad_max > 0 else 0

class Ambulancia:
    def __init__(self, id, lat, lon, especialidad=None):
        self.id = id
        self.pos = Nodo(lat, lon)
        self.especialidad = especialidad
        self.historial = []

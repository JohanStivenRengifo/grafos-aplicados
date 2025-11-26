import math

def calcular_distancia_km(nodo1, nodo2):
    """Calcula la distancia entre dos nodos en kilómetros usando la fórmula de Haversine"""
    R = 6371  # Radio de la Tierra en km
    lat1, lon1 = math.radians(nodo1.lat), math.radians(nodo1.lon)
    lat2, lon2 = math.radians(nodo2.lat), math.radians(nodo2.lon)
    dlat, dlon = lat2 - lat1, lon2 - lon1
    a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    return R * c

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
        tiempo_base = (self.distancia_km / 30) * 60  # minutos asumiendo 30 km/h
        multiplicador_trafico = 1 + (self.trafico * 1)  # hasta 1x más tiempo
        return tiempo_base * multiplicador_trafico

# Especialidades ecvaluadas   
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


# Listas enlazadas, árboles binarios de búsqueda y grafos
class NodoLista:
    """Nodo de una lista enlazada"""
    def __init__(self, dato):
        self.dato = dato
        self.siguiente = None

class ListaEnlazada:
    """Implementación de lista enlazada simple"""
    def __init__(self):
        self.cabeza = None
        self.tamanio = 0
    
    def agregar(self, dato):
        """Agrega un elemento al inicio de la lista"""
        nuevo_nodo = NodoLista(dato)
        nuevo_nodo.siguiente = self.cabeza
        self.cabeza = nuevo_nodo
        self.tamanio += 1
    
    def agregar_final(self, dato):
        """Agrega un elemento al final de la lista"""
        nuevo_nodo = NodoLista(dato)
        if self.cabeza is None:
            self.cabeza = nuevo_nodo
        else:
            actual = self.cabeza
            while actual.siguiente is not None:
                actual = actual.siguiente
            actual.siguiente = nuevo_nodo
        self.tamanio += 1
    
    def obtener(self, indice):
        """Obtiene el elemento en el índice dado"""
        if indice < 0 or indice >= self.tamanio:
            return None
        actual = self.cabeza
        for i in range(indice):
            actual = actual.siguiente
        return actual.dato
    
    def to_lista(self):
        """Convierte la lista enlazada a una lista de Python"""
        resultado = []
        actual = self.cabeza
        while actual is not None:
            resultado.append(actual.dato)
            actual = actual.siguiente
        return resultado
    
    def __len__(self):
        return self.tamanio
    
    def __iter__(self):
        """Permite iterar sobre la lista"""
        actual = self.cabeza
        while actual is not None:
            yield actual.dato
            actual = actual.siguiente

# 2. ÁRBOL BINARIO DE BÚSQUEDA
class NodoArbol:
    """Nodo de un árbol binario de búsqueda"""
    def __init__(self, hospital, costo):
        self.hospital = hospital
        self.costo = costo
        self.izquierdo = None
        self.derecho = None

class ArbolBinarioBusqueda:
    """Árbol binario de búsqueda ordenado por costo"""
    def __init__(self):
        self.raiz = None
        self.tamanio = 0
    
    def insertar(self, hospital, costo):
        """Inserta un hospital en el árbol ordenado por costo"""
        self.raiz = self._insertar_recursivo(self.raiz, hospital, costo)
        self.tamanio += 1
    
    def _insertar_recursivo(self, nodo, hospital, costo):
        """Método auxiliar recursivo para insertar"""
        if nodo is None:
            return NodoArbol(hospital, costo)
        
        if costo < nodo.costo:
            nodo.izquierdo = self._insertar_recursivo(nodo.izquierdo, hospital, costo)
        else:
            nodo.derecho = self._insertar_recursivo(nodo.derecho, hospital, costo)
        
        return nodo
    
    def obtener_menor(self):
        """Obtiene el hospital con menor costo"""
        if self.raiz is None:
            return None, None
        
        nodo = self.raiz
        while nodo.izquierdo is not None:
            nodo = nodo.izquierdo
        
        return nodo.hospital, nodo.costo
    
    def obtener_menores(self, n):
        """Obtiene los n hospitales con menor costo"""
        resultado = []
        self._inorden_limitado(self.raiz, resultado, n)
        return resultado
    
    def _inorden_limitado(self, nodo, resultado, limite):
        """Recorrido inorden limitado para obtener los menores"""
        if nodo is None or len(resultado) >= limite:
            return
        
        # Recorrer izquierdo (menores)
        self._inorden_limitado(nodo.izquierdo, resultado, limite)
        
        # Agregar nodo actual si aún hay espacio
        if len(resultado) < limite:
            resultado.append((nodo.hospital, nodo.costo))
        
        # Recorrer derecho (mayores)
        self._inorden_limitado(nodo.derecho, resultado, limite)
    
    def esta_vacio(self):
        """Verifica si el árbol está vacío"""
        return self.raiz is None
    
    def __len__(self):
        return self.tamanio

# 3. GRAFO CON ALGORITMO DE DIJKSTRA
class NodoGrafo:
    """Nodo de un grafo"""
    def __init__(self, id, lat, lon):
        self.id = id
        self.lat = lat
        self.lon = lon
        self.adyacentes = {}  # {id_destino: peso}
    
    def agregar_arista(self, destino_id, peso):
        """Agrega una arista hacia otro nodo"""
        self.adyacentes[destino_id] = peso

class Grafo:
    """Grafo dirigido con pesos para representar la red de calles"""
    def __init__(self):
        self.nodos = {}
        self.num_nodos = 0
    
    def agregar_nodo(self, id, lat, lon):
        """Agrega un nodo al grafo"""
        if id not in self.nodos:
            self.nodos[id] = NodoGrafo(id, lat, lon)
            self.num_nodos += 1
        return self.nodos[id]
    
    def agregar_arista(self, origen_id, destino_id, peso):
        """Agrega una arista dirigida con peso"""
        if origen_id in self.nodos and destino_id in self.nodos:
            self.nodos[origen_id].agregar_arista(destino_id, peso)
    
    def obtener_nodo(self, id):
        """Obtiene un nodo por su ID"""
        return self.nodos.get(id)
    
    def dijkstra(self, origen_id, destino_id):
        """
        Implementa el algoritmo de Dijkstra para encontrar el camino más corto
        Retorna: (distancia_total, camino_lista_nodos, tiempo_estimado)
        """
        if origen_id not in self.nodos or destino_id not in self.nodos:
            return None, None, None
        
        # Inicialización
        distancias = {nodo_id: float('inf') for nodo_id in self.nodos}
        distancias[origen_id] = 0
        predecesores = {}
        visitados = set()
        
        # Cola de prioridad simple (podría mejorarse con heap)
        nodos_restantes = set(self.nodos.keys())
        
        while nodos_restantes:
            # Encontrar el nodo no visitado con menor distancia
            nodo_actual = None
            menor_distancia = float('inf')
            
            for nodo_id in nodos_restantes:
                if distancias[nodo_id] < menor_distancia:
                    menor_distancia = distancias[nodo_id]
                    nodo_actual = nodo_id
            
            if nodo_actual is None or menor_distancia == float('inf'):
                break
            
            nodos_restantes.remove(nodo_actual)
            visitados.add(nodo_actual)
            
            # Si llegamos al destino, construir el camino
            if nodo_actual == destino_id:
                camino = []
                nodo = destino_id
                while nodo is not None:
                    nodo_obj = self.nodos[nodo]
                    camino.insert(0, [nodo_obj.lat, nodo_obj.lon])
                    nodo = predecesores.get(nodo)
                
                distancia_total = distancias[destino_id]
                # Estimar tiempo asumiendo velocidad promedio de 60 km/h
                tiempo_estimado = (distancia_total / 60) * 60  # minutos
                
                return distancia_total, camino, tiempo_estimado
            
            # Actualizar distancias de nodos adyacentes
            nodo_obj = self.nodos[nodo_actual]
            for vecino_id, peso in nodo_obj.adyacentes.items():
                if vecino_id not in visitados:
                    nueva_distancia = distancias[nodo_actual] + peso
                    if nueva_distancia < distancias[vecino_id]:
                        distancias[vecino_id] = nueva_distancia
                        predecesores[vecino_id] = nodo_actual
        
        return None, None, None
    
    def construir_grafo_desde_ruta(self, ruta_nodos, distancia_total, origen_id, destino_id, origen_lat, origen_lon, destino_lat, destino_lon):
        """
        Construye un grafo desde una ruta obtenida de una API externa
        Crea nodos intermedios y aristas entre ellos
        """
        if not ruta_nodos or len(ruta_nodos) < 2:
            return None, None, None
        
        # Limpiar nodos previos para este grafo
        self.nodos = {}
        self.num_nodos = 0
        
        # Agregar nodo origen
        self.agregar_nodo(origen_id, origen_lat, origen_lon)
        
        # Agregar nodos intermedios de la ruta
        nodos_intermedios = []
        for i, nodo_coords in enumerate(ruta_nodos):
            # Saltar si es el primer o último nodo (ya están como origen/destino)
            if i == 0 and abs(nodo_coords[0] - origen_lat) < 0.0001 and abs(nodo_coords[1] - origen_lon) < 0.0001:
                continue
            if i == len(ruta_nodos) - 1 and abs(nodo_coords[0] - destino_lat) < 0.0001 and abs(nodo_coords[1] - destino_lon) < 0.0001:
                continue
            
            nodo_inter_id = f"{origen_id}_inter_{i}"
            self.agregar_nodo(nodo_inter_id, nodo_coords[0], nodo_coords[1])
            nodos_intermedios.append(nodo_inter_id)
        
        # Agregar nodo destino
        self.agregar_nodo(destino_id, destino_lat, destino_lon)
        
        # Calcular distancia por segmento basado en la distancia real entre nodos consecutivos
        if nodos_intermedios:
            # Conectar origen al primer nodo intermedio
            dist_origen_primer = calcular_distancia_km(
                Nodo(origen_lat, origen_lon),
                Nodo(ruta_nodos[0][0], ruta_nodos[0][1])
            ) if ruta_nodos else distancia_total / (len(nodos_intermedios) + 1)
            self.agregar_arista(origen_id, nodos_intermedios[0], dist_origen_primer)
            
            # Conectar nodos intermedios entre sí usando distancias reales
            for i in range(len(nodos_intermedios)):
                if i < len(nodos_intermedios) - 1:
                    # Distancia entre nodos intermedios consecutivos
                    idx_ruta_1 = i + 1  # índice en ruta_nodos
                    idx_ruta_2 = i + 2
                    if idx_ruta_1 < len(ruta_nodos) and idx_ruta_2 < len(ruta_nodos):
                        dist = calcular_distancia_km(
                            Nodo(ruta_nodos[idx_ruta_1][0], ruta_nodos[idx_ruta_1][1]),
                            Nodo(ruta_nodos[idx_ruta_2][0], ruta_nodos[idx_ruta_2][1])
                        )
                    else:
                        dist = distancia_total / (len(nodos_intermedios) + 1)
                    self.agregar_arista(nodos_intermedios[i], nodos_intermedios[i + 1], dist)
            
            # Conectar último nodo intermedio al destino
            if len(ruta_nodos) >= 2:
                dist_ultimo_destino = calcular_distancia_km(
                    Nodo(ruta_nodos[-2][0], ruta_nodos[-2][1]),
                    Nodo(destino_lat, destino_lon)
                )
            else:
                dist_ultimo_destino = distancia_total / (len(nodos_intermedios) + 1)
            self.agregar_arista(nodos_intermedios[-1], destino_id, dist_ultimo_destino)
        else:
            # Si no hay nodos intermedios, conectar origen directamente a destino
            self.agregar_arista(origen_id, destino_id, distancia_total)
        
        # Ejecutar Dijkstra para obtener el camino optimizado
        distancia_grafo, camino_grafo, tiempo_grafo = self.dijkstra(origen_id, destino_id)
        
        # Si Dijkstra no devuelve un camino válido, usar la ruta original
        if not camino_grafo or len(camino_grafo) < 2:
            # Construir camino desde la ruta original
            camino_grafo = [[origen_lat, origen_lon]]
            for nodo_coords in ruta_nodos:
                camino_grafo.append([nodo_coords[0], nodo_coords[1]])
            camino_grafo.append([destino_lat, destino_lon])
            tiempo_grafo = tiempo_grafo if tiempo_grafo else (distancia_total / 60) * 60
        
        return distancia_total, camino_grafo, tiempo_grafo

class Ambulancia:
    def __init__(self, id, lat, lon, especialidad=None):
        self.id = id
        self.pos = Nodo(lat, lon)
        self.especialidad = especialidad
        self.historial = ListaEnlazada()  # Ahora usa ListaEnlazada

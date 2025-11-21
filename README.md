# 🚑 Simulador Profesional de Ambulancias - Popayán

Se crea un sistema web en tiempo real para simular la asignación y movimiento de ambulancias hacia hospitales en la ciudad de Popayán. Se implementan estructuras de datos avanzadas (Listas Enlazadas, Árboles Binarios de Búsqueda y Grafos) con algoritmos de optimización para encontrar las rutas más eficientes siguiendo las carreteras reales de la ciudad.

## 📋 Descripción

Este simulador permite visualizar en tiempo real cómo las ambulancias se asignan a hospitales basándose en múltiples criterios de optimización:

- **Rutas reales**: Utiliza APIs de routing (OpenRouteService, GraphHopper, OSRM) para obtener rutas que siguen las carreteras reales
- **Algoritmo de Dijkstra**: Aplica el algoritmo de Dijkstra sobre grafos para encontrar el camino más corto
- **Optimización multi-criterio**: Considera tiempo de viaje, especialidad médica, capacidad del hospital y tiempo de espera
- **Visualización en tiempo real**: Mapa interactivo con actualizaciones mediante WebSockets

## 🏗️ Estructuras de Datos Implementadas

### 1. Lista Enlazada (`ListaEnlazada`)
Almacena el historial de rutas de cada ambulancia de forma eficiente.

**Características:**
- Implementación de lista enlazada simple
- Operaciones: `agregar()`, `agregar_final()`, `obtener()`, `to_lista()`
- Complejidad: O(1) para inserción, O(n) para búsqueda

**Uso:**
```python
ambulancia.historial.agregar_final({
    "hospital": "Hospital X",
    "tiempo": 15.5,
    "timestamp": time.time(),
    "ruta": [...]
})
```

### 2. Árbol Binario de Búsqueda (`ArbolBinarioBusqueda`)
Organiza hospitales por costo/prioridad para optimizar la búsqueda del mejor hospital.

**Características:**
- Árbol binario de búsqueda ordenado por costo
- Operaciones: `insertar()`, `obtener_menor()`, `obtener_menores()`, `inorden()`
- Complejidad: O(log n) para inserción y búsqueda en promedio

**Uso:**
```python
arbol = ArbolBinarioBusqueda()
arbol.insertar((hospital, ruta), costo)
mejor_hospital, mejor_costo = arbol.obtener_menor()
```

### 3. Grafo (`Grafo`)
Representa la red de calles de la ciudad y calcula rutas óptimas usando el algoritmo de Dijkstra.

**Características:**
- Grafo dirigido con pesos (distancias)
- Implementación completa del algoritmo de Dijkstra
- Construcción dinámica desde rutas de APIs externas
- Operaciones: `agregar_nodo()`, `agregar_arista()`, `dijkstra()`, `construir_grafo_desde_ruta()`

**Uso:**
```python
grafo = Grafo()
grafo.agregar_nodo("origen", lat, lon)
grafo.agregar_nodo("destino", lat, lon)
grafo.agregar_arista("origen", "destino", distancia)
distancia, camino, tiempo = grafo.dijkstra("origen", "destino")
```

## 📊 Diagramas

### Diagrama Conceptual del Sistema

```mermaid
graph TB
    subgraph "Sistema de Simulación de Ambulancias"
        A[Ambulancia] -->|tiene| B[Posición GPS]
        A -->|almacena| C[ListaEnlazada<br/>Historial de Rutas]
        A -->|requiere| D[Especialidad Médica]
        
        E[Hospital] -->|tiene| F[Ubicación]
        E -->|tiene| G[Capacidad]
        E -->|tiene| H[Especialidades]
        E -->|tiene| I[Tiempo de Espera]
        
        J[Sistema de Asignación] -->|usa| K[Árbol Binario<br/>de Búsqueda]
        J -->|evalúa| L[Grafo con Dijkstra]
        J -->|obtiene| M[Rutas de APIs Externas]
        
        K -->|organiza| E
        K -->|ordena por| N[Costo Total]
        
        L -->|construye desde| M
        L -->|calcula| O[Camino Más Corto]
        
        A -->|asignado a| E
        O -->|conecta| B
        O -->|conecta| F
        
        P[API Externa] -->|proporciona| M
        P -->|OpenRouteService| M
        P -->|GraphHopper| M
        P -->|OSRM| M
        
        Q[Flask WebSocket] -->|actualiza| R[Mapa Interactivo]
        Q -->|envía| S[Posiciones en Tiempo Real]
        Q -->|envía| T[Rutas Visualizadas]
    end
    
    style A fill:#ff6b6b
    style E fill:#4ecdc4
    style K fill:#95e1d3
    style L fill:#f38181
    style C fill:#a8e6cf
```

### Diagrama de Clases

```mermaid
classDiagram
    class Nodo {
        +float lat
        +float lon
        +string id
    }
    
    class Ruta {
        +list nodos
        +float tiempo_total
    }
    
    class Hospital {
        +string nombre
        +float lat
        +float lon
        +int tiempo_espera
        +list especialidades
        +int capacidad_max
        +int pacientes_actuales
        +puede_recibir() bool
        +porcentaje_ocupacion() float
    }
    
    class Ambulancia {
        +string id
        +Nodo pos
        +string especialidad
        +ListaEnlazada historial
    }
    
    class NodoLista {
        +object dato
        +NodoLista siguiente
    }
    
    class ListaEnlazada {
        +NodoLista cabeza
        +int tamanio
        +agregar(dato) void
        +agregar_final(dato) void
        +obtener(indice) object
        +to_lista() list
        +__len__() int
        +__iter__() iterator
    }
    
    class NodoArbol {
        +tuple hospital
        +float costo
        +NodoArbol izquierdo
        +NodoArbol derecho
    }
    
    class ArbolBinarioBusqueda {
        +NodoArbol raiz
        +int tamanio
        +insertar(hospital, costo) void
        +obtener_menor() tuple
        +obtener_menores(n) list
        +esta_vacio() bool
        +__len__() int
    }
    
    class NodoGrafo {
        +string id
        +float lat
        +float lon
        +dict adyacentes
        +agregar_arista(destino, peso) void
    }
    
    class Grafo {
        +dict nodos
        +int num_nodos
        +agregar_nodo(id, lat, lon) NodoGrafo
        +agregar_arista(origen, destino, peso) void
        +obtener_nodo(id) NodoGrafo
        +dijkstra(origen, destino) tuple
        +construir_grafo_desde_ruta(ruta, distancia, origen, destino) tuple
    }
    
    %% Relaciones
    Ambulancia --> Nodo : usa
    Ambulancia --> ListaEnlazada : contiene
    ListaEnlazada --> NodoLista : compuesta de
    Ruta --> Nodo : contiene
    Hospital --> Nodo : tiene posición
    
    ArbolBinarioBusqueda --> NodoArbol : compuesto de
    NodoArbol --> Hospital : almacena referencia
    
    Grafo --> NodoGrafo : compuesto de
    NodoGrafo --> NodoGrafo : conecta con
    
    %% Relaciones de uso
    Ambulancia ..> Hospital : asignado a
    ArbolBinarioBusqueda ..> Hospital : organiza
    Grafo ..> Ruta : construye desde
```

### Diagrama UML: Grafo y Dijkstra

```mermaid
classDiagram
    class Grafo {
        -dict nodos
        -int num_nodos
        +agregar_nodo(id, lat, lon) NodoGrafo
        +agregar_arista(origen, destino, peso) void
        +obtener_nodo(id) NodoGrafo
        +dijkstra(origen, destino) tuple
        +construir_grafo_desde_ruta(ruta, distancia, origen, destino) tuple
    }
    
    class NodoGrafo {
        -string id
        -float lat
        -float lon
        -dict adyacentes
        +agregar_arista(destino_id, peso) void
    }
    
    class AlgoritmoDijkstra {
        <<algorithm>>
        +calcular_camino_corto(grafo, origen, destino) tuple
        -inicializar_distancias() dict
        -obtener_nodo_no_visitado_mas_cercano() string
        -actualizar_distancias() void
        -construir_camino() list
    }
    
    Grafo *-- NodoGrafo : contiene
    NodoGrafo --> NodoGrafo : conecta con
    Grafo ..> AlgoritmoDijkstra : usa
    AlgoritmoDijkstra ..> Grafo : procesa
    
    note for Grafo "Representa la red de calles\ncomo un grafo dirigido con pesos"
    note for NodoGrafo "Cada nodo representa\nun punto en el mapa"
    note for AlgoritmoDijkstra "Algoritmo de Dijkstra\npara encontrar el camino más corto"
```

### Diagrama UML: Árbol Binario de Búsqueda

```mermaid
classDiagram
    class ArbolBinarioBusqueda {
        -NodoArbol raiz
        -int tamanio
        +insertar(hospital, costo) void
        +obtener_menor() tuple
        +obtener_menores(n) list
        +esta_vacio() bool
        +__len__() int
        -_insertar_recursivo(nodo, hospital, costo) NodoArbol
        -_inorden_limitado(nodo, resultado, limite) void
    }
    
    class NodoArbol {
        -tuple hospital
        -float costo
        -NodoArbol izquierdo
        -NodoArbol derecho
    }
    
    class Hospital {
        +string nombre
        +float lat
        +float lon
        +float costo_total
    }
    
    ArbolBinarioBusqueda *-- NodoArbol : contiene
    NodoArbol --> NodoArbol : izquierdo
    NodoArbol --> NodoArbol : derecho
    NodoArbol --> Hospital : referencia
    
    note for ArbolBinarioBusqueda "Árbol ordenado por costo\npara búsqueda eficiente O(log n)"
    note for NodoArbol "Nodo del árbol con\nreferencia a hospital y costo"
    note for Hospital "Hospital con su\ncosto de asignación"
```

### Flujo de Funcionamiento

```mermaid
sequenceDiagram
    participant A as Ambulancia
    participant S as Sistema Asignación
    participant API as API Routing
    participant ABB as Árbol Binario
    participant G as Grafo
    participant M as Mapa
    
    A->>S: Solicita asignación
    S->>API: Obtiene rutas reales
    API-->>S: Retorna rutas con nodos
    
    loop Para cada hospital
        S->>S: Calcula costo total
        S->>ABB: Inserta (hospital, costo)
    end
    
    S->>ABB: Obtiene menor costo
    ABB-->>S: Retorna mejor hospital
    
    S->>G: Construye grafo desde ruta
    G->>G: Aplica Dijkstra
    G-->>S: Retorna camino optimizado
    
    S->>A: Asigna hospital y ruta
    S->>M: Envía grafo para visualización
    M->>M: Dibuja ruta en mapa
```

## 🚀 Instalación y Uso

### Requisitos

```bash
pip install flask flask-socketio requests
```

### Ejecución

```bash
python app.py
```

Luego abre tu navegador en `http://127.0.0.1:5000`


## 📝 Autores

Johan Stiven Rengifo
Tatiana Muñoz Daza 

## 📄 Licencia

Este proyecto es de uso educativo y académico.


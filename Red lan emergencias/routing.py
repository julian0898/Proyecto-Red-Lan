# routing.py
import heapq
from collections import defaultdict

def dijkstra(graph, start, end=None):
    """
    Algoritmo de Dijkstra para encontrar la ruta más corta desde 'start' a todos los nodos.
    Si se especifica 'end', se detiene al llegar a ese nodo.
    Retorna:
        dist: diccionario con la distancia mínima desde 'start' a cada nodo.
        prev: diccionario con el nodo anterior en el camino más corto para cada nodo.
    """
    if start not in graph:
        return {}, {}
    
    # Obtener todos los nodos del grafo (incluyendo vecinos que no sean claves directas)
    all_nodes = set(graph.keys())
    for node in graph:
        for neighbor, _ in graph[node]:
            all_nodes.add(neighbor)
    
    dist = {node: float('inf') for node in all_nodes}
    dist[start] = 0
    prev = {node: None for node in all_nodes}
    pq = [(0, start)]  # Cola de prioridad (distancia acumulada, nodo)
    visited = set()
    
    while pq:
        current_dist, current_node = heapq.heappop(pq)
        
        if current_node in visited:
            continue
        
        visited.add(current_node)
        
        # Si solo buscamos ruta a un destino específico, podemos salir antes
        if end and current_node == end:
            break
        
        if current_dist > dist[current_node]:
            continue
        
        if current_node in graph:
            for neighbor, weight in graph[current_node]:
                if neighbor not in visited:
                    distance = current_dist + weight
                    if distance < dist[neighbor]:
                        dist[neighbor] = distance
                        prev[neighbor] = current_node
                        heapq.heappush(pq, (distance, neighbor))
    
    return dist, prev

def reconstruct_path(prev, start, end):
    """
    Reconstruye el camino más corto desde 'start' hasta 'end' usando el diccionario 'prev'.
    Retorna una lista con los nodos del camino en orden.
    Si no hay camino, retorna una lista vacía.
    """
    if end not in prev or prev[end] is None:
        return []
    
    path = []
    current = end
    while current is not None:
        path.append(current)
        current = prev[current]
    
    # Verifica que el camino realmente inicia en 'start'
    return path[::-1] if path and path[-1] == start else []

def find_alternative_routes(graph, start, end, k=3):
    """
    Encuentra hasta 'k' rutas alternativas entre 'start' y 'end' usando una variante de Dijkstra.
    Cada vez que encuentra una ruta, elimina sus aristas del grafo temporal para buscar la siguiente.
    Retorna una lista de tuplas: (camino, distancia_total)
    """
    routes = []
    temp_graph = dict(graph)
    
    for _ in range(k):
        dist, prev = dijkstra(temp_graph, start, end)
        
        if end not in dist or dist[end] == float('inf'):
            break
        
        path = reconstruct_path(prev, start, end)
        if path:
            routes.append((path, dist[end]))
            
            # Remueve las aristas del camino encontrado para buscar rutas alternativas
            for i in range(len(path) - 1):
                u, v = path[i], path[i + 1]
                if u in temp_graph:
                    temp_graph[u] = [(n, w) for n, w in temp_graph[u] if n != v]
        else:
            break
    
    return routes
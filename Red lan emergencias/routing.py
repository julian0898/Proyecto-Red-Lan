# routing.py
import heapq
from collections import defaultdict

def dijkstra(graph, start, end=None):
   
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
    pq = [(0, start)] 
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
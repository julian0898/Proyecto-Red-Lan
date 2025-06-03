# network.py
from collections import defaultdict
import shutil

# Importar graphviz solo si está disponible
try:
    import graphviz
    GRAPHVIZ_AVAILABLE = True
except ImportError:
    GRAPHVIZ_AVAILABLE = False

class Network:
    def __init__(self):
        self.graph = defaultdict(list)
        self.nodes = set()
        self.stats = defaultdict(int)  # Para estadísticas de tráfico
    
    def add_connection(self, u, v, weight):
        """Agregar conexión bidireccional entre nodos"""
        self.graph[u].append((v, weight))
        self.graph[v].append((u, weight))
        self.nodes.add(u)
        self.nodes.add(v)
    
    def load_topology(self, path):
        """Cargar topología desde archivo"""
        try:
            with open(path, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#'):
                        parts = line.split()
                        if len(parts) >= 3:
                            u, v, w = parts[0], parts[1], int(parts[2])
                            self.add_connection(u, v, w)
            print(f"Topología cargada: {len(self.nodes)} nodos, {self.count_edges()} conexiones")
        except FileNotFoundError:
            print(f"Archivo {path} no encontrado. Creando topología por defecto...")
            self.create_default_topology()
    
    def create_default_topology(self):
        """Crear topología por defecto para pruebas"""
        connections = [
            ("Estacion1", "Estacion2", 10),
            ("Estacion1", "Estacion3", 15),
            ("Estacion2", "Estacion3", 5),
            ("Estacion2", "Estacion4", 8),
            ("Estacion3", "Estacion4", 12),
            ("Estacion3", "Estacion5", 20),
            ("Estacion4", "Estacion5", 7),
            ("Estacion1", "Estacion5", 25)
        ]
        for u, v, w in connections:
            self.add_connection(u, v, w)
    
    def count_edges(self):
        """Contar número total de aristas"""
        edges = set()
        for node in self.graph:
            for neighbor, _ in self.graph[node]:
                edge = tuple(sorted([node, neighbor]))
                edges.add(edge)
        return len(edges)
    
    def simulate_node_failure(self, failed_node):
        """Simular falla de un nodo"""
        if failed_node in self.nodes:
            print(f"⚠️  FALLA SIMULADA: Nodo {failed_node} fuera de servicio")
            # Crear grafo temporal sin el nodo fallido
            temp_graph = defaultdict(list)
            for node in self.graph:
                if node != failed_node:
                    for neighbor, weight in self.graph[node]:
                        if neighbor != failed_node:
                            temp_graph[node].append((neighbor, weight))
            return temp_graph
        return self.graph
    
    def update_traffic_stats(self, node):
        """Actualizar estadísticas de tráfico"""
        self.stats[node] += 1
    
    def get_network_stats(self):
        """Obtener estadísticas de la red"""
        return {
            'total_nodes': len(self.nodes),
            'total_connections': self.count_edges(),
            'traffic_per_node': dict(self.stats)
        }
    
    def visualize(self, output_file="network_graph", exclude_nodes=None):
        import graphviz
        import shutil

        if not shutil.which("dot"):
            print("[ADVERTENCIA] Graphviz no está instalado en el sistema o no se encuentra en el PATH.")
            return

        dot = graphviz.Graph(format='png', engine='dot')
        dot.attr(rankdir='LR', size='10,7', nodesep='1.2', ranksep='1.2', bgcolor="#f8f9fa")
        dot.attr('node', shape='circle', style='filled', fontsize='14', fontname='Segoe UI', color='#222f3e', width='0.5', height='0.5', fixedsize='true')

        exclude_nodes = set(exclude_nodes) if exclude_nodes else set()
        for node in self.nodes:
            if node in exclude_nodes:
                continue
            # Extraer número de estación
            num = ''.join(filter(str.isdigit, node))
            dot.node(num, tooltip=node, fillcolor='#a8edea')

        added_edges = set()
        for node in self.graph:
            if node in exclude_nodes:
                continue
            num1 = ''.join(filter(str.isdigit, node))
            for neighbor, weight in self.graph[node]:
                if neighbor in exclude_nodes:
                    continue
                num2 = ''.join(filter(str.isdigit, neighbor))
                edge = tuple(sorted([num1, num2]))
                if edge not in added_edges:
                    dot.edge(num1, num2, label=str(weight), color='#576574', penwidth='2')
                    added_edges.add(edge)

        dot.render(output_file, view=True)
        print(f"Gráfico generado: {output_file}.png")
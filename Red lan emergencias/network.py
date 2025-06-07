# network.py

from collections import defaultdict

# Clase que representa la red de estaciones y sus conexiones
class Network:
    def __init__(self):
        # Inicializa el grafo, el conjunto de nodos y las estadísticas de tráfico
        self.graph = defaultdict(list)
        self.nodes = set()
        self.stats = defaultdict(int)  

    def add_connection(self, u, v, weight):
        
        self.graph[u].append((v, weight))
        self.graph[v].append((u, weight))
        self.nodes.add(u)
        self.nodes.add(v)

    def load_topology(self, filename):
        
        with open(filename, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                parts = line.split()
                if len(parts) != 3:
                    continue  # Salta líneas mal formateadas
                u, v, w = parts[0], parts[1], int(parts[2])
                self.add_connection(u, v, w)
        print(f"Topología cargada: {len(self.nodes)} nodos, {self.count_edges()} conexiones")

    def create_default_topology(self):
        
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
        
        edges = set()
        for node in self.graph:
            for neighbor, _ in self.graph[node]:
                edge = tuple(sorted([node, neighbor]))
                edges.add(edge)
        return len(edges)

    def simulate_node_failure(self, failed_node):
        
        if failed_node in self.nodes:
            print(f"⚠️  FALLA SIMULADA: Nodo {failed_node} fuera de servicio")
           
            temp_graph = defaultdict(list)
            for node in self.graph:
                if node != failed_node:
                    for neighbor, weight in self.graph[node]:
                        if neighbor != failed_node:
                            temp_graph[node].append((neighbor, weight))
            return temp_graph
        return self.graph

    def update_traffic_stats(self, node):
        
        self.stats[node] += 1

    def get_network_stats(self):
       
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
            # Extrae el número de la estación para el nodo
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

import os
import tkinter as tk
from tkinter import simpledialog, messagebox
from tkinter import font
from network import Network
from emergency import EmergencyManager
from routing import dijkstra, reconstruct_path
from simulator import EmergencySimulator
import random
import graphviz
import shutil

# --- Configuración del entorno para Graphviz ---
os.environ["PATH"] += os.pathsep + r"C:\Program Files\Graphviz\bin"

# --- Variables globales para notificaciones y recursos ---
notificaciones_globales = []

# Diccionario de recursos disponibles por tipo y estación
recursos_disponibles = {
    "bomberos": ["Estacion1", "Estacion3"],
    "ambulancia": ["Estacion2", "Estacion5"],
    "policia": ["Estacion4", "Estacion6"],
    "rescate": ["Estacion1", "Estacion4"],
    "salud": ["Estacion5"],
    "ambiental": ["Estacion3"]
}

# Lista de estaciones de la red
estaciones = ["Estacion1", "Estacion2", "Estacion3", "Estacion4", "Estacion5", "Estacion6"]

def run_gui():
    
    network = Network()  
    emergency_manager = EmergencyManager()  
    simulator = EmergencySimulator()  
    nodos_fuera = set()  

    network.load_topology("topology.txt")

    # Configuración de la ventana principal de Tkinter
    root = tk.Tk()
    root.title("Simulador de Red LAN para Emergencias")
    root.geometry("400x500")
    root.configure(bg="#f8f9fa")

    #Definición de fuentes para la interfaz
    title_font = font.Font(family="Segoe UI", size=18, weight="bold")
    subtitle_font = font.Font(family="Segoe UI", size=10, slant="italic")
    button_font = font.Font(family="Segoe UI", size=11, weight="normal")

    # Títulos principales
    tk.Label(root, text="Simulador de Red LAN para Emergencias", bg="#f9f9fa", fg="#222f3e", font=title_font).pack(pady=(18, 2))
    tk.Label(root, text="Gestión y simulación de emergencias en red", bg="#f9f9fa", fg="#576574", font=subtitle_font).pack(pady=(0, 10))

    # Frame para los botones principales
    frame = tk.Frame(root, bg="#f9f9fa")
    frame.pack(expand=True)

    # Función para asignar el recurso más cercano a una emergencia
    def asignar_recurso_mas_cercano(emergency_location, resource_type):
        min_dist = float('inf')
        mejor_recurso = None
        for recurso in recursos_disponibles.get(resource_type, []):
            # Calcula la distancia desde cada recurso disponible hasta la emergencia
            temp_graph = {n: [(v, w) for v, w in network.graph[n] if v not in nodos_fuera] for n in network.graph if n not in nodos_fuera}
            dist, _ = dijkstra(temp_graph, recurso, emergency_location)
            if emergency_location in dist and dist[emergency_location] < min_dist:
                min_dist = dist[emergency_location]
                mejor_recurso = recurso
        return mejor_recurso, min_dist

    # Función para encontrar la estación más cercana a una ubicación
    def estacion_mas_cercana(ubicacion_emergencia, excluir=None):
        min_dist = float('inf')
        estacion_cercana = None
        for estacion in estaciones:
            # Solo considera estaciones operativas y distintas a la excluida
            if estacion not in network.nodes or estacion in nodos_fuera or estacion == excluir:
                continue
            temp_graph = {n: [(v, w) for v, w in network.graph[n] if v not in nodos_fuera] for n in network.graph if n not in nodos_fuera}
            dist, _ = dijkstra(temp_graph, estacion, ubicacion_emergencia)
            if ubicacion_emergencia in dist and dist[ubicacion_emergencia] < min_dist:
                min_dist = dist[ubicacion_emergencia]
                estacion_cercana = estacion
        return estacion_cercana, min_dist

    # Función para mostrar la asignación de recursos a una emergencia
    def mostrar_asignacion(asignacion, emergency_type):
        if not isinstance(asignacion, dict) or "assignments" not in asignacion or not asignacion["assignments"]:
            messagebox.showinfo("Ayuda enviada", "No se pudo asignar ayuda a esta emergencia.")
            return

        tipo_entidad = {
            "incendio": " Bomberos",
            "accidente": " Ambulancia y  Policía",
            "robo": " Policía",
            "inundacion": " Bomberos y  Ambulancia",
            "explosion": " Bomberos,  Ambulancia y  Policía",
            "emergencia_medica": " Ambulancia",
            "disturbio": " Policía",
            "desastre_natural": " Rescate,  Bomberos,  Ambulancia,  Policía",
            "accidente_transito": " Ambulancia y  Policía",
            "violencia": " Policía",
            "salud_publica": " Salud y  Ambulancia",
            "medio_ambiente": " Ambiental y  Bomberos"
        }
        entidades = []
        for recurso, datos in asignacion["assignments"].items():
            nombre = {
                "bomberos": " Bomberos",
                "ambulancia": " Ambulancia",
                "policia": " Policía",
                "rescate": " Rescate",
                "salud": " Salud",
                "ambiental": " Ambiental"
            }.get(recurso, recurso.capitalize())
            entidades.append(f"• {nombre}  |  ETA: {datos['eta']} min  |  ID: {datos['resource_id']}")
        entidades_str = "\n".join(entidades)
        mensaje = (
            f" Tipo de emergencia: {tipo_entidad.get(emergency_type, emergency_type.capitalize())}\n\n"
            f" **Ayuda enviada:**\n{entidades_str}"
        )
        messagebox.showinfo("Ayuda enviada", mensaje)

    def visualizar_ruta_grafica(path):
        if not shutil.which("dot"):
            messagebox.showinfo("Visualización", "Graphviz no está instalado en el sistema o no se encuentra en el PATH.")
            return

        dot = graphviz.Graph(format='png', engine='dot')
        dot.attr(rankdir='LR', size='10,7', nodesep='1.2', ranksep='1.2', bgcolor="#f8f9fa")
        dot.attr('node', shape='circle', style='filled', fontsize='14', fontname='Segoe UI', color='#222f3e', width='0.5', height='0.5', fixedsize='true')

        # Añadir nodos
        for node in network.nodes:
            color = "#feca57" if node in path else "#a8edea"
            dot.node(node, tooltip=node, fillcolor=color)

        # Añadir aristas
        added_edges = set()
        for node in network.graph:
            for neighbor, weight in network.graph[node]:
                edge = tuple(sorted([node, neighbor]))
                if edge in added_edges:
                    continue
                
                if node in path and neighbor in path:
                    idx1 = path.index(node)
                    idx2 = path.index(neighbor)
                    if abs(idx1 - idx2) == 1:
                        dot.edge(node, neighbor, label=str(weight), color="#ee5253", penwidth='4')
                    else:
                        dot.edge(node, neighbor, label=str(weight), color='#576574', penwidth='2')
                else:
                    dot.edge(node, neighbor, label=str(weight), color='#576574', penwidth='2')
                added_edges.add(edge)

        dot.render("ruta_mas_corta", view=True)

    def visualizar_ruta_grafica_personalizada(path, nodo_ficticio):
        if not shutil.which("dot"):
            messagebox.showinfo("Visualización", "Graphviz no está instalado en el sistema o no se encuentra en el PATH.")
            return

        dot = graphviz.Graph(format='png', engine='dot')
        dot.attr(rankdir='LR', size='10,7', nodesep='1.2', ranksep='1.2', bgcolor="#f8f9fa")
        dot.attr('node', shape='circle', style='filled', fontsize='14', fontname='Segoe UI', color='#222f3e', width='0.5', height='0.5', fixedsize='true')

        # Añadir todos los nodos de la red y el ficticio
        todos_nodos = set(network.nodes) | {nodo_ficticio}
        for node in todos_nodos:
            if node == nodo_ficticio:
                color = "#ee5253"  
            elif node in path:
                color = "#feca57"  
            else:
                color = "#a8edea"  
            dot.node(node, tooltip=node, fillcolor=color)

        # Añadir aristas de la red
        added_edges = set()
        for node in network.graph:
            for neighbor, weight in network.graph[node]:
                edge = tuple(sorted([node, neighbor]))
                if edge in added_edges:
                    continue
                if node in path and neighbor in path:
                    idx1 = path.index(node)
                    idx2 = path.index(neighbor)
                    if abs(idx1 - idx2) == 1:
                        dot.edge(node, neighbor, label=str(weight), color="#ee5253", penwidth='4')
                    else:
                        dot.edge(node, neighbor, label=str(weight), color='#576574', penwidth='2')
                else:
                    dot.edge(node, neighbor, label=str(weight), color='#576574', penwidth='2')
                added_edges.add(edge)
        # Conexión ficticia
        if len(path) > 1:
            dot.edge(path[-2], path[-1], color="#ee5253", penwidth='4', style='dashed')
        dot.render("ruta_mas_corta", view=True)

    # FUNCIÓN CENTRAL PARA GESTIONAR EMERGENCIAS EN CUALQUIER PUNTO
    def gestionar_emergencia_en_punto(location, severity, emergency_type, description):
        estacion, distancia = estacion_mas_cercana(location)
        if not estacion:
            messagebox.showinfo("Emergencia", "No hay estaciones disponibles para atender la emergencia.")
            return

        emergency = emergency_manager.add_emergency(location, severity, emergency_type, description)
        asignacion = simulator.assign_resources(emergency)

        # Notificar a todas las estaciones
        for n in network.nodes:
            noti = f" Emergencia de tipo {emergency_type} en {location}. Estación más cercana: {estacion} (distancia: {distancia})"
            if noti not in notificaciones_globales:
                notificaciones_globales.append(noti)

        messagebox.showinfo(
            "Emergencia",
            f"Emergencia registrada en '{location}' ({emergency_type}).\n"
            f"Estación más cercana: {estacion}\n"
            f"Distancia: {distancia} unidades.\n"
            f"Las demás estaciones han sido notificadas."
        )
        mostrar_asignacion(asignacion, emergency_type)

        # Visualizar la ruta óptima desde la estación más cercana
        temp_graph = {n: [(v, w) for v, w in network.graph[n] if v not in nodos_fuera] for n in network.graph if n not in nodos_fuera}
        distances, prev = dijkstra(temp_graph, estacion, location)
        if location in distances and distances[location] != float('inf'):
            path = reconstruct_path(prev, estacion, location)
            visualizar_ruta_grafica(path)

    def ver_topologia():
        info = f" Nodos: {len(network.nodes)}\n Conexiones: {network.count_edges()}\n\n"
        for node in sorted(network.graph.keys()):
            connections = [(neighbor, weight) for neighbor, weight in network.graph[node]]
            info += f"• {node}:\n"
            for n, w in connections:
                info += f"    ↳ {n}  (peso: {w})\n"
        if nodos_fuera:
            info += f"\n Nodos fuera de servicio: {', '.join(sorted(nodos_fuera))}"
        messagebox.showinfo("Topología de Red", info)

    def reportar_emergencia_estacion():
        nodos_disponibles = sorted(network.nodes - nodos_fuera)
        ubicaciones_ficticias = [
            "Madrid", "Ibague", "Poblado", "Los Patios", "Playa", "Montaña",
            "Ciudad", "Río", "Bosque", "Zona Industrial", "Aeropuerto", "Puerto"
        ]
        opciones = nodos_disponibles + ubicaciones_ficticias

        ubicacion = simpledialog.askstring(
            "Ubicación de emergencia",
            f"Ubicaciones disponibles:\n{opciones}\n¿Dónde ocurre la emergencia?"
        )
        if not ubicacion or ubicacion not in opciones:
            messagebox.showinfo("Error", "Ubicación no válida.")
            return
        if ubicacion in nodos_fuera:
            messagebox.showinfo("Nodo fuera de servicio", "Nodo fuera de servicio. Recalculando rutas...")
            return

        tipo = simpledialog.askstring("Tipo de emergencia", "Tipo (incendio/accidente/robo/inundacion/explosion):")
        if not tipo:
            return
        gravedad = simpledialog.askinteger("Gravedad", "Gravedad (1-10):")
        if not gravedad:
            return
        desc = simpledialog.askstring("Descripción", "Descripción (opcional):") or ""

        nodo_ficticio = None
        temp_graph = {n: [(v, w) for v, w in network.graph[n] if v not in nodos_fuera] for n in network.graph if n not in nodos_fuera}
        ruta_guardada = None
        ruta_es_ficticia = False

        if ubicacion in ubicaciones_ficticias:
            nodo_ficticio = ubicacion
            for est in estaciones:
                if est in temp_graph:
                    peso = random.randint(5, 25)
                    temp_graph.setdefault(nodo_ficticio, []).append((est, peso))
                    temp_graph[est].append((nodo_ficticio, peso))
            min_dist = float('inf')
            estacion_cercana = None
            for est in estaciones:
                if est in temp_graph:
                    dist, prev = dijkstra(temp_graph, est, nodo_ficticio)
                    if nodo_ficticio in dist and dist[nodo_ficticio] < min_dist:
                        min_dist = dist[nodo_ficticio]
                        estacion_cercana = est
                        ruta_guardada = reconstruct_path(prev, estacion_cercana, nodo_ficticio)
                        ruta_es_ficticia = True
            distancia = min_dist
        else:
            # Si la emergencia ocurre en una estación, exclúyela de la búsqueda
            estacion_cercana, distancia = estacion_mas_cercana(ubicacion, excluir=ubicacion)
            # Guardar la ruta ANTES de sacar la estación de servicio
            temp_graph2 = {n: [(v, w) for v, w in network.graph[n] if v not in nodos_fuera] for n in network.graph if n not in nodos_fuera}
            dist, prev = dijkstra(temp_graph2, estacion_cercana, ubicacion)
            if ubicacion in dist and dist[ubicacion] != float('inf'):
                ruta_guardada = reconstruct_path(prev, estacion_cercana, ubicacion)
                ruta_es_ficticia = False

        if not estacion_cercana:
            messagebox.showinfo("Emergencia", "No hay estaciones disponibles para atender la emergencia.")
            return

        emergency = emergency_manager.add_emergency(ubicacion, gravedad, tipo, desc)
        asignacion = simulator.assign_resources(emergency)
        emergency.assigned_station = estacion_cercana
        emergency.assigned_resources = [datos['resource_id'] for datos in asignacion["assignments"].values()] if isinstance(asignacion, dict) and "assignments" in asignacion else []
        emergency.attended = False

        # SACAR EL NODO DE SERVICIO
        if ubicacion in network.nodes:
            nodos_fuera.add(ubicacion)
            network.simulate_node_failure(ubicacion)

        estaciones_afectadas = sorted(network.nodes - nodos_fuera - {ubicacion})
        noti = (
            f" Emergencia de tipo {tipo} en {ubicacion}. "
            f"Estación más cercana: {emergency.assigned_station} (distancia: {distancia})"
        )
        if noti not in notificaciones_globales:
            notificaciones_globales.append(noti)

        ayuda = []
        if isinstance(asignacion, dict) and "assignments" in asignacion:
            for recurso, datos in asignacion["assignments"].items():
                ayuda.append(
                    f"• {recurso.capitalize()}  |  ETA: {datos['eta']} min  |  ID: {datos['resource_id']}"
                )
        ayuda_str = "\n".join(ayuda) if ayuda else "No se pudo asignar ayuda."

        mensaje = (
            f" Emergencia en: {ubicacion}\n"
            f"Tipo: {tipo}\n"
            f"Gravedad: {gravedad}\n\n"
            f" Estación más cercana: {emergency.assigned_station} (distancia: {distancia})\n"
            f" Otras estaciones notificadas: {', '.join(estaciones_afectadas) if estaciones_afectadas else 'Ninguna'}\n\n"
            f" Ayuda enviada:\n{ayuda_str}"
        )
        messagebox.showinfo("Emergencia registrada", mensaje)

        def mostrar_ruta():
            if ruta_guardada:
                if ruta_es_ficticia:
                    visualizar_ruta_grafica_personalizada(ruta_guardada, nodo_ficticio)
                else:
                    visualizar_ruta_grafica(ruta_guardada)
            else:
                messagebox.showinfo("Ruta", "No existe ruta disponible.")

        ventana = tk.Toplevel(root)
        ventana.title("Emergencia registrada")
        ventana.geometry("400x350")
        ventana.configure(bg="#f8f9fa")
        tk.Label(ventana, text=mensaje, bg="#f9f9fa", fg="#222f3e", font=button_font, justify="left", wraplength=380).pack(pady=(18, 10))
        tk.Button(ventana, text="Observar ruta", command=mostrar_ruta, bg="#0984e3", fg="white", font=button_font, width=20).pack(pady=10)
        tk.Button(ventana, text="Cerrar", command=ventana.destroy, bg="#e9ecef", fg="#222f3e", font=button_font, width=20).pack(pady=4)
    def simular_automatica():
        lugares_ficticios = [
            "Madrid", "Ibague", "Poblado", "Los Patios", "Playa", "Montaña",
            "Ciudad", "Río", "Bosque", "Zona Industrial", "Aeropuerto", "Puerto"
        ]
        lugar = random.choice(lugares_ficticios)
        nodo_ficticio = lugar

        # Crear grafo temporal con nodo ficticio conectado a estaciones operativas
        temp_graph = {n: [(v, w) for v, w in network.graph[n] if v not in nodos_fuera] for n in network.graph if n not in nodos_fuera}
        for est in estaciones:
            if est in temp_graph:
                peso = random.randint(5, 25)
                temp_graph.setdefault(nodo_ficticio, []).append((est, peso))
                temp_graph[est].append((nodo_ficticio, peso))

        # Calcular estación más cercana al nodo ficticio y la ruta más corta
        min_dist = float('inf')
        estacion_cercana = None
        mejor_path = []
        for est in estaciones:
            if est in temp_graph:
                dist, prev = dijkstra(temp_graph, est, nodo_ficticio)
                if nodo_ficticio in dist and dist[nodo_ficticio] < min_dist:
                    min_dist = dist[nodo_ficticio]
                    estacion_cercana = est
                    mejor_path = reconstruct_path(prev, est, nodo_ficticio)
        distancia = min_dist

        gravedad = random.randint(1, 10)
        tipos_emergencia = [
            "desastre_natural", "incendio", "accidente_transito", "violencia",
            "salud_publica", "medio_ambiente"
        ]
        tipo = random.choice(tipos_emergencia)
        descripcion = f"Emergencia simulada en {lugar}"

        # Simular ayuda enviada
        ayuda = []
        recursos_tipo = {
            "desastre_natural": ["rescate", "bomberos", "ambulancia", "policia"],
            "incendio": ["bomberos"],
            "accidente_transito": ["ambulancia", "policia"],
            "violencia": ["policia"],
            "salud_publica": ["salud", "ambulancia"],
            "medio_ambiente": ["ambiental", "bomberos"]
        }
        for recurso in recursos_tipo.get(tipo, []):
            ayuda.append(f"{recurso.capitalize()} desde {estacion_cercana}")

        ayuda_str = "\n".join([f"• {a} | ETA: {int(distancia)} minuto{'s' if int(distancia) != 1 else ''}" for a in ayuda]) if ayuda else "No se pudo asignar ayuda."

        # Otras estaciones notificadas
        estaciones_afectadas = sorted(set(estaciones) - {estacion_cercana})

        # REGISTRAR LA EMERGENCIA SIMULADA EN EL MANAGER
        emergencia_simulada = emergency_manager.add_emergency(lugar, gravedad, tipo, descripcion)
        emergencia_simulada.simulada = True
        emergencia_simulada.assigned_station = estacion_cercana
        emergencia_simulada.assigned_resources = ayuda
        emergencia_simulada.attended = False

        # Notificar a todas las estaciones
        for n in estaciones:
            noti = (
                f" Emergencia simulada de tipo {tipo} en {lugar}. "
                f"Estación más cercana: {estacion_cercana} (distancia: {distancia})"
            )
            if noti not in notificaciones_globales:
                notificaciones_globales.append(noti)

        if mejor_path and distancia != float('inf'):
            mensaje = (
                f" Emergencia simulada en: {lugar}\n"
                f"Tipo: {tipo}\n"
                f"Gravedad: {gravedad}\n\n"
                f" Estación respondiendo: {estacion_cercana}\n"
                f" Ruta más corta: {' → '.join(mejor_path)}\n"
                f" Tiempo estimado de llegada: {int(distancia)} minuto{'s' if int(distancia) != 1 else ''}\n"
                f" Otras estaciones notificadas: {', '.join(estaciones_afectadas) if estaciones_afectadas else 'Ninguna'}\n\n"
                f" Ayuda enviada:\n{ayuda_str}"
            )
        else:
            mensaje = (
                f" Emergencia simulada en: {lugar}\n"
                f"Tipo: {tipo}\n"
                f"Gravedad: {gravedad}\n\n"
                f" No hay ruta disponible desde ninguna estación operativa.\n"
                f" Otras estaciones notificadas: {', '.join(estaciones_afectadas) if estaciones_afectadas else 'Ninguna'}\n"
                f" No se pudo asignar ayuda."
            )

        messagebox.showinfo(
            "Emergencia simulada",
            mensaje
        )

        # Visualizar la ruta óptima desde la estación más cercana al nodo ficticio
        if mejor_path and distancia != float('inf'):
            visualizar_ruta_grafica_personalizada(mejor_path, nodo_ficticio)

    def pronostico_ia():
        eventos = [
            {"tipo": "sismo", "prob": 0.2},
            {"tipo": "inundacion", "prob": 0.3},
            {"tipo": "huracan", "prob": 0.1},
            {"tipo": "terremoto", "prob": 0.4}
        ]
        evento = random.choices(eventos, weights=[e["prob"] for e in eventos])[0]
        estaciones_propensas = random.sample(estaciones, k=2)  
        estacion_afectada = random.choice(estaciones_propensas)
        gravedad = random.randint(5, 10)
        dias_prediccion = random.randint(1, 7)
        descripcion = f"Pronóstico IA: {evento['tipo']} con alta probabilidad en {', '.join(estaciones_propensas)}"

        # Estaciones que podrían ayudar (todas operativas menos la afectada
        estaciones_ayuda = [e for e in estaciones if e != estacion_afectada and e not in nodos_fuera]

        messagebox.showinfo(
            "Pronóstico IA",
            f"⚠️ Se predice un {evento['tipo']}.\n"
            f"Estaciones más propensas a ser afectadas: {', '.join(estaciones_propensas)}\n"
            f"Probabilidad de ocurrencia: en aproximadamente {dias_prediccion} día{'s' if dias_prediccion > 1 else ''}.\n\n"
            f"Notificando a: {', '.join(estaciones_ayuda) if estaciones_ayuda else 'Ninguna disponible para ayudar'}"
        )

        # Preguntar si quiere visualizar la ruta
        respuesta = messagebox.askyesno("Visualizar ruta", f"¿Visualizar ruta más corta a {estacion_afectada}?")
        if respuesta:
            estaciones_operativas = [e for e in estaciones if e in network.nodes and e not in nodos_fuera and e != estacion_afectada]
            if estaciones_operativas:
                origen = random.choice(estaciones_operativas)
                temp_graph = {n: [(v, w) for v, w in network.graph[n] if v not in nodos_fuera] for n in network.graph if n not in nodos_fuera}
                distances, prev = dijkstra(temp_graph, origen, estacion_afectada)
                if estacion_afectada in distances and distances[estacion_afectada] != float('inf'):
                    path = reconstruct_path(prev, origen, estacion_afectada)
                    visualizar_ruta_grafica_personalizada(path, estacion_afectada)

    def mostrar_estadisticas():
        em_stats = emergency_manager.get_statistics()
        net_stats = network.get_network_stats()
        estaciones_fuera = sorted(nodos_fuera & set(estaciones))
        info = (
            f" **Estadísticas Generales**\n\n"
            f" Emergencias: {em_stats.get('total', 0)} total\n"
            f" Pendientes: {em_stats.get('pending', 0)}\n"
            f" Atendidas: {em_stats.get('attended', 0)}\n"
            f" Nodos en red: {net_stats.get('total_nodes', 0)}\n"
            f" Conexiones: {net_stats.get('total_connections', 0)}\n"
            f" Estaciones fuera de servicio: {len(estaciones_fuera)}\n"
            f"{'• ' + ', '.join(estaciones_fuera) if estaciones_fuera else ''}"
        )

        def ver_detalles():
            detalles = ""
            if not emergency_manager.emergencies:
                detalles = "No hay emergencias registradas."
            else:
                for idx, e in enumerate(emergency_manager.emergencies, 1):
                    estado = "Atendida" if getattr(e, "attended", False) else "Pendiente"
                    asignacion = getattr(e, "assigned_station", None)
                    recursos = getattr(e, "assigned_resources", None)
                    recursos_str = ""
                    if recursos:
                        recursos_str = f" | Recursos enviados: {', '.join(recursos)}"
                    asignacion_str = f" | Atendida por: {asignacion}" if asignacion else ""
                    detalles += (
                        f"{idx}. Ubicación: {getattr(e, 'location', '?')} | Tipo: {getattr(e, 'emergency_type', getattr(e, 'type', '?'))} | "
                        f"Gravedad: {getattr(e, 'severity', '?')} | Estado: {estado}{asignacion_str}{recursos_str}\n"
                    )
            detalles_win = tk.Toplevel(root)
            detalles_win.title("Detalles de Emergencias")
            detalles_win.geometry("500x400")
            detalles_win.configure(bg="#f8f9fa")
            tk.Label(detalles_win, text="Detalles de todas las emergencias", bg="#f9f9fa", fg="#222f3e", font=button_font).pack(pady=(12, 6))
            text = tk.Text(detalles_win, wrap="word", font=("Segoe UI", 10), bg="#f9f9fa", fg="#222f3e")
            text.insert("1.0", detalles)
            text.config(state="disabled")
            text.pack(expand=True, fill="both", padx=10, pady=10)
            tk.Button(detalles_win, text="Cerrar", command=detalles_win.destroy, bg="#e9ecef", fg="#222f3e", font=button_font).pack(pady=8)

        # Ventana de estadísticas con botón de detalles
        stats_win = tk.Toplevel(root)
        stats_win.title("Estadísticas")
        stats_win.geometry("400x350")
        stats_win.configure(bg="#f8f9fa")
        tk.Label(stats_win, text=info, bg="#f9f9fa", fg="#222f3e", font=button_font, justify="left").pack(pady=(18, 10))
        tk.Button(stats_win, text="Detalles", command=ver_detalles, bg="#0984e3", fg="white", font=button_font, width=18).pack(pady=10)
        tk.Button(stats_win, text="Cerrar", command=stats_win.destroy, bg="#e9ecef", fg="#222f3e", font=button_font, width=18).pack(pady=4)

    def simular_falla():
        disponibles = sorted(set(estaciones) & set(network.nodes) - nodos_fuera)
        failed_node = simpledialog.askstring("Falla de nodo", f"Estaciones disponibles: {disponibles}\nNodo a simular falla:")
        if failed_node and failed_node in disponibles:
            nodos_fuera.add(failed_node)
            network.simulate_node_failure(failed_node)
            for n in network.nodes:
                if n != failed_node:
                    noti = f" Notificación: La estación {failed_node} ha sido desactivada por falla."
                    if noti not in notificaciones_globales:
                        notificaciones_globales.append(noti)
            estaciones_afectadas = sorted(set(estaciones) & set(network.nodes) - nodos_fuera - {failed_node})

            # Ya NO se reasignan emergencias ni se muestra mensaje de reasignación
            messagebox.showinfo(
                "Falla de nodo",
                f"¡Atención! La estación '{failed_node}' ha fallado.\n"
                f"Estaciones notificadas: {', '.join(estaciones_afectadas)}\n\n"
                "Nodo fuera de servicio. Recalculando rutas"
            )
        else:
            messagebox.showinfo("Falla", "Nodo no válido o ya está fuera de servicio.")

    def restaurar_estacion():
        fuera = sorted(set(estaciones) & set(nodos_fuera))
        if not fuera:
            messagebox.showinfo("Restaurar", "No hay estaciones fuera de servicio.")
            return
        opciones = fuera + ["[Restaurar todos]"]
        nodo = simpledialog.askstring(
            "Restaurar estación",
            f"Estaciones fuera de servicio:\n{', '.join(fuera)}\n\n"
            "Escribe el nombre de la estación a restaurar o '[Restaurar todos]' para restaurar toda la red:"
        )
        if nodo == "[Restaurar todos]":
            nodos_fuera.clear()
            network.load_topology("topology.txt")
            messagebox.showinfo("Restaurar", "¡Todas las estaciones han sido restauradas!")
        elif nodo in fuera:
            nodos_fuera.remove(nodo)
            network.load_topology("topology.txt")
            for nf in nodos_fuera:
                network.simulate_node_failure(nf)
            messagebox.showinfo("Restaurar", f"Estación {nodo} restaurada.")
        else:
            messagebox.showinfo("Restaurar", "Estación no válida.")

    def calcular_ruta():
        start = simpledialog.askstring("Ruta", f"Nodos disponibles: {sorted(network.nodes)}\nNodo origen:")
        end = simpledialog.askstring("Ruta", "Nodo destino:")
        if start in network.nodes and end in network.nodes:
            temp_graph = {n: [(v, w) for v, w in network.graph[n] if v not in nodos_fuera] for n in network.graph if n not in nodos_fuera}
            distances, prev = dijkstra(temp_graph, start, end)
            if end in distances and distances[end] != float('inf'):
                path = reconstruct_path(prev, start, end)
                info = f"Ruta más corta: {' → '.join(path)}\nDistancia total: {distances[end]} unidades"
                visualizar_ruta_grafica(path)
            else:
                if end in nodos_fuera:
                    info = f"La estación '{end}' se encuentra en desperfectos y no es accesible."
                elif start in nodos_fuera:
                    info = f"La estación de origen '{start}' se encuentra en desperfectos y no es accesible."
                else:
                    info = "No existe ruta entre los nodos especificados (puede que una estación esté en desperfectos)."
        else:
            info = "Uno o ambos nodos no existen en la red"
        messagebox.showinfo("Ruta", info)

    def visualizar_red():
        network.visualize("emergency_network", exclude_nodes=nodos_fuera)

    def reportar_emergencia_en_nodo():
        nodos = sorted(network.nodes - nodos_fuera)
        if not nodos:
            messagebox.showinfo("Error", "No hay nodos disponibles en la red.")
            return
        nodo = simpledialog.askstring("Seleccionar nodo", f"Nodos disponibles: {nodos}\n¿En qué nodo desea reportar la emergencia?")
        if nodo not in network.nodes or nodo in nodos_fuera:
            messagebox.showinfo("Error", "Nodo no válido o fuera de servicio.")
            return
        severity = simpledialog.askinteger("Gravedad", "Gravedad (1-10):")
        if not severity: return
        emergency_type = simpledialog.askstring("Tipo", "Tipo (incendio/accidente/robo/inundacion/explosion):")
        if not emergency_type: return
        description = simpledialog.askstring("Descripción", "Descripción (opcional):") or ""
        emergency = emergency_manager.add_emergency(nodo, severity, emergency_type, description)
        asignacion = simulator.assign_resources(emergency)
        
        emergency.assigned_station, _ = estacion_mas_cercana(nodo, excluir=nodo)
        emergency.assigned_resources = [datos['resource_id'] for datos in asignacion["assignments"].values()] if isinstance(asignacion, dict) and "assignments" in asignacion else []
        emergency.attended = False

        if nodo in network.nodes:
            nodos_fuera.add(nodo)
            network.simulate_node_failure(nodo)
        estaciones_afectadas = sorted(network.nodes - nodos_fuera - {nodo})
        messagebox.showinfo("Aviso", f"¡Atención! La estación '{nodo}' ha fallado por emergencia.\n"
                                     f"Estaciones notificadas: {', '.join(estaciones_afectadas)}")

        # REASIGNAR EMERGENCIAS PENDIENTES
        pendientes = [
            e for e in emergency_manager.emergencies
            if not getattr(e, "attended", False) and getattr(e, "assigned_station", None) == nodo
        ]
        reasignaciones = []
        for emergencia in pendientes:
            nueva_estacion, nueva_dist = estacion_mas_cercana(emergencia.location, excluir=nodo)
            if nueva_estacion:
                anterior = emergencia.assigned_station
                emergencia.assigned_station = nueva_estacion
                noti = (
                    f"Emergencia en {emergencia.location} ha sido reasignada a {nueva_estacion} "
                    f"por falla de {nodo}."
                )
                if noti not in notificaciones_globales:
                    notificaciones_globales.append(noti)
                reasignaciones.append(
                    f"• Emergencia en {emergencia.location} (tipo: {getattr(emergencia, 'emergency_type', getattr(emergencia, 'type', '?'))}, gravedad: {getattr(emergencia, 'severity', '?')})\n"
                    f"   reasignada de {anterior} a {nueva_estacion}."
                )
            else:
                emergencia.assigned_station = None  
                reasignaciones.append(
                    f"• Emergencia en {emergencia.location} (tipo: {getattr(emergencia, 'emergency_type', getattr(emergencia, 'type', '?'))}, gravedad: {getattr(emergencia, 'severity', '?')})\n"
                    f"   no pudo ser reasignada (no hay estaciones disponibles)."
                )

        # Asignación óptima de recursos para la emergencia recién creada
        if emergency_type in recursos_disponibles:
            recurso, distancia = asignar_recurso_mas_cercano(nodo, emergency_type)
            if recurso:
                messagebox.showinfo("Asignación óptima", f"🚨 {emergency_type.capitalize()} enviados desde {recurso}.\nDistancia: {distancia} unidades.")
            else:
                messagebox.showinfo("Asignación óptima", f"No hay {emergency_type} disponibles.")

    #FUNCIÓN PARA INGRESAR A UNA ESTACIÓN
    def ingresar_estacion():
        nodos = sorted(set(estaciones) & set(network.nodes))
        if not nodos:
            messagebox.showinfo("Error", "No hay estaciones en la red.")
            return
        estacion = simpledialog.askstring("Ingresar a estación", f"Estaciones disponibles: {nodos}\n¿A cuál desea ingresar?")
        if estacion not in nodos:
            messagebox.showinfo("Error", "Estación no válida.")
            return

        est_win = tk.Toplevel(root)
        est_win.title(f"Sistema de {estacion}")
        est_win.geometry("400x500")
        est_win.configure(bg="#f8f9fa")

        est_font = font.Font(family="Segoe UI", size=14, weight="bold")
        tk.Label(est_win, text=f"Estación: {estacion}", bg="#f9f9fa", fg="#222f3e", font=est_font).pack(pady=(10, 5))

        def ver_topologia_estacion():
            info = f"📡 Nodos: {len(network.nodes)}\n🔗 Conexiones: {network.count_edges()}\n\n"
            for node in sorted(network.graph.keys()):
                connections = [(neighbor, weight) for neighbor, weight in network.graph[node]]
                info += f"• {node}:\n"
                for n, w in connections:
                    info += f"    ↳ {n}  (peso: {w})\n"
            if nodos_fuera:
                info += f"\n Nodos fuera de servicio: {', '.join(sorted(nodos_fuera))}"
            messagebox.showinfo("Topología de Red", info)

        def ver_ruta_corta():
            otros = [n for n in (set(estaciones) & set(network.nodes)) if n != estacion and n not in nodos_fuera]
            if not otros:
                messagebox.showinfo("Ruta", "No hay otras estaciones disponibles.")
                return
            destino = simpledialog.askstring("Ruta", f"Estaciones destino disponibles: {otros}\n¿A cuál desea calcular la ruta?")
            if destino not in otros:
                messagebox.showinfo("Ruta", "Estación destino no válida o fuera de servicio.")
                return
            temp_graph = {n: [(v, w) for v, w in network.graph[n] if v not in nodos_fuera] for n in network.graph if n not in nodos_fuera}
            distances, prev = dijkstra(temp_graph, estacion, destino)
            if destino in distances and distances[destino] != float('inf'):
                path = reconstruct_path(prev, estacion, destino)
                info = f"Ruta más corta: {' → '.join(path)}\nDistancia total: {distances[destino]} unidades"
                visualizar_ruta_grafica(path)
            else:
                info = "No existe ruta disponible."
            messagebox.showinfo("Ruta más corta", info)        
           
        def marcar_atendida():
            emergencia_activa = None
            for e in emergency_manager.emergencies:
                if not getattr(e, "attended", False) and getattr(e, "assigned_station", None) == estacion:
                    emergencia_activa = e
                    break
            if emergencia_activa:
                emergencia_activa.attended = True
                emergency_manager.attend_emergency(emergencia_activa)
                if emergencia_activa.location in nodos_fuera:
                    nodos_fuera.remove(emergencia_activa.location)
                    network.load_topology("topology.txt")
                    for nf in nodos_fuera:
                        network.simulate_node_failure(nf)
                messagebox.showinfo("Atendida", f"La emergencia en {emergencia_activa.location} ha sido atendida y la estación ha sido reconectada.")
            else:
                messagebox.showinfo("Atendida", f" No hay emergencia activa asignada a esta estación.\nLa estación está operativa.")

        def ver_notificaciones():
            if not notificaciones_globales:
                messagebox.showinfo("Notifs", "No hay notificaciones nuevas.")
            else:
                messagebox.showinfo("Notifs", "\n".join(notificaciones_globales))

        def ver_emergencias_pendientes():
            pendientes = [
                e for e in emergency_manager.emergencies
                if not getattr(e, "attended", False) and getattr(e, "assigned_station", None) == estacion
            ]
            pendientes.sort(key=lambda e: (-getattr(e, "severity", 0), getattr(e, "timestamp", 0)))
            if pendientes:
                ventana = tk.Toplevel(est_win)
                ventana.title("Emergencias pendientes")
                ventana.geometry(f"600x{80 + 50 * len(pendientes)}")
                ventana.configure(bg="#f8f9fa")
                tk.Label(ventana, text=f"Emergencias pendientes en {estacion}", bg="#f9f9fa", fg="#222f3e", font=button_font).pack(pady=(10, 8))
                for idx, e in enumerate(pendientes, 1):
                    frame_em = tk.Frame(ventana, bg="#f9f9fa")
                    frame_em.pack(fill="x", padx=10, pady=2)
                    info = (
                        f"{idx}. Ubicación: {getattr(e, 'location', '?')} | "
                        f"Tipo: {getattr(e, 'emergency_type', getattr(e, 'type', '?'))} | "
                        f"Gravedad: {getattr(e, 'severity', '?')}"
                    )
                    tk.Label(frame_em, text=info, bg="#f9f9fa", fg="#222f3e", font=("Segoe UI", 10)).pack(side="left", padx=(0, 8))
                    def marcar_atendida_local(em=e, fr=frame_em):
                        em.attended = True
                        emergency_manager.attend_emergency(em)
                        messagebox.showinfo("Atendida", f"La emergencia en {em.location} ha sido marcada como atendida.")
                        fr.destroy()
                    tk.Button(frame_em, text="Atendida", command=marcar_atendida_local, bg="#00b894", fg="white", font=("Segoe UI", 10, "bold"), width=10).pack(side="right")
                tk.Button(ventana, text="Cerrar", command=ventana.destroy, bg="#e9ecef", fg="#222f3e", font=button_font, width=20).pack(pady=10)
            else:
                messagebox.showinfo("Emergencias pendientes", "No hay emergencias pendientes asignadas a esta estación.")

        # Botones del menú de estación
        tk.Button(est_win, text=" Visualizar topología de red", width=32, command=ver_topologia_estacion, bg="#e9ecef", fg="#222f3e", font=button_font).pack(pady=6)
        tk.Button(est_win, text=" Ruta más corta a otra estación", width=32, command=ver_ruta_corta, bg="#e9ecef", fg="#222f3e", font=button_font).pack(pady=6)
        tk.Button(est_win, text=" Agregar emergencia manual", width=32, command=reportar_emergencia_estacion, bg="#e9ecef", fg="#222f3e", font=button_font).pack(pady=6)
        tk.Button(est_win, text=" Marcar emergencia como atendida", width=32, command=marcar_atendida, bg="#e9ecef", fg="#222f3e", font=button_font).pack(pady=6)
        tk.Button(est_win, text=" Ver notificaciones", width=32, command=ver_notificaciones, bg="#e9ecef", fg="#222f3e", font=button_font).pack(pady=6)
        tk.Button(est_win, text=" Ver emergencias pendientes", width=32, command=ver_emergencias_pendientes, bg="#e9ecef", fg="#222f3e", font=button_font).pack(pady=6)
        tk.Button(est_win, text="⬅ Volver al menú principal", width=32, command=est_win.destroy, bg="#e9ecef", fg="#222f3e", font=button_font).pack(pady=12)

   
    def salir():
        root.destroy()

    
    botones = [
        (" Ver topología de red", ver_topologia),  
        (" Simulación automática", simular_automatica),  
        (" Estadísticas", mostrar_estadisticas),  
        (" Simular falla de nodo", simular_falla),  
        (" Restaurar estación", restaurar_estacion),  
        (" Calcular ruta", calcular_ruta),  
        (" Visualizar red", visualizar_red),  
        (" reportar emergencia", reportar_emergencia_estacion),  
        (" Ingresar a una estación", ingresar_estacion),  
        (" Pronóstico IA de emergencias", pronostico_ia), 
        ("Salir", salir)  
    ]

    # Creación de los botones en la interfaz principal
    for texto, comando in botones:
        tk.Button(
            frame, text=texto, width=30, height=1, command=comando,
            bg="#e9ecef", fg="#222f3e", font=button_font, relief="groove", bd=2, activebackground="#dee2e6"
        ).pack(pady=4)

    
    root.mainloop()


run_gui()
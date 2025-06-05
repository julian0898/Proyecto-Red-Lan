# main.py
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

# Especifica la ruta a Graphviz si es necesario
os.environ["PATH"] += os.pathsep + r"C:\Program Files\Graphviz\bin"

notificaciones_globales = []

recursos_disponibles = {
    "bomberos": ["Estacion1", "Estacion3"],
    "ambulancia": ["Estacion2", "Estacion5"],
    "policia": ["Estacion4", "Estacion6"]
}

estaciones = ["Estacion1", "Estacion2", "Estacion3", "Estacion4", "Estacion5", "Estacion6"]

def run_gui():
    network = Network()
    emergency_manager = EmergencyManager()
    simulator = EmergencySimulator()
    nodos_fuera = set()

    network.load_topology("topology.txt")

    root = tk.Tk()
    root.title("Simulador de Red LAN para Emergencias")
    root.geometry("400x500")
    root.configure(bg="#f8f9fa")

    # Fuentes profesionales
    title_font = font.Font(family="Segoe UI", size=18, weight="bold")
    subtitle_font = font.Font(family="Segoe UI", size=10, slant="italic")
    button_font = font.Font(family="Segoe UI", size=11, weight="normal")

    # Título
    tk.Label(root, text="Simulador de Red LAN para Emergencias", bg="#f8f9fa", fg="#222f3e", font=title_font).pack(pady=(18, 2))
    tk.Label(root, text="Gestión y simulación de emergencias en red", bg="#f9f9fa", fg="#576574", font=subtitle_font).pack(pady=(0, 10))

    # Frame para centrar botones
    frame = tk.Frame(root, bg="#f9f9fa")
    frame.pack(expand=True)

    def asignar_recurso_mas_cercano(emergency_location, resource_type):
        min_dist = float('inf')
        mejor_recurso = None
        for recurso in recursos_disponibles.get(resource_type, []):
            temp_graph = {n: [(v, w) for v, w in network.graph[n] if v not in nodos_fuera] for n in network.graph if n not in nodos_fuera}
            dist, _ = dijkstra(temp_graph, recurso, emergency_location)
            if emergency_location in dist and dist[emergency_location] < min_dist:
                min_dist = dist[emergency_location]
                mejor_recurso = recurso
        return mejor_recurso, min_dist

    def estacion_mas_cercana(ubicacion_emergencia):
        min_dist = float('inf')
        estacion_cercana = None
        for estacion in estaciones:
            if estacion not in network.nodes or estacion in nodos_fuera:
                continue
            temp_graph = {n: [(v, w) for v, w in network.graph[n] if v not in nodos_fuera] for n in network.graph if n not in nodos_fuera}
            dist, _ = dijkstra(temp_graph, estacion, ubicacion_emergencia)
            if ubicacion_emergencia in dist and dist[ubicacion_emergencia] < min_dist:
                min_dist = dist[ubicacion_emergencia]
                estacion_cercana = estacion
        return estacion_cercana, min_dist

    def mostrar_asignacion(asignacion, emergency_type):
        if not isinstance(asignacion, dict) or "assignments" not in asignacion or not asignacion["assignments"]:
            messagebox.showinfo("Ayuda enviada", "No se pudo asignar ayuda a esta emergencia.")
            return

        tipo_entidad = {
            "incendio": "🚒 Bomberos",
            "accidente": "🚑 Ambulancia y 🚓 Policía",
            "robo": "🚓 Policía",
            "inundacion": "🚒 Bomberos y 🚑 Ambulancia",
            "explosion": "🚒 Bomberos, 🚑 Ambulancia y 🚓 Policía",
            "emergencia_medica": "🚑 Ambulancia",
            "disturbio": "🚓 Policía"
        }
        entidades = []
        for recurso, datos in asignacion["assignments"].items():
            nombre = {
                "bomberos": "🚒 Bomberos",
                "ambulancia": "🚑 Ambulancia",
                "policia": "🚓 Policía"
            }.get(recurso, recurso.capitalize())
            entidades.append(f"• {nombre}  |  ETA: {datos['eta']} min  |  ID: {datos['resource_id']}")
        entidades_str = "\n".join(entidades)
        mensaje = (
            f"🆘 Tipo de emergencia: {tipo_entidad.get(emergency_type, emergency_type.capitalize())}\n\n"
            f"👮‍♂️👩‍🚒👩‍⚕️ **Ayuda enviada:**\n{entidades_str}"
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
                # Si la arista está en el camino más corto, resáltala
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
                color = "#ee5253"  # Rojo para el punto ficticio
            elif node in path:
                color = "#feca57"  # Amarillo para la ruta
            else:
                color = "#a8edea"  # Azul claro para el resto
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

    # --- FUNCIÓN CENTRAL PARA GESTIONAR EMERGENCIAS EN CUALQUIER PUNTO ---
    def gestionar_emergencia_en_punto(location, severity, emergency_type, description):
        estacion, distancia = estacion_mas_cercana(location)
        if not estacion:
            messagebox.showinfo("Emergencia", "No hay estaciones disponibles para atender la emergencia.")
            return

        emergency = emergency_manager.add_emergency(location, severity, emergency_type, description)
        asignacion = simulator.assign_resources(emergency)

        # Notificar a todas las estaciones
        for n in network.nodes:
            noti = f"🔔 Emergencia de tipo {emergency_type} en {location}. Estación más cercana: {estacion} (distancia: {distancia})"
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
        info = f"📡 Nodos: {len(network.nodes)}\n🔗 Conexiones: {network.count_edges()}\n\n"
        for node in sorted(network.graph.keys()):
            connections = [(neighbor, weight) for neighbor, weight in network.graph[node]]
            info += f"• {node}:\n"
            for n, w in connections:
                info += f"    ↳ {n}  (peso: {w})\n"
        if nodos_fuera:
            info += f"\n🚫 Nodos fuera de servicio: {', '.join(sorted(nodos_fuera))}"
        messagebox.showinfo("Topología de Red", info)

    def agregar_emergencia():
        ubicacion = simpledialog.askstring("Ubicación", "¿Dónde ocurre la emergencia? (debe ser un punto conectado a la red)")
        if not ubicacion or ubicacion not in network.nodes:
            messagebox.showinfo("Error", "Ubicación no válida o no conectada a la red.")
            return
        gravedad = simpledialog.askinteger("Gravedad", "Gravedad (1-10):")
        if not gravedad: return
        tipo = simpledialog.askstring("Tipo", "Tipo (incendio/accidente/robo/inundacion/explosion):")
        if not tipo: return
        descripcion = simpledialog.askstring("Descripción", "Descripción (opcional):") or ""
        gestionar_emergencia_en_punto(ubicacion, gravedad, tipo, descripcion)

    def simular_automatica():
        lugares_ficticios = ["Madrid", "Ibague", "Poblado", "Los Patios", "Playa", "Montaña", "Ciudad", "Río", "Bosque", "Zona Industrial", "Aeropuerto", "Puerto"]
        lugar = random.choice(lugares_ficticios)
        # Elige una estación real como "la más cercana"
        estacion_cercana = random.choice([e for e in estaciones if e in network.nodes and e not in nodos_fuera])
        gravedad = random.randint(1, 10)
        tipo = random.choice(["incendio", "accidente", "robo", "inundacion", "explosion"])
        descripcion = f"Emergencia simulada en {lugar}"

        # Notificar a todas las estaciones
        for n in estaciones:
            noti = f"🔔 Emergencia de tipo {tipo} en {lugar}. Estación más cercana: {estacion_cercana}"
            if noti not in notificaciones_globales:
                notificaciones_globales.append(noti)

        messagebox.showinfo(
            "Emergencia simulada",
            f"Emergencia en '{lugar}' ({tipo}).\n"
            f"Estación más cercana: {estacion_cercana}\n"
            f"Las demás estaciones han sido notificadas."
        )

        # Calcula la ruta más corta desde cualquier estación a la estación_cercana (la que atiende)
        # Por ejemplo, desde todas las estaciones operativas (puedes elegir la más lejana, la más cercana, etc.)
        estaciones_operativas = [e for e in estaciones if e in network.nodes and e not in nodos_fuera and e != estacion_cercana]
        if estaciones_operativas:
            # Aquí puedes elegir la estación de origen (por ejemplo, la más lejana, o pedir al usuario)
            origen = random.choice(estaciones_operativas)
            temp_graph = {n: [(v, w) for v, w in network.graph[n] if v not in nodos_fuera] for n in network.graph if n not in nodos_fuera}
            distances, prev = dijkstra(temp_graph, origen, estacion_cercana)
            if estacion_cercana in distances and distances[estacion_cercana] != float('inf'):
                path = reconstruct_path(prev, origen, estacion_cercana)
                # Visualiza la ruta real entre estaciones
                visualizar_ruta_grafica(path)

    def pronostico_ia():
        eventos = [
            {"tipo": "sismo", "prob": 0.2},
            {"tipo": "inundacion", "prob": 0.3},
            {"tipo": "huracan", "prob": 0.1},
            {"tipo": "terremoto", "prob": 0.4}
        ]
        evento = random.choices(eventos, weights=[e["prob"] for e in eventos])[0]
        estaciones_propensas = random.sample(estaciones, k=2)  # Ejemplo: 2 estaciones propensas
        estacion_afectada = random.choice(estaciones_propensas)
        gravedad = random.randint(5, 10)
        descripcion = f"Pronóstico IA: {evento['tipo']} con alta probabilidad en {', '.join(estaciones_propensas)}"
        messagebox.showinfo(
            "Pronóstico IA",
            f"⚠️ Se predice un {evento['tipo']}.\n"
            f"Estaciones más propensas a ser afectadas: {', '.join(estaciones_propensas)}\n"
            f"¿Deseas visualizar la ruta más corta de una estación a la afectada?"
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
                    # Aquí se usa la visualización personalizada para resaltar la estación afectada
                    visualizar_ruta_grafica_personalizada(path, estacion_afectada)
        # También puedes registrar la emergencia si lo deseas
        # gestionar_emergencia_en_punto(estacion_afectada, gravedad, evento["tipo"], descripcion)

    def mostrar_estadisticas():
        em_stats = emergency_manager.get_statistics()
        net_stats = network.get_network_stats()
        info = (
            f"📊 **Estadísticas Generales**\n\n"
            f"🚨 Emergencias: {em_stats.get('total', 0)} total\n"
            f"🕒 Pendientes: {em_stats.get('pending', 0)}\n"
            f"✅ Atendidas: {em_stats.get('attended', 0)}\n"
            f"🌐 Nodos en red: {net_stats.get('total_nodes', 0)}\n"
            f"🔗 Conexiones: {net_stats.get('total_connections', 0)}\n"
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
            text = tk.Text(detalles_win, wrap="word", font=("Segoe UI", 10), bg="#f8f9fa", fg="#222f3e")
            text.insert("1.0", detalles)
            text.config(state="disabled")
            text.pack(expand=True, fill="both", padx=10, pady=10)
            tk.Button(detalles_win, text="Cerrar", command=detalles_win.destroy, bg="#e9ecef", fg="#222f3e", font=button_font).pack(pady=8)

        # Ventana de estadísticas con botón de detalles
        stats_win = tk.Toplevel(root)
        stats_win.title("Estadísticas")
        stats_win.geometry("400x320")
        stats_win.configure(bg="#f8f9fa")
        tk.Label(stats_win, text=info, bg="#f8f9fa", fg="#222f3e", font=button_font, justify="left").pack(pady=(18, 10))
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
                    noti = f"🔔 Notificación: La estación {failed_node} ha sido desactivada por falla."
                    if noti not in notificaciones_globales:
                        notificaciones_globales.append(noti)
            estaciones_afectadas = sorted(set(estaciones) & set(network.nodes) - nodos_fuera - {failed_node})
            messagebox.showinfo(
                "Falla de nodo",
                f"¡Atención! La estación '{failed_node}' ha fallado.\n"
                f"Estaciones notificadas: {', '.join(estaciones_afectadas)}\n\n"
                "Nodo fuera de servicio. Recalculando rutas y emergencias..."
            )
            # NO se crea emergencia ni se asignan recursos aquí
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
        nodos_fuera.add(nodo)
        network.simulate_node_failure(nodo)
        estaciones_afectadas = sorted(network.nodes - nodos_fuera - {nodo})
        messagebox.showinfo("Aviso", f"¡Atención! La estación '{nodo}' ha fallado por emergencia.\n"
                                     f"Estaciones notificadas: {', '.join(estaciones_afectadas)}")
        # Asignación óptima de recursos
        if emergency_type in recursos_disponibles:
            recurso, distancia = asignar_recurso_mas_cercano(nodo, emergency_type)
            if recurso:
                messagebox.showinfo("Asignación óptima", f"🚨 {emergency_type.capitalize()} enviados desde {recurso}.\nDistancia: {distancia} unidades.")
            else:
                messagebox.showinfo("Asignación óptima", f"No hay {emergency_type} disponibles.")

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
                info += f"\n🚫 Nodos fuera de servicio: {', '.join(sorted(nodos_fuera))}"
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

        def reportar_emergencia_estacion():
            # Nodos reales y ubicaciones ficticias
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

            # Si es una ubicación ficticia, crear nodo temporal y conectarlo a la estación más cercana
            nodo_ficticio = None
            temp_graph = {n: [(v, w) for v, w in network.graph[n] if v not in nodos_fuera] for n in network.graph if n not in nodos_fuera}
            if ubicacion in ubicaciones_ficticias:
                nodo_ficticio = ubicacion
                # Conectar el nodo ficticio a todas las estaciones operativas con peso aleatorio (simula distancia)
                for est in estaciones:
                    if est in temp_graph:
                        peso = random.randint(5, 25)
                        temp_graph.setdefault(nodo_ficticio, []).append((est, peso))
                        temp_graph[est].append((nodo_ficticio, peso))
                # Ahora calcula la estación más cercana
                min_dist = float('inf')
                estacion_cercana = None
                for est in estaciones:
                    if est in temp_graph:
                        dist, _ = dijkstra(temp_graph, est, nodo_ficticio)
                        if nodo_ficticio in dist and dist[nodo_ficticio] < min_dist:
                            min_dist = dist[nodo_ficticio]
                            estacion_cercana = est
                distancia = min_dist
            else:
                # Nodo real
                estacion_cercana, distancia = estacion_mas_cercana(ubicacion)

            if not estacion_cercana:
                messagebox.showinfo("Emergencia", "No hay estaciones disponibles para atender la emergencia.")
                return

            # Registrar emergencia y asignar ayuda
            emergency = emergency_manager.add_emergency(ubicacion, gravedad, tipo, desc)
            asignacion = simulator.assign_resources(emergency)
            # Guardar estación y recursos asignados en la emergencia
            emergency.assigned_station = estacion_cercana
            emergency.assigned_resources = [datos['resource_id'] for datos in asignacion["assignments"].values()] if isinstance(asignacion, dict) and "assignments" in asignacion else []
            emergency.attended = False

            if ubicacion in network.nodes:
                nodos_fuera.add(ubicacion)
                network.simulate_node_failure(ubicacion)

            # Notificar a otras estaciones
            estaciones_afectadas = sorted(network.nodes - nodos_fuera - {ubicacion})
            noti = (
                f"🔔 Emergencia de tipo {tipo} en {ubicacion}. "
                f"Estación más cercana: {estacion_cercana} (distancia: {distancia})"
            )
            if noti not in notificaciones_globales:
                notificaciones_globales.append(noti)

            # Mostrar resumen
            ayuda = []
            if isinstance(asignacion, dict) and "assignments" in asignacion:
                for recurso, datos in asignacion["assignments"].items():
                    ayuda.append(
                        f"• {recurso.capitalize()}  |  ETA: {datos['eta']} min  |  ID: {datos['resource_id']}"
                    )
            ayuda_str = "\n".join(ayuda) if ayuda else "No se pudo asignar ayuda."

            mensaje = (
                f"🆘 Emergencia en: {ubicacion}\n"
                f"Tipo: {tipo}\n"
                f"Gravedad: {gravedad}\n\n"
                f"🚨 Estación más cercana: {estacion_cercana} (distancia: {distancia})\n"
                f"🏢 Otras estaciones notificadas: {', '.join(estaciones_afectadas) if estaciones_afectadas else 'Ninguna'}\n\n"
                f"👮‍♂️👩‍🚒👩‍⚕️ Ayuda enviada:\n{ayuda_str}"
            )
            messagebox.showinfo("Emergencia registrada", mensaje)

            # Mostrar mensaje y botón para observar ruta
            def mostrar_ruta():
                if nodo_ficticio:
                    dist, prev = dijkstra(temp_graph, estacion_cercana, nodo_ficticio)
                    if nodo_ficticio in dist and dist[nodo_ficticio] != float('inf'):
                        path = reconstruct_path(prev, estacion_cercana, nodo_ficticio)
                        visualizar_ruta_grafica_personalizada(path, nodo_ficticio)
                else:
                    temp_graph2 = {n: [(v, w) for v, w in network.graph[n] if v not in nodos_fuera] for n in network.graph if n not in nodos_fuera}
                    dist, prev = dijkstra(temp_graph2, estacion_cercana, ubicacion)
                    if ubicacion in dist and dist[ubicacion] != float('inf'):
                        path = reconstruct_path(prev, estacion_cercana, ubicacion)
                        visualizar_ruta_grafica(path)

            ventana = tk.Toplevel(est_win)
            ventana.title("Emergencia registrada")
            ventana.geometry("400x350")
            ventana.configure(bg="#f8f9fa")
            tk.Label(ventana, text=mensaje, bg="#f8f9fa", fg="#222f3e", font=button_font, justify="left", wraplength=380).pack(pady=(18, 10))
            tk.Button(ventana, text="Observar ruta", command=mostrar_ruta, bg="#0984e3", fg="white", font=button_font, width=20).pack(pady=10)
            tk.Button(ventana, text="Cerrar", command=ventana.destroy, bg="#e9ecef", fg="#222f3e", font=button_font, width=20).pack(pady=4)

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
                messagebox.showinfo("Atendida", f"✅ La emergencia en {emergencia_activa.location} ha sido atendida y la estación ha sido reconectada.")
            else:
                messagebox.showinfo("Atendida", f"✅ No hay emergencia activa asignada a esta estación.\nLa estación está operativa.")

        def ver_notificaciones():
            relevantes = [msg for msg in notificaciones_globales if estacion not in msg]
            if not relevantes:
                messagebox.showinfo("Notifs", "No hay notificaciones nuevas.")
            else:
                messagebox.showinfo("Notifs", "\n".join(relevantes))

        tk.Button(est_win, text="👁️ Visualizar topología de red", width=32, command=ver_topologia_estacion, bg="#e9ecef", fg="#222f3e", font=button_font).pack(pady=6)
        tk.Button(est_win, text="🧭 Ruta más corta a otra estación", width=32, command=ver_ruta_corta, bg="#e9ecef", fg="#222f3e", font=button_font).pack(pady=6)
        tk.Button(est_win, text="➕ Agregar emergencia manual", width=32, command=reportar_emergencia_estacion, bg="#e9ecef", fg="#222f3e", font=button_font).pack(pady=6)
        tk.Button(est_win, text="✅ Marcar emergencia como atendida", width=32, command=marcar_atendida, bg="#e9ecef", fg="#222f3e", font=button_font).pack(pady=6)
        tk.Button(est_win, text="🔔 Ver notificaciones", width=32, command=ver_notificaciones, bg="#e9ecef", fg="#222f3e", font=button_font).pack(pady=6)
        tk.Button(est_win, text="📋 Ver emergencias pendientes", width=32, command=ver_emergencias_pendientes, bg="#e9ecef", fg="#222f3e", font=button_font).pack(pady=6)
        tk.Button(est_win, text="⬅️ Volver al menú principal", width=32, command=est_win.destroy, bg="#e9ecef", fg="#222f3e", font=button_font).pack(pady=12)

    def salir():
        root.destroy()

    def ver_emergencias_pendientes():
        pendientes = []
        for e in emergency_manager.emergencies:
            if not getattr(e, "attended", False):
                asignacion = getattr(e, "assigned_station", None)
                pendientes.append(
                    f"Ubicación: {getattr(e, 'location', '?')} | Tipo: {getattr(e, 'emergency_type', getattr(e, 'type', '?'))} | "
                    f"Gravedad: {getattr(e, 'severity', '?')} | Atendida por: {asignacion or 'Sin asignar'}"
                )
        if pendientes:
            messagebox.showinfo("Emergencias pendientes", "\n".join(pendientes))
        else:
            messagebox.showinfo("Emergencias pendientes", "No hay emergencias pendientes.")

    # Botones del menú principal (sin "Agregar emergencia")
    botones = [
        ("🔎 Ver topología de red", ver_topologia),
        # ("➕ Agregar emergencia manual", agregar_emergencia),  # <--- ELIMINADO DEL MENÚ PRINCIPAL
        ("⚡ Simulación automática", simular_automatica),
        ("📊 Estadísticas", mostrar_estadisticas),
        ("❌ Simular falla de nodo", simular_falla),
        ("🔄 Restaurar estación", restaurar_estacion),
        ("🧭 Calcular ruta", calcular_ruta),
        ("🌐 Visualizar red", visualizar_red),
        ("🚨 Reportar emergencia en nodo", reportar_emergencia_en_nodo),
        ("🏢 Ingresar a una estación", ingresar_estacion),
        ("🤖 Pronóstico IA de emergencias", pronostico_ia),
        ("⏹️ Salir", salir)
    ]

    for texto, comando in botones:
        tk.Button(
            frame, text=texto, width=30, height=1, command=comando,
            bg="#e9ecef", fg="#222f3e", font=button_font, relief="groove", bd=2, activebackground="#dee2e6"
        ).pack(pady=4)

    root.mainloop()

run_gui()
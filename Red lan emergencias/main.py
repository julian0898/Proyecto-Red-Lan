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
    tk.Label(root, text="Gestión y simulación de emergencias en red", bg="#f8f9fa", fg="#576574", font=subtitle_font).pack(pady=(0, 10))

    # Frame para centrar botones
    frame = tk.Frame(root, bg="#f8f9fa")
    frame.pack(expand=True)

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
        location = simpledialog.askstring("Ubicación", "Ubicación:")
        if not location: return
        severity = simpledialog.askinteger("Gravedad", "Gravedad (1-10):")
        if not severity: return
        emergency_type = simpledialog.askstring("Tipo", "Tipo (incendio/accidente/robo/inundacion/explosion):")
        if not emergency_type: return
        description = simpledialog.askstring("Descripción", "Descripción (opcional):") or ""
        emergency = emergency_manager.add_emergency(location, severity, emergency_type, description)
        asignacion = simulator.assign_resources(emergency)
        nodos_fuera.add(location)
        network.simulate_node_failure(location)
        for n in network.nodes:
            if n != location:
                noti = f"🔔 Notificación: Emergencia reportada en {location} ({emergency_type})"
                if noti not in notificaciones_globales:
                    notificaciones_globales.append(noti)
        estaciones_afectadas = sorted(network.nodes - nodos_fuera - {location})
        messagebox.showinfo("Emergencia", f"Emergencia registrada en '{location}'.\nEstaciones notificadas: {', '.join(estaciones_afectadas)}")
        mostrar_asignacion(asignacion, emergency_type)

    def simular_automatica():
        if not network.nodes or len(network.nodes - nodos_fuera) == 0:
            messagebox.showinfo("Simulación", "No hay nodos disponibles en la red.")
            return
        location = random.choice(list(network.nodes - nodos_fuera))
        severity = random.randint(1, 10)
        emergency_type = random.choice(["incendio", "accidente", "robo", "inundacion", "explosion"])
        description = f"Emergencia simulada automáticamente en {location}"
        emergency = emergency_manager.add_emergency(location, severity, emergency_type, description)
        asignacion = simulator.assign_resources(emergency)
        nodos_fuera.add(location)
        network.simulate_node_failure(location)
        noti = f"🔔 Notificación: Emergencia reportada en {location} ({emergency_type})"
        if noti not in notificaciones_globales:
            notificaciones_globales.append(noti)
        estaciones_afectadas = sorted(network.nodes - nodos_fuera - {location})
        messagebox.showinfo(
            "Aviso",
            f"¡Atención! Emergencia simulada en '{location}' ({emergency_type}).\n"
            f"Estaciones notificadas: {', '.join(estaciones_afectadas)}"
        )
        mostrar_asignacion(asignacion, emergency_type)
    

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
        messagebox.showinfo("Estadísticas", info)

    def simular_falla():
        failed_node = simpledialog.askstring("Falla de nodo", f"Nodos disponibles: {sorted(network.nodes)}\nNodo a simular falla:")
        if failed_node and failed_node in network.nodes and failed_node not in nodos_fuera:
            nodos_fuera.add(failed_node)
            network.simulate_node_failure(failed_node)
            for n in network.nodes:
                if n != failed_node:
                    noti = f"🔔 Notificación: La estación {failed_node} ha sido desactivada por falla."
                    if noti not in notificaciones_globales:
                        notificaciones_globales.append(noti)
            estaciones_afectadas = sorted(network.nodes - nodos_fuera - {failed_node})
            messagebox.showinfo("Aviso", f"¡Atención! La estación '{failed_node}' ha fallado.\n"
                                         f"Estaciones notificadas: {', '.join(estaciones_afectadas)}")
            emergency_type = "accidente"
            severity = 5
            description = f"Falla automática detectada en {failed_node}"
            emergency = emergency_manager.add_emergency(failed_node, severity, emergency_type, description)
            asignacion = simulator.assign_resources(emergency)
            mostrar_asignacion(asignacion, emergency_type)
        else:
            messagebox.showinfo("Falla", "Nodo no válido o ya está fuera de servicio.")

    def restaurar_estacion():
        if not nodos_fuera:
            messagebox.showinfo("Restaurar", "No hay nodos fuera de servicio.")
            return
        opciones = sorted(nodos_fuera) + ["[Restaurar todos]"]
        nodo = simpledialog.askstring(
            "Restaurar nodo",
            f"Nodos fuera de servicio:\n{', '.join(sorted(nodos_fuera))}\n\n"
            "Escribe el nombre del nodo a restaurar o '[Restaurar todos]' para restaurar toda la red:"
        )
        if nodo == "[Restaurar todos]":
            nodos_fuera.clear()
            network.load_topology("topology.txt")
            messagebox.showinfo("Restaurar", "¡Todos los nodos han sido restaurados!")
        elif nodo in nodos_fuera:
            nodos_fuera.remove(nodo)
            network.load_topology("topology.txt")
            for nf in nodos_fuera:
                network.simulate_node_failure(nf)
            messagebox.showinfo("Restaurar", f"Nodo {nodo} restaurado.")
        else:
            messagebox.showinfo("Restaurar", "Nodo no válido.")

    def calcular_ruta():
        start = simpledialog.askstring("Ruta", f"Nodos disponibles: {sorted(network.nodes)}\nNodo origen:")
        end = simpledialog.askstring("Ruta", "Nodo destino:")
        if start in network.nodes and end in network.nodes:
            temp_graph = {n: [(v, w) for v, w in network.graph[n] if v not in nodos_fuera] for n in network.graph if n not in nodos_fuera}
            distances, prev = dijkstra(temp_graph, start, end)
            if end in distances and distances[end] != float('inf'):
                path = reconstruct_path(prev, start, end)
                info = f"Ruta más corta: {' → '.join(path)}\nDistancia total: {distances[end]} unidades"
                visualizar_ruta_grafica(path)  # <--- Visualiza la ruta gráficamente
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
        mostrar_asignacion(asignacion, emergency_type)

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

    def ingresar_estacion():
        nodos = sorted(network.nodes)
        if not nodos:
            messagebox.showinfo("Error", "No hay estaciones en la red.")
            return
        estacion = simpledialog.askstring("Ingresar a estación", f"Estaciones disponibles: {nodos}\n¿A cuál desea ingresar?")
        if estacion not in network.nodes:
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
            otros = [n for n in network.nodes if n != estacion and n not in nodos_fuera]
            if not otros:
                messagebox.showinfo("Ruta", "No hay otras estaciones disponibles.")
                return
            destino = simpledialog.askstring("Ruta", f"Estaciones destino disponibles: {otros}\n¿A cuál desea calcular la ruta?")
            if destino not in network.nodes or destino == estacion or destino in nodos_fuera:
                messagebox.showinfo("Ruta", "Estación destino no válida o fuera de servicio.")
                return
            temp_graph = {n: [(v, w) for v, w in network.graph[n] if v not in nodos_fuera] for n in network.graph if n not in nodos_fuera}
            distances, prev = dijkstra(temp_graph, estacion, destino)
            if destino in distances and distances[destino] != float('inf'):
                path = reconstruct_path(prev, estacion, destino)
                info = f"Ruta más corta: {' → '.join(path)}\nDistancia total: {distances[destino]} unidades"
            else:
                info = "No existe ruta disponible."
            messagebox.showinfo("Ruta más corta", info)

        def reportar_emergencia_estacion():
            tipo = simpledialog.askstring("Tipo de emergencia", "Tipo (incendio/accidente/robo/inundacion/explosion):")
            if not tipo: return
            gravedad = simpledialog.askinteger("Gravedad", "Gravedad (1-10):")
            if not gravedad: return
            desc = simpledialog.askstring("Descripción", "Descripción (opcional):") or ""
            emergency = emergency_manager.add_emergency(estacion, gravedad, tipo, desc)
            asignacion = simulator.assign_resources(emergency)
            nodos_fuera.add(estacion)
            network.simulate_node_failure(estacion)
            for n in network.nodes:
                if n != estacion:
                    noti = f"🔔 Notificación: Emergencia reportada en {estacion} ({tipo})"
                    if noti not in notificaciones_globales:
                        notificaciones_globales.append(noti)
            mostrar_asignacion(asignacion, tipo)
            messagebox.showinfo("Emergencia", f"Emergencia registrada en {estacion} y ayuda solicitada.")

        def marcar_atendida():
            emergencia_activa = None
            for e in emergency_manager.emergencies:
                if e.location == estacion and getattr(emergency_manager, "attended_emergencies", None) is not None:
                    if e not in emergency_manager.attended_emergencies:
                        emergencia_activa = e
                        break
                elif e.location == estacion:
                    emergencia_activa = e
                    break
            if emergencia_activa and getattr(emergency_manager, "attend_emergency", None):
                emergency_manager.attend_emergency(emergencia_activa)
                if estacion in nodos_fuera:
                    nodos_fuera.remove(estacion)
                    network.load_topology("topology.txt")
                    for nf in nodos_fuera:
                        network.simulate_node_failure(nf)
                messagebox.showinfo("Atendida", f"✅ La emergencia en {estacion} ha sido atendida y la estación ha sido reconectada.")
            else:
                messagebox.showinfo("Atendida", f"✅ No hay emergencia activa en {estacion}.\nLa estación está operativa.")

        def ver_notificaciones():
            relevantes = [msg for msg in notificaciones_globales if estacion not in msg]
            if not relevantes:
                messagebox.showinfo("Notifs", "No hay notificaciones nuevas.")
            else:
                messagebox.showinfo("Notifs", "\n".join(relevantes))

        tk.Button(est_win, text="👁️ Visualizar topología de red", width=32, command=ver_topologia_estacion, bg="#e9ecef", fg="#222f3e", font=button_font).pack(pady=6)
        tk.Button(est_win, text="🧭 Ruta más corta a otra estación", width=32, command=ver_ruta_corta, bg="#e9ecef", fg="#222f3e", font=button_font).pack(pady=6)
        tk.Button(est_win, text="🚨 Reportar emergencia", width=32, command=reportar_emergencia_estacion, bg="#e9ecef", fg="#222f3e", font=button_font).pack(pady=6)
        tk.Button(est_win, text="✅ Marcar emergencia como atendida", width=32, command=marcar_atendida, bg="#e9ecef", fg="#222f3e", font=button_font).pack(pady=6)
        tk.Button(est_win, text="🔔 Ver notificaciones", width=32, command=ver_notificaciones, bg="#e9ecef", fg="#222f3e", font=button_font).pack(pady=6)
        tk.Button(est_win, text="⬅️ Volver al menú principal", width=32, command=est_win.destroy, bg="#e9ecef", fg="#222f3e", font=button_font).pack(pady=12)

    def salir():
        root.destroy()

    def pronostico_ia():
        eventos = [
            {"tipo": "sismo", "radio_km": random.randint(10, 100)},
            {"tipo": "inundacion", "radio_km": random.randint(5, 30)},
            {"tipo": "huracan", "radio_km": random.randint(50, 300)},
            {"tipo": "terremoto", "radio_km": random.randint(20, 150)}
        ]
        evento = random.choice(eventos)
        epicentro = random.choice(list(network.nodes))
        mensaje = f"🤖 Pronóstico IA:\n\n"
        mensaje += f"Evento: {evento['tipo'].capitalize()}\n"
        mensaje += f"Epicentro: {epicentro}\n"
        mensaje += f"Radio de posible afectación: {evento['radio_km']} km\n\n"

        # Simular estaciones afectadas (por distancia ficticia)
        afectadas = []
        for nodo in network.nodes:
            if nodo == epicentro:
                afectadas.append(nodo)
            elif random.random() < 0.3:
                afectadas.append(nodo)
        if afectadas:
            mensaje += f"Estaciones posiblemente afectadas:\n" + ", ".join(afectadas)
            for nodo in afectadas:
                if nodo not in nodos_fuera:
                    nodos_fuera.add(nodo)
                    network.simulate_node_failure(nodo)
                    noti = f"🔔 Notificación: {evento['tipo'].capitalize()} pronosticado en {nodo} (IA)"
                    if noti not in notificaciones_globales:
                        notificaciones_globales.append(noti)
            mensaje += "\n\n🚨 Servicios de emergencia enviados a las estaciones afectadas."
        else:
            mensaje += "No se pronostican afectaciones directas a estaciones."

        messagebox.showinfo("Pronóstico IA", mensaje)
        
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

    botones = [
        ("🔎 Ver topología de red", ver_topologia),
        ("➕ Agregar emergencia manual", agregar_emergencia),
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
import random
import time
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from typing import List, Dict, Optional
from enum import Enum
import json
from tkinter import simpledialog, messagebox

# --- Definición de tipos de emergencia y prioridad ---
class EmergencyType(Enum):
    INCENDIO = "incendio"
    ACCIDENTE = "accidente"
    ROBO = "robo"
    INUNDACION = "inundacion"
    EXPLOSION = "explosion"
    EMERGENCIA_MEDICA = "emergencia_medica"
    DISTURBIO = "disturbio"

class Priority(Enum):
    BAJA = 1
    MEDIA = 2
    ALTA = 3
    CRITICA = 4

# --- Clase que representa una emergencia individual ---
@dataclass
class Emergency:
    id: str
    emergency_type: EmergencyType
    location: str
    description: str
    priority: Priority
    timestamp: datetime
    status: str = "pending"
    response_time: Optional[int] = None
    resources_assigned: List[str] = field(default_factory=list)
    resolution_time: Optional[datetime] = None

    def get_priority(self) -> int:
        # Devuelve el valor numérico de la prioridad
        return self.priority.value

    def get_duration_minutes(self) -> int:
        """Calcula la duración en minutos desde que se reportó la emergencia"""
        if self.resolution_time:
            return int((self.resolution_time - self.timestamp).total_seconds() / 60)
        return int((datetime.now() - self.timestamp).total_seconds() / 60)

    def to_dict(self) -> Dict:
        # Convierte la emergencia a un diccionario para exportar o mostrar
        return {
            "id": self.id,
            "type": self.emergency_type.value,
            "location": self.location,
            "description": self.description,
            "priority": self.priority.name,
            "timestamp": self.timestamp.isoformat(),
            "status": self.status,
            "response_time": self.response_time,
            "resources_assigned": self.resources_assigned,
            "duration_minutes": self.get_duration_minutes()
        }

# --- Generador de emergencias aleatorias y escenarios realistas ---
class EmergencyGenerator:
    def __init__(self):
        # Plantillas de descripciones por tipo de emergencia
        self.emergency_templates = {
            EmergencyType.INCENDIO: [
                "Incendio estructural en edificio residencial",
                "Fuego en vehículo en vía pública",
                "Incendio forestal cerca a zona urbana",
                "Fuego en local comercial",
                "Incendio en bodega industrial"
            ],
            EmergencyType.ACCIDENTE: [
                "Accidente de tránsito con heridos",
                "Colisión múltiple en autopista",
                "Accidente peatonal",
                "Volcamiento de vehículo de carga",
                "Choque frontal entre automóviles"
            ],
            EmergencyType.ROBO: [
                "Robo a mano armada en establecimiento",
                "Hurto de vehículo en zona comercial",
                "Robo a transeúnte en vía pública",
                "Atraco a entidad bancaria",
                "Robo en residencia"
            ],
            EmergencyType.INUNDACION: [
                "Inundación en zona residencial",
                "Desbordamiento de alcantarillado",
                "Inundación por rotura de tubería",
                "Encharcamiento en vía principal",
                "Inundación en túnel vehicular"
            ],
            EmergencyType.EXPLOSION: [
                "Explosión en planta industrial",
                "Fuga de gas con explosión",
                "Explosión de cilindro de gas doméstico",
                "Explosión en estación de combustible",
                "Detonación de artefacto sospechoso"
            ],
            EmergencyType.EMERGENCIA_MEDICA: [
                "Persona inconsciente en vía pública",
                "Ataque cardíaco en centro comercial",
                "Accidente laboral con heridas graves",
                "Emergencia obstétrica",
                "Intoxicación masiva en evento"
            ],
            EmergencyType.DISTURBIO: [
                "Riña masiva en zona comercial",
                "Disturbios en manifestación",
                "Alteración del orden público",
                "Pelea en establecimiento nocturno",
                "Vandalismo en transporte público"
            ]
        }
        # Pesos para prioridad y ubicación (probabilidad de ocurrencia)
        self.priority_weights = {
            Priority.BAJA: 0.3,
            Priority.MEDIA: 0.4,
            Priority.ALTA: 0.2,
            Priority.CRITICA: 0.1
        }
        self.location_weights = {
            "centro": 0.15,
            "zona_rosa": 0.12,
            "chapinero": 0.10,
            "kennedy": 0.08,
            "suba": 0.08,
            "usaquen": 0.07,
            "engativa": 0.06,
            "aeropuerto": 0.05,
            "norte": 0.05,
            "sur": 0.05,
            "oeste": 0.05,
            "este": 0.04,
            "bosa": 0.04,
            "fontibon": 0.03,
            "ciudad_bolivar": 0.03
        }

    def generate_emergency(self, emergency_id: str = None) -> Emergency:
        """Genera una emergencia aleatoria"""
        if not emergency_id:
            emergency_id = f"E{random.randint(1000, 9999)}"

        # Seleccionar tipo de emergencia con pesos diferentes
        emergency_type = random.choices(
            list(EmergencyType),
            weights=[0.2, 0.25, 0.15, 0.1, 0.05, 0.15, 0.1]
        )[0]

        # Seleccionar descripción
        description = random.choice(self.emergency_templates[emergency_type])

        # Seleccionar ubicación con pesos
        location = random.choices(
            list(self.location_weights.keys()),
            weights=list(self.location_weights.values())
        )[0]

        # Seleccionar prioridad
        priority = random.choices(
            list(Priority),
            weights=list(self.priority_weights.values())
        )[0]

        # Timestamp aleatorio en las últimas 2 horas
        timestamp = datetime.now() - timedelta(minutes=random.randint(0, 120))

        return Emergency(
            id=emergency_id,
            emergency_type=emergency_type,
            location=location,
            description=description,
            priority=priority,
            timestamp=timestamp
        )

    def generate_emergency_batch(self, count: int) -> List[Emergency]:
        """Genera múltiples emergencias aleatorias"""
        return [self.generate_emergency() for _ in range(count)]

    def generate_realistic_scenario(self, duration_hours: int = 1) -> List[Emergency]:
        """Genera un escenario realista de emergencias distribuidas en el tiempo"""
        emergencies = []
        start_time = datetime.now() - timedelta(hours=duration_hours)

        # Generar entre 5-15 emergencias por hora
        total_emergencies = random.randint(5 * duration_hours, 15 * duration_hours)

        for i in range(total_emergencies):
            # Distribuir emergencias a lo largo del tiempo
            minutes_offset = random.randint(0, duration_hours * 60)
            timestamp = start_time + timedelta(minutes=minutes_offset)

            emergency = self.generate_emergency(f"E{1000 + i}")
            emergency.timestamp = timestamp
            emergencies.append(emergency)

        # Ordenar por timestamp
        emergencies.sort(key=lambda x: x.timestamp)
        return emergencies

# --- Simulador principal de emergencias ---
class EmergencySimulator:
    def __init__(self, routing_system=None):
        self.generator = EmergencyGenerator()
        self.routing_system = routing_system
        self.active_emergencies: List[Emergency] = []
        self.resolved_emergencies: List[Emergency] = []
        self.simulation_stats = {
            "total_emergencies": 0,
            "avg_response_time": 0,
            "resolution_rate": 0,
            "resource_efficiency": {}
        }
        # Recursos disponibles simulados
        self.available_resources = {
            "bomberos": ["B1", "B2", "B3", "B4", "B5"],
            "ambulancia": ["A1", "A2", "A3", "A4"],
            "policia": ["P1", "P2", "P3", "P4", "P5", "P6", "P7", "P8"]
        }
        self.resource_assignments = {}  # Recursos actualmente asignados

    def add_emergency(self, emergency: Emergency):
        """Agrega una emergencia al simulador"""
        self.active_emergencies.append(emergency)
        self.simulation_stats["total_emergencies"] += 1
        print(f"🚨 Nueva emergencia: {emergency.id} - {emergency.emergency_type.value} en {emergency.location}")

    def assign_resources(self, emergency):
        """Asigna recursos a una emergencia según su tipo"""
        resource_requirements = {
            "incendio": ["bomberos", "ambulancia"],
            "accidente": ["ambulancia", "policia"],
            "robo": ["policia"],
            "inundacion": ["bomberos", "ambulancia"],
            "explosion": ["bomberos", "ambulancia", "policia"],
            "emergencia_medica": ["ambulancia"],
            "disturbio": ["policia"]
        }
        # Acepta tanto Enum como string
        if hasattr(emergency, "emergency_type"):
            if hasattr(emergency.emergency_type, "value"):
                emergency_type_str = emergency.emergency_type.value
            else:
                emergency_type_str = str(emergency.emergency_type)
        else:
            emergency_type_str = str(getattr(emergency, "type", "policia"))
        required_resources = resource_requirements.get(emergency_type_str, ["policia"])
        assignment_result = {"emergency_id": getattr(emergency, "id", "N/A"), "assignments": {}}
        for resource_type in required_resources:
            eta = random.randint(2, 10)
            assignment_result["assignments"][resource_type] = {
                "resource_type": resource_type,
                "eta": eta,
                "resource_id": resource_type.upper() + str(random.randint(1, 9))
            }
        return assignment_result

    def resolve_emergency(self, emergency_id: str, resolution_time: datetime = None) -> bool:
        """Marca una emergencia como resuelta y libera recursos"""
        emergency = self.find_emergency_by_id(emergency_id)
        if not emergency:
            return False

        if not resolution_time:
            resolution_time = datetime.now()

        emergency.status = "resolved"
        emergency.resolution_time = resolution_time

        # Liberar recursos asignados
        for resource_id in emergency.resources_assigned:
            if resource_id in self.resource_assignments:
                del self.resource_assignments[resource_id]

        # Mover a emergencias resueltas
        self.active_emergencies.remove(emergency)
        self.resolved_emergencies.append(emergency)

        print(f"✅ Emergencia {emergency_id} resuelta - Duración: {emergency.get_duration_minutes()} min")
        return True

    def find_emergency_by_id(self, emergency_id: str) -> Optional[Emergency]:
        """Busca una emergencia activa por su ID"""
        for emergency in self.active_emergencies:
            if emergency.id == emergency_id:
                return emergency
        return None

    def simulate_time_progression(self, minutes: int = 60):
        """Simula la progresión del tiempo y resuelve emergencias automáticamente"""
        print(f"\n🕐 Simulando {minutes} minutos de operación...")

        start_time = datetime.now()

        for minute in range(minutes):
            current_time = start_time + timedelta(minutes=minute)

            # Resolver algunas emergencias aleatoriamente
            if self.active_emergencies and random.random() < 0.1:  # 10% chance cada minuto
                emergency_to_resolve = random.choice(self.active_emergencies)
                if emergency_to_resolve.get_duration_minutes() > 15:  # Resolver si ha durado más de 15 min
                    self.resolve_emergency(emergency_to_resolve.id, current_time)

            # Generar nuevas emergencias ocasionalmente
            if random.random() < 0.05:  # 5% chance cada minuto
                new_emergency = self.generator.generate_emergency()
                new_emergency.timestamp = current_time
                self.add_emergency(new_emergency)
                if self.routing_system:
                    self.assign_resources(new_emergency)

        print(f"✅ Simulación completada")

    def run_scenario(self, scenario_name: str = "normal") -> Dict:
        """Ejecuta un escenario predefinido de simulación"""
        print(f"\n🎯 EJECUTANDO ESCENARIO: {scenario_name.upper()}")
        print("=" * 50)

        scenarios = {
            "normal": {"emergencies": 8, "duration": 2},
            "crisis": {"emergencies": 15, "duration": 1},
            "quiet": {"emergencies": 3, "duration": 3}
        }

        scenario_config = scenarios.get(scenario_name, scenarios["normal"])

        # Generar emergencias iniciales
        initial_emergencies = self.generator.generate_realistic_scenario(
            scenario_config["duration"]
        )

        print(f"📊 Generadas {len(initial_emergencies)} emergencias")

        # Procesar emergencias
        for emergency in initial_emergencies[:scenario_config["emergencies"]]:
            self.add_emergency(emergency)
            if self.routing_system:
                self.assign_resources(emergency)

        # Simular progresión
        self.simulate_time_progression(scenario_config["duration"] * 60)

        # Generar reporte
        return self.generate_report()

    def generate_report(self) -> Dict:
        """Genera un reporte con estadísticas de la simulación"""
        total_emergencies = len(self.active_emergencies) + len(self.resolved_emergencies)
        resolved_count = len(self.resolved_emergencias)

        # Calcular estadísticas
        avg_response_time = 0
        if self.resolved_emergencias:
            total_response_time = sum(
                e.response_time for e in self.resolved_emergencias 
                if e.response_time
            )
            avg_response_time = total_response_time / len(self.resolved_emergencias)

        resolution_rate = (resolved_count / total_emergencies * 100) if total_emergencies > 0 else 0

        # Estadísticas por tipo de emergencia
        emergency_types_stats = {}
        all_emergencies = self.active_emergencies + self.resolved_emergencias

        for emergency_type in EmergencyType:
            emergencies_of_type = [e for e in all_emergencies if e.emergency_type == emergency_type]
            resolved_of_type = [e for e in emergencies_of_type if e.status == "resolved"]
            
            if emergencies_of_type:
                emergency_types_stats[emergency_type.value] = {
                    "total": len(emergencies_of_type),
                    "resolved": len(resolved_of_type),
                    "resolution_rate": len(resolved_of_type) / len(emergencies_of_type) * 100,
                    "avg_duration": sum(e.get_duration_minutes() for e in resolved_of_type) / len(resolved_of_type) if resolved_of_type else 0
                }
        
        # Utilización de recursos
        resource_utilization = {}
        for resource_type, resources in self.available_resources.items():
            assigned_count = sum(1 for r_id in resources if r_id in self.resource_assignments)
            utilization_rate = (assigned_count / len(resources)) * 100
            resource_utilization[resource_type] = {
                "total": len(resources),
                "assigned": assigned_count,
                "utilization_rate": utilization_rate
            }
        
        report = {
            "simulation_summary": {
                "total_emergencies": total_emergencies,
                "resolved_emergencies": resolved_count,
                "active_emergencies": len(self.active_emergencies),
                "resolution_rate": round(resolution_rate, 2),
                "avg_response_time": round(avg_response_time, 2)
            },
            "emergency_types": emergency_types_stats,
            "resource_utilization": resource_utilization,
            "active_emergencies_list": [e.to_dict() for e in self.active_emergencies],
            "timestamp": datetime.now().isoformat()
        }
        
        return report

    def print_status(self):
        """Imprime el estado actual del simulador en consola"""
        print(f"\n📊 ESTADO ACTUAL DEL SIMULADOR")
        print(f"Emergencias activas: {len(self.active_emergencies)}")
        print(f"Emergencias resueltas: {len(self.resolved_emergencias)}")
        print(f"Recursos asignados: {len(self.resource_assignments)}")
        
        if self.active_emergencies:
            print("\n🚨 EMERGENCIAS ACTIVAS:")
            for emergency in self.active_emergencies:
                duration = emergency.get_duration_minutes()
                print(f"  {emergency.id}: {emergency.emergency_type.value} en {emergency.location} ({duration} min)")

    def export_results(self, filename: str = "simulation_results.json"):
        """Exporta los resultados de la simulación a un archivo JSON"""
        report = self.generate_report()
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(report, f, indent=2, ensure_ascii=False)
            print(f"📄 Resultados exportados a {filename}")
        except Exception as e:
            print(f"❌ Error al exportar: {e}")

    def get_performance_metrics(self) -> Dict:
        """Obtiene métricas de rendimiento de la simulación"""
        if not self.resolved_emergencias:
            return {"error": "No hay emergencias resueltas para analizar"}
        
        response_times = [e.response_time for e in self.resolved_emergencias if e.response_time]
        durations = [e.get_duration_minutes() for e in self.resolved_emergencias]
        
        metrics = {
            "response_time_stats": {
                "min": min(response_times) if response_times else 0,
                "max": max(response_times) if response_times else 0,
                "avg": sum(response_times) / len(response_times) if response_times else 0,
                "median": sorted(response_times)[len(response_times)//2] if response_times else 0
            },
            "duration_stats": {
                "min": min(durations),
                "max": max(durations),
                "avg": sum(durations) / len(durations),
                "median": sorted(durations)[len(durations)//2]
            },
            "priority_distribution": {},
            "location_hotspots": {}
        }
        
        # Distribución por prioridad
        for priority in Priority:
            count = len([e for e in self.resolved_emergencias if e.priority == priority])
            metrics["priority_distribution"][priority.name] = count
        
        # Puntos calientes por ubicación
        locations = [e.location for e in self.resolved_emergencias]
        for location in set(locations):
            metrics["location_hotspots"][location] = locations.count(location)
        
        return metrics

# --- Función para ejecutar una simulación completa de ejemplo ---
def run_complete_simulation():
    """Ejecuta una demo completa de simulación de emergencias"""
    print("🚨 SIMULADOR DE EMERGENCIAS - DEMO COMPLETO")
    print("=" * 60)
    
    # Crear simulador (sin routing system para demo independiente)
    simulator = EmergencySimulator()
    
    # Ejecutar diferentes escenarios
    scenarios = ["normal", "crisis", "quiet"]
    
    for scenario in scenarios:
        print(f"\n{'='*20} ESCENARIO {scenario.upper()} {'='*20}")
        report = simulator.run_scenario(scenario)
        
        # Mostrar resumen
        summary = report["simulation_summary"]
        print(f"\n📊 RESUMEN DEL ESCENARIO:")
        print(f"  Total emergencias: {summary['total_emergencies']}")
        print(f"  Tasa de resolución: {summary['resolution_rate']}%")
        print(f"  Tiempo promedio respuesta: {summary['avg_response_time']} min")
        
        time.sleep(1)  # Pausa para mejor visualización
    
    # Mostrar métricas finales
    print(f"\n📈 MÉTRICAS FINALES DE RENDIMIENTO:")
    metrics = simulator.get_performance_metrics()
    if "error" not in metrics:
        print(f"  Tiempo respuesta promedio: {metrics['response_time_stats']['avg']:.1f} min")
        print(f"  Duración promedio emergencia: {metrics['duration_stats']['avg']:.1f} min")
    
    # Exportar resultados
    simulator.export_results("demo_simulation_results.json")
    
    print(f"\n✅ Simulación completa finalizada")
    return simulator

# --- Función de prueba básica del sistema ---
def test_emergency_system():
    """Prueba básica del sistema de emergencias"""
    print("🧪 PRUEBA DEL SISTEMA DE EMERGENCIAS")
    print("=" * 40)
    
    # Crear generador y generar emergencias de prueba
    generator = EmergencyGenerator()
    
    print("\n📝 Generando emergencias de ejemplo:")
    for i in range(3):
        emergency = generator.generate_emergency()
        print(f"  {emergency.id}: {emergency.emergency_type.value} - {emergency.priority.name}")
    
    # Crear y probar simulador básico
    simulator = EmergencySimulator()
    batch_emergencies = generator.generate_emergency_batch(5)
    
    for emergency in batch_emergencies:
        simulator.add_emergency(emergency)
    
    simulator.print_status()
    
    print(f"\n✅ Prueba completada exitosamente")

# --- Función para agregar una emergencia desde la interfaz gráfica ---
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
    estaciones_afectadas = sorted(network.nodes - nodos_fuera - {location})
    messagebox.showinfo("Aviso", f"¡Atención! Emergencia en '{location}' ({emergency_type}).\n"
                                 f"Estaciones notificadas: {', '.join(estaciones_afectadas)}")
    mostrar_asignacion(asignacion, emergency_type)

# --- Ejecución directa del simulador si se ejecuta este archivo ---
if __name__ == "__main__":
    run_complete_simulation()
    print(f"\n" + "="*60)
    print("Para usar con el sistema de routing, importa RoutingSystem:")
    print("from routing import RoutingSystem")
    print("routing = RoutingSystem()")
    print("simulator = EmergencySimulator(routing)")
    print("="*60)
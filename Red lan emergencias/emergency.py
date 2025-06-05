# emergency.py
from datetime import datetime
import uuid

class Emergency:
    """
    Representa una emergencia individual.
    Guarda información sobre ubicación, gravedad, tipo, descripción, fecha y estado.
    """
    def __init__(self, location, severity, emergency_type, description=""):
        self.id = str(uuid.uuid4())[:8]  # Identificador único corto para la emergencia
        self.location = location         # Ubicación de la emergencia
        self.severity = severity         # Gravedad de la emergencia
        self.emergency_type = emergency_type  # Tipo de emergencia (incendio, accidente, etc.)
        self.description = description   # Descripción opcional
        self.timestamp = datetime.now()  # Fecha y hora de creación
        self.status = "PENDIENTE"        # Estado inicial

    def __str__(self):
        # Representación legible de la emergencia
        return f"[{self.id}] {self.emergency_type} en {self.location} (Gravedad: {self.severity})"

class EmergencyManager:
    """
    Gestiona todas las emergencias del sistema.
    Permite agregar, marcar como atendidas y obtener estadísticas.
    """
    def __init__(self):
        self.emergencies = []            # Lista de todas las emergencias registradas
        self.attended_emergencies = []   # Lista de emergencias ya atendidas

    def add_emergency(self, location, severity, emergency_type, description=""):
        """
        Agrega una nueva emergencia al sistema.
        """
        emergency = Emergency(location, severity, emergency_type, description)
        self.emergencies.append(emergency)
        return emergency

    def attend_emergency(self, emergency):
        """
        Marca una emergencia como atendida.
        """
        if emergency in self.emergencies and emergency not in self.attended_emergencies:
            self.attended_emergencies.append(emergency)

    def get_statistics(self):
        """
        Devuelve estadísticas de emergencias:
        - total: total de emergencias registradas
        - attended: cuántas han sido atendidas
        - pending: cuántas están pendientes
        """
        total = len(self.emergencies)
        attended = len(self.attended_emergencies)
        pending = total - attended
        return {
            "total": total,
            "attended": attended,
            "pending": pending
        }

# Ejemplo de uso del EmergencyManager:
emergency_manager = EmergencyManager()
failed_node = "Node 42"
severity = "Alta"
emergency_type = "Fallo Crítico"
description = "El nodo 42 ha dejado de funcionar y necesita atención inmediata."

emergency = emergency_manager.add_emergency(failed_node, severity, emergency_type, description)


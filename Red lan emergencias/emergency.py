
from datetime import datetime
import uuid

class Emergency:
    
    def __init__(self, location, severity, emergency_type, description=""):
        self.id = str(uuid.uuid4())[:8]  
        self.location = location         
        self.severity = severity         
        self.emergency_type = emergency_type  
        self.description = description   
        self.timestamp = datetime.now()  
        self.status = "PENDIENTE"        

    def __str__(self):
        # Representación legible de la emergencia
        return f"[{self.id}] {self.emergency_type} en {self.location} (Gravedad: {self.severity})"

class EmergencyManager:
    
    def __init__(self):
        self.emergencies = []            
        self.attended_emergencies = []  

    def add_emergency(self, location, severity, emergency_type, description=""):
        
        emergency = Emergency(location, severity, emergency_type, description)
        self.emergencies.append(emergency)
        return emergency

    def attend_emergency(self, emergency):
        
        if emergency in self.emergencies and emergency not in self.attended_emergencies:
            self.attended_emergencies.append(emergency)

    def get_statistics(self):
        
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


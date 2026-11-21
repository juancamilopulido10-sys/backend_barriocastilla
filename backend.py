"""Backend (almacenamiento) del Barrio Castilla. Define la abstracción y su implementación."""
import json, os
from typing import Protocol

class IDataRepository(Protocol):
    def load(self) -> dict: ...

class JsonFileRepository:
    FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data.json")
    DEFAULT = {"barrio":"Castilla","habitantes":18420,"superficie_km2":3.2,"viviendas":6180,
     "comercios":312,"servicios_activos":47,"lineas_transporte":12,
     "demografia":{"menores_18":24,"entre_18_64":61,"mayores_65":15,"mujeres":9480,"hombres":8720,"otro_nd":220,"por_edad":[4420,3180,4610,3760,2450]},
     "servicios":{"salud":3,"educacion":8,"deporte":5,"cultura":1,"farmacias":12,"cobertura_salud":98},
     "transporte":{"bus":38,"metro":24,"bici":16,"auto":12,"pie":10},
     "comercio":{"almacenes":94,"gastronomia":61,"salud":47,"servicios":38,"moda":29,"tecnologia":22,"otros":21},
     "seguridad":{"incidentes_mes":[42,38,35,30,28,26,31,24,22,20,18],"camaras":38,"variacion_pct":-12},
     "ambiente":{"espacios_verdes_ha":42,"arboles":1240,"calidad_aire":"Buena","reciclaje_pct":68}}

    def load(self) -> dict:
        if os.path.exists(self.FILE):
            try: return json.load(open(self.FILE, encoding="utf-8"))
            except: pass
        return self.DEFAULT

def get_repository() -> IDataRepository:
    return JsonFileRepository()

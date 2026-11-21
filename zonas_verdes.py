"""Backend: reglas de negocio y datos de zonas verdes del Barrio Castilla."""
import json, os, uuid
from typing import Protocol, List, Dict, Any

ZONAS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "zonas_verdes.json")

SEED = [
    {"nombre": "Zona verde cicloruta Castilla", "actividades": "Ciclismo, paseo, ejercicio al aire libre", "lat": 4.63483, "lon": -74.14495, "direccion": "Cl. 7a #78c2"},
    {"nombre": "Parque Castilla (IDRD 08-030)", "actividades": "Juegos infantiles, descanso, paseo", "lat": 4.64096, "lon": -74.14271, "direccion": "Avenida Cra 8"},
    {"nombre": "Nueva Castilla Park", "actividades": "Descanso, paseo, juegos", "lat": 4.65005, "lon": -74.15153, "direccion": "Ak 88d #8C-21"},
    {"nombre": "Plaza Castilla", "actividades": "Descanso, encuentro comunitario", "lat": 4.64631, "lon": -74.14365, "direccion": "Cl. 10 #80f-40"},
    {"nombre": "Casas de Nueva Castilla Park", "actividades": "Juegos infantiles, descanso", "lat": 4.65033, "lon": -74.15116, "direccion": "Ak 88d #87B-75"},
    {"nombre": "Villa Alsacia Park", "actividades": "Descanso, paseo, juegos, deporte", "lat": 4.64437, "lon": -74.13558, "direccion": "Tv. 78d #10B-54"},
    {"nombre": "Castilla Reserved Park", "actividades": "Descanso, paseo", "lat": 4.65412, "lon": -74.15530, "direccion": "Cl. 8a #92-1"},
    {"nombre": "Coliseo Deportivo Castilla", "actividades": "Deporte, eventos, ejercicio", "lat": 4.63942, "lon": -74.13911, "direccion": "Cl. 8b Bis #7343"},
    {"nombre": "Polideportivo Castilla", "actividades": "Deporte, juegos, ejercicio", "lat": 4.63927, "lon": -74.13922, "direccion": "Cl. 8b Bis #73b-1"},
    {"nombre": "Parque de Bolsillo Castilla (08-090)", "actividades": "Descanso, paseo", "lat": 4.63756, "lon": -74.14140, "direccion": "Cl. 7f #76a-19"},
    {"nombre": "Parque Zonal Castilla", "actividades": "Deporte, juegos, lectura, descanso", "lat": 4.6395, "lon": -74.1420, "direccion": "Carrera 74 con Calle 8a Bis"},
]

class IZonasVerdesRepository(Protocol):
    def list_all(self) -> List[Dict[str, Any]]: ...
    def get(self, zid: str) -> Dict[str, Any] | None: ...
    def create(self, data: Dict[str, Any]) -> Dict[str, Any]: ...
    def update(self, zid: str, data: Dict[str, Any]) -> Dict[str, Any] | None: ...
    def delete(self, zid: str) -> bool: ...

class JsonZonasVerdesRepository:
    def __init__(self):
        if not os.path.exists(ZONAS_FILE):
            data = [{"id": str(uuid.uuid4())[:8], **s} for s in SEED]
            with open(ZONAS_FILE, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)

    def _read(self):
        with open(ZONAS_FILE, encoding="utf-8") as f:
            return json.load(f)

    def _write(self, data):
        with open(ZONAS_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def list_all(self):
        return self._read()

    def get(self, zid):
        for z in self._read():
            if z["id"] == zid:
                return z
        return None

    def create(self, data):
        items = self._read()
        nuevo = {"id": str(uuid.uuid4())[:8],
                 "nombre": data.get("nombre", "Sin nombre"),
                 "actividades": data.get("actividades", ""),
                 "lat": float(data.get("lat", 0)),
                 "lon": float(data.get("lon", 0)),
                 "direccion": data.get("direccion")}
        items.append(nuevo)
        self._write(items)
        return nuevo

    def update(self, zid, data):
        items = self._read()
        for z in items:
            if z["id"] == zid:
                z.update({k: v for k, v in data.items() if k in ("nombre", "actividades", "lat", "lon", "direccion")})
                self._write(items)
                return z
        return None

    def delete(self, zid):
        items = self._read()
        new = [z for z in items if z["id"] != zid]
        if len(new) == len(items):
            return False
        self._write(new)
        return True

class ZonasVerdesService:
    def __init__(self, repo: IZonasVerdesRepository):
        self.repo = repo

    def listar(self):
        return self.repo.list_all()

    def obtener(self, zid):
        return self.repo.get(zid)

    def crear(self, data):
        if not data.get("nombre"):
            raise ValueError("El nombre es obligatorio")
        if data.get("lat") is None or data.get("lon") is None:
            raise ValueError("Latitud y longitud son obligatorias")
        return self.repo.create(data)

    def actualizar(self, zid, data):
        if not self.repo.get(zid):
            return None
        return self.repo.update(zid, data)

    def eliminar(self, zid):
        return self.repo.delete(zid)

def get_zonasverdes_service() -> ZonasVerdesService:
    return ZonasVerdesService(JsonZonasVerdesRepository())

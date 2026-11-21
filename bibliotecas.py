"""Backend: reglas de negocio y datos de bibliotecas del Barrio Castilla."""
import json, os, uuid
from typing import Protocol, List, Dict, Any

BIBLIOS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "bibliotecas.json")

# Bibliotecas en el barrio Castilla (fuentes: BibloRed, bogota.gov.co, Google Maps)
SEED = [
    {"nombre": "PPP Castilla (Paradero Paralibros Paraparques)", "horario": "Viernes, sabados y domingos de 9:00 a. m. a 2:00 p. m.", "lat": 4.6420, "lon": -74.1430, "direccion": "Carrera 75 #8A-50, parque Zonal Castilla"},
    {"nombre": "Biblioteca comunitaria e itinerante Alcaravan con rio", "horario": "Consultar horario", "lat": 4.6458675, "lon": -74.1481214, "direccion": "Cl. 8b #82-51, Kennedy"},
    {"nombre": "Biblioteca Publica El Tintal Manuel Zapata Olivella", "horario": "Martes a sabado de 8:00 a. m. a 7:00 p. m.; domingos de 10:00 a. m. a 5:00 p. m.", "lat": 4.6430923, "lon": -74.1547938, "direccion": "Avenida Ciudad de Cali #6C-09, Kennedy"},
]

class IBibliotecasRepository(Protocol):
    def list_all(self) -> List[Dict[str, Any]]: ...
    def get(self, bid: str) -> Dict[str, Any] | None: ...
    def create(self, data: Dict[str, Any]) -> Dict[str, Any]: ...
    def update(self, bid: str, data: Dict[str, Any]) -> Dict[str, Any] | None: ...
    def delete(self, bid: str) -> bool: ...

class JsonBibliotecasRepository:
    def __init__(self):
        if not os.path.exists(BIBLIOS_FILE):
            data = [{"id": str(uuid.uuid4())[:8], **s} for s in SEED]
            with open(BIBLIOS_FILE, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)

    def _read(self):
        with open(BIBLIOS_FILE, encoding="utf-8") as f:
            return json.load(f)

    def _write(self, data):
        with open(BIBLIOS_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def list_all(self):
        return self._read()

    def get(self, bid):
        for b in self._read():
            if b["id"] == bid:
                return b
        return None

    def create(self, data):
        items = self._read()
        nuevo = {"id": str(uuid.uuid4())[:8],
                 "nombre": data.get("nombre", "Sin nombre"),
                 "horario": data.get("horario", ""),
                 "lat": float(data.get("lat", 0)),
                 "lon": float(data.get("lon", 0)),
                 "direccion": data.get("direccion")}
        items.append(nuevo)
        self._write(items)
        return nuevo

    def update(self, bid, data):
        items = self._read()
        for b in items:
            if b["id"] == bid:
                b.update({k: v for k, v in data.items() if k in ("nombre", "horario", "lat", "lon", "direccion")})
                self._write(items)
                return b
        return None

    def delete(self, bid):
        items = self._read()
        new = [b for b in items if b["id"] != bid]
        if len(new) == len(items):
            return False
        self._write(new)
        return True

class BibliotecasService:
    def __init__(self, repo: IBibliotecasRepository):
        self.repo = repo

    def listar(self):
        return self.repo.list_all()

    def obtener(self, bid):
        return self.repo.get(bid)

    def crear(self, data):
        if not data.get("nombre"):
            raise ValueError("El nombre es obligatorio")
        if data.get("lat") is None or data.get("lon") is None:
            raise ValueError("Latitud y longitud son obligatorias")
        return self.repo.create(data)

    def actualizar(self, bid, data):
        if not self.repo.get(bid):
            return None
        return self.repo.update(bid, data)

    def eliminar(self, bid):
        return self.repo.delete(bid)

def get_bibliotecas_service() -> BibliotecasService:
    return BibliotecasService(JsonBibliotecasRepository())

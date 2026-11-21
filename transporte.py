"""Backend: reglas de negocio y datos de transporte publico del Barrio Castilla."""
import json, os, uuid
from typing import Protocol, List, Dict, Any

TRANS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "transporte.json")

# Estaciones de TransMilenio cercanas al barrio Castilla (color rojo, sin linea de ruta)
TM_STATIONS = [
    {"nombre": "Estacion Banderas", "paradas": ["Banderas", "Mandalay", "Castilla", "Av. Boyaca"], "rutas": ["F14", "F-C19", "F-J23", "F-B28", "F-C29", "F-E32", "F-M51", "F-D50", "16", "593"]},
    {"nombre": "Portal Americas", "paradas": ["Portal Americas", "Castilla", "Ciudad Kennedy"], "rutas": ["F14", "F-E32", "F-D50", "16", "9-1", "9-2", "9-3", "9-4"]},
    {"nombre": "Estacion Mandalay", "paradas": ["Mandalay", "Castilla", "Av. Boyaca"], "rutas": ["F423", "F424", "F402", "F407", "F409"]},
    {"nombre": "Transversal 86", "paradas": ["Transversal 86", "Castilla", "Av. Boyaca"], "rutas": ["F427", "A427", "A587"]},
]

# SITP (zonales) - color azul, con paradas por barrio
SITP_ROUTES = [
    {"nombre": "C19 Jardines de Castilla - Germania", "paradas": ["Jardines de Castilla", "Castilla", "Germania", "Centro"]},
    {"nombre": "C125 Villa Alsacia - El Consuelo", "paradas": ["Villa Alsacia", "Castilla", "El Consuelo"]},
    {"nombre": "Z8", "paradas": ["Castilla", "Metrovivienda", "Av. Boyaca"]},
    {"nombre": "E72", "paradas": ["Castilla", "Centro Comercial Andino", "Av. Boyaca"]},
    {"nombre": "ZP-C42", "paradas": ["Castilla", "Av. Boyaca", "Calle 26"]},
    {"nombre": "T48", "paradas": ["Castilla", "Parque Zonal San Ignacio", "Nueva Castilla"]},
    {"nombre": "108 Calle 80 - Kennedy", "paradas": ["Calle 80", "Castilla", "Kennedy"]},
    {"nombre": "16 Portal Americas - Portal Usme", "paradas": ["Portal Americas", "Castilla", "Portal Usme"]},
    {"nombre": "112B Bachue - Centro Internacional", "paradas": ["Bachue", "Castilla", "Centro Internacional"]},
    {"nombre": "13 Brasilia - Germania", "paradas": ["Brasilia", "Castilla", "Germania"]},
    {"nombre": "14 Betania - Chapinero", "paradas": ["Betania", "Castilla", "Chapinero"]},
    {"nombre": "15 Brasil - Marly", "paradas": ["Brasil", "Castilla", "Marly"]},
    {"nombre": "579 Marly - El Recreo", "paradas": ["Marly", "Castilla", "El Recreo"]},
    {"nombre": "593 Chico - Metrovivienda", "paradas": ["Chico", "Castilla", "Metrovivienda"]},
    {"nombre": "C201 Patio Bonito - Paraiso", "paradas": ["Patio Bonito", "Castilla", "Paraiso"]},
    {"nombre": "F401 Tierra Buena", "paradas": ["Tierra Buena", "Castilla", "Av. Boyaca"]},
    {"nombre": "F422 Patio Bonito", "paradas": ["Patio Bonito", "Castilla", "Av. Boyaca"]},
    {"nombre": "F423 Favidi AM", "paradas": ["Favidi", "Castilla", "Av. Boyaca", "Av. Americas"]},
    {"nombre": "F424 Favidi PM", "paradas": ["Favidi", "Castilla", "Av. Boyaca", "Av. Americas"]},
]

# Alimentadores - color verde, con paradas
ALIMENTADORES = [
    {"nombre": "8-3 Castilla", "paradas": ["Castilla", "Kennedy"]},
    {"nombre": "8-1 Kennedy Central", "paradas": ["Kennedy Central", "Castilla"]},
    {"nombre": "8-4 Corabastos", "paradas": ["Corabastos", "Castilla"]},
    {"nombre": "8-5 Biblioteca Tintal", "paradas": ["Biblioteca Tintal", "Castilla"]},
    {"nombre": "8-6 Timiza", "paradas": ["Timiza", "Castilla"]},
    {"nombre": "F402 Palmitas", "paradas": ["Palmitas", "Castilla"]},
    {"nombre": "F407 La Magdalena", "paradas": ["La Magdalena", "Castilla"]},
    {"nombre": "F409 Tierra Buena", "paradas": ["Tierra Buena", "Castilla"]},
    {"nombre": "F425 Circular Timiza", "paradas": ["Timiza", "Castilla"]},
]

class ITransporteRepository(Protocol):
    def list_all(self) -> List[Dict[str, Any]]: ...
    def get(self, tid: str) -> Dict[str, Any] | None: ...
    def create(self, data: Dict[str, Any]) -> Dict[str, Any]: ...
    def update(self, tid: str, data: Dict[str, Any]) -> Dict[str, Any] | None: ...
    def delete(self, tid: str) -> bool: ...

def _seed():
    items = []
    # TransMilenio stations (red, sin linea)
    for s in TM_STATIONS:
        items.append({"id": str(uuid.uuid4())[:8], "nombre": s["nombre"], "categoria": "transmilenio",
                      "color": "red", "paradas": [], "rutas": s["rutas"], "estacion": s["nombre"]})
    # SITP (azul)
    for r in SITP_ROUTES:
        items.append({"id": str(uuid.uuid4())[:8], "nombre": r["nombre"], "categoria": "sitp",
                      "color": "blue", "paradas": r["paradas"], "rutas": [], "estacion": None})
    # Alimentadores (verde)
    for a in ALIMENTADORES:
        items.append({"id": str(uuid.uuid4())[:8], "nombre": a["nombre"], "categoria": "alimentador",
                      "color": "green", "paradas": a["paradas"], "rutas": [], "estacion": None})
    return items

class JsonTransporteRepository:
    def __init__(self):
        if not os.path.exists(TRANS_FILE):
            data = _seed()
            with open(TRANS_FILE, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)

    def _read(self):
        with open(TRANS_FILE, encoding="utf-8") as f:
            return json.load(f)

    def _write(self, data):
        with open(TRANS_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def list_all(self):
        return self._read()

    def get(self, tid):
        for t in self._read():
            if t["id"] == tid:
                return t
        return None

    def create(self, data):
        items = self._read()
        nuevo = {"id": str(uuid.uuid4())[:8],
                 "nombre": data.get("nombre", "Sin nombre"),
                 "categoria": data.get("categoria", "sitp"),
                 "color": data.get("color", "blue"),
                 "paradas": data.get("paradas", []),
                 "rutas": data.get("rutas", []),
                 "estacion": data.get("estacion")}
        items.append(nuevo)
        self._write(items)
        return nuevo

    def update(self, tid, data):
        items = self._read()
        for t in items:
            if t["id"] == tid:
                t.update({k: v for k, v in data.items() if k in ("nombre", "categoria", "color", "paradas", "rutas", "estacion")})
                self._write(items)
                return t
        return None

    def delete(self, tid):
        items = self._read()
        new = [t for t in items if t["id"] != tid]
        if len(new) == len(items):
            return False
        self._write(new)
        return True

class TransporteService:
    def __init__(self, repo):
        self.repo = repo

    def listar(self):
        return self.repo.list_all()

    def obtener(self, tid):
        return self.repo.get(tid)

    def crear(self, data):
        if not data.get("nombre"):
            raise ValueError("El nombre es obligatorio")
        return self.repo.create(data)

    def actualizar(self, tid, data):
        if not self.repo.get(tid):
            return None
        return self.repo.update(tid, data)

    def eliminar(self, tid):
        return self.repo.delete(tid)

def get_transporte_service() -> TransporteService:
    return TransporteService(JsonTransporteRepository())

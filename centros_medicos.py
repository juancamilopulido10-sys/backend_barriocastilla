"""Backend: reglas de negocio y datos de centros medicos del Barrio Castilla."""
import json, os, uuid
from typing import Protocol, List, Dict, Any

MEDICOS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "centros_medicos.json")
GEOJSON_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "api", "castilla.geojson")

# Extras de la web (centros medicos en el barrio Castilla con coordenadas)
EXTRAS = [
    {"nombre": "Centro Medico Kennedy", "lat": 4.6315145, "lon": -74.1501014, "direccion": "Calle 5b #7840"},
    {"nombre": "Centro Radiologico en Castilla", "lat": 4.6419001, "lon": -74.1405183, "direccion": "Cra. 78a #9-39 Loc 1"},
]

class ICentrosMedicosRepository(Protocol):
    def list_all(self) -> List[Dict[str, Any]]: ...
    def get(self, mid: str) -> Dict[str, Any] | None: ...
    def create(self, data: Dict[str, Any]) -> Dict[str, Any]: ...
    def update(self, mid: str, data: Dict[str, Any]) -> Dict[str, Any] | None: ...
    def delete(self, mid: str) -> bool: ...

def _centroid(geometry):
    gtype = geometry.get("type")
    coords = geometry.get("coordinates", [])
    if gtype == "Point":
        return coords[1], coords[0]
    if gtype == "Polygon":
        ring = coords[0]
        lons = [c[0] for c in ring]; lats = [c[1] for c in ring]
        return sum(lats)/len(lats), sum(lons)/len(lons)
    if gtype == "MultiPolygon":
        allpts = [c for poly in coords for ring in poly for c in ring]
        lons = [c[0] for c in allpts]; lats = [c[1] for c in allpts]
        return sum(lats)/len(lats), sum(lons)/len(lons)
    return None, None

def _seed_from_geojson():
    items = []
    try:
        with open(GEOJSON_FILE, encoding="utf-8") as f:
            gj = json.load(f)
    except FileNotFoundError:
        return items
    for feat in gj.get("features", []):
        props = feat.get("properties", {}) or {}
        if props.get("amenity") == "doctors" or props.get("healthcare") == "doctor":
            lat, lon = _centroid(feat.get("geometry", {}))
            if lat is None:
                continue
            name = props.get("name") or "Centro medico sin nombre"
            items.append({"id": str(uuid.uuid4())[:8], "nombre": name,
                          "lat": round(lat, 6), "lon": round(lon, 6),
                          "direccion": props.get("addr:street")})
    # extras de la web
    for e in EXTRAS:
        items.append({"id": str(uuid.uuid4())[:8], "nombre": e["nombre"],
                      "lat": e["lat"], "lon": e["lon"], "direccion": e["direccion"]})
    return items

class JsonCentrosMedicosRepository:
    def __init__(self):
        if not os.path.exists(MEDICOS_FILE):
            data = _seed_from_geojson()
            with open(MEDICOS_FILE, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)

    def _read(self):
        with open(MEDICOS_FILE, encoding="utf-8") as f:
            return json.load(f)

    def _write(self, data):
        with open(MEDICOS_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def list_all(self):
        return self._read()

    def get(self, mid):
        for m in self._read():
            if m["id"] == mid:
                return m
        return None

    def create(self, data):
        items = self._read()
        nuevo = {"id": str(uuid.uuid4())[:8],
                 "nombre": data.get("nombre", "Sin nombre"),
                 "lat": float(data.get("lat", 0)),
                 "lon": float(data.get("lon", 0)),
                 "direccion": data.get("direccion")}
        items.append(nuevo)
        self._write(items)
        return nuevo

    def update(self, mid, data):
        items = self._read()
        for m in items:
            if m["id"] == mid:
                m.update({k: v for k, v in data.items() if k in ("nombre", "lat", "lon", "direccion")})
                self._write(items)
                return m
        return None

    def delete(self, mid):
        items = self._read()
        new = [m for m in items if m["id"] != mid]
        if len(new) == len(items):
            return False
        self._write(new)
        return True

class CentrosMedicosService:
    def __init__(self, repo: ICentrosMedicosRepository):
        self.repo = repo

    def listar(self):
        return self.repo.list_all()

    def obtener(self, mid):
        return self.repo.get(mid)

    def crear(self, data):
        if not data.get("nombre"):
            raise ValueError("El nombre es obligatorio")
        if data.get("lat") is None or data.get("lon") is None:
            raise ValueError("Latitud y longitud son obligatorias")
        return self.repo.create(data)

    def actualizar(self, mid, data):
        if not self.repo.get(mid):
            return None
        return self.repo.update(mid, data)

    def eliminar(self, mid):
        return self.repo.delete(mid)

def get_centrosmedicos_service() -> CentrosMedicosService:
    return CentrosMedicosService(JsonCentrosMedicosRepository())

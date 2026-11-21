"""Backend: reglas de negocio y datos de supermercados del Barrio Castilla."""
import json, os, uuid
from typing import Protocol, List, Dict, Any

SUPERS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "supermercados.json")
GEOJSON_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "api", "castilla.geojson")

class ISupermercadosRepository(Protocol):
    def list_all(self) -> List[Dict[str, Any]]: ...
    def get(self, sid: str) -> Dict[str, Any] | None: ...
    def create(self, data: Dict[str, Any]) -> Dict[str, Any]: ...
    def update(self, sid: str, data: Dict[str, Any]) -> Dict[str, Any] | None: ...
    def delete(self, sid: str) -> bool: ...

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
        if props.get("shop") != "supermarket":
            continue
        lat, lon = _centroid(feat.get("geometry", {}))
        if lat is None:
            continue
        name = props.get("name") or "Supermercado sin nombre"
        items.append({"id": str(uuid.uuid4())[:8], "nombre": name,
                      "lat": round(lat, 6), "lon": round(lon, 6),
                      "direccion": props.get("addr:street")})
    return items

class JsonSupermercadosRepository:
    def __init__(self):
        if not os.path.exists(SUPERS_FILE):
            data = _seed_from_geojson()
            with open(SUPERS_FILE, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)

    def _read(self):
        with open(SUPERS_FILE, encoding="utf-8") as f:
            return json.load(f)

    def _write(self, data):
        with open(SUPERS_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def list_all(self):
        return self._read()

    def get(self, sid):
        for s in self._read():
            if s["id"] == sid:
                return s
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

    def update(self, sid, data):
        items = self._read()
        for s in items:
            if s["id"] == sid:
                s.update({k: v for k, v in data.items() if k in ("nombre", "lat", "lon", "direccion")})
                self._write(items)
                return s
        return None

    def delete(self, sid):
        items = self._read()
        new = [s for s in items if s["id"] != sid]
        if len(new) == len(items):
            return False
        self._write(new)
        return True

class SupermercadosService:
    def __init__(self, repo: ISupermercadosRepository):
        self.repo = repo

    def listar(self):
        return self.repo.list_all()

    def obtener(self, sid):
        return self.repo.get(sid)

    def crear(self, data):
        if not data.get("nombre"):
            raise ValueError("El nombre es obligatorio")
        if data.get("lat") is None or data.get("lon") is None:
            raise ValueError("Latitud y longitud son obligatorias")
        return self.repo.create(data)

    def actualizar(self, sid, data):
        if not self.repo.get(sid):
            return None
        return self.repo.update(sid, data)

    def eliminar(self, sid):
        return self.repo.delete(sid)

def get_supermercados_service() -> SupermercadosService:
    return SupermercadosService(JsonSupermercadosRepository())

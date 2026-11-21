"""Backend: reglas de negocio y datos de cultos religiosos del Barrio Castilla."""
import json, os, uuid
from typing import Protocol, List, Dict, Any

CULTOS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "cultos_religiosos.json")
GEOJSON_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "api", "castilla.geojson")

class ICultosRepository(Protocol):
    def list_all(self) -> List[Dict[str, Any]]: ...
    def get(self, cid: str) -> Dict[str, Any] | None: ...
    def create(self, data: Dict[str, Any]) -> Dict[str, Any]: ...
    def update(self, cid: str, data: Dict[str, Any]) -> Dict[str, Any] | None: ...
    def delete(self, cid: str) -> bool: ...

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
        if props.get("amenity") != "place_of_worship":
            continue
        lat, lon = _centroid(feat.get("geometry", {}))
        if lat is None:
            continue
        name = props.get("name") or "Culto religioso sin nombre"
        items.append({"id": str(uuid.uuid4())[:8], "nombre": name,
                      "horario": props.get("opening_hours") or "Consultar horario",
                      "religion": props.get("religion"),
                      "denominacion": props.get("denomination"),
                      "lat": round(lat, 6), "lon": round(lon, 6),
                      "direccion": props.get("addr:street")})
    return items

class JsonCultosRepository:
    def __init__(self):
        if not os.path.exists(CULTOS_FILE):
            data = _seed_from_geojson()
            with open(CULTOS_FILE, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)

    def _read(self):
        with open(CULTOS_FILE, encoding="utf-8") as f:
            return json.load(f)

    def _write(self, data):
        with open(CULTOS_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def list_all(self):
        return self._read()

    def get(self, cid):
        for c in self._read():
            if c["id"] == cid:
                return c
        return None

    def create(self, data):
        items = self._read()
        nuevo = {"id": str(uuid.uuid4())[:8],
                 "nombre": data.get("nombre", "Sin nombre"),
                 "horario": data.get("horario", ""),
                 "religion": data.get("religion"),
                 "denominacion": data.get("denominacion"),
                 "lat": float(data.get("lat", 0)),
                 "lon": float(data.get("lon", 0)),
                 "direccion": data.get("direccion")}
        items.append(nuevo)
        self._write(items)
        return nuevo

    def update(self, cid, data):
        items = self._read()
        for c in items:
            if c["id"] == cid:
                c.update({k: v for k, v in data.items() if k in ("nombre", "horario", "religion", "denominacion", "lat", "lon", "direccion")})
                self._write(items)
                return c
        return None

    def delete(self, cid):
        items = self._read()
        new = [c for c in items if c["id"] != cid]
        if len(new) == len(items):
            return False
        self._write(new)
        return True

class CultosService:
    def __init__(self, repo: ICultosRepository):
        self.repo = repo

    def listar(self):
        return self.repo.list_all()

    def obtener(self, cid):
        return self.repo.get(cid)

    def crear(self, data):
        if not data.get("nombre"):
            raise ValueError("El nombre es obligatorio")
        if data.get("lat") is None or data.get("lon") is None:
            raise ValueError("Latitud y longitud son obligatorias")
        return self.repo.create(data)

    def actualizar(self, cid, data):
        if not self.repo.get(cid):
            return None
        return self.repo.update(cid, data)

    def eliminar(self, cid):
        return self.repo.delete(cid)

def get_cultos_service() -> CultosService:
    return CultosService(JsonCultosRepository())

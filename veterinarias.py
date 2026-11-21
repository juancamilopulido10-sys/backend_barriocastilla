"""Backend: reglas de negocio y datos de veterinarias del Barrio Castilla."""
import json, os, uuid
from typing import Protocol, List, Dict, Any

VET_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "veterinarias.json")
GEOJSON_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "api", "castilla.geojson")

class IVeterinariasRepository(Protocol):
    def list_all(self) -> List[Dict[str, Any]]: ...
    def get(self, vid: str) -> Dict[str, Any] | None: ...
    def create(self, data: Dict[str, Any]) -> Dict[str, Any]: ...
    def update(self, vid: str, data: Dict[str, Any]) -> Dict[str, Any] | None: ...
    def delete(self, vid: str) -> bool: ...

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
        if props.get("amenity") != "veterinary":
            continue
        lat, lon = _centroid(feat.get("geometry", {}))
        if lat is None:
            continue
        name = props.get("name") or "Veterinaria sin nombre"
        horario = props.get("opening_hours") or "Consultar horario"
        items.append({"id": str(uuid.uuid4())[:8], "nombre": name,
                      "horario": horario,
                      "lat": round(lat, 6), "lon": round(lon, 6),
                      "direccion": props.get("addr:street")})
    return items

class JsonVeterinariasRepository:
    def __init__(self):
        if not os.path.exists(VET_FILE):
            data = _seed_from_geojson()
            with open(VET_FILE, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)

    def _read(self):
        with open(VET_FILE, encoding="utf-8") as f:
            return json.load(f)

    def _write(self, data):
        with open(VET_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def list_all(self):
        return self._read()

    def get(self, vid):
        for v in self._read():
            if v["id"] == vid:
                return v
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

    def update(self, vid, data):
        items = self._read()
        for v in items:
            if v["id"] == vid:
                v.update({k: val for k, val in data.items() if k in ("nombre", "horario", "lat", "lon", "direccion")})
                self._write(items)
                return v
        return None

    def delete(self, vid):
        items = self._read()
        new = [v for v in items if v["id"] != vid]
        if len(new) == len(items):
            return False
        self._write(new)
        return True

class VeterinariasService:
    def __init__(self, repo: IVeterinariasRepository):
        self.repo = repo

    def listar(self):
        return self.repo.list_all()

    def obtener(self, vid):
        return self.repo.get(vid)

    def crear(self, data):
        if not data.get("nombre"):
            raise ValueError("El nombre es obligatorio")
        if data.get("lat") is None or data.get("lon") is None:
            raise ValueError("Latitud y longitud son obligatorias")
        return self.repo.create(data)

    def actualizar(self, vid, data):
        if not self.repo.get(vid):
            return None
        return self.repo.update(vid, data)

    def eliminar(self, vid):
        return self.repo.delete(vid)

def get_veterinarias_service() -> VeterinariasService:
    return VeterinariasService(JsonVeterinariasRepository())

"""Backend: reglas de negocio y datos de avaluo/predios del Barrio Castilla."""
import json, os, uuid
from typing import Protocol, List, Dict, Any

PREDIOS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "predios.json")
GEOJSON_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "api", "castilla.geojson")

class IPrediosRepository(Protocol):
    def list_all(self) -> List[Dict[str, Any]]: ...
    def get(self, pid: str) -> Dict[str, Any] | None: ...
    def create(self, data: Dict[str, Any]) -> Dict[str, Any]: ...
    def update(self, pid: str, data: Dict[str, Any]) -> Dict[str, Any] | None: ...
    def delete(self, pid: str) -> bool: ...

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
        if "building" not in props:
            continue
        if not props.get("addr:street"):
            continue
        lat, lon = _centroid(feat.get("geometry", {}))
        if lat is None:
            continue
        name = props.get("name")
        house = props.get("addr:housenumber")
        if not name:
            name = f"Predio {house}" if house else f"Predio {props.get('addr:street')}"
        tipo = props.get("building", "residencial")
        niveles = props.get("building:levels")
        direccion = props.get("addr:street")
        if props.get("addr:housenumber"):
            direccion = f"{props.get('addr:street')} {props.get('addr:housenumber')}"
        desc = f"{tipo.capitalize()}, {niveles + ' niveles' if niveles else 'niveles N/D'}, direccion: {direccion}"
        items.append({"id": str(uuid.uuid4())[:8], "nombre": name,
                      "tipo": tipo, "niveles": niveles, "direccion": direccion,
                      "avaluo": 0, "descripcion": desc,
                      "lat": round(lat, 6), "lon": round(lon, 6)})
    return items

class JsonPrediosRepository:
    def __init__(self):
        if not os.path.exists(PREDIOS_FILE):
            data = _seed_from_geojson()
            with open(PREDIOS_FILE, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)

    def _read(self):
        with open(PREDIOS_FILE, encoding="utf-8") as f:
            return json.load(f)

    def _write(self, data):
        with open(PREDIOS_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def list_all(self):
        return self._read()

    def get(self, pid):
        for p in self._read():
            if p["id"] == pid:
                return p
        return None

    def create(self, data):
        items = self._read()
        nuevo = {"id": str(uuid.uuid4())[:8],
                 "nombre": data.get("nombre", "Sin nombre"),
                 "tipo": data.get("tipo", "residencial"),
                 "niveles": data.get("niveles"),
                 "direccion": data.get("direccion"),
                 "avaluo": float(data.get("avaluo", 0)),
                 "descripcion": data.get("descripcion", ""),
                 "lat": float(data.get("lat", 0)),
                 "lon": float(data.get("lon", 0))}
        items.append(nuevo)
        self._write(items)
        return nuevo

    def update(self, pid, data):
        items = self._read()
        for p in items:
            if p["id"] == pid:
                p.update({k: v for k, v in data.items() if k in ("nombre", "tipo", "niveles", "direccion", "avaluo", "descripcion", "lat", "lon")})
                self._write(items)
                return p
        return None

    def delete(self, pid):
        items = self._read()
        new = [p for p in items if p["id"] != pid]
        if len(new) == len(items):
            return False
        self._write(new)
        return True

class PrediosService:
    def __init__(self, repo: IPrediosRepository):
        self.repo = repo

    def listar(self):
        return self.repo.list_all()

    def obtener(self, pid):
        return self.repo.get(pid)

    def crear(self, data):
        if not data.get("nombre"):
            raise ValueError("El nombre es obligatorio")
        return self.repo.create(data)

    def actualizar(self, pid, data):
        if not self.repo.get(pid):
            return None
        return self.repo.update(pid, data)

    def eliminar(self, pid):
        return self.repo.delete(pid)

def get_predios_service() -> PrediosService:
    return PrediosService(JsonPrediosRepository())

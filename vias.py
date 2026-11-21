"""Backend: reglas de negocio y datos de vias del Barrio Castilla."""
import json, os, uuid, math
from typing import Protocol, List, Dict, Any

VIAS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "vias.json")
GEOJSON_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "api", "castilla.geojson")

def _haversine(lat1, lon1, lat2, lon2):
    R = 6371000
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2-lat1)
    dl = math.radians(lon2-lon1)
    a = math.sin(dphi/2)**2 + math.cos(p1)*math.cos(p2)*math.sin(dl/2)**2
    return 2*R*math.asin(math.sqrt(a))

def _tipo(highway):
    if highway in ("primary", "trunk", "secondary"):
        return "principal"
    if highway in ("tertiary", "primary_link", "secondary_link", "trunk_link", "unclassified"):
        return "secundaria"
    return "local"

class IViasRepository(Protocol):
    def list_all(self) -> List[Dict[str, Any]]: ...
    def get(self, vid: str) -> Dict[str, Any] | None: ...
    def create(self, data: Dict[str, Any]) -> Dict[str, Any]: ...
    def update(self, vid: str, data: Dict[str, Any]) -> Dict[str, Any] | None: ...
    def delete(self, vid: str) -> bool: ...

def _seed_from_geojson():
    # group segments by (name, tipo)
    groups = {}
    try:
        with open(GEOJSON_FILE, encoding="utf-8") as f:
            gj = json.load(f)
    except FileNotFoundError:
        return []
    for feat in gj.get("features", []):
        p = feat.get("properties", {}) or {}
        highway = p.get("highway")
        name = p.get("name")
        if not highway or not name:
            continue
        tipo = _tipo(highway)
        geom = feat.get("geometry", {})
        if geom.get("type") != "LineString":
            continue
        coords = geom.get("coordinates", [])
        if len(coords) < 2:
            continue
        latlons = [[c[1], c[0]] for c in coords]
        # length
        length = 0
        for i in range(len(latlons)-1):
            length += _haversine(latlons[i][0], latlons[i][1], latlons[i+1][0], latlons[i+1][1])
        key = (name, tipo)
        if key not in groups:
            groups[key] = {"nombre": name, "tipo": tipo, "longitud_m": 0, "ruta": [], "lat": 0, "lon": 0, "n": 0}
        g = groups[key]
        g["longitud_m"] += length
        g["ruta"].extend(latlons)
        # centroid accumulator
        for pt in latlons:
            g["lat"] += pt[0]
            g["lon"] += pt[1]
            g["n"] += 1
    items = []
    for key, g in groups.items():
        if g["n"] == 0:
            continue
        if g["tipo"] != "principal":
            continue
        items.append({"id": str(uuid.uuid4())[:8],
                      "nombre": g["nombre"],
                      "tipo": g["tipo"],
                      "longitud_m": round(g["longitud_m"], 1),
                      "lat": round(g["lat"]/g["n"], 6),
                      "lon": round(g["lon"]/g["n"], 6),
                      "ruta": g["ruta"]})
    return items

class JsonViasRepository:
    def __init__(self):
        if not os.path.exists(VIAS_FILE):
            data = _seed_from_geojson()
            with open(VIAS_FILE, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)

    def _read(self):
        with open(VIAS_FILE, encoding="utf-8") as f:
            return json.load(f)

    def _write(self, data):
        with open(VIAS_FILE, "w", encoding="utf-8") as f:
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
                 "tipo": data.get("tipo", "local"),
                 "longitud_m": float(data.get("longitud_m", 0)),
                 "lat": float(data.get("lat", 0)),
                 "lon": float(data.get("lon", 0)),
                 "ruta": data.get("ruta", [])}
        items.append(nuevo)
        self._write(items)
        return nuevo

    def update(self, vid, data):
        items = self._read()
        for v in items:
            if v["id"] == vid:
                v.update({k: val for k, val in data.items() if k in ("nombre", "tipo", "longitud_m", "lat", "lon", "ruta")})
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

class ViasService:
    def __init__(self, repo):
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

def get_vias_service() -> ViasService:
    return ViasService(JsonViasRepository())

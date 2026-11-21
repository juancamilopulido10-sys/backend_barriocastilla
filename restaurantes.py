"""Backend: reglas de negocio y datos de restaurantes del Barrio Castilla."""
import json, os, uuid
from typing import Protocol, List, Dict, Any

REST_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "restaurantes.json")
GEOJSON_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "api", "castilla.geojson")

class IRestaurantesRepository(Protocol):
    def list_all(self) -> List[Dict[str, Any]]: ...
    def get(self, rid: str) -> Dict[str, Any] | None: ...
    def create(self, data: Dict[str, Any]) -> Dict[str, Any]: ...
    def update(self, rid: str, data: Dict[str, Any]) -> Dict[str, Any] | None: ...
    def delete(self, rid: str) -> bool: ...

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
    idx = 1
    try:
        with open(GEOJSON_FILE, encoding="utf-8") as f:
            gj = json.load(f)
    except FileNotFoundError:
        return items
    for feat in gj.get("features", []):
        props = feat.get("properties", {}) or {}
        if props.get("amenity") != "restaurant":
            continue
        # agrupar duplicados: el restaurante 8 es el mismo que el 7
        if idx == 8:
            idx += 1
            continue
        lat, lon = _centroid(feat.get("geometry", {}))
        if lat is None:
            continue
        if idx == 7:
            name = "Americas Jireth Pizza"
        else:
            name = props.get("name") or f"Restaurante sin nombre {idx}"
        items.append({"id": str(uuid.uuid4())[:8], "nombre": name,
                      "cuisine": props.get("cuisine"),
                      "lat": round(lat, 6), "lon": round(lon, 6),
                      "direccion": props.get("addr:street")})
        idx += 1
    return items

class JsonRestaurantesRepository:
    def __init__(self):
        if not os.path.exists(REST_FILE):
            data = _seed_from_geojson()
            with open(REST_FILE, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)

    def _read(self):
        with open(REST_FILE, encoding="utf-8") as f:
            return json.load(f)

    def _write(self, data):
        with open(REST_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def list_all(self):
        return self._read()

    def get(self, rid):
        for r in self._read():
            if r["id"] == rid:
                return r
        return None

    def create(self, data):
        items = self._read()
        nuevo = {"id": str(uuid.uuid4())[:8],
                 "nombre": data.get("nombre", "Sin nombre"),
                 "cuisine": data.get("cuisine"),
                 "lat": float(data.get("lat", 0)),
                 "lon": float(data.get("lon", 0)),
                 "direccion": data.get("direccion")}
        items.append(nuevo)
        self._write(items)
        return nuevo

    def update(self, rid, data):
        items = self._read()
        for r in items:
            if r["id"] == rid:
                r.update({k: v for k, v in data.items() if k in ("nombre", "cuisine", "lat", "lon", "direccion")})
                self._write(items)
                return r
        return None

    def delete(self, rid):
        items = self._read()
        new = [r for r in items if r["id"] != rid]
        if len(new) == len(items):
            return False
        self._write(new)
        return True

class RestaurantesService:
    def __init__(self, repo: IRestaurantesRepository):
        self.repo = repo

    def listar(self):
        return self.repo.list_all()

    def obtener(self, rid):
        return self.repo.get(rid)

    def crear(self, data):
        if not data.get("nombre"):
            raise ValueError("El nombre es obligatorio")
        if data.get("lat") is None or data.get("lon") is None:
            raise ValueError("Latitud y longitud son obligatorias")
        return self.repo.create(data)

    def actualizar(self, rid, data):
        if not self.repo.get(rid):
            return None
        return self.repo.update(rid, data)

    def eliminar(self, rid):
        return self.repo.delete(rid)

def get_restaurantes_service() -> RestaurantesService:
    return RestaurantesService(JsonRestaurantesRepository())

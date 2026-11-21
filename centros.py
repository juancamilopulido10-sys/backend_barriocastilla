"""Backend: reglas de negocio y datos de centros educativos del Barrio Castilla."""
import json, os, uuid
from typing import Protocol, List, Dict, Any

CENTROS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "centros.json")
GEOJSON_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "api", "castilla.geojson")

# Agrupacion de marcadores duplicados a un solo centro educativo con nombre y descripcion.
GRUPOS = {
    2: ("Colegio San Jose de Castilla (sede C)", "Institucion educativa distrital ubicada en el barrio Castilla (Kennedy), Bogota. Forma parte de la red de colegios distritales de la ciudad."),
    7: ("General Gustavo Rojas Pinilla", "Institucion educativa distrital ubicada en el barrio Castilla, Bogota."),
    8: ("Centro Educativo San Luis de Gonzaga Fe y Alegria", "Centro educativo de la fundacion Fe y Alegria ubicado en el barrio Castilla, Bogota. Atiende a la comunidad del sector."),
    21: ("Colegio I.E.D. Castilla", "Institucion Educativa Distrital (IED) Castilla, ubicada en el barrio Castilla, Bogota."),
    22: ("Colegio Isabel Segunda", "Institucion educativa ubicada en el barrio Castilla, Bogota."),
}
NOMBRES = {
    1: ("Gimnasio Maria Luisa Tricheth", "Institucion educativa (gimnasio) ubicada en el barrio Castilla, Bogota."),
    6: ("Jingle School", "Jardin infantil privado ubicado en el barrio Castilla, localidad de Kennedy. Atiende a la primera infancia."),
    23: ("Colegio Distrital Nueva Castilla", "Institucion educativa distrital publica ubicada en el barrio Castilla (Kennedy), Bogota. Forma parte de la red de colegios distritales."),
    25: ("Mimositos", "Jardin infantil ubicado en el barrio Castilla, Bogota."),
}

class ICentrosRepository(Protocol):
    def list_all(self) -> List[Dict[str, Any]]: ...
    def get(self, cid: str) -> Dict[str, Any] | None: ...
    def create(self, data: Dict[str, Any]) -> Dict[str, Any]: ...
    def update(self, cid: str, data: Dict[str, Any]) -> Dict[str, Any] | None: ...
    def delete(self, cid: str) -> bool: ...

def _centroid(geometry):
    gtype = geometry.get("type")
    coords = geometry.get("coordinates", [])
    if gtype == "Point":
        lon, lat = coords[0], coords[1]
        return lat, lon
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
    centers = []
    idx = 0
    try:
        with open(GEOJSON_FILE, encoding="utf-8") as f:
            gj = json.load(f)
    except FileNotFoundError:
        return centers
    # indices de features que son escuelas (en orden)
    school_indices = []
    for feat in gj.get("features", []):
        props = feat.get("properties", {}) or {}
        if props.get("building") == "school" or props.get("amenity") in ("school", "kindergarten", "college", "university"):
            school_indices.append(feat)
    # agrupar: solo emitir un marcador por grupo
    skip = set()
    for i in range(2, 6):   # 2-5 -> grupo en idx 2
        skip.add(i)
    for i in range(9, 21):  # 8-20 -> grupo en idx 8 (1-based: 9..21? ajustar)
        pass
    # Recorremos con indice 1-based
    for i, feat in enumerate(school_indices, start=1):
        props = feat.get("properties", {}) or {}
        lat, lon = _centroid(feat.get("geometry", {}))
        if lat is None:
            continue
        # determinar si este idx es representante de un grupo
        if i in (3, 4, 5):  # duplicados de 2
            continue
        if i in range(9, 21):  # duplicados de 8 (indices 9..20)
            continue
        # nombre/descripcion
        if i in GRUPOS:
            nombre, desc = GRUPOS[i]
        elif i in NOMBRES:
            nombre, desc = NOMBRES[i]
        else:
            nombre = props.get("name") or f"Centro educativo sin nombre {i}"
            desc = "Centro educativo ubicado en el barrio Castilla, Bogota."
        tipo = props.get("amenity") or props.get("building") or "school"
        address = props.get("addr:street")
        centers.append({"id": str(uuid.uuid4())[:8], "nombre": nombre, "descripcion": desc,
                        "tipo": tipo, "lat": round(lat, 6), "lon": round(lon, 6), "direccion": address})
    return centers

class JsonCentrosRepository:
    def __init__(self):
        if not os.path.exists(CENTROS_FILE):
            data = _seed_from_geojson()
            with open(CENTROS_FILE, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)

    def _read(self):
        with open(CENTROS_FILE, encoding="utf-8") as f:
            return json.load(f)

    def _write(self, data):
        with open(CENTROS_FILE, "w", encoding="utf-8") as f:
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
                 "descripcion": data.get("descripcion", ""),
                 "tipo": data.get("tipo", "school"),
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
                c.update({k: v for k, v in data.items() if k in ("nombre", "descripcion", "tipo", "lat", "lon", "direccion")})
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

class CentrosService:
    def __init__(self, repo: ICentrosRepository):
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

def get_centros_service() -> CentrosService:
    return CentrosService(JsonCentrosRepository())

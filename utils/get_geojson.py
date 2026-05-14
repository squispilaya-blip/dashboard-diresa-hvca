import requests, json, os, sys

URLS = [
    "https://raw.githubusercontent.com/gnamb/geojson_peru/master/provincias-peru.json",
    "https://raw.githubusercontent.com/juaneladio/peru-geojson/master/peru_provincias_geo.json",
]
OUT = os.path.join(os.path.dirname(__file__), '..', 'assets', 'huancavelica.geojson')

def _is_hvca(props):
    for k in ('DEPARTAMEN', 'NOMBDEP', 'departamento', 'DEPARTAMENTO'):
        if 'HUANCAVEL' in str(props.get(k, '')).upper():
            return True
    for k in ('UBIGEO', 'ubigeo'):
        if str(props.get(k, '')).startswith('09'):
            return True
    return False

def _normalize_feature(feat):
    p = feat['properties']
    nombre = (p.get('NOMBPROV') or p.get('PROVINCIA') or
              p.get('provincia') or p.get('Name') or '').upper()
    feat['properties']['NOMBPROV'] = nombre
    feat['id'] = nombre
    return feat

def download():
    if os.path.exists(OUT):
        d = json.load(open(OUT, encoding='utf-8'))
        if d.get('features'):
            print(f"GeoJSON ya existe ({len(d['features'])} provincias). OK")
            return True
    for url in URLS:
        try:
            print(f"Descargando: {url}")
            r = requests.get(url, timeout=30)
            r.raise_for_status()
            data = r.json()
            feats = [_normalize_feature(f) for f in data.get('features', []) if _is_hvca(f['properties'])]
            if len(feats) >= 7:
                out = {"type": "FeatureCollection", "features": feats}
                with open(OUT, 'w', encoding='utf-8') as fp:
                    json.dump(out, fp)
                print(f"Guardado: {len(feats)} provincias")
                return True
        except Exception as e:
            print(f"Error: {e}")
    return False

if __name__ == '__main__':
    if not download():
        print("Usando GeoJSON simplificado de respaldo...")
        fallback = {
          "type": "FeatureCollection",
          "features": [
            {"type":"Feature","id":"ACOBAMBA","properties":{"NOMBPROV":"ACOBAMBA"},"geometry":{"type":"Polygon","coordinates":[[[-74.7,-12.7],[-74.3,-12.7],[-74.3,-13.1],[-74.7,-13.1],[-74.7,-12.7]]]}},
            {"type":"Feature","id":"ANGARAES","properties":{"NOMBPROV":"ANGARAES"},"geometry":{"type":"Polygon","coordinates":[[[-74.9,-12.9],[-74.5,-12.9],[-74.5,-13.4],[-74.9,-13.4],[-74.9,-12.9]]]}},
            {"type":"Feature","id":"CASTROVIRREYNA","properties":{"NOMBPROV":"CASTROVIRREYNA"},"geometry":{"type":"Polygon","coordinates":[[[-75.5,-12.9],[-74.9,-12.9],[-74.9,-13.6],[-75.5,-13.6],[-75.5,-12.9]]]}},
            {"type":"Feature","id":"CHURCAMPA","properties":{"NOMBPROV":"CHURCAMPA"},"geometry":{"type":"Polygon","coordinates":[[[-74.5,-12.3],[-74.1,-12.3],[-74.1,-12.7],[-74.5,-12.7],[-74.5,-12.3]]]}},
            {"type":"Feature","id":"HUANCAVELICA","properties":{"NOMBPROV":"HUANCAVELICA"},"geometry":{"type":"Polygon","coordinates":[[[-75.3,-12.4],[-74.7,-12.4],[-74.7,-12.9],[-75.3,-12.9],[-75.3,-12.4]]]}},
            {"type":"Feature","id":"HUAYTARA","properties":{"NOMBPROV":"HUAYTARA"},"geometry":{"type":"Polygon","coordinates":[[[-75.5,-13.5],[-74.9,-13.5],[-74.9,-14.2],[-75.5,-14.2],[-75.5,-13.5]]]}},
            {"type":"Feature","id":"TAYACAJA","properties":{"NOMBPROV":"TAYACAJA"},"geometry":{"type":"Polygon","coordinates":[[[-74.7,-11.9],[-74.1,-11.9],[-74.1,-12.4],[-74.7,-12.4],[-74.7,-11.9]]]}}
          ]
        }
        with open(OUT, 'w', encoding='utf-8') as fp:
            json.dump(fallback, fp)
        print("GeoJSON de respaldo guardado.")

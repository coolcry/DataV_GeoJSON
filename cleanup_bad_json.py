import json
from pathlib import Path


ROOTS = (Path('geojson'), Path('geojson_full'))
VALID_TYPES = ('FeatureCollection', 'Feature', 'GeometryCollection')


def is_valid_geojson(path):
    try:
        with path.open(encoding='utf-8') as f:
            data = json.load(f)
    except Exception:
        return False

    return isinstance(data, dict) and data.get('type') in VALID_TYPES


def main():
    removed = 0
    for root in ROOTS:
        for path in root.rglob('*.json'):
            if is_valid_geojson(path):
                continue
            path.unlink()
            removed += 1
            print(f"removed {path}")

    print(f"removed_count={removed}")


if __name__ == '__main__':
    main()

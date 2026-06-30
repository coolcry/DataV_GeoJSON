import re
import requests
from bs4 import BeautifulStoneSoup as bs
import json
import os
import time
import geopandas

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
REQUEST_DELAY = 0.4
MAX_RETRIES = 5


def getLevel(code):
    if (code == '100000'):
        return ''
    elif (code[-4:] == '0000'):
        return 'province'
    elif (code[-2:] == '00'):
        return 'city'
    else:
        return 'county'


def get_save_path(areaCode, level, full=False):
    suffix = '_full.json' if full else '.json'
    if (level == ''):
        return os.path.join(BASE_DIR, 'geojson_full' if full else 'geojson', areaCode + suffix)
    elif(level == 'province'):
        return os.path.join(BASE_DIR, 'geojson_full' if full else 'geojson', 'province', areaCode + suffix)
    elif (level == 'city'):
        return os.path.join(BASE_DIR, 'geojson_full' if full else 'geojson', 'city', areaCode + suffix)
    else:
        return os.path.join(BASE_DIR, 'geojson_full' if full else 'geojson', 'county', areaCode + suffix)


def save_text(areaCode, level, content, full=False):
    path = get_save_path(areaCode, level, full)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)


def log_failed(areaCode, full, reason):
    with open(os.path.join(BASE_DIR, 'log.txt'), 'a', encoding='utf-8') as f:
        f.write(f"{areaCode},{'full' if full else 'normal'},{reason}\n")


def is_valid_geojson(content):
    try:
        data = json.loads(content)
    except json.JSONDecodeError:
        return False
    return data.get('type') in ('FeatureCollection', 'Feature', 'GeometryCollection')


def remove_invalid_file(areaCode, full=False):
    path = get_save_path(str(areaCode), getLevel(str(areaCode)), full)
    if not os.path.exists(path):
        return

    with open(path, encoding='utf-8') as f:
        content = f.read()
    if not is_valid_geojson(content):
        os.remove(path)
        print(f"removed invalid file: {path}")


def has_valid_file(areaCode, full=False):
    path = get_save_path(str(areaCode), getLevel(str(areaCode)), full)
    if not os.path.exists(path):
        return False

    with open(path, encoding='utf-8') as f:
        return is_valid_geojson(f.read())


def getJson(areaCode, full=False, retries=MAX_RETRIES, delay=REQUEST_DELAY):
    if (full and getLevel(areaCode) == 'county'):
        return False
    if has_valid_file(areaCode, full):
        print(f"skip {areaCode} ({'full' if full else 'normal'}): exists")
        return False
    url = 'https://geo.datav.aliyun.com/areas_v2/bound/' + \
        str(areaCode) + ('_full.json' if full else '.json')
    headers = {
        'Accept': 'application/json, text/javascript, */*; q=0.01',
        'Origin': 'http://datav.aliyun.com',
        'Referer': 'http://datav.aliyun.com/tools/atlas/',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/75.0.3770.142 Safari/537.36'
    }
    print("areaCode："+str(areaCode))
    for attempt in range(retries + 1):
        try:
            r = requests.get(url=url, headers=headers, timeout=30)
            mapJson = r.text

            if r.status_code == 200 and 'Error' not in mapJson and is_valid_geojson(mapJson):
                save_text(str(areaCode), getLevel(areaCode), mapJson, full)
                return True

            reason = f"status={r.status_code}"
            if r.status_code == 403 or 'rate limit' in mapJson.lower():
                reason = 'rate limit'
        except Exception as e:
            reason = repr(e)

        if attempt < retries:
            sleep_seconds = delay * (2 ** attempt)
            print(f"retry {areaCode} ({'full' if full else 'normal'}): {reason}, sleep {sleep_seconds:.1f}s")
            time.sleep(sleep_seconds)
        else:
            print(f"failed {areaCode} ({'full' if full else 'normal'}): {reason}")
            remove_invalid_file(areaCode, full)
            log_failed(areaCode, full, reason)
            return True


def saveShapefile(code, full=False):
    level = getLevel(code)
    try:
        data = geopandas.read_file(
            'shp_full' if full else 'shp'+'map/city/' + str(code) + '.json')
        localPath = 'map/shp/'  # 用于存放生成的文件
        data.to_file(localPath+str(code)+".shp",
                     driver='ESRI Shapefile', encoding='utf-8')
        print("--保存成功，文件存放位置："+localPath)
    except Exception:
        print("--------JSON文件不存在，请检查后重试！----")
        pass


def getAllCodes():
    f = open(os.path.join(BASE_DIR, "code/location.txt"),
             encoding='UTF-8')               # 返回一个文件对象
    line = f.readline()  # 调用文件的 readline()方法
    ls = []
    while line:
        arr = line.split(',')
        ls.append(arr[0])
        line = f.readline()
    f.close()
    return ls


if __name__ == '__main__':
    getJson('100000', False)
    getJson('100000', True)

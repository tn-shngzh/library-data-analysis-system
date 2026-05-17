import urllib.request
import json

base_url = "http://localhost:8000"

print("=" * 70)
print("清除缓存并重启后端")
print("=" * 70)

# 清除缓存
cache_endpoints = [
    "/api/cache/clear",
]

for endpoint in cache_endpoints:
    url = base_url + endpoint
    try:
        req = urllib.request.Request(url, method='DELETE')
        with urllib.request.urlopen(req, timeout=10) as response:
            print(f"{endpoint}: {response.status} - OK")
    except Exception as e:
        print(f"{endpoint}: {e}")

print("\n✅ 缓存清除完成")
print("请重启后端服务以应用最新数据")

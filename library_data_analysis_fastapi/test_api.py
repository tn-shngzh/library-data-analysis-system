import urllib.request
import json

base_url = "http://localhost:8000"

endpoints = [
    "/api/overview/stats",
    "/api/borrows/stats",
    "/api/readers/stats",
]

print("=" * 70)
print("验证 API 接口")
print("=" * 70)

for endpoint in endpoints:
    url = base_url + endpoint
    print(f"\n--- {endpoint} ---")
    try:
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req, timeout=10) as response:
            data = json.loads(response.read().decode())
            print(f"状态: {response.status}")
            print(f"数据: {json.dumps(data, indent=2, ensure_ascii=False)[:500]}")
    except Exception as e:
        print(f"❌ 错误: {e}")

print("\n✅ API 验证完成")

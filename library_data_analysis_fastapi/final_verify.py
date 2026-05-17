import urllib.request
import json

base_url = "http://localhost:8000"

endpoints = [
    "/api/overview/stats",
    "/api/borrows/stats",
    "/api/readers/stats",
    "/api/borrows/action-stats",
    "/api/borrows/monthly-trend",
]

print("=" * 70)
print("最终验证 API 接口数据")
print("=" * 70)

for endpoint in endpoints:
    url = base_url + endpoint
    print(f"\n{'='*60}")
    print(f"端点: {endpoint}")
    print(f"{'='*60}")
    try:
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req, timeout=10) as response:
            data = json.loads(response.read().decode())
            print(f"✅ 状态: {response.status}")
            # 打印关键字段
            if isinstance(data, dict):
                for key in list(data.keys())[:10]:
                    val = data[key]
                    if isinstance(val, (int, float)):
                        print(f"  {key}: {val:,}")
                    else:
                        print(f"  {key}: {val}")
    except Exception as e:
        print(f"❌ 错误: {e}")

print("\n" + "=" * 70)
print("✅ 验证完成")
print("=" * 70)

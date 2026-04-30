import requests
import time

print("=" * 60)
print("系统连接诊断测试")
print("=" * 60)

# Test 1: Frontend
print("\n1. 测试前端服务器...")
try:
    r = requests.get('http://localhost:5174', timeout=3)
    print(f"   ✅ 前端正常运行 (状态码: {r.status_code})")
except Exception as e:
    print(f"   ❌ 前端无法访问: {e}")

# Test 2: Backend
print("\n2. 测试后端服务器...")
try:
    r = requests.get('http://localhost:8000/docs', timeout=3)
    print(f"   ✅ 后端正常运行 (状态码: {r.status_code})")
except Exception as e:
    print(f"   ❌ 后端无法访问: {e}")

# Test 3: Captcha API
print("\n3. 测试验证码API...")
try:
    r = requests.get('http://localhost:8000/api/captcha', timeout=3)
    if r.status_code == 200:
        data = r.json()
        print(f"   ✅ 验证码API正常")
        print(f"   - Key: {data['key'][:30]}...")
        print(f"   - Image length: {len(data['image'])} chars")
    else:
        print(f"   ❌ 验证码API返回错误: {r.status_code}")
except Exception as e:
    print(f"   ❌ 验证码API失败: {e}")

# Test 4: Login API with wrong captcha (should return 400)
print("\n4. 测试登录API连通性...")
try:
    # First get a fresh captcha
    r1 = requests.get('http://localhost:8000/api/captcha', timeout=3)
    captcha_key = r1.json()['key']
    
    # Try login with wrong captcha
    formData = {
        'username': 'user',
        'password': 'user123',
        'captcha': 'WRONG',
        'captcha_key': captcha_key
    }
    r2 = requests.post('http://localhost:8000/api/login', data=formData, timeout=3)
    
    if r2.status_code == 400:
        print(f"   ✅ 登录API可达 (预期返回400)")
        print(f"   - 响应: {r2.json()['detail']}")
    elif r2.status_code == 200:
        print(f"   ✅ 登录API可达，登录成功!")
        print(f"   - Token: {r2.json()['access_token'][:30]}...")
        print(f"   - Role: {r2.json()['role']}")
        print(f"   - System: {r2.json()['system']}")
    else:
        print(f"   ❌ 登录API返回意外状态码: {r2.status_code}")
        print(f"   - 响应: {r2.text}")
except Exception as e:
    print(f"   ❌ 登录API调用失败: {e}")

# Test 5: Check if user account exists
print("\n5. 检查用户账户...")
try:
    import psycopg2
    conn = psycopg2.connect(
        host='localhost',
        port='5432',
        dbname='library_db',
        user='postgres',
        password='GXYL2405'
    )
    cur = conn.cursor()
    cur.execute("SELECT id, username, role FROM users WHERE username = 'user'")
    user = cur.fetchone()
    if user:
        print(f"   ✅ 用户 'user' 存在")
        print(f"   - ID: {user[0]}")
        print(f"   - Username: {user[1]}")
        print(f"   - Role: {user[2]}")
    else:
        print(f"   ⚠️  用户 'user' 不存在")
        print(f"   - 需要创建测试用户")
    cur.close()
    conn.close()
except Exception as e:
    print(f"   ❌ 数据库检查失败: {e}")

print("\n" + "=" * 60)
print("诊断完成!")
print("=" * 60)

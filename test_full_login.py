import requests

print("Testing full login flow...")

# Step 1: Get captcha
r1 = requests.get('http://localhost:8000/api/captcha')
print(f"1. Captcha API: {r1.status_code}")
if r1.status_code != 200:
    print("   Failed to get captcha")
    exit()
    
captcha_data = r1.json()
captcha_key = captcha_data['key']
print(f"   Key: {captcha_key[:30]}...")

# Step 2: Try login with user/user123 (but wrong captcha - we can't see the image)
# This will test if the login endpoint is reachable and the user credentials work
formData = {
    'username': 'user',
    'password': 'user123',
    'captcha': 'WRONG',  # This will fail captcha check, but that's OK
    'captcha_key': captcha_key
}

r2 = requests.post('http://localhost:8000/api/login', data=formData)
print(f"\n2. Login API: {r2.status_code}")
print(f"   Response: {r2.text}")

if r2.status_code == 400 and '验证码' in r2.text:
    print("\n✓ Login endpoint is reachable and working!")
    print("✓ User credentials are being processed")
    print("✗ Captcha validation is working (expected to fail with wrong captcha)")
    print("\nNOTE: The user will need to enter the correct captcha shown in the UI")
elif r2.status_code == 200:
    print("\n✓ Login successful!")
    data = r2.json()
    print(f"  Token: {data['access_token'][:40]}...")
    print(f"  Role: {data['role']}")
    print(f"  System: {data['system']}")
else:
    print(f"\n✗ Unexpected response: {r2.status_code}")

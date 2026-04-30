import requests

# Step 1: Get captcha
r1 = requests.get('http://localhost:8000/api/captcha')
print(f"Step 1: Get captcha - Status: {r1.status_code}")
if r1.status_code != 200:
    print(f"Error: {r1.text}")
    exit()
captcha_data = r1.json()
captcha_key = captcha_data['key']
print(f"  Captcha key: {captcha_key[:20]}...")

# Step 2: Try login (will fail due to wrong captcha, but that's ok)
formData = {
    'username': 'user',
    'password': 'user123',
    'captcha': 'WRONG',
    'captcha_key': captcha_key
}

r2 = requests.post('http://localhost:8000/api/login', data=formData)
print(f"Step 2: Login attempt - Status: {r2.status_code}")
print(f"  Response: {r2.text}")

# Step 3: Get a new captcha and try with correct credentials (if we know the code)
# We can't actually see the captcha code from the API, so this will fail on captcha
# but at least we can verify the endpoint is reachable

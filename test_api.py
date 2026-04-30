import requests

base_url = 'http://localhost:8000'

endpoints = [
    '/api/borrows/stats',
    '/api/books/hot',
    '/api/borrows/recent',
    '/api/books/categories'
]

for endpoint in endpoints:
    try:
        r = requests.get(f'{base_url}{endpoint}', timeout=5)
        print(f'{endpoint}: {r.status_code}')
        if r.status_code != 200:
            print(f'  Error: {r.text}')
    except Exception as e:
        print(f'{endpoint}: FAILED - {str(e)}')

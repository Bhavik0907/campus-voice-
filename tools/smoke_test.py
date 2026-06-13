import urllib.request
urls = ['http://127.0.0.1:5000/', 'http://127.0.0.1:5000/login', 'http://127.0.0.1:5000/register']
for u in urls:
    try:
        with urllib.request.urlopen(u, timeout=5) as r:
            data = r.read()
            print(u, r.status, len(data))
    except Exception as e:
        print(u, 'ERROR', e)

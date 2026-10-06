import os, urllib.request, json

token = os.environ.get('GITHUB_TOKEN')
env_file = os.path.expanduser('~/.env')
if not token and os.path.exists(env_file):
    with open(env_file) as f:
        for line in f:
            if line.startswith('GITHUB_TOKEN='):
                token = line.strip().split('=', 1)[1].strip('"\'')

if token:
    # 1. Update repo visibility to public for GitHub Pages if needed
    try:
        url = 'https://api.github.com/repos/pixelwizards72-star/kibotube'
        req = urllib.request.Request(url, data=json.dumps({'private': False}).encode(), headers={'Authorization': f'token {token}', 'Accept': 'application/vnd.github.v3+json', 'Content-Type': 'application/json'}, method='PATCH')
        res = urllib.request.urlopen(req)
        print("Updated repository visibility to Public.")
    except Exception as e:
        print("Repo visibility update:", e)

    # 2. Enable GitHub Pages
    try:
        url = 'https://api.github.com/repos/pixelwizards72-star/kibotube/pages'
        req = urllib.request.Request(url, data=json.dumps({'source': {'branch': 'main', 'path': '/'}}).encode(), headers={'Authorization': f'token {token}', 'Accept': 'application/vnd.github.v3+json', 'Content-Type': 'application/json'}, method='POST')
        res = urllib.request.urlopen(req)
        print("GitHub Pages enabled successfully!")
        data = json.loads(res.read().decode())
        print("Pages URL:", data.get('html_url'))
    except Exception as e:
        print("GitHub Pages enable response:", e)

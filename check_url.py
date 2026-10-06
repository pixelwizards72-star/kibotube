import urllib.request
try:
    res = urllib.request.urlopen('https://pixelwizards72-star.github.io/kibotube/')
    print("STATUS:", res.status)
    print("SUCCESSFULLY LIVE!")
except Exception as e:
    print("ERROR:", e)

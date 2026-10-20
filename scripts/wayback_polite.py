"""Consultas Wayback con pausa fija; aborta ante 429 (no reintenta)."""
import sys, time, urllib.request, urllib.error
UA = "Mozilla/5.0 (X11; Linux x86_64) Chrome/124.0 (uso academico; consultas puntuales)"
PAUSA = 15  # s entre peticiones (~4/min)
def get(url, out=None):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    try:
        with urllib.request.urlopen(req, timeout=90) as r:
            data = r.read(); print(r.status, r.geturl(), len(data), file=sys.stderr)
    except urllib.error.HTTPError as e:
        print("HTTP", e.code, "Retry-After:", e.headers.get("Retry-After"), url, file=sys.stderr)
        if e.code == 429: sys.exit(42)
        data = b""
    if out: open(out, "wb").write(data)
    time.sleep(PAUSA)
    return data
if __name__ == "__main__":
    get(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else None)

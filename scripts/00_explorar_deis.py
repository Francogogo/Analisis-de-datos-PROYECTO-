import sys, re
from playwright.sync_api import sync_playwright
url = sys.argv[1] if len(sys.argv) > 1 else "https://deis.minsal.cl/"
pat = sys.argv[2] if len(sys.argv) > 2 else r"egres|grd|hospital|dataset|datos|repositorio|\.(zip|csv|rar)"
with sync_playwright() as p:
    b = p.chromium.launch(); pg = b.new_page()
    r = pg.goto(url, wait_until="networkidle", timeout=60000)
    pg.wait_for_timeout(3000)
    print(r.status, pg.url, pg.title())
    for a in pg.eval_on_selector_all("a", "e=>e.map(x=>[x.innerText.trim().slice(0,70),x.href])"):
        if re.search(pat, a[0]+a[1], re.I): print(a)
    b.close()

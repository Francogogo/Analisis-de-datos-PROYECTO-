"""Una visita a una URL archivada; lista enlaces. Una sola pagina por ejecucion."""
import sys, re
from playwright.sync_api import sync_playwright
url = sys.argv[1]; pat = sys.argv[2] if len(sys.argv) > 2 else r"grd|egreso|base|hospital|\.(zip|csv|rar|xlsx?)|descarg|assets|tableau|powerbi"
with sync_playwright() as p:
    b = p.chromium.launch(); pg = b.new_page()
    r = pg.goto(url, wait_until="load", timeout=90000)
    pg.wait_for_timeout(5000)
    print(r.status if r else None, pg.url, pg.title())
    for a in pg.eval_on_selector_all("a", "e=>e.map(x=>[x.innerText.trim().replace(/\\s+/g,' ').slice(0,60),x.href])"):
        if re.search(pat, a[0]+a[1], re.I) and "web-static" not in a[1]: print(a)
    b.close()

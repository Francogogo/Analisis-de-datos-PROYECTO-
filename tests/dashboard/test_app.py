import re
import shutil
import socket
import subprocess
import sys
import time
from pathlib import Path

import httpx
import pytest

RAIZ = Path(__file__).parents[2]
sys.path.insert(0, str(RAIZ / "dashboard"))

import datos  # noqa: E402
import modelo  # noqa: E402
import p_whatif  # noqa: E402
import resumen  # noqa: E402

ORDEN = ["Contexto", "Exploración", "Relaciones", "Diagnósticos", "Modelos", "What if", "Conclusiones"]


def test_app_importa():
    import app

    html = str(app.app_ui)
    assert [t for t, _, _ in app.PESTANAS] == ORDEN
    assert "Estadías hospitalarias FONASA 2020" in html
    assert len(re.findall(r'data-bs-toggle="tab"|data-toggle="tab"', html)) == 7 or html.count("nav-link") >= 7
    pos = [html.index(f">{t}<") for t in ORDEN if f">{t}<" in html]
    assert pos == sorted(pos) and len(pos) == 7
    assert "MathJax" in html


def test_sin_filtro_calza_paper():
    d = datos.cargar()
    r = resumen.descriptivos(resumen.filtrar(d.base, {k: [] for k in ("sexo", "region")}))
    assert r["n"] == 968098
    assert abs(r["pct_prolongadas"] - 9.39) < 1e-2
    assert abs(r["pct_dias_cama_prolongadas"] - 47.07) < 1e-2


def test_whatif_real():
    m = datos.cargar().m3
    ref = p_whatif.perfil_ref(m)
    dias = modelo.dias_estimados(ref, m)[0]
    snss = modelo.dias_estimados({**ref, "establecimiento": "SNSS"}, m)[0]
    assert f"{dias:.2f}" == "1.82"
    assert abs((snss / dias - 1) * 100 - 70.0) < 0.05


def test_arranca():
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        puerto = s.getsockname()[1]
    p = subprocess.Popen([sys.executable, "-m", "shiny", "run", str(RAIZ / "dashboard" / "app.py"),
                          "--port", str(puerto)], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    try:
        fin = time.time() + 60
        codigo = None
        while time.time() < fin and codigo is None:
            try:
                codigo = httpx.get(f"http://127.0.0.1:{puerto}", timeout=2).status_code
            except httpx.HTTPError:
                time.sleep(1)
        assert codigo == 200
    finally:
        p.terminate()
        p.wait(timeout=15)


def test_mathjax_local():
    from starlette.testclient import TestClient

    import app

    c = TestClient(app.app)
    pagina = c.get("/").text
    assert not re.search(r'src="https?://', pagina) and re.search(r'src="mathjax/tex-svg\.js\?v=\w+"', pagina)
    r = c.get("/mathjax/tex-svg.js")
    assert r.status_code == 200 and len(r.content) > 1_000_000


def test_fuentes_locales():
    from starlette.testclient import TestClient
    import app

    c = TestClient(app.app)
    for fuente in ("Figtree-variable.woff2", "BricolageGrotesque-variable.woff2"):
        r = c.get(f"/fonts/{fuente}")
        assert r.status_code == 200 and len(r.content) > 20_000


def test_menu_movil():
    playwright = pytest.importorskip("playwright.sync_api")
    chromium = shutil.which("chromium") or shutil.which("google-chrome")
    if not chromium:
        pytest.skip("Navegador Chromium no disponible")
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        puerto = s.getsockname()[1]
    p = subprocess.Popen([sys.executable, "-m", "shiny", "run", str(RAIZ / "dashboard" / "app.py"),
                          "--port", str(puerto)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    try:
        fin = time.time() + 60
        while True:
            try:
                httpx.get(f"http://127.0.0.1:{puerto}", timeout=2).raise_for_status()
                break
            except httpx.HTTPError:
                if time.time() >= fin:
                    raise
                time.sleep(0.5)
        with playwright.sync_playwright() as pw:
            browser = pw.chromium.launch(headless=True, executable_path=chromium, args=["--no-sandbox"])
            try:
                page = browser.new_page(viewport={"width": 390, "height": 844})
                page.goto(f"http://127.0.0.1:{puerto}", wait_until="networkidle")
                boton = page.locator(".navbar-toggler")
                boton.click()
                page.get_by_role("tab", name="Exploración").click()
                page.wait_for_function("document.querySelector('.navbar-toggler').getAttribute('aria-expanded') === 'false'")
                assert page.get_by_role("tab", name="Exploración").get_attribute("aria-selected") == "true"
                assert boton.evaluate("el => document.activeElement === el")
                page.wait_for_function("document.querySelector('.navbar-collapse').classList.contains('collapse')")
                page.keyboard.press("Enter")
                page.get_by_role("tab", name="Contexto").focus()
                page.keyboard.press("Enter")
                page.wait_for_function("document.querySelector('.navbar-toggler').getAttribute('aria-expanded') === 'false'")
                assert page.get_by_role("tab", name="Contexto").get_attribute("aria-selected") == "true"
                assert boton.evaluate("el => document.activeElement === el")
            finally:
                browser.close()
    finally:
        p.terminate()
        p.wait(timeout=15)

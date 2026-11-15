"""Prueba de interacción real: etiquetas visibles y valores analíticos intactos."""
import shutil
import socket
import subprocess
import sys
import time
from pathlib import Path

import httpx
import pytest

import datos
import graficos
import modelo
import p_whatif

RAIZ = Path(__file__).resolve().parents[2]


def test_capitulo_y_establecimiento_en_navegador():
    playwright = pytest.importorskip("playwright.sync_api")
    chromium = shutil.which("chromium") or shutil.which("google-chrome")
    if not chromium:
        pytest.skip("Navegador Chromium no disponible")
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        puerto = s.getsockname()[1]
    server = subprocess.Popen([sys.executable, "-m", "shiny", "run", str(RAIZ / "dashboard" / "app.py"),
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
        d = datos.cargar()
        with playwright.sync_playwright() as pw:
            browser = pw.chromium.launch(headless=True, executable_path=chromium, args=["--no-sandbox"])
            try:
                page = browser.new_page(viewport={"width": 1440, "height": 900})
                page.goto(f"http://127.0.0.1:{puerto}", wait_until="networkidle", timeout=60000)
                page.get_by_role("tab", name="Exploración").click()
                for campo, valor, texto in (("capitulo", "F00-F99", "Trastornos mentales"),
                                            ("establecimiento", "SNSS", "Red de servicios")):
                    entrada = page.locator(f"#exploracion-{campo} + .selectize-control input")
                    entrada.fill(valor)
                    opcion = page.locator(f'.selectize-dropdown [data-value="{valor}"]')
                    opcion.wait_for(state="visible")
                    assert texto in opcion.inner_text()
                    opcion.click()
                    assert page.locator(f"#exploracion-{campo}").input_value() == valor
                esperado = graficos.num(int(((d.base.capitulo == "F00-F99") &
                                             (d.base.establecimiento == "SNSS")).sum()), 0)
                page.wait_for_function("v => document.querySelector('#exploracion-caja0_v').innerText.trim() === v",
                                       arg=esperado, timeout=30000)
                page.get_by_role("tab", name="What if").click()
                for campo, valor, texto in (("capitulo", "F00-F99", "Trastornos mentales"),
                                            ("establecimiento", "SNSS", "Red de servicios")):
                    select = page.locator(f"#whatif-{campo}")
                    opcion = select.locator(f'option[value="{valor}"]')
                    opcion.wait_for(state="attached")
                    assert texto in opcion.inner_text()
                    select.select_option(valor)
                    assert select.input_value() == valor
                perfil = {**p_whatif.perfil_ref(d.m3), "capitulo": "F00-F99", "establecimiento": "SNSS"}
                esperado = graficos.num(modelo.dias_estimados(perfil, d.m3)[0], 2)
                page.wait_for_function("v => document.querySelector('#whatif-resultado .whatif-cifra strong')?.textContent.includes(v)",
                                       arg=esperado, timeout=30000)
                assert "Trastornos mentales" in page.locator("#whatif-detalle_capitulo").inner_text()
                page.locator("#whatif-variable").select_option("capitulo")
                page.wait_for_function("document.querySelector('#whatif-graf_niveles').clientHeight > 600")
                page.locator("#whatif-ayuda_capitulos summary").click()
                assert "Trastornos mentales" in page.locator("#whatif-ayuda_capitulos").inner_text()
                page.set_viewport_size({"width": 390, "height": 844})
                assert page.locator("#whatif-graf_niveles").bounding_box()["height"] > 600
                page.locator("#whatif-variable").select_option("establecimiento")
                page.wait_for_function("document.querySelector('#whatif-graf_niveles').clientHeight == 400")
            finally:
                browser.close()
    finally:
        server.terminate()
        server.wait(timeout=15)

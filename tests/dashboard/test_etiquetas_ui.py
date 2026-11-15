"""El texto descriptivo no cambia el valor que reciben los filtros ni el modelo."""
import shutil
import socket
import subprocess
import sys
import time
from pathlib import Path

import httpx
import pytest


def test_etiquetas_en_selectores_y_calculos():
    playwright = pytest.importorskip("playwright.sync_api")
    chromium = shutil.which("chromium") or shutil.which("google-chrome")
    if not chromium:
        pytest.skip("Navegador Chromium no disponible")
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        puerto = sock.getsockname()[1]
    app = Path(__file__).parents[2] / "dashboard" / "app.py"
    proceso = subprocess.Popen([sys.executable, "-m", "shiny", "run", str(app), "--port", str(puerto)],
                               stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    try:
        limite = time.time() + 60
        while True:
            try:
                httpx.get(f"http://127.0.0.1:{puerto}", timeout=2).raise_for_status()
                break
            except httpx.HTTPError:
                if time.time() >= limite:
                    raise
                time.sleep(0.5)
        with playwright.sync_playwright() as pw:
            navegador = pw.chromium.launch(headless=True, executable_path=chromium, args=["--no-sandbox"])
            try:
                pagina = navegador.new_page()
                pagina.goto(f"http://127.0.0.1:{puerto}", wait_until="networkidle")
                pagina.get_by_role("tab", name="Exploración").click()
                pagina.wait_for_function("document.querySelector('#exploracion-caja0_v').textContent.trim() === '968.098'")
                opcion = pagina.evaluate("$('#exploracion-capitulo')[0].selectize.options['F00-F99']")
                assert opcion["value"] == "F00-F99" and "Trastornos mentales" in opcion["label"]
                pagina.evaluate("$('#exploracion-capitulo')[0].selectize.addItem('F00-F99')")
                pagina.wait_for_function("document.querySelector('#exploracion-caja0_v').textContent.trim() === '19.808'")
                pagina.get_by_role("tab", name="What if").click()
                pagina.wait_for_function("document.querySelector('#whatif-capitulo').options.length > 10")
                assert pagina.locator('#whatif-capitulo').input_value() == 'K00-K93'
                assert 'digestivo' in pagina.locator('#whatif-capitulo option:checked').inner_text()
                pagina.select_option('#whatif-capitulo', 'F00-F99')
                pagina.wait_for_function("document.querySelector('#whatif-resultado').textContent.includes('5,74 días')")
                assert "Trastornos mentales" in pagina.locator('#whatif-detalle_capitulo').inner_text()
                pagina.select_option('#whatif-variable', 'capitulo')
                pagina.wait_for_function("document.querySelector('#whatif-graf_niveles').getBoundingClientRect().height >= 666")
                pagina.get_by_text("Ver nombres de los capítulos CIE-10").click()
                assert "F00-F99 — Trastornos mentales" in pagina.locator('#whatif-ayuda_capitulos').inner_text()
                pagina.select_option('#whatif-variable', 'establecimiento')
                pagina.wait_for_function("document.querySelector('#whatif-graf_niveles').getBoundingClientRect().height == 400")
            finally:
                navegador.close()
    finally:
        proceso.terminate()
        proceso.wait(timeout=15)

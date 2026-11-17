"""shinyapps.io lee event["more_body"] en cada cuerpo de respuesta; la app debe mandarlo siempre."""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "dashboard"))
import app as modulo  # noqa: E402


def _pedir(ruta, query=b"", gzip=False):
    cuerpos = []

    pedidos = [{"type": "http.request", "body": b"", "more_body": False}]

    async def recibir():
        if pedidos:
            return pedidos.pop()
        await asyncio.Event().wait()  # el cliente no se desconecta

    async def enviar(msg):
        if msg["type"] == "http.response.body":
            msg["more_body"]  # igual que shiny_support.injector_send: KeyError si falta
            cuerpos.append(msg)

    headers = [(b"host", b"localhost")] + ([(b"accept-encoding", b"gzip")] if gzip else [])
    scope = {"type": "http", "asgi": {"version": "3.0"}, "http_version": "1.1", "method": "GET",
             "scheme": "http", "path": ruta, "raw_path": ruta.encode(), "query_string": query,
             "root_path": "", "headers": headers, "client": ("127.0.0.1", 1), "server": ("localhost", 80)}
    asyncio.run(modulo.app(scope, recibir, enviar))
    return cuerpos


def test_more_body_en_todas_las_respuestas():
    for gzip in (False, True):
        assert _pedir("/", gzip=gzip)
        assert _pedir("/css/clinica.css", gzip=gzip)
        assert _pedir("/no-existe", gzip=gzip)

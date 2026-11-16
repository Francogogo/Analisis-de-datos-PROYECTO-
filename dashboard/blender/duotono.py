"""Pasada de 'shader' pre-renderizada: duotono marino -> cobalto -> hielo según luminancia, grano fino
y oscurecido hacia la izquierda para que el texto blanco de la cabecera tenga contraste."""
import json, shutil, sys
import numpy as np
from PIL import Image
src, dst = sys.argv[1], sys.argv[2]
def hexa(h): return np.array([int(h[i:i + 2], 16) for i in (1, 3, 5)], dtype=np.float32)
PARADAS = [(0.0, hexa("#071a33")), (0.45, hexa("#163a9e")), (0.78, hexa("#5d8cf0")), (1.0, hexa("#e6eefd"))]
for k in json.load(open(f"{src}/creditos.json")):
    im = Image.open(f"{src}/{k}.jpg").convert("RGB")
    w = 1800; im = im.resize((w, round(im.height * w / im.width)), Image.LANCZOS)
    alto = 640; top = max(0, (im.height - alto) // 2); im = im.crop((0, top, w, top + min(alto, im.height)))
    a = np.asarray(im, dtype=np.float32) / 255
    L = 0.2126 * a[..., 0] + 0.7152 * a[..., 1] + 0.0722 * a[..., 2]
    L = np.clip((L - np.percentile(L, 2)) / (np.percentile(L, 98) - np.percentile(L, 2) + 1e-6), 0, 1)
    out = np.zeros(a.shape, np.float32)
    for (t0, c0), (t1, c1) in zip(PARADAS, PARADAS[1:]):
        m = (L >= t0) & (L <= t1); u = ((L - t0) / (t1 - t0))[..., None]
        out[m] = (c0 + (c1 - c0) * u)[m]
    x = np.linspace(0, 1, out.shape[1])[None, :, None]
    sombra = 0.18 + 0.82 * np.clip((x - 0.05) / 0.6, 0, 1) ** 1.4   # izquierda oscura para el texto
    out = out * sombra + hexa("#071a33") * (1 - sombra)
    rng = np.random.default_rng(3); out += rng.normal(0, 3.2, out.shape[:2])[..., None]
    Image.fromarray(np.clip(out, 0, 255).astype(np.uint8)).save(f"{dst}/{k}.webp", quality=78, method=6)
    print(k, out.shape)
shutil.copy(f"{src}/creditos.json", f"{dst}/creditos.json")

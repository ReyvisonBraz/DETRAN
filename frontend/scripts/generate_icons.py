"""Gera os icones PWA (PNG) sem dependencias externas.

Desenha uma lupa branca sobre fundo azul (tema "consulta"). Pure-python:
constroi o PNG via zlib, sem Pillow.
"""

import os
import struct
import zlib
import math

OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "public")
BG = (37, 99, 235)        # azul --primary
FG = (255, 255, 255)      # branco


def _png(width: int, height: int, pixels: bytes) -> bytes:
    def chunk(tag, data):
        c = tag + data
        return struct.pack(">I", len(data)) + c + struct.pack(">I", zlib.crc32(c) & 0xFFFFFFFF)

    sig = b"\x89PNG\r\n\x1a\n"
    ihdr = struct.pack(">IIBBBBB", width, height, 8, 6, 0, 0, 0)  # 8-bit RGBA
    raw = bytearray()
    stride = width * 4
    for y in range(height):
        raw.append(0)  # filtro None
        raw.extend(pixels[y * stride:(y + 1) * stride])
    idat = zlib.compress(bytes(raw), 9)
    return sig + chunk(b"IHDR", ihdr) + chunk(b"IDAT", idat) + chunk(b"IEND", b"")


def render(size: int) -> bytes:
    px = bytearray(size * size * 4)
    # Lupa: anel + cabo, dentro da zona segura (maskable)
    cx, cy = size * 0.43, size * 0.43
    R = size * 0.24       # raio externo do anel
    r = size * 0.155      # raio interno
    pen = size * 0.085    # espessura do cabo
    # cabo: do ponto na borda inferior-direita do anel ate baixo-direita
    hx1, hy1 = cx + R * 0.62, cy + R * 0.62
    hx2, hy2 = cx + R * 1.45, cy + R * 1.45

    def dist_seg(x, y, x1, y1, x2, y2):
        dx, dy = x2 - x1, y2 - y1
        l2 = dx * dx + dy * dy
        t = max(0.0, min(1.0, ((x - x1) * dx + (y - y1) * dy) / l2)) if l2 else 0.0
        return math.hypot(x - (x1 + t * dx), y - (y1 + t * dy))

    for y in range(size):
        for x in range(size):
            d = math.hypot(x - cx, y - cy)
            white = (r < d < R) or (dist_seg(x, y, hx1, hy1, hx2, hy2) < pen / 2)
            col = FG if white else BG
            i = (y * size + x) * 4
            px[i], px[i + 1], px[i + 2], px[i + 3] = col[0], col[1], col[2], 255
    return _png(size, size, bytes(px))


os.makedirs(OUT, exist_ok=True)
for s in (192, 512):
    with open(os.path.join(OUT, f"icon-{s}.png"), "wb") as f:
        f.write(render(s))
    print(f"icon-{s}.png gerado")

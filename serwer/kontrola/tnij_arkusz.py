"""Tnie arkusz 3x3 (rzeczy na jednolitym ciemnym tle) na osobne pliki WebP z przezroczystym tłem, przycięte jak img/wzorce."""
import sys, json, os
import numpy as np
from PIL import Image
from scipy import ndimage

def tnij(sciezka, pliki, katalog, maks=420, siatka=None):
    im = Image.open(sciezka).convert('RGB'); a = np.asarray(im).astype(np.float32)
    H, W = a.shape[:2]
    # tło: mediana pikseli z ramki 8 px
    ramka = np.concatenate([a[:8].reshape(-1, 3), a[-8:].reshape(-1, 3), a[:, :8].reshape(-1, 3), a[:, -8:].reshape(-1, 3)])
    tlo = np.median(ramka, axis=0)
    odl = np.sqrt(((a - tlo) ** 2).sum(2))
    maska = odl > 10
    maska = ndimage.binary_closing(maska, iterations=3)
    maska = ndimage.binary_fill_holes(maska)
    etyk, n = ndimage.label(maska)
    rozm = ndimage.sum(maska, etyk, range(1, n + 1))
    srodki = ndimage.center_of_mass(maska, etyk, range(1, n + 1))
    wi, ko = siatka or ((2, 2) if len(pliki) == 4 else (3, 3))  # wiersze, kolumny
    komorki = {i: [] for i in range(wi * ko)}
    for k, (s, (cy, cx)) in enumerate(zip(rozm, srodki), start=1):
        if s < 400:
            continue
        komorki[min(wi - 1, int(cy / (H / wi))) * ko + min(ko - 1, int(cx / (W / ko)))].append(k)
    wyn = []
    for i, plik in enumerate(pliki):
        if not komorki[i]:
            wyn.append((plik, 'BRAK')); continue
        m = np.isin(etyk, komorki[i])
        ys, xs = np.where(m)
        y0, y1, x0, x1 = ys.min(), ys.max() + 1, xs.min(), xs.max() + 1
        # przezroczystość: miękko według odległości od tła, tylko w obrębie obiektu (rozszerzonego o 2 px)
        obszar = ndimage.binary_dilation(m, iterations=2)[y0:y1, x0:x1]
        alfa = np.clip((odl[y0:y1, x0:x1] - 6) / 16, 0, 1)
        alfa = np.where(ndimage.binary_erosion(obszar, iterations=4), np.maximum(alfa, 0.0), alfa) * obszar
        rgba = np.dstack([a[y0:y1, x0:x1], alfa * 255]).astype(np.uint8)
        out = Image.new('RGBA', (x1 - x0 + 6, y1 - y0 + 6), (0, 0, 0, 0))
        out.paste(Image.fromarray(rgba, 'RGBA'), (3, 3))
        dl = max(out.size)
        if dl > maks:
            sk = maks / dl; out = out.resize((round(out.size[0] * sk), round(out.size[1] * sk)), Image.LANCZOS)
        kat = katalog[i] if isinstance(katalog, list) else katalog
        out.save(f'{kat}/{plik}.webp', 'WEBP', quality=88, method=6)
        wyn.append((plik, out.size))
    return wyn

if __name__ == '__main__':
    plan = json.load(open(sys.argv[1]))
    for nr, sciezka in zip(sys.argv[3::2], sys.argv[4::2]):
        ark = plan['arkusze'][nr]
        kat = [sys.argv[2].rstrip('/').rsplit('/', 1)[0] + '/' + c['katalog'] if c.get('katalog') else sys.argv[2] for c in ark]
        for k in set(kat):
            os.makedirs(k, exist_ok=True)
        siatka = tuple(plan.get('siatki', {}).get(nr, [])) or None
        for p in tnij(sciezka, [c['plik'] for c in ark], kat, maks=560 if any(c.get('katalog') for c in ark) else 420, siatka=siatka):
            print(nr, *p)

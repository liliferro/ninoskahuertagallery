#!/usr/bin/env python3
"""Download the heaviest and above-the-fold gallery images and write WebP/AVIF variants.

Images that are not selected stay on ninoskahuertagallery.com. The manifest records both.
GIF files are left remote so lenticular animation is not flattened.
"""
import hashlib, json, os, re, ssl, urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from io import BytesIO
from pathlib import Path
from urllib.parse import unquote, urlparse, urlsplit, urlunsplit, quote

from PIL import Image, ImageOps
import pillow_avif  # noqa: F401

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'media' / 'opt'
MANIFEST = ROOT / 'media' / 'manifest.json'
UPL = 'https://ninoskahuertagallery.com/wp-content/uploads/'
UA = 'Mozilla/5.0 (compatible; NinoskaHuertaGalleryStatic/1.0)'
CTX = ssl.create_default_context()
MAX_BYTES = 25_000_000
HEAVY_MIN = 350_000
HEAVY_EXTRA = 25


def load_content():
    import subprocess
    raw = (ROOT / 'src/content/content.js').read_text()
    data = json.loads(re.search(r'var C = (\{.*\});\s*$', raw, re.S).group(1))
    script = (
        'const fs=require("fs");const vm=require("vm");const s={};'
        'vm.createContext(s);vm.runInContext(fs.readFileSync("src/data.js","utf8"),s);'
        'process.stdout.write(JSON.stringify(s.PRODUCTS));'
    )
    products = json.loads(subprocess.check_output(['node', '-e', script], cwd=ROOT))
    return data, products


def abs_url(src):
    if not src:
        return ''
    src = str(src).strip()
    if src.startswith('~U/'):
        src = UPL + src[3:]
    if src.startswith('//'):
        src = 'https:' + src
    parts = urlsplit(src)
    path = quote(unquote(parts.path), safe='/%')
    return urlunsplit((parts.scheme, parts.netloc, path, parts.query, ''))


def collect(data, products):
    all_urls = []

    def add(src, bucket):
        u = abs_url(src)
        if u:
            all_urls.append(u)
            bucket.add(u)

    priority = set()
    add(data.get('monahan'), priority)
    add(data.get('amalia'), priority)
    add(data.get('aboutPortrait'), priority)
    for src in data.get('beyond') or []:
        add(src, priority)
    for block in data.get('about') or []:
        if block[0] == 'img':
            add(block[1], priority)
    for artist in data['artists']:
        if artist.get('listed'):
            add(artist.get('portrait'), priority)
    posts = data['posts']
    exh = [p for p in posts if p.get('kind') == 'Exhibitions']
    blog = [p for p in posts if p.get('kind') == 'Blog']
    for p in exh[:3] + blog[:3]:
        add(p.get('thumb'), priority)
        add(p.get('hero'), priority)
    home_ids = ['soto-y-la-escritura', 'happiness-with-frame', 'health', 'prosperity',
                'chateau-de-versailles-i', 'chateau-de-versailles-ii',
                'chateau-de-versailles-iv', 'chateau-de-versailles-v']
    by_id = {p['id']: p for p in products}
    for pid in home_ids:
        for src in by_id[pid]['imgs']:
            add(src, priority)
    for p in products:
        for src in p['imgs']:
            add(src, set())  # counted in all_urls only; products also added to priority below
            add(src, priority)
    # every remaining content image is a candidate for the heavy pass
    for artist in data['artists']:
        add(artist.get('portrait'), set())
        for block in artist.get('blocks') or []:
            if block[0] == 'img':
                add(block[1], set())
    for p in posts:
        add(p.get('thumb'), set())
        add(p.get('hero'), set())
        for block in p.get('blocks') or []:
            if block[0] == 'img':
                add(block[1], set())
    # unique, keep order
    seen = set()
    uniq = []
    for u in all_urls:
        if u not in seen:
            seen.add(u)
            uniq.append(u)
    return uniq, priority


def request(url, method='GET'):
    req = urllib.request.Request(url, method=method, headers={'User-Agent': UA, 'Accept': '*/*'})
    with urllib.request.urlopen(req, timeout=45, context=CTX) as res:
        info = res.info()
        if method == 'HEAD':
            return info, b''
        return info, res.read(MAX_BYTES + 1)


def head_one(url):
    try:
        info, _ = request(url, 'HEAD')
        length = info.get('Content-Length')
        ctype = (info.get('Content-Type') or '').split(';')[0].strip().lower()
        return url, int(length) if length and length.isdigit() else None, ctype, None
    except Exception as exc:
        return url, None, '', str(exc)


def slug_for(url):
    path = unquote(urlparse(url).path)
    base = os.path.basename(path)
    base = re.sub(r'\.[A-Za-z0-9]+$', '', base)
    base = re.sub(r'[^a-zA-Z0-9]+', '-', base).strip('-').lower()[:48]
    digest = hashlib.sha1(url.encode()).hexdigest()[:8]
    return f'{base}-{digest}' if base else digest


def convert(url, data):
    im = Image.open(BytesIO(data))
    im = ImageOps.exif_transpose(im)
    if im.mode == 'P':
        im = im.convert('RGBA' if 'transparency' in im.info else 'RGB')
    elif im.mode not in ('RGB', 'RGBA'):
        im = im.convert('RGB')
    ow, oh = im.size
    widths = []
    if ow > 900:
        widths.append(800)
    widths.append(min(ow, 1600))
    folder = OUT / slug_for(url)
    folder.mkdir(parents=True, exist_ok=True)
    variants = []
    for width in widths:
        height = max(1, round(oh * (width / ow)))
        frame = im if width == ow else im.resize((width, height), Image.Resampling.LANCZOS)
        webp = folder / f'{width}.webp'
        avif = folder / f'{width}.avif'
        frame.save(webp, 'WEBP', quality=68, method=6)
        frame.save(avif, 'AVIF', quality=42, speed=6)
        rel = f'/media/opt/{folder.name}'
        variants.append({
            'w': width, 'h': height,
            'webp': f'{rel}/{width}.webp',
            'avif': f'{rel}/{width}.avif',
        })
    variants.sort(key=lambda v: v['w'])
    return {
        'width': ow, 'height': oh,
        'variants': variants,
        'fallback': variants[-1]['webp'],
    }


def main():
    data, products = load_content()
    urls, priority = collect(data, products)
    print(f'unique images {len(urls)} priority {len(priority)}')
    meta = {}
    with ThreadPoolExecutor(max_workers=16) as pool:
        for url, length, ctype, err in pool.map(head_one, urls):
            meta[url] = {'bytes': length, 'type': ctype, 'error': err}
    selected = set(priority)
    heavy = sorted(
        (u for u in urls if (meta[u]['bytes'] or 0) >= HEAVY_MIN and not u.lower().endswith('.gif')),
        key=lambda u: meta[u]['bytes'] or 0,
        reverse=True,
    )
    for u in heavy[:HEAVY_EXTRA]:
        selected.add(u)
    # Never flatten animated GIF.
    selected = {u for u in selected if not u.lower().endswith('.gif')}
    print(f'selected {len(selected)} heavy candidates {len(heavy)}')

    sources = {}
    skipped = []

    def fetch_one(url):
        info = meta.get(url) or {}
        if info.get('bytes') and info['bytes'] > MAX_BYTES:
            return url, None, f'se omite: {info["bytes"]} bytes supera el tope de descarga'
        ctype = info.get('type') or ''
        if 'gif' in ctype:
            return url, None, 'gif remoto (posible lenticular animado)'
        try:
            got, body = request(url, 'GET')
        except Exception as exc:
            return url, None, f'no se pudo descargar: {exc.__class__.__name__}'
        ctype = (got.get('Content-Type') or ctype or '').lower()
        if 'gif' in ctype or url.lower().endswith('.gif'):
            return url, None, 'gif remoto (posible lenticular animado)'
        if len(body) > MAX_BYTES:
            return url, None, f'se omite: descarga de {len(body)} bytes'
        if len(body) < 32:
            return url, None, 'respuesta vacía'
        try:
            return url, convert(url, body), None
        except Exception as exc:
            return url, None, f'no se pudo convertir: {exc.__class__.__name__}'

    with ThreadPoolExecutor(max_workers=6) as pool:
        futures = [pool.submit(fetch_one, u) for u in sorted(selected)]
        done = 0
        for fut in as_completed(futures):
            url, info, reason = fut.result()
            done += 1
            if info:
                sources[url] = info
            else:
                skipped.append({'url': url, 'reason': reason, 'bytes': (meta.get(url) or {}).get('bytes')})
            if done % 10 == 0 or done == len(selected):
                print(f'converted {done}/{len(selected)} ok {len(sources)} skipped {len(skipped)}')

    remote = []
    for url in urls:
        if url in sources:
            continue
        reason = next((s['reason'] for s in skipped if s['url'] == url), None)
        if reason is None:
            if url.lower().endswith('.gif'):
                reason = 'gif remoto (posible lenticular animado)'
            else:
                reason = 'fuera del grupo prioritario; sigue en el WordPress de origen'
        remote.append({'url': url, 'reason': reason, 'bytes': (meta.get(url) or {}).get('bytes')})

    MANIFEST.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        'sources': sources,
        'remote': remote,
        'counts': {
            'unique': len(urls),
            'local': len(sources),
            'remote': len(remote),
        },
    }
    MANIFEST.write_text(json.dumps(payload, ensure_ascii=False, indent=2))
    total = sum(p.stat().st_size for p in OUT.rglob('*') if p.is_file())
    print('manifest', MANIFEST, 'local', len(sources), 'remote', len(remote), 'bytes', total)


if __name__ == '__main__':
    main()

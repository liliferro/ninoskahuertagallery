#!/usr/bin/env python3
"""Genera el sitio estático de Ninoska Huerta Gallery.

Lee src/content/content.js, src/data.js y media/manifest.json.
Escribe HTML con una URL por vista, metadatos, JSON-LD y los archivos
robots.txt, sitemap.xml, llms.txt y favicon.ico.

No inventa precios, fechas, direcciones ni premios: solo usa datos ya
presentes en el prototipo. Los huecos quedan como comentarios TODO.
"""
import html
import json
import re
import subprocess
import unicodedata
from pathlib import Path
from urllib.parse import quote, unquote, urlsplit, urlunsplit

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
ORIGIN = 'https://ninoskahuertagallery.vercel.app'
UPL = 'https://ninoskahuertagallery.com/wp-content/uploads/'
MONTHS = ['enero', 'febrero', 'marzo', 'abril', 'mayo', 'junio', 'julio', 'agosto', 'septiembre', 'octubre', 'noviembre', 'diciembre']

# TODO: confirmar fecha de fundación (el texto cita 1994 en Venezuela y 2020 en Miracle Mile),
# coordenadas, horario semanal (solo consta "con cita previa"), identificadores Wikidata / sameAs
# de cada artista, autoría de los artículos y disponibilidad de stock. No se inventan.

NAV = [
    ('/acerca-de/', 'Acerca de', 'about'),
    ('/artistas/', 'Artistas', 'artists'),
    ('/exposiciones/', 'Exposiciones', 'exhibitions'),
    ('/tienda/', 'Tienda', 'shop'),
    ('/blog/', 'Blog', 'blog'),
    ('/contacto/', 'Contacto', 'contact'),
]
SPEC_LABELS = {
    'Dimensions': 'Medidas', 'Print length': 'Extensión', 'Essay': 'Ensayo',
    'Artist statement': 'Texto del artista', 'Art critic': 'Crítica', 'Editor': 'Editor',
    'Published': 'Publicado', 'Language': 'Idioma', 'Medium': 'Técnica', 'Year': 'Año',
    'Edition': 'Edición', 'Presentation': 'Presentación', 'Frame': 'Marco',
}
SPEC_VALUES = {
    'Original work': 'Obra original', 'Included': 'Incluido', 'Not included': 'No incluido',
    'Spanish': 'Español', '160 pages': '160 páginas',
}
HOME_IDS = [
    'soto-y-la-escritura', 'happiness-with-frame', 'health', 'prosperity',
    'chateau-de-versailles-i', 'chateau-de-versailles-ii',
    'chateau-de-versailles-iv', 'chateau-de-versailles-v',
]
DIM_RE = re.compile(r'^([\d.]+)\s*[″"]\s*[×x]\s*([\d.]+)\s*[″"]$')
GALLERY_ID = ORIGIN + '/#galeria'
SITE_ID = ORIGIN + '/#sitio'
NINOSKA_ID = ORIGIN + '/acerca-de/#ninoska-huerta'


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


def esc(value):
    return html.escape('' if value is None else str(value), quote=True)


def plain(value):
    text = re.sub(r'<br\s*/?>', ' · ', '' if value is None else str(value), flags=re.I)
    text = re.sub(r'<[^>]+>', '', text)
    text = html.unescape(text)
    return re.sub(r'\s+', ' ', text).strip()


def tidy(value):
    return re.sub(r'\s+', ' ', plain(value)).strip()


def clamp(value, limit=155):
    text = tidy(value)
    if len(text) <= limit:
        return text
    cut = text[:limit - 1].rsplit(' ', 1)[0]
    return (cut or text[:limit - 1]).rstrip('.,;:') + '…'


def sort_key(name):
    folded = ''.join(c for c in unicodedata.normalize('NFD', name) if unicodedata.category(c) != 'Mn')
    return folded.lower()


def fdate(iso):
    year, month, day = iso.split('-')
    return f'{int(day)} de {MONTHS[int(month) - 1]} de {year}'


def money(amount):
    return f'${float(amount):.2f}'


def load_data():
    raw = (ROOT / 'src/content/content.js').read_text()
    content = json.loads(re.search(r'var C = (\{.*\});\s*$', raw, re.S).group(1))
    script = (
        'const fs=require("fs");const vm=require("vm");const s={};'
        'vm.createContext(s);vm.runInContext(fs.readFileSync("src/data.js","utf8"),s);'
        'process.stdout.write(JSON.stringify(s.PRODUCTS));'
    )
    products = json.loads(subprocess.check_output(['node', '-e', script], cwd=ROOT))
    manifest = {'sources': {}}
    path = ROOT / 'media' / 'manifest.json'
    if path.exists():
        manifest = json.loads(path.read_text())
    return content, products, manifest.get('sources') or {}


def subtitle(artist):
    text = tidy(artist.get('sub') or '')
    if not text or text.strip('–-—') == '':
        return ''
    return text


def artist_alt(name):
    return f'Retrato de {name}'


def work_alt(product):
    if product['id'] == 'soto-y-la-escritura':
        return 'Soto y la Escritura, libro editado por Ninoska Huerta'
    return f"{tidy(product['title'])}, obra de {product['artist']}"


def display_src(src, media):
    url = abs_url(src)
    info = media.get(url)
    if info:
        return info['fallback']
    return url


def picture(src, alt, media, ratio=(800, 800), eager=False, sizes='(max-width: 767px) 100vw, 50vw', cls='', style=''):
    url = abs_url(src)
    alt = tidy(alt)
    info = media.get(url)
    loading = 'eager' if eager else 'lazy'
    fetch = ' fetchpriority="high"' if eager else ''
    if info:
        width, height = info['width'], info['height']
        variants = info['variants']
        avif = ', '.join(f"{v['avif']} {v['w']}w" for v in variants)
        webp = ', '.join(f"{v['webp']} {v['w']}w" for v in variants)
        inner = (
            '<picture>'
            f'<source type="image/avif" srcset="{esc(avif)}" sizes="{esc(sizes)}">'
            f'<source type="image/webp" srcset="{esc(webp)}" sizes="{esc(sizes)}">'
            f'<img src="{esc(info["fallback"])}" alt="{esc(alt)}" width="{width}" height="{height}" loading="{loading}" decoding="async"{fetch}>'
            '</picture>'
        )
    else:
        width, height = ratio
        inner = (
            f'<img src="{esc(url)}" alt="{esc(alt)}" width="{width}" height="{height}" '
            f'loading="{loading}" decoding="async"{fetch}>'
        )
    klass = ('img ' + cls).strip()
    style_attr = f' style="{esc(style)}"' if style else ''
    return f'<div class="{klass}"{style_attr} data-label="{esc(alt)}">{inner}</div>'


def vid_embed(src):
    base = src.split('?')[0]
    if 'vimeo' in src:
        return base + '?dnt=1&autoplay=1'
    return base + '?autoplay=1&rel=0'


def vid_watch(src):
    match = re.search(r'youtube\.com/embed/([\w-]+)', src)
    if match:
        return 'https://www.youtube.com/watch?v=' + match.group(1)
    match = re.search(r'vimeo\.com/video/(\d+)', src)
    if match:
        return 'https://vimeo.com/' + match.group(1)
    return src


def vid_host(src):
    return 'Vimeo' if 'vimeo' in src else 'YouTube'


def vbox(src, title=''):
    label = 'Reproducir vídeo' + (': ' + title if title else '')
    host = vid_host(src)
    return (
        '<div><div class="vbox"><button type="button" data-play="' + esc(vid_embed(src)) + '" aria-label="' + esc(label) + '">'
        '<svg width="54" height="54" viewBox="0 0 54 54" aria-hidden="true"><circle cx="27" cy="27" r="26" fill="none" stroke="currentColor" stroke-width="1.2"/>'
        '<path d="M22 17l15 10-15 10z" fill="currentColor"/></svg>'
        '<span class="lbl">Reproducir vídeo</span></button></div>'
        f'<a class="vlink" href="{esc(vid_watch(src))}">{esc("Ver en " + host)} ↗</a></div>'
    )


def fig(block, media, artist=None, use_alt=False, fallback=''):
    alt_raw = plain(block[2]) if len(block) > 2 else ''
    cap_raw = plain(block[3]) if len(block) > 3 else ''
    cap = cap_raw or (alt_raw if use_alt else '')
    alt = cap_raw if len(cap_raw) > len(alt_raw) else (alt_raw or cap_raw)
    if artist and alt and artist not in alt:
        alt = alt + ', ' + artist
    elif not alt and fallback:
        # TODO: la imagen no trae pie propio; se usa el título de la página, que sí está publicado.
        alt = fallback
    elif artist and not alt:
        # TODO: esta imagen no trae pie ni texto alternativo en el contenido migrado.
        alt = 'Obra de ' + artist
    cap_html = f'<figcaption>{esc(cap)}</figcaption>' if cap else ''
    shown = display_src(block[1], media)
    return (
        f'<figure><button type="button" data-lb="{esc(shown)}" data-cap="{esc(cap)}" aria-label="{esc("Ampliar" + (": " + alt if alt else ""))}">'
        + picture(block[1], alt, media, (800, 800), sizes='(max-width: 767px) 50vw, 280px')
        + f'</button>{cap_html}</figure>'
    )


def render_blocks(blocks, media, artist=None, use_alt=False, grid=False, fallback=''):
    out = []
    i = 0
    in_list = False

    def close():
        nonlocal in_list
        if in_list:
            out.append('</ul>')
            in_list = False

    while i < len(blocks):
        kind = blocks[i][0]
        if kind == 'img':
            close()
            group = []
            while i < len(blocks) and blocks[i][0] == 'img':
                group.append(blocks[i])
                i += 1
            klass = 'gal one' if len(group) == 1 and not grid else 'gal'
            out.append('<div class="' + klass + '">' + ''.join(fig(item, media, artist, use_alt, fallback) for item in group) + '</div>')
            continue
        if kind == 'video':
            close()
            out.append('<div style="margin:28px 0;max-width:860px">' + vbox(blocks[i][1], artist or '') + '</div>')
            i += 1
            continue
        if kind == 'li':
            if not in_list:
                out.append('<ul>')
                in_list = True
            out.append('<li>' + esc(blocks[i][1]) + '</li>')
            i += 1
            continue
        close()
        if kind in ('h1', 'h2', 'h3', 'h4', 'h5', 'h6'):
            # Un solo h1 por documento: el título de la página. El contenido interno baja un nivel si traía h1.
            tag = 'h2' if kind == 'h1' else kind
            out.append(f'<{tag}>{esc(blocks[i][1])}</{tag}>')
        elif kind == 'blockquote':
            out.append('<blockquote>' + esc(blocks[i][1]) + '</blockquote>')
        else:
            text = blocks[i][1] if len(blocks[i]) > 1 else ''
            if plain(text):
                out.append('<p>' + esc(text) + '</p>')
        i += 1
    close()
    return ''.join(out)


def pcard(product, media):
    alt = work_alt(product)
    artist = 'Libro' if product['artist'] == 'Book' else product['artist']
    return (
        f'<div class="pcard-wrap" data-product data-line="{esc(product["line"])}" data-price="{product["price"]}" data-title="{esc(tidy(product["title"]))}">'
        f'<a class="pcard" href="/tienda/{esc(product["id"])}/">'
        + picture(product['imgs'][0], alt, media, (800, 800), sizes='(max-width: 767px) 45vw, (max-width: 1100px) 30vw, 280px', cls='contain')
        + f'<span class="art">{esc(artist)}</span><span class="t">{esc(tidy(product["title"]))}</span><span class="p">{money(product["price"])}</span></a>'
        f'<button class="btn line add" type="button" data-add="{esc(product["id"])}" style="min-height:38px;padding:0 14px;margin-top:10px">Añadir al carrito</button></div>'
    )


def acard(artist, media):
    sub = subtitle(artist)
    sub_html = f'<span class="mono" style="color:var(--muted);font-size:12px">{esc(sub)}</span>' if sub else ''
    return (
        f'<a class="acard" href="/artistas/{esc(artist["id"])}/">'
        + picture(artist.get('portrait'), artist_alt(artist['name']), media, (800, 800), sizes='(max-width: 767px) 45vw, 220px')
        + f'<span class="n">{esc(artist["name"])}</span>{sub_html}</a>'
    )


def post_path(post):
    base = '/exposiciones/' if post['kind'] == 'Exhibitions' else '/blog/'
    return base + post['id'] + '/'


def ccard(post, media, recent=False, heading='h3'):
    label = fdate(post['date'])
    if recent:
        label = 'Reciente · ' + label
    excerpt = tidy(post.get('excerpt') or '')
    excerpt_html = f'<p>{esc(excerpt)}</p>' if excerpt else ''
    thumb = post.get('thumb') or post.get('hero')
    return (
        f'<a class="ccard" href="{esc(post_path(post))}">'
        + picture(thumb, tidy(post['title']), media, (800, 600), sizes='(max-width: 767px) 100vw, 360px')
        + f'<p class="lbl{" now" if recent else ""}" style="{"color:var(--ink)" if recent else "color:var(--muted)"}">'
        + ('<span class="dot" aria-hidden="true"></span>' if recent else '')
        + esc(label) + '</p>'
        + f'<{heading}>{esc(tidy(post["title"]))}</{heading}>{excerpt_html}<span class="tlink">Leer más →</span></a>'
    )


def split_artist(blocks):
    bio, work, seen = [], [], False
    for block in blocks:
        if block[0] == 'h2' and block[1] == 'Featured work':
            seen = True
            continue
        (work if seen else bio).append(block)
    if not seen:
        bio = [block for block in blocks if block[0] != 'img']
        work = [block for block in blocks if block[0] == 'img']
    return bio, work


def pager(items, index, href_for, label):
    prev_item = items[index - 1] if index > 0 else None
    next_item = items[index + 1] if index + 1 < len(items) else None
    left = (
        f'<a href="{esc(href_for(prev_item))}"><small>← Anterior</small>{esc(tidy(prev_item.get("name") or prev_item.get("title")))}</a>'
        if prev_item else '<span></span>'
    )
    right = (
        f'<a href="{esc(href_for(next_item))}" style="text-align:right"><small>Siguiente →</small>{esc(tidy(next_item.get("name") or next_item.get("title")))}</a>'
        if next_item else '<span></span>'
    )
    return f'<nav class="pager" aria-label="Más {esc(label)}">{left}{right}</nav>'


def line_label(line):
    return 'Libros' if line == 'Books' else line


def spec_rows(product):
    rows = []
    for key, value in product['specs']:
        rows.append(f'<dt>{esc(SPEC_LABELS.get(key, key))}</dt><dd>{esc(SPEC_VALUES.get(value, value))}</dd>')
    return ''.join(rows)


def parse_dims(value):
    if not value:
        return None
    match = DIM_RE.match(value.strip())
    if not match:
        return None
    return (match.group(1) + ' in', match.group(2) + ' in')


def json_script(graph):
    payload = {'@context': 'https://schema.org', '@graph': graph}
    raw = json.dumps(payload, ensure_ascii=False, separators=(',', ':'))
    return raw.replace('<', '\\u003c')


def absolute_image(src, media):
    url = abs_url(src)
    info = media.get(url)
    if info:
        return ORIGIN + info['fallback']
    return url


def gallery_node():
    return {
        '@type': 'ArtGallery',
        '@id': GALLERY_ID,
        'name': 'Ninoska Huerta Gallery',
        'url': ORIGIN + '/',
        'description': 'Ninoska Huerta Gallery, Coral Gables, Miami. Constructivism, abstraction and kinetic art: Latin American masters and new voices. By appointment only.',
        'email': 'ninoskahuerta@gmail.com',
        'telephone': '+1-305-588-1231',
        'currenciesAccepted': 'USD',
        'address': {
            '@type': 'PostalAddress',
            'streetAddress': '290 Miracle Mile',
            'addressLocality': 'Coral Gables',
            'addressRegion': 'FL',
            'postalCode': '33134',
            'addressCountry': 'US',
        },
        'sameAs': [
            'https://www.instagram.com/galleryninoskahuerta/',
            'https://www.facebook.com/NinoskaHuertaGallery',
            'https://www.youtube.com/channel/UCAxbyWPj5At8foQhLUB0moA',
        ],
        'logo': {'@type': 'ImageObject', 'url': ORIGIN + '/assets/logos/nh-logo-short.svg'},
    }


def website_node():
    return {
        '@type': 'WebSite',
        '@id': SITE_ID,
        'name': 'Ninoska Huerta Gallery',
        'url': ORIGIN + '/',
        'inLanguage': 'es',
        'publisher': {'@id': GALLERY_ID},
    }


def ninoska_node(content, media):
    first = next((plain(block[1]) for block in content['about'] if block[0] == 'p' and plain(block[1])), '')
    node = {
        '@type': 'Person',
        '@id': NINOSKA_ID,
        'name': 'Ninoska Huerta',
        'jobTitle': 'Connoisseur, Collector, Advisor & Private Art Dealer',
        'url': ORIGIN + '/acerca-de/',
        'email': 'ninoskahuerta@gmail.com',
        'telephone': '+1-305-588-1231',
        'workLocation': {'@id': GALLERY_ID},
        # El texto dice que se graduó en Iles Academy. No se añade la UCV como alumniOf: el texto solo dice que siguió estudios allí.
        'alumniOf': {'@type': 'EducationalOrganization', 'name': 'Iles Academy'},
    }
    if content.get('aboutPortrait'):
        node['image'] = absolute_image(content['aboutPortrait'], media)
    if first:
        node['description'] = clamp(first, 500)
    return node


def artist_node(artist, media):
    first = next((plain(block[1]) for block in artist['blocks'] if block[0] == 'p' and plain(block[1])), '')
    parts = [part for part in (subtitle(artist), first) if part]
    node = {
        '@type': 'Person',
        '@id': ORIGIN + '/artistas/' + artist['id'] + '/#persona',
        'name': artist['name'],
        'url': ORIGIN + '/artistas/' + artist['id'] + '/',
        'affiliation': {'@id': GALLERY_ID},
    }
    if artist.get('portrait'):
        node['image'] = absolute_image(artist['portrait'], media)
    if parts:
        node['description'] = clamp(' '.join(parts), 500)
    # TODO: no se rellena birthDate. Varios subtítulos empiezan por un año, pero la ficha no lo llama fecha de nacimiento.
    return node


def offer(product):
    # TODO: no consta disponibilidad (InStock u otra). El precio sí está publicado, en USD.
    return {
        '@type': 'Offer',
        'price': f'{float(product["price"]):.2f}',
        'priceCurrency': 'USD',
        'url': ORIGIN + '/tienda/' + product['id'] + '/',
    }


def artwork_node(product, artists_by_name, media):
    if product['id'] == 'soto-y-la-escritura':
        specs = dict(product['specs'])
        pages = re.search(r'(\d+)', specs.get('Print length') or '')
        node = {
            '@type': 'Book',
            '@id': ORIGIN + '/tienda/' + product['id'] + '/#libro',
            'name': tidy(product['title']),
            'editor': {'@id': NINOSKA_ID},
            'url': ORIGIN + '/tienda/' + product['id'] + '/',
            'image': absolute_image(product['imgs'][0], media),
            'offers': offer(product),
            'description': 'Ensayo: Arturo Uslar Pietri. Texto del artista: Jesús Rafael Soto. Editor: Ninoska Huerta.',
        }
        if specs.get('Published'):
            node['datePublished'] = specs['Published']
        if (specs.get('Language') or '').lower() == 'spanish':
            node['inLanguage'] = 'es'
        if pages:
            node['numberOfPages'] = int(pages.group(1))
        # TODO: el libro no trae ISBN ni un campo "autor". No se asigna author.
        return node
    node = {
        '@type': 'VisualArtwork',
        '@id': ORIGIN + '/tienda/' + product['id'] + '/#obra',
        'name': tidy(product['title']),
        'image': absolute_image(product['imgs'][0], media),
        'url': ORIGIN + '/tienda/' + product['id'] + '/',
        'offers': offer(product),
    }
    artist = artists_by_name.get(product['artist'])
    if artist:
        node['creator'] = {'@id': ORIGIN + '/artistas/' + artist['id'] + '/#persona'}
    else:
        node['creator'] = {'@type': 'Person', 'name': product['artist']}
        # TODO: Karim Borjas tiene obras en la tienda y no tiene ficha en el listado de artistas.
    specs = dict(product['specs'])
    if specs.get('Medium'):
        node['artMedium'] = specs['Medium']
    if specs.get('Year'):
        node['dateCreated'] = specs['Year']
    if specs.get('Edition'):
        node['artEdition'] = specs['Edition']
    dims = parse_dims(specs.get('Dimensions'))
    if dims:
        node['width'] = {'@type': 'Distance', 'name': dims[0]}
        node['height'] = {'@type': 'Distance', 'name': dims[1]}
    return node


def article_node(post, media):
    node = {
        '@type': 'BlogPosting' if post['kind'] == 'Blog' else 'Article',
        '@id': ORIGIN + post_path(post) + '#articulo',
        'headline': tidy(post['title']),
        'datePublished': post['date'],
        'url': ORIGIN + post_path(post),
        'publisher': {'@id': GALLERY_ID},
    }
    excerpt = tidy(post.get('excerpt') or '')
    if excerpt:
        node['description'] = clamp(excerpt, 400)
    image = post.get('hero') or post.get('thumb')
    if image:
        node['image'] = absolute_image(image, media)
    # TODO: los textos no indican autor de forma uniforme. No se rellena author.
    # TODO: la fecha es la de la entrada, no necesariamente el inicio de la exposición. No se usa ExhibitionEvent.
    return node


def breadcrumb(items, page_path):
    return {
        '@type': 'BreadcrumbList',
        '@id': ORIGIN + page_path + '#migas',
        'itemListElement': [
            {'@type': 'ListItem', 'position': index + 1, 'name': name, 'item': ORIGIN + path}
            for index, (name, path) in enumerate(items)
        ],
    }


def webpage(title, description, path, about):
    return {
        '@type': 'WebPage',
        '@id': ORIGIN + path + '#pagina',
        'url': ORIGIN + path,
        'name': title,
        'description': description,
        'inLanguage': 'es',
        'isPartOf': {'@id': SITE_ID},
        'about': {'@id': about},
    }


def item_list(name, entries):
    return {
        '@type': 'ItemList',
        'name': name,
        'itemListElement': [
            {'@type': 'ListItem', 'position': index + 1, 'name': label, 'url': ORIGIN + path}
            for index, (label, path) in enumerate(entries)
        ],
    }


class OgCache:
    def __init__(self, media):
        self.media = media
        self.made = {}

    def jpeg(self, src):
        url = abs_url(src)
        if not url:
            return None
        if url in self.made:
            return self.made[url]
        info = self.media.get(url)
        if not info:
            self.made[url] = {'url': url, 'width': None, 'height': None}
            return self.made[url]
        source = ROOT / info['fallback'].lstrip('/')
        slug = Path(info['fallback']).parent.name
        dest = ROOT / 'media' / 'og' / f'{slug}.jpg'
        dest.parent.mkdir(parents=True, exist_ok=True)
        image = Image.open(source)
        if image.mode == 'RGBA':
            base = Image.new('RGB', image.size, (255, 255, 255))
            base.paste(image, mask=image.split()[-1])
            image = base
        else:
            image = image.convert('RGB')
        image.thumbnail((1200, 1200), Image.Resampling.LANCZOS)
        image.save(dest, 'JPEG', quality=78, optimize=True)
        result = {'url': ORIGIN + '/media/og/' + dest.name, 'width': image.size[0], 'height': image.size[1]}
        self.made[url] = result
        return result


def nav_html(current, mobile=False):
    parts = []
    for href, label, key in NAV:
        current_attr = ' aria-current="page"' if key == current else ''
        parts.append(f'<a href="{href}"{current_attr}>{label}</a>')
    return ''.join(parts)


def header(current):
    return f'''<header class="site-h" id="top">
  <div class="wrap bar">
    <a class="logo" href="/" aria-label="Ninoska Huerta Gallery, inicio"></a>
    <nav class="hnav" aria-label="Principal">{nav_html(current)}</nav>
    <div class="hicons">
      <button class="iconbtn" id="cartBtn" type="button" aria-label="Abrir carrito, 0 obras">
        <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="square"><path d="M5 8h14l-1 12H6z M9 8V6a3 3 0 0 1 6 0v2"/></svg>
        <span class="count" id="cartCount" hidden>0</span>
      </button>
      <button class="iconbtn menu-btn" id="menuBtn" type="button" aria-label="Abrir menú" aria-expanded="false" aria-controls="mnav">
        <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="square"><path d="M4 8h16M4 16h16"/></svg>
      </button>
    </div>
  </div>
</header>
<div class="mnav" id="mnav" hidden role="dialog" aria-modal="true" aria-label="Menú">
  <div class="top"><a class="logo" href="/" aria-label="Ninoska Huerta Gallery, inicio"></a>
    <button class="iconbtn" id="menuClose" type="button" aria-label="Cerrar menú"><svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="square"><path d="M6 6l12 12M18 6L6 18"/></svg></button></div>
  <nav aria-label="Principal (móvil)">{nav_html(current, True)}</nav>
  <a class="btn dark" href="/contacto/">Reservar una visita</a>
  <p class="mono">290 Miracle Mile, Coral Gables, FL 33134 · Solo con cita previa<br>+1 305 588 1231 · ninoskahuerta@gmail.com</p>
</div>'''


def newsletter():
    return '''<section class="news" aria-labelledby="nl">
  <div class="wrap grid2" style="align-items:center">
    <div><p class="kicker lbl" style="color:var(--gray)">Boletín</p><h2 id="nl" style="margin:0">Suscríbete al boletín</h2></div>
    <div>
      <form id="nform" novalidate><label class="sr" for="nemail" style="position:absolute;left:-9999px">Correo</label>
        <input id="nemail" type="email" placeholder="Correo" autocomplete="email"><button class="btn light" type="submit">Suscribirse</button></form>
      <p class="msg" id="nmsg" hidden></p>
    </div>
  </div>
</section>'''


def footer():
    return '''<footer class="site-f">
  <div class="wrap">
    <div class="fgrid">
      <div><span class="flogo" role="img" aria-label="Ninoska Huerta Gallery"></span><p style="color:var(--gray)">Constructivismo · Abstracción · Arte cinético</p></div>
      <div><h4>Contacto</h4><p>290 Miracle Mile<br>Coral Gables, FL 33134, USA</p><p>Solo con cita previa</p><p><a href="tel:+13055881231">+1 305 588 1231</a><br><a href="mailto:ninoskahuerta@gmail.com">ninoskahuerta@gmail.com</a></p></div>
      <div><h4>Contenido</h4><ul><li><a href="/acerca-de/">Acerca de</a></li><li><a href="/artistas/">Artistas</a></li><li><a href="/exposiciones/">Exposiciones</a></li><li><a href="/tienda/">Tienda</a></li><li><a href="/blog/">Blog</a></li><li><a href="/contacto/">Contacto</a></li><li><a href="/terminos/">Términos y condiciones</a></li></ul></div>
      <div><h4>Síguenos</h4><ul><li><a href="https://www.instagram.com/galleryninoskahuerta/">Instagram</a></li><li><a href="https://www.facebook.com/NinoskaHuertaGallery">Facebook</a></li><li><a href="https://www.youtube.com/channel/UCAxbyWPj5At8foQhLUB0moA">YouTube</a></li></ul></div>
    </div>
    <div class="fbottom"><span>© 2026 Ninoska Huerta Gallery · ninoskahuertagallery.com</span><span>Precios en USD</span></div>
  </div>
</footer>'''


def cart_html():
    return '''<div class="scrim-cart" id="cartScrim" hidden></div>
<aside class="drawer" id="cart" hidden role="dialog" aria-modal="true" aria-labelledby="cartTitle">
  <div class="top"><h2 id="cartTitle">Tu carrito</h2><button class="iconbtn" id="cartClose" type="button" aria-label="Cerrar carrito"><svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="square"><path d="M6 6l12 12M18 6L6 18"/></svg></button></div>
  <div class="lines" id="cartLines"></div>
  <div class="totals" id="cartTotals"></div>
</aside>
<div class="toast" id="toast" hidden role="status"></div>
<div class="modal" id="checkoutModal" hidden role="dialog" aria-modal="true" aria-labelledby="coT">
  <div class="box"><h3 id="coT">Finalizar compra</h3><p id="coBody" style="color:var(--muted)"></p><div class="ctas"><button class="btn dark" type="button" id="coClose">Volver al carrito</button><a class="btn line" href="/contacto/" id="coContact">Contactar con la galería</a></div></div>
</div>'''


def render_document(spec, og_cache):
    og = og_cache.jpeg(spec['og_src']) if spec.get('og_src') else None
    if not og or not og.get('url'):
        og = og_cache.jpeg(spec['default_og'])
    canonical = ORIGIN + spec['path']
    graph = [website_node(), gallery_node(), webpage(spec['title'], spec['description'], spec['path'], spec['about'])]
    if spec.get('crumbs'):
        graph.append(breadcrumb(spec['crumbs'], spec['path']))
    graph.extend(spec.get('extra') or [])
    script = json_script(graph)
    links = []
    if spec.get('prev'):
        links.append(f'<link rel="prev" href="{esc(ORIGIN + spec["prev"])}">')
    if spec.get('next'):
        links.append(f'<link rel="next" href="{esc(ORIGIN + spec["next"])}">')
    og_tags = [
        f'<meta property="og:image" content="{esc(og["url"])}">',
        f'<meta property="og:image:alt" content="{esc(spec["og_alt"])}">',
    ]
    if og.get('width') and og.get('height'):
        og_tags.append(f'<meta property="og:image:width" content="{og["width"]}">')
        og_tags.append(f'<meta property="og:image:height" content="{og["height"]}">')
    extra = ''
    if spec.get('price') is not None:
        extra = f'<meta property="product:price:amount" content="{float(spec["price"]):.2f}">\n<meta property="product:price:currency" content="USD">'
    kinetic = '<script src="/assets/kinetic.js"></script>' if spec.get('kinetic') else ''
    body_class = spec.get('body_class') or ''
    return f'''<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>{esc(spec["title"])}</title>
<meta name="description" content="{esc(spec["description"])}">
<meta name="robots" content="{esc(spec.get("robots") or "index, follow")}">
<link rel="canonical" href="{esc(canonical)}">
{''.join(links)}
<meta property="og:site_name" content="Ninoska Huerta Gallery">
<meta property="og:locale" content="es_ES">
<meta property="og:type" content="{esc(spec.get("og_type") or "website")}">
<meta property="og:title" content="{esc(spec["title"])}">
<meta property="og:description" content="{esc(spec["description"])}">
<meta property="og:url" content="{esc(canonical)}">
{chr(10).join(og_tags)}
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{esc(spec["title"])}">
<meta name="twitter:description" content="{esc(spec["description"])}">
<meta name="twitter:image" content="{esc(og["url"])}">
<meta name="twitter:image:alt" content="{esc(spec["og_alt"])}">
{extra}
<link rel="icon" href="/favicon.ico" sizes="any">
<link rel="icon" type="image/svg+xml" href="/assets/logos/nh-logo-short.svg">
<link rel="preload" href="/assets/fonts/Jost-wght.woff2" as="font" type="font/woff2" crossorigin>
<link rel="preload" href="/assets/fonts/IBMPlexMono-400.woff2" as="font" type="font/woff2" crossorigin>
<link rel="preconnect" href="https://ninoskahuertagallery.com" crossorigin>
<link rel="stylesheet" href="/assets/site.css">
<!-- TODO: faltan, y no se inventan, fecha de fundación unívoca, coordenadas, horario semanal, Wikidata y sameAs de artistas, autor de cada texto y disponibilidad de stock. -->
<script type="application/ld+json">{script}</script>
</head>
<body class="{esc(body_class)}">
{header(spec["current"])}
<main id="main">
{spec["main"]}
{newsletter()}
</main>
{footer()}
{cart_html()}
<script src="/assets/catalog.js"></script>
<script src="/assets/app.js"></script>
{kinetic}
</body>
</html>
'''


def write_page(spec, og_cache):
    target = ROOT / 'index.html' if spec['path'] == '/' else ROOT / spec['path'].strip('/') / 'index.html'
    if spec['path'] == '/404.html':
        target = ROOT / '404.html'
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(render_document(spec, og_cache))
    return target


def first_paragraph(blocks):
    for block in blocks:
        if block[0] == 'p' and plain(block[1]):
            return plain(block[1])
    return ''


def build():
    content, products, media = load_data()
    artists = sorted(content['artists'], key=lambda artist: sort_key(artist['name']))
    listed = [artist for artist in artists if artist.get('listed')]
    by_name = {artist['name']: artist for artist in artists}
    by_id = {product['id']: product for product in products}
    exhibitions = [post for post in content['posts'] if post['kind'] == 'Exhibitions']
    blog = [post for post in content['posts'] if post['kind'] == 'Blog']
    og_cache = OgCache(media)
    default_og = content.get('aboutPortrait')
    pages = []

    def add(spec):
        spec.setdefault('default_og', default_og)
        spec.setdefault('og_alt', 'Ninoska Huerta Gallery')
        pages.append(spec)

    home_desc = 'Ninoska Huerta Gallery en Coral Gables, Miami. Arte cinético, óptico y constructivo de América Latina, de los maestros a las nuevas voces. Solo con cita previa.'
    beyond = ''.join(picture(src, 'Marcos Marín, Beyond the Visible', media, (1600, 1000), sizes='(max-width: 980px) 100vw, 55vw') for src in content['beyond'])
    home_products = ''.join(pcard(by_id[pid], media) for pid in HOME_IDS)
    home_artists = ''.join(acard(artist, media) for artist in listed)
    home_exh = ''.join(ccard(post, media, recent=(index == 0)) for index, post in enumerate(exhibitions[:3]))
    home_posts = ''.join(ccard(post, media) for post in blog[:3])
    home_videos = ''.join(vbox(src) for src in content['homeVideos'])
    works = [artwork_node(product, by_name, media) for product in products]
    add({
        'path': '/',
        'title': 'Ninoska Huerta Gallery · Arte cinético en Coral Gables',
        'description': home_desc,
        'current': 'home',
        'body_class': 'route-home on-hero',
        'kinetic': True,
        'og_src': (content.get('beyond') or [None])[0] or default_og,
        'og_alt': 'Marcos Marín, Beyond the Visible, en Ninoska Huerta Gallery',
        'about': GALLERY_ID,
        'extra': [
            ninoska_node(content, media),
            item_list('Artistas', [(artist['name'], '/artistas/' + artist['id'] + '/') for artist in listed]),
            {'@type': 'ItemList', 'name': 'Obras en la tienda', 'itemListElement': [
                {'@type': 'ListItem', 'position': index + 1, 'item': {'@id': work['@id']}}
                for index, work in enumerate(works)
            ]},
            *works,
        ],
        'main': f'''<div class="hero" id="hero">
    <canvas id="field" aria-hidden="true"></canvas>
    <div class="scrim" aria-hidden="true"></div>
    <div class="inner wrap">
      <div class="content">
        <p class="eyebrow lbl"><span class="dot" aria-hidden="true"></span>Constructivismo · Abstracción · Arte cinético</p>
        <div class="br-frame"><span class="br l" aria-hidden="true"></span><h1>The eye takes part.</h1><span class="br r" aria-hidden="true"></span></div>
        <p class="lead">Latin American kinetic, optical and constructive art, from the masters to new voices. <span>Coral Gables, Miami · By appointment only.</span></p>
        <div class="ctas"><a class="btn light" href="/exposiciones/">Ver exposiciones</a><a class="btn ghost" href="/tienda/">Visitar la tienda</a></div>
      </div>
      <div class="foot">
        <button class="pause" id="pause" type="button" aria-pressed="false">
          <svg id="pi" width="12" height="12" viewBox="0 0 12 12" aria-hidden="true"><rect x="2" y="1.5" width="2.5" height="9" fill="currentColor"/><rect x="7.5" y="1.5" width="2.5" height="9" fill="currentColor"/></svg>
          <span id="pl">Pausar movimiento</span>
        </button>
        <p class="credit">Efecto cinético inspirado en el lenguaje de Cruz-Diez y Soto</p>
      </div>
    </div>
  </div>
  <section class="s" style="border-top:0">
    <div class="wrap grid2">
      <figure class="monahan" style="margin:0">
        {picture(content.get("monahan"), "Peter Monahan, S/T", media, (1600, 1000), sizes="(max-width: 980px) 100vw, 50vw", style="aspect-ratio:16/10")}
        <figcaption class="mono" style="margin-top:10px"><span class="lbl" style="color:var(--ink)">Peter Monahan</span> · <i class="it">S/T</i></figcaption>
      </figure>
      <div>
        <p class="kicker lbl">La galería</p>
        <h2>“For those who love innovation and contemporary art”</h2>
        <div class="prose">
          <p class="lead">At Ninoska Huerta Gallery, we celebrate creativity, movement, and vision. Our space in Coral Gables, Miami, is dedicated to showcasing groundbreaking works in constructivism, abstraction, and kinetic art—featuring both iconic masters and bold new voices from Latin America and beyond.</p>
          <p>Here, innovation meets legacy. Discover the vibrant visual language of renowned artists such as Carlos Cruz-Diez and Jesús Soto, alongside the daring proposals of emerging talents who are redefining the boundaries of contemporary art.</p>
          <a class="tlink" href="/acerca-de/">Leer más →</a>
        </div>
      </div>
    </div>
  </section>
  <section class="s alt" aria-labelledby="feat">
    <div class="wrap grid2 wide">
      <div class="feat-imgs" aria-label="Beyond the Visible, obras de Marcos Marín">{beyond}</div>
      <div>
        <p class="kicker lbl"><span class="dot" aria-hidden="true"></span>Destacado · Marcos Marín</p>
        <h2 id="feat">Beyond the Visible<br><span class="it" style="font-size:.55em;font-weight:400">The Symbol as Visual Energy</span></h2>
        <div class="prose">
          <p>The exhibition presented by Ninoska Huerta Gallery offers an opportunity to enter a lesser known yet extraordinarily revealing territory within Marcos Marín’s artistic research.</p>
          <p>In 2010, the artist turned his attention to the ancient symbols associated with Feng Shui, a millennia-old Chinese tradition rooted in the pursuit of harmony between the human being, space, and the forces that move through it.</p>
          <p>Marín does not approach these symbols as ornamental elements or merely as cultural representations. He perceives them as forms charged with meaning and energy, subjecting them to a process of visual transformation. The symbol becomes structure; structure becomes rhythm; and rhythm becomes movement.</p>
          <p>On paper, Marín reconstructs these signs through a rigorous geometric organization, creating compositions in which symmetry, repetition, and optical interaction generate a distinctive sense of vibration.</p>
          <p>In this series, the eye does not merely observe: it participates.</p>
          <p>Each work establishes a dialogue between what we recognize and what our perception can barely decipher. The forms seem to open, shift, and multiply, as if the energy contained within the symbol were finding a new dimension through the language of Op Art.</p>
          <p>Thus, the ancient and the contemporary converge in a space where the symbol becomes a visual experience and geometry transforms into energy.</p>
          <p class="sig">Ninoska Huerta</p>
        </div>
        <div class="ctas" style="margin-top:22px"><a class="btn dark" href="/artistas/marcos-marin-art/">Marcos Marín</a><a class="btn line" href="/tienda/?linea={quote('Marcos Marín')}">Ver sus obras</a></div>
      </div>
    </div>
  </section>
  <section class="s" aria-labelledby="oa">
    <div class="wrap">
      <div class="sec-head"><h2 id="oa">Nuestros artistas</h2><a class="tlink" href="/artistas/">Todos los artistas →</a></div>
      <div class="agrid">{home_artists}</div>
      <div class="feature-box" style="margin-top:56px">
        <div class="grid2">
          {picture(content.get("amalia"), "Retrato de Amalia Pereira", media, (800, 600), sizes="(max-width: 980px) 100vw, 50vw", style="aspect-ratio:4/3")}
          <div><p class="kicker lbl">Artista destacada</p><h3 style="font-size:34px;font-weight:300;margin-bottom:4px">Amalia Pereira</h3><p class="it" style="font-size:22px;margin:0 0 18px">Poetics of the Intimate Fragment</p>
          <div class="prose"><p>Amalia Pereira explores collage as a poetic language, integrating photography, drawing, and diverse elements into delicate small-format compositions. With a subtle surrealist sensibility, her work intertwines memory, nature, and the unconscious, creating intimate images that invite contemplation and reveal the beauty within the fragment.</p></div>
          <a class="tlink" href="/artistas/amalia-pereira-art/">Ver artista →</a></div>
        </div>
      </div>
    </div>
  </section>
  <section class="s alt" aria-labelledby="ex">
    <div class="wrap">
      <div class="sec-head"><h2 id="ex">Exposiciones</h2><a class="tlink" href="/exposiciones/">Todas las exposiciones →</a></div>
      <div class="cards3">{home_exh}</div>
    </div>
  </section>
  <section class="s" aria-labelledby="st">
    <div class="wrap">
      <div class="sec-head"><div><p class="kicker lbl">De la tienda</p><h2 id="st" style="margin-bottom:10px">Visita la tienda</h2><p style="margin:0;color:var(--muted)">Hay obras y ediciones que pueden interesarte.</p></div><a class="btn dark" href="/tienda/">Ir a la tienda</a></div>
      <div class="products">{home_products}</div>
    </div>
  </section>
  <section class="s alt" aria-labelledby="bl">
    <div class="wrap">
      <div class="sec-head"><h2 id="bl">Lo último del blog</h2><a class="tlink" href="/blog/">Todas las entradas →</a></div>
      <div class="cards3">{home_posts}</div>
    </div>
  </section>
  <section class="s" aria-labelledby="vd">
    <div class="wrap">
      <div class="sec-head"><div><p class="kicker lbl">Vídeos</p><h2 id="vd" style="margin:0">Síguenos</h2></div><a class="tlink" href="https://www.youtube.com/channel/UCAxbyWPj5At8foQhLUB0moA">Canal de YouTube →</a></div>
      <div class="vgrid">{home_videos}</div>
    </div>
  </section>''',
    })

    about_text = [block for block in content['about'] if block[0] not in ('img', 'video')]
    about_media_blocks = [block for block in content['about'] if block[0] in ('img', 'video')]
    about_desc = 'Ninoska Huerta, conocedora, coleccionista, asesora y marchante. Ninoska Huerta Gallery, 290 Miracle Mile, Coral Gables. Solo con cita previa.'
    add({
        'path': '/acerca-de/',
        'title': 'Ninoska Huerta · Ninoska Huerta Gallery',
        'description': about_desc,
        'current': 'about',
        'og_src': content.get('aboutPortrait'),
        'og_alt': 'Retrato de Ninoska Huerta',
        'about': NINOSKA_ID,
        'crumbs': [('Inicio', '/'), ('Acerca de', '/acerca-de/')],
        'extra': [ninoska_node(content, media)],
        'main': f'''<div class="wrap page-head"><p class="kicker lbl">Acerca de</p><h1>Ninoska Huerta</h1><p class="lbl" style="color:var(--ink)">Connoisseur, Collector, Advisor &amp; Private Art Dealer</p></div>
  <div class="wrap" style="padding-bottom:96px">
    <div class="grid2 wide">
      {picture(content.get("aboutPortrait"), "Retrato de Ninoska Huerta", media, (800, 1000), eager=True, sizes="(max-width: 980px) 100vw, 420px", cls="")}
      <div><div class="prose">{render_blocks(about_text, media)}</div>
        <div class="ctas" style="margin-top:8px"><a class="btn dark" href="/contacto/">Reservar una visita</a><a class="btn line" href="/tienda/soto-y-la-escritura/">Soto y la Escritura</a></div></div>
    </div>
    <div style="margin-top:64px">{render_blocks(about_media_blocks, media, use_alt=True, grid=True)}</div>
  </div>''',
    })
    # The about portrait uses a sticky frame in the previous template. Restore that presentation.
    pages[-1]['main'] = pages[-1]['main'].replace(
        'class="img"',
        'class="img" style="aspect-ratio:4/5;position:sticky;top:100px"',
        1,
    )

    add({
        'path': '/artistas/',
        'title': 'Artistas · Ninoska Huerta Gallery',
        'description': 'Artistas de Ninoska Huerta Gallery: arte cinético, óptico y constructivo. Coral Gables, Miami.',
        'current': 'artists',
        'og_src': listed[0].get('portrait') if listed else default_og,
        'og_alt': artist_alt(listed[0]['name']) if listed else 'Ninoska Huerta Gallery',
        'about': GALLERY_ID,
        'crumbs': [('Inicio', '/'), ('Artistas', '/artistas/')],
        'extra': [item_list('Artistas', [(artist['name'], '/artistas/' + artist['id'] + '/') for artist in listed])],
        'main': f'''<div class="wrap page-head"><p class="kicker lbl">Artistas</p><h1>Artistas</h1></div>
  <div class="wrap" style="padding-bottom:96px"><div class="agrid">{''.join(acard(artist, media) for artist in listed)}</div></div>''',
    })

    for index, artist in enumerate(listed):
        bio, work = split_artist(artist['blocks'])
        seq = listed
        own_products = [product for product in products if product['artist'] == artist['name']]
        bio_text = first_paragraph(artist['blocks'])
        description = clamp(bio_text or (subtitle(artist) + '. Artista en Ninoska Huerta Gallery, Coral Gables.'))
        extra = [artist_node(artist, media)]
        extra.extend(artwork_node(product, by_name, media) for product in own_products)
        shop_link = f'<a class="btn line" href="/tienda/?linea={quote(artist["name"])}">Ver en la tienda</a>' if own_products else ''
        work_html = f'<section class="rich" style="margin-top:48px"><h2>Obra destacada</h2>{render_blocks(work, media, artist=artist["name"], grid=True)}</section>' if work else ''
        prod_html = ''
        if own_products:
            prod_html = (
                '<section style="margin-top:56px"><div class="sec-head"><h2 style="margin:0">Disponible en la tienda</h2>'
                f'<a class="tlink" href="/tienda/?linea={quote(artist["name"])}">Ver todo →</a></div>'
                f'<div class="products">{"".join(pcard(product, media) for product in own_products)}</div></section>'
            )
        add({
            'path': '/artistas/' + artist['id'] + '/',
            'title': f'{artist["name"]} · Ninoska Huerta Gallery',
            'description': description,
            'current': 'artists',
            'og_type': 'profile',
            'og_src': artist.get('portrait') or default_og,
            'og_alt': artist_alt(artist['name']),
            'about': ORIGIN + '/artistas/' + artist['id'] + '/#persona',
            'crumbs': [('Inicio', '/'), ('Artistas', '/artistas/'), (artist['name'], '/artistas/' + artist['id'] + '/')],
            'prev': '/artistas/' + seq[index - 1]['id'] + '/' if index else None,
            'next': '/artistas/' + seq[index + 1]['id'] + '/' if index + 1 < len(seq) else None,
            'extra': extra,
            'main': (
                '<div class="wrap" style="padding-bottom:96px">'
                '<p style="padding-top:28px;margin:0"><a class="tlink" href="/artistas/">← Todos los artistas</a></p>'
                '<header class="artist-head">'
                + picture(artist.get('portrait'), artist_alt(artist['name']), media, (800, 800), eager=True, sizes='(max-width: 980px) 80vw, 320px')
                + '<div><p class="lbl" style="color:var(--muted)">Artista</p><h1>' + esc(artist['name']) + '</h1>'
                + (f'<p class="mono" style="margin:0;color:var(--muted)">{esc(subtitle(artist))}</p>' if subtitle(artist) else '')
                + f'<div class="ctas" style="margin-top:22px"><a class="btn dark" href="/contacto/">Consultar por este artista</a>{shop_link}</div></div></header>'
                + f'<div class="prose rich">{render_blocks(bio, media, artist=artist["name"])}</div>'
                + work_html + prod_html
                + pager(seq, index, lambda item: '/artistas/' + item['id'] + '/', 'artistas')
                + '</div>'
            ),
        })

    unlisted = [artist for artist in artists if not artist.get('listed')]
    for artist in unlisted:
        bio, work = split_artist(artist['blocks'])
        add({
            'path': '/artistas/' + artist['id'] + '/',
            'title': f'{artist["name"]} · Ninoska Huerta Gallery',
            'description': clamp(first_paragraph(artist['blocks']) or artist['name']),
            'current': 'artists',
            'robots': 'noindex, follow',
            'og_src': artist.get('portrait') or default_og,
            'og_alt': artist_alt(artist['name']),
            'about': ORIGIN + '/artistas/' + artist['id'] + '/#persona',
            'crumbs': [('Inicio', '/'), ('Artistas', '/artistas/'), (artist['name'], '/artistas/' + artist['id'] + '/')],
            'extra': [artist_node(artist, media)],
            'main': (
                '<div class="wrap" style="padding-bottom:96px">'
                '<p style="padding-top:28px;margin:0"><a class="tlink" href="/artistas/">← Todos los artistas</a></p>'
                '<header class="artist-head">'
                + picture(artist.get('portrait'), artist_alt(artist['name']), media, (800, 800), eager=True, sizes='(max-width: 980px) 80vw, 320px')
                + f'<div><p class="lbl" style="color:var(--muted)">Artista</p><h1>{esc(artist["name"])}</h1></div></header>'
                + f'<div class="prose rich">{render_blocks(bio, media, artist=artist["name"])}</div>'
                + (f'<section class="rich" style="margin-top:48px"><h2>Obra destacada</h2>{render_blocks(work, media, artist=artist["name"], grid=True)}</section>' if work else '')
                + '</div>'
            ),
        })

    exh_video = ''
    if content.get('exhVideo'):
        exh_video = '<div class="vid-intro">' + vbox(content['exhVideo'][0], 'Exposiciones') + '</div>'
    add({
        'path': '/exposiciones/',
        'title': 'Exposiciones · Ninoska Huerta Gallery',
        'description': 'Exposiciones de Ninoska Huerta Gallery en Coral Gables, Miami.',
        'current': 'exhibitions',
        'og_src': (exhibitions[0].get('hero') or exhibitions[0].get('thumb')) if exhibitions else default_og,
        'og_alt': tidy(exhibitions[0]['title']) if exhibitions else 'Exposiciones',
        'about': GALLERY_ID,
        'crumbs': [('Inicio', '/'), ('Exposiciones', '/exposiciones/')],
        'extra': [item_list('Exposiciones', [(tidy(post['title']), post_path(post)) for post in exhibitions])],
        'main': f'''<div class="wrap page-head"><p class="kicker lbl">Exposiciones</p><h1>Exposiciones</h1></div>
  <div class="wrap" style="padding-bottom:96px">{exh_video}<div class="cards3">{''.join(ccard(post, media, recent=(index == 0), heading="h2") for index, post in enumerate(exhibitions))}</div></div>''',
    })
    add({
        'path': '/blog/',
        'title': 'Blog · Ninoska Huerta Gallery',
        'description': 'Artículos del blog de Ninoska Huerta Gallery.',
        'current': 'blog',
        'og_src': (blog[0].get('hero') or blog[0].get('thumb')) if blog else default_og,
        'og_alt': tidy(blog[0]['title']) if blog else 'Blog',
        'about': GALLERY_ID,
        'crumbs': [('Inicio', '/'), ('Blog', '/blog/')],
        'extra': [item_list('Blog', [(tidy(post['title']), post_path(post)) for post in blog])],
        'main': f'''<div class="wrap page-head"><p class="kicker lbl">Blog</p><h1>Blog</h1></div>
  <div class="wrap" style="padding-bottom:96px"><div class="cards3">{''.join(ccard(post, media, heading="h2") for post in blog)}</div></div>''',
    })

    def add_posts(posts, section, current, crumb_name):
        for index, post in enumerate(posts):
            excerpt = tidy(post.get('excerpt') or '')
            hero = ''
            if post.get('hero'):
                hero = '<div class="post-hero">' + picture(post['hero'], tidy(post['title']), media, (1600, 900), eager=True, sizes='(max-width: 900px) 100vw, 900px') + '</div>'
            add({
                'path': post_path(post),
                'title': f'{tidy(post["title"])} · Ninoska Huerta Gallery',
                'description': clamp(excerpt or tidy(post['title'])),
                'current': current,
                'og_type': 'article',
                'og_src': post.get('hero') or post.get('thumb') or default_og,
                'og_alt': tidy(post['title']),
                'about': GALLERY_ID,
                'crumbs': [('Inicio', '/'), (crumb_name, section), (tidy(post['title']), post_path(post))],
                'prev': post_path(posts[index - 1]) if index else None,
                'next': post_path(posts[index + 1]) if index + 1 < len(posts) else None,
                'extra': [article_node(post, media)],
                'main': (
                    '<div class="wrap" style="padding-bottom:96px">'
                    f'<p style="padding-top:28px;margin:0"><a class="tlink" href="{section}">← {esc(crumb_name if current == "blog" else "Todas las exposiciones")}</a></p>'
                    f'<header class="post-head"><p class="lbl" style="color:var(--muted)">{esc("Blog" if current == "blog" else "Exposición")} · {esc(fdate(post["date"]))}</p><h1>{esc(tidy(post["title"]))}</h1></header>'
                    + hero
                    + f'<div class="prose rich">{render_blocks(post["blocks"], media, fallback=tidy(post["title"]))}</div>'
                    + '<div class="ctas" style="margin-top:36px"><a class="btn dark" href="/contacto/">Reservar una visita</a></div>'
                    + pager(posts, index, post_path, 'entradas' if current == 'blog' else 'exposiciones')
                    + '</div>'
                ),
            })

    add_posts(exhibitions, '/exposiciones/', 'exhibitions', 'Exposiciones')
    add_posts(blog, '/blog/', 'blog', 'Blog')

    shop_desc = 'Obras originales sobre papel y el libro Soto y la Escritura. Precios en USD. Ninoska Huerta Gallery, Coral Gables.'
    add({
        'path': '/tienda/',
        'title': 'Tienda · Ninoska Huerta Gallery',
        'description': shop_desc,
        'current': 'shop',
        'og_src': products[0]['imgs'][0],
        'og_alt': work_alt(products[0]),
        'about': GALLERY_ID,
        'crumbs': [('Inicio', '/'), ('Tienda', '/tienda/')],
        'extra': works,
        'main': f'''<div class="wrap page-head"><p class="kicker lbl">Tienda</p><h1>Tienda</h1><p>Obras originales sobre papel y el libro <i class="it">Soto y la Escritura</i>.</p></div>
  <div class="wrap" style="padding-bottom:96px">
    <div class="filters" role="group" aria-label="Filtrar obras">
      <button class="chip" type="button" data-f="all" aria-pressed="true">Todas</button>
      <button class="chip" type="button" data-f="Marcos Marín" aria-pressed="false">Marcos Marín</button>
      <button class="chip" type="button" data-f="Karim Borjas" aria-pressed="false">Karim Borjas</button>
      <button class="chip" type="button" data-f="Books" aria-pressed="false">Libros</button>
      <div class="sort"><label class="lbl" for="sort">Ordenar</label>
        <select id="sort"><option value="feat">Destacadas</option><option value="asc">Precio: menor a mayor</option><option value="desc">Precio: mayor a menor</option><option value="az">Título: A–Z</option></select></div>
    </div>
    <p class="mono" id="pcount" style="margin:0 0 18px">{len(products)} obras</p>
    <div class="products" data-products-all>{''.join(pcard(product, media) for product in products)}</div>
  </div>''',
    })

    for product in products:
        related = [item for item in products if item['line'] == product['line'] and item['id'] != product['id']][:4]
        specs = dict(product['specs'])
        bits = [work_alt(product)]
        if specs.get('Medium'):
            bits.append(specs['Medium'])
        if specs.get('Year'):
            bits.append(specs['Year'])
        if specs.get('Dimensions'):
            bits.append(specs['Dimensions'])
        bits.append(money(product['price']) + ' USD')
        thumbs = ''
        if len(product['imgs']) > 1:
            buttons = []
            for index, src in enumerate(product['imgs']):
                buttons.append(
                    f'<button type="button" data-thumb="{index}" data-src="{esc(display_src(src, media))}" data-alt="{esc(work_alt(product))}" aria-current="{str(index == 0).lower()}" aria-label="Imagen {index + 1} de {esc(tidy(product['title']))}">'
                    + picture(src, work_alt(product), media, (72, 72), sizes='72px')
                    + '</button>'
                )
            thumbs = '<div class="thumbs">' + ''.join(buttons) + '</div>'
        artist_link = esc(line_label(product['artist'] if product['artist'] != 'Book' else 'Libro'))
        known = by_name.get(product['artist'])
        if known:
            artist_link = f'<a href="/artistas/{esc(known["id"])}/">{esc(product["artist"])}</a>'
        elif product['artist'] == 'Book':
            artist_link = 'Libro'
        related_html = ''
        if related:
            related_html = (
                f'<div style="grid-column:1/-1;margin-top:40px"><h2 style="font-size:32px">Más de {esc(line_label(product["line"]))}</h2>'
                f'<div class="products">{"".join(pcard(item, media) for item in related)}</div></div>'
            )
        add({
            'path': '/tienda/' + product['id'] + '/',
            'title': f'{tidy(product["title"])} · Ninoska Huerta Gallery',
            'description': clamp('. '.join(bits)),
            'current': 'shop',
            'og_type': 'product',
            'og_src': product['imgs'][0],
            'og_alt': work_alt(product),
            'price': product['price'],
            'about': ORIGIN + '/tienda/' + product['id'] + ('/#libro' if product['id'] == 'soto-y-la-escritura' else '/#obra'),
            'crumbs': [('Inicio', '/'), ('Tienda', '/tienda/'), (tidy(product['title']), '/tienda/' + product['id'] + '/')],
            'extra': [artwork_node(product, by_name, media)],
            'main': (
                '<div class="wrap"><div class="product">'
                + '<div class="gallery">'
                + picture(product['imgs'][0], work_alt(product), media, (1200, 1200), eager=True, sizes='(max-width: 980px) 100vw, 50vw', cls='main contain')
                + thumbs + '</div><div>'
                + f'<p class="crumbs"><a href="/tienda/">Tienda</a> / <a href="/tienda/?linea={quote(product["line"])}">{esc(line_label(product["line"]))}</a></p>'
                + f'<p class="lbl">{artist_link}</p><h1 class="it" style="font-family:var(--f-s);font-style:italic;font-weight:300">{esc(tidy(product["title"]))}</h1>'
                + f'<p class="price">{money(product["price"])}</p>'
                + f'<dl class="specs">{spec_rows(product)}</dl>'
                + '<div class="buy"><div class="qty"><button type="button" data-q="-1" aria-label="Reducir cantidad">−</button>'
                + '<input id="pq" type="number" min="1" max="10" value="1" aria-label="Cantidad">'
                + '<button type="button" data-q="1" aria-label="Aumentar cantidad">+</button></div>'
                + f'<button class="btn dark" type="button" data-add="{esc(product["id"])}" data-qty-from="#pq">Añadir al carrito</button></div>'
                + '<p class="note">¿Preguntas sobre esta obra? <a href="/contacto/">Contacta con la galería</a> o llama al +1 305 588 1231. Visitas solo con cita previa.</p>'
                + '</div>' + related_html + '</div></div>'
            ),
        })

    add({
        'path': '/contacto/',
        'title': 'Contacto · Ninoska Huerta Gallery',
        'description': '290 Miracle Mile, Coral Gables, FL 33134, EE. UU. Solo con cita previa. Teléfono +1 305 588 1231. Correo ninoskahuerta@gmail.com.',
        'current': 'contact',
        'og_src': default_og,
        'og_alt': 'Retrato de Ninoska Huerta',
        'about': GALLERY_ID,
        'crumbs': [('Inicio', '/'), ('Contacto', '/contacto/')],
        'extra': [ninoska_node(content, media)],
        'main': '''<div class="wrap page-head"><p class="kicker lbl"><span class="dot" aria-hidden="true"></span>Solo con cita previa</p><h1>Contacto</h1><p>Escríbenos y te ayudamos a elegir una obra.</p></div>
  <div class="wrap contact">
    <div class="cinfo">
      <dl>
        <div><dt>Visita</dt><dd><a href="https://www.google.com/maps/search/?api=1&amp;query=290+Miracle+Mile+Coral+Gables+FL+33134">290 Miracle Mile<br>Coral Gables, FL 33134, USA</a></dd></div>
        <div><dt>Horario</dt><dd>Solo con cita previa</dd></div>
        <div><dt>Teléfono</dt><dd><a href="tel:+13055881231">+1 305 588 1231</a><button class="copy" type="button" data-copy="+1 305 588 1231">Copiar</button></dd></div>
        <div><dt>Correo</dt><dd><a href="mailto:ninoskahuerta@gmail.com">ninoskahuerta@gmail.com</a><button class="copy" type="button" data-copy="ninoskahuerta@gmail.com">Copiar</button></dd></div>
        <div><dt>Síguenos</dt><dd style="font-size:18px"><a href="https://www.instagram.com/galleryninoskahuerta/">Instagram</a> · <a href="https://www.facebook.com/NinoskaHuertaGallery">Facebook</a> · <a href="https://www.youtube.com/channel/UCAxbyWPj5At8foQhLUB0moA">YouTube</a></dd></div>
      </dl>
    </div>
    <form class="cform" id="cform" novalidate>
      <div class="field"><label for="cname">Tu nombre (obligatorio)</label><input id="cname" name="name" autocomplete="name" required><span class="err" hidden>Escribe tu nombre.</span></div>
      <div class="field"><label for="cemail">Tu correo (obligatorio)</label><input id="cemail" name="email" type="email" autocomplete="email" required><span class="err" hidden>Escribe un correo al que podamos responder, como nombre@ejemplo.com.</span></div>
      <div class="field"><label for="csubj">Asunto</label><input id="csubj" name="subject" placeholder="Una visita, una obra, asesoría…"></div>
      <div class="field"><label for="cmsg">Tu mensaje</label><textarea id="cmsg" name="message"></textarea></div>
      <div><button class="btn dark" type="submit">Enviar mensaje</button></div>
      <p class="formmsg" id="cformMsg" hidden></p>
    </form>
  </div>''',
    })

    terms_desc = 'Términos y condiciones de uso del sitio de Ninoska Huerta Gallery.'
    add({
        'path': '/terminos/',
        'title': 'Términos y condiciones · Ninoska Huerta Gallery',
        'description': terms_desc,
        'current': '',
        'og_src': default_og,
        'og_alt': 'Ninoska Huerta Gallery',
        'about': GALLERY_ID,
        'crumbs': [('Inicio', '/'), ('Términos y condiciones', '/terminos/')],
        'main': f'''<div class="wrap page-head"><p class="kicker lbl">Legal</p><h1>Términos y condiciones</h1></div>
  <div class="wrap" style="padding-bottom:96px"><div class="prose rich">{render_blocks(content["terms"], media)}</div></div>''',
    })

    add({
        'path': '/404.html',
        'title': 'Página no encontrada · Ninoska Huerta Gallery',
        'description': 'Esa dirección no está en Ninoska Huerta Gallery.',
        'current': '',
        'robots': 'noindex, follow',
        'og_src': default_og,
        'og_alt': 'Ninoska Huerta Gallery',
        'about': GALLERY_ID,
        'main': '''<div class="wrap page-head"><p class="kicker lbl">404</p><h1>Página no encontrada</h1><p>La dirección no corresponde a una página de la galería.</p><p style="margin-top:24px"><a class="btn dark" href="/">Volver al inicio</a></p></div>''',
    })

    written = [write_page(spec, og_cache) for spec in pages]
    catalog = [{
        'id': product['id'],
        'title': tidy(product['title']),
        'artist': 'Libro' if product['artist'] == 'Book' else product['artist'],
        'price': product['price'],
        'img': display_src(product['imgs'][0], media),
        'line': product['line'],
    } for product in products]
    post_paths = {post['id']: post_path(post) for post in content['posts']}
    (ROOT / 'assets' / 'catalog.js').write_text(
        'var PRODUCTS = ' + json.dumps(catalog, ensure_ascii=False) + ';\n'
        'var POST_PATHS = ' + json.dumps(post_paths, ensure_ascii=False) + ';\n'
    )
    write_robots_and_sitemap(pages)
    write_llms(content, products, listed, exhibitions, blog)
    write_favicon()
    validate(written)
    index_size = (ROOT / 'index.html').stat().st_size
    print(f'pages {len(written)} index {index_size} bytes')


def write_robots_and_sitemap(pages):
    robots = '''# Ninoska Huerta Gallery. El rastreo está permitido, también para los buscadores de IA indicados.
User-agent: *
Allow: /

User-agent: GPTBot
Allow: /

User-agent: ChatGPT-User
Allow: /

User-agent: OAI-SearchBot
Allow: /

User-agent: ClaudeBot
Allow: /

User-agent: anthropic-ai
Allow: /

User-agent: PerplexityBot
Allow: /

User-agent: Perplexity-User
Allow: /

User-agent: Google-Extended
Allow: /

User-agent: Applebot-Extended
Allow: /

Sitemap: https://ninoskahuertagallery.vercel.app/sitemap.xml
'''
    (ROOT / 'robots.txt').write_text(robots)
    urls = []
    for spec in pages:
        if spec['path'] == '/404.html':
            continue
        if 'noindex' in (spec.get('robots') or ''):
            continue
        loc = ORIGIN + spec['path']
        urls.append('  <url><loc>' + esc(loc) + '</loc></url>')
    xml = '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' + '\n'.join(urls) + '\n</urlset>\n'
    (ROOT / 'sitemap.xml').write_text(xml)


def write_llms(content, products, listed, exhibitions, blog):
    lines = [
        '# Ninoska Huerta Gallery',
        '',
        '> Galería en Coral Gables, Miami, dedicada al arte cinético, óptico y constructivo de América Latina, de los maestros a las nuevas voces. Visitas solo con cita previa. Este resumen usa solo datos publicados en el propio sitio.',
        '',
        '## Contacto',
        '- Nombre: Ninoska Huerta Gallery',
        '- Dirección: 290 Miracle Mile, Coral Gables, FL 33134, USA',
        '- Horario publicado: solo con cita previa',
        '- Teléfono: +1 305 588 1231',
        '- Correo: ninoskahuerta@gmail.com',
        '- Instagram: https://www.instagram.com/galleryninoskahuerta/',
        '- Facebook: https://www.facebook.com/NinoskaHuertaGallery',
        '- YouTube: https://www.youtube.com/channel/UCAxbyWPj5At8foQhLUB0moA',
        '- Sitio: https://ninoskahuertagallery.vercel.app/',
        '- Dominio citado en el pie: ninoskahuertagallery.com',
        '',
        '## Ninoska Huerta',
        '- Oficio publicado en la página: Connoisseur, Collector, Advisor & Private Art Dealer',
        '- El texto biográfico dice que se graduó como interiorista en Iles Academy (Caracas), que siguió estudios de arte en la Universidad Central de Venezuela, que abrió una galería en Venezuela en 1994, que se estableció en Miami en 2006 y que en 2020 presentó “Art in Motion” en 290 Miracle Mile.',
        '- Editó el libro Soto y la Escritura (publicado en 2000; ensayo de Arturo Uslar Pietri; texto del artista de Jesús Rafael Soto; 160 páginas; español).',
        '- Ficha: https://ninoskahuertagallery.vercel.app/acerca-de/',
        '',
        '## Páginas',
        '- Inicio: https://ninoskahuertagallery.vercel.app/',
        '- Acerca de: https://ninoskahuertagallery.vercel.app/acerca-de/',
        '- Artistas: https://ninoskahuertagallery.vercel.app/artistas/',
        '- Exposiciones: https://ninoskahuertagallery.vercel.app/exposiciones/',
        '- Tienda: https://ninoskahuertagallery.vercel.app/tienda/',
        '- Blog: https://ninoskahuertagallery.vercel.app/blog/',
        '- Contacto: https://ninoskahuertagallery.vercel.app/contacto/',
        '- Términos: https://ninoskahuertagallery.vercel.app/terminos/',
        '',
        '## Artistas en el listado público',
    ]
    for artist in listed:
        sub = subtitle(artist)
        suffix = f' — {sub}' if sub else ''
        lines.append(f'- {artist["name"]}{suffix}: {ORIGIN}/artistas/{artist["id"]}/')
    lines += ['', '## Tienda (precios publicados, USD)']
    for product in products:
        specs = dict(product['specs'])
        bits = [tidy(product['title']), 'Libro' if product['artist'] == 'Book' else product['artist'], money(product['price']) + ' USD']
        if specs.get('Medium'):
            bits.append(specs['Medium'])
        if specs.get('Year'):
            bits.append(specs['Year'])
        if specs.get('Dimensions'):
            bits.append(specs['Dimensions'])
        lines.append(f'- {", ".join(bits)}: {ORIGIN}/tienda/{product["id"]}/')
    lines += ['', '## Exposiciones (fecha de la entrada)']
    for post in exhibitions:
        lines.append(f'- {post["date"]} — {tidy(post["title"])}: {ORIGIN}{post_path(post)}')
    lines += ['', '## Blog (fecha de la entrada)']
    for post in blog:
        lines.append(f'- {post["date"]} — {tidy(post["title"])}: {ORIGIN}{post_path(post)}')
    lines += [
        '',
        '## Qué no consta en el sitio',
        '- Coordenadas, horario semanal, fecha de fundación única, premios, ISBN del libro y disponibilidad de stock.',
        '- Identificadores de Wikidata u otros sameAs de los artistas.',
        '- Autor explícito de cada artículo. La fecha de una entrada no se trata como inicio de exposición.',
        '- Títulos individuales de las imágenes de la serie Beyond the Visible: en la portada comparten el pie “Marcos Marín, Beyond the Visible”.',
        '- Una ficha de artista para Karim Borjas, aunque sus obras están en la tienda.',
        '- Mario Villasierra está en los datos con listed en falso y no aparece en la cuadrícula pública. Su ficha existe y lleva noindex.',
        '- La imagen con pie “Peter Monahan, S/T” usa el mismo archivo que el retrato de portada de Ninoska Huerta. Hay que confirmar cuál corresponde.',
        '- La mayoría de las imágenes de obras dentro de las fichas sigue alojada en ninoskahuertagallery.com/wp-content. El detalle está en media/manifest.json.',
        '- Los textos largos (biografías, ensayos, términos) siguen en su idioma original, en general inglés. La interfaz visible usa español.',
        '',
    ]
    (ROOT / 'llms.txt').write_text('\n'.join(lines))


def write_favicon():
    svg = ROOT / 'assets/logos/nh-logo-short.svg'
    png = Path('/tmp/nh-favicon-256.png')
    subprocess.check_call(['rsvg-convert', '-w', '256', '-h', '256', str(svg), '-o', str(png)])
    image = Image.open(png).convert('RGBA')
    image.save(ROOT / 'favicon.ico', format='ICO', sizes=[(16, 16), (32, 32), (48, 48)])


def validate(paths):
    local_missing = []
    for path in paths:
        text = path.read_text()
        if text.count('<h1') != 1:
            raise SystemExit(f'{path} tiene {text.count("<h1")} h1')
        if '<html lang="es">' not in text:
            raise SystemExit(f'{path} sin lang=es')
        for needle in ('rel="canonical"', 'property="og:title"', 'property="og:description"', 'property="og:image"', 'name="twitter:card"', 'name="description"', 'name="robots"'):
            if needle not in text:
                raise SystemExit(f'{path} sin {needle}')
        match = re.search(r'<script type="application/ld\+json">(.*?)</script>', text)
        if not match:
            raise SystemExit(f'{path} sin JSON-LD')
        data = json.loads(match.group(1))
        if data.get('@context') != 'https://schema.org' or not data.get('@graph'):
            raise SystemExit(f'{path} JSON-LD incompleto')
        for node in data['@graph']:
            if '@type' not in node:
                raise SystemExit(f'{path} nodo sin @type')
        refs = re.findall(r'(?:src|href)="(/[^"]+)"', text)
        for srcset in re.findall(r'srcset="([^"]+)"', text):
            refs.extend(part.strip().split(' ')[0] for part in srcset.split(','))
        for ref in refs:
            if ref.startswith('//') or ref.startswith('/http'):
                continue
            file_path = ROOT / ref.split('?', 1)[0].lstrip('/')
            if not file_path.exists():
                local_missing.append(f'{path.name}: {ref}')
    if local_missing:
        preview = '\n'.join(local_missing[:12])
        raise SystemExit(f'Faltan {len(local_missing)} archivos locales\n{preview}')
    print('JSON-LD OK', len(paths), 'páginas')


if __name__ == '__main__':
    build()

import json, re, html, sys
D = json.load(open(sys.argv[1]))
P = D['pages']
UP = 'https://ninoskahuertagallery.com/wp-content/uploads/'
DATE_RE = re.compile(r'^[A-Z][a-z]{2} \d{1,2}, \d{4} \|')

def norm(u):
    u = re.sub(r'\.(jpe?g|png|gif)\.webp$', r'.\1', u, flags=re.I)
    u = re.sub(r'-\d{2,4}x\d{2,4}(?=\.(jpe?g|png|gif|webp)$)', '', u, flags=re.I)
    return u.replace(UP, '~U/')

def clean(s):
    return html.unescape(s).replace(' ', ' ').strip()

def trim_related(blocks):
    for i in range(len(blocks) - 2):
        if blocks[i][0] == 'img' and blocks[i+1][0] == 'h2' and blocks[i+2][0] == 'p' and DATE_RE.match(blocks[i+2][1]):
            return blocks[:i]
    return blocks

def tidy(blocks, drop_texts=()):
    out = []
    drops = {t.lower().strip() for t in drop_texts if t}
    for b in blocks:
        k = b[0]
        if k == 'img':
            out.append(['img', norm(b[1]), clean(b[2]) if len(b) > 2 else ''])
        elif k == 'video':
            out.append(['video', b[1]])
        else:
            t = clean(b[1])
            if not t: continue
            if t.lower().rstrip('.') in drops: continue
            if k in ('h5', 'cap') and out and out[-1][0] == 'img' and len(out[-1]) == 3 and 'cap' not in out[-1]:
                out[-1] = ['img', out[-1][1], out[-1][2], t]; continue
            if k in ('h1', 'h2') and t.upper() == 'FEATURED WORK':
                if out and out[-1] == ['h3', 'Work']: out.pop()
                out.append(['h2', 'Featured work']); continue
            if k == 'h3' and t == 'Work': out.append(['h3', 'Work']); continue
            out.append([k if k in ('h1','h2','h3','h4','h5','h6','p','li','blockquote') else 'p', t])
    # remove a dangling 'Work' h3
    out = [b for b in out if b != ['h3', 'Work']]
    # dedupe identical consecutive paragraphs
    res = []
    for b in out:
        if res and b == res[-1]: continue
        res.append(b)
    return res

FIX_TITLE = {
    '/11333-volviendo-a-mi/': '11:33 — Volviendo a Mí',
    '/geomtry-in-monochrome-conversation/': '“Geometry in Monochrome” – Conversation',
}

# ---------- artists ----------
ART = [
 ['Adriana Dorta','adriana-dorta-art'],['Carlos Cruz-Diez','carlos-cruz-diez-art'],['Ivonne Ferrer','ivonne-ferrer'],['Jorge Salas','jorge-salas-2'],
 ['Lynn Kislak','lynn-kislak-art'],['Rubem Robierb','rubem-robierb-art'],['Víctor Valera','victor-valera-art'],['Alain Arias-Misson','alain-arias-misson'],
 ['Carlos Estévez','carlos-estevez-art'],['Jesús Rafael Soto','jesus-rafael-soto-art'],['Ludwig Wilding','ludwig-wilding-art'],['Marcos Marín','marcos-marin-art'],
 ['Saverio Cecere','saverio-cecere-art'],['William Barboza','william-barboza'],['Amalia Pereira','amalia-pereira-art'],['Darío Pérez-Flores','dario-perez-flores-art'],
 ['Jorge Blanco','jorge-blanco-art'],['Luis Gómez R','luis-gomez-r-art'],['Paul Amundaraín','paul-amundarain-art'],['Speedy Graphito','speedy-graphito-art'],
 ['Carlos Anzola','carlos-anzola-art'],['Eduardo Orozco','eduardo-orozco'],['Lluís Barba','lluis-barba-art'],['Luz Pérez-Ojeda','luz-perez-ojeda-art'],
 ['Rafael Montilla','rafael-montilla'],['Valeria Yamamoto','valeria-yamamoto-art'],
]
listing = [b for b in P['/artists/']['blocks'] if b[0] in ('img', 'h4')]
portraits = {}
last_img = None
for b in listing:
    if b[0] == 'img': last_img = norm(b[1])
    elif last_img: portraits[clean(b[1]).lower()] = last_img; last_img = None
# Speedy Graphito's listing image comes last without an h4 after it
if last_img: portraits['speedy graphito'] = last_img

def portrait_for(name, raw):
    key = {'Ivonne Ferrer':'ivonne-ferrer','Víctor Valera':'victor valera','Jesús Rafael Soto':'jesus rafael soto','Marcos Marín':'marcos marin','Darío Pérez-Flores':'dario pérez-flores','Paul Amundaraín':'paul amundarain','Lluís Barba':'lluis barba','Luz Pérez-Ojeda':'luz perez-ojeda'}.get(name, name).lower()
    return portraits.get(key) or portraits.get(name.lower())

artists = []
for name, slug in ART + [['Mario Villasierra', 'mario-villasierra-art']]:
    path = '/' + slug + '/'
    pg = P.get(path)
    if not pg: print('MISSING', path, file=sys.stderr); continue
    bl = pg['blocks']
    sub = ''
    # first heading is the name, the h4 right after is birth/place
    i = 0
    while i < len(bl) and bl[i][0] not in ('h1', 'h2'): i += 1
    rest = bl[:i] + bl[i+1:] if i < len(bl) else bl
    for j, b in enumerate(rest[:4]):
        if b[0] == 'h4': sub = clean(b[1]); rest = rest[:j] + rest[j+1:]; break
    blocks = tidy(rest, drop_texts=[name, clean(pg['title']), clean(bl[i][1]) if i < len(bl) else ''])
    portrait = portrait_for(name, pg)
    if blocks and blocks[0][0] == 'img':
        first = blocks.pop(0)
        if not portrait: portrait = first[1]
    artists.append({'id': slug, 'name': name, 'sub': sub, 'portrait': portrait, 'blocks': blocks, 'listed': slug != 'mario-villasierra-art'})

# ---------- posts ----------
cats = {c['id']: c['name'] for c in D['meta']['cats']}
thumbs, excerpts = {}, {}
for lp in ('/blog/', '/exhibitions/'):
    bl = P[lp]['blocks']
    for i in range(len(bl) - 2):
        if bl[i][0] == 'img' and bl[i+1][0] == 'h2':
            t = clean(bl[i+1][1]).lower()
            thumbs.setdefault(t, norm(bl[i][1]))
            for k in (i+2, i+3):
                if k < len(bl) and bl[k][0] == 'p' and not DATE_RE.match(bl[k][1]):
                    excerpts.setdefault(t, clean(bl[k][1])); break
posts = []
for m in D['meta']['posts']:
    pg = P.get(m['path'])
    if not pg: print('MISSING POST', m['path'], file=sys.stderr); continue
    title_raw = clean(pg['title'])
    bl = trim_related(pg['blocks'])
    # drop the page title heading
    bl2 = []
    dropped = False
    for b in bl:
        if not dropped and b[0] in ('h1', 'h2') and clean(b[1]).lower().strip('“” ') in (title_raw.lower().strip('“” '),):
            dropped = True; continue
        bl2.append(b)
    if not dropped:
        for k, b in enumerate(bl2):
            if b[0] == 'h1': bl2.pop(k); break
    blocks = tidy(bl2)
    hero = None
    if blocks and blocks[0][0] == 'img': hero = blocks.pop(0)[1]
    tl = title_raw.lower()
    thumb = thumbs.get(tl) or hero or next((b[1] for b in blocks if b[0] == 'img'), None)
    exc = excerpts.get(tl) or next((b[1] for b in blocks if b[0] == 'p' and len(b[1]) > 60), '')
    exc = re.sub(r'\s*\.\.\.$|…$', '', exc)
    if len(exc) > 230: exc = exc[:230].rsplit(' ', 1)[0] + '…'
    kind = 'Exhibitions' if 26 in m['cats'] else 'Blog'
    posts.append({'id': m['path'].strip('/'), 'title': FIX_TITLE.get(m['path'], title_raw), 'date': m['date'][:10], 'kind': kind,
                  'cats': [cats.get(c, '') for c in m['cats'] if c not in (26, 31, 1)], 'hero': hero, 'thumb': thumb, 'excerpt': exc, 'blocks': blocks})

# ---------- pages ----------
about = tidy(P['/about/']['blocks'], drop_texts=['Ninoska Huerta', 'Connoisseur, Collector, Advisor & Private Art Dealer'])
if about and about[0][0] == 'img': about_portrait = about.pop(0)[1]
else: about_portrait = None
terms = tidy(P['/terms-and-conditions/']['blocks'], drop_texts=['Terms and Conditions for Ninoska Huerta Gallery'])
home = P['/']['blocks']
home_videos = [b[1] for b in home if b[0] == 'video']
beyond = []
seen = False
for b in home:
    if b[0] == 'h1' and 'Beyond' in b[1]: seen = True; continue
    if seen and b[0] == 'img': beyond.append(norm(b[1]))
    if seen and b[0] == 'p': break
exh_video = [b[1] for b in P['/exhibitions/']['blocks'] if b[0] == 'video']
amalia_feat = next((norm(b[1]) for i, b in enumerate(home) if b[0] == 'img' and i + 1 < len(home) and home[i+1][0] == 'h1' and 'Amalia' in home[i+1][1]), None)

out = {'artists': artists, 'posts': posts, 'about': about, 'aboutPortrait': about_portrait, 'terms': terms,
       'homeVideos': home_videos, 'beyond': beyond, 'exhVideo': exh_video, 'amalia': amalia_feat,
       'monahan': norm(UP + '2022/06/Ninoska-huerta-portada.jpg')}
js = 'var UPL = "' + UP + '";\nvar C = ' + json.dumps(out, ensure_ascii=False) + ';\n'
open(sys.argv[2], 'w').write(js)
ex = sum(1 for p in posts if p['kind'] == 'Exhibitions')
imgs = set()
def walk(o):
    if isinstance(o, str) and o.startswith('~U/'): imgs.add(o)
    elif isinstance(o, list): [walk(x) for x in o]
    elif isinstance(o, dict): [walk(x) for x in o.values()]
walk(out)
print('artists', len(artists), 'posts', len(posts), 'exhibitions', ex, 'blog', len(posts) - ex, 'unique images', len(imgs), 'kb', len(js) // 1024)
print('no portrait:', [a['name'] for a in artists if not a['portrait']])
print('beyond', len(beyond), 'videos', len(home_videos), exh_video, amalia_feat)
open(sys.argv[2] + '.imgs.txt', 'w').write('\n'.join(sorted(i.replace('~U/', UP) for i in imgs)))

(function(){
'use strict';
var $ = function(s, r){ return (r||document).querySelector(s); };
var $$ = function(s, r){ return Array.prototype.slice.call((r||document).querySelectorAll(s)); };
function esc(s){ return String(s).replace(/[&<>"]/g, function(c){ return {'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]; }); }
function money(n){ return '$' + n.toFixed(2); }
var byId = {}; PRODUCTS.forEach(function(p){ byId[p.id] = p; });

/* External links: '_blank' for previews; set to '_top' if this page is ever embedded in an iframe on the gallery's own domain. */
var LINK_TARGET = '_blank';
function extLinks(root){ $$('a[data-ext], a[href^="http"]', root).forEach(function(a){ a.target = LINK_TARGET; if (LINK_TARGET === '_blank') a.rel = 'noopener'; }); }

/* ---------- images with a quiet fallback ---------- */
function imgSlot(src, label, cls){
  return '<div class="img ' + (cls||'') + '" data-label="' + esc(label) + '">' + (src ? '<img src="' + esc(src) + '" alt="' + esc(label) + '" loading="lazy" decoding="async">' : '') + '</div>';
}
function wireImgs(root){
  $$('.img', root).forEach(function(box){
    var im = box.querySelector('img');
    if (!im && box.dataset.src){ box.innerHTML = '<img src="' + esc(UP + box.dataset.src) + '" alt="' + esc(box.dataset.label || '') + '" loading="lazy">'; im = box.querySelector('img'); }
    if (!im){ box.classList.add('noimg'); return; }
    if (im.complete && im.naturalWidth === 0 && im.src) box.classList.add('noimg');
    im.addEventListener('error', function(){ box.classList.add('noimg'); });
  });
}

/* ---------- renderers ---------- */
function pcard(p){
  return '<div class="pcard-wrap"><a class="pcard" href="#product-' + p.id + '">' + imgSlot(p.imgs[0], p.artist + ' · ' + p.title, 'contain') +
    '<span class="art">' + esc(p.artist) + '</span><span class="t">' + esc(p.title) + '</span><span class="p">' + money(p.price) + '</span></a>' +
    '<button class="btn line add" type="button" data-add="' + p.id + '" style="min-height:38px;padding:0 14px;margin-top:10px">Add to cart</button></div>';
}
var HOME_IDS = ['soto-y-la-escritura','happiness-with-frame','health','prosperity','chateau-de-versailles-i','chateau-de-versailles-ii','chateau-de-versailles-iv','chateau-de-versailles-v'];
$('[data-products-home]').innerHTML = HOME_IDS.map(function(id){ return pcard(byId[id]); }).join('');

/* ---------- migrated content (C, from content.js) ---------- */
function u(x){ return x ? String(x).replace(/^~U\//, UPL) : ''; }
function plain(s){ return String(s || '').replace(/<br\s*\/?>/gi, ' · ').replace(/<[^>]+>/g, '').replace(/\s+/g, ' ').trim(); }
var MONTHS = ['January','February','March','April','May','June','July','August','September','October','November','December'];
function fdate(d){ var p = d.split('-'); return MONTHS[+p[1]-1] + ' ' + (+p[2]) + ', ' + p[0]; }
var ARTS = C.artists.slice().sort(function(a,b){ return a.name.localeCompare(b.name, 'es'); });
var artById = {}; C.artists.forEach(function(a){ artById[a.id] = a; });
var postById = {}; C.posts.forEach(function(p){ postById[p.id] = p; });
var EXH = C.posts.filter(function(p){ return p.kind === 'Exhibitions'; });
var BLOG = C.posts.filter(function(p){ return p.kind === 'Blog'; });

function vidHost(src){ return /vimeo/.test(src) ? 'Vimeo' : 'YouTube'; }
function vidWatch(src){
  var m = src.match(/youtube\.com\/embed\/([\w-]+)/); if (m) return 'https://www.youtube.com/watch?v=' + m[1];
  m = src.match(/vimeo\.com\/video\/(\d+)/); if (m) return 'https://vimeo.com/' + m[1];
  return src;
}
function vidEmbed(src){ return src.split('?')[0] + (/vimeo/.test(src) ? '?dnt=1&autoplay=1' : '?autoplay=1&rel=0'); }
function vbox(src, title){
  return '<div><div class="vbox"><button type="button" data-play="' + esc(vidEmbed(src)) + '" aria-label="Play video' + (title ? ': ' + esc(title) : '') + '">' +
    '<svg width="54" height="54" viewBox="0 0 54 54" aria-hidden="true"><circle cx="27" cy="27" r="26" fill="none" stroke="currentColor" stroke-width="1.2"/><path d="M22 17l15 10-15 10z" fill="currentColor"/></svg>' +
    '<span class="lbl">Play video</span></button></div><a class="vlink" href="' + esc(vidWatch(src)) + '" data-ext>Open on ' + vidHost(src) + ' ↗</a></div>';
}
document.addEventListener('click', function(e){
  var b = e.target.closest('[data-play]'); if (!b) return;
  var box = b.parentNode; box.innerHTML = '<iframe src="' + esc(b.dataset.play) + '" title="Video" allow="autoplay; fullscreen; picture-in-picture" allowfullscreen loading="lazy"></iframe>';
});

/* Gallery figure: caption from the old site's caption line, falling back to alt text where asked */
function fig(b, useAlt){
  var cap = b[3] ? plain(b[3]) : (useAlt ? plain(b[2]) : '');
  var alt = plain(b[2]) || cap;
  return '<figure><button type="button" data-lb="' + esc(u(b[1])) + '" data-cap="' + esc(cap) + '" aria-label="Enlarge' + (alt ? ': ' + esc(alt) : ' image') + '">' + imgSlot(u(b[1]), alt) + '</button>' +
    (cap ? '<figcaption>' + esc(cap) + '</figcaption>' : '') + '</figure>';
}
function renderBlocks(blocks, opt){
  opt = opt || {};
  var out = '', i = 0, inList = false;
  function closeList(){ if (inList){ out += '</ul>'; inList = false; } }
  while (i < blocks.length){
    var b = blocks[i], k = b[0];
    if (k === 'img'){
      closeList();
      var g = [];
      while (i < blocks.length && blocks[i][0] === 'img'){ g.push(blocks[i]); i++; }
      out += '<div class="gal' + (g.length === 1 && !opt.grid ? ' one' : '') + '">' + g.map(function(x){ return fig(x, opt.useAlt); }).join('') + '</div>';
      continue;
    }
    if (k === 'video'){ closeList(); out += '<div style="margin:28px 0;max-width:860px">' + vbox(b[1]) + '</div>'; i++; continue; }
    if (k === 'li'){ if (!inList){ out += '<ul>'; inList = true; } out += '<li>' + esc(b[1]) + '</li>'; i++; continue; }
    closeList();
    if (k === 'h2' || k === 'h3' || k === 'h4' || k === 'h5' || k === 'h6') out += '<' + k + '>' + esc(b[1]) + '</' + k + '>';
    else if (k === 'blockquote') out += '<blockquote>' + esc(b[1]) + '</blockquote>';
    else out += '<p>' + esc(b[1]) + '</p>';
    i++;
  }
  closeList();
  return out;
}

function acard(a){ return '<a class="acard" href="#artist-' + a.id + '">' + imgSlot(u(a.portrait), a.name) + '<span class="n">' + esc(a.name) + '</span>' + (a.sub ? '<span class="mono" style="color:var(--muted);font-size:12px">' + esc(a.sub) + '</span>' : '') + '</a>'; }
function ccard(p, i, latest){
  return '<a class="ccard" href="#post-' + p.id + '">' + imgSlot(u(p.thumb), p.title) +
    '<p class="lbl' + (latest && i === 0 ? ' now' : '') + '" style="' + (latest && i === 0 ? '' : 'color:var(--muted)') + '">' + (latest && i === 0 ? '<span class="dot" aria-hidden="true"></span>Latest · ' : '') + esc(fdate(p.date)) + '</p>' +
    '<h3>' + esc(p.title) + '</h3>' + (p.excerpt ? '<p>' + esc(p.excerpt) + '</p>' : '') + '<span class="tlink">Read more →</span></a>';
}

$$('[data-c]').forEach(function(box){ var src = u(C[box.dataset.c]); if (src) box.innerHTML = '<img src="' + esc(src) + '" alt="' + esc(box.dataset.label || '') + '" loading="lazy" decoding="async">'; });
$('[data-beyond]').innerHTML = C.beyond.map(function(src){ return imgSlot(u(src), 'Marcos Marín, Beyond the Visible'); }).join('');
$$('[data-artist-grid]').forEach(function(g){ g.innerHTML = ARTS.filter(function(a){ return a.listed; }).map(acard).join(''); });
$('[data-exh-latest]').innerHTML = EXH.slice(0,3).map(function(p,i){ return ccard(p,i,true); }).join('');
$('[data-exh-all]').innerHTML = EXH.map(function(p,i){ return ccard(p,i,true); }).join('');
$('[data-posts-home]').innerHTML = BLOG.slice(0,3).map(function(p,i){ return ccard(p,i,false); }).join('');
$('[data-posts-all]').innerHTML = BLOG.map(function(p,i){ return ccard(p,i,false); }).join('');
$('[data-videos]').innerHTML = C.homeVideos.map(function(v){ return vbox(v); }).join('');
if (C.exhVideo && C.exhVideo[0]) $('[data-exh-video]').innerHTML = vbox(C.exhVideo[0], 'Exhibitions');
(function(){
  var txt = [], media = [];
  C.about.forEach(function(b){ (b[0] === 'img' || b[0] === 'video' ? media : txt).push(b); });
  $('[data-about-text]').innerHTML = renderBlocks(txt);
  var vids = media.filter(function(b){ return b[0] === 'video'; }), imgs = media.filter(function(b){ return b[0] === 'img'; });
  $('[data-about-media]').innerHTML = (vids.length ? '<div class="vgrid" style="margin-bottom:40px">' + vids.map(function(v){ return vbox(v[1], 'Ninoska Huerta'); }).join('') + '</div>' : '') +
    '<div class="rich">' + renderBlocks(imgs, {useAlt:true, grid:true}) + '</div>';
})();
$('[data-terms]').innerHTML = renderBlocks(C.terms);

function pagerHtml(list, idx, pre, label){
  var prev = list[idx-1], next = list[idx+1];
  return '<nav class="pager" aria-label="More ' + label + '">' +
    (prev ? '<a href="#' + pre + prev.id + '"><small>← Previous</small>' + esc(prev.name || prev.title) + '</a>' : '<span></span>') +
    (next ? '<a href="#' + pre + next.id + '" style="text-align:right"><small>Next →</small>' + esc(next.name || next.title) + '</a>' : '<span></span>') + '</nav>';
}
function renderArtist(id){
  var a = artById[id], v = $('#artistView');
  if (!a){ v.innerHTML = '<div style="padding:80px 0"><h1>Artist not found</h1><a class="tlink" href="#artists">All artists →</a></div>'; return; }
  var bio = [], work = [], seen = false;
  a.blocks.forEach(function(b){ if (b[0] === 'h2' && b[1] === 'Featured work'){ seen = true; return; } (seen ? work : bio).push(b); });
  if (!seen){ bio = a.blocks.filter(function(b){ return b[0] !== 'img'; }); work = a.blocks.filter(function(b){ return b[0] === 'img'; }); }
  var prods = PRODUCTS.filter(function(p){ return p.artist === a.name; });
  var list = ARTS.filter(function(x){ return x.listed || x.id === id; }), idx = list.indexOf(a);
  v.innerHTML = '<p style="padding-top:28px;margin:0"><a class="tlink" href="#artists">← All artists</a></p>' +
    '<header class="artist-head">' + imgSlot(u(a.portrait), a.name) + '<div><p class="lbl" style="color:var(--muted)">Artist</p><h1>' + esc(a.name) + '</h1>' + (a.sub ? '<p class="mono" style="margin:0;color:var(--muted)">' + esc(a.sub) + '</p>' : '') +
    '<div class="ctas" style="margin-top:22px"><a class="btn dark" href="#contact">Enquire about this artist</a>' + (prods.length ? '<a class="btn line" href="#shop" data-filter="' + esc(a.name) + '">Shop works</a>' : '') + '</div></div></header>' +
    '<div class="prose rich">' + renderBlocks(bio) + '</div>' +
    (work.length ? '<section class="rich" style="margin-top:48px"><h2>Featured work</h2>' + renderBlocks(work, {grid:true}) + '</section>' : '') +
    (prods.length ? '<section style="margin-top:56px"><div class="sec-head"><h2 style="margin:0">Available in the store</h2><a class="tlink" href="#shop" data-filter="' + esc(a.name) + '">See all →</a></div><div class="products">' + prods.map(pcard).join('') + '</div></section>' : '') +
    pagerHtml(list, idx, 'artist-', 'artists');
  wireImgs(v); extLinks(v);
}
function renderPost(id){
  var p = postById[id], v = $('#postView');
  if (!p){ v.innerHTML = '<div style="padding:80px 0"><h1>Post not found</h1><a class="tlink" href="#blog">Blog →</a></div>'; return; }
  var list = p.kind === 'Exhibitions' ? EXH : BLOG, back = p.kind === 'Exhibitions' ? 'exhibitions' : 'blog';
  v.innerHTML = '<p style="padding-top:28px;margin:0"><a class="tlink" href="#' + back + '">← ' + (back === 'blog' ? 'Blog' : 'All exhibitions') + '</a></p>' +
    '<header class="post-head"><p class="lbl" style="color:var(--muted)">' + esc(p.kind === 'Exhibitions' ? 'Exhibition' : 'Blog') + ' · ' + esc(fdate(p.date)) + '</p><h1>' + esc(p.title) + '</h1></header>' +
    (p.hero ? '<div class="post-hero">' + imgSlot(u(p.hero), p.title) + '</div>' : '') +
    '<div class="prose rich">' + renderBlocks(p.blocks) + '</div>' +
    '<div class="ctas" style="margin-top:36px"><a class="btn dark" href="#contact">Book a visit</a></div>' +
    pagerHtml(list, list.indexOf(p), 'post-', back);
  wireImgs(v); extLinks(v);
}

/* ---------- lightbox ---------- */
var lb = null, lbList = [], lbI = 0, lbFrom = null;
function lbShow(){ var it = lbList[lbI]; lb.querySelector('img').src = it.src; lb.querySelector('img').alt = it.cap || ''; lb.querySelector('figcaption').textContent = it.cap || ''; lb.querySelector('.cnt').textContent = (lbI+1) + ' / ' + lbList.length; }
function lbOpen(btn){
  var gal = btn.closest('.gal'), btns = $$('[data-lb]', gal.parentNode);
  lbList = btns.map(function(x){ return {src:x.dataset.lb, cap:x.dataset.cap}; }); lbI = btns.indexOf(btn); lbFrom = btn;
  if (!lb){
    lb = document.createElement('div'); lb.className = 'lb'; lb.setAttribute('role','dialog'); lb.setAttribute('aria-modal','true'); lb.setAttribute('aria-label','Image viewer');
    lb.innerHTML = '<figure style="margin:0;width:100%;height:100%;display:flex;align-items:center;justify-content:center"><img alt=""><figcaption></figcaption></figure>' +
      '<button class="btn ghost x" type="button" aria-label="Close">Close</button><button class="nav prev" type="button" aria-label="Previous image">‹</button><button class="nav next" type="button" aria-label="Next image">›</button>' +
      '<span class="cnt mono" style="position:absolute;top:22px;left:20px;color:#B3B3B3;font-size:12px"></span>';
    document.body.appendChild(lb);
    lb.querySelector('.x').addEventListener('click', lbClose);
    lb.querySelector('.prev').addEventListener('click', function(){ lbI = (lbI - 1 + lbList.length) % lbList.length; lbShow(); });
    lb.querySelector('.next').addEventListener('click', function(){ lbI = (lbI + 1) % lbList.length; lbShow(); });
    lb.addEventListener('click', function(e){ if (e.target === lb || e.target.tagName === 'FIGURE') lbClose(); });
  }
  lb.hidden = false; var one = lbList.length < 2; lb.querySelector('.prev').hidden = one; lb.querySelector('.next').hidden = one;
  lbShow(); document.body.style.overflow = 'hidden'; lb.querySelector('.x').focus();
}
function lbClose(){ if (!lb || lb.hidden) return; lb.hidden = true; document.body.style.overflow = ''; if (lbFrom) lbFrom.focus(); }
document.addEventListener('click', function(e){ var b = e.target.closest('[data-lb]'); if (b){ e.preventDefault(); lbOpen(b); } });
document.addEventListener('keydown', function(e){
  if (!lb || lb.hidden) return;
  if (e.key === 'Escape'){ e.stopPropagation(); lbClose(); }
  else if (e.key === 'ArrowLeft') lb.querySelector('.prev').click();
  else if (e.key === 'ArrowRight') lb.querySelector('.next').click();
}, true);


var filter = 'all', sort = 'feat';
function renderShop(){
  var list = PRODUCTS.filter(function(p){ return filter === 'all' || p.line === filter; });
  if (sort === 'asc') list.sort(function(a,b){ return a.price - b.price; });
  if (sort === 'desc') list.sort(function(a,b){ return b.price - a.price; });
  if (sort === 'az') list.sort(function(a,b){ return a.title.localeCompare(b.title); });
  $('[data-products-all]').innerHTML = list.map(pcard).join('');
  $('#pcount').textContent = list.length + (list.length === 1 ? ' product' : ' products');
  $$('.chip').forEach(function(c){ c.setAttribute('aria-pressed', String(c.dataset.f === filter)); });
  wireImgs($('[data-products-all]'));
}
$$('.chip').forEach(function(c){ c.addEventListener('click', function(){ filter = c.dataset.f; renderShop(); }); });
$('#sort').addEventListener('change', function(e){ sort = e.target.value; renderShop(); });
document.addEventListener('click', function(e){ var a = e.target.closest('[data-filter]'); if (a) filter = a.dataset.filter; }, true);

function renderProduct(id){
  var p = byId[id], v = $('#productView');
  if (!p){ v.innerHTML = '<div><h1>Product not found</h1><a class="tlink" href="#shop">Back to the shop →</a></div>'; return; }
  var related = PRODUCTS.filter(function(x){ return x.line === p.line && x.id !== p.id; }).slice(0,4);
  v.innerHTML =
    '<div class="gallery">' + imgSlot(p.imgs[0], p.artist + ' · ' + p.title, 'main contain') +
      (p.imgs.length > 1 ? '<div class="thumbs">' + p.imgs.map(function(src, i){ return '<button type="button" data-thumb="' + i + '" aria-current="' + (i===0) + '" aria-label="Image ' + (i+1) + '">' + imgSlot(src, '') + '</button>'; }).join('') + '</div>' : '') +
    '</div>' +
    '<div><p class="crumbs"><a href="#shop">Shop</a> / ' + esc(p.line) + '</p>' +
      '<p class="lbl">' + esc(p.artist) + '</p><h1 class="it" style="font-family:var(--f-s);font-style:italic;font-weight:300">' + esc(p.title) + '</h1>' +
      '<p class="price">' + money(p.price) + '</p>' +
      '<dl class="specs">' + p.specs.map(function(s){ return '<dt>' + esc(s[0]) + '</dt><dd>' + esc(s[1]) + '</dd>'; }).join('') + '</dl>' +
      '<div class="buy"><div class="qty"><button type="button" data-q="-1" aria-label="Decrease quantity">−</button><input id="pq" type="number" min="1" max="10" value="1" aria-label="Quantity"><button type="button" data-q="1" aria-label="Increase quantity">+</button></div>' +
      '<button class="btn dark" type="button" data-add="' + p.id + '" data-qty-from="#pq">Add to cart</button></div>' +
      '<p class="note">Questions about this work? <a href="#contact">Contact the gallery</a> or call +1 305 588 1231. Visits by appointment.</p>' +
    '</div>' +
    (related.length ? '<div style="grid-column:1/-1;margin-top:40px"><h2 style="font-size:32px">More from ' + esc(p.line) + '</h2><div class="products">' + related.map(pcard).join('') + '</div></div>' : '');
  wireImgs(v);
  $$('[data-thumb]', v).forEach(function(b){ b.addEventListener('click', function(){
    var src = p.imgs[+b.dataset.thumb], main = $('.gallery .main', v);
    main.classList.remove('noimg'); main.innerHTML = '<img src="' + esc(src) + '" alt="' + esc(p.artist + ' · ' + p.title) + '">'; wireImgs(main.parentNode);
    $$('[data-thumb]', v).forEach(function(x){ x.setAttribute('aria-current', String(x === b)); });
  }); });
  $$('[data-q]', v).forEach(function(b){ b.addEventListener('click', function(){ var i = $('#pq'); i.value = Math.max(1, Math.min(10, (+i.value||1) + (+b.dataset.q))); }); });
}

/* ---------- cart (prototype; Shopify Cart API replaces this) ---------- */
var cart = [];
try { cart = JSON.parse(localStorage.getItem('nhg-cart') || '[]').filter(function(l){ return byId[l.id]; }); } catch(e){ cart = []; }
function save(){ try { localStorage.setItem('nhg-cart', JSON.stringify(cart)); } catch(e){} }
function count(){ return cart.reduce(function(n,l){ return n + l.q; }, 0); }
function add(id, q){
  var l = cart.filter(function(x){ return x.id === id; })[0];
  if (l) l.q = Math.min(10, l.q + q); else cart.push({id:id, q:q});
  save(); renderCart(); toast(esc(byId[id].title) + ' added to your cart', true);
}
function renderCart(){
  var n = count();
  $('#cartCount').textContent = n; $('#cartCount').hidden = n === 0;
  $('#cartBtn').setAttribute('aria-label', 'Open cart, ' + n + (n === 1 ? ' item' : ' items'));
  var lines = $('#cartLines'), tot = $('#cartTotals');
  if (!cart.length){
    lines.innerHTML = '<div class="empty"><p>Your cart is empty.</p><a class="btn dark" href="#shop" data-close-cart>Visit the shop</a></div>';
    tot.innerHTML = ''; return;
  }
  lines.innerHTML = cart.map(function(l){
    var p = byId[l.id];
    return '<div class="line">' + imgSlot(p.imgs[0], p.title, 'contain') +
      '<div><p class="a">' + esc(p.artist) + '</p><p class="t"><a href="#product-' + p.id + '" data-close-cart style="text-decoration:none">' + esc(p.title) + '</a></p>' +
      '<div class="qty"><button type="button" data-lq="-1" data-id="' + p.id + '" aria-label="Decrease quantity of ' + esc(p.title) + '">−</button><input type="number" value="' + l.q + '" min="1" max="10" data-li="' + p.id + '" aria-label="Quantity of ' + esc(p.title) + '"><button type="button" data-lq="1" data-id="' + p.id + '" aria-label="Increase quantity of ' + esc(p.title) + '">+</button></div>' +
      '<br><button class="rm" type="button" data-rm="' + p.id + '">Remove</button></div>' +
      '<div class="p">' + money(p.price * l.q) + '</div></div>';
  }).join('');
  var sub = cart.reduce(function(s,l){ return s + byId[l.id].price * l.q; }, 0);
  tot.innerHTML = '<div class="row big"><span>Subtotal</span><span>' + money(sub) + ' USD</span></div>' +
    '<p class="note">Shipping and taxes are calculated at checkout.</p><button class="btn dark" type="button" id="checkout">Checkout</button>';
  wireImgs(lines);
}
document.addEventListener('click', function(e){
  var a = e.target.closest('[data-add]');
  if (a){ var q = 1; if (a.dataset.qtyFrom){ q = Math.max(1, Math.min(10, +$(a.dataset.qtyFrom).value || 1)); } add(a.dataset.add, q); return; }
  var lq = e.target.closest('[data-lq]');
  if (lq){ cart.forEach(function(l){ if (l.id === lq.dataset.id) l.q = Math.max(1, Math.min(10, l.q + (+lq.dataset.lq))); }); save(); renderCart(); return; }
  var rm = e.target.closest('[data-rm]');
  if (rm){ cart = cart.filter(function(l){ return l.id !== rm.dataset.rm; }); save(); renderCart(); $('#cartClose').focus(); return; }
  if (e.target.closest('[data-close-cart]')){ openCart(false); }
  if (e.target.id === 'checkout'){
    $('#coBody').textContent = 'This is the design prototype. In the Shopify store, this button takes you to secure checkout with your ' + count() + (count() === 1 ? ' item' : ' items') + '. Your cart is saved on this device.';
    $('#checkoutModal').hidden = false; $('#coClose').focus();
  }
  var cp = e.target.closest('[data-copy]');
  if (cp){
    var t = cp.dataset.copy;
    var done = function(){ var o = cp.textContent; cp.textContent = 'Copied'; setTimeout(function(){ cp.textContent = o; }, 1200); };
    if (navigator.clipboard && navigator.clipboard.writeText) navigator.clipboard.writeText(t).then(done, function(){ selectText(cp.previousElementSibling); });
    else selectText(cp.previousElementSibling);
  }
});
function selectText(el){ var r = document.createRange(); r.selectNodeContents(el); var s = getSelection(); s.removeAllRanges(); s.addRange(r); }
document.addEventListener('change', function(e){
  if (e.target.dataset.li){ var v = Math.max(1, Math.min(10, +e.target.value || 1)); cart.forEach(function(l){ if (l.id === e.target.dataset.li) l.q = v; }); save(); renderCart(); }
});
$('#coClose').addEventListener('click', function(){ $('#checkoutModal').hidden = true; $('#checkout') && $('#checkout').focus(); });
$('#coContact').addEventListener('click', function(){ $('#checkoutModal').hidden = true; openCart(false); });

var lastFocus = null;
function openCart(open){
  $('#cart').hidden = !open; $('#cartScrim').hidden = !open;
  if (open){ lastFocus = document.activeElement; $('#cartClose').focus(); } else if (lastFocus && lastFocus.focus) lastFocus.focus();
}
$('#cartBtn').addEventListener('click', function(){ openCart(true); });
$('#cartClose').addEventListener('click', function(){ openCart(false); });
$('#cartScrim').addEventListener('click', function(){ openCart(false); });

var toastT;
function toast(html, withCart){
  var t = $('#toast');
  t.innerHTML = '<span>' + html + '</span>' + (withCart ? '<button type="button" id="toastView">View cart</button>' : '');
  t.hidden = false; clearTimeout(toastT); toastT = setTimeout(function(){ t.hidden = true; }, 3200);
  var b = $('#toastView'); if (b) b.addEventListener('click', function(){ t.hidden = true; openCart(true); });
}

/* ---------- menu ---------- */
var mnav = $('#mnav');
function setMenu(open){ mnav.hidden = !open; $('#menuBtn').setAttribute('aria-expanded', String(open)); document.body.style.overflow = open ? 'hidden' : ''; if (open) $('#menuClose').focus(); else $('#menuBtn').focus(); }
$('#menuBtn').addEventListener('click', function(){ setMenu(true); });
$('#menuClose').addEventListener('click', function(){ setMenu(false); });
mnav.addEventListener('click', function(e){ if (e.target.closest('a')) { mnav.hidden = true; document.body.style.overflow = ''; $('#menuBtn').setAttribute('aria-expanded','false'); } });
document.addEventListener('keydown', function(e){
  if (e.key !== 'Escape') return;
  if (!$('#checkoutModal').hidden) { $('#checkoutModal').hidden = true; return; }
  if (!$('#cart').hidden) { openCart(false); return; }
  if (!mnav.hidden) setMenu(false);
});

/* ---------- forms (prototype: Shopify's contact and newsletter forms replace these) ---------- */
$('#cform').addEventListener('submit', function(e){
  e.preventDefault();
  var ok = true;
  [['#cname', function(v){ return v.trim().length > 0; }], ['#cemail', function(v){ return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(v); }]].forEach(function(f){
    var el = $(f[0]), good = f[1](el.value), err = el.parentNode.querySelector('.err');
    err.hidden = good; el.setAttribute('aria-invalid', String(!good)); if (!good && ok){ el.focus(); ok = false; }
  });
  if (!ok) return;
  var body = $('#cmsg').value + '\n\n— ' + $('#cname').value + ' (' + $('#cemail').value + ')';
  var href = 'mailto:ninoskahuerta@gmail.com?subject=' + encodeURIComponent($('#csubj').value || 'Website enquiry') + '&body=' + encodeURIComponent(body);
  var m = $('#cformMsg'); m.hidden = false;
  m.innerHTML = 'Thank you, ' + esc($('#cname').value.split(' ')[0]) + '. Your email app should open with your message. If it doesn’t, write to <b>ninoskahuerta@gmail.com</b> or call +1 305 588 1231.';
  window.location.href = href;
});
$('#nform').addEventListener('submit', function(e){
  e.preventDefault();
  var v = $('#nemail').value, m = $('#nmsg'); m.hidden = false;
  if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(v)){ m.textContent = 'Add a valid email, like name@example.com.'; $('#nemail').focus(); return; }
  m.textContent = 'Thank you. ' + v + ' will receive our exhibition news. (Prototype: in the Shopify store this adds you to the customer newsletter list.)';
  $('#nemail').value = '';
});

/* ---------- router ---------- */
var PAGES = ['home','about','artists','exhibitions','shop','blog','contact','terms'];
function route(){
  var h = (location.hash || '#home').slice(1), page = h, arg = null;
  [['product-','product'],['artist-','artist'],['post-','post']].forEach(function(x){ if (h.indexOf(x[0]) === 0){ page = x[1]; arg = h.slice(x[0].length); } });
  if (PAGES.indexOf(page) < 0 && ['product','artist','post'].indexOf(page) < 0) page = 'home';
  $$('[data-page]').forEach(function(d){ d.hidden = d.dataset.page !== page; });
  document.body.className = 'route-' + page;
  var navKey = page === 'product' ? 'shop' : page === 'artist' ? 'artists' : page === 'post' ? (postById[arg] && postById[arg].kind === 'Blog' ? 'blog' : 'exhibitions') : page;
  $$('.hnav a, #mnav nav a').forEach(function(a){ if (a.getAttribute('href') === '#' + navKey) a.setAttribute('aria-current','page'); else a.removeAttribute('aria-current'); });
  if (page === 'shop') renderShop();
  if (page === 'product') renderProduct(arg);
  if (page === 'artist') renderArtist(arg);
  if (page === 'post') renderPost(arg);
  var t = page === 'product' && byId[arg] ? byId[arg].title : page === 'artist' && artById[arg] ? artById[arg].name : page === 'post' && postById[arg] ? postById[arg].title : page === 'terms' ? 'Terms and Conditions' : page.charAt(0).toUpperCase() + page.slice(1);
  document.title = page === 'home' ? 'Ninoska Huerta Gallery' : t + ' · Ninoska Huerta Gallery';
  if (lb && !lb.hidden) lbClose();
  window.scrollTo(0, 0);
  onScroll();
  if (window.NHKinetic) window.NHKinetic.setActive(page === 'home');
}
function onScroll(){
  var onHero = document.body.classList.contains('route-home') && window.scrollY < ($('#hero').offsetHeight - 80);
  document.body.classList.toggle('on-hero', onHero);
}
window.addEventListener('scroll', onScroll, {passive:true});
window.addEventListener('hashchange', route);

/* ---------- kinetic hero ---------- */
(function(){
  var cv = document.getElementById('field');
  var ctx = cv.getContext('2d', {alpha:false});
  var btn = document.getElementById('pause'), lbl = document.getElementById('pl'), ico = document.getElementById('pi');
  var reduce = window.matchMedia('(prefers-reduced-motion: reduce)');
{{KINETIC_CORE}}
  var running=false, paused=false, active=true, inView=true, raf=0, last=0;
  function loop(now){ if (!running) return; raf = requestAnimationFrame(loop); if (now - last < frameMs - 1) return; last = now; draw(now); }
  function canRun(){ return !paused && active && inView && !document.hidden; }
  function start(){ if (running || !canRun()) return; running = true; last = 0; raf = requestAnimationFrame(loop); }
  function stop(){ running = false; cancelAnimationFrame(raf); }
  function setPaused(p){
    paused = p; btn.setAttribute('aria-pressed', String(p));
    lbl.textContent = p ? 'Activar movimiento' : 'Pausar movimiento';
    ico.innerHTML = p ? '<path d="M3 1.5v9l7-4.5z" fill="currentColor"/>' : '<rect x="2" y="1.5" width="2.5" height="9" fill="currentColor"/><rect x="7.5" y="1.5" width="2.5" height="9" fill="currentColor"/>';
    if (p){ stop(); draw(performance.now()); } else start();
  }
  btn.addEventListener('click', function(){ setPaused(!paused); });
  document.addEventListener('visibilitychange', function(){ if (document.hidden) stop(); else start(); });
  if (reduce.addEventListener) reduce.addEventListener('change', function(e){ setPaused(e.matches); });
  new IntersectionObserver(function(es){ inView = es[0].isIntersecting; if (inView) start(); else stop(); }).observe(cv);
  new ResizeObserver(function(){ resize(); }).observe(cv);
  window.NHKinetic = { setActive: function(a){ active = a; if (a){ resize(); start(); } else stop(); } };
  resize();
  if (reduce.matches) setPaused(true); else start();
})();

extLinks(document);
wireImgs(document);
renderCart();
route();
})();

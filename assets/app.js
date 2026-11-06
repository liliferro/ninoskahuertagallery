(function(){
'use strict';
var $ = function(s, r){ return (r||document).querySelector(s); };
var $$ = function(s, r){ return Array.prototype.slice.call((r||document).querySelectorAll(s)); };
function esc(s){ return String(s).replace(/[&<>"]/g, function(c){ return {'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]; }); }
function money(n){ return '$' + Number(n).toFixed(2); }

var byId = {};
(window.PRODUCTS || []).forEach(function(p){ byId[p.id] = p; });

/* Old hash URLs from the single-page prototype. */
(function(){
  var path = location.pathname;
  if (path !== '/' && path !== '/index.html') return;
  var h = (location.hash || '').replace(/^#\/?/, '');
  if (!h) return;
  var map = {home:'/', about:'/acerca-de/', artists:'/artistas/', exhibitions:'/exposiciones/', shop:'/tienda/', blog:'/blog/', contact:'/contacto/', terms:'/terminos/'};
  var dest = map[h] || null;
  if (h.indexOf('artist-') === 0) dest = '/artistas/' + encodeURIComponent(h.slice(7)) + '/';
  else if (h.indexOf('product-') === 0) dest = '/tienda/' + encodeURIComponent(h.slice(8)) + '/';
  else if (h.indexOf('post-') === 0 && window.POST_PATHS) dest = window.POST_PATHS[h.slice(5)] || null;
  if (dest) location.replace(dest);
})();

$$('a[href^="http"]').forEach(function(a){
  if (a.target !== '_blank') a.target = '_blank';
  a.rel = 'noopener noreferrer';
});

$$('.img').forEach(function(box){
  var im = box.querySelector('img');
  if (!im){ box.classList.add('noimg'); return; }
  function fail(){ if (im.naturalWidth === 0) box.classList.add('noimg'); }
  if (im.complete) fail();
  im.addEventListener('error', function(){ box.classList.add('noimg'); });
  im.addEventListener('load', function(){ if (im.naturalWidth === 0) box.classList.add('noimg'); });
});

document.addEventListener('click', function(e){
  var b = e.target.closest('[data-play]'); if (!b) return;
  var box = b.parentNode;
  box.innerHTML = '<iframe src="' + esc(b.dataset.play) + '" title="Vídeo" width="640" height="360" allow="autoplay; fullscreen; picture-in-picture" allowfullscreen loading="lazy"></iframe>';
});

/* ---------- lightbox ---------- */
var lb = null, lbList = [], lbI = 0, lbFrom = null;
function lbShow(){
  var it = lbList[lbI];
  var img = lb.querySelector('img');
  img.src = it.src; img.alt = it.cap || '';
  lb.querySelector('figcaption').textContent = it.cap || '';
  lb.querySelector('.cnt').textContent = (lbI + 1) + ' / ' + lbList.length;
}
function lbOpen(btn){
  var gal = btn.closest('.gal');
  var btns = $$('[data-lb]', gal ? gal : document);
  lbList = btns.map(function(x){ return {src:x.dataset.lb, cap:x.dataset.cap}; });
  lbI = Math.max(0, btns.indexOf(btn));
  lbFrom = btn;
  if (!lb){
    lb = document.createElement('div'); lb.className = 'lb'; lb.hidden = true;
    lb.setAttribute('role','dialog'); lb.setAttribute('aria-modal','true'); lb.setAttribute('aria-label','Visor de imágenes');
    lb.innerHTML = '<figure style="margin:0;width:100%;height:100%;display:flex;align-items:center;justify-content:center"><img alt="" width="1600" height="1600"><figcaption></figcaption></figure>' +
      '<button class="btn ghost x" type="button" aria-label="Cerrar">Cerrar</button><button class="nav prev" type="button" aria-label="Imagen anterior">‹</button><button class="nav next" type="button" aria-label="Imagen siguiente">›</button>' +
      '<span class="cnt mono" style="position:absolute;top:22px;left:20px;color:#B3B3B3;font-size:12px"></span>';
    document.body.appendChild(lb);
    lb.querySelector('.x').addEventListener('click', lbClose);
    lb.querySelector('.prev').addEventListener('click', function(){ lbI = (lbI - 1 + lbList.length) % lbList.length; lbShow(); });
    lb.querySelector('.next').addEventListener('click', function(){ lbI = (lbI + 1) % lbList.length; lbShow(); });
    lb.addEventListener('click', function(e){ if (e.target === lb || e.target.tagName === 'FIGURE') lbClose(); });
  }
  lb.hidden = false;
  var one = lbList.length < 2;
  lb.querySelector('.prev').hidden = one; lb.querySelector('.next').hidden = one;
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

/* ---------- shop filters (the markup is already in the page) ---------- */
var grid = $('[data-products-all]');
if (grid && $('#sort')){
  var filter = 'all', sort = 'feat';
  var cards = $$('[data-product]', grid);
  function apply(){
    var list = cards.filter(function(c){ return filter === 'all' || c.dataset.line === filter; });
    var sorted = list.slice();
    if (sort === 'asc') sorted.sort(function(a,b){ return +a.dataset.price - +b.dataset.price; });
    if (sort === 'desc') sorted.sort(function(a,b){ return +b.dataset.price - +a.dataset.price; });
    if (sort === 'az') sorted.sort(function(a,b){ return a.dataset.title.localeCompare(b.dataset.title, 'es'); });
    cards.forEach(function(c){ c.hidden = sorted.indexOf(c) < 0; });
    sorted.forEach(function(c){ grid.appendChild(c); });
    var n = sorted.length;
    var count = $('#pcount');
    if (count) count.textContent = n + (n === 1 ? ' obra' : ' obras');
    $$('.chip').forEach(function(c){ c.setAttribute('aria-pressed', String(c.dataset.f === filter)); });
  }
  $$('.chip').forEach(function(c){ c.addEventListener('click', function(){ filter = c.dataset.f; apply(); }); });
  $('#sort').addEventListener('change', function(e){ sort = e.target.value; apply(); });
  var linea = new URLSearchParams(location.search).get('linea');
  if (linea) filter = linea;
  apply();
}

$$('[data-thumb]').forEach(function(b){
  b.addEventListener('click', function(){
    var main = $('.gallery .main');
    if (!main) return;
    main.classList.remove('noimg');
    var img = main.querySelector('img');
    if (!img) return;
    img.removeAttribute('srcset');
    main.querySelectorAll('source').forEach(function(s){ s.removeAttribute('srcset'); });
    img.src = b.getAttribute('data-src');
    img.alt = b.getAttribute('data-alt') || img.alt;
    $$('[data-thumb]').forEach(function(x){ x.setAttribute('aria-current', String(x === b)); });
  });
});
$$('[data-q]').forEach(function(b){
  b.addEventListener('click', function(){
    var input = $('#pq'); if (!input) return;
    input.value = Math.max(1, Math.min(10, (+input.value || 1) + (+b.dataset.q)));
  });
});

/* ---------- cart (prototype; no checkout is connected) ---------- */
var cart = [];
try { cart = JSON.parse(localStorage.getItem('nhg-cart') || '[]').filter(function(l){ return byId[l.id]; }); } catch (e){ cart = []; }
function save(){ try { localStorage.setItem('nhg-cart', JSON.stringify(cart)); } catch (e){} }
function count(){ return cart.reduce(function(n,l){ return n + l.q; }, 0); }
function add(id, q){
  var item = byId[id]; if (!item) return;
  var line = cart.filter(function(x){ return x.id === id; })[0];
  if (line) line.q = Math.min(10, line.q + q); else cart.push({id:id, q:q});
  save(); renderCart(); toast(esc(item.title) + ' se añadió al carrito', true);
}
function renderCart(){
  var n = count();
  var badge = $('#cartCount'), btn = $('#cartBtn'), lines = $('#cartLines'), tot = $('#cartTotals');
  if (!badge || !lines) return;
  badge.textContent = n; badge.hidden = n === 0;
  if (btn) btn.setAttribute('aria-label', 'Abrir carrito, ' + n + (n === 1 ? ' obra' : ' obras'));
  if (!cart.length){
    lines.innerHTML = '<div class="empty"><p>El carrito está vacío.</p><a class="btn dark" href="/tienda/" data-close-cart>Visitar la tienda</a></div>';
    tot.innerHTML = ''; return;
  }
  lines.innerHTML = cart.map(function(l){
    var p = byId[l.id];
    return '<div class="line"><div class="img contain" data-label="' + esc(p.title) + '"><img src="' + esc(p.img) + '" alt="' + esc(p.artist + ', ' + p.title) + '" width="72" height="72" loading="lazy" decoding="async"></div>' +
      '<div><p class="a">' + esc(p.artist) + '</p><p class="t"><a href="/tienda/' + encodeURIComponent(p.id) + '/" data-close-cart style="text-decoration:none">' + esc(p.title) + '</a></p>' +
      '<div class="qty"><button type="button" data-lq="-1" data-id="' + esc(p.id) + '" aria-label="Reducir cantidad de ' + esc(p.title) + '">−</button><input type="number" value="' + l.q + '" min="1" max="10" data-li="' + esc(p.id) + '" aria-label="Cantidad de ' + esc(p.title) + '"><button type="button" data-lq="1" data-id="' + esc(p.id) + '" aria-label="Aumentar cantidad de ' + esc(p.title) + '">+</button></div>' +
      '<br><button class="rm" type="button" data-rm="' + esc(p.id) + '">Quitar</button></div>' +
      '<div class="p">' + money(p.price * l.q) + '</div></div>';
  }).join('');
  var sub = cart.reduce(function(s,l){ return s + byId[l.id].price * l.q; }, 0);
  tot.innerHTML = '<div class="row big"><span>Subtotal</span><span>' + money(sub) + ' USD</span></div>' +
    '<p class="note">El envío y los impuestos se calculan al pagar. El pago no está conectado en este prototipo.</p>' +
    '<button class="btn dark" type="button" id="checkout">Finalizar compra</button>';
  $$('.img', lines).forEach(function(box){
    var im = box.querySelector('img');
    if (!im) return;
    im.addEventListener('error', function(){ box.classList.add('noimg'); });
  });
}
document.addEventListener('click', function(e){
  var a = e.target.closest('[data-add]');
  if (a){
    var q = 1;
    if (a.dataset.qtyFrom){ var input = $(a.dataset.qtyFrom); q = Math.max(1, Math.min(10, +(input && input.value) || 1)); }
    add(a.dataset.add, q); return;
  }
  var lq = e.target.closest('[data-lq]');
  if (lq){ cart.forEach(function(l){ if (l.id === lq.dataset.id) l.q = Math.max(1, Math.min(10, l.q + (+lq.dataset.lq))); }); save(); renderCart(); return; }
  var rm = e.target.closest('[data-rm]');
  if (rm){ cart = cart.filter(function(l){ return l.id !== rm.dataset.rm; }); save(); renderCart(); var close = $('#cartClose'); if (close) close.focus(); return; }
  if (e.target.closest('[data-close-cart]')) openCart(false);
  if (e.target.id === 'checkout'){
    var body = $('#coBody');
    if (body) body.textContent = 'Este es el prototipo. El botón no abre un pago: en la tienda de Shopify llevaría al pago seguro con ' + count() + (count() === 1 ? ' obra' : ' obras') + '. El carrito queda guardado en este dispositivo.';
    var modal = $('#checkoutModal'); if (modal){ modal.hidden = false; var b = $('#coClose'); if (b) b.focus(); }
  }
  var cp = e.target.closest('[data-copy]');
  if (cp){
    var t = cp.dataset.copy;
    var done = function(){ var o = cp.textContent; cp.textContent = 'Copiado'; setTimeout(function(){ cp.textContent = o; }, 1200); };
    if (navigator.clipboard && navigator.clipboard.writeText) navigator.clipboard.writeText(t).then(done, function(){});
  }
});
document.addEventListener('change', function(e){
  if (e.target.dataset && e.target.dataset.li){
    var v = Math.max(1, Math.min(10, +e.target.value || 1));
    cart.forEach(function(l){ if (l.id === e.target.dataset.li) l.q = v; });
    save(); renderCart();
  }
});
var coClose = $('#coClose'), coContact = $('#coContact');
if (coClose) coClose.addEventListener('click', function(){ $('#checkoutModal').hidden = true; var c = $('#checkout'); if (c) c.focus(); });
if (coContact) coContact.addEventListener('click', function(){ $('#checkoutModal').hidden = true; openCart(false); });

var lastFocus = null;
function openCart(open){
  var drawer = $('#cart'), scrim = $('#cartScrim');
  if (!drawer || !scrim) return;
  drawer.hidden = !open; scrim.hidden = !open;
  if (open){ lastFocus = document.activeElement; $('#cartClose').focus(); }
  else if (lastFocus && lastFocus.focus) lastFocus.focus();
}
var cartBtn = $('#cartBtn'), cartClose = $('#cartClose'), cartScrim = $('#cartScrim');
if (cartBtn) cartBtn.addEventListener('click', function(){ openCart(true); });
if (cartClose) cartClose.addEventListener('click', function(){ openCart(false); });
if (cartScrim) cartScrim.addEventListener('click', function(){ openCart(false); });

var toastT;
function toast(html, withCart){
  var t = $('#toast'); if (!t) return;
  t.innerHTML = '<span>' + html + '</span>' + (withCart ? '<button type="button" id="toastView">Ver carrito</button>' : '');
  t.hidden = false; clearTimeout(toastT); toastT = setTimeout(function(){ t.hidden = true; }, 3200);
  var b = $('#toastView'); if (b) b.addEventListener('click', function(){ t.hidden = true; openCart(true); });
}

var mnav = $('#mnav'), menuBtn = $('#menuBtn');
function setMenu(open){
  if (!mnav || !menuBtn) return;
  mnav.hidden = !open; menuBtn.setAttribute('aria-expanded', String(open));
  document.body.style.overflow = open ? 'hidden' : '';
  if (open) $('#menuClose').focus(); else menuBtn.focus();
}
if (menuBtn) menuBtn.addEventListener('click', function(){ setMenu(true); });
var menuClose = $('#menuClose');
if (menuClose) menuClose.addEventListener('click', function(){ setMenu(false); });
if (mnav) mnav.addEventListener('click', function(e){ if (e.target.closest('a')){ mnav.hidden = true; document.body.style.overflow = ''; if (menuBtn) menuBtn.setAttribute('aria-expanded','false'); } });
document.addEventListener('keydown', function(e){
  if (e.key !== 'Escape') return;
  var modal = $('#checkoutModal');
  if (modal && !modal.hidden){ modal.hidden = true; return; }
  var drawer = $('#cart');
  if (drawer && !drawer.hidden){ openCart(false); return; }
  if (mnav && !mnav.hidden) setMenu(false);
});

/* Forms stay prototypes: mailto for contact, no list for the newsletter. */
var cform = $('#cform');
if (cform) cform.addEventListener('submit', function(e){
  e.preventDefault();
  var ok = true;
  [['#cname', function(v){ return v.trim().length > 0; }], ['#cemail', function(v){ return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(v); }]].forEach(function(pair){
    var el = $(pair[0]), good = pair[1](el.value), err = el.parentNode.querySelector('.err');
    err.hidden = good; el.setAttribute('aria-invalid', String(!good)); if (!good && ok){ el.focus(); ok = false; }
  });
  if (!ok) return;
  var body = $('#cmsg').value + '\n\n— ' + $('#cname').value + ' (' + $('#cemail').value + ')';
  var href = 'mailto:ninoskahuerta@gmail.com?subject=' + encodeURIComponent($('#csubj').value || 'Consulta desde el sitio') + '&body=' + encodeURIComponent(body);
  var m = $('#cformMsg'); m.hidden = false;
  m.innerHTML = 'Gracias, ' + esc($('#cname').value.split(' ')[0]) + '. Debería abrirse tu aplicación de correo con el mensaje. Si no se abre, escribe a <b>ninoskahuerta@gmail.com</b> o llama al +1 305 588 1231.';
  window.location.href = href;
});
var nform = $('#nform');
if (nform) nform.addEventListener('submit', function(e){
  e.preventDefault();
  var v = $('#nemail').value, m = $('#nmsg'); m.hidden = false;
  if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(v)){ m.textContent = 'Escribe un correo válido, como nombre@ejemplo.com.'; $('#nemail').focus(); return; }
  m.textContent = 'Gracias. Este boletín es un prototipo y no está conectado: ' + v + ' no se ha guardado en ninguna lista.';
  $('#nemail').value = '';
});

var hero = $('#hero');
function onScroll(){
  if (!hero) return;
  var onHero = window.scrollY < (hero.offsetHeight - 80);
  document.body.classList.toggle('on-hero', onHero);
}
if (hero){
  window.addEventListener('scroll', onScroll, {passive:true});
  onScroll();
}

renderCart();
})();

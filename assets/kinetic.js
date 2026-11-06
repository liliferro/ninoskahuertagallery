(function(){
  var cv = document.getElementById('field');
  if (!cv) return;
  var ctx = cv.getContext('2d', {alpha:false});
  var btn = document.getElementById('pause'), lbl = document.getElementById('pl'), ico = document.getElementById('pi');
  var reduce = window.matchMedia('(prefers-reduced-motion: reduce)');
  // Complementary pairs for the two faces of each lamella (left face / right face).
  var PAIRS = [
    ['#D9262B','#2E9A62'],  // red / green
    ['#2B4FC2','#EE8A24'],  // blue / orange
    ['#B8317A','#4FAE6A'],  // magenta / green
    ['#EE8A24','#2B4FC2'],  // orange / blue (inverted rhythm)
    ['#2E9A62','#D9262B']   // green / red
  ];
  var NEUTRAL = ['#E8E6E1','#1E1E1E'];
  function hex(h){h=h.replace('#','');return [parseInt(h.slice(0,2),16),parseInt(h.slice(2,4),16),parseInt(h.slice(4,6),16)];}
  function rgba(c,k,a){return 'rgba('+Math.round(c[0]*k)+','+Math.round(c[1]*k)+','+Math.round(c[2]*k)+','+a+')';}

  // 1-px-tall row buffers: everything purely vertical is drawn once per frame on a row, then stretched to full height.
  var row = document.createElement('canvas'), rctx = row.getContext('2d');
  var grat = document.createElement('canvas'), gctx = grat.getContext('2d');
  var W=0,H=0,dpr=1,mobile=false,N=64,slats=[],p1=7,p2=7.3,ang=6*Math.PI/180,R=130,AMP=13,frameMs=1000/60;

  function build(){
    mobile = window.innerWidth < 768;
    N = mobile ? 30 : Math.max(44, Math.min(72, Math.round(W/22)));
    p1 = mobile ? 9 : 7;
    p2 = p1 * 1.042;                     // 4.2% spacing difference
    ang = (mobile ? 5 : 6) * Math.PI/180;// plus a 5–6° tilt → moiré
    R = mobile ? 90 : 130;
    AMP = mobile ? 9 : 13;
    frameMs = 1000 / (mobile ? 30 : 60);
    slats = [];
    for (var i=0;i<=N;i++){
      // modules of 8: colour pairs alternate slat by slat, the module shifts the sequence; one neutral (white/black) lamella per module
      var g = (i + Math.floor(i/8)*2) % PAIRS.length, p = PAIRS[g];
      var neutral = (i % 8 === 7);
      var L = neutral ? NEUTRAL[0] : p[0], Rr = neutral ? NEUTRAL[1] : p[1];
      slats.push({L:hex(L), R:hex(Rr)});
    }
  }

  function resize(){
    var r = cv.getBoundingClientRect();
    W = Math.max(1, r.width); H = Math.max(1, r.height);
    dpr = Math.min(window.devicePixelRatio || 1, window.innerWidth < 768 ? 1.5 : 2);
    cv.width = Math.round(W*dpr); cv.height = Math.round(H*dpr);
    ctx.setTransform(dpr,0,0,dpr,0,0);
    row.width = grat.width = cv.width; row.height = grat.height = 1;
    rctx.setTransform(dpr,0,0,1,0,0); gctx.setTransform(dpr,0,0,1,0,0);
    build();
    if (!running) draw(performance.now());
  }

  // Viewer state: target from pointer, smoothed slowly.
  var tx=.38, ty=.5, sx=.38, sy=.5, mx=-9999, my=-9999, rip=0, ripT=0, lastMove=-1e9, inside=false;
  function onMove(e){
    var r = cv.getBoundingClientRect();
    mx = e.clientX - r.left; my = e.clientY - r.top;
    tx = Math.min(1, Math.max(0, mx / W)); ty = Math.min(1, Math.max(0, my / H));
    lastMove = performance.now(); inside = true;
    if (!running && !paused) start();
  }
  window.addEventListener('pointermove', onMove, {passive:true});
  document.addEventListener('pointerleave', function(){inside=false;});
  window.addEventListener('blur', function(){inside=false;});

  function draw(now){
    var t = now/1000;
    var idle = (now - lastMove) > 4000 || !inside;
    if (idle){                                   // no pointer: very slight oscillation
      tx = .42 + .16*Math.sin(t*.11);
      ty = .5 + .08*Math.sin(t*.07);
    }
    var ease = running ? .035 : 1;               // slow follow
    sx += (tx - sx)*ease; sy += (ty - sy)*ease;
    ripT = (!idle && inside) ? 1 : 0;
    rip += (ripT - rip)*(running ? .05 : 1);

    // ---------- Layer 1: Physichromie lamellae ----------
    var cw = W / N;
    var vx = W*(sx*1.3 - .15);                   // viewer position along the wall
    var k = (cw*.78) / (W*1.15);                 // depth/(Z-depth): face width per px of offset, unsaturated across the wall
    var shear = (sy - .5)*.34;                   // subtle vertical perspective
    var i, x0, tan0, tan1, aR, aL, g;
    rctx.fillStyle = '#121212'; rctx.fillRect(0,0,W,1);
    // reflected colour in each gap: right face of blade i mixes with left face of blade i+1
    for (i=0;i<N;i++){
      x0 = i*cw;
      tan0 = Math.max(-1, Math.min(1, (x0 - vx)/(W*.9)));
      tan1 = Math.max(-1, Math.min(1, (x0 + cw - vx)/(W*.9)));
      aR = .24 + .38*Math.max(0, -tan0);         // viewer right of blade i sees its right face lit
      aL = .24 + .38*Math.max(0, tan1);
      g = rctx.createLinearGradient(x0,0,x0+cw,0);
      g.addColorStop(0, rgba(slats[i].R,1,aR));
      g.addColorStop(.5, rgba([(slats[i].R[0]+slats[i+1].L[0])/2,(slats[i].R[1]+slats[i+1].L[1])/2,(slats[i].R[2]+slats[i+1].L[2])/2],1,(aR+aL)*.32));
      g.addColorStop(1, rgba(slats[i+1].L,1,aL));
      rctx.fillStyle = g; rctx.fillRect(x0,0,cw+.5,1);
    }
    ctx.imageSmoothingEnabled = false;
    ctx.drawImage(row, 0,0,row.width,1, 0,0,W,H);
    // the faces of the blades, projected toward the viewer
    for (i=0;i<=N;i++){
      x0 = i*cw;
      var f = (x0 - vx)*k;
      f = Math.max(-cw*.86, Math.min(cw*.86, f));
      var c = f > 0 ? slats[i].L : slats[i].R;
      var lit = .66 + .34*Math.min(1, Math.abs(f)/(cw*.7));
      var ft = f*(1 - shear), fb = f*(1 + shear);
      ctx.fillStyle = rgba(c, lit, 1);
      ctx.beginPath(); ctx.moveTo(x0,0); ctx.lineTo(x0+ft,0); ctx.lineTo(x0+fb,H); ctx.lineTo(x0,H); ctx.closePath(); ctx.fill();
      // edge of the blade (thin light line at its tip) and its root shadow
      ctx.strokeStyle = 'rgba(255,255,255,'+(.10 + .18*Math.min(1,Math.abs(f)/cw))+')';
      ctx.lineWidth = 1;
      ctx.beginPath(); ctx.moveTo(x0+ft,0); ctx.lineTo(x0+fb,H); ctx.stroke();
      ctx.strokeStyle = 'rgba(0,0,0,.55)'; ctx.lineWidth = 1.2;
      ctx.beginPath(); ctx.moveTo(x0,0); ctx.lineTo(x0,H); ctx.stroke();
    }

    // fine vertical grating fixed to the wall (moves with the lamellae)
    var o1 = -((sx - .5)*28) % p1;
    gctx.clearRect(0,0,W,1); gctx.fillStyle = 'rgba(8,8,8,.5)';
    var lw = p1*.32;
    for (var x = o1 - p1; x < W + p1; x += p1){ gctx.fillRect(x - lw/2, 0, lw, 1); }
    ctx.drawImage(grat, 0,0,grat.width,1, 0,0,W,H);

    // ---------- Layer 2: Chromointerférence / Soto vibration ----------
    var ca = Math.cos(ang), sa = Math.sin(ang);        // line direction d=(sa,ca); normal n=(ca,-sa)
    var cx = W/2, cy = H/2;
    var o2 = -((sx - .5)*11) - ((sy - .5)*6);           // parallax: slower than layer 1
    var span = Math.sqrt(W*W + H*H)/2 + p2*2;
    // cursor in rotated space (u along normal, v along line)
    var pmx = (rip > .01) ? mx : -1e5, pmy = (rip > .01) ? my : -1e5;
    var cu = (pmx - cx)*ca - (pmy - cy)*sa, cvv = (pmx - cx)*sa + (pmy - cy)*ca;
    var A = AMP*rip, R2 = R*R, step = mobile ? 10 : 7;
    ctx.strokeStyle = 'rgba(236,234,229,.36)'; ctx.lineWidth = mobile ? 1.2 : 1.05;
    ctx.beginPath();
    var start = Math.floor((-span - o2)/p2), end = Math.ceil((span - o2)/p2);
    for (var n = start; n <= end; n++){
      var u = n*p2 + o2;
      var du = u - cu;
      if (A < .2 || Math.abs(du) > R*2.4){               // far from cursor: straight line
        ctx.moveTo(cx + u*ca + (-span)*sa, cy - u*sa + (-span)*ca);
        ctx.lineTo(cx + u*ca + span*sa,    cy - u*sa + span*ca);
        continue;
      }
      var first = true;
      for (var v = -span; v <= span + step; v += step){
        var dv = v - cvv, d2 = du*du + dv*dv, push = 0;
        if (d2 < R2*6){
          var e = Math.exp(-d2/R2);
          // opens the lines like a soft penetrable + a faint ring
          push = (du >= 0 ? 1 : -1)*A*e + A*.18*Math.exp(-d2/(R2*3))*Math.sin(Math.sqrt(d2)*.07 - t*1.4);
        }
        var uu = u + push;
        var px = cx + uu*ca + v*sa, py = cy - uu*sa + v*ca;
        if (first){ ctx.moveTo(px,py); first=false; } else ctx.lineTo(px,py);
      }
    }
    ctx.stroke();
  }


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

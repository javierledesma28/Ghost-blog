#!/usr/bin/env python3
"""
Post Marquee — filas horizontales estilo Supabase 'Join the community'.
Inyecta CSS + JS en Ghost via codeinjection_head/foot en la DB.

El <div id="pmq-root"></div> está hardcodeado en:
  /var/lib/ghost/current/content/themes/source/home.hbs
  (entre {{> "components/cta"}} y {{> "components/post-list" ...}})

El JS carga los posts desde la Content API y renderiza 4 filas animadas.

Uso:
    python3 inject_marquee.py
"""

import subprocess

def read_env():
    with open('/home/javierledesma/docker/ghost-blog/.env') as f:
        return dict(l.strip().split('=',1) for l in f if '=' in l and not l.startswith('#'))

ENV         = read_env()
GHOST_URL   = ENV['GHOST_URL']
CONTENT_KEY = '9d053295e3096a4e81b30910d7'

def sql(query):
    r = subprocess.run(
        ['docker','exec','ghost-db','mysql','--default-character-set=utf8mb4',
         f'-u{ENV["MYSQL_USER"]}', f'-p{ENV["MYSQL_PASSWORD"]}', ENV['MYSQL_DATABASE'],
         '-se', query],
        capture_output=True, text=True, encoding='utf-8'
    )
    if 'ERROR' in r.stderr and 'Warning' not in r.stderr:
        print(f"  SQL ERROR: {r.stderr.strip()}")
    return r.stdout.strip()

def esc_sql(s):
    return s.replace('\\', '\\\\').replace("'", "\\'")

# ── CSS ────────────────────────────────────────────────────────────────────────
CSS = """<style id="pmq-css">
/* ── Override variable raíz de Ghost ── */
:root{--background-color:#0f0f0f!important}
/* ── Fondo global ── */
html,body{background:#0f0f0f!important;color:#e0e0e0!important}
.gh-viewport,.gh-main,.gh-outer,.gh-inner,.gh-container,.gh-article,.gh-content,
.gh-head,.gh-foot,.gh-canvas,.gh-hero,.gh-hero-inner,.gh-header,.gh-header-inner,
.gh-cta,.gh-cta-inner,.gh-cta-wrapper,
section,header,footer,main{background:#0f0f0f!important}
.gh-hero::before,.gh-hero::after,
.gh-cta::before,.gh-cta::after,
.gh-header::before,.gh-header::after{background:#0f0f0f!important}

/* ── Navegación ── */
.gh-navigation,.gh-navigation-inner,.gh-navigation-brand{background:#0f0f0f!important}
.gh-navigation-logo{color:#fff!important}
.gh-navigation-menu a{color:#aaa!important}
.gh-navigation-menu a:hover{color:#fff!important}
.gh-navigation-actions a,.gh-navigation-members a{color:#aaa!important}
.gh-navigation-actions a:hover,.gh-navigation-members a:hover{color:#fff!important}
.gh-navigation svg,.gh-navigation-actions svg{color:#aaa!important;fill:#aaa!important}

/* ── Hero / CTA ── */
.gh-hero-title,.gh-hero h1,.gh-hero h2{color:#fff!important}
.gh-hero-description,.gh-hero p{color:#888!important}
.gh-cta-title{color:#fff!important}
.gh-cta-description{color:#888!important}

/* ── Tarjetas de posts (lista) ── */
.gh-card{background:transparent!important;border:none!important;box-shadow:none!important}
.gh-card-link:hover .gh-card-title{color:#fff!important}
.gh-card-title{color:#e8e8e8!important;font-weight:600!important}
.gh-card-excerpt{color:#888!important}
.gh-card-meta,.gh-card-meta *,.gh-card-footer,.gh-card-footer *{color:#555!important}

/* ── Imágenes de post: sin box de fondo ── */
.gh-card-image,.gh-card-image-wrapper{background:#1a1a1a!important;border-radius:8px!important;overflow:hidden!important}

/* ── Featured posts ── */
.gh-featured-card{background:#141414!important;border:1px solid #1e1e1e!important;border-radius:12px!important}
.gh-featured-title{color:#fff!important}

/* ── Footer ── */
.gh-footer,.gh-footer-inner{background:#0f0f0f!important}
.gh-footer-logo{color:#fff!important}
.gh-footer-signup-header{color:#fff!important}
.gh-footer-signup-subhead{color:#888!important}
.gh-footer-menu a{color:#aaa!important}
.gh-footer-menu a:hover{color:#fff!important}
.gh-footer-copyright,.gh-footer-copyright a{color:#555!important}
.gh-footer-bar,.gh-footer-bar *{color:#555!important}
[class*="gh-powered"],[class*="gh-powered"] *{color:#555!important}

/* ── Separadores ── */
hr,.gh-divider{border-color:#1e1e1e!important}

/* ── About: ocultar título "About this site" ── */
.page-about .gh-article-title{display:none!important}

/* ── See all → mismo color que LATEST ── */
.gh-more a,.gh-more a *{color:#e8e8e8!important}
.gh-more a:hover,.gh-more a:hover *{color:#fff!important}

/* ── Post feed: solo 3 items ── */
.gh-feed .gh-card:nth-child(n+4),
.gh-postfeed .gh-card:nth-child(n+4){display:none!important}
.gh-feed-seeall,.gh-pagenavigation,.view-all{display:none!important}

/* ── Marquee ── */
#pmq-root{display:block!important;width:100%!important;background:#0f0f0f;padding:40px 0 60px;overflow:hidden;box-sizing:border-box}
.pmq-header{text-align:center;margin-bottom:40px;padding:0 24px}
/* Filas marquee */
.pmq-rows{width:100%;overflow:hidden;display:flex;flex-direction:column;gap:16px;-webkit-mask-image:linear-gradient(to right,transparent 0%,black 8%,black 92%,transparent 100%),linear-gradient(to bottom,transparent 0%,black 12%,black 88%,transparent 100%);-webkit-mask-composite:source-in;mask-image:linear-gradient(to right,transparent 0%,black 8%,black 92%,transparent 100%),linear-gradient(to bottom,transparent 0%,black 12%,black 88%,transparent 100%);mask-composite:intersect}
.pmq-rows:hover .pmq-track{animation-play-state:paused!important}
.pmq-row{overflow:hidden;padding:4px 0}
.pmq-track{display:flex;flex-direction:row;gap:16px;animation:marquee-left var(--dur,35s) linear infinite;will-change:transform}
.pmq-track.reverse{animation-name:marquee-right}
/* Cards */
.pmq-card{flex-shrink:0;width:300px;background:#1c1c1c;border:1px solid #2e2e2e;border-radius:12px;padding:18px;text-decoration:none!important;color:#fff!important;display:block;font-family:sans-serif}
.pmq-card:hover{background:#242424;border-color:#404040}
.pmq-avatar{width:36px;height:36px;border-radius:50%;flex-shrink:0;background-size:cover!important;background-position:center!important;display:inline-flex;align-items:center;justify-content:center;font-size:11px;font-weight:700;color:#fff;vertical-align:middle;margin-right:10px}
.pmq-card-top{display:flex;align-items:center;margin-bottom:12px}
.pmq-card-name{font-size:13px;font-weight:600}
.pmq-card-date{font-size:11px;color:#666;margin-left:auto}
.pmq-card-text{font-size:13px;color:#bbb;line-height:1.5;margin:0;display:-webkit-box;-webkit-line-clamp:3;-webkit-box-orient:vertical;overflow:hidden;text-align:center!important}
@keyframes marquee-left{from{transform:translateX(0)}to{transform:translateX(-50%)}}
@keyframes marquee-right{from{transform:translateX(-50%)}to{transform:translateX(0)}}

/* ── Post meta: fecha, tiempo de lectura, share ── */
.gh-article-meta,.gh-article-meta *,
.post-meta,.post-meta *{
  color:#666!important;font-weight:400!important;
  font-size:13px!important;background:transparent!important;
  box-shadow:none!important;transform:none!important;
}
.gh-article-date,.gh-article-readtime,
time,.post-date,.reading-time{
  color:#555!important;font-weight:400!important;
}
/* Share button — múltiples selectores para cubrir versiones de Ghost Source */
.gh-article-share,
.gh-article-actions{
  display:flex!important;align-items:center!important;
}
.gh-article-share a,
.gh-article-share button,
.gh-article-share .gh-share-button,
.gh-article-actions a,
.gh-article-actions button,
button.gh-share-button,
a.gh-share-button{
  color:#e0e0e0!important;font-weight:500!important;
  background:transparent!important;text-decoration:none!important;
  box-shadow:none!important;
  border:1px solid #444!important;border-radius:6px!important;
  padding:6px 16px!important;font-size:13px!important;
  display:inline-flex!important;align-items:center!important;gap:6px!important;
  transition:color .2s,border-color .2s,background .2s!important;
  cursor:none!important;
}
.gh-article-share a:hover,
.gh-article-share button:hover,
.gh-article-share .gh-share-button:hover,
.gh-article-actions a:hover,
.gh-article-actions button:hover,
button.gh-share-button:hover{
  color:#fff!important;border-color:#666!important;
  background:#1a1a1a!important;
}

/* ── Todas las imágenes en posts: hover zoom + overlay Azure ── */
/* cualquier figure/card dentro del contenido de un artículo */
.gh-content figure,
.gh-content .kg-card,
.gh-content .kg-image-card,
.gh-content .kg-gallery-image,
figure.kg-card{
  overflow:hidden!important;
  position:relative!important;
  border-radius:8px!important;
  display:block!important;
}
/* la imagen en sí */
.gh-content figure img,
.gh-content .kg-card img,
.gh-content img,
figure.kg-card img{
  transition:transform .45s ease,filter .45s ease!important;
  display:block!important;
}
/* zoom + brillo al hover sobre el contenedor */
.gh-content figure:hover img,
.gh-content .kg-card:hover img,
figure.kg-card:hover img{
  transform:scale(1.05)!important;
  filter:brightness(1.1)!important;
}
/* overlay Azure */
.gh-content figure::after,
.gh-content .kg-card::after,
figure.kg-card::after{
  content:'';position:absolute;inset:0;
  background:linear-gradient(135deg,rgba(0,120,212,0.18) 0%,transparent 60%);
  opacity:0;transition:opacity .35s ease;
  pointer-events:none;border-radius:inherit;
}
.gh-content figure:hover::after,
.gh-content .kg-card:hover::after,
figure.kg-card:hover::after{opacity:1}

/* ── Latest cards: hover interactivo ── */
.gh-card{transition:transform .28s ease,box-shadow .28s ease!important}
.gh-card:hover{
  transform:translateY(-3px)!important;
  box-shadow:0 8px 32px rgba(0,0,0,0.5)!important;
}
/* zoom en imagen */
.gh-card-image,.gh-card-image-wrapper{
  overflow:hidden!important;position:relative!important;
}
.gh-card-image img,.gh-card-image-wrapper img{
  transition:transform .45s ease,filter .45s ease!important;
  display:block!important;
}
.gh-card:hover .gh-card-image img,
.gh-card:hover .gh-card-image-wrapper img{
  transform:scale(1.07)!important;
  filter:brightness(1.1)!important;
}
/* overlay Azure sutil */
.gh-card-image::after,.gh-card-image-wrapper::after{
  content:'';position:absolute;inset:0;
  background:linear-gradient(135deg,rgba(0,120,212,0.18) 0%,transparent 65%);
  opacity:0;transition:opacity .35s ease;pointer-events:none;
}
.gh-card:hover .gh-card-image::after,
.gh-card:hover .gh-card-image-wrapper::after{opacity:1}
/* título se ilumina */
.gh-card:hover .gh-card-title{color:#fff!important}

/* ── Post nav arrows ── */
.pnav-arrow{position:fixed;top:50%;transform:translateY(-50%);z-index:999;display:flex;align-items:center;justify-content:center;width:32px;height:80px;background:rgba(255,255,255,0.06);border:1px solid rgba(255,255,255,0.1);border-radius:6px;color:#aaa;cursor:pointer;text-decoration:none!important;transition:background .2s,border-color .2s,color .2s,opacity .2s;opacity:0.5}
.pnav-arrow:hover{background:rgba(255,255,255,0.14);border-color:rgba(255,255,255,0.25);color:#fff;opacity:1}
.pnav-arrow.pnav-prev{left:12px}
.pnav-arrow.pnav-next{right:12px}
.pnav-arrow svg{width:18px;height:18px;flex-shrink:0}

/* ── Reading progress bar — Azure ── */
#rpb{position:fixed;top:0;left:0;width:0%;height:2px;background:linear-gradient(to right,#0078D4,#50b4f8);z-index:9999;transition:width .1s linear;pointer-events:none}

/* ── Dot grid overlay on hero ── */
.gh-hero,.gh-cta{position:relative!important;overflow:hidden!important}
.gh-hero::before,.gh-cta::before{content:'';position:absolute;inset:0;background-image:radial-gradient(rgba(255,255,255,0.045) 1px,transparent 1px);background-size:24px 24px;pointer-events:none;z-index:0!important;background-color:transparent!important}
.gh-hero-inner,.gh-cta-inner,.gh-cta-wrapper{position:relative;z-index:1!important}

/* ── Footer CTA: igualar estilos al hero ── */
.gh-cta{background:#0f0f0f!important}
.gh-cta-title{color:#fff!important;font-weight:700!important}
.gh-cta-description{color:#888!important}
.gh-cta .gh-btn,.gh-cta [data-portal]{
  background:#FF1A75!important;color:#fff!important;
  border:none!important;border-radius:999px!important;
  padding:12px 28px!important;font-size:15px!important;font-weight:600!important;
}
.cta-form-wrap{
  display:flex;align-items:center;
  width:100%;max-width:440px;
  margin:0 auto 20px;
  background:#fff;border-radius:999px;
  padding:6px 6px 6px 20px;box-sizing:border-box;
}
.cta-form-wrap input[type=email]{
  flex:1;border:none;outline:none;background:transparent;
  color:#111;font-size:15px;min-width:0;cursor:text!important;
}
.cta-form-wrap input[type=email]::placeholder{color:#aaa}
.cta-form-wrap .cta-sub-btn{
  flex-shrink:0;padding:10px 24px;
  background:#FF1A75;color:#fff;
  border:none;border-radius:999px;
  font-size:15px;font-weight:600;cursor:pointer!important;
  transition:background .2s;
}
.cta-form-wrap .cta-sub-btn:hover{background:#e0165f}

/* mega-menu completamente opaco e isolado del canvas blend-mode */
#mega-menu{
  z-index:10000!important;
  background:#080808!important;
  isolation:isolate!important;
  -webkit-isolation:isolate!important;
  backdrop-filter:none!important;
}

/* ── About page: tag / chip animations ── */
.page-about .gh-content a,.page-about .gh-content code,.page-about .gh-content strong{
  display:inline-block;
  transition:transform .22s ease,box-shadow .22s ease,color .22s ease;
}
.page-about .gh-content a:hover{
  transform:translateY(-2px) scale(1.04);
  box-shadow:0 0 0 1px rgba(0,120,212,0.45),0 4px 16px rgba(0,120,212,0.25);
  color:#4db8ff!important;
}
.page-about .gh-content code{
  background:#141414!important;border:1px solid #2a2a2a!important;
  border-radius:5px!important;padding:2px 7px!important;color:#7dd3f8!important;
  font-size:.88em!important;
}
.page-about .gh-content code:hover{
  border-color:#0078D4!important;
  box-shadow:0 0 8px rgba(0,120,212,0.35)!important;
}
/* Entrada animada de todos los elementos del about */
.page-about .anim-in{
  opacity:0;transform:translateY(18px) scale(0.97);
  transition:opacity .55s ease,transform .55s ease;
}
.page-about .anim-in.anim-done{opacity:1;transform:none}

/* ── Scanline sweep on hero ── */
.gh-hero::after{content:'';position:absolute;left:0;width:100%;height:2px;background:linear-gradient(to right,transparent,rgba(255,255,255,0.06),transparent);pointer-events:none;z-index:2;animation:ow-scan 6s linear infinite;background-color:transparent!important}
@keyframes ow-scan{0%{top:-2%}100%{top:102%}}

/* ── Corner reticles on marquee cards ── */
.pmq-card{position:relative!important}
.pmq-cr{position:absolute;width:10px;height:10px;border-color:rgba(255,255,255,0.2);border-style:solid;pointer-events:none;transition:border-color .2s}
.pmq-card:hover .pmq-cr{border-color:rgba(255,255,255,0.5)}
.pmq-cr-tl{top:6px;left:6px;border-width:1px 0 0 1px}
.pmq-cr-tr{top:6px;right:6px;border-width:1px 1px 0 0}
.pmq-cr-bl{bottom:6px;left:6px;border-width:0 0 1px 1px}
.pmq-cr-br{bottom:6px;right:6px;border-width:0 1px 1px 0}

/* ── Glitch animation ── */
@keyframes ow-glitch{
  0%{clip-path:inset(40% 0 50% 0);transform:translate(-2px,1px);filter:hue-rotate(90deg) contrast(1.8)}
  20%{clip-path:inset(70% 0 10% 0);transform:translate(2px,-1px);filter:hue-rotate(180deg)}
  40%{clip-path:inset(20% 0 70% 0);transform:translate(-1px,2px);filter:none}
  60%{clip-path:inset(55% 0 25% 0);transform:translate(1px,-2px);filter:hue-rotate(270deg)}
  80%{clip-path:inset(10% 0 80% 0);transform:translate(-2px,0px);filter:contrast(1.5)}
  100%{clip-path:inset(0% 0 0% 0);transform:translate(0,0);filter:none}
}
.gh-glitch{animation:ow-glitch 0.3s step-end 1}

/* ── Scroll reveal ── */
.sv{opacity:0;transform:translateY(28px);transition:opacity .65s ease,transform .65s ease}
.sv.sv-in{opacity:1;transform:translateY(0)}

/* ── Subscribe button glow ── */
[data-portal]:hover,.gh-btn:hover,.gh-cta-button:hover,button[data-portal]:hover{
  box-shadow:0 0 0 1px rgba(0,120,212,0.5),0 0 20px rgba(0,120,212,0.35),0 0 40px rgba(0,120,212,0.15)!important;
  border-color:rgba(0,120,212,0.6)!important;
  transition:box-shadow .3s,border-color .3s,transform .2s!important;
  transform:translateY(-1px)!important
}
[data-portal],[data-portal]:focus{outline:none!important}

/* ── Blinking cursor on hero title ── */
@keyframes cur-blink{0%,100%{opacity:1}50%{opacity:0}}
.gh-cursor-blink{display:inline-block;margin-left:2px;animation:cur-blink 1s step-end infinite;color:inherit;font-weight:inherit;line-height:1}

/* ── About page section reveals ── */
.page-about .gh-content>*{opacity:0;transform:translateY(22px);transition:opacity .7s ease,transform .7s ease}
.page-about .gh-content>.revealed{opacity:1;transform:none}

/* ── Ocultar Subscribe nativo del nav ── */
.gh-navigation-actions a[data-portal="signup"],.gh-navigation-actions a.gh-button{display:none!important}

/* ── Hamburger button ── */
#hbg-btn{display:flex;flex-direction:column;justify-content:center;align-items:center;gap:5px;width:36px;height:36px;background:transparent;border:1px solid #2a2a2a;border-radius:6px;cursor:none;flex-shrink:0;transition:border-color .2s,background .2s}
#hbg-btn:hover{border-color:#444;background:#1a1a1a}
#hbg-btn span{display:block;width:16px;height:1.5px;background:#aaa;border-radius:2px;transition:background .2s}
#hbg-btn:hover span,#hbg-btn.active span{background:#fff}
#hbg-btn.active span:nth-child(1){transform:translateY(6.5px) rotate(45deg)}
#hbg-btn.active span:nth-child(2){opacity:0}
#hbg-btn.active span:nth-child(3){transform:translateY(-6.5px) rotate(-45deg)}
#hbg-btn span{transition:transform .2s,opacity .15s,background .2s}

/* ── Mega menu ── */
#mega-menu{position:fixed;top:0;left:0;right:0;z-index:9990;background:#0a0a0a;border-bottom:1px solid #1e1e1e;padding:72px 40px 40px;opacity:0;pointer-events:none;transform:translateY(-10px);transition:opacity .25s,transform .25s}
#mega-menu.open{opacity:1;pointer-events:auto;transform:translateY(0)}
#mega-menu .mm-inner{max-width:1100px;margin:0 auto;display:flex;gap:60px;align-items:flex-start}
#mega-menu .mm-col{flex:1;min-width:0}
#mega-menu .mm-col-wide{flex:2}
#mega-menu .mm-label{font-size:9px;letter-spacing:.35em;color:#444;text-transform:uppercase;font-family:monospace;margin-bottom:16px}
#mega-menu .mm-links{display:flex;flex-direction:column;gap:8px}
#mega-menu .mm-link{font-size:15px;color:#aaa;text-decoration:none!important;transition:color .15s;padding:2px 0}
#mega-menu .mm-link:hover{color:#fff}
#mega-menu .mm-tags{display:flex;flex-wrap:wrap;gap:8px}
#mega-menu .mm-tag{display:inline-flex;align-items:center;gap:6px;padding:5px 12px;border-radius:6px;border:1px solid;font-size:12px;font-weight:600;text-decoration:none!important;transition:opacity .15s,transform .15s}
#mega-menu .mm-tag:hover{opacity:.8;transform:translateY(-1px)}
#mega-menu .mm-dot{width:6px;height:6px;border-radius:50%;flex-shrink:0}
#mega-menu .mm-ctas{display:flex;flex-direction:column;gap:10px;align-items:flex-end}
#mega-menu .mm-cta-primary{display:inline-flex;align-items:center;gap:8px;padding:10px 22px;background:#0078D4;color:#fff!important;border-radius:999px;font-size:13px;font-weight:600;text-decoration:none!important;transition:background .2s}
#mega-menu .mm-cta-primary:hover{background:#0066b8}
#mega-menu .mm-cta-secondary{display:inline-flex;align-items:center;gap:8px;padding:10px 22px;background:#1a1a1a;color:#fff!important;border:1px solid #2a2a2a;border-radius:999px;font-size:13px;font-weight:600;text-decoration:none!important;transition:background .2s,border-color .2s}
#mega-menu .mm-cta-secondary:hover{background:#242424;border-color:#3a3a3a}
.gh-search{position:relative}

/* ── Tag panel (search hover) ── */
#tag-panel{position:fixed;z-index:10001;background:#111;border:1px solid #2a2a2a;border-radius:12px;padding:16px;min-width:280px;max-width:360px;box-shadow:0 8px 32px rgba(0,0,0,0.5);opacity:0;pointer-events:none;transform:translateY(-6px);transition:opacity .2s,transform .2s;display:block}
#tag-panel.open{opacity:1;pointer-events:auto;transform:translateY(0)}
.tp-label{color:#666;font-size:11px;font-weight:600;letter-spacing:.08em;text-transform:uppercase;margin-bottom:10px}
.tp-grid{display:flex;flex-wrap:wrap;gap:6px}
.tp-tag{display:inline-flex;align-items:center;gap:5px;padding:4px 10px;border-radius:6px;border:1px solid;font-size:12px;font-weight:600;text-decoration:none!important;transition:opacity .15s,transform .15s}
.tp-tag:hover{opacity:.8;transform:translateY(-1px)}
.tp-dot{width:5px;height:5px;border-radius:50%;flex-shrink:0}
.tp-cr{position:absolute;width:6px;height:6px;border-color:#2a2a2a;border-style:solid}
.tp-tl{top:6px;left:6px;border-width:1px 0 0 1px}
.tp-tr{top:6px;right:6px;border-width:1px 1px 0 0}
.tp-bl{bottom:6px;left:6px;border-width:0 0 1px 1px}
.tp-br{bottom:6px;right:6px;border-width:0 1px 1px 0}

/* ── Custom cursor (cross/crosshair) — solo en dispositivos con mouse ── */
@media (hover:hover) and (pointer:fine){
  *{cursor:none!important}
  #csr{position:fixed;top:0;left:0;width:1px;height:1px;pointer-events:none;z-index:99999;will-change:transform;opacity:1;transition:opacity .15s}
  #csr::before,#csr::after{content:'';position:absolute;background:rgba(210,210,210,0.75);border-radius:1px;transition:width .22s ease,height .22s ease,left .22s ease,top .22s ease,background .22s}
  #csr::before{width:1px;height:28px;left:0px;top:-14px}
  #csr::after{height:1px;width:28px;top:0px;left:-14px}
  #csr.csr-link::before{height:42px;top:-21px;background:rgba(255,26,117,0.85)}
  #csr.csr-link::after{width:42px;left:-21px;background:rgba(255,26,117,0.85)}
  #csr.csr-hidden{opacity:0}
}
</style>"""

# ── JS ─────────────────────────────────────────────────────────────────────────
FOOT = f"""<script>
(function(){{
  var GU='{GHOST_URL}',KEY='{CONTENT_KEY}';
  var root=document.getElementById('pmq-root');
  if(!root)return;

  var TC={{azure:'#0078D4',ia:'#a855f7',lvl100:'#22c55e',lvl200:'#eab308',lvl300:'#ef4444',
          noticias:'#f97316',arquitectura:'#06b6d4',networking:'#3b82f6',iot:'#84cc16',
          electronica:'#a78bfa',natural:'#10b981',scripting:'#f59e0b',seguridad:'#ec4899',
          google:'#34d399','soft skills':'#fb7185',default:'#6366f1'}};
  function tc(n){{return TC[(n||'').toLowerCase().replace(/[^a-z0-9 ]/g,'').trim()]||TC.default;}}
  function fd(iso){{try{{return new Date(iso).toLocaleDateString('es-AR',{{day:'numeric',month:'short',year:'numeric'}});}}catch(e){{return '';}}}}

  function buildCard(p){{
    var tag=p.tags&&p.tags[0]?p.tags[0]:{{name:'Blog'}};
    var c=tc(tag.name);
    var ini=tag.name.slice(0,2).toUpperCase();
    var av=p.feature_image?'background:url('+p.feature_image+') center/cover':'background:linear-gradient(135deg,'+c+'66,'+c+'aa)';
    var title=p.title?p.title.slice(0,80)+(p.title.length>80?'…':''):'';
    var cr='<span class="pmq-cr pmq-cr-tl"></span><span class="pmq-cr pmq-cr-tr"></span><span class="pmq-cr pmq-cr-bl"></span><span class="pmq-cr pmq-cr-br"></span>';
    return '<a class="pmq-card" href="'+GU+'/'+p.slug+'/" target="_blank">'
      +cr
      +'<div class="pmq-card-top">'
      +'<div class="pmq-avatar" style="'+av+'">'+(p.feature_image?'':'<span>'+ini+'</span>')+'</div>'
      +'<span class="pmq-card-name" style="color:'+c+'">'+tag.name+'</span>'
      +'<span class="pmq-card-date">'+fd(p.published_at)+'</span>'
      +'</div>'
      +'<p class="pmq-card-text">'+title+'</p>'
      +'</a>';
  }}

  function buildTrack(posts,reverse){{
    var t=document.createElement('div');
    t.className='pmq-track'+(reverse?' reverse':'');
    t.style.setProperty('--dur',(reverse?28:35)+'s');
    var html=posts.map(buildCard).join('');
    t.innerHTML=html+html;
    return t;
  }}

  function buildRow(posts,reverse){{
    var r=document.createElement('div');r.className='pmq-row';
    r.appendChild(buildTrack(posts,reverse));
    return r;
  }}

  root.innerHTML=
    '<div class="pmq-header">'
    +'<h2 class="pmq-title">Explorá todos los posts</h2>'
    +'</div>'
    +'<div id="pmq-rows"></div>';

  var limit=parseInt(root.getAttribute('data-limit')||'0',10)||0;
  var numRows=parseInt(root.getAttribute('data-rows')||'4',10)||4;

  fetch(GU+'/ghost/api/content/posts/?key='+KEY+'&limit=all&include=tags&fields=title,slug,feature_image,published_at')
    .then(function(r){{return r.json();}})
    .then(function(j){{
      var all=(j.posts||[]).filter(function(p){{return p.slug!=='coming-soon';}});
      if(limit>0)all=all.slice(0,limit);
      if(!all.length)return;
      var rows=document.getElementById('pmq-rows');
      if(!rows)return;
      function shuffle(arr,offset){{
        var a=arr.slice();
        for(var i=a.length-1;i>0;i--){{
          var j=Math.floor((Math.sin(i*9301+offset*49297+233)*0.5+0.5)*(i+1));
          var t=a[i];a[i]=a[j];a[j]=t;
        }}
        return a;
      }}
      var dirs=[false,true,false,true];
      for(var i=0;i<numRows;i++){{
        rows.appendChild(buildRow(shuffle(all,i+1),dirs[i%2]));
      }}
    }})
    .catch(function(e){{
      var rows=document.getElementById('pmq-rows');
      if(rows)rows.innerHTML='<p style="color:#666;text-align:center;padding:20px">'+e+'</p>';
    }});
}})();

/* ── Particle sphere — solo homepage ── */
(function(){{
  if(!document.body.classList.contains('home-template'))return;
  /* crear canvas incondicionalmente */
  var c=document.createElement('canvas');
  c.id='psphere';
  var W=window.innerWidth,H=window.innerHeight;
  c.width=W; c.height=H;
  c.style.position='fixed';
  c.style.top='0'; c.style.left='0';
  c.style.width=W+'px'; c.style.height=H+'px';
  c.style.pointerEvents='none';
  c.style.zIndex='9998';
  c.style.mixBlendMode='screen';
  document.body.appendChild(c);
  var ctx=c.getContext('2d');

  window.addEventListener('resize',function(){{
    W=c.width=window.innerWidth;
    H=c.height=window.innerHeight;
    c.style.width=W+'px'; c.style.height=H+'px';
  }},{{passive:true}});

  /* posición fija: centro horizontal, 38% vertical */
  var OX=W*0.5, OY=H*0.38, R=Math.min(W*0.22,220);

  /* 400 partículas en esfera */
  var N=400,pts=[];
  for(var i=0;i<N;i++){{
    var th=Math.random()*6.283;
    var ph=Math.acos(2*Math.random()-1);
    pts.push({{
      ox:Math.sin(ph)*Math.cos(th),
      oy:Math.sin(ph)*Math.sin(th),
      oz:Math.cos(ph),
      pr:0.8+Math.random()*2.2,
      col:Math.random()<0.6
    }});
  }}

  var rx=0,ry=0,trx=0.08,trY=0,autoY=0,mx=0.5,my=0.5;
  document.addEventListener('mousemove',function(e){{
    mx=e.clientX/window.innerWidth;
    my=e.clientY/window.innerHeight;
  }},{{passive:true}});

  /* fade out al scrollear — no actúa si el mega-menu está abierto */
  window.addEventListener('scroll',function(){{
    var mm=document.getElementById('mega-menu');
    if(mm&&mm.classList.contains('open'))return;
    if(c.style.display==='none')return;
    var s=window.scrollY||window.pageYOffset;
    c.style.opacity=Math.max(0,1-s/(H*0.45)).toFixed(3);
  }},{{passive:true}});

  (function frame(){{
    ctx.clearRect(0,0,W,H);
    autoY+=0.002;
    trx=(my-0.5)*0.5;
    trY=autoY+(mx-0.5)*0.7;
    rx+=(trx-rx)*0.035; ry+=(trY-ry)*0.035;
    var cX=Math.cos(rx),sX=Math.sin(rx),cY=Math.cos(ry),sY=Math.sin(ry);
    var proj=[];
    for(var i=0;i<pts.length;i++){{
      var p=pts[i];
      var x1=p.ox*cY+p.oz*sY;
      var z1=-p.ox*sY+p.oz*cY;
      var y2=p.oy*cX-z1*sX;
      var z2=p.oy*sX+z1*cX;
      var sc=500/(500+z2*R);
      proj.push({{sx:OX+x1*R*sc,sy:OY+y2*R*sc,z:z2,r:p.pr*sc,col:p.col}});
    }}
    proj.sort(function(a,b){{return a.z-b.z;}});
    for(var j=0;j<proj.length;j++){{
      var q=proj[j];
      var d=(q.z+1)*0.5;
      var al=0.25+d*0.75;
      ctx.beginPath();
      ctx.arc(q.sx,q.sy,Math.max(0.5,q.r*(0.3+d*0.7)),0,6.283);
      ctx.fillStyle=q.col?'rgba(30,160,255,'+al.toFixed(2)+')':'rgba(200,230,255,'+(al*0.55).toFixed(2)+')';
      ctx.fill();
    }}
    requestAnimationFrame(frame);
  }})();
}})();

/* ── Footer CTA: agregar input de email ── */
(function(){{
  var inner=document.querySelector('.gh-cta-inner,.gh-cta .gh-inner');
  if(!inner)return;
  var btn=inner.querySelector('[data-portal="signup"],a.gh-btn');
  if(!btn)return;

  var wrap=document.createElement('div');
  wrap.className='cta-form-wrap';

  var inp=document.createElement('input');
  inp.type='email';
  inp.placeholder='jamie@example.com';

  var sub=document.createElement('button');
  sub.className='cta-sub-btn';
  sub.textContent='Subscribe';

  wrap.appendChild(inp);
  wrap.appendChild(sub);
  inner.insertBefore(wrap,btn);
  btn.style.display='none';

  sub.addEventListener('click',function(){{
    var email=inp.value.trim();
    if(!email){{inp.focus();return;}}
    fetch('/members/api/send-magic-link/',{{
      method:'POST',
      headers:{{'Content-Type':'application/json'}},
      body:JSON.stringify({{email:email,emailType:'signup',labels:[]}})
    }}).then(function(r){{
      if(r.ok){{
        wrap.innerHTML='<p style="color:#888;padding:12px 20px;font-size:14px">✓ Revisá tu email para confirmar.</p>';
      }} else {{
        btn.style.display='';btn.click();
      }}
    }}).catch(function(){{btn.style.display='';btn.click();}});
  }});
}})();

/* ── Mega-menu oculta la esfera de partículas ── */
(function(){{
  var menu=document.getElementById('mega-menu');
  var sphere=document.getElementById('psphere');
  if(!menu)return;
  function scrollOpacity(){{
    var s=window.scrollY||0;
    return Math.max(0,1-s/(window.innerHeight*0.45)).toFixed(3);
  }}
  function hideSphere(){{
    if(!sphere)sphere=document.getElementById('psphere');
    if(sphere)sphere.style.display='none';
  }}
  function showSphere(){{
    if(!sphere)sphere=document.getElementById('psphere');
    if(sphere){{sphere.style.display='block';sphere.style.opacity=scrollOpacity();}}
  }}
  /* MutationObserver — reacciona al cambio de clase */
  new MutationObserver(function(){{
    menu.classList.contains('open')?hideSphere():showSphere();
  }}).observe(menu,{{attributes:true,attributeFilter:['class']}});
  /* click directo en hamburguesa como respaldo inmediato */
  var hbg=document.getElementById('hbg-btn');
  if(hbg){{
    hbg.addEventListener('click',function(){{
      setTimeout(function(){{
        menu.classList.contains('open')?hideSphere():showSphere();
      }},10);
    }});
  }}
}})();

/* ── About: entrada animada por sección ── */
(function(){{
  if(!document.body.classList.contains('page-about'))return;
  var els=document.querySelectorAll('.gh-content>*,.gh-article-header');
  if(!els.length)return;
  els.forEach(function(el){{el.classList.add('anim-in');}});
  var io=new IntersectionObserver(function(entries){{
    entries.forEach(function(e){{
      if(e.isIntersecting){{
        setTimeout(function(){{e.target.classList.add('anim-done');}},50);
        io.unobserve(e.target);
      }}
    }});
  }},{{threshold:0.06,rootMargin:'0px 0px -20px 0px'}});
  els.forEach(function(el){{io.observe(el);}});
}})();

/* ── Reading progress bar ── */
(function(){{
  if(!document.body.classList.contains('post-template'))return;
  var bar=document.createElement('div');
  bar.id='rpb';
  document.body.appendChild(bar);
  window.addEventListener('scroll',function(){{
    var d=document.documentElement;
    var pct=(d.scrollTop/(d.scrollHeight-d.clientHeight))*100;
    bar.style.width=Math.min(pct,100)+'%';
  }},{{passive:true}});
}})();


/* ── Tag filter panel on search icon hover ── */
(function(){{
  var GU='{GHOST_URL}',KEY='{CONTENT_KEY}';
  var TC={{azure:'#0078D4',ia:'#a855f7',lvl100:'#22c55e',lvl200:'#eab308',lvl300:'#ef4444',
          noticias:'#f97316',arquitectura:'#06b6d4',networking:'#3b82f6',iot:'#84cc16',
          electronica:'#a78bfa',natural:'#10b981',scripting:'#f59e0b',seguridad:'#ec4899',
          google:'#34d399','soft skills':'#fb7185',default:'#6366f1'}};
  function tc(n){{return TC[(n||'').toLowerCase().replace(/[^a-z0-9 ]/g,'').trim()]||TC.default;}}

  var panel=document.createElement('div');
  panel.id='tag-panel';
  panel.innerHTML='<span class="tp-cr tp-tl"></span><span class="tp-cr tp-tr"></span><span class="tp-cr tp-bl"></span><span class="tp-cr tp-br"></span>'
    +'<div class="tp-label">Explorar por categoría</div>'
    +'<div class="tp-grid" id="tp-grid"><span style="color:#444;font-size:12px">Cargando...</span></div>';
  document.body.appendChild(panel);

  var loaded=false;
  function loadTags(){{
    if(loaded)return;
    loaded=true;
    fetch(GU+'/ghost/api/content/tags/?key='+KEY+'&limit=all&fields=name,slug')
      .then(function(r){{return r.json();}})
      .then(function(j){{
        var grid=document.getElementById('tp-grid');
        if(!grid)return;
        var tags=(j.tags||[]).filter(function(t){{return !t.slug.startsWith('hash-');}});
        grid.innerHTML=tags.map(function(t){{
          var c=tc(t.name);
          return '<a class="tp-tag" href="'+GU+'/tag/'+t.slug+'/" style="color:'+c+';border-color:'+c+'22;background:'+c+'0d">'
            +'<span class="tp-dot" style="background:'+c+'"></span>'+t.name+'</a>';
        }}).join('');
      }});
  }}

  function positionPanel(btn){{
    var r=btn.getBoundingClientRect();
    panel.style.top=(r.bottom+8)+'px';
    panel.style.right=(window.innerWidth-r.right)+'px';
    panel.style.left='auto';
  }}

  var closeTimer;
  function openPanel(btn){{
    clearTimeout(closeTimer);
    loadTags();
    positionPanel(btn);
    panel.classList.add('open');
  }}
  function closePanel(){{
    closeTimer=setTimeout(function(){{panel.classList.remove('open');}},250);
  }}

  /* delegación en document — captura todos los botones de search */
  document.addEventListener('mouseover',function(e){{
    var btn=e.target.closest('button[data-ghost-search],.gh-search');
    if(btn)openPanel(btn);
  }});
  document.addEventListener('mouseout',function(e){{
    var btn=e.target.closest('button[data-ghost-search],.gh-search');
    if(btn&&!panel.contains(e.relatedTarget))closePanel();
  }});
  panel.addEventListener('mouseenter',function(){{clearTimeout(closeTimer);}});
  panel.addEventListener('mouseleave',closePanel);
  document.addEventListener('click',function(e){{
    if(!panel.contains(e.target)&&!e.target.closest('button[data-ghost-search]')){{
      panel.classList.remove('open');
    }}
  }});
}})();

/* ── Custom cursor — solo en dispositivos con mouse real ── */
(function(){{
  if(!window.matchMedia('(hover:hover) and (pointer:fine)').matches)return;
  var dot=document.createElement('div');
  dot.id='csr';
  document.body.appendChild(dot);
  var mx=window.innerWidth/2,my=window.innerHeight/2,cx=mx,cy=my;
  document.addEventListener('mousemove',function(e){{mx=e.clientX;my=e.clientY;}},{{passive:true}});
  document.addEventListener('mouseleave',function(){{dot.classList.add('csr-hidden');}});
  document.addEventListener('mouseenter',function(){{dot.classList.remove('csr-hidden');}});
  document.addEventListener('mouseover',function(e){{
    var t=e.target.closest('a,button,[data-portal],[onclick]');
    dot.classList.toggle('csr-link',!!t);
  }});
  (function loop(){{
    cx+=(mx-cx)*0.13;
    cy+=(my-cy)*0.13;
    dot.style.transform='translate('+cx+'px,'+cy+'px)';
    requestAnimationFrame(loop);
  }})();
}})();

/* ── Blinking cursor "_" al final del título del hero ── */
(function(){{
  var title=document.querySelector('.gh-header-title,h1.gh-header-title');
  if(!title)return;
  var last=title.lastChild;
  if(last&&last.nodeType===3&&last.textContent.endsWith('.')){{
    last.textContent=last.textContent.slice(0,-1);
  }}
  var span=document.createElement('span');
  span.className='gh-cursor-blink';
  span.textContent='_';
  title.appendChild(span);
}})();

/* ── Share button: fallback JS por si el selector CSS no matchea ── */
(function(){{
  function styleShareBtn(btn){{
    btn.style.cssText='color:#e0e0e0!important;background:transparent!important;'
      +'border:1px solid #444!important;border-radius:6px!important;'
      +'padding:6px 16px!important;font-size:13px!important;font-weight:500!important;'
      +'display:inline-flex!important;align-items:center!important;gap:6px!important;'
      +'cursor:none!important;transition:color .2s,border-color .2s,background .2s!important;';
    btn.addEventListener('mouseenter',function(){{
      btn.style.color='#fff';btn.style.borderColor='#666';btn.style.background='#1a1a1a';
    }});
    btn.addEventListener('mouseleave',function(){{
      btn.style.color='#e0e0e0';btn.style.borderColor='#444';btn.style.background='transparent';
    }});
  }}
  function findAndStyle(){{
    var btns=document.querySelectorAll(
      '.gh-article-share button,.gh-article-share a,'
      +'.gh-article-actions button,.gh-article-actions a,'
      +'button.gh-share-button,a.gh-share-button'
    );
    btns.forEach(styleShareBtn);
    /* fallback: any button whose text contains "Share" */
    document.querySelectorAll('button,a').forEach(function(el){{
      if(el.textContent.trim()==='Share'&&!el.dataset.shareStyled){{
        el.dataset.shareStyled='1';
        styleShareBtn(el);
      }}
    }});
  }}
  findAndStyle();
  setTimeout(findAndStyle,500);
}})();

/* ── Glitch periódico en el título del hero ── */
(function(){{
  function glitch(){{
    var el=document.querySelector('.gh-header-title,h1.gh-header-title');
    if(!el)return;
    el.classList.add('gh-glitch');
    setTimeout(function(){{el.classList.remove('gh-glitch');}},320);
  }}
  setTimeout(glitch,2500);
  setInterval(function(){{glitch();}}, 9000+Math.random()*5000);
}})();

/* ── Scroll reveal en homepage ── */
(function(){{
  var targets=document.querySelectorAll('.gh-card,.gh-featured-card,.gh-feed,.pmq-header,.gh-more');
  if(!targets.length)return;
  targets.forEach(function(el){{el.classList.add('sv');}});
  var io=new IntersectionObserver(function(entries){{
    entries.forEach(function(e){{
      if(e.isIntersecting){{e.target.classList.add('sv-in');io.unobserve(e.target);}}
    }});
  }},{{threshold:0.1,rootMargin:'0px 0px -40px 0px'}});
  targets.forEach(function(el){{io.observe(el);}});
}})();

/* ── About page: reveal escalonado por sección ── */
(function(){{
  if(!document.body.classList.contains('page-about'))return;
  var kids=document.querySelectorAll('.gh-content>*');
  if(!kids.length)return;
  var io=new IntersectionObserver(function(entries){{
    entries.forEach(function(e){{
      if(e.isIntersecting){{e.target.classList.add('revealed');io.unobserve(e.target);}}
    }});
  }},{{threshold:0.08,rootMargin:'0px 0px -30px 0px'}});
  kids.forEach(function(el,i){{
    el.style.transitionDelay=(i*0.07)+'s';
    io.observe(el);
  }});
}})();

/* ── Hamburger mega menu ── */
(function(){{
  var GU='{GHOST_URL}',KEY='{CONTENT_KEY}';
  var TC={{azure:'#0078D4',ia:'#a855f7',lvl100:'#22c55e',lvl200:'#eab308',lvl300:'#ef4444',
          noticias:'#f97316',arquitectura:'#06b6d4',networking:'#3b82f6',iot:'#84cc16',
          electronica:'#a78bfa',natural:'#10b981',scripting:'#f59e0b',seguridad:'#ec4899',
          google:'#34d399','soft skills':'#fb7185',default:'#6366f1'}};
  function tc(n){{return TC[(n||'').toLowerCase().replace(/[^a-z0-9 ]/g,'').trim()]||TC.default;}}

  /* hamburger button */
  var btn=document.createElement('button');
  btn.id='hbg-btn';
  btn.setAttribute('aria-label','Menú');
  btn.innerHTML='<span></span><span></span><span></span>';

  /* mega menu shell */
  var menu=document.createElement('div');
  menu.id='mega-menu';
  menu.innerHTML=
    '<div class="mm-inner">'
    +'<div class="mm-col mm-col-wide">'
    +'<div class="mm-label">Categorías</div>'
    +'<div class="mm-tags" id="mm-tags-grid"><span style="color:#444;font-size:12px">Cargando...</span></div>'
    +'</div>'
    +'<div class="mm-col">'
    +'<div class="mm-label">Explorar</div>'
    +'<nav class="mm-links">'
    +'<a class="mm-link" href="'+GU+'/">Inicio</a>'
    +'<a class="mm-link" href="'+GU+'/about/">About</a>'
    +'<a class="mm-link" href="'+GU+'/rss/">RSS</a>'
    +'</nav>'
    +'</div>'
    +'<div class="mm-col" style="align-self:flex-end">'
    +'<div class="mm-ctas">'
    +'<a class="mm-cta-primary" href="#/portal/signup" data-portal="signup">&#x2709; Suscribirme</a>'
    +'<a class="mm-cta-secondary" href="'+GU+'/about/">Sobre el blog</a>'
    +'</div>'
    +'</div>'
    +'</div>';
  document.body.appendChild(menu);

  /* inject button into nav */
  var actions=document.querySelector('.gh-navigation-actions');
  if(actions)actions.appendChild(btn);

  /* load tags once */
  var loaded=false;
  function loadTags(){{
    if(loaded)return;
    loaded=true;
    fetch(GU+'/ghost/api/content/tags/?key='+KEY+'&limit=all&fields=name,slug')
      .then(function(r){{return r.json();}})
      .then(function(j){{
        var grid=document.getElementById('mm-tags-grid');
        if(!grid)return;
        var tags=(j.tags||[]).filter(function(t){{return !t.slug.startsWith('hash-');}});
        grid.innerHTML=tags.map(function(t){{
          var c=tc(t.name);
          return '<a class="mm-tag" href="'+GU+'/tag/'+t.slug+'/" style="color:'+c+';border-color:'+c+'44;background:'+c+'0f">'
            +'<span class="mm-dot" style="background:'+c+'"></span>'+t.name+'</a>';
        }}).join('');
      }});
  }}

  function openMenu(){{
    loadTags();
    menu.classList.add('open');
    btn.classList.add('active');
    document.body.style.overflow='hidden';
  }}
  function closeMenu(){{
    menu.classList.remove('open');
    btn.classList.remove('active');
    document.body.style.overflow='';
  }}

  btn.addEventListener('click',function(e){{
    e.stopPropagation();
    if(menu.classList.contains('open'))closeMenu();
    else openMenu();
  }});

  document.addEventListener('click',function(e){{
    if(menu.classList.contains('open')&&!menu.contains(e.target)&&e.target!==btn)closeMenu();
  }});
  document.addEventListener('keydown',function(e){{
    if(e.key==='Escape')closeMenu();
  }});
}})();

/* ── Post navigation arrows ── */
(function(){{
  if(!document.body.classList.contains('post-template'))return;
  var GU='{GHOST_URL}',KEY='{CONTENT_KEY}';
  var slug=window.location.pathname.replace(/[\/]/g,'');
  if(!slug)return;

  fetch(GU+'/ghost/api/content/posts/?key='+KEY+'&limit=all&fields=slug,title&order=published_at%20desc')
    .then(function(r){{return r.json();}})
    .then(function(j){{
      var posts=(j.posts||[]).filter(function(p){{return p.slug!=='coming-soon';}});
      var idx=posts.findIndex(function(p){{return p.slug===slug;}});
      if(idx<0)return;

      var svgL='<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><polyline points="15 18 9 12 15 6"/></svg>';
      var svgR='<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><polyline points="9 18 15 12 9 6"/></svg>';

      if(idx+1 < posts.length){{
        var older=posts[idx+1];
        var a=document.createElement('a');
        a.className='pnav-arrow pnav-prev';
        a.href=GU+'/'+older.slug+'/';
        a.title=older.title;
        a.innerHTML=svgL;
        document.body.appendChild(a);
      }}
      if(idx-1 >= 0){{
        var newer=posts[idx-1];
        var b=document.createElement('a');
        b.className='pnav-arrow pnav-next';
        b.href=GU+'/'+newer.slug+'/';
        b.title=newer.title;
        b.innerHTML=svgR;
        document.body.appendChild(b);
      }}
    }});
}})();
</script>"""

def inject():
    print("💉 CSS → codeinjection_head...")
    sql(f"UPDATE settings SET value='{esc_sql(CSS.strip())}', updated_at=NOW() WHERE `key`='codeinjection_head';")
    print("💉 JS  → codeinjection_foot...")
    sql(f"UPDATE settings SET value='{esc_sql(FOOT.strip())}', updated_at=NOW() WHERE `key`='codeinjection_foot';")
    print("⚡ Reiniciando Ghost...")
    subprocess.run(['docker','restart','ghost-blog'], check=True)
    print(f"✅ Listo → {GHOST_URL}")

if __name__ == '__main__':
    inject()

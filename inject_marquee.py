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

/* ── Post nav arrows ── */
.pnav-arrow{position:fixed;top:50%;transform:translateY(-50%);z-index:999;display:flex;align-items:center;justify-content:center;width:32px;height:80px;background:rgba(255,255,255,0.06);border:1px solid rgba(255,255,255,0.1);border-radius:6px;color:#aaa;cursor:pointer;text-decoration:none!important;transition:background .2s,border-color .2s,color .2s,opacity .2s;opacity:0.5}
.pnav-arrow:hover{background:rgba(255,255,255,0.14);border-color:rgba(255,255,255,0.25);color:#fff;opacity:1}
.pnav-arrow.pnav-prev{left:12px}
.pnav-arrow.pnav-next{right:12px}
.pnav-arrow svg{width:18px;height:18px;flex-shrink:0}
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
    return '<a class="pmq-card" href="'+GU+'/'+p.slug+'/" target="_blank">'
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

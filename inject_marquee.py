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
#pmq-root{display:block!important;width:100%!important;background:#0f0f0f;padding:60px 0;overflow:hidden;box-sizing:border-box}
.pmq-header{text-align:center;margin-bottom:40px;padding:0 24px}
.pmq-label{display:block;font-size:11px;font-weight:700;letter-spacing:.1em;text-transform:uppercase;color:#a855f7;margin-bottom:12px;font-family:sans-serif}
.pmq-title{font-size:40px;font-weight:700;color:#fff;margin:0 0 10px;line-height:1.2;font-family:sans-serif}
.pmq-sub{font-size:15px;color:#888;margin:0 auto 24px;max-width:480px;font-family:sans-serif}
.pmq-btn{display:inline-flex;align-items:center;gap:8px;background:#1a1a1a;border:1px solid #333;border-radius:8px;padding:11px 22px;color:#fff!important;font-size:14px;font-weight:500;text-decoration:none!important;font-family:sans-serif}
.pmq-btn:hover{background:#222;border-color:#555}
/* Filas marquee */
.pmq-rows{width:100%;overflow:hidden;display:flex;flex-direction:column;gap:16px;-webkit-mask-image:linear-gradient(to right,transparent,black 8%,black 92%,transparent);mask-image:linear-gradient(to right,transparent,black 8%,black 92%,transparent)}
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
.pmq-card-text{font-size:13px;color:#bbb;line-height:1.5;margin:0;display:-webkit-box;-webkit-line-clamp:3;-webkit-box-orient:vertical;overflow:hidden}
@keyframes marquee-left{from{transform:translateX(0)}to{transform:translateX(-50%)}}
@keyframes marquee-right{from{transform:translateX(-50%)}to{transform:translateX(0)}}
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
    +'<span class="pmq-label">✦ Blog</span>'
    +'<h2 class="pmq-title">Explorá todos los posts</h2>'
    +'<p class="pmq-sub">Azure, IA, redes, IoT, scripting y más.</p>'
    +'<a class="pmq-btn" href="'+GU+'">→ Ver todos los posts</a>'
    +'</div>'
    +'<div id="pmq-rows"></div>';

  fetch(GU+'/ghost/api/content/posts/?key='+KEY+'&limit=all&include=tags&fields=title,slug,feature_image,published_at')
    .then(function(r){{return r.json();}})
    .then(function(j){{
      var all=(j.posts||[]).filter(function(p){{return p.slug!=='coming-soon';}});
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
      rows.appendChild(buildRow(shuffle(all,1),false));
      rows.appendChild(buildRow(shuffle(all,2),true));
      rows.appendChild(buildRow(shuffle(all,3),false));
      rows.appendChild(buildRow(shuffle(all,4),true));
    }})
    .catch(function(e){{
      var rows=document.getElementById('pmq-rows');
      if(rows)rows.innerHTML='<p style="color:#666;text-align:center;padding:20px">'+e+'</p>';
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

#!/usr/bin/env python3
"""Inserta posts directamente en la DB de Ghost"""

import subprocess, uuid, json, re
from datetime import datetime

def read_env():
    with open('/home/javierledesma/docker/ghost-blog/.env') as f:
        return dict(l.strip().split('=',1) for l in f if '=' in l and not l.startswith('#'))

ENV = read_env()
MYSQL_USER = ENV['MYSQL_USER']
MYSQL_PASS = ENV['MYSQL_PASSWORD']
MYSQL_DB   = ENV['MYSQL_DATABASE']

def sql(query):
    r = subprocess.run(
        ['docker','exec','ghost-db','mysql',
         '--default-character-set=utf8mb4',
         f'-u{MYSQL_USER}', f'-p{MYSQL_PASS}', MYSQL_DB, '-se', query],
        capture_output=True, text=True, encoding='utf-8'
    )
    if r.returncode != 0 and 'ERROR' in r.stderr:
        print(f"  SQL ERROR: {r.stderr.strip()}")
    return r.stdout.strip()

def new_id():
    return uuid.uuid4().hex[:24]

AUTHOR_ID = sql("SELECT id FROM users LIMIT 1;")

def insert_post(title, html, slug, tags, feature_image=None, published_at=None, excerpt=None):
    post_id    = new_id()
    post_uuid  = str(uuid.uuid4())
    now        = published_at or datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
    pub_at     = now
    excerpt_v  = (excerpt or '')[:300].replace("'", "\\'")
    title_v    = title.replace("'", "\\'")
    slug_v     = slug
    fi         = feature_image or ''
    lexical    = json.dumps({"root":{"children":[{"children":[{"detail":0,"format":0,"mode":"normal","style":"","text":"","type":"text","version":1}],"direction":"ltr","format":"","indent":0,"type":"paragraph","version":1}],"direction":"ltr","format":"","indent":0,"type":"root","version":1}})
    lexical_v  = lexical.replace("'", "\\'")

    # Escapar HTML
    html_v = html.replace('\\', '\\\\').replace("'", "\\'")

    q = f"""
INSERT INTO posts
  (id, uuid, title, slug, html, lexical, comment_id, plaintext, feature_image,
   featured, type, status, visibility, email_recipient_filter,
   created_at, updated_at, published_at,
   published_by, custom_excerpt, show_title_and_feature_image)
VALUES
  ('{post_id}', '{post_uuid}', '{title_v}', '{slug_v}', '{html_v}', '{lexical_v}',
   '{post_id}', '', '{fi}',
   0, 'post', 'published', 'public', 'all',
   '{now}', '{now}', '{pub_at}',
   '{AUTHOR_ID}', '{excerpt_v}', 1);
"""
    result = sql(q)

    # Tags
    for tag_name in tags:
        tag_slug = re.sub(r'[^a-z0-9]+', '-', tag_name.lower()).strip('-')
        tag_id_r = sql(f"SELECT id FROM tags WHERE slug='{tag_slug}' LIMIT 1;")
        if not tag_id_r:
            tag_id = new_id()
            sql(f"INSERT INTO tags (id, name, slug, created_at, updated_at) VALUES ('{tag_id}','{tag_name}','{tag_slug}',NOW(),NOW());")
        else:
            tag_id = tag_id_r
        sort_order = sql(f"SELECT COALESCE(MAX(sort_order)+1,0) FROM posts_tags WHERE post_id='{post_id}';") or '0'
        pt_id = new_id()
        sql(f"INSERT INTO posts_tags (id, post_id, tag_id, sort_order) VALUES ('{pt_id}','{post_id}','{tag_id}',{sort_order});")

    print(f"✅ Creado: {title}")
    print(f"   Slug: {slug_v}")
    return post_id


# ── POST: Jetson Nano ────────────────────────────────────────────────────────

insert_post(
    title="[IA fuera de Cloud] Mi experiencia con Jetson Nano Parte#1..",
    slug="ia-fuera-de-cloud-mi-experiencia-con-jetson-nano-parte1",
    tags=["AZURE", "ELECTRÓNICA", "IA", "IOT", "LVL200"],
    feature_image="https://assets.zyrosite.com/cdn-cgi/image/format=auto,w=1440,h=990,fit=crop/Aq2BgVbxvECDEQ7B/trayectoriajeston-KgTsqqJWMZiQI0X3.png",
    published_at="2026-03-19 00:00:00",
    excerpt="Qué pasa cuando la inteligencia artificial deja el cloud y empieza a correr directamente en dispositivos? Mi experiencia con Jetson Nano y cómo conecta con mis inicios en IoT (MIT).",
    html="""
<h2>Cuando la IA sale del cloud: mi experiencia con Jetson Nano</h2>
<p>Hace años que trabajo con Azure, arquitecturas cloud y, más recientemente, con inteligencia artificial. Pero hace un tiempo me volvió a picar algo distinto: qué pasa cuando la IA deja el cloud y empieza a correr directamente en un dispositivo físico.</p>
<p>Y eso me llevó a meterme con el curso <strong>"Getting Started with AI on Jetson Nano"</strong> de NVIDIA.</p>
<figure class="kg-card kg-image-card"><img src="https://assets.zyrosite.com/cdn-cgi/image/format=auto,w=1440,h=990,fit=crop/Aq2BgVbxvECDEQ7B/trayectoriajeston-KgTsqqJWMZiQI0X3.png" class="kg-image" /></figure>
<h2>Un déjà vu: MIT + IoT + Raspberry</h2>
<p>En su momento hice un programa de IoT en el MIT y desarrollé una tesis para detectar caídas en personas mayores. El prototipo era un dispositivo bajo la suela del zapato con giroscopio y sensores de movimiento que detectaba patrones:</p>
<ul><li>Cambios bruscos de orientación</li><li>Ausencia de movimiento posterior</li><li>Posiciones anómalas mantenidas en el tiempo</li></ul>
<p>Cuando detectaba una caída, enviaba una alerta a los familiares. Simple a nivel hardware, muy interesante desde la lógica.</p>
<h2>Jetson Nano.. WTF!</h2>
<blockquote>"IA corriendo directamente en el dispositivo. Sin cloud, sin excusas"</blockquote>
<p>Trabajar con Jetson Nano fue volver a ese lugar, pero con un salto enorme. Ya no es un dispositivo que manda datos al cloud — acá tenés modelos de IA corriendo en el propio dispositivo, tomando decisiones en tiempo real sin depender de conectividad.</p>
<figure class="kg-card kg-image-card"><img src="https://assets.zyrosite.com/cdn-cgi/image/format=auto,w=1440,h=784,fit=crop/Aq2BgVbxvECDEQ7B/infografiajetson-JCuNknZGMHphCbqA.png" class="kg-image" /></figure>
<h2>Azure no se fué, sigue estando…</h2>
<p>El cloud sigue siendo clave para entrenar modelos, gobernar y escalar, mientras que los dispositivos se encargan de ejecutar y tomar decisiones en tiempo real. El paradigma cambia: primero procesás en el dispositivo, después mandás al cloud solo lo que aporta valor.</p>
<figure class="kg-card kg-image-card"><img src="https://assets.zyrosite.com/cdn-cgi/image/format=auto,w=1024,h=701,fit=crop/Aq2BgVbxvECDEQ7B/sdk-KNBlXnBl18jUhT5c.png" class="kg-image" /></figure>
<h2>La parte que nadie te cuenta (pero es la mejor)</h2>
<ul><li>Pelear con una microSD</li><li>Flashear imágenes (usé la v2.4.0.13236 del NVIDIA_SDK_Manager)</li><li>Probar cables que no funcionan</li><li>Entender por qué algo no levanta</li></ul>
<p>Me obliga a salir del confort del portal de Azure y volver a entender cómo funcionan las cosas por debajo. Nunca me olvidaré mis primeras líneas en C++:</p>
<pre><code>void setup() { pinMode(13, OUTPUT); }
void loop() { digitalWrite(13, HIGH); delay(1000); digitalWrite(13, LOW); delay(1000); }</code></pre>
<h2>Conclusión</h2>
<p>Volver a trabajar con dispositivos después de tanto tiempo en cloud no es retroceder, es sumar una pieza que faltaba. Al final, la IA no vive solo en el cloud… también vive donde realmente pasan las cosas.</p>
"""
)

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
    # Envolver el HTML en un nodo "html" de Lexical.
    # Esto es crítico: si se usa un Lexical vacío, Ghost Admin sobreescribe
    # el contenido al guardar cualquier cambio (ej: cambiar la feature image).
    # Con este formato, Ghost Admin ve un bloque HTML card y lo preserva.
    lexical    = json.dumps({"root":{"children":[{"type":"html","html":html,"version":1}],"direction":"ltr","format":"","indent":0,"type":"root","version":1}})
    lexical_v  = lexical.replace('\\', '\\\\').replace("'", "\\'")

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

    # Author
    pa_id = new_id()
    sql(f"INSERT IGNORE INTO posts_authors (id, post_id, author_id, sort_order) VALUES ('{pa_id}','{post_id}','{AUTHOR_ID}',0);")

    print(f"✅ Creado: {title}")
    print(f"   Slug: {slug_v}")
    return post_id

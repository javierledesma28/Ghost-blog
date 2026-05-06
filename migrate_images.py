#!/usr/bin/env python3
"""
Migra todas las imágenes de assets.zyrosite.com a ghost-content/images/migrated/
y actualiza los posts en la DB para apuntar a las URLs locales de Ghost.
"""

import subprocess, re, os, requests, shutil
from urllib.parse import urlparse
from pathlib import Path

# ── Config ────────────────────────────────────────────────────────────────────
def read_env():
    with open('/home/javierledesma/docker/ghost-blog/.env') as f:
        return dict(l.strip().split('=',1) for l in f if '=' in l and not l.startswith('#'))

ENV = read_env()
GHOST_URL      = ENV['GHOST_URL']   # https://blog.javierledesma.com.ar
LOCAL_IMG_DIR  = Path('/home/javierledesma/docker/ghost-blog/ghost-content/images/migrated')
LOCAL_IMG_DIR.mkdir(parents=True, exist_ok=True)

# URL pública donde Ghost servirá las imágenes migradas
PUBLIC_BASE = f"{GHOST_URL}/content/images/migrated"

# ── DB helpers ────────────────────────────────────────────────────────────────
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

# ── Extraer todas las URLs de zyrosite en los posts ──────────────────────────
ZYROSITE_PATTERN = re.compile(
    r'https://assets\.zyrosite\.com/[^\s\'"<>)]+',
    re.IGNORECASE
)

def get_all_posts():
    """Devuelve lista de (id, slug, feature_image, html)"""
    raw = sql("SELECT id, slug, feature_image, html FROM posts WHERE type='post' AND status='published';")
    posts = []
    for line in raw.split('\n'):
        parts = line.split('\t')
        if len(parts) >= 4:
            posts.append({
                'id':            parts[0],
                'slug':          parts[1],
                'feature_image': parts[2] if parts[2] != 'NULL' else '',
                'html':          '\t'.join(parts[3:])
            })
        elif len(parts) == 3:
            posts.append({
                'id':            parts[0],
                'slug':          parts[1],
                'feature_image': parts[2] if parts[2] != 'NULL' else '',
                'html':          ''
            })
    return posts

def collect_urls(posts):
    """Recolecta todas las URLs únicas de zyrosite en feature_image + html"""
    urls = set()
    for p in posts:
        if p['feature_image'] and 'zyrosite' in p['feature_image']:
            urls.add(p['feature_image'])
        for match in ZYROSITE_PATTERN.finditer(p['html']):
            urls.add(match.group(0))
    return urls

# ── Descargar y guardar imagen ────────────────────────────────────────────────
def filename_from_url(url):
    """Extrae el nombre de archivo limpio de la URL del CDN de zyrosite"""
    path = urlparse(url).path
    # El nombre real está al final, después del último /
    name = path.split('/')[-1]
    # Limpiar parámetros residuales si los hubiera
    name = name.split('?')[0]
    return name

URL_TO_LOCAL = {}  # cache old_url → new_public_url

def download_image(url):
    """Descarga la imagen y devuelve la URL pública local en Ghost"""
    if url in URL_TO_LOCAL:
        return URL_TO_LOCAL[url]

    filename = filename_from_url(url)
    dest = LOCAL_IMG_DIR / filename

    if dest.exists():
        print(f"  ↩️  Ya existe: {filename}")
        new_url = f"{PUBLIC_BASE}/{filename}"
        URL_TO_LOCAL[url] = new_url
        return new_url

    try:
        headers = {'User-Agent': 'Mozilla/5.0 (compatible; GhostMigration/1.0)'}
        resp = requests.get(url, headers=headers, timeout=30, stream=True)
        resp.raise_for_status()
        with open(dest, 'wb') as f:
            for chunk in resp.iter_content(chunk_size=8192):
                f.write(chunk)
        new_url = f"{PUBLIC_BASE}/{filename}"
        URL_TO_LOCAL[url] = new_url
        size_kb = dest.stat().st_size // 1024
        print(f"  ✅ Descargado: {filename} ({size_kb} KB)")
        return new_url
    except Exception as e:
        print(f"  ❌ Error descargando {url}: {e}")
        URL_TO_LOCAL[url] = url  # mantener original si falla
        return url

# ── Actualizar posts en DB ────────────────────────────────────────────────────
def esc(s):
    return s.replace('\\','\\\\').replace("'","\\'")

def update_post(post_id, feature_image, html):
    sql(f"""UPDATE posts
        SET feature_image='{esc(feature_image)}',
            html='{esc(html)}',
            updated_at=NOW()
        WHERE id='{post_id}';""")

# ── Main ──────────────────────────────────────────────────────────────────────
def main():
    print("📦 Leyendo posts de la DB...")
    posts = get_all_posts()
    print(f"   {len(posts)} posts encontrados")

    print("\n🔍 Recolectando URLs de imágenes...")
    all_urls = collect_urls(posts)
    print(f"   {len(all_urls)} imágenes únicas a descargar")

    print("\n⬇️  Descargando imágenes...")
    for url in sorted(all_urls):
        download_image(url)

    print(f"\n✏️  Actualizando posts en DB...")
    updated = 0
    for post in posts:
        new_fi   = post['feature_image']
        new_html = post['html']
        changed  = False

        # Reemplazar feature_image
        if new_fi and new_fi in URL_TO_LOCAL and URL_TO_LOCAL[new_fi] != new_fi:
            new_fi = URL_TO_LOCAL[new_fi]
            changed = True

        # Reemplazar todas las URLs en el HTML
        def replace_url(m):
            old = m.group(0)
            return URL_TO_LOCAL.get(old, old)

        new_html_replaced = ZYROSITE_PATTERN.sub(replace_url, new_html)
        if new_html_replaced != new_html:
            new_html = new_html_replaced
            changed = True

        if changed:
            update_post(post['id'], new_fi, new_html)
            print(f"   📝 Actualizado: {post['slug']}")
            updated += 1

    print(f"\n✅ {updated} posts actualizados")
    print("\n⚡ Reiniciando Ghost...")
    subprocess.run(['docker','restart','ghost-blog'], check=True)
    print("🎉 ¡Listo! Todas las imágenes son ahora locales en Ghost.")
    print(f"   📁 Guardadas en: ghost-content/images/migrated/")
    print(f"   🌐 Servidas desde: {PUBLIC_BASE}/")

if __name__ == '__main__':
    main()

# Ghost Blog

## Resumen
Infraestructura Docker para publicar y administrar un blog personal con Ghost CMS, expuesto públicamente mediante Cloudflare Tunnel bajo el dominio `blog.javierledesma.com.ar`. El acceso al panel de administración (`/ghost`) está disponible públicamente pero sin capa adicional de protección (Cloudflare Access pendiente).

## Stack
- **CMS:** Ghost:latest
- **DB:** MySQL 8
- **Tunnel:** Cloudflare Tunnel (cloudflared) — servicio dentro del mismo compose
- **Infra:** Ubuntu Server / Docker Compose / red Docker `ghost-net`

## Arquitectura
```
https://blog.javierledesma.com.ar
        ↓
Cloudflare Edge (SSL terminado)
        ↓
Cloudflare Tunnel → ghost-cloudflared (container)
        ↓
ghost-net (red Docker interna)
        ↓
ghost-blog:2368
```

Estructura de carpetas:
- `docker-compose.yml` → servicios ghost + ghost-db + cloudflared, red ghost-net
- `.env` → variables de entorno (no commiteado)
- `.env.example` → plantilla de variables requeridas
- `ghost-content/` → contenido del blog (no commiteado) — incluye imágenes migradas
- `mysql-data/` → datos MySQL (no commiteado)

## Comandos Clave
```bash
# Levantar stack completo
docker compose up -d

# Bajar
docker compose down

# Recrear (tras cambio de .env)
docker compose down && docker compose up -d

# Logs
docker compose logs -f
docker logs -f ghost-blog
docker logs -f ghost-cloudflared

# Estado
docker compose ps
docker network inspect ghost-net

# Insertar nuevo post manualmente
python3 insert_post.py

# Migrar imágenes externas a local
python3 migrate_images.py
```

## Archivos Críticos
- `docker-compose.yml` → define los tres servicios: ghost, ghost-db, cloudflared
- `.env.example` → referencia de todas las variables necesarias
- `.gitignore` → excluye `.env`, `mysql-data/`, `ghost-content/`, `backups/`
- `insert_post.py` → función reutilizable para insertar posts directamente en MySQL
- `insert_all_posts.py` → migración masiva: los 17 posts del blog original
- `migrate_images.py` → descarga imágenes externas y actualiza URLs en DB
- `inject_marquee.py` → inyecta CSS + JS del Post Marquee en la DB de Ghost
- `post-marquee.html` → versión standalone para desarrollo/preview del componente

## Scripts de Migración
### insert_post.py / insert_all_posts.py
Inserta posts directamente en la DB de Ghost (bypass del Admin API). Patrón probado y funcional.

```python
insert_post(
    title="Título del post",
    slug="slug-del-post",
    tags=["TAG1", "TAG2"],
    feature_image="https://...",
    published_at="2025-01-01 00:00:00",
    excerpt="Resumen corto...",
    html="<h2>...</h2><p>...</p>"
)
```

**Importante:** Después de insertar posts, ejecutar `docker restart ghost-blog` para que Ghost los cargue en memoria.

### migrate_images.py
- Escanea todos los posts en busca de URLs externas (`assets.zyrosite.com` u otras)
- Descarga cada imagen al volumen local `ghost-content/images/migrated/`
- Actualiza la DB con las nuevas URLs locales (`/content/images/migrated/`)
- Reinicia Ghost automáticamente al finalizar

## Migración desde sitio original
**Origen:** `javierledesma.com.ar` (Zyrosite/Hostinger) — **puede darse de baja**
**Destino:** `blog.javierledesma.com.ar` (Ghost en Docker)

**Estado: ✅ COMPLETA**
- 19 posts migrados con fechas originales, tags y feature images
- 26 imágenes descargadas y almacenadas localmente en `ghost-content/images/migrated/`
- Sin dependencias externas — el blog es 100% autónomo

## Convenciones
- `.env` nunca se commitea; `.env.example` es la referencia con valores placeholder
- `GHOST_URL` apunta al dominio público: `https://blog.javierledesma.com.ar`
- `TUNNEL_TOKEN` se obtiene desde Cloudflare Zero Trust → Tunnels → Blog JavierLedesma → Overview
- Ghost no expone puertos al host — todo el tráfico entra exclusivamente vía tunnel
- La red `ghost-net` es interna al compose; cloudflared resuelve `ghost-blog` por nombre de contenedor
- Las imágenes del blog se guardan en `ghost-content/images/migrated/` (no commiteado)

## Post Marquee — Componente de Showcase

Componente estilo Supabase "Join the community" con filas horizontales animadas mostrando los posts del blog.

### Arquitectura
- **CSS** inyectado en `codeinjection_head` de Ghost (via DB)
- **JS** inyectado en `codeinjection_foot` de Ghost (via DB)
- **Anchor HTML** `<div id="pmq-root"></div>` hardcodeado en el template del tema

### Template modificado
```
/var/lib/ghost/current/content/themes/source/home.hbs
```
> **Importante:** `ghost-content/themes/source` es un **symlink** a `/var/lib/ghost/current/content/themes/source`. Siempre editar via `docker exec ghost-blog` usando la ruta `/var/lib/ghost/...`

```handlebars
{{> "components/cta"}}
{{!-- Post Marquee --}}
<div id="pmq-root"></div>
{{> "components/post-list" ...}}
```

El `<div id="pmq-root">` debe estar como **sibling directo** de `section.gh-container` (fuera del grid interno). Si se inserta dentro de `.gh-container-inner.gh-inner` (12-column CSS grid), el componente aparece en una columna estrecha.

### Ejecutar
```bash
python3 inject_marquee.py
```

### Diseño
- 4 filas horizontales: odd=izquierda (35s), even=derecha (28s)
- Cards 300px: fondo `#1c1c1c`, borde `#2e2e2e`, avatar circular, tag con color por categoría, título del post
- Fade mask izquierda/derecha con `mask-image: linear-gradient(to right, transparent, black 8%, black 92%, transparent)`
- Hover pausa todas las animaciones
- Shuffle seeded para distinto orden por fila

### Content API
```
GET /ghost/api/content/posts/?key=KEY&limit=all&include=tags&fields=title,slug,feature_image,published_at
```
⚠️ `tags` va en `include=` (es una relación), **NO** en `fields=`. Si se pone en `fields=` da `ER_BAD_FIELD_ERROR`.

### Lecciones aprendidas
- **DOMContentLoaded nunca dispara** en `codeinjection_foot`: el script se ejecuta después de que el evento ya se emitió. El código debe ejecutarse **inmediatamente**, sin listener de eventos.
- **CSS animation name via variable no funciona**: `animation: var(--anim-name) var(--dur)` era poco confiable. Usar nombres de clase directos: `.pmq-track { animation-name: marquee-left }` y `.pmq-track.reverse { animation-name: marquee-right }`.
- **Ghost usa `home.hbs`, no `index.hbs`** para la homepage. `index.hbs` es para el archivo de posts.
- **Tema activo es `source`**, no `casper`. Verificar con `curl` en el HTML generado.

## Decisiones Técnicas Clave
- **Insert directo a MySQL** en lugar de Admin API — más confiable, sin problemas de caché
- **Charset:** `--default-character-set=utf8mb4` + `encoding='utf-8'` en subprocess para correcta codificación del español
- **Campo obligatorio:** `email_recipient_filter='all'` en INSERT de posts (no tiene default en Ghost)
- **Imágenes locales:** todas en `ghost-content/images/migrated/` para independencia total del hosting original

## Lo Que NO Necesita Explicación
- Docker Compose básico
- Variables de entorno en Docker
- Cloudflare Tunnel / cloudflared

## Pendiente
- Proteger `/ghost` (admin) con Cloudflare Access — política de email OTP o Google SSO
- Crear MCP Server `ghost-blog` para gestión de posts (ver repo `my-mcp-servers`)
- Mejoras al Post Marquee (base funcional en producción)

## Próximo Paso
Desarrollo de MCP Server propio para gestión de posts en Ghost y otros proyectos.
Ver: https://github.com/javierledesma28/my-mcp-servers (pendiente de crear)

## Trabajo Activo ← ACTUALIZAR FRECUENTEMENTE
- Estado: **Producción** — blog live en https://blog.javierledesma.com.ar
- Migración: **Completa** — 19 posts + 26 imágenes locales (mayo 2026)
- Post Marquee: **✅ Funcionando** — componente horizontal estilo Supabase en homepage (mayo 2026)
- Repo: https://github.com/javierledesma28/Ghost-blog
- Notion: https://www.notion.so/Blog-javierledesma-com-ar-3586c5f682d8803c80d9f3149b5b600e

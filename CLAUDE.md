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
- `ghost-content/` → contenido del blog (no commiteado)
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
```

## Archivos Críticos
- `docker-compose.yml` → define los tres servicios: ghost, ghost-db, cloudflared
- `.env.example` → referencia de todas las variables necesarias
- `.gitignore` → excluye `.env`, `mysql-data/`, `ghost-content/`, `backups/`

## Convenciones
- `.env` nunca se commitea; `.env.example` es la referencia con valores placeholder
- `GHOST_URL` apunta al dominio público: `https://blog.javierledesma.com.ar`
- `TUNNEL_TOKEN` se obtiene desde Cloudflare Zero Trust → Tunnels → Blog JavierLedesma → Overview
- Ghost no expone puertos al host — todo el tráfico entra exclusivamente vía tunnel
- La red `ghost-net` es interna al compose; cloudflared resuelve `ghost-blog` por nombre de contenedor

## Lo Que NO Necesita Explicación
- Docker Compose básico
- Variables de entorno en Docker
- Cloudflare Tunnel / cloudflared

## Pendiente
- Proteger `/ghost` (admin) con Cloudflare Access — política de email OTP o Google SSO

## Trabajo Activo ← ACTUALIZAR FRECUENTEMENTE
- Estado: **Producción** — blog live en https://blog.javierledesma.com.ar
- Repo: https://github.com/javierledesma28/Ghost-blog
- Notion: https://www.notion.so/Blog-javierledesma-com-ar-3586c5f682d8803c80d9f3149b5b600e

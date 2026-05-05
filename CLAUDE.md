# Ghost Blog

## Resumen
Infraestructura Docker para publicar y administrar un blog personal con Ghost CMS, expuesto públicamente mediante Cloudflare Tunnel bajo el dominio `blog.javierledesma.com.ar`.

## Stack
- **CMS:** Ghost:latest
- **DB:** MySQL 8
- **Tunnel:** Cloudflare Tunnel (cloudflared) — contenedor externo en `ghost-net`
- **Infra:** Ubuntu Server / Docker Compose / red Docker `ghost-net`

## Arquitectura
```
https://blog.javierledesma.com.ar
        ↓
Cloudflare Tunnel (cloudflared — contenedor externo)
        ↓
ghost-net (red Docker compartida)
        ↓
ghost-blog:2368
```

Estructura de carpetas:
- `docker-compose.yml` → servicios ghost + ghost-db, red ghost-net
- `.env` → variables de entorno (no commiteado)
- `.env.example` → plantilla de variables requeridas
- `ghost-content/` → contenido del blog (no commiteado)
- `mysql-data/` → datos MySQL (no commiteado)

## Comandos Clave
```bash
# Levantar
docker compose up -d

# Bajar
docker compose down

# Recrear (tras cambio de .env)
docker compose down && docker compose up -d

# Logs
docker compose logs -f
docker logs -f ghost-blog
docker logs -f ghost-db

# Estado
docker compose ps
docker network inspect ghost-net
```

## Archivos Críticos
- `docker-compose.yml` → define servicios, volúmenes y red
- `.env.example` → referencia de todas las variables necesarias
- `.gitignore` → excluye `.env`, `mysql-data/`, `ghost-content/`, `backups/`

## Convenciones
- `.env` nunca se commitea; `.env.example` es la referencia con valores placeholder
- `GHOST_URL` debe apuntar al dominio público (`https://blog.javierledesma.com.ar`), no a IP local
- La red `ghost-net` es `external: false` en este compose y es compartida con cloudflared via `docker network connect`
- El bloque `ports` de ghost se elimina una vez validado el túnel (sin él, el servicio solo es accesible desde la red Docker)

## Lo Que NO Necesita Explicación
- Docker Compose básico
- Variables de entorno en Docker
- Cloudflare Tunnel / cloudflared

## Trabajo Activo ← ACTUALIZAR FRECUENTEMENTE
- Sprint / tarea actual: Setup inicial — integración Cloudflare Tunnel
- Próximo hito: Validar `https://blog.javierledesma.com.ar` funcionando end-to-end

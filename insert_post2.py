#!/usr/bin/env python3
import subprocess, uuid, re

def read_env():
    with open('/home/javierledesma/docker/ghost-blog/.env') as f:
        return dict(l.strip().split('=',1) for l in f if '=' in l and not l.startswith('#'))

ENV = read_env()

def sql(query):
    r = subprocess.run(
        ['docker','exec','ghost-db','mysql','--default-character-set=utf8mb4',
         f'-u{ENV["MYSQL_USER"]}', f'-p{ENV["MYSQL_PASSWORD"]}', ENV['MYSQL_DATABASE'], '-se', query],
        capture_output=True, text=True, encoding='utf-8'
    )
    if 'ERROR' in r.stderr and 'Warning' not in r.stderr:
        print(f"  SQL ERROR: {r.stderr.strip()}")
    return r.stdout.strip()

def new_id():
    return uuid.uuid4().hex[:24]

AUTHOR_ID = sql("SELECT id FROM users LIMIT 1;")

def insert_post(title, html, slug, tags, feature_image='', published_at=None, excerpt=''):
    post_id   = new_id()
    post_uuid = str(uuid.uuid4())
    now       = published_at or '2026-01-01 00:00:00'
    lexical   = '{"root":{"children":[{"children":[{"detail":0,"format":0,"mode":"normal","style":"","text":"","type":"text","version":1}],"direction":"ltr","format":"","indent":0,"type":"paragraph","version":1}],"direction":"ltr","format":"","indent":0,"type":"root","version":1}}'

    def esc(s): return s.replace('\\','\\\\').replace("'","\\'")

    q = f"""INSERT INTO posts
  (id,uuid,title,slug,html,lexical,comment_id,plaintext,feature_image,
   featured,type,status,visibility,email_recipient_filter,
   created_at,updated_at,published_at,published_by,custom_excerpt,show_title_and_feature_image)
VALUES
  ('{post_id}','{post_uuid}','{esc(title)}','{slug}','{esc(html)}','{esc(lexical)}',
   '{post_id}','','{feature_image}',
   0,'post','published','public','all',
   '{now}','{now}','{now}',
   '{AUTHOR_ID}','{esc(excerpt[:300])}',1);"""

    sql(q)

    for tag_name in tags:
        tag_slug = re.sub(r'[^a-z0-9]+','-', tag_name.lower()).strip('-')
        tag_id = sql(f"SELECT id FROM tags WHERE slug='{tag_slug}' LIMIT 1;")
        if not tag_id:
            tag_id = new_id()
            sql(f"INSERT INTO tags (id,name,slug,created_at,updated_at) VALUES ('{tag_id}','{tag_name}','{tag_slug}',NOW(),NOW());")
        sort_order = sql(f"SELECT COALESCE(MAX(sort_order)+1,0) FROM posts_tags WHERE post_id='{post_id}';") or '0'
        sql(f"INSERT INTO posts_tags (id,post_id,tag_id,sort_order) VALUES ('{new_id()}','{post_id}','{tag_id}',{sort_order});")

    print(f"✅ Creado: {title}")

# ── POST: Premium v4 ──────────────────────────────────────────────────────────

insert_post(
    title="[Premium v4] ya está aquí: así mejora tu infraestructura PaaS en Azure",
    slug="premium-v4-ya-esta-aqui-asi-mejora-tu-infraestructura-paas-en-azure",
    tags=["AZURE", "NOTICIAS", "ARQUITECTURA", "LVL100"],
    feature_image="https://assets.zyrosite.com/cdn-cgi/image/format=auto,w=768,h=512,fit=crop/Aq2BgVbxvECDEQ7B/premiumv4-AR01vvbEbMF13ee1.png",
    published_at="2025-11-13 00:00:00",
    excerpt="Microsoft anunció la disponibilidad general de Azure App Service Premium v4, la nueva generación del servicio PaaS que ofrece más rendimiento, almacenamiento NVMe y eficiencia de costes.",
    html="""
<h2>El cambio que no sabías que necesitabas</h2>
<p>Hay lanzamientos en Azure que se notan… y otros que se sienten. Premium v4 pertenece a esta segunda categoría.</p>
<p>No trae un eslogan grandilocuente, ni una revolución de concepto. Pero si trabajás día a día con Azure App Service, si vivís esos picos de CPU que te obligan a escalar manualmente o a justificar costes ante finanzas, entonces sí: vas a sentir la diferencia.</p>
<p>Microsoft acaba de anunciar la disponibilidad general (GA) de Azure App Service Premium v4, y aunque parezca una evolución menor, detrás hay un cambio profundo en la forma en que ejecutamos aplicaciones PaaS en la nube.</p>

<h2>¿Qué es exactamente Premium v4?</h2>
<p>Premium v4 es la nueva generación del plan de hosting Premium dentro de Azure App Service. Está diseñado para aplicaciones que demandan más potencia y estabilidad, sin perder la flexibilidad del modelo PaaS.</p>
<p>Entre sus principales novedades:</p>
<ul>
  <li>🔹 Procesadores AMD EPYC 7763 y Intel Xeon Platinum 8370C, con hasta 20 % más rendimiento por núcleo.</li>
  <li>🔹 Almacenamiento local NVMe, hasta 3 veces más rápido que Premium v3.</li>
  <li>🔹 Arranque optimizado y reducción de latencia en despliegues.</li>
  <li>🔹 Compatible con Windows y Linux, manteniendo soporte completo para Web Apps, API Apps, Logic Apps y Mobile Apps.</li>
</ul>
<p>No hay curva de aprendizaje ni reescritura de código: basta con cambiar la SKU.</p>

<figure class="kg-card kg-image-card">
  <img src="https://assets.zyrosite.com/cdn-cgi/image/format=auto,w=1024,h=293,fit=crop/Aq2BgVbxvECDEQ7B/planilla-YrD4ppJxr9UgJMe0.png" class="kg-image" alt="Comparativa Premium v3 vs v4" />
</figure>

<h2>Lo que cambia (aunque no lo veas)</h2>
<p>En la práctica, Premium v4 transforma la manera en que tu infraestructura absorbe carga, escala y se mantiene estable. Las mejoras en hardware y aislamiento permiten que una misma aplicación procese más solicitudes, con menor uso de CPU y memoria.</p>
<p>Y ese punto es clave: no se trata de crecer, sino de crecer mejor. En proyectos donde cada milisegundo importa, o donde cada instancia cuesta, Premium v4 representa un avance silencioso pero profundo.</p>

<h2>Caso de uso: cuando mejorar no requiere romper nada</h2>
<p>Un cliente del sector retail ejecutaba su plataforma e-commerce en Premium v3 (P2v3). Durante campañas de alto tráfico, las alertas de CPU eran constantes y los costos se disparaban por el auto-escalado.</p>
<p>La migración a Premium v4 (P1v4) fue casi anecdótica: solo un cambio de SKU y verificación en los pipelines. El resultado, sin una sola línea de código modificada:</p>
<ul>
  <li>🚀 Tiempos de respuesta: de 450 ms a 270 ms (esto no lo he probado).</li>
  <li>📈 +80 % de rendimiento con menos instancias.</li>
  <li>💰 18 % de ahorro mensual.</li>
</ul>
<p>Una de esas migraciones que justifican solas el cambio.</p>

<h2>Recomendaciones antes de probarlo</h2>
<ul>
  <li>Verificá disponibilidad regional (no todos los datacenters lo ofrecen aún).</li>
  <li>Si necesitás IP saliente fija, considerá NAT Gateway (¡Ojo! que tiene coste fijo por hora + tráfico saliente, así que para entornos chicos puede ser excesivo).</li>
  <li>Actualizá tus pipelines CI/CD o IaC (Bicep, Terraform, ARM) con las nuevas SKUs.</li>
  <li>Realizá pruebas A/B para comparar rendimiento y coste real antes del despliegue total.</li>
</ul>

<h2>Más allá de la técnica: lo que creo que significa para nosotros</h2>
<p>Cada nuevo tier de App Service nos recuerda algo: la nube también madura. Creo que Microsoft no solo busca más velocidad, sino una plataforma más equilibrada — donde el costo, el rendimiento y la sostenibilidad se alineen.</p>
<p>Premium v4 no es un producto nuevo, sino una pieza más sólida del ecosistema. Y para quienes trabajamos día a día diseñando soluciones, representa una oportunidad de mejorar sin interrumpir.</p>

<h2>Conclusión</h2>
<p>A veces, las mejoras más valiosas son las que no hacen ruido. Azure App Service Premium v4 no cambia las reglas del juego… pero sí hace que jugar sea mucho más eficiente.</p>
<p>Si ya trabajás con App Service, vale la pena probarlo. Y si todavía no lo hiciste, este es un buen momento para descubrir por qué el modelo PaaS sigue siendo uno de los grandes aciertos de Azure.</p>
<p>Mi misión con este artículo es simple: compartir algo que descubrí casi por curiosidad, que puede marcar una diferencia real en tus entornos productivos de alto performance. Porque al final, la mejor forma de entender cloud es seguir explorándola juntos ☁️</p>

<h3>Algunos enlaces de contexto...</h3>
<ul>
  <li><a href="https://techcommunity.microsoft.com/t5/apps-on-azure-blog/generally-available-azure-app-service-premium-v4/ba-p/4274581">Anuncio oficial en Microsoft Tech Community</a></li>
  <li><a href="https://learn.microsoft.com/en-us/azure/app-service/overview-hosting-plans">Documentación de App Service Premium v4</a></li>
  <li><a href="https://learn.microsoft.com/en-us/azure/app-service/app-service-configure-premium-tier">Comparativa Premium v3 vs v4 en Azure Docs</a></li>
</ul>
"""
)

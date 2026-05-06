#!/usr/bin/env python3
"""Migración masiva: inserta los 17 posts restantes directamente en Ghost DB"""

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
            sql(f"INSERT INTO tags (id,name,slug,created_at,updated_at) VALUES ('{tag_id}','{esc(tag_name)}','{tag_slug}',NOW(),NOW());")
        sort_order = sql(f"SELECT COALESCE(MAX(sort_order)+1,0) FROM posts_tags WHERE post_id='{post_id}';") or '0'
        sql(f"INSERT INTO posts_tags (id,post_id,tag_id,sort_order) VALUES ('{new_id()}','{post_id}','{tag_id}',{sort_order});")

    print(f"✅ Creado: {title}")

# ─────────────────────────────────────────────────────────────────────────────
# POST 1: WAF vs Firewall
# ─────────────────────────────────────────────────────────────────────────────
insert_post(
    title="[WAF vs Firewall] Gran confusión",
    slug="waf-vs-firewall-gran-confusion",
    tags=["AZURE", "ARQUITECTURA", "LVL100"],
    feature_image="https://assets.zyrosite.com/cdn-cgi/image/format=auto,w=768,h=512,fit=crop/Aq2BgVbxvECDEQ7B/0_pu4ybzlgoyreo3gx-1vaYlNN77lMN8qjV.jpg",
    published_at="2025-11-10 00:00:00",
    excerpt="En este artículo tocamos conceptos que parecen sinónimos… hasta que un día te explotan en producción. El eterno WAF vs Firewall: no es lo mismo y podés necesitar ambos.",
    html="""
<h2>Un caso real</h2>
<p>Hace menos de un año, estaba haciendo doble click en una arquitectura de un cliente con una web crítica de e-commerce sobre Azure App Service.</p>
<p>El entorno ya tenía su Network Security Group (NSG) y su Azure Firewall perfectamente configurados, extremadamente cerrado para ser más preciso.</p>
<p>Puertos cerrados, IPs controladas, reglas limpias. Todo parecía de manual.</p>
<p>Un día, recibimos alertas de comportamiento anómalo: el típico intento de inyección en el login, consultas SQL sospechosas y hasta una pequeña caída en la API pública. La red, según los logs, estaba perfecta. Nada extraño. Pero los ataques entraban igual.</p>
<p>Ahí vino el clásico momento de "mare miaaa". La red estaba segura, pero la aplicación no. El firewall no entiende de payloads HTTP ni de parámetros maliciosos en un formulario.</p>
<p>Es ahí donde necesitábamos control sobre esa capa — y activamos Azure Web Application Firewall (WAF) sobre un Application Gateway. Configuramos las reglas OWASP 3.2, ajustamos el modo de detección a prevención, y… magia: los mismos patrones que antes se colaban, ahora quedaban registrados y bloqueados. Sin tocar una línea del código.</p>

<h2>Cuándo usar uno, cuándo usar ambos</h2>
<p><strong>Usá un Firewall cuando:</strong></p>
<ul>
  <li>Querés controlar tráfico entre redes, subredes o zonas (Internet ↔ Backend, VNet ↔ VNet).</li>
  <li>Necesitás registrar, auditar o limitar conexiones.</li>
  <li>Querés proteger a nivel de infraestructura, no de aplicación.</li>
</ul>
<p><strong>Usá un WAF cuando:</strong></p>
<ul>
  <li>Tenés aplicaciones web o APIs expuestas a Internet.</li>
  <li>Querés inspeccionar contenido HTTP y aplicar protección OWASP.</li>
  <li>No podés confiar solo en la validación de tu código.</li>
</ul>
<p><strong>Usá ambos cuando:</strong></p>
<ul>
  <li>Tu aplicación es pública o crítica, y no querés elegir entre "proteger la casa" o "proteger lo que hay adentro".</li>
</ul>
<p>Uno filtra el acceso al edificio; el otro, vigila cada paquete que entra por la puerta.</p>

<h2>Dónde y por qué colocar el WAF</h2>
<p><strong>En el borde global: Front Door WAF (recomendado)</strong></p>
<p>Filtra todo lo que llega desde Internet antes de tocar tu red. Ideal cuando ya usás Front Door y los orígenes son privados mediante Private Link. Protege HTTP/HTTPS hacia la Web App. Ventajas clave: escala en la red perimetral de Microsoft, mitigación temprana de ataques L7 (OWASP, bots, rate limiting, geo/IP), políticas por ruta.</p>
<p><strong>Flujo recomendado:</strong></p>
<p>Internet → Front Door (WAF) → (Private Link) → VNet → Web App ↓ Azure Firewall</p>
<p>El Firewall sigue aplicando control L3/L4/egreso, pero no sustituye al WAF.</p>
<p><strong>En la capa regional: Application Gateway WAF (como complemento)</strong></p>
<p>Agrega defensa en profundidad para escenarios regionales (multi-región activo/activo, requisitos locales). Cuándo usarlo además del Front Door WAF: cargas muy críticas, false-positives que requieren tuning por región, requisitos de segregación.</p>

<h2>Checklist de implementación (Front Door WAF)</h2>
<ul>
  <li>Front Door Premium + origen privado por Private Link.</li>
  <li>Managed Rules OWASP (3.x) en Prevention con Anomaly Scoring.</li>
  <li>Rate limiting en /login y /api/*.</li>
  <li>Bot Management y bloqueo de IP/ASN/Geo según riesgo.</li>
  <li>TLS: certificado en Front Door + re-encripción al origen (end-to-end TLS).</li>
  <li>Logs: habilitar Diagnostic Settings a Log Analytics; crear alertas.</li>
  <li>Tuning: iniciar en Detection, revisar 3–7 días, pasar a Prevention por rutas priorizadas.</li>
</ul>

<h2>Resumen de decisión</h2>
<ul>
  <li>Si ya tenés Front Door y orígenes privados → WAF en Front Door: mejor cobertura, menor latencia, control por ruta, bots y rate limiting en el borde.</li>
  <li>Si necesitás doble capa o políticas por región/app → añadí Application Gateway WAF detrás de Front Door (defensa en profundidad).</li>
  <li>Azure Firewall permanece para L3/L4/egreso y segmentación; no sustituye al WAF.</li>
</ul>

<h2>Lo que quiero que te lleves...</h2>
<p>El Firewall protege la red; el WAF, la aplicación. Juntos promueven la armonía digital, porque la verdadera seguridad no está en competir, sino en complementarse. En tech, como en la vida, hagamos "la defensa", no la guerra.</p>
<p>Gracias por pasarte y dedicarle tiempo a la lectura!</p>
"""
)

# ─────────────────────────────────────────────────────────────────────────────
# POST 2: Azure Storage Discovery
# ─────────────────────────────────────────────────────────────────────────────
insert_post(
    title='[AZURE] Azure Storage Discovery "Preview"',
    slug="azure-azure-storage-discovery-preview",
    tags=["AZURE", "LVL200", "ARQUITECTURA"],
    feature_image="https://assets.zyrosite.com/cdn-cgi/image/format=auto,w=768,h=512,fit=crop/Aq2BgVbxvECDEQ7B/blog3-AGBzNx0ZQqckpzjV.png",
    published_at="2025-09-03 00:00:00",
    excerpt="Exploramos Azure Storage Discovery, el nuevo servicio en vista previa de Microsoft que centraliza la gestión de Blob Storage en un único panel con integración nativa de Copilot.",
    html="""
<h2>Introducción</h2>
<p>El 6 de agosto de 2025, Microsoft anunció el lanzamiento en vista previa de Azure Storage Discovery, un servicio totalmente gestionado que permite obtener una visión integral de todo el ecosistema de Azure Blob Storage. Gracias a su integración con Azure Copilot, ahora es posible consultar y analizar datos en lenguaje natural, sin necesidad de desarrollar scripts ni desplegar infraestructura adicional.</p>

<h2>¿Qué es Azure Storage Discovery?</h2>
<p>Azure Storage Discovery es un servicio centralizado de insights para Blob Storage que ofrece:</p>
<ul>
  <li>Un único panel ("single pane of glass") para analizar hasta 1 millón de cuentas de almacenamiento distribuidas en múltiples suscripciones y regiones.</li>
  <li>Dashboards interactivos con métricas sobre capacidad, actividad, errores y configuraciones de seguridad.</li>
  <li>Integración nativa con Copilot para hacer preguntas en lenguaje natural.</li>
  <li>Backfill automático de 15 a 30 días y retención de hasta 18 meses (según el plan).</li>
</ul>

<h2>Funcionalidades principales</h2>
<ul>
  <li>Informes visuales de capacidad, transacciones, errores y configuraciones de seguridad.</li>
  <li>Filtros avanzados por región, redundancia, cifrado y más.</li>
  <li>Exportación de insights en CSV para integrarlos en pipelines o automatizaciones.</li>
  <li>Análisis a gran escala sin impacto en el rendimiento de las cuentas de almacenamiento.</li>
  <li>Soporte para Azure Blob Storage y Data Lake Storage (HNS).</li>
</ul>

<h2>Cómo funciona</h2>
<ol>
  <li>Registrar el proveedor de recursos: <code>Microsoft.StorageDiscovery</code>.</li>
  <li>Crear un Workspace en una de las regiones disponibles (France Central, Canada Central, East US2, North Europe, West Europe).</li>
  <li>Definir workspaceRoots: suscripciones o grupos de recursos (hasta 100).</li>
  <li>Configurar hasta 5 scopes por workspace, agrupando cuentas mediante etiquetas ARM.</li>
  <li>Explorar los insights desde el portal o vía CLI/PowerShell.</li>
</ol>

<h2>Requisitos y permisos</h2>
<ul>
  <li>Rol Contributor u Owner para crear workspaces.</li>
  <li>Rol Reader sobre las cuentas de almacenamiento y el workspace para visualizar insights.</li>
  <li>Azure CLI versión 2.75 o superior para creación desde línea de comandos.</li>
</ul>

<h2>Planes y precios</h2>
<p>Durante la vista previa, ambos planes son gratuitos hasta el 30 de septiembre de 2025.</p>
<p><strong>Plan Free:</strong> Tendencias, distribuciones, principales cuentas — BackFill 15 días — Retención 15 días.</p>
<p><strong>Plan Standard:</strong> Todo lo del Free + actividad, errores, configuraciones y seguridad — BackFill 30 días — Retención 18 meses.</p>
<p>A partir del 1 de octubre de 2025, la facturación será escalonada en función del número de cuentas y objetos analizados.</p>

<h2>Casos de uso reales recomendados</h2>
<ul>
  <li>Gobernanza multi-suscripción: visión única de cientos de cuentas en distintas regiones.</li>
  <li>Optimización de costes: identificar datos fríos y moverlos a capas más baratas.</li>
  <li>Seguridad y compliance: validar cifrado, redundancia y alineación con GDPR o ISO.</li>
  <li>Consolidación post-adquisiciones: mapear rápidamente el ecosistema heredado.</li>
  <li>Soporte a FinOps: establecer KPIs de costes y showback/chargeback por unidad de negocio.</li>
  <li>Migraciones y modernización: diagnosticar el data estate antes de proyectos de transformación.</li>
</ul>

<h2>Conclusión</h2>
<p>Azure Storage Discovery llega para simplificar la gestión, seguridad y optimización de Blob Storage en organizaciones con entornos complejos. Al centralizar métricas y permitir consultas con Copilot, elimina la necesidad de scripts manuales y habilita decisiones basadas en datos reales.</p>
<p>Más info: <a href="https://learn.microsoft.com/en-us/azure/storage-discovery/overview">https://learn.microsoft.com/en-us/azure/storage-discovery/overview</a></p>
<p>Gracias por pasarte!</p>
"""
)

# ─────────────────────────────────────────────────────────────────────────────
# POST 3: Azure Local - Problemas Típicos
# ─────────────────────────────────────────────────────────────────────────────
insert_post(
    title="[AZURE-LOCAL] Problemas Típicos y Cómo Evitarlos",
    slug="azure-local-problemas-tipicos-y-como-evitarlos",
    tags=["AZURE", "LVL100"],
    feature_image="https://assets.zyrosite.com/cdn-cgi/image/format=auto,w=768,h=512,fit=crop/Aq2BgVbxvECDEQ7B/jump-m5Knqp7geNF0Jvl5.png",
    published_at="2025-08-11 00:00:00",
    excerpt="Configurar Azure en un entorno local puede parecer simple en los diagramas de marketing, pero la realidad tiene varios puntos críticos. Los 8 problemas más comunes según mi experiencia, con ejemplos reales.",
    html="""
<p>Configurar Azure en un entorno local (Azure Stack, Azure Stack HCI, entornos híbridos) puede parecer simple en los diagramas de marketing, pero la realidad es que hay varios puntos críticos que pueden convertir un despliegue en un dolor de cabeza… o en un éxito rotundo.</p>
<p>¿Recuerdan Azure Local? Se presentó en el Ignite del 2024 como una plataforma de computación híbrida y edge computing que eliminó las barreras entre los entornos locales y los servicios en la nube, basada en Azure Arc.</p>
<p>Hoy comparto los 8 problemas más comunes, ordenados por prioridad según mi experiencia y charlas con colegas en el Azure Global Spain de Zaragoza este 2025.</p>

<h2>1. Configuración de red mal diseñada</h2>
<p><strong>Prioridad: Alta</strong> – Sin red, no hay cloud.</p>
<p>Uno de los errores más frecuentes es no planificar bien la segmentación, DNS y reglas de firewall antes de instalar Azure local.</p>
<p><em>Ejemplo real:</em> En una petrolera, la falta de VLAN dedicadas para tráfico de administración provocó que la replicación entre nodos fallara constantemente. Se perdió una semana entera rastreando paquetes antes de aislar el problema.</p>
<p><strong>Consejo:</strong> Define la topología de red y valida conectividad y latencias antes de montar nada.</p>

<h2>2. Requisitos de hardware ignorados</h2>
<p><strong>Prioridad: Alta</strong> – Si el hardware no cumple, Azure Local no arranca.</p>
<p>Azure Stack tiene requisitos estrictos de CPU, memoria, almacenamiento y firmware.</p>
<p><em>Ejemplo real:</em> Un cliente en México adquirió servidores con controladoras no soportadas. Resultado: instalación bloqueada y semanas de negociación con el proveedor para cambiar hardware.</p>
<p><strong>Consejo:</strong> Valida con la <a href="https://azurelocalsolutions.azure.microsoft.com/#/catalog">Hardware Compatibility List de Microsoft</a> antes de gastar un duro.</p>

<h2>3. Problemas de conectividad con la nube</h2>
<p><strong>Prioridad: Alta</strong> – Sin conexión estable, pierdes sincronización y soporte. Es tu cordón umbilical.</p>
<p><em>Ejemplo real:</em> Un proxy mal configurado bloqueó las actualizaciones de Azure Stack. El sistema quedó desactualizado y varias funciones críticas dejaron de estar disponibles.</p>
<p><strong>Consejo:</strong> Establece redundancia de Internet y abre los puertos recomendados por Microsoft.</p>

<h2>4. Sincronización de directorios fallida</h2>
<p><strong>Prioridad: Media</strong> – Impacta el acceso y la autenticación.</p>
<p><em>Ejemplo real:</em> En una integración con Azure AD Connect, un error en las reglas de filtrado provocó que usuarios clave no aparecieran en la nube. Resultado: no podían acceder a portales ni recursos.</p>
<p><strong>Consejo:</strong> Documenta y valida la sincronización con entornos de prueba antes del corte final.</p>

<h2>5. Certificados y seguridad mal gestionados</h2>
<p><strong>Prioridad: Media</strong> – La seguridad no es opcional.</p>
<p><em>Ejemplo real:</em> Un certificado SSL caducado bloqueó el acceso HTTPS al portal de administración de Azure Stack. El downtime se pudo evitar con un monitoreo básico de fechas de expiración.</p>
<p><strong>Consejo:</strong> Centraliza la gestión de certificados y usa recordatorios automáticos.</p>

<h2>6. Integración deficiente de servicios híbridos</h2>
<p><strong>Prioridad: Media/Baja</strong> – El potencial híbrido se pierde.</p>
<p><em>Ejemplo real:</em> Un cliente no pudo integrar Azure Backup con su almacenamiento local por no cumplir los requisitos de latencia. Resultado: backup incompleto y pérdida de datos en un incidente.</p>
<p><strong>Consejo:</strong> Mide y documenta requisitos de cada servicio antes de implementarlo.</p>

<h2>7. Actualizaciones y parches olvidados</h2>
<p><strong>Prioridad: Baja</strong> – Hasta que algo falla.</p>
<p><em>Ejemplo real:</em> Un entorno que no recibía actualizaciones por seis meses perdió soporte y tuvo que ser reinstalado desde cero.</p>
<p><strong>Consejo:</strong> Define un calendario de mantenimiento y síguelo religiosamente.</p>

<h2>8. Costes y licenciamiento mal calculados</h2>
<p><strong>Prioridad: Baja</strong> – Pero puede doler en el presupuesto.</p>
<p><em>Ejemplo real:</em> Un cliente no consideró los costos de transferencia de datos a Azure público. La factura mensual se disparó un 35%.</p>
<p><strong>Consejo:</strong> Usa la <a href="https://azure.microsoft.com/es-es/pricing/details/azure-local/">calculadora oficial de Microsoft</a> y añade un margen para imprevistos.</p>

<h2>Conclusión</h2>
<p>Montar Azure Local no es simplemente "bajar un instalador" y seguir un asistente. Es un proyecto de ingeniería que combina planificación estratégica, precisión técnica y una buena dosis de previsión.</p>
<p>La clave: planifica, valida, documenta y revisa. En cloud, como en la vida, lo más caro no es el hardware ni el software… es aprender de los errores cuando ya es demasiado tarde.</p>
"""
)

# ─────────────────────────────────────────────────────────────────────────────
# POST 4: Azure Functions Proxies
# ─────────────────────────────────────────────────────────────────────────────
insert_post(
    title="[AZURE] Chau chau! Azure Functions Proxies",
    slug="azure-chau-chau-azure-functions-proxies",
    tags=["AZURE", "LVL200", "ARQUITECTURA"],
    feature_image="",
    published_at="2025-07-30 00:00:00",
    excerpt="Microsoft anunció que Azure Functions Proxies dejará de recibir soporte a partir del 30 de septiembre de 2025. Te cuento un ejemplo práctico y cómo migrar a Azure API Management.",
    html="""
<h2>Adiós a Azure Functions Proxies: tips y qué hacer antes de septiembre 2025</h2>
<p>Si alguna vez trabajaste con Azure Functions, seguramente recuerdas Azure Functions Proxies, esa funcionalidad práctica para crear endpoints ligeros y unificar rutas sin tener que montar un gateway completo.</p>
<p>Microsoft anunció que Azure Functions Proxies dejará de recibir soporte a partir del 30 de septiembre de 2025. Aunque puede seguir funcionando por un tiempo, ya está deprecado y podría eliminarse en cualquier momento.</p>
<p><a href="https://learn.microsoft.com/en-us/answers/questions/2285459/official-clarification-needed-azure-functions-prox">Ver aviso oficial aquí.</a></p>

<h2>Caso práctico: Unificando APIs con Azure Functions Proxies</h2>
<p>Supongamos que tenés dos Azure Functions: FunctionA en <code>/api/func-a</code> y FunctionB en <code>/api/func-b</code>. Con Proxies podías definir un archivo <code>proxies.json</code> como este:</p>
<pre><code class="language-json">{
  "$schema": "http://json.schemastore.org/proxies",
  "proxies": {
    "MyAPI": {
      "matchCondition": {
        "route": "api/my-api/{endpoint}"
      },
      "backendUri": "https://&lt;funcapp&gt;.azurewebsites.net/api/{endpoint}"
    }
  }
}</code></pre>
<p>Esto permitía exponer un único endpoint <code>/api/my-api/...</code> que redirigía dinámicamente a las Functions según el parámetro <code>{endpoint}</code>.</p>

<h2>¿Cuál es el problema ahora?</h2>
<p>A partir de septiembre de 2025, este tipo de configuración dejará de estar soportada. Si tu aplicación depende de Proxies, existe el riesgo de que tus endpoints dejen de funcionar.</p>

<h2>Alternativa recomendada: Azure API Management</h2>
<p>Con APIM, podemos lograr la misma funcionalidad creando una API con rutas personalizadas y políticas de reenvío (backend URL rewrite). Ejemplo de política APIM para la misma lógica:</p>
<pre><code class="language-xml">&lt;inbound&gt;
  &lt;base /&gt;
  &lt;set-backend-service base-url="https://&lt;funcapp&gt;.azurewebsites.net/api" /&gt;
&lt;/inbound&gt;</code></pre>
<p>Luego definimos las rutas <code>/func-a</code> y <code>/func-b</code> dentro de la API, gestionando autenticación, permisos y versionado de forma centralizada.</p>
<p>Ejemplo oficial: <a href="https://github.com/Azure-Samples/functions-proxies/blob/master/ProxiesSamples/proxies.json">github.com/Azure-Samples/functions-proxies</a></p>

<h2>Lo que esto nos deja</h2>
<p>El "Shift + Delete" de Azure Functions Proxies marca el fin de una herramienta sencilla que muchos usamos para resolver problemas rápidos en entornos serverless. Sin embargo, también abre la puerta a adoptar soluciones más completas como Azure API Management, que nos brindan mayor seguridad, escalabilidad y control.</p>
<p>Con APIM en mi experiencia no fue todo color de rosas — el mayor defecto es su complejidad inicial de configuración y la curva de aprendizaje para equipos que no están familiarizados con la gestión de políticas y versiones de API.</p>
<p>Más info: <a href="https://learn.microsoft.com/es-es/azure/api-management/">Documentación oficial de Azure API Management</a></p>
"""
)

# ─────────────────────────────────────────────────────────────────────────────
# POST 5: Google Compra de WIZ
# ─────────────────────────────────────────────────────────────────────────────
insert_post(
    title="[GOOGLE] Compra de WIZ!",
    slug="google-compra-de-wiz",
    tags=["NOTICIAS", "GOOGLE"],
    feature_image="https://assets.zyrosite.com/cdn-cgi/image/format=auto,w=768,h=512,fit=crop/Aq2BgVbxvECDEQ7B/1ab216d3-5f6d-441a-8c3e-0e61975ba6d3-m7Vb74Nn03Ur7W03.png",
    published_at="2025-03-28 00:00:00",
    excerpt="Google acaba de cerrar la operación más grande de su historia: la compra de Wiz por 32.000 millones de dólares. Una apuesta que redefine el futuro de la ciberseguridad en la nube.",
    html="""
<h2>¿32.000 millones por una startup?</h2>
<p>Sí, y todo gira en torno a la ciberseguridad.</p>
<p>Google anunció su mayor adquisición hasta la fecha: la compra de Wiz, una startup de ciberseguridad nacida en 2020, por nada menos que 32.000 millones de dólares. Una cifra que, más allá del impacto, marca una tendencia clara en el mercado tecnológico.</p>

<h2>Una startup joven, con foco y resultados</h2>
<p>Wiz no lleva ni cinco años en el mercado, pero supo hacer bien las cosas desde el principio. Apuntó directo a uno de los dolores más sensibles del ecosistema actual: la seguridad en la nube. Hoy trabaja con más del 40% de las empresas del Fortune 100 y genera alrededor de 700 millones de dólares al año en ingresos recurrentes.</p>
<p>Y si te preguntás por qué alguien pagaría semejante suma por una empresa tan joven, la respuesta está en la estrategia: Wiz no quiso abarcar todo, quiso hacerlo bien y hacerlo seguro.</p>

<h2>Más que una adquisición, una jugada estratégica</h2>
<p>Para Google, esto no es solo sumar tecnología. Es una apuesta fuerte por diferenciarse en el mundo cloud, integrando capacidades de seguridad que ya vienen listas para escalar en entornos híbridos y multinube. Y, de paso, preparar el terreno para la inteligencia artificial, donde la protección de datos es (y va a seguir siendo) una prioridad crítica.</p>

<h2>Una nota de color…</h2>
<p>Hace unos meses, Wiz rechazó una oferta de 23.000 millones. Y ahora, cierra trato por 32.000. Parece que el equipo de ventas no solo tiene visión técnica… también sabe negociar. Uno no se encuentra con una contraoferta de 9 mil millones todos los días.</p>

<h2>¿Y esto qué nos dice a los que trabajamos en tecnología?</h2>
<ul>
  <li>Que la ciberseguridad dejó de ser un tema "de IT" y se volvió core del negocio.</li>
  <li>Que la especialización sigue siendo una ventaja competitiva real.</li>
  <li>Y que el crecimiento exponencial todavía es posible, incluso en mercados maduros, cuando se resuelve un problema crítico con claridad y foco.</li>
</ul>
<p>No suelo escribir sobre adquisiciones, pero este caso me pareció especialmente relevante para quienes estamos en el mundo de la nube, la arquitectura y la seguridad. No tanto por el número en sí (que impacta), sino por lo que refleja del momento actual del mercado.</p>
<p>☁️ Wiz + Google marcan tendencia en seguridad multicloud.</p>
"""
)

# ─────────────────────────────────────────────────────────────────────────────
# POST 6: Azure Dev Box
# ─────────────────────────────────────────────────────────────────────────────
insert_post(
    title="[AZURE] Azure Dev Box",
    slug="azure-azure-dev-box",
    tags=["AZURE", "LVL100"],
    feature_image="https://assets.zyrosite.com/cdn-cgi/image/format=auto,w=768,h=512,fit=crop/Aq2BgVbxvECDEQ7B/dev-box-concepts-overview-1-mk3zNM9lXgsBWkbq.png",
    published_at="2024-09-22 00:00:00",
    excerpt="Microsoft Dev Box es un servicio de Azure que proporciona a los desarrolladores acceso de autoservicio a equipos de desarrollo preconfigurados específicos para cada proyecto.",
    html="""
<h2>Explorando Azure Dev Box: La navaja suiza para desarrolladores</h2>
<p>En el mundo del desarrollo de software, contar con un entorno de desarrollo eficiente y flexible es crucial. Aquí es donde entra en juego Azure Dev Box, una solución innovadora de Microsoft diseñada para optimizar y simplificar el trabajo de los desarrolladores.</p>

<h2>¿Qué es Azure Dev Box?</h2>
<p>Azure Dev Box es un servicio de Microsoft Azure que proporciona entornos de desarrollo preconfigurados y escalables en la nube. Estos entornos están diseñados para ser utilizados por equipos de desarrollo de software, permitiendo a los desarrolladores trabajar en proyectos complejos sin preocuparse por la configuración y el mantenimiento de sus estaciones de trabajo, evitando burocracias y tiempos muertos.</p>

<h2>Beneficios de Azure Dev Box</h2>
<ul>
  <li><strong>Configuración Rápida y Sencilla:</strong> Los desarrolladores pueden desplegar entornos de desarrollo en cuestión de minutos, eliminando la necesidad de configurar manualmente cada máquina.</li>
  <li><strong>Escalabilidad:</strong> Azure Dev Box permite escalar los recursos según las necesidades del proyecto.</li>
  <li><strong>Seguridad:</strong> Al ser full cloud, Azure Dev Box se beneficia de las robustas medidas de seguridad de Microsoft.</li>
  <li><strong>Colaboración Mejorada:</strong> Los equipos pueden compartir entornos de desarrollo y colaborar en tiempo real.</li>
  <li><strong>Personalización:</strong> Es posible utilizar imágenes custom en los despliegues.</li>
</ul>

<h2>Casos de Uso</h2>
<ul>
  <li><strong>Desarrollo de Aplicaciones:</strong> Ideal para equipos que desarrollan aplicaciones complejas y necesitan entornos consistentes y reproducibles.</li>
  <li><strong>Pruebas y QA:</strong> Permite crear entornos de prueba idénticos al entorno de producción, mejorando la calidad del software.</li>
  <li><strong>Proyectos Temporales:</strong> Perfecto para proyectos a corto plazo donde se requiere un entorno de desarrollo rápido y desechable.</li>
</ul>

<figure class="kg-card kg-image-card">
  <img src="https://assets.zyrosite.com/cdn-cgi/image/format=auto,w=768,h=512,fit=crop/Aq2BgVbxvECDEQ7B/dev-box-concepts-overview-1-mk3zNM9lXgsBWkbq.png" class="kg-image" alt="Azure Dev Box Architecture" />
</figure>

<h2>Conclusión</h2>
<p>Azure Dev Box es una herramienta extremadamente poderosa que puede transformar la manera en que los desarrolladores trabajan. Permite a los equipos centrarse en lo que realmente importa: escribir código de calidad y entregar productos en menos tiempo.</p>
<p>Muchos de los que leemos estas líneas probablemente hayamos trabajado en empresas donde los Devs son los que más burocracia técnica requieren. Aquí hay una excelente herramienta para que puedan autogestionarse.</p>
<p>Gracias por pasarte y dedicarle un tiempo al post!</p>
"""
)

# ─────────────────────────────────────────────────────────────────────────────
# POST 7: Azure Bot Services
# ─────────────────────────────────────────────────────────────────────────────
insert_post(
    title="[AZURE] Azure Bot Services",
    slug="azure-azure-bot-services-copy",
    tags=["AZURE", "IA", "LVL100"],
    feature_image="https://assets.zyrosite.com/cdn-cgi/image/format=auto,w=768,h=512,fit=crop/Aq2BgVbxvECDEQ7B/abs-A3QJ83bQBJf5ZB5j.png",
    published_at="2024-07-23 00:00:00",
    excerpt="Azure Bot Services es la plataforma de Microsoft que permite crear, desplegar y gestionar bots conversacionales de IA integrados en sitios web, Teams, WhatsApp y más.",
    html="""
<p>Azure Bot Services es una plataforma de Microsoft que permite a los desarrolladores crear, desplegar y gestionar bots conversacionales de inteligencia artificial. Estos bots pueden integrarse en diversas aplicaciones y servicios, como sitios web, aplicaciones móviles, Microsoft Teams, y muchas otras integraciones más.</p>

<h2>¿Para qué sirve?</h2>
<p>Azure Bot Services facilita la creación de bots que pueden:</p>
<ul>
  <li><strong>Automatizar tareas repetitivas:</strong> como responder preguntas frecuentes o procesar solicitudes de servicio al cliente.</li>
  <li><strong>Mejorar la interacción con los usuarios:</strong> Brindando respuestas rápidas y precisas.</li>
  <li><strong>Integración con otros servicios de Azure:</strong> Como Azure Cognitive Services para añadir capacidades de lenguaje natural (NLP) y reconocimiento de voz.</li>
</ul>

<h2>Ejemplos de uso</h2>
<ul>
  <li><strong>Servicio al cliente:</strong> Un bot puede manejar consultas comunes de los clientes, como el estado de un pedido o la política de devoluciones.</li>
  <li><strong>Asistente virtual:</strong> Empresas pueden crear asistentes virtuales que ayuden a los empleados con tareas internas, como programar reuniones o buscar información en la base de datos.</li>
  <li><strong>E-commerce:</strong> Un bot puede guiar a los clientes a través del proceso de compra y recomendar productos basados en sus preferencias.</li>
</ul>

<h2>Azure Bot Services vs QnA Maker</h2>
<p><strong>Propósitos:</strong></p>
<ul>
  <li><strong>Azure Bot Services:</strong> Es una plataforma completa para crear, testear, implementar y gestionar bots inteligentes. Permite integrar diferentes servicios como LUIS, QnA Maker, y otros servicios de Azure para crear bots más complejos y funcionales.</li>
  <li><strong>QnA Maker:</strong> Específicamente diseñado para crear bots de preguntas y respuestas. Permite convertir documentos y bases de datos en una base de conocimiento que los bots pueden usar para responder preguntas de manera automática.</li>
</ul>
<p><strong>Funcionalidades:</strong></p>
<ul>
  <li><strong>Azure Bot Services:</strong> Ofrece una capa de aplicación donde puedes implementar lógica de negocio adicional, integrar APIs externas, y manejar interacciones más complejas. Facilita la integración con múltiples canales de comunicación como Teams, Slack, Facebook Messenger.</li>
  <li><strong>QnA Maker:</strong> Se centra en recuperar respuestas de una base de conocimiento predefinida. Es ideal para información estática y preguntas frecuentes.</li>
</ul>

<h2>Conclusión</h2>
<p>No hay uno mejor que otro, pero sí siempre hay uno que es más acorde a la necesidad. Para bots concisos y eliminación de tareas repetitivas o información clara, iremos por QnA Maker — es siempre el primer paso. Mientras que para explotar la integración, debemos avanzar a un servicio más complejo con sus respectivos componentes.</p>
<p>Gracias por pasarte y leerme!</p>
"""
)

# ─────────────────────────────────────────────────────────────────────────────
# POST 8: IaC - Azure Resource Manager
# ─────────────────────────────────────────────────────────────────────────────
insert_post(
    title="[AZURE] IaC - Azure Resource Manager",
    slug="azure-iac-azure-resource-manager",
    tags=["AZURE", "LVL100"],
    feature_image="https://assets.zyrosite.com/cdn-cgi/image/format=auto,w=768,h=512,fit=crop/Aq2BgVbxvECDEQ7B/arquitectura-mjE9WQzonBf54QEz.png",
    published_at="2024-07-08 00:00:00",
    excerpt="Azure Resource Manager (ARM) es el servicio de implementación y administración de Azure que permite configurar infraestructura una vez y desplegarla en múltiples entornos sin problemas.",
    html="""
<h2>¿Qué y Por qué?</h2>
<p>Cuando se trata de infraestructura en la nube, a medida que tu aplicación comienza a utilizar más componentes y a tener múltiples entornos (desarrollo, pruebas, producción), vas a encontrar la necesidad de una forma consistente de implementar la misma infraestructura en todos los entornos sin modificaciones.</p>
<p>Aquí es donde entra en juego Azure Resource Manager (ARM) — nos permite configurar infraestructura una vez y luego usar la parametrización para implementarla en múltiples entornos sin problemas. Y recuerden: no es Bicep (quizás armo uno más adelante de Bicep).</p>

<h2>Puntos clave a tener en cuenta</h2>
<ul>
  <li><strong>Administración Coherente:</strong> ARM proporciona una interfaz consistente para administrar todos los aspectos de tus recursos de Azure.</li>
  <li><strong>Control de Acceso:</strong> Podés definir quién tiene permiso para hacer qué dentro de tu infraestructura de Azure.</li>
  <li><strong>Plantillas Declarativas:</strong> Podés definir la infraestructura y las dependencias de tu aplicación en una plantilla declarativa, facilitando la implementación repetida y consistente.</li>
  <li><strong>Agrupación de Recursos:</strong> Permite agrupar recursos relacionados, simplificando la administración y la visualización.</li>
</ul>

<h2>¿Qué instalar?</h2>
<p><strong>Azure Tools:</strong> Extensiones para Visual Studio Code. Con la CLI de Azure o las diversas extensiones del paquete de extensión de Azure Tools, podemos ejecutarlas en nuestra aplicación en minutos.</p>
<p><strong>Azure Resource Manager (ARM) Tools:</strong> Para la creación de un nuevo ARM template — cuando tengamos un archivo .json vacío, escribir <code>arm</code> para que muestre toda la lista de posibilidades. Se pueden usar para crear plantillas de Tenant, Subscription, Management Group, y Resource Group.</p>
<p><strong>ARM Template Viewer:</strong> Algo asombroso: usarlo para tener la vista previa de las plantillas ARM. Muestra todos los recursos con sus iconos oficiales de Azure y los vínculos que existen entre ellos. Basado en la biblioteca Cytoscape.js. Se pueden arrastrar y mover los iconos, acercar y alejar.</p>

<h2>Recursos útiles</h2>
<ul>
  <li><a href="https://github.com/Azure/azure-quickstart-templates">Azure Quickstart Templates en GitHub</a> — Miles de templates para iniciarte.</li>
  <li><a href="http://armviz.io/">Armviz.IO</a> — Designer visual para tener tus ARM más gráficos.</li>
</ul>

<p>Espero que los motive a iniciarse con sus ARMs. Gracias por pasarse y leerme!</p>
"""
)

# ─────────────────────────────────────────────────────────────────────────────
# POST 9: Copilot Studio
# ─────────────────────────────────────────────────────────────────────────────
insert_post(
    title="[IA] Alguien dijo Copilot Studio??",
    slug="ia-alguien-dijo-copilot-studio",
    tags=["AZURE", "LVL100"],
    feature_image="https://assets.zyrosite.com/cdn-cgi/image/format=auto,w=1024,h=436,fit=crop/Aq2BgVbxvECDEQ7B/2023-12-04-14-28-27-203-Y4L4B754OPskQ33y.png",
    published_at="2024-06-05 00:00:00",
    excerpt="Copilot Studio: la plataforma de Microsoft que permite crear y personalizar copilotos utilizando IA generativa, diálogos sofisticados, complementos y análisis integrados.",
    html="""
<p>Esta vez no hablaré de tortillas de papas! Hablemos de vanguardia de la innovación tecnológica: Copilot Studio es como la herramienta epicentro de la inteligencia artificial aplicada al desarrollo en la nube. Esta plataforma de Microsoft es una de las últimas joyitas públicas conocidas donde la creatividad de los desarrolladores se fusionan con la precisión de la IA para crear copilotos personalizados en la suite de Microsoft 365.</p>

<h2>Arquitectura Técnica de Copilot Studio</h2>
<p>Copilot Studio se basa en una arquitectura de bajo código gráfico, permitiendo a los usuarios diseñar interfaces conversacionales impulsadas por modelos de lenguaje de gran escala (LLMs) y fuentes adicionales de conocimiento. Su entorno de desarrollo integrado proporciona un lienzo unificado para construir copilotos con IA generativa, facilitando la creación rápida y la integración sencilla en sitios web y aplicaciones.</p>

<h2>Funcionalidades Clave</h2>
<ul>
  <li><strong>Diseño Personalizado:</strong> Permite a los usuarios definir la funcionalidad y el comportamiento del copiloto, desde la automatización de tareas hasta la interacción con servicios de Azure.</li>
  <li><strong>IA Generativa:</strong> Utiliza inteligencia artificial avanzada para construir copilotos que pueden entender y responder en lenguaje natural, mejorando la experiencia del usuario final.</li>
  <li><strong>Conectores de Copilot Studio:</strong> Incluye derechos de Power Automate con límites de aceleración superiores, incluyendo conectores Premium, asegurando que todos los flujos comiencen y terminen con conectores de Copilot Studio.</li>
</ul>

<h2>Capacidades de Integración</h2>
<p>Copilot Studio ofrece una integración fluida con otros servicios y plataformas, permitiendo la publicación en Microsoft Teams, Facebook y otros canales. Además, proporciona herramientas para monitorear y diagnosticar el rendimiento del copiloto.</p>

<h2>Consideraciones de Implementación</h2>
<ul>
  <li><strong>Licenciamiento:</strong> Se factura mensualmente con capacidad acumulada a nivel de inquilino, con 2000 sesiones sin límites en el canal.</li>
  <li><strong>Capacidad de Dataverse:</strong> Incluye 10 GB de base de datos, 10 GB de archivos y 2 GB de registro.</li>
  <li><strong>Mejores prácticas:</strong> La documentación oficial ofrece una amplia variedad de orientación desde la creación hasta la extensión de copilotos.</li>
</ul>

<h2>Conclusión</h2>
<p>Si trabajaste con Power Virtual Agent, o Azure Bot Services, Copilot Studio te resultará muy familiar. Sin dudas, democratiza el acceso a soluciones de IA porque eleva el potencial creativo y la facilidad para técnicos (y no tanto) de los desarrolladores. Es una herramienta que no solo responde a las necesidades actuales sino que también anticipa las demandas futuras de un mundo que cada vez está más impulsado por la IA 🤖</p>
<p><em>"Copilot Studio, herramienta epicentro de la inteligencia artificial aplicada al desarrollo en la nube"</em></p>
"""
)

# ─────────────────────────────────────────────────────────────────────────────
# POST 10: Networking SQL Warehouse + StorageAccount
# ─────────────────────────────────────────────────────────────────────────────
insert_post(
    title="[Networking] SQL Warehouse + StorageAccount",
    slug="networking-sql-warehouse-storageaccount",
    tags=["AZURE", "LVL300", "NETWORKING", "SCRIPTING"],
    feature_image="https://assets.zyrosite.com/cdn-cgi/image/format=auto,w=1024,h=436,fit=crop/Aq2BgVbxvECDEQ7B/blog-databricks-mk3DpGN2GDU14WnN.png",
    published_at="2024-06-03 00:00:00",
    excerpt="Si querías leer datos desde un SQL Warehouse dentro de DataBricks pero no tenés lecturas del Storage Account con networking habilitado, estás en el lugar correcto.",
    html="""
<p>Un componente como SQL Warehouse dentro de Azure Databricks es un recurso de cómputo que permite consultar y explorar datos en la plataforma. Databricks recomienda el uso de almacenes SQL serverless mientras sea posible.</p>

<h2>El error típico — la verdad de la milanesa</h2>
<p>¿Qué pasa si tengo mi SQL Warehouse (serverless) dentro de mi Workspace de Databricks y necesito leer datos de mi Storage Account? Si este Storage Account está configurado bajo mejores prácticas de securización (Security/Networking habilitado como "Enable from selected virtual networks and IP addresses"), entonces el problema comienza.</p>
<p>Al estar queriendo acceder a un serverless, debo indicarle al Storage Account desde donde será consumido. Debo tener identificado el NW de la zona específica donde está dado de alta mi SQL Warehouse, para atachar las reglas de networking. ¡Ojo! El serverless es un servicio ajeno a nuestra administración.</p>

<h2>Zonas y subnets</h2>
<p>En mi caso tengo todos los recursos desplegados en East US 2.</p>
<ul>
  <li><a href="https://learn.microsoft.com/en-us/azure/databricks/administration-guide/cloud-configurations/azure/serverless-firewall">Zonas admitidas</a></li>
  <li><a href="https://learn.microsoft.com/en-us/azure/databricks/security/network/serverless-network-security/serverless-firewall">Subnets admitidas</a></li>
</ul>

<h2>Configuración por Bash o PowerShell</h2>
<p><strong>BASH:</strong></p>
<pre><code class="language-bash">#!/bin/bash
SUBNETS=(
  /subscriptions/8453a5d5-9e9e-40c7-87a4-0ab4cc197f48/resourceGroups/prod-azure-eastusc3-nephos2/providers/Microsoft.Network/virtualNetworks/kaas-vnet/subnets/worker-subnet
  /subscriptions/8453a5d5-9e9e-40c7-87a4-0ab4cc197f48/resourceGroups/prod-azure-eastusc3-nephos3/providers/Microsoft.Network/virtualNetworks/kaas-vnet/subnets/worker-subnet
)
for SUBNET in ${SUBNETS[@]}
do
  az storage account network-rule add \
    --subscription 9999999-1ff3-43f4-b91e-d0ceb97111111 \
    --resource-group mystorage-rg \
    --account-name myaccount \
    --subnet ${SUBNET}
done</code></pre>

<p><strong>POWERSHELL:</strong></p>
<pre><code class="language-powershell">Add-AzStorageAccountNetworkRule `
  -ResourceGroupName &lt;resource group name&gt; `
  -Name &lt;storage account name&gt; `
  -VirtualNetworkResourceId &lt;subnets&gt;</code></pre>

<p>No olvides sustituir los placeholders con los valores reales de tu entorno.</p>
<p>Gracias por pasarte y leerme!</p>
"""
)

# ─────────────────────────────────────────────────────────────────────────────
# POST 11: Políticas y/o baseline de seguridad
# ─────────────────────────────────────────────────────────────────────────────
insert_post(
    title="[AZURE] Políticas y/o baseline de seguridad",
    slug="azure-politicas-yo-baseline-de-seguridad",
    tags=["AZURE", "SEGURIDAD", "LVL100"],
    feature_image="https://assets.zyrosite.com/cdn-cgi/image/format=auto,w=1024,h=436,fit=crop/Aq2BgVbxvECDEQ7B/azurepolicy-d95pjXeVM2IEO5eZ.png",
    published_at="2024-06-01 00:00:00",
    excerpt="Las Azure Security Baseline Policies son un conjunto de configuraciones y prácticas recomendadas diseñadas para proteger los servicios y recursos sobre Azure.",
    html="""
<h2>Políticas baselines de Seguridad sobre Azure</h2>
<p>La seguridad de la información es más importante que nunca, especialmente cuando se trata de infraestructuras cloud. En nuestro tenant de Microsoft tenemos un conjunto de políticas conocidas como Azure Security Baseline Policies, que son únicas e importantes para mantener tus recursos/componentes en la nube seguros y protegidos.</p>

<h2>¿Qué son las Azure Security Baseline Policies?</h2>
<p>Las Azure Security Baseline Policies son un conjunto de configuraciones y prácticas recomendadas diseñadas para proteger los servicios y recursos sobre Azure. Estas políticas están alineadas con el Microsoft Cloud Security Benchmark, que proporciona recomendaciones sobre cómo asegurar las distintas soluciones en el tenant.</p>

<h2>Componentes Principales</h2>
<ul>
  <li><strong>Perfil de Seguridad:</strong> Resume los comportamientos de alto impacto de Azure Policy, que pueden resultar en consideraciones de seguridad aumentadas.</li>
  <li><strong>Gestión de Identidades:</strong> Incluye prácticas para gestionar identidades de aplicaciones de forma segura y automática.</li>
  <li><strong>Protección de Datos:</strong> Se centra en la encriptación de datos sensibles en tránsito y en reposo.</li>
</ul>

<h2>¿Por qué debo implementar las Políticas de Línea Base de Seguridad?</h2>
<ul>
  <li><strong>Estandarización:</strong> Proporcionan un marco estandarizado que describe las capacidades de seguridad disponibles y las configuraciones óptimas.</li>
  <li><strong>Herramienta madura:</strong> Ayuda a fortalecer la seguridad a través de un mejor seguimiento y características de los actores de seguridad.</li>
  <li><strong>Cumplimiento:</strong> Permiten medir el cumplimiento con los controles y recomendaciones del benchmark de seguridad de Microsoft.</li>
</ul>

<h2>Implementación</h2>
<p>Para implementar estas políticas, podés seguir una guía paso a paso que incluye navegar a la sección de Políticas en el portal de Azure, buscar las políticas baselines de seguridad y asignarlas a los servicios de Azure que considerés proteger.</p>

<h2>Conclusión</h2>
<p>Las Azure Security Baseline Policies deben existir en cualquier organización. Son esenciales ya que buscan siempre proteger los recursos en la nube. Proporcionan un conjunto de prácticas recomendadas y configuraciones que, cuando se implementan, pueden mejorar significativamente la postura de seguridad de tus servicios en Azure.</p>
<p><a href="https://learn.microsoft.com/en-us/security/benchmark/azure/">Más info oficial</a></p>
"""
)

# ─────────────────────────────────────────────────────────────────────────────
# POST 12: Hub & Spokes
# ─────────────────────────────────────────────────────────────────────────────
insert_post(
    title="[AZURE] Hub & Spokes",
    slug="azure-hub-and-spokes",
    tags=["AZURE", "SEGURIDAD", "ARQUITECTURA", "LVL100"],
    feature_image="https://assets.zyrosite.com/cdn-cgi/image/format=auto,w=1024,h=638,fit=crop/Aq2BgVbxvECDEQ7B/hub-spoke-A0xNZyjKVyfyN50E.png",
    published_at="2024-06-01 00:00:00",
    excerpt="Diseño de red Hub & Spoke en Azure priorizando la seguridad y aislamiento de los entornos, siendo eficientes y generando ahorro sobre el tenant.",
    html="""
<h2>La Topología de Red Hub and Spoke en Azure</h2>
<p>En el mundo cloud, la eficiencia y la organización de la red son cruciales para el rendimiento y la seguridad. Una de las topologías de red más efectivas utilizadas en Azure es la conocida como hub and spoke. Esta arquitectura permite una gestión centralizada y una optimización en la comunicación entre distintos recursos y componentes.</p>

<h2>¿Qué es la Topología Hub and Spoke?</h2>
<p>La topología hub and spoke es un diseño de red que consiste en un nodo central (el hub) que actúa como punto de interconexión para otros nodos (los spokes). En Azure, uso esta topología para simplificar la conectividad, proporcionar servicios centralizados sin dejar afuera la seguridad y la conectividad a Internet. Sin dejar afuera nuestras queridas VPN's 😁</p>

<h2>Componentes clave</h2>
<ul>
  <li><strong>Red Virtual del Hub:</strong> Es el corazón de la topología, donde se alojan servicios compartidos como Azure Firewall, Azure VPN Gateway y Azure Bastion. Esta red central facilita la conectividad y la administración de los servicios de seguridad aislados.</li>
  <li><strong>Redes Virtuales de Spoke:</strong> Son redes periféricas conectadas al hub. Cada spoke puede representar diferentes unidades de negocio, proyectos o entornos (prod, dev, qa, staging), manteniendo la separación y las propias cargas de trabajo.</li>
  <li><strong>Conectividad de Red Virtual:</strong> Las redes virtuales se conectan mediante emparejamientos o grupos conectados, permitiendo el intercambio de tráfico a través de la red troncal de Azure sin necesidad de un enrutador generalmente.</li>
</ul>

<h2>Ventajas de la Topología Hub and Spoke</h2>
<ul>
  <li><strong>Centralización:</strong> Facilita la gestión de servicios críticos en un solo lugar, reduciendo la complejidad y mejorando la seguridad.</li>
  <li><strong>Escalabilidad:</strong> Permite añadir nuevos spokes fácilmente, lo que hace que la red sea altamente escalable.</li>
  <li><strong>Aislamiento:</strong> Asegura que las cargas de trabajo en diferentes spokes estén aisladas, lo que es esencial para la seguridad y la gestión de riesgos.</li>
</ul>

<h2>Implementación en Azure</h2>
<p>Para implementar una topología hub and spoke en Azure, se deben crear la red virtual del hub, configurar los spokes y definir las políticas de conectividad y seguridad. Recomiendo usar <strong>Azure Virtual Network Manager</strong> para su creación y gestión.</p>

<figure class="kg-card kg-image-card">
  <img src="https://assets.zyrosite.com/cdn-cgi/image/format=auto,w=1024,h=638,fit=crop/Aq2BgVbxvECDEQ7B/hub-spoke-A0xNZyjKVyfyN50E.png" class="kg-image" alt="Hub and Spoke Architecture" />
</figure>

<h2>Conclusión</h2>
<p>El modelo hub and spoke es una arquitectura poderosa y flexible que puede ayudar indefectiblemente a las organizaciones a gestionar sus recursos sobre Azure de manera más eficiente y, por consecuencia, rápidamente poder gestionar, innovar y crecer.</p>
<p><a href="https://learn.microsoft.com/en-us/azure/architecture/networking/hub-spoke-vwan-architecture">Más info oficial</a></p>
"""
)

# ─────────────────────────────────────────────────────────────────────────────
# POST 13: Design Thinking
# ─────────────────────────────────────────────────────────────────────────────
insert_post(
    title="[Soft] Yo y el Design Thinking (Sí! el burro por delante)",
    slug="soft-yo-y-el-design-thinking-si-el-burro-por-delante",
    tags=["SOFT SKILLS"],
    feature_image="https://assets.zyrosite.com/cdn-cgi/image/format=auto,w=1024,h=436,fit=crop/Aq2BgVbxvECDEQ7B/body-image-why-bankers-think-like-designers-now-1-Yg2lozq8X4IvrQXd.jpg",
    published_at="2024-05-28 00:00:00",
    excerpt="Hermosa y gran metodología de diseño de resolución de problemas que nos ayuda a abordar situaciones complejas mediante un marco de contexto centrado en nosotros, los seres humanos.",
    html="""
<p>Aunque se originó y es mucho más popular en el ámbito del diseño, el Design Thinking se puede aplicar en diversas áreas, como modelos de negocio, marketing, productos y educación — y por qué no, en uno mismo.</p>

<h2>Historia del Design Thinking</h2>
<ul>
  <li>El término "Design Thinking" se remonta a 1987, cuando el profesor Peter G. Rowe publicó el libro "Design Thinking", enfocado en arquitectura y planificación urbana.</li>
  <li>Rolf A. Faste, diseñador, desarrolló este concepto y afirmó que es un método de acción creativa que trasciende una sola disciplina.</li>
  <li>En la Universidad de Stanford, David Kelley (fundador de IDEO) y Terry Winograd contribuyeron al desarrollo del Design Thinking.</li>
  <li>En 2005, los hermanos Kelley fundaron el Instituto de Diseño de Hasso Plattner (HPI) en Stanford, donde se estableció un programa de maestría en Design Thinking.</li>
</ul>

<h2>Enfoque No Lineal</h2>
<p>El Design Thinking no sigue un proceso lineal. Cada etapa proporciona información para que se nutra las siguientes. Tiene cinco etapas:</p>
<ol>
  <li><strong>Empatía:</strong> Entender las necesidades y puntos de vista de los usuarios.</li>
  <li><strong>Definición del problema:</strong> Distinguir el problema principal.</li>
  <li><strong>Ideación:</strong> Producir ideas innovadoras.</li>
  <li><strong>Prototipado:</strong> Desarrollar soluciones concretas.</li>
  <li><strong>Prueba y experimentación:</strong> Testear y perfeccionar las soluciones. Y como en cualquier metodología, iterar el proceso.</li>
</ol>

<figure class="kg-card kg-image-card">
  <img src="https://assets.zyrosite.com/cdn-cgi/image/format=auto,w=1024,h=683,fit=crop/Aq2BgVbxvECDEQ7B/designthinking-A0xN6D8Z27tXw1ZJ.png" class="kg-image" alt="Design Thinking Stages" />
</figure>

<h2>Ventajas</h2>
<ul>
  <li>Fomenta la innovación.</li>
  <li>Se centra en las necesidades del usuario.</li>
  <li>Promueve la colaboración multidisciplinaria.</li>
  <li>Proporciona un enfoque iterativo para resolver problemas.</li>
</ul>

<h2>Desventajas</h2>
<ul>
  <li>Requiere tiempo y recursos.</li>
  <li>Posibilidad de sesgos en la empatía (que parece sencilla, pero es desafiante realmente).</li>
  <li>Dificultad para medir el éxito de las soluciones generadas.</li>
</ul>

<h2>Ejemplos aplicados en importantes empresas</h2>
<p><strong>Tecnológicas:</strong></p>
<ul>
  <li><strong>Philips:</strong> Utilizó Design Thinking para mejorar la experiencia del paciente en escáneres médicos, reduciendo la ansiedad y la necesidad de sedantes.</li>
  <li><strong>Rotterdam Eye Hospital:</strong> Transformó su entorno hospitalario aplicando principios de diseño.</li>
</ul>
<p><strong>Salud:</strong></p>
<ul>
  <li><strong>GE Healthcare:</strong> Mejoró la experiencia de los pacientes pediátricos en procedimientos de diagnóstico.</li>
  <li><strong>Dubai Health Authority:</strong> Facilitó la interacción de los pacientes con el sistema de salud.</li>
</ul>

<h2>Herramientas recomendadas</h2>
<p>Para las distintas etapas del proceso:</p>
<ul>
  <li><strong>Para empatizar:</strong> Mapas de actores, Mood Board, Benchmarking.</li>
  <li><strong>Para definir:</strong> Smaply, Userforge.</li>
  <li><strong>Para idear y colaborar:</strong> SessionLab, Stormboard.</li>
  <li><strong>Para prototipar:</strong> POP, Mockingbird.</li>
  <li><strong>Para validar:</strong> Mapas de calor con Hotjar.</li>
</ul>
<p>Parece complejo, pero verán que hermosa experiencia es transcurrir una necesidad aplicándole esta metodología. Nos vemos! Gracias por leerme!</p>
"""
)

# ─────────────────────────────────────────────────────────────────────────────
# POST 14: Sustentabilidad - Carbon neutral, net-zero
# ─────────────────────────────────────────────────────────────────────────────
insert_post(
    title="[Sustentabilidad] Carbon neutral, net-zero?",
    slug="sustentabilidad-carbon-neutral-net-zero",
    tags=["NATURAL"],
    feature_image="https://assets.zyrosite.com/Aq2BgVbxvECDEQ7B/luke-blog-carbon-neutral-800-a-455px-YleMJvKGGKfZP3bj.gif",
    published_at="2021-06-23 00:00:00",
    excerpt="La sustentabilidad se refiere a la capacidad de algo para sostenerse a lo largo del tiempo sin agotar sus recursos o perjudicar el medio ambiente. Naciones alrededor del mundo aspiran ser emisores netos cero de CO₂ para 2050.",
    html="""
<p>Naciones alrededor del mundo están tomando medidas para enfrentar el cambio climático y aspiran ser emisores netos cero de CO₂ para 2050, un objetivo recientemente adoptado por Estados Unidos. Un estado de cero emisiones netas no implica eliminar completamente las emisiones, sino equilibrar las cantidades emitidas con las removidas de la atmósfera.</p>
<p>El término se ha popularizado en los medios, con países como China apuntando a 2060, mientras que Francia, el Reino Unido y Nueva Zelanda tienen como meta el 2050.</p>

<h2>La Orden Ejecutiva 14057 (EE.UU.)</h2>
<p>La Orden Ejecutiva del presidente Biden sobre la catalización de industrias y empleos de energía limpia describe un camino ambicioso para lograr emisiones netas cero en todas las operaciones federales para 2050. Para ello, el Gobierno Federal hará la transición de su infraestructura a vehículos y edificios de cero emisiones, impulsados por electricidad libre de contaminación de carbono.</p>
<p><a href="https://www.sustainability.gov/">Office of the Federal Chief Sustainability Officer</a></p>

<h2>Diferencias entre los conceptos clave</h2>
<p><strong>Cero emisiones:</strong> Se refiere a un proceso en el que no se libera CO₂ en absoluto. En nuestro actual sistema global de minería y fabricación, ninguna tecnología produce verdaderamente cero emisiones (tienen "emisiones incorporadas"). Sin embargo, la energía eólica y solar no producen emisiones <em>continuas</em> después de su instalación.</p>
<p><strong>Carbono negativo:</strong> Significa eliminar CO₂ de la atmósfera o secuestrar más CO₂ del que se emite. Esto podría incluir un proceso de bioenergía con captura y almacenamiento de carbono.</p>
<p><strong>Bajas emisiones:</strong> Generar gases de efecto invernadero a un ritmo menor que el habitual. Por ejemplo, cambiar de energía de carbón a energía de gas para generar la misma cantidad de electricidad con menos emisiones.</p>
<p><strong>Emisiones netas cero:</strong> No se deben confundir con los conceptos anteriores. Implica equilibrar las emisiones con las remociones.</p>

<h2>Microsoft y la sostenibilidad</h2>
<p>En junio del 2020, Microsoft declaró ser "carbon negative" para el 2030. ¿Podrán? 🤔</p>
"""
)

# ─────────────────────────────────────────────────────────────────────────────
# POST 15: Enfriamiento - Nube cooling friendly
# ─────────────────────────────────────────────────────────────────────────────
insert_post(
    title="[Enfriamiento] Nube cooling friendly?",
    slug="enfriamiento-nube-cooling-friendly",
    tags=["ARQUITECTURA"],
    feature_image="https://assets.zyrosite.com/cdn-cgi/image/format=auto,w=1024,h=436,fit=crop/Aq2BgVbxvECDEQ7B/aires-acondicionados-1280x855-AzGrl8vxvZUXPNKy.jpg",
    published_at="2021-06-21 00:00:00",
    excerpt="Si bien parece sacado de una película de ciencia ficción... Microsoft Azure está liderando el camino hacia un futuro más sostenible con tecnología de enfriamiento por inmersión líquida.",
    html="""
<h2>Innovación Sostenible: El Futuro del Enfriamiento en la Nube</h2>
<p>En la era de la inteligencia artificial (IA), mantener los sistemas de cómputo frescos es más crucial que nunca. Microsoft Azure está liderando el camino hacia un futuro más sostenible con su tecnología de enfriamiento por inmersión líquida, prometiendo revolucionar la eficiencia energética y la potencia de procesamiento en los centros de datos.</p>

<h2>Eficiencia de Carbono y Sostenibilidad</h2>
<p>Microsoft Azure ha logrado ser un 98% más eficiente en carbono, y ahora busca ayudar a otras empresas a alcanzar este hito. La implementación de métodos de enfriamiento innovadores es un paso hacia centros de datos con menor consumo de energía y mayor potencia de procesamiento, sin dejar de lado la eliminación del consumo de agua.</p>

<h2>Enfriamiento de Chips de IA con Inmersión</h2>
<p>Los chips de IA avanzados requieren métodos de enfriamiento más allá de las técnicas convencionales de circulación de aire. La inmersión de estos chips en un fluido dieléctrico de bajo punto de ebullición no solo mejora las latencias y el rendimiento, sino que también ofrece un mejor desempeño general.</p>

<figure class="kg-card kg-image-card">
  <img src="https://assets.zyrosite.com/cdn-cgi/image/format=auto,w=768,h=707,fit=crop/Aq2BgVbxvECDEQ7B/1-mnl3R6Z32aH8O0vD.jpeg" class="kg-image" alt="Enfriamiento por inmersión líquida" />
</figure>

<h2>Puntos clave del enfriamiento líquido</h2>
<ul>
  <li><strong>Chips Más Potentes:</strong> Los microchips más avanzados tienen hasta seis veces más potencia de procesamiento que los chips estándar, manejando cargas de trabajo de IA más sofisticadas.</li>
  <li><strong>Transferencia de Calor Innovadora:</strong> El fluido dieléctrico convierte la energía térmica de los chips en vapor que luego se recaptura en un sistema cerrado para su reutilización.</li>
  <li><strong>Menos Espacio, Mayor Impacto:</strong> Con un enfriamiento adecuado, los microprocesadores pueden configurarse de manera más densa, permitiendo servidores más pequeños.</li>
  <li><strong>Beneficios para el Uso de Energía y Agua:</strong> Se prevé que reduzca el consumo de energía de los servidores en un mínimo del 5 al 15%, minimizando en gran medida el uso general de agua.</li>
  <li><strong>Densidad de enfriamiento:</strong> Permite mayor densidad en comparación con los métodos tradicionales de refrigeración por aire.</li>
  <li><strong>Historia:</strong> Aunque parece una tecnología nueva, la refrigeración líquida ha sido utilizada desde finales del siglo XIX.</li>
</ul>

<figure class="kg-card kg-image-card">
  <img src="https://assets.zyrosite.com/cdn-cgi/image/format=auto,w=768,h=707,fit=crop/Aq2BgVbxvECDEQ7B/2-mnl3R6Z9w8iOonW0.jpeg" class="kg-image" alt="Centro de datos con enfriamiento líquido" />
</figure>

<h2>Conclusión</h2>
<p>Muchas empresas van camino hacia un futuro carbono-negativo. Ojalá se llegue lo antes posible a ser catalogadas como "emisor neto cero", aunque carbono negativo claramente no está mal.</p>
<p>Para más información sobre las iniciativas de sostenibilidad por el lado de Azure: <a href="https://aka.ms/AzureSustainability">aka.ms/AzureSustainability</a></p>
"""
)

# ─────────────────────────────────────────────────────────────────────────────
# POST 16: IoT - ESP8266
# ─────────────────────────────────────────────────────────────────────────────
insert_post(
    title="[IoT] Mi amigo definitivo. Mister ESP8266",
    slug="iot-mi-amigo-definitivo-mister-esp8266-copy-copy",
    tags=["IOT", "ELECTRÓNICA"],
    feature_image="https://assets.zyrosite.com/Aq2BgVbxvECDEQ7B/descarga-mxBreykKQRt3yENE.gif",
    published_at="2021-06-09 00:00:00",
    excerpt="Si no lo conocías, te cuento sobre el excepcional microcontrolador ESP8266 y cómo conectarlo con Microsoft IoT Core y Azure IoT Hub.",
    html="""
<h2>ESP8266 y Microsoft IoT Core 😇</h2>
<p>Si estás en la integración en el mundo actual, tenés que saber que se requiere una combinación de hardware confiable y software robusto. El módulo ESP8266, conocido por su versatilidad y bajo costo, se ha convertido en una elección popular para proyectos de IoT con aplicaciones inteligentes y conectadas.</p>
<p><em>Nota importante:</em> Estas líneas no significan que el SO se tiene que montar sobre un ESP8266 (yo sí lo he montado sobre Raspberry Pi 2), pero me pareció importante tocar estos dos temas juntos.</p>

<h2>Hardware ESP8266</h2>
<p>El ESP8266 es un SoC (System on Chip) que ofrece capacidades de Wi-Fi y una variedad de pines GPIO para conectar sensores y actuadores.</p>

<figure class="kg-card kg-image-card">
  <img src="https://assets.zyrosite.com/cdn-cgi/image/format=auto,w=768,h=707,fit=crop/Aq2BgVbxvECDEQ7B/esp-nodemcu-v1_pinouts_ll-m7VpxW4y58hJR9GO.jpg" class="kg-image" alt="ESP8266 Pinouts" />
</figure>

<h2>Microsoft IoT Core</h2>
<p>Microsoft IoT Core es un sistema operativo optimizado para dispositivos de bajo consumo y rendimiento. Aunque tradicionalmente se ha asociado con dispositivos como Raspberry Pi, existen métodos para implementarlo en un ESP8266.</p>

<h2>Configuración del Entorno de Desarrollo</h2>
<p>Para programar el ESP8266, necesitarás un entorno de desarrollo como Arduino IDE o PlatformIO, y las bibliotecas adecuadas para establecer la comunicación con Microsoft IoT Core. Esto incluye configurar el ESP8266 para conectarse a tu red Wi-Fi y a los servicios de Azure.</p>

<h2>Conexión con Azure IoT Hub</h2>
<p>Azure IoT Hub actúa como un puente entre tus dispositivos IoT y la nube. Configurá tu ESP8266 para enviar y recibir mensajes utilizando protocolos estándar como MQTT, que es compatible con Azure IoT Hub.</p>
<p>En mi tesis del MIT armé un "Hub de salud para Ancianos" que utilizaba estas capacidades de procesamiento en tiempo real para analizar y actuar sobre los datos recopilados.</p>

<h2>Ventajas del Hardware ESP8266</h2>
<ul>
  <li><strong>Bajo Costo:</strong> Su precio accesible lo hace ideal para proyectos a gran escala o para aficionados con presupuesto limitado.</li>
  <li><strong>Conectividad Wi-Fi Integrada:</strong> Facilita la conexión a Internet sin necesidad de módulos adicionales.</li>
  <li><strong>Bajo Consumo Energético:</strong> Perfecto para aplicaciones donde la eficiencia energética es crucial.</li>
  <li><strong>Gran Comunidad de Desarrolladores:</strong> Existe una amplia gama de bibliotecas y ejemplos disponibles.</li>
  <li><strong>Compatibilidad con Diversos Entornos de Desarrollo:</strong> Puede ser programado con herramientas populares como Arduino IDE.</li>
  <li><strong>Flexibilidad:</strong> Adecuado para una variedad de aplicaciones, desde automatización del hogar hasta monitoreo industrial.</li>
</ul>

<h2>Especificaciones técnicas</h2>
<ul>
  <li>CPU de 32 bits (80 MHz o 160 MHz)</li>
  <li>Memoria flash hasta 16 MB</li>
  <li>RAM: 96K Datos y 64K Instrucción</li>
  <li>16 pines GPIO</li>
  <li>Voltaje de funcionamiento: 3V - 3.6V</li>
  <li>WiFi B, G, N con IPv4</li>
  <li>Soporta TCP, UDP, HTTP y FTP</li>
  <li>Comunicación: SPI, I2C y UART</li>
  <li>Consumo: de 10uA a 180mA</li>
</ul>

<p><a href="https://github.com/NVIDIA-AI-IOT/jetbot">Más info en Wiki</a></p>
"""
)

# ─────────────────────────────────────────────────────────────────────────────
# POST 17: Q# - Hola mundo quantico
# ─────────────────────────────────────────────────────────────────────────────
insert_post(
    title="[Q#] Hola mundo quantico?",
    slug="q-hola-mundo-quantico",
    tags=["AZURE", "ELECTRÓNICA"],
    feature_image="https://assets.zyrosite.com/cdn-cgi/image/format=auto,w=1024,h=523,fit=crop/Aq2BgVbxvECDEQ7B/0x0-1-AoPeXqgvrRtjxNRd.jpg",
    published_at="2021-06-04 00:00:00",
    excerpt="¿Sabías que la computación cuántica utiliza principios de la mecánica cuántica para realizar cálculos a velocidades potencialmente mucho mayores que las computadoras clásicas?",
    html="""
<p>Azure Quantum es el servicio de computación cuántica en la nube de Azure. Ofrece una ruta abierta, flexible y preparada para el futuro hacia la computación cuántica, adaptándose a tu forma de trabajar, acelerando el progreso y protegiendo tus inversiones tecnológicas.</p>
<p>Azure Quantum proporciona un entorno de desarrollo óptimo para crear algoritmos cuánticos que funcionen en múltiples plataformas al mismo tiempo. Podés escribir el código una vez y ejecutarlo con pocos o ningún cambio en diferentes objetivos dentro de la misma familia.</p>

<h2>¿Para qué se usa la computación cuántica?</h2>
<p>La computación cuántica se emplea para la resolución de problemas que involucran examinar una gran cantidad de posibilidades para encontrar una solución óptima o eficiente. Son problemas muy complejos que requieren tanta potencia de cálculo que las tecnologías actuales no pueden abordar:</p>
<ul>
  <li>Estudios relacionados con el cambio climático</li>
  <li>Optimización del transporte</li>
  <li>Química molecular</li>
  <li>Finanzas</li>
  <li>Lucha contra el cáncer</li>
</ul>

<h2>Un "Hola mundo" en Q#</h2>
<pre><code class="language-qsharp">/// # Quantum Hello World!
namespace QuantumHelloWorld {
    @EntryPoint()
    operation RandomBit() : Result {
        Message("Hola mundo!");
        use qubit = Qubit();
        H(qubit);
        let result = M(qubit);
        Reset(qubit);
        return result;
    }
}</code></pre>

<p>En criollo: este código Q# es un programa que genera un bit aleatorio. Lo hace creando un qubit, aplicando una transformación de Hadamard para poner el qubit en una superposición de estados |0〉 y |1〉, y luego midiendo el qubit. El resultado de la medición es 'Zero' o 'One' con una probabilidad del 50% para cada uno. Luego, el qubit se reinicia antes de ser liberado.</p>

<h2>Recursos para explorar</h2>
<ul>
  <li><a href="https://quantum.microsoft.com/">Azure Quantum — Quantum coding with Copilot in Azure Quantum</a></li>
  <li><a href="https://vscode.dev/">Visual Studio Code Web</a> — Una alternativa sin instalar nada.</li>
</ul>

<p>De esta manera no tenés que caer en adquirir máquinas virtuales cuánticas, cuyo costo solo se puede ver contactando con un oficial de ventas. ¡Adiós calculadora!</p>
<p>Gracias por pasarte!</p>
"""
)

print("\n🎉 Migración completa! Todos los posts han sido insertados.")
print("⚡ Ahora ejecutá: docker restart ghost-blog")

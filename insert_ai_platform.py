#!/usr/bin/env python3
"""Inserta el post AI Platform"""
import sys
sys.path.insert(0, '/home/javierledesma/docker/ghost-blog')
from insert_post import insert_post

HTML = """
<blockquote>Construí mi propia plataforma de AI orquestada, híbrida (local + cloud), corriendo en un Dell laptop bajo mi escritorio. 13 contenedores Docker, routing inteligente por tiers y observabilidad completa. Esto es lo que aprendí.</blockquote>

<h2>¿Por qué construir tu propia AI Platform?</h2>
<p>Hay algo que no te da ningún SaaS de AI: visibilidad real sobre qué modelo respondió qué, con qué latencia, a qué costo, y por qué tomó esa decisión de routing. Yo quería eso. También quería un entorno donde poder experimentar con Semantic Kernel, probar modelos locales contra cloud, y tener un stack que realmente entendiera de punta a punta.</p>
<p>La AI Platform nació de esa necesidad: un solo cerebro operativo para mis proyectos de Azure, DevOps y automatización técnica. Frontend conversacional, orquestación con Semantic Kernel, routing de modelos por tiers, y observabilidad completa con Langfuse.</p>
<p>Todo corriendo en un Dell laptop dedicado bajo mi escritorio, con acceso externo vía <code>*.t28.io</code>.</p>

<h2>El stack en producción</h2>
<p>13 contenedores Docker sobre Ubuntu 26.04 LTS. Cada capa tiene un rol claro:</p>
<ul>
  <li><strong>Frontend:</strong> Open WebUI v0.8.6 — interfaz de chat accesible en <code>chat.t28.io</code></li>
  <li><strong>Orquestador:</strong> FastAPI + Semantic Kernel v1.41.3 — el cerebro que decide qué modelo usa cada prompt</li>
  <li><strong>Modelos locales:</strong> Ollama con <code>llama3.2</code> (T1) y <code>qwen3:14b</code> (T2)</li>
  <li><strong>Modelo cloud:</strong> NVIDIA NIM / Anthropic (T3) — para prompts complejos que necesitan más capacidad</li>
  <li><strong>Observabilidad:</strong> Langfuse v3 + ClickHouse 24.8 — cada invocación trazada con OTEL</li>
  <li><strong>Infraestructura:</strong> PostgreSQL 15, Valkey 8 (cache/queues), MinIO (object storage)</li>
  <li><strong>Gestión:</strong> Portainer CE, Dozzle (logs live), Netdata (host monitoring)</li>
  <li><strong>Acceso externo:</strong> Cloudflare Tunnel — igual que en el blog, sin puertos expuestos</li>
</ul>
<p>El servidor host es un Dell laptop dedicado con IP estática (<code>192.168.1.34</code>), sin suspend via logind, con autostart via systemd. 14 GB RAM, 98 GB disco, 46 GB usados.</p>

<h2>El Hybrid Router: la parte más interesante</h2>
<p>El componente central de la plataforma es el router híbrido. Cada prompt pasa por dos decisiones antes de llegar a un modelo:</p>

<h3>1. Intent Classifier</h3>
<p>El primer paso es clasificar la intención: ¿es un chat conversacional o necesita ejecutar una skill? Esto lo hace <code>llama3.2</code> corriendo local, con <code>temperature=0</code> para máxima consistencia. Rápido, determinístico, sin costo.</p>

<h3>2. Tier Router</h3>
<p>Si es chat, el router decide qué modelo usar según la longitud del prompt:</p>
<pre><code>≤150 chars → llama3.2   (T1, local, ~instant)
≤500 chars → qwen3:14b  (T2, local, más capaz)
 >500 chars → NVIDIA NIM (T3, cloud, máxima capacidad)</code></pre>
<p>Si es una skill, pasa al SK Planner (<code>qwen3:14b</code>, function calling automático) que elige qué función ejecutar:</p>
<pre><code>"azure"        → bicep_generator
"devops"       → github_reader
"diagram"      → mermaid_gen
"productivity" → email_composer
"research"     → web_search</code></pre>
<p>Toda la lógica de routing está en <code>router.py</code> y todas las rutas quedan trazadas en Langfuse con modelo, tier, intent, latencia y costo por invocación.</p>

<h2>Observabilidad con Langfuse</h2>
<p>Esta fue una de las decisiones más importantes del proyecto. Langfuse v3 con backend en ClickHouse te da algo que no tenés en ninguna interfaz de chat estándar: saber exactamente qué pasó con cada prompt.</p>
<p>Cada invocación registra:</p>
<ul>
  <li>Modelo usado y tier asignado</li>
  <li>Intent clasificado (chat vs skill)</li>
  <li>Latencia de cada paso del pipeline</li>
  <li>Tokens consumidos y costo estimado</li>
  <li>Traces completos via OTEL SDK v4</li>
</ul>
<p>Cuando algo falla o la respuesta no es la esperada, abrís Langfuse y en segundos sabés si fue el classifier, el planner o el modelo. Sin esto, operar un sistema de AI multi-modelo es trabajar a ciegas.</p>

<h2>Acceso externo vía Cloudflare Tunnel</h2>
<p>El mismo patrón que uso en este blog: ningún puerto expuesto directamente a internet. Cloudflare Tunnel enruta el tráfico hacia los servicios internos por nombre de contenedor.</p>
<ul>
  <li><code>chat.t28.io</code> → Open WebUI</li>
  <li><code>langfuse.t28.io</code> → Observabilidad</li>
  <li><code>status.t28.io</code> → Dashboard de estado del stack</li>
</ul>
<p>SSL terminado en el edge de Cloudflare, sin certificados que gestionar localmente. Para un servidor casero, este patrón es imbatible.</p>

<h2>Estado actual y próximos pasos</h2>
<p>Las fases 0, 1 y 2 están completas y en producción: entorno estable, MVP funcional, hybrid router con skills operativas.</p>
<p>Lo que viene en la Fase 3 es lo que más me entusiasma: <strong>MCP Azure read-only</strong>. La idea es que el orquestador pueda consultar el estado real de mis suscripciones Azure — costos, recomendaciones de seguridad, recursos — directamente desde el chat. Un Service Principal con mínimo privilegio, integrado como skills en el registry de Semantic Kernel.</p>
<p>Después: streaming en los endpoints compatibles con OpenAI/Ollama, RAG con Qdrant, y eventualmente un modelo de tenants para aislar proyectos.</p>

<h2>Lo que aprendí construyendo esto</h2>
<p><strong>1. El routing por tiers es más valioso que el mejor modelo.</strong> La mayoría de los prompts conversacionales cortos no necesitan un modelo T3. <code>llama3.2</code> local responde en milisegundos y resuelve el 70% de los casos. Reservar el poder para cuando realmente importa es más inteligente que mandarlo todo a cloud.</p>
<p><strong>2. Sin observabilidad, no tenés plataforma.</strong> Tener un chat con AI sin Langfuse es como tener una app en producción sin logs. Sabés que funciona cuando funciona, pero no tenés idea de por qué falla cuando falla.</p>
<p><strong>3. Semantic Kernel es la pieza correcta para orquestar.</strong> Abstraer los modelos detrás del Kernel y dejar que el Planner decida qué función llamar cambia completamente la forma de pensar los flujos. En lugar de codear lógica de routing manual, describís capabilities y el modelo hace el resto.</p>
<p><strong>4. Un servidor casero como producción funciona, con matices.</strong> Cloudflare Tunnel + systemd autostart + logind sin suspend convierte un laptop viejo en un servidor razonablemente confiable. No es para cargas críticas, pero para experimentación y uso propio es más que suficiente.</p>
<p>El repo está en <a href="https://github.com/javierledesma28/ai-platform">github.com/javierledesma28/ai-platform</a>. El stack sigue evolucionando — cuando la Fase 3 esté lista, escribo el siguiente post.</p>
"""

insert_post(
    title="AI Platform: construí mi propia plataforma de AI orquestada",
    slug="ai-platform-orquestacion-hibrida-local-cloud",
    tags=["IA", "ARQUITECTURA", "LVL300"],
    feature_image="",
    published_at="2026-05-07 12:00:00",
    excerpt="Construí mi propia plataforma de AI orquestada, híbrida (local + cloud), con routing inteligente por tiers, Semantic Kernel, Langfuse y 13 contenedores Docker. Esto es lo que aprendí.",
    html=HTML,
)

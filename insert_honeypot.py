#!/usr/bin/env python3
"""Inserta el post HoneyPot"""
import sys
sys.path.insert(0, '/home/javierledesma/docker/ghost-blog')
from insert_post import insert_post

HTML = """
<blockquote>Desplegué un servidor intencionalmente vulnerable en internet. En menos de 4 horas ya lo habían comprometido. Esto es lo que pasó.</blockquote>

<h2>¿Por qué un HoneyPot?</h2>
<p>La seguridad en papel siempre parece sólida. Firewalls, políticas, segmentación de red. Pero a veces la mejor forma de entender cómo funciona un ataque real es dejarlo pasar. Controladamente, claro.</p>
<p>Un honeypot es exactamente eso: un servidor desplegado intencionalmente para ser atacado. No es un servidor de producción. No tiene datos reales. Pero se ve, se comporta y responde como si los tuviera. Y eso es suficiente para atraer actores reales.</p>
<p>El objetivo era simple: observar qué pasa cuando un servidor Linux con root expuesto queda visible en internet. La respuesta fue más rápida y más compleja de lo que esperaba.</p>

<h2>Arquitectura del sistema</h2>
<p>El honeypot corrió sobre un VPS en Hetzner Cloud (Frankfurt), con hostname <code>db-001-prod</code> — un nombre deliberadamente diseñado para parecer un servidor de base de datos productivo. IP pública sin ningún filtrado, visible para cualquier scanner global.</p>
<p>Tres capas funcionando sobre Docker:</p>

<h3>Capa de engaño</h3>
<ul>
  <li><strong>Cowrie SSH/Telnet</strong> en puerto <code>:22</code> — emula una shell Linux real. Registra cada comando, cada credencial intentada, cada archivo que el atacante intenta descargar.</li>
  <li><strong>Servicios falsos</strong> en puertos de bases de datos: MySQL <code>:3306</code>, PostgreSQL <code>:5432</code>, Redis <code>:6379</code>, MongoDB <code>:27017</code>.</li>
  <li>El SSH real de administración fue movido al puerto <code>:2222</code>.</li>
</ul>

<h3>Capa de observabilidad</h3>
<ul>
  <li>Prometheus + Grafana para métricas en tiempo real.</li>
  <li>Loki + Promtail para logs centralizados.</li>
</ul>

<p>El servidor fue desplegado el <strong>30 de abril de 2026</strong>. El primer compromiso ocurrió esa misma noche.</p>

<h2>El timeline: 48 horas de caos controlado</h2>

<h3>Día 1 — 30 de abril: El backdoor silencioso</h3>
<p>A las <strong>20:03:59 UTC</strong>, menos de 4 horas después del despliegue, el primer actor entró. No con exploits sofisticados. Con la contraseña de root.</p>
<p>Lo que hizo a continuación fue inteligente: no instaló malware. No consumió CPU. No hizo ruido. Instaló <strong>Cloudflare Tunnel</strong> como servicio systemd usando un token de su propia cuenta de Cloudflare.</p>
<pre><code>Account ID: 237f15b5e4fa24ef5465ae87da6986de
Tunnel ID:  7fe175d5-5dce-416b-837d-f129f8703c87</code></pre>
<p>En 33 minutos tenía una puerta trasera permanente, silenciosa, que sobreviviría reinicios y no generaría ninguna alerta obvia. Acceso garantizado desde cualquier lugar del mundo, enrutado a través de la infraestructura de Cloudflare.</p>

<h3>Día 2 — 1 de mayo: Los bots que nunca paran</h3>
<p>Durante todo el día siguiente, una botnet automatizada (<code>SSH-2.0-Go</code>, HASSH <code>16443846...</code>) intentó credenciales a un ritmo exacto de <strong>1 intento por minuto durante ~5 horas 46 minutos</strong>. Aproximadamente 346 intentos totales.</p>
<p>El ritmo no es aleatorio. La mayoría de las configuraciones estándar de fail2ban requieren múltiples intentos en ventanas cortas para activar el bloqueo. Un intento por minuto queda justo por debajo del umbral. Es evasión deliberada.</p>
<p>Contraseñas probadas en Cowrie: <code>root/1qaz@WSX</code>, <code>root/root@123</code>, <code>root/Aa123456</code>. Listas de credential stuffing de uso masivo.</p>

<h3>Día 3 — 2 de mayo: Monetización en 10 segundos</h3>
<p>A las <strong>07:44:45 UTC</strong> ocurrió algo notable. Dos IPs distintas autenticaron con 1 segundo de diferencia:</p>
<ul>
  <li><code>207.180.222.68</code> — Hetzner GmbH, Alemania</li>
  <li><code>130.12.180.51</code> — Lumen Technologies, Estados Unidos</li>
</ul>
<p>Dos geografías, un segundo de separación, mismo objetivo. Coordinación.</p>
<p>Exactamente <strong>10 segundos</strong> después del primer login, el archivo <code>/.g2JIcU5vVJEh2GSpVKkCFrMJb0Q</code> apareció en el sistema. Un cryptominer XMRig/Monero listo para ejecutar. El script de instalación estaba completamente automatizado y preparado de antemano.</p>
<p>A las <strong>15:37:49 UTC</strong>, un cuarto actor entró usando una llave SSH ED25519 pre-instalada. Seis conexiones simultáneas. Supervisión activa.</p>

<h2>Los 4 actores</h2>

<h3>Actor 1 — El Backdoor Silencioso</h3>
<p><strong>IP:</strong> <code>150.228.85.67</code> — Claro Brasil (LACNIC 🇧🇷)</p>
<p>El primero en llegar y el más sofisticado en comportamiento. Su modus operandi: persistencia de largo plazo sin levantar sospechas. Primero probó el puerto 22 (Cowrie) para reconocimiento, luego encontró el SSH real en 2222. Instaló Cloudflare Tunnel como backdoor y se fue. Sin malware, sin ruido, sin rastro obvio.</p>
<p>Lo interesante: operó con al menos dos pares de llaves ED25519 distintas. Una capturada por Cowrie, otra usada en el SSH real.</p>

<h3>Actor 2 — La Botnet</h3>
<p><strong>SSH Client:</strong> <code>SSH-2.0-Go</code> — botnet distribuida</p>
<p>Automatización pura. ~346 intentos de credential stuffing a ritmo de 1/minuto. No tiene objetivo específico — escanea rangos de IP buscando cualquier servidor con contraseñas débiles. Evasión de fail2ban incorporada en el ritmo.</p>

<h3>Actor 3 — Los Cryptominers</h3>
<p><strong>IPs:</strong> <code>207.180.222.68</code> (Hetzner DE) y <code>130.12.180.51</code> (Lumen US)</p>
<p>Orientados completamente a monetización. Drop del malware en 10 segundos, persistencia instalada vía crontab, CPU al 99% en segundos. Operación coordinada con múltiples VPS alquilados para ofuscar origen.</p>

<h3>Actor 4 — El Supervisor</h3>
<p><strong>IP:</strong> <code>188.92.253.158</code> — Telnyx Europe LLC 🇪🇺</p>
<p>Llegó 8 horas después del drop del malware con una llave SSH pre-instalada (alguien tuvo acceso previo para instalarla, probablemente Actor 1 o Actor 3). Seis sesiones simultáneas activas al momento del análisis forense. Estaba conectado cuando empezó el incident response.</p>

<h2>El malware: XMRig/Monero</h2>
<p>El archivo tenía todo lo necesario para pasar desapercibido:</p>
<ul>
  <li><strong>Nombre aleatorio</strong> en el directorio raíz: <code>/.g2JIcU5vVJEh2GSpVKkCFrMJb0Q</code></li>
  <li><strong>Process masquerading</strong> (T1036.005): corría disfrazado como <code>/usr/lib/systemd/systemd</code> (PID 905) y como <code>-bash</code> (PID 4861)</li>
  <li><strong>Persistencia</strong> via <code>@reboot</code> en el crontab de root</li>
</ul>
<p>La señal delatora estaba en <code>/proc/&lt;PID&gt;/status</code>: un VmSize de ~2.4 GB para lo que supuestamente eran systemd y bash. Completamente inconsistente. XMRig en modo RandomX usa hugepages del kernel para maximizar el rendimiento de hashing — ese espacio virtual mapeado no representa RAM física pero sí el espacio reservado para operaciones criptográficas.</p>
<p>Con 6 threads corriendo en el servidor (6-8 vCPUs), el hashrate estimado es de 2.000-4.000 H/s. La ganancia por servidor: ~$0.20-0.50 USD por día. Multiplicado por miles de servidores comprometidos: $200-500 USD/día sin costo de infraestructura propia.</p>
<pre><code>SHA256: 59c29436755b0778e968d49feeae20ed65f5fa5e35f9f7965b8ed93420db91e5
Tipo:   ELF x86-64, Linux (XMRig/Monero RandomX)</code></pre>

<h2>MITRE ATT&amp;CK — Las técnicas usadas</h2>
<ul>
  <li><strong>T1110.001</strong> — Brute Force: Password Guessing (Actor 2)</li>
  <li><strong>T1078.003</strong> — Valid Accounts: Local Accounts (Actors 1, 3, 4)</li>
  <li><strong>T1098.004</strong> — Account Manipulation: SSH Authorized Keys (Actor 4)</li>
  <li><strong>T1505</strong> — Server Software Component (Cloudflare Tunnel backdoor)</li>
  <li><strong>T1053.003</strong> — Scheduled Task/Job: Cron (persistencia del miner)</li>
  <li><strong>T1036.005</strong> — Masquerading: Match Legitimate Name (process masquerading)</li>
  <li><strong>T1496</strong> — Resource Hijacking (cryptomining)</li>
</ul>

<h2>Incident Response</h2>
<p>El 2 de mayo de 2026, a las <strong>17:12 UTC</strong>, el administrador (<code>rescueadmin</code>) conectó por TTY1 — consola física, sin pasar por SSH (que estaba potencialmente comprometido).</p>
<p>En 37 minutos:</p>
<ol>
  <li>Kill de los PIDs maliciosos</li>
  <li>Limpieza del crontab de root</li>
  <li>Remoción de llaves SSH no autorizadas de <code>authorized_keys</code></li>
  <li>Quarantine del binario malicioso (preservado para análisis)</li>
  <li>Generación del forensic export: <code>forensic-collection-20260502_180100.tar.gz</code></li>
</ol>

<h2>Lo que aprendí</h2>
<p><strong>1. La velocidad es brutal.</strong> Menos de 4 horas desde el despliegue hasta el primer compromiso. En internet, un servidor con root expuesto tiene una vida útil muy corta.</p>
<p><strong>2. Los actores tienen roles diferenciados.</strong> No es un solo atacante haciendo todo — hay especialización. El que instala backdoors no es el mismo que instala miners. El supervisor llega cuando el trabajo sucio ya está hecho.</p>
<p><strong>3. La evasión está incorporada por defecto.</strong> El ritmo de 1 intento/minuto de la botnet no es accidental. El process masquerading del miner no es accidental. Estas operaciones están optimizadas para durar.</p>
<p><strong>4. Cloudflare como vector de ataque.</strong> El uso de Cloudflare Tunnel como backdoor es particularmente elegante: el tráfico es HTTPS legítimo saliendo del servidor hacia Cloudflare, lo que hace casi imposible detectarlo por firewalls de egreso simples.</p>
<p><strong>5. El objetivo final es económico.</strong> Todo apunta a monetización. El cryptominer es la forma más directa: convierte CPU robada en Monero. Sin fricción, sin víctima obvia, difícil de rastrear.</p>
<p>El experimento duró 48 horas y generó más datos de los que esperaba. Si querés profundizar en algún aspecto específico — la arquitectura del stack de observabilidad, el análisis forense del malware, o el mapeo completo de MITRE ATT&amp;CK — lo cubrimos en posts siguientes.</p>
"""

insert_post(
    title="HoneyPot: lo que pasa cuando dejás un servidor expuesto en internet",
    slug="honeypot-servidor-expuesto-internet-atacantes-reales",
    tags=["SEGURIDAD", "LVL300"],
    feature_image="",
    published_at="2026-05-07 00:00:00",
    excerpt="Desplegué un servidor intencionalmente vulnerable en internet. En menos de 4 horas lo habían comprometido. 4 actores distintos, un cryptominer, un backdoor via Cloudflare Tunnel y técnicas MITRE ATT&CK reales.",
    html=HTML,
)

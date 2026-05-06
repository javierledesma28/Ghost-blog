#!/usr/bin/env python3
"""
Script de migración: crea un post en Ghost vía Admin API
"""

import jwt
import requests
import datetime
import json
import sys

# Ghost Admin API credentials
GHOST_KEY_ID     = "69fa3aa67c14b200018142dd"
GHOST_KEY_SECRET = "ff02b94bd228e28d5a8437cc84608caefa57c6d0398f22289b98607db02d94af"
GHOST_API_URL    = "http://172.19.0.3:2368/ghost/api/admin"

def get_token():
    import time
    iat = int(time.time())
    payload = {
        "iat": iat,
        "exp": iat + 300,
        "aud": "/admin/"
    }
    token = jwt.encode(
        payload,
        bytes.fromhex(GHOST_KEY_SECRET),
        algorithm="HS256",
        headers={"kid": GHOST_KEY_ID}
    )
    return token

def create_post(title, html, tags, feature_image=None, published_at=None, excerpt=None):
    token = get_token()
    headers = {
        "Authorization": f"Ghost {token}",
        "Content-Type": "application/json"
    }

    post_data = {
        "title": title,
        "html": html,
        "status": "published",
        "tags": [{"name": t} for t in tags],
    }

    if feature_image:
        post_data["feature_image"] = feature_image
    if published_at:
        post_data["published_at"] = published_at
    if excerpt:
        post_data["custom_excerpt"] = excerpt[:300]

    payload = {"posts": [post_data]}
    r = requests.post(f"{GHOST_API_URL}/posts/?source=html", headers=headers, json=payload)

    if r.status_code == 201:
        post = r.json()["posts"][0]
        print(f"✅ Post creado: {post['title']}")
        print(f"   URL: {post['url']}")
        return post
    else:
        print(f"❌ Error {r.status_code}: {r.text[:300]}")
        return None

# ── POST: [IA fuera de Cloud] Mi experiencia con Jetson Nano Parte#1 ──────────

TITLE = "[IA fuera de Cloud] Mi experiencia con Jetson Nano Parte#1.."

EXCERPT = "Qué pasa cuando la inteligencia artificial deja el cloud y empieza a correr directamente en dispositivos? En este artículo comparto mi experiencia con Jetson Nano y cómo conecta con mis inicios en IoT (MIT), donde desarrollé un dispositivo de detección de caídas con Raspberry Pi y Azure IoT Hub."

FEATURE_IMAGE = "https://assets.zyrosite.com/cdn-cgi/image/format=auto,w=1440,h=990,fit=crop/Aq2BgVbxvECDEQ7B/trayectoriajeston-KgTsqqJWMZiQI0X3.png"

TAGS = ["AZURE", "ELECTRÓNICA", "IA", "IOT", "LVL200"]

PUBLISHED_AT = "2026-03-19T00:00:00Z"

HTML = """
<h2>Cuando la IA sale del cloud: mi experiencia con Jetson Nano (y por qué me volvió a conectar con IoT)</h2>

<p>Hace años que trabajo con Azure, arquitecturas cloud y no tan clouds y, más recientemente, con inteligencia artificial (imposible no hacerlo). Es un terreno donde me siento incómodo y claramente eso atrapa: servicios gestionados, escalabilidad, pipelines bien armados, todo bastante ordenado.</p>

<p>Pero hace un tiempo me volvió a picar algo distinto de casi 500 pavos y unos 67TOPS que no se cuanto usaré al menos el 15%.</p>

<p>No tanto cómo escalar IA, sino qué pasa cuando la IA deja el cloud y empieza a correr directamente en un dispositivo físico.</p>

<p>Y eso me llevó a meterme con el curso "Getting Started with AI on Jetson Nano" de NVIDIA.</p>

<p>Lo interesante de este curso no es solo el contenido (clasificación de imágenes, regresión, inferencia, etc.), sino el contexto en el que sucede todo: un dispositivo físico, limitado, que tenés que preparar, conectar y hacer funcionar como en su momento, mi querido Arduino.</p>

<p>Y ahí es donde, casi sin buscarlo, me encontré volviendo varios años atrás.</p>

<figure class="kg-card kg-image-card">
  <img src="https://assets.zyrosite.com/cdn-cgi/image/format=auto,w=1440,h=990,fit=crop/Aq2BgVbxvECDEQ7B/trayectoriajeston-KgTsqqJWMZiQI0X3.png" alt="Trayectoria Jetson Nano" class="kg-image" />
</figure>

<h2>Un déjà vu bastante claro: MIT + IoT + Raspberry</h2>

<p>En su momento hice un programa de IoT en el MIT (Massachusetts), y para poder certificar tuve que desarrollar una tesis bastante particular.</p>

<p>La idea era resolver un problema real: detectar caídas en personas mayores.</p>

<p>El prototipo consistía en un dispositivo que se colocaba debajo de la suela del zapato. A partir de sensores (principalmente giroscopio y movimiento), el sistema analizaba el comportamiento de los abuelos, claramente quise sumar la parte de Azucar en Sangre y se me acabo el tiempo de tesis, sí, correcto, me quedo pendiente.</p>

<p>No se trataba solo de medir movimiento, sino de identificar patrones en vectores y para de contar:</p>

<ul>
  <li>Cambios bruscos de orientación</li>
  <li>Ausencia de movimiento posterior</li>
  <li>Posiciones anómalas mantenidas en el tiempo</li>
</ul>

<p>Cuando el sistema detectaba un comportamiento compatible con una caída, enviaba una alerta a los familiares indicando que el abuelo/a podía haber sufrido un accidente.</p>

<p>Era algo bastante simple a nivel hardware, pero muy interesante desde el punto de vista de lógica y contexto cuando tuve que pelearme con el IDE de Arduino. Claro, ahora es muy fácil poder decirme, hey! usa Visual Studio Code + PlatformIO....no olvidar que estoy hablando del 2018 :)</p>

<h2>Jetson Nano.. WTF!</h2>

<blockquote>"IA corriendo directamente en el dispositivo. Sin cloud, sin excusas"</blockquote>

<h2>Volver a lo físico (pero ahora con IA)</h2>

<p>Trabajar con Jetson Nano fue, en cierto punto, volver a ese lugar, pero con un salto bastante grande. Ya no es solo un dispositivo que junta datos y los manda al cloud para que alguien los procese después. Acá directamente tenés modelos de IA corriendo en el propio dispositivo, tomando decisiones en tiempo real y detectando patrones sin depender de conectividad.</p>

<p>Y eso cambia completamente el enfoque: lo que antes resolvía con lógica programada y algunos thresholds, hoy podría abordarse con un modelo entrenado específicamente para detectar caídas de forma mucho más precisa.</p>

<figure class="kg-card kg-image-card">
  <img src="https://assets.zyrosite.com/cdn-cgi/image/format=auto,w=1440,h=784,fit=crop/Aq2BgVbxvECDEQ7B/infografiajetson-JCuNknZGMHphCbqA.png" alt="Infografía Jetson Nano" class="kg-image" />
</figure>

<h2>Entender la IA más allá del Copilot y Claudio ;)</h2>

<p>Algo que también me ayudó mucho en este proceso fue dejar de ver la IA solo como usuario y empezar a entender qué pasa realmente por detrás. En ese camino me sirvió bastante todo el recorrido de e-learning que hice con Anthropic, porque me dio contexto para dimensionar mejor cómo funcionan estos sistemas en serio.</p>

<p>Ahí trabajé desde cómo interactuar correctamente con modelos, hasta cómo integrarlos vía API en flujos reales y conectarlos con otros sistemas. Y eso fue un antes y un después. Porque muchas veces arrancamos usando copilots o herramientas ya armadas —que está perfecto, de hecho también fue mi punto de entrada—, pero cuando empezás a profundizar un poco más, dejás de simplemente usar IA y empezás a diseñar soluciones con IA.</p>

<h2>Azure no se fué, sigue estando…</h2>

<p>Esto no reemplaza nada de lo que ya venía haciendo con Azure, al contrario, lo complementa bastante bien. Hoy lo veo mucho más claro: el cloud sigue siendo clave para entrenar modelos, gobernar y escalar, mientras que los dispositivos —como Jetson o incluso una Raspberry— se encargan de ejecutar y tomar decisiones en tiempo real.</p>

<p>En su momento, cuando trabajaba con Raspberry y Azure IoT Hub (sí, ese viejo conocido que ya todos sabemos que actualmente es parte del recuerdo 😅), el enfoque era bastante claro: enviar telemetría, procesarla en el cloud y desde ahí disparar acciones. Pero ahora el paradigma cambia un poco: primero procesás y tomás decisiones directamente en el dispositivo, y después le mandás al cloud solo lo que realmente aporta valor.</p>

<figure class="kg-card kg-image-card">
  <img src="https://assets.zyrosite.com/cdn-cgi/image/format=auto,w=1024,h=701,fit=crop/Aq2BgVbxvECDEQ7B/sdk-KNBlXnBl18jUhT5c.png" alt="NVIDIA SDK Manager" class="kg-image" />
</figure>

<h2>La parte que nadie te cuenta (pero es la mejor)</h2>

<p>También hay algo que me parece importante decir, que claramente con los tiempos que corren, sumarle la palabra IA a cualquier cosa, suena cool (öjo! a mi tambien me gusta hacerlo, jejejej). Así y todo aquí realmente hay bastante de:</p>

<ul>
  <li>Pelear con una microSD</li>
  <li>Flashear imágenes (al momento de este blog, usé la version 2.4.0.13236 del NVIDIA_SDK_Manager)</li>
  <li>Probar cables que no funcionan</li>
  <li>Entender por qué algo no levanta</li>
</ul>

<p>Y sinceramente… está buenísimo. Mi mujer se enfoca con la Kindle, porque yo no con mi hardware???</p>

<p>Porque me obliga a salir del confort del portal de Azure y volver a entender cómo funcionan las cosas por debajo frustrandome una y otra vez.... demostrandome, que hay algo más allá.</p>

<p>Nunca me olvidare mis primeras líneas en C++, pido disculpas a los desarrolladores de verdad, sabrán entenderme! A los DEVs de verdad, les dejo mas info acá: <a href="https://github.com/NVIDIA-AI-IOT/jetbot">github.com/NVIDIA-AI-IOT/jetbot</a></p>

<h2>Lo que estoy buscando ahora</h2>

<p>Hace tiempo que vengo explorando este camino, primero con IoT, después con cloud, y ahora con IA corriendo directamente en dispositivos.</p>

<p>Este curso es parte de ese recorrido, y mi idea es llevarlo un poco más allá: Certifiqué (el mismo día que saque este blog :) ), profundizar y empezar a aplicarlo en escenarios reales de manera "doméstica". Donde lo de doméstico ni yo me lo creo realmente, pero me gusta!</p>

<p>Especialmente donde el contexto es físico, el tiempo real y la autonomía del dispositivo hacen la diferencia y muy lejos de unas "Managed rule" en un WAF por ejemplo.</p>

<pre><code class="language-cpp">void setup() {
  pinMode(13, OUTPUT); // Configura el pin 13 como salida
}

void loop() {
  digitalWrite(13, HIGH); // Enciende el LED
  delay(1000);            // Espera 1 segundo
  digitalWrite(13, LOW);  // Apaga el LED
  delay(1000);            // Espera 1 segundo
}</code></pre>

<h2>Cierre a modo conclusión...</h2>

<p>Si algo me dejó toda esta experiencia es una sensación bastante clara: volver a trabajar con dispositivos, después de tanto tiempo en cloud, no es retroceder, es sumar una pieza que faltaba. Porque cuando las cosas pasan en el mundo físico, toman otro sentido, se vuelven más reales. No es lo mismo ver datos en una pantalla que tener un dispositivo funcionando, reaccionando y tomando decisiones ahí mismo. Y eso te cambia la perspectiva.</p>

<p>Al final, la IA no vive solo en el cloud… también vive donde realmente pasan las cosas.</p>

<p>Gracias! gracias de verdad por pasarse, un gusto como siempre compartir!</p>

<p><em>Woww! No se tomen en serio que esta es la parte #1, esto de no escribir nada hace un tiempo largo, que emoción, espero la pueda disimular :) !</em></p>
"""

if __name__ == "__main__":
    print("🚀 Creando post en Ghost...")
    create_post(
        title=TITLE,
        html=HTML,
        tags=TAGS,
        feature_image=FEATURE_IMAGE,
        published_at=PUBLISHED_AT,
        excerpt=EXCERPT
    )

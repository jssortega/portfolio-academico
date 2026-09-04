# Práctica 1: Introducción a SPADE con PyCharm

## Sistemas Multiagente — [Grado en Ingeniería Informática](https://eps.ujaen.es/grados/grado-en-ingenieria-informatica)

**[Universidad de Jaén](https://www.ujaen.es/)** · [Departamento de Informática](https://www.ujaen.es/departamentos/dinformatica/)
[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)
---

A continuación explicaré como realizar la ejecución de cada una de las mejoras y una breve descripción de lo que he implementado.

Para una descripción completa del análisis y diseño de cada una de las mejoras se encuentra en la rama de este proyecto de analisis-diseno.

## Mejora 1 — Respuesta del receptor

### Ejecución

Para la ejecución de esta mejora tendrá que seguir los siguientes pasos cada uno en una terminal distinta:
1. Arranca el servidor XMPP: spade run
2. En otro terminal: python .\mejora1\main_mejora1.py

El resultado debe ser el siguiente:

```
[RECEPTOR] Agente receptor@localhost iniciado
[RECEPTOR] Web: http://localhost:10002/spade
[EMISOR] Agente emisor@localhost iniciado
[EMISOR] Web: http://localhost:10001/spade
Sistema activo. Presiona Ctrl+C para detener.
[EMISOR] Enviado: Mensaje #1
[RECEPTOR] Recibido de emisor@localhost:
           Contenido: Mensaje #1
           Performativa: inform
[RECEPTOR] Enviado: Confirmación Mensaje #1
[EMISOR] Mensaje #1 confirmado por: receptor@localhost:
           Performativa: confirm
[EMISOR] Enviado: Mensaje #2
[RECEPTOR] Recibido de emisor@localhost:
           Contenido: Mensaje #2
           Performativa: inform
[RECEPTOR] Enviado: Confirmación Mensaje #2
[EMISOR] Mensaje #2 confirmado por: receptor@localhost:
           Performativa: confirm
[EMISOR] Enviado: Mensaje #3
[RECEPTOR] Recibido de emisor@localhost:
           Contenido: Mensaje #3
           Performativa: inform
[RECEPTOR] Enviado: Confirmación Mensaje #3
[EMISOR] Mensaje #3 confirmado por: receptor@localhost:
           Performativa: confirm
```

### Breve descripción de la mejora

He tenido que modificar ambos agentes emisor y receptor.

En el agente emisor he añadido el comportamiento `RecibirConfirmacionBehaviour()` que es de tipo `CyclicBehaviour` lo cual hace que esté continuamente en escucha para recibir los mensajes de confirmación del agente receptor.

En el agente receptor, en el comportamiento que tenía para recibir mensaejes, lo he modificado a `RecibirMensajeYConfirmarBehaviour(CyclicBehaviour)` de tal forma que cuando recibe un mensaje crea un nuevo mensaje con performativa `confirm` y se lo envía al agente emisor, confirmándole así que ha recibido el mensaje.

## Mejora 2 — Mensajes con timestamp

### Ejecución

Para la ejecución de esta mejora tendrá que seguir los siguientes pasos cada uno en una terminal distinta:
1. Arranca el servidor XMPP: spade run
2. En otro terminal: python .\mejora2\main_mejora2.py

El resultado debe ser el siguiente, mostrando la fecha y hora en la que el emisor envió los mensajes:

```
[EMISOR] Enviado: Mensaje #1
[RECEPTOR] Recibido de emisor@localhost:
           Contenido: Mensaje #1
           Performativa: inform
           Fecha y hora: 28/02/2026 16:00:39
[RECEPTOR] Enviado: Confirmación Mensaje #1
[EMISOR] Mensaje #1 confirmado por: receptor@localhost:
           Performativa: confirm
```

### Breve descripción de la mejora

Para esta mejora he mantenido lo que implementé en la `Mejora 1`, en la que el receptor envía al emisor una confirmación de los mensajes.

En el emisor utilizando la librería `datetime` añado al mensaje un metadata de tipo `timestamp` el cual contiene la fecha y hora actual utilizando el método `now()` y espicificando el formato, que en mi caso es `%d/%m/%Y %H:%M:%S`.

En el agente receptor simplemente muestro por terminal la fecha y hora que contiene el mensaje.

## Mejora 3 — Contador de mensajes con parada automática

### Ejecución

Para la ejecución de esta mejora tendrá que seguir los siguientes pasos cada uno en una terminal distinta:
1. Arranca el servidor XMPP: spade run
2. En otro terminal: python .\mejora3\main_mejora3.py

El resultado debe ser el siguiente, en este caso había establecido el umbral de parada en 5 mensajes, por lo que tras recibir el receptor ese último mensaje comienza la parada y la salida se ve de la siguiente forma:

```
[EMISOR] Enviado: Mensaje #5
[RECEPTOR] Recibido de emisor@localhost:
           Contenido: Mensaje #5
           Performativa: inform
           Fecha y hora: 02/03/2026 10:47:07
[RECEPTOR] Enviado: Confirmación Mensaje #5
[RECEPTOR] Umbral de mensajes alcanzado (5). Enviando mensaje cancel...
[EMISOR] Mensaje #5 confirmado por: receptor@localhost:
           Performativa: confirm
[EMISOR] Recibido mensaje de cancelación. Deteniendo agente emisor...
```

De esta forma vemos que el agente receptor tras recibir el mensaje 5 envía la confirmación y envía el mensaje de cancelación seguido en ese orden, por lo que el mensaje emisor los recibe también en ese orden.

### Breve descripción de la mejora

Para esta mejora parto de lo ya implementado en la `Mejora 1` y `Mejora 2`.

Simplemente, creo una variable en el agente receptor, `mensajes_maximos`, donde defino como máximo 5 mensajes. Cada vez que recibe un mensaje comprueba si ya ha superado ese umbral, en caso de que lo haya hecho crea un nuevo mensaje con performativa de tipo `cancel` y se lo envía al emisor.

Una vez lo recibe el emisor, siguiendo la lógica de la `Mejora 1` el emisor crea un mensaje con performativa `confirm_cancel` y se lo envía de vuelta al agente receptor, tras esto se detiene el emisor y cuando el receptor recibe este último mensaje también se detiene.

## Mejora 4 — Tercer agente intermediario (Logger)

### Ejecución

Para la ejecución de esta mejora tendrá que seguir los siguientes pasos cada uno en una terminal distinta:
1. Arranca el servidor XMPP: spade run
2. En otro terminal: python .\mejora4\main_mejora4.py

El resultado en el archivo log.txt tiene que ser de la siguiente manera:
```
03/03/2026 12:40:11 | emisor@localhost -> receptor@localhost | inform | Mensaje #1
03/03/2026 12:40:11 | receptor@localhost -> emisor@localhost | confirm | Mensaje #1
03/03/2026 12:40:14 | emisor@localhost -> receptor@localhost | inform | Mensaje #2
03/03/2026 12:40:14 | receptor@localhost -> emisor@localhost | confirm | Mensaje #2
03/03/2026 12:40:17 | emisor@localhost -> receptor@localhost | inform | Mensaje #3
03/03/2026 12:40:17 | receptor@localhost -> emisor@localhost | confirm | Mensaje #3
03/03/2026 12:40:20 | emisor@localhost -> receptor@localhost | inform | Mensaje #4
03/03/2026 12:40:20 | receptor@localhost -> emisor@localhost | confirm | Mensaje #4
03/03/2026 12:40:23 | emisor@localhost -> receptor@localhost | inform | Mensaje #5
03/03/2026 12:40:23 | receptor@localhost -> emisor@localhost | confirm | Mensaje #5
03/03/2026 12:40:23 | receptor@localhost -> emisor@localhost | cancel | Limite de mensajes alcanzado
03/03/2026 12:40:23 | emisor@localhost -> receptor@localhost | confirm_cancel | Limite de mensajes alcanzado
```

### Breve descripción de la mejora

Para esta mejora, en primer lugar he hecho que tanto el `agente emisor` como el `agente receptor` cada vez que se envíen un mensaje entre ellos envíen antes una copia del mensaje al `agente logger`.

He creado al logger que con un comportamiento de tipo `CyclicBehaviour` se mantiene a la escucha para recibir mensajes de los otros agentes. Cuando recibe esos mensajes los copia en un archivo `log.txt` con el formato mostrado anteriormente.

## Mejora 5 — Protocolo pregunta-respuesta 

### Ejecución

Para la ejecución de esta mejora tendrá que seguir los siguientes pasos cada uno en una terminal distinta:
1. Arranca el servidor XMPP: spade run
2. En otro terminal: python .\mejora5\main_mejora5.py

El resultado en terminal con el siguiente diccionario (`diccionario.txt`):
```
capital_espana:Madrid
lenguaje_spade:Python
deporte_mas_popular:Futbol
```

Y el siguiente banco de preguntas en el agente emisor:
```
self.preguntas = [
            "capital_espana",
            "lenguaje_spade",
            "autor_quijote",
            "deporte_mas_popular"
        ]
```

Debe ser el siguiente:
```
[RECEPTOR] Agente receptor@localhost iniciado
[RECEPTOR] Web: http://localhost:10002/spade
[EMISOR] Agente emisor@localhost iniciado
[EMISOR] Web: http://localhost:10001/spade
Sistema activo. Presiona Ctrl+C para detener.
[EMISOR] Enviado: capital_espana
[RECEPTOR] Recibido de emisor@localhost:
           Pregunta: capital_espana
           Respuesta: Madrid
[EMISOR] Respuesta recibida de: receptor@localhost:
           Performativa: inform
           Mensaje: Madrid
[EMISOR] Enviado: lenguaje_spade
[RECEPTOR] Recibido de emisor@localhost:
           Pregunta: lenguaje_spade
           Respuesta: Python
[EMISOR] Respuesta recibida de: receptor@localhost:
           Performativa: inform
           Mensaje: Python
[EMISOR] Enviado: autor_quijote
[RECEPTOR] Recibido de emisor@localhost:
           Pregunta: autor_quijote
           Respuesta: Clave no encontrada
[EMISOR] Respuesta recibida de: receptor@localhost:
           Performativa: failure
           Mensaje: Clave no encontrada
[EMISOR] Enviado: deporte_mas_popular
[RECEPTOR] Recibido de emisor@localhost:
           Pregunta: deporte_mas_popular
           Respuesta: Futbol
[EMISOR] Respuesta recibida de: receptor@localhost:
           Performativa: inform
           Mensaje: Futbol
[EMISOR] Máximo de preguntas enviado
[RECEPTOR] Mensaje de parada recibido.
```

### Breve descripción de la mejora

Para esta mejora al cambiar el objetivo bastante respecto a las anteriores he partido de 0 con los agentes emisor y receptor.

Para el agente emisor he creado una lista con las preguntas a realizar al receptor, por lo que en el comportamiento `EnviarMensajeBehaviour` que envía las preguntas hace lo siguiente:
1. Comprobar que le siguen quedando preguntas en `self.preguntas`. En caso de que no le envía un mensaje al receptor para que se detenga y se detiene también el mismo.
2. Envíar pregunta tras pregunta al receptor.

En el comportamiento `RecibirRespuestaBehaviour` simplemente recibe la respuesta del emisor y la muestra por terminal.

Para el agente receptor, lo que hace en el comportamiento `PreguntaRespuestaBehaviour` recibe las preguntas del emisor, consulta la respuesta en el diccionario y se la envía de vuelta.

También tiene un comportamiento `RecibirParadaBehaviour` que solo recibe mensajes con performativa `cancel` para detenerse cuando el emisor no tiene más preguntas.

# Verificación del servidor XMPP con STARTTLS

**Audiencia:** alumnos del Nivel 2 — Sistemas Multiagente
**Asignatura:** Sistemas Multiagente — Universidad de Jaén
**Curso:** 2025-2026

---

## 1. Resumen del cambio

A partir de esta versión del proyecto, el contenedor Docker de
**Prosody ofrece STARTTLS** con un certificado autofirmado
(*self-signed*) generado en el primer arranque. Antes el servidor
escuchaba en TCP plano y la compatibilidad con `slixmpp ≥ 1.12`
(cliente XMPP que usa SPADE) se conseguía mediante un parche en
`utils.py` que activaba `unencrypted_plain` y `unencrypted_scram`.

**Por qué ha cambiado.** La solución correcta a "slixmpp rechaza SASL
sobre TCP plano" es ofrecer cifrado en el servidor, no parchear el
cliente. Mover la solución al servidor:

- Hace que **cualquier cliente XMPP estándar** (slixmpp, profanity,
  Gajim, conversations…) pueda conectarse sin trucos.
- **Elimina el parche de `utils.py`** y reduce la cantidad de código
  inicial que un alumno debe entender.
- Es **igual de seguro** (el certificado es local y la red sigue sin
  cifrado obligatorio): `c2s_require_encryption` continúa en `false`.
- Es **idéntica al patrón** del proyecto `TicTacToe` de la asignatura.

> En resumen: el contenedor hace lo correcto, los agentes hablan en
> claro o en STARTTLS según prefieran y nada en el código Python
> tiene que enterarse.

---

## 2. Cómo verificar que todo funciona

### 2.1. Comprobación rápida (1 minuto)

```bash
# Reconstruir el contenedor con la nueva configuración
docker compose down
docker compose up -d

# Esperar 2-3 segundos a que Prosody arranque
sleep 3

# Ver el registro (*log*) del punto de entrada (*entrypoint*):
# la primera vez genera el certificado.
docker compose logs prosody | head -30
```

Debes ver algo como:

```
prosody-ssmmaa | [entrypoint] Generando certificado self-signed para localhost...
prosody-ssmmaa | ........+......+...+...+....+...+
prosody-ssmmaa | -----
prosody-ssmmaa | Prosody 0.11.x
prosody-ssmmaa | Started on listener: tcp ports 5222 5269
```

A partir del segundo arranque la primera línea no aparece (el
certificado ya existe en el volumen `ssmmaa-prosody-data`).

### 2.2. Comprobación profunda (con el guion)

```bash
python verificar_conexion.py xmpp
```

El guion de verificación incluye un caso de uso que registra una
cuenta nueva, autentica con SCRAM-SHA-1 y crea una sala MUC.
Si TLS funciona, los tres pasos pasan en verde.

### 2.3. Comprobación manual con `openssl`

```bash
openssl s_client -connect localhost:5222 -starttls xmpp -quiet </dev/null \
  | head -20
```

Debes ver el saludo (en inglés *handshake*) TLS: cabeceras
`CONNECTED`, certificado autofirmado (*self-signed*) con
`subject=CN=localhost`, `Verification: self-signed certificate`.
Si recibes `connection refused` o `no STARTTLS`, revisa los pasos
de la sección 3.

### 2.4. Comprobación del certificado

```bash
docker compose exec prosody \
  openssl x509 -in /etc/prosody/certs/localhost.crt -text -noout \
  | head -15
```

Debes ver `Issuer: CN=localhost`, `Subject: CN=localhost` y una
validez de 10 años.

---

## 3. Diagnóstico de fallos

| Síntoma | Causa probable | Solución |
|---|---|---|
| `not-authorized` al arrancar un agente | El parche de `utils.py` se retiró pero el contenedor **antiguo** (sin TLS) sigue en ejecución. | `docker compose down -v && docker compose up -d` para regenerar el certificado y reiniciar Prosody con la nueva configuración. |
| `Connection refused` en `localhost:5222` | El contenedor no arranca. Mirar `docker compose logs prosody`: si Prosody se daemoniza, el contenedor entra en bucle. | Verificar que `daemonize = false` está en `xmpp/prosody.cfg.lua` (línea 24). |
| `SSL: WRONG_VERSION_NUMBER` | El cliente espera TLS desde el primer byte (`xmpps://`) en lugar de STARTTLS. | SPADE usa STARTTLS por defecto en el puerto 5222; no cambies a 5223. |
| Prosody arranca pero falla `openssl s_client … -starttls xmpp` | El módulo `tls` no está cargado. | Verificar que `"tls"` está en `modules_enabled` de `prosody.cfg.lua`. |
| Cada `docker compose up` regenera el certificado | El volumen `ssmmaa-prosody-data` se ha borrado. | Es inocuo; el certificado nuevo es válido durante 10 años. Solo te molestará si reinicias muchas veces seguidas. |

---

## 4. Migración desde versiones anteriores del proyecto

Si tu copia local viene de una versión anterior del proyecto que ya
había arrancado el contenedor (con el parche en `utils.py`), debes:

```bash
# 1. Detener y borrar el contenedor antiguo y su volumen.
#    El volumen contenía estado XMPP del Prosody sin TLS,
#    y mezclar dos versiones puede dar errores raros.
docker compose down -v

# 2. Volver a arrancar con la configuración nueva.
docker compose up -d

# 3. Verificar que el log muestra la generación del certificado.
docker compose logs prosody | grep -i "certificado\|starttls\|tcp"

# 4. (Opcional) Borrar las credenciales locales antiguas si tus
#    agentes habían registrado cuentas sobre el Prosody anterior.
#    No es estrictamente necesario porque el registro automático
#    las recreará al primer login.
```

Si tienes scripts propios que aplican parches a `slixmpp` o
modifican `feature_mechanisms`, puedes eliminarlos: ya no aportan
nada con el contenedor TLS y solo añaden ruido a `utils.py`.

---

## 5. Detalles técnicos para curiosos

### 5.1. Por qué slixmpp ≥ 1.12 rechaza SASL en TCP plano

Es una decisión de seguridad: PLAIN expone la contraseña en claro
y SCRAM-SHA-1 también es vulnerable a un ataque de degradación
(en inglés *downgrade*) si no hay canal cifrado. La RFC 4422
recomienda no permitirlos sin TLS y los clientes modernos lo
aplican por defecto.

### 5.2. Cómo se valida el certificado self-signed

slixmpp permite STARTTLS sin verificar la cadena cuando el cliente
declara `verify_security=false`. SPADE pasa este parámetro al
construir el agente; en el proyecto se lee de
`config.yaml → perfiles_xmpp.local.verificar_seguridad: false`.
Para producción habría que poner un certificado de Let's Encrypt
y `verify_security=true`.

### 5.3. Persistencia del certificado entre reinicios

El volumen `ssmmaa-prosody-data` (montado en `/var/lib/prosody`)
**no** persiste `/etc/prosody/certs`. Por eso el punto de entrada
(*entrypoint*) comprueba si el certificado ya existe y solo lo
genera cuando falta. Como `/etc/prosody/certs` está dentro de la
imagen —no en un volumen—, al borrar el contenedor con
`docker compose down` (sin `-v`) el certificado **se mantiene**;
con `-v` se pierde y se regenera en el siguiente arranque.

### 5.4. Supervisor único en las salas MUC

`prosody.cfg.lua` declara
`muc_room_default_admins = { "profesor_emergencias@localhost" }`
en el componente MUC. Esto significa que **solo** el JID
`profesor_emergencias@localhost` recibe afiliación `admin` al
unirse a una sala recién creada. La afiliación es persistente y la
asigna Prosody, no el cliente, así que un agente del grupo no
puede obtenerla parcheando código Python.

Cómo verificarlo (el supervisor del profesor —`profesor_main.py`—
vive en la rama `agente-profesor-emergencias`; este experimento
asume que el profesor lo ha arrancado contra el mismo Prosody):

```bash
# Conectar un agente con el JID del supervisor falsificado
python -c "
import asyncio
from spade.agent import Agent
class Falso(Agent):
    pass
async def main():
    a = Falso('profesor_emergencias_fake@localhost', 'x', port=5222,
              verify_security=False)
    await a.start(auto_register=True)
    # ... el falso entra en una sala MUC con su JID, NO recibe admin
asyncio.run(main())
"
```

El agente del grupo puede unirse a la sala, pero su rol será
`participant` (o `member`), no `admin`. Cuando los grupos
implementen su Centralita, podrán comprobar la afiliación del
supervisor con `presence.get_role()` para confiar en quién está
realmente al otro lado del protocolo FIPA-Request.

### 5.5. Diferencias frente al servidor del laboratorio

`sinbad2.ujaen.es` (perfil `servidor` del `config.yaml`) ya tiene
TLS de verdad con certificado válido. El cambio del contenedor
local solo afecta al desarrollo en la máquina del alumno: el
laboratorio sigue funcionando igual.

---

## 6. Lista de comprobación final (*checklist*)

- [ ] `docker compose down -v && docker compose up -d` no devuelve errores.
- [ ] `docker compose logs prosody` muestra "Generando certificado…" la primera vez y "Started on listener: tcp ports 5222 5269" siempre.
- [ ] `nc -zv localhost 5222` devuelve "Connection succeeded".
- [ ] `openssl s_client -connect localhost:5222 -starttls xmpp` devuelve un certificado autofirmado (*self-signed*) con `CN=localhost`.
- [ ] `python verificar_conexion.py xmpp` pasa todas las comprobaciones.
- [ ] `grep -c parche_xmpp utils.py` devuelve `0` (el parche obsoleto se ha retirado).
- [ ] `python main.py` arranca el sistema sin errores de autenticación.
- [ ] `grep muc_room_default_admins xmpp/prosody.cfg.lua` muestra el JID `profesor_emergencias@localhost` como único administrador.

Cuando los siete puntos pasen, el contenedor está listo y puedes
seguir con el desarrollo de los agentes.

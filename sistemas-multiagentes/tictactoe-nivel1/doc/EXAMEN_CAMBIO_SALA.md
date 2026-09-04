# Cambio en `config/config.yaml` para el día del examen

El servidor `sinbad2.ujaen.es` aloja la sala del examen en un
componente MUC dedicado (`examen.sinbad2.ujaen.es`), distinto del
componente general usado en laboratorio y torneo. Esto garantiza
que **solo el supervisor del profesor pueda crear la sala** y, por
tanto, que ningún agente alumno empiece a jugar antes de que el
supervisor esté monitorizando.

Para que tu agente se una a la sala correcta el día del examen
tienes que ajustar dos campos del perfil `servidor` en
`config/config.yaml`. **No hay cambios en código.**

## Cambio (solo el día del examen)

```diff
 xmpp:
   perfil_activo: servidor

   perfiles:
     servidor:
       host: sinbad2.ujaen.es
       puerto: 8022
       dominio: sinbad2.ujaen.es
-      servicio_muc: conference.sinbad2.ujaen.es
+      servicio_muc: examen.sinbad2.ujaen.es
-      sala_tictactoe: tictactoe
+      sala_tictactoe: examen
       password_defecto: secret
       auto_register: true
       verify_security: false
```

Asegúrate también de que `perfil_activo: servidor`.

## Cuándo aplicarlo y cuándo revertirlo

| Momento                                | `servicio_muc`                  | `sala_tictactoe` |
|----------------------------------------|---------------------------------|------------------|
| Antes y después del examen (operación normal) | `conference.sinbad2.ujaen.es`   | `tictactoe`      |
| Durante el examen oficial              | `examen.sinbad2.ujaen.es`       | `examen`         |

Después del examen, **revierte los dos campos** para que tus pruebas
de torneo y laboratorio sigan funcionando como hasta ahora.

## Notas

- El **Prosody local del repositorio de infraestructura**
  (`perfil_activo: local`,
  <https://gitlab.com/ssmmaa/infraestructurassmmaa/ssmmaa-infraestructura>)
  **no se ve afectado por esta instrucción**: solo aplica al perfil
  `servidor`. Para tus pruebas locales sigues usando
  `conference.localhost` / `tictactoe` como siempre.
- Si no haces este cambio el día del examen, tu agente intentará
  unirse a `tictactoe@conference.sinbad2.ujaen.es` (sala genérica
  del torneo), mientras que el supervisor del profesor monitoriza
  `examen@examen.sinbad2.ujaen.es`. Estaríais en salas distintas y
  **tus partidas no se contabilizarían en la base de datos del
  examen**.
- Si intentas crear `examen@conference.sinbad2.ujaen.es` con la
  configuración antigua, Prosody no la encuentra (la sala del
  examen vive en otro componente). Si intentas crear
  `examen@examen.sinbad2.ujaen.es` antes que el supervisor, el
  servidor te devolverá un error `forbidden` con un mensaje en
  español explicando que debes esperar al supervisor (este es el
  comportamiento esperado y deseado por el profesor).

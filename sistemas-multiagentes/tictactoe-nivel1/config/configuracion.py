"""Módulo de carga de configuración del sistema Tic-Tac-Toe Multiagente.

Lee los ficheros config.yaml y agents.yaml, resuelve el perfil activo
y devuelve diccionarios con los parámetros listos para usar tanto por
el lanzador (main.py) como por los fixtures de pruebas (conftest.py).

Para el perfil LLM activo se preparan automáticamente las variables
de entorno que LiteLLM/ADK necesitan según el ``proveedor`` declarado
en ``config.yaml``:

* ``ollama``: se fija ``OLLAMA_API_BASE`` con la ``url_base`` del
  perfil para que LiteLLM enrute las peticiones al servidor Ollama
  correcto.
* ``gemini``: se comprueba que la variable indicada en
  ``api_key_env`` (por defecto ``GOOGLE_API_KEY``) está definida en
  el entorno; si no, se lanza un error didáctico que indica cómo
  obtener la clave gratuita.

Ejemplo de uso:
    from config.configuracion import cargar_configuracion, cargar_agentes

    config = cargar_configuracion()
    perfil_xmpp = config["xmpp"]
    perfil_llm = config["llm"]

    plantillas = cargar_plantillas()
    agentes = generar_agentes(config, plantillas)
    for agente in agentes:
        print(agente["nombre"], agente["clase"])
"""

import logging
import os
import re
from pathlib import Path
from typing import Any

import yaml

# ── Configuración del logger del módulo ────────────────────────
logger = logging.getLogger(__name__)

# ── Rutas por defecto de los ficheros de configuración ─────────
_DIRECTORIO_CONFIG = Path(__file__).parent
_RUTA_CONFIG = _DIRECTORIO_CONFIG / "config.yaml"
_RUTA_AGENTES = _DIRECTORIO_CONFIG / "agents.yaml"

# ── Constantes del modo examen ─────────────────────────────────
# Submodalidades válidas del modo examen. La selección la hace el
# alumno con 'alumno.submodo' en config.yaml; debe coincidir con la
# que el profesor pase a 'supervisor_main.py --submodo'.
SUBMODOS_EXAMEN_VALIDOS = ("grupo", "individual")
SUBMODO_EXAMEN_POR_DEFECTO = "grupo"

# Nombre local de la sala MUC cuando el examen se hace en grupo.
# Se concatena con 'servicio_muc_examen' para formar el JID
# completo: 'examen@examen.<dominio>'.
SALA_LOCAL_EXAMEN_GRUPO = "examen"

# ── Canonización de nombres de sala MUC ────────────────────────
# Patrón de los nombres de sala que identifican un puesto del aula:
# el prefijo 'pc' seguido del número de puesto, con cualquier
# separador (guion, guion bajo, espacio) o ninguno entre medias.
_PATRON_PUESTO_EXAMEN = re.compile(r"^pc[\s_-]*(\d+)$")

# Anchura a la que se rellena con ceros el número de puesto al
# canonizarlo (por ejemplo, 'PC-5' → 'pc-05').
_ANCHO_NUMERO_PUESTO = 2

# Prefijo del rol que se antepone al nick base por defecto cuando el
# alumno NO ha indicado un nick específico para ese rol en el bloque
# 'alumno' de config.yaml. Se mantienen iniciales breves ('T' / 'J')
# para que el sufijo identifique con claridad el rol sin alargar el
# nick más de lo necesario en el panel del supervisor.
_PREFIJO_NICK_TABLERO = "T"
_PREFIJO_NICK_JUGADOR = "J"

# Anchura a la que se rellenan con ceros los índices que añade la
# utilidad al final del nick para diferenciar agentes del mismo rol
# dentro de la sala (p. ej. 'Pedro-01', 'Pedro-02').
_ANCHO_INDICE_NICK = 2

# ── Constantes del perfil LLM ──────────────────────────────────
# Valor de 'llm.perfil_activo' que indica que el sistema NO debe
# usar ningún servicio LLM. La estrategia de nivel 4 (LLM) es
# OPCIONAL: solo la necesitan los alumnos que la implementen. Con
# este valor —o si 'perfil_activo' está vacío o ausente, o si falta
# por completo la sección 'llm'— 'cargar_configuracion' devuelve
# config["llm"] = None y el sistema arranca sin exigir ninguna
# API key. Es el valor por defecto del config.yaml de la asignatura.
PERFIL_LLM_NINGUNO = "ninguno"


def _calcular_nick_base(
    seccion_alumno: dict[str, Any],
    tipo_agente: str,
) -> str:
    """Devuelve el nick base que el alumno quiere ver en la sala MUC
    para los agentes de un rol concreto (tablero o jugador).

    La utilidad de creación de agentes parte de este nick base y le
    añade un sufijo único por instancia para que en la sala no
    aparezcan ocupantes con el mismo nick. Por eso esta función no
    devuelve el nick definitivo: solo el material a partir del cual
    se construye.

    Regla de resolución:

    1. Si ``alumno.nick_<tipo>`` está presente y no está vacío, se
       usa tal cual (con los espacios de los extremos eliminados).
    2. En cualquier otro caso (campo ausente, vacío o solo con
       espacios) se cae al ``alumno.usuario_uja``. Esto garantiza
       que un alumno que no toque la configuración nueva sigue
       obteniendo un nick reconocible (su usuario UJA).
    3. Si tampoco hay ``usuario_uja``, se devuelve una etiqueta
       neutra dependiente del rol (``"tablero"`` / ``"jugador"``)
       para no propagar una cadena vacía al servidor MUC.

    Args:
        seccion_alumno: Bloque ``alumno`` del config.yaml.
        tipo_agente: ``"tablero"`` o ``"jugador"``. La función no
            valida otros valores: cualquier otra cosa se trata como
            si el campo de nick específico estuviese ausente.

    Returns:
        Nick base sin sufijo, listo para que la utilidad de creación
        de agentes le añada el índice que lo hace único.
    """
    campo_nick = f"nick_{tipo_agente}"
    nick_preferido = (seccion_alumno.get(campo_nick) or "").strip()
    usuario_uja = (seccion_alumno.get("usuario_uja") or "").strip()
    etiqueta_neutra = tipo_agente if tipo_agente else "agente"

    if nick_preferido:
        nick_base = nick_preferido
    elif usuario_uja:
        nick_base = usuario_uja
    else:
        nick_base = etiqueta_neutra
    return nick_base


def construir_nick_tablero(nick_base: str, indice_tablero: int) -> str:
    """Compone el nick MUC de un agente tablero a partir del nick
    base y de su posición en la lista de tableros del alumno.

    El sufijo ``-NN`` (con ``NN`` empezando en 01) garantiza que
    todos los tableros de un mismo alumno aparezcan en la sala con
    nicks distintos, y permite al profesor reconocer en el panel el
    orden con el que el alumno los configuró.

    Args:
        nick_base: Nick base devuelto por :func:`_calcular_nick_base`
            o cualquier otra cadena no vacía.
        indice_tablero: Posición del tablero en la lista del alumno,
            empezando en 0.

    Returns:
        Nick definitivo con el sufijo aplicado.
    """
    sufijo = f"{indice_tablero + 1:0{_ANCHO_INDICE_NICK}d}"
    return f"{nick_base}-{sufijo}"


def construir_nick_jugador(
    nick_base: str, nivel: int, indice_jugador: int,
) -> str:
    """Compone el nick MUC de un agente jugador a partir del nick
    base, el nivel de estrategia que ejecuta y su posición dentro de
    ese nivel.

    El sufijo ``-n<nivel>-NN`` reúne dos datos que el profesor
    necesita reconocer de un vistazo en el panel: con qué estrategia
    juega el agente y cuál es dentro de su grupo. ``NN`` empieza en
    01 para mantener la coherencia con :func:`construir_nick_tablero`.

    Args:
        nick_base: Nick base devuelto por :func:`_calcular_nick_base`.
        nivel: Nivel de estrategia (1, 2, 3 o 4).
        indice_jugador: Posición del jugador dentro de su nivel,
            empezando en 0.

    Returns:
        Nick definitivo con el sufijo aplicado.
    """
    sufijo = f"{indice_jugador + 1:0{_ANCHO_INDICE_NICK}d}"
    return f"{nick_base}-n{nivel}-{sufijo}"


def normalizar_nombre_sala(nombre: str) -> str:
    """Canoniza el nombre de una sala MUC a una forma común.

    El nombre de la sala lo escriben tanto el profesor (en los
    ficheros de salas del supervisor) como el alumno (en el campo
    ``alumno.pc`` de su config.yaml). Para que ambos lados se unan
    EXACTAMENTE a la misma sala MUC —y el alumno no sea rechazado por
    el servidor al intentar unirse a una sala que el supervisor no
    creó con ese nombre exacto— el nombre debe canonizarse de forma
    idéntica en los dos lados. Esta función es esa forma común: es la
    MISMA que usa el Agente Supervisor del profesor.

    Reglas de canonización:

    1. Se eliminan los espacios sobrantes de los extremos y se pasa
       todo a minúsculas. El localpart de un JID XMPP es insensible a
       mayúsculas (RFC 7622), pero las comparaciones de cadenas en
       Python no lo son.
    2. Si el nombre identifica un puesto del aula —el prefijo ``pc``
       seguido de un número, con cualquier separador o ninguno— se
       canoniza al formato ``pc-NN`` con el número del puesto relleno
       a dos dígitos. Así ``PC-5``, ``pc5``, ``PC_05`` y ``pc 5`` se
       resuelven todos a ``pc-05``.
    3. Cualquier otro nombre (por ejemplo ``examen``, el de la sala
       del submodo grupo) se devuelve solo con la regla 1 aplicada.

    Args:
        nombre: Nombre de la sala tal como aparece en el fichero de
            configuración.

    Returns:
        El nombre de la sala canonizado a la forma común.
    """
    base = nombre.strip().lower()
    coincidencia = _PATRON_PUESTO_EXAMEN.match(base)
    if coincidencia is not None:
        numero_puesto = int(coincidencia.group(1))
        resultado = f"pc-{numero_puesto:0{_ANCHO_NUMERO_PUESTO}d}"
    else:
        resultado = base
    return resultado

def _resolver_clave_modalidad(seccion_alumno: dict[str, Any]) -> str:
    """Devuelve la clave de ``agents.yaml`` que corresponde a la
    modalidad activa del alumno.

    Para ``laboratorio`` y ``torneo`` la clave coincide con el valor
    del campo ``modalidad``. Para ``examen`` se compone con la
    submodalidad: ``examen_grupo`` o ``examen_individual``. La
    elección entre las dos la hace el alumno con
    ``alumno.submodo`` en ``config.yaml``.

    Args:
        seccion_alumno: Diccionario con los campos del bloque
            ``alumno`` del config.yaml.

    Returns:
        Clave que indexa ``agents.yaml`` ``modalidades:`` (por ej.
        ``"laboratorio"``, ``"torneo"``, ``"examen_grupo"``,
        ``"examen_individual"``).
    """
    modalidad = (seccion_alumno.get("modalidad") or "").strip()
    clave = modalidad
    if modalidad == "examen":
        submodo = (
            seccion_alumno.get("submodo") or SUBMODO_EXAMEN_POR_DEFECTO
        ).strip()
        clave = f"examen_{submodo}"
    return clave


def _aplicar_modo_examen_a_perfil(
    datos_xmpp: dict[str, Any],
    seccion_alumno: dict[str, Any],
) -> None:
    """Sobreescribe ``servicio_muc`` y ``sala_tictactoe`` del perfil
    XMPP cuando la modalidad activa es ``examen``.

    El servidor Prosody de la asignatura tiene un componente MUC
    DEDICADO al examen (``examen.<dominio>``) con la directiva
    ``restrict_room_creation = "admin"``. Para que los agentes del
    alumno apunten al componente correcto y a la sala adecuada
    según la submodalidad, esta función reemplaza en sitio dos
    campos del perfil XMPP activo:

    * ``servicio_muc`` → ``servicio_muc_examen`` del perfil
      (típicamente ``examen.sinbad2.ujaen.es``).
    * ``sala_tictactoe`` →

        - la sala del submodo grupo (``"examen"``) si
          ``alumno.submodo == "grupo"``.
        - el puesto ``alumno.pc`` si ``alumno.submodo ==
          "individual"``.

      En ambos casos el nombre se pasa por
      :func:`normalizar_nombre_sala`, la **forma común** que también
      usa el Agente Supervisor del profesor. Así, escriba el alumno
      ``PC-5``, ``pc-05`` o ``PC_5`` en su ``config.yaml``, su agente
      se unirá EXACTAMENTE a la misma sala (``pc-05@examen.<dominio>``)
      que el supervisor creó, y el servidor no lo rechazará por una
      discrepancia de escritura.

    De este modo el alumno SOLO modifica los campos del bloque
    ``alumno`` (``submodo`` y ``pc``); el perfil XMPP se ajusta
    automáticamente sin necesidad de tocar ``servicio_muc`` ni
    ``sala_tictactoe`` a mano.

    Si la modalidad no es ``examen``, esta función es un no-op.

    Args:
        datos_xmpp: Diccionario del perfil XMPP activo (se modifica
            en sitio).
        seccion_alumno: Bloque ``alumno`` del config.yaml.

    Raises:
        ValueError: Si ``alumno.submodo`` tiene un valor no
            reconocido o si ``submodo == "individual"`` pero falta
            ``alumno.pc``.
    """
    modalidad = (seccion_alumno.get("modalidad") or "").strip()
    if modalidad != "examen":
        return

    servicio_muc_examen = datos_xmpp.get("servicio_muc_examen")
    if servicio_muc_examen:
        datos_xmpp["servicio_muc"] = servicio_muc_examen

    submodo = (
        seccion_alumno.get("submodo") or SUBMODO_EXAMEN_POR_DEFECTO
    ).strip()
    if submodo == "grupo":
        datos_xmpp["sala_tictactoe"] = normalizar_nombre_sala(
            SALA_LOCAL_EXAMEN_GRUPO,
        )
    elif submodo == "individual":
        pc = (seccion_alumno.get("pc") or "").strip()
        if not pc:
            raise ValueError(
                "El submodo 'individual' del modo examen requiere "
                "el campo 'alumno.pc' con el identificador del "
                "puesto del aula (p. ej. 'PC-05'). Edita "
                "config/config.yaml y vuelve a lanzar."
            )

        # El nombre del puesto se canoniza con la forma común para
        # que coincida con la sala que crea el supervisor, sin que
        # importe cómo el alumno lo haya escrito (mayúsculas,
        # espacios, separadores o ceros a la izquierda).
        datos_xmpp["sala_tictactoe"] = normalizar_nombre_sala(pc)
    else:
        raise ValueError(
            f"alumno.submodo='{submodo}' no reconocido. Valores "
            f"válidos: {', '.join(SUBMODOS_EXAMEN_VALIDOS)}."
        )


def _preparar_entorno_llm(datos_llm: dict[str, Any]) -> None:
    """Fija las variables de entorno que LiteLLM/ADK necesitan según
    el proveedor del perfil LLM activo.

    * ``ollama``  → exporta ``OLLAMA_API_BASE`` con la ``url_base``
      del perfil (sin sobrescribir un valor previo del entorno).
    * ``gemini``  → comprueba que la variable indicada en
      ``api_key_env`` (por defecto ``GOOGLE_API_KEY``) está definida.
      Si no lo está, lanza ``RuntimeError`` con un mensaje didáctico
      que indica dónde obtener la clave gratuita.

    Si el perfil no declara ``proveedor`` se asume ``ollama`` por
    compatibilidad con configuraciones anteriores.

    Args:
        datos_llm: Diccionario con los datos del perfil LLM activo.

    Raises:
        RuntimeError: Si el perfil ``gemini`` está activo pero la
            variable de entorno con la API key no está definida.
    """
    proveedor = datos_llm.get("proveedor", "ollama")

    if proveedor == "ollama":
        url_base = datos_llm.get("url_base")
        if url_base:
            os.environ.setdefault("OLLAMA_API_BASE", url_base)
    elif proveedor == "gemini":
        nombre_var = datos_llm.get("api_key_env", "GOOGLE_API_KEY")
        if not os.environ.get(nombre_var):
            raise RuntimeError(
                f"El perfil LLM 'gemini' requiere la variable de "
                f"entorno '{nombre_var}' con una API key de Google "
                f"AI Studio.\n"
                f"  Obtén una clave gratuita en "
                f"https://aistudio.google.com/apikey\n"
                f"  Y expórtala antes de ejecutar:\n"
                f'      export {nombre_var}="tu-api-key"'
            )


def cargar_configuracion(ruta: str | Path = _RUTA_CONFIG) -> dict[str, Any]:
    """Carga la configuración general y resuelve los perfiles activos.

    Lee el fichero config.yaml, identifica el perfil activo de XMPP y
    el perfil activo de LLM, y devuelve un diccionario con las claves
    "xmpp", "llm" y "sistema" ya resueltas (es decir, con los datos
    del perfil seleccionado, no con todos los perfiles).

    Args:
        ruta: Ruta al fichero config.yaml. Por defecto usa el que
            está en el mismo directorio que este módulo.

    Returns:
        Diccionario con tres claves principales:
        - "xmpp": datos del perfil XMPP activo (host, puerto, dominio,
          servicio_muc, sala_tictactoe, password_defecto, etc.)
        - "llm": datos del perfil LLM activo (url_base, modelo,
          proveedor, etc.) o None si no se usa LLM (perfil
          'ninguno', sección 'llm' ausente o campo 'perfil_activo'
          vacío).
        - "sistema": parámetros generales (intervalos, timeouts, puertos, etc.)

    Raises:
        FileNotFoundError: Si el fichero config.yaml no existe.
        ValueError: Si el perfil activo referenciado no existe en los perfiles.
    """
    ruta = Path(ruta)
    resultado = {}

    try:
        contenido_yaml = ruta.read_text(encoding="utf-8")
        config_completa = yaml.safe_load(contenido_yaml)

        # ── Resolver perfil XMPP ───────────────────────────────
        seccion_xmpp = config_completa.get("xmpp", {})
        perfil_xmpp_activo = seccion_xmpp.get("perfil_activo", "local")
        perfiles_xmpp = seccion_xmpp.get("perfiles", {})

        if perfil_xmpp_activo not in perfiles_xmpp:
            raise ValueError(
                f"Perfil XMPP '{perfil_xmpp_activo}' no encontrado. "
                f"Perfiles disponibles: {list(perfiles_xmpp.keys())}"
            )

        datos_xmpp = perfiles_xmpp[perfil_xmpp_activo].copy()
        datos_xmpp["perfil"] = perfil_xmpp_activo

        # Si la modalidad activa es 'examen', el componente MUC del
        # perfil debe redirigirse al dedicado del examen (con
        # 'restrict_room_creation = "admin"') y la sala debe ser la
        # adecuada al submodo (grupo → 'examen', individual → PC-NN).
        # El bloque 'alumno' debe leerse ANTES de construir
        # 'sala_muc_completa' para que esta refleje los cambios.
        seccion_alumno = config_completa.get("alumno", {})
        _aplicar_modo_examen_a_perfil(datos_xmpp, seccion_alumno)

        # Construir la dirección completa de la sala MUC
        sala = datos_xmpp.get("sala_tictactoe", "tictactoe")
        servicio = datos_xmpp.get("servicio_muc", f"conference.{datos_xmpp['dominio']}")
        datos_xmpp["sala_muc_completa"] = f"{sala}@{servicio}"
        resultado["xmpp"] = datos_xmpp

        logger.info(
            "Perfil XMPP activo: '%s' → %s:%s (sala: %s)",
            perfil_xmpp_activo,
            datos_xmpp["host"],
            datos_xmpp["puerto"],
            datos_xmpp["sala_muc_completa"],
        )

        # ── Resolver perfil LLM (opcional) ─────────────────────
        # La estrategia de nivel 4 (LLM) NO es obligatoria. El
        # selector 'llm.perfil_activo' es INDEPENDIENTE del selector
        # 'xmpp.perfil_activo': cambiar el perfil XMPP a "servidor"
        # NO modifica el perfil LLM. Cuando 'perfil_activo' vale
        # 'ninguno' (o está vacío, o falta la sección 'llm' entera)
        # el sistema arranca SIN LLM: config["llm"] queda a None y
        # no se exige ninguna API key.
        seccion_llm = config_completa.get("llm", {})
        perfil_llm_activo = (
            seccion_llm.get("perfil_activo") or PERFIL_LLM_NINGUNO
        ).strip()

        if not seccion_llm or perfil_llm_activo == PERFIL_LLM_NINGUNO:
            resultado["llm"] = None
            logger.info(
                "Sin LLM seleccionado (perfil '%s'): la estrategia "
                "de nivel 4 no está disponible en esta ejecución.",
                PERFIL_LLM_NINGUNO,
            )
        else:
            perfiles_llm = seccion_llm.get("perfiles", {})

            if perfil_llm_activo not in perfiles_llm:
                raise ValueError(
                    f"Perfil LLM '{perfil_llm_activo}' no encontrado. "
                    f"Perfiles disponibles: {list(perfiles_llm.keys())}. "
                    f"Usa '{PERFIL_LLM_NINGUNO}' si tu estrategia no "
                    f"necesita ningún LLM."
                )

            datos_llm = perfiles_llm[perfil_llm_activo].copy()
            datos_llm["perfil"] = perfil_llm_activo
            resultado["llm"] = datos_llm

            # Preparar variables de entorno según el proveedor activo
            # para que LiteLLM/ADK conecten con el servicio correcto.
            _preparar_entorno_llm(datos_llm)

            proveedor = datos_llm.get("proveedor", "ollama")
            destino = datos_llm.get("url_base") or f"<{proveedor} cloud>"
            logger.info(
                "Perfil LLM activo: '%s' (%s) → %s (modelo: %s)",
                perfil_llm_activo,
                proveedor,
                destino,
                datos_llm["modelo"],
            )

        # ── Parámetros generales del sistema ───────────────────
        resultado["sistema"] = config_completa.get("sistema", {})

        # ── Parámetros del bloque "verificacion" (opcional) ────
        resultado["verificacion"] = config_completa.get("verificacion", {})

        # ── Datos del alumno y modalidad de ejecución ──────────
        # Se propagan tal cual para que generar_agentes() los
        # consulte sin tener que volver a leer el YAML. La sección
        # ya se ha leído arriba para resolver el modo examen, se
        # reutiliza la misma referencia.
        resultado["alumno"] = seccion_alumno

    except FileNotFoundError:
        logger.error("Fichero de configuración no encontrado: %s", ruta)
        raise
    except yaml.YAMLError as error_yaml:
        logger.error("Error al parsear %s: %s", ruta, error_yaml)
        raise ValueError(f"Error de sintaxis YAML en {ruta}: {error_yaml}") from error_yaml

    return resultado


def cargar_plantillas(
    ruta: str | Path = _RUTA_AGENTES,
) -> dict[str, Any]:
    """Carga el fichero de plantillas de agentes (agents.yaml).

    El fichero ya no contiene una lista de agentes concretos, sino
    plantillas (``plantilla_tablero`` y ``plantilla_jugador``) y la
    cantidad de cada uno por modalidad (``modalidades.laboratorio``,
    ``modalidades.torneo``).  Los agentes concretos se generan en
    tiempo de ejecución mediante :func:`generar_agentes`.

    Args:
        ruta: Ruta al fichero agents.yaml.

    Returns:
        Diccionario con las claves ``modalidades``,
        ``plantilla_tablero`` y ``plantilla_jugador``.

    Raises:
        FileNotFoundError: Si el fichero agents.yaml no existe.
        ValueError: Si el fichero no contiene un diccionario válido
            o le faltan claves obligatorias.
    """
    ruta = Path(ruta)
    plantillas = {}

    try:
        contenido_yaml = ruta.read_text(encoding="utf-8")
        datos = yaml.safe_load(contenido_yaml)

        if not isinstance(datos, dict):
            raise ValueError(
                f"El fichero {ruta} debe contener un diccionario YAML "
                f"con plantillas (encontrado: {type(datos).__name__})"
            )

        claves_obligatorias = (
            "modalidades", "plantilla_tablero", "plantilla_jugador",
        )
        for clave in claves_obligatorias:
            if clave not in datos:
                raise ValueError(
                    f"El fichero {ruta} debe contener la clave '{clave}'"
                )

        plantillas = datos
        logger.info("Plantillas de agentes cargadas desde: %s", ruta)

    except FileNotFoundError:
        logger.error("Fichero de plantillas no encontrado: %s", ruta)
        raise
    except yaml.YAMLError as error_yaml:
        logger.error("Error al parsear %s: %s", ruta, error_yaml)
        raise ValueError(
            f"Error de sintaxis YAML en {ruta}: {error_yaml}"
        ) from error_yaml

    return plantillas


def generar_agentes(
    config: dict[str, Any],
    plantillas: dict[str, Any],
) -> list[dict[str, Any]]:
    """Genera la lista de agentes concretos a partir de las plantillas.

    Construye los agentes propios del alumno (tableros y jugadores)
    según la modalidad activa.  El nombre de cada agente se forma
    como ``tablero_<usuario>_NN`` o ``jugador_<usuario>_NN``, con
    NN = ``01``, ``02``, …  El puerto web de cada tablero se
    asigna automáticamente como ``puerto_web_base + índice`` (con
    índice 0, 1, 2, …) para evitar colisiones.

    El nivel de estrategia se toma de ``config["alumno"]
    ["nivel_estrategia"]`` y se aplica a todos los jugadores
    generados.

    Args:
        config: Configuración resuelta (resultado de
            :func:`cargar_configuracion`).  Debe contener una sección
            ``alumno`` con ``usuario_uja``, ``modalidad`` y
            ``nivel_estrategia``.
        plantillas: Plantillas cargadas con :func:`cargar_plantillas`.

    Returns:
        Lista de definiciones de agentes con la misma estructura que
        la antigua salida de ``cargar_agentes``: cada elemento es un
        diccionario con ``nombre``, ``clase``, ``modulo``, ``nivel``,
        ``descripcion``, ``parametros`` y ``activo``.

    Raises:
        ValueError: Si la modalidad indicada en ``config`` no existe
            en las plantillas, o si falta algún dato del alumno.
    """
    seccion_alumno = config.get("alumno", {})
    usuario = seccion_alumno.get("usuario_uja", "").strip()
    modalidad = seccion_alumno.get("modalidad", "").strip()

    # Lista de niveles a probar.  Compatibilidad: si alguien aún tiene
    # el campo antiguo "nivel_estrategia" (escalar) se acepta también.
    niveles_estrategia = seccion_alumno.get("niveles_estrategia")
    if niveles_estrategia is None:
        nivel_legacy = seccion_alumno.get("nivel_estrategia")
        niveles_estrategia = [nivel_legacy] if nivel_legacy is not None else []

    if not usuario:
        raise ValueError(
            "Falta 'alumno.usuario_uja' en config.yaml. "
            "Indica tu usuario UJA para generar los agentes."
        )

    if not niveles_estrategia:
        raise ValueError(
            "Falta 'alumno.niveles_estrategia' en config.yaml "
            "(lista de niveles de estrategia a probar)."
        )

    # Para modalidad='examen', la clave que indexa agents.yaml
    # incorpora la submodalidad: 'examen_grupo' o 'examen_individual'.
    # _resolver_clave_modalidad encapsula esa lógica.
    clave_modalidad = _resolver_clave_modalidad(seccion_alumno)

    modalidades = plantillas.get("modalidades", {})
    if clave_modalidad not in modalidades:
        raise ValueError(
            f"Modalidad '{clave_modalidad}' no definida en agents.yaml. "
            f"Modalidades disponibles: {list(modalidades.keys())}"
        )

    cantidades = modalidades[clave_modalidad]
    num_tableros = int(cantidades.get("num_tableros", 0))
    num_jugadores = int(cantidades.get("num_jugadores", 0))

    plantilla_tablero = plantillas["plantilla_tablero"]
    plantilla_jugador = plantillas["plantilla_jugador"]

    # Puerto web base para los tableros (para asignación automática)
    parametros_tablero_base = plantilla_tablero.get("parametros", {})
    puerto_web_base = int(parametros_tablero_base.get("puerto_web_base", 10080))

    agentes: list[dict[str, Any]] = []

    # Nick base por rol: si el alumno no ha indicado uno, se cae a
    # 'usuario_uja' (más adelante se le añade el sufijo único por
    # agente para que no haya colisiones dentro de la sala).
    nick_base_tablero = _calcular_nick_base(seccion_alumno, "tablero")
    nick_base_jugador = _calcular_nick_base(seccion_alumno, "jugador")

    # ── Generar agentes tablero ────────────────────────────────
    for indice in range(num_tableros):
        sufijo = f"{indice + 1:02d}"
        nombre_tablero = f"tablero_{usuario}_{sufijo}"
        parametros = {
            "id_tablero": f"mesa{sufijo}",
            "puerto_web": puerto_web_base + indice,
            "nick_muc": construir_nick_tablero(
                nick_base_tablero, indice,
            ),
        }
        agentes.append({
            "nombre": nombre_tablero,
            "clase": plantilla_tablero["clase"],
            "modulo": plantilla_tablero["modulo"],
            "nivel": plantilla_tablero.get("nivel", 1),
            "descripcion": plantilla_tablero.get("descripcion", ""),
            "parametros": parametros,
            "activo": True,
        })

    # ── Reparto uniforme de jugadores entre niveles de estrategia ──
    # En modalidades con muchos jugadores (LABORATORIO, EXAMEN
    # INDIVIDUAL) se distribuye num_jugadores entre todos los
    # niveles indicados (p. ej. 4-4-4 con 12 jugadores y 3 niveles).
    # Si la división no es exacta, los primeros niveles reciben uno
    # más. En modalidades con un único jugador (TORNEO, EXAMEN
    # GRUPO) se usa solo el primer nivel.
    niveles_normalizados = [int(n) for n in niveles_estrategia]
    MODALIDADES_UN_JUGADOR = ("torneo", "examen_grupo")
    if clave_modalidad in MODALIDADES_UN_JUGADOR:
        plan_distribucion = [(niveles_normalizados[0], num_jugadores)]
    else:
        plan_distribucion = _repartir_uniformemente(
            num_jugadores, niveles_normalizados,
        )

    parametros_jugador_base = plantilla_jugador.get("parametros", {})
    max_partidas = int(parametros_jugador_base.get("max_partidas", 3))

    for nivel, cantidad in plan_distribucion:
        for indice_local in range(cantidad):
            sufijo = f"{indice_local + 1:02d}"
            # Sufijo 'n<nivel>' embebido en el nombre para que el
            # nivel sea visible a simple vista en logs y JIDs.
            nombre_jugador = f"jugador_{usuario}_n{nivel}_{sufijo}"
            parametros = {
                "nivel_estrategia": nivel,
                "max_partidas": max_partidas,
                "nick_muc": construir_nick_jugador(
                    nick_base_jugador, nivel, indice_local,
                ),
            }
            agentes.append({
                "nombre": nombre_jugador,
                "clase": plantilla_jugador["clase"],
                "modulo": plantilla_jugador["modulo"],
                "nivel": plantilla_jugador.get("nivel", 1),
                "descripcion": plantilla_jugador.get("descripcion", ""),
                "parametros": parametros,
                "activo": True,
            })

    logger.info(
        "Generados %d agentes para modalidad '%s' (usuario '%s'): "
        "%d tableros + %d jugadores (niveles %s)",
        len(agentes), clave_modalidad, usuario,
        num_tableros, num_jugadores, niveles_normalizados,
    )

    return agentes


def _repartir_uniformemente(
    total: int,
    niveles: list[int],
) -> list[tuple[int, int]]:
    """Reparte ``total`` jugadores uniformemente entre los niveles dados.

    Si la división no es exacta, los primeros niveles de la lista
    reciben un jugador extra hasta agotar el resto.

    Args:
        total: Número total de jugadores a repartir.
        niveles: Lista de niveles de estrategia entre los que repartir.

    Returns:
        Lista de tuplas ``(nivel, cantidad)`` que indica cuántos
        jugadores se generan para cada nivel.  Mantiene el orden de
        ``niveles`` para que el resultado sea reproducible.
    """
    distribucion: list[tuple[int, int]] = []

    if not niveles or total <= 0:
        return distribucion

    base = total // len(niveles)
    resto = total % len(niveles)

    for posicion, nivel in enumerate(niveles):
        cantidad = base + (1 if posicion < resto else 0)
        if cantidad > 0:
            distribucion.append((nivel, cantidad))

    return distribucion


def cargar_torneos(ruta: str | Path = "config/torneos.yaml") -> list[dict[str, Any]]:
    """Carga la configuración de torneos desde torneos.yaml.

    Si el fichero no existe o está vacío, devuelve una lista vacía
    sin lanzar excepciones (los torneos son opcionales).

    Args:
        ruta: Ruta al fichero torneos.yaml.

    Returns:
        Lista de diccionarios con la definición de cada torneo
        (nombre, sala, descripcion, tableros, jugadores).
        Lista vacía si no hay torneos configurados.
    """
    ruta = Path(ruta)
    resultado = []

    if not ruta.exists():
        logger.debug("Fichero de torneos no encontrado: %s (opcional)", ruta)
        return resultado

    try:
        contenido_yaml = ruta.read_text(encoding="utf-8")
        datos = yaml.safe_load(contenido_yaml)

        if datos is None:
            return resultado

        # El fichero puede contener un dict con clave "torneos"
        # o directamente una lista
        lista_torneos = datos
        if isinstance(datos, dict):
            lista_torneos = datos.get("torneos", [])

        if not isinstance(lista_torneos, list):
            logger.warning(
                "El fichero %s no contiene una lista de torneos válida",
                ruta,
            )
            return resultado

        for torneo in lista_torneos:
            if torneo is None:
                continue
            torneo.setdefault("tableros", [])
            torneo.setdefault("jugadores", [])
            torneo.setdefault("descripcion", "")
            resultado.append(torneo)

        logger.info("Torneos cargados: %d desde %s", len(resultado), ruta)

    except yaml.YAMLError as error_yaml:
        logger.warning(
            "Error al parsear %s: %s. Se continúa sin torneos.",
            ruta, error_yaml,
        )

    return resultado


def construir_jid(nombre_agente: str, config_xmpp: dict[str, Any]) -> str:
    """Construye el JID completo de un agente a partir de su nombre y el perfil XMPP.

    El JID se forma como: nombre@dominio_del_perfil_activo.
    Por ejemplo, con perfil local: "tablero_mesa1@localhost".
    Con perfil servidor: "tablero_mesa1@sinbad2.ujaen.es".

    Args:
        nombre_agente: Nombre del agente (parte local del JID).
        config_xmpp: Diccionario con la configuración XMPP resuelta
            (resultado de cargar_configuracion()["xmpp"]).

    Returns:
        JID completo como cadena (ej: "tablero_mesa1@sinbad2.ujaen.es").
    """
    dominio = config_xmpp.get("dominio", "localhost")
    jid_completo = f"{nombre_agente}@{dominio}"
    return jid_completo

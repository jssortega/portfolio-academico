"""Tabla resumen de la serie de validación del alumno.

Este conftest se aplica a todos los tests de la rama de examen del
alumno. La serie de validación tiene muchos tests y la salida
estándar de pytest resulta difícil de interpretar de un vistazo;
estos *hooks* añaden:

* **Tolerancia a la interrupción.** Cada test seleccionado se
  pre-registra en estado ``PEND`` (pendiente) en
  ``pytest_collection_finish``. Si la sesión termina antes de tiempo
  (``Ctrl+C``, error de colección, aborto del intérprete), los tests
  que no llegaron a ejecutarse quedan reflejados como ``PEND`` en
  lugar de desaparecer sin dejar rastro.
* **Tabla resumen por bloques.** Al cierre de la sesión,
  ``pytest_terminal_summary`` imprime una tabla con una fila por
  **bloque** (cada fichero de test es un bloque) y columnas que
  suman los tests correctos, los que han tenido incidencias y los
  omitidos. Una fila final agrega los totales de la serie.
* **Indicaciones de corrección.** Si algún bloque presenta
  incidencias, se imprime un detalle por test problemático con pasos
  concretos para diagnosticarlas y resolverlas.

Los errores de un test no abortan la sesión: pytest continúa con el
resto y la tabla final recoge todos los resultados.

El estilo coincide con el conftest análogo de la rama del profesor
(``feature/agente-supervisor-examen``) para que las dos series de
validación —la del supervisor y la del alumno— ofrezcan la misma
experiencia al ejecutar ``pytest``.
"""
from dataclasses import dataclass, field
from pathlib import Path

import pytest


# ═══════════════════════════════════════════════════════════════════
#  Estado compartido para la tabla resumen final
# ═══════════════════════════════════════════════════════════════════

# Estado de un test que pytest ha seleccionado pero todavía no ha
# llegado a ejecutar. Si la sesión termina antes de emitir su informe,
# el test conserva este estado y queda reflejado como pendiente.
ESTADO_PENDIENTE = "PEND"

# Clasificación de cada estado en una de las tres columnas de la tabla.
#   correctos    → el test pasó.
#   incidencias  → el test falló, dio error de accesorio o no se ejecutó.
#   omitidos     → el test se saltó por una precondición no cumplida.
_ESTADOS_CORRECTOS = frozenset({"PASS"})
_ESTADOS_INCIDENCIA = frozenset({"FAIL", "ERROR", ESTADO_PENDIENTE})
_ESTADOS_OMITIDO = frozenset({"SKIP", "XFAIL"})


@dataclass
class _ResumenTest:
    """Registro de un test para la tabla resumen final.

    El campo ``nombre`` guarda el nodeid de pytest (útil para volver a
    lanzar el test de forma puntual). El campo ``grupo`` identifica el
    bloque temático —el fichero de test— al que pertenece. El campo
    ``motivo`` lleva el tipo de excepción y el mensaje cuando hubo
    incidencia. El campo ``proposito`` resume, a partir del docstring
    del test, qué verifica; sirve de contexto en el detalle de
    incidencias.
    """

    nombre: str
    estado: str
    grupo: str
    motivo: str = ""
    proposito: str = ""


@dataclass
class _EstadoSesion:
    """Estado agregado de la sesión de pytest para la tabla resumen.

    Se mantiene como variable a nivel de módulo para que los hooks lo
    consulten y lo actualicen sin pasarlo por argumentos.
    """

    resultados: list = field(default_factory=list)


_ESTADO_SESION = _EstadoSesion()


def _grupo_legible(item) -> str:
    """Devuelve la etiqueta del bloque al que pertenece un test.

    Se construye a partir del nombre del fichero de test: se quita el
    prefijo ``test_``, se sustituyen los guiones bajos por espacios y
    se pone la primera letra en mayúscula. Así la tabla agrupa los
    tests por fichero con un encabezado legible.

    Args:
        item: Elemento de test recogido por pytest.

    Returns:
        Etiqueta descriptiva del bloque (por ejemplo, ``Agente
        supervisor``).
    """
    ruta = getattr(item, "fspath", None) or getattr(item, "path", None)
    nombre_fichero = Path(str(ruta)).stem if ruta else "desconocido"
    etiqueta = nombre_fichero
    if etiqueta.startswith("test_"):
        etiqueta = etiqueta[len("test_"):]
    etiqueta = etiqueta.replace("_", " ").strip()
    if etiqueta:
        etiqueta = etiqueta[0].upper() + etiqueta[1:]
    resultado = etiqueta or "Sin grupo"
    return resultado


def _extraer_proposito(item) -> str:
    """Resume qué verifica un test a partir de su docstring.

    Devuelve el primer párrafo del docstring de la función de test
    —su frase de resumen, según la convención PEP 257, aunque esté
    repartida en varias líneas—. Sirve de contexto en el detalle de
    incidencias: explica qué se esperaba del agente. Si el test no
    tiene docstring, devuelve la cadena vacía.

    Args:
        item: Elemento de test recogido por pytest.

    Returns:
        La frase de resumen del test, o ``""`` si no hay docstring.
    """
    proposito = ""
    funcion = getattr(item, "obj", None)
    documentacion = getattr(funcion, "__doc__", None)
    if documentacion:
        lineas_resumen = []
        fin_del_resumen = False
        for linea in documentacion.strip().splitlines():
            if not fin_del_resumen:
                if linea.strip():
                    lineas_resumen.append(linea.strip())
                elif lineas_resumen:
                    # Línea en blanco tras el resumen: cierra el
                    # primer párrafo, que es la frase de resumen.
                    fin_del_resumen = True
        proposito = " ".join(lineas_resumen)
    return proposito


def _extraer_motivo_skip(report) -> str:
    """Extrae el motivo de un informe ``skipped`` para la tabla.

    El informe de pytest guarda el motivo como tupla
    ``(fichero, línea, motivo)`` o como atributo ``wasxfail``.

    Args:
        report: Informe de test (``TestReport``) emitido por pytest.

    Returns:
        Cadena con el motivo, o cadena vacía si no hay motivo claro.
    """
    motivo = ""
    if hasattr(report, "wasxfail") and report.wasxfail:
        motivo = str(report.wasxfail)
    elif isinstance(report.longrepr, tuple) and len(report.longrepr) >= 3:
        motivo = str(report.longrepr[2])
    elif report.longrepr is not None:
        motivo = str(report.longrepr).split("\n", 1)[0]
    return motivo


def _registrar_resultado(
    nodeid: str, estado: str, grupo: str, motivo: str,
    proposito: str = "",
) -> None:
    """Inserta o actualiza el registro de un test en el estado de sesión.

    Si el test ya estaba registrado (por ejemplo, pre-registrado como
    ``PEND`` o con un fallo previo de accesorio), se actualiza su
    estado y su motivo en lugar de duplicar la entrada.

    Args:
        nodeid: Identificador del test (nodeid de pytest).
        estado: Estado final del test (``PASS``, ``FAIL``, …).
        grupo: Bloque temático al que pertenece el test.
        motivo: Tipo de excepción y mensaje cuando hubo incidencia.
        proposito: Frase de resumen del test (de su docstring), como
            contexto del detalle de incidencias.
    """
    existente = next(
        (r for r in _ESTADO_SESION.resultados if r.nombre == nodeid),
        None,
    )
    if existente is None:
        _ESTADO_SESION.resultados.append(
            _ResumenTest(
                nombre=nodeid, estado=estado, grupo=grupo,
                motivo=motivo, proposito=proposito,
            ),
        )
    else:
        existente.estado = estado
        if motivo:
            existente.motivo = motivo
        if not existente.grupo:
            existente.grupo = grupo
        if proposito:
            existente.proposito = proposito


# ═══════════════════════════════════════════════════════════════════
#  Captura de resultados — hooks de pytest
# ═══════════════════════════════════════════════════════════════════

def pytest_collection_finish(session) -> None:
    """Pre-registra cada test seleccionado en estado ``PEND``.

    Se ejecuta cuando ``session.items`` ya contiene la lista definitiva
    de tests que pytest va a ejecutar (filtrada por ``-m``, ``-k`` y
    rutas). Conforme ``pytest_runtest_makereport`` recibe los informes,
    cada registro se actualiza a su estado real. Los tests que no
    lleguen a ejecutarse conservan ``PEND``, lo que deja constancia en
    la tabla resumen de qué quedó sin ejecutar.

    Args:
        session: Sesión de pytest en curso.
    """
    for item in session.items:
        ya_registrado = any(
            registro.nombre == item.nodeid
            for registro in _ESTADO_SESION.resultados
        )
        if not ya_registrado:
            _ESTADO_SESION.resultados.append(
                _ResumenTest(
                    nombre=item.nodeid,
                    estado=ESTADO_PENDIENTE,
                    grupo=_grupo_legible(item),
                    proposito=_extraer_proposito(item),
                ),
            )


def pytest_collectreport(report) -> None:
    """Registra como incidencia los ficheros que fallan al recolectarse.

    Si un fichero de test no se puede importar (dependencia ausente,
    error de sintaxis, fallo en el módulo), pytest emite un informe de
    colección con error. Sin este hook, ese fichero no aparecería en
    la tabla resumen. Aquí se registra como un bloque con una
    incidencia de tipo ``ERROR`` para que quede visible.

    Args:
        report: Informe de colección emitido por pytest.
    """
    if report.failed:
        ruta = str(report.fspath) if report.fspath else report.nodeid
        nombre_fichero = Path(ruta).stem or "desconocido"
        grupo = nombre_fichero
        if grupo.startswith("test_"):
            grupo = grupo[len("test_"):]
        grupo = grupo.replace("_", " ").strip().capitalize() or "Sin grupo"
        motivo = str(report.longrepr).split("\n", 1)[0] if report.longrepr else ""
        _registrar_resultado(
            f"{report.nodeid} (colección)", "ERROR", grupo,
            motivo or "Error al recolectar el fichero de test",
        )


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """Captura el resultado de cada fase de cada test.

    Es un hook envolvente (``hookwrapper=True``): deja que pytest
    construya el ``TestReport`` con normalidad y luego lo posprocesa
    para actualizar la tabla resumen. Se distinguen las fases:

    * ``setup``  → un fallo aquí es un ``ERROR`` de accesorio; un salto
      es un ``SKIP``.
    * ``call``   → un fallo es ``FAIL``; un salto, ``SKIP`` o ``XFAIL``.

    El estado de la fase ``call`` prevalece sobre el de ``setup``
    cuando ambos producen información (un test que pasa el setup y
    luego falla figura como ``FAIL``).

    Args:
        item: Elemento de test en ejecución.
        call: Información de la llamada a la fase actual.

    Yields:
        El control a pytest para que genere el informe; el valor
        producido se posprocesa tras el ``yield``.
    """
    salida = yield
    report = salida.get_result()

    estado = ""
    motivo = ""

    if report.when == "call":
        if report.passed:
            estado = "PASS"
        elif report.failed:
            estado = "FAIL"
            if call.excinfo is not None:
                motivo = f"{type(call.excinfo.value).__name__}: {call.excinfo.value}"
        elif report.skipped:
            estado = "XFAIL" if hasattr(report, "wasxfail") else "SKIP"
            motivo = _extraer_motivo_skip(report)
    elif report.when == "setup":
        if report.failed:
            estado = "ERROR"
            if call.excinfo is not None:
                motivo = f"{type(call.excinfo.value).__name__}: {call.excinfo.value}"
        elif report.skipped:
            estado = "XFAIL" if hasattr(report, "wasxfail") else "SKIP"
            motivo = _extraer_motivo_skip(report)

    if estado != "":
        _registrar_resultado(
            item.nodeid, estado, _grupo_legible(item), motivo,
            _extraer_proposito(item),
        )


# ═══════════════════════════════════════════════════════════════════
#  Indicaciones de corrección de incidencias
# ═══════════════════════════════════════════════════════════════════

# Grupos cuyos tests montan agentes reales y verifican su
# comportamiento. Para sus fallos, las indicaciones apuntan al
# comportamiento del agente —no a la configuración del entorno—. El
# valor es la descripción que se inserta en la indicación.
_GRUPOS_DE_AGENTES = {
    "Protocolo registro": "el protocolo de registro",
    "Protocolo partida": "el protocolo de partida",
    "Protocolo informe": "el protocolo de informe",
    "Factoria jid": "el comportamiento de los agentes en la sala",
}


def _pasos_recuperacion(estado: str, motivo: str, grupo: str = "") -> list:
    """Devuelve los pasos sugeridos para diagnosticar una incidencia.

    El estado y el motivo se inspeccionan con coincidencias textuales
    sobre los errores frecuentes de este proyecto (servidor XMPP no
    accesible, base de datos bloqueada, puerto ocupado, dependencias
    ausentes, etc.). Cada rama devuelve una lista de pasos accionables
    que se imprimen bajo el test en el bloque «Detalle de incidencias».

    Args:
        estado: Estado del test (``FAIL``, ``ERROR``, ``SKIP``,
            ``PEND``).
        motivo: Cadena con el tipo de excepción y el mensaje de error.
        grupo: Bloque temático del test. Permite dar indicaciones
            específicas cuando el fallo es de un protocolo.

    Returns:
        Lista de cadenas con sugerencias accionables.
    """
    texto = (motivo or "").lower()
    pasos: list = []

    if estado == ESTADO_PENDIENTE:
        pasos = [
            "El test estaba seleccionado pero nunca llegó a ejecutarse.",
            "Causa habitual: la sesión se interrumpió (Ctrl+C) o un fallo "
            "previo abortó el intérprete.",
            "Para aislarlo, relanzarlo por su nodeid: "
            "pytest <ruta>::<Clase>::<test> -v",
        ]
    elif "errno 48" in texto or "address already in use" in texto:
        pasos = [
            "Un proceso anterior sigue escuchando en el puerto que un "
            "test reserva (por defecto, los del rango 10080-10089 que "
            "utilizan los tableros del alumno).",
            "Identificarlo: lsof -nP -iTCP:10080-10089 -sTCP:LISTEN",
            "Terminarlo: kill -9 <PID> y relanzar la serie de validación.",
        ]
    elif "modulenotfounderror" in texto or "importerror" in texto:
        pasos = [
            "Falta una dependencia o pytest no se ejecuta desde la raíz "
            "del proyecto.",
            "Reinstalar dependencias: pip install -r requirements.txt",
            "Comprobar que pytest se lanza desde el directorio que "
            "contiene config/, main.py y utils.py.",
        ]
    elif "authenticationfailure" in texto or "could not authenticate" in texto:
        pasos = [
            "Un agente de prueba no pudo autenticarse en el servidor "
            "XMPP. Es lo habitual al lanzar tests de integración "
            "contra el perfil 'servidor' (sinbad2.ujaen.es), cuyas "
            "cuentas no son de libre registro.",
            "Para validar solo la lógica del alumno sin servidor, "
            "lanzar: pytest -m \"not integration\" -v",
        ]
    elif "servidor xmpp" in texto and ("no accesible" in texto or "no disponible" in texto):
        pasos = [
            "El test de integración necesita un servidor XMPP accesible "
            "y el del perfil activo no respondió, así que se ha omitido.",
            "Para el perfil 'local': levantar el contenedor Prosody del "
            "repositorio de infraestructura de la asignatura.",
            "Para el perfil 'servidor': comprobar conectividad con "
            "nc -zv sinbad2.ujaen.es 8022.",
            "Si no se necesita ejecutar integración, esta omisión es "
            "esperada: usar pytest -m \"not integration\".",
        ]
    elif "connection refused" in texto or "connectionrefusederror" in texto:
        pasos = [
            "No se pudo conectar con el servidor XMPP configurado.",
            "Verificar el perfil activo en config/config.yaml (xmpp.perfil_activo).",
            "Perfil 'local': arrancar el Prosody del repositorio de "
            "infraestructura. Perfil 'servidor': nc -zv sinbad2.ujaen.es 8022.",
        ]
    elif "timeout" in texto or "timed out" in texto:
        pasos = [
            "Una operación superó el tiempo de espera configurado.",
            "Si es un test de integración, el servidor XMPP puede estar "
            "lento o saturado: reintentar la prueba aislada.",
            "Relanzar con traza completa para ver dónde se bloquea: "
            "pytest --tb=long <ruta>::<Clase>::<test>",
        ]
    elif estado == "ERROR":
        pasos = [
            "El fallo se produjo en la fase de preparación (accesorio), "
            "no en el cuerpo del test.",
            "Revisar el accesorio implicado y los ficheros que carga "
            "(config/config.yaml, ficheros de salas).",
            "Relanzar el bloque aislado con traza completa: "
            "pytest --tb=long <ruta_del_fichero>",
        ]
    elif estado in ("SKIP", "XFAIL"):
        pasos = [
            "La omisión no es un fallo de la rama: el test no se ha "
            "ejecutado porque una precondición declarada no se cumple "
            "en este entorno. El motivo (línea anterior) indica cuál.",
            "Si la precondición es un servidor XMPP, revisar la sección "
            "de tests de integración de tests/README.md; si es un nivel "
            "de estrategia opcional, revisar alumno.niveles_estrategia "
            "en config/config.yaml.",
        ]
    elif grupo in _GRUPOS_DE_AGENTES:
        pasos = [
            f"Fallo en {_GRUPOS_DE_AGENTES[grupo]}: el agente no "
            "produjo el mensaje o la transición que el test esperaba. "
            "El elemento concreto que falta es el que describe la "
            "línea «Verifica» de arriba.",
            "Causas posibles: (1) el comportamiento del protocolo aún "
            "no está implementado o no se registra en el setup() del "
            "agente; (2) la performativa, el conversation-id o el "
            "thread del mensaje saliente no coinciden con el contrato "
            "del diagrama de secuencia (revisar la metadata FIPA-ACL); "
            "(3) el cuerpo JSON no se construye con el constructor de "
            "la ontología y no valida contra el esquema; (4) el agente "
            "no reconoce el mensaje entrante porque su Template filtra "
            "más estricto de lo que el contrato pide; (5) los plazos "
            "que el agente concede a sus esperas son tan largos que el "
            "arnés cierra el escenario por «quietud» antes de que el "
            "protocolo avance (los techos del arnés están definidos "
            "en tests/simuladores/arnes.py como PERIODO_QUIETUD_SEGUNDOS "
            "y LIMITE_CONDUCCION_SEGUNDOS).",
            "Cuándo se necesita ejecución real: cuando el contrato del "
            "diagrama de secuencia depende de presencias MUC, afiliaciones "
            "(admin/owner) o restricciones del componente MUC del servidor "
            "(p. ej. restrict_room_creation), el arnés simulado no "
            "reproduce esos detalles. Esos tests se marcan con "
            "@pytest.mark.integration y se omiten salvo que se levante un "
            "servidor XMPP local; los demás se prueban en memoria.",
            "Revisar el comportamiento correspondiente del agente del "
            "alumno. Para ver el punto exacto: pytest --tb=long "
            "<ruta>::<Clase>::<test>.",
        ]
    elif grupo == "Reglas juego":
        pasos = [
            "Fallo en la lógica pura del juego: una regla de "
            "agentes/reglas_juego.py no se comportó como el test "
            "esperaba (ver la línea «Verifica» de arriba).",
            "Estas reglas son la base de la lógica de los agentes "
            "—estrategia, validación de jugadas y detección del "
            "desenlace—, así que conviene corregirlas antes de "
            "seguir: revisar la función implicada en "
            "agentes/reglas_juego.py.",
            "Para ver el punto exacto: pytest --tb=long "
            "<ruta>::<Clase>::<test>.",
        ]
    else:
        pasos = [
            "Relanzar este test aislado con traza completa para ver el "
            "punto exacto del fallo: pytest --tb=long <ruta>::<Clase>::<test>",
            "Comprobar que la configuración de config/config.yaml es "
            "coherente con el entorno (perfil XMPP activo).",
        ]

    return pasos


# ═══════════════════════════════════════════════════════════════════
#  Tabla resumen final — hook terminal_summary
# ═══════════════════════════════════════════════════════════════════

_ANCHO_BLOQUE = 26
_ANCHO_NUMERO = 11
_LIMITE_MOTIVO = 200


def _clasificar(estado: str) -> str:
    """Clasifica un estado en su columna de la tabla resumen.

    Args:
        estado: Estado de un test (``PASS``, ``FAIL``, ``SKIP``, …).

    Returns:
        ``"correctos"``, ``"incidencias"`` u ``"omitidos"``.
    """
    if estado in _ESTADOS_CORRECTOS:
        columna = "correctos"
    elif estado in _ESTADOS_INCIDENCIA:
        columna = "incidencias"
    else:
        columna = "omitidos"
    return columna


def _fila_tabla(bloque: str, correctos: int, incidencias: int,
                omitidos: int, total: int) -> str:
    """Compone una fila de la tabla resumen con el formato de columnas fijo.

    Args:
        bloque: Nombre del bloque (o ``TOTAL`` para la fila agregada).
        correctos: Número de tests correctos del bloque.
        incidencias: Número de tests con incidencia del bloque.
        omitidos: Número de tests omitidos del bloque.
        total: Número total de tests del bloque.

    Returns:
        Cadena con la fila formateada, sin salto de línea final.
    """
    fila = (
        f"│ {bloque:<{_ANCHO_BLOQUE}} "
        f"│ {correctos:>{_ANCHO_NUMERO}} "
        f"│ {incidencias:>{_ANCHO_NUMERO}} "
        f"│ {omitidos:>{_ANCHO_NUMERO}} "
        f"│ {total:>{_ANCHO_NUMERO}} │"
    )
    return fila


def _escribir_entrada_detalle(terminalreporter, resultado) -> None:
    """Escribe en el resumen el detalle de un test no superado.

    Imprime, para un test con incidencia u omitido, cuatro tramos:
    el estado y el nodeid, qué verifica el test (su propósito), el
    motivo, y las indicaciones de corrección o de interpretación
    propias de su tipo de fallo. Los tests superados no se detallan.

    Args:
        terminalreporter: Reportero de terminal de pytest.
        resultado: Registro del test (``_ResumenTest``).
    """
    mensaje = resultado.motivo or "(sin motivo registrado)"
    if len(mensaje) > _LIMITE_MOTIVO:
        mensaje = mensaje[: _LIMITE_MOTIVO - 3] + "..."
    terminalreporter.write_line(f"[{resultado.estado}] {resultado.nombre}")
    if resultado.proposito:
        terminalreporter.write_line(
            f"        Verifica: {resultado.proposito}",
        )
    terminalreporter.write_line(f"        → {mensaje}")
    for paso in _pasos_recuperacion(
        resultado.estado, resultado.motivo, resultado.grupo,
    ):
        terminalreporter.write_line(f"          • {paso}")


def pytest_terminal_summary(terminalreporter, exitstatus) -> None:
    """Imprime la tabla resumen por bloques al final de la sesión.

    La tabla muestra una fila por **bloque** (fichero de test) con
    cuatro columnas numéricas: tests correctos, tests con incidencia
    (fallos, errores de accesorio y pruebas que no se ejecutaron),
    tests omitidos y total del bloque. Una fila final agrega los
    totales de toda la serie.

    Si algún bloque tiene incidencias, debajo de la tabla se imprime
    un detalle por test problemático con su motivo y una lista de
    pasos concretos para corregirlo.

    Args:
        terminalreporter: Reportero de terminal de pytest.
        exitstatus: Código de salida de la sesión (no se usa aquí).
    """
    # En una recolección en seco ('pytest --collect-only') no se
    # ejecuta ningún test: todos quedarían en estado PEND y la tabla
    # daría una imagen engañosa. En ese caso no se imprime el resumen.
    if terminalreporter.config.getoption("collectonly", default=False):
        return

    resultados = _ESTADO_SESION.resultados

    terminalreporter.write_sep(
        "=", "Tabla resumen de la serie de validación de la rama de examen",
    )

    if not resultados:
        terminalreporter.write_line(
            "No hay resultados que mostrar: la sesión terminó antes de "
            "seleccionar tests, o el filtro aplicado (-m, -k, rutas) "
            "dejó la serie vacía.",
        )
        return

    # Agrupar por bloque, preservando el orden de primera aparición.
    bloques_ordenados: list = []
    conteo_por_bloque: dict = {}
    for resultado in resultados:
        if resultado.grupo not in conteo_por_bloque:
            bloques_ordenados.append(resultado.grupo)
            conteo_por_bloque[resultado.grupo] = {
                "correctos": 0, "incidencias": 0, "omitidos": 0,
            }
        conteo_por_bloque[resultado.grupo][_clasificar(resultado.estado)] += 1

    # Bordes de la tabla, ajustados a los anchos de columna fijos.
    ancho_num = _ANCHO_NUMERO + 2
    borde_sup = (
        "┌" + "─" * (_ANCHO_BLOQUE + 2) + ("┬" + "─" * ancho_num) * 4 + "┐"
    )
    borde_med = (
        "├" + "─" * (_ANCHO_BLOQUE + 2) + ("┼" + "─" * ancho_num) * 4 + "┤"
    )
    borde_inf = (
        "└" + "─" * (_ANCHO_BLOQUE + 2) + ("┴" + "─" * ancho_num) * 4 + "┘"
    )

    terminalreporter.write_line(borde_sup)
    terminalreporter.write_line(
        f"│ {'Bloque de tests':<{_ANCHO_BLOQUE}} "
        f"│ {'Correctos':>{_ANCHO_NUMERO}} "
        f"│ {'Incidencia':>{_ANCHO_NUMERO}} "
        f"│ {'Omitidos':>{_ANCHO_NUMERO}} "
        f"│ {'Total':>{_ANCHO_NUMERO}} │",
    )
    terminalreporter.write_line(borde_med)

    total_correctos = 0
    total_incidencias = 0
    total_omitidos = 0
    for bloque in bloques_ordenados:
        conteo = conteo_por_bloque[bloque]
        correctos = conteo["correctos"]
        incidencias = conteo["incidencias"]
        omitidos = conteo["omitidos"]
        total_bloque = correctos + incidencias + omitidos
        total_correctos += correctos
        total_incidencias += incidencias
        total_omitidos += omitidos
        nombre_bloque = bloque
        if len(nombre_bloque) > _ANCHO_BLOQUE:
            nombre_bloque = nombre_bloque[: _ANCHO_BLOQUE - 1] + "…"
        terminalreporter.write_line(
            _fila_tabla(nombre_bloque, correctos, incidencias, omitidos, total_bloque),
        )

    terminalreporter.write_line(borde_med)
    total_general = total_correctos + total_incidencias + total_omitidos
    terminalreporter.write_line(
        _fila_tabla(
            "TOTAL", total_correctos, total_incidencias, total_omitidos, total_general,
        ),
    )
    terminalreporter.write_line(borde_inf)

    # Veredicto de una línea: la serie es satisfactoria si no hay
    # ningún test con incidencia (los omitidos son precondiciones no
    # cumplidas, no fallos de la rama del alumno).
    if total_incidencias == 0:
        terminalreporter.write_line(
            f"Veredicto: OK — {total_correctos} test(s) correctos, "
            f"{total_omitidos} omitido(s), 0 incidencias.",
        )
    else:
        terminalreporter.write_line(
            f"Veredicto: REVISAR — {total_incidencias} test(s) con "
            f"incidencia sobre {total_general}. Ver el detalle más abajo.",
        )

    # Detalle de incidencias con indicaciones de corrección.
    incidencias = [
        r for r in resultados if r.estado in _ESTADOS_INCIDENCIA
    ]
    if incidencias:
        terminalreporter.write_sep(
            "-", "Detalle de incidencias y cómo corregirlas",
        )
        for resultado in incidencias:
            _escribir_entrada_detalle(terminalreporter, resultado)

    # Detalle de los tests omitidos: por qué se omitió cada uno.
    omitidos = [
        r for r in resultados if r.estado in _ESTADOS_OMITIDO
    ]
    if omitidos:
        terminalreporter.write_sep(
            "-", "Detalle de los tests omitidos",
        )
        for resultado in omitidos:
            _escribir_entrada_detalle(terminalreporter, resultado)

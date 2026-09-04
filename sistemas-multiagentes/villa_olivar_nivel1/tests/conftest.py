"""Tabla resumen e indicaciones de corrección de la batería del alumno.

Este conftest se aplica a todos los tests del proyecto: los del
profesor en ``tests/profesor/`` y los que el grupo añada en otras
carpetas de ``tests/``. Adapta el diseño pedagógico de la rama
hermana ``agente-profesor-emergencias-nivel3`` (donde el supervisor
lo usa para sus propias series de validación) a las necesidades
del alumno: el cuerpo del run muestra una línea por test gracias a
``--tb=line`` (declarado en ``pytest.ini``) y este conftest añade
al final una tabla resumen por bloque con indicaciones accionables
para cada incidencia, de modo que la salida no quede sepultada por
los tracebacks largos de ``httpx``/``aiohttp``.

Funcionalidades:

1. **Tolerancia a la interrupción.** Cada test seleccionado se
   pre-registra en estado ``PEND`` (pendiente) en
   ``pytest_collection_finish``. Si la sesión termina antes de
   tiempo (``Ctrl+C``, error de colección), los tests que no
   llegaron a ejecutarse quedan reflejados como ``PEND`` en lugar
   de desaparecer sin dejar rastro.

2. **Tabla resumen por bloques.** Al cierre de la sesión,
   ``pytest_terminal_summary`` imprime una tabla con una fila por
   **bloque** (cada fichero de test es un bloque) y columnas que
   suman tests correctos, con incidencia y omitidos. Una fila
   final agrega los totales de la serie.

3. **Indicaciones de corrección.** Si algún bloque presenta
   incidencias, se imprime un detalle por test problemático con
   pasos concretos para diagnosticarlas, adaptados a los errores
   frecuentes del alumno: Centralita no arrancada, bloque
   ``evaluacion:`` sin descomentar en ``config/config.yaml``,
   agente del grupo que no devuelve ``InformeResolucion`` válido,
   etc.

Los errores de un test no abortan la sesión: pytest continúa con
el resto y la tabla final recoge todos los resultados.
"""

from dataclasses import dataclass, field
from pathlib import Path

import pytest


# ═══════════════════════════════════════════════════════════════════
#  Estado compartido para la tabla resumen final
# ═══════════════════════════════════════════════════════════════════

# Estado de un test que pytest ha seleccionado pero todavía no ha
# llegado a ejecutar. Si la sesión termina antes de emitir su
# informe, el test conserva este estado y queda reflejado como
# pendiente.
ESTADO_PENDIENTE = "PEND"

# Clasificación de cada estado en una de las tres columnas de la
# tabla resumen.
_ESTADOS_CORRECTOS = frozenset({"PASS"})
_ESTADOS_INCIDENCIA = frozenset({"FAIL", "ERROR", ESTADO_PENDIENTE})
_ESTADOS_OMITIDO = frozenset({"SKIP", "XFAIL"})


@dataclass
class _ResumenTest:
    """Registro de un test para la tabla resumen final."""

    nombre: str
    estado: str
    grupo: str
    motivo: str = ""


@dataclass
class _EstadoSesion:
    """Estado agregado de la sesión de pytest para la tabla resumen."""

    resultados: list = field(default_factory=list)


_ESTADO_SESION = _EstadoSesion()


def _grupo_legible(item) -> str:
    """Devuelve la etiqueta del bloque al que pertenece un test.

    Se construye a partir del nombre del fichero de test: se quita
    el prefijo ``test_``, se sustituyen los guiones bajos por
    espacios y se pone la primera letra en mayúscula.
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


def _extraer_motivo_skip(report) -> str:
    """Extrae el motivo de un informe ``skipped`` para la tabla."""
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
) -> None:
    """Inserta o actualiza el registro de un test en el estado de sesión."""
    existente = next(
        (r for r in _ESTADO_SESION.resultados if r.nombre == nodeid),
        None,
    )
    if existente is None:
        _ESTADO_SESION.resultados.append(
            _ResumenTest(
                nombre=nodeid, estado=estado, grupo=grupo, motivo=motivo,
            ),
        )
    else:
        existente.estado = estado
        if motivo:
            existente.motivo = motivo
        if not existente.grupo:
            existente.grupo = grupo


# ═══════════════════════════════════════════════════════════════════
#  Captura de resultados — hooks de pytest
# ═══════════════════════════════════════════════════════════════════

def pytest_collection_finish(session) -> None:
    """Pre-registra cada test seleccionado en estado ``PEND``."""
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
                ),
            )


def pytest_collectreport(report) -> None:
    """Registra como incidencia los ficheros que fallan al recolectarse."""
    if report.failed:
        ruta = str(report.fspath) if report.fspath else report.nodeid
        nombre_fichero = Path(ruta).stem or "desconocido"
        grupo = nombre_fichero
        if grupo.startswith("test_"):
            grupo = grupo[len("test_"):]
        grupo = grupo.replace("_", " ").strip().capitalize() or "Sin grupo"
        motivo = (
            str(report.longrepr).split("\n", 1)[0]
            if report.longrepr else ""
        )
        _registrar_resultado(
            f"{report.nodeid} (colección)", "ERROR", grupo,
            motivo or "Error al recolectar el fichero de test",
        )


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """Captura el resultado de cada fase de cada test."""
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
                motivo = (
                    f"{type(call.excinfo.value).__name__}: "
                    f"{call.excinfo.value}"
                )
        elif report.skipped:
            estado = "XFAIL" if hasattr(report, "wasxfail") else "SKIP"
            motivo = _extraer_motivo_skip(report)
    elif report.when == "setup":
        if report.failed:
            estado = "ERROR"
            if call.excinfo is not None:
                motivo = (
                    f"{type(call.excinfo.value).__name__}: "
                    f"{call.excinfo.value}"
                )
        elif report.skipped:
            estado = "XFAIL" if hasattr(report, "wasxfail") else "SKIP"
            motivo = _extraer_motivo_skip(report)

    if estado != "":
        _registrar_resultado(
            item.nodeid, estado, _grupo_legible(item), motivo,
        )


# ═══════════════════════════════════════════════════════════════════
#  Indicaciones de corrección de incidencias
# ═══════════════════════════════════════════════════════════════════

def _pasos_recuperacion(estado: str, motivo: str) -> list:
    """Devuelve los pasos sugeridos para diagnosticar una incidencia.

    Las ramas se inspeccionan con coincidencias textuales sobre los
    errores frecuentes del alumno en la rama ``examen-alumno``:
    sistema multiagente no arrancado, bloque ``evaluacion:`` sin
    descomentar, agente del grupo con respuesta inválida, etc.
    """
    texto = (motivo or "").lower()
    pasos: list = []

    if estado == ESTADO_PENDIENTE:
        pasos = [
            "El test estaba seleccionado pero nunca llegó a "
            "ejecutarse.",
            "Causa habitual: la sesión se interrumpió (Ctrl+C) o un "
            "fallo previo abortó el intérprete.",
            "Para aislarlo, relanzarlo por su nodeid con traza "
            "completa: pytest --tb=long <ruta>::<Clase>::<test>",
        ]
    elif (
        "connecterror" in texto
        or "connection refused" in texto
        or "all connection attempts failed" in texto
    ):
        pasos = [
            "El sistema multiagente del grupo no está arrancado en "
            "la URL declarada, o la URL declarada no coincide con "
            "la del agente.",
            "Comprobar que `python main.py` está corriendo en otra "
            "terminal.",
            "Verificar la coherencia entre `config/agents.yaml` "
            "(puerto de cada agente) y el bloque `evaluacion:` de "
            "`config/config.yaml` (URL declarada para las pruebas).",
            "Comprobar manualmente con curl: "
            "curl http://localhost:8110/.well-known/agent.json",
        ]
    elif "timeout" in texto or "timed out" in texto:
        pasos = [
            "Una operación HTTP superó el tiempo de espera.",
            "Si es por el LLM, comprobar el perfil activo en "
            "`config/config.yaml` (`llm.perfil_activo`) y que el "
            "modelo está descargado (`make pull-modelo` en el repo "
            "de infraestructura).",
            "Relanzar el test aislado con traza completa para ver "
            "dónde se bloquea: "
            "pytest --tb=long <ruta>::<Clase>::<test>",
        ]
    elif (
        "task" in texto
        and ("failed" in texto or "rejected" in texto)
    ):
        pasos = [
            "Una Task A2A terminó en estado 'failed' o 'rejected' "
            "cuando se esperaba 'completed'.",
            "Revisar el log del agente que procesó la Task: el "
            "agente puede estar rechazando la alerta por validación "
            "Pydantic, clasificación errónea o error interno.",
            "El cuerpo de error suele venir en el campo "
            "status.message de la respuesta JSON-RPC.",
        ]
    elif (
        "informe" in texto
        and ("none" in texto or "no se localizó" in texto)
    ):
        pasos = [
            "La Task completó pero no se encontró un "
            "`InformeResolucion` válido en `artifacts[].parts[]`.",
            "Verificar que el agente emite el informe como DataPart "
            "(type: data) y que el JSON respeta el esquema Pydantic "
            "de `contrato/informe_resolucion.py`.",
            "El campo `tipo_emergencia` es la marca distintiva que "
            "el cliente usa para localizar el informe entre las "
            "partes.",
        ]
    elif "validationerror" in texto or "pydantic" in texto:
        pasos = [
            "Una estructura no respeta el contrato Pydantic.",
            "El mensaje detalla el campo concreto: el agente debe "
            "ajustar su salida al modelo afectado en `contrato/`.",
            "Atender especialmente a `id_emergencia` (debe coincidir "
            "con la alerta) y a `traza_participacion` (lista no "
            "vacía con eventos completos).",
        ]
    elif "modulenotfounderror" in texto or "importerror" in texto:
        pasos = [
            "Falta una dependencia o pytest no se ejecuta desde la "
            "raíz del proyecto.",
            "Reinstalar dependencias: pip install -r requirements.txt",
            "Comprobar que pytest se lanza desde el directorio que "
            "contiene `main.py`, `factoria/` y `config/`.",
        ]
    elif estado == "ERROR":
        pasos = [
            "El fallo se produjo en la fase de preparación "
            "(accesorio), no en el cuerpo del test.",
            "Revisar el accesorio implicado (típicamente "
            "`configuracion_grupo` de `tests/profesor/integracion/"
            "conftest.py`) y los ficheros que carga "
            "(`config/config.yaml`).",
            "Relanzar el bloque aislado con traza completa: "
            "pytest --tb=long <ruta_del_fichero>",
        ]
    elif estado == "SKIP":
        pasos = _pasos_recuperacion_omitido(motivo)
    else:
        pasos = [
            "Relanzar este test aislado con traza completa para ver "
            "el punto exacto del fallo: "
            "pytest --tb=long <ruta>::<Clase>::<test>",
            "Comprobar la coherencia entre `config/agents.yaml` y "
            "el bloque `evaluacion:` de `config/config.yaml`.",
        ]

    return pasos


def _pasos_recuperacion_omitido(motivo: str) -> list:
    """Pasos sugeridos para reactivar una prueba omitida.

    Las acciones dependen del motivo concreto del ``skipif``:
    bloque ``evaluacion:`` sin completar, rol no declarado por el
    grupo, etc.
    """
    texto = (motivo or "").lower()
    pasos: list = []

    if (
        "bomberos como público" in texto
        or "bomberos como publico" in texto
    ):
        pasos = [
            "El test del Hito 5 necesita la URL de un especialista "
            "público con rol 'bomberos' y el grupo no lo ha "
            "declarado en `config/config.yaml`.",
            "Si el grupo expone bomberos como público, descomentar "
            "el bloque `evaluacion:` de `config/config.yaml` y "
            "añadir la URL en `publicos.bomberos`.",
            "Si el grupo NO expone bomberos como público, esta "
            "omisión es esperada.",
        ]
    elif (
        "agente privado" in texto
        or "url de agente privado" in texto
    ):
        pasos = [
            "El test verifica el aislamiento de un privado y el "
            "grupo no ha declarado ninguna URL local de privado.",
            "En `config/config.yaml`, descomentar el bloque "
            "`evaluacion.privados` y añadir la URL local de al "
            "menos uno de los privados.",
            "Si el grupo no expone los privados en URL locales "
            "(viven dentro del proceso de la Centralita), la "
            "omisión es esperada.",
        ]
    elif "url_registro_doblado_en_grupo" in texto:
        pasos = [
            "El test requiere que el grupo haya arrancado su "
            "sistema apuntando al doble del registro REST que "
            "aporta la batería (escenarios H5 de cooperación con "
            "grupo simulado y de modalidad A sin tráfico).",
            "Exportar URL_REGISTRO_DOBLADO_EN_GRUPO=true antes de "
            "arrancar `main.py` para confirmar la configuración.",
            "Esta prueba es opcional para aprobar; aspira a "
            "verificar el Hito 5 en profundidad.",
        ]
    elif "registro rest no alcanzable" in texto:
        pasos = [
            "La prueba consulta el registro REST y este no "
            "respondió.",
            "Levantar la pila Docker del repositorio "
            "`ssmmaa-infraestructura` (`make up`) y comprobar "
            "`curl http://localhost:8020/agentes`.",
        ]
    elif "no hay agentes" in texto or "registro está accesible" in texto:
        pasos = [
            "El registro REST responde pero está vacío.",
            "Verificar que `python main.py` está corriendo y que "
            "los agentes públicos se inscriben al arrancar.",
        ]
    else:
        pasos = [
            "Precondición declarada explícitamente con "
            "`pytest.mark.skipif`; el motivo (línea anterior) "
            "indica cuál es.",
            "Revisar `doc/PRUEBAS_PREVIAS_AL_EXAMEN.md` para saber "
            "cómo activar las pruebas que dependen de declaraciones "
            "del grupo.",
        ]
    return pasos


# ═══════════════════════════════════════════════════════════════════
#  Tabla resumen final — hook terminal_summary
# ═══════════════════════════════════════════════════════════════════

_ANCHO_BLOQUE = 30
_ANCHO_NUMERO = 11
_LIMITE_MOTIVO = 200


def _clasificar(estado: str) -> str:
    """Clasifica un estado en su columna de la tabla resumen."""
    if estado in _ESTADOS_CORRECTOS:
        columna = "correctos"
    elif estado in _ESTADOS_INCIDENCIA:
        columna = "incidencias"
    else:
        columna = "omitidos"
    return columna


def _fila_tabla(
    bloque: str, correctos: int, incidencias: int,
    omitidos: int, total: int,
) -> str:
    """Compone una fila de la tabla resumen con el formato fijo."""
    fila = (
        f"│ {bloque:<{_ANCHO_BLOQUE}} "
        f"│ {correctos:>{_ANCHO_NUMERO}} "
        f"│ {incidencias:>{_ANCHO_NUMERO}} "
        f"│ {omitidos:>{_ANCHO_NUMERO}} "
        f"│ {total:>{_ANCHO_NUMERO}} │"
    )
    return fila


def pytest_terminal_summary(terminalreporter, exitstatus) -> None:
    """Imprime la tabla resumen por bloques al final de la sesión.

    La tabla muestra una fila por **bloque** (fichero de test) con
    cuatro columnas: tests correctos, tests con incidencia, tests
    omitidos y total. Una fila final agrega los totales.

    Si algún bloque tiene incidencias, debajo de la tabla se
    imprime un detalle por test problemático con su motivo y los
    pasos concretos para corregirlo.
    """
    # En una recolección en seco no se ejecuta ningún test; no
    # tiene sentido imprimir la tabla.
    if terminalreporter.config.getoption("collectonly", default=False):
        return

    resultados = _ESTADO_SESION.resultados

    terminalreporter.write_sep(
        "=", "Tabla resumen de la batería de pruebas",
    )

    if not resultados:
        terminalreporter.write_line(
            "No hay resultados que mostrar: la sesión terminó antes "
            "de seleccionar tests, o el filtro aplicado (-m, -k, "
            "rutas) dejó la serie vacía.",
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

    ancho_num = _ANCHO_NUMERO + 2
    borde_sup = (
        "┌" + "─" * (_ANCHO_BLOQUE + 2)
        + ("┬" + "─" * ancho_num) * 4 + "┐"
    )
    borde_med = (
        "├" + "─" * (_ANCHO_BLOQUE + 2)
        + ("┼" + "─" * ancho_num) * 4 + "┤"
    )
    borde_inf = (
        "└" + "─" * (_ANCHO_BLOQUE + 2)
        + ("┴" + "─" * ancho_num) * 4 + "┘"
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
            _fila_tabla(
                nombre_bloque, correctos, incidencias, omitidos,
                total_bloque,
            ),
        )

    terminalreporter.write_line(borde_med)
    total_general = total_correctos + total_incidencias + total_omitidos
    terminalreporter.write_line(
        _fila_tabla(
            "TOTAL", total_correctos, total_incidencias,
            total_omitidos, total_general,
        ),
    )
    terminalreporter.write_line(borde_inf)

    if total_incidencias == 0:
        terminalreporter.write_line(
            f"Veredicto: OK — {total_correctos} test(s) correctos, "
            f"{total_omitidos} omitido(s), 0 incidencias.",
        )
    else:
        terminalreporter.write_line(
            f"Veredicto: REVISAR — {total_incidencias} test(s) con "
            f"incidencia sobre {total_general}. Ver el detalle más "
            "abajo.",
        )

    # Detalle de incidencias con pasos de corrección.
    incidencias = [
        r for r in resultados if r.estado in _ESTADOS_INCIDENCIA
    ]
    if incidencias:
        terminalreporter.write_sep(
            "-", "Detalle de incidencias y cómo corregirlas",
        )
        for resultado in incidencias:
            mensaje = resultado.motivo or "(sin motivo registrado)"
            if len(mensaje) > _LIMITE_MOTIVO:
                mensaje = mensaje[: _LIMITE_MOTIVO - 3] + "..."
            terminalreporter.write_line(
                f"[{resultado.estado}] {resultado.nombre}\n"
                f"        → {mensaje}",
            )
            for paso in _pasos_recuperacion(
                resultado.estado, resultado.motivo,
            ):
                terminalreporter.write_line(f"          • {paso}")

    # Detalle de omisiones agrupado por motivo.
    omitidos = [
        r for r in resultados if r.estado in _ESTADOS_OMITIDO
    ]
    if omitidos:
        terminalreporter.write_sep(
            "-", "Detalle de pruebas omitidas y cómo activarlas",
        )
        agrupadas: dict[str, list] = {}
        orden: list = []
        for resultado in omitidos:
            clave = resultado.motivo or "(sin motivo registrado)"
            if clave not in agrupadas:
                agrupadas[clave] = []
                orden.append(clave)
            agrupadas[clave].append(resultado)

        for clave in orden:
            mensaje = clave
            if len(mensaje) > _LIMITE_MOTIVO:
                mensaje = mensaje[: _LIMITE_MOTIVO - 3] + "..."
            grupo = agrupadas[clave]
            terminalreporter.write_line(
                f"[SKIP] Motivo: {mensaje}",
            )
            terminalreporter.write_line(
                f"        Afecta a {len(grupo)} prueba(s):",
            )
            for resultado in grupo:
                terminalreporter.write_line(
                    f"          - {resultado.nombre}",
                )
            for paso in _pasos_recuperacion_omitido(clave):
                terminalreporter.write_line(f"          • {paso}")

"""Almacén SQLite del supervisor del profesor.

Persiste las ejecuciones del banco de pruebas para poder revisarlas
posteriormente en modo consulta. El esquema replica la idea del
supervisor de TicTacToe (una tabla maestra de ejecuciones más una
tabla de eventos por ejecución) adaptada al dominio Villa Olivar:
en lugar de partidas se almacenan seguimientos de incidentes.

Tablas:

- ``ejecuciones``      Una fila por arranque del supervisor.
- ``grupos``           Grupos bajo prueba en cada ejecución.
- ``seguimientos``     Seguimientos de incidentes (un registro por
                       seguimiento + JSON con la línea de tiempo).
- ``log_eventos``      Log cronológico de la ejecución.

El JSON de la línea de tiempo y del informe se guarda como cadena
para no inflar el esquema con tablas hijas: la información se
consume completa al recargar una ejecución, así que no se gana nada
con normalizarla. Patrón idéntico al del supervisor de TicTacToe.
"""
from __future__ import annotations

import json
import logging
import os
import sqlite3
import threading
from datetime import datetime
from typing import Any, Optional

logger = logging.getLogger(__name__)


# ─── Constantes simbólicas ──────────────────────────────────────────────────

VERSION_ESQUEMA = 1
RUTA_DB_DEFECTO = "data/supervisor.db"


# ─── Esquema SQL ────────────────────────────────────────────────────────────

_ESQUEMA_SQL = """
CREATE TABLE IF NOT EXISTS ejecuciones (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    modo          TEXT NOT NULL,
    inicio        TEXT NOT NULL,
    fin           TEXT,
    descripcion   TEXT
);

CREATE TABLE IF NOT EXISTS grupos (
    ejecucion_id     INTEGER NOT NULL,
    grupo_id         TEXT NOT NULL,
    nombre           TEXT,
    jid_centralita   TEXT,
    descripcion      TEXT,
    PRIMARY KEY (ejecucion_id, grupo_id),
    FOREIGN KEY (ejecucion_id) REFERENCES ejecuciones(id)
);

CREATE TABLE IF NOT EXISTS seguimientos (
    ejecucion_id        INTEGER NOT NULL,
    id_emergencia       TEXT NOT NULL,
    grupo               TEXT,
    jid_destino         TEXT,
    tipo_emergencia     TEXT,
    prioridad           TEXT,
    descripcion         TEXT,
    estado              TEXT,
    instante_creacion   TEXT,
    instante_envio      TEXT,
    instante_agree      TEXT,
    instante_informe    TEXT,
    latencia_agree_ms   INTEGER,
    latencia_informe_ms INTEGER,
    error               TEXT,
    informe_json        TEXT,
    eventos_json        TEXT,
    PRIMARY KEY (ejecucion_id, id_emergencia),
    FOREIGN KEY (ejecucion_id) REFERENCES ejecuciones(id)
);

CREATE TABLE IF NOT EXISTS log_eventos (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    ejecucion_id  INTEGER NOT NULL,
    ts            TEXT,
    tipo          TEXT,
    origen        TEXT,
    detalle       TEXT,
    FOREIGN KEY (ejecucion_id) REFERENCES ejecuciones(id)
);

CREATE INDEX IF NOT EXISTS idx_seguimientos_ejec
    ON seguimientos (ejecucion_id);
CREATE INDEX IF NOT EXISTS idx_log_eventos_ejec
    ON log_eventos (ejecucion_id);
"""


# ─── Almacén ────────────────────────────────────────────────────────────────

class AlmacenSupervisor:
    """Acceso SQLite a la persistencia del supervisor.

    Cada instancia gestiona una ejecución activa (la última creada
    con :py:meth:`crear_ejecucion`) y permite consultar todas las
    ejecuciones históricas. Es seguro frente a accesos concurrentes
    desde el mismo proceso gracias a un ``threading.Lock``: SQLite
    serializa las escrituras y aiohttp puede invocar handlers desde
    distintos hilos del *executor* en operaciones de larga duración.
    """

    def __init__(self, ruta_db: str = RUTA_DB_DEFECTO) -> None:
        self.ruta_db = ruta_db
        self._asegurar_directorio_padre()
        self._lock = threading.Lock()
        self._conexion: Optional[sqlite3.Connection] = sqlite3.connect(
            ruta_db, check_same_thread=False, isolation_level=None,
        )
        self._conexion.row_factory = sqlite3.Row
        self._ejecucion_actual: Optional[int] = None
        self._inicializar_esquema()
        logger.info("Almacén SQLite abierto en %s", ruta_db)

    def _asegurar_directorio_padre(self) -> None:
        """Crea el directorio que contiene la BD si no existe."""
        directorio = os.path.dirname(os.path.abspath(self.ruta_db))
        if directorio:
            os.makedirs(directorio, exist_ok=True)

    def _inicializar_esquema(self) -> None:
        """Ejecuta el script de creación del esquema (idempotente)."""
        with self._lock:
            self._conexion.executescript(_ESQUEMA_SQL)

    # ── Ciclo de vida de una ejecución ──────────────────────────────────

    def crear_ejecucion(
        self, modo: str, grupos: list[dict],
        descripcion: str = "",
    ) -> int:
        """Inserta una nueva ejecución y la marca como activa.

        Args:
            modo: Etiqueta libre para distinguir tipos de ejecución
                (``activo``, ``demo``…). Solo se usa al listar.
            grupos: Lista de grupos bajo prueba en esta ejecución.
            descripcion: Texto opcional para localizar la ejecución
                en la lista del dashboard.

        Returns:
            El ``id`` autoincremental asignado a la ejecución.
        """
        inicio = datetime.now().isoformat(timespec="seconds")
        with self._lock:
            cursor = self._conexion.execute(
                "INSERT INTO ejecuciones (modo, inicio, descripcion) "
                "VALUES (?, ?, ?)",
                (modo, inicio, descripcion),
            )
            self._ejecucion_actual = cursor.lastrowid
            for grupo in grupos:
                self._conexion.execute(
                    "INSERT OR REPLACE INTO grupos "
                    "(ejecucion_id, grupo_id, nombre, jid_centralita, descripcion) "
                    "VALUES (?, ?, ?, ?, ?)",
                    (
                        self._ejecucion_actual,
                        grupo.get("id", ""),
                        grupo.get("nombre", ""),
                        grupo.get("jid_centralita", ""),
                        grupo.get("descripcion", ""),
                    ),
                )

        logger.info(
            "Ejecución #%d creada (modo=%s, grupos=%d)",
            self._ejecucion_actual, modo, len(grupos),
        )
        resultado = self._ejecucion_actual
        return resultado

    def finalizar_ejecucion(self) -> None:
        """Marca la ejecución activa como finalizada (campo ``fin``)."""
        if self._ejecucion_actual is None:
            return
        fin = datetime.now().isoformat(timespec="seconds")
        with self._lock:
            self._conexion.execute(
                "UPDATE ejecuciones SET fin = ? WHERE id = ? "
                "AND fin IS NULL",
                (fin, self._ejecucion_actual),
            )
        logger.info(
            "Ejecución #%d marcada como finalizada", self._ejecucion_actual,
        )

    # ── Inserción/actualización de datos en vivo ───────────────────────

    def guardar_seguimiento(self, datos: dict) -> None:
        """Inserta o actualiza un seguimiento.

        Acepta el dict producido por ``Seguimiento.a_dict()`` para
        evitar acoplar la persistencia con la dataclass del autómata.
        """
        if self._ejecucion_actual is None:
            logger.warning(
                "guardar_seguimiento ignorado: sin ejecución activa",
            )
            return

        eventos = datos.get("eventos", [])
        informe = datos.get("informe")

        with self._lock:
            self._conexion.execute(
                "INSERT OR REPLACE INTO seguimientos ("
                "ejecucion_id, id_emergencia, grupo, jid_destino, "
                "tipo_emergencia, prioridad, descripcion, estado, "
                "instante_creacion, instante_envio, instante_agree, "
                "instante_informe, latencia_agree_ms, "
                "latencia_informe_ms, error, informe_json, eventos_json"
                ") VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    self._ejecucion_actual,
                    datos.get("id_emergencia"),
                    datos.get("grupo"),
                    datos.get("jid_destino"),
                    datos.get("tipo_emergencia"),
                    datos.get("prioridad"),
                    datos.get("descripcion"),
                    datos.get("estado"),
                    datos.get("instante_creacion"),
                    datos.get("instante_envio"),
                    datos.get("instante_agree"),
                    datos.get("instante_informe"),
                    datos.get("latencia_agree_ms"),
                    datos.get("latencia_informe_ms"),
                    datos.get("error"),
                    json.dumps(informe, ensure_ascii=False)
                        if informe is not None else None,
                    json.dumps(eventos, ensure_ascii=False),
                ),
            )

    def guardar_evento_log(self, evento: dict) -> None:
        """Persiste un evento del log cronológico."""
        if self._ejecucion_actual is None:
            return
        with self._lock:
            self._conexion.execute(
                "INSERT INTO log_eventos "
                "(ejecucion_id, ts, tipo, origen, detalle) "
                "VALUES (?, ?, ?, ?, ?)",
                (
                    self._ejecucion_actual,
                    evento.get("ts", ""),
                    evento.get("tipo", ""),
                    evento.get("de", ""),
                    evento.get("detalle", ""),
                ),
            )

    # ── Lectura — listado y detalle de ejecuciones ─────────────────────

    def listar_ejecuciones(self) -> list[dict]:
        """Devuelve todas las ejecuciones ordenadas de más reciente a antigua."""
        with self._lock:
            filas = self._conexion.execute(
                "SELECT e.id, e.modo, e.inicio, e.fin, e.descripcion, "
                "(SELECT COUNT(*) FROM seguimientos s "
                "  WHERE s.ejecucion_id = e.id) AS total "
                "FROM ejecuciones e "
                "ORDER BY e.id DESC",
            ).fetchall()

        resultado = [
            {
                "id": fila["id"],
                "modo": fila["modo"],
                "inicio": fila["inicio"],
                "fin": fila["fin"],
                "descripcion": fila["descripcion"] or "",
                "total_seguimientos": fila["total"],
                "etiqueta": _etiqueta_legible(fila),
            }
            for fila in filas
        ]
        return resultado

    def obtener_ejecucion(self, ejecucion_id: int) -> dict:
        """Devuelve el contenido completo de una ejecución pasada.

        El formato coincide con el de ``/api/state`` para que el
        frontend lo represente sin cambios.
        """
        with self._lock:
            metadatos_fila = self._conexion.execute(
                "SELECT id, modo, inicio, fin FROM ejecuciones WHERE id = ?",
                (ejecucion_id,),
            ).fetchone()
            grupos_filas = self._conexion.execute(
                "SELECT grupo_id, nombre, jid_centralita, descripcion "
                "FROM grupos WHERE ejecucion_id = ? ORDER BY grupo_id",
                (ejecucion_id,),
            ).fetchall()
            seguimientos_filas = self._conexion.execute(
                "SELECT * FROM seguimientos WHERE ejecucion_id = ? "
                "ORDER BY instante_creacion DESC",
                (ejecucion_id,),
            ).fetchall()
            log_filas = self._conexion.execute(
                "SELECT ts, tipo, origen, detalle "
                "FROM log_eventos WHERE ejecucion_id = ? "
                "ORDER BY id DESC",
                (ejecucion_id,),
            ).fetchall()

        resultado: dict[str, Any] = {
            "metadatos": {},
            "grupos": [],
            "seguimientos": [],
            "log": [],
        }

        if metadatos_fila is not None:
            resultado["metadatos"] = {
                "id": metadatos_fila["id"],
                "modo": metadatos_fila["modo"],
                "inicio": metadatos_fila["inicio"],
                "fin": metadatos_fila["fin"],
            }
            resultado["grupos"] = [
                {
                    "id": g["grupo_id"],
                    "nombre": g["nombre"] or g["grupo_id"],
                    "jid_centralita": g["jid_centralita"] or "",
                    "descripcion": g["descripcion"] or "",
                }
                for g in grupos_filas
            ]
            resultado["seguimientos"] = [
                _fila_a_seguimiento(fila) for fila in seguimientos_filas
            ]
            resultado["log"] = [
                {
                    "ts": fila["ts"] or "",
                    "tipo": fila["tipo"] or "",
                    "de": fila["origen"] or "",
                    "detalle": fila["detalle"] or "",
                }
                for fila in log_filas
            ]
        return resultado

    def hay_ejecuciones(self) -> bool:
        """¿La BD contiene al menos una ejecución?"""
        with self._lock:
            fila = self._conexion.execute(
                "SELECT 1 FROM ejecuciones LIMIT 1",
            ).fetchone()
        resultado = fila is not None
        return resultado

    # ── Sembrado controlado (usado por la utilidad de demo) ────────────

    def insertar_ejecucion_completa(
        self, modo: str, inicio_iso: str, fin_iso: Optional[str],
        descripcion: str, grupos: list[dict],
        seguimientos: list[dict], log: list[dict],
    ) -> int:
        """Inserta una ejecución entera con todos sus datos.

        Útil para sembrar la BD con la ejecución demo en un solo
        paso (sin pasar por ``crear_ejecucion`` + ``guardar_*``).
        Es la operación que usa :py:func:`sembrar_demo_si_vacio`.
        """
        with self._lock:
            cursor = self._conexion.execute(
                "INSERT INTO ejecuciones "
                "(modo, inicio, fin, descripcion) VALUES (?, ?, ?, ?)",
                (modo, inicio_iso, fin_iso, descripcion),
            )
            ejecucion_id = cursor.lastrowid

            for grupo in grupos:
                self._conexion.execute(
                    "INSERT OR REPLACE INTO grupos "
                    "(ejecucion_id, grupo_id, nombre, jid_centralita, descripcion) "
                    "VALUES (?, ?, ?, ?, ?)",
                    (
                        ejecucion_id,
                        grupo.get("id", ""),
                        grupo.get("nombre", ""),
                        grupo.get("jid_centralita", ""),
                        grupo.get("descripcion", ""),
                    ),
                )

            for datos in seguimientos:
                eventos = datos.get("eventos", [])
                informe = datos.get("informe")
                self._conexion.execute(
                    "INSERT OR REPLACE INTO seguimientos ("
                    "ejecucion_id, id_emergencia, grupo, jid_destino, "
                    "tipo_emergencia, prioridad, descripcion, estado, "
                    "instante_creacion, instante_envio, instante_agree, "
                    "instante_informe, latencia_agree_ms, "
                    "latencia_informe_ms, error, informe_json, eventos_json"
                    ") VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                    (
                        ejecucion_id,
                        datos.get("id_emergencia"),
                        datos.get("grupo"),
                        datos.get("jid_destino"),
                        datos.get("tipo_emergencia"),
                        datos.get("prioridad"),
                        datos.get("descripcion"),
                        datos.get("estado"),
                        datos.get("instante_creacion"),
                        datos.get("instante_envio"),
                        datos.get("instante_agree"),
                        datos.get("instante_informe"),
                        datos.get("latencia_agree_ms"),
                        datos.get("latencia_informe_ms"),
                        datos.get("error"),
                        json.dumps(informe, ensure_ascii=False)
                            if informe is not None else None,
                        json.dumps(eventos, ensure_ascii=False),
                    ),
                )

            for evento in log:
                self._conexion.execute(
                    "INSERT INTO log_eventos "
                    "(ejecucion_id, ts, tipo, origen, detalle) "
                    "VALUES (?, ?, ?, ?, ?)",
                    (
                        ejecucion_id,
                        evento.get("ts", ""),
                        evento.get("tipo", ""),
                        evento.get("de", ""),
                        evento.get("detalle", ""),
                    ),
                )

        logger.info(
            "Ejecución #%d sembrada (%d seguimientos, %d eventos)",
            ejecucion_id, len(seguimientos), len(log),
        )
        return ejecucion_id

    # ── Cierre ──────────────────────────────────────────────────────────

    def cerrar(self) -> None:
        """Cierra la conexión SQLite y libera recursos."""
        with self._lock:
            if self._conexion is not None:
                self._conexion.close()
                self._conexion = None
        logger.info("Almacén SQLite cerrado")


# ─── Helpers de conversión fila ↔ dict ──────────────────────────────────────

def _fila_a_seguimiento(fila: sqlite3.Row) -> dict:
    """Convierte una fila de ``seguimientos`` al formato del dashboard."""
    informe_json = fila["informe_json"]
    eventos_json = fila["eventos_json"]
    informe = json.loads(informe_json) if informe_json else None
    eventos = json.loads(eventos_json) if eventos_json else []

    resultado = {
        "id_emergencia": fila["id_emergencia"],
        "grupo": fila["grupo"],
        "jid_destino": fila["jid_destino"],
        "tipo_emergencia": fila["tipo_emergencia"],
        "prioridad": fila["prioridad"],
        "descripcion": fila["descripcion"],
        "estado": fila["estado"],
        "instante_creacion": fila["instante_creacion"],
        "instante_envio": fila["instante_envio"],
        "instante_agree": fila["instante_agree"],
        "instante_informe": fila["instante_informe"],
        "latencia_agree_ms": fila["latencia_agree_ms"],
        "latencia_informe_ms": fila["latencia_informe_ms"],
        "error": fila["error"],
        "informe": informe,
        "eventos": eventos,
    }
    return resultado


def _etiqueta_legible(fila: sqlite3.Row) -> str:
    """Construye una etiqueta legible para el selector de ejecuciones.

    Formato: ``"#7 · activo · 30 abr 18:42 (en curso)"`` o
    ``"#7 · demo · 30 abr 18:42 → 18:55"`` cuando ya está cerrada.
    """
    inicio = _formatear_iso_corto(fila["inicio"])
    fin = fila["fin"]
    sufijo = "(en curso)" if not fin else \
        f"→ {_formatear_iso_corto(fin, solo_hora=True)}"

    descripcion = (fila["descripcion"] or "").strip()
    detalle_descripcion = f" · {descripcion}" if descripcion else ""

    resultado = (
        f"#{fila['id']} · {fila['modo']} · {inicio} {sufijo}"
        f"{detalle_descripcion}"
    )
    return resultado


def _formatear_iso_corto(
    iso: Optional[str], solo_hora: bool = False,
) -> str:
    """Devuelve una versión corta de un ISO 8601 para mostrar."""
    resultado = ""
    if iso:
        try:
            fecha = datetime.fromisoformat(iso)
            if solo_hora:
                resultado = fecha.strftime("%H:%M")
            else:
                resultado = fecha.strftime("%d %b %H:%M")
        except ValueError:
            resultado = iso
    return resultado

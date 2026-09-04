"""
Almacén SQLite para persistir los datos del Agente Supervisor.

Gestiona una base de datos SQLite con tres tablas (ejecuciones,
informes y eventos) que permiten conservar los datos recopilados
por el supervisor entre distintas ejecuciones del sistema.

Cada vez que el supervisor arranca se crea un nuevo registro de
ejecución.  Al detenerse, se marca como finalizada.  Las ejecuciones
pasadas pueden consultarse desde el panel web.
"""

import json
import logging
import os
import sqlite3
from datetime import datetime

logger = logging.getLogger(__name__)


class AlmacenSupervisor:
    """Capa de persistencia SQLite para el supervisor.

    Atributos:
        ruta_db (str): Ruta al fichero de la base de datos.
        ejecucion_id (int | None): Identificador de la ejecución
            en curso.  ``None`` hasta que se llame a
            ``crear_ejecucion()``.
    """

    def __init__(self, ruta_db: str = "data/supervisor.db") -> None:
        """Abre (o crea) la base de datos e inicializa las tablas.

        Si los directorios intermedios no existen, se crean
        automáticamente.

        Args:
            ruta_db: Ruta al fichero SQLite.
        """
        directorio = os.path.dirname(ruta_db)
        if directorio:
            os.makedirs(directorio, exist_ok=True)

        self._conexion = sqlite3.connect(
            ruta_db, check_same_thread=False,
        )
        self._conexion.row_factory = sqlite3.Row
        self.ruta_db = ruta_db
        self.ejecucion_id = None

        self._crear_tablas()

        logger.info("Almacén SQLite abierto: %s", ruta_db)

    # ── Inicialización del esquema ───────────────────────────────

    def _crear_tablas(self) -> None:
        """Crea las tablas e índices si no existen."""
        cursor = self._conexion.cursor()

        cursor.executescript("""
            CREATE TABLE IF NOT EXISTS ejecuciones (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                inicio      TEXT    NOT NULL,
                fin         TEXT,
                salas_json  TEXT    NOT NULL
            );

            CREATE TABLE IF NOT EXISTS informes (
                id              INTEGER PRIMARY KEY AUTOINCREMENT,
                ejecucion_id    INTEGER NOT NULL,
                sala_id         TEXT    NOT NULL,
                remitente       TEXT    NOT NULL,
                cuerpo_json     TEXT    NOT NULL,
                ts              TEXT    NOT NULL,
                FOREIGN KEY (ejecucion_id) REFERENCES ejecuciones(id)
            );

            CREATE TABLE IF NOT EXISTS eventos (
                id              INTEGER PRIMARY KEY AUTOINCREMENT,
                ejecucion_id    INTEGER NOT NULL,
                sala_id         TEXT    NOT NULL,
                tipo            TEXT    NOT NULL,
                de              TEXT    NOT NULL,
                detalle         TEXT    NOT NULL,
                ts              TEXT    NOT NULL,
                FOREIGN KEY (ejecucion_id) REFERENCES ejecuciones(id)
            );

            CREATE INDEX IF NOT EXISTS idx_informes_ejec
                ON informes(ejecucion_id);
            CREATE INDEX IF NOT EXISTS idx_eventos_ejec
                ON eventos(ejecucion_id);
        """)

        self._conexion.commit()

    # ── Gestión de ejecuciones ───────────────────────────────────

    def crear_ejecucion(self, salas: list[dict]) -> int:
        """Registra una nueva ejecución del supervisor.

        Args:
            salas: Lista de diccionarios con ``id`` y ``jid`` de
                cada sala monitorizada.

        Returns:
            Identificador de la ejecución creada.
        """
        ahora = datetime.now().isoformat()
        salas_json = json.dumps(salas, ensure_ascii=False)

        cursor = self._conexion.cursor()
        cursor.execute(
            "INSERT INTO ejecuciones (inicio, salas_json) VALUES (?, ?)",
            (ahora, salas_json),
        )
        self._conexion.commit()

        self.ejecucion_id = cursor.lastrowid

        logger.info(
            "Ejecución %d creada (%s, %d salas)",
            self.ejecucion_id, ahora, len(salas),
        )

        return self.ejecucion_id

    def finalizar_ejecucion(self) -> None:
        """Marca la ejecución actual como finalizada."""
        if self.ejecucion_id is None:
            return

        ahora = datetime.now().isoformat()
        self._conexion.execute(
            "UPDATE ejecuciones SET fin = ? WHERE id = ?",
            (ahora, self.ejecucion_id),
        )
        self._conexion.commit()

        logger.info("Ejecución %d finalizada", self.ejecucion_id)

    # ── Escritura de datos ───────────────────────────────────────

    def guardar_informe(
        self, sala_id: str, remitente: str, cuerpo: dict,
    ) -> None:
        """Persiste un informe de partida recibido.

        Args:
            sala_id: Identificador de la sala MUC.
            remitente: JID del tablero que envió el informe.
            cuerpo: Diccionario con el cuerpo del informe
                (campos de la ontología).
        """
        if self.ejecucion_id is None:
            return

        ts = datetime.now().strftime("%H:%M:%S")
        cuerpo_json = json.dumps(cuerpo, ensure_ascii=False)

        self._conexion.execute(
            "INSERT INTO informes "
            "(ejecucion_id, sala_id, remitente, cuerpo_json, ts) "
            "VALUES (?, ?, ?, ?, ?)",
            (self.ejecucion_id, sala_id, remitente, cuerpo_json, ts),
        )
        self._conexion.commit()

    def guardar_evento(
        self, sala_id: str, tipo: str, de: str, detalle: str,
        ts: str,
    ) -> None:
        """Persiste un evento del registro cronológico.

        Args:
            sala_id: Identificador de la sala MUC.
            tipo: Tipo del evento (presencia, informe, etc.).
            de: Identificador del agente origen.
            detalle: Descripción del evento.
            ts: Marca temporal formateada (HH:MM:SS).
        """
        if self.ejecucion_id is None:
            return

        self._conexion.execute(
            "INSERT INTO eventos "
            "(ejecucion_id, sala_id, tipo, de, detalle, ts) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (self.ejecucion_id, sala_id, tipo, de, detalle, ts),
        )
        self._conexion.commit()

    # ── Lectura de datos ─────────────────────────────────────────

    def listar_ejecuciones(self) -> list[dict]:
        """Devuelve todas las ejecuciones ordenadas por inicio
        descendente.

        Returns:
            Lista de diccionarios con ``id``, ``inicio``, ``fin``
            y ``num_salas``.
        """
        cursor = self._conexion.execute(
            "SELECT id, inicio, fin, salas_json "
            "FROM ejecuciones ORDER BY inicio DESC",
        )

        resultado = []
        for fila in cursor.fetchall():
            salas = json.loads(fila["salas_json"])
            resultado.append({
                "id": fila["id"],
                "inicio": fila["inicio"],
                "fin": fila["fin"],
                "num_salas": len(salas),
            })

        return resultado

    def obtener_salas_ejecucion(self, ejecucion_id: int) -> list[dict]:
        """Devuelve la configuración de salas de una ejecución.

        Args:
            ejecucion_id: Identificador de la ejecución.

        Returns:
            Lista de diccionarios con ``id`` y ``jid`` de cada sala,
            o lista vacía si la ejecución no existe.
        """
        cursor = self._conexion.execute(
            "SELECT salas_json FROM ejecuciones WHERE id = ?",
            (ejecucion_id,),
        )

        fila = cursor.fetchone()
        resultado = []
        if fila is not None:
            resultado = json.loads(fila["salas_json"])

        return resultado

    def obtener_informes_ejecucion(
        self, ejecucion_id: int,
    ) -> dict[str, dict[str, dict]]:
        """Carga los informes de una ejecución, organizados por sala.

        El formato de retorno es idéntico al de
        ``agente.informes_por_sala``: un diccionario indexado
        primero por sala y luego por JID del tablero remitente.

        Args:
            ejecucion_id: Identificador de la ejecución.

        Returns:
            Diccionario ``{sala_id: {remitente: cuerpo}}``.
        """
        cursor = self._conexion.execute(
            "SELECT sala_id, remitente, cuerpo_json "
            "FROM informes WHERE ejecucion_id = ? "
            "ORDER BY id ASC",
            (ejecucion_id,),
        )

        resultado: dict[str, dict[str, dict]] = {}
        for fila in cursor.fetchall():
            sala_id = fila["sala_id"]
            if sala_id not in resultado:
                resultado[sala_id] = {}
            resultado[sala_id][fila["remitente"]] = json.loads(
                fila["cuerpo_json"],
            )

        return resultado

    def obtener_eventos_ejecucion(
        self, ejecucion_id: int,
    ) -> dict[str, list[dict]]:
        """Carga los eventos de una ejecución, organizados por sala.

        El formato de retorno es idéntico al de
        ``agente.log_por_sala``: un diccionario indexado por sala
        cuyo valor es una lista de eventos en orden cronológico
        inverso (más reciente primero).

        Args:
            ejecucion_id: Identificador de la ejecución.

        Returns:
            Diccionario ``{sala_id: [evento, ...]}``.
        """
        cursor = self._conexion.execute(
            "SELECT sala_id, tipo, de, detalle, ts "
            "FROM eventos WHERE ejecucion_id = ? "
            "ORDER BY id DESC",
            (ejecucion_id,),
        )

        resultado: dict[str, list[dict]] = {}
        for fila in cursor.fetchall():
            sala_id = fila["sala_id"]
            if sala_id not in resultado:
                resultado[sala_id] = []
            resultado[sala_id].append({
                "ts": fila["ts"],
                "tipo": fila["tipo"],
                "de": fila["de"],
                "detalle": fila["detalle"],
            })

        return resultado

    # ── Cierre ───────────────────────────────────────────────────

    def cerrar(self) -> None:
        """Cierra la conexión a la base de datos."""
        self._conexion.close()
        logger.info("Almacén SQLite cerrado: %s", self.ruta_db)

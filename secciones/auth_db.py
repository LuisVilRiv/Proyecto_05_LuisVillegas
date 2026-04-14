"""
secciones/auth_db.py
====================
Capa de autenticación sobre SQLite.

Reemplaza completamente el sistema basado en casino_auth.json.
La base de datos se crea automáticamente en data/assets/casino_auth.db
ejecutando data/assets/schema.sql la primera vez que se instancia AuthDB.

Uso desde casino_premium.py
----------------------------
    from secciones.auth_db import AuthDB, AuthError, TooManyAttemptsError

    auth = AuthDB(BASE_DIR / "data")

    # Registro
    auth.register(username, password, question, answer)   # lanza AuthError si falla

    # Login  →  devuelve True o lanza excepción
    auth.login(username, password)

    # Recuperación
    q = auth.get_security_question(username)
    auth.reset_password(username, answer, new_password)
"""

from __future__ import annotations

import hashlib
import sqlite3
from pathlib import Path


# ── Excepciones propias ─────────────────────────────────────────────────────

class AuthError(Exception):
    """Error de autenticación genérico (mensaje apto para mostrar al usuario)."""


class TooManyAttemptsError(AuthError):
    """Demasiados intentos fallidos en la ventana de 15 minutos."""


# ── Constantes ───────────────────────────────────────────────────────────────

_MAX_FAILED_ATTEMPTS = 5          # intentos fallidos antes de bloquear
_BLOCK_WINDOW_MINUTES = 15        # ventana de tiempo del bloqueo
_SCHEMA_RELATIVE = Path("assets") / "schema.sql"   # relativo a data_dir


# ── Helper ───────────────────────────────────────────────────────────────────

def _sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


# ── Clase principal ──────────────────────────────────────────────────────────

class AuthDB:
    """Gestiona registro, login y recuperación de contraseña con SQLite."""

    def __init__(self, data_dir: Path) -> None:
        """
        Parameters
        ----------
        data_dir : Path
            Ruta a la carpeta ``data/``.  La BD se guarda en
            ``data/assets/casino_auth.db`` y el esquema se lee de
            ``data/assets/schema.sql``.
        """
        assets_dir = data_dir / "assets"
        assets_dir.mkdir(parents=True, exist_ok=True)

        self._db_path = assets_dir / "casino_auth.db"
        self._schema_path = assets_dir / "schema.sql"

        self._init_db()

    # ── Conexión ─────────────────────────────────────────────────────────────

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self._db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode = WAL;")
        conn.execute("PRAGMA foreign_keys = ON;")
        return conn

    def _init_db(self) -> None:
        """Crea las tablas si no existen, usando schema.sql."""
        if not self._schema_path.exists():
            raise FileNotFoundError(
                f"No se encontró el esquema SQL en {self._schema_path}.\n"
                "Asegúrate de que data/assets/schema.sql está en el proyecto."
            )
        sql = self._schema_path.read_text(encoding="utf-8")
        with self._connect() as conn:
            conn.executescript(sql)

    # ── Rate-limiting ─────────────────────────────────────────────────────────

    def _check_rate_limit(self, conn: sqlite3.Connection, username: str) -> None:
        """Lanza TooManyAttemptsError si el usuario supera el límite."""
        row = conn.execute(
            "SELECT intentos_fallidos FROM v_intentos_recientes WHERE username = ? COLLATE NOCASE",
            (username,)
        ).fetchone()
        if row and row["intentos_fallidos"] >= _MAX_FAILED_ATTEMPTS:
            raise TooManyAttemptsError(
                f"Demasiados intentos fallidos. Espera {_BLOCK_WINDOW_MINUTES} minutos."
            )

    def _log_attempt(self, conn: sqlite3.Connection, username: str, *, success: bool) -> None:
        conn.execute(
            "INSERT INTO login_attempts (username, success) VALUES (?, ?)",
            (username, int(success))
        )

    # ── API pública ───────────────────────────────────────────────────────────

    def user_exists(self, username: str) -> bool:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT 1 FROM usuarios WHERE username = ? COLLATE NOCASE",
                (username,)
            ).fetchone()
            return row is not None

    def register(
        self,
        username: str,
        password: str,
        security_question: str,
        security_answer: str,
    ) -> None:
        """
        Registra un nuevo usuario.

        Raises
        ------
        AuthError
            Si el usuario ya existe o los datos son inválidos.
        """
        username = username.strip()
        password = password.strip()
        security_answer = security_answer.strip().lower()

        if not username:
            raise AuthError("El nombre de usuario no puede estar vacío.")
        if not password:
            raise AuthError("La contraseña no puede estar vacía.")
        if not security_question:
            raise AuthError("Debes seleccionar una pregunta de seguridad.")
        if not security_answer:
            raise AuthError("La respuesta de seguridad no puede estar vacía.")

        with self._connect() as conn:
            if self.user_exists(username):
                raise AuthError(f"El usuario '{username}' ya existe.")
            conn.execute(
                """
                INSERT INTO usuarios (username, password_hash, security_question, security_answer_hash)
                VALUES (?, ?, ?, ?)
                """,
                (username, _sha256(password), security_question, _sha256(security_answer))
            )

    def login(self, username: str, password: str) -> None:
        """
        Verifica credenciales.

        Raises
        ------
        AuthError             – usuario no existe o contraseña incorrecta.
        TooManyAttemptsError  – demasiados intentos recientes.
        """
        username = username.strip()

        with self._connect() as conn:
            self._check_rate_limit(conn, username)

            row = conn.execute(
                "SELECT password_hash FROM usuarios WHERE username = ? COLLATE NOCASE",
                (username,)
            ).fetchone()

            if row is None:
                raise AuthError(f"El usuario '{username}' no existe.")

            if row["password_hash"] != _sha256(password):
                self._log_attempt(conn, username, success=False)
                raise AuthError("Contraseña incorrecta.")

            # Login correcto
            self._log_attempt(conn, username, success=True)
            conn.execute(
                "UPDATE usuarios SET last_login = strftime('%Y-%m-%d %H:%M:%S', 'now', 'localtime') "
                "WHERE username = ? COLLATE NOCASE",
                (username,)
            )

    def get_security_question(self, username: str) -> str:
        """Devuelve la pregunta de seguridad del usuario."""
        with self._connect() as conn:
            row = conn.execute(
                "SELECT security_question FROM usuarios WHERE username = ? COLLATE NOCASE",
                (username,)
            ).fetchone()
        if row is None:
            raise AuthError(f"El usuario '{username}' no existe.")
        return row["security_question"]

    def reset_password(self, username: str, security_answer: str, new_password: str) -> None:
        """
        Restablece la contraseña si la respuesta de seguridad es correcta.

        Raises
        ------
        AuthError – usuario no encontrado o respuesta incorrecta.
        """
        username = username.strip()
        security_answer = security_answer.strip().lower()
        new_password = new_password.strip()

        if not new_password:
            raise AuthError("La nueva contraseña no puede estar vacía.")

        with self._connect() as conn:
            row = conn.execute(
                "SELECT security_answer_hash FROM usuarios WHERE username = ? COLLATE NOCASE",
                (username,)
            ).fetchone()
            if row is None:
                raise AuthError(f"El usuario '{username}' no existe.")
            if row["security_answer_hash"] != _sha256(security_answer):
                raise AuthError("Respuesta de seguridad incorrecta.")

            conn.execute(
                "UPDATE usuarios SET password_hash = ? WHERE username = ? COLLATE NOCASE",
                (_sha256(new_password), username)
            )

    # ── Migración desde JSON (utilidad de transición) ─────────────────────────

    def migrate_from_json(self, json_auth_path: Path) -> int:
        """
        Importa usuarios existentes del fichero casino_auth.json a SQLite.

        Returns
        -------
        int
            Número de usuarios migrados (los duplicados se omiten sin error).
        """
        import json

        if not json_auth_path.exists():
            return 0

        data = json.loads(json_auth_path.read_text(encoding="utf-8"))
        users = data.get("users", {})
        migrated = 0

        with self._connect() as conn:
            for username, info in users.items():
                if isinstance(info, str):
                    # Formato antiguo: solo hash
                    pwd_hash = info
                    question = "¿Ciudad donde naciste?"
                    answer_hash = _sha256("migrado")
                else:
                    pwd_hash = info.get("hash", "")
                    question = info.get("question", "¿Ciudad donde naciste?")
                    answer_hash = info.get("answer_hash", _sha256("migrado"))

                if not pwd_hash:
                    continue

                existing = conn.execute(
                    "SELECT 1 FROM usuarios WHERE username = ? COLLATE NOCASE",
                    (username,)
                ).fetchone()
                if existing:
                    continue

                conn.execute(
                    """
                    INSERT INTO usuarios (username, password_hash, security_question, security_answer_hash)
                    VALUES (?, ?, ?, ?)
                    """,
                    (username, pwd_hash, question, answer_hash)
                )
                migrated += 1

        return migrated
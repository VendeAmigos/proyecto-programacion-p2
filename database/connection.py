import sqlite3
import os

class DatabaseConnection:
    """
    Patrón Singleton para manejar la conexión a SQLite de forma global.
    """
    _instance = None

    def __new__(cls, db_name="database.db"):
        if cls._instance is None:
            cls._instance = super(DatabaseConnection, cls).__new__(cls)
            # La BD se guarda en la carpeta 'database'
            cls._instance.db_path = os.path.join(os.path.dirname(__file__), db_name)
            cls._instance.con = sqlite3.connect(cls._instance.db_path, check_same_thread=False)
            cls._instance.con.row_factory = sqlite3.Row
            cls._instance.con.execute("PRAGMA foreign_keys = ON;")
        return cls._instance

    def get_connection(self):
        return self.con

    def close(self):
        if self.con:
            self.con.close()
            self._instance = None

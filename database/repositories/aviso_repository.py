import sqlite3
from database.connection import DatabaseConnection
from database.models.aviso import Aviso

class AvisoRepository:
    def __init__(self):
        self.con = DatabaseConnection().get_connection()

    def crear_aviso(self, titulo, mensaje, autor_id=None):
        try:
            cur = self.con.execute(
                "INSERT INTO avisos (titulo, mensaje, autor_id) VALUES (?, ?, ?)",
                (titulo, mensaje, autor_id),
            )
            self.con.commit()
            return cur.lastrowid
        except sqlite3.Error as e:
            print(f"[DB] Error al crear aviso: {e}")
            return None

    def listar_avisos(self):
        cur = self.con.execute("SELECT * FROM avisos ORDER BY creado_en DESC")
        return [Aviso.from_row(row) for row in cur.fetchall()]

    def eliminar_aviso(self, aviso_id):
        try:
            cur = self.con.execute("DELETE FROM avisos WHERE id = ?", (aviso_id,))
            self.con.commit()
            return cur.rowcount > 0
        except sqlite3.Error:
            return False

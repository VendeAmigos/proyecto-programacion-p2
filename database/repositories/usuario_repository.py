import sqlite3
from database.connection import DatabaseConnection
from database.models.usuario import Usuario

class UsuarioRepository:
    def __init__(self):
        self.con = DatabaseConnection().get_connection()

    def crear_usuario(self, username, password_hash, es_admin=0, nombre_completo=""):
        try:
            self.con.execute(
                "INSERT INTO usuarios (username, password_hash, es_admin, nombre_completo) VALUES (?, ?, ?, ?)",
                (username, password_hash, es_admin, nombre_completo),
            )
            self.con.commit()
            return True
        except sqlite3.Error:
            return False

    def obtener_usuario(self, username):
        cur = self.con.execute("SELECT * FROM usuarios WHERE username = ?", (username,))
        row = cur.fetchone()
        return Usuario.from_row(row) if row else None

    def obtener_usuario_por_id(self, uid):
        cur = self.con.execute("SELECT * FROM usuarios WHERE id = ?", (uid,))
        row = cur.fetchone()
        return Usuario.from_row(row) if row else None

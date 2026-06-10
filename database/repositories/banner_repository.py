import sqlite3
from database.connection import DatabaseConnection
from database.models.banner import Banner

class BannerRepository:
    def __init__(self):
        self.con = DatabaseConnection().get_connection()

    def obtener_banner_activo(self):
        cur = self.con.execute("SELECT * FROM banners WHERE activo = 1 LIMIT 1")
        row = cur.fetchone()
        return Banner.from_row(row) if row else None

    def listar_banners(self):
        cur = self.con.execute("SELECT * FROM banners ORDER BY id DESC")
        return [Banner.from_row(row) for row in cur.fetchall()]

    def crear_banner(self, titulo, subtitulo, imagen, autor_id=None):
        try:
            self.con.execute(
                "INSERT INTO banners (titulo, subtitulo, imagen, autor_id) VALUES (?, ?, ?, ?)",
                (titulo, subtitulo, imagen, autor_id),
            )
            self.con.commit()
            return True
        except sqlite3.Error:
            return False

    def actualizar_banner(self, banner_id, titulo, subtitulo, imagen):
        try:
            cur = self.con.execute(
                "UPDATE banners SET titulo = ?, subtitulo = ?, imagen = ? WHERE id = ?",
                (titulo, subtitulo, imagen, banner_id),
            )
            self.con.commit()
            return cur.rowcount > 0
        except sqlite3.Error:
            return False

    def activar_banner(self, banner_id):
        try:
            self.con.execute("UPDATE banners SET activo = 0")
            self.con.execute("UPDATE banners SET activo = 1 WHERE id = ?", (banner_id,))
            self.con.commit()
            return True
        except sqlite3.Error:
            return False

    def eliminar_banner(self, banner_id):
        try:
            cur = self.con.execute("DELETE FROM banners WHERE id = ?", (banner_id,))
            self.con.commit()
            return cur.rowcount > 0
        except sqlite3.Error:
            return False

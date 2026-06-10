import sqlite3
from database.connection import DatabaseConnection

class VisitaRepository:
    def __init__(self):
        self.con = DatabaseConnection().get_connection()

    def registrar_visita(self, ruta, user_agent, usuario_id=None):
        try:
            self.con.execute(
                "INSERT INTO visitas (ruta, user_agent, usuario_id) VALUES (?, ?, ?)",
                (ruta, user_agent, usuario_id),
            )
            self.con.commit()
        except sqlite3.Error:
            pass

    def obtener_visitas_por_ruta(self):
        cur = self.con.execute(
            "SELECT ruta, COUNT(*) AS conteo FROM visitas GROUP BY ruta ORDER BY conteo DESC"
        )
        return [dict(row) for row in cur.fetchall()]

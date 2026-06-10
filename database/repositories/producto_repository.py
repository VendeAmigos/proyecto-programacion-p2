import sqlite3
from database.connection import DatabaseConnection
from database.models.producto import Producto

class ProductoRepository:
    def __init__(self):
        self.con = DatabaseConnection().get_connection()

    def crear_producto(self, nombre, descripcion, precio, stock, imagen=None, categoria="General"):
        try:
            cur = self.con.execute(
                "INSERT INTO productos (nombre, descripcion, precio, stock, imagen, categoria) VALUES (?, ?, ?, ?, ?, ?)",
                (nombre, descripcion, precio, stock, imagen, categoria),
            )
            self.con.commit()
            return cur.lastrowid
        except sqlite3.Error as e:
            print(f"[DB] Error al crear producto: {e}")
            return None

    def listar_productos(self):
        cur = self.con.execute("SELECT * FROM productos")
        return [dict(row) for row in cur.fetchall()]

    def obtener_producto(self, pid):
        cur = self.con.execute("SELECT * FROM productos WHERE id = ?", (pid,))
        row = cur.fetchone()
        return dict(row) if row else None

    def actualizar_producto(self, pid, precio, stock, imagen, categoria="General"):
        try:
            cur = self.con.execute(
                "UPDATE productos SET precio = ?, stock = ?, imagen = ?, categoria = ? WHERE id = ?",
                (precio, stock, imagen, categoria, pid),
            )
            self.con.commit()
            return cur.rowcount > 0
        except sqlite3.Error:
            return False

    def eliminar_producto(self, pid):
        try:
            cur = self.con.execute("DELETE FROM productos WHERE id = ?", (pid,))
            self.con.commit()
            return cur.rowcount > 0
        except sqlite3.Error:
            return False

    def limpiar_imagen_productos(self, ruta_imagen):
        try:
            cur = self.con.execute(
                "UPDATE productos SET imagen = '' WHERE imagen = ?",
                (ruta_imagen,),
            )
            self.con.commit()
            return cur.rowcount
        except sqlite3.Error as e:
            print(f"[DB] Error al limpiar referencia de imagen: {e}")
            return 0

import sqlite3
from datetime import date
from database.connection import DatabaseConnection
from database.models.pedido import Pedido

class PedidoRepository:
    def __init__(self):
        self.con = DatabaseConnection().get_connection()

    def crear_pedido(self, cliente_nombre, cliente_email, direccion, telefono, items, usuario_id=None):
        try:
            cur = self.con.cursor()
            cur.execute("BEGIN;")
            total = 0.0
            lineas = []

            for item in items:
                pid = int(item["producto_id"])
                qty = int(item["cantidad"])

                cur.execute("SELECT * FROM productos WHERE id = ?", (pid,))
                prod = cur.fetchone()
                if not prod or prod["stock"] < qty:
                    raise ValueError(f"Stock insuficiente para producto {pid}")

                precio_unit = float(prod["precio"])
                total += precio_unit * qty
                lineas.append((pid, qty, precio_unit))

            cur.execute(
                "INSERT INTO pedidos (usuario_id, cliente_nombre, cliente_email, direccion, telefono, total) VALUES (?, ?, ?, ?, ?, ?)",
                (usuario_id, cliente_nombre.strip(), cliente_email, direccion, telefono, total),
            )
            pedido_id = cur.lastrowid

            for pid, qty, precio_unit in lineas:
                cur.execute(
                    "INSERT INTO pedido_items (pedido_id, producto_id, cantidad, precio_unit) VALUES (?, ?, ?, ?)",
                    (pedido_id, pid, qty, precio_unit),
                )
                cur.execute(
                    "UPDATE productos SET stock = stock - ? WHERE id = ?",
                    (qty, pid),
                )

            self.con.commit()
            return pedido_id

        except Exception as e:
            self.con.rollback()
            print(f"[DB] Error creando pedido: {e}")
            return None

    def ventas_del_dia(self):
        hoy = date.today().isoformat()
        cur = self.con.execute(
            "SELECT COUNT(*) AS cantidad, COALESCE(SUM(total), 0) AS total "
            "FROM pedidos WHERE DATE(creado_en) = ?",
            (hoy,),
        )
        row = cur.fetchone()
        return {"total": row["total"], "cantidad_pedidos": row["cantidad"]}

    def listar_pedidos(self):
        cur = self.con.execute("SELECT * FROM pedidos ORDER BY creado_en DESC")
        return [Pedido.from_row(row) for row in cur.fetchall()]

    def actualizar_estado_pedido(self, pedido_id, estado):
        ESTADOS_VALIDOS = {"Esperando pago", "En proceso de envío", "Entregado", "Cancelado"}
        if estado not in ESTADOS_VALIDOS:
            return False
        try:
            cur = self.con.execute(
                "UPDATE pedidos SET estado = ? WHERE id = ?",
                (estado, pedido_id),
            )
            self.con.commit()
            return cur.rowcount > 0
        except sqlite3.Error as e:
            print(f"[DB] Error actualizando estado: {e}")
            return False

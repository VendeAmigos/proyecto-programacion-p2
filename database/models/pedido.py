class Pedido:
    def __init__(self, id=None, usuario_id=None, cliente_nombre="", cliente_email="", total=0.0, creado_en=None, estado="Esperando pago", direccion="", telefono=""):
        self.id = id
        self.usuario_id = usuario_id
        self.cliente_nombre = cliente_nombre
        self.cliente_email = cliente_email
        self.total = total
        self.creado_en = creado_en
        self.estado = estado
        self.direccion = direccion
        self.telefono = telefono

    @classmethod
    def from_row(cls, row):
        if not row:
            return None
        return cls(
            row["id"],
            row["usuario_id"] if "usuario_id" in row.keys() else None,
            row["cliente_nombre"],
            row["cliente_email"],
            row["total"],
            row["creado_en"] if "creado_en" in row.keys() else None,
            row["estado"] if "estado" in row.keys() else "Esperando pago",
            row["direccion"] if "direccion" in row.keys() else "",
            row["telefono"] if "telefono" in row.keys() else ""
        )

class Producto:
    def __init__(self, id=None, nombre="", descripcion="", precio=0.0, stock=0, imagen="", categoria="General"):
        self.id = id
        self.nombre = nombre
        self.descripcion = descripcion
        self.precio = precio
        self.stock = stock
        self.imagen = imagen
        self.categoria = categoria

    def __getitem__(self, key):
        """Permitir acceso tipo diccionario para compatibilidad con Jinja2"""
        return getattr(self, key)

    @classmethod
    def from_row(cls, row):
        if not row:
            return None
        return cls(
            row["id"], 
            row["nombre"], 
            row["descripcion"], 
            row["precio"], 
            row["stock"], 
            row["imagen"],
            row.keys() and "categoria" in row.keys() and row["categoria"] or "General"
        )

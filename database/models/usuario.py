class Usuario:
    def __init__(self, id=None, username="", password_hash="", es_admin=0, nombre_completo=""):
        self.id = id
        self.username = username
        self.password_hash = password_hash
        self.es_admin = es_admin
        self.nombre_completo = nombre_completo

    @classmethod
    def from_row(cls, row):
        if not row:
            return None
        return cls(
            row["id"], 
            row["username"], 
            row["password_hash"], 
            row["es_admin"],
            row.keys() and "nombre_completo" in row.keys() and row["nombre_completo"] or ""
        )

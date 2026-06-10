class Aviso:
    def __init__(self, id=None, autor_id=None, titulo="", mensaje="", creado_en=None):
        self.id = id
        self.autor_id = autor_id
        self.titulo = titulo
        self.mensaje = mensaje
        self.creado_en = creado_en

    @classmethod
    def from_row(cls, row):
        if not row:
            return None
        return cls(
            row["id"], 
            row["autor_id"] if "autor_id" in row.keys() else None, 
            row["titulo"], 
            row["mensaje"], 
            row["creado_en"]
        )

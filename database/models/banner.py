class Banner:
    def __init__(self, id=None, autor_id=None, titulo="", subtitulo="", imagen="", activo=1):
        self.id = id
        self.autor_id = autor_id
        self.titulo = titulo
        self.subtitulo = subtitulo
        self.imagen = imagen
        self.activo = activo

    @classmethod
    def from_row(cls, row):
        if not row:
            return None
        return cls(
            row["id"], 
            row["autor_id"] if "autor_id" in row.keys() else None, 
            row["titulo"], 
            row["subtitulo"], 
            row["imagen"], 
            row["activo"]
        )

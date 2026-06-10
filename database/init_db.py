import sqlite3
from database.connection import DatabaseConnection
from werkzeug.security import generate_password_hash

def inicializar_bd():
    """
    Crea las tablas necesarias y puebla con datos semilla.
    """
    con = DatabaseConnection().get_connection()
    con.executescript("""
        CREATE TABLE IF NOT EXISTS productos (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre      TEXT    NOT NULL,
            descripcion TEXT,
            precio      REAL    NOT NULL,
            stock       INTEGER NOT NULL DEFAULT 0,
            imagen      TEXT,
            categoria   TEXT    DEFAULT 'General'
        );

        CREATE TABLE IF NOT EXISTS usuarios (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            username        TEXT    NOT NULL UNIQUE,
            password_hash   TEXT    NOT NULL,
            es_admin        INTEGER DEFAULT 0,
            nombre_completo TEXT
        );

        CREATE TABLE IF NOT EXISTS pedidos (
            id              INTEGER  PRIMARY KEY AUTOINCREMENT,
            usuario_id      INTEGER,
            cliente_nombre  TEXT     NOT NULL,
            cliente_email   TEXT,
            direccion       TEXT,
            telefono        TEXT,
            total           REAL     NOT NULL DEFAULT 0,
            creado_en       DATETIME DEFAULT CURRENT_TIMESTAMP,
            estado          TEXT     DEFAULT 'Esperando pago',
            FOREIGN KEY(usuario_id) REFERENCES usuarios(id)
        );

        CREATE TABLE IF NOT EXISTS pedido_items (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            pedido_id   INTEGER,
            producto_id INTEGER,
            cantidad    INTEGER,
            precio_unit REAL,
            FOREIGN KEY(pedido_id)   REFERENCES pedidos(id),
            FOREIGN KEY(producto_id) REFERENCES productos(id)
        );

        CREATE TABLE IF NOT EXISTS visitas (
            id         INTEGER  PRIMARY KEY AUTOINCREMENT,
            usuario_id INTEGER,
            ruta       TEXT     NOT NULL,
            fecha      DATETIME DEFAULT CURRENT_TIMESTAMP,
            user_agent TEXT,
            FOREIGN KEY(usuario_id) REFERENCES usuarios(id)
        );

        CREATE TABLE IF NOT EXISTS avisos (
            id        INTEGER  PRIMARY KEY AUTOINCREMENT,
            autor_id  INTEGER,
            titulo    TEXT     NOT NULL,
            mensaje   TEXT     NOT NULL,
            creado_en DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(autor_id) REFERENCES usuarios(id)
        );

        CREATE TABLE IF NOT EXISTS banners (
            id        INTEGER PRIMARY KEY AUTOINCREMENT,
            autor_id  INTEGER,
            titulo    TEXT    NOT NULL DEFAULT '',
            subtitulo TEXT    NOT NULL DEFAULT '',
            imagen    TEXT    NOT NULL DEFAULT '',
            activo    INTEGER NOT NULL DEFAULT 1,
            FOREIGN KEY(autor_id) REFERENCES usuarios(id)
        );
    """)

    # Migración estado pedido
    try:
        con.execute("ALTER TABLE pedidos ADD COLUMN estado TEXT DEFAULT 'Esperando pago'")
        con.commit()
    except sqlite3.OperationalError:
        pass

    # Migración nuevos campos (categoria, nombre_completo, direccion, telefono)
    try:
        con.execute("ALTER TABLE productos ADD COLUMN categoria TEXT DEFAULT 'General'")
        con.commit()
    except sqlite3.OperationalError:
        pass

    try:
        con.execute("ALTER TABLE usuarios ADD COLUMN nombre_completo TEXT")
        con.commit()
    except sqlite3.OperationalError:
        pass

    try:
        con.execute("ALTER TABLE pedidos ADD COLUMN direccion TEXT")
        con.execute("ALTER TABLE pedidos ADD COLUMN telefono TEXT")
        con.commit()
    except sqlite3.OperationalError:
        pass

    try:
        con.execute("ALTER TABLE pedidos ADD COLUMN usuario_id INTEGER")
        con.commit()
    except sqlite3.OperationalError:
        pass

    try:
        con.execute("ALTER TABLE visitas ADD COLUMN usuario_id INTEGER")
        con.commit()
    except sqlite3.OperationalError:
        pass

    try:
        con.execute("ALTER TABLE avisos ADD COLUMN autor_id INTEGER")
        con.commit()
    except sqlite3.OperationalError:
        pass

    try:
        con.execute("ALTER TABLE banners ADD COLUMN autor_id INTEGER")
        con.commit()
    except sqlite3.OperationalError:
        pass

    semilla_inicial(con)


def semilla_inicial(con):
    cur = con.cursor()
    
    # Admin
    cur.execute("SELECT * FROM usuarios WHERE username = 'admin'")
    if not cur.fetchone():
        hashed = generate_password_hash("admin123")
        cur.execute("INSERT INTO usuarios (username, password_hash, es_admin, nombre_completo) VALUES (?, ?, ?, ?)", ("admin", hashed, 1, "Administrador Principal"))

    # Productos
    cur.execute("SELECT COUNT(*) as c FROM productos")
    if cur.fetchone()["c"] == 0:
        catalogo = [
            ("Sony WH-1000XM5", "Cancelación de ruido líder en la industria, sonido premium.", 398.00, 20, "/static/images/Sony_WH-1000XM5.avif", "Audífonos Inalámbricos"),
            ("Apple AirPods Max", "Audio de alta fidelidad, diseño en acero inoxidable.", 549.00, 15, "/static/images/Apple_AirPods_Max.jpg", "Audífonos Inalámbricos"),
            ("Bose QuietComfort 45", "Comodidad icónica y sonido nítido.", 329.00, 30, "/static/images/Bose_QuietComfort_45.jpg", "Audífonos Inalámbricos"),
            ("Sennheiser Momentum 4", "Batería de 60 horas y sonido Sennheiser característico.", 349.00, 25, "/static/images/Sennheiser_Momentum_4.jpg", "Audífonos Inalámbricos"),
            ("Audio-Technica ATH-M50x", "Monitor de estudio profesional aclamado por críticos.", 169.00, 50, "/static/images/Audio-Technica_ATH-M50x.jpg", "Audífonos de Estudio"),
            ("Beyerdynamic DT 770 Pro", "Referencia cerrada para control y monitoreo.", 159.00, 40, "/static/images/Beyerdynamic_DT_770_Pro.jpg", "Audífonos de Estudio"),
            ("Shure AONIC 50", "Calidad de estudio inalámbrica con cancelación de ruido.", 299.00, 35, "/static/images/Shure_AONIC_50.jpg", "Audífonos Inalámbricos"),
            ("Bang & Olufsen Beoplay HX", "Materiales de lujo y sonido equilibrado.", 499.00, 10, "/static/images/Bang_&_Olufsen_Beoplay_HX.png", "Audio de Lujo"),
            ("AKG K702", "Auriculares abiertos de referencia para mezcla y masterización.", 249.00, 20, "/static/images/AKG_K702.jpg", "Audífonos de Estudio"),
            ("HiFiMan Sundara", "Auriculares magnéticos planares para audiófilos.", 299.00, 15, "/static/images/HiFiMan_Sundara.jpg", "Audiófilo"),
        ]
        for p in catalogo:
            cur.execute("INSERT INTO productos (nombre, descripcion, precio, stock, imagen, categoria) VALUES (?, ?, ?, ?, ?, ?)", p)
    
    con.commit()

# tienda_db.py
import os
import sqlite3
from sqlite3 import Error


class BaseDatosTienda:
    def __init__(self, ruta="./", bd="tienda.sqlite3"):
        self.bd_path = os.path.join(ruta, bd)
        self.con = None
        self.cursor = None
        self.conectar()
        self.crear_tablas() # Asegura que las tablas existan al iniciar

    def conectar(self):
        try:
            self.con = sqlite3.connect(self.bd_path, check_same_thread=False)
            self.con.row_factory = sqlite3.Row
            self.cursor = self.con.cursor()
            self.cursor.execute("PRAGMA foreign_keys = ON;")
        except Error as e:
            print(f"[DB] Error al conectar: {e}")

    def cerrar(self):
        try:
            if self.con:
                self.con.close()
        except Error as e:
            print(f"[DB] Error al cerrar: {e}")

    def crear_tablas(self):
        try:
            # Productos
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS productos(
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nombre TEXT NOT NULL,
                    descripcion TEXT,
                    precio REAL NOT NULL,
                    stock INTEGER NOT NULL DEFAULT 0,
                    imagen TEXT
                );
            """)

            # Usuarios
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS usuarios(
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT NOT NULL UNIQUE,
                    password_hash TEXT NOT NULL,
                    es_admin INTEGER DEFAULT 0
                );
            """)

            # Analiticas/Visitas
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS visitas(
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    ruta TEXT NOT NULL,
                    fecha DATETIME DEFAULT CURRENT_TIMESTAMP,
                    user_agent TEXT
                );
            """)

            # Pedidos (existente simplificado)
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS pedidos(
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    cliente_nombre TEXT NOT NULL,
                    cliente_email TEXT,
                    total REAL NOT NULL,
                    creado_en DATETIME DEFAULT CURRENT_TIMESTAMP
                );
            """)

            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS pedido_items(
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    pedido_id INTEGER,
                    producto_id INTEGER,
                    cantidad INTEGER,
                    precio_unit REAL,
                    FOREIGN KEY(pedido_id) REFERENCES pedidos(id),
                    FOREIGN KEY(producto_id) REFERENCES productos(id)
                );
            """)
            
            self.con.commit()
            self.semilla_inicial() 

        except Error as e:
            print(f"[DB] Error creando tablas: {e}")

    def semilla_inicial(self):
        # Admin por defecto
        if not self.obtener_usuario("admin"):
            from werkzeug.security import generate_password_hash
            ph = generate_password_hash("admin123")
            self.crear_usuario("admin", ph, 1)

        # Productos de AUDÍFONOS si están vacíos
        prods = self.listar_productos()
        if not prods:
            audifonos = [
                ("Sony WH-1000XM5", "Cancelación de ruido líder en la industria, sonido premium.", 398.00, 20, "https://m.media-amazon.com/images/I/51SKmu2G9FL._AC_SL1000_.jpg"),
                ("Apple AirPods Max", "Audio de alta fidelidad, diseño en acero inoxidable.", 549.00, 15, "https://store.storeimages.cdn-apple.com/4668/as-images.apple.com/is/airpods-max-hero-select-202011?wid=940&hei=1112&fmt=jpeg&qlt=90&.v=1604709293000"),
                ("Bose QuietComfort 45", "Comodidad icónica y sonido nítido.", 329.00, 30, "https://m.media-amazon.com/images/I/51JbsHSktkL._AC_SL1000_.jpg"),
                ("Sennheiser Momentum 4", "Batería de 60 horas y sonido Sennheiser característico.", 349.00, 25, "https://m.media-amazon.com/images/I/61p-L9sL7mL._AC_SL1500_.jpg"),
                ("Audio-Technica ATH-M50x", "Monitor de estudio profesional aclamado por críticos.", 169.00, 50, "https://m.media-amazon.com/images/I/71HlGeWw3LL._AC_SL1500_.jpg"),
                ("Beyerdynamic DT 770 Pro", "Referencia cerrada para control y monitoreo.", 159.00, 40, "https://m.media-amazon.com/images/I/71-l7kX-U-L._AC_SL1500_.jpg"),
                ("Shure AONIC 50", "Calidad de estudio inalámbrica con cancelación de ruido.", 299.00, 35, "https://m.media-amazon.com/images/I/61CqYq+S0PL._AC_SL1000_.jpg"),
                ("Bang & Olufsen Beoplay HX", "Materiales de lujo y sonido equilibrado.", 499.00, 10, "https://m.media-amazon.com/images/I/61vJtN-8lLL._AC_SL1500_.jpg"),
                ("AKG K702", "Auriculares abiertos de referencia para mezcla y masterización.", 249.00, 20, "https://m.media-amazon.com/images/I/81M9a-zC8EL._AC_SL1500_.jpg"),
                ("HiFiMan Sundara", "Auriculares magnéticos planares para audiófilos.", 299.00, 15, "https://m.media-amazon.com/images/I/61b17a-cW+L._AC_SL1200_.jpg")
            ]
            for m in audifonos:
                self.crear_producto(m[0], m[1], m[2], m[3], m[4])

    # --------- Usuarios ----------
    def crear_usuario(self, username, password_hash, es_admin=0):
        try:
            self.cursor.execute("INSERT INTO usuarios(username, password_hash, es_admin) VALUES(?,?,?)", 
                                (username, password_hash, es_admin))
            self.con.commit()
            return True
        except Error:
            return False

    def obtener_usuario(self, username):
        self.cursor.execute("SELECT * FROM usuarios WHERE username=?", (username,))
        return self.cursor.fetchone()
    
    def obtener_usuario_por_id(self, uid):
        self.cursor.execute("SELECT * FROM usuarios WHERE id=?", (uid,))
        return self.cursor.fetchone()

    # --------- Analytics ----------
    def registrar_visita(self, ruta, user_agent):
        try:
            self.cursor.execute("INSERT INTO visitas(ruta, user_agent) VALUES(?,?)", (ruta, user_agent))
            self.con.commit()
        except:
            pass

    def obtener_visitas_por_ruta(self):
        try:
            self.cursor.execute("SELECT ruta, COUNT(*) as conteo FROM visitas GROUP BY ruta ORDER BY conteo DESC")
            return self.cursor.fetchall()
        except Error:
            return []

    # --------- Productos Modificado ----------
    def crear_producto(self, nombre, descripcion, precio, stock, imagen=None):
        try:
            self.cursor.execute("""
                INSERT INTO productos(nombre, descripcion, precio, stock, imagen)
                VALUES(?,?,?,?,?);
            """, (nombre, descripcion, precio, stock, imagen))
            self.con.commit()
            return self.cursor.lastrowid
        except Error as e:
            print(f"[DB] Error crear prod: {e}")
            return None
    
    def actualizar_stock(self, pid, nuevo_stock):
        try:
            self.cursor.execute("UPDATE productos SET stock=? WHERE id=?", (nuevo_stock, pid))
            self.con.commit()
            return True
        except Error:
            return False

    def actualizar_producto(self, pid, precio, stock, imagen):
        try:
            self.cursor.execute("UPDATE productos SET precio=?, stock=?, imagen=? WHERE id=?", (precio, stock, imagen, pid))
            self.con.commit()
            return True
        except Error:
            return False

    def eliminar_producto(self, pid):
        try:
            self.cursor.execute("DELETE FROM productos WHERE id=?", (pid,))
            self.con.commit()
            return True
        except Error:
            return False

    def listar_productos(self):
        self.cursor.execute("SELECT * FROM productos")
        return self.cursor.fetchall()

    def obtener_producto(self, pid):
        self.cursor.execute("SELECT * FROM productos WHERE id=?", (pid,))
        return self.cursor.fetchone()

    def crear_pedido(self, nombre, email, items):
        # Simplificado para no reescribir todo
        try:
            self.cursor.execute("INSERT INTO pedidos(cliente_nombre, cliente_email, total) VALUES(?,?,0)", (nombre, email))
            pid = self.cursor.lastrowid
            total = 0
            for item in items:
                prod = self.obtener_producto(item['producto_id'])
                if prod and prod['stock'] >= item['cantidad']:
                    subtotal = prod['precio'] * item['cantidad']
                    total += subtotal
                    self.cursor.execute("INSERT INTO pedido_items(pedido_id, producto_id, cantidad, precio_unit) VALUES(?,?,?,?)",
                                        (pid, item['producto_id'], item['cantidad'], prod['precio']))
                    # Restar stock
                    self.actualizar_stock(item['producto_id'], prod['stock'] - item['cantidad'])
                else:
                    return None # Stock insuficiente
            
            self.cursor.execute("UPDATE pedidos SET total=? WHERE id=?", (total, pid))
            self.con.commit()
            return pid
        except Error as e:
            print(e)
            return None

    def semilla_productos(self):
        pass # Ya se hace en semilla_inicial

    def actualizar_stock(self, producto_id, nuevo_stock):
        try:
            self.cursor.execute(
                "UPDATE productos SET stock=? WHERE id=?;",
                (int(nuevo_stock), producto_id)
            )
            self.con.commit()
            return self.cursor.rowcount > 0
        except Error as e:
            print(f"[DB] Error actualizando stock: {e}")
            return False

    # --------- Pedidos ----------
    def crear_pedido(self, cliente_nombre, cliente_email, items):
        """
        items: lista de dicts: [{"producto_id":1, "cantidad":2}, ...]
        - Calcula total
        - Valida stock
        - Descuenta stock
        - Inserta pedido + items en transacción
        """
        try:
            self.cursor.execute("BEGIN;")

            total = 0.0
            lineas = []

            for it in items:
                pid = int(it["producto_id"])
                qty = int(it["cantidad"])

                self.cursor.execute("SELECT id, precio, stock FROM productos WHERE id=?;", (pid,))
                p = self.cursor.fetchone()
                if not p:
                    raise ValueError(f"Producto {pid} no existe")
                if p["stock"] < qty:
                    raise ValueError(f"Stock insuficiente para producto {pid}")

                precio_unit = float(p["precio"])
                total += precio_unit * qty
                lineas.append((pid, qty, precio_unit))

            self.cursor.execute("""
                INSERT INTO pedidos(cliente_nombre, cliente_email, total)
                VALUES(?,?,?);
            """, (cliente_nombre.strip(), cliente_email, total))
            pedido_id = self.cursor.lastrowid

            for (pid, qty, precio_unit) in lineas:
                self.cursor.execute("""
                    INSERT INTO pedido_items(pedido_id, producto_id, cantidad, precio_unit)
                    VALUES(?,?,?,?);
                """, (pedido_id, pid, qty, precio_unit))

                # descontar stock
                self.cursor.execute("""
                    UPDATE productos SET stock = stock - ?
                    WHERE id=?;
                """, (qty, pid))

            self.con.commit()
            return pedido_id

        except Exception as e:
            self.con.rollback()
            print(f"[DB] Error creando pedido: {e}")
            return None

    def semilla_productos(self):
        """Crea productos de ejemplo si la tabla está vacía."""
        try:
            self.cursor.execute("SELECT COUNT(*) as c FROM productos;")
            c = self.cursor.fetchone()["c"]
            if c == 0:
                self.crear_producto("Playera", "Playera 100% algodón", 199.0, 20)
                self.crear_producto("Taza", "Taza cerámica 350ml", 129.0, 15)
                self.crear_producto("Sticker Pack", "Paquete de 10 stickers", 59.0, 50)
        except Error as e:
            print(f"[DB] Error semilla: {e}")
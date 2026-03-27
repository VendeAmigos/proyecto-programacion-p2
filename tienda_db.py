# tienda_db.py
import os
import sqlite3
from sqlite3 import Error
from werkzeug.security import generate_password_hash, check_password_hash
import json


class BaseDatosTienda:
    def __init__(self, ruta="./", bd="tienda.sqlite3"):
        self.bd_path = os.path.join(ruta, bd)
        self.con = None
        self.cursor = None
        self.conectar()
        self.crear_tablas()

    def conectar(self):
        try:
            self.con = sqlite3.connect(self.bd_path, check_same_thread=False)
            self.con.row_factory = sqlite3.Row
            self.cursor = self.con.cursor()
            self.cursor.execute("PRAGMA foreign_keys = ON;")
            self.con.commit()
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
            # Tabla de Usuarios
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS usuarios(
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nombre TEXT NOT NULL,
                    email TEXT NOT NULL UNIQUE,
                    password TEXT NOT NULL,
                    rol TEXT NOT NULL DEFAULT 'cliente' CHECK(rol IN ('cliente', 'admin')),
                    creado_en TEXT NOT NULL DEFAULT (datetime('now'))
                );
            """)

            # Tabla de Productos
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS productos(
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nombre TEXT NOT NULL,
                    descripcion TEXT,
                    imagen_url TEXT,
                    precio REAL NOT NULL CHECK(precio >= 0),
                    stock INTEGER NOT NULL DEFAULT 0 CHECK(stock >= 0),
                    destacado INTEGER DEFAULT 0,
                    creado_en TEXT NOT NULL DEFAULT (datetime('now'))
                );
            """)

            # Tabla de Carrito Persistente
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS carrito_items(
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    usuario_id INTEGER NOT NULL,
                    producto_id INTEGER NOT NULL,
                    cantidad INTEGER NOT NULL CHECK(cantidad > 0),
                    agregado_en TEXT NOT NULL DEFAULT (datetime('now')),
                    FOREIGN KEY(usuario_id) REFERENCES usuarios(id)
                        ON DELETE CASCADE ON UPDATE CASCADE,
                    FOREIGN KEY(producto_id) REFERENCES productos(id)
                        ON DELETE CASCADE ON UPDATE CASCADE,
                    UNIQUE(usuario_id, producto_id)
                );
            """)

            # Tabla de Pedidos
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS pedidos(
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    usuario_id INTEGER,
                    cliente_nombre TEXT NOT NULL,
                    cliente_email TEXT,
                    total REAL NOT NULL CHECK(total >= 0),
                    creado_en TEXT NOT NULL DEFAULT (datetime('now')),
                    FOREIGN KEY(usuario_id) REFERENCES usuarios(id)
                        ON DELETE SET NULL ON UPDATE CASCADE
                );
            """)

            # Tabla de Items del Pedido
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS pedido_items(
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    pedido_id INTEGER NOT NULL,
                    producto_id INTEGER NOT NULL,
                    cantidad INTEGER NOT NULL CHECK(cantidad > 0),
                    precio_unit REAL NOT NULL CHECK(precio_unit >= 0),
                    FOREIGN KEY(pedido_id) REFERENCES pedidos(id)
                        ON DELETE CASCADE ON UPDATE CASCADE,
                    FOREIGN KEY(producto_id) REFERENCES productos(id)
                        ON DELETE RESTRICT ON UPDATE CASCADE
                );
            """)

            self.con.commit()
        except Error as e:
            print(f"[DB] Error creando tablas: {e}")

    # ========== AUTENTICACIÓN DE USUARIOS ==========
    def registrar_usuario(self, nombre, email, password):
        """Registra un nuevo usuario con contraseña hasheada."""
        try:
            password_hash = generate_password_hash(password)
            self.cursor.execute("""
                INSERT INTO usuarios(nombre, email, password)
                VALUES(?, ?, ?);
            """, (nombre.strip(), email.strip().lower(), password_hash))
            self.con.commit()
            return self.cursor.lastrowid
        except sqlite3.IntegrityError:
            print(f"[DB] Email ya registrado: {email}")
            return None
        except Error as e:
            print(f"[DB] Error registrando usuario: {e}")
            return None

    def obtener_usuario_por_email(self, email):
        """Obtiene usuario por email."""
        try:
            self.cursor.execute("""
                SELECT * FROM usuarios WHERE email=?;
            """, (email.strip().lower(),))
            return self.cursor.fetchone()
        except Error as e:
            print(f"[DB] Error obteniendo usuario: {e}")
            return None

    def obtener_usuario_por_id(self, usuario_id):
        """Obtiene usuario por ID."""
        try:
            self.cursor.execute("""
                SELECT * FROM usuarios WHERE id=?;
            """, (usuario_id,))
            return self.cursor.fetchone()
        except Error as e:
            print(f"[DB] Error obteniendo usuario: {e}")
            return None

    def verificar_contraseña(self, usuario_id, password):
        """Verifica contraseña del usuario."""
        try:
            self.cursor.execute("""
                SELECT password FROM usuarios WHERE id=?;
            """, (usuario_id,))
            user = self.cursor.fetchone()
            if user:
                return check_password_hash(user["password"], password)
            return False
        except Error as e:
            print(f"[DB] Error verificando contraseña: {e}")
            return False

    def autenticar_usuario(self, email, password):
        """Autentica usuario y retorna ID si es exitoso."""
        user = self.obtener_usuario_por_email(email)
        if user and check_password_hash(user["password"], password):
            return user["id"]
        return None

    # ========== CARRITO PERSISTENTE ==========
    def agregar_a_carrito_persistente(self, usuario_id, producto_id, cantidad=1):
        """Agrega o actualiza cantidad en carrito persistente."""
        try:
            # Verificar que producto existe
            self.cursor.execute("SELECT id FROM productos WHERE id=?;", (producto_id,))
            if not self.cursor.fetchone():
                return False

            self.cursor.execute("""
                INSERT INTO carrito_items(usuario_id, producto_id, cantidad)
                VALUES(?, ?, ?)
                ON CONFLICT(usuario_id, producto_id)
                DO UPDATE SET cantidad = cantidad + ?;
            """, (usuario_id, producto_id, cantidad, cantidad))
            self.con.commit()
            return True
        except Error as e:
            print(f"[DB] Error agregando a carrito: {e}")
            return False

    def obtener_carrito(self, usuario_id):
        """Obtiene carrito persistente del usuario."""
        try:
            self.cursor.execute("""
                SELECT c.id, c.producto_id, c.cantidad, p.nombre, p.precio, p.stock
                FROM carrito_items c
                JOIN productos p ON c.producto_id = p.id
                WHERE c.usuario_id = ?
                ORDER BY c.agregado_en DESC;
            """, (usuario_id,))
            return self.cursor.fetchall()
        except Error as e:
            print(f"[DB] Error obteniendo carrito: {e}")
            return []

    def obtener_cantidad_carrito(self, usuario_id):
        """Obtiene cantidad total de items en carrito."""
        try:
            self.cursor.execute("""
                SELECT SUM(cantidad) as total FROM carrito_items WHERE usuario_id=?;
            """, (usuario_id,))
            result = self.cursor.fetchone()
            return result["total"] or 0 if result else 0
        except Error as e:
            print(f"[DB] Error obteniendo cantidad carrito: {e}")
            return 0

    def quitar_del_carrito(self, usuario_id, producto_id):
        """Elimina un producto del carrito."""
        try:
            self.cursor.execute("""
                DELETE FROM carrito_items WHERE usuario_id=? AND producto_id=?;
            """, (usuario_id, producto_id))
            self.con.commit()
            return self.cursor.rowcount > 0
        except Error as e:
            print(f"[DB] Error quitando del carrito: {e}")
            return False

    def vaciar_carrito(self, usuario_id):
        """Vacía todo el carrito del usuario."""
        try:
            self.cursor.execute("""
                DELETE FROM carrito_items WHERE usuario_id=?;
            """, (usuario_id,))
            self.con.commit()
            return True
        except Error as e:
            print(f"[DB] Error vaciando carrito: {e}")
            return False

    def actualizar_cantidad_carrito(self, usuario_id, producto_id, cantidad):
        """Actualiza cantidad de un producto en el carrito."""
        try:
            if cantidad <= 0:
                return self.quitar_del_carrito(usuario_id, producto_id)
            
            self.cursor.execute("""
                UPDATE carrito_items SET cantidad=?
                WHERE usuario_id=? AND producto_id=?;
            """, (cantidad, usuario_id, producto_id))
            self.con.commit()
            return self.cursor.rowcount > 0
        except Error as e:
            print(f"[DB] Error actualizando carrito: {e}")
            return False

    # ========== PRODUCTOS (CRUD) ==========
    def crear_producto(self, nombre, descripcion, precio, stock, imagen_url=None, destacado=0):
        """Crea un nuevo producto."""
        try:
            self.cursor.execute("""
                INSERT INTO productos(nombre, descripcion, precio, stock, imagen_url, destacado)
                VALUES(?, ?, ?, ?, ?, ?);
            """, (nombre.strip(), descripcion or "", float(precio), int(stock), imagen_url, int(destacado)))
            self.con.commit()
            return self.cursor.lastrowid
        except Error as e:
            print(f"[DB] No se pudo crear producto: {e}")
            return None

    def actualizar_producto(self, producto_id, nombre=None, descripcion=None, precio=None, stock=None, imagen_url=None, destacado=None):
        """Actualiza un producto existente."""
        try:
            campos = []
            valores = []
            
            if nombre is not None:
                campos.append("nombre = ?")
                valores.append(nombre.strip())
            if descripcion is not None:
                campos.append("descripcion = ?")
                valores.append(descripcion)
            if precio is not None:
                campos.append("precio = ?")
                valores.append(float(precio))
            if stock is not None:
                campos.append("stock = ?")
                valores.append(int(stock))
            if imagen_url is not None:
                campos.append("imagen_url = ?")
                valores.append(imagen_url)
            if destacado is not None:
                campos.append("destacado = ?")
                valores.append(int(destacado))
            
            if not campos:
                return False
            
            valores.append(producto_id)
            query = f"UPDATE productos SET {', '.join(campos)} WHERE id = ?;"
            self.cursor.execute(query, valores)
            self.con.commit()
            return self.cursor.rowcount > 0
        except Error as e:
            print(f"[DB] Error actualizando producto: {e}")
            return False

    def eliminar_producto(self, producto_id):
        """Elimina un producto."""
        try:
            self.cursor.execute("DELETE FROM productos WHERE id=?;", (producto_id,))
            self.con.commit()
            return self.cursor.rowcount > 0
        except Error as e:
            print(f"[DB] Error eliminando producto: {e}")
            return False

    def listar_productos(self):
        """Lista todos los productos ordenados."""
        try:
            self.cursor.execute("""
                SELECT * FROM productos ORDER BY destacado DESC, creado_en DESC;
            """)
            return self.cursor.fetchall()
        except Error as e:
            print(f"[DB] Error listando productos: {e}")
            return []

    def obtener_producto(self, producto_id):
        """Obtiene un producto por ID."""
        try:
            self.cursor.execute("SELECT * FROM productos WHERE id=?;", (producto_id,))
            return self.cursor.fetchone()
        except Error as e:
            print(f"[DB] Error obteniendo producto: {e}")
            return None

    def obtener_productos_destacados(self, limite=3):
        """Obtiene productos destacados."""
        try:
            self.cursor.execute("""
                SELECT * FROM productos WHERE destacado = 1
                ORDER BY creado_en DESC LIMIT ?;
            """, (limite,))
            return self.cursor.fetchall()
        except Error as e:
            print(f"[DB] Error obteniendo destacados: {e}")
            return []

    def actualizar_stock(self, producto_id, nuevo_stock):
        """Actualiza stock de un producto."""
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

    # ========== PEDIDOS ==========
    def crear_pedido(self, cliente_nombre, cliente_email, items, usuario_id=None):
        """
        Crea un pedido desde items del carrito.
        items: lista de dicts: [{"producto_id":1, "cantidad":2}, ...]
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
                INSERT INTO pedidos(usuario_id, cliente_nombre, cliente_email, total)
                VALUES(?, ?, ?, ?);
            """, (usuario_id, cliente_nombre.strip(), cliente_email, total))
            pedido_id = self.cursor.lastrowid

            for (pid, qty, precio_unit) in lineas:
                self.cursor.execute("""
                    INSERT INTO pedido_items(pedido_id, producto_id, cantidad, precio_unit)
                    VALUES(?, ?, ?, ?);
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

    def obtener_pedidos_usuario(self, usuario_id):
        """Obtiene historial de pedidos del usuario."""
        try:
            self.cursor.execute("""
                SELECT * FROM pedidos WHERE usuario_id=?
                ORDER BY creado_en DESC;
            """, (usuario_id,))
            return self.cursor.fetchall()
        except Error as e:
            print(f"[DB] Error obteniendo pedidos: {e}")
            return []

    # ========== DATOS DE PRUEBA ==========
    def semilla_admin(self):
        """Crea usuario admin de prueba."""
        try:
            admin = self.obtener_usuario_por_email("admin@smartwatches.com")
            if not admin:
                self.registrar_usuario("Admin", "admin@smartwatches.com", "admin123")
                # Actualizar rol a admin
                self.cursor.execute("""
                    UPDATE usuarios SET rol='admin' WHERE email='admin@smartwatches.com';
                """)
                self.con.commit()
                print("[DB] Usuario admin creado: admin@smartwatches.com / admin123")
        except Error as e:
            print(f"[DB] Error creando admin: {e}")

    def semilla_productos(self):
        """Crea smartwatches de ejemplo si la tabla está vacía."""
        try:
            self.cursor.execute("SELECT COUNT(*) as c FROM productos;")
            c = self.cursor.fetchone()["c"]
            if c == 0:
                # URLs de imágenes para cada producto
                image_urls = [
                    "https://http2.mlstatic.com/D_NQ_NP_817706-MLM74543623823_022024-O-smartwatch-at7-pro-max-carga-inalambrica-mejor-t500-m26-x7.webp",
                    "https://store.storeimages.cdn-apple.com/1/as-images.apple.com/is/watch-card-40-s11-202509_GEO_MX_FMT_WHH?wid=508&hei=472&fmt=jpeg&qlt=90&.v=RGt6QnVpU0piVDZnRHZnWmNNbHB2Nk9kcWgwd3VFL2F4Y3hZVmFwa0FxZnNPK21NTmFtSkpWQ3ZBMFB1WTlMTzltWDc4aXJHcmduU0dwUHg2UmFtWXoyTkNERHVqSk12b05selRrakVBT3NWZUtpNXhGOEpLaDNwa2dXbHBEK3A",
                    "https://resources.claroshop.com/medios-plazavip/t1/1737579463ELEGANCEROSAjpg",
                    "https://http2.mlstatic.com/D_Q_NP_874575-MLA99481317928_112025-O.webp",
                    "https://http2.mlstatic.com/D_Q_NP_920034-MLA99380214926_112025-O.webp",
                    "https://http2.mlstatic.com/D_NQ_NP_954727-MLA99968105041_112025-O.webp",
                    "https://target.scene7.com/is/image/Target/GUEST_6fb68107-c502-47d5-9e21-d45532692be1?wid=300&hei=300&fmt=pjpeg",
                    "https://http2.mlstatic.com/D_Q_NP_874575-MLA99481317928_112025-O.webp"
                ]
                
                # Productos smartwatches inspirados en Apple Watch
                self.crear_producto(
                    "Pro Max Smartwatch",
                    "Pantalla AMOLED de 1.9\", resistente al agua 5ATM, batería 7 días, monitoreo cardíaco avanzado",
                    2499.0, 15, image_urls[0], destacado=1
                )
                self.crear_producto(
                    "Ultra Fitness Watch",
                    "Diseño deportivo, GPS integrado, memoria 32GB, 50+ modos deportivos",
                    1799.0, 20, image_urls[1], destacado=1
                )
                self.crear_producto(
                    "Classic Elegance",
                    "Esfera redonda AMOLED, correas intercambiables, batería 10 días",
                    1599.0, 18, image_urls[2], destacado=1
                )
                self.crear_producto(
                    "Youth Smart",
                    "Perfecto para menores, pantalla colorida, juegos educativos, control parental",
                    899.0, 25, image_urls[3], destacado=0
                )
                self.crear_producto(
                    "Business Pro",
                    "Sincronización Outlook/Gmail, NFC para pagos, diseño minimalista profesional",
                    2099.0, 12, image_urls[4], destacado=0
                )
                self.crear_producto(
                    "Health Monitor Elite",
                    "Monitoreo de temperatura corporal, SPO2, estrés, ciclo menstrual",
                    2199.0, 10, image_urls[5], destacado=0
                )
                self.crear_producto(
                    "Budget Starter",
                    "Entrada de gama, pantalla IPS, batería 3 días, perfecto para principiantes",
                    599.0, 30, image_urls[6], destacado=0
                )
                self.crear_producto(
                    "Studio Edition",
                    "Edición limitada diseñador, correa tejida exclusiva, grabados personalizados",
                    2899.0, 5, image_urls[7], destacado=0
                )
                print("[DB] 8 smartwatches de ejemplo creados con imágenes")
        except Error as e:
            print(f"[DB] Error creando semilla: {e}")
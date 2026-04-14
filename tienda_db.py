# ============================================================
# tienda_db.py — Capa de acceso a datos (SQLite)
# ============================================================
#
# Este archivo es el ÚNICO que habla directamente con la base de
# datos. Ninguna ruta de app.py debe escribir SQL; en su lugar
# llama a los métodos de esta clase.
#
# ¿Qué es SQLite?
#   Una base de datos guardada en un solo archivo (.sqlite3).
#   No necesita instalación de servidor; perfecta para proyectos
#   pequeños y medianos como esta tienda.
#
# Estructura de tablas:
#   productos   → catálogo de audífonos (nombre, precio, stock, imagen)
#   usuarios    → cuentas de clientes y administradores
#   pedidos     → cada compra realizada (cabecera)
#   pedido_items→ productos dentro de cada pedido (detalle)
#   visitas     → registro de páginas visitadas (analítica)
#   avisos      → mensajes del admin visibles en la tienda
#
# Flujo al arrancar la app:
#   1. Se crea la instancia → abre conexión al archivo .sqlite3
#   2. crear_tablas() → genera tablas si no existen
#   3. semilla_inicial() → inserta admin + productos de ejemplo
#      si la BD está vacía (solo ocurre la primera vez)
# ============================================================

import os
import sqlite3
from datetime import date


class BaseDatosTienda:
    """
    Clase única de acceso a datos.
    Recibe:
        ruta — directorio donde vive el archivo .sqlite3
        bd   — nombre del archivo de base de datos
    """

    # ----------------------------------------------------------
    # Conexión
    # ----------------------------------------------------------

    def __init__(self, ruta="./", bd="tienda.sqlite3"):
        """
        Abre la conexión y garantiza que las tablas existan.
        """
        self.bd_path = os.path.join(ruta, bd)
        self.con = sqlite3.connect(self.bd_path, check_same_thread=False)
        self.con.row_factory = sqlite3.Row          # permite acceso por nombre de columna
        self.con.execute("PRAGMA foreign_keys = ON;")
        self.crear_tablas()
        self._migrar_estado_pedido()  # agrega columna 'estado' si no existe

    def cerrar(self):
        """Cierra la conexión de forma segura."""
        if self.con:
            self.con.close()

    # ----------------------------------------------------------
    # Creación de tablas + migraciones
    # ----------------------------------------------------------

    def _migrar_estado_pedido(self):
        """
        Migración segura: agrega la columna 'estado' a la tabla 'pedidos'
        si todavía no existe (la BD puede ser anterior a esta feature).
        SQLite no permite CREATE TABLE IF NOT EXISTS para columnas nuevas,
        por eso usamos ALTER TABLE dentro de un try/except.
        Valores posibles: 'Esperando pago' | 'En proceso de envío' | 'Entregado' | 'Cancelado'
        """
        try:
            self.con.execute(
                "ALTER TABLE pedidos ADD COLUMN estado TEXT DEFAULT 'Esperando pago'"
            )
            self.con.commit()
        except sqlite3.OperationalError:
            # La columna ya existe — no hacer nada
            pass


    def crear_tablas(self):
        """
        Crea todas las tablas necesarias si no existen.
        Se ejecuta una sola vez al iniciar la aplicación.
        """
        self.con.executescript("""
            CREATE TABLE IF NOT EXISTS productos (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre      TEXT    NOT NULL,
                descripcion TEXT,
                precio      REAL    NOT NULL,
                stock       INTEGER NOT NULL DEFAULT 0,
                imagen      TEXT
            );

            CREATE TABLE IF NOT EXISTS usuarios (
                id            INTEGER PRIMARY KEY AUTOINCREMENT,
                username      TEXT    NOT NULL UNIQUE,
                password_hash TEXT    NOT NULL,
                es_admin      INTEGER DEFAULT 0
            );

            CREATE TABLE IF NOT EXISTS pedidos (
                id              INTEGER  PRIMARY KEY AUTOINCREMENT,
                cliente_nombre  TEXT     NOT NULL,
                cliente_email   TEXT,
                total           REAL     NOT NULL DEFAULT 0,
                creado_en       DATETIME DEFAULT CURRENT_TIMESTAMP
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
                ruta       TEXT     NOT NULL,
                fecha      DATETIME DEFAULT CURRENT_TIMESTAMP,
                user_agent TEXT
            );

            CREATE TABLE IF NOT EXISTS avisos (
                id        INTEGER  PRIMARY KEY AUTOINCREMENT,
                titulo    TEXT     NOT NULL,
                mensaje   TEXT     NOT NULL,
                creado_en DATETIME DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS banners (
                id        INTEGER PRIMARY KEY AUTOINCREMENT,
                titulo    TEXT    NOT NULL DEFAULT '',
                subtitulo TEXT    NOT NULL DEFAULT '',
                imagen    TEXT    NOT NULL DEFAULT '',
                activo    INTEGER NOT NULL DEFAULT 1
            );
        """)
        self.semilla_inicial()

    # ----------------------------------------------------------
    # Datos de ejemplo (seed)
    # ----------------------------------------------------------

    def semilla_inicial(self):
        """
        Inserta un usuario admin y productos de ejemplo
        solo si la BD está vacía. Evita duplicados.
        """
        # Admin por defecto (usuario: admin / contraseña: admin123)
        if not self.obtener_usuario("admin"):
            from werkzeug.security import generate_password_hash
            self.crear_usuario("admin", generate_password_hash("admin123"), es_admin=1)

        # Productos de ejemplo — solo si no hay ninguno
        if not self.listar_productos():
            catalogo = [
                ("Sony WH-1000XM5",
                 "Cancelación de ruido líder en la industria, sonido premium.",
                 398.00, 20, "/static/images/sony-wh1000xm5.jpg"),

                ("Apple AirPods Max",
                 "Audio de alta fidelidad, diseño en acero inoxidable.",
                 549.00, 15, "/static/images/airpods-max.jpg"),

                ("Bose QuietComfort 45",
                 "Comodidad icónica y sonido nítido.",
                 329.00, 30, "/static/images/bose-qc45.jpg"),

                ("Sennheiser Momentum 4",
                 "Batería de 60 horas y sonido Sennheiser característico.",
                 349.00, 25, "/static/images/sennheiser-momentum4.jpg"),

                ("Audio-Technica ATH-M50x",
                 "Monitor de estudio profesional aclamado por críticos.",
                 169.00, 50, "/static/images/ath-m50x.jpg"),

                ("Beyerdynamic DT 770 Pro",
                 "Referencia cerrada para control y monitoreo.",
                 159.00, 40, "/static/images/beyerdynamic-dt770.jpg"),

                ("Shure AONIC 50",
                 "Calidad de estudio inalámbrica con cancelación de ruido.",
                 299.00, 35, "/static/images/shure-aonic50.jpg"),

                ("Bang & Olufsen Beoplay HX",
                 "Materiales de lujo y sonido equilibrado.",
                 499.00, 10, "/static/images/beoplay-hx.jpg"),

                ("AKG K702",
                 "Auriculares abiertos de referencia para mezcla y masterización.",
                 249.00, 20, "/static/images/akg-k702.jpg"),

                ("HiFiMan Sundara",
                 "Auriculares magnéticos planares para audiófilos.",
                 299.00, 15, "/static/images/hifiman-sundara.jpg"),
            ]
            for nombre, desc, precio, stock, img in catalogo:
                self.crear_producto(nombre, desc, precio, stock, img)

    # ==========================================================
    #  USUARIOS
    # ==========================================================

    def crear_usuario(self, username, password_hash, es_admin=0):
        """
        Registra un nuevo usuario.
        Recibe: username (str), password_hash (str), es_admin (0 o 1).
        Devuelve: True si se creó, False si hubo error (e.g. duplicado).
        """
        try:
            self.con.execute(
                "INSERT INTO usuarios (username, password_hash, es_admin) VALUES (?, ?, ?)",
                (username, password_hash, es_admin),
            )
            self.con.commit()
            return True
        except sqlite3.Error:
            return False

    def obtener_usuario(self, username):
        """
        Busca un usuario por nombre.
        Recibe: username (str).
        Devuelve: Row del usuario o None.
        """
        cur = self.con.execute("SELECT * FROM usuarios WHERE username = ?", (username,))
        return cur.fetchone()

    def obtener_usuario_por_id(self, uid):
        """
        Busca un usuario por su ID numérico.
        Recibe: uid (int).
        Devuelve: Row del usuario o None.
        """
        cur = self.con.execute("SELECT * FROM usuarios WHERE id = ?", (uid,))
        return cur.fetchone()

    # ==========================================================
    #  PRODUCTOS
    # ==========================================================

    def crear_producto(self, nombre, descripcion, precio, stock, imagen=None):
        """
        Inserta un producto nuevo.
        Recibe: datos del producto.
        Devuelve: el ID del nuevo producto, o None si falla.
        """
        try:
            cur = self.con.execute(
                "INSERT INTO productos (nombre, descripcion, precio, stock, imagen) VALUES (?, ?, ?, ?, ?)",
                (nombre, descripcion, precio, stock, imagen),
            )
            self.con.commit()
            return cur.lastrowid
        except sqlite3.Error as e:
            print(f"[DB] Error al crear producto: {e}")
            return None

    def listar_productos(self):
        """
        Devuelve todos los productos existentes.
        No recibe parámetros.
        Devuelve: lista de Rows.
        """
        cur = self.con.execute("SELECT * FROM productos")
        return cur.fetchall()

    def obtener_producto(self, pid):
        """
        Obtiene un producto por ID.
        Recibe: pid (int).
        Devuelve: Row del producto o None.
        """
        cur = self.con.execute("SELECT * FROM productos WHERE id = ?", (pid,))
        return cur.fetchone()

    def actualizar_producto(self, pid, precio, stock, imagen):
        """
        Actualiza precio, stock e imagen de un producto.
        Recibe: pid (int), precio (float), stock (int), imagen (str).
        Devuelve: True/False.
        """
        try:
            cur = self.con.execute(
                "UPDATE productos SET precio = ?, stock = ?, imagen = ? WHERE id = ?",
                (precio, stock, imagen, pid),
            )
            self.con.commit()
            return cur.rowcount > 0
        except sqlite3.Error:
            return False

    def eliminar_producto(self, pid):
        """
        Borra un producto de la tienda de forma permanente.
        Recibe: pid (int) — ID del producto a eliminar.
        Devuelve: True si se eliminó algo, False si no existía o hubo error.
        Nota: los pedidos que ya incluían este producto no se borran
        (pedido_items guarda precio_unit como copia, por eso es seguro).
        """
        try:
            cur = self.con.execute("DELETE FROM productos WHERE id = ?", (pid,))
            self.con.commit()
            return cur.rowcount > 0
        except sqlite3.Error:
            return False

    def limpiar_imagen_productos(self, ruta_imagen):
        """
        Se llama automáticamente cuando el admin ELIMINA una imagen
        del servidor desde el panel de control.

        ¿Qué hace?
          Busca todos los productos cuyo campo 'imagen' coincida con
          la ruta borrada y les pone la imagen en cadena vacía (""),
          así la tienda no mostrará una imagen rota.

        Recibe: ruta_imagen (str) — p.ej. "/static/images/sony.jpg"
        Devuelve: número de productos actualizados (int).
        """
        try:
            cur = self.con.execute(
                "UPDATE productos SET imagen = '' WHERE imagen = ?",
                (ruta_imagen,),
            )
            self.con.commit()
            return cur.rowcount   # cuántos productos se limpiaron
        except sqlite3.Error as e:
            print(f"[DB] Error al limpiar referencia de imagen: {e}")
            return 0

    # ==========================================================
    #  PEDIDOS (Checkout)
    # ==========================================================

    def crear_pedido(self, cliente_nombre, cliente_email, items):
        """
        Crea un pedido completo dentro de una transacción.
        Recibe:
            cliente_nombre (str)
            cliente_email  (str)
            items — lista de dicts: [{"producto_id": int, "cantidad": int}, ...]
        Devuelve: ID del pedido creado, o None si falla (stock insuficiente, etc.).
        Flujo:
            1. Valida stock de cada producto.
            2. Calcula el total.
            3. Inserta pedido + líneas.
            4. Descuenta stock.
            5. Hace commit si todo fue bien; rollback si no.
        """
        try:
            cur = self.con.cursor()
            cur.execute("BEGIN;")
            total = 0.0
            lineas = []  # (producto_id, cantidad, precio_unitario)

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

            # Insertar cabecera del pedido
            cur.execute(
                "INSERT INTO pedidos (cliente_nombre, cliente_email, total) VALUES (?, ?, ?)",
                (cliente_nombre.strip(), cliente_email, total),
            )
            pedido_id = cur.lastrowid

            # Insertar líneas y descontar stock
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
        """
        Calcula el total de ventas del día actual.
        No recibe parámetros.
        Devuelve: dict con 'total' (float) y 'cantidad_pedidos' (int).
        """
        hoy = date.today().isoformat()  # formato YYYY-MM-DD
        cur = self.con.execute(
            "SELECT COUNT(*) AS cantidad, COALESCE(SUM(total), 0) AS total "
            "FROM pedidos WHERE DATE(creado_en) = ?",
            (hoy,),
        )
        row = cur.fetchone()
        return {"total": row["total"], "cantidad_pedidos": row["cantidad"]}

    def listar_pedidos(self):
        """
        Devuelve todos los pedidos ordenados del más reciente al más antiguo.
        Incluye la columna 'estado' para mostrar la etiqueta en el dashboard.
        Devuelve: lista de Rows con columnas:
          id, cliente_nombre, cliente_email, total, creado_en, estado
        """
        cur = self.con.execute(
            "SELECT * FROM pedidos ORDER BY creado_en DESC"
        )
        return cur.fetchall()

    def actualizar_estado_pedido(self, pedido_id, estado):
        """
        Cambia la etiqueta de estado de un pedido.
        Se llama desde el dashboard cuando el admin selecciona un estado
        en el desplegable y hace clic en 'Actualizar'.

        Recibe:
          pedido_id (int) — ID del pedido a actualizar
          estado    (str) — nuevo estado, debe ser uno de:
                           'Esperando pago' | 'En proceso de envío' |
                           'Entregado'      | 'Cancelado'
        Devuelve: True si se actualizó, False si hubo error.
        """
        ESTADOS_VALIDOS = {
            "Esperando pago",
            "En proceso de envío",
            "Entregado",
            "Cancelado",
        }
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



    # ==========================================================
    #  AVISOS
    # ==========================================================

    def crear_aviso(self, titulo, mensaje):
        """
        Guarda un aviso nuevo creado por el administrador.
        Recibe: titulo (str), mensaje (str).
        Devuelve: ID del aviso creado o None.
        """
        try:
            cur = self.con.execute(
                "INSERT INTO avisos (titulo, mensaje) VALUES (?, ?)",
                (titulo, mensaje),
            )
            self.con.commit()
            return cur.lastrowid
        except sqlite3.Error as e:
            print(f"[DB] Error al crear aviso: {e}")
            return None

    def listar_avisos(self):
        """
        Devuelve todos los avisos ordenados por más recientes primero.
        Devuelve: lista de Rows.
        """
        cur = self.con.execute("SELECT * FROM avisos ORDER BY creado_en DESC")
        return cur.fetchall()

    def eliminar_aviso(self, aviso_id):
        """
        Elimina un aviso por ID.
        Recibe: aviso_id (int).
        Devuelve: True/False.
        """
        try:
            cur = self.con.execute("DELETE FROM avisos WHERE id = ?", (aviso_id,))
            self.con.commit()
            return cur.rowcount > 0
        except sqlite3.Error:
            return False

    # ==========================================================
    #  BANNERS
    # ==========================================================

    def obtener_banner_activo(self):
        cur = self.con.execute("SELECT * FROM banners WHERE activo = 1 LIMIT 1")
        return cur.fetchone()

    def listar_banners(self):
        cur = self.con.execute("SELECT * FROM banners ORDER BY id DESC")
        return cur.fetchall()

    def crear_banner(self, titulo, subtitulo, imagen):
        try:
            self.con.execute(
                "INSERT INTO banners (titulo, subtitulo, imagen) VALUES (?, ?, ?)",
                (titulo, subtitulo, imagen),
            )
            self.con.commit()
            return True
        except sqlite3.Error:
            return False

    def actualizar_banner(self, banner_id, titulo, subtitulo, imagen):
        try:
            cur = self.con.execute(
                "UPDATE banners SET titulo = ?, subtitulo = ?, imagen = ? WHERE id = ?",
                (titulo, subtitulo, imagen, banner_id),
            )
            self.con.commit()
            return cur.rowcount > 0
        except sqlite3.Error:
            return False

    def activar_banner(self, banner_id):
        try:
            self.con.execute("UPDATE banners SET activo = 0")
            self.con.execute("UPDATE banners SET activo = 1 WHERE id = ?", (banner_id,))
            self.con.commit()
            return True
        except sqlite3.Error:
            return False

    def eliminar_banner(self, banner_id):
        try:
            cur = self.con.execute("DELETE FROM banners WHERE id = ?", (banner_id,))
            self.con.commit()
            return cur.rowcount > 0
        except sqlite3.Error:
            return False

    # ==========================================================
    #  ANALÍTICA (Visitas)
    # ==========================================================

    def registrar_visita(self, ruta, user_agent):
        """
        Registra una visita a cualquier ruta del sitio.
        Recibe: ruta (str), user_agent (str).
        Se ejecuta automáticamente en cada request (middleware).
        """
        try:
            self.con.execute(
                "INSERT INTO visitas (ruta, user_agent) VALUES (?, ?)",
                (ruta, user_agent),
            )
            self.con.commit()
        except sqlite3.Error:
            pass

    def obtener_visitas_por_ruta(self):
        """
        Agrupa las visitas por ruta y las ordena de mayor a menor.
        Devuelve: lista de Rows con columnas 'ruta' y 'conteo'.
        """
        cur = self.con.execute(
            "SELECT ruta, COUNT(*) AS conteo FROM visitas GROUP BY ruta ORDER BY conteo DESC"
        )
        return cur.fetchall()
# ============================================================
# app.py — Archivo principal de la aplicación Flask
# ============================================================
#
# ¿Qué es Flask?
#   Un framework web minimalista de Python. Recibe peticiones
#   HTTP (GET, POST) del navegador y devuelve páginas HTML.
#
# Este archivo define TODAS las rutas (URLs) de la tienda.
# No escribe SQL directamente; para eso llama a tienda_db.py.
#
# Secciones:
#   MIDDLEWARES  → código que corre antes/después de cada request
#   DECORADORES  → login_requerido / admin_requerido
#   PÚBLICAS     → tienda principal (/), detalle de producto
#   AUTH         → registro, login, logout
#   CARRITO      → agregar, quitar, checkout
#   IMÁGENES     → subir, eliminar, reemplazar imágenes
#   ADMIN        → dashboard, productos, avisos
#   AVISOS API   → endpoint JSON público
# ============================================================

import os
from flask import (
    Flask, render_template, request,
    redirect, url_for, session, flash, g, jsonify,
)
from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug.utils import secure_filename  # convierte nombres peligrosos a nombres seguros
from functools import wraps
from tienda_db import BaseDatosTienda

# ------------------------------------------------------------
# Configuración de imágenes
# IMAGEN_UPLOAD_FOLDER: ruta absoluta a la carpeta donde se
#   guardan las fotos de los productos en el servidor.
# ALLOWED_EXTENSIONS: solo se aceptan estos formatos de imagen.
# ------------------------------------------------------------
IMAGEN_UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), 'static', 'images')
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp', 'avif'}

def allowed_file(filename):
    """
    Revisa que el nombre de archivo tenga una extensión válida.
    Ej: 'foto.jpg' → True  |  'virus.exe' → False
    """
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# ----------------------------------------------------------
# Inicialización
# ----------------------------------------------------------

app = Flask(__name__)
app.secret_key = "clave_super_secreta_para_sesiones"

# Conexión única a la base de datos (se reutiliza en toda la app)
db = BaseDatosTienda(ruta="./", bd="tienda.sqlite3")


# ==========================================================
#  MIDDLEWARES
# ==========================================================

@app.before_request
def cargar_usuario():
    """
    Se ejecuta ANTES de cada petición.
    Qué hace:
        1. Intenta cargar el usuario de la sesión en g.user.
        2. Registra la visita en la tabla de analítica.
    Por qué existe: para que todas las rutas tengan acceso
    al usuario actual sin repetir código.
    """
    g.user = None
    if "user_id" in session:
        g.user = db.obtener_usuario_por_id(session["user_id"])

    # No registrar visitas a archivos estáticos
    if request.path.startswith("/static") or request.path.startswith("/favicon"):
        return

    db.registrar_visita(request.path, request.user_agent.string)


@app.context_processor
def variables_globales():
    """
    Inyecta variables disponibles en TODOS los templates:
        - user:          el objeto del usuario logueado (o None)
        - carrito_count:  cantidad total de artículos en la bolsa
        - avisos:         lista de avisos activos (más recientes primero)
    Por qué existe: evita pasar estas variables manualmente
    en cada render_template.
    """
    carrito = session.get("carrito", {})
    cantidad = sum(carrito.values())
    avisos = db.listar_avisos()
    return dict(user=g.user, carrito_count=cantidad, avisos_globales=avisos)


# ==========================================================
#  DECORADORES DE ACCESO
# ==========================================================

def login_requerido(f):
    """
    Decorador: redirige al login si el usuario no ha iniciado sesión.
    Se aplica a rutas que necesitan autenticación.
    """
    @wraps(f)
    def wrapper(*args, **kwargs):
        if g.user is None:
            flash("Necesitas iniciar sesión.")
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return wrapper


def admin_requerido(f):
    """
    Decorador: redirige al inicio si el usuario no es administrador.
    Se aplica a rutas del panel de control.
    """
    @wraps(f)
    def wrapper(*args, **kwargs):
        if g.user is None or not g.user["es_admin"]:
            flash("Acceso denegado. Se requiere administrador.")
            return redirect(url_for("inicio"))
        return f(*args, **kwargs)
    return wrapper


# ==========================================================
#  RUTAS PÚBLICAS
# ==========================================================

@app.route("/")
def inicio():
    """
    Página principal: muestra el catálogo completo de productos.
    Devuelve: template index.html con la lista de productos.
    """
    productos = db.listar_productos()
    banner = db.obtener_banner_activo()
    return render_template("index.html", productos=productos, banner=banner)


@app.route("/producto/<int:producto_id>")
def producto(producto_id):
    """
    Detalle de un producto individual.
    Recibe: producto_id (int) desde la URL.
    Devuelve: template producto.html o error 404.
    """
    p = db.obtener_producto(producto_id)
    if not p:
        return "Producto no encontrado", 404
    return render_template("producto.html", p=p)


# ==========================================================
#  AVISOS — Endpoint público (GET)
# ==========================================================

@app.route("/avisos")
def obtener_avisos():
    """
    Endpoint público para obtener avisos en formato JSON.
    Qué hace: devuelve todos los avisos ordenados por más recientes.
    Por qué existe: permite que el frontend consuma avisos vía fetch/AJAX.
    Devuelve: JSON con lista de avisos.
    """
    avisos = db.listar_avisos()
    resultado = [
        {
            "id": a["id"],
            "titulo": a["titulo"],
            "mensaje": a["mensaje"],
            "creado_en": a["creado_en"],
        }
        for a in avisos
    ]
    return jsonify(resultado)


# ==========================================================
#  AUTENTICACIÓN
# ==========================================================

@app.route("/registro", methods=["GET", "POST"])
def registro():
    """
    Registro de nuevo usuario.
    GET:  muestra el formulario.
    POST: crea el usuario si no existe y redirige al login.
    """
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        if not username or not password:
            flash("Todos los campos son obligatorios.")
            return redirect(url_for("registro"))

        if db.obtener_usuario(username):
            flash("El usuario ya existe.")
            return redirect(url_for("registro"))

        hashed = generate_password_hash(password)
        if db.crear_usuario(username, hashed):
            flash("Cuenta creada. Ahora inicia sesión.")
            return redirect(url_for("login"))
        else:
            flash("Error en el registro.")

    return render_template("registro.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    """
    Inicio de sesión.
    GET:  muestra el formulario.
    POST: valida credenciales y crea la sesión.
    """
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        user = db.obtener_usuario(username)

        if user and check_password_hash(user["password_hash"], password):
            session["user_id"] = user["id"]
            # Si es admin, ir directo al panel de control
            if user["es_admin"]:
                return redirect(url_for("dashboard"))
            return redirect(url_for("inicio"))
        else:
            flash("Credenciales inválidas.")

    return render_template("login.html")


@app.route("/logout")
def logout():
    """
    Cierra la sesión del usuario y limpia el carrito.
    Redirige al inicio.
    """
    session.pop("user_id", None)
    session.pop("carrito", None)
    return redirect(url_for("inicio"))


# ==========================================================
#  CARRITO DE COMPRAS
# ==========================================================

def obtener_carrito():
    """
    Helper: devuelve el carrito de la sesión (dict).
    Si no existe todavía, lo inicializa vacío.
    Estructura: { "producto_id_str": cantidad_int, ... }
    """
    if "carrito" not in session:
        session["carrito"] = {}
    return session["carrito"]


@app.route("/carrito")
def carrito():
    """
    Muestra el contenido del carrito.
    Calcula subtotales y total para el template.
    """
    cart = obtener_carrito()
    items = []
    total = 0.0

    for pid_str, qty in cart.items():
        p = db.obtener_producto(int(pid_str))
        if not p:
            continue
        subtotal = float(p["precio"]) * int(qty)
        total += subtotal
        items.append({"p": p, "qty": int(qty), "subtotal": subtotal})

    return render_template("carrito.html", items=items, total=total)


@app.route("/carrito/agregar", methods=["POST"])
def carrito_agregar():
    """
    Agrega un producto al carrito (o incrementa cantidad).
    Recibe: producto_id y cantidad desde el formulario.
    Redirige: a la página anterior.
    """
    pid = request.form.get("producto_id", type=int)
    qty = request.form.get("cantidad", type=int, default=1)

    cart = obtener_carrito()
    cart[str(pid)] = int(cart.get(str(pid), 0)) + max(qty, 1)
    session["carrito"] = cart
    flash("Agregado al carrito.")
    return redirect(request.referrer or url_for("inicio"))


@app.route("/carrito/quitar", methods=["POST"])
def carrito_quitar():
    """
    Elimina un producto completo del carrito.
    Recibe: producto_id desde el formulario.
    """
    pid = request.form.get("producto_id", type=int)
    cart = obtener_carrito()
    cart.pop(str(pid), None)
    session["carrito"] = cart
    return redirect(url_for("carrito"))


@app.route("/checkout", methods=["POST"])
def checkout():
    """
    Procesa la compra: crea el pedido y vacía el carrito.
    Requiere sesión de usuario.
    Redirige al carrito si falla o muestra página de éxito.
    """
    if not g.user:
        flash("Debes iniciar sesión para comprar.")
        return redirect(url_for("login"))

    cart = obtener_carrito()
    if not cart:
        return redirect(url_for("inicio"))

    nombre = g.user["username"]
    email = "usuario@tienda.com"  # Placeholder
    items = [{"producto_id": int(pid), "cantidad": int(qty)} for pid, qty in cart.items()]

    pedido_id = db.crear_pedido(nombre, email, items)

    if pedido_id:
        session["carrito"] = {}
        return render_template("checkout_ok.html", pedido_id=pedido_id)
    else:
        flash("Error al procesar pedido. Stock insuficiente.")
        return redirect(url_for("carrito"))


# ==========================================================
#  PANEL DE ADMINISTRACIÓN
# ==========================================================

@app.route("/dashboard")
@admin_requerido
def dashboard():
    """
    Panel de control del administrador.
    Muestra: estadísticas, productos, avisos, ventas del día, imágenes, pedidos.
    """
    visitas = db.obtener_visitas_por_ruta()
    productos = db.listar_productos()
    avisos = db.listar_avisos()
    ventas_hoy = db.ventas_del_dia()
    imagen_subida = request.args.get("imagen_subida")
    imagenes = listar_imagenes()
    # Lista de todos los pedidos para mostrar sus etiquetas de estado
    pedidos = db.listar_pedidos()
    banners = db.listar_banners()
    return render_template(
        "dashboard.html",
        visitas=visitas,
        productos=productos,
        avisos=avisos,
        ventas_hoy=ventas_hoy,
        imagen_subida=imagen_subida,
        imagenes=imagenes,
        pedidos=pedidos,
        banners=banners,
    )


def listar_imagenes():
    """
    Helper: devuelve una lista de dicts con info de cada imagen
    que existe en /static/images/.
    Cada dict: { 'filename': str, 'ruta': str }
    """
    os.makedirs(IMAGEN_UPLOAD_FOLDER, exist_ok=True)
    archivos = []
    for f in sorted(os.listdir(IMAGEN_UPLOAD_FOLDER)):
        if allowed_file(f):
            archivos.append({
                "filename": f,
                "ruta": f"/static/images/{f}"
            })
    return archivos


@app.route("/dashboard/subir-imagen", methods=["POST"])
@admin_requerido
def subir_imagen():
    """
    Recibe un archivo de imagen vía formulario multipart,
    lo valida, lo guarda en /static/images/ y devuelve
    la ruta para usarla en los productos.
    """
    file = request.files.get("imagen")
    if not file or file.filename == "":
        flash("No se seleccionó ningún archivo.")
        return redirect(url_for("dashboard"))

    if not allowed_file(file.filename):
        flash("Tipo de archivo no permitido. Usa PNG, JPG, GIF o WebP.")
        return redirect(url_for("dashboard"))

    filename = secure_filename(file.filename)
    os.makedirs(IMAGEN_UPLOAD_FOLDER, exist_ok=True)
    file.save(os.path.join(IMAGEN_UPLOAD_FOLDER, filename))
    ruta = f"/static/images/{filename}"
    flash(f"Imagen '{filename}' subida correctamente.")
    return redirect(url_for("dashboard", imagen_subida=ruta))


@app.route("/dashboard/eliminar-imagen", methods=["POST"])
@admin_requerido
def eliminar_imagen():
    """
    Elimina una imagen del servidor Y limpia automáticamente
    la referencia en todos los productos que la usaban.

    Flujo:
      1. Valida que el nombre de archivo sea seguro.
      2. Borra el archivo físico de /static/images/.
      3. Actualiza en la BD todos los productos que tenían
         esa imagen → les pone imagen='' (cadena vacía).
         Así los clientes verán "sin imagen" en lugar de
         un enlace roto.
    """
    filename = request.form.get("filename", "")
    if not filename or not allowed_file(filename):
        flash("Nombre de archivo inválido.")
        return redirect(url_for("dashboard"))

    ruta = f"/static/images/{secure_filename(filename)}"
    filepath = os.path.join(IMAGEN_UPLOAD_FOLDER, secure_filename(filename))

    if os.path.isfile(filepath):
        # 1. Borrar el archivo del disco
        os.remove(filepath)
        # 2. Limpiar la referencia en la base de datos
        n = db.limpiar_imagen_productos(ruta)
        msg = f"Imagen '{filename}' eliminada."
        if n:
            msg += f" Se actualizaron {n} producto(s) que la usaban."
        flash(msg)
    else:
        flash(f"No se encontró el archivo '{filename}'.")
    return redirect(url_for("dashboard"))


@app.route("/dashboard/reemplazar-imagen", methods=["POST"])
@admin_requerido
def reemplazar_imagen():
    """
    Reemplaza una imagen existente manteniendo el mismo nombre de archivo.
    Recibe: filename (str) y el nuevo archivo (form multipart).
    Sobreescribe el archivo anterior en /static/images/.
    """
    filename = request.form.get("filename", "")
    file = request.files.get("nueva_imagen")

    if not filename or not allowed_file(filename):
        flash("Nombre de archivo inválido.")
        return redirect(url_for("dashboard"))

    if not file or file.filename == "":
        flash("Debes seleccionar una imagen para reemplazar.")
        return redirect(url_for("dashboard"))

    if not allowed_file(file.filename):
        flash("Tipo de archivo no permitido.")
        return redirect(url_for("dashboard"))

    # Guardar con el nombre ORIGINAL (sobreescribe el anterior)
    dest = os.path.join(IMAGEN_UPLOAD_FOLDER, secure_filename(filename))
    file.save(dest)
    flash(f"Imagen '{filename}' reemplazada correctamente.")
    return redirect(url_for("dashboard"))


# --- Pedidos (Admin) ---

@app.route("/dashboard/pedido/estado", methods=["POST"])
@admin_requerido
def actualizar_estado_pedido_route():
    """
    Actualiza la etiqueta de estado de un pedido.
    Se llama cuando el admin selecciona una etiqueta en el dropdown
    del panel de "Gestión de Pedidos" y hace clic en 'Actualizar'.

    Recibe del formulario:
      pedido_id (int) — ID del pedido
      estado    (str) — nuevo estado seleccionado
    """
    pedido_id = request.form.get("pedido_id", type=int)
    estado = request.form.get("estado", "")

    if not pedido_id or not estado:
        flash("Datos inválidos para actualizar estado.")
        return redirect(url_for("dashboard"))

    if db.actualizar_estado_pedido(pedido_id, estado):
        flash(f"Pedido #{pedido_id} actualizado a '{estado}'.")
    else:
        flash(f"Error al actualizar el pedido #{pedido_id}.")
    return redirect(url_for("dashboard"))


# --- Productos (Admin) ---


@app.route("/dashboard/producto/agregar", methods=["POST"])
@admin_requerido
def agregar_producto():
    """
    Crea un producto nuevo desde el formulario del dashboard.
    Recibe: nombre, descripcion, precio, stock, imagen (texto o archivo).
    Si se sube un archivo de imagen, tiene prioridad sobre la URL de texto.
    Redirige: al dashboard.
    """
    nombre = request.form["nombre"]
    desc = request.form["descripcion"]
    precio = float(request.form["precio"])
    stock = int(request.form["stock"])

    # Prioridad: archivo subido > URL escrita a mano
    file = request.files.get("imagen_file")
    if file and file.filename and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        os.makedirs(IMAGEN_UPLOAD_FOLDER, exist_ok=True)
        file.save(os.path.join(IMAGEN_UPLOAD_FOLDER, filename))
        img = f"/static/images/{filename}"
    else:
        img = request.form.get("imagen", "")

    db.crear_producto(nombre, desc, precio, stock, img)
    flash("Producto agregado correctamente.")
    return redirect(url_for("dashboard"))


@app.route("/dashboard/producto/actualizar", methods=["POST"])
@admin_requerido
def actualizar_producto_route():
    """
    Actualiza precio, stock e imagen de un producto existente.
    Recibe: producto_id, precio, stock, imagen (form).
    """
    pid = request.form.get("producto_id", type=int)
    precio = request.form.get("precio", type=float)
    stock = request.form.get("stock", type=int)
    imagen = request.form.get("imagen")

    if db.actualizar_producto(pid, precio, stock, imagen):
        flash("Producto actualizado.")
    else:
        flash("Error al actualizar producto.")
    return redirect(url_for("dashboard"))


@app.route("/dashboard/producto/eliminar/<int:pid>", methods=["POST"])
@admin_requerido
def eliminar_producto_route(pid):
    """
    Elimina un producto por ID.
    Recibe: pid (int) desde la URL.
    """
    if db.eliminar_producto(pid):
        flash("Producto eliminado.")
    else:
        flash("Error al eliminar producto.")
    return redirect(url_for("dashboard"))


# --- Avisos (Admin) ---

@app.route("/admin/avisos", methods=["POST"])
@admin_requerido
def crear_aviso():
    """
    Endpoint para que el admin cree un aviso.
    Recibe: titulo y mensaje (form POST).
    El aviso se guarda en BD y los usuarios lo verán
    automáticamente al entrar o recargar la página.
    """
    titulo = request.form["titulo"]
    mensaje = request.form["mensaje"]

    if not titulo or not mensaje:
        flash("Título y mensaje son obligatorios.")
        return redirect(url_for("dashboard"))

    db.crear_aviso(titulo, mensaje)
    flash("Aviso publicado correctamente.")
    return redirect(url_for("dashboard"))


@app.route("/admin/avisos/eliminar/<int:aviso_id>", methods=["POST"])
@admin_requerido
def eliminar_aviso_route(aviso_id):
    """
    Elimina un aviso del sistema.
    Recibe: aviso_id (int) desde la URL.
    """
    if db.eliminar_aviso(aviso_id):
        flash("Aviso eliminado.")
    else:
        flash("Error al eliminar aviso.")
    return redirect(url_for("dashboard"))


# --- Banners (Admin) ---

@app.route("/admin/banners/crear", methods=["POST"])
@admin_requerido
def crear_banner():
    titulo = request.form.get("titulo", "").strip()
    subtitulo = request.form.get("subtitulo", "").strip()
    imagen = request.form.get("imagen", "").strip()

    if not titulo or not imagen:
        flash("El banner necesita al menos un título y una imagen.")
        return redirect(url_for("dashboard"))

    db.crear_banner(titulo, subtitulo, imagen)
    flash("Banner creado correctamente.")
    return redirect(url_for("dashboard"))


@app.route("/admin/banners/activar/<int:banner_id>", methods=["POST"])
@admin_requerido
def activar_banner(banner_id):
    db.activar_banner(banner_id)
    flash("Banner activado.")
    return redirect(url_for("dashboard"))


@app.route("/admin/banners/eliminar/<int:banner_id>", methods=["POST"])
@admin_requerido
def eliminar_banner(banner_id):
    db.eliminar_banner(banner_id)
    flash("Banner eliminado.")
    return redirect(url_for("dashboard"))


# ==========================================================
#  PUNTO DE ENTRADA
# ==========================================================

if __name__ == "__main__":
    app.run(debug=True)

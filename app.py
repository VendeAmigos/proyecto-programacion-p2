import os
from flask import (
    Flask, render_template, request,
    redirect, url_for, session, flash, g, jsonify, send_file
)
from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug.utils import secure_filename
from functools import wraps

from database.init_db import inicializar_bd
from database.repositories.usuario_repository import UsuarioRepository
from database.repositories.producto_repository import ProductoRepository
from database.repositories.pedido_repository import PedidoRepository
from database.repositories.aviso_repository import AvisoRepository
from database.repositories.banner_repository import BannerRepository
from database.repositories.visita_repository import VisitaRepository
from export_excel import exportar_excel

IMAGEN_UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), 'static', 'images')
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp', 'avif'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

app = Flask(__name__)
app.secret_key = "clave_super_secreta_para_sesiones"

# Inicializar Base de datos
inicializar_bd()

usuario_repo = UsuarioRepository()
producto_repo = ProductoRepository()
pedido_repo = PedidoRepository()
aviso_repo = AvisoRepository()
banner_repo = BannerRepository()
visita_repo = VisitaRepository()


@app.before_request
def cargar_usuario():
    g.user = None
    if "user_id" in session:
        g.user = usuario_repo.obtener_usuario_por_id(session["user_id"])

    if request.path.startswith("/static") or request.path.startswith("/favicon"):
        return

    usuario_id = g.user.id if g.user else None
    visita_repo.registrar_visita(request.path, request.user_agent.string, usuario_id)


@app.context_processor
def variables_globales():
    carrito = session.get("carrito", {})
    cantidad = sum(carrito.values())
    avisos = aviso_repo.listar_avisos()
    return dict(user=g.user, carrito_count=cantidad, avisos_globales=avisos)


def login_requerido(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if g.user is None:
            flash("Necesitas iniciar sesión.")
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return wrapper


def admin_requerido(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if g.user is None or not g.user.es_admin:
            flash("Acceso denegado. Se requiere administrador.")
            return redirect(url_for("inicio"))
        return f(*args, **kwargs)
    return wrapper


@app.route("/")
def inicio():
    productos = producto_repo.listar_productos()
    banner = banner_repo.obtener_banner_activo()
    return render_template("index.html", productos=productos, banner=banner)


@app.route("/producto/<int:producto_id>")
def producto(producto_id):
    p = producto_repo.obtener_producto(producto_id)
    if not p:
        return "Producto no encontrado", 404
    return render_template("producto.html", p=p)


@app.route("/avisos")
def obtener_avisos():
    avisos = aviso_repo.listar_avisos()
    resultado = [
        {
            "id": a.id,
            "titulo": a.titulo,
            "mensaje": a.mensaje,
            "creado_en": a.creado_en,
        }
        for a in avisos
    ]
    return jsonify(resultado)


@app.route("/registro", methods=["GET", "POST"])
def registro():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        nombre_completo = request.form.get("nombre_completo", "")

        if not username or not password or not nombre_completo:
            flash("Todos los campos son obligatorios.")
            return redirect(url_for("registro"))

        if usuario_repo.obtener_usuario(username):
            flash("El usuario ya existe.")
            return redirect(url_for("registro"))

        hashed = generate_password_hash(password)
        if usuario_repo.crear_usuario(username, hashed, es_admin=0, nombre_completo=nombre_completo):
            flash("Cuenta creada. Ahora inicia sesión.")
            return redirect(url_for("login"))
        else:
            flash("Error en el registro.")

    return render_template("registro.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        user = usuario_repo.obtener_usuario(username)

        if user and check_password_hash(user.password_hash, password):
            session["user_id"] = user.id
            if user.es_admin:
                return redirect(url_for("dashboard"))
            return redirect(url_for("inicio"))
        else:
            flash("Credenciales inválidas.")

    return render_template("login.html")


@app.route("/logout")
def logout():
    session.pop("user_id", None)
    session.pop("carrito", None)
    return redirect(url_for("inicio"))


def obtener_carrito():
    if "carrito" not in session:
        session["carrito"] = {}
    return session["carrito"]


@app.route("/carrito")
def carrito():
    cart = obtener_carrito()
    items = []
    total = 0.0

    for pid_str, qty in cart.items():
        p = producto_repo.obtener_producto(int(pid_str))
        if not p:
            continue
        subtotal = float(p.precio) * int(qty)
        total += subtotal
        items.append({"p": p, "qty": int(qty), "subtotal": subtotal})

    return render_template("carrito.html", items=items, total=total)


@app.route("/carrito/agregar", methods=["POST"])
def carrito_agregar():
    pid = request.form.get("producto_id", type=int)
    qty = request.form.get("cantidad", type=int, default=1)

    cart = obtener_carrito()
    cart[str(pid)] = int(cart.get(str(pid), 0)) + max(qty, 1)
    session["carrito"] = cart
    flash("Agregado al carrito.")
    return redirect(request.referrer or url_for("inicio"))


@app.route("/carrito/quitar", methods=["POST"])
def carrito_quitar():
    pid = request.form.get("producto_id", type=int)
    cart = obtener_carrito()
    cart.pop(str(pid), None)
    session["carrito"] = cart
    return redirect(url_for("carrito"))


@app.route("/checkout", methods=["POST"])
def checkout():
    if not g.user:
        flash("Debes iniciar sesión para comprar.")
        return redirect(url_for("login"))

    cart = obtener_carrito()
    if not cart:
        return redirect(url_for("inicio"))

    nombre = request.form.get("nombre", g.user.username)
    email = request.form.get("email", "")
    direccion = request.form.get("direccion", "")
    telefono = request.form.get("telefono", "")
    
    if not direccion or not telefono:
        flash("La dirección y el teléfono son obligatorios.")
        return redirect(url_for("carrito"))
        
    items = [{"producto_id": int(pid), "cantidad": int(qty)} for pid, qty in cart.items()]

    pedido_id = pedido_repo.crear_pedido(nombre, email, direccion, telefono, items, usuario_id=g.user.id)

    if pedido_id:
        session["carrito"] = {}
        return render_template("checkout_ok.html", pedido_id=pedido_id)
    else:
        flash("Error al procesar pedido. Stock insuficiente.")
        return redirect(url_for("carrito"))


@app.route("/dashboard")
@admin_requerido
def dashboard():
    visitas = visita_repo.obtener_visitas_por_ruta()
    productos = producto_repo.listar_productos()
    avisos = aviso_repo.listar_avisos()
    ventas_hoy = pedido_repo.ventas_del_dia()
    imagen_subida = request.args.get("imagen_subida")
    imagenes = listar_imagenes()
    pedidos = pedido_repo.listar_pedidos()
    banners = banner_repo.listar_banners()
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


@app.route("/dashboard/descargar_bd")
@admin_requerido
def descargar_bd():
    mem_file = exportar_excel(in_memory=True)
    if not mem_file:
        flash("Error al generar el archivo de base de datos.")
        return redirect(url_for("dashboard"))
    
    return send_file(
        mem_file,
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        as_attachment=True,
        download_name="base_de_datos_exportada.xlsx"
    )


def listar_imagenes():
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
    filename = request.form.get("filename", "")
    if not filename or not allowed_file(filename):
        flash("Nombre de archivo inválido.")
        return redirect(url_for("dashboard"))

    ruta = f"/static/images/{secure_filename(filename)}"
    filepath = os.path.join(IMAGEN_UPLOAD_FOLDER, secure_filename(filename))

    if os.path.isfile(filepath):
        os.remove(filepath)
        n = producto_repo.limpiar_imagen_productos(ruta)
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

    dest = os.path.join(IMAGEN_UPLOAD_FOLDER, secure_filename(filename))
    file.save(dest)
    flash(f"Imagen '{filename}' reemplazada correctamente.")
    return redirect(url_for("dashboard"))


@app.route("/dashboard/pedido/estado", methods=["POST"])
@admin_requerido
def actualizar_estado_pedido_route():
    pedido_id = request.form.get("pedido_id", type=int)
    estado = request.form.get("estado", "")

    if not pedido_id or not estado:
        flash("Datos inválidos para actualizar estado.")
        return redirect(url_for("dashboard"))

    if pedido_repo.actualizar_estado_pedido(pedido_id, estado):
        flash(f"Pedido #{pedido_id} actualizado a '{estado}'.")
    else:
        flash(f"Error al actualizar el pedido #{pedido_id}.")
    return redirect(url_for("dashboard"))


@app.route("/dashboard/producto/agregar", methods=["POST"])
@admin_requerido
def agregar_producto():
    nombre = request.form["nombre"]
    desc = request.form["descripcion"]
    precio = float(request.form["precio"])
    stock = int(request.form["stock"])
    categoria = request.form.get("categoria", "General")

    file = request.files.get("imagen_file")
    if file and file.filename and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        os.makedirs(IMAGEN_UPLOAD_FOLDER, exist_ok=True)
        file.save(os.path.join(IMAGEN_UPLOAD_FOLDER, filename))
        img = f"/static/images/{filename}"
    else:
        img = request.form.get("imagen", "")

    producto_repo.crear_producto(nombre, desc, precio, stock, img, categoria)
    flash("Producto agregado correctamente.")
    return redirect(url_for("dashboard"))


@app.route("/dashboard/producto/actualizar", methods=["POST"])
@admin_requerido
def actualizar_producto_route():
    pid = request.form.get("producto_id", type=int)
    precio = request.form.get("precio", type=float)
    stock = request.form.get("stock", type=int)
    imagen = request.form.get("imagen")
    categoria = request.form.get("categoria", "General")

    if producto_repo.actualizar_producto(pid, precio, stock, imagen, categoria):
        flash("Producto actualizado.")
    else:
        flash("Error al actualizar producto.")
    return redirect(url_for("dashboard"))


@app.route("/dashboard/producto/eliminar/<int:pid>", methods=["POST"])
@admin_requerido
def eliminar_producto_route(pid):
    if producto_repo.eliminar_producto(pid):
        flash("Producto eliminado.")
    else:
        flash("Error al eliminar producto.")
    return redirect(url_for("dashboard"))


@app.route("/admin/avisos", methods=["POST"])
@admin_requerido
def crear_aviso():
    titulo = request.form["titulo"]
    mensaje = request.form["mensaje"]

    if not titulo or not mensaje:
        flash("Título y mensaje son obligatorios.")
        return redirect(url_for("dashboard"))

    aviso_repo.crear_aviso(titulo, mensaje, autor_id=g.user.id)
    flash("Aviso publicado correctamente.")
    return redirect(url_for("dashboard"))


@app.route("/admin/avisos/eliminar/<int:aviso_id>", methods=["POST"])
@admin_requerido
def eliminar_aviso_route(aviso_id):
    if aviso_repo.eliminar_aviso(aviso_id):
        flash("Aviso eliminado.")
    else:
        flash("Error al eliminar aviso.")
    return redirect(url_for("dashboard"))


@app.route("/admin/banners/crear", methods=["POST"])
@admin_requerido
def crear_banner():
    titulo = request.form.get("titulo", "").strip()
    subtitulo = request.form.get("subtitulo", "").strip()
    imagen = request.form.get("imagen", "").strip()

    if not titulo or not imagen:
        flash("El banner necesita al menos un título y una imagen.")
        return redirect(url_for("dashboard"))

    banner_repo.crear_banner(titulo, subtitulo, imagen, autor_id=g.user.id)
    flash("Banner creado correctamente.")
    return redirect(url_for("dashboard"))


@app.route("/admin/banners/activar/<int:banner_id>", methods=["POST"])
@admin_requerido
def activar_banner(banner_id):
    banner_repo.activar_banner(banner_id)
    flash("Banner activado.")
    return redirect(url_for("dashboard"))


@app.route("/admin/banners/eliminar/<int:banner_id>", methods=["POST"])
@admin_requerido
def eliminar_banner(banner_id):
    banner_repo.eliminar_banner(banner_id)
    flash("Banner eliminado.")
    return redirect(url_for("dashboard"))


if __name__ == "__main__":
    app.run(debug=True)

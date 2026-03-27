# app.py - E-commerce Smartwatches
from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from functools import wraps
from tienda_db import BaseDatosTienda
import os

# Initialize Flask with dist folder as static directory
static_dir = os.path.join(os.path.dirname(__file__), 'dist')
app = Flask(__name__, static_folder=static_dir, static_url_path='/static')
app.secret_key = "smartwatch-secret-key-change-in-production"

db = BaseDatosTienda(ruta="./", bd="tienda.sqlite3")
db.semilla_productos()
db.semilla_admin()

# ========== DECORADORES ==========
def login_requerido(f):
    """Verifica que el usuario esté autenticado."""
    @wraps(f)
    def decorado(*args, **kwargs):
        if "usuario_id" not in session:
            flash("Debes iniciar sesión para acceder a esta página.")
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorado

def admin_requerido(f):
    """Verifica que el usuario sea admin."""
    @wraps(f)
    def decorado(*args, **kwargs):
        if "usuario_id" not in session:
            flash("Debes iniciar sesión.")
            return redirect(url_for("login"))
        
        usuario = db.obtener_usuario_por_id(session["usuario_id"])
        if not usuario or usuario["rol"] != "admin":
            flash("No tienes permisos para acceder a esta página.")
            return redirect(url_for("index"))
        
        return f(*args, **kwargs)
    return decorado

# ========== CONTEXTO GLOBAL ==========
@app.context_processor
def inyectar_usuario():
    """Inyecta datos de usuario en todos los templates."""
    usuario = None
    cantidad_carrito = 0
    es_guest = False
    
    if "usuario_id" in session:
        usuario = db.obtener_usuario_por_id(session["usuario_id"])
        if usuario:
            cantidad_carrito = db.obtener_cantidad_carrito(session["usuario_id"])
    else:
        # Si no hay usuario, es guest
        es_guest = True
    
    return {
        "usuario_logueado": usuario,
        "cantidad_carrito": cantidad_carrito,
        "es_guest": es_guest
    }

# ========== AUTENTICACIÓN ==========
@app.route("/registro", methods=["GET", "POST"])
def registro():
    """Registro de nuevos usuarios."""
    if request.method == "POST":
        nombre = request.form.get("nombre", "").strip()
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "").strip()
        password_confirm = request.form.get("password_confirm", "").strip()
        
        if not nombre or not email or not password:
            flash("Por favor completa todos los campos.")
            return redirect(url_for("registro"))
        
        if password != password_confirm:
            flash("Las contraseñas no coinciden.")
            return redirect(url_for("registro"))
        
        if len(password) < 6:
            flash("La contraseña debe tener al menos 6 caracteres.")
            return redirect(url_for("registro"))
        
        usuario_id = db.registrar_usuario(nombre, email, password)
        if usuario_id:
            session["usuario_id"] = usuario_id
            # Cargar carrito de guest si existe
            carrito_guest = request.args.get("carrito_items", "").split(",")
            if carrito_guest and carrito_guest[0]:
                for item_id_str in carrito_guest:
                    if item_id_str.strip():
                        try:
                            item_id = int(item_id_str.strip())
                            db.agregar_a_carrito_persistente(usuario_id, item_id, 1)
                        except (ValueError, IndexError):
                            pass
            
            flash("¡Registro exitoso! Tu carrito ha sido sincronizado.")
            return redirect(url_for("index"))
        else:
            flash("El email ya está registrado. Intenta con otro.")
            return redirect(url_for("registro"))
    
    return render_template("registro.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    """Inicio de sesión."""
    if request.method == "POST":
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "").strip()
        
        usuario_id = db.autenticar_usuario(email, password)
        if usuario_id:
            session["usuario_id"] = usuario_id
            # Cargar carrito de guest si existe
            carrito_guest = request.args.get("carrito_items", "").split(",")
            if carrito_guest and carrito_guest[0]:
                for item_id_str in carrito_guest:
                    if item_id_str.strip():
                        try:
                            item_id = int(item_id_str.strip())
                            db.agregar_a_carrito_persistente(usuario_id, item_id, 1)
                        except (ValueError, IndexError):
                            pass
            
            flash("¡Bienvenido de nuevo!")
            return redirect(url_for("index"))
        else:
            flash("Email o contraseña incorrectos.")
            return redirect(url_for("login"))
    
    return render_template("login.html")

@app.route("/logout")
def logout():
    """Cierra la sesión del usuario."""
    session.pop("usuario_id", None)
    flash("Has cerrado sesión.")
    return redirect(url_for("index"))

# ========== CATÁLOGO Y PRODUCTOS ==========
@app.route("/")
def index():
    """Página principal con catálogo."""
    productos = db.listar_productos()
    destacados = db.obtener_productos_destacados(3)
    return render_template("index.html", productos=productos, destacados=destacados)

@app.route("/producto/<int:producto_id>")
def producto(producto_id):
    """Página de detalle del producto (sin login requerido)."""
    p = db.obtener_producto(producto_id)
    if not p:
        flash("Producto no encontrado.")
        return redirect(url_for("index"))
    return render_template("producto.html", producto=p)

# ========== CARRITO (GUEST + AUTH) ==========
@app.route("/carrito/agregar", methods=["POST"])
def carrito_agregar():
    """Agrega un producto al carrito (guest o auth)."""
    producto_id = request.form.get("producto_id", type=int)
    cantidad = request.form.get("cantidad", type=int, default=1)
    
    p = db.obtener_producto(producto_id)
    if not p:
        flash("Producto no existe.")
        return redirect(url_for("index"))
    
    if cantidad < 1:
        cantidad = 1
    
    if p["stock"] < cantidad:
        flash(f"Stock insuficiente. Disponibles: {p['stock']}")
        return redirect(request.referrer or url_for("index"))
    
    # Si usuario está logueado, guardar en BD
    if "usuario_id" in session:
        db.agregar_a_carrito_persistente(session["usuario_id"], producto_id, cantidad)
        flash(f"✓ {cantidad} {p['nombre']} agregado(s) al carrito.")
    else:
        # Guest: guardar en localStorage via JavaScript
        flash(f"✓ {cantidad} {p['nombre']} agregado(s) al carrito.")
    
    return redirect(request.referrer or url_for("index"))

@app.route("/carrito")
def carrito():
    """Muestra el carrito (guest o auth)."""
    if "usuario_id" in session:
        # Usuario autenticado: obtener de BD
        usuario_id = session["usuario_id"]
        items = db.obtener_carrito(usuario_id)
        total = 0.0
        for item in items:
            total += float(item["precio"]) * int(item["cantidad"])
        return render_template("carrito.html", items=items, total=total, es_guest=False)
    else:
        # Guest: obtener de localStorage (via template)
        return render_template("carrito.html", items=[], total=0.0, es_guest=True)

@app.route("/carrito/quitar/<int:producto_id>", methods=["POST"])
def carrito_quitar(producto_id):
    """Elimina un producto del carrito."""
    if "usuario_id" in session:
        db.quitar_del_carrito(session["usuario_id"], producto_id)
        flash("Producto eliminado del carrito.")
    return redirect(url_for("carrito"))

@app.route("/carrito/actualizar/<int:producto_id>", methods=["POST"])
def carrito_actualizar(producto_id):
    """Actualiza la cantidad de un producto en el carrito."""
    cantidad = request.form.get("cantidad", type=int, default=1)
    
    if "usuario_id" in session and cantidad > 0:
        db.actualizar_cantidad_carrito(session["usuario_id"], producto_id, cantidad)
        flash("Carrito actualizado.")
    
    return redirect(url_for("carrito"))

@app.route("/api/carrito/cantidad")
def api_carrito_cantidad():
    """API para obtener cantidad de items en carrito (guest o auth)."""
    if "usuario_id" in session:
        cantidad = db.obtener_cantidad_carrito(session["usuario_id"])
    else:
        # Guest: cantidad viene del cliente
        cantidad = request.args.get("cantidad", type=int, default=0)
    
    return jsonify({"cantidad": cantidad})

@app.route("/api/productos")
def api_productos():
    """API para obtener detalles de productos por IDs (para carrito guest)."""
    ids_str = request.args.get("ids", "")
    if not ids_str:
        return jsonify([])
    
    try:
        ids = [int(x) for x in ids_str.split(",") if x.strip()]
    except:
        return jsonify([])
    
    productos = []
    for pid in ids:
        p = db.obtener_producto(pid)
        if p:
            productos.append({
                "id": p["id"],
                "nombre": p["nombre"],
                "precio": float(p["precio"]),
                "imagen_url": p["imagen_url"]
            })
    
    return jsonify(productos)

@app.route("/checkout", methods=["POST"])
def checkout():
    """Procesa la compra."""
    if "usuario_id" not in session:
        flash("Debes iniciar sesión para completar tu compra.")
        return redirect(url_for("login"))
    
    usuario_id = session["usuario_id"]
    usuario = db.obtener_usuario_por_id(usuario_id)
    
    nombre = request.form.get("nombre", usuario["nombre"] if usuario else "").strip()
    email = request.form.get("email", usuario["email"] if usuario else "").strip()
    
    if not nombre or not email:
        flash("Por favor completa todos los campos.")
        return redirect(url_for("carrito"))
    
    items = db.obtener_carrito(usuario_id)
    if not items:
        flash("Tu carrito está vacío.")
        return redirect(url_for("carrito"))
    
    items_dict = [{"producto_id": item["producto_id"], "cantidad": item["cantidad"]} for item in items]
    
    pedido_id = db.crear_pedido(nombre, email, items_dict, usuario_id)
    if pedido_id:
        db.vaciar_carrito(usuario_id)
        return render_template("checkout_ok.html", pedido_id=pedido_id)
    else:
        flash("Error al procesar el pedido. Intenta de nuevo.")
        return redirect(url_for("carrito"))

# ========== ADMIN - DASHBOARD ==========
@app.route("/admin")
@admin_requerido
def admin_dashboard():
    """Dashboard del administrador."""
    productos = db.listar_productos()
    return render_template("admin_dashboard.html", productos=productos)

@app.route("/admin/producto/nuevo", methods=["GET", "POST"])
@admin_requerido
def admin_producto_nuevo():
    """Crea un nuevo producto."""
    if request.method == "POST":
        nombre = request.form.get("nombre", "").strip()
        descripcion = request.form.get("descripcion", "").strip()
        precio = request.form.get("precio", type=float)
        stock = request.form.get("stock", type=int, default=0)
        imagen_url = request.form.get("imagen_url", "").strip()
        destacado = 1 if request.form.get("destacado") else 0
        
        if not nombre or precio is None or stock is None:
            flash("Por favor completa los campos obligatorios.")
            return redirect(url_for("admin_producto_nuevo"))
        
        if precio < 0 or stock < 0:
            flash("Precio y stock no pueden ser negativos.")
            return redirect(url_for("admin_producto_nuevo"))
        
        producto_id = db.crear_producto(nombre, descripcion, precio, stock, imagen_url, destacado)
        if producto_id:
            flash(f"✓ Producto '{nombre}' creado exitosamente.")
            return redirect(url_for("admin_dashboard"))
        else:
            flash("Error al crear el producto.")
            return redirect(url_for("admin_producto_nuevo"))
    
    return render_template("admin_producto_nuevo.html")

@app.route("/admin/producto/<int:producto_id>/editar", methods=["GET", "POST"])
@admin_requerido
def admin_producto_editar(producto_id):
    """Edita un producto existente."""
    producto = db.obtener_producto(producto_id)
    if not producto:
        flash("Producto no encontrado.")
        return redirect(url_for("admin_dashboard"))
    
    if request.method == "POST":
        nombre = request.form.get("nombre", "").strip()
        descripcion = request.form.get("descripcion", "").strip()
        precio = request.form.get("precio", type=float)
        stock = request.form.get("stock", type=int)
        imagen_url = request.form.get("imagen_url", "").strip()
        destacado = 1 if request.form.get("destacado") else 0
        
        if not nombre or precio is None or stock is None:
            flash("Por favor completa los campos obligatorios.")
            return redirect(url_for("admin_producto_editar", producto_id=producto_id))
        
        if precio < 0 or stock < 0:
            flash("Precio y stock no pueden ser negativos.")
            return redirect(url_for("admin_producto_editar", producto_id=producto_id))
        
        if db.actualizar_producto(producto_id, nombre, descripcion, precio, stock, imagen_url, destacado):
            flash(f"✓ Producto '{nombre}' actualizado exitosamente.")
            return redirect(url_for("admin_dashboard"))
        else:
            flash("Error al actualizar el producto.")
            return redirect(url_for("admin_producto_editar", producto_id=producto_id))
    
    return render_template("admin_producto_editar.html", producto=producto)

@app.route("/admin/producto/<int:producto_id>/eliminar", methods=["POST"])
@admin_requerido
def admin_producto_eliminar(producto_id):
    """Elimina un producto."""
    producto = db.obtener_producto(producto_id)
    if not producto:
        flash("Producto no encontrado.")
        return redirect(url_for("admin_dashboard"))
    
    if db.eliminar_producto(producto_id):
        flash(f"✓ Producto '{producto['nombre']}' eliminado exitosamente.")
    else:
        flash("Error al eliminar el producto.")
    
    return redirect(url_for("admin_dashboard"))

# ========== MANEJO DE ERRORES ==========
@app.errorhandler(404)
def pagina_no_encontrada(error):
    return render_template("404.html"), 404

@app.errorhandler(500)
def error_servidor(error):
    return render_template("500.html"), 500

if __name__ == "__main__":
    print("=" * 60)
    print("[STORE] E-COMMERCE SMARTWATCHES")
    print("=" * 60)
    print("[OK] Base de datos inicializada")
    print("[OK] Productos cargados")
    print("\n[ACCOUNT] Cuenta de prueba:")
    print("   Email: admin@smartwatches.com")
    print("   Contraseña: admin123")
    print("\n[SERVER] Ejecutandose en http://localhost:5000")
    print("=" * 60)
    app.run(debug=True, port=5000)


if __name__ == "__main__":
    pass


@app.route("/carrito/quitar/<int:producto_id>", methods=["POST"])
@login_requerido
def carrito_quitar(producto_id):
    """Elimina un producto del carrito."""
    db.quitar_del_carrito(session["usuario_id"], producto_id)
    flash("Producto eliminado del carrito.")
    return redirect(url_for("carrito"))

@app.route("/carrito/actualizar/<int:producto_id>", methods=["POST"])
@login_requerido
def carrito_actualizar(producto_id):
    """Actualiza la cantidad de un producto en el carrito."""
    cantidad = request.form.get("cantidad", type=int, default=1)
    
    if cantidad < 1:
        return redirect(url_for("carrito"))
    
    db.actualizar_cantidad_carrito(session["usuario_id"], producto_id, cantidad)
    flash("Carrito actualizado.")
    return redirect(url_for("carrito"))

@app.route("/checkout", methods=["POST"])
@login_requerido
def checkout():
    """Procesa la compra."""
    usuario_id = session["usuario_id"]
    usuario = db.obtener_usuario_por_id(usuario_id)
    
    nombre = request.form.get("nombre", usuario["nombre"] if usuario else "").strip()
    email = request.form.get("email", usuario["email"] if usuario else "").strip()
    
    if not nombre or not email:
        flash("Por favor completa todos los campos.")
        return redirect(url_for("carrito"))
    
    # Obtener items del carrito
    items = db.obtener_carrito(usuario_id)
    if not items:
        flash("Tu carrito está vacío.")
        return redirect(url_for("carrito"))
    
    # Convertir formato para crear_pedido
    items_dict = [{"producto_id": item["producto_id"], "cantidad": item["cantidad"]} for item in items]
    
    # Crear pedido
    pedido_id = db.crear_pedido(nombre, email, items_dict, usuario_id)
    if pedido_id:
        db.vaciar_carrito(usuario_id)
        return render_template("checkout_ok.html", pedido_id=pedido_id)
    else:
        flash("Error al procesar el pedido. Intenta de nuevo.")
        return redirect(url_for("carrito"))

# ========== ADMIN - DASHBOARD ==========
@app.route("/admin")
@admin_requerido
def admin_dashboard():
    """Dashboard del administrador."""
    productos = db.listar_productos()
    return render_template("admin_dashboard.html", productos=productos)

@app.route("/admin/producto/nuevo", methods=["GET", "POST"])
@admin_requerido
def admin_producto_nuevo():
    """Crea un nuevo producto."""
    if request.method == "POST":
        nombre = request.form.get("nombre", "").strip()
        descripcion = request.form.get("descripcion", "").strip()
        precio = request.form.get("precio", type=float)
        stock = request.form.get("stock", type=int, default=0)
        imagen_url = request.form.get("imagen_url", "").strip()
        destacado = 1 if request.form.get("destacado") else 0
        
        # Validaciones
        if not nombre or precio is None or stock is None:
            flash("Por favor completa los campos obligatorios.")
            return redirect(url_for("admin_producto_nuevo"))
        
        if precio < 0 or stock < 0:
            flash("Precio y stock no pueden ser negativos.")
            return redirect(url_for("admin_producto_nuevo"))
        
        # Crear producto
        producto_id = db.crear_producto(nombre, descripcion, precio, stock, imagen_url, destacado)
        if producto_id:
            flash(f"✓ Producto '{nombre}' creado exitosamente.")
            return redirect(url_for("admin_dashboard"))
        else:
            flash("Error al crear el producto.")
            return redirect(url_for("admin_producto_nuevo"))
    
    return render_template("admin_producto_nuevo.html")

@app.route("/admin/producto/<int:producto_id>/editar", methods=["GET", "POST"])
@admin_requerido
def admin_producto_editar(producto_id):
    """Edita un producto existente."""
    producto = db.obtener_producto(producto_id)
    if not producto:
        flash("Producto no encontrado.")
        return redirect(url_for("admin_dashboard"))
    
    if request.method == "POST":
        nombre = request.form.get("nombre", "").strip()
        descripcion = request.form.get("descripcion", "").strip()
        precio = request.form.get("precio", type=float)
        stock = request.form.get("stock", type=int)
        imagen_url = request.form.get("imagen_url", "").strip()
        destacado = 1 if request.form.get("destacado") else 0
        
        # Validaciones
        if not nombre or precio is None or stock is None:
            flash("Por favor completa los campos obligatorios.")
            return redirect(url_for("admin_producto_editar", producto_id=producto_id))
        
        if precio < 0 or stock < 0:
            flash("Precio y stock no pueden ser negativos.")
            return redirect(url_for("admin_producto_editar", producto_id=producto_id))
        
        # Actualizar producto
        if db.actualizar_producto(producto_id, nombre, descripcion, precio, stock, imagen_url, destacado):
            flash(f"✓ Producto '{nombre}' actualizado exitosamente.")
            return redirect(url_for("admin_dashboard"))
        else:
            flash("Error al actualizar el producto.")
            return redirect(url_for("admin_producto_editar", producto_id=producto_id))
    
    return render_template("admin_producto_editar.html", producto=producto)

@app.route("/admin/producto/<int:producto_id>/eliminar", methods=["POST"])
@admin_requerido
def admin_producto_eliminar(producto_id):
    """Elimina un producto."""
    producto = db.obtener_producto(producto_id)
    if not producto:
        flash("Producto no encontrado.")
        return redirect(url_for("admin_dashboard"))
    
    if db.eliminar_producto(producto_id):
        flash(f"✓ Producto '{producto['nombre']}' eliminado exitosamente.")
    else:
        flash("Error al eliminar el producto.")
    
    return redirect(url_for("admin_dashboard"))

# ========== MANEJO DE ERRORES ==========
@app.errorhandler(404)
def pagina_no_encontrada(error):
    return render_template("404.html"), 404

@app.errorhandler(500)
def error_servidor(error):
    return render_template("500.html"), 500

if __name__ == "__main__":
    print("=" * 60)
    print("🏪 E-COMMERCE SMARTWATCHES")
    print("=" * 60)
    print("✓ Base de datos inicializada")
    print("✓ Productos cargados")
    print("\n👤 Cuenta de prueba:")
    print("   Email: admin@smartwatches.com")
    print("   Contraseña: admin123")
    print("\n🚀 Servidor ejecutándose en http://localhost:5000")
    print("=" * 60)
    app.run(debug=True, port=5000)

from flask import Flask, render_template, request, redirect, url_for, session, flash, g
from werkzeug.security import check_password_hash, generate_password_hash
from functools import wraps
from tienda_db import BaseDatosTienda
import os

app = Flask(__name__)
app.secret_key = "clave_super_secreta_para_sesiones"

db = BaseDatosTienda(ruta="./", bd="tienda.sqlite3")

# --- Middlewares y Contexto ---

@app.before_request
def before_request():
    g.user = None
    if 'user_id' in session:
        # AquÃ simulamos obtener usuario ya que db.obtener_usuario_por_id podrÃa no estar refrescado
        # Si modificas tienda_db.py asegúrate que existe el método
        try:
           g.user = db.obtener_usuario_por_id(session['user_id'])
        except:
           pass
    
    # Registrar visita (Analytics)
    if request.path.startswith('/static') or request.path.startswith('/favicon'):
        return
        
    db.registrar_visita(request.path, request.user_agent.string)

@app.context_processor
def inject_user():
    def carrito_count():
        c = session.get("carrito", {})
        return sum(c.values())
    return dict(user=g.user, carrito_count=carrito_count())

# --- Decoradores ---

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if g.user is None:
            flash("Necesitas iniciar sesión.")
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if g.user is None or not g.user['es_admin']:
            flash("Acceso denegado. Se requiere administrador.")
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function

# --- Rutas Públicas ---

@app.route("/")
def index():
    productos = db.listar_productos()
    return render_template("index.html", productos=productos)

@app.route("/producto/<int:producto_id>")
def producto(producto_id):
    p = db.obtener_producto(producto_id)
    if not p:
        return "Producto no encontrado", 404
    return render_template("producto.html", p=p)

# --- Auth ---

@app.route("/registro", methods=["GET", "POST"])
def registro():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        if not username or not password:
            flash("Todos los campos obligatorios.")
            return redirect(url_for('registro'))
        
        if db.obtener_usuario(username):
            flash("El usuario ya existe.")
            return redirect(url_for('registro'))
            
        ph = generate_password_hash(password)
        if db.crear_usuario(username, ph):
            flash("Cuenta creada. Ahora inicia sesión.")
            return redirect(url_for('login'))
        else:
            flash("Error en el registro.")

    return render_template("registro.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        
        user = db.obtener_usuario(username)
        
        # Verificar hash correctamente
        if user and check_password_hash(user['password_hash'], password):
            session['user_id'] = user['id']
            # MANTENER CARRITO:
            # Si hay carrito en sesion anonima, se queda. Opcionalmente podriamos fusionarlo con uno de BD.
            # Por ahora, el comportamiento default de Flask session es persistir a menos que lo borremos.
            
            if user['es_admin']:
                return redirect(url_for('dashboard'))
            return redirect(url_for('index'))
        else:
            flash("Credenciales inválidas.")
    
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.pop('user_id', None)
    session.pop('carrito', None)
    return redirect(url_for('index'))

# --- Dashboard Admin ---

@app.route("/dashboard")
@admin_required
def dashboard():
    visitas = db.obtener_visitas_por_ruta()
    productos = db.listar_productos()
    return render_template("dashboard.html", visitas=visitas, productos=productos)

@app.route("/dashboard/producto/agregar", methods=["POST"])
@admin_required
def agregar_producto():
    nombre = request.form["nombre"]
    desc = request.form["descripcion"]
    precio = float(request.form["precio"])
    stock = int(request.form["stock"])
    img = request.form["imagen"]
    
    db.crear_producto(nombre, desc, precio, stock, img)
    flash("Producto agregado correctamente.")
    return redirect(url_for('dashboard'))

@app.route("/dashboard/producto/actualizar", methods=["POST"])
@admin_required
def actualizar_producto_route():
    pid = request.form.get("producto_id", type=int)
    precio = request.form.get("precio", type=float)
    stock = request.form.get("stock", type=int)
    imagen = request.form.get("imagen")
    
    if db.actualizar_producto(pid, precio, stock, imagen):
        flash("Producto actualizado.")
    else:
        flash("Error al actualizar producto.")
    return redirect(url_for('dashboard'))

@app.route("/dashboard/producto/eliminar/<int:pid>", methods=["POST"])
@admin_required
def eliminar_producto_route(pid):
    if db.eliminar_producto(pid):
        flash("Producto eliminado.")
    else:
        flash("Error al eliminar producto.")
    return redirect(url_for('dashboard'))

@app.route("/dashboard/stock/actualizar", methods=["POST"])
@admin_required
def actualizar_stock_route():
    pid = request.form.get("producto_id", type=int)
    nuevo_stock = request.form.get("stock", type=int)
    db.actualizar_stock(pid, nuevo_stock)
    flash("Stock actualizado.")
    return redirect(url_for('dashboard'))

# --- Carrito ---

def get_carrito():
    if "carrito" not in session:
        session["carrito"] = {}
    return session["carrito"]

@app.route("/carrito")
def carrito():
    cart = get_carrito()
    items = []
    total = 0.0

    for pid_str, qty in cart.items():
        p = db.obtener_producto(int(pid_str))
        if not p: continue
        subtotal = float(p["precio"]) * int(qty)
        total += subtotal
        items.append({"p": p, "qty": int(qty), "subtotal": subtotal})

    return render_template("carrito.html", items=items, total=total)

@app.route("/carrito/agregar", methods=["POST"])
def carrito_agregar():
    pid = request.form.get("producto_id", type=int)
    qty = request.form.get("cantidad", type=int, default=1)
    
    cart = get_carrito()
    cart[str(pid)] = int(cart.get(str(pid), 0)) + max(qty, 1)
    session["carrito"] = cart
    flash("Agregado al carrito.")
    return redirect(request.referrer or url_for('index'))

@app.route("/carrito/quitar", methods=["POST"])
def carrito_quitar():
    pid = request.form.get("producto_id", type=int)
    cart = get_carrito()
    cart.pop(str(pid), None)
    session["carrito"] = cart
    return redirect(url_for("carrito"))

@app.route("/checkout", methods=["POST"])
def checkout():
    if not g.user:
         flash("Debes iniciar sesión para comprar.")
         return redirect(url_for('login'))

    nombre = g.user['username']
    email = "usuario@tienda.com" # Placeholder

    cart = get_carrito()
    if not cart: return redirect(url_for("index"))

    items = [{"producto_id": int(pid), "cantidad": int(qty)} for pid, qty in cart.items()]
    pedido_id = db.crear_pedido(nombre, email, items)
    
    if pedido_id:
        session["carrito"] = {}
        return render_template("checkout_ok.html", pedido_id=pedido_id)
    else:
        flash("Error al procesar pedido. Stock insuficiente.")
        return redirect(url_for("carrito"))

if __name__ == "__main__":
    app.run(debug=True)

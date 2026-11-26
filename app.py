"""TecnoHogar MTY - Aplicacion de laboratorio.

Version integrada con correcciones de SQL Injection, XSS e IDOR/BOLA.
Es solo para el laboratorio del curso, con datos ficticios.
Escucha unicamente en 127.0.0.1. Nunca la expongas a internet ni la uses con
datos reales.

Ejecucion:  python app.py   ->  http://127.0.0.1:5000
"""
import html
import logging
import os
import sqlite3

from flask import Flask, g, jsonify, redirect, request, session

BASE = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE, "tecnohogar.db")
LOG_PATH = os.path.join(BASE, "app.log")

app = Flask(__name__)
# Clave de laboratorio: cambiarla por variable de entorno si se publica algo.
app.secret_key = os.environ.get("SECRET_KEY", "laboratorio-no-usar-en-produccion")

logging.basicConfig(
    filename=LOG_PATH,
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    encoding="utf-8",
)
log = logging.getLogger("tecnohogar")


# ---------------------------------------------------------------- base de datos
def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(DB_PATH)
        g.db.row_factory = sqlite3.Row
    return g.db


@app.teardown_appcontext
def close_db(exc):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db():
    """Crea la base con datos ficticios la primera vez que se ejecuta."""
    if os.path.exists(DB_PATH):
        return
    db = sqlite3.connect(DB_PATH)
    db.executescript(
        """
        CREATE TABLE usuarios(
            id INTEGER PRIMARY KEY, usuario TEXT, password TEXT,
            nombre TEXT, rol TEXT);
        CREATE TABLE productos(
            id INTEGER PRIMARY KEY, nombre TEXT, precio REAL);
        CREATE TABLE pedidos(
            id INTEGER PRIMARY KEY, usuario_id INTEGER, producto TEXT,
            total REAL, direccion TEXT, telefono TEXT);
        CREATE TABLE resenas(
            id INTEGER PRIMARY KEY, autor TEXT, texto TEXT);

        INSERT INTO usuarios VALUES
            (1,'ana','ana123','Ana Torres','cliente'),
            (2,'luis','luis123','Luis Perez','cliente'),
            (3,'soporte','soporte123','Soporte tecnico','admin');

        INSERT INTO productos VALUES
            (1,'Licuadora 600W',899.00),
            (2,'Microondas 20L',2199.00),
            (3,'Cafetera de goteo',749.00),
            (4,'Aspiradora compacta',1599.00),
            (5,'Plancha de vapor',529.00),
            (6,'Freidora de aire 4L',1899.00);

        INSERT INTO pedidos VALUES
            (1,1,'Licuadora 600W',899.00,'Calle Ficticia 101, Monterrey','8110000001'),
            (2,1,'Plancha de vapor',529.00,'Calle Ficticia 101, Monterrey','8110000001'),
            (3,2,'Microondas 20L',2199.00,'Avenida Inventada 202, Monterrey','8110000002'),
            (4,2,'Freidora de aire 4L',1899.00,'Avenida Inventada 202, Monterrey','8110000002');

        INSERT INTO resenas VALUES
            (1,'Ana','Excelente licuadora, llego rapido.'),
            (2,'Luis','El microondas funciona muy bien.');
        """
    )
    db.commit()
    db.close()


# ---------------------------------------------------------------------- vistas
def pagina(titulo, cuerpo):
    """Plantilla visual compartida. La logica de las rutas se conserva."""
    usuario = session.get("usuario")
    estado = (
        f"<span class='account-label'>Hola, <strong>{usuario}</strong></span> "
        "<a class='account-link' href='/logout'>Cerrar sesión</a>"
        if usuario
        else "<a class='account-link' href='/login'>Iniciar sesión</a>"
    )
    ruta = request.path
    enlaces = [
        ("/", "Inicio", "&#8962;"),
        ("/buscar", "Productos", "&#9638;"),
        ("/resenas", "Reseñas", "&#9734;"),
        ("/pedido/1", "Mis pedidos", "&#9636;"),
    ]
    nav = "".join(
        f"<a class='nav-link {'active' if ruta == href or (href == '/pedido/1' and ruta.startswith('/pedido/')) else ''}' href='{href}'><span>{icon}</span>{label}</a>"
        for href, label, icon in enlaces
    )
    return f"""<!doctype html>
<html lang="es">
<head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="theme-color" content="#101827">
<title>{titulo} | TecnoHogar MTY</title>
<style>
:root{{--bg:#f4f6fa;--surface:#fff;--ink:#172033;--muted:#69758a;--line:#e7ebf2;--navy:#101827;--blue:#3268e8;--blue2:#2454ca;--pale:#edf3ff;--green:#13866b;--shadow:0 18px 50px rgba(24,39,75,.08)}}
*{{box-sizing:border-box}}html{{scroll-behavior:smooth}}body{{margin:0;background:var(--bg);color:var(--ink);font-family:Inter,ui-sans-serif,system-ui,-apple-system,"Segoe UI",sans-serif;font-size:15px;line-height:1.6}}
a{{color:var(--blue);text-decoration:none}}a:hover{{color:var(--blue2)}}.topbar{{background:#0b1220;color:#cbd5e1;font-size:12px;letter-spacing:.02em}}.topbar-inner{{max-width:1180px;margin:auto;padding:9px 24px;display:flex;justify-content:space-between;gap:16px}}.topbar strong{{color:#fff}}.site-header{{background:var(--navy);color:white;position:relative;overflow:hidden}}.site-header:after{{content:"";position:absolute;width:430px;height:430px;border:1px solid rgba(120,160,255,.12);border-radius:50%;right:-120px;top:-280px;box-shadow:0 0 0 45px rgba(120,160,255,.035),0 0 0 90px rgba(120,160,255,.025)}}.header-inner{{max-width:1180px;margin:auto;padding:24px;display:flex;align-items:center;justify-content:space-between;gap:24px;position:relative;z-index:1}}.brand{{display:flex;align-items:center;gap:13px;color:#fff}}.brand-mark{{width:46px;height:46px;border-radius:14px;background:linear-gradient(135deg,#5b8cff,#2454ca);display:grid;place-items:center;font-size:23px;box-shadow:0 8px 24px rgba(50,104,232,.3)}}.brand-name{{font-size:20px;font-weight:800;letter-spacing:-.04em;line-height:1.15}}.brand-sub{{font-size:10px;color:#9eacc4;letter-spacing:.18em;text-transform:uppercase;margin-top:4px}}.header-right{{display:flex;align-items:center;gap:18px;color:#dbe5f7;font-size:13px}}.account-link{{display:inline-flex;align-items:center;background:#fff;color:#1a2b49;padding:10px 16px;border-radius:10px;font-weight:750}}.account-link:hover{{background:#eaf0ff;color:#183f9b}}.account-label{{color:#cbd5e1}}.main-nav{{background:#fff;border-bottom:1px solid var(--line);box-shadow:0 4px 14px rgba(20,35,65,.035)}}.nav-inner{{max-width:1180px;margin:auto;padding:0 24px;display:flex;align-items:center;gap:7px;min-height:60px}}.nav-link{{padding:18px 16px;color:#667187;font-size:13px;font-weight:700;display:flex;align-items:center;gap:9px;border-bottom:3px solid transparent;transition:.18s}}.nav-link span{{font-size:17px;color:#8b98ae}}.nav-link:hover,.nav-link.active{{color:var(--blue);border-bottom-color:var(--blue)}}.nav-link.active span{{color:var(--blue)}}.lab-strip{{max-width:1180px;margin:20px auto 0;padding:0 24px}}.lab-strip-inner{{background:#fff8e9;border:1px solid #f4dfb5;color:#875b13;padding:10px 14px;border-radius:10px;font-size:12px;display:flex;align-items:center;gap:9px}}.lab-dot{{width:8px;height:8px;border-radius:50%;background:#e3a32e;flex:none}}main{{max-width:1180px;margin:0 auto;padding:30px 24px 70px;min-height:55vh}}.page-heading{{margin:0 0 22px}}.eyebrow{{color:var(--blue);font-size:11px;font-weight:800;letter-spacing:.16em;text-transform:uppercase;margin-bottom:7px}}h1,h2,h3{{letter-spacing:-.035em;line-height:1.2}}h1{{font-size:clamp(27px,4vw,40px);margin:0 0 8px}}h2{{font-size:25px;margin:0 0 16px}}h3{{font-size:17px;margin:0 0 8px}}p{{color:var(--muted);margin:0 0 14px}}.content-panel{{background:var(--surface);border:1px solid var(--line);border-radius:18px;padding:26px;box-shadow:var(--shadow)}}.content-panel>h2:first-child{{margin-top:0}}form{{background:#fff;border:1px solid var(--line);border-radius:16px;padding:24px;max-width:620px;box-shadow:var(--shadow);margin:18px 0}}form:has(input[name='q']){{display:flex;align-items:center;gap:10px;max-width:760px}}form:has(input[name='q']) input{{flex:1}}input,textarea,select{{width:100%;border:1px solid #dce3ee;background:#fbfcff;border-radius:10px;padding:12px 14px;font:inherit;color:var(--ink);outline:none;margin:5px 0 12px;transition:.2s}}input:focus,textarea:focus,select:focus{{border-color:#7da2ff;box-shadow:0 0 0 4px #3268e81a}}button{{border:0;background:linear-gradient(135deg,#3977f4,#2454ca);color:#fff;padding:12px 19px;border-radius:10px;font:700 13px inherit;cursor:pointer;box-shadow:0 7px 18px rgba(50,104,232,.2);transition:.2s}}button:hover{{transform:translateY(-1px);filter:brightness(1.05)}}table{{width:100%;border-collapse:separate;border-spacing:0;background:#fff;border:1px solid var(--line);border-radius:14px;overflow:hidden;margin:18px 0;box-shadow:0 8px 24px rgba(24,39,75,.04)}}th,td{{padding:14px 16px;text-align:left;border-bottom:1px solid var(--line)}}th{{background:#f5f7fc;color:#59667d;font-size:11px;text-transform:uppercase;letter-spacing:.08em}}td{{color:#46536a;font-size:14px}}tr:last-child td{{border-bottom:0}}tr:hover td{{background:#fbfcff}}ul{{padding-left:22px;color:var(--muted)}}li{{margin:7px 0}}hr{{border:0;border-top:1px solid var(--line);margin:24px 0}}.error,.alert{{padding:13px 16px;border-radius:11px;background:#fff0f0;color:#a52b37;border:1px solid #f5d2d5;margin:12px 0}}.review-list{{list-style:none;padding:0;display:grid;gap:12px}}.review-list li{{background:#f8faff;border:1px solid var(--line);padding:16px;border-radius:12px;color:#4b5870}}.review-list b{{display:block;color:#1d2b45;margin-bottom:5px}}.site-footer{{background:#0b1220;color:#8e9bb1;padding:28px 24px}}.footer-inner{{max-width:1180px;margin:auto;display:flex;justify-content:space-between;gap:20px;align-items:center;font-size:12px}}.footer-brand{{color:#fff;font-weight:800}}.footer-note{{color:#78869e}}.hero{{position:relative;overflow:hidden;border-radius:24px;background:linear-gradient(115deg,#101d35 0%,#18376d 60%,#3268e8 100%);color:white;padding:clamp(28px,5vw,58px);display:grid;grid-template-columns:1.3fr .7fr;gap:24px;align-items:center;box-shadow:0 24px 55px rgba(29,65,133,.2)}}.hero:after{{content:"";position:absolute;width:360px;height:360px;border:1px solid #ffffff20;border-radius:50%;right:-100px;top:-130px;box-shadow:0 0 0 35px #ffffff09,0 0 0 75px #ffffff07}}.hero-copy,.hero-art{{position:relative;z-index:1}}.hero-kicker{{display:inline-flex;background:#ffffff18;border:1px solid #ffffff30;color:#dce8ff;border-radius:30px;padding:7px 12px;font-size:11px;font-weight:800;letter-spacing:.12em;text-transform:uppercase;margin-bottom:18px}}.hero h1{{font-size:clamp(32px,5vw,52px);max-width:600px;line-height:1.06;margin:0 0 16px;color:white}}.hero p{{color:#c5d4f0;max-width:520px;font-size:15px;line-height:1.8}}.hero-actions{{display:flex;gap:12px;flex-wrap:wrap;margin-top:25px}}.hero-btn{{display:inline-flex;padding:12px 18px;border-radius:10px;background:#fff;color:#1d3e80;font-weight:800;font-size:13px}}.hero-btn.secondary{{background:#ffffff15;border:1px solid #ffffff40;color:white}}.hero-art{{display:grid;place-items:center;min-height:210px}}.hero-orb{{width:205px;height:205px;border-radius:42px;transform:rotate(-8deg);background:linear-gradient(145deg,#ffffff30,#ffffff08);border:1px solid #ffffff50;display:grid;place-items:center;box-shadow:inset 0 0 50px #ffffff15,0 20px 50px #07142e55}}.hero-orb span{{font-size:104px;filter:drop-shadow(0 12px 16px #07142e55);transform:rotate(8deg)}}.section-row{{display:flex;justify-content:space-between;align-items:end;gap:18px;margin:34px 0 16px}}.section-row p{{font-size:13px;margin:0}}.product-grid{{display:grid;grid-template-columns:repeat(3,1fr);gap:16px}}.product-card{{background:#fff;border:1px solid var(--line);border-radius:16px;padding:18px;box-shadow:0 8px 24px rgba(24,39,75,.04);transition:.2s}}.product-card:hover{{transform:translateY(-3px);box-shadow:var(--shadow)}}.product-art{{height:118px;border-radius:12px;background:linear-gradient(135deg,#f2f5fb,#e8eefb);display:grid;place-items:center;font-size:52px;margin-bottom:15px}}.product-card h3{{font-size:15px;letter-spacing:-.01em}}.product-card p{{font-size:12px;margin:0 0 10px}}.price{{font-size:20px;font-weight:850;color:#1b2a45}}.price small{{font-size:11px;color:#8490a4;font-weight:500}}.feature-grid{{display:grid;grid-template-columns:repeat(3,1fr);gap:14px;margin-top:22px}}.feature{{background:#fff;border:1px solid var(--line);border-radius:14px;padding:17px;display:flex;gap:12px;align-items:center}}.feature-icon{{width:40px;height:40px;display:grid;place-items:center;border-radius:12px;background:var(--pale);color:var(--blue);font-size:19px;flex:none}}.feature strong{{display:block;font-size:12px;color:#26334c}}.feature small{{color:#8792a5;font-size:11px}}.search-caption{{font-size:12px;color:#8994a8;margin-top:10px}}@media(max-width:760px){{.header-inner{{align-items:flex-start;flex-direction:column}}.header-right{{width:100%;justify-content:space-between}}.nav-inner{{overflow-x:auto}}.nav-link{{white-space:nowrap;padding:16px 12px}}.hero{{grid-template-columns:1fr}}.hero-art{{display:none}}.product-grid,.feature-grid{{grid-template-columns:1fr 1fr}}.footer-inner{{align-items:flex-start;flex-direction:column}}main{{padding:22px 16px 50px}}.lab-strip{{padding:0 16px}}.topbar-inner,.header-inner{{padding-left:16px;padding-right:16px}}}}@media(max-width:480px){{.product-grid,.feature-grid{{grid-template-columns:1fr}}.content-panel{{padding:18px}}form:has(input[name='q']){{display:block}}.hero{{padding:27px 22px}}.hero h1{{font-size:32px}}th,td{{padding:10px;font-size:12px}}}}
</style></head>
<body>
<div class="topbar"><div class="topbar-inner"><span>TECNOHOGAR MTY <strong>· Tecnología para tu hogar</strong></span><span>Monterrey, Nuevo León · Atención en línea</span></div></div>
<header class="site-header"><div class="header-inner"><a class="brand" href="/"><span class="brand-mark">&#8962;</span><span><span class="brand-name">TecnoHogar MTY</span><span class="brand-sub">Electrodomésticos & hogar</span></span></a><div class="header-right">{estado}</div></div></header>
<nav class="main-nav"><div class="nav-inner">{nav}</div></nav>
<div class="lab-strip"><div class="lab-strip-inner"><span class="lab-dot"></span><strong>Entorno académico de laboratorio</strong> · Información ficticia y uso local exclusivamente.</div></div>
<main>
<div class="page-heading"><div class="eyebrow">Experiencia TecnoHogar</div><h1>{titulo}</h1></div>
{cuerpo}
</main>
<footer class="site-footer"><div class="footer-inner"><div><div class="footer-brand">TecnoHogar MTY</div><div>Soluciones prácticas para cada espacio de tu hogar.</div></div><div class="footer-note">Proyecto académico de ciberseguridad · Aplicación local de laboratorio</div></div></footer>
</body></html>"""


@app.after_request
def registrar(resp):
    log.info(
        "%s %s %s -> %s usuario=%s",
        request.remote_addr,
        request.method,
        request.full_path.rstrip("?"),
        resp.status_code,
        session.get("usuario", "-"),
    )
    return resp


@app.route("/")
def inicio():
    return pagina(
        "Inicio",
        "<section class='hero'>"
        "<div class='hero-copy'><span class='hero-kicker'>Tecnología que transforma tu hogar</span>"
        "<h1>Todo lo que tu hogar necesita, en un solo lugar.</h1>"
        "<p>Descubre electrodomésticos funcionales, diseño práctico y productos seleccionados para hacer tu día a día más sencillo.</p>"
        "<div class='hero-actions'><a class='hero-btn' href='/buscar'>Explorar productos&nbsp; &#8594;</a>"
        "<a class='hero-btn secondary' href='/resenas'>Opiniones de clientes</a></div></div>"
        "<div class='hero-art'><div class='hero-orb'><span>&#8962;</span></div></div></section>"
        "<div class='feature-grid'>"
        "<div class='feature'><span class='feature-icon'>&#10003;</span><div><strong>Compra con confianza</strong><small>Experiencia sencilla y clara</small></div></div>"
        "<div class='feature'><span class='feature-icon'>&#9671;</span><div><strong>Productos para tu hogar</strong><small>Opciones para cada espacio</small></div></div>"
        "<div class='feature'><span class='feature-icon'>&#8961;</span><div><strong>Atención cercana</strong><small>Estamos para ayudarte</small></div></div></div>"
        "<div class='section-row'><div><div class='eyebrow'>Selección destacada</div><h2>Encuentra tu próximo favorito</h2><p>Una selección de productos disponibles en nuestra tienda.</p></div><a href='/buscar'>Ver catálogo completo&nbsp; &#8594;</a></div>"
        "<div class='product-grid'>"
        "<article class='product-card'><div class='product-art'>&#129380;</div><h3>Licuadora 600W</h3><p>Practicidad para tus preparaciones diarias.</p><div class='price'>$899.00 <small>MXN</small></div></article>"
        "<article class='product-card'><div class='product-art'>&#9635;</div><h3>Microondas 20L</h3><p>Comodidad y rapidez para tu cocina.</p><div class='price'>$2,199.00 <small>MXN</small></div></article>"
        "<article class='product-card'><div class='product-art'>&#9749;</div><h3>Cafetera de goteo</h3><p>Disfruta tu café favorito en casa.</p><div class='price'>$749.00 <small>MXN</small></div></article>"
        "</div><p class='search-caption'>* Catálogo demostrativo con productos y precios ficticios para fines académicos.</p>",
    )


# ------------------------------------------------------------------- login
@app.route("/login", methods=["GET", "POST"])
def login():
    mensaje = ""
    if request.method == "POST":
        u = request.form.get("usuario", "")
        p = request.form.get("password", "")
        # SQLi: parametros separados de la consulta.
        consulta = "SELECT * FROM usuarios WHERE usuario = ? AND password = ?"
        try:
            fila = get_db().execute(consulta, (u, p)).fetchone()
        except sqlite3.Error as e:
            log.error("Error SQL en login: %s", e)
            return pagina("Iniciar sesión", "<p>Error interno de base de datos.</p>"), 500
        if fila:
            session["uid"] = fila["id"]
            session["usuario"] = fila["usuario"]
            log.info("Login correcto usuario=%s", fila["usuario"])
            return redirect("/")
        log.warning("Login fallido usuario=%r desde %s", u, request.remote_addr)
        mensaje = "<p style='color:#b00'>Usuario o contraseña incorrectos.</p>"
    return pagina(
        "Iniciar sesión",
        mensaje
        + "<form method='post'><label>Usuario</label><input name='usuario' placeholder='Escribe tu usuario' autocomplete='username'>"
        "<label>Contraseña</label><input name='password' type='password' placeholder='Escribe tu contraseña' autocomplete='current-password'>"
        "<button>Iniciar sesión</button><p class='search-caption'>Acceso de demostración para el entorno académico.</p></form>",
    )


@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")


# ----------------------------------------------------- busqueda (SQLi + XSS)
@app.route("/buscar")
def buscar():
    q = request.args.get("q", "")
    formulario = (
        "<form method='get'><input name='q' placeholder='Buscar producto'>"
        "<button>Buscar</button></form>"
    )
    if not q:
        return pagina("Buscar productos", formulario)
    # SQLi: el patron LIKE se envia como un parametro, no como SQL.
    consulta = "SELECT id, nombre, precio FROM productos WHERE nombre LIKE ?"
    try:
        filas = get_db().execute(consulta, (f"%{q}%",)).fetchall()
    except sqlite3.Error as e:
        log.error("Error SQL en busqueda: %s | q=%r", e, q)
        return pagina("Buscar productos", formulario + "<p>Error interno de base de datos.</p>"), 500
    tabla = "".join(
        f"<tr><td>{f[0]}</td><td>{f[1]}</td><td>{f[2]}</td></tr>" for f in filas
    )
    # XSS reflejado: el texto buscado se escapa antes de mostrarlo.
    return pagina(
        "Buscar productos",
        formulario
        + f"<p>Resultados para: {html.escape(q)}</p>"
        + "<table><tr><th>ID</th><th>Producto</th><th>Precio</th></tr>"
        + tabla
        + "</table>",
    )


# ------------------------------------------------------------ resenas (XSS)
@app.route("/resenas", methods=["GET", "POST"])
def resenas():
    db = get_db()
    if request.method == "POST":
        autor = request.form.get("autor", "Anonimo")
        texto = request.form.get("texto", "")
        db.execute("INSERT INTO resenas(autor, texto) VALUES (?, ?)", (autor, texto))
        db.commit()
        return redirect("/resenas")
    filas = db.execute("SELECT autor, texto FROM resenas ORDER BY id").fetchall()
    # XSS almacenado: autor y texto se escapan antes de mostrarlos.
    lista = "".join(f"<li><b>{html.escape(f['autor'])}</b>: {html.escape(f['texto'])}</li>" for f in filas)
    return pagina(
        "Reseñas de clientes",
        f"<ul class='review-list'>{lista}</ul><hr><form method='post'>"
        "Nombre: <input name='autor'><br><br>"
        "Comentario: <input name='texto' size='50'><br><br>"
        "<button>Publicar</button></form>",
    )


# ----------------------------------------------------------- pedidos (IDOR)
def _pedido(pid):
    return get_db().execute("SELECT * FROM pedidos WHERE id = ?", (pid,)).fetchone()


@app.route("/pedido/<int:pid>")
def ver_pedido(pid):
    if "uid" not in session:
        return redirect("/login")
    fila = _pedido(pid)
    if fila is None:
        return pagina("Pedido", "<p>Pedido no encontrado.</p>"), 404
    # IDOR/BOLA: verificar el propietario del recurso.
    if fila["usuario_id"] != session["uid"]:
        return pagina("Acceso denegado", "<p>Acceso denegado: ese pedido no es tuyo.</p>"), 403
    return pagina(
        f"Pedido {fila['id']}",
        f"<table><tr><th>Producto</th><td>{fila['producto']}</td></tr>"
        f"<tr><th>Total</th><td>${fila['total']}</td></tr>"
        f"<tr><th>Dirección</th><td>{fila['direccion']}</td></tr>"
        f"<tr><th>Teléfono</th><td>{fila['telefono']}</td></tr></table>",
    )


@app.route("/api/pedidos/<int:pid>")
def api_pedido(pid):
    if "uid" not in session:
        return jsonify(error="No autenticado"), 401
    fila = _pedido(pid)
    if fila is None:
        return jsonify(error="No encontrado"), 404
    if fila["usuario_id"] != session["uid"]:
        return jsonify(error="Acceso denegado"), 403
    return jsonify(dict(fila))


if __name__ == "__main__":
    init_db()
    app.run(host="127.0.0.1", port=5000, debug=False)

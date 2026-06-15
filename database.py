import sqlite3

conexion = sqlite3.connect(
    "pinterest.db",
    check_same_thread=False
)

cursor = conexion.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS usuarios(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre TEXT NOT NULL,
    correo TEXT NOT NULL UNIQUE,
    password TEXT NOT NULL
)
""")

# TABLA ACTUALIZADA CON LA COLUMNA CATEGORÍA
cursor.execute("""
CREATE TABLE IF NOT EXISTS publicaciones(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    titulo TEXT NOT NULL,
    descripcion TEXT,
    imagen TEXT,
    categoria TEXT DEFAULT 'Otros',
    usuario_id INTEGER,
    creado_en DATETIME DEFAULT CURRENT_TIMESTAMP
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS comentarios(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    comentario TEXT NOT NULL,
    usuario_id INTEGER,
    publicacion_id INTEGER
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS guardados(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    usuario_id INTEGER,
    publicacion_id INTEGER
)
""")

conexion.commit()
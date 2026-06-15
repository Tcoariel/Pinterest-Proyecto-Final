import os
from dotenv import load_dotenv
from fastapi import FastAPI, File, UploadFile, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from database import conexion
import boto3
import uuid


load_dotenv()

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

S3_BUCKET_NAME = "pinterest-uide-pereira"
S3_REGION = "us-east-2"

s3_client = boto3.client(
    's3',
    aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
    aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY')
)

@app.post("/registro")
def registro(nombre: str = Form(...), correo: str = Form(...), password: str = Form(...)):
    cursor = conexion.cursor()
    cursor.execute("INSERT INTO usuarios(nombre,correo,password) VALUES(?,?,?)", (nombre, correo, password))
    conexion.commit()
    
    cursor.execute("SELECT id FROM usuarios WHERE correo = ?", (correo,))
    nuevo_usuario = cursor.fetchone()
    return {"mensaje": "usuario registered", "usuario_id": nuevo_usuario[0]}

@app.post("/login")
def login(correo: str = Form(...), password: str = Form(...)):
    cursor = conexion.cursor()
    cursor.execute("SELECT id, nombre FROM usuarios WHERE correo=? AND password=?", (correo, password))
    usuario = cursor.fetchone()
    if usuario:
        return {"id": usuario[0], "nombre": usuario[1]}
    return {"mensaje": "error"}

@app.post("/publicacion")
def publicacion(
    titulo: str = Form(...), 
    descripcion: str = Form(""), 
    categoria: str = Form("Otros"), 
    usuario_id: int = Form(...), 
    file: UploadFile = File(...)
):
    cursor = conexion.cursor()
    cursor.execute("SELECT id FROM usuarios WHERE id = ?", (usuario_id,))
    if not cursor.fetchone() or usuario_id <= 0:
        return {"mensaje": "error", "detalle": "Es obligatorio iniciar sesión."}

    nombre_archivo = f"{uuid.uuid4()}-{file.filename}"
    try:
        s3_client.upload_fileobj(
            file.file, 
            S3_BUCKET_NAME, 
            nombre_archivo, 
            ExtraArgs={"ContentType": file.content_type}
        )
        url_imagen = f"https://{S3_BUCKET_NAME}.s3.{S3_REGION}.amazonaws.com/{nombre_archivo}"
        
        cursor.execute(
            "INSERT INTO publicaciones(titulo,descripcion,imagen,categoria,usuario_id) VALUES(?,?,?,?,?)", 
            (titulo, descripcion, url_imagen, categoria, usuario_id)
        )
        conexion.commit()
        return {"mensaje": "publicacion creada"}
    except Exception as e:
        return {"mensaje": "error", "detalle": str(e)}

@app.get("/publicaciones")
def publicaciones():
    cursor = conexion.cursor()
    cursor.execute("SELECT id, titulo, descripcion, imagen, categoria FROM publicaciones ORDER BY id DESC")
    pines_crudos = cursor.fetchall()
    
    resultado = []
    for pin in pines_crudos:
        resultado.append({
            "id": pin[0],
            "titulo": pin[1],
            "descripcion": pin[2],
            "imagen": pin[3],
            "categoria": pin[4] if pin[4] else "Otros"
        }
                        )
    return resultado

@app.get("/publicacion/{id}")
def publicacion_id(id: int):
    cursor = conexion.cursor()
    cursor.execute("""
        SELECT p.id, p.titulo, p.descripcion, p.imagen, p.usuario_id, p.creado_en, IFNULL(u.nombre, 'Anónimo') 
        FROM publicaciones p 
        LEFT JOIN usuarios u ON p.usuario_id = u.id 
        WHERE p.id=?
    """, 
                   (id,))
    pub = cursor.fetchone()
    if pub:
        return {
            "id": pub[0],
            "titulo": pub[1],
            "descripcion": pub[2],
            "imagen": pub[3],
            "usuario_id": pub[4],
            "creado_en": pub[5],
            "autor_nombre": pub[6]
        }
        
    return None

@app.get("/usuario/{id}")
def usuario(id: int):
    cursor = conexion.cursor()
    cursor.execute("SELECT id, nombre, correo FROM usuarios WHERE id=?", (id,))
    user = cursor.fetchone()
    if user:
        return {"id": user[0], "nombre": user[1], "correo": user[2]}
    return {"mensaje": "error"}

@app.get("/usuario_publicaciones/{id}")
def usuario_publicaciones(id: int):
    cursor = conexion.cursor()
    cursor.execute("SELECT id, titulo, descripcion, imagen, categoria FROM publicaciones WHERE usuario_id=?", (id,))
    pines_crudos = cursor.fetchall()
    
    resultado = []
    for pin in pines_crudos:
        resultado.append({
            "id": pin[0],
            "titulo": pin[1],
            "descripcion": pin[2],
            "imagen": pin[3],
            "categoria": pin[4] if pin[4] else "Otros"
        })
    return resultado

@app.post("/comentario")
def comentario(comentario: str = Form(...), usuario_id: int = Form(...), publicacion_id: int = Form(...)):
    cursor = conexion.cursor()
    cursor.execute("SELECT id FROM usuarios WHERE id = ?", (usuario_id,))
    if not cursor.fetchone() or usuario_id <= 0:
        return {"mensaje": "error", "detalle": "Acceso denegado."}

    cursor.execute("INSERT INTO comentarios(comentario,usuario_id,publicacion_id) VALUES(?,?,?)", (comentario, usuario_id, publicacion_id))
    conexion.commit()
    return {"mensaje": "comentario agregado"}

@app.get("/comentarios/{id}")
def comentarios(id: int):
    cursor = conexion.cursor()
    cursor.execute("""
        SELECT c.id, c.comentario, IFNULL(u.nombre, 'Anónimo') 
        FROM comentarios c 
        LEFT JOIN usuarios u ON c.usuario_id = u.id 
        WHERE c.publicacion_id=?
        ORDER BY c.id DESC
    """, 
                   (id,))
    return cursor.fetchall()

app.mount("/", StaticFiles(directory=".", html=True), name="static")

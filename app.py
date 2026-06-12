import os
import time
from flask import Flask, jsonify, render_template_string
import psycopg2
from psycopg2.extras import RealDictCursor

app = Flask(__name__)

# Leer variables de entorno desde el .env (inyectadas por Docker Compose)
APP_NAME = os.getenv("APP_NAME", "Aplicación Flask")
APP_VERSION = os.getenv("APP_VERSION", "1.0.0")
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_NAME = os.getenv("DB_NAME", "postgres")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "postgres")

def get_db_connection():
    """Intenta conectar a la base de datos con reintentos si no está lista."""
    retries = 5
    while retries > 0:
        try:
            conn = psycopg2.connect(
                host=DB_HOST,
                database=DB_NAME,
                user=DB_USER,
                password=DB_PASSWORD,
                port=5432
            )
            return conn
        except psycopg2.OperationalError:
            retries -= 1
            time.sleep(2)
    return None

def init_db():
    """Crea la tabla e inserta los 5 registros requeridos por el examen."""
    conn = get_db_connection()
    if conn:
        cursor = conn.cursor()
        # Crear tabla productos
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS productos (
                id SERIAL PRIMARY KEY,
                nombre VARCHAR(100) NOT NULL,
                precio NUMERIC(10, 2) NOT NULL,
                stock INT NOT NULL
            );
        ''')
        
        # Verificar si ya hay datos para no duplicar en cada reinicio
        cursor.execute("SELECT COUNT(*) FROM productos;")
        if cursor.fetchone()[0] == 0:
            productos_iniciales = [
                ('Camiseta Oversize Studio Melek', 25.00, 50),
                ('Jean Slim Fit Ironcode', 45.50, 30),
                ('Chompa Impermeable', 60.00, 15),
                ('Gorra Trucker', 15.00, 100),
                ('Medias Deportivas Pack x3', 12.00, 80)
            ]
            cursor.executemany(
                "INSERT INTO productos (nombre, precio, stock) VALUES (%s, %s, %s);",
                productos_iniciales
            )
        conn.commit()
        cursor.close()
        conn.close()

# Inicializar la base de datos al arrancar
init_db()

@app.route('/')
def home():
    """Ruta principal solicitada por el examen."""
    conn = get_db_connection()
    if conn:
        status = " Conectado exitosamente a PostgreSQL"
        conn.close()
    else:
        status = "Error de conexión con PostgreSQL"
        
    html_template = """
    <h1>Examen Práctico de DevOps</h1>
    <p><strong>Nombre de la App:</strong> {{ name }}</p>
    <p><strong>Versión:</strong> {{ version }}</p>
    <p><strong>Estado de la Base de Datos:</strong> {{ status }}</p>
    <hr>
    <p><a href="/productos"> Ver todos los productos en formato JSON</a></p>
    """
    return render_template_string(html_template, name=APP_NAME, version=APP_VERSION, status=status)

@app.route('/productos')
def listar_productos():
    """Ruta para consultar y visualizar los productos almacenados."""
    conn = get_db_connection()
    if not conn:
        return jsonify({"error": "No se pudo conectar a la base de datos"}), 500
    
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    cursor.execute("SELECT * FROM productos;")
    productos = cursor.fetchall()
    cursor.close()
    conn.close()
    
    return jsonify(productos)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000)
import sqlite3
import os

# Definimos la ruta de la base de datos dentro de la carpeta 'data'
DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'propyme_pos.db')

def get_connection():
    """Crea y retorna una conexión a la base de datos SQLite."""
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row 
    return conn

def init_db():
    """Inicializa la base de datos creando las tablas requeridas si no existen."""
    conn = get_connection()
    cursor = conn.cursor()

    # 1. Tabla: PRODUCTOS
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS productos (
            id_producto INTEGER PRIMARY KEY AUTOINCREMENT,
            codigo_qr TEXT,
            sku TEXT UNIQUE,
            nombre_producto TEXT NOT NULL,
            categoria TEXT,
            costo_compra_neto REAL,
            precio_venta_base REAL NOT NULL,
            descuento_producto REAL DEFAULT 0,
            valor_final REAL NOT NULL,
            stock_actual INTEGER NOT NULL DEFAULT 0,
            stock_minimo INTEGER DEFAULT 5,
            estado_producto TEXT DEFAULT 'Activo',
            fecha_ultima_compra TEXT
        )
    ''')

    # 2. Tabla: VENTAS
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS ventas (
            id_venta INTEGER PRIMARY KEY AUTOINCREMENT,
            fecha TEXT NOT NULL,
            hora TEXT NOT NULL,
            total_valor_final REAL NOT NULL,
            descuento_general REAL DEFAULT 0,
            total_monto REAL NOT NULL,
            turno TEXT NOT NULL,
            id_usuario INTEGER,
            FOREIGN KEY (id_usuario) REFERENCES usuarios(id_usuario)
        )
    ''')

    # 3. Tabla: VENTA_ITEMS
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS venta_items (
            id_item INTEGER PRIMARY KEY AUTOINCREMENT,
            id_venta INTEGER NOT NULL,
            id_producto INTEGER NOT NULL,
            cantidad INTEGER NOT NULL,
            precio_base REAL NOT NULL,
            valor_final REAL NOT NULL,
            subtotal REAL NOT NULL,
            FOREIGN KEY (id_venta) REFERENCES ventas(id_venta),
            FOREIGN KEY (id_producto) REFERENCES productos(id_producto)
        )
    ''')

    # 4. Tabla: CAJA
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS caja (
            id_caja INTEGER PRIMARY KEY AUTOINCREMENT,
            id_venta INTEGER NOT NULL,
            total_monto REAL NOT NULL,
            descuento_final REAL DEFAULT 0,
            total_pagar REAL NOT NULL,
            medio_pago TEXT NOT NULL,
            impuesto_monto REAL NOT NULL,
            monto_venta REAL NOT NULL,
            descuentos_totales REAL DEFAULT 0,
            FOREIGN KEY (id_venta) REFERENCES ventas(id_venta)
        )
    ''')

    # 5. Tabla: USUARIOS (Control de Roles y Accesos)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS usuarios (
            id_usuario INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL,
            pin_seguridad TEXT NOT NULL,
            rol TEXT NOT NULL DEFAULT 'Vendedor',
            estado TEXT DEFAULT 'Activo',
            fecha_creacion DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Inserción inicial de usuarios por defecto (solo si la tabla está vacía)
    cursor.execute('SELECT COUNT(*) FROM usuarios')
    total_usuarios = cursor.fetchone()[0]
    
    if total_usuarios == 0:
        usuarios_iniciales = [
            ("Administrador", "1234", "Administrador"),
            ("Cajero 1", "0000", "Vendedor")
        ]
        cursor.executemany('''
            INSERT INTO usuarios (nombre, pin_seguridad, rol)
            VALUES (?, ?, ?)
        ''', usuarios_iniciales)
        print("Usuarios base creados: Admin (PIN: 1234), Cajero (PIN: 0000)")

    conn.commit()
    conn.close()
    print("Base de datos inicializada correctamente.")

if __name__ == '__main__':
    init_db()
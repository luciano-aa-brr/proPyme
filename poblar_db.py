import sqlite3
from database.connection import get_connection

def inicializar_y_poblar_db():
    productos_demo = [
        # --- ABARROTES Y LÁCTEOS (Por Unidad) ---
        ("AB-001", "780290000101", "Aceite Vegetal 1L", "Abarrotes", "UN", 1600, 2290, 0, 24, 6),
        ("AB-002", "780290000102", "Arroz Grado 1 1kg", "Abarrotes", "UN", 900, 1350, 0, 30, 10),
        ("AB-003", "780290000103", "Fideos Tallarines 400g", "Abarrotes", "UN", 550, 890, 0, 40, 10),
        ("LA-001", "780123450001", "Leche Entera 1L", "Lácteos", "UN", 800, 1150, 0, 20, 5),
        ("LA-002", "780123450002", "Yogurt Batido 120g", "Lácteos", "UN", 220, 380, 0, 50, 12),

        # --- BEBIDAS Y SNACKS (Por Unidad) ---
        ("BE-001", "780500000201", "Bebida Coca-Cola 1.5L", "Bebidas", "UN", 1300, 1890, 0, 18, 6),
        ("BE-002", "780500000202", "Agua Mineral sin Gas 1.5L", "Bebidas", "UN", 600, 990, 0, 25, 8),
        ("SN-001", "780700000301", "Papas Fritas 130g", "Snacks", "UN", 1100, 1650, 0, 15, 5),
        ("SN-002", "780700000302", "Galletas Tritón 126g", "Snacks", "UN", 600, 950, 0, 30, 10),

        # --- FRUTAS Y VERDURAS (Por Kilo) ---
        ("FV-001", None, "Manzanas Fuji (kg)", "Frutas y Verduras", "KG", 850, 1490, 0, 12.500, 3.000),
        ("FV-002", None, "Plátanos (kg)", "Frutas y Verduras", "KG", 900, 1590, 0, 18.200, 4.000),
        ("FV-003", None, "Tomates Larga Vida (kg)", "Frutas y Verduras", "KG", 1100, 1890, 0, 15.000, 5.000),

        # --- CECINAS, QUESOS Y PANADERÍA (Por Kilo / Fraccionado) ---
        ("PA-001", None, "Pan Marraqueta (kg)", "Panadería", "KG", 1300, 1990, 0, 25.000, 5.000),
        ("CE-001", None, "Queso Gouda Laminado (kg)", "Fiambrería", "KG", 6500, 9890, 0, 5.400, 1.500),
        ("CE-002", None, "Jamón Cervezero (kg)", "Fiambrería", "KG", 4200, 6490, 0, 6.800, 2.000),
    ]

    try:
        conn = get_connection()
        cursor = conn.cursor()

        # 1. Crear tabla TERMINALES
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS terminales (
                id_terminal INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre TEXT NOT NULL,
                activa BOOLEAN DEFAULT 1
            )
        ''')

        # Insertar un terminal por defecto si no existe ninguno
        cursor.execute("SELECT COUNT(*) FROM terminales")
        if cursor.fetchone()[0] == 0:
            cursor.execute("INSERT INTO terminales (nombre, activa) VALUES ('Caja Principal', 1)")

        # 2. Crear tabla PRODUCTOS
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS productos (
                id_producto INTEGER PRIMARY KEY AUTOINCREMENT,
                codigo_qr TEXT UNIQUE,
                sku TEXT UNIQUE NOT NULL,
                nombre_producto TEXT NOT NULL,
                categoria TEXT,
                unidad_medida TEXT DEFAULT 'UN' NOT NULL,
                costo_compra_neto REAL DEFAULT 0.0 NOT NULL,
                precio_venta_base REAL NOT NULL,
                descuento_producto REAL DEFAULT 0.0,
                valor_final REAL NOT NULL,
                stock_actual REAL DEFAULT 0.0,
                stock_minimo REAL DEFAULT 0.0,
                estado_producto TEXT DEFAULT 'Activo',
                fecha_ultima_compra DATE
            )
        ''')

        # 3. Crear tabla VENTAS
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS ventas (
                id_venta INTEGER PRIMARY KEY AUTOINCREMENT,
                id_terminal INTEGER NOT NULL,
                fecha DATE,
                hora TIME,
                turno TEXT,
                total_valor_final REAL DEFAULT 0.0,
                descuento_general REAL DEFAULT 0.0,
                total_monto REAL DEFAULT 0.0,
                FOREIGN KEY (id_terminal) REFERENCES terminales (id_terminal)
            )
        ''')

        # 4. Crear tabla VENTA_ITEMS
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS venta_items (
                id_item INTEGER PRIMARY KEY AUTOINCREMENT,
                id_venta INTEGER NOT NULL,
                id_producto INTEGER NOT NULL,
                cantidad REAL NOT NULL,
                precio_base REAL NOT NULL,
                valor_final REAL NOT NULL,
                subtotal REAL NOT NULL,
                FOREIGN KEY (id_venta) REFERENCES ventas (id_venta),
                FOREIGN KEY (id_producto) REFERENCES productos (id_producto)
            )
        ''')

        # 5. Crear tabla CAJA
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS caja (
                id_caja INTEGER PRIMARY KEY AUTOINCREMENT,
                id_venta INTEGER UNIQUE NOT NULL,
                total_monto REAL NOT NULL,
                descuento_final REAL DEFAULT 0.0,
                total_pagar REAL NOT NULL,
                medio_pago TEXT NOT NULL,
                impuesto_monto REAL DEFAULT 0.0,
                monto_venta REAL NOT NULL,
                descuentos_totales REAL DEFAULT 0.0,
                FOREIGN KEY (id_venta) REFERENCES ventas (id_venta)
            )
        ''')

        # 6. Insertar los productos de ejemplo
        query_insert = '''
            INSERT INTO productos (
                sku, codigo_qr, nombre_producto, categoria, unidad_medida,
                costo_compra_neto, precio_venta_base, descuento_producto, valor_final, 
                stock_actual, stock_minimo, estado_producto
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'Activo')
        '''

        for prod in productos_demo:
            sku, qr, nombre, cat, unidad, costo, precio, desc, stock, stock_min = prod
            valor_final = max(0.0, precio - desc)
            
            try:
                cursor.execute(query_insert, (
                    sku, qr, nombre, cat, unidad, 
                    costo, precio, desc, valor_final, 
                    stock, stock_min
                ))
            except sqlite3.IntegrityError:
                pass

        conn.commit()
        print("¡Estructura de la base de datos (ventas, caja, ítems) creada y poblada con éxito!")

    except Exception as e:
        print(f"Error al inicializar la base de datos: {str(e)}")
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    inicializar_y_poblar_db()
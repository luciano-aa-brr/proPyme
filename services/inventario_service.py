import sqlite3
from database.connection import get_connection

def crear_producto(sku, codigo_qr, nombre_producto, categoria, costo_neto, precio_base, stock_inicial, stock_minimo):
    """
    Recibe los datos del producto, aplica lógica de negocio y lo guarda en la base de datos.
    Retorna una tupla: (éxito: bool, mensaje: str)
    """
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        # --- LÓGICA DE NEGOCIO BÁSICA ---
        # Por defecto, al crear, el valor final es igual al precio base (sin descuentos aún)
        valor_final = precio_base
        
        # Consulta SQL parametrizada (Evita inyecciones SQL y errores de formato)
        query = '''
            INSERT INTO productos (
                sku, codigo_qr, nombre_producto, categoria, 
                costo_compra_neto, precio_venta_base, valor_final, 
                stock_actual, stock_minimo
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        '''
        
        # Ejecutamos la inserción
        cursor.execute(query, (
            sku, codigo_qr, nombre_producto, categoria, 
            costo_neto, precio_base, valor_final, 
            stock_inicial, stock_minimo
        ))
        
        conn.commit()
        return True, "Producto guardado con éxito."

    except sqlite3.IntegrityError:
        # Esto salta automáticamente si intentas guardar un SKU que ya existe en la base de datos
        return False, "Error: El SKU ingresado ya existe en el sistema."
    
    except Exception as e:
        # Atrapa cualquier otro error inesperado
        return False, f"Error interno: {str(e)}"
        
    finally:
        # Siempre nos aseguramos de cerrar la conexión
        if 'conn' in locals():
            conn.close()

def obtener_todos_los_productos():
    """
    Obtiene la lista completa de productos para llenar la tabla de la interfaz.
    """
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM productos ORDER BY id_producto DESC")
        # esto retorna diccionarios, no solo tuplas
        productos = cursor.fetchall() 
        
        return True, productos
        
    except Exception as e:
        return False, f"Error al obtener productos: {str(e)}"
        
    finally:
        if 'conn' in locals():
            conn.close()
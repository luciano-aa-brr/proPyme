import sqlite3
from database.connection import get_connection

def crear_producto(sku, codigo_qr, nombre_producto, categoria, costo_neto, precio_base, 
                   stock_inicial=0.0, stock_minimo=0.0, unidad_medida="UN", descuento=0.0):
    """
    Recibe los datos del producto, valida campos obligatorios, aplica lógica 
    de negocio y lo guarda en la base de datos.
    Retorna: (éxito: bool, mensaje: str)
    """
    # --- VALIDACIONES DE CAMPOS OBLIGATORIOS Y NULOS ---
    if not sku or not str(sku).strip():
        return False, "El campo SKU es obligatorio."
    
    if not nombre_producto or not str(nombre_producto).strip():
        return False, "El nombre del producto es obligatorio."

    # Sanitización y casting de valores numéricos
    try:
        costo_neto = float(costo_neto) if costo_neto is not None else -1.0
        precio_base = float(precio_base) if precio_base is not None else -1.0
        
        if costo_neto < 0:
            return False, "El costo de compra es obligatorio y debe ser mayor o igual a 0."
        if precio_base <= 0:
            return False, "El precio de venta es obligatorio y debe ser mayor a 0."

        # Manejo seguro de stocks opcionales (evita fallos por inputs vacíos)
        stock_inicial = float(stock_inicial) if (stock_inicial is not None and str(stock_inicial).strip() != "") else 0.0
        stock_minimo = float(stock_minimo) if (stock_minimo is not None and str(stock_minimo).strip() != "") else 0.0
        descuento = float(descuento) if (descuento is not None and str(descuento).strip() != "") else 0.0

    except ValueError:
        return False, "Los campos numéricos (costos, precios, stocks) contienen formatos inválidos."

    # --- LÓGICA DE NEGOCIO ---
    # Cálculo del valor final considerando el descuento aplicado
    valor_final = max(0.0, precio_base - descuento)

    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        query = '''
            INSERT INTO productos (
                sku, codigo_qr, nombre_producto, categoria, unidad_medida,
                costo_compra_neto, precio_venta_base, descuento_producto, valor_final, 
                stock_actual, stock_minimo, estado_producto
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'Activo')
        '''
        
        cursor.execute(query, (
            sku.strip(), 
            codigo_qr.strip() if codigo_qr else None, 
            nombre_producto.strip(), 
            categoria, 
            unidad_medida,
            costo_neto, 
            precio_base, 
            descuento, 
            valor_final, 
            stock_inicial, 
            stock_minimo
        ))
        
        conn.commit()
        return True, "Producto guardado con éxito."

    except sqlite3.IntegrityError as e:
        error_msg = str(e).lower()
        if "sku" in error_msg:
            return False, f"El SKU '{sku}' ya se encuentra registrado en el sistema."
        elif "codigo_qr" in error_msg:
            return False, "El Código QR/Barras ya se encuentra registrado."
        return False, "Error de duplicidad: El SKU o Código QR ya existe."
    
    except Exception as e:
        return False, f"Error interno al guardar: {str(e)}"
        
    finally:
        if 'conn' in locals():
            conn.close()


def obtener_todos_los_productos():
    """
    Obtiene la lista de productos activos para llenar la tabla de la interfaz.
    """
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT * FROM productos 
            WHERE estado_producto = 'Activo' 
            ORDER BY id_producto DESC
        """)
        productos = cursor.fetchall() 
        
        return True, productos
        
    except Exception as e:
        return False, f"Error al obtener productos: {str(e)}"
        
    finally:
        if 'conn' in locals():
            conn.close()


def buscar_productos(criterio):
    """
    Busca productos activos por nombre, SKU o categoría con coincidencia parcial.
    """
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        param = f"%{criterio.strip()}%"
        query = """
            SELECT * FROM productos 
            WHERE estado_producto = 'Activo' 
              AND (nombre_producto LIKE ? OR sku LIKE ? OR categoria LIKE ?)
            ORDER BY nombre_producto ASC
        """
        cursor.execute(query, (param, param, param))
        productos = cursor.fetchall()
        
        return True, productos
    except Exception as e:
        return False, f"Error en la búsqueda: {str(e)}"
    finally:
        if 'conn' in locals():
            conn.close()


def eliminar_producto_logico(id_producto):
    """
    Realiza un borrado lógico del producto cambiando su estado a 'Inactivo'.
    Evita romper la integridad referencial de ventas pasadas.
    """
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE productos 
            SET estado_producto = 'Inactivo' 
            WHERE id_producto = ?
        """, (id_producto,))
        
        conn.commit()
        return True, "Producto eliminado correctamente."
    except Exception as e:
        return False, f"Error al eliminar el producto: {str(e)}"
    finally:
        if 'conn' in locals():
            conn.close()
import sqlite3
from database.connection import get_connection
from datetime import datetime 


def buscar_producto_para_venta(criterio):
    """
    Busca un producto por SKU, QR o coincidencia de nombre.
    Retorna (éxito: bool, resultado: dict/str)
    """
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        # Buscamos coincidencias exactas en SKU/QR, o parciales en el nombre
        query = '''
            SELECT id_producto, sku, nombre_producto, precio_venta_base, valor_final, stock_actual 
            FROM productos 
            WHERE sku = ? OR codigo_qr = ? OR nombre_producto LIKE ?
            LIMIT 1
        '''
        
        # búsquedas parciales (ej: si buscas "Mouse", encuentra "Mousepad")
        cursor.execute(query, (criterio, criterio, f'%{criterio}%'))
        producto = cursor.fetchone()
        
        if producto:
            if producto['stock_actual'] <= 0:
                return False, f"El producto '{producto['nombre_producto']}' no tiene stock disponible."
            
            return True, dict(producto) 
        else:
            return False, "Producto no encontrado. Verifique el código o nombre."

    except Exception as e:
        return False, f"Error en la base de datos: {str(e)}"
    finally:
        if 'conn' in locals():
            conn.close()
            

def registrar_venta(carrito, turno="Mañana"):
    """
    Toma los items del carrito, crea la venta, guarda el detalle y descuenta el stock.
    Todo en una sola transacción segura.
    """
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        # Obtenemos la fecha y hora actual del sistema
        ahora = datetime.now()
        fecha_str = ahora.strftime("%Y-%m-%d")
        hora_str = ahora.strftime("%H:%M:%S")
        
        # Calculamos los totales en el backend 
        total_valor_final = sum(item['subtotal'] for item in carrito)
        descuento_general = 0
        total_monto = total_valor_final - descuento_general
        
        # 1. Insertamos la cabecera de la venta 
        cursor.execute('''
            INSERT INTO ventas (fecha, hora, total_valor_final, descuento_general, total_monto, turno)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (fecha_str, hora_str, total_valor_final, descuento_general, total_monto, turno))
        
        # Obtenemos el ID que SQLite le asignó automáticamente a esta nueva venta
        id_venta = cursor.lastrowid 
        
        # 2. Insertamos cada producto en el detalle y descontamos stock 
        for item in carrito:
            # Guardar el item de la venta
            cursor.execute('''
                INSERT INTO venta_items (id_venta, id_producto, cantidad, precio_base, valor_final, subtotal)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (id_venta, item['id_producto'], item['cantidad'], item['precio_base'], item['valor_final'], item['subtotal']))
            
            # Descontar el stock del inventario
            cursor.execute('''
                UPDATE productos 
                SET stock_actual = stock_actual - ? 
                WHERE id_producto = ?
            ''', (item['cantidad'], item['id_producto']))
            
        # guardamos los cambios (Transacción exitosa)
        conn.commit()
        return True, id_venta
        
    except Exception as e:
        # Si algo falló, deshacemos todos los cambios para no corromper la BD
        if 'conn' in locals():
            conn.rollback() 
        return False, f"Error al registrar la venta: {str(e)}"
        
    finally:
        if 'conn' in locals():
            conn.close()
import sqlite3
from datetime import datetime, date
from database.connection import get_connection

def buscar_producto_para_venta(criterio):
    """Busca un producto por código QR, SKU o nombre para agregarlo al carrito."""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        criterio_clean = criterio.strip()
        query = """
            SELECT id_producto, sku, codigo_qr, nombre_producto, 
                   precio_venta_base, valor_final, stock_actual, unidad_medida
            FROM productos
            WHERE estado_producto = 'Activo' 
              AND (codigo_qr = ? OR sku = ? OR nombre_producto LIKE ?)
            LIMIT 1
        """
        cursor.execute(query, (criterio_clean, criterio_clean, f"%{criterio_clean}%"))
        prod = cursor.fetchone()
        
        if not prod:
            return False, f"No se encontró ningún producto con '{criterio}'."
            
        es_dict = isinstance(prod, dict)
        producto_data = {
            "id_producto": prod["id_producto"] if es_dict else prod[0],
            "sku": prod["sku"] if es_dict else prod[1],
            "codigo_qr": prod["codigo_qr"] if es_dict else prod[2],
            "nombre_producto": prod["nombre_producto"] if es_dict else prod[3],
            "precio_venta_base": prod["precio_venta_base"] if es_dict else prod[4],
            "valor_final": prod["valor_final"] if es_dict else prod[5],
            "stock_actual": prod["stock_actual"] if es_dict else prod[6],
            "unidad_medida": prod["unidad_medida"] if es_dict else prod[7]
        }
        
        return True, producto_data
    except Exception as e:
        return False, f"Error al buscar producto: {str(e)}"
    finally:
        if 'conn' in locals() and conn:
            conn.close()


def registrar_venta_directa(carrito, medio_pago, id_terminal=1):
    """Registra la venta, descuenta stock e inserta el cobro en la tabla 'caja'."""
    if not carrito:
        return False, "El carrito está vacío."
        
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        total_valor_final = sum(float(item['subtotal']) for item in carrito)
        total_monto = total_valor_final
        fecha_actual = date.today().strftime('%Y-%m-%d')
        hora_actual = datetime.now().strftime('%H:%M:%S')

        # 1. Insertar Cabecera de Venta
        query_venta = """
            INSERT INTO ventas (
                id_terminal, fecha, hora, turno, 
                total_valor_final, descuento_general, total_monto
            ) VALUES (?, ?, ?, 'General', ?, 0.0, ?)
        """
        cursor.execute(query_venta, (id_terminal, fecha_actual, hora_actual, total_valor_final, total_monto))
        id_venta = cursor.lastrowid

        # 2. Registrar Ítems y Descontar Stock
        query_item = """
            INSERT INTO venta_items (
                id_venta, id_producto, cantidad, precio_base, valor_final, subtotal
            ) VALUES (?, ?, ?, ?, ?, ?)
        """
        query_stock = """
            UPDATE productos 
            SET stock_actual = ROUND(stock_actual - ?, 3) 
            WHERE id_producto = ?
        """

        for item in carrito:
            cant = float(item['cantidad'])
            prod_id = int(item['id_producto'])

            cursor.execute(query_item, (
                id_venta, 
                prod_id, 
                cant, 
                float(item['precio_base']), 
                float(item['valor_final']), 
                float(item['subtotal'])
            ))
            cursor.execute(query_stock, (cant, prod_id))

        # 3. Registrar Cobro en Tabla 'caja'
        query_caja = """
            INSERT INTO caja (
                id_venta, total_monto, descuento_final, total_pagar, 
                medio_pago, impuesto_monto, monto_venta, descuentos_totales
            ) VALUES (?, ?, 0.0, ?, ?, 0.0, ?, 0.0)
        """
        cursor.execute(query_caja, (id_venta, total_monto, total_monto, medio_pago, total_monto))

        conn.commit()
        return True, id_venta

    except Exception as e:
        if 'conn' in locals() and conn:
            conn.rollback()
        return False, f"Error al procesar la venta directa: {str(e)}"
    finally:
        if 'conn' in locals() and conn:
            conn.close()
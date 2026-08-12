import sqlite3
from database.connection import get_connection

def obtener_ventas_pendientes():
    """
    Obtiene las ventas registradas que aún no tienen un pago procesado en la tabla 'caja'.
    """
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        query = """
            SELECT v.id_venta, v.fecha, v.hora, v.total_monto 
            FROM ventas v
            LEFT JOIN caja c ON v.id_venta = c.id_venta
            WHERE c.id_caja IS NULL
            ORDER BY v.id_venta DESC
        """
        cursor.execute(query)
        ventas = cursor.fetchall()
        return True, ventas
    except Exception as e:
        return False, f"Error al consultar ventas pendientes: {str(e)}"
    finally:
        if 'conn' in locals():
            conn.close()


def obtener_detalle_venta(id_venta):
    """
    Obtiene los ítems/productos asociados a un ID de venta.
    """
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        query = """
            SELECT p.nombre_producto, vi.cantidad, p.unidad_medida, vi.valor_final, vi.subtotal
            FROM venta_items vi
            JOIN productos p ON vi.id_producto = p.id_producto
            WHERE vi.id_venta = ?
        """
        cursor.execute(query, (id_venta,))
        items = cursor.fetchall()
        return True, items
    except Exception as e:
        return False, f"Error al obtener detalle de la venta: {str(e)}"
    finally:
        if 'conn' in locals():
            conn.close()


def procesar_cobro_caja(id_venta, total_monto, medio_pago):
    """
    Registra el pago de una venta en la tabla 'caja'.
    """
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        query = """
            INSERT INTO caja (
                id_venta, total_monto, descuento_final, total_pagar, 
                medio_pago, impuesto_monto, monto_venta, descuentos_totales
            ) VALUES (?, ?, 0.0, ?, ?, 0.0, ?, 0.0)
        """
        cursor.execute(query, (id_venta, total_monto, total_monto, medio_pago, total_monto))
        conn.commit()
        return True, "Cobro procesado e ingresado a caja con éxito."
    except sqlite3.IntegrityError:
        return False, "Esta venta ya fue cobrada previamente."
    except Exception as e:
        return False, f"Error al procesar el cobro: {str(e)}"
    finally:
        if 'conn' in locals():
            conn.close()


def obtener_arqueo_actual():
    """
    Calcula los totales cobrados agrupados por medio de pago.
    """
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        query = """
            SELECT medio_pago, SUM(total_pagar) as total
            FROM caja
            GROUP BY medio_pago
        """
        cursor.execute(query)
        totales = cursor.fetchall()
        
        resumen = {"Efectivo": 0.0, "Débito": 0.0, "Crédito": 0.0, "Transferencia": 0.0}
        total_general = 0.0
        
        for fila in totales:
            medio = fila["medio_pago"] if isinstance(fila, dict) else fila[0]
            monto = fila["total"] if isinstance(fila, dict) else fila[1]
            if medio in resumen:
                resumen[medio] = monto
            total_general += monto
            
        resumen["Total"] = total_general
        return True, resumen
    except Exception as e:
        return False, f"Error al calcular el arqueo: {str(e)}"
    finally:
        if 'conn' in locals():
            conn.close()
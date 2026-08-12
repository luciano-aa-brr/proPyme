import sqlite3
from database.connection import get_connection

def obtener_historial_ventas(fecha_inicio=None, fecha_fin=None):
    """
    Obtiene las ventas registradas con su medio de pago cobrado.
    Permite filtrado opcional por rango de fechas (YYYY-MM-DD).
    """
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        query = """
            SELECT v.id_venta, v.fecha, v.hora, c.medio_pago, v.total_monto
            FROM ventas v
            JOIN caja c ON v.id_venta = c.id_venta
        """
        params = []

        if fecha_inicio and fecha_fin:
            query += " WHERE v.fecha BETWEEN ? AND ?"
            params.extend([fecha_inicio, fecha_fin])

        query += " ORDER BY v.id_venta DESC"
        
        cursor.execute(query, params)
        ventas = cursor.fetchall()
        return True, ventas
    except Exception as e:
        return False, f"Error al obtener historial de ventas: {str(e)}"
    finally:
        if 'conn' in locals():
            conn.close()


def obtener_detalle_historial(id_venta):
    """
    Obtiene los ítems/productos de una venta específica para el historial.
    """
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        query = """
            SELECT p.sku, p.nombre_producto, vi.cantidad, p.unidad_medida, vi.valor_final, vi.subtotal
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
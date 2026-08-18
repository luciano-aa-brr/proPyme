import sqlite3
from database.connection import get_connection

def obtener_historial_completo(fecha_desde=None, fecha_hasta=None, filtro_texto=None):
    """
    Retorna el historial de ventas cruzado con el medio de pago registrado en caja.
    """
    try:
        conn = get_connection()
        cursor = conn.cursor()

        query = """
            SELECT 
                v.id_venta,
                v.fecha,
                v.hora,
                v.turno,
                COALESCE(c.medio_pago, 'Efectivo') AS medio_pago,
                v.total_monto
            FROM ventas v
            LEFT JOIN caja c ON v.id_venta = c.id_venta
            WHERE 1=1
        """
        params = []

        if fecha_desde and fecha_hasta:
            query += " AND v.fecha BETWEEN ? AND ?"
            params.extend([fecha_desde, fecha_hasta])
        elif fecha_desde:
            query += " AND v.fecha >= ?"
            params.append(fecha_desde)
        elif fecha_hasta:
            query += " AND v.fecha <= ?"
            params.append(fecha_hasta)

        if filtro_texto and filtro_texto.strip():
            txt = f"%{filtro_texto.strip()}%"
            query += " AND (CAST(v.id_venta AS TEXT) LIKE ? OR v.turno LIKE ? OR c.medio_pago LIKE ?)"
            params.extend([txt, txt, txt])

        query += " ORDER BY v.id_venta DESC"

        cursor.execute(query, params)
        ventas = cursor.fetchall()

        lista_ventas = []
        for row in ventas:
            es_d = isinstance(row, dict)
            lista_ventas.append({
                "id_venta": row["id_venta"] if es_d else row[0],
                "fecha": row["fecha"] if es_d else row[1],
                "hora": row["hora"] if es_d else row[2],
                "cajero": row["turno"] if es_d else (row[3] or "Caja Principal"),
                "medio_pago": row["medio_pago"] if es_d else row[4],
                "total_monto": float(row["total_monto"] if es_d else row[5])
            })

        return True, lista_ventas
    except Exception as e:
        return False, f"Error al consultar historial: {str(e)}"
    finally:
        if 'conn' in locals() and conn:
            conn.close()


def obtener_detalle_ticket(id_venta):
    """
    Obtiene los productos vendidos en una transacción cruzando con 'productos'.
    """
    try:
        conn = get_connection()
        cursor = conn.cursor()

        query = """
            SELECT 
                COALESCE(p.sku, 'N/A') AS sku,
                COALESCE(p.nombre_producto, 'Producto') AS nombre_producto,
                vi.cantidad,
                COALESCE(p.unidad_medida, 'UN') AS unidad_medida,
                vi.valor_final,
                vi.subtotal
            FROM venta_items vi
            LEFT JOIN productos p ON vi.id_producto = p.id_producto
            WHERE vi.id_venta = ?
        """
        cursor.execute(query, (id_venta,))
        items = cursor.fetchall()

        resultado = []
        for it in items:
            es_d = isinstance(it, dict)
            resultado.append({
                "sku": it["sku"] if es_d else (it[0] or "N/A"),
                "nombre": it["nombre_producto"] if es_d else (it[1] or "Producto"),
                "cantidad": float(it["cantidad"] if es_d else it[2]),
                "unidad": it["unidad_medida"] if es_d else (it[3] or "UN"),
                "precio": float(it["valor_final"] if es_d else it[4]),
                "subtotal": float(it["subtotal"] if es_d else it[5])
            })

        return True, resultado
    except Exception as e:
        return False, f"Error al obtener detalle del ticket: {str(e)}"
    finally:
        if 'conn' in locals() and conn:
            conn.close()
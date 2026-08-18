import sqlite3
from datetime import date, datetime
from database.connection import get_connection

def buscar_producto_para_venta(termino):
    """
    Busca un producto por código de barras, SKU o coincidencia de nombre.
    """
    try:
        conn = get_connection()
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # 1. Búsqueda exacta por código de barras o SKU
        cursor.execute("""
            SELECT id_producto, sku, codigo_barras, nombre_producto, precio_costo,
                   precio_venta, stock_actual, stock_critico, unidad_medida, es_activo
            FROM productos
            WHERE es_activo = 1 AND (codigo_barras = ? OR sku = ?)
        """, (termino, termino))
        prod = cursor.fetchone()

        # 2. Si no coincide exacto, buscar por coincidencia en el nombre
        if not prod:
            cursor.execute("""
                SELECT id_producto, sku, codigo_barras, nombre_producto, precio_costo,
                       precio_venta, stock_actual, stock_critico, unidad_medida, es_activo
                FROM productos
                WHERE es_activo = 1 AND nombre_producto LIKE ?
                ORDER BY nombre_producto ASC
                LIMIT 1
            """, (f"%{termino}%",))
            prod = cursor.fetchone()

        if prod:
            p_dict = dict(prod)
            p_dict["precio_venta_base"] = p_dict["precio_venta"]
            p_dict["valor_final"] = p_dict["precio_venta"]
            return True, p_dict
        else:
            return False, f"No se encontró ningún producto activo con '{termino}'."

    except Exception as e:
        return False, f"Error al buscar producto: {str(e)}"
    finally:
        if 'conn' in locals() and conn:
            conn.close()


def registrar_venta_directa(items_carrito, medio_pago, usuario="Cajero"):
    """
    Registra la venta con validación atómica de existencias para no permitir stock negativo.
    """
    if not items_carrito:
        return False, "El carrito de compras está vacío."

    try:
        conn = get_connection()
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # 1. Validar que exista stock suficiente para cada producto
        for item in items_carrito:
            cursor.execute("SELECT nombre_producto, stock_actual FROM productos WHERE id_producto = ?", (item["id_producto"],))
            prod = cursor.fetchone()
            if not prod:
                conn.rollback()
                return False, f"El producto con ID {item['id_producto']} ya no existe."

            stock_disponible = float(prod["stock_actual"])
            cantidad_pedida = float(item["cantidad"])

            if stock_disponible < cantidad_pedida:
                conn.rollback()
                return False, f"Stock insuficiente para '{prod['nombre_producto']}'. Disponible: {stock_disponible}, Solicitado: {cantidad_pedida}."

        # 2. Insertar en tabla ventas
        total_monto = sum(float(it["subtotal"]) for it in items_carrito)
        fecha_actual = date.today().strftime('%Y-%m-%d')
        hora_actual = datetime.now().strftime('%H:%M:%S')

        cursor.execute("""
            INSERT INTO ventas (fecha, hora, total_monto, turno)
            VALUES (?, ?, ?, ?)
        """, (fecha_actual, hora_actual, total_monto, usuario))

        id_venta = cursor.lastrowid

        # 3. Insertar ítems y descontar stock
        for it in items_carrito:
            cursor.execute("""
                INSERT INTO venta_items (id_venta, id_producto, cantidad, valor_final, subtotal)
                VALUES (?, ?, ?, ?, ?)
            """, (id_venta, it["id_producto"], it["cantidad"], it["valor_final"], it["subtotal"]))

            cursor.execute("""
                UPDATE productos
                SET stock_actual = stock_actual - ?
                WHERE id_producto = ?
            """, (it["cantidad"], it["id_producto"]))

        # 4. Registrar en caja del turno activo
        cursor.execute("""
            INSERT INTO caja (id_venta, medio_pago, total_pagar)
            VALUES (?, ?, ?)
        """, (id_venta, medio_pago, total_monto))

        conn.commit()
        return True, id_venta

    except Exception as e:
        if 'conn' in locals() and conn:
            conn.rollback()
        return False, f"Error al procesar la venta: {str(e)}"
    finally:
        if 'conn' in locals() and conn:
            conn.close()
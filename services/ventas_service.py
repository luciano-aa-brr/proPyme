import sqlite3
from datetime import date, datetime
from database.connection import get_connection

def _obtener_columnas_tabla(cursor, nombre_tabla):
    """Devuelve un diccionario {nombre_columna: info} de la tabla indicada."""
    cursor.execute(f"PRAGMA table_info({nombre_tabla})")
    return {row[1]: row for row in cursor.fetchall()}

def _insertar_dinamico(cursor, nombre_tabla, datos_posibles):
    """
    Inserta únicamente las columnas que realmente existen en la tabla física de SQLite,
    garantizando compatibilidad con cualquier versión del esquema.
    """
    cols_existentes = _obtener_columnas_tabla(cursor, nombre_tabla)
    datos_filtrados = {k: v for k, v in datos_posibles.items() if k in cols_existentes}

    columnas_sql = ", ".join(datos_filtrados.keys())
    placeholders = ", ".join(["?"] * len(datos_filtrados))
    valores = tuple(datos_filtrados.values())

    cursor.execute(
        f"INSERT INTO {nombre_tabla} ({columnas_sql}) VALUES ({placeholders})",
        valores
    )
    return cursor.lastrowid

def buscar_producto_para_venta(termino):
    """
    Busca un producto por código QR, código de barra, SKU o nombre.
    """
    try:
        conn = get_connection()
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        termino_limpio = str(termino).strip()
        cols_prod = _obtener_columnas_tabla(cursor, "productos")

        # Filtro de estado activo
        filtro_estado = "1=1"
        if "estado_producto" in cols_prod:
            filtro_estado = "estado_producto = 'Activo'"
        elif "es_activo" in cols_prod:
            filtro_estado = "es_activo = 1"

        # Columnas de identificación directa
        filtros_id = []
        params_id = []

        if "codigo_qr" in cols_prod:
            filtros_id.append("codigo_qr = ?")
            params_id.append(termino_limpio)
        if "codigo_barra" in cols_prod:
            filtros_id.append("codigo_barra = ?")
            params_id.append(termino_limpio)
        if "codigo_barras" in cols_prod:
            filtros_id.append("codigo_barras = ?")
            params_id.append(termino_limpio)
        if "sku" in cols_prod:
            filtros_id.append("sku = ?")
            params_id.append(termino_limpio)

        prod = None

        # 1. Búsqueda exacta
        if filtros_id:
            query_exacta = f"""
                SELECT * FROM productos
                WHERE {filtro_estado} AND ({' OR '.join(filtros_id)})
                LIMIT 1
            """
            cursor.execute(query_exacta, params_id)
            prod = cursor.fetchone()

        # 2. Búsqueda parcial por nombre
        if not prod and "nombre_producto" in cols_prod:
            query_nombre = f"""
                SELECT * FROM productos
                WHERE {filtro_estado} AND nombre_producto LIKE ?
                ORDER BY nombre_producto ASC
                LIMIT 1
            """
            cursor.execute(query_nombre, (f"%{termino_limpio}%",))
            prod = cursor.fetchone()

        if prod:
            p_dict = dict(prod)

            precio_final = float(p_dict.get("valor_final") or p_dict.get("precio_venta") or p_dict.get("precio_venta_base") or 0.0)
            precio_base = float(p_dict.get("precio_venta_base") or p_dict.get("precio_costo") or precio_final)

            p_dict["id_producto"] = p_dict["id_producto"]
            p_dict["sku"] = str(p_dict.get("sku") or "S/SKU")
            p_dict["nombre_producto"] = str(p_dict.get("nombre_producto") or "Producto")
            p_dict["precio_base"] = precio_base
            p_dict["precio_venta_base"] = precio_base
            p_dict["valor_final"] = precio_final
            p_dict["unidad_medida"] = str(p_dict.get("unidad_medida") or "UN").upper()
            p_dict["stock_actual"] = float(p_dict.get("stock_actual") or 0.0)

            return True, p_dict
        else:
            return False, f"No se encontró ningún producto activo con '{termino_limpio}'."

    except Exception as e:
        return False, f"Error al buscar producto: {str(e)}"
    finally:
        if 'conn' in locals() and conn:
            conn.close()

def registrar_venta_directa(items_carrito, medio_pago, usuario="Cajero"):
    """
    Registra la venta de forma atómica y mapea dinámicamente todos los campos requeridos por la base de datos.
    """
    if not items_carrito:
        return False, "El carrito de compras está vacío."

    try:
        conn = get_connection()
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # 1. Validar existencias disponibles
        for item in items_carrito:
            cursor.execute("SELECT nombre_producto, stock_actual FROM productos WHERE id_producto = ?", (item["id_producto"],))
            prod = cursor.fetchone()
            if not prod:
                conn.rollback()
                return False, f"El producto con ID {item['id_producto']} ya no existe."

            stock_disponible = float(prod["stock_actual"] or 0.0)
            cantidad_pedida = float(item["cantidad"])

            if stock_disponible < cantidad_pedida:
                conn.rollback()
                return False, f"Stock insuficiente para '{prod['nombre_producto']}'. Disponible: {stock_disponible}, Solicitado: {cantidad_pedida}."

        fecha_actual = date.today().strftime('%Y-%m-%d')
        hora_actual = datetime.now().strftime('%H:%M:%S')
        total_monto = sum(float(it["subtotal"]) for it in items_carrito)

        # 2. Insertar en tabla ventas
        datos_venta = {
            "id_terminal": 1,
            "fecha": fecha_actual,
            "hora": hora_actual,
            "total_monto": total_monto,
            "total": total_monto,
            "turno": usuario,
            "cajero": usuario,
            "usuario": usuario,
            "medio_pago": medio_pago
        }
        id_venta = _insertar_dinamico(cursor, "ventas", datos_venta)

        # 3. Insertar detalle de venta y descontar stock
        for it in items_carrito:
            p_base = float(it.get("precio_base") or it.get("valor_final") or 0.0)
            p_final = float(it.get("valor_final") or p_base)
            subtotal = float(it.get("subtotal") or (p_final * float(it["cantidad"])))

            datos_item = {
                "id_venta": id_venta,
                "id_producto": it["id_producto"],
                "cantidad": float(it["cantidad"]),
                "precio_base": p_base,
                "precio_unitario": p_final,
                "valor_final": p_final,
                "subtotal": subtotal
            }
            _insertar_dinamico(cursor, "venta_items", datos_item)

            cursor.execute("""
                UPDATE productos
                SET stock_actual = stock_actual - ?
                WHERE id_producto = ?
            """, (it["cantidad"], it["id_producto"]))

        # 4. Insertar registro en caja
        datos_caja = {
            "id_terminal": 1,
            "id_venta": id_venta,
            "fecha": fecha_actual,
            "hora": hora_actual,
            "tipo_movimiento": "Venta",
            "medio_pago": medio_pago,
            "total_monto": total_monto,
            "total_pagar": total_monto,
            "monto": total_monto,
            "total": total_monto,
            "usuario": usuario,
            "cajero": usuario,
            "descripcion": f"Venta directa #{id_venta}"
        }
        _insertar_dinamico(cursor, "caja", datos_caja)

        conn.commit()
        return True, id_venta

    except Exception as e:
        if 'conn' in locals() and conn:
            conn.rollback()
        return False, f"Error al procesar la venta: {str(e)}"
    finally:
        if 'conn' in locals() and conn:
            conn.close()
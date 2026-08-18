import sqlite3
from datetime import date, datetime
from database.connection import get_connection

def _obtener_columnas_info(cursor, nombre_tabla):
    """Retorna información detallada de las columnas de una tabla."""
    cursor.execute(f"PRAGMA table_info({nombre_tabla})")
    return {
        row[1]: {
            'type': str(row[2]).upper(),
            'notnull': bool(row[3]),
            'default': row[4],
            'pk': bool(row[5])
        }
        for row in cursor.fetchall()
    }

def _insertar_inteligente(cursor, nombre_tabla, mapeo_valores):
    """
    Inserta datos en la tabla rellenando dinámicamente cualquier columna NOT NULL 
    sin valor por defecto para evitar excepciones por constraints.
    """
    cols_info = _obtener_columnas_info(cursor, nombre_tabla)
    payload = {}

    fecha_hoy = date.today().strftime('%Y-%m-%d')
    hora_hoy = datetime.now().strftime('%H:%M:%S')

    for col_nombre, info in cols_info.items():
        if info['pk']:
            continue

        if col_nombre in mapeo_valores:
            payload[col_nombre] = mapeo_valores[col_nombre]
        elif info['notnull'] and info['default'] is None:
            tipo = info['type']
            if "INT" in tipo:
                payload[col_nombre] = 1 if ("terminal" in col_nombre or "id" in col_nombre) else 0
            elif any(t in tipo for t in ["REAL", "FLOA", "NUM", "DOUB"]):
                payload[col_nombre] = 0.0
            elif "DATE" in tipo or "fecha" in col_nombre:
                payload[col_nombre] = fecha_hoy
            elif "TIME" in tipo or "hora" in col_nombre:
                payload[col_nombre] = hora_hoy
            else:
                payload[col_nombre] = "Cerrada" if "estado" in col_nombre else "N/A"

    cols_sql = ", ".join(payload.keys())
    placeholders = ", ".join(["?"] * len(payload))
    valores = tuple(payload.values())

    cursor.execute(f"INSERT INTO {nombre_tabla} ({cols_sql}) VALUES ({placeholders})", valores)
    return cursor.lastrowid

def buscar_producto_para_venta(termino):
    """
    Busca un producto por código QR, SKU o coincidencia de nombre.
    """
    try:
        conn = get_connection()
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        termino_limpio = str(termino).strip()
        cursor.execute("PRAGMA table_info(productos)")
        columnas = [col[1] for col in cursor.fetchall()]

        # 1. Filtro de estado
        filtro_estado = "estado_producto = 'Activo'" if "estado_producto" in columnas else "1=1"

        # 2. Búsqueda exacta
        filtros_id = []
        params_id = []

        if "codigo_qr" in columnas:
            filtros_id.append("codigo_qr = ?")
            params_id.append(termino_limpio)
        if "sku" in columnas:
            filtros_id.append("sku = ?")
            params_id.append(termino_limpio)

        prod = None
        if filtros_id:
            query_exacta = f"SELECT * FROM productos WHERE {filtro_estado} AND ({' OR '.join(filtros_id)}) LIMIT 1"
            cursor.execute(query_exacta, params_id)
            prod = cursor.fetchone()

        # 3. Búsqueda por nombre
        if not prod and "nombre_producto" in columnas:
            query_nombre = f"SELECT * FROM productos WHERE {filtro_estado} AND nombre_producto LIKE ? ORDER BY nombre_producto ASC LIMIT 1"
            cursor.execute(query_nombre, (f"%{termino_limpio}%",))
            prod = cursor.fetchone()

        if prod:
            p_dict = dict(prod)
            precio_final = float(p_dict.get("valor_final") or p_dict.get("precio_venta_base") or 0.0)
            precio_base = float(p_dict.get("precio_venta_base") or precio_final)

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
    Registra la venta satisfaciendo todos los constraints de la base de datos de proPyme.
    """
    if not items_carrito:
        return False, "El carrito de compras está vacío."

    try:
        conn = get_connection()
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # 1. Validar existencias
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
            "id_usuario_apertura": 1,
            "id_usuario_cierre": 1,
            "fecha_apertura": fecha_actual,
            "hora_apertura": hora_actual,
            "fecha_cierre": fecha_actual,
            "hora_cierre": hora_actual,
            "fecha": fecha_actual,
            "hora": hora_actual,
            "total_monto": total_monto,
            "monto_venta": total_monto,
            "monto_total": total_monto,
            "total": total_monto,
            "turno": usuario,
            "cajero": usuario,
            "usuario": usuario,
            "estado_venta": "Cerrada",
            "medio_pago": medio_pago
        }
        id_venta = _insertar_inteligente(cursor, "ventas", datos_venta)

        # 3. Insertar detalle de venta y descontar existencias
        for it in items_carrito:
            p_base = float(it.get("precio_base") or it.get("valor_final") or 0.0)
            p_final = float(it.get("valor_final") or p_base)
            subtotal = float(it.get("subtotal") or (p_final * float(it["cantidad"])))

            datos_item = {
                "id_venta": id_venta,
                "id_producto": it["id_producto"],
                "cantidad": float(it["cantidad"]),
                "precio_base": p_base,
                "descuento_aplicado": 0.0,
                "valor_final": p_final,
                "subtotal": subtotal
            }
            _insertar_inteligente(cursor, "venta_items", datos_item)

            cursor.execute("""
                UPDATE productos
                SET stock_actual = stock_actual - ?
                WHERE id_producto = ?
            """, (it["cantidad"], it["id_producto"]))

        # 4. Insertar en caja
        datos_caja = {
            "id_terminal": 1,
            "id_venta": id_venta,
            "id_usuario_apertura": 1,
            "id_usuario_cierre": 1,
            "fecha_apertura": fecha_actual,
            "hora_apertura": hora_actual,
            "fecha_cierre": fecha_actual,
            "hora_cierre": hora_actual,
            "fecha": fecha_actual,
            "hora": hora_actual,
            "tipo_movimiento": "Venta",
            "medio_pago": medio_pago,
            "monto_venta": total_monto,
            "total_monto": total_monto,
            "total_pagar": total_monto,
            "monto": total_monto,
            "total": total_monto,
            "usuario": usuario,
            "cajero": usuario,
            "turno": usuario,
            "descripcion": f"Venta directa #{id_venta}"
        }
        _insertar_inteligente(cursor, "caja", datos_caja)

        conn.commit()
        return True, id_venta

    except Exception as e:
        if 'conn' in locals() and conn:
            conn.rollback()
        return False, f"Error al procesar la venta: {str(e)}"
    finally:
        if 'conn' in locals() and conn:
            conn.close()
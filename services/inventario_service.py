import sqlite3
from database.connection import get_connection

def obtener_todos_los_productos():
    """Retorna todos los productos activos e inactivos para el inventario."""
    try:
        conn = get_connection()
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM productos ORDER BY id_producto DESC")
        filas = cursor.fetchall()
        return True, [dict(f) for f in filas]
    except Exception as e:
        return False, f"Error al obtener productos: {str(e)}"
    finally:
        if 'conn' in locals() and conn:
            conn.close()

def buscar_productos(termino):
    """Busca productos por SKU, código de barra o nombre."""
    try:
        conn = get_connection()
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        query = """
            SELECT * FROM productos 
            WHERE sku LIKE ? OR codigo_barra LIKE ? OR nombre_producto LIKE ?
            ORDER BY nombre_producto ASC
        """
        param = f"%{termino}%"
        cursor.execute(query, (param, param, param))
        filas = cursor.fetchall()
        return True, [dict(f) for f in filas]
    except Exception as e:
        return False, f"Error al buscar productos: {str(e)}"
    finally:
        if 'conn' in locals() and conn:
            conn.close()

def crear_producto(datos):
    """Inserta un nuevo producto validando que no posea stock o precios negativos."""
    try:
        # Validación de valores no negativos
        if float(datos.get("stock_actual", 0)) < 0:
            return False, "El stock actual no puede ser un número negativo."
        if float(datos.get("stock_critico", 0)) < 0:
            return False, "El stock crítico no puede ser un número negativo."
        if float(datos.get("precio_costo", 0)) < 0 or float(datos.get("precio_venta", 0)) < 0:
            return False, "Los precios no pueden ser negativos."

        conn = get_connection()
        cursor = conn.cursor()
        query = """
            INSERT INTO productos (
                sku, codigo_barra, nombre_producto, descripcion, categoria,
                precio_costo, precio_venta, stock_actual, stock_critico,
                unidad_medida, imagen_url, es_activo
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        valores = (
            datos.get("sku"),
            datos.get("codigo_barra"),
            datos.get("nombre_producto"),
            datos.get("descripcion", ""),
            datos.get("categoria", "General"),
            float(datos.get("precio_costo", 0)),
            float(datos.get("precio_venta", 0)),
            float(datos.get("stock_actual", 0)),
            float(datos.get("stock_critico", 0)),
            datos.get("unidad_medida", "UN"),
            datos.get("imagen_url", ""),
            datos.get("es_activo", 1)
        )
        cursor.execute(query, valores)
        conn.commit()
        return True, "Producto creado exitosamente."
    except sqlite3.IntegrityError:
        return False, "El SKU o Código de Barra ya existe en el sistema."
    except Exception as e:
        return False, f"Error inesperado: {str(e)}"
    finally:
        if 'conn' in locals() and conn:
            conn.close()

def actualizar_producto(id_producto, datos):
    """Actualiza un producto existente validando valores no negativos."""
    try:
        # Validación de valores no negativos
        if float(datos.get("stock_actual", 0)) < 0:
            return False, "El stock actual no puede ser un número negativo."
        if float(datos.get("stock_critico", 0)) < 0:
            return False, "El stock crítico no puede ser un número negativo."
        if float(datos.get("precio_costo", 0)) < 0 or float(datos.get("precio_venta", 0)) < 0:
            return False, "Los precios no pueden ser negativos."

        conn = get_connection()
        cursor = conn.cursor()
        query = """
            UPDATE productos SET
                sku = ?, codigo_barra = ?, nombre_producto = ?, descripcion = ?,
                categoria = ?, precio_costo = ?, precio_venta = ?,
                stock_actual = ?, stock_critico = ?, unidad_medida = ?,
                imagen_url = ?, es_activo = ?
            WHERE id_producto = ?
        """
        valores = (
            datos.get("sku"),
            datos.get("codigo_barra"),
            datos.get("nombre_producto"),
            datos.get("descripcion", ""),
            datos.get("categoria", "General"),
            float(datos.get("precio_costo", 0)),
            float(datos.get("precio_venta", 0)),
            float(datos.get("stock_actual", 0)),
            float(datos.get("stock_critico", 0)),
            datos.get("unidad_medida", "UN"),
            datos.get("imagen_url", ""),
            datos.get("es_activo", 1),
            id_producto
        )
        cursor.execute(query, valores)
        conn.commit()
        return True, "Producto actualizado exitosamente."
    except sqlite3.IntegrityError:
        return False, "El SKU o Código de Barra ya pertenece a otro producto."
    except Exception as e:
        return False, f"Error inesperado: {str(e)}"
    finally:
        if 'conn' in locals() and conn:
            conn.close()

def eliminar_producto_logico(id_producto):
    """Desactiva un producto (borrado lógico) para preservar el historial de ventas."""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("UPDATE productos SET es_activo = 0 WHERE id_producto = ?", (id_producto,))
        conn.commit()
        return True, "Producto desactivado exitosamente."
    except Exception as e:
        return False, f"Error al desactivar el producto: {str(e)}"
    finally:
        if 'conn' in locals() and conn:
            conn.close()
import sqlite3
from datetime import date, datetime
from database.connection import get_connection

def inicializar_tablas_movimientos_caja():
    """Crea la tabla de movimientos/gastos y configuración de caja si no existen."""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS movimientos_caja (
                id_movimiento INTEGER PRIMARY KEY AUTOINCREMENT,
                fecha TEXT NOT NULL,
                hora TEXT NOT NULL,
                tipo TEXT NOT NULL, -- INGRESO / RETIRO / FONDO
                monto REAL NOT NULL,
                motivo TEXT,
                usuario TEXT NOT NULL DEFAULT 'Administrador'
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS config_caja (
                clave TEXT PRIMARY KEY,
                valor REAL NOT NULL
            )
        """)
        cursor.execute("INSERT OR IGNORE INTO config_caja (clave, valor) VALUES ('fondo_base', 50000.0)")
        
        conn.commit()
    except Exception as e:
        print(f"Error al inicializar tablas de movimientos de caja: {e}")
    finally:
        if 'conn' in locals() and conn:
            conn.close()

# Ejecutar inicialización al importar
inicializar_tablas_movimientos_caja()


# ========================================================
# SECCIÓN 1: COMPATIBILIDAD CON FLUJO PREVIO DE VENTAS/COBROS
# ========================================================

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
        if 'conn' in locals() and conn:
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
        if 'conn' in locals() and conn:
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
        if 'conn' in locals() and conn:
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
            monto = float(fila["total"] if isinstance(fila, dict) else fila[1])
            if medio in resumen:
                resumen[medio] = monto
            total_general += monto
            
        resumen["Total"] = total_general
        return True, resumen
    except Exception as e:
        return False, f"Error al calcular el arqueo: {str(e)}"
    finally:
        if 'conn' in locals() and conn:
            conn.close()


# ========================================================
# SECCIÓN 2: CONTROL FINANCIERO, FONDO BASE Y MOVIMIENTOS
# ========================================================

def obtener_fondo_base():
    """Retorna el monto configurado como fondo base en caja."""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT valor FROM config_caja WHERE clave = 'fondo_base'")
        res = cursor.fetchone()
        if res:
            return float(res["valor"] if isinstance(res, dict) else res[0])
        return 50000.0
    except Exception:
        return 50000.0
    finally:
        if 'conn' in locals() and conn:
            conn.close()


def ajustar_fondo_inicial(nuevo_fondo):
    """Actualiza el fondo base y deja constancia en auditoría."""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("UPDATE config_caja SET valor = ? WHERE clave = 'fondo_base'", (nuevo_fondo,))
        hora_actual = datetime.now().strftime('%H:%M:%S')
        fecha_actual = date.today().strftime('%Y-%m-%d')
        cursor.execute("""
            INSERT INTO movimientos_caja (fecha, hora, tipo, monto, motivo, usuario)
            VALUES (?, ?, 'FONDO', ?, 'Ajuste de Fondo Base', 'Administrador')
        """, (fecha_actual, hora_actual, nuevo_fondo))
        conn.commit()
        return True, "Fondo base actualizado."
    except Exception as e:
        return False, str(e)
    finally:
        if 'conn' in locals() and conn:
            conn.close()


def registrar_movimiento(tipo, monto, motivo, usuario="Administrador"):
    """Registra entradas extraordinarias o salidas/gastos de gaveta."""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        fecha_actual = date.today().strftime('%Y-%m-%d')
        hora_actual = datetime.now().strftime('%H:%M:%S')
        cursor.execute("""
            INSERT INTO movimientos_caja (fecha, hora, tipo, monto, motivo, usuario)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (fecha_actual, hora_actual, tipo, monto, motivo, usuario))
        conn.commit()
        return True, "Movimiento registrado con éxito."
    except Exception as e:
        return False, str(e)
    finally:
        if 'conn' in locals() and conn:
            conn.close()


def obtener_resumen_caja():
    fecha_hoy = date.today().strftime('%Y-%m-%d')
    fondo_base = obtener_fondo_base()
    
    resumen = {
        "fondo_base": fondo_base,
        "efectivo_caja": fondo_base,
        "debito": 0.0,
        "credito": 0.0,
        "transferencia": 0.0,
        "total_turno": 0.0,
        "movimientos": []
    }

    try:
        conn = get_connection()
        cursor = conn.cursor()

        # 1. Consultar directamente de la tabla 'caja'
        # Usamos LEFT JOIN con ventas por si se requiere validar fecha, o sumamos directo de caja
        query_ventas = """
            SELECT c.medio_pago, COALESCE(SUM(c.total_pagar), 0) AS total
            FROM caja c
            LEFT JOIN ventas v ON c.id_venta = v.id_venta
            WHERE v.fecha = ? OR v.fecha IS NULL
            GROUP BY c.medio_pago
        """
        cursor.execute(query_ventas, (fecha_hoy,))
        ventas = cursor.fetchall()

        # Si no arrojó resultados con la fecha de hoy, consultar el acumulado directo de caja
        if not ventas:
            cursor.execute("SELECT medio_pago, COALESCE(SUM(total_pagar), 0) AS total FROM caja GROUP BY medio_pago")
            ventas = cursor.fetchall()

        v_efectivo = 0.0
        for row in ventas:
            mp = row["medio_pago"] if isinstance(row, dict) else row[0]
            total = float(row["total"] if isinstance(row, dict) else row[1])
            
            if mp == "Efectivo":
                v_efectivo += total
            elif mp == "Débito":
                resumen["debito"] += total
            elif mp == "Crédito":
                resumen["credito"] += total
            elif mp == "Transferencia":
                resumen["transferencia"] += total

        # 2. Consultar movimientos manuales
        query_movs = """
            SELECT hora, tipo, monto, motivo, usuario 
            FROM movimientos_caja 
            ORDER BY id_movimiento DESC
        """
        cursor.execute(query_movs)
        movs = cursor.fetchall()

        ingresos_extra = 0.0
        retiros = 0.0
        lista_movs = []

        for m in movs:
            es_d = isinstance(m, dict)
            tipo = m["tipo"] if es_d else m[1]
            monto = float(m["monto"] if es_d else m[2])
            
            if tipo == "INGRESO":
                ingresos_extra += monto
            elif tipo == "RETIRO":
                retiros += monto

            lista_movs.append({
                "hora": m["hora"] if es_d else m[0],
                "tipo": tipo,
                "monto": monto,
                "motivo": m["motivo"] if es_d else m[3],
                "usuario": m["usuario"] if es_d else m[4]
            })

        resumen["movimientos"] = lista_movs
        resumen["efectivo_caja"] = fondo_base + v_efectivo + ingresos_extra - retiros
        resumen["total_turno"] = v_efectivo + resumen["debito"] + resumen["credito"] + resumen["transferencia"]

        return resumen

    except Exception as e:
        print(f"Error al obtener resumen de caja: {e}")
        return resumen
    finally:
        if 'conn' in locals() and conn:
            conn.close()
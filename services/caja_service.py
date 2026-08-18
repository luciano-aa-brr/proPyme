import sqlite3
from datetime import date, datetime
from database.connection import get_connection

def inicializar_tablas_caja_y_auditoria():
    """Crea las tablas de movimientos, configuración y auditoría de cierres."""
    try:
        conn = get_connection()
        cursor = conn.cursor()

        # Tabla de movimientos manuales de caja (inyecciones y retiros)
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
        
        # Configuración persistente del fondo base
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS config_caja (
                clave TEXT PRIMARY KEY,
                valor REAL NOT NULL
            )
        """)
        cursor.execute("INSERT OR IGNORE INTO config_caja (clave, valor) VALUES ('fondo_base', 50000.0)")

        # Tabla histórica de cierres de caja para auditorías
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS cierres_caja (
                id_cierre INTEGER PRIMARY KEY AUTOINCREMENT,
                fecha_cierre TEXT NOT NULL,
                hora_cierre TEXT NOT NULL,
                usuario_cierre TEXT NOT NULL,
                fondo_inicial REAL NOT NULL,
                ventas_efectivo REAL NOT NULL,
                ventas_debito REAL NOT NULL,
                ventas_credito REAL NOT NULL,
                ventas_transferencia REAL NOT NULL,
                total_ventas REAL NOT NULL,
                total_ingresos_extra REAL NOT NULL,
                total_retiros REAL NOT NULL,
                efectivo_teorico REAL NOT NULL,
                efectivo_real_declarado REAL NOT NULL,
                diferencia_efectivo REAL NOT NULL,
                estado_cuadre TEXT NOT NULL,
                observaciones TEXT
            )
        """)
        
        conn.commit()
    except Exception as e:
        print(f"Error al inicializar tablas de caja: {e}")
    finally:
        if 'conn' in locals() and conn:
            conn.close()

# Ejecutar inicialización al importar
inicializar_tablas_caja_y_auditoria()


def obtener_fondo_base():
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
        return True, "Fondo base actualizado con éxito."
    except Exception as e:
        return False, str(e)
    finally:
        if 'conn' in locals() and conn:
            conn.close()


def registrar_movimiento(tipo, monto, motivo, usuario="Administrador"):
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

        # 1. Totalizar ventas registradas en la tabla 'caja'
        cursor.execute("""
            SELECT medio_pago, COALESCE(SUM(total_pagar), 0) AS total
            FROM caja
            GROUP BY medio_pago
        """)
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

        # 2. Consultar movimientos del turno
        cursor.execute("""
            SELECT hora, tipo, monto, motivo, usuario 
            FROM movimientos_caja 
            ORDER BY id_movimiento DESC
        """)
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


def procesar_cierre_turno(efectivo_declarado, observaciones="", usuario="Administrador"):
    """
    Registra el acta contable de cierre de caja y reinicia los contadores para el nuevo turno.
    """
    conn = None
    try:
        conn = get_connection()
        cursor = conn.cursor()

        # 1. Obtener estado teórico
        resumen = obtener_resumen_caja()
        fondo = resumen["fondo_base"]
        teorico_efectivo = resumen["efectivo_caja"]
        v_debito = resumen["debito"]
        v_credito = resumen["credito"]
        v_transf = resumen["transferencia"]
        v_total = resumen["total_turno"]
        v_efectivo = v_total - (v_debito + v_credito + v_transf)

        ingresos_extra = sum(m["monto"] for m in resumen["movimientos"] if m["tipo"] == "INGRESO")
        retiros = sum(m["monto"] for m in resumen["movimientos"] if m["tipo"] == "RETIRO")

        # 2. Calcular descuadre
        diferencia = efectivo_declarado - teorico_efectivo
        if diferencia == 0:
            estado_cuadre = "CUADRADO"
        elif diferencia > 0:
            estado_cuadre = f"SOBRANTE (+${diferencia:,.0f})".replace(',', '.')
        else:
            estado_cuadre = f"FALTANTE (-${abs(diferencia):,.0f})".replace(',', '.')

        fecha_cierre = date.today().strftime('%Y-%m-%d')
        hora_cierre = datetime.now().strftime('%H:%M:%S')

        # 3. Insertar snapshot en la tabla de auditoría
        cursor.execute("""
            INSERT INTO cierres_caja (
                fecha_cierre, hora_cierre, usuario_cierre, fondo_inicial,
                ventas_efectivo, ventas_debito, ventas_credito, ventas_transferencia,
                total_ventas, total_ingresos_extra, total_retiros, efectivo_teorico,
                efectivo_real_declarado, diferencia_efectivo, estado_cuadre, observaciones
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            fecha_cierre, hora_cierre, usuario, fondo,
            v_efectivo, v_debito, v_credito, v_transf,
            v_total, ingresos_extra, retiros, teorico_efectivo,
            efectivo_declarado, diferencia, estado_cuadre, observaciones
        ))

        # 4. Limpiar los registros temporales del turno cerrado
        cursor.execute("DELETE FROM movimientos_caja")
        cursor.execute("DELETE FROM caja")

        conn.commit()

        return True, {
            "estado_cuadre": estado_cuadre,
            "diferencia": diferencia,
            "teorico": teorico_efectivo,
            "declarado": efectivo_declarado,
            "total_ventas": v_total
        }

    except Exception as e:
        if conn:
            conn.rollback()
        return False, f"Error al procesar el cierre: {str(e)}"
    finally:
        if conn:
            conn.close()


def obtener_historial_cierres():
    """
    Retorna la lista histórica de todos los cierres de caja guardados para auditoría.
    """
    try:
        conn = get_connection()
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM cierres_caja ORDER BY id_cierre DESC")
        filas = cursor.fetchall()
        return True, [dict(f) for f in filas]
    except Exception as e:
        return False, f"Error al consultar historial de cierres: {str(e)}"
    finally:
        if 'conn' in locals() and conn:
            conn.close()
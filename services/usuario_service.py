import sqlite3
from database.connection import get_connection

def autenticar_por_pin(pin_ingresado):
    pin_str = str(pin_ingresado).strip()
    if not pin_str:
        return False, "Debes ingresar un PIN."

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id_usuario, nombre, rol, estado 
        FROM usuarios 
        WHERE pin_seguridad = ? AND estado = 'Activo'
    """, (pin_str,))
    usuario = cursor.fetchone()
    conn.close()

    if usuario:
        return True, {
            "id_usuario": usuario["id_usuario"],
            "nombre": usuario["nombre"],
            "rol": usuario["rol"]
        }
    return False, "PIN incorrecto o usuario inactivo."

def obtener_todos_los_usuarios():
    """Retorna todos los usuarios registrados (Activos e Inactivos)."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id_usuario, nombre, pin_seguridad, rol, estado FROM usuarios ORDER BY id_usuario ASC")
    usuarios = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return True, usuarios

def crear_usuario(nombre, pin, rol):
    """Registra un nuevo usuario validando que el PIN sea único y numérico."""
    nombre = nombre.strip()
    pin = pin.strip()

    if not nombre or not pin:
        return False, "Nombre y PIN son obligatorios."
    
    if not pin.isdigit() or len(pin) < 4:
        return False, "El PIN debe ser numérico y tener al menos 4 dígitos."

    conn = get_connection()
    cursor = conn.cursor()

    # Validar unicidad de PIN
    cursor.execute("SELECT id_usuario FROM usuarios WHERE pin_seguridad = ? AND estado = 'Activo'", (pin,))
    if cursor.fetchone():
        conn.close()
        return False, "Ese PIN ya está en uso por otro usuario activo."

    cursor.execute("""
        INSERT INTO usuarios (nombre, pin_seguridad, rol, estado)
        VALUES (?, ?, ?, 'Activo')
    """, (nombre, pin, rol))
    conn.commit()
    conn.close()
    return True, "Usuario creado exitosamente."

def cambiar_estado_usuario(id_usuario, nuevo_estado):
    """Activa o desactiva un usuario (evita eliminar historial)."""
    conn = get_connection()
    cursor = conn.cursor()
    
    # Evitar desactivar al último administrador
    if nuevo_estado == 'Inactivo':
        cursor.execute("SELECT COUNT(*) FROM usuarios WHERE rol = 'Administrador' AND estado = 'Activo'")
        admins_activos = cursor.fetchone()[0]
        cursor.execute("SELECT rol FROM usuarios WHERE id_usuario = ?", (id_usuario,))
        usuario_target = cursor.fetchone()
        
        if usuario_target and usuario_target["rol"] == "Administrador" and admins_activos <= 1:
            conn.close()
            return False, "No puedes desactivar al único Administrador activo."

    cursor.execute("UPDATE usuarios SET estado = ? WHERE id_usuario = ?", (nuevo_estado, id_usuario))
    conn.commit()
    conn.close()
    return True, f"Usuario marcado como {nuevo_estado}."
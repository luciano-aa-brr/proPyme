import sys
from PySide6.QtWidgets import QApplication, QDialog
from database.connection import init_db
from ui.login_dialog import LoginDialog
from ui.main_window import MainWindow

def main():
    app = QApplication(sys.argv)
    
    # Inicializar tablas y usuarios base
    init_db()

    # Bucle de sesión (Login -> MainWindow -> Logout -> Login)
    while True:
        login = LoginDialog()
        if login.exec() != QDialog.DialogCode.Accepted:
            break  # Si el usuario cierra el modal con la X, sale de la app

        usuario = login.usuario_autenticado
        window = MainWindow(usuario_actual=usuario)
        
        # Bandera para controlar si se solicitó cambio de usuario
        cambio_usuario = {"activo": False}

        def on_logout():
            cambio_usuario["activo"] = True

        window.solicitar_logout.connect(on_logout)
        
        # PANTALLA COMPLETA AUTOMÁTICA
        window.showMaximized()  # Usa window.showFullScreen() si deseas ocultar la barra de Windows
        
        app.exec()

        if not cambio_usuario["activo"]:
            break

if __name__ == "__main__":
    main()
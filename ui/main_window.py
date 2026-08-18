from PySide6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                               QPushButton, QStackedWidget, QLabel, QFrame)
from PySide6.QtCore import Qt, Signal
from ui.inventario_view import InventarioView
from ui.ventas_view import VentasView
from ui.caja_view import CajaView
from ui.historial_view import HistorialView
from ui.usuarios_modal import UsuariosModal

class MainWindow(QMainWindow):
    # Señal emitida cuando el usuario decide cerrar sesión / cambiar de turno
    solicitar_logout = Signal()

    def __init__(self, usuario_actual=None):
        super().__init__()
        self.setWindowTitle("KoaLink - ProPyme POS")
        self.resize(1100, 700)

        # Si no se pasa usuario (por ejemplo en pruebas), asignamos Admin por defecto
        self.usuario_actual = usuario_actual or {
            "id_usuario": 1,
            "nombre": "Administrador",
            "rol": "Administrador"
        }

        # Contenedor principal
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        
        layout = QHBoxLayout(main_widget)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(15)

        # --- Menú lateral Responsivo ---
        sidebar_widget = QWidget()
        sidebar_widget.setMaximumWidth(250) 
        sidebar_widget.setMinimumWidth(180)
        
        sidebar = QVBoxLayout(sidebar_widget)
        sidebar.setContentsMargins(0, 0, 0, 0)
        sidebar.setSpacing(8)

        # --- Tarjeta de Usuario Activo ---
        user_card = QFrame()
        user_card.setStyleSheet("""
            QFrame {
                background-color: #2D2D3A;
                border-radius: 8px;
                padding: 10px;
            }
        """)
        user_card_layout = QVBoxLayout(user_card)
        user_card_layout.setContentsMargins(8, 8, 8, 8)
        user_card_layout.setSpacing(6)

        lbl_nombre = QLabel(f"👤 {self.usuario_actual['nombre']}")
        lbl_nombre.setStyleSheet("color: #FFFFFF; font-size: 13px; font-weight: bold;")
        
        color_badge = "#BFA2DB" if self.usuario_actual['rol'] == "Administrador" else "#81C784"
        lbl_rol = QLabel(self.usuario_actual['rol'].upper())
        lbl_rol.setStyleSheet(f"""
            color: #1E1E24; 
            background-color: {color_badge}; 
            border-radius: 4px; 
            font-size: 10px; 
            font-weight: bold; 
            padding: 2px 6px;
            qproperty-alignment: AlignCenter;
        """)

        # Botón de Gestión de Usuarios (Exclusivo Administrador)
        self.btn_gestionar_usuarios = QPushButton("⚙️ Gestionar Equipo")
        self.btn_gestionar_usuarios.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_gestionar_usuarios.setStyleSheet("""
            QPushButton {
                background-color: #3A3A4A;
                color: #FFFFFF;
                border: none;
                border-radius: 4px;
                padding: 5px 8px;
                font-size: 11px;
                font-weight: bold;
                margin-top: 2px;
            }
            QPushButton:hover { background-color: #BFA2DB; color: #1E1E24; }
        """)
        self.btn_gestionar_usuarios.clicked.connect(self.abrir_gestion_usuarios)

        user_card_layout.addWidget(lbl_nombre)
        user_card_layout.addWidget(lbl_rol)
        user_card_layout.addWidget(self.btn_gestionar_usuarios)
        sidebar.addWidget(user_card)

        # --- Botones de Navegación ---
        self.btn_inventario = QPushButton("Inventario")
        self.btn_venta = QPushButton("Nueva Venta")
        self.btn_caja = QPushButton("Caja")
        self.btn_historial = QPushButton("Historial")
        
        self.botones_menu = [self.btn_inventario, self.btn_venta, self.btn_caja, self.btn_historial]

        self.estilo_base = """
            QPushButton {
                background-color: #E6E6FA;
                color: #2D2D3A;
                border: 1px solid #D8BFD8;
                padding: 12px;
                border-radius: 6px;
                font-size: 14px;
                font-weight: bold;
                text-align: center;
            }
            QPushButton:hover { background-color: #D8BFD8; }
            QPushButton:pressed { background-color: #CBAACD; }
        """

        self.estilo_activo = """
            QPushButton {
                background-color: #BFA2DB;
                color: #1E1E24;
                border: 2px solid #9370DB;
                padding: 12px;
                border-radius: 6px;
                font-size: 14px;
                font-weight: bold;
                text-align: center;
            }
        """

        for btn in self.botones_menu:
            btn.setStyleSheet(self.estilo_base)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            sidebar.addWidget(btn)

        sidebar.addStretch()

        # Botón para Cambiar Usuario / Cerrar Sesión
        self.btn_logout = QPushButton("🔒 Cambiar Usuario")
        self.btn_logout.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_logout.setStyleSheet("""
            QPushButton {
                background-color: #2D2D3A;
                color: #E0E0E0;
                border: 1px solid #4A4A5A;
                padding: 10px;
                border-radius: 6px;
                font-size: 12px;
                font-weight: bold;
            }
            QPushButton:hover { background-color: #3A3A4A; color: #FFFFFF; }
        """)
        self.btn_logout.clicked.connect(self.cerrar_sesion)
        sidebar.addWidget(self.btn_logout)

        # --- Sistema de Vistas ---
        self.stacked_widget = QStackedWidget() 

        self.vista_inventario = InventarioView()
        self.vista_venta = VentasView() 
        self.vista_caja = CajaView() 
        self.vista_historial = HistorialView()

        self.stacked_widget.addWidget(self.vista_inventario) # Índice 0
        self.stacked_widget.addWidget(self.vista_venta)      # Índice 1
        self.stacked_widget.addWidget(self.vista_caja)       # Índice 2
        self.stacked_widget.addWidget(self.vista_historial)  # Índice 3

        # Conectar navegación
        self.btn_inventario.clicked.connect(lambda: self.cambiar_vista(0, self.btn_inventario))
        self.btn_venta.clicked.connect(lambda: self.cambiar_vista(1, self.btn_venta))
        self.btn_caja.clicked.connect(lambda: self.cambiar_vista(2, self.btn_caja))
        self.btn_historial.clicked.connect(lambda: self.cambiar_vista(3, self.btn_historial))

        # Ensamblar layout
        layout.addWidget(sidebar_widget)
        layout.addWidget(self.stacked_widget, 1)

        # Aplicar permisos según el rol del usuario conectado
        self.aplicar_permisos()

    def aplicar_permisos(self):
        """Oculta o muestra vistas y botones de administración según el rol."""
        rol = self.usuario_actual.get("rol", "Vendedor")

        if rol == "Vendedor":
            self.btn_inventario.setVisible(False)
            self.btn_historial.setVisible(False)
            self.btn_gestionar_usuarios.setVisible(False)
            self.cambiar_vista(1, self.btn_venta)
        else:
            self.btn_inventario.setVisible(True)
            self.btn_historial.setVisible(True)
            self.btn_gestionar_usuarios.setVisible(True)
            self.cambiar_vista(0, self.btn_inventario)

    def cambiar_vista(self, indice, boton_activo):
        """Cambia la vista activa, resalta el botón y refresca los datos correspondientes."""
        self.stacked_widget.setCurrentIndex(indice)
        
        for btn in self.botones_menu:
            if btn == boton_activo:
                btn.setStyleSheet(self.estilo_activo)
            else:
                btn.setStyleSheet(self.estilo_base)

        # Disparar actualización en vivo según la pestaña a la que se ingresa
        if indice == 0 and hasattr(self.vista_inventario, 'cargar_datos_tabla'):
            self.vista_inventario.cargar_datos_tabla()
        elif indice == 1 and hasattr(self.vista_venta, 'search_input'):
            self.vista_venta.search_input.setFocus()
        elif indice == 2 and hasattr(self.vista_caja, 'refrescar_datos'):
            self.vista_caja.refrescar_datos()
        elif indice == 3 and hasattr(self.vista_historial, 'cargar_ventas'):
            self.vista_historial.cargar_ventas()

    def abrir_gestion_usuarios(self):
        """Abre el diálogo modal para crear, listar y desactivar cajeros/usuarios."""
        modal = UsuariosModal(self)
        modal.exec()

    def cerrar_sesion(self):
        """Emite la señal para volver a la pantalla de PIN."""
        self.solicitar_logout.emit()
        self.close()
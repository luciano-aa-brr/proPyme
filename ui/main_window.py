from PySide6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                               QPushButton, QStackedWidget)
from PySide6.QtCore import Qt
from ui.inventario_view import InventarioView
from ui.ventas_view import VentasView
from ui.caja_view import CajaView
from ui.historial_view import HistorialView

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("KoaLink - ProPyme POS")

        # Contenedor principal
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        
        # Layout principal (Horizontal)
        layout = QHBoxLayout(main_widget)
        layout.setContentsMargins(15, 15, 15, 15)

        # --- Menú lateral Responsivo ---
        sidebar_widget = QWidget()
        sidebar_widget.setMaximumWidth(250) 
        sidebar_widget.setMinimumWidth(160)
        
        sidebar = QVBoxLayout(sidebar_widget)
        sidebar.setContentsMargins(0, 0, 0, 0)
        sidebar.setSpacing(8)
        
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

        # --- Sistema de Vistas ---
        self.stacked_widget = QStackedWidget() 

        self.vista_inventario = InventarioView()
        self.vista_venta = VentasView() 
        self.vista_caja = CajaView() 
        self.vista_historial = HistorialView()

        self.stacked_widget.addWidget(self.vista_inventario)
        self.stacked_widget.addWidget(self.vista_venta)
        self.stacked_widget.addWidget(self.vista_caja)
        self.stacked_widget.addWidget(self.vista_historial)

        # Conectar navegación
        self.btn_inventario.clicked.connect(lambda: self.cambiar_vista(0, self.btn_inventario))
        self.btn_venta.clicked.connect(lambda: self.cambiar_vista(1, self.btn_venta))
        self.btn_caja.clicked.connect(lambda: self.cambiar_vista(2, self.btn_caja))
        self.btn_historial.clicked.connect(lambda: self.cambiar_vista(3, self.btn_historial))

        # Vista inicial
        self.cambiar_vista(0, self.btn_inventario)

        # Ensamblar layout
        layout.addWidget(sidebar_widget)
        layout.addWidget(self.stacked_widget, 1) 

    def cambiar_vista(self, indice, boton_activo):
        """Cambia la vista activa y resalta el botón seleccionado."""
        self.stacked_widget.setCurrentIndex(indice)
        for btn in self.botones_menu:
            if btn == boton_activo:
                btn.setStyleSheet(self.estilo_activo)
            else:
                btn.setStyleSheet(self.estilo_base)
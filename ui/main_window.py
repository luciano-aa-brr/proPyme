from PySide6.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QStackedWidget, QLabel, QMessageBox
from PySide6.QtCore import Qt
from ui.inventario_view import InventarioView
from ui.ventas_view import VentasView
from ui.caja_view import CajaView

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("KoaLink - ProPyme POS")

        # Contenedor principal
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        
        # Layout principal (Horizontal)
        layout = QHBoxLayout(main_widget)
        layout.setContentsMargins(15, 15, 15, 15) # Márgenes generales limpios

        # --- Menú lateral Responsivo ---
        sidebar_widget = QWidget()
        # Esto es clave para tablets/PC: el menú no pasará de 250px ni bajará de 150px
        sidebar_widget.setMaximumWidth(250) 
        sidebar_widget.setMinimumWidth(150)
        
        sidebar = QVBoxLayout(sidebar_widget)
        sidebar.setContentsMargins(0, 0, 0, 0)
        
        self.btn_inventario = QPushButton("Inventario")
        self.btn_venta = QPushButton("Nueva Venta")
        self.btn_caja = QPushButton("Caja")
        self.btn_historial = QPushButton("Historial")
        
        # Botón extra para probar tu requerimiento de ventanas centradas
        self.btn_prueba_popup = QPushButton("Probar Popup") 

        # Estilos lavanda de KoaLink
        estilo_base = """
            QPushButton {
                background-color: #E6E6FA;
                color: #4A4A4A;
                border: 1px solid #D8BFD8;
                padding: 12px;
                border-radius: 6px;
                font-size: 14px;
                font-weight: bold;
                margin-bottom: 5px;
            }
            QPushButton:hover {
                background-color: #D8BFD8;
            }
            QPushButton:pressed {
                background-color: #CBAACD;
            }
        """
        self.setStyleSheet(estilo_base)

        sidebar.addWidget(self.btn_inventario)
        sidebar.addWidget(self.btn_venta)
        sidebar.addWidget(self.btn_caja)
        sidebar.addWidget(self.btn_historial)
        sidebar.addStretch() # Empuja los botones arriba
        sidebar.addWidget(self.btn_prueba_popup)

        # --- Sistema de Vistas ---
        self.stacked_widget = QStackedWidget() 

        # Vistas reales (¡Ya tenemos 3!)
        self.vista_inventario = InventarioView()
        self.vista_venta = VentasView() 
        self.vista_caja = CajaView() 

        # Placeholder restante
        self.vista_historial = QLabel("Pantalla de Historial (Reportes básicos)")

        # Agregamos las vistas reales al sistema
        self.stacked_widget.addWidget(self.vista_inventario)
        self.stacked_widget.addWidget(self.vista_venta)
        self.stacked_widget.addWidget(self.vista_caja) # <- Agregamos la caja

        # Mantenemos el bucle solo para el placeholder de historial
        for vista in [self.vista_historial]:
            vista.setAlignment(Qt.AlignmentFlag.AlignCenter)
            vista.setStyleSheet("font-size: 24px; color: #888; background-color: #f5f5f5; border-radius: 8px;")
            self.stacked_widget.addWidget(vista)

        # Conectar navegación 
        self.btn_inventario.clicked.connect(lambda: self.stacked_widget.setCurrentIndex(0))
        self.btn_venta.clicked.connect(lambda: self.stacked_widget.setCurrentIndex(1))
        self.btn_caja.clicked.connect(lambda: self.stacked_widget.setCurrentIndex(2))
        self.btn_historial.clicked.connect(lambda: self.stacked_widget.setCurrentIndex(3))
        
        # Conectar el popup
        self.btn_prueba_popup.clicked.connect(self.mostrar_popup)

        # Ensamblar layout
        layout.addWidget(sidebar_widget)
        # Al darle peso '1' al stacked_widget, le decimos que tome todo el espacio sobrante
        layout.addWidget(self.stacked_widget, 1) 

    def mostrar_popup(self):
        # ALERTA UX: Al pasar 'self' como argumento, le decimos a PySide6 que este 
        # mensaje pertenece a MainWindow. Así lo centrará automáticamente en la pantalla.
        msg = QMessageBox(self)
        msg.setWindowTitle("Mensaje del Sistema")
        msg.setText("¡Este popup aparece perfectamente centrado!")
        msg.setIcon(QMessageBox.Icon.Information)
        msg.exec()
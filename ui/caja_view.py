from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                               QLineEdit, QLabel, QFrame, QGridLayout, QComboBox,
                               QTabWidget, QTableWidget, QTableWidgetItem, QHeaderView)
from PySide6.QtCore import Qt

class CajaView(QWidget):
    def __init__(self):
        super().__init__()
        
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        
        # --- HEADER COMPARTIDO (Siempre visible) ---
        header_layout = QHBoxLayout()
        lbl_terminal = QLabel("🟢 Terminal Activa: Caja 1")
        lbl_terminal.setStyleSheet("font-size: 14px; font-weight: bold; color: #2E8B57;")
        
        lbl_turno = QLabel("Turno: Mañana")
        lbl_turno.setStyleSheet("font-size: 14px; color: #666;")
        lbl_turno.setAlignment(Qt.AlignmentFlag.AlignRight)
        
        header_layout.addWidget(lbl_terminal)
        header_layout.addWidget(lbl_turno)
        main_layout.addLayout(header_layout)
        main_layout.addSpacing(10)

        # --- SISTEMA DE PESTAÑAS ---
        self.tabs = QTabWidget()
        self.tabs.setStyleSheet("""
            QTabWidget::pane { border: 1px solid #D8BFD8; border-radius: 4px; background: white; }
            QTabBar::tab { background: #F8F8FF; border: 1px solid #D8BFD8; padding: 10px 20px; font-weight: bold; color: #4A4A4A; border-top-left-radius: 4px; border-top-right-radius: 4px; }
            QTabBar::tab:selected { background: #9370DB; color: white; }
        """)
        main_layout.addWidget(self.tabs)

        # Instanciar las dos sub-vistas
        self.tab_cobro = QWidget()
        self.tab_cierre = QWidget()
        
        self.tabs.addTab(self.tab_cobro, "💰 Cobrar Venta")
        self.tabs.addTab(self.tab_cierre, "📊 Cierre de Turno")

        # Llamar a los métodos constructores
        self.construir_tab_cobro()
        self.construir_tab_cierre()

    def construir_tab_cobro(self):
        # Layout centrado para el ticket
        layout = QVBoxLayout(self.tab_cobro)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        center_wrapper = QWidget()
        center_wrapper.setMaximumWidth(550) 
        wrapper_layout = QVBoxLayout(center_wrapper)
        wrapper_layout.setSpacing(20)
        
        # Buscador de Venta
        search_layout = QHBoxLayout()
        self.input_id_venta = QLineEdit()
        self.input_id_venta.setPlaceholderText("ID de Venta (Ej: V-1024)...")
        self.input_id_venta.setStyleSheet("padding: 12px; border: 1px solid #ccc; border-radius: 6px; font-size: 14px; background-color: white; color: #333;")
        
        self.btn_buscar = QPushButton("Cargar")
        self.btn_buscar.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_buscar.setStyleSheet("QPushButton { background-color: #D8BFD8; color: #4A4A4A; border: none; padding: 12px 20px; border-radius: 6px; font-weight: bold; } QPushButton:hover { background-color: #CBAACD; }")
        
        search_layout.addWidget(self.input_id_venta)
        search_layout.addWidget(self.btn_buscar)
        wrapper_layout.addLayout(search_layout)

        # Tarjeta de Resumen (Ticket)
        ticket_frame = QFrame()
        ticket_frame.setStyleSheet("QFrame { background-color: white; border: 2px dashed #D8BFD8; border-radius: 10px; } QLabel { border: none; background-color: transparent; }")
        ticket_layout = QVBoxLayout(ticket_frame)
        ticket_layout.setContentsMargins(30, 30, 30, 30)
        ticket_layout.setSpacing(15)
        
        titulo_ticket = QLabel("Detalle de Cobro - Venta #1024")
        titulo_ticket.setAlignment(Qt.AlignmentFlag.AlignCenter)
        titulo_ticket.setStyleSheet("font-size: 18px; font-weight: bold; color: #333; margin-bottom: 10px;")
        ticket_layout.addWidget(titulo_ticket)

        grid_calculos = QGridLayout()
        grid_calculos.setVerticalSpacing(10)
        campos = [("Monto Venta (Neto):", "$55.042"), ("Impuesto (IVA 19%):", "$10.458"), ("Descuentos Totales:", "-$0")]
        
        for fila, (etiqueta, valor) in enumerate(campos):
            lbl_etiq = QLabel(etiqueta)
            lbl_etiq.setStyleSheet("font-size: 15px; color: #666;")
            lbl_val = QLabel(valor)
            lbl_val.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            lbl_val.setStyleSheet("font-size: 15px; color: #333; font-weight: bold;")
            grid_calculos.addWidget(lbl_etiq, fila, 0)
            grid_calculos.addWidget(lbl_val, fila, 1)
            
        ticket_layout.addLayout(grid_calculos)
        
        linea = QFrame()
        linea.setFrameShape(QFrame.Shape.HLine)
        linea.setStyleSheet("background-color: #E6E6FA; border: none;")
        ticket_layout.addWidget(linea)
        
        total_layout = QHBoxLayout()
        lbl_total_txt = QLabel("Total a Pagar:")
        lbl_total_txt.setStyleSheet("font-size: 20px; font-weight: bold; color: #333;")
        lbl_total_val = QLabel("$65.500")
        lbl_total_val.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        lbl_total_val.setStyleSheet("font-size: 24px; font-weight: bold; color: #9370DB;")
        
        total_layout.addWidget(lbl_total_txt)
        total_layout.addWidget(lbl_total_val)
        ticket_layout.addLayout(total_layout)

        wrapper_layout.addWidget(ticket_frame)

        # Selector de Medio de Pago y Botón
        pago_layout = QHBoxLayout()
        self.combo_pago = QComboBox()
        self.combo_pago.addItems(["Efectivo", "Tarjeta de Débito", "Tarjeta de Crédito", "Transferencia"])
        self.combo_pago.setStyleSheet("QComboBox { padding: 12px; border: 1px solid #D8BFD8; border-radius: 6px; font-size: 14px; background-color: white; color: #333; } QComboBox QAbstractItemView { background-color: white; color: #333; selection-background-color: #E6E6FA; }")
        
        self.btn_procesar = QPushButton("Procesar Cobro")
        self.btn_procesar.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_procesar.setStyleSheet("QPushButton { background-color: #9370DB; color: white; border: none; padding: 14px; border-radius: 6px; font-size: 16px; font-weight: bold; } QPushButton:hover { background-color: #8A2BE2; }")
        
        pago_layout.addWidget(self.combo_pago, 1)
        pago_layout.addWidget(self.btn_procesar, 2)
        wrapper_layout.addLayout(pago_layout)
        
        layout.addWidget(center_wrapper)

    def construir_tab_cierre(self):
        layout = QVBoxLayout(self.tab_cierre)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)

        titulo = QLabel("Arqueo de Caja - Turno Mañana")
        titulo.setStyleSheet("font-size: 18px; font-weight: bold; color: #333;")
        layout.addWidget(titulo)

        # Tabla de todas las ventas del turno
        self.tabla_cierre = QTableWidget(4, 4)
        self.tabla_cierre.setHorizontalHeaderLabels(["ID Venta", "Hora", "Medio de Pago", "Total"])
        header = self.tabla_cierre.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.tabla_cierre.setStyleSheet("QTableWidget { background-color: white; border: 1px solid #E6E6FA; font-size: 14px; color: #333; } QHeaderView::section { background-color: #F8F8FF; padding: 8px; border: 1px solid #E6E6FA; font-weight: bold; color: #4A4A4A; }")
        
        datos_prueba = [
            ["V-1021", "09:15", "Efectivo", "$15.000"],
            ["V-1022", "10:30", "Tarjeta de Débito", "$40.500"],
            ["V-1023", "11:05", "Efectivo", "$5.000"],
            ["V-1024", "11:45", "Tarjeta de Crédito", "$65.500"]
        ]
        
        for fila, datos in enumerate(datos_prueba):
            for columna, valor in enumerate(datos):
                item = QTableWidgetItem(valor)
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                self.tabla_cierre.setItem(fila, columna, item)
        
        layout.addWidget(self.tabla_cierre)

        # Resumen Financiero por medio de pago
        resumen_frame = QFrame()
        resumen_frame.setStyleSheet("QFrame { background-color: #F8F8FF; border: 1px solid #D8BFD8; border-radius: 8px; } QLabel { border: none; }")
        resumen_layout = QHBoxLayout(resumen_frame)
        resumen_layout.setContentsMargins(20, 20, 20, 20)
        
        lbl_efectivo = QLabel("💵 Efectivo: $20.000")
        lbl_tarjetas = QLabel("💳 Tarjetas: $106.000")
        lbl_total = QLabel("💰 Total en Caja: $126.000")
        
        for lbl in [lbl_efectivo, lbl_tarjetas]:
            lbl.setStyleSheet("font-size: 16px; font-weight: bold; color: #555;")
            lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            resumen_layout.addWidget(lbl)
            
        lbl_total.setStyleSheet("font-size: 18px; font-weight: bold; color: #9370DB;")
        lbl_total.setAlignment(Qt.AlignmentFlag.AlignCenter)
        resumen_layout.addWidget(lbl_total)
        
        layout.addWidget(resumen_frame)

        # Botón Cierre Definitivo
        btn_layout = QHBoxLayout()
        self.btn_cerrar_caja = QPushButton("🔒 Registrar Cierre de Caja")
        self.btn_cerrar_caja.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_cerrar_caja.setFixedWidth(300)
        # Usamos un color de contraste (rojo suave) para indicar una acción de cierre definitivo
        self.btn_cerrar_caja.setStyleSheet("QPushButton { background-color: #DC143C; color: white; border: none; padding: 15px; border-radius: 6px; font-size: 16px; font-weight: bold; } QPushButton:hover { background-color: #B22222; }")
        
        btn_layout.addStretch()
        btn_layout.addWidget(self.btn_cerrar_caja)
        layout.addLayout(btn_layout)
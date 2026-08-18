from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                               QLineEdit, QTableWidget, QTableWidgetItem, 
                               QHeaderView, QLabel, QMessageBox, QDateEdit, 
                               QAbstractItemView, QFrame)
from PySide6.QtCore import Qt, QDate
from PySide6.QtGui import QColor

# Si tienes un servicio para historial, asegúrate de importarlo aquí
# from services.ventas_service import obtener_historial_ventas, anular_venta

class HistorialView(QWidget):
    def __init__(self):
        super().__init__()

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(16)

        # --- 1. TARJETAS KPI DE RESUMEN DE VENTAS ---
        kpi_layout = QHBoxLayout()
        kpi_layout.setSpacing(16)

        self.card_total_ventas = self.crear_tarjeta_kpi("Transacciones Realizadas", "0", "#BFA2DB")
        self.card_recaudado = self.crear_tarjeta_kpi("Monto Total Recaudado", "$0", "#81C784")

        kpi_layout.addWidget(self.card_total_ventas)
        kpi_layout.addWidget(self.card_recaudado)
        layout.addLayout(kpi_layout)

        # --- 2. BARRA DE FILTROS TOTALMENTE VISIBLE ---
        filtro_container = QFrame()
        filtro_container.setStyleSheet("""
            QFrame {
                background-color: #2D2D3A;
                border-radius: 8px;
                padding: 6px;
            }
        """)
        filtro_layout = QHBoxLayout(filtro_container)
        filtro_layout.setContentsMargins(12, 10, 12, 10)
        filtro_layout.setSpacing(12)

        # Estilo para inputs y fechas
        estilo_fecha = """
            QDateEdit {
                background-color: #1E1E24;
                color: #FFFFFF;
                border: 1px solid #4A4A5A;
                border-radius: 6px;
                padding: 6px 10px;
                font-size: 13px;
                font-weight: bold;
            }
            QDateEdit:focus {
                border: 2px solid #BFA2DB;
            }
            QDateEdit::drop-down {
                subcontrol-origin: padding;
                subcontrol-position: top right;
                width: 24px;
                border-left: 1px solid #4A4A5A;
                background-color: #3A3A4A;
                border-top-right-radius: 6px;
                border-bottom-right-radius: 6px;
            }
            QDateEdit::down-arrow {
                image: none;
                border-left: 4px solid transparent;
                border-right: 4px solid transparent;
                border-top: 6px solid #BFA2DB;
                width: 0;
                height: 0;
            }
            /* Calendario Popup */
            QCalendarWidget QWidget {
                alternate-background-color: #2D2D3A;
                background-color: #1E1E24;
                color: #FFFFFF;
            }
            QCalendarWidget QAbstractItemView:enabled {
                color: #FFFFFF;
                selection-background-color: #BFA2DB;
                selection-color: #1E1E24;
            }
        """

        lbl_desde = QLabel("Desde:")
        lbl_desde.setStyleSheet("color: #FFFFFF; font-weight: bold; font-size: 13px;")
        
        self.date_desde = QDateEdit()
        self.date_desde.setCalendarPopup(True)
        self.date_desde.setDate(QDate.currentDate())
        self.date_desde.setDisplayFormat("dd/MM/yyyy")
        self.date_desde.setStyleSheet(estilo_fecha)

        lbl_hasta = QLabel("Hasta:")
        lbl_hasta.setStyleSheet("color: #FFFFFF; font-weight: bold; font-size: 13px;")

        self.date_hasta = QDateEdit()
        self.date_hasta.setCalendarPopup(True)
        self.date_hasta.setDate(QDate.currentDate())
        self.date_hasta.setDisplayFormat("dd/MM/yyyy")
        self.date_hasta.setStyleSheet(estilo_fecha)

        # Botón Buscar / Filtrar con buen contraste
        self.btn_filtrar = QPushButton("🔍 Filtrar")
        self.btn_filtrar.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_filtrar.setStyleSheet("""
            QPushButton {
                background-color: #BFA2DB;
                color: #1E1E24;
                border: none;
                padding: 7px 16px;
                border-radius: 6px;
                font-weight: bold;
                font-size: 13px;
            }
            QPushButton:hover { background-color: #A888CB; }
            QPushButton:pressed { background-color: #9370DB; color: white; }
        """)
        self.btn_filtrar.clicked.connect(self.aplicar_filtro_fechas)

        # Botones Rápidos (Hoy, Este Mes)
        self.btn_hoy = QPushButton("Hoy")
        self.btn_mes = QPushButton("Este Mes")
        
        estilo_btn_rapido = """
            QPushButton {
                background-color: #3A3A4A;
                color: #FFFFFF;
                border: 1px solid #4A4A5A;
                padding: 7px 14px;
                border-radius: 6px;
                font-size: 12px;
                font-weight: bold;
            }
            QPushButton:hover { background-color: #4A4A5A; border-color: #BFA2DB; }
        """
        self.btn_hoy.setStyleSheet(estilo_btn_rapido)
        self.btn_mes.setStyleSheet(estilo_btn_rapido)
        self.btn_hoy.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_mes.setCursor(Qt.CursorShape.PointingHandCursor)

        self.btn_hoy.clicked.connect(self.filtrar_hoy)
        self.btn_mes.clicked.connect(self.filtrar_mes)

        # Buscador por Folio / Ticket
        self.search_folio = QLineEdit()
        self.search_folio.setPlaceholderText("Buscar por Folio / Boleta...")
        self.search_folio.setStyleSheet("""
            QLineEdit {
                background-color: #1E1E24;
                color: #FFFFFF;
                border: 1px solid #4A4A5A;
                border-radius: 6px;
                padding: 6px 12px;
                font-size: 13px;
            }
            QLineEdit:focus { border: 2px solid #BFA2DB; }
            QLineEdit::placeholder { color: #8E8E9F; }
        """)
        self.search_folio.textChanged.connect(self.filtrar_por_folio)

        # Ensamblar Filtros
        filtro_layout.addWidget(lbl_desde)
        filtro_layout.addWidget(self.date_desde)
        filtro_layout.addWidget(lbl_hasta)
        filtro_layout.addWidget(self.date_hasta)
        filtro_layout.addWidget(self.btn_filtrar)
        filtro_layout.addWidget(self.btn_hoy)
        filtro_layout.addWidget(self.btn_mes)
        filtro_layout.addStretch()
        filtro_layout.addWidget(self.search_folio)

        layout.addWidget(filtro_container)

        # --- 3. TABLA DE HISTORIAL DE VENTAS ---
        self.tabla = QTableWidget(0, 7)
        self.tabla.setHorizontalHeaderLabels(["ID", "Folio Ticket", "Fecha", "Hora", "Cajero / Turno", "Medio de Pago", "Total Venta"])
        self.tabla.verticalHeader().setVisible(False)
        self.tabla.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.tabla.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.tabla.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.tabla.setColumnHidden(0, True) # Ocultar ID interno

        header = self.tabla.horizontalHeader()
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Interactive) # Folio
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Interactive) # Fecha
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Interactive) # Hora
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.Stretch)     # Cajero
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.Interactive) # Medio Pago
        header.setSectionResizeMode(6, QHeaderView.ResizeMode.Interactive) # Total

        self.tabla.setColumnWidth(1, 130)
        self.tabla.setColumnWidth(2, 110)
        self.tabla.setColumnWidth(3, 90)
        self.tabla.setColumnWidth(5, 130)
        self.tabla.setColumnWidth(6, 130)

        self.tabla.setAlternatingRowColors(True)

        self.tabla.setStyleSheet("""
            QTableWidget { 
                background-color: #FFFFFF; 
                alternate-background-color: #F8F8FC;
                border: 1px solid #E0E0E0; 
                border-radius: 10px;
                font-size: 13px; 
                color: #1E1E24; 
                gridline-color: #EEEEEE;
            }
            QHeaderView::section { 
                background-color: #2D2D3A; 
                color: #FFFFFF;
                padding: 12px 10px; 
                border: none; 
                font-weight: bold; 
                font-size: 13px;
            }
            QTableWidget::item { padding: 8px; }
            QTableWidget::item:selected { 
                background-color: #BFA2DB; 
                color: #1E1E24; 
                font-weight: bold;
            }
        """)

        layout.addWidget(self.tabla)

        # Cargar datos iniciales
        self.cargar_ventas()

    def crear_tarjeta_kpi(self, titulo, valor_inicial, color_borde):
        card = QWidget()
        card.setStyleSheet(f"""
            QWidget {{
                background-color: #2D2D3A;
                border-radius: 10px;
                border-left: 5px solid {color_borde};
            }}
        """)
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(16, 12, 16, 12)
        card_layout.setSpacing(4)

        lbl_tit = QLabel(titulo)
        lbl_tit.setStyleSheet("color: #A0A0B0; font-size: 12px; font-weight: bold;")

        lbl_val = QLabel(valor_inicial)
        lbl_val.setStyleSheet("color: #FFFFFF; font-size: 18px; font-weight: bold;")

        if "Transacciones" in titulo:
            self.lbl_total_transacciones = lbl_val
        elif "Recaudado" in titulo:
            self.lbl_total_recaudado = lbl_val

        card_layout.addWidget(lbl_tit)
        card_layout.addWidget(lbl_val)
        return card

    def showEvent(self, event):
        super().showEvent(event)
        self.cargar_ventas()

    def cargar_ventas(self, lista_ventas=None):
        """Llena la tabla y recalcula los totales."""
        self.tabla.setRowCount(0)
        
        # Simulación / Consulta de ventas (conectar a tu service cuando esté listo)
        ventas = lista_ventas if lista_ventas is not None else []
        
        total_acumulado = 0.0

        for fila_idx, v in enumerate(ventas):
            self.tabla.insertRow(fila_idx)
            
            es_dict = isinstance(v, dict)
            monto = float(v["total_monto"] if es_dict else v[5])
            total_acumulado += monto

            celdas = [
                str(v["id_venta"] if es_dict else v[0]),
                str(v["folio"] if es_dict else f"TCK-{1000 + (v['id_venta'] if es_dict else v[0])}"),
                str(v["fecha"] if es_dict else v[1]),
                str(v["hora"] if es_dict else v[2]),
                str(v["cajero"] if es_dict else "Caja Principal"),
                str(v["medio_pago"] if es_dict else "Efectivo"),
                f"${monto:,.0f}".replace(',', '.')
            ]

            for col_idx, valor in enumerate(celdas):
                item = QTableWidgetItem(valor)
                if col_idx in [1, 2, 3, 5]:
                    item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                elif col_idx == 6: # Monto Venta
                    item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                else:
                    item.setTextAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
                
                self.tabla.setItem(fila_idx, col_idx, item)

        if hasattr(self, 'lbl_total_transacciones'):
            self.lbl_total_transacciones.setText(str(len(ventas)))
        if hasattr(self, 'lbl_total_recaudado'):
            self.lbl_total_recaudado.setText(f"${total_acumulado:,.0f}".replace(',', '.'))

    def filtrar_hoy(self):
        hoy = QDate.currentDate()
        self.date_desde.setDate(hoy)
        self.date_hasta.setDate(hoy)
        self.aplicar_filtro_fechas()

    def filtrar_mes(self):
        hoy = QDate.currentDate()
        primer_dia_mes = QDate(hoy.year(), hoy.month(), 1)
        self.date_desde.setDate(primer_dia_mes)
        self.date_hasta.setDate(hoy)
        self.aplicar_filtro_fechas()

    def aplicar_filtro_fechas(self):
        desde_str = self.date_desde.date().toString("yyyy-MM-dd")
        hasta_str = self.date_hasta.date().toString("yyyy-MM-dd")
        # Aquí conectas con tu función SQL: buscar_ventas_por_rango(desde_str, hasta_str)
        self.cargar_ventas([])

    def filtrar_por_folio(self, texto):
        # Lógica de búsqueda reactiva por boleta/folio
        pass
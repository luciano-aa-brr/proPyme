from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                               QTableWidget, QTableWidgetItem, QHeaderView, 
                               QLabel, QFrame, QMessageBox, QDateEdit, 
                               QListWidget, QAbstractItemView, QCalendarWidget)
from PySide6.QtCore import Qt, QDate

from services.historial_service import obtener_historial_ventas, obtener_detalle_historial

class HistorialView(QWidget):
    def __init__(self):
        super().__init__()
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)

        # --- PANEL IZQUIERDO: Filtros y Tabla de Ventas ---
        left_layout = QVBoxLayout()
        left_layout.setSpacing(12)

        # --- BARRA SUPERIOR DE FILTROS ---
        filter_layout = QHBoxLayout()
        filter_layout.setSpacing(12)

        lbl_desde = QLabel("Desde:")
        lbl_desde.setStyleSheet("font-size: 14px; font-weight: bold; color: #FFFFFF;")
        
        self.date_desde = QDateEdit(QDate.currentDate())
        self.date_desde.setCalendarPopup(True) # Habilita el desplegable del calendario
        self.date_desde.setDisplayFormat("dd/MM/yyyy")

        lbl_hasta = QLabel("Hasta:")
        lbl_hasta.setStyleSheet("font-size: 14px; font-weight: bold; color: #FFFFFF;")
        
        self.date_hasta = QDateEdit(QDate.currentDate())
        self.date_hasta.setCalendarPopup(True) # Habilita el desplegable del calendario
        self.date_hasta.setDisplayFormat("dd/MM/yyyy")

        # Estilo visual moderno para el QDateEdit y el Popup del Calendario
        estilo_fecha = """
            QDateEdit {
                padding: 8px 12px;
                border: 1px solid #4A4A5A;
                border-radius: 6px;
                background-color: #2D2D3A;
                color: #FFFFFF;
                font-size: 13px;
                font-weight: bold;
                min-width: 120px;
            }
            QDateEdit:focus {
                border: 2px solid #BFA2DB;
            }
            QDateEdit::drop-down {
                subcontrol-origin: padding;
                subcontrol-position: top right;
                width: 24px;
                border-left: none;
            }
            /* Estilos del Calendario Desplegable */
            QCalendarWidget QWidget {
                background-color: #FFFFFF;
                color: #1E1E24;
            }
            QCalendarWidget QToolButton {
                color: #1E1E24;
                font-weight: bold;
                background-color: #F4F4F9;
                border: none;
                border-radius: 4px;
                padding: 4px;
            }
            QCalendarWidget QToolButton:hover {
                background-color: #BFA2DB;
            }
            QCalendarWidget QMenu {
                background-color: #FFFFFF;
                color: #1E1E24;
            }
            QCalendarWidget QSpinBox {
                background-color: #FFFFFF;
                color: #1E1E24;
            }
            QCalendarWidget QAbstractItemView:enabled {
                color: #1E1E24;
                selection-background-color: #BFA2DB;
                selection-color: #1E1E24;
            }
        """
        self.date_desde.setStyleSheet(estilo_fecha)
        self.date_hasta.setStyleSheet(estilo_fecha)

        self.btn_filtrar = QPushButton("🔍  Filtrar")
        self.btn_filtrar.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_filtrar.setStyleSheet("""
            QPushButton {
                background-color: #BFA2DB;
                color: #1E1E24;
                border: none;
                padding: 9px 20px;
                border-radius: 6px;
                font-weight: bold;
                font-size: 13px;
            }
            QPushButton:hover { background-color: #A888CB; }
            QPushButton:pressed { background-color: #9370DB; color: white; }
        """)
        self.btn_filtrar.clicked.connect(self.aplicar_filtro)

        self.btn_todos = QPushButton("Ver Todos")
        self.btn_todos.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_todos.setStyleSheet("""
            QPushButton {
                background-color: #3A3A4A;
                color: #FFFFFF;
                border: 1px solid #5A5A6A;
                padding: 9px 18px;
                border-radius: 6px;
                font-weight: bold;
                font-size: 13px;
            }
            QPushButton:hover { background-color: #4A4A5A; }
        """)
        self.btn_todos.clicked.connect(self.cargar_todas_las_ventas)

        filter_layout.addWidget(lbl_desde)
        filter_layout.addWidget(self.date_desde)
        filter_layout.addSpacing(6)
        filter_layout.addWidget(lbl_hasta)
        filter_layout.addWidget(self.date_hasta)
        filter_layout.addSpacing(6)
        filter_layout.addWidget(self.btn_filtrar)
        filter_layout.addWidget(self.btn_todos)
        filter_layout.addStretch()

        left_layout.addLayout(filter_layout)

        # --- TABLA DE HISTORIAL ---
        self.tabla_historial = QTableWidget(0, 5)
        self.tabla_historial.setHorizontalHeaderLabels(["ID Venta", "Fecha", "Hora", "Medio Pago", "Total Monto"])
        
        self.tabla_historial.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.tabla_historial.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.tabla_historial.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)

        header = self.tabla_historial.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        
        self.tabla_historial.setStyleSheet("""
            QTableWidget { 
                background-color: #FFFFFF; 
                border: 1px solid #E0E0E0; 
                border-radius: 8px; 
                font-size: 13px; 
                color: #1E1E24; 
                gridline-color: #F0F0F5;
            }
            QHeaderView::section { 
                background-color: #F4F4F9; 
                padding: 10px; 
                border: none; 
                border-bottom: 2px solid #E0E0E0; 
                font-weight: bold; 
                color: #2D2D3A; 
            }
            QTableWidget::item { padding: 6px; }
            QTableWidget::item:selected { background-color: #BFA2DB; color: #1E1E24; font-weight: bold; }
        """)
        self.tabla_historial.itemSelectionChanged.connect(self.mostrar_detalle_seleccionado)

        left_layout.addWidget(self.tabla_historial)

        # --- PANEL DERECHO: Métricas y Detalle de Productos ---
        right_frame = QFrame()
        right_frame.setFixedWidth(340)
        right_frame.setStyleSheet("""
            QFrame { background-color: #FFFFFF; border: 1px solid #E0E0E0; border-radius: 12px; } 
            QLabel { border: none; }
        """)
        
        right_layout = QVBoxLayout(right_frame)
        right_layout.setContentsMargins(20, 20, 20, 20)
        right_layout.setSpacing(12)

        titulo_metricas = QLabel("📊 Métricas de Ventas")
        titulo_metricas.setStyleSheet("font-size: 16px; font-weight: bold; color: #1E1E24;")
        right_layout.addWidget(titulo_metricas)

        self.lbl_total_recaudado = QLabel("Total Recaudado: $0")
        self.lbl_cant_ventas = QLabel("Total Ventas: 0")
        self.lbl_ticket_promedio = QLabel("Ticket Promedio: $0")

        for lbl in [self.lbl_total_recaudado, self.lbl_cant_ventas, self.lbl_ticket_promedio]:
            lbl.setStyleSheet("font-size: 13px; color: #444; background-color: #F8F8FC; padding: 10px; border-radius: 6px; font-weight: bold;")

        right_layout.addWidget(self.lbl_total_recaudado)
        right_layout.addWidget(self.lbl_cant_ventas)
        right_layout.addWidget(self.lbl_ticket_promedio)

        right_layout.addSpacing(10)

        lbl_detalle_titulo = QLabel("🛒 Detalle de Venta Seleccionada:")
        lbl_detalle_titulo.setStyleSheet("font-size: 14px; font-weight: bold; color: #1E1E24;")
        right_layout.addWidget(lbl_detalle_titulo)

        self.lista_detalle = QListWidget()
        self.lista_detalle.setStyleSheet("""
            QListWidget { 
                background-color: #FFFFFF; 
                border: 1px solid #E0E0E0; 
                border-radius: 6px; 
                padding: 8px; 
                font-size: 12px; 
                color: #333; 
            }
        """)
        right_layout.addWidget(self.lista_detalle)

        layout.addLayout(left_layout)
        layout.addWidget(right_frame)

        self.cargar_todas_las_ventas()

    def showEvent(self, event):
        """Refresco automático al ingresar a la vista de Historial."""
        super().showEvent(event)
        self.cargar_todas_las_ventas()

    def cargar_todas_las_ventas(self):
        exito, resultado = obtener_historial_ventas()
        if exito:
            self.poblar_tabla_y_metricas(resultado)

    def aplicar_filtro(self):
        f_inicio = self.date_desde.date().toString("yyyy-MM-dd")
        f_fin = self.date_hasta.date().toString("yyyy-MM-dd")
        
        exito, resultado = obtener_historial_ventas(f_inicio, f_fin)
        if exito:
            self.poblar_tabla_y_metricas(resultado)

    def poblar_tabla_y_metricas(self, ventas):
        self.tabla_historial.setRowCount(0)
        self.lista_detalle.clear()
        
        total_monto_acumulado = 0.0
        cantidad_ventas = len(ventas)

        for fila_idx, venta in enumerate(ventas):
            self.tabla_historial.insertRow(fila_idx)
            
            es_dict = isinstance(venta, dict)
            id_v = str(venta["id_venta"] if es_dict else venta[0])
            fecha = str(venta["fecha"] if es_dict else venta[1])
            hora = str(venta["hora"] if es_dict else venta[2])
            medio = str(venta["medio_pago"] if es_dict else venta[3])
            monto_val = float(venta["total_monto"] if es_dict else venta[4])
            
            total_monto_acumulado += monto_val
            monto_str = f"${monto_val:,.0f}".replace(',', '.')

            for col_idx, val in enumerate([f"V-{id_v}", fecha, hora, medio, monto_str]):
                item = QTableWidgetItem(val)
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.tabla_historial.setItem(fila_idx, col_idx, item)

        # Cálculo de Métricas
        ticket_prom = (total_monto_acumulado / cantidad_ventas) if cantidad_ventas > 0 else 0.0
        
        self.lbl_total_recaudado.setText(f"💰 Total Recaudado: ${total_monto_acumulado:,.0f}".replace(',', '.'))
        self.lbl_cant_ventas.setText(f"🧾 Total Ventas: {cantidad_ventas}")
        self.lbl_ticket_promedio.setText(f"📈 Ticket Promedio: ${ticket_prom:,.0f}".replace(',', '.'))

    def mostrar_detalle_seleccionado(self):
        fila = self.tabla_historial.currentRow()
        if fila < 0:
            return

        id_texto = self.tabla_historial.item(fila, 0).text()
        id_venta = int(id_texto.replace("V-", ""))

        self.lista_detalle.clear()
        exito, items = obtener_detalle_historial(id_venta)
        
        if exito:
            for item in items:
                es_dict = isinstance(item, dict)
                sku = item["sku"] if es_dict else item[0]
                nombre = item["nombre_producto"] if es_dict else item[1]
                cant = float(item["cantidad"] if es_dict else item[2])
                unid = item["unidad_medida"] if es_dict else item[3]
                subtotal = float(item["subtotal"] if es_dict else item[5])

                cant_str = f"{cant:.3f} kg" if unid in ["KG", "LT", "GR"] else f"{int(cant)} un"
                subtotal_str = f"${subtotal:,.0f}".replace(',', '.')

                self.lista_detalle.addItem(f"• [{sku}] {nombre}\n   Cant: {cant_str} | Total: {subtotal_str}")
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                               QLineEdit, QTableWidget, QTableWidgetItem, 
                               QHeaderView, QLabel, QMessageBox, QDateEdit, 
                               QAbstractItemView, QFrame, QDialog)
from PySide6.QtCore import Qt, QDate
from PySide6.QtGui import QColor

from services.historial_service import obtener_historial_completo, obtener_detalle_ticket

class ModalDetalleVenta(QDialog):
    """Modal emergente para inspeccionar los productos de una venta seleccionada."""
    def __init__(self, id_venta, folio, fecha, total, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"Detalle de Venta - {folio}")
        self.setFixedSize(560, 420)
        self.setStyleSheet("background-color: #FFFFFF; border-radius: 10px;")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)

        lbl_tit = QLabel(f"📄 Comprobante: {folio}")
        lbl_tit.setStyleSheet("font-size: 16px; font-weight: bold; color: #1E1E24;")
        
        lbl_sub = QLabel(f"Fecha: {fecha} | Total: ${total:,.0f}".replace(',', '.'))
        lbl_sub.setStyleSheet("font-size: 13px; font-weight: bold; color: #6A1B9A;")

        layout.addWidget(lbl_tit)
        layout.addWidget(lbl_sub)

        tabla = QTableWidget(0, 4)
        tabla.setHorizontalHeaderLabels(["SKU", "Producto", "Cant / Peso", "Subtotal"])
        tabla.verticalHeader().setVisible(False)
        tabla.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        tabla.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        tabla.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)

        tabla.setStyleSheet("""
            QTableWidget { 
                background-color: #FFFFFF; 
                border: 1px solid #E0E0E0; 
                border-radius: 6px; 
                color: #1E1E24; 
                font-size: 12px;
            }
            QHeaderView::section { 
                background-color: #2D2D3A; 
                color: #FFFFFF; 
                padding: 6px; 
                font-weight: bold; 
            }
        """)

        exito, items = obtener_detalle_ticket(id_venta)
        if exito:
            for f_idx, item in enumerate(items):
                tabla.insertRow(f_idx)
                
                unidad = item["unidad"]
                cant_str = f"{item['cantidad']:.3f}".rstrip('0').rstrip('.') + f" {unidad.lower()}" if unidad in ["KG", "LT", "GR"] else str(int(item["cantidad"]))

                tabla.setItem(f_idx, 0, QTableWidgetItem(item["sku"]))
                tabla.setItem(f_idx, 1, QTableWidgetItem(item["nombre"]))
                
                it_cant = QTableWidgetItem(cant_str)
                it_cant.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                tabla.setItem(f_idx, 2, it_cant)

                it_sub = QTableWidgetItem(f"${item['subtotal']:,.0f}".replace(',', '.'))
                it_sub.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                tabla.setItem(f_idx, 3, it_sub)

        layout.addWidget(tabla)

        btn_cerrar = QPushButton("Cerrar")
        btn_cerrar.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_cerrar.setStyleSheet("""
            QPushButton {
                background-color: #BFA2DB; color: #1E1E24; font-weight: bold;
                padding: 8px 16px; border-radius: 6px; font-size: 13px;
            }
            QPushButton:hover { background-color: #A888CB; }
        """)
        btn_cerrar.clicked.connect(self.accept)
        layout.addWidget(btn_cerrar, alignment=Qt.AlignmentFlag.AlignRight)


class HistorialView(QWidget):
    def __init__(self):
        super().__init__()

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(16)

        # --- 1. TARJETAS KPI ---
        kpi_layout = QHBoxLayout()
        kpi_layout.setSpacing(16)

        self.card_total_ventas = self.crear_tarjeta_kpi("Transacciones Realizadas", "0", "#BFA2DB")
        self.card_recaudado = self.crear_tarjeta_kpi("Monto Total Recaudado", "$0", "#81C784")

        kpi_layout.addWidget(self.card_total_ventas)
        kpi_layout.addWidget(self.card_recaudado)
        layout.addLayout(kpi_layout)

        # --- 2. BARRA DE FILTROS ---
        filtro_container = QFrame()
        filtro_container.setStyleSheet("""
            QFrame {
                background-color: #2D2D3A;
                border-radius: 8px;
            }
        """)
        filtro_layout = QHBoxLayout(filtro_container)
        filtro_layout.setContentsMargins(12, 10, 12, 10)
        filtro_layout.setSpacing(10)

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
            QDateEdit:focus { border: 2px solid #BFA2DB; }
            QDateEdit::drop-down {
                subcontrol-origin: padding;
                subcontrol-position: top right;
                width: 22px;
                border-left: 1px solid #4A4A5A;
                background-color: #3A3A4A;
                border-top-right-radius: 6px;
                border-bottom-right-radius: 6px;
            }
            QDateEdit::down-arrow {
                image: none;
                border-left: 4px solid transparent;
                border-right: 4px solid transparent;
                border-top: 5px solid #BFA2DB;
                width: 0;
                height: 0;
            }
        """

        lbl_desde = QLabel("Desde:")
        lbl_desde.setStyleSheet("color: #FFFFFF; font-weight: bold; font-size: 13px;")
        
        self.date_desde = QDateEdit()
        self.date_desde.setCalendarPopup(True)
        self.date_desde.setDate(QDate.currentDate())
        self.date_desde.setDisplayFormat("yyyy-MM-dd")
        self.date_desde.setStyleSheet(estilo_fecha)

        lbl_hasta = QLabel("Hasta:")
        lbl_hasta.setStyleSheet("color: #FFFFFF; font-weight: bold; font-size: 13px;")

        self.date_hasta = QDateEdit()
        self.date_hasta.setCalendarPopup(True)
        self.date_hasta.setDate(QDate.currentDate())
        self.date_hasta.setDisplayFormat("yyyy-MM-dd")
        self.date_hasta.setStyleSheet(estilo_fecha)

        self.btn_filtrar = QPushButton("🔍 Filtrar")
        self.btn_filtrar.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_filtrar.setStyleSheet("""
            QPushButton {
                background-color: #BFA2DB; color: #1E1E24; border: none;
                padding: 7px 16px; border-radius: 6px; font-weight: bold; font-size: 13px;
            }
            QPushButton:hover { background-color: #A888CB; }
        """)
        self.btn_filtrar.clicked.connect(self.aplicar_filtro_fechas)

        estilo_btn_rapido = """
            QPushButton {
                background-color: #3A3A4A; color: #FFFFFF; border: 1px solid #4A4A5A;
                padding: 7px 14px; border-radius: 6px; font-size: 12px; font-weight: bold;
            }
            QPushButton:hover { background-color: #4A4A5A; border-color: #BFA2DB; }
        """

        self.btn_hoy = QPushButton("Hoy")
        self.btn_mes = QPushButton("Este Mes")
        self.btn_todos = QPushButton("Ver Todo")

        for b in [self.btn_hoy, self.btn_mes, self.btn_todos]:
            b.setStyleSheet(estilo_btn_rapido)
            b.setCursor(Qt.CursorShape.PointingHandCursor)

        self.btn_hoy.clicked.connect(self.filtrar_hoy)
        self.btn_mes.clicked.connect(self.filtrar_mes)
        self.btn_todos.clicked.connect(self.filtrar_todos)

        self.search_folio = QLineEdit()
        self.search_folio.setPlaceholderText("🔍 Buscar por Folio / ID...")
        self.search_folio.setStyleSheet("""
            QLineEdit {
                background-color: #1E1E24; color: #FFFFFF; border: 1px solid #4A4A5A;
                border-radius: 6px; padding: 6px 12px; font-size: 13px;
            }
            QLineEdit:focus { border: 2px solid #BFA2DB; }
            QLineEdit::placeholder { color: #8E8E9F; }
        """)
        self.search_folio.textChanged.connect(self.aplicar_filtro_fechas)

        filtro_layout.addWidget(lbl_desde)
        filtro_layout.addWidget(self.date_desde)
        filtro_layout.addWidget(lbl_hasta)
        filtro_layout.addWidget(self.date_hasta)
        filtro_layout.addWidget(self.btn_filtrar)
        filtro_layout.addWidget(self.btn_hoy)
        filtro_layout.addWidget(self.btn_mes)
        filtro_layout.addWidget(self.btn_todos)
        filtro_layout.addStretch()
        filtro_layout.addWidget(self.search_folio)

        layout.addWidget(filtro_container)

        # --- 3. TABLA DE HISTORIAL ---
        self.tabla = QTableWidget(0, 7)
        self.tabla.setHorizontalHeaderLabels(["ID", "Folio Ticket", "Fecha", "Hora", "Turno / Cajero", "Medio de Pago", "Total Venta"])
        self.tabla.verticalHeader().setVisible(False)
        self.tabla.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.tabla.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.tabla.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.tabla.setColumnHidden(0, True)

        header = self.tabla.horizontalHeader()
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Interactive)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Interactive)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Interactive)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.Interactive)
        header.setSectionResizeMode(6, QHeaderView.ResizeMode.Interactive)

        self.tabla.setColumnWidth(1, 130)
        self.tabla.setColumnWidth(2, 110)
        self.tabla.setColumnWidth(3, 90)
        self.tabla.setColumnWidth(5, 140)
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
        self.tabla.doubleClicked.connect(self.abrir_modal_detalle_fila)
        layout.addWidget(self.tabla)

        self.cargar_ventas()

    def crear_tarjeta_kpi(self, titulo, valor_inicial, color_borde):
        card = QWidget()
        card.setStyleSheet(f"background-color: #2D2D3A; border-radius: 10px; border-left: 5px solid {color_borde};")
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
        """Llena la tabla con la lista provista o consulta el servicio."""
        if lista_ventas is None:
            desde = self.date_desde.date().toString("yyyy-MM-dd")
            hasta = self.date_hasta.date().toString("yyyy-MM-dd")
            texto = self.search_folio.text().strip()
            exito, resultado = obtener_historial_completo(desde, hasta, texto)
            ventas = resultado if exito else []
        else:
            ventas = lista_ventas

        self.tabla.setRowCount(0)
        total_acumulado = 0.0

        for fila_idx, v in enumerate(ventas):
            self.tabla.insertRow(fila_idx)
            monto = float(v["total_monto"])
            total_acumulado += monto

            celdas = [
                str(v["id_venta"]),
                f"TCK-{1000 + v['id_venta']}",
                str(v["fecha"]),
                str(v["hora"]),
                str(v["cajero"]),
                str(v["medio_pago"]),
                f"${monto:,.0f}".replace(',', '.')
            ]

            for col_idx, valor in enumerate(celdas):
                item = QTableWidgetItem(valor)
                if col_idx in [1, 2, 3, 5]:
                    item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                elif col_idx == 6:
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
        self.cargar_ventas()

    def filtrar_mes(self):
        hoy = QDate.currentDate()
        primer_dia = QDate(hoy.year(), hoy.month(), 1)
        self.date_desde.setDate(primer_dia)
        self.date_hasta.setDate(hoy)
        self.cargar_ventas()

    def filtrar_todos(self):
        self.date_desde.setDate(QDate(2020, 1, 1))
        self.date_hasta.setDate(QDate.currentDate().addYears(1))
        self.cargar_ventas()

    def aplicar_filtro_fechas(self):
        self.cargar_ventas()

    def abrir_modal_detalle_fila(self, index):
        fila = index.row()
        id_venta = int(self.tabla.item(fila, 0).text())
        folio = self.tabla.item(fila, 1).text()
        fecha = self.tabla.item(fila, 2).text()
        monto_txt = self.tabla.item(fila, 6).text().replace('$', '').replace('.', '')
        monto = float(monto_txt) if monto_txt.isdigit() else 0.0

        modal = ModalDetalleVenta(id_venta, folio, fecha, monto, self)
        modal.exec()
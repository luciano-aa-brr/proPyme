from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, 
                               QPushButton, QLabel, QTableWidget, QTableWidgetItem, 
                               QHeaderView, QFrame, QAbstractItemView)
from PySide6.QtCore import Qt

class CajaView(QWidget):
    def __init__(self):
        super().__init__()

        layout = QHBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(18)

        # ==========================================
        # COLUMNA IZQUIERDA: ESTADO Y MOVIMIENTOS
        # ==========================================
        col_izq = QVBoxLayout()
        col_izq.setSpacing(16)

        # 1. Encabezado con Estado
        header_layout = QHBoxLayout()
        lbl_titulo = QLabel("📊 Control y Estado Financiero de Caja")
        lbl_titulo.setStyleSheet("color: #FFFFFF; font-size: 18px; font-weight: bold;")
        
        lbl_estado = QLabel("🟢 TURNO ACTIVO")
        lbl_estado.setStyleSheet("""
            background-color: #2E7D32; color: #FFFFFF; 
            padding: 4px 10px; border-radius: 6px; 
            font-size: 11px; font-weight: bold;
        """)
        header_layout.addWidget(lbl_titulo)
        header_layout.addStretch()
        header_layout.addWidget(lbl_estado)
        col_izq.addLayout(header_layout)

        # 2. Grid de Métricas Financieras (Tarjetas)
        grid_kpi = QGridLayout()
        grid_kpi.setSpacing(12)

        self.card_fondo = self.crear_card_metrica("Fondo Base Inicial", "$50.000", "#BFA2DB")
        self.card_efectivo = self.crear_card_metrica("Efectivo Total en Caja", "$50.000", "#81C784")
        self.card_debito = self.crear_card_metrica("Recaudado Débito", "$0", "#64B5F6")
        self.card_credito = self.crear_card_metrica("Recaudado Crédito", "$0", "#4DD0E1")
        self.card_transf = self.crear_card_metrica("Recaudado Transferencia", "$0", "#BA68C8")

        grid_kpi.addWidget(self.card_fondo, 0, 0)
        grid_kpi.addWidget(self.card_efectivo, 0, 1)
        grid_kpi.addWidget(self.card_debito, 1, 0)
        grid_kpi.addWidget(self.card_credito, 1, 1)
        grid_kpi.addWidget(self.card_transf, 1, 2)
        
        # Banner Gran Total
        self.banner_total = QFrame()
        self.banner_total.setStyleSheet("""
            QFrame {
                background-color: #BFA2DB;
                border-radius: 8px;
                padding: 10px 16px;
            }
        """)
        b_layout = QHBoxLayout(self.banner_total)
        lbl_b_tit = QLabel("💰 Total Recaudado en el Turno:")
        lbl_b_tit.setStyleSheet("color: #1E1E24; font-size: 15px; font-weight: bold;")
        self.lbl_b_monto = QLabel("$50.000")
        self.lbl_b_monto.setStyleSheet("color: #1E1E24; font-size: 20px; font-weight: 900;")
        b_layout.addWidget(lbl_b_tit)
        b_layout.addStretch()
        b_layout.addWidget(self.lbl_b_monto)

        grid_kpi.addWidget(self.banner_total, 0, 2)
        col_izq.addLayout(grid_kpi)

        # 3. Tabla de Auditoría de Movimientos
        lbl_movs = QLabel("📋 Historial de Entradas, Salidas y Gastos del Turno")
        lbl_movs.setStyleSheet("color: #FFFFFF; font-size: 14px; font-weight: bold;")
        col_izq.addWidget(lbl_movs)

        self.tabla_movs = QTableWidget(0, 5)
        self.tabla_movs.setHorizontalHeaderLabels(["Hora", "Tipo Movimiento", "Monto", "Motivo / Detalle", "Usuario"])
        self.tabla_movs.verticalHeader().setVisible(False)
        self.tabla_movs.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.tabla_movs.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.tabla_movs.setAlternatingRowColors(True)

        header = self.tabla_movs.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Interactive)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Interactive)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Interactive)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.Interactive)

        self.tabla_movs.setColumnWidth(0, 80)
        self.tabla_movs.setColumnWidth(1, 140)
        self.tabla_movs.setColumnWidth(2, 110)
        self.tabla_movs.setColumnWidth(4, 120)

        self.tabla_movs.setStyleSheet("""
            QTableWidget { 
                background-color: #FFFFFF; 
                alternate-background-color: #F8F8FC;
                border: 1px solid #E0E0E0; 
                border-radius: 8px;
                font-size: 13px; 
                color: #1E1E24; 
                gridline-color: #EEEEEE;
            }
            QHeaderView::section { 
                background-color: #2D2D3A; 
                color: #FFFFFF;
                padding: 8px; 
                border: none; 
                font-weight: bold; 
                font-size: 12px;
            }
        """)
        col_izq.addWidget(self.tabla_movs)

        layout.addLayout(col_izq, 3)

        # ==========================================
        # COLUMNA DERECHA: PANEL DE ACCIONES
        # ==========================================
        panel_acciones = QFrame()
        panel_acciones.setMaximumWidth(280)
        panel_acciones.setStyleSheet("""
            QFrame {
                background-color: #FFFFFF;
                border-radius: 12px;
                border: 1px solid #E0E0E0;
            }
        """)
        panel_layout = QVBoxLayout(panel_acciones)
        panel_layout.setContentsMargins(18, 20, 18, 20)
        panel_layout.setSpacing(12)

        lbl_tit_acc = QLabel("Acciones de Caja")
        lbl_tit_acc.setStyleSheet("color: #1E1E24; font-size: 16px; font-weight: bold; border: none;")
        lbl_tit_acc.setAlignment(Qt.AlignmentFlag.AlignCenter)
        panel_layout.addWidget(lbl_tit_acc)

        estilo_btn_accion = """
            QPushButton {
                background-color: #F4F4F9;
                color: #2D2D3A;
                border: 1px solid #D1D1E0;
                padding: 12px;
                border-radius: 8px;
                font-size: 13px;
                font-weight: bold;
                text-align: left;
            }
            QPushButton:hover { background-color: #E6E6FA; border-color: #BFA2DB; }
        """

        self.btn_inyectar = QPushButton("➕  Ingresar Efectivo")
        self.btn_retiro = QPushButton("➖  Registrar Retiro / Gasto")
        self.btn_fondo = QPushButton("⚙️  Ajustar Fondo Base")

        for b in [self.btn_inyectar, self.btn_retiro, self.btn_fondo]:
            b.setStyleSheet(estilo_btn_accion)
            b.setCursor(Qt.CursorShape.PointingHandCursor)
            panel_layout.addWidget(b)

        panel_layout.addStretch()

        # Botón Cierre de Turno
        self.btn_cierre = QPushButton("🔒 Cerrar Caja / Turno")
        self.btn_cierre.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_cierre.setStyleSheet("""
            QPushButton {
                background-color: #BFA2DB;
                color: #1E1E24;
                border: none;
                padding: 14px;
                border-radius: 8px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover { background-color: #A888CB; }
            QPushButton:pressed { background-color: #9370DB; color: white; }
        """)
        panel_layout.addWidget(self.btn_cierre)

        layout.addWidget(panel_acciones, 1)

    def crear_card_metrica(self, titulo, valor, color_borde):
        card = QFrame()
        card.setStyleSheet(f"""
            QFrame {{
                background-color: #2D2D3A;
                border-radius: 8px;
                border-left: 4px solid {color_borde};
                padding: 8px 12px;
            }}
        """)
        c_layout = QVBoxLayout(card)
        c_layout.setContentsMargins(4, 4, 4, 4)
        c_layout.setSpacing(2)

        lbl_t = QLabel(titulo)
        lbl_t.setStyleSheet("color: #A0A0B0; font-size: 11px; font-weight: bold; border: none;")
        
        lbl_v = QLabel(valor)
        lbl_v.setStyleSheet("color: #FFFFFF; font-size: 16px; font-weight: bold; border: none;")

        c_layout.addWidget(lbl_t)
        c_layout.addWidget(lbl_v)
        return card
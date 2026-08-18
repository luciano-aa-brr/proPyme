from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, 
                               QPushButton, QLabel, QTableWidget, QTableWidgetItem, 
                               QHeaderView, QFrame, QAbstractItemView, QDialog, 
                               QLineEdit, QMessageBox)
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor

from services.caja_service import (obtener_resumen_caja, registrar_movimiento, 
                                   ajustar_fondo_inicial, procesar_cierre_turno,
                                   obtener_historial_cierres)

def mostrar_alerta_caja(parent, titulo, mensaje, icono=QMessageBox.Icon.Warning):
    """Muestra alertas modales con texto oscuro y contraste garantizado."""
    msg = QMessageBox(parent)
    msg.setWindowTitle(titulo)
    msg.setText(mensaje)
    msg.setIcon(icono)
    msg.setStyleSheet("""
        QMessageBox {
            background-color: #FFFFFF;
        }
        QLabel {
            color: #1E1E24;
            font-size: 13px;
            font-weight: 500;
        }
        QPushButton {
            background-color: #BFA2DB;
            color: #1E1E24;
            border: none;
            padding: 6px 18px;
            border-radius: 6px;
            font-weight: bold;
            min-width: 80px;
        }
        QPushButton:hover {
            background-color: #A888CB;
        }
    """)
    msg.exec()


class ModalMovimientoCaja(QDialog):
    """Modal para registrar ingresos, retiros o ajuste de fondo."""
    def __init__(self, titulo, tipo, usuario="Administrador", parent=None):
        super().__init__(parent)
        self.setWindowTitle(titulo)
        self.setFixedSize(380, 270)
        self.setStyleSheet("""
            QDialog { background-color: #FFFFFF; border-radius: 10px; }
            QLabel { color: #1E1E24; }
        """)

        self.tipo = tipo
        self.usuario = usuario
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(12)

        lbl_tit = QLabel(titulo)
        lbl_tit.setStyleSheet("font-size: 16px; font-weight: bold; color: #1E1E24;")
        layout.addWidget(lbl_tit)

        estilo_inps = """
            QLineEdit {
                background-color: #F8F8FC; 
                border: 1px solid #D1D1E0; 
                border-radius: 6px; 
                padding: 10px; 
                font-size: 14px; 
                color: #1E1E24;
            }
            QLineEdit:focus { border: 2px solid #BFA2DB; background-color: #FFFFFF; }
        """

        self.inp_monto = QLineEdit()
        self.inp_monto.setPlaceholderText("Monto ($) Ej: 15000")
        self.inp_monto.setStyleSheet(estilo_inps)
        layout.addWidget(self.inp_monto)

        self.inp_motivo = QLineEdit()
        self.inp_motivo.setPlaceholderText("Motivo / Detalle (Ej: Compra de insumos)")
        self.inp_motivo.setStyleSheet(estilo_inps)
        if self.tipo == "FONDO":
            self.inp_motivo.setText("Ajuste de Fondo Base")
            self.inp_motivo.setEnabled(False)
        layout.addWidget(self.inp_motivo)

        btn_box = QHBoxLayout()
        btn_cancelar = QPushButton("Cancelar")
        btn_guardar = QPushButton("💾 Guardar")
        
        btn_cancelar.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_guardar.setCursor(Qt.CursorShape.PointingHandCursor)

        btn_cancelar.setStyleSheet("""
            QPushButton { background-color: #EFEFF5; color: #333; padding: 10px; border-radius: 6px; font-weight: bold; }
            QPushButton:hover { background-color: #E2E2EC; }
        """)
        btn_guardar.setStyleSheet("""
            QPushButton { background-color: #BFA2DB; color: #1E1E24; padding: 10px; border-radius: 6px; font-weight: bold; }
            QPushButton:hover { background-color: #A888CB; }
        """)
        
        btn_cancelar.clicked.connect(self.reject)
        btn_guardar.clicked.connect(self.guardar)

        btn_box.addWidget(btn_cancelar)
        btn_box.addWidget(btn_guardar)
        layout.addLayout(btn_box)

    def guardar(self):
        monto_txt = self.inp_monto.text().strip().replace('.', '').replace(',', '')
        motivo = self.inp_motivo.text().strip()

        if not monto_txt.isdigit() or float(monto_txt) <= 0:
            mostrar_alerta_caja(self, "Monto Inválido", "Ingresa un monto numérico válido mayor a 0.")
            return

        monto = float(monto_txt)
        if self.tipo == "FONDO":
            exito, msg = ajustar_fondo_inicial(monto)
        else:
            exito, msg = registrar_movimiento(self.tipo, monto, motivo, usuario=self.usuario)

        if exito:
            self.accept()
        else:
            mostrar_alerta_caja(self, "Error", msg, QMessageBox.Icon.Critical)


class ModalCierreCaja(QDialog):
    """Modal de conteo de efectivo y auditoría de arqueo final."""
    def __init__(self, resumen_actual, usuario="Administrador", parent=None):
        super().__init__(parent)
        self.setWindowTitle("Arqueo y Cierre de Turno")
        self.setFixedSize(480, 530)
        self.setStyleSheet("""
            QDialog { background-color: #FFFFFF; border-radius: 10px; }
            QLabel { color: #1E1E24; }
        """)

        self.resumen = resumen_actual
        self.usuario = usuario
        self.teorico = self.resumen["efectivo_caja"]

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(12)

        lbl_tit = QLabel("🔒 Arqueo Final de Caja")
        lbl_tit.setStyleSheet("font-size: 18px; font-weight: bold; color: #1E1E24;")
        layout.addWidget(lbl_tit)

        # Resumen Teórico del Sistema con contraste nítido
        box_resumen = QFrame()
        box_resumen.setStyleSheet("background-color: #F8F8FC; border: 1px solid #D1D1E0; border-radius: 8px; padding: 10px;")
        l_res = QGridLayout(box_resumen)
        l_res.setSpacing(8)
        
        lbl_fb_t = QLabel("Fondo Base Inicial:")
        lbl_fb_t.setStyleSheet("color: #4A4A5A; font-size: 13px; font-weight: bold;")
        lbl_fb_v = QLabel(f"${self.resumen['fondo_base']:,.0f}".replace(',', '.'))
        lbl_fb_v.setStyleSheet("color: #1E1E24; font-size: 13px; font-weight: bold;")

        lbl_vt_t = QLabel("Total Ventas Turno:")
        lbl_vt_t.setStyleSheet("color: #4A4A5A; font-size: 13px; font-weight: bold;")
        lbl_vt_v = QLabel(f"${self.resumen['total_turno']:,.0f}".replace(',', '.'))
        lbl_vt_v.setStyleSheet("color: #1E1E24; font-size: 13px; font-weight: bold;")
        
        lbl_t_tit = QLabel("Efectivo Teórico en Gaveta:")
        lbl_t_tit.setStyleSheet("color: #1E1E24; font-size: 14px; font-weight: bold;")
        lbl_teorico = QLabel(f"${self.teorico:,.0f}".replace(',', '.'))
        lbl_teorico.setStyleSheet("color: #6A1B9A; font-size: 16px; font-weight: 900;")
        
        l_res.addWidget(lbl_fb_t, 0, 0)
        l_res.addWidget(lbl_fb_v, 0, 1)
        l_res.addWidget(lbl_vt_t, 1, 0)
        l_res.addWidget(lbl_vt_v, 1, 1)
        l_res.addWidget(lbl_t_tit, 2, 0)
        l_res.addWidget(lbl_teorico, 2, 1)
        layout.addWidget(box_resumen)

        # Declaración física del cajero
        lbl_inst = QLabel(f"Cajero responsable: <b>{self.usuario}</b><br>Ingresa el monto de efectivo real contado:")
        lbl_inst.setStyleSheet("font-size: 13px; color: #1E1E24;")
        layout.addWidget(lbl_inst)

        estilo_inps = """
            QLineEdit {
                background-color: #F8F8FC; 
                color: #1E1E24; 
                border: 1px solid #D1D1E0; 
                border-radius: 6px; 
                padding: 10px; 
                font-size: 15px; 
                font-weight: bold;
            }
            QLineEdit:focus { border: 2px solid #BFA2DB; background-color: #FFFFFF; }
        """

        self.inp_efectivo = QLineEdit()
        self.inp_efectivo.setPlaceholderText("Efectivo contado ($)")
        self.inp_efectivo.setStyleSheet(estilo_inps)
        self.inp_efectivo.textChanged.connect(self.calcular_diferencia_en_vivo)
        layout.addWidget(self.inp_efectivo)

        self.inp_obs = QLineEdit()
        self.inp_obs.setPlaceholderText("Observaciones de auditoría (Opcional)")
        self.inp_obs.setStyleSheet("""
            QLineEdit {
                background-color: #F8F8FC; 
                color: #1E1E24; 
                border: 1px solid #D1D1E0; 
                border-radius: 6px; 
                padding: 8px; 
                font-size: 13px;
            }
            QLineEdit:focus { border: 2px solid #BFA2DB; background-color: #FFFFFF; }
        """)
        layout.addWidget(self.inp_obs)

        # Indicador de Descuadre en Tiempo Real
        self.box_dif = QFrame()
        self.box_dif.setStyleSheet("background-color: #E8F5E9; border-radius: 8px; padding: 10px; border: 1px solid #C8E6C9;")
        l_dif = QHBoxLayout(self.box_dif)
        
        self.lbl_dif_txt = QLabel("Estado del Cuadre:")
        self.lbl_dif_txt.setStyleSheet("font-size: 13px; font-weight: bold; color: #2E7D32;")
        
        self.lbl_dif_val = QLabel("$0 (Caja Cuadrada)")
        self.lbl_dif_val.setStyleSheet("font-size: 14px; font-weight: 900; color: #2E7D32;")
        
        l_dif.addWidget(self.lbl_dif_txt)
        l_dif.addStretch()
        l_dif.addWidget(self.lbl_dif_val)
        layout.addWidget(self.box_dif)

        layout.addStretch()

        # Botones de Acción
        btn_box = QHBoxLayout()
        btn_cancelar = QPushButton("Cancelar")
        btn_confirmar = QPushButton("🔒 Confirmar Cierre de Turno")
        
        btn_cancelar.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_confirmar.setCursor(Qt.CursorShape.PointingHandCursor)

        btn_cancelar.setStyleSheet("""
            QPushButton { background-color: #EFEFF5; color: #333; padding: 10px 18px; border-radius: 6px; font-weight: bold; }
            QPushButton:hover { background-color: #E2E2EC; }
        """)
        btn_confirmar.setStyleSheet("""
            QPushButton { background-color: #BFA2DB; color: #1E1E24; padding: 10px 22px; border-radius: 6px; font-weight: bold; font-size: 13px; }
            QPushButton:hover { background-color: #A888CB; }
        """)
        
        btn_cancelar.clicked.connect(self.reject)
        btn_confirmar.clicked.connect(self.ejecutar_cierre)

        btn_box.addWidget(btn_cancelar)
        btn_box.addWidget(btn_confirmar)
        layout.addLayout(btn_box)

    def calcular_diferencia_en_vivo(self):
        txt = self.inp_efectivo.text().strip().replace('.', '')
        try:
            declarado = float(txt) if txt else 0.0
            dif = declarado - self.teorico
            if dif == 0:
                self.box_dif.setStyleSheet("background-color: #E8F5E9; border: 1px solid #C8E6C9; border-radius: 8px; padding: 10px;")
                self.lbl_dif_txt.setStyleSheet("color: #2E7D32; font-weight: bold;")
                self.lbl_dif_val.setStyleSheet("color: #2E7D32; font-weight: 900;")
                self.lbl_dif_val.setText("$0 (Caja Cuadrada)")
            elif dif > 0:
                self.box_dif.setStyleSheet("background-color: #E3F2FD; border: 1px solid #BBDEFB; border-radius: 8px; padding: 10px;")
                self.lbl_dif_txt.setStyleSheet("color: #1565C0; font-weight: bold;")
                self.lbl_dif_val.setStyleSheet("color: #1565C0; font-weight: 900;")
                self.lbl_dif_val.setText(f"+${dif:,.0f} (Sobrante)".replace(',', '.'))
            else:
                self.box_dif.setStyleSheet("background-color: #FFEBEE; border: 1px solid #FFCDD2; border-radius: 8px; padding: 10px;")
                self.lbl_dif_txt.setStyleSheet("color: #C62828; font-weight: bold;")
                self.lbl_dif_val.setStyleSheet("color: #C62828; font-weight: 900;")
                self.lbl_dif_val.setText(f"-${abs(dif):,.0f} (Faltante)".replace(',', '.'))
        except ValueError:
            pass

    def ejecutar_cierre(self):
        txt = self.inp_efectivo.text().strip().replace('.', '')
        if not txt.isdigit():
            mostrar_alerta_caja(self, "Valor Inválido", "Por favor ingresa el monto de efectivo que contaste en caja.")
            self.inp_efectivo.setFocus()
            return

        efectivo_dec = float(txt)
        obs = self.inp_obs.text().strip()

        exito, data = procesar_cierre_turno(
            efectivo_declarado=efectivo_dec,
            observaciones=obs,
            usuario=self.usuario
        )

        if exito:
            mostrar_alerta_caja(
                self, 
                "Cierre Exitoso", 
                f"El turno fue cerrado y registrado para auditoría con éxito.\n\n"
                f"• Cajero: {self.usuario}\n"
                f"• Estado: {data['estado_cuadre']}\n"
                f"• Total Ventas Turno: ${data['total_ventas']:,.0f}\n"
                f"• Efectivo Declarado: ${data['declarado']:,.0f}".replace(',', '.'),
                QMessageBox.Icon.Information
            )
            self.accept()
        else:
            mostrar_alerta_caja(self, "Error al Cerrar", data, QMessageBox.Icon.Critical)


class ModalHistorialCierres(QDialog):
    """Modal moderno de auditoría y análisis de cierres de caja."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Auditoría y Cuadre de Cierres de Turno")
        self.resize(1020, 580)
        self.setStyleSheet("""
            QDialog {
                background-color: #1E1E24;
                border-radius: 12px;
            }
            QLabel {
                color: #FFFFFF;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 22, 24, 22)
        layout.setSpacing(16)

        # --- Encabezado ---
        header_layout = QHBoxLayout()
        lbl_tit = QLabel("📋 Historial y Auditoría Contable de Caja")
        lbl_tit.setStyleSheet("font-size: 18px; font-weight: bold; color: #FFFFFF;")
        
        lbl_sub = QLabel("Registro histórico e inmutable de turnos y arqueos")
        lbl_sub.setStyleSheet("font-size: 12px; color: #A0A0B0;")
        
        tit_vbox = QVBoxLayout()
        tit_vbox.addWidget(lbl_tit)
        tit_vbox.addWidget(lbl_sub)
        header_layout.addLayout(tit_vbox)
        header_layout.addStretch()
        layout.addLayout(header_layout)

        # --- Métricas Rápidas KPI ---
        exito, cierres = obtener_historial_cierres()
        cierres = cierres if exito else []

        total_turnos = len(cierres)
        turnos_cuadrados = sum(1 for c in cierres if "CUADRADO" in str(c.get("estado_cuadre", "")))
        total_descuadres = sum(float(c.get("diferencia_efectivo", 0)) for c in cierres)

        kpi_layout = QHBoxLayout()
        kpi_layout.setSpacing(12)
        
        kpi_layout.addWidget(self.crear_card_resumen("Turnos Auditados", str(total_turnos), "#BFA2DB"))
        kpi_layout.addWidget(self.crear_card_resumen("Cajas Cuadradas", f"{turnos_cuadrados} / {total_turnos}", "#81C784"))
        
        color_dif = "#81C784" if total_descuadres == 0 else ("#64B5F6" if total_descuadres > 0 else "#E57373")
        simbolo = "+" if total_descuadres > 0 else ""
        kpi_layout.addWidget(self.crear_card_resumen("Balance Neto Descuadres", f"{simbolo}${total_descuadres:,.0f}".replace(',', '.'), color_dif))
        
        layout.addLayout(kpi_layout)

        # --- Tabla Principal ---
        self.tabla = QTableWidget(0, 7)
        self.tabla.setHorizontalHeaderLabels([
            "Fecha y Hora", "Cajero a Cargo", "Total Ventas", "Efectivo Teórico", 
            "Efectivo Real", "Diferencia", "Estado Cuadre"
        ])
        self.tabla.verticalHeader().setVisible(False)
        self.tabla.verticalHeader().setDefaultSectionSize(40)
        self.tabla.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.tabla.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.tabla.setAlternatingRowColors(True)

        header = self.tabla.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Interactive)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Interactive)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Interactive)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Interactive)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.Interactive)
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.Interactive)
        header.setSectionResizeMode(6, QHeaderView.ResizeMode.Stretch)

        self.tabla.setColumnWidth(0, 160)
        self.tabla.setColumnWidth(1, 140)
        self.tabla.setColumnWidth(2, 110)
        self.tabla.setColumnWidth(3, 120)
        self.tabla.setColumnWidth(4, 120)
        self.tabla.setColumnWidth(5, 110)

        self.tabla.setStyleSheet("""
            QTableWidget { 
                background-color: #2D2D3A; 
                alternate-background-color: #242430;
                border: 1px solid #3A3A4A; 
                border-radius: 8px;
                font-size: 13px; 
                color: #FFFFFF; 
                gridline-color: #3A3A4A;
            }
            QHeaderView::section { 
                background-color: #1A1A22; 
                color: #BFA2DB;
                padding: 10px 8px; 
                border: none; 
                font-weight: bold; 
                font-size: 12px;
            }
            QTableWidget::item { 
                padding: 6px 8px; 
            }
            QTableWidget::item:selected { 
                background-color: #3E3E52; 
                color: #FFFFFF; 
            }
        """)

        # Poblar filas
        for f_idx, c in enumerate(cierres):
            self.tabla.insertRow(f_idx)
            
            dif = float(c.get("diferencia_efectivo", 0))
            dif_str = f"${dif:,.0f}".replace(',', '.')
            if dif > 0:
                dif_str = f"+{dif_str}"

            items = [
                f"{c.get('fecha_cierre', '')} {c.get('hora_cierre', '')}",
                str(c.get('usuario_cierre', 'Cajero')),
                f"${float(c.get('total_ventas', 0)):,.0f}".replace(',', '.'),
                f"${float(c.get('efectivo_teorico', 0)):,.0f}".replace(',', '.'),
                f"${float(c.get('efectivo_real_declarado', 0)):,.0f}".replace(',', '.'),
                dif_str,
                "" # Celda del Badge
            ]

            for col_idx, val in enumerate(items):
                if col_idx < 6:
                    it = QTableWidgetItem(val)
                    if col_idx in [0, 1]:
                        it.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                    else:
                        it.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                    
                    if col_idx == 5:
                        if dif < 0:
                            it.setForeground(QColor("#FF8A80"))
                        elif dif > 0:
                            it.setForeground(QColor("#80D8FF"))
                        else:
                            it.setForeground(QColor("#B9F6CA"))
                    
                    self.tabla.setItem(f_idx, col_idx, it)

            estado = str(c.get('estado_cuadre', 'CUADRADO'))
            badge_widget = self.crear_badge_estado(estado, dif)
            self.tabla.setCellWidget(f_idx, 6, badge_widget)

        layout.addWidget(self.tabla)

        # --- Pie con Botón de Salida ---
        footer_layout = QHBoxLayout()
        btn_cerrar = QPushButton("Cerrar")
        btn_cerrar.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_cerrar.setStyleSheet("""
            QPushButton {
                background-color: #BFA2DB; 
                color: #1E1E24; 
                font-weight: bold;
                padding: 9px 24px; 
                border-radius: 6px; 
                font-size: 13px;
                border: none;
            }
            QPushButton:hover { 
                background-color: #D8BFD8; 
            }
        """)
        btn_cerrar.clicked.connect(self.accept)
        footer_layout.addStretch()
        footer_layout.addWidget(btn_cerrar)

        layout.addLayout(footer_layout)

    def crear_card_resumen(self, titulo, valor, color_borde):
        card = QFrame()
        card.setStyleSheet(f"""
            QFrame {{
                background-color: #2D2D3A; 
                border-radius: 8px; 
                border-left: 4px solid {color_borde};
                padding: 6px 12px;
            }}
        """)
        l = QVBoxLayout(card)
        l.setContentsMargins(4, 4, 4, 4)
        l.setSpacing(2)

        lbl_t = QLabel(titulo)
        lbl_t.setStyleSheet("color: #A0A0B0; font-size: 11px; font-weight: bold;")
        lbl_v = QLabel(valor)
        lbl_v.setStyleSheet(f"color: {color_borde}; font-size: 15px; font-weight: 900;")

        l.addWidget(lbl_t)
        l.addWidget(lbl_v)
        return card

    def crear_badge_estado(self, estado, diferencia):
        contenedor = QWidget()
        l = QHBoxLayout(contenedor)
        l.setContentsMargins(4, 2, 4, 2)
        l.setAlignment(Qt.AlignmentFlag.AlignCenter)

        badge = QLabel()
        badge.setAlignment(Qt.AlignmentFlag.AlignCenter)

        if diferencia == 0:
            badge.setText("✔ CUADRADO")
            badge.setStyleSheet("""
                background-color: #1B5E20; 
                color: #FFFFFF; 
                font-weight: bold; 
                font-size: 11px; 
                border-radius: 4px; 
                padding: 4px 12px;
            """)
        elif diferencia > 0:
            badge.setText(f"▲ SOBRANTE (+${diferencia:,.0f})".replace(',', '.'))
            badge.setStyleSheet("""
                background-color: #0D47A1; 
                color: #FFFFFF; 
                font-weight: bold; 
                font-size: 11px; 
                border-radius: 4px; 
                padding: 4px 12px;
            """)
        else:
            badge.setText(f"▼ FALTANTE (-${abs(diferencia):,.0f})".replace(',', '.'))
            badge.setStyleSheet("""
                background-color: #B71C1C; 
                color: #FFFFFF; 
                font-weight: bold; 
                font-size: 11px; 
                border-radius: 4px; 
                padding: 4px 12px;
            """)

        l.addWidget(badge)
        return contenedor


class CajaView(QWidget):
    def __init__(self, usuario_actual=None):
        super().__init__()

        self.usuario_actual = usuario_actual or {"nombre": "Administrador", "rol": "Administrador"}

        layout = QHBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(18)

        # ==========================================
        # COLUMNA IZQUIERDA: MÉTRICAS Y AUDITORÍA
        # ==========================================
        col_izq = QVBoxLayout()
        col_izq.setSpacing(16)

        header_layout = QHBoxLayout()
        lbl_titulo = QLabel("📊 Control y Estado Financiero de Caja")
        lbl_titulo.setStyleSheet("color: #FFFFFF; font-size: 18px; font-weight: bold;")
        
        lbl_estado = QLabel("🟢 TURNO ACTIVO")
        lbl_estado.setStyleSheet("background-color: #2E7D32; color: #FFFFFF; padding: 4px 10px; border-radius: 6px; font-size: 11px; font-weight: bold;")
        header_layout.addWidget(lbl_titulo)
        header_layout.addStretch()
        header_layout.addWidget(lbl_estado)
        col_izq.addLayout(header_layout)

        # Tarjetas KPI
        grid_kpi = QGridLayout()
        grid_kpi.setSpacing(12)

        self.lbl_val_fondo = QLabel("$0")
        self.lbl_val_efectivo = QLabel("$0")
        self.lbl_val_debito = QLabel("$0")
        self.lbl_val_credito = QLabel("$0")
        self.lbl_val_transf = QLabel("$0")

        grid_kpi.addWidget(self.crear_card("Fondo Base Inicial", self.lbl_val_fondo, "#BFA2DB"), 0, 0)
        grid_kpi.addWidget(self.crear_card("Efectivo Total en Caja", self.lbl_val_efectivo, "#81C784"), 0, 1)
        grid_kpi.addWidget(self.crear_card("Recaudado Débito", self.lbl_val_debito, "#64B5F6"), 1, 0)
        grid_kpi.addWidget(self.crear_card("Recaudado Crédito", self.lbl_val_credito, "#4DD0E1"), 1, 1)
        grid_kpi.addWidget(self.crear_card("Recaudado Transferencia", self.lbl_val_transf, "#BA68C8"), 1, 2)
        
        # Banner Gran Total
        banner_total = QFrame()
        banner_total.setStyleSheet("background-color: #BFA2DB; border-radius: 8px; padding: 10px 16px;")
        b_layout = QHBoxLayout(banner_total)
        lbl_b_tit = QLabel("💰 Total Recaudado Turno:")
        lbl_b_tit.setStyleSheet("color: #1E1E24; font-size: 14px; font-weight: bold;")
        self.lbl_b_monto = QLabel("$0")
        self.lbl_b_monto.setStyleSheet("color: #1E1E24; font-size: 20px; font-weight: 900;")
        b_layout.addWidget(lbl_b_tit)
        b_layout.addStretch()
        b_layout.addWidget(self.lbl_b_monto)

        grid_kpi.addWidget(banner_total, 0, 2)
        col_izq.addLayout(grid_kpi)

        # Tabla de Movimientos
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

        self.tabla_movs.setColumnWidth(0, 90)
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
                padding: 10px; 
                border: none; 
                font-weight: bold; 
                font-size: 12px;
            }
            QTableWidget::item { padding: 6px; }
            QTableWidget::item:selected { background-color: #BFA2DB; color: #1E1E24; font-weight: bold; }
        """)
        col_izq.addWidget(self.tabla_movs)
        layout.addLayout(col_izq, 3)

        # ==========================================
        # COLUMNA DERECHA: ACCIONES
        # ==========================================
        panel_acciones = QFrame()
        panel_acciones.setMaximumWidth(280)
        panel_acciones.setStyleSheet("background-color: #FFFFFF; border-radius: 12px; border: 1px solid #E0E0E0;")
        panel_layout = QVBoxLayout(panel_acciones)
        panel_layout.setContentsMargins(18, 20, 18, 20)
        panel_layout.setSpacing(12)

        lbl_tit_acc = QLabel("Acciones de Caja")
        lbl_tit_acc.setStyleSheet("color: #1E1E24; font-size: 16px; font-weight: bold; border: none;")
        lbl_tit_acc.setAlignment(Qt.AlignmentFlag.AlignCenter)
        panel_layout.addWidget(lbl_tit_acc)

        estilo_btn_accion = """
            QPushButton {
                background-color: #F4F4F9; color: #2D2D3A; border: 1px solid #D1D1E0;
                padding: 12px; border-radius: 8px; font-size: 13px; font-weight: bold; text-align: left;
            }
            QPushButton:hover { background-color: #E6E6FA; border-color: #BFA2DB; }
        """

        self.btn_historial_cierres = QPushButton("📋  Auditoría de Cierres")
        self.btn_inyectar = QPushButton("➕  Ingresar Efectivo")
        self.btn_retiro = QPushButton("➖  Registrar Retiro / Gasto")
        self.btn_fondo = QPushButton("⚙️  Ajustar Fondo Base")

        for b in [self.btn_historial_cierres, self.btn_inyectar, self.btn_retiro, self.btn_fondo]:
            b.setStyleSheet(estilo_btn_accion)
            b.setCursor(Qt.CursorShape.PointingHandCursor)
            panel_layout.addWidget(b)

        self.btn_historial_cierres.clicked.connect(self.abrir_historial_cierres)
        self.btn_inyectar.clicked.connect(lambda: self.abrir_modal("Ingresar Efectivo", "INGRESO"))
        self.btn_retiro.clicked.connect(lambda: self.abrir_modal("Registrar Retiro", "RETIRO"))
        self.btn_fondo.clicked.connect(lambda: self.abrir_modal("Ajustar Fondo Base", "FONDO"))

        panel_layout.addStretch()

        btn_cierre = QPushButton("🔒 Cerrar Caja / Turno")
        btn_cierre.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_cierre.setStyleSheet("""
            QPushButton {
                background-color: #BFA2DB; color: #1E1E24; border: none;
                padding: 14px; border-radius: 8px; font-size: 14px; font-weight: bold;
            }
            QPushButton:hover { background-color: #A888CB; }
        """)
        btn_cierre.clicked.connect(self.cerrar_turno)
        panel_layout.addWidget(btn_cierre)

        layout.addWidget(panel_acciones, 1)

        self.refrescar_datos()

    def showEvent(self, event):
        super().showEvent(event)
        self.refrescar_datos()

    def crear_card(self, titulo, label_valor, color_borde):
        card = QFrame()
        card.setStyleSheet(f"background-color: #2D2D3A; border-radius: 8px; border-left: 4px solid {color_borde}; padding: 8px 12px;")
        c_layout = QVBoxLayout(card)
        c_layout.setContentsMargins(4, 4, 4, 4)
        c_layout.setSpacing(2)

        lbl_t = QLabel(titulo)
        lbl_t.setStyleSheet("color: #A0A0B0; font-size: 11px; font-weight: bold; border: none;")
        label_valor.setStyleSheet("color: #FFFFFF; font-size: 16px; font-weight: bold; border: none;")

        c_layout.addWidget(lbl_t)
        c_layout.addWidget(label_valor)
        return card

    def refrescar_datos(self):
        res = obtener_resumen_caja()
        
        self.lbl_val_fondo.setText(f"${res['fondo_base']:,.0f}".replace(',', '.'))
        self.lbl_val_efectivo.setText(f"${res['efectivo_caja']:,.0f}".replace(',', '.'))
        self.lbl_val_debito.setText(f"${res['debito']:,.0f}".replace(',', '.'))
        self.lbl_val_credito.setText(f"${res['credito']:,.0f}".replace(',', '.'))
        self.lbl_val_transf.setText(f"${res['transferencia']:,.0f}".replace(',', '.'))
        self.lbl_b_monto.setText(f"${res['total_turno']:,.0f}".replace(',', '.'))

        self.tabla_movs.setRowCount(0)
        for fila_idx, m in enumerate(res["movimientos"]):
            self.tabla_movs.insertRow(fila_idx)
            
            tipo_txt = "🟢 Ingreso Extra" if m["tipo"] == "INGRESO" else "🔴 Retiro / Gasto"
            if m["tipo"] == "FONDO":
                tipo_txt = "⚙️ Ajuste Fondo"

            items = [
                m["hora"],
                tipo_txt,
                f"${m['monto']:,.0f}".replace(',', '.'),
                m["motivo"] or "Sin detalle",
                m["usuario"]
            ]

            for col_idx, val in enumerate(items):
                it = QTableWidgetItem(val)
                if col_idx in [0, 1, 4]:
                    it.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                elif col_idx == 2:
                    it.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                self.tabla_movs.setItem(fila_idx, col_idx, it)

    def abrir_modal(self, titulo, tipo):
        nom_usr = self.usuario_actual.get("nombre", "Administrador")
        modal = ModalMovimientoCaja(titulo, tipo, usuario=nom_usr, parent=self)
        if modal.exec() == QDialog.DialogCode.Accepted:
            self.refrescar_datos()

    def abrir_historial_cierres(self):
        modal = ModalHistorialCierres(self)
        modal.exec()

    def cerrar_turno(self):
        resumen = obtener_resumen_caja()
        nom_usr = self.usuario_actual.get("nombre", "Administrador")
        modal = ModalCierreCaja(resumen, usuario=nom_usr, parent=self)
        if modal.exec() == QDialog.DialogCode.Accepted:
            self.refrescar_datos()
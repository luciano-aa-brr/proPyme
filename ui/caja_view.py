from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                               QLabel, QFrame, QMessageBox, QInputDialog, QListWidget)
from PySide6.QtCore import Qt

from services.caja_service import obtener_arqueo_actual

class CajaView(QWidget):
    def __init__(self):
        super().__init__()
        
        self.fondo_inicial = 50000.0  # Fondo base inicial para sencillos/vueltos
        self.movimientos = []          # Registro de entradas/salidas manuales de dinero
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)

        # --- PANEL IZQUIERDO: Resumen de Arqueo en Tiempo Real ---
        left_layout = QVBoxLayout()
        left_layout.setSpacing(15)

        lbl_titulo = QLabel("📊 Estado Financiero de la Caja (Turno Activo)")
        lbl_titulo.setStyleSheet("font-size: 18px; font-weight: bold; color: #FFFFFF;")
        left_layout.addWidget(lbl_titulo)

        # Tarjetas de Totales por Medio de Pago
        grid_frame = QFrame()
        grid_frame.setStyleSheet("""
            QFrame { background-color: #FFFFFF; border: 1px solid #E0E0E0; border-radius: 12px; }
            QLabel { border: none; }
        """)
        grid_layout = QVBoxLayout(grid_frame)
        grid_layout.setContentsMargins(20, 20, 20, 20)
        grid_layout.setSpacing(12)

        self.lbl_fondo_inicial = QLabel("💵 Fondo Base Inicial (Sencillo): $50.000")
        self.lbl_efectivo = QLabel("💵 Recaudado en Efectivo: $0")
        self.lbl_debito = QLabel("💳 Recaudado en Débito: $0")
        self.lbl_credito = QLabel("💳 Recaudado en Crédito: $0")
        self.lbl_transferencia = QLabel("📲 Recaudado en Transferencia: $0")
        self.lbl_total_esperado = QLabel("💰 Total Esperado en Caja: $50.000")

        for lbl in [self.lbl_fondo_inicial, self.lbl_efectivo, self.lbl_debito, 
                    self.lbl_credito, self.lbl_transferencia]:
            lbl.setStyleSheet("font-size: 14px; color: #333344; padding: 6px; background-color: #F8F8FC; border-radius: 6px;")

        self.lbl_total_esperado.setStyleSheet("""
            font-size: 22px; 
            font-weight: bold; 
            color: #9370DB; 
            background-color: #E6E6FA; 
            padding: 12px; 
            border-radius: 8px;
            margin-top: 10px;
        """)

        grid_layout.addWidget(self.lbl_fondo_inicial)
        grid_layout.addWidget(self.lbl_efectivo)
        grid_layout.addWidget(self.lbl_debito)
        grid_layout.addWidget(self.lbl_credito)
        grid_layout.addWidget(self.lbl_transferencia)
        grid_layout.addWidget(self.lbl_total_esperado)

        left_layout.addWidget(grid_frame)

        # Historial de Movimientos Manuales (Sangrías / Depósitos de dinero)
        lbl_mov = QLabel("📝 Registros e Inyecciones de Efectivo:")
        lbl_mov.setStyleSheet("font-size: 14px; font-weight: bold; color: #FFFFFF;")
        left_layout.addWidget(lbl_mov)

        self.lista_movimientos = QListWidget()
        self.lista_movimientos.setStyleSheet("""
            QListWidget {
                background-color: #FFFFFF;
                border: 1px solid #E0E0E0;
                border-radius: 8px;
                padding: 8px;
                font-size: 13px;
                color: #333;
            }
        """)
        left_layout.addWidget(self.lista_movimientos)

        # --- PANEL DERECHO: Acciones Operativas de Caja ---
        right_frame = QFrame()
        right_frame.setFixedWidth(340)
        right_frame.setStyleSheet("""
            QFrame { background-color: #FFFFFF; border: 1px solid #E0E0E0; border-radius: 12px; } 
            QLabel { border: none; }
        """)
        right_layout = QVBoxLayout(right_frame)
        right_layout.setContentsMargins(20, 20, 20, 20)
        right_layout.setSpacing(14)

        titulo_acciones = QLabel("Acciones de Caja")
        titulo_acciones.setStyleSheet("font-size: 18px; font-weight: bold; color: #1E1E24;")
        titulo_acciones.setAlignment(Qt.AlignmentFlag.AlignCenter)
        right_layout.addWidget(titulo_acciones)

        self.btn_ajustar_fondo = QPushButton("⚙️ Ajustar Fondo Base Inicial")
        self.btn_ingresar_dinero = QPushButton("📥 Registrar Inyección de Efectivo")
        self.btn_retirar_dinero = QPushButton("📤 Registrar Retiro / Sangría")
        
        estilo_btn_operativo = """
            QPushButton {
                background-color: #F4F4F9;
                color: #2D2D3A;
                border: 1px solid #D1D1E0;
                padding: 12px;
                border-radius: 6px;
                font-weight: bold;
                font-size: 13px;
            }
            QPushButton:hover { background-color: #BFA2DB; color: #1E1E24; }
        """

        for btn in [self.btn_ajustar_fondo, self.btn_ingresar_dinero, self.btn_retirar_dinero]:
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setStyleSheet(estilo_btn_operativo)
            right_layout.addWidget(btn)

        self.btn_ajustar_fondo.clicked.connect(self.ajustar_fondo_base)
        self.btn_ingresar_dinero.clicked.connect(lambda: self.registrar_movimiento_efectivo("Inyección"))
        self.btn_retirar_dinero.clicked.connect(lambda: self.registrar_movimiento_efectivo("Retiro"))

        right_layout.addStretch()

        # Botón Principal de Cierre de Caja
        self.btn_cierre = QPushButton("🔒 Realizar Cierre de Caja / Turno")
        self.btn_cierre.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_cierre.setStyleSheet("""
            QPushButton { 
                background-color: #BFA2DB; 
                color: #1E1E24; 
                border: none; 
                padding: 16px; 
                border-radius: 8px; 
                font-size: 15px; 
                font-weight: bold; 
            }
            QPushButton:hover { background-color: #A888CB; }
            QPushButton:pressed { background-color: #9370DB; color: white; }
        """)
        self.btn_cierre.clicked.connect(self.ejecutar_cierre_caja)
        right_layout.addWidget(self.btn_cierre)

        layout.addLayout(left_layout)
        layout.addWidget(right_frame)

        self.actualizar_panel_caja()

    def showEvent(self, event):
        """Refresco dinámico al abrir la pestaña 'Caja'."""
        super().showEvent(event)
        self.actualizar_panel_caja()

    def actualizar_panel_caja(self):
        exito, resumen = obtener_arqueo_actual()
        if exito:
            efectivo_ventas = resumen.get("Efectivo", 0.0)
            debito = resumen.get("Débito", 0.0)
            credito = resumen.get("Crédito", 0.0)
            transf = resumen.get("Transferencia", 0.0)

            # Cálculo de ajuste por inyecciones y retiros
            ajustes_efectivo = sum(mov["monto"] for mov in self.movimientos)
            efectivo_total_en_caja = self.fondo_inicial + efectivo_ventas + ajustes_efectivo
            total_general_sistema = efectivo_total_en_caja + debito + credito + transf

            self.lbl_fondo_inicial.setText(f"💵 Fondo Base Inicial: ${self.fondo_inicial:,.0f}".replace(',', '.'))
            self.lbl_efectivo.setText(f"💵 Efectivo en Caja (Ventas + Fondo): ${efectivo_total_en_caja:,.0f}".replace(',', '.'))
            self.lbl_debito.setText(f"💳 Recaudado en Débito: ${debito:,.0f}".replace(',', '.'))
            self.lbl_credito.setText(f"💳 Recaudado en Crédito: ${credito:,.0f}".replace(',', '.'))
            self.lbl_transferencia.setText(f"📲 Recaudado en Transferencia: ${transf:,.0f}".replace(',', '.'))
            
            self.lbl_total_esperado.setText(f"💰 Total Recaudado Turno: ${total_general_sistema:,.0f}".replace(',', '.'))

    def ajustar_fondo_base(self):
        monto, ok = QInputDialog.getDouble(
            self, 
            "Ajuste de Fondo Inicial", 
            "Ingrese el monto base para dar sencillo ($):", 
            value=self.fondo_inicial, 
            minValue=0.0, 
            maxValue=1000000.0, 
            decimals=0
        )
        if ok:
            self.fondo_inicial = monto
            self.actualizar_panel_caja()

    def registrar_movimiento_efectivo(self, tipo):
        monto, ok = QInputDialog.getDouble(
            self, 
            f"Registro de {tipo}", 
            f"Ingrese el monto del {tipo.lower()} en efectivo ($):", 
            value=10000.0, 
            minValue=100.0, 
            maxValue=500000.0, 
            decimals=0
        )
        if ok and monto > 0:
            monto_real = monto if tipo == "Inyección" else -monto
            self.movimientos.append({"tipo": tipo, "monto": monto_real})
            
            signo = "+" if tipo == "Inyección" else "-"
            monto_str = f"${monto:,.0f}".replace(',', '.')
            self.lista_movimientos.addItem(f"• [{tipo}] {signo}{monto_str}")
            self.actualizar_panel_caja()

    def ejecutar_cierre_caja(self):
        exito, resumen = obtener_arqueo_actual()
        if not exito:
            QMessageBox.warning(self, "Error", "No se pudo obtener el arqueo para el cierre.")
            return

        efectivo_ventas = resumen.get("Efectivo", 0.0)
        ajustes_efectivo = sum(mov["monto"] for mov in self.movimientos)
        efectivo_esperado = self.fondo_inicial + efectivo_ventas + ajustes_efectivo

        monto_fisico, ok = QInputDialog.getDouble(
            self, 
            "Cierre de Caja - Conteo Físico", 
            f"Efectivo esperado en caja (Fondo + Ventas): ${efectivo_esperado:,.0f}\n\n"
            f"Ingrese el dinero real contado en la caja ($):".replace(',', '.'),
            value=efectivo_esperado,
            minValue=0.0,
            maxValue=10000000.0,
            decimals=0
        )

        if ok:
            diferencia = monto_fisico - efectivo_esperado
            dif_str = f"${abs(diferencia):,.0f}".replace(',', '.')
            
            if diferencia == 0:
                resultado_str = "✅ Cierre perfecto. Sin diferencias en efectivo."
            elif diferencia > 0:
                resultado_str = f"⚠️ Sobrante en caja: +{dif_str}"
            else:
                resultado_str = f"❌ Faltante en caja: -{dif_str}"

            tot_ventas = resumen.get("Total", 0.0)

            resumen_msg = (
                f"📋 RESUMEN DE CIERRE DE CAJA\n\n"
                f"• Fondo Inicial: ${self.fondo_inicial:,.0f}\n"
                f"• Ventas en Efectivo: ${efectivo_ventas:,.0f}\n"
                f"• Efectivo Esperado en Caja: ${efectivo_esperado:,.0f}\n"
                f"• Conteo Físico Real: ${monto_fisico:,.0f}\n\n"
                f"• Ventas Tarjetas/Transf: ${(tot_ventas - efectivo_ventas):,.0f}\n"
                f"• TOTAL VENDIDO EN TURNO: ${tot_ventas:,.0f}\n\n"
                f"CUADRATURA: {resultado_str}"
            ).replace(',', '.')

            QMessageBox.information(self, "Cierre de Caja Completado", resumen_msg)
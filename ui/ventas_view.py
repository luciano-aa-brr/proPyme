from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, 
                               QPushButton, QLineEdit, QTableWidget, QTableWidgetItem, 
                               QHeaderView, QLabel, QMessageBox, QFrame, 
                               QAbstractItemView, QDialog)
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QKeySequence, QShortcut

from services.ventas_service import buscar_producto_para_venta, registrar_venta_directa

class DialogoPeso(QDialog):
    """Modal express para ingresar peso exacto en productos por KG/GR/LT."""
    def __init__(self, nombre_producto, precio_unitario, unidad="KG", parent=None):
        super().__init__(parent)
        self.setWindowTitle("Ingreso de Peso / Cantidad")
        self.setFixedSize(360, 420)
        self.setStyleSheet("background-color: #1E1E24; border-radius: 10px;")
        
        self.peso_ingresado = 1.0
        self.precio_unit = precio_unitario

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)

        lbl_nombre = QLabel(f"⚖️ {nombre_producto}")
        lbl_nombre.setStyleSheet("color: #FFFFFF; font-size: 16px; font-weight: bold;")
        lbl_nombre.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl_nombre.setWordWrap(True)

        lbl_precio = QLabel(f"Precio por {unidad}: ${precio_unitario:,.0f}".replace(',', '.'))
        lbl_precio.setStyleSheet("color: #BFA2DB; font-size: 13px; font-weight: bold;")
        lbl_precio.setAlignment(Qt.AlignmentFlag.AlignCenter)

        layout.addWidget(lbl_nombre)
        layout.addWidget(lbl_precio)

        # Input de Peso
        self.inp_peso = QLineEdit()
        self.inp_peso.setPlaceholderText(f"Ej: 0.750 {unidad.lower()}")
        self.inp_peso.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.inp_peso.setStyleSheet("""
            QLineEdit {
                background-color: #2D2D3A;
                color: #FFFFFF;
                border: 2px solid #BFA2DB;
                border-radius: 8px;
                padding: 10px;
                font-size: 24px;
                font-weight: bold;
            }
        """)
        self.inp_peso.textChanged.connect(self.actualizar_subtotal_en_vivo)
        self.inp_peso.returnPressed.connect(self.confirmar)
        layout.addWidget(self.inp_peso)

        self.lbl_subtotal_calculado = QLabel("Subtotal: $0")
        self.lbl_subtotal_calculado.setStyleSheet("color: #81C784; font-size: 16px; font-weight: bold;")
        self.lbl_subtotal_calculado.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.lbl_subtotal_calculado)

        # Botonera numérica rápida
        grid = QGridLayout()
        grid.setSpacing(6)
        teclas = [
            ('1', 0, 0), ('2', 0, 1), ('3', 0, 2),
            ('4', 1, 0), ('5', 1, 1), ('6', 1, 2),
            ('7', 2, 0), ('8', 2, 1), ('9', 2, 2),
            ('C', 3, 0), ('0', 3, 1), ('.', 3, 2)
        ]
        
        for t, f, c in teclas:
            btn = QPushButton(t)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            if t == 'C':
                btn.setStyleSheet("background-color: #D32F2F; color: white; border-radius: 6px; padding: 10px; font-weight: bold; font-size: 15px;")
                btn.clicked.connect(self.inp_peso.clear)
            else:
                btn.setStyleSheet("background-color: #2D2D3A; color: white; border-radius: 6px; padding: 10px; font-weight: bold; font-size: 15px;")
                btn.clicked.connect(lambda _, txt=t: self.inp_peso.setText(self.inp_peso.text() + txt))
            grid.addWidget(btn, f, c)

        layout.addLayout(grid)

        # Botón Aceptar
        btn_ok = QPushButton("✔ Confirmar Peso")
        btn_ok.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_ok.setStyleSheet("""
            QPushButton {
                background-color: #BFA2DB; color: #1E1E24; border: none;
                padding: 12px; border-radius: 8px; font-size: 14px; font-weight: bold;
            }
            QPushButton:hover { background-color: #A888CB; }
        """)
        btn_ok.clicked.connect(self.confirmar)
        layout.addWidget(btn_ok)

        self.inp_peso.setFocus()

    def actualizar_subtotal_en_vivo(self):
        try:
            val = float(self.inp_peso.text().strip().replace(',', '.'))
            sub = val * self.precio_unit
            self.lbl_subtotal_calculado.setText(f"Subtotal: ${sub:,.0f}".replace(',', '.'))
        except ValueError:
            self.lbl_subtotal_calculado.setText("Subtotal: $0")

    def confirmar(self):
        try:
            val = float(self.inp_peso.text().strip().replace(',', '.'))
            if val > 0:
                self.peso_ingresado = val
                self.accept()
            else:
                QMessageBox.warning(self, "Valor Inválido", "El peso debe ser mayor a 0.")
        except ValueError:
            QMessageBox.warning(self, "Valor Inválido", "Ingresa un número válido (ej: 0.550).")


class VentasView(QWidget):
    def __init__(self, usuario_actual=None):
        super().__init__()

        self.usuario_actual = usuario_actual or {"nombre": "Administrador", "rol": "Administrador"}
        self.carrito = []
        self.medio_pago_seleccionado = "Efectivo"

        layout = QHBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(18)

        # ====================================================
        # COLUMNA IZQUIERDA: ESCÁNER, TABLA CARRITO Y LIMPIEZA
        # ====================================================
        col_izq = QVBoxLayout()
        col_izq.setSpacing(14)

        # 1. Buscador y Escáner Continuo
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("🔍  Escanear código de barras, SKU o escribir nombre...")
        self.search_input.setStyleSheet("""
            QLineEdit {
                background-color: #2D2D3A;
                color: #FFFFFF;
                border: 2px solid #4A4A5A;
                border-radius: 8px;
                padding: 12px 16px;
                font-size: 15px;
                font-weight: bold;
            }
            QLineEdit:focus { border: 2px solid #BFA2DB; }
            QLineEdit::placeholder { color: #8E8E9F; font-weight: normal; }
        """)
        self.search_input.returnPressed.connect(self.procesar_escaneo_o_busqueda)
        col_izq.addWidget(self.search_input)

        # 2. Tabla del Carrito de Compras
        self.tabla_carrito = QTableWidget(0, 6)
        self.tabla_carrito.setHorizontalHeaderLabels(["SKU", "Descripción del Producto", "Cant. / Peso", "Precio Unit.", "Subtotal", "Acción"])
        self.tabla_carrito.verticalHeader().setVisible(False)
        self.tabla_carrito.verticalHeader().setDefaultSectionSize(46)
        self.tabla_carrito.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.tabla_carrito.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.tabla_carrito.setAlternatingRowColors(True)

        header = self.tabla_carrito.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Interactive) # SKU
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)     # Producto
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Interactive) # Cantidad / Peso
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Interactive) # Precio
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.Interactive) # Subtotal
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.Fixed)       # Eliminar

        self.tabla_carrito.setColumnWidth(0, 100)
        self.tabla_carrito.setColumnWidth(2, 175)
        self.tabla_carrito.setColumnWidth(3, 110)
        self.tabla_carrito.setColumnWidth(4, 120)
        self.tabla_carrito.setColumnWidth(5, 60)

        self.tabla_carrito.setStyleSheet("""
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
                padding: 12px 8px; 
                border: none; 
                font-weight: bold; 
                font-size: 13px;
            }
            QTableWidget::item { padding: 4px 8px; }
            QTableWidget::item:selected { 
                background-color: #BFA2DB; 
                color: #1E1E24; 
                font-weight: bold;
            }
        """)
        col_izq.addWidget(self.tabla_carrito)

        # 3. Barra Inferior
        bar_inf = QHBoxLayout()
        self.lbl_items_totales = QLabel("Ítems en carrito: 0 unidades")
        self.lbl_items_totales.setStyleSheet("color: #8E8E9F; font-size: 13px; font-weight: bold;")
        
        self.btn_limpiar = QPushButton("🗑️ Cancelar Venta (F4)")
        self.btn_limpiar.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_limpiar.setStyleSheet("""
            QPushButton {
                background-color: #3A3A4A; color: #E0E0E0; border: none;
                padding: 8px 16px; border-radius: 6px; font-size: 12px; font-weight: bold;
            }
            QPushButton:hover { background-color: #D32F2F; color: #FFFFFF; }
        """)
        self.btn_limpiar.clicked.connect(self.limpiar_venta)

        bar_inf.addWidget(self.lbl_items_totales)
        bar_inf.addStretch()
        bar_inf.addWidget(self.btn_limpiar)
        col_izq.addLayout(bar_inf)

        layout.addLayout(col_izq, 3)

        # ====================================================
        # COLUMNA DERECHA: PANEL DE COBRO
        # ====================================================
        panel_cobro = QFrame()
        panel_cobro.setMaximumWidth(390)
        panel_cobro.setMinimumWidth(350)
        panel_cobro.setStyleSheet("""
            QFrame {
                background-color: #FFFFFF;
                border-radius: 12px;
                border: 1px solid #E0E0E0;
            }
        """)
        cobro_layout = QVBoxLayout(panel_cobro)
        cobro_layout.setContentsMargins(18, 18, 18, 18)
        cobro_layout.setSpacing(10)

        lbl_tit_cobro = QLabel("Módulo de Cobro")
        lbl_tit_cobro.setStyleSheet("color: #1E1E24; font-size: 18px; font-weight: bold; border: none;")
        lbl_tit_cobro.setAlignment(Qt.AlignmentFlag.AlignCenter)
        cobro_layout.addWidget(lbl_tit_cobro)

        # Display Total a Pagar
        box_total = QFrame()
        box_total.setStyleSheet("""
            QFrame {
                background-color: #F8F8FC;
                border: 2px solid #BFA2DB;
                border-radius: 10px;
                padding: 6px;
            }
        """)
        bt_layout = QVBoxLayout(box_total)
        lbl_sub_tot = QLabel("TOTAL A PAGAR")
        lbl_sub_tot.setStyleSheet("color: #8E8E9F; font-size: 11px; font-weight: bold; border: none;")
        lbl_sub_tot.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        self.lbl_total_grande = QLabel("$0")
        self.lbl_total_grande.setStyleSheet("color: #6A1B9A; font-size: 32px; font-weight: 900; border: none;")
        self.lbl_total_grande.setAlignment(Qt.AlignmentFlag.AlignCenter)

        bt_layout.addWidget(lbl_sub_tot)
        bt_layout.addWidget(self.lbl_total_grande)
        cobro_layout.addWidget(box_total)

        # Medios de Pago
        lbl_mp = QLabel("Medio de Pago:")
        lbl_mp.setStyleSheet("color: #2D2D3A; font-size: 12px; font-weight: bold; border: none;")
        cobro_layout.addWidget(lbl_mp)

        grid_mp = QGridLayout()
        grid_mp.setSpacing(6)

        self.btn_efectivo = QPushButton("💵 Efectivo")
        self.btn_debito = QPushButton("💳 Débito")
        self.btn_credito = QPushButton("💳 Crédito")
        self.btn_transfer = QPushButton("📱 Transf.")

        self.botones_pago = [self.btn_efectivo, self.btn_debito, self.btn_credito, self.btn_transfer]

        for idx, btn in enumerate(self.botones_pago):
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            f, c = divmod(idx, 2)
            grid_mp.addWidget(btn, f, c)

        self.btn_efectivo.clicked.connect(lambda: self.seleccionar_medio_pago("Efectivo", self.btn_efectivo))
        self.btn_debito.clicked.connect(lambda: self.seleccionar_medio_pago("Débito", self.btn_debito))
        self.btn_credito.clicked.connect(lambda: self.seleccionar_medio_pago("Crédito", self.btn_credito))
        self.btn_transfer.clicked.connect(lambda: self.seleccionar_medio_pago("Transferencia", self.btn_transfer))

        cobro_layout.addLayout(grid_mp)

        # Monto Recibido y Botones de Billetes
        self.box_efectivo_container = QWidget()
        self.box_efectivo_container.setStyleSheet("border: none;")
        layout_box_efectivo = QVBoxLayout(self.box_efectivo_container)
        layout_box_efectivo.setContentsMargins(0, 2, 0, 0)
        layout_box_efectivo.setSpacing(6)

        lbl_recibido = QLabel("Monto Recibido ($):")
        lbl_recibido.setStyleSheet("color: #2D2D3A; font-size: 12px; font-weight: bold;")
        
        self.inp_recibido = QLineEdit()
        self.inp_recibido.setPlaceholderText("Ej: 10000")
        self.inp_recibido.setStyleSheet("""
            QLineEdit {
                background-color: #F8F8FC;
                color: #1E1E24;
                border: 1px solid #D1D1E0;
                border-radius: 6px;
                padding: 8px;
                font-size: 15px;
                font-weight: bold;
            }
            QLineEdit:focus { border: 2px solid #BFA2DB; background-color: #FFFFFF; }
        """)
        self.inp_recibido.textChanged.connect(self.calcular_vuelto)
        self.inp_recibido.returnPressed.connect(self.procesar_venta)

        grid_billetes = QGridLayout()
        grid_billetes.setSpacing(4)
        billetes = [("Exacto", 0), ("$1.000", 1000), ("$2.000", 2000), ("$5.000", 5000), ("$10.000", 10000), ("$20.000", 20000)]
        
        for idx, (txt, val) in enumerate(billetes):
            b_btn = QPushButton(txt)
            b_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            b_btn.setStyleSheet("""
                QPushButton {
                    background-color: #EFEFF5; color: #2D2D3A; border: 1px solid #D1D1E0;
                    padding: 5px; border-radius: 4px; font-weight: bold; font-size: 11px;
                }
                QPushButton:hover { background-color: #BFA2DB; color: #1E1E24; }
            """)
            b_btn.clicked.connect(lambda _, v=val: self.asignar_monto_rapido(v))
            f, c = divmod(idx, 3)
            grid_billetes.addWidget(b_btn, f, c)

        layout_box_efectivo.addWidget(lbl_recibido)
        layout_box_efectivo.addWidget(self.inp_recibido)
        layout_box_efectivo.addLayout(grid_billetes)
        cobro_layout.addWidget(self.box_efectivo_container)

        # Display Vuelto
        self.box_vuelto = QFrame()
        self.box_vuelto.setStyleSheet("""
            QFrame {
                background-color: #E8F5E9;
                border-radius: 8px;
                padding: 8px 12px;
                border: 1px solid #C8E6C9;
            }
        """)
        v_layout = QVBoxLayout(self.box_vuelto)
        v_layout.setContentsMargins(4, 4, 4, 4)
        v_layout.setSpacing(2)

        self.lbl_v_txt = QLabel("Vuelto al Cliente:")
        self.lbl_v_txt.setStyleSheet("color: #2E7D32; font-size: 12px; font-weight: bold; border: none;")
        
        self.lbl_vuelto_monto = QLabel("$0")
        self.lbl_vuelto_monto.setStyleSheet("color: #2E7D32; font-size: 20px; font-weight: 900; border: none;")
        self.lbl_vuelto_monto.setWordWrap(True)

        v_layout.addWidget(self.lbl_v_txt)
        v_layout.addWidget(self.lbl_vuelto_monto)
        cobro_layout.addWidget(self.box_vuelto)

        cobro_layout.addStretch()

        # Botón Principal de Cobro (F2)
        self.btn_procesar = QPushButton("💳 Procesar Venta (F2)")
        self.btn_procesar.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_procesar.setStyleSheet("""
            QPushButton {
                background-color: #BFA2DB;
                color: #1E1E24;
                border: none;
                padding: 14px;
                border-radius: 8px;
                font-size: 15px;
                font-weight: 900;
            }
            QPushButton:hover { background-color: #A888CB; }
            QPushButton:pressed { background-color: #9370DB; color: white; }
        """)
        self.btn_procesar.clicked.connect(self.procesar_venta)
        cobro_layout.addWidget(self.btn_procesar)

        layout.addWidget(panel_cobro, 1)

        self.seleccionar_medio_pago("Efectivo", self.btn_efectivo)

        # Atajos Globales
        QShortcut(QKeySequence("F2"), self, self.procesar_venta)
        QShortcut(QKeySequence("F4"), self, self.limpiar_venta)

    def showEvent(self, event):
        super().showEvent(event)
        self.search_input.setFocus()

    def seleccionar_medio_pago(self, medio, boton_activo):
        self.medio_pago_seleccionado = medio
        
        estilo_inactivo = """
            QPushButton {
                background-color: #F8F8FC; color: #2D2D3A; border: 1px solid #D1D1E0;
                padding: 8px; border-radius: 6px; font-size: 11px; font-weight: bold;
            }
            QPushButton:hover { background-color: #EFEFF5; }
        """
        estilo_activo = """
            QPushButton {
                background-color: #BFA2DB; color: #1E1E24; border: 2px solid #9370DB;
                padding: 8px; border-radius: 6px; font-size: 11px; font-weight: bold;
            }
        """

        for b in self.botones_pago:
            b.setStyleSheet(estilo_activo if b == boton_activo else estilo_inactivo)

        if medio != "Efectivo":
            self.box_efectivo_container.setVisible(False)
            self.box_vuelto.setVisible(False)
        else:
            self.box_efectivo_container.setVisible(True)
            self.box_vuelto.setVisible(True)
            self.calcular_vuelto()

    def procesar_escaneo_o_busqueda(self):
        texto = self.search_input.text().strip()
        if not texto:
            return

        exito, producto = buscar_producto_para_venta(texto)
        if exito:
            self.agregar_producto_al_carrito(producto)
            self.search_input.clear()
        else:
            QMessageBox.warning(self, "No Encontrado", str(producto))
            self.search_input.selectAll()

        self.search_input.setFocus()

    def agregar_producto_al_carrito(self, producto):
        id_prod = producto["id_producto"]
        sku = producto["sku"]
        nombre = producto["nombre_producto"]
        precio_base = float(producto["precio_venta_base"])
        valor_final = float(producto["valor_final"])
        unidad = (producto["unidad_medida"] or "UN").upper()
        stock_disp = float(producto.get("stock_actual", 0))

        if stock_disp <= 0:
            QMessageBox.warning(self, "Sin Stock", f"El producto '{nombre}' no tiene existencias disponibles.")
            return

        cant_actual_carrito = sum(it["cantidad"] for it in self.carrito if it["id_producto"] == id_prod)

        # Manejo de productos a granel / balanza
        if unidad in ["KG", "LT", "GR"]:
            dialogo = DialogoPeso(nombre, valor_final, unidad, self)
            if dialogo.exec() == QDialog.DialogCode.Accepted:
                peso = dialogo.peso_ingresado
                if cant_actual_carrito + peso > stock_disp:
                    QMessageBox.warning(
                        self, 
                        "Stock Insuficiente", 
                        f"No puedes agregar {peso:.3f} {unidad.lower()}. Stock disponible: {stock_disp:.3f} (En carrito: {cant_actual_carrito:.3f})."
                    )
                    return

                for item in self.carrito:
                    if item["id_producto"] == id_prod:
                        item["cantidad"] += peso
                        self.renderizar_carrito()
                        return
                
                self.carrito.append({
                    "id_producto": id_prod,
                    "sku": sku,
                    "nombre": nombre,
                    "precio_base": precio_base,
                    "valor_final": valor_final,
                    "cantidad": peso,
                    "unidad": unidad,
                    "stock_max": stock_disp
                })
                self.renderizar_carrito()
            return

        # Productos estándar por unidad
        if cant_actual_carrito + 1.0 > stock_disp:
            QMessageBox.warning(
                self, 
                "Stock Insuficiente", 
                f"No puedes agregar más unidades. Stock disponible: {int(stock_disp)} (En carrito: {int(cant_actual_carrito)})."
            )
            return

        for item in self.carrito:
            if item["id_producto"] == id_prod:
                item["cantidad"] += 1.0
                self.renderizar_carrito()
                return

        self.carrito.append({
            "id_producto": id_prod,
            "sku": sku,
            "nombre": nombre,
            "precio_base": precio_base,
            "valor_final": valor_final,
            "cantidad": 1.0,
            "unidad": "UN",
            "stock_max": stock_disp
        })
        self.renderizar_carrito()

    def abrir_edicion_peso(self, fila_idx):
        item = self.carrito[fila_idx]
        dialogo = DialogoPeso(item["nombre"], item["valor_final"], item["unidad"], self)
        dialogo.inp_peso.setText(str(item["cantidad"]))
        dialogo.inp_peso.selectAll()
        if dialogo.exec() == QDialog.DialogCode.Accepted:
            nuevo_peso = dialogo.peso_ingresado
            stock_disp = item.get("stock_max", 999999)
            if nuevo_peso > stock_disp:
                QMessageBox.warning(self, "Stock Insuficiente", f"El peso ingresado supera el stock ({stock_disp:.3f} {item['unidad'].lower()}).")
                return
            self.carrito[fila_idx]["cantidad"] = nuevo_peso
            self.renderizar_carrito()

    def renderizar_carrito(self):
        self.tabla_carrito.setRowCount(0)
        total_acumulado = 0.0
        total_unidades = 0.0

        for fila_idx, item in enumerate(self.carrito):
            self.tabla_carrito.insertRow(fila_idx)
            subtotal = item["cantidad"] * item["valor_final"]
            total_acumulado += subtotal
            total_unidades += item["cantidad"]

            sku_it = QTableWidgetItem(item["sku"])
            sku_it.setTextAlignment(Qt.AlignmentFlag.AlignCenter)

            nom_it = QTableWidgetItem(item["nombre"])
            nom_it.setTextAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)

            box_cant = QWidget()
            layout_cant = QHBoxLayout(box_cant)
            layout_cant.setContentsMargins(2, 2, 2, 2)
            layout_cant.setSpacing(4)
            layout_cant.setAlignment(Qt.AlignmentFlag.AlignCenter)

            es_pesable = item["unidad"] in ["KG", "LT", "GR"]

            if es_pesable:
                cant_str = f"⚖️ {item['cantidad']:.3f}".rstrip('0').rstrip('.') + f" {item['unidad'].lower()}"
                btn_editar_peso = QPushButton(cant_str)
                btn_editar_peso.setCursor(Qt.CursorShape.PointingHandCursor)
                btn_editar_peso.setStyleSheet("""
                    QPushButton {
                        background-color: #E8F5E9; color: #2E7D32; font-weight: 900;
                        border: 1px solid #A5D6A7; border-radius: 6px; padding: 4px 10px; font-size: 12px;
                    }
                    QPushButton:hover { background-color: #C8E6C9; }
                """)
                btn_editar_peso.clicked.connect(lambda _, idx=fila_idx: self.abrir_edicion_peso(idx))
                layout_cant.addWidget(btn_editar_peso)
            else:
                btn_menos = QPushButton("-")
                btn_mas = QPushButton("+")
                estilo_btns = """
                    QPushButton {
                        background-color: #2D2D3A; color: #FFFFFF; font-weight: bold; 
                        border-radius: 4px; min-width: 28px; max-width: 28px; min-height: 26px; max-height: 26px; font-size: 14px;
                    }
                    QPushButton:hover { background-color: #BFA2DB; color: #1E1E24; }
                """
                btn_menos.setStyleSheet(estilo_btns)
                btn_mas.setStyleSheet(estilo_btns)

                lbl_c = QLabel(str(int(item["cantidad"])))
                lbl_c.setAlignment(Qt.AlignmentFlag.AlignCenter)
                lbl_c.setStyleSheet("font-weight: 900; font-size: 13px; color: #1E1E24; min-width: 28px;")

                btn_menos.clicked.connect(lambda _, idx=fila_idx: self.modificar_cantidad(idx, -1))
                btn_mas.clicked.connect(lambda _, idx=fila_idx: self.modificar_cantidad(idx, 1))

                layout_cant.addWidget(btn_menos)
                layout_cant.addWidget(lbl_c)
                layout_cant.addWidget(btn_mas)

            precio_it = QTableWidgetItem(f"${item['valor_final']:,.0f}".replace(',', '.'))
            precio_it.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)

            sub_it = QTableWidgetItem(f"${subtotal:,.0f}".replace(',', '.'))
            sub_it.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)

            btn_del = QPushButton("❌")
            btn_del.setCursor(Qt.CursorShape.PointingHandCursor)
            btn_del.setStyleSheet("background: transparent; border: none; font-size: 13px;")
            btn_del.clicked.connect(lambda _, idx=fila_idx: self.eliminar_item_carrito(idx))

            self.tabla_carrito.setItem(fila_idx, 0, sku_it)
            self.tabla_carrito.setItem(fila_idx, 1, nom_it)
            self.tabla_carrito.setCellWidget(fila_idx, 2, box_cant)
            self.tabla_carrito.setItem(fila_idx, 3, precio_it)
            self.tabla_carrito.setItem(fila_idx, 4, sub_it)
            self.tabla_carrito.setCellWidget(fila_idx, 5, btn_del)

        self.lbl_total_grande.setText(f"${total_acumulado:,.0f}".replace(',', '.'))
        self.lbl_items_totales.setText(f"Ítems en carrito: {total_unidades:.2f}".rstrip('0').rstrip('.') + f" unidades ({len(self.carrito)} productos)")
        self.calcular_vuelto()

    def modificar_cantidad(self, indice, delta):
        if 0 <= indice < len(self.carrito):
            item = self.carrito[indice]
            nueva_cant = item["cantidad"] + delta
            if delta > 0 and nueva_cant > item.get("stock_max", 999999):
                QMessageBox.warning(self, "Stock Insuficiente", f"No hay más stock disponible para '{item['nombre']}'.")
                return
            item["cantidad"] = nueva_cant
            if item["cantidad"] <= 0:
                self.carrito.pop(indice)
            self.renderizar_carrito()

    def eliminar_item_carrito(self, indice):
        if 0 <= indice < len(self.carrito):
            self.carrito.pop(indice)
            self.renderizar_carrito()

    def asignar_monto_rapido(self, monto):
        total = self.obtener_total_actual()
        if monto == 0:
            self.inp_recibido.setText(str(int(total)))
        else:
            self.inp_recibido.setText(str(monto))
        self.calcular_vuelto()

    def obtener_total_actual(self):
        return sum(item["cantidad"] * item["valor_final"] for item in self.carrito)

    def calcular_vuelto(self):
        if self.medio_pago_seleccionado != "Efectivo":
            return

        total = self.obtener_total_actual()
        txt = self.inp_recibido.text().strip().replace('.', '')

        try:
            recibido = float(txt) if txt else 0.0
            vuelto = recibido - total
            if vuelto >= 0:
                self.box_vuelto.setStyleSheet("background-color: #E8F5E9; border-radius: 8px; padding: 8px; border: 1px solid #C8E6C9;")
                self.lbl_v_txt.setText("Vuelto al Cliente:")
                self.lbl_v_txt.setStyleSheet("color: #2E7D32; font-size: 12px; font-weight: bold; border: none;")
                self.lbl_vuelto_monto.setText(f"${vuelto:,.0f}".replace(',', '.'))
                self.lbl_vuelto_monto.setStyleSheet("color: #2E7D32; font-size: 22px; font-weight: 900; border: none;")
            else:
                falta = abs(vuelto)
                self.box_vuelto.setStyleSheet("background-color: #FFEBEE; border-radius: 8px; padding: 8px; border: 1px solid #FFCDD2;")
                self.lbl_v_txt.setText("Monto Insuficiente:")
                self.lbl_v_txt.setStyleSheet("color: #C62828; font-size: 12px; font-weight: bold; border: none;")
                self.lbl_vuelto_monto.setText(f"Faltan ${falta:,.0f}".replace(',', '.'))
                self.lbl_vuelto_monto.setStyleSheet("color: #C62828; font-size: 20px; font-weight: 900; border: none;")
        except ValueError:
            self.lbl_vuelto_monto.setText("$0")

    def limpiar_venta(self):
        if self.carrito:
            self.carrito.clear()
            self.inp_recibido.clear()
            self.renderizar_carrito()
        self.search_input.clear()
        self.search_input.setFocus()

    def procesar_venta(self):
        if not self.carrito:
            QMessageBox.warning(self, "Carrito Vacío", "No hay productos en el carrito para procesar.")
            return

        total = self.obtener_total_actual()
        
        if self.medio_pago_seleccionado == "Efectivo":
            txt = self.inp_recibido.text().strip().replace('.', '')
            recibido = float(txt) if txt else 0.0
            if recibido < total:
                QMessageBox.warning(self, "Monto Insuficiente", "El monto recibido es menor al total a pagar.")
                self.inp_recibido.setFocus()
                return

        payload_carrito = []
        for it in self.carrito:
            payload_carrito.append({
                "id_producto": it["id_producto"],
                "cantidad": it["cantidad"],
                "precio_base": it["precio_base"],
                "valor_final": it["valor_final"],
                "subtotal": it["cantidad"] * it["valor_final"]
            })

        cajero_nom = self.usuario_actual.get("nombre", "Cajero")

        exito, resultado = registrar_venta_directa(payload_carrito, self.medio_pago_seleccionado, usuario=cajero_nom)

        if exito:
            QMessageBox.information(
                self, 
                "Venta Exitosa", 
                f"Venta #{resultado} procesada correctamente por {cajero_nom}.\nTotal: ${total:,.0f} ({self.medio_pago_seleccionado})"
            )
            self.limpiar_venta()
        else:
            QMessageBox.critical(self, "Error al Cobrar", resultado)
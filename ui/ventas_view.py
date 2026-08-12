from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                               QLineEdit, QTableWidget, QTableWidgetItem, 
                               QHeaderView, QLabel, QFrame, QMessageBox, 
                               QInputDialog, QComboBox, QAbstractItemView)
from PySide6.QtCore import Qt
from PySide6.QtGui import QKeySequence, QShortcut

from services.ventas_service import buscar_producto_para_venta, registrar_venta_directa

class VentasView(QWidget):
    def __init__(self):
        super().__init__()
        
        self.carrito = [] 
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)

        # --- PANEL IZQUIERDO ---
        left_layout = QVBoxLayout()
        left_layout.setSpacing(12)
        
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("🔍 Escanear código QR/SKU o buscar por nombre y presionar ENTER...")
        self.search_input.setStyleSheet("""
            QLineEdit {
                background-color: #2D2D3A;
                color: #FFFFFF;
                border: 1px solid #4A4A5A;
                border-radius: 8px;
                padding: 12px 16px;
                font-size: 15px;
            }
            QLineEdit:focus { border: 2px solid #BFA2DB; }
            QLineEdit::placeholder { color: #8E8E9F; }
        """)
        self.search_input.returnPressed.connect(self.procesar_busqueda)
        left_layout.addWidget(self.search_input)

        self.tabla_carrito = QTableWidget(0, 6) 
        self.tabla_carrito.setHorizontalHeaderLabels(["SKU", "Producto", "Cant. / Peso", "Precio Unit.", "Subtotal", "Acciones"])
        
        self.tabla_carrito.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.tabla_carrito.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.tabla_carrito.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)

        header = self.tabla_carrito.horizontalHeader()
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)
        
        self.tabla_carrito.setStyleSheet("""
            QTableWidget { 
                background-color: #FFFFFF; 
                border: 1px solid #E0E0E0; 
                border-radius: 8px; 
                font-size: 14px; 
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

        left_layout.addWidget(self.tabla_carrito)

        # --- PANEL DERECHO (Resumen de Cobro Directo) ---
        right_frame = QFrame()
        right_frame.setFixedWidth(340)
        right_frame.setStyleSheet("""
            QFrame { background-color: #FFFFFF; border: 1px solid #E0E0E0; border-radius: 12px; } 
            QLabel { border: none; }
        """)
        
        right_layout = QVBoxLayout(right_frame)
        right_layout.setContentsMargins(20, 20, 20, 20)
        right_layout.setSpacing(10)

        titulo_resumen = QLabel("Módulo de Cobro Directo")
        titulo_resumen.setStyleSheet("font-size: 18px; font-weight: bold; color: #1E1E24;")
        titulo_resumen.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.lbl_cant_items = QLabel("Productos en carrito: 0")
        self.lbl_cant_items.setStyleSheet("font-size: 13px; color: #555566;")

        # Total Destacado
        self.lbl_total = QLabel("$0")
        self.lbl_total.setStyleSheet("""
            font-size: 30px; 
            font-weight: bold; 
            color: #9370DB; 
            background-color: #F8F8FC; 
            border: 1px solid #D1D1E0;
            border-radius: 8px;
            padding: 10px;
        """)
        self.lbl_total.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Selector Medio de Pago
        lbl_medio = QLabel("Medio de Pago:")
        lbl_medio.setStyleSheet("font-size: 13px; font-weight: bold; color: #2D2D3A;")

        self.cmb_medio_pago = QComboBox()
        self.cmb_medio_pago.addItems(["Efectivo", "Débito", "Crédito", "Transferencia"])
        self.cmb_medio_pago.setStyleSheet("""
            QComboBox { 
                padding: 8px; 
                border: 1px solid #D1D1E0; 
                border-radius: 6px; 
                background-color: #F8F8FC; 
                color: #1E1E24; 
                font-size: 13px; 
            }
            QComboBox QAbstractItemView { background-color: #FFFFFF; color: #1E1E24; selection-background-color: #BFA2DB; }
        """)
        self.cmb_medio_pago.currentTextChanged.connect(self.evaluar_cambio_medio_pago)

        # Campo Efectivo Entregado / Vuelto
        self.lbl_paga_con = QLabel("Monto Recibido ($):")
        self.lbl_paga_con.setStyleSheet("font-size: 13px; font-weight: bold; color: #2D2D3A;")

        self.input_paga_con = QLineEdit()
        self.input_paga_con.setPlaceholderText("Ej: 10000")
        self.input_paga_con.setStyleSheet("""
            QLineEdit { 
                padding: 8px; 
                border: 1px solid #D1D1E0; 
                border-radius: 6px; 
                background-color: #F8F8FC; 
                color: #1E1E24; 
                font-size: 14px; 
                font-weight: bold;
            }
        """)
        self.input_paga_con.textChanged.connect(self.calcular_vuelto)

        self.lbl_vuelto = QLabel("Vuelto: $0")
        self.lbl_vuelto.setStyleSheet("font-size: 15px; font-weight: bold; color: #2E7D32; background-color: #E8F5E9; padding: 8px; border-radius: 6px;")

        # Botón Cobrar Venta
        self.btn_confirmar = QPushButton("💳 Procesar Venta (F2)")
        self.btn_confirmar.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_confirmar.setStyleSheet("""
            QPushButton { 
                background-color: #BFA2DB; 
                color: #1E1E24; 
                border: none; 
                padding: 14px; 
                border-radius: 8px; 
                font-size: 16px; 
                font-weight: bold; 
            }
            QPushButton:hover { background-color: #A888CB; }
            QPushButton:pressed { background-color: #9370DB; color: white; }
        """)
        self.btn_confirmar.clicked.connect(self.procesar_venta_directa)

        right_layout.addWidget(titulo_resumen)
        right_layout.addWidget(self.lbl_cant_items)
        right_layout.addWidget(self.lbl_total)
        right_layout.addSpacing(5)
        right_layout.addWidget(lbl_medio)
        right_layout.addWidget(self.cmb_medio_pago)
        right_layout.addWidget(self.lbl_paga_con)
        right_layout.addWidget(self.input_paga_con)
        right_layout.addWidget(self.lbl_vuelto)
        right_layout.addStretch()
        right_layout.addWidget(self.btn_confirmar)

        layout.addLayout(left_layout)
        layout.addWidget(right_frame)

        self.shortcut_confirmar = QShortcut(QKeySequence("F2"), self)
        self.shortcut_confirmar.activated.connect(self.procesar_venta_directa)

    def procesar_busqueda(self):
        criterio = self.search_input.text().strip()
        if not criterio:
            return 
            
        exito, resultado = buscar_producto_para_venta(criterio)
        
        if exito:
            self.agregar_al_carrito(resultado)
            self.search_input.clear() 
        else:
            msg = QMessageBox(self)
            msg.setWindowTitle("Atención")
            msg.setText(resultado)
            msg.setIcon(QMessageBox.Icon.Warning)
            msg.setStyleSheet("QMessageBox { background-color: #FFFFFF; } QLabel { color: #1E1E24; font-weight: bold; }")
            msg.exec()
            self.search_input.selectAll()

    def agregar_al_carrito(self, producto):
        unidad = producto.get('unidad_medida', 'UN')
        stock_disp = float(producto.get('stock_actual', 0.0))
        
        if stock_disp <= 0:
            QMessageBox.warning(self, "Stock Agotado", f"El producto '{producto['nombre_producto']}' no tiene stock disponible.")
            return

        cant_en_carrito = sum(item['cantidad'] for item in self.carrito if item['id_producto'] == producto['id_producto'])
        stock_remanente = stock_disp - cant_en_carrito

        if stock_remanente <= 0:
            QMessageBox.warning(self, "Límite de Stock", f"Ya agregaste todo el stock disponible ({stock_disp} {unidad}) al carrito.")
            return

        cantidad = 1.0

        if unidad in ['KG', 'GR', 'LT']:
            precio_formateado = f"${producto['valor_final']:,.0f}".replace(',', '.')
            peso, ok = QInputDialog.getDouble(
                self, 
                "Ingreso de Peso / Cantidad", 
                f"Producto: '{producto['nombre_producto']}' ({precio_formateado} / {unidad})\n"
                f"Stock disponible: {stock_remanente:.3f} {unidad}\n\n"
                f"Ingrese el peso a vender ({unidad}):", 
                value=min(1.000, stock_remanente), 
                minValue=0.001, 
                maxValue=stock_remanente,
                decimals=3
            )
            if not ok or peso <= 0:
                return
            cantidad = peso
        else:
            if (cant_en_carrito + 1.0) > stock_disp:
                QMessageBox.warning(self, "Stock Insuficiente", f"No puedes agregar más unidades de '{producto['nombre_producto']}'.")
                return

        encontrado = False
        for item in self.carrito:
            if item['id_producto'] == producto['id_producto'] and unidad == 'UN':
                item['cantidad'] += cantidad
                item['subtotal'] = item['cantidad'] * item['valor_final']
                encontrado = True
                break
                
        if not encontrado:
            nuevo_item = {
                'id_producto': producto['id_producto'],
                'sku': producto['sku'],
                'nombre_producto': producto['nombre_producto'],
                'unidad_medida': unidad,
                'stock_maximo': stock_disp,
                'cantidad': cantidad,
                'precio_base': producto['precio_venta_base'],
                'valor_final': producto['valor_final'],
                'subtotal': cantidad * producto['valor_final']
            }
            self.carrito.append(nuevo_item)
            
        self.refrescar_tabla_y_totales()

    def cambiar_cantidad(self, indice, delta):
        if 0 <= indice < len(self.carrito):
            item = self.carrito[indice]
            paso = 0.5 if item['unidad_medida'] in ['KG', 'LT'] else 1.0
            nueva_cant = item['cantidad'] + (delta * paso)
            
            if delta > 0 and nueva_cant > item['stock_maximo']:
                QMessageBox.warning(self, "Límite de Stock", f"No puedes superar el stock registrado en inventario ({item['stock_maximo']} {item['unidad_medida']}).")
                return

            if nueva_cant <= 0:
                self.eliminar_del_carrito(indice)
            else:
                item['cantidad'] = nueva_cant
                item['subtotal'] = item['cantidad'] * item['valor_final']
                self.refrescar_tabla_y_totales()

    def eliminar_del_carrito(self, indice):
        if 0 <= indice < len(self.carrito):
            del self.carrito[indice]
            self.refrescar_tabla_y_totales()
            self.search_input.setFocus()

    def evaluar_cambio_medio_pago(self, texto_medio):
        es_efectivo = texto_medio == "Efectivo"
        self.lbl_paga_con.setVisible(es_efectivo)
        self.input_paga_con.setVisible(es_efectivo)
        self.lbl_vuelto.setVisible(es_efectivo)
        if not es_efectivo:
            self.input_paga_con.clear()

    def calcular_vuelto(self):
        total_acumulado = sum(item['subtotal'] for item in self.carrito)
        paga_str = self.input_paga_con.text().strip()
        
        if paga_str.isdigit():
            paga_val = float(paga_str)
            vuelto = paga_val - total_acumulado
            if vuelto >= 0:
                self.lbl_vuelto.setText(f"Vuelto: ${vuelto:,.0f}".replace(',', '.'))
                self.lbl_vuelto.setStyleSheet("font-size: 15px; font-weight: bold; color: #2E7D32; background-color: #E8F5E9; padding: 8px; border-radius: 6px;")
            else:
                self.lbl_vuelto.setText(f"Falta: ${abs(vuelto):,.0f}".replace(',', '.'))
                self.lbl_vuelto.setStyleSheet("font-size: 15px; font-weight: bold; color: #C62828; background-color: #FFEBEE; padding: 8px; border-radius: 6px;")
        else:
            self.lbl_vuelto.setText("Vuelto: $0")

    def refrescar_tabla_y_totales(self):
        self.tabla_carrito.setRowCount(0)
        total_acumulado = 0
        
        for fila_idx, item in enumerate(self.carrito):
            self.tabla_carrito.insertRow(fila_idx)
            
            unidad = item.get('unidad_medida', 'UN')
            if unidad in ['KG', 'LT', 'GR']:
                cant_str = f"{item['cantidad']:.3f}".rstrip('0').rstrip('.') + f" {unidad.lower()}"
            else:
                cant_str = f"{int(item['cantidad'])} un"

            celdas = [
                item['sku'],
                item['nombre_producto'],
                cant_str,
                f"${item['valor_final']:,.0f}".replace(',', '.'),
                f"${item['subtotal']:,.0f}".replace(',', '.')
            ]
            
            for col_idx, valor in enumerate(celdas):
                celda_ui = QTableWidgetItem(valor)
                celda_ui.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.tabla_carrito.setItem(fila_idx, col_idx, celda_ui)
            
            # Botones de Acción
            action_widget = QWidget()
            action_layout = QHBoxLayout(action_widget)
            action_layout.setContentsMargins(2, 2, 2, 2)
            action_layout.setSpacing(4)

            btn_menos = QPushButton("-")
            btn_mas = QPushButton("+")
            btn_del = QPushButton("❌")

            for btn in [btn_menos, btn_mas, btn_del]:
                btn.setCursor(Qt.CursorShape.PointingHandCursor)
                btn.setStyleSheet("""
                    QPushButton { 
                        background-color: #EFEFF5; 
                        border: none; 
                        border-radius: 4px; 
                        font-weight: bold; 
                        padding: 4px 8px; 
                    } 
                    QPushButton:hover { background-color: #BFA2DB; color: #1E1E24; }
                """)

            btn_menos.clicked.connect(lambda chk=False, idx=fila_idx: self.cambiar_cantidad(idx, -1))
            btn_mas.clicked.connect(lambda chk=False, idx=fila_idx: self.cambiar_cantidad(idx, 1))
            btn_del.clicked.connect(lambda chk=False, idx=fila_idx: self.eliminar_del_carrito(idx))

            action_layout.addWidget(btn_menos)
            action_layout.addWidget(btn_mas)
            action_layout.addWidget(btn_del)

            self.tabla_carrito.setCellWidget(fila_idx, 5, action_widget)
                
            total_acumulado += item['subtotal']
            
        texto_total = f"${total_acumulado:,.0f}".replace(',', '.')
        self.lbl_cant_items.setText(f"Productos en carrito: {len(self.carrito)}")
        self.lbl_total.setText(texto_total)
        self.calcular_vuelto()

    def procesar_venta_directa(self):
        if not self.carrito:
            QMessageBox.warning(self, "Carrito Vacío", "No hay productos en la lista para vender.")
            return

        medio = self.cmb_medio_pago.currentText()
        total_acumulado = sum(item['subtotal'] for item in self.carrito)

        # Validación de vuelto en efectivo
        if medio == "Efectivo":
            paga_str = self.input_paga_con.text().strip()
            if paga_str.isdigit():
                if float(paga_str) < total_acumulado:
                    QMessageBox.warning(self, "Monto Insuficiente", "El dinero recibido es menor que el total de la venta.")
                    return
            elif total_acumulado > 0:
                QMessageBox.warning(self, "Monto Requerido", "Ingrese el monto recibido en efectivo para calcular el vuelto.")
                return

        exito, resultado = registrar_venta_directa(self.carrito, medio)
        
        if exito:
            id_generado = resultado
            mensaje = f"✅ Venta V-{id_generado} procesada e ingresada a Caja con éxito."
            if medio == "Efectivo" and self.input_paga_con.text().strip().isdigit():
                vuelto_val = float(self.input_paga_con.text()) - total_acumulado
                mensaje += f"\n\n💵 Entregar Vuelto: ${vuelto_val:,.0f}".replace(',', '.')
            
            msg = QMessageBox(self)
            msg.setWindowTitle("Venta Completada")
            msg.setText(mensaje)
            msg.setIcon(QMessageBox.Icon.Information)
            msg.setStyleSheet("""
                QMessageBox { background-color: #FFFFFF; } 
                QLabel { color: #1E1E24; font-weight: bold; font-size: 14px; }
                QPushButton { background-color: #BFA2DB; color: #1E1E24; border: none; padding: 8px 20px; border-radius: 6px; font-weight: bold; }
            """)
            msg.exec()
            
            self.carrito.clear()
            self.input_paga_con.clear()
            self.refrescar_tabla_y_totales()
            self.search_input.setFocus()
        else:
            QMessageBox.critical(self, "Error de Venta", str(resultado))
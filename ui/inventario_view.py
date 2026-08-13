import random
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QPushButton, 
                               QLineEdit, QTableWidget, QTableWidgetItem, 
                               QHeaderView, QDialog, QLabel, 
                               QMessageBox, QComboBox, QMenu, QAbstractItemView)
from PySide6.QtCore import Qt
from PySide6.QtGui import QAction, QColor

from services.inventario_service import (crear_producto, obtener_todos_los_productos, 
                                           buscar_productos, eliminar_producto_logico)

class InventarioView(QWidget):
    def __init__(self):
        super().__init__()
        
        # Estado para Paginación de alto rendimiento
        self.pagina_actual = 1
        self.items_por_pagina = 50
        self.total_paginas = 1
        self.todos_los_productos_cache = []
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(16)

        # --- 1. TARJETAS KPI DE RESUMEN ---
        kpi_layout = QHBoxLayout()
        kpi_layout.setSpacing(16)

        self.card_total = self.crear_tarjeta_kpi("Total Productos", "0", "#BFA2DB")
        self.card_critico = self.crear_tarjeta_kpi("Stock Crítico", "0", "#D32F2F")
        self.card_valor = self.crear_tarjeta_kpi("Valoración Inv. Total", "$0", "#2E7D32")

        kpi_layout.addWidget(self.card_total)
        kpi_layout.addWidget(self.card_critico)
        kpi_layout.addWidget(self.card_valor)
        
        layout.addLayout(kpi_layout)

        # --- 2. BARRA SUPERIOR (Buscador y Agregar) ---
        top_layout = QHBoxLayout()
        top_layout.setSpacing(12)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("🔍  Buscar por código, nombre o categoría...")
        self.search_input.setStyleSheet("""
            QLineEdit {
                background-color: #2D2D3A;
                color: #FFFFFF;
                border: 1px solid #4A4A5A;
                border-radius: 8px;
                padding: 10px 14px;
                font-size: 14px;
            }
            QLineEdit:focus { border: 2px solid #BFA2DB; }
            QLineEdit::placeholder { color: #8E8E9F; }
        """)
        self.search_input.textChanged.connect(self.filtrar_productos)

        self.btn_agregar = QPushButton("+ Agregar Producto")
        self.btn_agregar.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_agregar.setStyleSheet("""
            QPushButton { 
                background-color: #BFA2DB; 
                color: #1E1E24; 
                border: none; 
                padding: 10px 22px; 
                border-radius: 8px; 
                font-size: 14px; 
                font-weight: bold; 
            }
            QPushButton:hover { background-color: #A888CB; }
            QPushButton:pressed { background-color: #9370DB; color: white; }
        """)
        self.btn_agregar.clicked.connect(self.abrir_modal_agregar)

        top_layout.addWidget(self.search_input)
        top_layout.addWidget(self.btn_agregar)

        layout.addLayout(top_layout)

        # --- 3. TABLA DE DATOS OPTIMIZADA ---
        self.tabla = QTableWidget(0, 7)
        self.tabla.setHorizontalHeaderLabels(["ID", "SKU", "Nombre del Producto", "Categoría", "Precio Base", "Valor Final", "Stock Actual"])
        
        self.tabla.verticalHeader().setVisible(False)
        
        self.tabla.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.tabla.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.tabla.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.tabla.setColumnHidden(0, True)

        self.tabla.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.tabla.customContextMenuRequested.connect(self.mostrar_menu_contextual)

        header = self.tabla.horizontalHeader()
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Interactive)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Interactive)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.Interactive)
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.Interactive)
        header.setSectionResizeMode(6, QHeaderView.ResizeMode.Interactive)

        self.tabla.setColumnWidth(1, 110)
        self.tabla.setColumnWidth(3, 160)
        self.tabla.setColumnWidth(4, 120)
        self.tabla.setColumnWidth(5, 120)
        self.tabla.setColumnWidth(6, 120)

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

        # --- 4. BARRA DE PAGINACIÓN ---
        pag_layout = QHBoxLayout()
        pag_layout.setContentsMargins(0, 4, 0, 0)
        
        self.lbl_info_pag = QLabel("Mostrando 0 - 0 de 0 productos")
        self.lbl_info_pag.setStyleSheet("color: #8E8E9F; font-size: 12px; font-weight: bold;")
        
        self.btn_anterior = QPushButton("◀ Anterior")
        self.btn_siguiente = QPushButton("Siguiente ▶")
        
        estilo_btn_pag = """
            QPushButton { 
                background-color: #2D2D3A; color: #FFFFFF; border: none; 
                padding: 6px 14px; border-radius: 6px; font-weight: bold; font-size: 12px; 
            }
            QPushButton:hover { background-color: #3A3A4A; }
            QPushButton:disabled { background-color: #E0E0E0; color: #A0A0A0; }
        """
        self.btn_anterior.setStyleSheet(estilo_btn_pag)
        self.btn_siguiente.setStyleSheet(estilo_btn_pag)
        self.btn_anterior.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_siguiente.setCursor(Qt.CursorShape.PointingHandCursor)
        
        self.btn_anterior.clicked.connect(self.pagina_anterior)
        self.btn_siguiente.clicked.connect(self.pagina_siguiente)

        pag_layout.addWidget(self.lbl_info_pag)
        pag_layout.addStretch()
        pag_layout.addWidget(self.btn_anterior)
        pag_layout.addWidget(self.btn_siguiente)
        
        layout.addLayout(pag_layout)

        self.cargar_datos_tabla()

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
        
        tit_lower = titulo.lower()
        if "total" in tit_lower:
            self.lbl_val_total = lbl_val
        elif "crítico" in tit_lower or "critico" in tit_lower:
            self.lbl_val_critico = lbl_val
        elif "valor" in tit_lower or "inv" in tit_lower:
            self.lbl_val_inv = lbl_val

        card_layout.addWidget(lbl_tit)
        card_layout.addWidget(lbl_val)
        return card

    def showEvent(self, event):
        super().showEvent(event)
        self.cargar_datos_tabla()

    def cargar_datos_tabla(self, lista_productos=None):
        if lista_productos is None:
            exito, resultado = obtener_todos_los_productos()
            if not exito:
                QMessageBox.critical(self, "Error de Lectura", resultado)
                return
            self.todos_los_productos_cache = resultado
        else:
            self.todos_los_productos_cache = lista_productos

        tot_criticos = 0
        tot_valorizacion = 0.0
        
        for p in self.todos_los_productos_cache:
            es_dict = isinstance(p, dict)
            stock = float(p["stock_actual"] if es_dict else p[10])
            stock_min = float(p["stock_minimo"] if es_dict else p[11])
            val_final = float(p["valor_final"] if es_dict else p[9])
            
            tot_valorizacion += (stock * val_final)
            if stock <= stock_min:
                tot_criticos += 1

        if hasattr(self, 'lbl_val_total'):
            self.lbl_val_total.setText(str(len(self.todos_los_productos_cache)))
        if hasattr(self, 'lbl_val_critico'):
            self.lbl_val_critico.setText(str(tot_criticos))
        if hasattr(self, 'lbl_val_inv'):
            self.lbl_val_inv.setText(f"${tot_valorizacion:,.0f}".replace(',', '.'))

        total_items = len(self.todos_los_productos_cache)
        self.total_paginas = max(1, (total_items + self.items_por_pagina - 1) // self.items_por_pagina)
        self.pagina_actual = min(self.pagina_actual, self.total_paginas)

        self.renderizar_pagina()

    def renderizar_pagina(self):
        self.tabla.setRowCount(0)
        total_items = len(self.todos_los_productos_cache)
        
        if total_items == 0:
            self.lbl_info_pag.setText("Mostrando 0 - 0 de 0 productos")
            self.btn_anterior.setEnabled(False)
            self.btn_siguiente.setEnabled(False)
            return

        inicio_idx = (self.pagina_actual - 1) * self.items_por_pagina
        fin_idx = min(inicio_idx + self.items_por_pagina, total_items)
        
        productos_pagina = self.todos_los_productos_cache[inicio_idx:fin_idx]

        for fila_idx, producto in enumerate(productos_pagina):
            self.tabla.insertRow(fila_idx)
            
            es_dict = isinstance(producto, dict)
            unidad = producto["unidad_medida"] if es_dict else producto[5]
            stock_val = float(producto["stock_actual"] if es_dict else producto[10])
            stock_min = float(producto["stock_minimo"] if es_dict else producto[11])
            val_final = float(producto["valor_final"] if es_dict else producto[9])

            if unidad in ["KG", "LT", "GR"]:
                stock_str = f"{stock_val:.3f}".rstrip('0').rstrip('.') + f" {unidad.lower()}"
            else:
                stock_str = f"{int(stock_val)}"

            celdas = [
                str(producto["id_producto"] if es_dict else producto[0]),
                str(producto["sku"] if es_dict else producto[2]),
                str(producto["nombre_producto"] if es_dict else producto[3]),
                str(producto["categoria"] if es_dict else producto[4]),
                f"${(producto['precio_venta_base'] if es_dict else producto[7]):,.0f}".replace(',', '.'),
                f"${val_final:,.0f}".replace(',', '.'),
                stock_str
            ]
            
            es_critico = stock_val <= stock_min

            for col_idx, valor in enumerate(celdas):
                item = QTableWidgetItem(valor)
                
                if col_idx in [1, 3]:
                    item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                elif col_idx in [4, 5]:
                    item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                elif col_idx == 6:
                    item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                else:
                    item.setTextAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)

                if es_critico:
                    item.setBackground(QColor("#FFEBEE"))
                    item.setForeground(QColor("#C62828"))
                    if col_idx == 6:
                        item.setText(f"⚠️ {valor}")
                        
                self.tabla.setItem(fila_idx, col_idx, item)

        self.lbl_info_pag.setText(f"Mostrando {inicio_idx + 1} - {fin_idx} de {total_items} productos | Pág. {self.pagina_actual} de {self.total_paginas}")
        self.btn_anterior.setEnabled(self.pagina_actual > 1)
        self.btn_siguiente.setEnabled(self.pagina_actual < self.total_paginas)

    def pagina_anterior(self):
        if self.pagina_actual > 1:
            self.pagina_actual -= 1
            self.renderizar_pagina()

    def pagina_siguiente(self):
        if self.pagina_actual < self.total_paginas:
            self.pagina_actual += 1
            self.renderizar_pagina()

    def filtrar_productos(self, texto):
        self.pagina_actual = 1
        if not texto.strip():
            self.cargar_datos_tabla()
            return
            
        exito, resultados = buscar_productos(texto)
        if exito:
            self.cargar_datos_tabla(resultados)

    def mostrar_menu_contextual(self, posicion):
        item = self.tabla.itemAt(posicion)
        if not item:
            return

        fila = item.row()
        id_producto = int(self.tabla.item(fila, 0).text())
        nombre_producto = self.tabla.item(fila, 2).text()

        menu = QMenu(self)
        menu.setStyleSheet("""
            QMenu { 
                background-color: #2D2D3A; 
                color: #FFFFFF;
                border: 1px solid #4A4A5A; 
                border-radius: 6px;
                padding: 4px;
                font-size: 13px; 
            } 
            QMenu::item { padding: 6px 20px; border-radius: 4px; }
            QMenu::item:selected { background-color: #BFA2DB; color: #1E1E24; font-weight: bold; }
        """)
        
        accion_eliminar = QAction(f"🗑️  Eliminar '{nombre_producto}'", self)
        accion_eliminar.triggered.connect(lambda: self.confirmar_eliminacion(id_producto, nombre_producto))
        
        menu.addAction(accion_eliminar)
        menu.exec(self.tabla.viewport().mapToGlobal(posicion))

    def confirmar_eliminacion(self, id_producto, nombre_producto):
        respuesta = QMessageBox.question(
            self, 
            "Confirmar Eliminación", 
            f"¿Estás seguro de que deseas eliminar el producto '{nombre_producto}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if respuesta == QMessageBox.StandardButton.Yes:
            exito, mensaje = eliminar_producto_logico(id_producto)
            if exito:
                self.mostrar_mensaje_exito("Éxito", mensaje)
                self.cargar_datos_tabla()
            else:
                QMessageBox.warning(self, "Error", mensaje)

    def mostrar_mensaje_exito(self, titulo, mensaje):
        msg = QMessageBox(self)
        msg.setWindowTitle(titulo)
        msg.setText(mensaje)
        msg.setIcon(QMessageBox.Icon.Information)
        msg.setStyleSheet("""
            QMessageBox { background-color: #FFFFFF; }
            QLabel { color: #1E1E24; font-size: 14px; font-weight: bold; }
            QPushButton { 
                background-color: #BFA2DB; 
                color: #1E1E24; 
                border: none; 
                padding: 8px 24px; 
                border-radius: 6px; 
                font-weight: bold; 
                min-width: 90px; 
            }
            QPushButton:hover { background-color: #A888CB; }
        """)
        
        layout = msg.layout()
        if layout:
            for i in range(layout.count()):
                item = layout.itemAt(i)
                if isinstance(item, QHBoxLayout):
                    item.setAlignment(Qt.AlignmentFlag.AlignCenter)
                    
        msg.exec()

    def abrir_modal_agregar(self):
        modal = QDialog(self)
        modal.setWindowTitle("Agregar Nuevo Producto")
        modal.setMinimumWidth(700)
        modal.setStyleSheet("QDialog { background-color: #FFFFFF; border-radius: 12px; }")
        
        layout_modal = QVBoxLayout(modal)
        layout_modal.setContentsMargins(28, 24, 28, 24)
        layout_modal.setSpacing(16)
        
        titulo = QLabel("Complete los datos del nuevo producto")
        titulo.setStyleSheet("font-size: 18px; font-weight: bold; color: #1E1E24;")
        layout_modal.addWidget(titulo)
        
        grid_layout = QGridLayout()
        grid_layout.setHorizontalSpacing(20)
        grid_layout.setVerticalSpacing(12)
        
        self.inputs = {}
        
        estilo_inputs = """
            QLineEdit, QComboBox { 
                padding: 9px; 
                border: 1px solid #D1D1E0; 
                border-radius: 6px; 
                background-color: #F8F8FC; 
                color: #1E1E24; 
                font-size: 13px; 
            } 
            QLineEdit:focus, QComboBox:focus { 
                border: 2px solid #BFA2DB; 
                background-color: #FFFFFF;
            }
            QComboBox QAbstractItemView {
                background-color: #FFFFFF;
                color: #1E1E24;
                selection-background-color: #BFA2DB;
                selection-color: #1E1E24;
                border: 1px solid #D1D1E0;
                outline: none;
                padding: 4px;
            }
        """
        estilo_labels = "font-size: 13px; font-weight: bold; color: #2D2D3A;"
        
        def crear_label(texto):
            lbl = QLabel(texto)
            lbl.setStyleSheet(estilo_labels)
            return lbl

        # --- COLUMNA IZQUIERDA ---
        lbl_sku = crear_label("SKU (*):")
        layout_sku = QHBoxLayout()
        inp_sku = QLineEdit()
        inp_sku.setPlaceholderText("Ej: PRD-006")
        inp_sku.setStyleSheet(estilo_inputs)
        
        btn_auto_sku = QPushButton("⚡ Auto")
        btn_auto_sku.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_auto_sku.setStyleSheet("""
            QPushButton { 
                background-color: #EFEFF5; color: #333; border: 1px solid #CCC; 
                padding: 8px 12px; border-radius: 6px; font-weight: bold; font-size: 12px;
            }
            QPushButton:hover { background-color: #BFA2DB; }
        """)
        btn_auto_sku.clicked.connect(lambda: inp_sku.setText(f"PRD-{random.randint(100, 999)}"))
        
        layout_sku.addWidget(inp_sku)
        layout_sku.addWidget(btn_auto_sku)
        self.inputs["sku"] = inp_sku

        lbl_qr = crear_label("Cód. Barras / QR:")
        inp_qr = QLineEdit()
        inp_qr.setPlaceholderText("Ej: 780123456789")
        inp_qr.setStyleSheet(estilo_inputs)
        self.inputs["qr"] = inp_qr

        lbl_nombre = crear_label("Nombre del Producto (*):")
        inp_nombre = QLineEdit()
        inp_nombre.setPlaceholderText("Ej: Galletas Tritón 126g")
        inp_nombre.setStyleSheet(estilo_inputs)
        self.inputs["nombre"] = inp_nombre

        # CATEGORÍA EDITABLE CON AUTOCOMPLETADO
        lbl_cat = crear_label("Categoría:")
        cmb_categoria = QComboBox()
        cmb_categoria.setEditable(True)
        cmb_categoria.setStyleSheet(estilo_inputs)
        
        # Extraer categorías únicas de la lista en caché
        categorias_existentes = sorted(list(set(
            (p["categoria"] if isinstance(p, dict) else p[4]) 
            for p in self.todos_los_productos_cache 
            if (p["categoria"] if isinstance(p, dict) else p[4])
        )))
        
        cmb_categoria.addItems(categorias_existentes)
        cmb_categoria.setCurrentIndex(-1)
        cmb_categoria.lineEdit().setPlaceholderText("Ej: Snacks / Galletas")
        self.inputs["categoria"] = cmb_categoria

        lbl_unidad = crear_label("Unidad de Medida:")
        cmb_unidad = QComboBox()
        cmb_unidad.addItems(["UN (Unidades)", "KG (Kilos)", "LT (Litros)", "GR (Gramos)"])
        cmb_unidad.setStyleSheet(estilo_inputs)
        self.inputs["unidad"] = cmb_unidad

        grid_layout.addWidget(lbl_sku, 0, 0)
        grid_layout.addLayout(layout_sku, 1, 0)
        grid_layout.addWidget(lbl_qr, 2, 0)
        grid_layout.addWidget(inp_qr, 3, 0)
        grid_layout.addWidget(lbl_nombre, 4, 0)
        grid_layout.addWidget(inp_nombre, 5, 0)
        grid_layout.addWidget(lbl_cat, 6, 0)
        grid_layout.addWidget(cmb_categoria, 7, 0)
        grid_layout.addWidget(lbl_unidad, 8, 0)
        grid_layout.addWidget(cmb_unidad, 9, 0)

        # --- COLUMNA DERECHA ---
        lbl_costo = crear_label("Costo Compra Neto Unitario (*):")
        inp_costo = QLineEdit()
        inp_costo.setPlaceholderText("Ej: 5000")
        inp_costo.setStyleSheet(estilo_inputs)
        self.inputs["costo"] = inp_costo

        # CALCULADORA RÁPIDA DE CAJAS
        box_cajas = QWidget()
        box_cajas.setStyleSheet("background-color: #F0F0F8; border-radius: 6px; padding: 6px;")
        layout_box_cajas = QGridLayout(box_cajas)
        layout_box_cajas.setContentsMargins(6, 6, 6, 6)
        
        lbl_info_caja = QLabel("📦 ¿Ingresas por caja/display?")
        lbl_info_caja.setStyleSheet("font-size: 11px; font-weight: bold; color: #4A4A5A;")
        
        inp_cant_cajas = QLineEdit()
        inp_cant_cajas.setPlaceholderText("Nº Cajas")
        inp_cant_cajas.setStyleSheet(estilo_inputs)
        
        inp_u_por_caja = QLineEdit()
        inp_u_por_caja.setPlaceholderText("Unid/Caja (ej: 50 u 34)")
        inp_u_por_caja.setStyleSheet(estilo_inputs)
        
        inp_costo_caja = QLineEdit()
        inp_costo_caja.setPlaceholderText("Costo x Caja ($)")
        inp_costo_caja.setStyleSheet(estilo_inputs)

        layout_box_cajas.addWidget(lbl_info_caja, 0, 0, 1, 3)
        layout_box_cajas.addWidget(inp_cant_cajas, 1, 0)
        layout_box_cajas.addWidget(inp_u_por_caja, 1, 1)
        layout_box_cajas.addWidget(inp_costo_caja, 1, 2)

        lbl_precio = crear_label("Precio Venta Base (*):")
        inp_precio = QLineEdit()
        inp_precio.setPlaceholderText("Ej: 8990")
        inp_precio.setStyleSheet(estilo_inputs)
        self.inputs["precio"] = inp_precio

        lbl_desc = crear_label("Descuento Aplicado ($):")
        inp_desc = QLineEdit()
        inp_desc.setPlaceholderText("Ej: 500 (Opcional)")
        inp_desc.setStyleSheet(estilo_inputs)
        self.inputs["descuento"] = inp_desc

        lbl_valor_final = QLabel("Valor Final al Cliente: $0")
        lbl_valor_final.setStyleSheet("""
            font-size: 13px; font-weight: bold; color: #2E7D32; 
            background-color: #E8F5E9; padding: 8px; border-radius: 6px;
        """)

        lbl_stock = crear_label("Stock Inicial (Unidades):")
        inp_stock = QLineEdit()
        inp_stock.setPlaceholderText("Ej: 20 ó 1.500")
        inp_stock.setStyleSheet(estilo_inputs)
        self.inputs["stock"] = inp_stock

        lbl_stock_min = crear_label("Stock Mínimo (Alerta):")
        inp_stock_min = QLineEdit()
        inp_stock_min.setPlaceholderText("Ej: 5 ó 0.500")
        inp_stock_min.setStyleSheet(estilo_inputs)
        self.inputs["stock_min"] = inp_stock_min

        # Lógica de cálculo automático por cajas
        def calcular_desde_cajas():
            try:
                cajas = float(inp_cant_cajas.text().strip()) if inp_cant_cajas.text().strip().replace('.', '').isdigit() else 0.0
                u_por_caja = float(inp_u_por_caja.text().strip()) if inp_u_por_caja.text().strip().replace('.', '').isdigit() else 0.0
                costo_caja = float(inp_costo_caja.text().strip()) if inp_costo_caja.text().strip().replace('.', '').isdigit() else 0.0

                if cajas > 0 and u_por_caja > 0:
                    stock_total = cajas * u_por_caja
                    inp_stock.setText(f"{stock_total:.0f}" if stock_total.is_integer() else f"{stock_total:.3f}")
                    
                    if costo_caja > 0:
                        costo_unitario = costo_caja / u_por_caja
                        inp_costo.setText(f"{costo_unitario:.0f}")
            except Exception:
                pass

        inp_cant_cajas.textChanged.connect(calcular_desde_cajas)
        inp_u_por_caja.textChanged.connect(calcular_desde_cajas)
        inp_costo_caja.textChanged.connect(calcular_desde_cajas)

        def calcular_valor_final_en_vivo():
            try:
                p_base = float(inp_precio.text().strip()) if inp_precio.text().strip().replace('.', '').isdigit() else 0.0
                desc = float(inp_desc.text().strip()) if inp_desc.text().strip().replace('.', '').isdigit() else 0.0
                v_final = max(0.0, p_base - desc)
                lbl_valor_final.setText(f"Valor Final al Cliente: ${v_final:,.0f}".replace(',', '.'))
            except ValueError:
                lbl_valor_final.setText("Valor Final al Cliente: $0")

        inp_precio.textChanged.connect(calcular_valor_final_en_vivo)
        inp_desc.textChanged.connect(calcular_valor_final_en_vivo)

        grid_layout.addWidget(lbl_costo, 0, 1)
        grid_layout.addWidget(inp_costo, 1, 1)
        grid_layout.addWidget(box_cajas, 2, 1)
        grid_layout.addWidget(lbl_precio, 3, 1)
        grid_layout.addWidget(inp_precio, 4, 1)
        grid_layout.addWidget(lbl_desc, 5, 1)
        grid_layout.addWidget(inp_desc, 6, 1)
        grid_layout.addWidget(lbl_valor_final, 7, 1)

        layout_stocks = QHBoxLayout()
        layout_stocks.setSpacing(10)
        
        box_s_ini = QVBoxLayout()
        box_s_ini.addWidget(lbl_stock)
        box_s_ini.addWidget(inp_stock)
        
        box_s_min = QVBoxLayout()
        box_s_min.addWidget(lbl_stock_min)
        box_s_min.addWidget(inp_stock_min)
        
        layout_stocks.addLayout(box_s_ini)
        layout_stocks.addLayout(box_s_min)
        
        grid_layout.addLayout(layout_stocks, 8, 1, 2, 1)

        layout_modal.addLayout(grid_layout)

        def intentar_guardar():
            faltantes = []
            if not self.inputs["sku"].text().strip():
                faltantes.append("SKU")
            if not self.inputs["nombre"].text().strip():
                faltantes.append("Nombre del Producto")
            if not self.inputs["costo"].text().strip():
                faltantes.append("Costo Compra")
            if not self.inputs["precio"].text().strip():
                faltantes.append("Precio Venta Base")

            if faltantes:
                QMessageBox.warning(
                    modal, 
                    "Campos Obligatorios Vacíos", 
                    f"Debes completar los siguientes campos obligatorios:\n\n• " + "\n• ".join(faltantes)
                )
                return

            sku = self.inputs["sku"].text().strip()
            qr = self.inputs["qr"].text().strip()
            nombre = self.inputs["nombre"].text().strip()
            categoria = self.inputs["categoria"].currentText().strip()
            costo_str = self.inputs["costo"].text().strip()
            precio_str = self.inputs["precio"].text().strip()
            descuento_str = self.inputs["descuento"].text().strip()
            stock_str = self.inputs["stock"].text().strip()
            stock_min_str = self.inputs["stock_min"].text().strip()
            
            unidad_seleccionada = self.inputs["unidad"].currentText().split()[0]

            exito, mensaje = crear_producto(
                sku=sku, 
                codigo_qr=qr, 
                nombre_producto=nombre, 
                categoria=categoria, 
                costo_neto=costo_str, 
                precio_base=precio_str, 
                stock_inicial=stock_str, 
                stock_minimo=stock_min_str,
                unidad_medida=unidad_seleccionada,
                descuento=descuento_str
            )
            
            if exito:
                modal.accept()
                self.mostrar_mensaje_exito("Éxito", mensaje)
                self.cargar_datos_tabla()
            else:
                QMessageBox.warning(modal, "Atención", mensaje)

        inp_stock_min.returnPressed.connect(intentar_guardar)

        btn_layout = QHBoxLayout()
        btn_layout.setContentsMargins(0, 10, 0, 0)
        btn_layout.setSpacing(10)
        
        btn_cancelar = QPushButton("Cancelar")
        btn_guardar = QPushButton("💾 Guardar Producto")
        
        btn_cancelar.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_guardar.setCursor(Qt.CursorShape.PointingHandCursor)

        btn_cancelar.setStyleSheet("""
            QPushButton { 
                padding: 10px 18px; 
                background-color: #EFEFF5; 
                color: #555; 
                border: none; 
                border-radius: 6px; 
                font-weight: bold; 
            }
            QPushButton:hover { background-color: #E2E2EC; }
        """)
        btn_guardar.setStyleSheet("""
            QPushButton { 
                padding: 10px 22px; 
                background-color: #BFA2DB; 
                color: #1E1E24; 
                border: none; 
                font-weight: bold; 
                border-radius: 6px; 
                font-size: 14px;
            }
            QPushButton:hover { background-color: #A888CB; }
            QPushButton:pressed { background-color: #9370DB; color: white; }
        """)
        
        btn_cancelar.clicked.connect(modal.reject)
        btn_guardar.clicked.connect(intentar_guardar)
        
        btn_layout.addStretch()
        btn_layout.addWidget(btn_cancelar)
        btn_layout.addWidget(btn_guardar)
        
        layout_modal.addLayout(btn_layout)
        
        inp_qr.setFocus()
        
        modal.exec()
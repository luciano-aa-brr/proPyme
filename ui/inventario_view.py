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
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(18)

        # --- BARRA SUPERIOR ---
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

        # --- TABLA DE DATOS ---
        self.tabla = QTableWidget(0, 7)
        self.tabla.setHorizontalHeaderLabels(["ID", "SKU", "Nombre Producto", "Categoría", "Precio Base", "Valor Final", "Stock"])
        
        self.tabla.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.tabla.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.tabla.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.tabla.setColumnHidden(0, True)

        self.tabla.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.tabla.customContextMenuRequested.connect(self.mostrar_menu_contextual)

        header = self.tabla.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        
        self.tabla.setStyleSheet("""
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
            QTableWidget::item:selected { 
                background-color: #BFA2DB; 
                color: #1E1E24; 
                font-weight: bold;
            }
        """)

        layout.addLayout(top_layout)
        layout.addWidget(self.tabla)

        self.cargar_datos_tabla()

    def showEvent(self, event):
        """Se ejecuta automáticamente cada vez que el usuario ingresa a la pestaña 'Inventario'."""
        super().showEvent(event)
        self.cargar_datos_tabla()

    def cargar_datos_tabla(self, lista_productos=None):
        """Limpia y vuelve a cargar los datos actualizados de la base de datos."""
        self.tabla.setRowCount(0)
        
        if lista_productos is None:
            exito, resultado = obtener_todos_los_productos()
            if not exito:
                QMessageBox.critical(self, "Error de Lectura", resultado)
                return
            productos = resultado
        else:
            productos = lista_productos

        for fila_idx, producto in enumerate(productos):
            self.tabla.insertRow(fila_idx)
            
            es_dict = isinstance(producto, dict)
            unidad = producto["unidad_medida"] if es_dict else producto[5]
            stock_val = float(producto["stock_actual"] if es_dict else producto[10])
            stock_min = float(producto["stock_minimo"] if es_dict else producto[11])

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
                f"${(producto['valor_final'] if es_dict else producto[9]):,.0f}".replace(',', '.'),
                stock_str
            ]
            
            # Evaluación de Stock Crítico
            es_critico = stock_val <= stock_min

            for col_idx, valor in enumerate(celdas):
                item = QTableWidgetItem(valor)
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                
                # Resaltar en rosado pastel si el stock está por debajo o igual al mínimo
                if es_critico:
                    item.setBackground(QColor("#FFEBEE")) # Fondo rosado tenue
                    item.setForeground(QColor("#C62828")) # Texto rojo oscuro
                    if col_idx == 6:
                        item.setText(f"⚠️ {valor}") # Icono de advertencia en columna Stock
                        
                self.tabla.setItem(fila_idx, col_idx, item)

    def filtrar_productos(self, texto):
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
        modal.setMinimumWidth(680)
        modal.setStyleSheet("QDialog { background-color: #FFFFFF; border-radius: 12px; }")
        
        layout_modal = QVBoxLayout(modal)
        layout_modal.setContentsMargins(28, 24, 28, 24)
        layout_modal.setSpacing(16)
        
        titulo = QLabel("Complete los datos del nuevo producto")
        titulo.setStyleSheet("font-size: 18px; font-weight: bold; color: #1E1E24;")
        layout_modal.addWidget(titulo)
        
        # Grid Layout de 2 columnas
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
            /* Estilo para la lista desplegable del ComboBox */
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
        # SKU con Auto
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

        # Código de Barras / QR
        lbl_qr = crear_label("Cód. Barras / QR:")
        inp_qr = QLineEdit()
        inp_qr.setPlaceholderText("Ej: 780123456789")
        inp_qr.setStyleSheet(estilo_inputs)
        self.inputs["qr"] = inp_qr

        # Nombre
        lbl_nombre = crear_label("Nombre del Producto (*):")
        inp_nombre = QLineEdit()
        inp_nombre.setPlaceholderText("Ej: Galletas Tritón 126g")
        inp_nombre.setStyleSheet(estilo_inputs)
        self.inputs["nombre"] = inp_nombre

        # Categoría
        lbl_cat = crear_label("Categoría:")
        inp_categoria = QLineEdit()
        inp_categoria.setPlaceholderText("Ej: Snacks / Galletas")
        inp_categoria.setStyleSheet(estilo_inputs)
        self.inputs["categoria"] = inp_categoria

        # Unidad
        lbl_unidad = crear_label("Unidad de Medida:")
        cmb_unidad = QComboBox()
        cmb_unidad.addItems(["UN (Unidades)", "KG (Kilos)", "LT (Litros)", "GR (Gramos)"])
        cmb_unidad.setStyleSheet(estilo_inputs)
        self.inputs["unidad"] = cmb_unidad

        # Ubicación Columna Izquierda
        grid_layout.addWidget(lbl_sku, 0, 0)
        grid_layout.addLayout(layout_sku, 1, 0)
        grid_layout.addWidget(lbl_qr, 2, 0)
        grid_layout.addWidget(inp_qr, 3, 0)
        grid_layout.addWidget(lbl_nombre, 4, 0)
        grid_layout.addWidget(inp_nombre, 5, 0)
        grid_layout.addWidget(lbl_cat, 6, 0)
        grid_layout.addWidget(inp_categoria, 7, 0)
        grid_layout.addWidget(lbl_unidad, 8, 0)
        grid_layout.addWidget(cmb_unidad, 9, 0)

        # --- COLUMNA DERECHA ---
        # Costo
        lbl_costo = crear_label("Costo Compra Neto (*):")
        inp_costo = QLineEdit()
        inp_costo.setPlaceholderText("Ej: 5000")
        inp_costo.setStyleSheet(estilo_inputs)
        self.inputs["costo"] = inp_costo

        # Precio Base
        lbl_precio = crear_label("Precio Venta Base (*):")
        inp_precio = QLineEdit()
        inp_precio.setPlaceholderText("Ej: 8990")
        inp_precio.setStyleSheet(estilo_inputs)
        self.inputs["precio"] = inp_precio

        # Descuento
        lbl_desc = crear_label("Descuento Aplicado ($):")
        inp_desc = QLineEdit()
        inp_desc.setPlaceholderText("Ej: 500 (Opcional)")
        inp_desc.setStyleSheet(estilo_inputs)
        self.inputs["descuento"] = inp_desc

        # Valor Final
        lbl_valor_final = QLabel("Valor Final al Cliente: $0")
        lbl_valor_final.setStyleSheet("""
            font-size: 13px; font-weight: bold; color: #2E7D32; 
            background-color: #E8F5E9; padding: 8px; border-radius: 6px;
        """)

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

        # Stock Inicial y Mínimo
        lbl_stock = crear_label("Stock Inicial:")
        inp_stock = QLineEdit()
        inp_stock.setPlaceholderText("Ej: 20 ó 1.500")
        inp_stock.setStyleSheet(estilo_inputs)
        self.inputs["stock"] = inp_stock

        lbl_stock_min = crear_label("Stock Mínimo (Alerta):")
        inp_stock_min = QLineEdit()
        inp_stock_min.setPlaceholderText("Ej: 5 ó 0.500")
        inp_stock_min.setStyleSheet(estilo_inputs)
        self.inputs["stock_min"] = inp_stock_min

        # Ubicación Columna Derecha
        grid_layout.addWidget(lbl_costo, 0, 1)
        grid_layout.addWidget(inp_costo, 1, 1)
        grid_layout.addWidget(lbl_precio, 2, 1)
        grid_layout.addWidget(inp_precio, 3, 1)
        grid_layout.addWidget(lbl_desc, 4, 1)
        grid_layout.addWidget(inp_desc, 5, 1)
        grid_layout.addWidget(lbl_valor_final, 6, 1)

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
        
        grid_layout.addLayout(layout_stocks, 7, 1, 3, 1)

        layout_modal.addLayout(grid_layout)

        # Guardar
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
            categoria = self.inputs["categoria"].text().strip()
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

        # Botones
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
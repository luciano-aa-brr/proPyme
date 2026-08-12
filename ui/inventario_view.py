from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                               QLineEdit, QTableWidget, QTableWidgetItem, 
                               QHeaderView, QDialog, QFormLayout, QLabel, 
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

            if unidad == "KG":
                stock_str = f"{stock_val:.3f}".rstrip('0').rstrip('.') + " kg"
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
        modal.setMinimumWidth(500)
        modal.setStyleSheet("QDialog { background-color: #FFFFFF; border-radius: 12px; }")
        
        layout_modal = QVBoxLayout(modal)
        layout_modal.setContentsMargins(28, 28, 28, 28)
        
        titulo = QLabel("Complete los datos del nuevo producto")
        titulo.setStyleSheet("font-size: 18px; font-weight: bold; color: #1E1E24; margin-bottom: 12px;")
        layout_modal.addWidget(titulo)
        
        form_layout = QFormLayout()
        form_layout.setSpacing(12)
        
        self.inputs = {}
        
        campos_datos = [
            ("sku", "SKU (*):", "Ej: PRD-006"),
            ("qr", "Cód. Barras / QR:", "Ej: 780123456789"),
            ("nombre", "Nombre del Producto (*):", "Ej: Mousepad Gamer XL / Manzanas"),
            ("categoria", "Categoría:", "Ej: Accesorios / Frutas"),
            ("costo", "Costo Compra Neto (*):", "Ej: 5000"),
            ("precio", "Precio Venta Base (*):", "Ej: 8990"),
            ("descuento", "Descuento Aplicado ($):", "Ej: 500 (Opcional)"),
            ("stock", "Stock Inicial:", "Ej: 20 ó 1.500 (Opcional)"),
            ("stock_min", "Stock Mínimo:", "Ej: 5 ó 0.500 (Opcional)")
        ]
        
        estilo_inputs = """
            QLineEdit { 
                padding: 9px; 
                border: 1px solid #D1D1E0; 
                border-radius: 6px; 
                background-color: #F8F8FC; 
                color: #1E1E24; 
                font-size: 13px; 
            } 
            QLineEdit:focus { 
                border: 2px solid #BFA2DB; 
                background-color: #FFFFFF;
            }
        """
        estilo_labels = "font-size: 13px; font-weight: bold; color: #2D2D3A;"
        
        for clave, label_text, placeholder in campos_datos:
            lbl = QLabel(label_text)
            lbl.setStyleSheet(estilo_labels)
            
            inp = QLineEdit()
            inp.setPlaceholderText(placeholder)
            inp.setStyleSheet(estilo_inputs)
            
            self.inputs[clave] = inp 
            form_layout.addRow(lbl, inp)
            
        lbl_unidad = QLabel("Unidad de Medida:")
        lbl_unidad.setStyleSheet(estilo_labels)
        
        cmb_unidad = QComboBox()
        cmb_unidad.addItems(["UN (Unidades)", "KG (Kilos)", "LT (Litros)", "GR (Gramos)"])
        
        cmb_unidad.setStyleSheet("""
            QComboBox { 
                padding: 8px; 
                border: 1px solid #D1D1E0; 
                border-radius: 6px; 
                background-color: #F8F8FC; 
                color: #1E1E24; 
                font-size: 13px; 
            } 
            QComboBox:focus { border: 2px solid #BFA2DB; }
            QComboBox QAbstractItemView {
                background-color: #FFFFFF;
                color: #1E1E24;
                selection-background-color: #BFA2DB;
                selection-color: #1E1E24;
                border: 1px solid #D1D1E0;
                outline: none;
                padding: 4px;
            }
        """)
        self.inputs["unidad"] = cmb_unidad
        form_layout.addRow(lbl_unidad, cmb_unidad)

        layout_modal.addLayout(form_layout)
        
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

        btn_layout = QHBoxLayout()
        btn_layout.setContentsMargins(0, 18, 0, 0)
        btn_layout.setSpacing(10)
        
        btn_cancelar = QPushButton("Cancelar")
        btn_guardar = QPushButton("Guardar Producto")
        
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
                padding: 10px 20px; 
                background-color: #BFA2DB; 
                color: #1E1E24; 
                border: none; 
                font-weight: bold; 
                border-radius: 6px; 
            }
            QPushButton:hover { background-color: #A888CB; }
        """)
        
        btn_cancelar.clicked.connect(modal.reject)
        btn_guardar.clicked.connect(intentar_guardar)
        
        btn_layout.addStretch()
        btn_layout.addWidget(btn_cancelar)
        btn_layout.addWidget(btn_guardar)
        
        layout_modal.addLayout(btn_layout)
        modal.exec()
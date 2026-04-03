from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                               QLineEdit, QTableWidget, QTableWidgetItem, 
                               QHeaderView, QLabel, QFrame, QMessageBox)
from PySide6.QtCore import Qt

# Importamos las DOS funciones de nuestro servicio real
from services.ventas_service import buscar_producto_para_venta, registrar_venta

class VentasView(QWidget):
    def __init__(self):
        super().__init__()
        
        self.carrito = [] 
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)

        # --- PANEL IZQUIERDO ---
        left_layout = QVBoxLayout()
        
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Escanear código, SKU o buscar por nombre y presionar ENTER...")
        self.search_input.setStyleSheet("padding: 12px; border: 1px solid #ccc; border-radius: 6px; font-size: 16px; background-color: white; color: #333;")
        self.search_input.returnPressed.connect(self.procesar_busqueda)
        left_layout.addWidget(self.search_input)

        # UX: Agregamos una sexta columna para el botón de eliminar
        self.tabla_carrito = QTableWidget(0, 6) 
        self.tabla_carrito.setHorizontalHeaderLabels(["SKU", "Producto", "Cant.", "Precio", "Subtotal", "Acción"])
        
        header = self.tabla_carrito.horizontalHeader()
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch) # El nombre se estira
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents) # La columna de acción queda pequeña
        
        self.tabla_carrito.setStyleSheet("""
            QTableWidget { background-color: white; border: 1px solid #E6E6FA; font-size: 14px; color: #333;}
            QHeaderView::section { background-color: #F8F8FF; padding: 8px; border: 1px solid #E6E6FA; font-weight: bold; color: #4A4A4A; }
        """)

        left_layout.addWidget(self.tabla_carrito)

        # --- PANEL DERECHO ---
        right_frame = QFrame()
        right_frame.setFixedWidth(320)
        right_frame.setStyleSheet("QFrame { background-color: #F8F8FF; border: 1px solid #D8BFD8; border-radius: 8px; } QLabel { border: none; }")
        
        right_layout = QVBoxLayout(right_frame)
        right_layout.setContentsMargins(20, 20, 20, 20)
        right_layout.setSpacing(15)

        titulo_resumen = QLabel("Resumen de Venta")
        titulo_resumen.setStyleSheet("font-size: 18px; font-weight: bold; color: #4A4A4A;")
        titulo_resumen.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.lbl_subtotal = QLabel("Total Valor Final: $0")
        self.lbl_descuento = QLabel("Descuento General: -$0")
        self.lbl_total = QLabel("Total Monto: $0")

        for lbl in [self.lbl_subtotal, self.lbl_descuento]:
            lbl.setStyleSheet("font-size: 15px; color: #555;")
            
        self.lbl_total.setStyleSheet("font-size: 22px; font-weight: bold; color: #9370DB; margin-top: 15px;")

        self.btn_confirmar = QPushButton("Confirmar Venta")
        self.btn_confirmar.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_confirmar.setStyleSheet("""
            QPushButton { background-color: #9370DB; color: white; border: none; padding: 15px; border-radius: 6px; font-size: 16px; font-weight: bold; }
            QPushButton:hover { background-color: #8A2BE2; }
            QPushButton:pressed { background-color: #7B68EE; }
        """)
        
        # Conectamos a la función real que guarda en base de datos
        self.btn_confirmar.clicked.connect(self.confirmar_venta_real)

        right_layout.addWidget(titulo_resumen)
        right_layout.addSpacing(10)
        right_layout.addWidget(self.lbl_subtotal)
        right_layout.addWidget(self.lbl_descuento)
        right_layout.addWidget(self.lbl_total)
        right_layout.addStretch()
        right_layout.addWidget(self.btn_confirmar)

        layout.addLayout(left_layout)
        layout.addWidget(right_frame)

    # --- LÓGICA DE INTERFAZ Y CARRITO ---
    
    def procesar_busqueda(self):
        criterio = self.search_input.text().strip()
        if not criterio:
            return 
            
        exito, resultado = buscar_producto_para_venta(criterio)
        
        if exito:
            self.agregar_al_carrito(resultado)
            self.search_input.clear() 
        else:
            # Forzamos estilo de alerta para que se vea en modo oscuro
            msg = QMessageBox(self)
            msg.setWindowTitle("Atención")
            msg.setText(resultado)
            msg.setStyleSheet("QMessageBox { background-color: #F8F8FF; } QLabel { color: #333; font-weight: bold; }")
            msg.exec()
            self.search_input.selectAll() 

    def agregar_al_carrito(self, producto):
        encontrado = False
        for item in self.carrito:
            if item['id_producto'] == producto['id_producto']:
                item['cantidad'] += 1
                item['subtotal'] = item['cantidad'] * item['valor_final']
                encontrado = True
                break
                
        if not encontrado:
            nuevo_item = {
                'id_producto': producto['id_producto'],
                'sku': producto['sku'],
                'nombre_producto': producto['nombre_producto'],
                'cantidad': 1,
                'precio_base': producto['precio_venta_base'],
                'valor_final': producto['valor_final'],
                'subtotal': producto['valor_final']
            }
            self.carrito.append(nuevo_item)
            
        self.refrescar_tabla_y_totales()

    def eliminar_del_carrito(self, indice):
        """Elimina un producto del carrito según la fila seleccionada."""
        if 0 <= indice < len(self.carrito):
            producto_nombre = self.carrito[indice]['nombre_producto']
            del self.carrito[indice]
            self.refrescar_tabla_y_totales()
            self.search_input.setFocus() # Devuelve el cursor al buscador por comodidad

    def refrescar_tabla_y_totales(self):
        self.tabla_carrito.setRowCount(0)
        total_acumulado = 0
        
        for fila_idx, item in enumerate(self.carrito):
            self.tabla_carrito.insertRow(fila_idx)
            
            celdas = [
                item['sku'],
                item['nombre_producto'],
                str(item['cantidad']),
                f"${item['valor_final']:,.0f}".replace(',', '.'),
                f"${item['subtotal']:,.0f}".replace(',', '.')
            ]
            
            for col_idx, valor in enumerate(celdas):
                celda_ui = QTableWidgetItem(valor)
                celda_ui.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                celda_ui.setFlags(celda_ui.flags() & ~Qt.ItemFlag.ItemIsEditable)
                self.tabla_carrito.setItem(fila_idx, col_idx, celda_ui)
            
            # --- INYECCIÓN DEL BOTÓN ELIMINAR ---
            btn_eliminar = QPushButton("❌")
            btn_eliminar.setCursor(Qt.CursorShape.PointingHandCursor)
            btn_eliminar.setStyleSheet("background-color: transparent; border: none; font-size: 14px; padding: 5px;")
            # Usamos una función lambda para pasarle el índice exacto de la fila al botón
            btn_eliminar.clicked.connect(lambda checked=False, idx=fila_idx: self.eliminar_del_carrito(idx))
            
            self.tabla_carrito.setCellWidget(fila_idx, 5, btn_eliminar)
                
            total_acumulado += item['subtotal']
            
        texto_total = f"${total_acumulado:,.0f}".replace(',', '.')
        self.lbl_subtotal.setText(f"Total Valor Final: {texto_total}")
        self.lbl_total.setText(f"Total Monto: {texto_total}")

    # --- CONEXIÓN REAL A SQLITE ---
    def confirmar_venta_real(self):
        if not self.carrito:
            msg = QMessageBox(self)
            msg.warning(self, "Carrito Vacío", "No hay productos para vender.")
            return
            
        # Llamamos al servicio (Capa 2) que ejecuta la transacción
        exito, resultado = registrar_venta(self.carrito)
        
        if exito:
            id_generado = resultado
            mensaje = f"Venta registrada en base de datos con éxito.\n\nEl ID de esta venta es: V-{id_generado}\n\nPor favor, diríjase a la Caja para procesar el pago."
            
            msg = QMessageBox(self)
            msg.setWindowTitle("Venta Exitosa")
            msg.setText(mensaje)
            msg.setStyleSheet("QMessageBox { background-color: #F8F8FF; } QLabel { color: #333; font-weight: bold; }")
            msg.exec()
            
            self.carrito.clear()
            self.refrescar_tabla_y_totales()
        else:
            msg = QMessageBox(self)
            msg.setWindowTitle("Error")
            msg.setText(resultado)
            msg.setStyleSheet("QMessageBox { background-color: #F8F8FF; } QLabel { color: #333; font-weight: bold; }")
            msg.exec()
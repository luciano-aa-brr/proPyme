from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                               QLineEdit, QTableWidget, QTableWidgetItem, 
                               QHeaderView, QDialog, QFormLayout, QLabel, QMessageBox)
from PySide6.QtCore import Qt

# Importamos la capa de servicios (El puente a la BD)
from services.inventario_service import crear_producto, obtener_todos_los_productos

class InventarioView(QWidget):
    def __init__(self):
        super().__init__()
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        # --- Barra superior ---
        top_layout = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Buscar producto por código, nombre o categoría...")
        self.search_input.setStyleSheet("padding: 10px; border: 1px solid #ccc; border-radius: 6px; font-size: 14px;")
        
        self.btn_agregar = QPushButton("+ Agregar Producto")
        self.btn_agregar.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_agregar.setStyleSheet("""
            QPushButton { background-color: #9370DB; color: white; border: none; padding: 10px 20px; border-radius: 6px; font-size: 14px; font-weight: bold; }
            QPushButton:hover { background-color: #8A2BE2; }
            QPushButton:pressed { background-color: #7B68EE; }
        """)
        self.btn_agregar.clicked.connect(self.abrir_modal_agregar)

        top_layout.addWidget(self.search_input)
        top_layout.addWidget(self.btn_agregar)

        # --- Tabla de Datos ---
        self.tabla = QTableWidget(0, 6) # Empezamos con 0 filas reales
        self.tabla.setHorizontalHeaderLabels(["SKU", "Nombre Producto", "Categoría", "Precio Base", "Valor Final", "Stock"])
        header = self.tabla.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.tabla.setStyleSheet("""
            QTableWidget { background-color: white; border: 1px solid #E6E6FA; font-size: 14px; color: #333; }
            QHeaderView::section { background-color: #F8F8FF; padding: 8px; border: 1px solid #E6E6FA; font-weight: bold; color: #4A4A4A; }
        """)

        self.setStyleSheet("QMessageBox { background-color: #F8F8FF; } QMessageBox QLabel { color: #333; font-weight: bold; }")

        layout.addLayout(top_layout)
        layout.addWidget(self.tabla)

        # Cargar los datos reales desde SQLite al iniciar la vista
        self.cargar_datos_tabla()

    def cargar_datos_tabla(self):
        """Limpia la tabla y la llena con los datos reales de la BD."""
        self.tabla.setRowCount(0) # Limpiar tabla
        exito, resultado = obtener_todos_los_productos()
        
        if exito:
            for fila_idx, producto in enumerate(resultado):
                self.tabla.insertRow(fila_idx)
                
                # Mapeamos las columnas de la BD a las celdas de la tabla visual
                celdas = [
                    producto["sku"],
                    producto["nombre_producto"],
                    producto["categoria"],
                    f"${producto['precio_venta_base']:,.0f}".replace(',', '.'), # Formato moneda
                    f"${producto['valor_final']:,.0f}".replace(',', '.'),       # Formato moneda
                    str(producto["stock_actual"])
                ]
                
                for col_idx, valor in enumerate(celdas):
                    item = QTableWidgetItem(valor)
                    item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                    item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable) 
                    self.tabla.setItem(fila_idx, col_idx, item)
        else:
            QMessageBox.critical(self, "Error de Lectura", resultado)

    def abrir_modal_agregar(self):
        modal = QDialog(self)
        modal.setWindowTitle("Agregar Nuevo Producto")
        modal.setMinimumWidth(450)
        modal.setStyleSheet("QDialog { background-color: #F8F8FF; }")
        
        layout_modal = QVBoxLayout(modal)
        layout_modal.setContentsMargins(25, 25, 25, 25)
        
        titulo = QLabel("Complete los datos del nuevo producto")
        titulo.setStyleSheet("font-size: 16px; font-weight: bold; color: #4A4A4A; margin-bottom: 10px;")
        layout_modal.addWidget(titulo)
        
        form_layout = QFormLayout()
        form_layout.setSpacing(12)
        
        # Diccionario para guardar referencias a los inputs y leerlos después
        self.inputs = {}
        
        # Definimos los campos con una clave interna para identificarlos
        campos_datos = [
            ("sku", "SKU:", "Ej: PRD-006"),
            ("qr", "Cód. Barras / QR:", "Ej: 780123456789"),
            ("nombre", "Nombre del Producto:", "Ej: Mousepad Gamer XL"),
            ("categoria", "Categoría:", "Ej: Accesorios"),
            ("costo", "Costo Compra (Neto):", "Ej: 5000"),
            ("precio", "Precio Venta Base:", "Ej: 8990"),
            ("stock", "Stock Inicial:", "Ej: 20"),
            ("stock_min", "Stock Mínimo:", "Ej: 5")
        ]
        
        estilo_inputs = "QLineEdit { padding: 8px; border: 1px solid #D8BFD8; border-radius: 4px; background-color: white; color: #333; font-size: 14px; } QLineEdit:focus { border: 2px solid #9370DB; }"
        estilo_labels = "font-size: 14px; font-weight: bold; color: #4A4A4A;"
        
        for clave, label_text, placeholder in campos_datos:
            lbl = QLabel(label_text)
            lbl.setStyleSheet(estilo_labels)
            
            inp = QLineEdit()
            inp.setPlaceholderText(placeholder)
            inp.setStyleSheet(estilo_inputs)
            
            # Guardamos el input en nuestro diccionario
            self.inputs[clave] = inp 
            form_layout.addRow(lbl, inp)
            
        layout_modal.addLayout(form_layout)
        
        # --- LÓGICA DE GUARDADO ---
        def intentar_guardar():
            try:
                # 1. Extraemos y validamos los textos (convertimos a números donde corresponda)
                sku = self.inputs["sku"].text().strip()
                qr = self.inputs["qr"].text().strip()
                nombre = self.inputs["nombre"].text().strip()
                categoria = self.inputs["categoria"].text().strip()
                
                # Validamos que los campos numéricos no estén vacíos y sean números
                costo = float(self.inputs["costo"].text() or 0)
                precio = float(self.inputs["precio"].text() or 0)
                stock = int(self.inputs["stock"].text() or 0)
                stock_min = int(self.inputs["stock_min"].text() or 0)
                
                if not sku or not nombre or precio <= 0:
                    QMessageBox.warning(modal, "Campos Incompletos", "El SKU, Nombre y Precio son obligatorios.")
                    return
                
                # 2. Enviamos los datos al servicio
                exito, mensaje = crear_producto(sku, qr, nombre, categoria, costo, precio, stock, stock_min)
                
                if exito:
                    QMessageBox.information(modal, "Éxito", mensaje)
                    self.cargar_datos_tabla() # Refrescamos la tabla visual
                    modal.accept() # Cerramos el modal
                else:
                    QMessageBox.warning(modal, "Error", mensaje)
                    
            except ValueError:
                QMessageBox.warning(modal, "Error de Formato", "Los campos de Costo, Precio y Stock deben ser numéricos.")

        # --- Botones de acción ---
        btn_layout = QHBoxLayout()
        btn_layout.setContentsMargins(0, 15, 0, 0)
        
        btn_cancelar = QPushButton("Cancelar")
        btn_guardar = QPushButton("Guardar Producto")
        
        btn_cancelar.setStyleSheet("padding: 10px 15px; background-color: #e0e0e0; color: #333; border: none; border-radius: 6px; font-weight: bold;")
        btn_guardar.setStyleSheet("padding: 10px 15px; background-color: #9370DB; color: white; border: none; font-weight: bold; border-radius: 6px;")
        
        btn_cancelar.clicked.connect(modal.reject)
        btn_guardar.clicked.connect(intentar_guardar) # Conectamos a nuestra nueva función
        
        btn_layout.addStretch()
        btn_layout.addWidget(btn_cancelar)
        btn_layout.addWidget(btn_guardar)
        
        layout_modal.addLayout(btn_layout)
        modal.exec()
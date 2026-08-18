from PySide6.QtWidgets import (QDialog, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, 
                               QPushButton, QLineEdit, QLabel, QMessageBox, 
                               QTableWidget, QTableWidgetItem, QHeaderView, 
                               QComboBox, QAbstractItemView)
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor

from services.usuario_service import (obtener_todos_los_usuarios, 
                                       crear_usuario, cambiar_estado_usuario)

class UsuariosModal(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Gestión de Usuarios y Roles - ProPyme POS")
        self.resize(700, 480)
        self.setStyleSheet("background-color: #1E1E24; border-radius: 10px;")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(16)

        # Encabezado
        lbl_titulo = QLabel("👥 Administración de Usuarios y Cajeros")
        lbl_titulo.setStyleSheet("color: #FFFFFF; font-size: 18px; font-weight: bold;")
        layout.addWidget(lbl_titulo)

        # --- FORMULARIO RÁPIDO SUPERIOR ---
        form_box = QWidget()
        form_box.setStyleSheet("background-color: #2D2D3A; border-radius: 8px; padding: 10px;")
        form_layout = QHBoxLayout(form_box)
        form_layout.setContentsMargins(10, 8, 10, 8)
        form_layout.setSpacing(10)

        estilo_input = """
            QLineEdit, QComboBox {
                background-color: #1E1E24;
                color: #FFFFFF;
                border: 1px solid #4A4A5A;
                border-radius: 6px;
                padding: 8px;
                font-size: 13px;
            }
            QLineEdit:focus, QComboBox:focus { border: 2px solid #BFA2DB; }
        """

        self.inp_nombre = QLineEdit()
        self.inp_nombre.setPlaceholderText("Nombre (ej: Juan Pérez)")
        self.inp_nombre.setStyleSheet(estilo_input)

        self.inp_pin = QLineEdit()
        self.inp_pin.setPlaceholderText("PIN (4-6 dígitos)")
        self.inp_pin.setMaxLength(6)
        self.inp_pin.setStyleSheet(estilo_input)

        self.cmb_rol = QComboBox()
        self.cmb_rol.addItems(["Vendedor", "Administrador"])
        self.cmb_rol.setStyleSheet(estilo_input)

        btn_guardar = QPushButton("+ Crear Usuario")
        btn_guardar.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_guardar.setStyleSheet("""
            QPushButton {
                background-color: #BFA2DB;
                color: #1E1E24;
                border: none;
                padding: 8px 16px;
                border-radius: 6px;
                font-size: 13px;
                font-weight: bold;
            }
            QPushButton:hover { background-color: #A888CB; }
        """)
        btn_guardar.clicked.connect(self.procesar_creacion)

        form_layout.addWidget(self.inp_nombre, 2)
        form_layout.addWidget(self.inp_pin, 1)
        form_layout.addWidget(self.cmb_rol, 1)
        form_layout.addWidget(btn_guardar, 1)

        layout.addWidget(form_box)

        # --- TABLA DE USUARIOS ---
        self.tabla = QTableWidget(0, 5)
        self.tabla.setHorizontalHeaderLabels(["ID", "Nombre", "Rol", "Estado", "Acciones"])
        self.tabla.verticalHeader().setVisible(False)
        self.tabla.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.tabla.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)

        header = self.tabla.horizontalHeader()
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Interactive)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Interactive)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.Fixed)
        self.tabla.setColumnWidth(0, 40)
        self.tabla.setColumnWidth(2, 130)
        self.tabla.setColumnWidth(3, 100)
        self.tabla.setColumnWidth(4, 120)

        self.tabla.setStyleSheet("""
            QTableWidget {
                background-color: #FFFFFF;
                border: 1px solid #E0E0E0;
                border-radius: 8px;
                color: #1E1E24;
                font-size: 13px;
            }
            QHeaderView::section {
                background-color: #2D2D3A;
                color: #FFFFFF;
                padding: 8px;
                border: none;
                font-weight: bold;
            }
        """)

        layout.addWidget(self.tabla)

        # Botón Cerrar
        btn_cerrar = QPushButton("Cerrar")
        btn_cerrar.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_cerrar.setStyleSheet("""
            QPushButton {
                background-color: #2D2D3A;
                color: #FFFFFF;
                border: 1px solid #4A4A5A;
                padding: 8px 20px;
                border-radius: 6px;
                font-weight: bold;
            }
            QPushButton:hover { background-color: #3A3A4A; }
        """)
        btn_cerrar.clicked.connect(self.accept)
        layout.addWidget(btn_cerrar, alignment=Qt.AlignmentFlag.AlignRight)

        self.cargar_usuarios()

    def cargar_usuarios(self):
        self.tabla.setRowCount(0)
        exito, usuarios = obtener_todos_los_usuarios()
        if not exito:
            return

        for fila_idx, u in enumerate(usuarios):
            self.tabla.insertRow(fila_idx)

            id_item = QTableWidgetItem(str(u["id_usuario"]))
            id_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            
            nom_item = QTableWidgetItem(u["nombre"])
            rol_item = QTableWidgetItem(u["rol"])
            rol_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)

            est_item = QTableWidgetItem(u["estado"])
            est_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            if u["estado"] == "Inactivo":
                est_item.setForeground(QColor("#D32F2F"))

            self.tabla.setItem(fila_idx, 0, id_item)
            self.tabla.setItem(fila_idx, 1, nom_item)
            self.tabla.setItem(fila_idx, 2, rol_item)
            self.tabla.setItem(fila_idx, 3, est_item)

            # Botón Cambiar Estado
            btn_toggle = QPushButton("Desactivar" if u["estado"] == "Activo" else "Activar")
            btn_toggle.setCursor(Qt.CursorShape.PointingHandCursor)
            color_bg = "#EF9A9A" if u["estado"] == "Activo" else "#A5D6A7"
            color_tx = "#B71C1C" if u["estado"] == "Activo" else "#1B5E20"
            btn_toggle.setStyleSheet(f"""
                QPushButton {{
                    background-color: {color_bg};
                    color: {color_tx};
                    border: none;
                    border-radius: 4px;
                    font-weight: bold;
                    font-size: 11px;
                    padding: 4px;
                }}
            """)
            
            nuevo_est = "Inactivo" if u["estado"] == "Activo" else "Activo"
            btn_toggle.clicked.connect(lambda _, uid=u["id_usuario"], nest=nuevo_est: self.toggle_estado(uid, nest))
            self.tabla.setCellWidget(fila_idx, 4, btn_toggle)

    def procesar_creacion(self):
        nombre = self.inp_nombre.text().strip()
        pin = self.inp_pin.text().strip()
        rol = self.cmb_rol.currentText()

        exito, msg = crear_usuario(nombre, pin, rol)
        if exito:
            QMessageBox.information(self, "Éxito", msg)
            self.inp_nombre.clear()
            self.inp_pin.clear()
            self.cargar_usuarios()
        else:
            QMessageBox.warning(self, "Atención", msg)

    def toggle_estado(self, id_usuario, nuevo_estado):
        exito, msg = cambiar_estado_usuario(id_usuario, nuevo_estado)
        if exito:
            self.cargar_usuarios()
        else:
            QMessageBox.warning(self, "Acción Denegada", msg)